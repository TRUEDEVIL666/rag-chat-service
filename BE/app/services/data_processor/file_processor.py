# app/services/data_processor/file_processor.py
import uuid
from typing import List

from app.core.logger import get_logger

from llama_index.core.schema import BaseNode, NodeRelationship
from llama_index.core import Document, Settings
from llama_index.readers.file import DocxReader, CSVReader, PDFReader, PptxReader
from llama_index.readers.json import JSONReader

from app.services.supabase.document_repository import DocumentRepository
from app.services.indexer.embedding_service import EmbeddingService, CustomEmbedding
from app.services.supabase.metadata_repository import MetadataRepository
from app.services.indexer.vector_store import VectorRepository
from app.services.minio.minio_storage import MinioStorage
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository

from app.helper.document_extractor import extract_documents
from app.helper.chunker import process_chunks, _detect_or_create_document_id
from app.core.enums.file import FileExtension

logger = get_logger("File Processor Log")


class FileProcessor:
  def __init__(
      self,
      embedding_service: EmbeddingService,
      vector_repository: VectorRepository,
      meta_data_store: MetadataRepository,
      original_file_store: MinioStorage,
      document_repository: DocumentRepository,
      kb_repository: KnowledgeBaseRepository,
  ):
    self.embedding_service = embedding_service
    self.vector_repository = vector_repository
    Settings.embed_model = CustomEmbedding(
      self.embedding_service, embed_batch_size=64
    )

    self.meta_data_store = meta_data_store
    self.original_file_store = original_file_store
    self.document_repository = document_repository
    self.kb_repository = kb_repository
    self._initialize_readers()
    self._detect_or_create_document_id = _detect_or_create_document_id

  def _initialize_readers(self):
    """Map file extensions to appropriate LlamaIndex readers."""
    self.readers = {}
    self.reader_arg_map = {}

    self.readers.update(
      {
        FileExtension.DOCX: DocxReader(),
        FileExtension.CSV: CSVReader(),
        FileExtension.JSON: JSONReader(),
        FileExtension.PDF: PDFReader(),
        FileExtension.PPTX: PptxReader(),
      }
    )
    self.reader_arg_map.update(
      {
          FileExtension.DOCX: "file",
          FileExtension.CSV: "file",
          FileExtension.JSON: "input_file",
          FileExtension.PDF: "file",
          FileExtension.PPTX: "file",
      }
    )

  def process_file(
      self,
      file_bytes: bytes,
      file_name: str,
      kb_id: str,
      tenant_id: str,
      created_by: str,
      access_token: str = None,
      chunking_method: str = "sentence",
      use_sparse: bool = True
  ):
    document_id = self._detect_or_create_document_id(file_name)
    file_path = self._upload_original_file(file_bytes, file_name)

    # Create initial document record
    self.document_repository.create_document({
        "id": document_id,
        "name": file_name,
        "path": file_path,
        "knowledgebase_id": kb_id,
        "tenant_id": tenant_id,
        "created_by": created_by,
        "status": "learning"
    }, access_token)

    try:
      documents = extract_documents(
          file_bytes,
          file_name,
          self.readers,
          self.reader_arg_map
      )
      chunks = process_chunks(
          documents=documents,
          chunking_method=chunking_method,
          filename=file_name,
      )
      wrapped_chunks = self._wrap_chunks(
          chunks,
          document_id,
          file_path,
          kb_id,
          tenant_id
      )

      self.meta_data_store.store(wrapped_chunks, access_token)

      # Determine embedding model from Knowledge Base
      embed_model = None
      # Config for Sparse Vector Generation is now passed via API (use_sparse)

      kb_data = self.kb_repository.get_one(kb_id, tenant_id, access_token)

      if kb_data:
        # Resolve Embedding Model
        if kb_data.get("embedding_model"):
          embedding_config = kb_data["embedding_model"]
          # Expected format: "provider/model"
          if "/" in embedding_config:
            provider, model = embedding_config.split("/", 1)
            from app.core.factory import get_embedding_service
            # Create a specific embedding service for this file
            specific_embedding_service = get_embedding_service(
              provider=provider, model=model)
            embed_model = CustomEmbedding(
              specific_embedding_service, embed_batch_size=64)
          else:
            logger.warning(
              f"Invalid embedding_model format for KB {kb_id}: {embedding_config}")

      self._insert_to_qdrant(wrapped_chunks, embed_model, use_sparse)

      # Update status to learned
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
      # Use the LlamaIndex Node ID as the Qdrant Point ID to ensure we can retrieve Parents by ID
      chunk_id = chunk.node_id

      # Extract Parent ID for Auto-Merging Retrieval
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
    self.vector_repository.upsert_documents(documents, embed_model, use_sparse)

  def _upload_original_file(self, file_bytes: bytes, filename: str) -> str:
    """Upload the original document to MinIO and return its storage path."""
    return self.original_file_store.upload_file(file_bytes, filename)
