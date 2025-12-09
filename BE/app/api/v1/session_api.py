from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.core.factory import get_session_service
from app.schemas.session import SessionResponse, SessionCreateRequest

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, summary="Create a new session")
async def create_session(
  body: SessionCreateRequest,
  session_service=Depends(get_session_service),
  auth=Depends(get_current_user)
):
  try:
    session = session_service.create_session(
      user_id=str(auth["user_id"]),
      bot_id=str(body.bot_id),
      tenant_id=str(auth.get("tenant_id")) if auth.get("tenant_id") else None
    )
    return session
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
