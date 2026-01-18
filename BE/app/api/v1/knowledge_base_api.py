# app/api/v1/knowledge_base.py
from app.schemas.common import MessageResponse
from fastapi_cache.decorator import cache
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body

from app.core.logger import get_logger
from app.core.factory import get_knowledge_base_service
from fastapi.security import HTTPAuthorizationCredentials

from app.utils.auth import get_current_user, security

from app.helper.utils_kb import INDEX_MAP, PERM_MAP, api_to_db_retrieval, db_to_api_retrieval, to_epoch
from app.schemas.knowledge_base import (
    KnowledgeBaseDetail, KnowledgeBaseInput, KnowledgeBaseItem,
    KnowledgeBaseResponse, KnowledgeBaseListResponse,
    RetrievalModeSchema, RetrievalModel, RetrievalModelSchema, UpdateKnowledgeBaseRequest
)
from app.schemas.document import DocumentListResponse, DocumentItem

logger = get_logger("kb_api")
router = APIRouter()


def _to_epoch(ts) -> int:
  if not ts:
    return 0
  if isinstance(ts, str):
    try:
      return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    except Exception:
      return 0
  if isinstance(ts, datetime):
    return int(ts.timestamp())
  return 0


@router.get(
    "/knowledge_bases",
    # response_model=KnowledgeBaseListResponse,
    summary="Get Knowledge Base List",
    description="Retrieves a list of knowledge bases, with options for pagination and filtering."
)
@cache(expire=60)
def list_knowledge_bases(
    # keyword: Optional[str] = Query(None, description="Search keyword to filter by name"),
    # tag_ids: Optional[List[str]] = Query(None, description="List of tag IDs (ALL-of filtering)"),
    # page: int = Query(1, ge=1, description="Page number"),
    # limit: int = Query(20, ge=1, le=100, description="Items per page"),
    # include_all: bool = Query(False, description="Only effective for workspace owners"),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  try:
    tenant_id = auth["tenant_id"]
    is_owner = bool(auth.get("is_owner", False))

    rows, total = kb_service.list_knowledge_bases(
        tenant_id=tenant_id,
        access_token=auth.get("token")
    )

    data = []
    for r in rows:
      data.append(KnowledgeBaseItem(
          id=str(r["id"]),
          name=r["name"],
          description=r.get("description"),
          permission=r.get("permission"),
          indexing_technique=r.get("indexing_technique"),
          document_count=r.get("document_count") or 0,
          created_at=_to_epoch(r.get("created_at")),
          updated_at=_to_epoch(r.get("updated_at")),
          embedding_model=r.get("embedding_model_name"),
          embedding_model_id=r.get("embedding_model_id"),
          embedding_provider_id=r.get("embedding_provider_id"),
          embedding_model_provider=r["embedding_provider"]["name"] if r.get(
            "embedding_provider") else None,
          embedding_available=r["embedding_model"]["is_active"] if r.get(
            "embedding_model") else False,
      ))

    return KnowledgeBaseListResponse(
        data=data,
        has_more=False,
        limit=100,
        total=total,
        page=1,
    )
  except Exception as e:
    logger.exception("Failed to fetch knowledge bases")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post(
    "/knowledge_bases",
    # response_model=KnowledgeBaseResponse,
    summary="Create an Empty Knowledge Base",
    status_code=201
)
def create_knowledge_base(
    request: KnowledgeBaseInput,
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  try:
    created = kb_service.create_knowledge_base(
        tenant_id=auth["tenant_id"],
        user_id=auth.get("user_id"),
        access_token=auth.get("token"),
        request=request
    )
    if not created:
      raise HTTPException(
        status_code=500, detail="Failed to create knowledge base.")

    return KnowledgeBaseResponse(
        id=created["id"],
        name=created["name"],
        description=created.get("description"),
        retrieval_model=RetrievalModel(**created["retrieval_model"]),
    )
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/knowledge_bases/{knowledge_base_id}",
    response_model=KnowledgeBaseDetail,
    summary="Get Knowledge Base Details",
    description="Fetches the detailed information of a specific knowledge base by its ID."
)
def get_knowledge_base_details(
    knowledge_base_id: UUID = Path(..., description="KB ID (uuid)"),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]

  kb_detail = kb_service.get_knowledge_base_details(
      knowledge_base_id=str(knowledge_base_id),
      tenant_id=tenant_id,
      access_token=auth.get("token")
  )

  if not kb_detail:
    raise HTTPException(status_code=404, detail="Knowledge base not found")

  return kb_detail


@router.patch(
    "/knowledge_bases/{knowledge_base_id}",
    summary="Update Knowledge Base",
)
def update_knowledge_base(
    knowledge_base_id: UUID = Path(..., description="KB ID"),
    body: UpdateKnowledgeBaseRequest = Body(...),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  kb_id = str(knowledge_base_id)

  try:
    updated = kb_service.update_knowledge_base(
        kb_id, tenant_id, body, access_token=auth.get("token"))
    if not updated:
      raise HTTPException(
        status_code=404, detail="Knowledge base not found or update failed.")

    full_detail = kb_service.get_knowledge_base_details(kb_id, tenant_id)
    return full_detail
  except ValueError as e:
    if "exists" in str(e):
      raise HTTPException(status_code=409, detail=str(e))
    raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/knowledge_bases/{knowledge_base_id}",
    summary="Delete Knowledge Base",
    description="Deletes a knowledge base and all its associated data (documents, chunks, vectors).",
    response_model=MessageResponse
)
def delete_knowledge_base(
    knowledge_base_id: UUID = Path(..., description="KB ID"),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  kb_id = str(knowledge_base_id)

  try:
    success = kb_service.delete_knowledge_base(
        kb_id, tenant_id, access_token=auth.get("token"))
    if not success:
      raise HTTPException(
        status_code=404, detail="Knowledge base not found or failed to delete.")

    return {"status": "success", "message": "Knowledge base deleted successfully."}
  except Exception as e:
    logger.exception(f"Failed to delete knowledge base {kb_id}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get(
    "/knowledge_bases/{knowledge_base_id}/documents",
    response_model=DocumentListResponse,
    summary="List Documents in Knowledge Base",
)
def list_documents(
    knowledge_base_id: UUID = Path(..., description="KB ID"),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  kb_id = str(knowledge_base_id)

  try:
    docs = kb_service.list_documents(
        kb_id, tenant_id, access_token=auth.get("token"))
    data = []
    for d in docs:
      data.append(DocumentItem(
          id=str(d["id"]),
          name=d["name"],
          path=d.get("path"),
          status=d.get("status"),
          knowledgebase_id=str(d["knowledgebase_id"]),
          tenant_id=str(d["tenant_id"]) if d.get("tenant_id") else None,
          created_by=d["created_by"],
          creator=d.get("creator"),
          created_at=_to_epoch(d.get("created_at")),
          updated_at=_to_epoch(d.get("updated_at")),
      ))
    logger.info(
      f"[API] list_documents for KB {kb_id}: Found {len(data)} items")
    return DocumentListResponse(data=data, total=len(data))
  except Exception as e:
    logger.exception(f"Failed to list documents for {kb_id}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
