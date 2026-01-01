# app/api/v1/document_api.py
import json  # Added import
from fastapi import APIRouter, Depends, Path, HTTPException
from app.core.logger import get_logger
from app.utils.auth import get_current_user
from app.core.factory import get_document_service
from app.schemas.document import (
    FileUploadResponse, FileUploadRequest,
    TaskStatusResponse, TaskIdRequest,
    DocumentUpdateRequest, BatchDeleteRequest
)


router = APIRouter()
logger = get_logger("document_api")


@router.post("/", response_model=FileUploadResponse, summary="Upload New Document(s)")
async def upload_documents(
    request: FileUploadRequest = Depends(),
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Upload one or more documents to a knowledge base.
  Automatically performs upsert if file exists in the same KB.
  """
  chunk_params = json.loads(
    request.chunking_params) if request.chunking_params else {}
  return await service.upload_documents(
      kb_id=request.knowledge_base_id,
      files=request.files,
      tenant_id=auth["tenant_id"],
      user_id=auth["user_id"],
      access_token=auth.get("token"),
      chunking_method=request.chunking_method,
      use_sparse=request.use_sparse,
      **chunk_params
  )


@router.put("/{document_id}", summary="Update Existing Document")
async def update_document(
    document_id: str = Path(..., description="Document ID"),
    request: DocumentUpdateRequest = Depends(),
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Update a specific document using incremental sync.
  """
  chunk_params = json.loads(
    request.chunking_params) if request.chunking_params else {}
  return await service.update_document(
      document_id=document_id,
      file=request.file,
      tenant_id=auth["tenant_id"],
      user_id=auth["user_id"],
      access_token=auth.get("token"),
      chunking_method=request.chunking_method,
      use_sparse=request.use_sparse,
      **chunk_params
  )


@router.delete("/{document_id}", summary="Delete Document")
async def delete_document(
    document_id: str = Path(..., description="Document ID"),
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Hard delete a document and all related artifacts (file, vectors, metadata).
  """
  return service.delete_document(
      document_id=document_id,
      tenant_id=auth["tenant_id"],
      user_id=auth["user_id"],
      access_token=auth.get("token")
  )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, summary="Get Task Status")
def get_task_status(
    req: TaskIdRequest = Depends(),
    service=Depends(get_document_service)
):
  """
  Check the status of any document-related background task.
  """
  return service.get_task_status(req.task_id)


@router.post("/batch-delete", summary="Batch Delete Documents")
async def batch_delete_documents(
    request: BatchDeleteRequest,
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Batch delete multiple documents.
  """
  return service.batch_delete_documents(
      doc_ids=request.ids,
      tenant_id=auth["tenant_id"],
      user_id=auth["user_id"],
      access_token=auth.get("token")
  )


@router.post("/{document_id}/retry", summary="Retry Document Processing")
async def retry_document(
    document_id: str = Path(..., description="Document ID"),
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Retry processing for a failed document.
  """
  return await service.retry_document_processing(
      document_id=document_id,
      tenant_id=auth["tenant_id"],
      user_id=auth["user_id"],
      access_token=auth.get("token")
  )
