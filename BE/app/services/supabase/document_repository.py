from typing import List, Optional
from uuid import UUID
from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger

logger = get_logger("document_repository")


class DocumentRepository:
  def __init__(self):
    self.table_name = "documents"

  def create_document(self, data: dict) -> dict | None:
    try:
      response = supabase.table(self.table_name).insert(data).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to create document: {e}")
      # Don't raise, just return None so processing can continue if DB fails
      return None

  def get_document_by_id(self, document_id: str) -> dict | None:
    try:
      response = supabase.table(self.table_name).select(
        "*").eq("id", document_id).single().execute()
      if response.data:
        return response.data
      return None
    except Exception as e:
      logger.exception(f"Failed to get document {document_id}: {e}")
      return None

  def list_documents(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[dict]:
    try:
      response = (
          supabase.table(self.table_name)
          .select("*")
          .eq("tenant_id", tenant_id)
          .range(offset, offset + limit - 1)
          .order("created_at", desc=True)
          .execute()
      )
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to list documents for tenant {tenant_id}: {e}")
      return []

  def update_document_status(self, document_id: str, status: str) -> dict | None:
    try:
      response = (
          supabase.table(self.table_name)
          .update({"status": status})
          .eq("id", document_id)
          .execute()
      )
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to update document status {document_id}: {e}")
      return None

  def delete_document(self, document_id: str) -> bool:
    try:
      supabase.table(self.table_name).delete().eq("id", document_id).execute()
      return True
    except Exception as e:
      logger.exception(f"Failed to delete document {document_id}: {e}")
      return False
