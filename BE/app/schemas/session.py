from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from uuid import UUID


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
