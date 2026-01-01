from datetime import datetime
from typing import Annotated, Optional, List
from uuid import UUID
from fastapi import Path, Query
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
  bot_id: UUID


class SessionResponse(BaseModel):
  id: UUID
  user_id: UUID
  bot_id: UUID
  created_at: datetime
  updated_at: datetime
  started_at: Optional[datetime] = None
  is_closed: Optional[bool] = False
  is_transfer_agent: Optional[bool] = False
  summary_text: Optional[str] = None
  tenant_id: Optional[UUID] = None

  class Config:
    from_attributes = True


class SessionListRequest(BaseModel):
  limit: Annotated[
    Optional[int],
    Field(100, ge=1, le=100, description="Page size")
  ] = 100
  cursor_timestamp: Annotated[
    Optional[int],
    Field(description="Cursor timestamp for pagination")
  ] = None
  bot_id: Annotated[
    Optional[UUID],
    Query(description="Filter by Bot ID")
  ] = None


class SessionIdRequest(BaseModel):
  session_id: Annotated[UUID, Path(description="Session ID")]


class ChatMessageResponse(BaseModel):
  id: UUID
  session_id: UUID
  content: str
  role: str
  created_at: datetime
  sender_id: Optional[UUID] = None


class ChatMessageListResponse(BaseModel):
  items: List[ChatMessageResponse]
  total: int
  limit: int
  next_cursor: Optional[int] = None


class SessionMessagesRequest(BaseModel):
  session_id: Annotated[UUID, Path(description="Session ID")]
