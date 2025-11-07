# app/services/supabase/metadata_repository.py
from datetime import datetime
from typing import List, Dict, Optional

from llama_index.core import Document

from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase

logger = get_logger("supabase")

class MetadataRepository:
    """
    Handles storing and querying document metadata and knowledge base info in Supabase.
    """

    def __init__(self, table_name: str = "metadata"):
        self.table_name = table_name

    def store(self, documents: List[Document]):
        """
        Store metadata for each document chunk into Supabase.
        """
        try:
            records = [self._build_chunk_metadata(doc) for doc in documents]
            response = supabase.table(self.table_name).insert(records).execute()
            if hasattr(response, "error") and response.error:
                logger.error(f"[Supabase] Insert error: {response.error.get('message')}")
            else:
                logger.info(f"[Supabase] Inserted {len(response.data)} records.")
        except Exception as e:
            logger.exception(f"[Supabase] Failed to insert metadata: {e}")

    def find_by_filename(self, file_name: str) -> Optional[dict]:
        """
        Search metadata by document filename in Supabase.
        """
        try:
            result = (
                supabase.table(self.table_name)
                .select("*")
                .eq("document_id", file_name)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.exception(f"[Supabase] Failed to query by filename '{file_name}': {e}")
            return None

    def _build_chunk_metadata(self, doc: Document) -> Dict:
        """
        Extract metadata fields from a Document for Supabase insertion.
        """
        meta = doc.metadata or {}
        backlash = '\n'
        kb_id = meta.get("kb_id")
        logger.info(f"DEBUG: chunk_text trước khi gửi Supabase: {doc.text[:100].replace(backlash, ' ')} (kiểm tra 100 ký tự đầu)")
        return {
            "chunk_text": doc.text,
            "chunk_size": len(doc.text),
            "document_id": meta.get("document_id"),
            "file_path": meta.get("file_path"),
            "source_file": meta.get("file_name") or meta.get("source_file"),
            "source": meta.get("source"),
            "created_at": datetime.utcnow().isoformat(),
            "tenant_id": meta.get("tenant_id"),
            "kb_id": kb_id if kb_id is not None else None,
            "chunk_id": meta.get("chunk_id"),
            "chunk_hash": meta.get("chunk_hash"),
        }