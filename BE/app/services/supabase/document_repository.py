from typing import List, Optional, Tuple
from uuid import UUID
from app.services.supabase.supabase_client import get_supabase_client
from app.core.logger import get_logger

logger = get_logger("document_repository")


class DocumentRepository:
  def __init__(self):
    self.table_name = "documents"

  def create_document(self, data: dict, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token)
      response = client.table(self.table_name).insert(data).execute()
      if response and hasattr(response, 'data') and response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"[Supabase] Failed to create document: {e}")
      # Don't raise, just return None so processing can continue if DB fails
      return None

  def get_document_by_id(self, document_id: str, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token)
      response = client.table(self.table_name).select(
        "*").eq("id", document_id).maybe_single().execute()
      if response and hasattr(response, 'data'):
        return response.data
      return None
    except Exception as e:
      logger.exception(f"Failed to get document {document_id}: {e}")
      return None

  def get_document_by_name(self, kb_id: str, name: str, tenant_id: str, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .select("*")
          .eq("knowledgebase_id", kb_id)
          .eq("tenant_id", tenant_id)
          .eq("name", name)
          .limit(1)
          .execute()
      )
      if response and hasattr(response, 'data') and response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(
          f"Failed to get document by name {name} in KB {kb_id} for tenant {tenant_id}: {e}")
      return None

  def list_documents(
      self,
      tenant_id: str = None,
      limit: int = 100,
      cursor_timestamp: int = None,
      sort_column: str = "created_at",
      sort_desc: bool = True,
      access_token: str = None
  ) -> List[dict]:
    try:
      client = get_supabase_client(access_token)
      query = client.table(self.table_name).select(
        "*, creator:users!created_by(name), knowledgebases(id, name)")

      if tenant_id:
        query = query.eq("tenant_id", tenant_id)

      query = query.neq("status", "trashed")

      if cursor_timestamp is not None:
        if sort_desc:
          query = query.lt(sort_column, cursor_timestamp)
        else:
          query = query.gt(sort_column, cursor_timestamp)

      response = (
          query
          .order(sort_column, desc=sort_desc)
          .limit(limit)
          .execute()
      )
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to list documents for tenant {tenant_id}: {e}")
      return []

  def get_documents_by_kb(self, kb_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    """Retrieve all documents associated with a specific Knowledge Base."""
    try:
      client = get_supabase_client(access_token)
      response = (
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

  def update_document_upload_success(self, document_id: str, file_path: str, access_token: str = None) -> bool:
    """Updates status to 'processing' and sets the valid MinIO path."""
    try:
      client = get_supabase_client(access_token)
      client.table(self.table_name).update({
          "status": "learning",
          "path": file_path
      }).eq("id", document_id).execute()
      return True
    except Exception as e:
      logger.exception(f"Failed to update document success {document_id}: {e}")
      return False

  def update_document_status(self, document_id: str, status: str, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .update({
              "status": status,
          })
          .eq("id", document_id)
          .execute()
      )
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to update document status {document_id}: {e}")
      return None

  def delete_document(self, document_id: str, access_token: str = None) -> bool:
    try:
      client = get_supabase_client(access_token)
      client.table(self.table_name).delete().eq("id", document_id).execute()
      return True
    except Exception as e:
      logger.exception(f"Failed to delete document {document_id}: {e}")
      return False

  def count_documents_by_kb(self, kb_id: str, tenant_id: str, access_token: str = None) -> int:
    """Count all documents associated with a specific Knowledge Base."""
    try:
      client = get_supabase_client(access_token)
      response = (
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

  def get_total_documents(self, access_token: str = None) -> int:
    """Count all documents in the system (Global)."""
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .select("*", count="exact", head=True)
          .neq("status", "trashed")
          .execute()
      )
      return response.count or 0
    except Exception as e:
      logger.exception(f"Failed to count total documents: {e}")
      return 0
