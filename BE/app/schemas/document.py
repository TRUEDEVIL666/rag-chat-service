from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import File, Form, Path, UploadFile
from pydantic import BaseModel


class DocumentItem(BaseModel):
  id: UUID
  name: str
  path: Optional[str] = None
  status: Optional[str] = None
  knowledgebase_id: UUID
  tenant_id: Optional[UUID] = None
  created_by: Optional[UUID] = None
  creator: Optional[Dict[str, Any]] = None
  created_at: datetime
  updated_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
  data: List[DocumentItem]
  total: int


@dataclass
class DocumentUpdateRequest:
  file: UploadFile = File(...)
  chunking_method: str = Form("sentence")
  chunking_params: Optional[str] = Form(None)
  enable_extraction: bool = Form(True)


@dataclass
class FileUploadRequest:
  knowledge_base_id: str = Form(...)
  files: List[UploadFile] = File(...)
  chunking_method: str = Form("sentence")
  chunking_params: Optional[str] = Form(None)
  enable_extraction: bool = Form(True)


class FileUploadResult(BaseModel):
  filename: str
  task_id: str
  status: str


class FileUploadResponse(BaseModel):
  files_queued: int
  results: List[FileUploadResult]


class TaskStatusResponse(BaseModel):
  task_id: str
  status: str
  result: Optional[Any] = None
  message: Optional[str] = None


class TaskIdRequest(BaseModel):
  task_id: str = Path(..., description="Celery Task ID")


class BatchDeleteRequest(BaseModel):
  ids: List[UUID]
