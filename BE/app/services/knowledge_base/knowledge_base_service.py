from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.knowledge_base import (
    KnowledgeBaseInput, UpdateKnowledgeBaseRequest, KnowledgeBaseDetail,
    RetrievalModelSchema
)
from app.helper.utils_kb import (
    INDEX_MAP, PERM_MAP, api_to_db_retrieval, db_to_api_retrieval, to_epoch
)


from app.services.supabase.document_repository import DocumentRepository
from app.services.supabase.tenant_repository import TenantRepository


class KnowledgeBaseService:
  def __init__(
      self,
      kb_repo: KnowledgeBaseRepository,
      doc_repo: DocumentRepository,
      tenant_repo: TenantRepository
  ):
    self.kb_repo = kb_repo
    self.doc_repo = doc_repo
    self.tenant_repo = tenant_repo

  async def list_knowledge_bases(self, tenant_id: str, access_token: str = None) -> Tuple[List[dict], int]:
    return await self.kb_repo.list_knowledge_bases(tenant_id, access_token)

  async def create_knowledge_base(
      self,
      tenant_id: str,
      user_id: str,
      access_token: str,
      request: KnowledgeBaseInput
  ) -> Optional[dict]:

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

    # Map permission and indexing_technique
    perm = kb_dict.get("permission")
    if perm:
      # Default to as-is if not found, or None? Update logic uses strict check.
      perm = PERM_MAP.get(perm, perm)

    idx = kb_dict.get("indexing_technique")
    if idx:
      idx = INDEX_MAP.get(idx, idx)

    payload = {
        "tenant_id": str(tenant_id),
        "name": kb_name,
        "description": kb_dict.get("description"),
        "permission": perm,
        "indexing_technique": idx,
        "embedding_provider_id": str(kb_dict.get("embedding_provider_id")) if kb_dict.get("embedding_provider_id") else None,
        "embedding_model_id": str(kb_dict.get("embedding_model_id")) if kb_dict.get("embedding_model_id") else None,
        "created_at": datetime.utcnow().isoformat(),
        "retrieval_model": api_to_db_retrieval(kb_dict.get("retrieval_model").dict() if hasattr(kb_dict.get("retrieval_model"), "dict") else (kb_dict.get("retrieval_model") or {
            "search_method": "semantic",
            "auto_merging": False
        })),
    }

    return await self.kb_repo.create(payload, access_token=access_token)

  async def get_knowledge_base_details(self, knowledge_base_id: str, tenant_id: str, access_token: str = None) -> Optional[KnowledgeBaseDetail]:
    row = await self.kb_repo.get_one(
      knowledge_base_id, tenant_id, access_token=access_token)
    if not row:
      return None

    rm = row.get("retrieval_model") or {}

    retrieval_model_dict = RetrievalModelSchema(
        search_method=str(rm.get("search_method", "semantic")),
        auto_merging=bool(rm.get("auto_merging", False))
    )

    return KnowledgeBaseDetail(
        id=str(row["id"]),
        name=row["name"],
        description=row.get("description"),
        permission=row.get("permission"),
        indexing_technique=row.get("indexing_technique"),
        document_count=row.get("document_count", 0),
        created_at=str(row.get("created_at")),
        updated_at=str(row.get("updated_at")),
        embedding_model=row.get("embedding_model_name"),
        retrieval_model=retrieval_model_dict,
        doc_form=row.get("doc_form"),
    )

  async def update_knowledge_base(self, kb_id: str, tenant_id: str, body: UpdateKnowledgeBaseRequest, access_token: str = None) -> Optional[dict]:
    upd: Dict[str, Any] = {}

    if body.name is not None:
      new_name = body.name.strip()
      if not new_name:
        raise ValueError("Name cannot be empty.")

      if await self.kb_repo.name_conflict(tenant_id, new_name, exclude_id=kb_id):
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

    if body.retrieval_model is not None:
      upd["retrieval_model"] = api_to_db_retrieval(
          body.retrieval_model.dict(exclude_unset=True))

    if body.embedding_provider_id is not None:
      upd["embedding_provider_id"] = str(body.embedding_provider_id)

    if body.embedding_model_id is not None:
      upd["embedding_model_id"] = str(body.embedding_model_id)

    if body.partial_member_list is not None:
      row = await self.kb_repo.get_knowledge_base_detail(
        kb_id, tenant_id, access_token=access_token)
      if not row:
        return None

      target_perm = upd.get("permission", row.get("permission"))
      if target_perm != "partial":
        raise ValueError(
          "partial_member_list allowed only when permission=partial_members.")
      upd["partial_member_list"] = body.partial_member_list

    return await self.kb_repo.patch(kb_id, tenant_id, upd, access_token=access_token)

  async def check_name_conflict(self, tenant_id: str, name: str, exclude_id: str, access_token: str = None) -> bool:
    return await self.kb_repo.name_conflict(tenant_id, name, exclude_id, access_token=access_token)

  async def delete_knowledge_base(self, kb_id: str, tenant_id: str, access_token: str = None) -> bool:
    """
    Delete a KB (Cascade: Files -> Vectors -> DB Rows).
    """
    # 0. Delete Orphaned Files from MinIO
    from app.core.factory import get_minio_storage
    minio_storage = get_minio_storage()

    documents = await self.doc_repo.get_documents_by_kb(
      kb_id, tenant_id, access_token=access_token)
    for doc in documents:
      file_path = doc.get("path")
      if file_path:
        minio_storage.delete_file(file_path)

    # 1. Delete DB Row (Cascade handles graph_chunks → vectors)
    return await self.kb_repo.delete_kb(kb_id, tenant_id, access_token=access_token)

  async def get_total_kbs(self, tenant_id: str = None, access_token: str = None) -> int:
    return await self.kb_repo.get_total_kbs(tenant_id, access_token)

  async def list_documents(self, kb_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    """
    List all documents in a knowledge base.
    """
    return await self.doc_repo.get_documents_by_kb(kb_id, tenant_id, access_token)
