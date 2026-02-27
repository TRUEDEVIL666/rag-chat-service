from __future__ import annotations

from typing import TYPE_CHECKING

from llama_index.core.base.embeddings.base import BaseEmbedding

from app.config.config import settings
from app.core.logger import get_logger
from app.services.indexer.embedding_service import create_embedding_model

logger = get_logger(__name__)


if TYPE_CHECKING:
  from app.services.tool.tool_service import ToolService

  from app.services.ai_model.ai_model_service import AiModelService
  from app.services.analytics.analytics_service import AnalyticsService
  from app.services.auth.auth_service import AuthService
  from app.services.bot.bot_service import BotService
  from app.services.chat.chat_service import ChatService
  from app.services.course.class_service import ClassService
  from app.services.course.course_service import CourseService
  from app.services.course.semester_service import SemesterService
  from app.services.data_processor.file_processor import FileProcessor
  from app.services.document.document_service import DocumentService
  from app.services.extractor.extractor_service import ExtractorService
  from app.services.indexer.vector_store import VectorRepository
  from app.services.knowledge_base.knowledge_base_service import KnowledgeBaseService
  from app.services.minio.minio_storage import MinioStorage
  from app.services.session.session_service import SessionService
  from app.services.supabase.ai_model_repository import AiModelRepository
  from app.services.supabase.bot_repository import BotRepository
  from app.services.supabase.chat_message_repository import ChatMessageRepository
  from app.services.supabase.class_repository import ClassRepository
  from app.services.supabase.course_repository import CourseRepository
  from app.services.supabase.document_repository import DocumentRepository
  from app.services.supabase.graph_chunk_repository import GraphChunkRepository
  from app.services.supabase.graph_edge_repository import GraphEdgeRepository
  from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
  from app.services.supabase.quiz_repository import QuizRepository
  from app.services.supabase.semester_repository import SemesterRepository
  from app.services.supabase.session_repository import SessionRepository
  from app.services.supabase.session_summary_repository import SessionSummaryRepository
  from app.services.supabase.tenant_repository import TenantRepository
  from app.services.supabase.user_repository import UserRepository
  from app.services.users.user_service import UserService


# ----------------------------------------------------------------
# SINGLETON INSTANCES
# ----------------------------------------------------------------
_analytics_service_instance: AnalyticsService | None = None
_ai_model_repo_instance: AiModelRepository | None = None
_ai_model_service_instance: AiModelService | None = None
_auth_service_instance: AuthService | None = None
_bot_repo_instance: BotRepository | None = None
_bot_service_instance: BotService | None = None
_chat_message_repo_instance: ChatMessageRepository | None = None
_chat_service_instance: ChatService | None = None
_class_repo_instance: ClassRepository | None = None
_class_service_instance: ClassService | None = None
_course_repo_instance: CourseRepository | None = None
_course_service_instance: CourseService | None = None
_document_repo_instance: DocumentRepository | None = None
_document_service_instance: DocumentService | None = None
_embedding_model_instance: BaseEmbedding | None = None
_file_service_instance: FileProcessor | None = None
_kb_repo_instance: KnowledgeBaseRepository | None = None
_knowledge_base_service_instance: KnowledgeBaseService | None = None
_graph_chunk_repo_instance: GraphChunkRepository | None = None
_graph_edge_repo_instance: GraphEdgeRepository | None = None
_minio_storage_instance: MinioStorage | None = None
_quiz_repo_instance: QuizRepository | None = None
_semester_repo_instance: SemesterRepository | None = None
_semester_service_instance: SemesterService | None = None
_session_repo_instance: SessionRepository | None = None
_session_service_instance: SessionService | None = None
_session_summary_repo_instance: SessionSummaryRepository | None = None
_tenant_repo_instance: TenantRepository | None = None
_tool_service_instance: ToolService | None = None
_user_repository_instance: UserRepository | None = None
_user_service_instance: UserService | None = None
_vector_repo_instance: VectorRepository | None = None
_extractor_service_instance: ExtractorService | None = None


