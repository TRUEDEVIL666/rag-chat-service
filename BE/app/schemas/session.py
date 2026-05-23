from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import Path, Query
from pydantic import BaseModel
from pydantic.fields import Field

from app.schemas.common_params import PaginationParams


class BotSimpleResponse(BaseModel):
  name: str

  class Config:
    from_attributes = True


class SessionCreateRequest(BaseModel):
  bot_id: UUID


class SessionResponse(BaseModel):
  id: UUID
  user_id: UUID
  bot_id: UUID
  created_at: datetime
  updated_at: datetime
  started_at: Optional[datetime] = None
  is_transfer_agent: Optional[bool] = False
  summary_text: Optional[str] = None
  tenant_id: Optional[UUID] = None
  bots: Optional[BotSimpleResponse] = None

  class Config:
    from_attributes = True


class SessionListRequest(PaginationParams):
  bot_id: Annotated[Optional[UUID], Query(description="Filter by Bot ID")] = None
  search: Annotated[Optional[str], Query(description="Search by summary or title")] = (
    None
  )
  start_date: Annotated[
    Optional[datetime], Query(description="Filter by start date")
  ] = None
  end_date: Annotated[Optional[datetime], Query(description="Filter by end date")] = (
    None
  )


class SessionIdRequest(BaseModel):
  session_id: Annotated[UUID, Path(description="Session ID")]


class ChatMessageResponse(BaseModel):
  id: UUID
  session_id: UUID
  content: str
  role: str
  created_at: datetime
  sender_id: Optional[UUID] = None
  rating: Optional[str] = None


class ChatMessageListResponse(BaseModel):
  items: List[ChatMessageResponse]
  total: int
  limit: int
  next_cursor: Optional[int] = None


class SessionMessagesRequest(BaseModel):
  session_id: Annotated[UUID, Path(description="Session ID")]


class MessageRatingRequest(BaseModel):
  rating: Optional[str] = Field(
    None, description="Rating type: 'thumbs_up', 'thumbs_down', or None to clear"
  )
