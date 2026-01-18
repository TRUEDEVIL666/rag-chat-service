from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime


class QuizAttemptRequest(BaseModel):
  bot_id: UUID
  session_id: UUID
  score: float
  total_questions: int
  quiz_data: List[Dict[str, Any]]
  user_answers: Dict[str, Any]


class QuizHistoryItem(BaseModel):
  id: UUID
  bot_id: UUID
  bot_name: Optional[str] = None
  session_id: Optional[UUID] = None
  score: float
  total_questions: int
  created_at: datetime
  # We might not send full quiz data in list view, but having it is fine for now


class QuizLogResponse(BaseModel):
  id: UUID
  status: str = "saved"
