# app/api/v1/document_api.py
import json  # Added import
from fastapi import APIRouter, Depends, Path, HTTPException, Query
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
  return await service.delete_document(
      document_id=document_id,
      tenant_id=auth["tenant_id"],
      user_id=auth["user_id"],
      access_token=auth.get("token")
  )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse, summary="Get Task Status")
async def get_task_status(
    req: TaskIdRequest = Depends(),
    service=Depends(get_document_service)
):
  """
  Check the status of any document-related background task.
  """
  return await service.get_task_status(req.task_id)


@router.post("/batch-delete", summary="Batch Delete Documents")
async def batch_delete_documents(
    request: BatchDeleteRequest,
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Batch delete multiple documents.
  """
  return await service.batch_delete_documents(
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


@router.get("/{document_id}/content", summary="Get Document Content Stream")
async def get_document_content(
    document_id: str = Path(..., description="Document ID"),
    token: str = Query(None),
    # We still allow header auth, but we need to handle if it's missing manually if we want hybrid
    # Simpler: Inspect request manually or use a custom dependency.
    # For now, let's just use the query token if present, else fallback to header?
    # FastAPI doesn't easily support "OR" logic in deps without custom code.
    # Let's rely on manual token validation here since it's a special endpoint.
):
  """
  Stream the document content directly from the Backend.
  Used to avoid Mixed Content issues with MinIO.
  Supports 'token' query parameter for iframe access.
  """
  from app.utils.auth import validate_token
  from fastapi.responses import StreamingResponse
  from fastapi.security import HTTPBearer

  # Manual Auth Check
  user_auth = None

  # 1. Try Query Param
  if token:
    user_auth = validate_token(token)

  # 2. Try Header (if no token in query) but we can't easily access Depends inside body.
  # So we should have used a Depends.
  # Let's just Require the Query Param for this specific endpoint as it's generated by us.

  if not user_auth:
    raise HTTPException(
      status_code=401, detail="Authentication required (token query param)")

  # Manually instantiate since we dropped the Depends(get_document_service) to declutter signature?
  service = get_document_service()
  # Actually better to keep service injection.

  stream, filename, media_type = await service.get_document_stream(
      document_id=document_id,
      tenant_id=user_auth["tenant_id"],
      access_token=user_auth.get("token")
  )

  from urllib.parse import quote
  encoded_filename = quote(filename)
  return StreamingResponse(
      stream,
      media_type=media_type,
      headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
  )


@router.get("/{document_id}/download", summary="Get Document Download URL")
async def get_document_download_url(
    document_id: str = Path(..., description="Document ID"),
    service=Depends(get_document_service),
    auth=Depends(get_current_user)
):
  """
  Get a presigned URL to download/view the document.
  """
  # Return the relative path to the content proxy endpoint.
  # We embed the current access token to allow iframe/browser access without headers.
  token = auth.get("token")
  url = f"/api/v1/documents/{document_id}/content?token={token}"
  return {"url": url}
