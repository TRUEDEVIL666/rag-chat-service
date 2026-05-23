from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
  message: str


class BaseResponse(BaseModel, Generic[T]):
  """
  Standard API response wrapper.
  """

  success: bool = True
  data: Optional[T] = None
  message: Optional[str] = None
  error: Optional[str] = None
