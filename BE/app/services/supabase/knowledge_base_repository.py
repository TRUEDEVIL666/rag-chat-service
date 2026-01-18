# app/services/supabase/knowledge_base_repository.py

from datetime import datetime, timezone
from app.services.supabase.supabase_client import get_supabase_client
from app.core.logger import get_logger
from typing import Any, Dict, Optional, List, Tuple

logger = get_logger("knowledge_base_repository")


class KnowledgeBaseRepository:
  def __init__(self):
    self.table_name = "knowledgebases"

  def check_exists(self, tenant_id: str, kb_name: str, access_token: str = None) -> bool:
    """
    Kiểm tra knowledge base đã tồn tại theo tenant + kb_name
    """
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .select("id")
          .eq("tenant_id", tenant_id)
          .eq("name", kb_name)
          .limit(1)
          .execute()
      )
      return bool(response.data)
    except Exception as e:
      logger.exception(f"[Supabase] Error checking KB exists: {e}")
      return False

  def create(self, kb_data: dict, access_token: str = None) -> Optional[dict]:
    """
    Tạo mới knowledge base (nếu chưa tồn tại). Trả về toàn bộ bản ghi vừa insert.
    """
    try:
      tenant_id = kb_data["tenant_id"]
      kb_name = kb_data["name"]

      if self.check_exists(tenant_id, kb_name, access_token):
        raise ValueError(f"Knowledge base '{kb_name}' already exists.")

      kb_data.setdefault("created_at", datetime.utcnow().isoformat())

      client = get_supabase_client(access_token)
      response = client.table(self.table_name).insert(kb_data).execute()

      created = response.data[0] if getattr(response, "data", None) else None
      if not created:
        err = getattr(response, "error", None)
        if err:
          logger.error(
            f"[Supabase] Insert KB error: {getattr(err, 'message', err)}")
        else:
          logger.error("[Supabase] Insert KB returned no data")
        return None

      logger.info(f"[Supabase] Created KB: {kb_name}")
      return created

    except Exception as e:
      logger.exception(f"[Supabase] Failed to create knowledge base: {e}")
      return None

  def list_knowledge_bases(
      self,
      tenant_id: str,
      access_token: str = None,
      # keyword: Optional[str],
      # tag_ids: List[str],
      # page: int,
      # limit: int,
      # include_all: bool,
      # is_owner: bool,
  ):
    """
    Trả danh sách KB theo spec /knowledge_bases, kèm total.
    - Phân trang: page, limit
    - Filter: keyword theo name, tag_ids (ALL-of)
    - include_all: chỉ hiệu lực khi is_owner=True
    """
    try:
      # offset = (page - 1) * limit
      # start = offset
      # end = offset + limit - 1
      client = get_supabase_client(access_token)
      q = (client.table(self.table_name)
           .select("*, embedding_provider:embedding_provider_id(name), embedding_model:embedding_model_id(name, model_id, is_active)")
           .eq("tenant_id", tenant_id)
           .execute())

      # if not (include_all and is_owner):
      # 	q = q.eq("tenant_id", tenant_id)

      # if keyword:
      # 	q = q.ilike("name", f"%{keyword}%")

      # if tag_ids:
      # 	ids_q = supabase.table("knowledge_base_tags").select("kb_id").eq("tag_id", tag_ids[0]).execute()
      # 	if not ids_q.data:
      # 		return [], 0
      # 	kb_ids = {row["kb_id"] for row in ids_q.data}
      #
      # 	for t in tag_ids[1:]:
      # 		t_q = supabase.table("knowledge_base_tags").select("kb_id").eq("tag_id", t).execute()
      # 		kb_ids &= {row["kb_id"] for row in (t_q.data or [])}
      # 		if not kb_ids:
      # 			return [], 0

      # q = q.in_("id", list(kb_ids))

      # q = q.order("updated_at", desc=True).order("created_at", desc=True)

      # page_res = q.execute()

      # rows = page_res.data or []
      # total = page_res.count or 0
      if q.data:
        for row in q.data:
          if row.get("embedding_model") and row.get("embedding_provider"):
            provider = row["embedding_provider"].get("name", "ollama")
            model_id = row["embedding_model"].get("model_id")
            if provider and model_id:
              row["embedding_model_name"] = f"{provider}/{model_id}"
        return q.data, len(q.data)
      return [], 0
    except Exception as e:
      logger.exception(f"[Supabase] Failed to list knowledge bases: {e}")
      return [], 0

  def get_knowledge_base_detail(
      self,
      knowledge_base_id: str,
      tenant_id: str,
      access_token: str = None
  ) -> Optional[dict]:
    """
    Lấy chi tiết 1 KB theo id + tenant scope.
    """
    try:
      client = get_supabase_client(access_token)
      kb_q = (
          client.table(self.table_name)
          .select("*")
          .eq("id", knowledge_base_id)
          .eq("tenant_id", tenant_id)
          .limit(1)
          .execute()
      )
      return (kb_q.data or [None])[0]

    except Exception as e:
      logger.exception(
        f"[Supabase] Failed to get knowledge base detail {knowledge_base_id}: {e}")
      return None

  def get_one(self, kb_id: str, tenant_id: str, access_token: str = None) -> Optional[dict]:
    client = get_supabase_client(access_token)
    res = (client.table(self.table_name)
           .select("*, embedding_provider:embedding_provider_id(name), embedding_model:embedding_model_id(name, model_id)")
           .eq("id", kb_id)
           .eq("tenant_id", tenant_id)
           .limit(1)
           .execute())

    data = (res.data or [None])[0]
    if data:
      if data.get("embedding_model") and data.get("embedding_provider"):
        provider = data["embedding_provider"].get("name", "ollama")
        model_id = data["embedding_model"].get("model_id")
        if provider and model_id:
          data["embedding_model_name"] = f"{provider}/{model_id}"

    return data

  def name_conflict(self, tenant_id: str, name: str, exclude_id: str, access_token: str = None) -> bool:
    client = get_supabase_client(access_token)
    res = (client.table(self.table_name)
           .select("id").eq("tenant_id", tenant_id).eq("name", name)
           .neq("id", exclude_id).limit(1).execute())
    return bool(res.data)

  def patch(self, kb_id: str, tenant_id: str, fields: Dict[str, Any], access_token: str = None) -> Optional[dict]:
    if not fields:
      return self.get_one(kb_id, tenant_id, access_token)

    fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    client = get_supabase_client(access_token)
    res = (client.table(self.table_name)
           .update(fields)
           .eq("id", kb_id).eq("tenant_id", tenant_id)
           .execute())
    # Return get_one to ensure consistency with list/get views (e.g. joined fields)
    return self.get_one(kb_id, tenant_id, access_token)

  def get_retrieval_configs_by_ids(self, kb_ids: List[str], tenant_id: str, access_token: str = None) -> Dict[str, dict]:
    """
    Batch fetch retrieval configs for multiple KBs.
    Returns: { kb_id: { "retrieval_model": ..., "embedding_model": ... } }
    """
    if not kb_ids:
      return {}

    try:
      client = get_supabase_client(access_token)
      res = (
          client.table(self.table_name)
          .select("id, name, description, retrieval_model, embedding_model:embedding_model_id(name, model_id), embedding_provider:embedding_provider_id(name)")
          .in_("id", kb_ids)
          .eq("tenant_id", tenant_id)
          .execute()
      )

      result_map = {}
      for row in (res.data or []):
        if row.get("embedding_model") and row.get("embedding_provider"):
          provider = row["embedding_provider"].get("name", "ollama")
          model_id = row["embedding_model"].get("model_id")
          if provider and model_id:
            row["embedding_model_name"] = f"{provider}/{model_id}"

        result_map[row["id"]] = row
      return result_map

    except Exception as e:
      logger.exception(
        f"[Supabase] Failed to batch get retrieval models: {e}")
      return {}

  def delete_kb(self, kb_id: str, tenant_id: str, access_token: str = None) -> bool:
    """
    Delete a knowledge base.
    This should trigger ON DELETE CASCADE for metadata and documents if configured in DB.
    """
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .delete()
          .eq("id", kb_id)
          .eq("tenant_id", tenant_id)
          .execute()
      )
      # Check if any row was returned (deleted)
      if response.data:
        logger.info(f"[Supabase] Deleted KB {kb_id}")
        return True
      logger.warning(f"[Supabase] KB {kb_id} not found or not deleted")
      return False
    except Exception as e:
      logger.exception(f"[Supabase] Failed to delete KB {kb_id}: {e}")
      return False

  def get_total_kbs(self, tenant_id: str = None, access_token: str = None) -> int:
    try:
      client = get_supabase_client(access_token)
      res = client.table(self.table_name).select(
        "*", count="exact", head=True)

      if tenant_id:
        res = res.eq("tenant_id", tenant_id)

      res = res.execute()
      return res.count or 0
    except Exception as e:
      logger.exception("Failed to get total KBs count")
      return 0
