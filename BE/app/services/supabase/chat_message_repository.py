from typing import List, Optional
from app.services.supabase.supabase_client import get_supabase_client, supabase
from app.core.logger import get_logger

logger = get_logger("chat_message_repository")


class ChatMessageRepository:
  def __init__(self):
    self.table_name = "chat_messages"

  def create_message(self, session_id: str, content: str, role: str, sender_id: Optional[str] = None, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token) if access_token else supabase
      data = {
          "session_id": session_id,
          "content": content,
          "role": role,
          "sender_id": sender_id
      }
      response = client.table(self.table_name).insert(data).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to create chat message: {e}")
      raise RuntimeError(f"Failed to create chat message: {e}")

  def get_messages_by_session(self, session_id: str, limit: int = 50, offset: int = 0, access_token: str = None) -> List[dict]:
    try:
      client = get_supabase_client(access_token) if access_token else supabase
      response = (
          client.table(self.table_name)
          .select("*")
          .eq("session_id", session_id)
          # Usually we want latest first for pagination, or asc for display. Let's do desc for now.
          .order("created_at", desc=True)
          .range(offset, offset + limit - 1)
          .execute()
      )
      # Reverse to return in chronological order if needed, but usually API returns as is.
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to get messages for session {session_id}: {e}")
      return []
