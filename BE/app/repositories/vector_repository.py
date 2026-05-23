import asyncio
import re
from typing import List, Optional

from langchain_core.documents import Document as LCDocument
from langchain_postgres import PGVectorStore
from llama_index.core import Document
from llama_index.core.base.embeddings.base import BaseEmbedding
from sentence_transformers import CrossEncoder
from sqlalchemy import text

from app.config.config import settings
from app.core.database import postgres_engine
from app.core.logger import get_logger
from app.repositories.base_repository import BaseRepository

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# HELPER CLASSES & FUNCTIONS
# ----------------------------------------------------------------------
class _LlamaEmbedWrapper:
  """Bridge between LlamaIndex Embedding Service and LangChain Embeddings."""

  def __init__(self, model: BaseEmbedding):
    self.model = model

  async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
    return await self.model.aget_text_embedding_batch(texts)

  async def aembed_query(self, text: str) -> List[float]:
    return await self.model.aget_text_embedding(text)

  def embed_documents(self, texts: List[str]) -> List[List[float]]:
    return asyncio.run(self.aembed_documents(texts))

  def embed_query(self, text: str) -> List[float]:
    return asyncio.run(self.aembed_query(text))


def sanitize_table_name(name: str) -> str:
  """Convert a model name to a valid Supabase table name."""
  if "/" in name:
    name = name.split("/")[-1]
  sanitized = re.sub(r"[^a-zA-Z0-9]", "_", name).lower()
  if sanitized and sanitized[0].isdigit():
    sanitized = "vec_" + sanitized
  return sanitized


