from typing import Dict, List
from uuid import UUID

from app.repositories.quiz_repository import QuizAttemptCreate


class QuizService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "QuizService":
    if cls._instance is None:
      from app.repositories import QuizRepository

      cls._instance = cls(quiz_repo_instance=QuizRepository.get_instance())
    return cls._instance

  def __init__(self, quiz_repo_instance):
    self.quiz_repo_instance = quiz_repo_instance

  async def create_attempt(self, attempt: QuizAttemptCreate) -> Dict:
    return await self.quiz_repo_instance.create_attempt(attempt)

  async def get_history(
    self, user_id: UUID, tenant_id: UUID, limit: int = 20
  ) -> List[Dict]:
    return await self.quiz_repo_instance.get_history(user_id, tenant_id, limit)
