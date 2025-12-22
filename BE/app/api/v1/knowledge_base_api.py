# app/api/v1/knowledge_base.py
from fastapi_cache.decorator import cache
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query

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
        access_token=auth.get("token"),
        # keyword=keyword,
        # tag_ids=tag_ids or [],
        # page=page,
        # limit=limit,
        # include_all=include_all,
        # is_owner=is_owner,
    )

    # has_more = ((page - 1) * limit + len(rows)) < total

    data = []
    for r in rows:
      data.append(KnowledgeBaseItem(
          id=str(r["id"]),
          name=r["name"],
          description=r.get("description"),
          provider=r.get("provider"),
          permission=r.get("permission"),
          data_source_type=r.get("data_source_type"),
          indexing_technique=r.get("indexing_technique"),
          app_count=r.get("app_count") or 0,
          document_count=r.get("document_count") or 0,
          word_count=r.get("word_count") or 0,
          created_by=str(r.get("created_by")) if r.get(
            "created_by") is not None else None,
          created_at=_to_epoch(r.get("created_at")),
          updated_by=str(r.get("updated_by")) if r.get(
            "updated_by") is not None else None,
          updated_at=_to_epoch(r.get("updated_at")),
          embedding_model=r.get("embedding_model"),
          embedding_model_provider=r.get("embedding_model_provider"),
          embedding_available=bool(r.get("embedding_model")),
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
    created = kb_service.create_knowledge_base(auth["tenant_id"], request)
    if not created:
      raise HTTPException(
        status_code=500, detail="Failed to create knowledge base in Supabase.")

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
    body: UpdateKnowledgeBaseRequest = Depends(),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  kb_id = str(knowledge_base_id)

  try:
    updated = kb_service.update_knowledge_base(kb_id, tenant_id, body)
    if not updated:
      raise HTTPException(
        status_code=404, detail="Knowledge base not found or update failed.")

    rm_api = db_to_api_retrieval(updated.get("retrieval_model") or {})
    resp = {
        "id": str(updated["id"]),
        "name": updated["name"],
        "description": updated.get("description"),
        "created_at": to_epoch(updated.get("created_at")),
        "embedding_model": updated.get("embedding_model"),
    }
    return resp
  except ValueError as e:
    if "exists" in str(e):
      raise HTTPException(status_code=409, detail=str(e))
    raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/knowledge_bases/{knowledge_base_id}",
    summary="Delete Knowledge Base",
    description="Deletes a knowledge base and all its associated data (documents, chunks, vectors)."
)
def delete_knowledge_base(
    knowledge_base_id: UUID = Path(..., description="KB ID"),
    kb_service=Depends(get_knowledge_base_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  kb_id = str(knowledge_base_id)

  try:
    success = kb_service.delete_knowledge_base(kb_id, tenant_id)
    if not success:
      raise HTTPException(
        status_code=404, detail="Knowledge base not found or failed to delete.")

    return {"status": "success", "message": "Knowledge base deleted successfully."}
  except Exception as e:
    logger.exception(f"Failed to delete knowledge base {kb_id}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
