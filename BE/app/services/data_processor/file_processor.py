import os
from typing import Any, Dict, List, Optional, Generator

from llama_index.core import Document
from llama_index.core.schema import BaseNode, NodeRelationship
from llama_index.readers.file import CSVReader, DocxReader, PDFReader, PptxReader
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
      reader = PDFReader()
    elif ext == FileExtension.PPTX:
      # Heavy model load, only do if needed
      reader = PptxReader()

    if reader:
      self._readers[ext] = reader

    return reader

    # Initialize argument map for LlamaIndex readers
    self.arg_map = {
        FileExtension.DOCX: "file",
        FileExtension.PPTX: "file",
        FileExtension.PDF: "file",
    }

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

        from app.core.factory import get_embedding_service
        specific_service = get_embedding_service(
            provider=provider,
            model=model
        )
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
      use_sparse: bool = True,
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
      use_sparse: bool = True,
      **kwargs
  ) -> Dict[str, Any]:
    """Bulk update: process full stream, then calc diff logic."""
    self.document_repository.update_document_status(
        document_id, "learning", access_token)

    from datetime import datetime
    sync_start_time = datetime.utcnow().isoformat()
    stream_response = None

    try:
      embed_model = self._get_embedding_model(kb_id, tenant_id, access_token)

      logger.info(
          f"Starting bulk update for {file_name} from MinIO key: {file_path}")
      stream_response = self.original_file_store.get_file_stream(file_path)

      # 1. Read stream to bytes
      file_bytes = stream_response.read()

      existing_chunks = self.meta_data_store.get_chunks_by_doc_id(
        document_id, access_token)
      if existing_chunks:
        ids_to_delete = [c['chunk_id'] for c in existing_chunks]
        model_name_for_del = embed_model.model_name if embed_model else None

        from app.core.factory import get_vector_store
        get_vector_store().delete_points_by_ids(ids_to_delete, model_name_for_del)

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

      # 2. Chunk ALL
      chunks = process_chunks(
          documents=documents,
          chunking_method=chunking_method,
          filename=file_name,
          embed_model=embed_model,
          **kwargs
      )

      wrapped_chunks = []
      if chunks:
          # 3. Wrap
        wrapped_chunks = self._wrap_chunks(
            chunks, document_id, file_path, kb_id, tenant_id)

        # 4. Upsert (Bulk)
        self.meta_data_store.store(wrapped_chunks, access_token)
        self._insert_to_qdrant(wrapped_chunks, embed_model, use_sparse)

      # 5. Sweep (Cleanup Stale)
      deleted_ids = self.meta_data_store.delete_stale_chunks(
          document_id=document_id,
          sync_start_time=sync_start_time,
          access_token=access_token
      )

      # 6. Sync Vector Deletion
      if deleted_ids:
        logger.info(f"Syncing deletion of {len(deleted_ids)} stale vectors.")
        # Get model name for vector deletion
        kb_data = self.kb_repository.get_one(kb_id, tenant_id, access_token)
        model_name = kb_data.get("embedding_model") if kb_data else None

        # NOTE: Fixed previous bug where model_name was undefined if deleted_ids was falsy but block entered?
        # Actually in new logic, we are inside if deleted_ids, so model_name is defined.
        from app.core.factory import get_vector_store
        get_vector_store().delete_points_by_ids(deleted_ids, model_name)

      self.document_repository.update_document_status(
          document_id, "learned", access_token)

      return {
          "status": "success",
          "chunks_deleted": len(deleted_ids),
          "chunks_added": len(wrapped_chunks),
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
      chunk_id = chunk.node_id

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
          "chunk_id": chunk_id,
      }

      if parent_id:
        metadata["parent_id"] = parent_id

      doc = Document(
          text=chunk_text,
          metadata=metadata,
      )
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
