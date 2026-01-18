from app.services.supabase.supabase_client import get_supabase_client
from app.core.logger import get_logger

logger = get_logger("SessionRepository")


class SessionRepository:
  def __init__(self):
    self.table_name = "chat_sessions"

  def create_session(self, user_id: str, bot_id: str, tenant_id: str = None, access_token: str = None) -> dict | None:
    try:
      # Start the query builder
      client = get_supabase_client(access_token)
      payload = {
          "user_id": user_id,
          "bot_id": bot_id
      }
      if tenant_id:
        payload["tenant_id"] = tenant_id

      query = client.table(self.table_name).insert(payload)

      result = query.execute()
      if result.data:
        return result.data[0]

      return None
    except Exception as e:
      logger.exception("Failed to create session: " + str(e))
      raise Exception("Failed to create session: " + str(e))

  def get_session(self, session_id: str, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .select("*, bots(name)")
          .eq("id", session_id)
          .maybe_single()
          .execute()
      )
      if response.data:
        return response.data
      return None
    except Exception as e:
      logger.exception(f"Failed to get session {session_id}: {e}")
      return None

  def list_sessions(self, user_id: str, tenant_id: str, limit: int = 20, cursor_timestamp: int = None, access_token: str = None, bot_id: str = None, search: str = None, start_date=None, end_date=None) -> list[dict]:
    try:
      client = get_supabase_client(access_token)
      query = (
          client.table(self.table_name)
          .select("*, bots(name)")
          .eq("user_id", user_id)
          .order("updated_at", desc=True)
          .limit(limit)
      )

      from datetime import datetime

      if cursor_timestamp:
        from datetime import datetime, timezone
        # Assuming cursor_timestamp is unix timestamp (int).
        dt_cursor = datetime.fromtimestamp(
          cursor_timestamp, tz=timezone.utc).isoformat()
        query = query.lt("updated_at", dt_cursor)

      if tenant_id:
        query = query.eq("tenant_id", tenant_id)
      if bot_id:
        query = query.eq("bot_id", bot_id)

      if search:
        # Search in summary_text and title
        # Note: We can't easily search foreign table 'bots.name' with OR in the same query via JS client syntax effortlessly without raw SQL or embedded resource filtering.
        # Sticking to session fields for now.
        search_filter = f"summary_text.ilike.%{search}%,title.ilike.%{search}%"
        query = query.or_(search_filter)

      if start_date:
        query = query.gte("updated_at", start_date.isoformat()
                          if isinstance(start_date, datetime) else start_date)

      if end_date:
        query = query.lte("updated_at", end_date.isoformat()
                          if isinstance(end_date, datetime) else end_date)

      response = query.execute()
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to list sessions for user {user_id}: {e}")
      return []

  def update_session(self, session_id: str, data: dict, access_token: str = None) -> dict | None:
    try:
      client = get_supabase_client(access_token)
      response = client.table(self.table_name).update(
        data).eq("id", session_id).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to update session {session_id}: {e}")
      raise RuntimeError(f"Failed to update session {session_id}: {e}")

  def delete_session(self, session_id: str, user_id: str, access_token: str = None) -> bool:
    """
    Delete a session.
    This should trigger ON DELETE CASCADE for chat_messages if configured in DB.
    """
    try:
      client = get_supabase_client(access_token)
      response = (
          client.table(self.table_name)
          .delete()
          .eq("id", session_id)
          .eq("user_id", user_id)
          .execute()
      )
      if response.data:
        logger.info(f"Deleted session {session_id}")
        return True
      logger.warning(f"Session {session_id} not found or permission denied")
      return False
    except Exception as e:
      logger.exception(f"Failed to delete session {session_id}: {e}")
      return False

  def get_total_sessions(self, tenant_id: str = None, access_token: str = None) -> int:
    try:
      client = get_supabase_client(access_token)
      q = client.table(self.table_name).select("*", count="exact", head=True)
      if tenant_id:
        q = q.eq("tenant_id", tenant_id)
      res = q.execute()
      return res.count or 0
    except Exception as e:
      logger.exception("Failed to get total sessions count")
      return 0
