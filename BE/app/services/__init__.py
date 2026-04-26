from .ai_model_service import AiModelService
from .analytics_service import AnalyticsService
from .auth_service import AuthService
from .course_service import CourseService
from .document_service import DocumentService
from .embedding_service import create_embedding_model
from .extractor_service import ExtractorService
from .file_processing_service import FileProcessor
from .knowledge_base_service import KnowledgeBaseService
from .memory_service import MemoryService
from .minio_storage_service import MinioStorageService
from .session_service import SessionService
from .user_service import UserService

ai_model_service_instance = AiModelService.get_instance()
analytics_service_instance = AnalyticsService.get_instance()
auth_service_instance = AuthService.get_instance()
course_service_instance = CourseService.get_instance()
document_service_instance = DocumentService.get_instance()
extractor_service_instance = ExtractorService.get_instance()
file_processor_instance = FileProcessor.get_instance()
kb_service_instance = KnowledgeBaseService.get_instance()
memory_service_instance = MemoryService.get_instance()
minio_storage_instance = MinioStorageService.get_instance()
session_service_instance = SessionService.get_instance()
user_service_instance = UserService.get_instance()

__all__ = [
  "AiModelService",
  "AnalyticsService",
  "AuthService",
  "CourseService",
  "DocumentService",
  "ExtractorService",
  "FileProcessor",
  "KnowledgeBaseService",
  "MemoryService",
  "MinioStorageService",
  "SessionService",
  "UserService",
  "ai_model_service_instance",
  "analytics_service_instance",
  "auth_service_instance",
  "course_service_instance",
  "create_embedding_model",
  "document_service_instance",
  "extractor_service_instance",
  "file_processor_instance",
  "kb_service_instance",
  "memory_service_instance",
  "minio_storage_instance",
  "session_service_instance",
  "user_service_instance",
]
