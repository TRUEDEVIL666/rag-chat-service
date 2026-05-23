from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
  question: str = Field(description="The question text")
  options: List[str] = Field(description="List of 4 options", min_items=4, max_items=4)
  correct_answer: int = Field(description="Index (0-3) of the correct option")


class QuizOutput(BaseModel):
  quiz: List[QuizQuestion] = Field(
    description="A list of multiple choice questions to test the user's knowledge based on the context."
  )


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
