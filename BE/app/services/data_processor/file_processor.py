import os
import pymupdf4llm
from typing import Any, Dict, List, Optional, Generator

from llama_index.core import Document
from llama_index.core.schema import BaseNode, NodeRelationship
from llama_index.readers.file import (
    CSVReader, DocxReader, PDFReader, PptxReader,
    MarkdownReader, HTMLTagReader, ImageReader
)
from llama_index.readers.json import JSONReader

from app.core.enums.file import FileExtension
from app.core.logger import get_logger
from app.helper.chunker import process_chunks
from app.helper.document_extractor import extract_documents
from app.services.indexer.embedding_service import CustomEmbedding, EmbeddingService
from app.services.indexer.vector_store import VectorRepository
from app.services.minio.minio_storage import MinioStorage
from app.services.supabase.document_repository import DocumentRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.metadata_repository import MetadataRepository

logger = get_logger("File Processor Log")


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
      meta_data_store: MetadataRepository,
      original_file_store: MinioStorage,
      document_repository: DocumentRepository,
      kb_repository: KnowledgeBaseRepository,
  ):
    self.meta_data_store = meta_data_store
    self.original_file_store = original_file_store
    self.document_repository = document_repository
    self.kb_repository = kb_repository

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

  def _get_embedding_model(self, kb_id: str, tenant_id: str, access_token: Optional[str]) -> Optional[CustomEmbedding]:
    """Resolves the correct embedding model for the Knowledge Base."""
    kb_data = self.kb_repository.get_one(kb_id, tenant_id, access_token)
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
          return None

        import asyncio
        from app.core.factory import get_embedding_service

        # Helper to run async factory in sync context
        async def _fetch_service():
          return await get_embedding_service(
              provider=provider,
              model=model
          )

        try:
          loop = asyncio.get_event_loop()
        except RuntimeError:
          loop = None

        if loop and loop.is_running():
          # Fallback if nest_asyncio is present, or error out
          import nest_asyncio
          nest_asyncio.apply(loop)
          specific_service = loop.run_until_complete(_fetch_service())
        else:
          specific_service = asyncio.run(_fetch_service())
        return CustomEmbedding(specific_service, embed_batch_size=64)
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
      use_sparse: bool = False,
      **kwargs
  ) -> Dict[str, Any]:
    # Create initial document record
    # Update status to learning (Document created synchronously in DocumentService)
    self.document_repository.update_document_status(
        document_id, "learning", access_token)

    stream_response = None
    try:
      embed_model = self._get_embedding_model(kb_id, tenant_id, access_token)

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
        self.document_repository.update_document_status(
            document_id, "learned", access_token)
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

      if not chunks:
        logger.warning(f"No chunks generated for {file_name}")
        self.document_repository.update_document_status(
           document_id, "learned", access_token)
        return {
           "status": "success",
           "chunks_inserted": 0,
           "document_id": document_id
            }

      # 3. Wrap with Metadata (Bulk)
      wrapped_chunks = self._wrap_chunks(
          chunks, document_id, file_path, kb_id, tenant_id)

      # 4. Upsert Metadata & Vectors (Bulk)
      self.meta_data_store.store(wrapped_chunks, access_token)
      self._insert_to_qdrant(wrapped_chunks, embed_model, use_sparse)

      self.document_repository.update_document_status(
          document_id, "learned", access_token)

      return {
          "status": "success",
          "chunks_inserted": len(wrapped_chunks),
          "document_id": document_id,
          "file_path": file_path,
      }
    except Exception as e:
      logger.exception(f"Failed to process file {file_name}: {e}")
      self.document_repository.update_document_status(
          document_id, "error", access_token)
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
      use_sparse: bool = False,
      **kwargs
  ) -> Dict[str, Any]:
    """Bulk update: process full stream, then calc diff logic."""
    self.document_repository.update_document_status(
        document_id, "learning", access_token)

    from datetime import datetime
    # sync_start_time = datetime.utcnow().isoformat() # REMOVED: using ID-based sync
    stream_response = None

    try:
      embed_model = self._get_embedding_model(kb_id, tenant_id, access_token)

      logger.info(
          f"Starting bulk update for {file_name} from MinIO key: {file_path}")
      stream_response = self.original_file_store.get_file_stream(file_path)

      # 1. Read stream to bytes
      file_bytes = stream_response.read()

      # OPTIMIZATION: Do NOT delete all existing chunks upfront.
      # We will perform a differential update using hashes.
      existing_hashes_data = self.meta_data_store.get_hashes_by_document(
        document_id, access_token)
      existing_hash_map = {item['chunk_hash']: item['node_id']
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
        self.meta_data_store.store(wrapped_chunks, access_token)

        # 6. Upsert Vectors (ONLY NEW)
        if wrapped_chunks_to_vectorize:
          logger.info(
            f"Vectorizing {len(wrapped_chunks_to_vectorize)} new/changed chunks.")
          self._insert_to_qdrant(
            wrapped_chunks_to_vectorize, embed_model, use_sparse)
        else:
          logger.info("No new chunks to vectorize.")

      # 7. Sweep (Cleanup Stale)
      # This deletes anything in Supabase that wasn't included in 'wrapped_chunks' ( upserted above)
      # Robust fix using ID set difference
      active_node_ids = [c.node_id for c in wrapped_chunks]
      deleted_node_ids = self.meta_data_store.delete_stale_nodes(
          document_id=document_id,
          active_node_ids=active_node_ids,
          access_token=access_token
      )

      # 8. Sync Vector Deletion
      logger.info(f"Deleted IDs returned from Supabase: {deleted_node_ids}")
      if deleted_node_ids:
        logger.info(
          f"Syncing deletion of {len(deleted_node_ids)} stale vectors.")
        # Get model name for vector deletion
        kb_data = self.kb_repository.get_one(kb_id, tenant_id, access_token)
        model_data = kb_data.get("embedding_model") if kb_data else None
        model_name = model_data.get("model_id") if isinstance(
            model_data, dict) else model_data

        from app.core.factory import get_vector_store
        # Use FAST O(1) delete_points_by_ids since IDs now match
        get_vector_store().delete_points_by_ids(deleted_node_ids, model_name)

      self.document_repository.update_document_status(
          document_id, "learned", access_token)

      return {
          "status": "success",
          "chunks_deleted": len(deleted_node_ids),
          "chunks_added": len(wrapped_chunks),  # Total active chunks
          "chunks_vectorized": len(chunks_to_vectorize),
          "document_id": document_id
      }
    except Exception as e:
      logger.exception(f"Failed to update document {document_id}: {e}")
      self.document_repository.update_document_status(
          document_id, "error", access_token)
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
          "node_id": node_id,
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

  def _insert_to_qdrant(self, documents: List[Document], embed_model: CustomEmbedding = None, use_sparse: bool = True):
    """Insert documents (chunks) into Qdrant vector store."""
    from app.core.factory import get_vector_store
    get_vector_store().upsert_documents(
      documents, embed_model, use_sparse)

  def _upload_original_file(self, file_bytes: bytes, filename: str) -> str:
    """Upload the original document to MinIO and return its storage path."""
    return self.original_file_store.upload_file(file_bytes, filename)