# ----------------------------------------------------------------
# CORE SERVICES
# ----------------------------------------------------------------
async def get_embedding_model(provider: str = None, model: str = None) -> BaseEmbedding:
  global _embedding_model_instance

  # If specific provider/model requested, return a new instance (don't use singleton)
  # logic: If model is passed like "ollama/gemma", we need to split it if provider is missing
  target_model = model

  if provider or model:
    api_key = None
    endpoint = None

    try:
      if provider:
        repo = get_ai_model_repository()
        resolved_key, resolved_url, _ = await repo.resolve_model_config(
          provider_name=provider, model_name=target_model
        )

        if resolved_key:
          api_key = resolved_key
        if resolved_url:
          endpoint = resolved_url

        # Defaults if DB resolution failed (e.g. initial setup)
        if not endpoint and provider.lower() == "ollama":
          endpoint = settings.OLLAMA_EMBEDDING_API_URL

    except Exception as e:
      logger.warning(f"Failed to resolve config for {provider} from DB: {e}")
      # Fallback for Ollama if DB fail
      if provider and provider.lower() == "ollama":
        endpoint = settings.OLLAMA_EMBEDDING_API_URL

    return create_embedding_model(
        provider=provider,
        model_name=target_model,
        api_key=api_key,
        endpoint=endpoint
    )

  # Default singleton logic
  if _embedding_model_instance is None:
    try:
      _embedding_model_instance = create_embedding_model()
      logger.info("Initialized EmbeddingModel (Default)")
    except Exception as e:
      logger.exception("Failed to initialize EmbeddingModel")
      raise
  return _embedding_model_instance


def get_vector_store() -> VectorRepository:
  """Singleton for VectorRepository - Supabase-backed vector storage."""
  global _vector_repo_instance
  if _vector_repo_instance is None:
    from app.services.indexer.vector_store import VectorRepository
    _vector_repo_instance = VectorRepository()
  return _vector_repo_instance


def get_minio_storage() -> MinioStorage:
  """Singleton cho MinioStorage - dùng để lưu trữ file gốc (PDF, Word, etc.)."""
  global _minio_storage_instance
  if _minio_storage_instance is None:
    try:
      from app.services.minio.minio_storage import MinioStorage
      _minio_storage_instance = MinioStorage(bucket_name="rag-file")
      logger.info("Initialized MinioStorage")
    except Exception as e:
      logger.exception("Failed to initialize MinioStorage")
      raise
  return _minio_storage_instance


def get_graph_chunk_repository() -> GraphChunkRepository:
  """Singleton for GraphChunkRepository - stores chunks (graph nodes) in Supabase."""
  global _graph_chunk_repo_instance
  if _graph_chunk_repo_instance is None:
    try:
      from app.services.supabase.graph_chunk_repository import GraphChunkRepository
      _graph_chunk_repo_instance = GraphChunkRepository()
      logger.info("Initialized GraphChunkRepository")
    except Exception as e:
      logger.exception("Failed to initialize GraphChunkRepository")
      raise
  return _graph_chunk_repo_instance


def get_graph_edge_repository() -> GraphEdgeRepository:
  """Singleton for GraphEdgeRepository - stores graph edges (relationships) in Supabase."""
  global _graph_edge_repo_instance
  if _graph_edge_repo_instance is None:
    try:
      from app.services.supabase.graph_edge_repository import GraphEdgeRepository
      _graph_edge_repo_instance = GraphEdgeRepository()
      logger.info("Initialized GraphEdgeRepository")
    except Exception as e:
      logger.exception("Failed to initialize GraphEdgeRepository")
      raise
  return _graph_edge_repo_instance


def get_knowledge_base_repository() -> KnowledgeBaseRepository:
  """Singleton cho KnowledgeBaseRepository - quản lý bảng `knowledge_base`."""
  global _kb_repo_instance
  if _kb_repo_instance is None:
    try:
      from app.services.supabase.knowledge_base_repository import (
        KnowledgeBaseRepository,
      )
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
      from app.services.supabase.bot_repository import BotRepository
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
      from app.services.supabase.session_repository import SessionRepository
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
      from app.services.supabase.user_repository import UserRepository
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
      from app.services.auth.auth_service import AuthService
      _auth_service_instance = AuthService()
      logger.info("Initialized AuthService")
    except Exception as e:
      logger.exception("Failed to initialize AuthService")
      raise
  return _auth_service_instance


