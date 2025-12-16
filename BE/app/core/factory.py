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
from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.session_repository import SessionRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.user_repository import UserRepository
from app.services.supabase.document_repository import DocumentRepository
from app.services.supabase.chat_message_repository import ChatMessageRepository
from app.services.supabase.session_summary_repository import SessionSummaryRepository
from app.services.supabase.tenant_repository import TenantRepository
from app.services.session.session_service import SessionService
from app.services.users.user_service import UserService
from app.services.knowledge_base.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger("service_factory")

_user_repository_instance: UserRepository | None = None
_auth_service_instance: AuthService | None = None
_file_service_instance: FileProcessor | None = None
_embedding_service_instance: EmbeddingService | None = None
_vector_repo_instance: VectorRepository | None = None
_minio_storage_instance: MinioStorage | None = None
_metadata_repo_instance: MetadataRepository | None = None
_kb_repo_instance: KnowledgeBaseRepository | None = None
_bot_service_instance: BotService | None = None
_session_service_instance: SessionService | None = None
_user_service_instance: UserService | None = None
_knowledge_base_service_instance: KnowledgeBaseService | None = None
_document_repo_instance: DocumentRepository | None = None
_chat_message_repo_instance: ChatMessageRepository | None = None
_session_summary_repo_instance: SessionSummaryRepository | None = None
_tenant_repo_instance: TenantRepository | None = None
_bot_repo_instance: BotRepository | None = None
_session_repo_instance: SessionRepository | None = None


def get_embedding_service(provider: str = None, model: str = None) -> EmbeddingService:
  global _embedding_service_instance

  # If specific provider/model requested, return a new instance (don't use singleton)
  if provider:
    api_key = None
    endpoint = settings.EMBEDDING_API_URL
    target_model = model

    match provider.lower():
      case "openai":
        api_key = settings.OPENAI_API_KEY
        endpoint = None  # OpenAI SDK doesn't need endpoint usually, or uses default
        if not target_model:
          target_model = settings.OPENAI_EMBEDDING_MODEL
      case "ollama":
        # Use OLLAMA_URL for consistency if provider is explicitly ollama
        endpoint = settings.OLLAMA_EMBEDDING_API_URL
        if not target_model:
          target_model = settings.OLLAMA_EMBEDDING_MODEL
      case "google":
        api_key = settings.GEMINI_API_KEY
        endpoint = None
        if not target_model:
          target_model = settings.GEMINI_EMBEDDING_MODEL

    # Fallback to default if still not set
    if not target_model:
      target_model = settings.EMBEDDING_MODEL

    return EmbeddingService(
        provider=provider,
        model_name=target_model,
        api_key=api_key,
        endpoint=endpoint
    )

  # Default singleton logic
  if _embedding_service_instance is None:
    try:
      _embedding_service_instance = EmbeddingService()
      logger.info("Initialized EmbeddingService")
    except Exception as e:
      logger.exception("Failed to initialize EmbeddingService")
      raise
  return _embedding_service_instance


def get_vector_store() -> VectorRepository:
  """Singleton cho VectorRepository - kết nối đến Qdrant, quản lý vector DB."""
  global _vector_repo_instance
  if _vector_repo_instance is None:
    _vector_repo_instance = VectorRepository(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection=settings.QDRANT_COLLECTION,
        embedding_service=get_embedding_service(),
    )
  return _vector_repo_instance


def get_minio_storage() -> MinioStorage:
  """Singleton cho MinioStorage - dùng để lưu trữ file gốc (PDF, Word, etc.)."""
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
  """Singleton cho MetadataRepository - lưu metadata các chunk tài liệu vào Supabase."""
  global _metadata_repo_instance
  if _metadata_repo_instance is None:
    try:
      _metadata_repo_instance = MetadataRepository()
      logger.info("Initialized MetadataRepository")
    except Exception as e:
      logger.exception("Failed to initialize MetadataRepository")
      raise
  return _metadata_repo_instance


