from datetime import timezone
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from app.repositories import (
  KnowledgeBaseRepository,
  DocumentRepository,
  TenantRepository,
)
from app.schemas.knowledge_base import (
  KnowledgeBaseInput,
  UpdateKnowledgeBaseRequest,
  KnowledgeBaseDetail,
  RetrievalModelSchema,
)
from app.helper.utils_kb import INDEX_MAP, PERM_MAP, api_to_db_retrieval


class KnowledgeBaseService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "KnowledgeBaseService":
    if cls._instance is None:
      from app.repositories import (
        DocumentRepository,
        KnowledgeBaseRepository,
        TenantRepository,
      )

      cls._instance = cls(
        kb_repo_instance=KnowledgeBaseRepository.get_instance(),
        document_repo_instance=DocumentRepository.get_instance(),
        tenant_repo_instance=TenantRepository.get_instance(),
      )
    return cls._instance

  def __init__(
    self,
    kb_repo_instance: KnowledgeBaseRepository,
    document_repo_instance: DocumentRepository,
    tenant_repo_instance: TenantRepository,
  ):
    self.kb_repo_instance = kb_repo_instance
    self.document_repo_instance = document_repo_instance
    self.tenant_repo_instance = tenant_repo_instance

  async def list_knowledge_bases(self) -> Tuple[List[dict], int]:
    return await self.kb_repo_instance.list_knowledge_bases()

  async def create_knowledge_base(
    self, request: KnowledgeBaseInput = None
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
      "name": kb_name,
      "description": kb_dict.get("description"),
      "permission": perm,
      "indexing_technique": idx,
      "embedding_provider_id": str(kb_dict.get("embedding_provider_id"))
      if kb_dict.get("embedding_provider_id")
      else None,
      "embedding_model_id": str(kb_dict.get("embedding_model_id"))
      if kb_dict.get("embedding_model_id")
      else None,
      "created_at": datetime.now(timezone.utc).isoformat(),
      "retrieval_model": api_to_db_retrieval(
        kb_dict.get("retrieval_model").dict()
        if hasattr(kb_dict.get("retrieval_model"), "dict")
        else (
          kb_dict.get("retrieval_model")
          or {"search_method": "semantic", "auto_merging": False}
        )
      ),
    }

    return await self.kb_repo_instance.create(payload)

  async def get_knowledge_base_details(
    self, knowledge_base_id: str
  ) -> Optional[KnowledgeBaseDetail]:
    row = await self.kb_repo_instance.get_one(knowledge_base_id)
    if not row:
      return None

    rm = row.get("retrieval_model") or {}

    retrieval_model_dict = RetrievalModelSchema(
      search_method=str(rm.get("search_method", "semantic")),
      auto_merging=bool(rm.get("auto_merging", False)),
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

  async def update_knowledge_base(
    self, kb_id: str, body: UpdateKnowledgeBaseRequest = None
  ) -> Optional[dict]:
    upd: Dict[str, Any] = {}

    if body.name is not None:
      new_name = body.name.strip()
      if not new_name:
        raise ValueError("Name cannot be empty.")

      if await self.kb_repo_instance.name_conflict(new_name, exclude_id=kb_id):
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
        body.retrieval_model.dict(exclude_unset=True)
      )

    if body.embedding_provider_id is not None:
      upd["embedding_provider_id"] = str(body.embedding_provider_id)

    if body.embedding_model_id is not None:
      upd["embedding_model_id"] = str(body.embedding_model_id)

    if body.partial_member_list is not None:
      row = await self.kb_repo_instance.get_knowledge_base_detail(kb_id)
      if not row:
        return None

      target_perm = upd.get("permission", row.get("permission"))
      if target_perm != "partial":
        raise ValueError(
          "partial_member_list allowed only when permission=partial_members."
        )
      upd["partial_member_list"] = body.partial_member_list

    return await self.kb_repo_instance.patch(kb_id, upd)

  async def check_name_conflict(self, name: str = None, exclude_id: str = None) -> bool:
    return await self.kb_repo_instance.name_conflict(name, exclude_id)

  async def delete_knowledge_base(self, kb_id: str) -> bool:
    """
    Delete a KB (Cascade: Files -> Vectors -> DB Rows).
    """
    # 0. Delete Orphaned Files from MinIO
    from app.services.minio_storage_service import MinioStorageService

    minio_storage_instance = MinioStorageService.get_instance()

    documents = await self.document_repo_instance.get_documents_by_kb(kb_id)
    for doc in documents:
      file_path = doc.get("path")
      if file_path:
        minio_storage_instance.delete_file(file_path)

    # 1. Delete DB Row (Cascade handles graph_chunks → vectors)
    return await self.kb_repo_instance.delete_kb(kb_id)

  async def get_total_kbs(self) -> int:
    return await self.kb_repo_instance.get_total_kbs()

  async def list_documents(self, kb_id: str) -> List[dict]:
    """
    List all documents in a knowledge base.
    """
    return await self.document_repo_instance.get_documents_by_kb(kb_id)
