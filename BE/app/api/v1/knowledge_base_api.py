# app/api/v1/knowledge_base_api.py
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Path

from app.api.dependencies import KnowledgeBaseServiceDep
from app.core.logger import get_logger
from app.schemas.common import BaseResponse, MessageResponse
from app.schemas.document import DocumentItem, DocumentListResponse
from app.schemas.knowledge_base import (
  KnowledgeBaseDetail,
  KnowledgeBaseInput,
  KnowledgeBaseItem,
  KnowledgeBaseListResponse,
  KnowledgeBaseResponse,
  RetrievalModel,
  UpdateKnowledgeBaseRequest,
)

logger = get_logger(__name__)
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
  response_model=BaseResponse[KnowledgeBaseListResponse],
  summary="Get Knowledge Base List",
  description="Retrieves a list of knowledge bases, with options for pagination and filtering.",
)
async def list_knowledge_bases(
  kb_service: KnowledgeBaseServiceDep,
):
  try:
    rows, total = await kb_service.list_knowledge_bases()

    data = []
    for r in rows:
      data.append(
        KnowledgeBaseItem(
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
          embedding_model_provider=r["embedding_provider"]["name"]
          if r.get("embedding_provider")
          else None,
          retrieval_model=r.get("retrieval_model"),
          embedding_available=r["embedding_model"]["is_active"]
          if r.get("embedding_model")
          else False,
        )
      )

    result = KnowledgeBaseListResponse(
      data=data,
      has_more=False,
      limit=100,
      total=total,
      page=1,
    )
    return BaseResponse(data=result)
  except Exception as e:
    logger.exception("Failed to fetch knowledge bases")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post(
  "/knowledge_bases",
  response_model=BaseResponse[KnowledgeBaseResponse],
  summary="Create an Empty Knowledge Base",
  status_code=201,
)
async def create_knowledge_base(
  request: KnowledgeBaseInput,
  kb_service: KnowledgeBaseServiceDep,
):
  try:
    created = await kb_service.create_knowledge_base(request=request)
    if not created:
      raise HTTPException(status_code=500, detail="Failed to create knowledge base.")

    result = KnowledgeBaseResponse(
      id=created["id"],
      name=created["name"],
      description=created.get("description"),
      retrieval_model=RetrievalModel(**created["retrieval_model"]),
    )
    return BaseResponse(data=result)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


@router.get(
  "/knowledge_bases/{knowledge_base_id}",
  response_model=BaseResponse[KnowledgeBaseDetail],
  summary="Get Knowledge Base Details",
  description="Fetches the detailed information of a specific knowledge base by its ID.",
)
async def get_knowledge_base_details(
  knowledge_base_id: Annotated[UUID, Path(description="KB ID (uuid)")],
  kb_service: KnowledgeBaseServiceDep,
):
  kb_detail = await kb_service.get_knowledge_base_details(
    knowledge_base_id=str(knowledge_base_id)
  )

  if not kb_detail:
    raise HTTPException(status_code=404, detail="Knowledge base not found")

  return BaseResponse(data=kb_detail)


@router.patch(
  "/knowledge_bases/{knowledge_base_id}",
  response_model=BaseResponse[KnowledgeBaseDetail],
  summary="Update Knowledge Base",
)
async def update_knowledge_base(
  knowledge_base_id: Annotated[UUID, Path(description="KB ID")],
  body: Annotated[UpdateKnowledgeBaseRequest, Body(...)],
  kb_service: KnowledgeBaseServiceDep,
):
  kb_id = str(knowledge_base_id)

  try:
    updated = await kb_service.update_knowledge_base(kb_id, body=body)
    if not updated:
      raise HTTPException(
        status_code=404, detail="Knowledge base not found or update failed."
      )

    full_detail = await kb_service.get_knowledge_base_details(kb_id)
    return BaseResponse(data=full_detail)
  except ValueError as e:
    if "exists" in str(e):
      raise HTTPException(status_code=409, detail=str(e))
    raise HTTPException(status_code=400, detail=str(e))


@router.delete(
  "/knowledge_bases/{knowledge_base_id}",
  summary="Delete Knowledge Base",
  description="Deletes a knowledge base and all its associated data (documents, chunks, vectors).",
  response_model=BaseResponse[MessageResponse],
)
async def delete_knowledge_base(
  knowledge_base_id: Annotated[UUID, Path(description="KB ID")],
  kb_service: KnowledgeBaseServiceDep,
):
  kb_id = str(knowledge_base_id)

  try:
    success = await kb_service.delete_knowledge_base(kb_id)
    if not success:
      raise HTTPException(
        status_code=404, detail="Knowledge base not found or failed to delete."
      )

    return BaseResponse(
      data=MessageResponse(message="Knowledge base deleted successfully.")
    )
  except Exception as e:
    logger.exception(f"Failed to delete knowledge base {kb_id}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get(
  "/knowledge_bases/{knowledge_base_id}/documents",
  response_model=BaseResponse[DocumentListResponse],
  summary="List Documents in Knowledge Base",
)
async def list_documents(
  knowledge_base_id: Annotated[UUID, Path(description="KB ID")],
  kb_service: KnowledgeBaseServiceDep,
):
  kb_id = str(knowledge_base_id)

  try:
    docs = await kb_service.list_documents(kb_id)
    data = []
    for d in docs:
      data.append(
        DocumentItem(
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
        )
      )
    logger.info(f"[API] list_documents for KB {kb_id}: Found {len(data)} items")
    result = DocumentListResponse(data=data, total=len(data))
    return BaseResponse(data=result)
  except Exception as e:
    logger.exception(f"Failed to list documents for {kb_id}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