def get_file_processor_service() -> FileProcessor:
  global _file_service_instance
  if _file_service_instance is None:
    from app.services.data_processor.file_processor import FileProcessor
    _file_service_instance = FileProcessor(
        original_file_store=get_minio_storage(),
        meta_data_store=get_graph_chunk_repository(),
        graph_edge_repository=get_graph_edge_repository(),
        document_repository=get_document_repository(),
        kb_repository=get_knowledge_base_repository()
    )
  return _file_service_instance


def get_bot_service() -> BotService:
  global _bot_service_instance
  if _bot_service_instance is None:
    from app.services.bot.bot_service import BotService
    _bot_service_instance = BotService(
        bot_repo=get_bot_repository(),
        session_repo=get_session_repository()
    )
  return _bot_service_instance


def get_tool_service() -> ToolService:
  global _tool_service_instance
  if _tool_service_instance is None:
    try:
      from app.services.tool.tool_service import ToolService
      _tool_service_instance = ToolService()
      logger.info("Initialized ToolService")
    except Exception as e:
      logger.exception("Failed to initialize ToolService")
      raise
  return _tool_service_instance


def get_chat_service() -> ChatService:
  global _chat_service_instance
  if _chat_service_instance is None:
    from app.services.chat.chat_service import ChatService
    from app.services.llm.llm_service import LLMService
    _chat_service_instance = ChatService(
        bot_repo=get_bot_repository(),
        session_repo=get_session_repository(),
        llm_service=LLMService(),
        message_repo=get_chat_message_repository(),
        kb_repo=get_knowledge_base_repository(),
        ai_model_service=get_ai_model_service(),
        tool_service=get_tool_service()
    )
  return _chat_service_instance


def get_session_service() -> SessionService:
  global _session_service_instance
  if _session_service_instance is None:
    from app.services.session.session_service import SessionService
    _session_service_instance = SessionService(
        session_repo=get_session_repository(),
        chat_message_repo=get_chat_message_repository()
    )
  return _session_service_instance


def get_user_service() -> UserService:
  global _user_service_instance
  if _user_service_instance is None:
    from app.services.users.user_service import UserService
    _user_service_instance = UserService(user_repo=get_user_repository())
  return _user_service_instance


def get_knowledge_base_service() -> KnowledgeBaseService:
  global _knowledge_base_service_instance
  if _knowledge_base_service_instance is None:
    from app.services.knowledge_base.knowledge_base_service import KnowledgeBaseService
    _knowledge_base_service_instance = KnowledgeBaseService(
        kb_repo=get_knowledge_base_repository(),
        doc_repo=get_document_repository(),
        # vector_repo=get_vector_store(),
        tenant_repo=get_tenant_repository()
    )
  return _knowledge_base_service_instance


def get_ai_model_service() -> AiModelService:
  global _ai_model_service_instance
  if _ai_model_service_instance is None:
    from app.services.ai_model.ai_model_service import AiModelService
    _ai_model_service_instance = AiModelService(
        repo=get_ai_model_repository()
    )
  return _ai_model_service_instance


def get_document_service() -> DocumentService:
  global _document_service_instance
  if _document_service_instance is None:
    from app.services.document.document_service import DocumentService
    _document_service_instance = DocumentService(
        doc_repo=get_document_repository(),
        minio_storage=get_minio_storage(),
        graph_chunk_repo=get_graph_chunk_repository(),
        kb_repo=get_knowledge_base_repository()
    )
  return _document_service_instance


