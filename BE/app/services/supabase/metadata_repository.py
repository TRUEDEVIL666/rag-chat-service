# app/services/supabase/metadata_repository.py
from datetime import datetime
from typing import List, Dict, Optional

from llama_index.core import Document

from app.core.logger import get_logger
from app.services.supabase.supabase_client import get_supabase_client

logger = get_logger("supabase")


class MetadataRepository:
  """
  Handles storing and querying document metadata and knowledge base info in Supabase.
  """

  def __init__(self, table_name: str = "metadata"):
    self.table_name = table_name

  def store(self, documents: List[Document], access_token: str = None):
    """
    Store metadata for each document chunk into Supabase (Upsert).
    """
    try:
      client = get_supabase_client(access_token)
      records = [self._build_chunk_metadata(doc) for doc in documents]
      # Upsert to ensure we update existing records or insert new ones
      response = client.table(self.table_name).upsert(records).execute()
      if hasattr(response, "error") and response.error:
        logger.error(
            f"[Supabase] Upsert error: {response.error.get('message')}")
      else:
        logger.info(f"[Supabase] Upserted {len(response.data)} records.")
    except Exception as e:
      logger.exception(f"[Supabase] Failed to upsert metadata: {e}")

  def delete_stale_chunks(self, document_id: str, sync_start_time: str, access_token: str = None) -> List[str]:
    """
    Delete chunks that were not updated during the sync process (stale).
    Returns a list of deleted chunk_ids.
    """
    try:
      client = get_supabase_client(access_token)
      # Delete rows where valid_until < sync_start_time ("last_seen_at")
      # We assume 'created_at' is updated during upsert to act as 'last_seen_at'
      response = (
          client.table(self.table_name)
          .delete()
          .eq("document_id", document_id)
          .lt("created_at", sync_start_time)  # Delete older timestamps
          .execute()
      )

      if response.data:
        deleted_ids = [item['chunk_id'] for item in response.data]
        logger.info(
            f"[Supabase] Deleted {len(deleted_ids)} stale chunks for doc {document_id}")
        return deleted_ids
      return []
    except Exception as e:
      logger.exception(
          f"Failed to delete stale chunks for doc {document_id}: {e}")
      return []

  def find_by_filename(self, file_name: str, access_token: str = None) -> Optional[dict]:
    """
    Search metadata by document filename in Supabase.
    """
    try:
      client = get_supabase_client(access_token)
      result = (
          client.table(self.table_name)
          .select("*")
          .eq("document_id", file_name)
          .limit(1)
          .execute()
      )
      return result.data[0] if result.data else None
    except Exception as e:
      logger.exception(
          f"[Supabase] Failed to query by filename '{file_name}': {e}")
      return None

  def get_hashes_by_document(self, document_id: str, access_token: str = None) -> List[Dict[str, str]]:
    """
    Get all chunk_ids and chunk_hashes for a given document.
    """
    try:
      client = get_supabase_client(access_token)
      result = (
          client.table(self.table_name)
          .select("chunk_id, chunk_hash")
          .eq("document_id", document_id)
          .execute()
      )
      return result.data or []
    except Exception as e:
      logger.exception(f"Failed to fetch hashes for doc {document_id}: {e}")
      return []

  def delete_by_document_id(self, document_id: str, access_token: str = None) -> bool:
    """
    Delete all chunks associated with a document_id.
    """
    try:
      client = get_supabase_client(access_token)
      client.table(self.table_name).delete().eq(
          "document_id", document_id).execute()
      logger.info(f"[Supabase] Deleted metadata for document {document_id}")
      return True
    except Exception as e:
      logger.exception(f"Failed to delete metadata for doc {document_id}: {e}")
      return False

  def delete_chunks_by_ids(self, chunk_ids: List[str], access_token: str = None) -> bool:
    """
    Delete specific chunks by their IDs.
    """
    if not chunk_ids:
      return True
    try:
      client = get_supabase_client(access_token)
      client.table(self.table_name).delete().in_(
          "chunk_id", chunk_ids).execute()
      return True
    except Exception as e:
      logger.exception(f"Failed to delete chunks: {e}")
      return False

  def _build_chunk_metadata(self, doc: Document) -> Dict:
    """
    Extract metadata fields from a Document for Supabase insertion.
    """
    meta = doc.metadata or {}
    backlash = '\n'
    kb_id = meta.get("kb_id")
    logger.info(
        f"DEBUG: chunk_text trước khi gửi Supabase: {doc.text[:100].replace(backlash, ' ')} (kiểm tra 100 ký tự đầu)")
    # Remove redundant fields that are already stored in dedicated columns
    redundant_keys = {
        "document_id", "file_path", "kb_id", "tenant_id", "chunk_id",
        "chunk_hash", "chunk_size", "source_file", "file_name", "source"
    }
    clean_meta = {k: v for k, v in meta.items() if k not in redundant_keys}

    return {
        "chunk_text": doc.text,
        "chunk_size": len(doc.text),
        "document_id": meta.get("document_id"),
        "file_path": meta.get("file_path"),
        "source_file": meta.get("file_name") or meta.get("source_file"),
        "source": meta.get("source"),
        "created_at": datetime.utcnow().isoformat(),
        "kb_id": kb_id if kb_id is not None else None,
        "tenant_id": meta.get("tenant_id"),
        "chunk_id": meta.get("chunk_id"),
        "chunk_hash": meta.get("chunk_hash"),
        "metadata": clean_meta,
    }
