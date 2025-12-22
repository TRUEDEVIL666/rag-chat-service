from fastapi_cache.decorator import cache
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.utils.auth import get_current_user
from app.core.factory import get_session_service
from app.services.session.session_service import SessionService

router = APIRouter()


@router.get("/sessions", summary="List all chat sessions")
@cache(expire=60)
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    session_service: SessionService = Depends(get_session_service),
    auth=Depends(get_current_user)
):
  user_id = auth["user_id"]
  tenant_id = auth["tenant_id"]
  access_token = auth.get("token")
  try:
    sessions = session_service.list_sessions(
      user_id, tenant_id, limit, offset, access_token)
    return sessions
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", summary="Delete a chat session")
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    auth=Depends(get_current_user)
):
  user_id = auth["user_id"]
  try:
    success = session_service.delete_session(session_id, user_id)
    if not success:
      raise HTTPException(
        status_code=404, detail="Session not found or failed to delete")
    return {"message": "Session deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
