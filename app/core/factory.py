# app/core/factory.py
import logging
from app.config.config import settings
from app.services.auth.auth_service import AuthService
from app.services.data_processor.file_processor import FileProcessor
from app.services.indexer.embedding_service import EmbeddingService
from app.services.indexer.vector_store import VectorRepository
from app.services.supabase.metadata_repository import MetadataRepository
from app.services.minio.minio_storage import MinioStorage
from app.services.bot.bot_service import BotService
from app.services.llm.llm_service import LLMService
from app.services.supabase.kb_repository import KnowledgeBaseRepository

logger = logging.getLogger("service_factory")

_auth_service_instance: AuthService | None = None
_file_service_instance: FileProcessor | None = None
_embedding_service_instance: EmbeddingService | None = None
_vector_repo_instance: VectorRepository | None = None
_minio_storage_instance: MinioStorage | None = None
_metadata_repo_instance: MetadataRepository | None = None
_kb_repo_instance: KnowledgeBaseRepository | None = None
_bot_service_instance: BotService | None = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service_instance
    if _embedding_service_instance is None:
        try:
            _embedding_service_instance = EmbeddingService()
            logger.info("Initialized EmbeddingService")
        except Exception as e:
            logger.exception("Failed to initialize EmbeddingService")
            raise
    return _embedding_service_instance

def get_vector_store() -> VectorRepository:
    """Singleton cho VectorRepository – kết nối đến Qdrant, quản lý vector DB."""
    global _vector_repo_instance
    if _vector_repo_instance is None:
        _vector_repo_instance = VectorRepository(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection=settings.qdrant_collection,
            embedding_service=get_embedding_service(),
        )
    return _vector_repo_instance

def get_minio_storage() -> MinioStorage:
    """Singleton cho MinioStorage – dùng để lưu trữ file gốc (PDF, Word, etc.)."""
    global _minio_storage_instance
    if _minio_storage_instance is None:
        try:
            _minio_storage_instance = MinioStorage(bucket_name="rag-file")
            logger.info("Initialized MinioStorage")
        except Exception as e:
            logger.exception("Failed to initialize MinioStorage")
            raise
    return _minio_storage_instance

def get_metadata_repository() -> MetadataRepository:
    """Singleton cho MetadataRepository – lưu metadata các chunk tài liệu vào Supabase."""
    global _metadata_repo_instance
    if _metadata_repo_instance is None:
        try:
            _metadata_repo_instance = MetadataRepository()
            logger.info("Initialized MetadataRepository")
        except Exception as e:
            logger.exception("Failed to initialize MetadataRepository")
            raise
    return _metadata_repo_instance

def get_kb_repository() -> KnowledgeBaseRepository:
    """Singleton cho KnowledgeBaseRepository – quản lý bảng `knowledge_base`."""
    global _kb_repo_instance
    if _kb_repo_instance is None:
        try:
            _kb_repo_instance = KnowledgeBaseRepository()
            logger.info("Initialized KnowledgeBaseRepository")
        except Exception as e:
            logger.exception("Failed to initialize KnowledgeBaseRepository")
            raise
    return _kb_repo_instance

def get_auth_service() -> AuthService:
    global _auth_service_instance
    if _auth_service_instance is None:
        try:
            _auth_service_instance = AuthService()
            logger.info("Initialized AuthService")
        except Exception as e:
            logger.exception("Failed to initialize AuthService")
            raise
    return _auth_service_instance

def get_file_processor_service() -> FileProcessor:
    global _file_service_instance
    if _file_service_instance is None:
        _file_service_instance = FileProcessor(
            embedding_service=get_embedding_service(),
            vector_repository=get_vector_store(),
            original_file_store=get_minio_storage(),
            meta_data_store=get_metadata_repository()
        )
    return _file_service_instance

def get_bot_service() -> BotService:
    global _bot_service_instance
    if _bot_service_instance is None:
        _bot_service_instance = BotService(
            vector_repo=get_vector_store(),
            llm_service=LLMService()
        )
    return _bot_service_instance
