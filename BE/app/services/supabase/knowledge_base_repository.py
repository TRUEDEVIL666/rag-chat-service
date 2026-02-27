# app/services/supabase/knowledge_base_repository.py

from datetime import datetime, timezone
from app.services.supabase.supabase_client import get_async_supabase_client
from app.core.logger import get_logger
from typing import Any, Dict, Optional, List, Tuple

logger = get_logger(__name__)


class KnowledgeBaseRepository:
  def __init__(self):
    self.table_name = "knowledgebases"

  async def check_exists(self, tenant_id: str, kb_name: str, access_token: str = None) -> bool:
    """
    Kiểm tra knowledge base đã tồn tại theo tenant + kb_name
    """
    try:
      client = await get_async_supabase_client(access_token)
      response = await (
          client.table(self.table_name)
          .select("id")
          .eq("tenant_id", tenant_id)
          .eq("name", kb_name)
          .limit(1)
          .execute()
      )
      return bool(response.data)
    except Exception as e:
      logger.exception(f"[KBRepo]: Error checking KB exists: {e}")
      return False

  async def create(self, kb_data: dict, access_token: str = None) -> Optional[dict]:
    """
    Tạo mới knowledge base (nếu chưa tồn tại). Trả về toàn bộ bản ghi vừa insert.
    """
    try:
      tenant_id = kb_data["tenant_id"]
      kb_name = kb_data["name"]

      if await self.check_exists(tenant_id, kb_name, access_token):
        raise ValueError(f"Knowledge base '{kb_name}' already exists.")

      kb_data.setdefault("created_at", datetime.utcnow().isoformat())

      client = await get_async_supabase_client(access_token)
      response = await client.table(self.table_name).insert(kb_data).execute()

      created = response.data[0] if getattr(response, "data", None) else None
      if not created:
        err = getattr(response, "error", None)
        if err:
          logger.error(
            f"[KBRepo]: Insert KB error: {getattr(err, 'message', err)}")
        else:
          logger.error("[KBRepo]: Insert KB returned no data")
        return None

      logger.info(f"[KBRepo]: Created KB: {kb_name}")
      return created

    except Exception as e:
      logger.exception(f"[KBRepo]: Failed to create knowledge base: {e}")
      return None

  async def list_knowledge_bases(
      self,
      tenant_id: str,
      access_token: str = None,
  ):
    """
    Trả danh sách KB theo spec /knowledge_bases, kèm total.
    """
    try:
      client = await get_async_supabase_client(access_token)
      q = await (client.table(self.table_name)
                 .select("*, embedding_provider:embedding_provider_id(name), embedding_model:embedding_model_id(name, model_id, is_active)")
                 .eq("tenant_id", tenant_id)
                 .execute())

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
      logger.exception(f"[KBRepo]: Failed to list knowledge bases: {e}")
      return [], 0

  async def get_knowledge_base_detail(
      self,
      knowledge_base_id: str,
      tenant_id: str,
      access_token: str = None
  ) -> Optional[dict]:
    """
    Lấy chi tiết 1 KB theo id + tenant scope.
    """
    try:
      client = await get_async_supabase_client(access_token)
      kb_q = await (
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
        f"[KBRepo]: Failed to get knowledge base detail {knowledge_base_id}: {e}")
      return None

  async def get_one(self, kb_id: str, tenant_id: str, access_token: str = None) -> Optional[dict]:
    client = await get_async_supabase_client(access_token)
    res = await (client.table(self.table_name)
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

  async def name_conflict(self, tenant_id: str, name: str, exclude_id: str, access_token: str = None) -> bool:
    client = await get_async_supabase_client(access_token)
    res = await (client.table(self.table_name)
                 .select("id").eq("tenant_id", tenant_id).eq("name", name)
                 .neq("id", exclude_id).limit(1).execute())
    return bool(res.data)

  async def patch(self, kb_id: str, tenant_id: str, fields: Dict[str, Any], access_token: str = None) -> Optional[dict]:
    if not fields:
      return await self.get_one(kb_id, tenant_id, access_token)

    fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    client = await get_async_supabase_client(access_token)
    res = await (client.table(self.table_name)
                 .update(fields)
                 .eq("id", kb_id).eq("tenant_id", tenant_id)
                 .execute())
    # Return get_one to ensure consistency with list/get views (e.g. joined fields)
    return await self.get_one(kb_id, tenant_id, access_token)

  async def get_retrieval_configs_by_ids(self, kb_ids: List[str], tenant_id: str, access_token: str = None) -> Dict[str, dict]:
    """
    Batch fetch retrieval configs for multiple KBs.
    Returns: { kb_id: { "retrieval_model": ..., "embedding_model": ... } }
    """
    if not kb_ids:
      return {}

    try:
      client = await get_async_supabase_client(access_token)
      res = await (
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
        f"[KBRepo]: Failed to batch get retrieval models: {e}")
      return {}

  async def delete_kb(self, kb_id: str, tenant_id: str, access_token: str = None) -> bool:
    """
    Delete a knowledge base.
    This should trigger ON DELETE CASCADE for metadata and documents if configured in DB.
    """
    try:
      client = await get_async_supabase_client(access_token)
      response = await (
          client.table(self.table_name)
          .delete()
          .eq("id", kb_id)
          .eq("tenant_id", tenant_id)
          .execute()
      )
      # Check if any row was returned (deleted)
      if response.data:
        logger.info(f"[KBRepo]: Deleted KB {kb_id}")
        return True
      logger.warning(f"[KBRepo]: KB {kb_id} not found or not deleted")
      return False
    except Exception as e:
      logger.exception(f"[KBRepo]: Failed to delete KB {kb_id}: {e}")
      return False

  async def get_total_kbs(self, tenant_id: str = None, access_token: str = None) -> int:
    try:
      client = await get_async_supabase_client(access_token)
      res = client.table(self.table_name).select(
        "*", count="exact", head=True)

      if tenant_id:
        res = res.eq("tenant_id", tenant_id)

      res = await res.execute()
      return res.count or 0
    except Exception as e:
      logger.exception("Failed to get total KBs count")
      return 0
