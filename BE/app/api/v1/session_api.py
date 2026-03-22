from app.schemas.common import MessageResponse
from app.schemas.common_params import PaginationParams
from app.schemas.session import (
    SessionResponse, SessionListRequest, SessionIdRequest,
    ChatMessageListResponse, SessionMessagesRequest, MessageRatingRequest
)
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.utils.auth import get_current_user
from app.core.factory import get_session_service
from app.services.session.session_service import SessionService
from datetime import datetime

router = APIRouter()


@router.get("/sessions", summary="List all chat sessions", response_model=List[SessionResponse])
async def list_sessions(
    req: SessionListRequest = Depends(),
    session_service: SessionService = Depends(get_session_service),
    auth=Depends(get_current_user)
):
  user_id = auth["user_id"]
  tenant_id = auth["tenant_id"]
  access_token = auth.get("token")
  try:
    sessions = await session_service.list_sessions(
      user_id=user_id,
      tenant_id=tenant_id,
      limit=req.limit,
      cursor_timestamp=req.cursor_timestamp,
      access_token=access_token,
      bot_id=str(req.bot_id) if req.bot_id else None,
      search=req.search,
      start_date=req.start_date,
      end_date=req.end_date
    )
    return sessions
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", summary="List chat messages for a session", response_model=ChatMessageListResponse)
async def get_messages(
    req: SessionMessagesRequest = Depends(),
    pagination: PaginationParams = Depends(),
    session_service: SessionService = Depends(get_session_service),
    auth: dict = Depends(get_current_user)
):
  try:
    messages = await session_service.get_chat_messages(
        session_id=str(req.session_id),
        limit=pagination.limit,
        cursor_timestamp=pagination.cursor_timestamp,
        sort_column=pagination.sort_column,
        sort_desc=pagination.sort_desc,
        access_token=auth["token"]
    )

    if messages:
      last_msg_time = messages[-1]["created_at"]
      if isinstance(last_msg_time, str):
        last_msg_time = datetime.fromisoformat(last_msg_time)
      next_cursor = int(last_msg_time.timestamp())
    else:
      next_cursor = None

    return ChatMessageListResponse(
        items=messages,
        total=len(messages),
        limit=pagination.limit,
        next_cursor=next_cursor
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", summary="Get session details", response_model=SessionResponse)
async def get_session_details(
    req: SessionIdRequest = Depends(),
    session_service: SessionService = Depends(get_session_service),
    auth=Depends(get_current_user)
):
  try:
    session = await session_service.get_session(
      str(req.session_id), access_token=auth.get("token"))
    if not session:
      raise HTTPException(status_code=404, detail="Session not found")
    return session
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", summary="Delete a chat session", response_model=MessageResponse)
async def delete_session(
    req: SessionIdRequest = Depends(),
    session_service: SessionService = Depends(get_session_service),
    auth=Depends(get_current_user)
):
  user_id = auth["user_id"]
  try:
    success = await session_service.delete_session(
      str(req.session_id), user_id, access_token=auth.get("token"))
    if not success:
      raise HTTPException(
        status_code=404, detail="Session not found or failed to delete")

    return {"message": "Session deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/rate", summary="Rate a chat message", response_model=MessageResponse)
async def rate_message(
    message_id: str,
    req: MessageRatingRequest,
    session_service: SessionService = Depends(get_session_service),
    auth: dict = Depends(get_current_user)
):
  try:
    success = await session_service.update_message_rating(
        message_id,
        req.rating,
        access_token=auth["token"]
    )
    if not success:
      raise HTTPException(
          status_code=404, detail="Message not found or failed to update rating")

    return MessageResponse(message="Rating updated successfully")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
