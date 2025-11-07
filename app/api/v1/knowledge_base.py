# app/api/v1/knowledge_base.py
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query

from app.core.logger import get_logger
from app.core.factory import get_kb_repository

from app.utils.auth import get_current_user

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
	response_model=KnowledgeBaseListResponse,
	summary="Get Knowledge Base List",
	description="Retrieves a list of knowledge bases, with options for pagination and filtering."
)
def list_knowledge_bases(
		keyword: Optional[str] = Query(None, description="Search keyword to filter by name"),
		tag_ids: Optional[List[str]] = Query(None, description="List of tag IDs (ALL-of filtering)"),
		page: int = Query(1, ge=1, description="Page number"),
		limit: int = Query(20, ge=1, le=100, description="Items per page"),
		include_all: bool = Query(False, description="Only effective for workspace owners"),
		kb_repo=Depends(get_kb_repository),
		auth=Depends(get_current_user),
):
	try:
		tenant_id = auth["tenant_id"]
		is_owner = bool(auth.get("is_owner", False))

		rows, total = kb_repo.list_knowledge_bases(
			tenant_id=tenant_id,
			keyword=keyword,
			tag_ids=tag_ids or [],
			page=page,
			limit=limit,
			include_all=include_all,
			is_owner=is_owner,
		)

		has_more = ((page - 1) * limit + len(rows)) < total

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
				created_by=str(r.get("created_by")) if r.get("created_by") is not None else None,
				created_at=_to_epoch(r.get("created_at")),
				updated_by=str(r.get("updated_by")) if r.get("updated_by") is not None else None,
				updated_at=_to_epoch(r.get("updated_at")),
				embedding_model=r.get("embedding_model"),
				embedding_model_provider=r.get("embedding_model_provider"),
				embedding_available=bool(r.get("embedding_model")),
			))

		return KnowledgeBaseListResponse(
			data=data,
			has_more=has_more,
			limit=limit,
			total=total,
			page=page,
		)
	except Exception as e:
		logger.exception("Failed to fetch knowledge bases")
		raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post(
	"/knowledge_bases",
	response_model=KnowledgeBaseResponse,
	summary="Create an Empty Knowledge Base",
	status_code=201
)
def create_knowledge_base(
		request: KnowledgeBaseInput,
		kb_repository=Depends(get_kb_repository),
		auth=Depends(get_current_user)
):
	kb_name = (request.name or "").strip()
	if not kb_name:
		raise HTTPException(status_code=400, detail="Knowledge base name cannot be empty.")

	dump = getattr(request, "model_dump", None)
	if callable(dump):
		kb_dict = dump()
	elif hasattr(request, "dict") and callable(getattr(request, "dict", None)):
		kb_dict = request.dict()
	elif isinstance(request, dict):
		kb_dict = request
	else:
		kb_dict = dict(request)

	if not isinstance(kb_dict, dict):
		raise HTTPException(status_code=400, detail="Failed to parse request data as dictionary.")

	payload = {
		"tenant_id": auth["tenant_id"],
		"name": kb_name,
		"description": kb_dict.get("description"),
		"indexing_technique": kb_dict["indexing_technique"],
		"permission": kb_dict["permission"],
		"embedding_model_provider": kb_dict.get("embedding_model_provider"),
		"embedding_model": kb_dict.get("embedding_model"),
		"retrieval_model": (
			getattr(request.retrieval_model, "model_dump", request.retrieval_model.dict)()
		),  # jsonb
		"partial_member_list": kb_dict.get("partial_member_list"),
		"created_at": datetime.utcnow().isoformat(),
	}

	created = kb_repository.create(payload)
	if not created:
		raise HTTPException(status_code=500, detail="Failed to create knowledge base in Supabase.")

	return KnowledgeBaseResponse(
		id=created["id"],
		name=created["name"],
		description=created.get("description"),
		retrieval_model=RetrievalModel(**created["retrieval_model"]),
	)


