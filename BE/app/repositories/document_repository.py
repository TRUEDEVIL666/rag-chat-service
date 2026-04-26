from typing import List
from app.core.supabase_client import get_async_supabase_client
from app.core.logger import get_logger

logger = get_logger(__name__)


class DocumentRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "DocumentRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self.table_name = "documents"

  async def create_document(self, data: dict) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = await client.table(self.table_name).insert(data).execute()
      if response and hasattr(response, "data") and response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"[DocRepo]: Failed to create document: {e}")
      # Don't raise, just return None so processing can continue if DB fails
      return None

  async def get_document_by_id(self, document_id: str) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = (
        await client.table(self.table_name)
        .select("*")
        .eq("id", document_id)
        .maybe_single()
        .execute()
      )
      if response and hasattr(response, "data"):
        return response.data
      return None
    except Exception as e:
      logger.exception(f"Failed to get document {document_id}: {e}")
      return None

  async def get_document_by_name(self, kb_id: str, name: str) -> dict | None:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await get_async_supabase_client()
      response = await (
        client.table(self.table_name)
        .select("*")
        .eq("knowledgebase_id", kb_id)
        .eq("tenant_id", tenant_id)
        .eq("name", name)
        .limit(1)
        .execute()
      )
      if response and hasattr(response, "data") and response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(
        f"Failed to get document by name {name} in KB {kb_id} for tenant {tenant_id}: {e}"
      )
      return None

  async def list_documents(
    self,
    limit: int = 100,
    cursor_timestamp: int = None,
    sort_column: str = "created_at",
    sort_desc: bool = True,
  ) -> List[dict]:
    try:
      client = await get_async_supabase_client()
      query = client.table(self.table_name).select(
        "*, creator:users!created_by(name), knowledgebases(id, name)"
      )

      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      if tenant_id:
        query = query.eq("tenant_id", tenant_id)

      query = query.neq("status", "trashed")

      if cursor_timestamp is not None:
        if sort_desc:
          query = query.lt(sort_column, cursor_timestamp)
        else:
          query = query.gt(sort_column, cursor_timestamp)

      response = await query.order(sort_column, desc=sort_desc).limit(limit).execute()
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to list documents for tenant {tenant_id}: {e}")
      return []

  async def get_documents_by_kb(self, kb_id: str) -> List[dict]:
    """Retrieve all documents associated with a specific Knowledge Base."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await get_async_supabase_client()
      response = await (
        client.table(self.table_name)
        .select("*, creator:users!created_by(name)")
        .eq("knowledgebase_id", kb_id)
        .eq("tenant_id", tenant_id)
        .neq("status", "trashed")
        .execute()
      )
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to get documents for KB {kb_id}: {e}")
      return []

  async def update_document_upload_success(
    self, document_id: str, file_path: str
  ) -> bool:
    """Updates status to 'processing' and sets the valid MinIO path."""
    try:
      client = await get_async_supabase_client()
      await (
        client.table(self.table_name)
        .update({"status": "learning", "path": file_path})
        .eq("id", document_id)
        .execute()
      )
      return True
    except Exception as e:
      logger.exception(f"Failed to update document success {document_id}: {e}")
      return False

  async def update_document_status(self, document_id: str, status: str) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = await (
        client.table(self.table_name)
        .update(
          {
            "status": status,
          }
        )
        .eq("id", document_id)
        .execute()
      )
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to update document status {document_id}: {e}")
      return None

  async def delete_document(self, document_id: str) -> bool:
    try:
      client = await get_async_supabase_client()
      await client.table(self.table_name).delete().eq("id", document_id).execute()
      return True
    except Exception as e:
      logger.exception(f"Failed to delete document {document_id}: {e}")
      return False

  async def count_documents_by_kb(self, kb_id: str) -> int:
    """Count all documents associated with a specific Knowledge Base."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await get_async_supabase_client()
      response = await (
        client.table(self.table_name)
        .select("*", count="exact", head=True)
        .eq("knowledgebase_id", kb_id)
        .eq("tenant_id", tenant_id)
        .neq("status", "trashed")
        .execute()
      )
      return response.count or 0
    except Exception as e:
      logger.exception(f"Failed to count documents for KB {kb_id}: {e}")
      return 0

  async def get_total_documents(self) -> int:
    """Count all documents in the system (Global)."""
    try:
      client = await get_async_supabase_client()
      response = await (
        client.table(self.table_name)
        .select("*", count="exact", head=True)
        .neq("status", "trashed")
        .execute()
      )
      return response.count or 0
    except Exception as e:
      logger.exception(f"Failed to count total documents: {e}")
      return 0
