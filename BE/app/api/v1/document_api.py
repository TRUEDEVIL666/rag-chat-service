# app/api/v1/document_api.py
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import DocumentServiceDep
from app.core.logger import get_logger
from app.schemas.common import BaseResponse
from app.schemas.document import (
  BatchDeleteRequest,
  DocumentUpdateRequest,
  FileUploadRequest,
  FileUploadResponse,
  TaskIdRequest,
  TaskStatusResponse,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post(
  "/",
  response_model=BaseResponse[FileUploadResponse],
  summary="Upload New Document(s)",
)
async def upload_documents(
  request: Annotated[FileUploadRequest, Depends()],
  document_service: DocumentServiceDep,
):
  """
  Upload one or more documents to a knowledge base.
  """
  chunk_params = json.loads(request.chunking_params) if request.chunking_params else {}
  result = await document_service.upload_documents(
    kb_id=request.knowledge_base_id,
    files=request.files,
    chunking_method=request.chunking_method,
    enable_extraction=request.enable_extraction,
    **chunk_params,
  )
  return BaseResponse(data=result)


@router.put(
  "/{document_id}",
  response_model=BaseResponse[dict],
  summary="Update Existing Document",
)
async def update_document(
  document_id: Annotated[str, Path(description="Document ID")],
  request: Annotated[DocumentUpdateRequest, Depends()],
  document_service: DocumentServiceDep,
):
  """
  Update a specific document using incremental sync.
  """
  chunk_params = json.loads(request.chunking_params) if request.chunking_params else {}
  result = await document_service.update_document(
    document_id=document_id,
    file=request.file,
    chunking_method=request.chunking_method,
    enable_extraction=request.enable_extraction,
    **chunk_params,
  )
  return BaseResponse(data=result)


@router.delete(
  "/{document_id}", response_model=BaseResponse[dict], summary="Delete Document"
)
async def delete_document(
  document_id: Annotated[str, Path(description="Document ID")],
  document_service: DocumentServiceDep,
):
  """
  Hard delete a document and all related artifacts (file, vectors, metadata).
  """
  result = await document_service.delete_document(document_id=document_id)
  return BaseResponse(data=result)


@router.get(
  "/tasks/{task_id}",
  response_model=BaseResponse[TaskStatusResponse],
  summary="Get Task Status",
)
async def get_task_status(
  req: Annotated[TaskIdRequest, Depends()],
  document_service: DocumentServiceDep,
):
  """
  Check the status of any document-related background task.
  """
  result = await document_service.get_task_status(req.task_id)
  return BaseResponse(data=result)


@router.post(
  "/batch-delete", response_model=BaseResponse[dict], summary="Batch Delete Documents"
)
async def batch_delete_documents(
  request: BatchDeleteRequest,
  document_service: DocumentServiceDep,
):
  """
  Batch delete multiple documents.
  """
  result = await document_service.batch_delete_documents(doc_ids=request.ids)
  return BaseResponse(data=result)


@router.post(
  "/{document_id}/retry",
  response_model=BaseResponse[dict],
  summary="Retry Document Processing",
)
async def retry_document(
  document_id: Annotated[str, Path(description="Document ID")],
  document_service: DocumentServiceDep,
):
  """
  Retry processing for a failed document.
  """
  result = await document_service.retry_document_processing(document_id=document_id)
  return BaseResponse(data=result)


@router.get("/{document_id}/content", summary="Get Document Content Stream")
async def get_document_content(
  document_id: Annotated[str, Path(description="Document ID")],
  document_service: DocumentServiceDep,
  token: Annotated[str | None, Query()] = None,
):
  """
  Stream the document content directly from the Backend.
  """
  from app.core.context import set_auth_context
  from app.utils.auth import validate_token

  # Manual Auth Check for iframe/proxy access
  user_auth = None
  if token:
    user_auth = await validate_token(token)

  if not user_auth:
    raise HTTPException(
      status_code=401, detail="Authentication required (token query param)"
    )

  # MANUALLY POPULATE CONTEXT because we bypassed the dependency
  set_auth_context(user_auth)

  stream, filename, media_type = await document_service.get_document_stream(
    document_id=document_id
  )

  from urllib.parse import quote

  encoded_filename = quote(filename)
  return StreamingResponse(
    stream,
    media_type=media_type,
    headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"},
  )


@router.get(
  "/{document_id}/download",
  response_model=BaseResponse[dict],
  summary="Get Document Download URL",
)
async def get_document_download_url(
  document_id: Annotated[str, Path(description="Document ID")],
):
  """
  Get a proxy URL to download/view the document via content endpoint.
  """
  from app.core.context import get_current_token

  token = get_current_token()
  url = f"/api/v1/documents/{document_id}/content?token={token}"
  return BaseResponse(data={"url": url})