@router.get(
	"/knowledge_bases/{knowledge_base_id}",
	response_model=KnowledgeBaseDetail,
	summary="Get Knowledge Base Details",
	description="Fetches the detailed information of a specific knowledge base by its ID."
)
def get_knowledge_base_details(
		knowledge_base_id: UUID = Path(..., description="KB ID (uuid)"),
		kb_repo=Depends(get_kb_repository),
		auth=Depends(get_current_user)
):
	tenant_id = auth["tenant_id"]

	row, tags, counts = kb_repo.get_knowledge_base_detail(
		knowledge_base_id=str(knowledge_base_id),
		tenant_id=tenant_id,
	)

	if not row:
		raise HTTPException(status_code=404, detail="Knowledge base not found")

	rm = row.get("retrieval_model") or {}
	rm_mode = rm.get("reranking_mode") or {}
	if "provider" in rm_mode or "model" in rm_mode:
		rm_mode = {
			"reranking_provider_name": rm_mode.get("provider"),
			"reranking_model_name": rm_mode.get("model"),
		}

	retrieval_model_dict = RetrievalModelSchema(
		search_method=str(rm.get("search_method") or ""),
		reranking_enable=bool(rm.get("reranking_enable")),
		reranking_mode=RetrievalModeSchema(**rm_mode) if rm_mode else None,
		top_k=int(rm.get("top_k", 0)),
		score_threshold_enabled=bool(rm.get("score_threshold_enabled")),
		score_threshold=rm.get("score_threshold"),
		weights=rm.get("weights"),
	)

	return KnowledgeBaseDetail(
		id=str(row["id"]),
		name=row["name"],
		description=row.get("description"),
		provider=row.get("provider"),
		permission=row.get("permission"),
		data_source_type=row.get("data_source_type"),
		indexing_technique=row.get("indexing_technique"),
		app_count=counts.get("app_count", 0),
		document_count=counts.get("document_count", 0),
		word_count=counts.get("word_count", 0),
		created_by=row.get("created_by"),
		created_at=_to_epoch(row.get("created_at")),
		updated_by=row.get("updated_by"),
		updated_at=_to_epoch(row.get("updated_at")),
		embedding_model=row.get("embedding_model"),
		embedding_model_provider=row.get("embedding_model_provider"),
		embedding_available=bool(row.get("embedding_model")),
		retrieval_model_dict=retrieval_model_dict,
		tags=tags,
		doc_form=row.get("doc_form"),
	)


@router.patch(
	"/knowledge_bases/{knowledge_base_id}",
	summary="Update Knowledge Base",
)
def update_knowledge_base(
		knowledge_base_id: UUID = Path(..., description="KB ID"),
		body: UpdateKnowledgeBaseRequest = Depends(),
		kb_repo=Depends(get_kb_repository),
		auth=Depends(get_current_user)
):
	tenant_id = auth["tenant_id"]
	kb_id = str(knowledge_base_id)

	row = kb_repo.get_one(kb_id, tenant_id)
	if not row:
		raise HTTPException(status_code=404, detail="Knowledge base not found")

	upd: Dict[str, Any] = {}

	if body.name is not None:
		new_name = body.name.strip()
		if not new_name:
			raise HTTPException(status_code=400, detail="Name cannot be empty.")

		if kb_repo.name_conflict(tenant_id, new_name, exclude_id=kb_id):
			raise HTTPException(status_code=409, detail="Knowledge base name already exists.")
		upd["name"] = new_name

	if body.description is not None:
		upd["description"] = body.description

	if body.indexing_technique is not None:
		idx = INDEX_MAP.get(body.indexing_technique)
		if not idx:
			raise HTTPException(status_code=400, detail="Invalid indexing_technique.")
		upd["indexing_technique"] = idx

	if body.permission is not None:
		perm = PERM_MAP.get(body.permission)
		if not perm:
			raise HTTPException(status_code=400, detail="Invalid permission.")
		upd["permission"] = perm
		if perm != "partial" and body.partial_member_list is None:
			upd["partial_member_list"] = []

	if body.embedding_model_provider is not None:
		upd["embedding_model_provider"] = body.embedding_model_provider

	if body.embedding_model is not None:
		upd["embedding_model"] = body.embedding_model

	if body.retrieval_model is not None:
		upd["retrieval_model"] = api_to_db_retrieval(body.retrieval_model.dict(exclude_unset=True))

	if body.partial_member_list is not None:
		target_perm = upd.get("permission", row.get("permission"))
		if target_perm != "partial":
			raise HTTPException(status_code=400, detail="partial_member_list allowed only when permission=partial_members.")
		upd["partial_member_list"] = body.partial_member_list

	updated = kb_repo.patch(kb_id, tenant_id, upd)
	if not updated:
		raise HTTPException(status_code=500, detail="Failed to update knowledge base.")

	rm_api = db_to_api_retrieval(updated.get("retrieval_model") or {})
	resp = {
		"id": str(updated["id"]),
		"name": updated["name"],
		"description": updated.get("description"),
		"provider": updated.get("provider"),
		"permission": updated.get("permission"),
		"data_source_type": updated.get("data_source_type"),
		"indexing_technique": updated.get("indexing_technique"),
		"app_count": 0,
		"document_count": 0,
		"word_count": 0,
		"created_by": updated.get("created_by"),
		"created_at": to_epoch(updated.get("created_at")),
		"updated_by": updated.get("updated_by"),
		"updated_at": to_epoch(updated.get("updated_at")),
		"embedding_model": updated.get("embedding_model"),
		"embedding_model_provider": updated.get("embedding_model_provider"),
		"embedding_available": bool(updated.get("embedding_model")),
		"retrieval_model_dict": rm_api,
		"tags": [],
		"doc_form": updated.get("doc_form"),
	}
	return resp
