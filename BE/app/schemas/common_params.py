from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
  limit: Annotated[Optional[int], Field(20, ge=1, le=100, description="Page size")] = 20
  cursor_timestamp: Annotated[
    Optional[int], Field(description="Cursor timestamp for pagination")
  ] = None
  sort_column: Annotated[Optional[str], Field(description="Sort column")] = "created_at"
  sort_desc: Annotated[Optional[bool], Field(description="Sort descending")] = True


class UserSearchParams(BaseModel):
  query: Optional[str] = None
  role: Optional[str] = None
  tenant_id: Optional[str] = None
  date_from: Optional[datetime] = None
  date_to: Optional[datetime] = None
