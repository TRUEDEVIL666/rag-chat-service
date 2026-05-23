from typing import List

from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="documents")

  async def create_document(self, data: dict) -> dict | None:
    try:
      result = await self.insert(data)
      return result[0] if result else None
    except Exception as e:
      self.logger.exception(f"[DocRepo]: Failed to create document: {e}")
      return None

  async def get_document_by_id(self, document_id: str) -> dict | None:
    try:
      client = await self._get_client()
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
      self.logger.exception(f"Failed to get document {document_id}: {e}")
      return None

  async def get_document_by_name(self, kb_id: str, name: str) -> dict | None:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
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
      self.logger.exception(f"Failed to get document by name {name} in KB {kb_id}: {e}")
      return None

  async def list_documents(
    self,
    limit: int = 100,
    cursor_timestamp: int = None,
    sort_column: str = "created_at",
    sort_desc: bool = True,
  ) -> List[dict]:
    try:
      client = await self._get_client()
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
      self.logger.exception(f"Failed to list documents: {e}")
      return []

  async def get_documents_by_kb(self, kb_id: str) -> List[dict]:
    """Retrieve all documents associated with a specific Knowledge Base."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
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
      self.logger.exception(f"Failed to get documents for KB {kb_id}: {e}")
      return []

  async def update_document_upload_success(
    self, document_id: str, file_path: str
  ) -> bool:
    """Updates status to 'learning' and sets the valid MinIO path."""
    try:
      await self.update("id", document_id, {"status": "learning", "path": file_path})
      return True
    except Exception as e:
      self.logger.exception(f"Failed to update document success {document_id}: {e}")
      return False

  async def update_document_status(self, document_id: str, status: str) -> dict | None:
    try:
      result = await self.update("id", document_id, {"status": status})
      return result[0] if result else None
    except Exception as e:
      self.logger.exception(f"Failed to update document status {document_id}: {e}")
      return None

  async def delete_document(self, document_id: str) -> bool:
    try:
      await self.delete("id", document_id)
      return True
    except Exception as e:
      self.logger.exception(f"Failed to delete document {document_id}: {e}")
      return False

  async def count_documents_by_kb(self, kb_id: str) -> int:
    """Count all documents associated with a specific Knowledge Base."""
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
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
      self.logger.exception(f"Failed to count documents for KB {kb_id}: {e}")
      return 0

  async def get_total_documents(self) -> int:
    """Count all documents in the system (Global)."""
    try:
      client = await self._get_client()
      response = await (
        client.table(self.table_name)
        .select("*", count="exact", head=True)
        .neq("status", "trashed")
        .execute()
      )
      return response.count or 0
    except Exception as e:
      self.logger.exception(f"Failed to count total documents: {e}")
      return 0
