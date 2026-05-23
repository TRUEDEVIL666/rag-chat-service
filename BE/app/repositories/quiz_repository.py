from typing import Dict, List
from uuid import UUID

from app.repositories.base_repository import BaseRepository


class QuizAttemptCreate:
  def __init__(
    self,
    bot_id: UUID,
    session_id: UUID,
    score: float,
    total_questions: int,
    quiz_data: List[Dict],
    user_answers: Dict,
    tenant_id: UUID,
    user_id: UUID,
  ):
    self.bot_id = bot_id
    self.session_id = session_id
    self.score = score
    self.total_questions = total_questions
    self.quiz_data = quiz_data
    self.user_answers = user_answers
    self.tenant_id = tenant_id
    self.user_id = user_id

  def to_dict(self):
    return {
      "bot_id": str(self.bot_id),
      "session_id": str(self.session_id),
      "score": self.score,
      "total_questions": self.total_questions,
      "quiz_data": self.quiz_data,
      "user_answers": self.user_answers,
      "tenant_id": str(self.tenant_id)
      if self.tenant_id and str(self.tenant_id) != "None"
      else None,
      "user_id": str(self.user_id),
    }


class QuizRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="quiz_attempts")

  async def create_attempt(self, attempt: QuizAttemptCreate) -> Dict:
    """Creates a new quiz attempt record."""
    try:
      result = await self.insert(attempt.to_dict())
      return result[0] if result else None
    except Exception as e:
      self.logger.error(f"Error creating quiz attempt: {e}")
      raise e

  async def get_history(
    self, user_id: UUID, tenant_id: UUID, limit: int = 20
  ) -> List[Dict]:
    """Fetches quiz history for a user."""
    try:
      client = await self._get_client()
      t_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      query = (
        client.table(self.table_name)
        .select("*, bots(name)")
        .eq("user_id", str(user_id))
        .eq("tenant_id", t_id)
        .order("created_at", desc=True)
        .limit(limit)
      )

      res = await query.execute()
      return res.data
    except Exception as e:
      self.logger.error(f"Error fetching quiz history: {e}")
      return []
