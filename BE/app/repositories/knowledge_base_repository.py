# app/services/supabase/knowledge_base_repository.py
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.repositories.base_repository import BaseRepository


class KnowledgeBaseRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="knowledgebases")

  async def check_exists(self, kb_name: str) -> bool:
    """Kiểm tra knowledge base đã tồn tại theo tenant + kb_name"""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
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
      self.logger.exception(f"[KBRepo]: Error checking KB exists: {e}")
      return False

  async def create(self, kb_data: dict) -> Optional[dict]:
    """Tạo mới knowledge base (nếu chưa tồn tại)."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      kb_name = kb_data["name"]

      if await self.check_exists(kb_name):
        raise ValueError(f"Knowledge base '{kb_name}' already exists.")

      kb_data["tenant_id"] = tenant_id
      kb_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())

      result = await self.insert(kb_data)
      created = result[0] if result else None
      if not created:
        self.logger.error("[KBRepo]: Insert KB returned no data")
        return None

      self.logger.info(f"[KBRepo]: Created KB: {kb_name}")
      return created

    except Exception as e:
      self.logger.exception(f"[KBRepo]: Failed to create knowledge base: {e}")
      return None

  async def list_knowledge_bases(self):
    """Trả danh sách KB theo spec /knowledge_bases, kèm total."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
      q = await (
        client.table(self.table_name)
        .select(
          "*, embedding_provider:embedding_provider_id(name), embedding_model:embedding_model_id(name, model_id, is_active)"
        )
        .eq("tenant_id", tenant_id)
        .execute()
      )

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
      self.logger.exception(f"[KBRepo]: Failed to list knowledge bases: {e}")
      return [], 0

  async def get_knowledge_base_detail(self, knowledge_base_id: str) -> Optional[dict]:
    """Lấy chi tiết 1 KB theo id + tenant scope."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
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
      self.logger.exception(
        f"[KBRepo]: Failed to get knowledge base detail {knowledge_base_id}: {e}"
      )
      return None

  async def get_one(self, kb_id: str) -> Optional[dict]:
    from app.core.context import get_current_tenant_id

    tenant_id = get_current_tenant_id()
    client = await self._get_client()
    res = await (
      client.table(self.table_name)
      .select(
        "*, embedding_provider:embedding_provider_id(name), embedding_model:embedding_model_id(name, model_id)"
      )
      .eq("id", kb_id)
      .eq("tenant_id", tenant_id)
      .limit(1)
      .execute()
    )

    data = (res.data or [None])[0]
    if data:
      if data.get("embedding_model") and data.get("embedding_provider"):
        provider = data["embedding_provider"].get("name", "ollama")
        model_id = data["embedding_model"].get("model_id")
        if provider and model_id:
          data["embedding_model_name"] = f"{provider}/{model_id}"

    return data

  async def name_conflict(self, name: str, exclude_id: str) -> bool:
    from app.core.context import get_current_tenant_id

    tenant_id = get_current_tenant_id()
    client = await self._get_client()
    res = await (
      client.table(self.table_name)
      .select("id")
      .eq("tenant_id", tenant_id)
      .eq("name", name)
      .neq("id", exclude_id)
      .limit(1)
      .execute()
    )
    return bool(res.data)

  async def patch(self, kb_id: str, fields: Dict[str, Any]) -> Optional[dict]:
    if not fields:
      return await self.get_one(kb_id)

    from app.core.context import get_current_tenant_id

    tenant_id = get_current_tenant_id()
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    client = await self._get_client()
    await (
      client.table(self.table_name)
      .update(fields)
      .eq("id", kb_id)
      .eq("tenant_id", tenant_id)
      .execute()
    )
    return await self.get_one(kb_id)

  async def get_retrieval_configs_by_ids(self, kb_ids: List[str]) -> Dict[str, dict]:
    """Batch fetch retrieval configs for multiple KBs."""
    if not kb_ids:
      return {}

    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
      res = await (
        client.table(self.table_name)
        .select(
          "id, name, description, retrieval_model, embedding_model:ai_models(name, model_id), embedding_provider:ai_providers(name)"
        )
        .in_("id", kb_ids)
        .eq("tenant_id", tenant_id)
        .execute()
      )

      result_map = {}
      for row in res.data or []:
        if row.get("embedding_model") and row.get("embedding_provider"):
          provider = row["embedding_provider"].get("name", "ollama")
          model_id = row["embedding_model"].get("model_id")
          if provider and model_id:
            row["embedding_model_name"] = f"{provider}/{model_id}"

        result_map[row["id"]] = row
      return result_map

    except Exception as e:
      self.logger.exception(f"[KBRepo]: Failed to batch get retrieval models: {e}")
      return {}

  async def delete_kb(self, kb_id: str) -> bool:
    """Delete a knowledge base."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
      response = await (
        client.table(self.table_name)
        .delete()
        .eq("id", kb_id)
        .eq("tenant_id", tenant_id)
        .execute()
      )
      if response.data:
        self.logger.info(f"[KBRepo]: Deleted KB {kb_id}")
        return True
      self.logger.warning(f"[KBRepo]: KB {kb_id} not found or not deleted")
      return False
    except Exception as e:
      self.logger.exception(f"[KBRepo]: Failed to delete KB {kb_id}: {e}")
      return False

  async def get_total_kbs(self) -> int:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
      res = client.table(self.table_name).select("*", count="exact", head=True)

      if tenant_id:
        res = res.eq("tenant_id", tenant_id)

      res = await res.execute()
      return res.count or 0
    except Exception:
      self.logger.exception("Failed to get total KBs count")
      return 0
