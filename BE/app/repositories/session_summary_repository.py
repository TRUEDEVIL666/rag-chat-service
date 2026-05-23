from datetime import datetime, timezone
from typing import Optional

from app.repositories.base_repository import BaseRepository


class SessionSummaryRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="session_summaries")

  async def upsert_summary(
    self,
    session_id: str,
    summary_text: str,
    facts: Optional[dict] = None,
    version: int = 1,
    access_token: str = None,
  ) -> dict | None:
    try:
      client = await self._get_client(access_token)
      data = {
        "session_id": session_id,
        "summary_text": summary_text,
        "facts": facts,
        "version": version,
        "updated_at": datetime.now(timezone.utc).isoformat(),
      }
      response = (
        await client.table(self.table_name)
        .upsert(data, on_conflict="session_id")
        .execute()
      )
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      self.logger.exception(f"Failed to upsert session summary for {session_id}: {e}")
      raise RuntimeError(f"Failed to upsert session summary for {session_id}: {e}")

  async def get_summary_by_session(
    self, session_id: str, access_token: str = None
  ) -> dict | None:
    try:
      client = await self._get_client(access_token)
      response = await (
        client.table(self.table_name)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
      )
      if response.data:
        return response.data
      return None
    except Exception:
      # It's okay if summary doesn't exist
      return None
