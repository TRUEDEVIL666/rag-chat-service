from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.utils.auth import get_current_user
from app.core.factory import get_session_service
from app.services.session.session_service import SessionService

router = APIRouter()


@router.get("/sessions", summary="List all chat sessions")
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    session_service: SessionService = Depends(get_session_service),
    auth=Depends(get_current_user)
):
  user_id = auth["user_id"]
  tenant_id = auth["tenant_id"]
  try:
    sessions = session_service.list_sessions(user_id, tenant_id, limit, offset)
    return sessions
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