def get_document_repository() -> DocumentRepository:
  global _document_repo_instance
  if _document_repo_instance is None:
    try:
      from app.services.supabase.document_repository import DocumentRepository
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
      from app.services.supabase.chat_message_repository import ChatMessageRepository
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
      from app.services.supabase.session_summary_repository import (
        SessionSummaryRepository,
      )
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
      from app.services.supabase.tenant_repository import TenantRepository
      _tenant_repo_instance = TenantRepository()
      logger.info("Initialized TenantRepository")
    except Exception as e:
      logger.exception("Failed to initialize TenantRepository")
      raise
  return _tenant_repo_instance


def get_ai_model_repository() -> AiModelRepository:
  global _ai_model_repo_instance
  if _ai_model_repo_instance is None:
    try:
      from app.services.supabase.ai_model_repository import AiModelRepository
      _ai_model_repo_instance = AiModelRepository()
      logger.info("Initialized AiModelRepository")
    except Exception as e:
      logger.exception("Failed to initialize AiModelRepository")
      raise
  return _ai_model_repo_instance


def get_analytics_service() -> AnalyticsService:
  global _analytics_service_instance
  if _analytics_service_instance is None:
    from app.services.analytics.analytics_service import AnalyticsService
    _analytics_service_instance = AnalyticsService(
        user_service=get_user_service(),
        session_service=get_session_service(),
        kb_service=get_knowledge_base_service(),
        doc_repo=get_document_repository(),
        chat_repo=get_chat_message_repository(),
        class_repo=get_class_repository()
    )
  return _analytics_service_instance


def get_quiz_repository() -> QuizRepository:
  global _quiz_repo_instance
  if _quiz_repo_instance is None:
    try:
      from app.services.supabase.quiz_repository import QuizRepository
      _quiz_repo_instance = QuizRepository()
      logger.info("Initialized QuizRepository")
    except Exception as e:
      logger.exception("Failed to initialize QuizRepository")
      raise
  return _quiz_repo_instance


# ----------------------------------------------------------------
# LMS MODULES (Semester, Course, Class)
# ----------------------------------------------------------------

# --- REPOSITORIES ---


# --- SERVICES ---


# --- SEMESTERS ---
def get_semester_repository() -> SemesterRepository:
  global _semester_repo_instance
  if _semester_repo_instance is None:
    from app.services.supabase.semester_repository import SemesterRepository
    _semester_repo_instance = SemesterRepository(supabase_client=None)
  return _semester_repo_instance


def get_semester_service() -> SemesterService:
  global _semester_service_instance
  if _semester_service_instance is None:
    from app.services.course.semester_service import SemesterService
    _semester_service_instance = SemesterService(
      repo=get_semester_repository())
  return _semester_service_instance


# --- COURSES ---
def get_course_repository() -> CourseRepository:
  global _course_repo_instance
  if _course_repo_instance is None:
    from app.services.supabase.course_repository import CourseRepository
    _course_repo_instance = CourseRepository(supabase_client=None)
  return _course_repo_instance


def get_course_service() -> CourseService:
  global _course_service_instance
  if _course_service_instance is None:
    from app.services.course.course_service import CourseService
    _course_service_instance = CourseService(repo=get_course_repository())
  return _course_service_instance


# --- CLASSES ---
def get_class_repository() -> ClassRepository:
  global _class_repo_instance
  if _class_repo_instance is None:
    from app.services.supabase.class_repository import ClassRepository
    _class_repo_instance = ClassRepository(supabase_client=None)
  return _class_repo_instance


def get_class_service() -> ClassService:
  global _class_service_instance
  if _class_service_instance is None:
    from app.services.course.class_service import ClassService
    _class_service_instance = ClassService(
      repo=get_class_repository(),
      doc_repo=get_document_repository()
    )
  return _class_service_instance


def get_extractor_service() -> ExtractorService:
  global _extractor_service_instance
  if _extractor_service_instance is None:
    try:
      from app.services.extractor.extractor_service import ExtractorService
      _extractor_service_instance = ExtractorService()
      logger.info("Initialized ExtractorService")
    except Exception as e:
      logger.exception("Failed to initialize ExtractorService")
      raise
  return _extractor_service_instance
