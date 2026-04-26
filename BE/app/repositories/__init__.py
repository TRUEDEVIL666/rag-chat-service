from app.core.supabase_client import get_async_supabase_client
from .ai_model_repository import AiModelRepository
from .bot_repository import BotRepository
from .chat_message_repository import (
  ChatMessageRepository,
  CustomPostgresChatMessageHistory,
)
from .class_repository import ClassRepository
from .course_repository import CourseRepository
from .document_repository import DocumentRepository
from .graph_chunk_repository import GraphChunkRepository
from .graph_edge_repository import GraphEdgeRepository
from .graph_entity_repository import GraphEntityRepository
from .knowledge_base_repository import KnowledgeBaseRepository
from .quiz_repository import QuizRepository, QuizAttemptCreate
from .semester_repository import SemesterRepository
from .session_repository import SessionRepository
from .session_summary_repository import SessionSummaryRepository
from .tenant_repository import TenantRepository
from .user_repository import UserRepository
from .vector_repository import VectorRepository

# Initialize repo instances
ai_model_repo_instance = AiModelRepository.get_instance()
bot_repo_instance = BotRepository.get_instance()
chat_message_repo_instance = ChatMessageRepository.get_instance()
class_repo_instance = ClassRepository.get_instance()
course_repo_instance = CourseRepository.get_instance()
document_repo_instance = DocumentRepository.get_instance()
graph_chunk_repo_instance = GraphChunkRepository.get_instance()
graph_edge_repo_instance = GraphEdgeRepository.get_instance()
graph_entity_repo_instance = GraphEntityRepository.get_instance()
kb_repo_instance = KnowledgeBaseRepository.get_instance()
quiz_repo_instance = QuizRepository.get_instance()
semester_repo_instance = SemesterRepository.get_instance()
session_repo_instance = SessionRepository.get_instance()
session_summary_repo_instance = SessionSummaryRepository.get_instance()
tenant_repo_instance = TenantRepository.get_instance()
user_repo_instance = UserRepository.get_instance()
vector_repo_instance = VectorRepository.get_instance()

__all__ = [
  "get_async_supabase_client",
  "AiModelRepository",
  "ai_model_repo_instance",
  "BotRepository",
  "bot_repo_instance",
  "ChatMessageRepository",
  "chat_message_repo_instance",
  "CustomPostgresChatMessageHistory",
  "ClassRepository",
  "class_repo_instance",
  "CourseRepository",
  "course_repo_instance",
  "DocumentRepository",
  "document_repo_instance",
  "GraphChunkRepository",
  "graph_chunk_repo_instance",
  "GraphEdgeRepository",
  "graph_edge_repo_instance",
  "GraphEntityRepository",
  "graph_entity_repo_instance",
  "KnowledgeBaseRepository",
  "kb_repo_instance",
  "QuizRepository",
  "quiz_repo_instance",
  "QuizAttemptCreate",
  "SemesterRepository",
  "semester_repo_instance",
  "SessionRepository",
  "session_repo_instance",
  "SessionSummaryRepository",
  "session_summary_repo_instance",
  "TenantRepository",
  "tenant_repo_instance",
  "UserRepository",
  "user_repo_instance",
  "VectorRepository",
  "vector_repo_instance",
]
