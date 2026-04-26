from app.schemas.common import MessageResponse
from app.schemas.common_params import PaginationParams
from app.schemas.session import (
  SessionResponse,
  SessionListRequest,
  SessionIdRequest,
  ChatMessageListResponse,
  SessionMessagesRequest,
  MessageRatingRequest,
)
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services import session_service_instance
from datetime import datetime

router = APIRouter()


@router.get(
  "/sessions", summary="List all chat sessions", response_model=List[SessionResponse]
)
async def list_sessions(
  req: SessionListRequest = Depends(),
):
  try:
    sessions = await session_service_instance.list_sessions(
      limit=req.limit,
      cursor_timestamp=req.cursor_timestamp,
      bot_id=str(req.bot_id) if req.bot_id else None,
      search=req.search,
      start_date=req.start_date,
      end_date=req.end_date,
    )
    return sessions
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get(
  "/sessions/{session_id}/messages",
  summary="List chat messages for a session",
  response_model=ChatMessageListResponse,
)
async def get_messages(
  req: SessionMessagesRequest = Depends(),
  pagination: PaginationParams = Depends(),
):
  try:
    messages = await session_service_instance.get_chat_messages(
      session_id=str(req.session_id),
      limit=pagination.limit,
      cursor_timestamp=pagination.cursor_timestamp,
      sort_column=pagination.sort_column,
      sort_desc=pagination.sort_desc,
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
      next_cursor=next_cursor,
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get(
  "/sessions/{session_id}",
  summary="Get session details",
  response_model=SessionResponse,
)
async def get_session_details(
  req: SessionIdRequest = Depends(),
):
  try:
    session = await session_service_instance.get_session(str(req.session_id))
    if not session:
      raise HTTPException(status_code=404, detail="Session not found")
    return session
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete(
  "/sessions/{session_id}",
  summary="Delete a chat session",
  response_model=MessageResponse,
)
async def delete_session(
  req: SessionIdRequest = Depends(),
):
  try:
    success = await session_service_instance.delete_session(str(req.session_id))
    if not success:
      raise HTTPException(
        status_code=404, detail="Session not found or failed to delete"
      )

    return {"message": "Session deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post(
  "/messages/{message_id}/rate",
  summary="Rate a chat message",
  response_model=MessageResponse,
)
async def rate_message(
  message_id: str,
  req: MessageRatingRequest,
):
  try:
    success = await session_service_instance.update_message_rating(
      message_id, req.rating
    )
    if not success:
      raise HTTPException(
        status_code=404, detail="Message not found or failed to update rating"
      )

    return MessageResponse(message="Rating updated successfully")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
