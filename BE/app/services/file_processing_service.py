from typing import Any, Dict, List, Optional

import pymupdf4llm
from llama_index.core import Document
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import BaseNode, NodeRelationship
from llama_index.readers.file import (
  CSVReader,
  DocxReader,
  HTMLTagReader,
  ImageReader,
  MarkdownReader,
  PptxReader,
)
from llama_index.readers.json import JSONReader

from app.core.enums.file import FileExtension
from app.core.logger import get_logger
from app.helper.chunker import process_chunks
from app.helper.document_extractor import extract_documents
from app.services.minio_storage_service import MinioStorageService
from app.repositories import (
  DocumentRepository,
  GraphChunkRepository,
  GraphEdgeRepository,
  GraphEntityRepository,
  KnowledgeBaseRepository,
)

logger = get_logger(__name__)


class PyMuPDFReader:
  """
  Custom reader using pymupdf4llm for high-quality Markdown extraction.
  Mimics the interface of LlamaIndex readers.
  """

  def load_data(self, file, extra_info=None):
    # file is a Path object or string passed from extract_documents
    md_text = pymupdf4llm.to_markdown(str(file))
    return [Document(text=md_text, metadata=extra_info or {})]


class FileProcessor:
  _instance = None

  @classmethod
  def get_instance(cls) -> "FileProcessor":
    if cls._instance is None:
      from app.repositories import (
        DocumentRepository,
        GraphChunkRepository,
        GraphEdgeRepository,
        GraphEntityRepository,
        KnowledgeBaseRepository,
      )
      from .minio_storage_service import MinioStorageService

      cls._instance = cls(
        meta_data_store=GraphChunkRepository.get_instance(),
        original_file_store=MinioStorageService.get_instance(),
        document_repository=DocumentRepository.get_instance(),
        kb_repository=KnowledgeBaseRepository.get_instance(),
        graph_edge_repository=GraphEdgeRepository.get_instance(),
        graph_entity_repository=GraphEntityRepository.get_instance(),
      )
    return cls._instance

  def __init__(
    self,
    meta_data_store: GraphChunkRepository,
    original_file_store: MinioStorageService,
    document_repository: DocumentRepository,
    kb_repository: KnowledgeBaseRepository,
    graph_edge_repository: GraphEdgeRepository = None,
    graph_entity_repository: GraphEntityRepository = None,
  ):
    self.graph_chunk_store = meta_data_store
    self.original_file_store = original_file_store
    self.document_repository = document_repository
    self.kb_repository = kb_repository
    self.graph_edge_store = graph_edge_repository
    self.graph_entity_store = graph_entity_repository

    # Readers will be initialized lazily
    self._readers = {}

    # Initialize argument map for LlamaIndex readers
    self.arg_map = {
      FileExtension.DOCX: "file",
      FileExtension.PPTX: "file",
      FileExtension.PDF: "file",
      FileExtension.MD: "file",
      FileExtension.HTML: "file",
      FileExtension.JPG: "file",
      FileExtension.JPEG: "file",
      FileExtension.PNG: "file",
      FileExtension.BMP: "file",
      FileExtension.TIFF: "file",
    }

  def _get_reader(self, ext: FileExtension):
    if ext in self._readers:
      return self._readers[ext]

    reader = None
    if ext == FileExtension.DOCX:
      reader = DocxReader()
    elif ext == FileExtension.CSV:
      reader = CSVReader()
    elif ext == FileExtension.JSON:
      reader = JSONReader()
    elif ext == FileExtension.PDF:
      reader = PyMuPDFReader()
    elif ext == FileExtension.PPTX:
      reader = PptxReader()
    elif ext == FileExtension.MD:
      reader = MarkdownReader()
    elif ext == FileExtension.HTML:
      reader = HTMLTagReader()
    elif ext in [
      FileExtension.JPG,
      FileExtension.JPEG,
      FileExtension.PNG,
      FileExtension.BMP,
      FileExtension.TIFF,
    ]:
      reader = ImageReader()

    if reader:
      self._readers[ext] = reader

    return reader

  def _run_async(self, coro):
    """Helper to run async coroutines in a synchronous context."""
    import asyncio

    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

    if loop.is_running():
      import nest_asyncio

      nest_asyncio.apply(loop)
      return loop.run_until_complete(coro)
    else:
      return loop.run_until_complete(coro)

  async def _get_embedding_model(
    self, kb_id: str, tenant_id: str, access_token: Optional[str]
  ) -> Optional[BaseEmbedding]:
    """Resolves the correct embedding model for the Knowledge Base."""
    kb_data = await self.kb_repository.get_one(kb_id, tenant_id, access_token)
    if kb_data and kb_data.get("embedding_provider") and kb_data.get("embedding_model"):
      try:
        provider_data = kb_data["embedding_provider"]
        model_data = kb_data["embedding_model"]

        # Handle list vs dict (Supabase join quirks)
        provider = (
          provider_data[0]["name"]
          if isinstance(provider_data, list) and provider_data
          else provider_data.get("name")
        )
        model = (
          model_data[0]["model_id"]
          if isinstance(model_data, list) and model_data
          else model_data.get("model_id")
        )

        if not provider or not model:
          # No provider found -> default
          from app.core.factory import get_embedding_model

          return await get_embedding_model()

        from app.core.factory import get_embedding_model

        return await get_embedding_model(provider=provider, model=model)
      except Exception as e:
        logger.exception(f"[_get_embedding_model] Failed to parse provider/model: {e}")
        return None
    return None

  def process_file(
    self,
    file_path: str,
    file_name: str,
    kb_id: str,
    tenant_id: str,
    created_by: str,
    document_id: str,
    access_token: str = None,
    chunking_method: str = "sentence",
    enable_extraction: bool = True,
    **kwargs,
  ) -> Dict[str, Any]:
    # Create initial document record
    # Update status to learning (Document created synchronously in DocumentService)
    self._run_async(
      self.document_repository.update_document_status(
        document_id, "learning", access_token
      )
    )

    stream_response = None
    try:
      embed_model = self._run_async(
        self._get_embedding_model(kb_id, tenant_id, access_token)
      )

      logger.info(
        f"Starting bulk processing for {file_name} from MinIO key: {file_path}"
      )
      stream_response = self.original_file_store.get_file_stream(file_path)

      # 1. Read stream to bytes (Buffer in memory for extraction)
      file_bytes = stream_response.read()

      # 2. Extract ALL documents
      import os

      ext = os.path.splitext(file_name)[1].lower()
      reader = self._get_reader(ext)
      reader_map = {ext: reader} if reader else {}

      doc_iterator = extract_documents(
        file_bytes=file_bytes,
        filename=file_name,
        reader_map=reader_map,
        arg_map=self.arg_map,
      )
      documents = list(doc_iterator)
      logger.info(f"Extracted {len(documents)} raw documents for {file_name}")

      if not documents:
        logger.warning(f"No content extracted for {file_name}")
        self._run_async(
          self.document_repository.update_document_status(
            document_id, "learned", access_token
          )
        )
        return {
          "status": "success",
          "chunks_inserted": 0,
          "document_id": document_id,
        }

      # 2. Chunk ALL documents (Bulk)
      chunks = process_chunks(
        documents=documents,
        chunking_method=chunking_method,
        filename=file_name,
        embed_model=embed_model,
        **kwargs,
      )

      # Entity Extraction
      # TODO: We currently run this on the first few pages to avoid excessive LLM costs
      # This can be made configurable via kwargs later
      extracted_edges = []
      extracted_entities = []
      extracted_mentions = []
      try:
        if enable_extraction:
          extracted_entities, extracted_mentions, extracted_edges = (
            self._extract_and_create_entity_nodes(
              chunks, file_name, kb_id, tenant_id, access_token
            )
          )
          if extracted_entities:
            logger.info(
              f"Extracted {len(extracted_entities)} entities, {len(extracted_mentions)} mentions, and {len(extracted_edges)} edges for {file_name}"
            )
      except Exception as e:
        logger.warning(f"Entity extraction skipped/failed: {e}")

      if not chunks:
        logger.warning(f"No chunks generated for {file_name}")
        self._run_async(
          self.document_repository.update_document_status(
            document_id, "learned", access_token
          )
        )
        return {
          "status": "success",
          "chunks_inserted": 0,
          "document_id": document_id,
        }

      # 4. Wrap Chunks
      wrapped_chunks = self._wrap_chunks(
        chunks, document_id, file_path, kb_id, tenant_id
      )

      # 5. Upsert Metadata & Vectors (Bulk)
      self._run_async(self.graph_chunk_store.store(wrapped_chunks, access_token))
      self._upsert_vectors(wrapped_chunks, embed_model)

      # 5. Upsert Entities & Mentions
      if self.graph_entity_store and (extracted_entities or extracted_mentions):
        self._run_async(
          self.graph_entity_store.store(
            extracted_entities, extracted_mentions, access_token
          )
        )

      # 6. Upsert Edges
      if extracted_edges and self.graph_edge_store:
        self._run_async(self.graph_edge_store.store(extracted_edges, access_token))

      self._run_async(
        self.document_repository.update_document_status(
          document_id, "learned", access_token
        )
      )

      return {
        "status": "success",
        "chunks_inserted": len(wrapped_chunks),
        "document_id": document_id,
        "file_path": file_path,
      }
    except Exception as e:
      logger.exception(f"Failed to process file {file_name}: {e}")
      self._run_async(
        self.document_repository.update_document_status(
          document_id, "error", access_token
        )
      )
      raise e
    finally:
      if stream_response:
        stream_response.close()
        stream_response.release_conn()

  def process_file_update(
    self,
    document_id: str,
    file_path: str,
    file_name: str,
    kb_id: str,
    tenant_id: str,
    created_by: str,
    access_token: str = None,
    chunking_method: str = "sentence",
    enable_extraction: bool = True,
    **kwargs,
  ) -> Dict[str, Any]:
    """Bulk update: process full stream, then calc diff logic."""
    self._run_async(
      self.document_repository.update_document_status(
        document_id, "learning", access_token
      )
    )

    # sync_start_time = datetime.utcnow().isoformat() # REMOVED: using ID-based sync
    stream_response = None

    try:
      embed_model = self._run_async(
        self._get_embedding_model(kb_id, tenant_id, access_token)
      )

      logger.info(f"Starting bulk update for {file_name} from MinIO key: {file_path}")
      stream_response = self.original_file_store.get_file_stream(file_path)

      # 1. Read stream to bytes
      file_bytes = stream_response.read()

      # OPTIMIZATION: Do NOT delete all existing chunks upfront.
      # We will perform a differential update using hashes.
      existing_hashes_data = self._run_async(
        self.graph_chunk_store.get_hashes_by_document(document_id, access_token)
      )
      existing_hash_map = {
        item["chunk_hash"]: item["id"]
        for item in existing_hashes_data
        if item.get("chunk_hash")
      }

      # 2. Extract ALL
      import os

      ext = os.path.splitext(file_name)[1].lower()
      reader = self._get_reader(ext)
      reader_map = {ext: reader} if reader else {}

      doc_iterator = extract_documents(
        file_bytes=file_bytes,
        filename=file_name,
        reader_map=reader_map,
        arg_map=self.arg_map,
      )
      documents = list(doc_iterator)

      # 3. Chunk ALL
      chunks = process_chunks(
        documents=documents,
        chunking_method=chunking_method,
        filename=file_name,
        embed_model=embed_model,
        **kwargs,
      )

      # [NEW] Entity Extraction for Update
      extracted_edges = []
      extracted_entities = []
      extracted_mentions = []
      try:
        if enable_extraction:
          extracted_entities, extracted_mentions, extracted_edges = (
            self._extract_and_create_entity_nodes(
              chunks, file_name, kb_id, tenant_id, access_token
            )
          )
          if extracted_entities:
            logger.info(
              f"Extracted {len(extracted_entities)} entities, {len(extracted_mentions)} mentions, and {len(extracted_edges)} edges for {file_name} (Update)"
            )
      except Exception as e:
        logger.warning(f"Entity extraction skipped/failed during update: {e}")

      wrapped_chunks = []
      chunks_to_vectorize = []

      if chunks:
        # 4. Wrap & Diff
        # Identify which chunks are new vs existing
        for chunk in chunks:
          c_hash = chunk.metadata.get("chunk_hash")
          if c_hash and c_hash in existing_hash_map:
            # REUSE existing ID
            chunk.node_id = existing_hash_map[c_hash]
            # We do NOT add to chunks_to_vectorize (Skip Embedding)
          else:
            # New Chunk (Keep random ID)
            chunks_to_vectorize.append(chunk)

        # Wrap all chunks (to update metadata timestamp in Supabase)
        wrapped_chunks = self._wrap_chunks(
          chunks, document_id, file_path, kb_id, tenant_id
        )

        # Filter the wrapped chunks for vectorization to match chunks_to_vectorize IDs
        # (Since _wrap_chunks creates new Document objects, checking by ID is safest)
        vectorize_ids = set(c.node_id for c in chunks_to_vectorize)
        wrapped_chunks_to_vectorize = [
          wc for wc in wrapped_chunks if wc.node_id in vectorize_ids
        ]

        # 5. Upsert Metadata (ALL - guarantees timestamps are updated)
        self._run_async(self.graph_chunk_store.store(wrapped_chunks, access_token))

        # 6. Upsert Vectors (ONLY NEW)
        if wrapped_chunks_to_vectorize:
          logger.info(
            f"Vectorizing {len(wrapped_chunks_to_vectorize)} new/changed chunks."
          )
          self._upsert_vectors(wrapped_chunks_to_vectorize, embed_model)
        else:
          logger.info("No new chunks to vectorize.")

        # Upsert Entities & Mentions
        if self.graph_entity_store and (extracted_entities or extracted_mentions):
          self._run_async(
            self.graph_entity_store.store(
              extracted_entities, extracted_mentions, access_token
            )
          )

        # Upsert Edges
        if extracted_edges and self.graph_edge_store:
          self._run_async(self.graph_edge_store.store(extracted_edges, access_token))

      # 7. Sweep (Cleanup Stale)
      # This deletes anything in Supabase that wasn't included in 'wrapped_chunks' ( upserted above)
      # Robust fix using ID set difference
      active_ids = [c.node_id for c in wrapped_chunks]
      deleted_ids = self._run_async(
        self.graph_chunk_store.delete_stale_nodes(
          document_id=document_id,
          active_ids=active_ids,
          access_token=access_token,
        )
      )

      # 8. Sync Vector Deletion (CASCADE handles this automatically)
      # Deleting from graph_chunks cascades to vectors.* tables
      if deleted_ids:
        logger.info(
          f"Deleted {len(deleted_ids)} stale chunks (CASCADE auto-deleted vectors)"
        )

      self._run_async(
        self.document_repository.update_document_status(
          document_id, "learned", access_token
        )
      )

      return {
        "status": "success",
        "chunks_deleted": len(deleted_ids),
        "chunks_added": len(wrapped_chunks),  # Total active chunks
        "chunks_vectorized": len(chunks_to_vectorize),
        "document_id": document_id,
      }
    except Exception as e:
      logger.exception(f"Failed to update document {document_id}: {e}")
      self._run_async(
        self.document_repository.update_document_status(
          document_id, "error", access_token
        )
      )
      raise e
    finally:
      if stream_response:
        stream_response.close()
        stream_response.release_conn()

  def _wrap_chunks(
    self,
    chunks: List[BaseNode],
    document_id: str,
    file_path: str,
    kb_id: str,
    tenant_id: str,
  ) -> List[Document]:
    """Attach metadata to each chunk before embedding."""
    wrapped_chunks = []
    for _, chunk in enumerate(chunks):
      chunk_text = chunk.text
      node_id = chunk.node_id

      parent_id = None
      if chunk.relationships and NodeRelationship.PARENT in chunk.relationships:
        parent_info = chunk.relationships[NodeRelationship.PARENT]
        if parent_info:
          parent_id = parent_info.node_id

      metadata = {
        **chunk.metadata,
        "document_id": document_id,
        "file_path": file_path,
        "kb_id": kb_id,
        "tenant_id": tenant_id,
      }

      if parent_id:
        metadata["parent_id"] = parent_id

      doc = Document(
        text=chunk_text,
        metadata=metadata,
      )
      doc.id_ = node_id  # CRITICAL: Preserve the Node ID (Reused or New)
      wrapped_chunks.append(doc)

    return wrapped_chunks

  def _upsert_vectors(
    self, documents: List[Document], embed_model: BaseEmbedding = None
  ):
    """Upsert document vectors into Supabase vector store."""
    from app.repositories.vector_repository import vector_repo_instance

    vector_repo_instance.upsert_documents(documents, embed_model)

  def _extract_and_create_entity_nodes(
    self,
    chunks: List[BaseNode],
    file_name: str,
    kb_id: str,
    tenant_id: str,
    access_token: str = None,
  ) -> tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Extracts entities and relationships from the chunks using ExtractorService.
    Returns (entities, chunk_mentions, edges)
    """
    import uuid

    from app.services.extractor_service import extractor_service_instance

    entities = []
    chunk_mentions = []
    edges = []

    # Simple strategy: Join first few chunks (approx 5)
    subset_chunks = chunks[:5]
    full_text = "\n\n".join([c.text for c in subset_chunks])

    if not full_text.strip():
      return [], [], []

    try:
      extractions = extractor_service_instance.extract(full_text)

      # Pre-fetch existing entities from the database to prevent duplicates
      existing_entities_map = {}
      if self.graph_entity_store:
        # Extract all unique names the LLM found
        extracted_names = []
        for entity in extractions:
          if entity.extraction_class != "Relationship":
            extracted_names.append(entity.extraction_text)
          else:
            parts = [p.strip() for p in entity.extraction_text.split("||")]
            if len(parts) == 3:
              extracted_names.extend([parts[0], parts[2]])

        extracted_names = list(set(extracted_names))
        if extracted_names:
          # Run synchronous lookup since _extract_and_create_entity_nodes is currently sync,
          # but wait, we need to use _run_async since it's an async db call.
          existing_entities_map = self._run_async(
            self.graph_entity_store.check_existing_entities(
              names=extracted_names,
              kb_id=kb_id,
              access_token=access_token,
            )
          )

      # entity_map will store the mapping of lowercase name -> UUID for this entire run
      # Initialize it with the existing DB entities to reuse their UUIDs
      entity_map = {
        name.lower(): entity_id for name, entity_id in existing_entities_map.items()
      }

      # 1. Process Entities
      if extractions:
        for entity in extractions:
          name = entity.extraction_text
          etype = entity.extraction_class

          if etype == "Relationship":
            continue

          name_lower = name.lower()
          # Determine if we've already tracked this entity in this run
          if name_lower not in entity_map:
            entity_id = str(uuid.uuid4())
            entity_map[name_lower] = entity_id

            entity_record = {
              "id": entity_id,
              "name": name,
              "entity_type": etype,
              # "description": "" # Future: could aggregate descriptions
              "kb_id": kb_id,
              "tenant_id": tenant_id,
            }
            entities.append(entity_record)

          mention_record = {
            "chunk_id": subset_chunks[0].node_id if subset_chunks else None,
            "entity_id": entity_map[name_lower],
            "extraction_source": "llm",
          }
          if mention_record["chunk_id"]:
            chunk_mentions.append(mention_record)

        # 2. Process Relationships
        for entity in extractions:
          etype = entity.extraction_class

          if etype == "Relationship":
            rel_text = entity.extraction_text
            parts = [p.strip() for p in rel_text.split("||")]

            if len(parts) == 3:
              source, relation, target = parts
              source_lower = source.lower()
              target_lower = target.lower()

              # Auto-create missing source entity
              if source_lower not in entity_map:
                source_id = str(uuid.uuid4())
                entity_map[source_lower] = source_id
                entities.append(
                  {
                    "id": source_id,
                    "name": source,
                    "entity_type": "Concept",  # Default fallback type
                    "kb_id": kb_id,
                    "tenant_id": tenant_id,
                  }
                )

              # Auto-create missing target entity
              if target_lower not in entity_map:
                target_id = str(uuid.uuid4())
                entity_map[target_lower] = target_id
                entities.append(
                  {
                    "id": target_id,
                    "name": target,
                    "entity_type": "Concept",  # Default fallback type
                    "kb_id": kb_id,
                    "tenant_id": tenant_id,
                  }
                )

              source_id = entity_map[source_lower]
              target_id = entity_map[target_lower]

              edge = {
                "source_entity_id": source_id,
                "target_entity_id": target_id,
                "relationship_type": relation,
                "properties": {
                  "source_text": rel_text,
                  "extraction_source": "llm",
                },
              }
              edges.append(edge)

    except Exception as e:
      logger.error(f"Detailed extraction failed: {e}")

    # Remove duplicates from chunk mentions using a set logic
    unique_mentions = []
    seen = set()
    for m in chunk_mentions:
      key = (m["chunk_id"], m["entity_id"])
      if key not in seen:
        seen.add(key)
        unique_mentions.append(m)

    return entities, unique_mentions, edges
