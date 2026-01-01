from typing import Annotated, Optional
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
  limit: Annotated[
    Optional[int],
    Field(100, ge=1, le=100, description="Page size")
  ] = 100
  cursor_timestamp: Annotated[
    Optional[int],
    Field(description="Cursor timestamp for pagination")
  ] = None
  sort_column: Annotated[
    Optional[str],
    Field(description="Sort column")
  ] = "created_at"
  sort_desc: Annotated[
    Optional[bool],
    Field(description="Sort descending")
  ] = True
