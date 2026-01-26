from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.services.supabase.supabase_client import get_async_supabase_client


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
      user_id: UUID
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
        "tenant_id": str(self.tenant_id),
        "user_id": str(self.user_id)
    }


class QuizRepository:
  async def create_attempt(self, attempt: QuizAttemptCreate, access_token: str = None) -> Dict:
    """
    Creates a new quiz attempt record.
    """
    client = await get_async_supabase_client(access_token)
    data = attempt.to_dict()

    try:
      res = await client.table("quiz_attempts").insert(data).execute()
      if res.data and len(res.data) > 0:
        return res.data[0]
      return None
    except Exception as e:
      print(f"Error creating quiz attempt: {e}")
      raise e

  async def get_history(self, user_id: UUID, tenant_id: UUID, limit: int = 20, access_token: str = None) -> List[Dict]:
    """
    Fetches quiz history for a user.
    """
    client = await get_async_supabase_client(access_token)

    try:
      # We want to fetch user's attempts. RLS handles the user_id check implicitly if token is valid,
      # but we filter explicitly for safety/clarity.
      query = client.table("quiz_attempts")\
          .select("*, bots(name)")\
          .eq("user_id", str(user_id))\
          .eq("tenant_id", str(tenant_id))\
          .order("created_at", desc=True)\
          .limit(limit)

      res = await query.execute()
      return res.data
    except Exception as e:
      print(f"Error fetching quiz history: {e}")
      return []
