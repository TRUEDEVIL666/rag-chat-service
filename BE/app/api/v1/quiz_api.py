from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.dependencies import QuizServiceDep
from app.core.logger import get_logger
from app.repositories import QuizAttemptCreate
from app.schemas.quiz import QuizAttemptRequest, QuizLogResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/submit", response_model=QuizLogResponse)
async def submit_quiz_attempt(
  request: QuizAttemptRequest,
  quiz_service: QuizServiceDep,
):
  """
  Submit a quiz attempt.
  """
  from app.core.context import get_current_tenant_id, get_current_user_id

  try:
    user_id = get_current_user_id()
    tenant_id = get_current_tenant_id()

    if not tenant_id:
      raise HTTPException(status_code=400, detail="Tenant ID not found for user")

    attempt = QuizAttemptCreate(
      bot_id=request.bot_id,
      session_id=request.session_id,
      score=request.score,
      total_questions=request.total_questions,
      quiz_data=request.quiz_data,
      user_answers=request.user_answers,
      tenant_id=UUID(tenant_id),
      user_id=UUID(user_id),
    )

    result = await quiz_service.create_attempt(attempt)
    if result:
      return QuizLogResponse(id=UUID(result["id"]), status="saved")
    else:
      raise HTTPException(status_code=500, detail="Failed to save attempt")

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error submitting quiz: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[Dict])
async def get_quiz_history(
  quiz_service: QuizServiceDep,
  limit: int = 20,
):
  """
  Get quiz history for the current user.
  """
  from app.core.context import get_current_tenant_id, get_current_user_id

  try:
    user_id = get_current_user_id()
    tenant_id = get_current_tenant_id()

    if not tenant_id:
      raise HTTPException(status_code=400, detail="Tenant ID not found")

    history = await quiz_service.get_history(UUID(user_id), UUID(tenant_id), limit)
    return history
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error getting history: {e}")
    raise HTTPException(status_code=500, detail=str(e))
