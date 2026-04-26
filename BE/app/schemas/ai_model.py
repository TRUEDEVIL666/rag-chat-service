from pydantic import BaseModel
from fastapi import Query, Path
from typing import Optional
from uuid import UUID
from datetime import datetime


class AiProviderResponse(BaseModel):
  id: UUID
  name: str
  display_name: str
  base_url: Optional[str] = None
  is_active: bool
  created_at: datetime
  secret_id: Optional[UUID] = None  # To check if key is set


class AiModelResponse(BaseModel):
  id: UUID
  provider_id: UUID
  model_id: str
  name: str
  model_type: str
  is_active: bool
  created_at: datetime


class AiModelProviderRequest(BaseModel):
  provider_id: UUID = Path(..., description="Provider ID")
  model_type: Optional[str] = Query(
    None, description="Filter by model type (chat, reranker)"
  )


class AiModelTypeRequest(BaseModel):
  model_type: str = Path(..., description="Model Type (chat, reranker)")


class AiProviderCreate(BaseModel):
  name: str
  display_name: str
  base_url: Optional[str] = None
  api_key: Optional[str] = None  # Optional, but often needed
  is_active: bool = True


class AiProviderUpdate(BaseModel):
  name: Optional[str] = None
  display_name: Optional[str] = None
  base_url: Optional[str] = None
  api_key: Optional[str] = None
  is_active: Optional[bool] = None


class AiModelCreate(BaseModel):
  provider_id: UUID
  model_id: str
  name: str
  model_type: str = "chat"  # chat, reranker, embedding
  is_active: bool = True


class AiModelUpdate(BaseModel):
  model_id: Optional[str] = None
  name: Optional[str] = None
  model_type: Optional[str] = None
  is_active: Optional[bool] = None