def get_knowledge_base_repository() -> KnowledgeBaseRepository:
  """Singleton cho KnowledgeBaseRepository - quản lý bảng `knowledge_base`."""
  global _kb_repo_instance
  if _kb_repo_instance is None:
    try:
      _kb_repo_instance = KnowledgeBaseRepository()
      logger.info("Initialized KnowledgeBaseRepository")
    except Exception as e:
      logger.exception("Failed to initialize KnowledgeBaseRepository")
      raise
  return _kb_repo_instance


def get_bot_repository() -> BotRepository:
  global _bot_repo_instance
  if _bot_repo_instance is None:
    try:
      _bot_repo_instance = BotRepository()
      logger.info("Initialized BotRepository")
    except Exception as e:
      logger.exception("Failed to initialize BotRepository")
      raise
  return _bot_repo_instance


def get_session_repository() -> SessionRepository:
  global _session_repo_instance
  if _session_repo_instance is None:
    try:
      _session_repo_instance = SessionRepository()
      logger.info("Initialized SessionRepository")
    except Exception as e:
      logger.exception("Failed to initialize SessionRepository")
      raise
  return _session_repo_instance


def get_user_repository() -> UserRepository:
  global _user_repository_instance
  if _user_repository_instance is None:
    try:
      _user_repository_instance = UserRepository()
      logger.info("Initialized UserRepository")
    except Exception as e:
      logger.exception("Failed to initialize UserRepository")
      raise
  return _user_repository_instance


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
        meta_data_store=get_metadata_repository(),
        document_repository=get_document_repository(),
        kb_repository=get_knowledge_base_repository()
    )
  return _file_service_instance


def get_bot_service() -> BotService:
  global _bot_service_instance
  if _bot_service_instance is None:
    _bot_service_instance = BotService(
        bot_repo=get_bot_repository(),
        session_repo=get_session_repository(),
        vector_repo=get_vector_store(),
        llm_service=LLMService(),
        message_repo=get_chat_message_repository(),
        kb_repo=get_knowledge_base_repository(),
    )
  return _bot_service_instance


def get_session_service() -> SessionService:
  global _session_service_instance
  if _session_service_instance is None:
    _session_service_instance = SessionService(
        session_repo=get_session_repository())
  return _session_service_instance


def get_user_service() -> UserService:
  global _user_service_instance
  if _user_service_instance is None:
    _user_service_instance = UserService(user_repo=get_user_repository())
  return _user_service_instance


def get_knowledge_base_service() -> KnowledgeBaseService:
  global _knowledge_base_service_instance
  if _knowledge_base_service_instance is None:
    _knowledge_base_service_instance = KnowledgeBaseService(
        kb_repo=get_knowledge_base_repository())
  return _knowledge_base_service_instance


def get_document_repository() -> DocumentRepository:
  global _document_repo_instance
  if _document_repo_instance is None:
    try:
      _document_repo_instance = DocumentRepository()
      logger.info("Initialized DocumentRepository")
    except Exception as e:
      logger.exception("Failed to initialize DocumentRepository")
      raise
  return _document_repo_instance


def get_chat_message_repository() -> ChatMessageRepository:
  global _chat_message_repo_instance
  if _chat_message_repo_instance is None:
    try:
      _chat_message_repo_instance = ChatMessageRepository()
      logger.info("Initialized ChatMessageRepository")
    except Exception as e:
      logger.exception("Failed to initialize ChatMessageRepository")
      raise
  return _chat_message_repo_instance


def get_session_summary_repository() -> SessionSummaryRepository:
  global _session_summary_repo_instance
  if _session_summary_repo_instance is None:
    try:
      _session_summary_repo_instance = SessionSummaryRepository()
      logger.info("Initialized SessionSummaryRepository")
    except Exception as e:
      logger.exception("Failed to initialize SessionSummaryRepository")
      raise
  return _session_summary_repo_instance


def get_tenant_repository() -> TenantRepository:
  global _tenant_repo_instance
  if _tenant_repo_instance is None:
    try:
      _tenant_repo_instance = TenantRepository()
      logger.info("Initialized TenantRepository")
    except Exception as e:
      logger.exception("Failed to initialize TenantRepository")
      raise
  return _tenant_repo_instance
