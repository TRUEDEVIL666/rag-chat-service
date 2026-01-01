from typing import Optional
from app.services.supabase.supabase_client import get_supabase_client
from app.core.logger import get_logger

logger = get_logger("session_summary_repository")


class SessionSummaryRepository:
  def __init__(self):
    self.table_name = "session_summaries"

  def upsert_summary(self, session_id: str, summary_text: str, facts: Optional[dict] = None, version: int = 1) -> dict | None:
    try:
      client = get_supabase_client()
      data = {
          "session_id": session_id,
          "summary_text": summary_text,
          "facts": facts,
          "version": version
      }
      # Upsert based on session_id (unique constraint)
      response = client.table(self.table_name).upsert(
        data, on_conflict="session_id").execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(
        f"Failed to upsert session summary for {session_id}: {e}")
      raise RuntimeError(
        f"Failed to upsert session summary for {session_id}: {e}")

  def get_summary_by_session(self, session_id: str) -> dict | None:
    try:
      client = get_supabase_client()
      response = (
          client.table(self.table_name)
          .select("*")
          .eq("session_id", session_id)
          .single()
          .execute()
      )
      if response.data:
        return response.data
      return None
    except Exception as e:
      # It's okay if summary doesn't exist
      return None
