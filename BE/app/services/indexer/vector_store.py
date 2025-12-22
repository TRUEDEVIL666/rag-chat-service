import re
from typing import List, Optional

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import FilterOperator, MetadataFilter, MetadataFilters
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, PayloadSchemaType, VectorParams, SparseVectorParams, SparseIndexParams
from sentence_transformers import CrossEncoder
from fastembed import SparseTextEmbedding

from app.config.config import settings
from app.core.logger import get_logger
from app.services.indexer.embedding_service import CustomEmbedding, EmbeddingService

logger = get_logger("vector_repository")


# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def to_qdrant_payload(node: TextNode) -> dict:
  return {
      "_node_content": node.to_dict(),
      **node.metadata,
  }


def sanitize_collection_name(name: str) -> str:
  """
  Sanitize text to be a valid Qdrant collection name.
  Replaces non-alphanumeric characters with underscores.
  """
  # Replace slashes, colons, dots, spaces with underscores
  sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name)
  # Ensure it doesn't start with numbers or special chars if Qdrant requires (optional but safer)
  if sanitized and sanitized[0].isdigit():
    sanitized = "vec_" + sanitized
  return sanitized


# ----------------------------------------------------------------------
# VECTOR REPOSITORY
# ----------------------------------------------------------------------
class VectorRepository:
  """
  Handles document indexing and semantic search using Qdrant + LlamaIndex.
  """

  def __init__(
      self,
      embedding_service: EmbeddingService,
      host: str,
      port: int,
      collection: str,
      vector_size: int = 768
  ):
    self.host = settings.QDRANT_HOST
    self.port = settings.QDRANT_PORT
    self.embedding_service = embedding_service
    self.vector_size = vector_size
    self._rerankers = {}  # Cache for reranker models: {model_name: CrossEncoder}

    # Dynamic Collection Name Logic
    # 1. Start with the model name from embedding service
    model_name_raw = self.embedding_service.model_name
    # 2. Sanitize it
    model_name_safe = sanitize_collection_name(model_name_raw)
    # 3. Formulate collection name (e.g., "vec_ollama_gemma3_4b")
    self.qdrant_collection = f"vec_{model_name_safe}"

    logger.info(
      f"[VectorRepo] Using dynamic collection name: {self.qdrant_collection}")

    Settings.embed_model = CustomEmbedding(
      self.embedding_service, embed_batch_size=64
    )

    # Initialize Sparse Embedding Model (BM25 / SPLADE)
    # This runs locally on CPU
    self.sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    self.qdrant_client = QdrantClient(
        host=self.host,
        port=self.port
    )

    # Ensure collection exists
    self.create_collection(self.qdrant_collection)

    self.vector_store = QdrantVectorStore(
        client=self.qdrant_client,
        collection_name=self.qdrant_collection
    )
    self.storage_context = StorageContext.from_defaults(
      vector_store=self.vector_store)
    self.index: Optional[VectorStoreIndex] = None

  def _resolve_index(self, model_name: Optional[str] = None) -> VectorStoreIndex:
    """
    Get or create a VectorStoreIndex for the specified model.
    If model_name is None, uses the default self.index.
    """
    if not model_name:
      if self.index is None:
        self.index = VectorStoreIndex.from_vector_store(self.vector_store)
      return self.index

    # Dynamic resolution for specific model
    raw_name = model_name
    if "/" in model_name:
      _, raw_name = model_name.split("/", 1)

    safe_name = sanitize_collection_name(raw_name)
    collection_name = f"vec_{safe_name}"

    # Check if we are requesting the default collection
    if collection_name == self.qdrant_collection:
      if self.index is None:
        self.index = VectorStoreIndex.from_vector_store(self.vector_store)
      return self.index

    # Safe Approach: Always create a temporary lightweight Index/Context for the request
    logger.info(
      f"[VectorRepo] Resolving index for model: {model_name} -> {collection_name}")

    # 1. Create Vector Store pointing to collection
    temp_store = QdrantVectorStore(
        client=self.qdrant_client,
        collection_name=collection_name
    )

    # 2. Resolve Embedding Service
    # Expected model_name format: "provider/model" or just "model" (defaulting to ollama?)
    # We need to construct the embedding service.
    provider = "ollama"  # Default assumption
    model_str = model_name
    if "/" in model_name:
      provider, model_str = model_name.split("/", 1)

    # Use Factory to get service (it might be cached or new)
    from app.core.factory import get_embedding_service
    embed_service = get_embedding_service(provider, model_str)
    custom_embed_runner = CustomEmbedding(
        embed_service, embed_batch_size=64
    )

    # 3. Create Index
    # We pass the embed_model explicitly to ensure the query is embedded correctly
    return VectorStoreIndex.from_vector_store(
        vector_store=temp_store,
        embed_model=custom_embed_runner
    )

  def _get_reranker(self, model_name: str = None):
    target_model = model_name or settings.RERANKER_MODEL
    if target_model not in self._rerankers:
      logger.info(
        f"[VectorRepo] Initializing CrossEncoder reranker: {target_model}")
      self._rerankers[target_model] = CrossEncoder(target_model)
    return self._rerankers[target_model]

  def create_collection(self, collection_name: Optional[str] = None):
    target_collection = collection_name or "test_documents"
    if not self.qdrant_client.collection_exists(target_collection):
      logger.info(
        f"[VectorRepo] Creating Qdrant collection '{target_collection}'")
      self.qdrant_client.create_collection(
          collection_name=target_collection,
          vectors_config=VectorParams(
              size=self.vector_size,
              distance=Distance.COSINE
          ),
          sparse_vectors_config={
              "bm25": SparseVectorParams(
                  index=SparseIndexParams(
                      on_disk=True,
                  )
              )
          }
      )
      logger.info(
        f"[VectorRepo] Collection '{target_collection}' created successfully.")
    else:
      logger.info(
        f"[VectorRepo] Collection '{target_collection}' already exists.")

    # Ensure indices exist (safe to run repeatedly)
    self.create_payload_index(target_collection)

  def create_payload_index(self, collection_name: str = "test_documents"):
    for field in ["kb_id", "parent_id", "tenant_id"]:
      try:
        self.qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD
        )
      except Exception as e:
        if "already exists" in str(e):
          logger.info(
            f"[VectorRepo] Payload index for '{field}' already exists in {collection_name}")
        else:
          logger.error(
            f"[VectorRepo] Failed to create payload index for '{field}' in {collection_name}: {e}")

  def upsert_documents(self, documents: List[Document], embed_model: Optional[BaseEmbedding] = None, use_sparse: bool = True):
    if embed_model:
      # CRITICAL: Isolate keys by Collection/Model
      # 1. Determine collection name from model
      model_name_raw = embed_model.model_name
      model_name_safe = sanitize_collection_name(model_name_raw)
      target_collection = f"vec_{model_name_safe}"

      logger.info(
        f"[VectorRepo] Upserting into dynamic collection: {target_collection}")

      # 2. Ensure collection exists
      self.create_collection(target_collection)

      # 3. Create TEMPORARY Storage Context for this specific collection
      # We cannot reuse self.storage_context as it's bound to the default collection
      tmp_client = QdrantClient(host=self.host, port=self.port)
      tmp_vector_store = QdrantVectorStore(
          client=tmp_client,
          collection_name=target_collection
      )
      tmp_storage_context = StorageContext.from_defaults(
        vector_store=tmp_vector_store)

      # 4. Upsert using this ISOLATED context
      # Note: from_documents creates nodes internally.
      # To ensure we capture node IDs for sparse updates, we prefer explicit node creation.
      nodes = [TextNode(text=doc.text, metadata=doc.metadata)
               for doc in documents]

      VectorStoreIndex(
          nodes=nodes,
          storage_context=tmp_storage_context,
          embed_model=embed_model
      )

      # 5. Manual Sparse Vector Update for Custom Collection (CONDITIONAL)
      if use_sparse:
        # Generate Sparse Embeddings (BM25)
        texts = [n.text for n in nodes]
        sparse_gen = self.sparse_embedding_model.embed(texts)

        for i, sparse_vec in enumerate(sparse_gen):
          node = nodes[i]
          qdrant_sparse = models.SparseVector(
              indices=sparse_vec.indices.tolist(),
              values=sparse_vec.values.tolist()
          )

          self.qdrant_client.update_vectors(
              collection_name=target_collection,
              points=[
                  models.PointVectors(
                      id=node.node_id,
                      vector={"bm25": qdrant_sparse}
                  )
              ]
          )
        logger.info(
            f"[VectorRepo] Enriched {len(documents)} documents with BM25 sparse vectors in {target_collection}.")
      else:
        logger.info(
          f"[VectorRepo] Skipped sparse vector generation for {target_collection} (use_sparse=False)")

      return

    if self.index is None:
      self.index = VectorStoreIndex.from_documents(
          documents=documents,
          storage_context=self.storage_context
      )
    else:
      document_nodes = [
          TextNode(text=doc.text, metadata=doc.metadata)
          for doc in documents
      ]
      self.index.insert_nodes(document_nodes)

      # --- HYBRID UPDATE: UPSERT SPARSE VECTORS ---
      # LlamaIndex's insert_nodes doesn't easily support named sparse vectors yet in this version without complex config.
      # So we will MANUALLY update the points with their sparse vectors immediately after insertion.
      # This is a robust "Patch" approach.

      # 1. Get the texts
      texts = [doc.text for doc in documents]

      # 2. Generate Sparse Vectors (Generator)
      sparse_vectors_gen = self.sparse_embedding_model.embed(texts)

      # 3. Create Update Operations
      # We need the IDs that LlamaIndex assigned.
      # Fortunately, the 'document_nodes' we created above have the IDs.
      points = []
      for i, sparse_vec in enumerate(sparse_vectors_gen):
        node = document_nodes[i]
        # Convert FastEmbed sparse format to Qdrant format
        qdrant_sparse = models.SparseVector(
            indices=sparse_vec.indices.tolist(),
        )

        # We prefer to use the PointStruct update or just Update Vectors
        # But since we just inserted, we can just "Update Vectors"
        self.qdrant_client.update_vectors(
            collection_name=self.qdrant_collection,
            points=[
                models.PointVectors(
                    id=node.node_id,
                    vector={
                        "bm25": qdrant_sparse
                    }
                )
            ]
        )
      logger.info(
          f"[VectorRepo] Enriched {len(documents)} documents with BM25 sparse vectors.")

  async def embed_text(self, text: str) -> List[float]:
    if not text.strip():
      return []
    embeddings = await self.embedding_service.embed_texts([text])
    return embeddings[0] if embeddings else []

  async def search(
      self,
      query: str,
      k: int = 5,
      kb_id: Optional[str] = None,
      score_threshold: float = 0.0,
      model_name: Optional[str] = None,
      search_method: str = "semantic",
      enable_auto_merging: bool = False
  ) -> List[dict]:
    # 1. Resolve Target Collection
    # Default = global collection
    target_collection = self.qdrant_collection

    if model_name:
      # If model specified, dynamic resolution
      raw_name = model_name
      safe_name = sanitize_collection_name(raw_name)
      possible_collection = f"vec_{safe_name}"

      if self.qdrant_client.collection_exists(possible_collection):
        target_collection = possible_collection
        logger.info(f"[VectorRepo] Search redirect -> {target_collection}")
      else:
        logger.warning(
          f"[VectorRepo] Requested model collection '{possible_collection}' not found. Fallback to default.")

    # 2. Generate Query Vectors AND Perform Search
    # Logic branches based on search_method

    # Dense (Embedding Model) - Required for both
    dense_vector = await self.embed_text(query)

    # Build Filter
    qdrant_filters = None
    if kb_id:
      qdrant_filters = models.Filter(
          must=[
              models.FieldCondition(
                  key="kb_id",
                  match=models.MatchValue(value=kb_id)
              )
          ]
      )

    results = []

    if search_method == "semantic":
      # --- SEMANTIC SEARCH ONLY ---
      logger.info("[VectorRepo] Executing Semantic Search (Dense Only)")
      results = self.qdrant_client.query_points(
          collection_name=target_collection,
          query=dense_vector,
          query_filter=qdrant_filters,
          limit=k,
          with_payload=True
      ).points

    else:
      # --- HYBRID SEARCH (DEFAULT) ---
      logger.info("[VectorRepo] Executing Hybrid Search (RRF)")

      # Sparse (BM25) - Only needed for Hybrid
      sparse_gen = list(self.sparse_embedding_model.embed([query]))
      sparse_vec = sparse_gen[0] if sparse_gen else None

      qdrant_sparse_query = models.SparseVector(
          indices=sparse_vec.indices.tolist(),
          values=sparse_vec.values.tolist()
      )

      prefetch = [
          models.Prefetch(
              query=dense_vector,
              filter=qdrant_filters,
              limit=k,
          ),
          models.Prefetch(
              query=qdrant_sparse_query,
              using="bm25",
              filter=qdrant_filters,
              limit=k,
          ),
      ]

      results = self.qdrant_client.query_points(
          collection_name=target_collection,
          prefetch=prefetch,
          query=models.FusionQuery(fusion=models.Fusion.RRF),
          with_payload=True,
          limit=k,
      ).points

    # 5. Format Results
    formatted_results = []

    # Auto-Merging: Collect Parent IDs to fetch
    parent_ids_to_fetch = set()
    if enable_auto_merging:
      for point in results:
        payload = point.payload or {}
        if "parent_id" in payload:
          parent_ids_to_fetch.add(payload["parent_id"])

    # Fetch Parents if any
    parent_map = {}
    if parent_ids_to_fetch:
      try:
        parent_points = self.qdrant_client.retrieve(
            collection_name=target_collection,
            ids=list(parent_ids_to_fetch),
            with_payload=True
        )
        for pp in parent_points:
          pp_payload = pp.payload or {}
          pp_node = pp_payload.get("_node_content", {})
          pp_text = pp_node.get("text", "") if isinstance(
              pp_node, dict) else str(pp_node)
          parent_map[pp.id] = pp_text
      except Exception as e:
        logger.error(f"[VectorRepo] Failed to fetch parent nodes: {e}")

    for point in results:
      payload = point.payload or {}
      node_content = payload.get("_node_content", {})
      text = node_content.get("text", "") if isinstance(
        node_content, dict) else str(node_content)

      # --- Metadata Replacement (Sliding Window) ---
      if "window" in payload:
        text = payload["window"]

      # --- Auto-Merging (Hierarchical) ---
      if "parent_id" in payload:
        pid = payload["parent_id"]
        # If we successfully fetched the parent text, use it
        if pid in parent_map:
          text = parent_map[pid]
          # Optional: You might want to indicate this was swapped
          payload["_is_parent_context"] = True

      metadata = payload
      if "_node_content" in metadata:
        metadata = {k: v for k, v in metadata.items() if k != "_node_content"}

      formatted_results.append({
          "id": point.id,
          "text": text,
          "metadata": metadata,
          "score": point.score
      })

    return formatted_results

  def rerank_results(
      self,
      results: List[dict],
      query: str,
      top_k: int,
      model_name: str
  ) -> List[dict]:
    if not results:
      return []

    try:
      reranker = self._get_reranker(model_name)
      # Prepare pairs for CrossEncoder: (query, document_text)
      pairs = [[query, r["text"]] for r in results]
      scores = reranker.predict(pairs)

      # Update scores
      for i, r in enumerate(results):
        r["score"] = float(scores[i])

      # Re-sort by new score
      results.sort(key=lambda x: x["score"], reverse=True)

      # Take top k
      return results[:top_k]

    except Exception as e:
      logger.error(f"[VectorRepo] Reranking failed: {e}")
      # Fallback to original results if reranking fails
      return results[:top_k]

  def build_kb_filter(self, kb_id: Optional[str]) -> MetadataFilters:
    filters = []
    if kb_id:
      filters.append(MetadataFilter(
          key="kb_id",
          value=kb_id,
          operator=FilterOperator.EQ
      ))
    return MetadataFilters(filters=filters)

  def delete_by_kb(self, kb_id: str, model_name: Optional[str] = None) -> bool:
    """
    Delete all points associated with a specific Knowledge Base ID.
    Using Qdrant's delete API with a filter.
    """
    try:
      if not isinstance(kb_id, str):
        logger.error(f"[VectorRepo] kb_id must be string, got {type(kb_id)}")
        return False

      logger.info(
        f"[VectorRepo] Deleting vectors for kb_id: {kb_id} (model: {model_name})")

      # Resolve correct collection
      target_collection = self.qdrant_collection
      if model_name:
        safe_name = sanitize_collection_name(model_name)
        possible_collection = f"vec_{safe_name}"
        if self.qdrant_client.collection_exists(possible_collection):
          target_collection = possible_collection

      # Use qdrant_client specific delete method with Qdrant Filter
      self.qdrant_client.delete(
          collection_name=target_collection,
          points_selector=models.FilterSelector(
              filter=models.Filter(
                  must=[
                      models.FieldCondition(
                          key="kb_id",
                          match=models.MatchValue(value=kb_id)
                      )
                  ]
              )
          )
      )
      logger.info(
        f"[VectorRepo] Successfully deleted vectors for kb_id: {kb_id}")
      return True
    except Exception as e:
      logger.exception(
        f"[VectorRepo] Failed to delete vectors for kb_id {kb_id}: {e}")
      return False
