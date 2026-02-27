import os
import pymupdf4llm
from typing import Any, Dict, List, Optional, Generator

from llama_index.core import Document
from llama_index.core.schema import BaseNode, NodeRelationship, TextNode
from llama_index.readers.file import (
    CSVReader, DocxReader, PDFReader, PptxReader,
    MarkdownReader, HTMLTagReader, ImageReader
)
from llama_index.readers.json import JSONReader

from app.core.enums.file import FileExtension
from app.core.logger import get_logger
from app.helper.chunker import process_chunks
from app.helper.document_extractor import extract_documents
from llama_index.core.base.embeddings.base import BaseEmbedding
from app.services.indexer.vector_store import VectorRepository
from app.services.minio.minio_storage import MinioStorage
from app.services.supabase.document_repository import DocumentRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.graph_chunk_repository import GraphChunkRepository
from app.services.supabase.graph_edge_repository import GraphEdgeRepository

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
  def __init__(
      self,
      meta_data_store: GraphChunkRepository,
      original_file_store: MinioStorage,
      document_repository: DocumentRepository,
      kb_repository: KnowledgeBaseRepository,
      graph_edge_repository: GraphEdgeRepository = None,
  ):
    self.graph_chunk_store = meta_data_store
    self.original_file_store = original_file_store
    self.document_repository = document_repository
    self.kb_repository = kb_repository
    self.graph_edge_store = graph_edge_repository

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
    elif ext in [FileExtension.JPG, FileExtension.JPEG, FileExtension.PNG, FileExtension.BMP, FileExtension.TIFF]:
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

  async def _get_embedding_model(self, kb_id: str, tenant_id: str, access_token: Optional[str]) -> Optional[BaseEmbedding]:
    """Resolves the correct embedding model for the Knowledge Base."""
    kb_data = await self.kb_repository.get_one(kb_id, tenant_id, access_token)
    if kb_data and kb_data.get("embedding_provider") and kb_data.get("embedding_model"):
      try:
        provider_data = kb_data["embedding_provider"]
        model_data = kb_data["embedding_model"]

        # Handle list vs dict (Supabase join quirks)
        provider = provider_data[0]["name"] if isinstance(
            provider_data, list) and provider_data else provider_data.get("name")
        model = model_data[0]["model_id"] if isinstance(
            model_data, list) and model_data else model_data.get("model_id")

        if not provider or not model:
          # No provider found -> default
          from app.core.factory import get_embedding_model
          return await get_embedding_model()

        from app.core.factory import get_embedding_model
        return await get_embedding_model(
            provider=provider,
            model=model
        )
      except Exception as e:
        logger.exception(
            f"[_get_embedding_model] Failed to parse provider/model: {e}")
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
      **kwargs
  ) -> Dict[str, Any]:
    # Create initial document record
    # Update status to learning (Document created synchronously in DocumentService)
    self._run_async(self.document_repository.update_document_status(
        document_id, "learning", access_token))

    stream_response = None
    try:
      embed_model = self._run_async(self._get_embedding_model(
          kb_id, tenant_id, access_token))

      logger.info(
          f"Starting bulk processing for {file_name} from MinIO key: {file_path}")
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
          arg_map=self.arg_map
      )
      documents = list(doc_iterator)
      logger.info(
          f"Extracted {len(documents)} raw documents for {file_name}")

      if not documents:
        logger.warning(f"No content extracted for {file_name}")
        self._run_async(self.document_repository.update_document_status(
            document_id, "learned", access_token))
        return {
            "status": "success",
            "chunks_inserted": 0,
            "document_id": document_id
        }

      # 2. Chunk ALL documents (Bulk)
      chunks = process_chunks(
          documents=documents,
          chunking_method=chunking_method,
          filename=file_name,
          embed_model=embed_model,
          **kwargs
      )

      # Entity Extraction
      # TODO: We currently run this on the first few pages to avoid excessive LLM costs
      # This can be made configurable via kwargs later
      extracted_edges = []
      try:
        from app.core.factory import get_extractor_service
        if enable_extraction:
          entity_nodes, extracted_edges = self._extract_and_create_entity_nodes(
            documents)
          if entity_nodes:
            logger.info(
              f"Extracted {len(entity_nodes)} entity nodes and {len(extracted_edges)} edges for {file_name}")
            chunks.extend(entity_nodes)
      except Exception as e:
        logger.warning(f"Entity extraction skipped/failed: {e}")

      if not chunks:
        logger.warning(f"No chunks generated for {file_name}")
        self._run_async(self.document_repository.update_document_status(
           document_id, "learned", access_token))
        return {
           "status": "success",
           "chunks_inserted": 0,
           "document_id": document_id
            }

      # 4. Wrap Chunks
      wrapped_chunks = self._wrap_chunks(
          chunks, document_id, file_path, kb_id, tenant_id)

      # 5. Upsert Metadata & Vectors (Bulk)
      self._run_async(self.graph_chunk_store.store(
        wrapped_chunks, access_token))
      self._upsert_vectors(wrapped_chunks, embed_model)

      # 5. Upsert Edges
      if extracted_edges and self.graph_edge_store:
        self._run_async(self.graph_edge_store.store(
          extracted_edges, access_token))

      self._run_async(self.document_repository.update_document_status(
          document_id, "learned", access_token))

      return {
          "status": "success",
          "chunks_inserted": len(wrapped_chunks),
          "document_id": document_id,
          "file_path": file_path,
      }
    except Exception as e:
      logger.exception(f"Failed to process file {file_name}: {e}")
      self._run_async(self.document_repository.update_document_status(
          document_id, "error", access_token))
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
      **kwargs
  ) -> Dict[str, Any]:
    """Bulk update: process full stream, then calc diff logic."""
    self._run_async(self.document_repository.update_document_status(
        document_id, "learning", access_token))

    from datetime import datetime
    # sync_start_time = datetime.utcnow().isoformat() # REMOVED: using ID-based sync
    stream_response = None

    try:
      embed_model = self._run_async(self._get_embedding_model(
          kb_id, tenant_id, access_token))

      logger.info(
          f"Starting bulk update for {file_name} from MinIO key: {file_path}")
      stream_response = self.original_file_store.get_file_stream(file_path)

      # 1. Read stream to bytes
      file_bytes = stream_response.read()

      # OPTIMIZATION: Do NOT delete all existing chunks upfront.
      # We will perform a differential update using hashes.
      existing_hashes_data = self._run_async(self.graph_chunk_store.get_hashes_by_document(
        document_id, access_token))
      existing_hash_map = {item['chunk_hash']: item['id']
                           for item in existing_hashes_data if item.get('chunk_hash')}

      # 2. Extract ALL
      import os
      ext = os.path.splitext(file_name)[1].lower()
      reader = self._get_reader(ext)
      reader_map = {ext: reader} if reader else {}

      doc_iterator = extract_documents(
          file_bytes=file_bytes,
          filename=file_name,
          reader_map=reader_map,
          arg_map=self.arg_map
      )
      documents = list(doc_iterator)

      # 3. Chunk ALL
      chunks = process_chunks(
          documents=documents,
          chunking_method=chunking_method,
          filename=file_name,
          embed_model=embed_model,
          **kwargs
      )

      # [NEW] Entity Extraction for Update
      extracted_edges = []
      try:
        if enable_extraction:
          entity_nodes, extracted_edges = self._extract_and_create_entity_nodes(
            documents)
          if entity_nodes:
            logger.info(
              f"Extracted {len(entity_nodes)} entity nodes and {len(extracted_edges)} edges for {file_name} (Update)")
            chunks.extend(entity_nodes)
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
            chunks, document_id, file_path, kb_id, tenant_id)

        # Filter the wrapped chunks for vectorization to match chunks_to_vectorize IDs
        # (Since _wrap_chunks creates new Document objects, checking by ID is safest)
        vectorize_ids = set(c.node_id for c in chunks_to_vectorize)
        wrapped_chunks_to_vectorize = [
          wc for wc in wrapped_chunks if wc.node_id in vectorize_ids]

        # 5. Upsert Metadata (ALL - guarantees timestamps are updated)
        self._run_async(self.graph_chunk_store.store(
          wrapped_chunks, access_token))

        # 6. Upsert Vectors (ONLY NEW)
        if wrapped_chunks_to_vectorize:
          logger.info(
            f"Vectorizing {len(wrapped_chunks_to_vectorize)} new/changed chunks.")
          self._upsert_vectors(
            wrapped_chunks_to_vectorize, embed_model)
        else:
          logger.info("No new chunks to vectorize.")

        # Upsert Edges
        if extracted_edges and self.graph_edge_store:
          self._run_async(self.graph_edge_store.store(
            extracted_edges, access_token))

      # 7. Sweep (Cleanup Stale)
      # This deletes anything in Supabase that wasn't included in 'wrapped_chunks' ( upserted above)
      # Robust fix using ID set difference
      active_ids = [c.node_id for c in wrapped_chunks]
      deleted_ids = self._run_async(self.graph_chunk_store.delete_stale_nodes(
          document_id=document_id,
          active_ids=active_ids,
          access_token=access_token
      ))

      # 8. Sync Vector Deletion (CASCADE handles this automatically)
      # Deleting from graph_chunks cascades to vectors.* tables
      if deleted_ids:
        logger.info(
          f"Deleted {len(deleted_ids)} stale chunks (CASCADE auto-deleted vectors)")

      self._run_async(self.document_repository.update_document_status(
          document_id, "learned", access_token))

      return {
          "status": "success",
          "chunks_deleted": len(deleted_ids),
          "chunks_added": len(wrapped_chunks),  # Total active chunks
          "chunks_vectorized": len(chunks_to_vectorize),
          "document_id": document_id
      }
    except Exception as e:
      logger.exception(f"Failed to update document {document_id}: {e}")
      self._run_async(self.document_repository.update_document_status(
          document_id, "error", access_token))
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

  def _upsert_vectors(self, documents: List[Document], embed_model: BaseEmbedding = None):
    """Upsert document vectors into Supabase vector store."""
    from app.core.factory import get_vector_store
    get_vector_store().upsert_documents(documents, embed_model)

  def _extract_and_create_entity_nodes(self, documents: List[Document]) -> tuple[List[TextNode], List[Dict]]:
    """
    Extracts entities and relationships from the documents using ExtractorService.
    Currently processes a subset of text to avoid context limits.
    Returns (entity_nodes, edges)
    """
    from app.core.factory import get_extractor_service

    extractor = get_extractor_service()
    entity_nodes = []
    edges = []

    # Simple strategy: Join first few pages (approx 5)
    subset_docs = documents[:5]
    full_text = "\n\n".join([d.text for d in subset_docs])

    if not full_text.strip():
      return [], []

    try:
      extractions = extractor.extract(full_text)

      entity_map = {}

      # 1. Process Entities
      if extractions:
        for entity in extractions:
          name = entity.extraction_text
          etype = entity.extraction_class

          if etype == "Relationship":
            continue

          # Create a meaningful text representation for embedding/search
          node_text = f"{name} ({etype})"

          node = TextNode(
              text=node_text,
              metadata={
                  "type": "entity",
                  "entity_name": name,
                  "entity_type": etype,
                  "extraction_source": "llm",
                  "included_in_graph": True
              }
          )
          entity_nodes.append(node)
          entity_map[name.lower()] = node

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

              if source_lower in entity_map and target_lower in entity_map:
                source_node = entity_map[source_lower]
                target_node = entity_map[target_lower]

                edge = {
                    "source_chunk_id": source_node.node_id,
                    "target_chunk_id": target_node.node_id,
                    "relationship_type": relation,
                    "properties": {
                        "source_text": rel_text,
                        "extraction_source": "llm"
                    }
                }
                edges.append(edge)

    except Exception as e:
      logger.error(f"Detailed extraction failed: {e}")

    return entity_nodes, edges
