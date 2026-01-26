from typing import List, Optional
from app.services.supabase.supabase_client import get_async_supabase_client
from app.core.logger import get_logger

logger = get_logger("chat_message_repository")


class ChatMessageRepository:
  def __init__(self):
    self.table_name = "chat_messages"

  async def create_message(self, session_id: str, content: str, role: str, sender_id: Optional[str] = None, access_token: str = None) -> dict | None:
    try:
      client = await get_async_supabase_client(access_token)
      data = {
          "session_id": session_id,
          "content": content,
          "role": role,
          "sender_id": sender_id
      }
      response = await client.table(self.table_name).insert(data).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.error(
        f"Failed to create chat message. Data: {data}, Token (last 6): {access_token[-6:] if access_token else 'None'}. Error: {e}")
      raise RuntimeError(f"Failed to create chat message: {e}")

  async def get_messages_by_session(
      self,
      session_id: str,
      limit: int = 50,
      cursor_timestamp: int = None,
      sort_column: str = "created_at",
      sort_desc: bool = True,
      access_token: str = None
  ) -> List[dict]:
    try:
      client = await get_async_supabase_client(access_token)
      query = (
          client.table(self.table_name)
          .select("*")
          .eq("session_id", session_id)
          .order(sort_column, desc=sort_desc)
          .limit(limit)
      )

      if cursor_timestamp:
        from datetime import datetime, timezone
        dt_cursor = datetime.fromtimestamp(
          cursor_timestamp, tz=timezone.utc).isoformat()
        if sort_desc:
          query = query.lt(sort_column, dt_cursor)
        else:
          query = query.gt(sort_column, dt_cursor)

      response = await query.execute()
      # Reverse to return in chronological order if needed, but usually API returns as is.
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to get messages for session {session_id}: {e}")
      return []

  async def get_analytics_counts(
      self,
      interval: str,
      start_date: str,
      end_date: str,
      access_token: str = None
  ) -> List[dict]:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.rpc("get_message_counts_by_period", {
          "interval_type": interval,
          "start_date": start_date,
          "end_date": end_date
      }).execute()
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to get analytics counts: {e}")
      return []
