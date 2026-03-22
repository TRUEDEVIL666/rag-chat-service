# app/services/supabase/graph_chunk_repository.py
from datetime import datetime
from typing import List, Dict, Optional

from llama_index.core import Document

from app.core.logger import get_logger
from app.services.supabase.supabase_client import get_async_supabase_client

logger = get_logger(__name__)


class GraphChunkRepository:
  """
  Handles storing and querying document chunks (graph nodes) in Supabase.
  Table: "graph_chunks" (renamed from metadata)
  """

  def __init__(self, table_name: str = "graph_chunks"):
    self.table_name = table_name

  async def store(self, documents: List[Document], access_token: str = None):
    """
    Store metadata for each document chunk into Supabase (Upsert).
    """
    try:
      client = await get_async_supabase_client(access_token)
      records = [self._build_chunk_metadata(doc) for doc in documents]
      # Upsert to ensure we update existing records or insert new ones
      response = await client.table(self.table_name).upsert(records).execute()
      if hasattr(response, "error") and response.error:
        logger.error(
            f"[GraphChunkRepo]: Upsert error: {response.error.get('message')}")
      else:
        logger.info(
          f"[GraphChunkRepo]: Upserted {len(response.data)} records.")
    except Exception as e:
      logger.exception(f"[GraphChunkRepo]: Failed to upsert chunks: {e}")

  async def delete_stale_nodes(self, document_id: str, active_ids: List[str], access_token: str = None) -> List[str]:
    """
    Delete nodes that are no longer active (not present in the current update).
    """
    try:
      client = await get_async_supabase_client(access_token)

      query = client.table(self.table_name).delete().eq(
        "document_id", document_id)

      if active_ids:
        # Format IDs for PostgREST: (id1,id2,id3)
        ids_param = f"({','.join(str(cid) for cid in active_ids)})"
        query = query.filter("id", "not.in", ids_param)

      response = await query.execute()
      deleted_ids = [item['id'] for item in (response.data or [])]

      if deleted_ids:
        logger.info(
            f"[GraphChunkRepo]: Deleted {len(deleted_ids)} stale nodes for doc {document_id}")

      return deleted_ids

    except Exception as e:
      logger.exception(
          f"Failed to delete stale chunks for doc {document_id}: {e}")
      return []

  async def find_by_filename(self, file_name: str, access_token: str = None) -> Optional[dict]:
    """
    Search chunks by document filename in Supabase (less common for chunks, but kept for compatibility).
    """
    try:
      client = await get_async_supabase_client(access_token)
      result = await (
          client.table(self.table_name)
          .select("*")
          # Potential bug in original code: eq("document_id", file_name)? Kept as is.
          .eq("document_id", file_name)
          .limit(1)
          .execute()
      )
      return result.data[0] if result.data else None
    except Exception as e:
      logger.exception(
          f"[GraphChunkRepo]: Failed to query by filename '{file_name}': {e}")
      return None

  async def get_chunks_by_doc_id(self, document_id: str, access_token: str = None) -> List[Dict]:
    """
    Get all chunks for a document.
    """
    try:
      client = await get_async_supabase_client(access_token)
      result = await (
          client.table(self.table_name)
          .select("*")
          .eq("document_id", document_id)
          .execute()
      )
      return result.data or []
    except Exception as e:
      logger.exception(
        f"[GraphChunkRepo]: Failed to get chunks for doc {document_id}: {e}")
      return []

  async def get_hashes_by_document(self, document_id: str, access_token: str = None) -> List[Dict[str, str]]:
    """
    Get all ids and chunk_hashes for a given document.
    """
    try:
      client = await get_async_supabase_client(access_token)
      result = await (
          client.table(self.table_name)
          .select("id, chunk_hash")
          .eq("document_id", document_id)
          .execute()
      )
      return result.data or []
    except Exception as e:
      logger.exception(
        f"[GraphChunkRepo]: Failed to fetch hashes for doc {document_id}: {e}")
      return []

  async def delete_by_document_id(self, document_id: str, access_token: str = None) -> bool:
    """
    Delete all chunks associated with a document_id.
    """
    try:
      client = await get_async_supabase_client(access_token)
      await client.table(self.table_name).delete().eq(
          "document_id", document_id).execute()
      logger.info(
        f"[GraphChunkRepo]: Deleted chunks for document {document_id}")
      return True
    except Exception as e:
      logger.exception(
        f"[GraphChunkRepo]: Failed to delete chunks for doc {document_id}: {e}")
      return False

  def _build_chunk_metadata(self, doc: Document) -> Dict:
    """
    Extract metadata fields from a Document for Supabase insertion.
    """
    meta = doc.metadata or {}
    kb_id = meta.get("kb_id")
    tenant_id = meta.get("tenant_id")

    # Remove redundant fields that are already stored in dedicated columns
    redundant_keys = {
        "document_id", "file_path", "kb_id", "tenant_id",
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
        # New Promoted Columns
        "kb_id": kb_id if kb_id is not None else None,
        "tenant_id": tenant_id if tenant_id is not None else None,
        "id": doc.node_id,
        "chunk_hash": meta.get("chunk_hash"),
        "metadata": clean_meta,
    }
