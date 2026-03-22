from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.services.supabase.quiz_repository import QuizRepository, QuizAttemptCreate
from app.core.factory import get_quiz_repository
from app.utils.auth import get_current_user
from app.schemas.quiz import QuizAttemptRequest, QuizLogResponse
from uuid import UUID

router = APIRouter()


@router.post("/submit", response_model=QuizLogResponse)
async def submit_quiz_attempt(
    request: QuizAttemptRequest,
    current_user: Dict = Depends(get_current_user),  # Ensures auth
    repo: QuizRepository = Depends(get_quiz_repository)
):
  """
  Submit a quiz attempt.
  """
  try:
    user_id = UUID(current_user["user_id"])
    token = current_user.get("token")
    # Should be in user dict or metadata
    tenant_id = UUID(current_user.get("tenant_id"))

    # Current user object structure verification might be needed, assuming standard Supabase user dict
    # If tenant_id missing, we might need to fallback or error.
    # usually app_metadata has tenant_id.
    if not tenant_id and "app_metadata" in current_user:
      tenant_id_str = current_user["app_metadata"].get("tenant_id")
      if tenant_id_str:
        tenant_id = UUID(tenant_id_str)

    if not tenant_id:
      # Fallback: check user metadata
      if "user_metadata" in current_user:
        tenant_id_str = current_user["user_metadata"].get("tenant_id")
        if tenant_id_str:
          tenant_id = UUID(tenant_id_str)

    if not tenant_id:
      raise HTTPException(
        status_code=400, detail="Tenant ID not found for user")

    attempt = QuizAttemptCreate(
        bot_id=request.bot_id,
        session_id=request.session_id,
        score=request.score,
        total_questions=request.total_questions,
        quiz_data=request.quiz_data,
        user_answers=request.user_answers,
        tenant_id=tenant_id,
        user_id=user_id
    )

    result = await repo.create_attempt(attempt, access_token=token)
    if result:
      return QuizLogResponse(id=UUID(result["id"]), status="saved")
    else:
      raise HTTPException(status_code=500, detail="Failed to save attempt")

  except Exception as e:
    print(f"Error submitting quiz: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[Dict])
async def get_quiz_history(
    limit: int = 20,
    current_user: Dict = Depends(get_current_user),
    repo: QuizRepository = Depends(get_quiz_repository)
):
  """
  Get quiz history for the current user.
  """
  try:
    user_id = UUID(current_user["user_id"])
    token = current_user.get("token")
    # Tenant resolution (duplicate logic, could be in deps but fine here for now)
    tenant_id: Any = current_user.get("tenant_id")
    if not tenant_id and "app_metadata" in current_user:
      tenant_id = current_user["app_metadata"].get("tenant_id")
    if not tenant_id and "user_metadata" in current_user:
      tenant_id = current_user["user_metadata"].get("tenant_id")

    if tenant_id:
      tenant_id = UUID(str(tenant_id))
    else:
      raise HTTPException(status_code=400, detail="Tenant ID not found")

    history = await repo.get_history(user_id, tenant_id, limit, access_token=token)
    return history
  except Exception as e:
    print(f"Error getting history: {e}")
    raise HTTPException(status_code=500, detail=str(e))
