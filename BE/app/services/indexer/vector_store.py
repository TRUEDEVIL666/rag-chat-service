# app/services/indexer/vector_store.py
import re
from typing import List, Optional

from llama_index.core import Document
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import BaseNode, TextNode
from sentence_transformers import CrossEncoder

from app.config.config import settings
from app.core.logger import get_logger

from app.services.supabase.supabase_client import get_async_supabase_client

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def sanitize_table_name(name: str) -> str:
  """
  Convert a model name to a valid Supabase table name in the vectors schema.
  E.g. "ollama/bge-m3" -> "bge_m3", "nomic-embed-text" -> "nomic_embed_text"
  """
  # Strip provider prefix if present (e.g. "ollama/gemma" -> "gemma")
  if "/" in name:
    name = name.split("/")[-1]
  # Replace non-alphanumeric characters with underscores
  sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
  # Prefix with "vec_" if starts with a digit
  if sanitized and sanitized[0].isdigit():
    sanitized = "vec_" + sanitized
  return sanitized


# ----------------------------------------------------------------------
# VECTOR REPOSITORY (Supabase-backed)
# ----------------------------------------------------------------------
class VectorRepository:
  """
  Handles document vector indexing and semantic search using Supabase pgvector.
  """

  def __init__(
      self,
      embedding_service: Optional[BaseEmbedding] = None,
  ):
    self.embedding_service = embedding_service
    self._rerankers = {}  # Cache for reranker models: {model_name: CrossEncoder}
    self._ensured_tables = set()  # Cache of tables confirmed to exist

    logger.info("[VectorStore]: Initialized with Supabase backend")

  # ------------------------------------------------------------------
  # RERANKER (unchanged - CrossEncoder is storage-independent)
  # ------------------------------------------------------------------
  def _get_reranker(self, model_name: str = None):
    target_model = model_name or settings.RERANKER_MODEL
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if target_model not in self._rerankers:
      logger.info(
        f"[VectorStore]: Initializing CrossEncoder reranker: {target_model} on device: {device}")
      self._rerankers[target_model] = CrossEncoder(target_model, device=device)
    return self._rerankers[target_model]

  # ------------------------------------------------------------------
  # DYNAMIC TABLE CREATION
  # ------------------------------------------------------------------
  async def ensure_vector_table(self, table_name: str, vector_dim: int):
    """
    Create vectors.<table_name> if it doesn't exist, with HNSW index + CASCADE FK.
    Uses the create_vector_table_if_not_exists RPC (SECURITY DEFINER).
    Results are cached to avoid redundant checks.
    """
    if table_name in self._ensured_tables:
      return

    try:
      client = await get_async_supabase_client()
      await client.rpc("create_vector_table_if_not_exists", {
          "p_table_name": table_name,
          "p_vector_dim": vector_dim
      }).execute()
      self._ensured_tables.add(table_name)
      logger.info(
        f"[VectorStore]: Ensured vector table exists: vectors.{table_name} (dim={vector_dim})")
    except Exception as e:
      logger.error(
        f"[VectorStore]: Failed to ensure vector table {table_name}: {e}")
      raise

  # ------------------------------------------------------------------
  # UPSERT
  # ------------------------------------------------------------------
  def upsert_documents(
      self,
      documents: List[Document],
      embed_model: Optional[BaseEmbedding] = None,
  ):
    """
    Generate embeddings and upsert vectors into Supabase vectors.<model> table.
    The graph_chunks metadata is handled separately by GraphChunkRepository.
    """
    if not embed_model:
      logger.warning(
        "[VectorStore]: No embed_model provided. Skipping upsert.")
      return

    import asyncio
    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

    if loop.is_running():
      import nest_asyncio
      nest_asyncio.apply(loop)
      loop.run_until_complete(
        self._upsert_documents_async(documents, embed_model))
    else:
      loop.run_until_complete(
        self._upsert_documents_async(documents, embed_model))

  async def _upsert_documents_async(
      self,
      documents: List[Document],
      embed_model: BaseEmbedding,
  ):
    """Async implementation of upsert_documents."""
    # 1. Resolve table name from model
    model_name_raw = embed_model.model_name
    table_name = sanitize_table_name(model_name_raw)

    logger.info(
      f"[VectorStore]: Upserting {len(documents)} documents into vectors.{table_name}")

    # 2. Prepare Nodes
    nodes = []
    for doc in documents:
      if isinstance(doc, (TextNode, BaseNode)):
        nodes.append(doc)
      else:
        nodes.append(
          TextNode(text=doc.text, metadata=doc.metadata, id_=doc.doc_id))

    # 3. Generate Dense Embeddings
    texts = [n.text for n in nodes]
    embeddings = await embed_model.aget_text_embedding_batch(texts)

    if not embeddings:
      logger.warning(
        "[VectorStore]: No embeddings generated. Skipping upsert.")
      return

    # 4. Ensure vector table exists with correct dimensions
    vector_dim = len(embeddings[0])
    await self.ensure_vector_table(table_name, vector_dim)

    # 5. Build records for upsert
    records = []
    for node, emb in zip(nodes, embeddings):
      records.append({
          "id": node.node_id,
          "embedding": emb,
      })

    # 6. Batch upsert into Supabase (batch size 100 to avoid payload limits)
    client = await get_async_supabase_client()
    batch_size = 100
    total_upserted = 0

    for i in range(0, len(records), batch_size):
      batch = records[i:i + batch_size]
      try:
        await client.schema("vectors").table(table_name).upsert(batch).execute()
        total_upserted += len(batch)
      except Exception as e:
        logger.error(
          f"[VectorStore]: Supabase upsert failed for batch {i // batch_size + 1}: {e}")
        raise e

    logger.info(
      f"[VectorStore]: Successfully upserted {total_upserted} vectors into vectors.{table_name}")

  # ------------------------------------------------------------------
  # EMBEDDING
  # ------------------------------------------------------------------
  async def embed_text(self, text: str, model_name: Optional[str] = None, provider: Optional[str] = None) -> List[float]:
    """Generate embedding for a single text using the specified or default model."""
    if not text.strip():
      return []

    target_service: Optional[BaseEmbedding] = self.embedding_service

    if model_name:
      # If model requested differs, or we have no service, fetch new one
      if not self.embedding_service or model_name != self.embedding_service.model_name:
        from app.core.factory import get_embedding_model
        try:
          target_service = await get_embedding_model(provider=provider, model=model_name)
        except ValueError:
          # Fallback logic if provider is missing but model might be a slug?
          # We'll rely on factory throwing if it can't resolve.
          raise
    elif not target_service:
      raise ValueError(
        "No embedding model specified and no default service available.")

    embeddings = await target_service.aget_text_embedding_batch([text])
    return embeddings[0] if embeddings else []

  # ------------------------------------------------------------------
  # SEARCH (via search_chunks RPC)
  # ------------------------------------------------------------------
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
      precomputed_dense_vector: Optional[List[float]] = None
  ) -> List[dict]:
    """
    Search for relevant chunks using the search_chunks RPC.
    Supports 'dense', 'keyword', and 'hybrid' modes.
    """
    # 1. Map search_method names for backward compatibility
    search_mode = search_method
    if search_method == "semantic":
      search_mode = "dense"

    # 2. Generate query embedding (required for dense/hybrid)
    if search_mode in ("dense", "hybrid"):
      if precomputed_dense_vector:
        dense_vector = precomputed_dense_vector
      else:
        dense_vector = await self.embed_text(query, model_name=model_name, provider=provider)
    else:
      # For keyword-only search, we still need to pass a vector (RPC requires it)
      # Use a zero vector as placeholder
      dense_vector = [0.0] * 768  # Will be ignored by keyword mode

    # 3. Call search_chunks RPC
    rpc_params = {
        "query_text": query,
        "query_embedding": dense_vector,
        "match_count": k,
        "filter_kb_id": kb_id,
        "embedding_model": model_name or (
          self.embedding_service.model_name if self.embedding_service else "bge-m3"),
        "search_mode": search_mode,
        "match_threshold": score_threshold,
    }

    try:
      client = await get_async_supabase_client()
      response = await client.rpc("search_chunks", rpc_params).execute()
      results = response.data or []
    except Exception as e:
      logger.error(f"[VectorStore]: search_chunks RPC failed: {e}")
      return []

    # 4. Format results
    formatted_results = []

    # Auto-Merging: Collect parent IDs to fetch
    parent_ids_to_fetch = set()
    if enable_auto_merging:
      for row in results:
        meta = row.get("metadata") or {}
        if "parent_id" in meta:
          parent_ids_to_fetch.add(meta["parent_id"])

    # Fetch parent chunk texts if auto-merging
    parent_map = {}
    if parent_ids_to_fetch:
      try:
        parent_response = await client.table("graph_chunks").select(
            "id, chunk_text"
        ).in_("id", list(parent_ids_to_fetch)).execute()
        for p in (parent_response.data or []):
          parent_map[p["id"]] = p["chunk_text"]
      except Exception as e:
        logger.error(f"[VectorStore]: Failed to fetch parent nodes: {e}")

    for row in results:
      text = row.get("chunk_text", "")
      metadata = row.get("metadata") or {}

      # Auto-Merging: Replace with parent text if available
      if enable_auto_merging and "parent_id" in metadata:
        pid = metadata["parent_id"]
        if pid in parent_map:
          text = parent_map[pid]
          metadata["_is_parent_context"] = True

      formatted_results.append({
          "id": str(row.get("id", "")),
          "text": text,
          "metadata": metadata,
          "score": row.get("similarity", 0.0),
          "kb_id": metadata.get("kb_id"),
      })

    return formatted_results

  # ------------------------------------------------------------------
  # RERANKING
  # ------------------------------------------------------------------
  def rerank_results(
      self,
      results: List[dict],
      query: str,
      top_k: int,
      model_name: str
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

  # ------------------------------------------------------------------
  # DELETE (via CASCADE from graph_chunks)
  # ------------------------------------------------------------------
  async def delete_by_kb(self, kb_id: str, model_name: Optional[str] = None) -> bool:
    """
    Delete all vectors for a KB. CASCADE from graph_chunks handles vector cleanup.
    NOTE: This only deletes vectors. graph_chunks deletion should be handled separately.
    """
    if not kb_id:
      return False

    try:
      table_name = sanitize_table_name(model_name) if model_name else None
      if not table_name:
        logger.warning(
          "[VectorStore]: No model_name for delete_by_kb, skipping vector-specific deletion (CASCADE will handle it)")
        return True

      # Delete from the specific vector table by joining with graph_chunks
      client = await get_async_supabase_client()
      # Get all chunk IDs for this KB
      chunks_resp = await client.table("graph_chunks").select(
          "id"
      ).eq("kb_id", kb_id).execute()

      chunk_ids = [c["id"] for c in (chunks_resp.data or [])]
      if chunk_ids:
        # Delete from vector table
        batch_size = 500
        for i in range(0, len(chunk_ids), batch_size):
          batch = chunk_ids[i:i + batch_size]
          await client.schema("vectors").table(table_name).delete().in_(
              "id", batch
          ).execute()

      logger.info(
        f"[VectorStore]: Deleted {len(chunk_ids)} vectors for kb_id: {kb_id}")
      return True
    except Exception as e:
      logger.exception(
        f"[VectorStore]: Failed to delete vectors for kb_id {kb_id}: {e}")
      return False

  def delete_points_by_ids(self, point_ids: List[str], model_name: Optional[str] = None) -> bool:
    """
    Delete specific vectors by their IDs.
    With CASCADE, deleting graph_chunks rows auto-deletes vectors.
    This method is kept for backward compatibility but is now largely unnecessary.
    """
    if not point_ids:
      return True

    import asyncio
    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

    if loop.is_running():
      import nest_asyncio
      nest_asyncio.apply(loop)
      return loop.run_until_complete(
        self._delete_points_async(point_ids, model_name))
    else:
      return loop.run_until_complete(
        self._delete_points_async(point_ids, model_name))

  async def _delete_points_async(self, point_ids: List[str], model_name: Optional[str] = None) -> bool:
    """Async implementation of delete_points_by_ids."""
    try:
      table_name = sanitize_table_name(model_name) if model_name else None
      if not table_name:
        logger.warning(
          "[VectorStore]: No model_name for delete, relying on CASCADE")
        return True

      client = await get_async_supabase_client()
      batch_size = 500
      total_deleted = 0

      for i in range(0, len(point_ids), batch_size):
        batch = point_ids[i:i + batch_size]
        await client.schema("vectors").table(table_name).delete().in_(
            "id", batch
        ).execute()
        total_deleted += len(batch)

      logger.info(
        f"[VectorStore]: Deleted {total_deleted} vectors from vectors.{table_name}")
      return True
    except Exception as e:
      logger.exception(f"[VectorStore]: Failed to delete vectors: {e}")
      return False

  def delete_by_doc_id(self, doc_id: str, model_name: Optional[str] = None) -> bool:
    """
    Delete all vectors for a document.
    With CASCADE from graph_chunks, this is handled automatically when
    graph_chunks rows are deleted. Kept for backward compatibility.
    """
    logger.info(
      f"[VectorStore]: delete_by_doc_id called for {doc_id} - CASCADE handles this automatically")
    return True
