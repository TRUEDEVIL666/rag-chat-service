from typing import List, Optional
from app.services.supabase.supabase_client import get_async_supabase_client
from app.core.logger import get_logger

logger = get_logger(__name__)


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

  async def get_message_count_by_bot(self, bot_id: str, access_token: str = None, filter_user_ids: List[str] = None) -> int:
    try:
      client = await get_async_supabase_client(access_token)
      # Count messages for specific bot by inner joining with chat_sessions
      query = client.table(self.table_name)\
          .select("id, chat_sessions!inner(bot_id, user_id)", count="exact", head=True)\
          .eq("role", "user")\
          .eq("chat_sessions.bot_id", bot_id)

      if filter_user_ids is not None:
        if not filter_user_ids:
          return 0
        query = query.in_("chat_sessions.user_id", filter_user_ids)

      response = await query.execute()

      return response.count if hasattr(response, "count") else 0
    except Exception as e:
      logger.error(f"Failed to get message count for bot {bot_id}: {e}")
      return 0

  async def get_top_active_user_ids(self, limit_messages: int = 2000, access_token: str = None) -> List[dict]:
    """
    Identifies top active users based on message volume in the last N messages.
    Returns a list of dicts: {'user_id': str, 'count': int}
    """
    try:
      client = await get_async_supabase_client(access_token)

      response = await client.table(self.table_name)\
          .select("id, chat_sessions!inner(user_id)")\
          .eq("role", "user")\
          .order("created_at", desc=True)\
          .limit(limit_messages)\
          .execute()

      messages = response.data or []

      # Aggregate in Python
      from collections import Counter
      user_counts = Counter()

      for msg in messages:
        session = msg.get("chat_sessions")
        if session:
          # If header join returns list (rare for N:1 but possible depending on definition), handle it
          if isinstance(session, list):
            uid = session[0].get("user_id") if session else None
          else:
            uid = session.get("user_id")

          if uid:
            user_counts[uid] += 1

      # Convert to list of dicts
      top_users = [
          {"user_id": uid, "count": count}
          for uid, count in user_counts.most_common(5)  # Top 5
      ]

      return top_users

    except Exception as e:
      logger.error(f"Failed to get top active users: {e}")
      return []

  async def update_message_rating(self, message_id: str, rating: Optional[str], access_token: str = None) -> bool:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.table(self.table_name).update({"rating": rating}).eq("id", message_id).execute()
      return len(response.data) > 0
    except Exception as e:
      logger.error(f"Failed to update message rating for {message_id}: {e}")
      return False
