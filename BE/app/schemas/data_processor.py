from typing import List, Any, Optional
from pydantic import BaseModel
from dataclasses import dataclass
from fastapi import Form, File, UploadFile


@dataclass
class FileUploadRequest:
  knowledge_base_id: str = Form(...)
  files: List[UploadFile] = File(...)
  chunking_method: str = Form("sentence")
  use_sparse: bool = Form(True)


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
