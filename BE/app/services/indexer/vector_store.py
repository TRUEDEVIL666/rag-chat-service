import re
from typing import List, Optional
import asyncio
import json

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import TextNode, BaseNode
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
  # Strip provider prefix if present (e.g. "ollama/gemma" -> "gemma")
  if "/" in name:
    name = name.split("/")[-1]
  # Replace slashes, colons, dots, spaces with underscores
  sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
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
      host: str,
      port: int,
      collection: str,
      embedding_service: Optional[EmbeddingService] = None,
      vector_size: int = 768
  ):
    self.host = settings.QDRANT_HOST
    self.port = settings.QDRANT_PORT
    self.embedding_service = embedding_service
    self.vector_size = vector_size
    self._rerankers = {}  # Cache for reranker models: {model_name: CrossEncoder}

    # Dynamic Collection Name Logic
    # 1. Start with the model name from embedding service
    model_name_raw = self.embedding_service.model_name if self.embedding_service else None

    if model_name_raw:
      # 2. Sanitize it
      model_name_safe = sanitize_collection_name(model_name_raw)
      # 3. Formulate collection name (e.g., "vec_ollama_gemma3_4b")
      self.qdrant_collection = f"vec_{model_name_safe}"
    else:
      self.qdrant_collection = collection

    logger.info(
      f"[VectorRepo] Using dynamic collection name: {self.qdrant_collection}")

    # Settings.embed_model = CustomEmbedding(
    #   self.embedding_service, embed_batch_size=64
    # )
    # Avoid modifying global settings to prevent concurrency issues

    # Initialize Sparse Embedding Model (BM25 / SPLADE)
    # This runs locally on CPU
    self.sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    self.qdrant_client = QdrantClient(
        host=self.host,
        port=self.port
    )

    # Ensure collection exists ONLY if we have a concrete model
    if model_name_raw:
      self.create_collection(self.qdrant_collection)
    else:
      logger.info(
        "[VectorRepo] Lazy initialization: Skipping eager collection creation (using default name waiting for runtime override).")

    self.vector_store = QdrantVectorStore(
        client=self.qdrant_client,
        collection_name=self.qdrant_collection
    )
    self.storage_context = StorageContext.from_defaults(
      vector_store=self.vector_store)
    self.index: Optional[VectorStoreIndex] = None

  def _get_reranker(self, model_name: str = None):
    target_model = model_name or settings.RERANKER_MODEL
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if target_model not in self._rerankers:
      logger.info(
        f"[VectorRepo] Initializing CrossEncoder reranker: {target_model} on device: {device}")
      self._rerankers[target_model] = CrossEncoder(target_model, device=device)
    return self._rerankers[target_model]

  def create_collection(self, collection_name: Optional[str] = None, vector_size: Optional[int] = None):
    target_collection = collection_name or "test_documents"
    if not self.qdrant_client.collection_exists(target_collection):
      logger.info(
        f"[VectorRepo] Creating Qdrant collection '{target_collection}'")
      self.qdrant_client.create_collection(
          collection_name=target_collection,
          vectors_config=VectorParams(
              size=vector_size or self.vector_size,
              distance=Distance.COSINE,
              quantization_config=models.ScalarQuantization(
                  scalar=models.ScalarQuantizationConfig(
                      type=models.ScalarType.INT8,
                      always_ram=True
                  )
              )
          ),
          sparse_vectors_config={
              "bm25": SparseVectorParams(
                  index=SparseIndexParams(
                      on_disk=False,
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

  def upsert_documents(self, documents: List[Document], embed_model: Optional[BaseEmbedding] = None, use_sparse: bool = False):
    if embed_model:
      # CRITICAL: Isolate keys by Collection/Model
      # 1. Determine collection name from model
      model_name_raw = embed_model.model_name
      model_name_safe = sanitize_collection_name(model_name_raw)
      target_collection = f"vec_{model_name_safe}"

      logger.info(
        f"[VectorRepo] Upserting into dynamic collection: {target_collection}")

      # 1. Prepare Nodes (Convert Documents if needed)
      nodes = []
      for doc in documents:
        # If the input is already a Node, use it. If it's a Document, convert to TextNode keeping the ID.
        if isinstance(doc, (TextNode, BaseNode)):
          nodes.append(doc)
        else:
          nodes.append(
            TextNode(text=doc.text, metadata=doc.metadata, id_=doc.doc_id))

      # 2. Generate Dense Embeddings
      embeddings = embed_model.get_text_embedding_batch(
        [n.text for n in nodes])

      if not embeddings:
        logger.warning(
          "[VectorRepo] No embeddings generated. Skipping upsert.")
        return

      # 3. Create Collection with CORRECT Dimension
      current_dim = len(embeddings[0])
      self.create_collection(target_collection, vector_size=current_dim)

      points = []
      for node, emb in zip(nodes, embeddings):
        # 1. Get Node Dictionary
        node_dict = node.dict()

        # 2. STRIP METADATA from internal dict to save storage
        # The metadata is already stored as top-level fields in 'payload'
        node_dict["metadata"] = {}

        # 3. Construct Payload
        # Filter metadata to remove redundant/internal keys
        excluded_keys = {
            "chunk_size", "source", "source_file", "node_id"
        }
        filtered_metadata = {
          k: v for k, v in node.metadata.items() if k not in excluded_keys}

        payload = {
            # Minimized content (Text + Relationships + Empty Metadata)
            "_node_content": json.dumps(node_dict),
            "_node_type": node.class_name(),
            "document_id": node.metadata.get("document_id"),
            **filtered_metadata
        }

        points.append(models.PointStruct(
          id=node.node_id, vector=emb, payload=payload))

      # 5. Upsert Dense Points
      try:
        self.qdrant_client.upsert(
            collection_name=target_collection,
            points=points
        )
      except Exception as e:
        logger.error(
          f"[VectorRepo] Qdrant upsert failed. Collection: {target_collection}")
        if hasattr(e, "body"):
          logger.error(f"[VectorRepo] Qdrant Error Body: {e.body}")
        if hasattr(e, "reason"):
          logger.error(f"[VectorRepo] Qdrant Error Reason: {e.reason}")
        raise e

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
            storage_context=self.storage_context,
            embed_model=CustomEmbedding(
              self.embedding_service, embed_batch_size=64)
        )
    else:
      document_nodes = [
          TextNode(text=doc.text, metadata=doc.metadata)
          for doc in documents
      ]
      self.index.insert_nodes(
        document_nodes,
        embed_model=CustomEmbedding(
          self.embedding_service, embed_batch_size=64)
      )

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

  async def embed_text(self, text: str, model_name: Optional[str] = None) -> List[float]:
    if not text.strip():
      return []

    # Resolve correct embedding service
    target_service = self.embedding_service

    # If explicit model requested, or if we have no default service
    if model_name:
      if not self.embedding_service or model_name != self.embedding_service.model_name:
        from app.core.factory import get_embedding_service
        target_service = get_embedding_service(model=model_name)
    elif not target_service:
        # No model provided AND no default service
      raise ValueError(
        "No embedding model specified and no default service available.")

    embeddings = await target_service.embed_texts([text])
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
    # CRITICAL: Pass model_name to ensure we generate vector using the Correct Model!
    dense_vector = await self.embed_text(query, model_name=model_name)

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
      points_result = await asyncio.to_thread(
          self.qdrant_client.query_points,
          collection_name=target_collection,
          query=dense_vector,
          query_filter=qdrant_filters,
          limit=k,
          with_payload=True
      )
      results = points_result.points

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

      points_result = await asyncio.to_thread(
          self.qdrant_client.query_points,
          collection_name=target_collection,
          prefetch=prefetch,
          query=models.FusionQuery(fusion=models.Fusion.RRF),
          with_payload=True,
          limit=k,
      )
      results = points_result.points

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
        parent_points = await asyncio.to_thread(
            self.qdrant_client.retrieve,
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

  def delete_points_by_ids(self, point_ids: List[str], model_name: Optional[str] = None) -> bool:
    """
    Batch delete specific points from Qdrant.
    """
    if not point_ids:
      return True
    try:
      # Resolve correct collection
      target_collection = self.qdrant_collection
      if model_name:
        safe_name = sanitize_collection_name(model_name)
        # FORCE usage of derived name. Do not fallback.
        target_collection = f"vec_{safe_name}"

      # Batch delete to avoid payload limits
      batch_size = 500
      total_deleted = 0
      for i in range(0, len(point_ids), batch_size):
        batch = point_ids[i:i + batch_size]
        self.qdrant_client.delete(
            collection_name=target_collection,
            points_selector=models.PointIdsList(
                points=batch,
            )
        )
        total_deleted += len(batch)

      logger.info(
        f"[VectorRepo] Deleted {total_deleted} points from {target_collection}")
      return True
    except Exception as e:
      logger.exception(f"[VectorRepo] Failed to delete points: {e}")
      return False

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
        target_collection = f"vec_{safe_name}"

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
      logger.exception(f"[VectorRepo] Failed to delete for kb_id {kb_id}: {e}")
      return False

  def delete_by_doc_id(self, doc_id: str, model_name: Optional[str] = None) -> bool:
    """
    Delete all points for a specific document ID.
    """
    try:
      if not isinstance(doc_id, str):
        logger.error(f"[VectorRepo] doc_id must be string, got {type(doc_id)}")
        return False

      logger.info(
          f"[VectorRepo] Deleting vectors for doc_id: {doc_id} (model: {model_name})")

      target_collection = self.qdrant_collection
      if model_name:
        safe_name = sanitize_collection_name(model_name)
        target_collection = f"vec_{safe_name}"

      self.qdrant_client.delete(
          collection_name=target_collection,
          points_selector=models.FilterSelector(
              filter=models.Filter(
                  must=[
                      models.FieldCondition(
                          key="document_id",
                          match=models.MatchValue(value=doc_id)
                      )
                  ]
              )
          )
      )
      logger.info(
          f"[VectorRepo] Successfully deleted vectors for doc_id: {doc_id}")
      return True
    except Exception as e:
      logger.exception(
          f"[VectorRepo] Failed to delete vectors for doc_id {doc_id}: {e}")
      return False