# ----------------------------------------------------------------------
# VECTOR REPOSITORY
# ----------------------------------------------------------------------
class VectorRepository(BaseRepository):
  """
  Handles document vector indexing and semantic search using PGVector with model-specific tables.
  """

  def __init__(self, embedding_service: Optional[BaseEmbedding] = None):
    """Initializes the repository with a PGVector backend."""
    super().__init__(table_name="")
    self.embedding_service = embedding_service
    self._rerankers = {}
    self._ensured_tables = set()
    self.connection_string = postgres_engine.get_normalized_url()

    logger.info("[VectorStore]: Initialized with PGVector backend")

  def _run_sync(self, coro):
    """Bridge to run async coroutines in a synchronous context."""
    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

    if loop.is_running():
      import nest_asyncio

      nest_asyncio.apply(loop)

    return loop.run_until_complete(coro)

  async def ensure_vector_table(self, table_name: str, vector_dim: int):
    """Ensures the vector table exists and is optimized."""
    if table_name in self._ensured_tables:
      return

    try:
      engine_obj = await postgres_engine.get_engine()
      async with engine_obj._pool.begin() as conn:
        await self._ensure_vectors_schema(conn)
        await self._create_or_migrate_table(conn, table_name, vector_dim)
        await self._ensure_hnsw_index(conn, table_name)

      self._ensured_tables.add(table_name)
    except Exception as e:
      logger.error(f"[VectorStore]: Setup failed for table {table_name}: {e}")
      raise

  async def _ensure_vectors_schema(self, conn):
    """Create the vectors schema if missing."""
    await conn.execute(text("CREATE SCHEMA IF NOT EXISTS vectors"))

  async def _create_or_migrate_table(self, conn, table_name: str, vector_dim: int):
    """Atomic check for table existence and column alignment."""
    sql_check = text(
      "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'vectors' AND table_name = :table_name)"
    )
    result = await conn.execute(sql_check, {"table_name": table_name})
    if not result.scalar():
      logger.info(f"[VectorStore]: Creating table vectors.{table_name}")
      await conn.execute(
        text(f"""
        CREATE TABLE vectors.{table_name} (
          id uuid PRIMARY KEY,
          embedding vector({vector_dim}),
          document text,
          cmetadata jsonb
        )
      """)
      )
      return

    # Migration check
    sql_cols = text(
      "SELECT column_name FROM information_schema.columns WHERE table_schema = 'vectors' AND table_name = :table_name"
    )
    result = await conn.execute(sql_cols, {"table_name": table_name})
    existing_cols = {row[0] for row in result.fetchall()}

    for col, col_type in [("document", "text"), ("cmetadata", "jsonb")]:
      if col not in existing_cols:
        logger.info(f"[VectorStore]: Adding column '{col}' to vectors.{table_name}")
        await conn.execute(
          text(f"ALTER TABLE vectors.{table_name} ADD COLUMN {col} {col_type}")
        )

  async def _ensure_hnsw_index(self, conn, table_name: str):
    """Enable high-performance HNSW indexing."""
    index_name = f"idx_{table_name}_embedding"
    await conn.execute(
      text(f"""
      CREATE INDEX IF NOT EXISTS {index_name} 
      ON vectors.{table_name} USING hnsw (embedding vector_cosine_ops)
    """)
    )

  def _get_reranker(self, model_name: str = None):
    """Retrieve or initialize a CrossEncoder reranker."""
    target_model = model_name or settings.RERANKER_MODEL
    if target_model not in self._rerankers:
      import torch

      device = "cuda" if torch.cuda.is_available() else "cpu"
      logger.info(f"[VectorStore]: Initializing reranker {target_model} on {device}")
      self._rerankers[target_model] = CrossEncoder(target_model, device=device)
    return self._rerankers[target_model]

  async def _get_vector_store(self, model_name: str, embed_model: BaseEmbedding):
    """Returns a configured PGVectorStore (v2) instance using PGEngine."""

    table_name = sanitize_table_name(model_name)
    engine_obj = await postgres_engine.get_engine()

    # Verify dimension
    probe_emb = await embed_model.aget_text_embedding_batch(["dim_probe"])
    dim = len(probe_emb[0])

    await self.ensure_vector_table(table_name, dim)

    return await PGVectorStore.create(
      engine=engine_obj,
      embedding_service=_LlamaEmbedWrapper(embed_model),
      table_name=table_name,
      schema_name="vectors",
      content_column="document",
      embedding_column="embedding",
      metadata_json_column="cmetadata",
      id_column="id",
    )

  # ------------------------------------------------------------------
  # PUBLIC API
  # ------------------------------------------------------------------
  def upsert_documents(
    self, documents: List[Document], embed_model: Optional[BaseEmbedding] = None
  ):
    """Sync wrapper for document upsertion."""
    if not embed_model:
      logger.warning("[VectorStore]: No embed_model provided. Skipping.")
      return
    return self._run_sync(self._upsert_documents_async(documents, embed_model))

  async def _upsert_documents_async(
    self, documents: List[Document], embed_model: BaseEmbedding
  ):
    """Async implementation of document upsertion."""
    logger.info(
      f"[VectorStore]: Upserting {len(documents)} docs with {embed_model.model_name}"
    )

    lc_docs = []
    for doc in documents:
      metadata = doc.metadata.copy() if hasattr(doc, "metadata") else {}
      metadata["id"] = doc.node_id if hasattr(doc, "node_id") else doc.doc_id

      lc_docs.append(
        LCDocument(
          page_content=doc.text if hasattr(doc, "text") else doc.get_content(),
          metadata=metadata,
        )
      )

    store = await self._get_vector_store(embed_model.model_name, embed_model)
    ids = [d.metadata["id"] for d in lc_docs]
    await store.aadd_documents(lc_docs, ids=ids)

  async def _get_vector_embedding(
    self, text: str, model_name: Optional[str] = None, provider: Optional[str] = None
  ) -> List[float]:
    """Generates embedding for a single text."""
    target_service = self.embedding_service
    if model_name and (not target_service or model_name != target_service.model_name):
      from app.core.factory import get_embedding_model

      target_service = await get_embedding_model(provider=provider, model=model_name)

    results = await target_service.aget_text_embedding_batch([text])
    return results[0] if results else []

  async def search(
    self,
    query: str,
    k: int = 5,
    kb_id: Optional[str] = None,
    score_threshold: float = 0.0,
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    search_method: str = "hybrid",
    enable_auto_merging: bool = False,
    precomputed_dense_vector: Optional[List[float]] = None,
  ) -> List[dict]:
    """Semantic search with PGVector and optional auto-merging."""
    target_service = self.embedding_service

    # If kb_id is provided but model_name is missing, resolve it from the database
    if kb_id and not model_name:
      provider, model_name = await self._resolve_kb_embedding_config(kb_id)

    if model_name and (not target_service or model_name != target_service.model_name):
      from app.core.factory import get_embedding_model

      target_service = await get_embedding_model(provider=provider, model=model_name)

    store = await self._get_vector_store(target_service.model_name, target_service)
    filter_dict = {"kb_id": kb_id} if kb_id else {}

    try:
      docs_with_scores = await store.asimilarity_search_with_relevance_scores(
        query, k=k, filter=filter_dict, score_threshold=score_threshold
      )
    except Exception as e:
      logger.error(f"[VectorStore]: Search failed: {e}")
      return []

    return await self._process_search_results(docs_with_scores, enable_auto_merging)

  async def _process_search_results(
    self, docs_with_scores, enable_auto_merging: bool
  ) -> List[dict]:
    """Format and optionally merge search results."""
    formatted = []
    parent_ids = set()

    for doc, score in docs_with_scores:
      metadata = doc.metadata or {}
      if enable_auto_merging and "parent_id" in metadata:
        parent_ids.add(metadata["parent_id"])

      formatted.append(
        {
          "id": metadata.get("id"),
          "text": doc.page_content,
          "metadata": metadata,
          "score": score,
          "kb_id": metadata.get("kb_id"),
        }
      )

    if enable_auto_merging and parent_ids:
      await self._apply_auto_merging(formatted, list(parent_ids))

    return formatted

  async def _apply_auto_merging(self, results: List[dict], parent_ids: List[str]):
    """Fetch and replace chunk text with parent context."""
    try:
      client = await self._get_client()
      resp = (
        await client.table("graph_chunks")
        .select("id, chunk_text")
        .in_("id", parent_ids)
        .execute()
      )
      parent_map = {p["id"]: p["chunk_text"] for p in (resp.data or [])}

      for res in results:
        pid = res["metadata"].get("parent_id")
        if pid in parent_map:
          res["text"] = parent_map[pid]
          res["metadata"]["_is_parent_context"] = True
    except Exception as e:
      logger.error(f"[VectorStore]: Auto-merging failed: {e}")

  def rerank_results(
    self, results: List[dict], query: str, top_k: int, model_name: str
  ) -> List[dict]:
    """Rerank search results using CrossEncoder."""
    if not results:
      return []

    try:
      reranker = self._get_reranker(model_name)
      pairs = [[query, r["text"]] for r in results]
      scores = reranker.predict(pairs)

      for i, r in enumerate(results):
        r["score"] = float(scores[i])

      results.sort(key=lambda x: x["score"], reverse=True)
      return results[:top_k]
    except Exception as e:
      logger.error(f"[VectorStore]: Reranking failed: {e}")
      return results[:top_k]

  async def delete_by_kb(self, kb_id: str, model_name: Optional[str] = None) -> bool:
    """Delete all vectors for a KB."""
    if not kb_id:
      logger.warning("[VectorStore]: Missing kb_id for deletion.")
      return True

    try:
      provider = None
      if not model_name:
        provider, model_name = await self._resolve_kb_embedding_config(kb_id)

      target_service = self.embedding_service
      if model_name != (target_service.model_name if target_service else ""):
        from app.core.factory import get_embedding_model

        target_service = await get_embedding_model(provider=provider, model=model_name)

      store = await self._get_vector_store(model_name, target_service)
      client = await self._get_client()
      resp = (
        await client.table("graph_chunks").select("id").eq("kb_id", kb_id).execute()
      )
      ids = [c["id"] for c in (resp.data or [])]

      if ids:
        await store.adelete(ids=ids)
      return True
    except Exception as e:
      logger.exception(f"[VectorStore]: Delete KB {kb_id} failed: {e}")
      return False

  def delete_points_by_ids(
    self, point_ids: List[str], model_name: Optional[str] = None
  ) -> bool:
    """Sync wrapper for point deletion."""
    if not point_ids or not model_name:
      return True
    return self._run_sync(self._delete_points_async(point_ids, model_name))

  async def _delete_points_async(self, point_ids: List[str], model_name: str) -> bool:
    """Async implementation of point deletion."""
    try:
      target_service = self.embedding_service
      if model_name != (target_service.model_name if target_service else ""):
        from app.core.factory import get_embedding_model

        target_service = await get_embedding_model(model=model_name)

      store = await self._get_vector_store(model_name, target_service)
      await store.adelete(ids=point_ids)
      return True
    except Exception as e:
      logger.exception(f"[VectorStore]: Delete points failed: {e}")
      return False

  def delete_by_doc_id(self, doc_id: str, model_name: Optional[str] = None) -> bool:
    """Handled via graph_chunks linkage."""
    logger.info(
      f"[VectorStore]: delete_by_doc_id {doc_id} skipped (handled via CASCADE)"
    )
    return True

  async def _resolve_kb_embedding_config(self, kb_id: str) -> tuple[str, str]:
    """Resolves the embedding provider and model for a given knowledge base."""
    client = await self._get_client()
    response = await (
      client.table("knowledgebases")
      .select(
        "embedding_provider:embedding_provider_id(name), "
        "embedding_model:embedding_model_id(model_id)"
      )
      .eq("id", kb_id)
      .single()
      .execute()
    )

    data = response.data
    if (
      not data or not data.get("embedding_provider") or not data.get("embedding_model")
    ):
      raise ValueError(
        f"Knowledge base {kb_id} not found or missing embedding configuration."
      )

    return (data["embedding_provider"]["name"], data["embedding_model"]["model_id"])
