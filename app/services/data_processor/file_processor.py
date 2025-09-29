# app/services/data_processor/file_processor.py
import uuid
from typing import List

from app.core.logger import get_logger

from llama_index.core.schema import BaseNode
from llama_index.core import Document, Settings
from llama_index.readers.file import DocxReader, CSVReader
from llama_index.readers.json import JSONReader

from app.services.indexer.embedding_service import EmbeddingService, CustomEmbedding
from app.services.supabase.metadata_repository import MetadataRepository
from app.services.indexer.vector_store import VectorRepository
from app.services.minio.minio_storage import MinioStorage

from app.helper.document_extractor import extract_documents 
from app.helper.chunker import semantic_chunk_documents, _detect_or_create_document_id

logger = get_logger("File Processor Log")
class FileProcessor:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        meta_data_store: MetadataRepository,
        original_file_store: MinioStorage
        
    ):
        self.embedding_service=embedding_service
        self.vector_repository = vector_repository
        Settings.embed_model = CustomEmbedding(self.embedding_service, embed_batch_size=64)
        
        self.meta_data_store=meta_data_store
        self.original_file_store=original_file_store
        self._initialize_readers()
        self._detect_or_create_document_id = _detect_or_create_document_id

    def _initialize_readers(self):
        """Map file extensions to appropriate LlamaIndex readers."""
        self.readers = {}
        self.reader_arg_map = {}

        self.readers.update({
            ".docx": DocxReader(),
            ".csv": CSVReader(),
            ".json": JSONReader(),
        })
        self.reader_arg_map.update({
            ".docx": "file",
            ".csv": "file",
            ".json": "input_file"
        })
    
    def process_file(
        self,
        file_bytes: bytes,
        file_name: str,
        kb_id: int,
        tenant_id: str
    ):
        document_id = self._detect_or_create_document_id(file_name, tenant_id)
        file_path = self._upload_original_file(file_bytes, file_name)
        documents = extract_documents(file_bytes, file_name, self.readers, self.reader_arg_map)
        chunks = semantic_chunk_documents(documents, file_name)
        wrapped_chunks = self._wrap_chunks(chunks, document_id, file_path, tenant_id, str(kb_id))
        
        self.meta_data_store.store(wrapped_chunks)
        self._insert_to_qdrant(wrapped_chunks)

        return {
            "status": "success",
            "chunks_inserted": len(wrapped_chunks),
            "document_id": document_id,
            "file_path": file_path
        }

    def _wrap_chunks(
        self,
        chunks: List[BaseNode],
        document_id: str,
        file_path: str,
        tenant_id: str,
        kb_id: str
    ) -> List[Document]:
        """Attach metadata to each chunk before embedding."""

        wrapped_chunks = []
        for _, chunk in enumerate(chunks):
            chunk_text = chunk.text
            chunk_id = str(uuid.uuid4()) 

            doc = Document(
                text=chunk_text,
                metadata={
                    **chunk.metadata,
                    "document_id": document_id,
                    "file_path": file_path,
                    "tenant_id": tenant_id,
                    "kb_id": kb_id,
                    "chunk_id": chunk_id
                }
            )
            wrapped_chunks.append(doc)

        return wrapped_chunks
    
    def _insert_to_qdrant(self, documents: List[Document]):
        """Insert documents (chunks) into Qdrant vector store."""
        self.vector_repository.upsert_documents(documents)
        
    def _upload_original_file(self, file_bytes: bytes, filename: str) -> str:
        """Upload the original document to MinIO and return its storage path."""
        return self.original_file_store.upload_file(file_bytes, filename)
