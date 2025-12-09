from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.knowledge_base import (
    KnowledgeBaseInput, UpdateKnowledgeBaseRequest, KnowledgeBaseDetail,
    RetrievalModelSchema, RetrievalModeSchema
)
from app.helper.utils_kb import (
    INDEX_MAP, PERM_MAP, api_to_db_retrieval, db_to_api_retrieval, to_epoch
)


class KnowledgeBaseService:
  def __init__(self, kb_repo: KnowledgeBaseRepository):
    self.kb_repo = kb_repo

  def list_knowledge_bases(self, tenant_id: str) -> Tuple[List[dict], int]:
    return self.kb_repo.list_knowledge_bases(tenant_id)

  def create_knowledge_base(self, tenant_id: str, request: KnowledgeBaseInput) -> Optional[dict]:
    kb_name = (request.name or "").strip()
    if not kb_name:
      raise ValueError("Knowledge base name cannot be empty.")

    # Convert request to dict
    dump = getattr(request, "model_dump", None)
    if callable(dump):
      kb_dict = dump()
    elif hasattr(request, "dict") and callable(getattr(request, "dict", None)):
      kb_dict = request.dict()
    elif isinstance(request, dict):
      kb_dict = request
    else:
      kb_dict = dict(request)

    payload = {
        "tenant_id": tenant_id,
        "name": kb_name,
        "description": kb_dict.get("description"),
        "embedding_model": kb_dict.get("embedding_model"),
        "created_at": datetime.utcnow().isoformat(),
    }

    return self.kb_repo.create(payload)

  def get_knowledge_base_details(self, knowledge_base_id: str, tenant_id: str) -> Optional[KnowledgeBaseDetail]:
    row, tags, counts = self.kb_repo.get_knowledge_base_detail(
      knowledge_base_id, tenant_id)
    if not row:
      return None

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
        created_at=to_epoch(row.get("created_at")),
        updated_by=row.get("updated_by"),
        updated_at=to_epoch(row.get("updated_at")),
        embedding_model=row.get("embedding_model"),
        embedding_model_provider=row.get("embedding_model_provider"),
        embedding_available=bool(row.get("embedding_model")),
        retrieval_model_dict=retrieval_model_dict,
        tags=tags,
        doc_form=row.get("doc_form"),
    )

  def update_knowledge_base(self, kb_id: str, tenant_id: str, body: UpdateKnowledgeBaseRequest) -> Optional[dict]:
    upd: Dict[str, Any] = {}

    if body.name is not None:
      new_name = body.name.strip()
      if not new_name:
        raise ValueError("Name cannot be empty.")

      if self.kb_repo.name_conflict(tenant_id, new_name, exclude_id=kb_id):
        raise ValueError("Knowledge base name already exists.")
      upd["name"] = new_name

    if body.description is not None:
      upd["description"] = body.description

    if body.indexing_technique is not None:
      idx = INDEX_MAP.get(body.indexing_technique)
      if not idx:
        raise ValueError("Invalid indexing_technique.")
      upd["indexing_technique"] = idx

    if body.permission is not None:
      perm = PERM_MAP.get(body.permission)
      if not perm:
        raise ValueError("Invalid permission.")
      upd["permission"] = perm
      if perm != "partial" and body.partial_member_list is None:
        upd["partial_member_list"] = []

    if body.embedding_model_provider is not None:
      upd["embedding_model_provider"] = body.embedding_model_provider

    if body.embedding_model is not None:
      upd["embedding_model"] = body.embedding_model

    if body.retrieval_model is not None:
      upd["retrieval_model"] = api_to_db_retrieval(
          body.retrieval_model.dict(exclude_unset=True))

    if body.partial_member_list is not None:
      row, _, _ = self.kb_repo.get_knowledge_base_detail(kb_id, tenant_id)
      if not row:
        return None

      target_perm = upd.get("permission", row.get("permission"))
      if target_perm != "partial":
        raise ValueError(
          "partial_member_list allowed only when permission=partial_members.")
      upd["partial_member_list"] = body.partial_member_list

    return self.kb_repo.patch(kb_id, tenant_id, upd)

  def check_name_conflict(self, tenant_id: str, name: str, exclude_id: str) -> bool:
    return self.kb_repo.name_conflict(tenant_id, name, exclude_id)
