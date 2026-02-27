from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class KnowledgeBaseCreateRequest(BaseModel):
  name: str
  description: Optional[str] = None


class KnowledgeBaseItem(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  permission: Optional[str] = None
  indexing_technique: Optional[str] = None
  document_count: int = 0
  created_at: int
  updated_at: int
  embedding_model: Optional[str] = None
  embedding_model_id: Optional[UUID] = None
  embedding_provider_id: Optional[UUID] = None
  embedding_model_provider: Optional[str] = None
  embedding_available: bool = False
  retrieval_model: Optional[Dict[str, Any]] = None


class KnowledgeBaseListResponse(BaseModel):
  data: List[KnowledgeBaseItem]
  has_more: bool
  limit: int
  total: int
  page: int


class RetrievalModel(BaseModel):
  search_method: str = "semantic"
  auto_merging: bool = False


class KnowledgeBaseInput(BaseModel):
  name: str
  description: str = Field(..., min_length=1)
  indexing_technique: Optional[str] = None
  permission: Optional[str] = None
  embedding_provider_id: Optional[UUID] = None
  embedding_model_id: Optional[UUID] = None
  retrieval_model: Optional[RetrievalModel] = None
  partial_member_list: Optional[List[str]] = None


class KnowledgeBaseResponse(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  retrieval_model: Optional[RetrievalModel] = None


class RetrievalModelSchema(BaseModel):
  search_method: str
  auto_merging: bool


class KnowledgeBaseDetail(BaseModel):
  id: UUID
  name: str
  description: Optional[str] = None
  permission: Optional[str] = None
  indexing_technique: Optional[str] = None
  document_count: int
  created_by: Optional[str] = None
  created_at: str
  updated_by: Optional[str] = None
  updated_at: str
  embedding_model: Optional[str] = None
  retrieval_model: Optional[RetrievalModelSchema] = None
  doc_form: Optional[str] = None


class UpdateRetrievalModel(BaseModel):
  search_method: Optional[str] = None
  auto_merging: Optional[bool] = None


class UpdateKnowledgeBaseRequest(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  indexing_technique: Optional[str] = None
  permission: Optional[str] = None
  embedding_provider_id: Optional[UUID] = None
  embedding_model_id: Optional[UUID] = None
  retrieval_model: Optional[UpdateRetrievalModel] = None
  partial_member_list: Optional[List[str]] = None
