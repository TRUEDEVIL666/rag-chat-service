from app.services.supabase.supabase_client import supabase, get_supabase_client
from app.core.logger import get_logger

logger = get_logger("SessionRepository")


class SessionRepository:
  def __init__(self):
    self.table_name = "chat_sessions"

  def create_session(self, user_id: str, bot_id: str, tenant_id: str = None, access_token: str = None) -> dict | None:
    try:
      # Start the query builder
      client = get_supabase_client(access_token) if access_token else supabase
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
      client = get_supabase_client(access_token) if access_token else supabase
      response = (
          client.table(self.table_name)
          .select("*")
          .eq("id", session_id)
          .single()
          .execute()
      )
      if response.data:
        return response.data
      return None
    except Exception as e:
      logger.exception(f"Failed to get session {session_id}: {e}")
      return None

  def list_sessions(self, user_id: str, tenant_id: str, limit: int = 20, offset: int = 0, access_token: str = None) -> list[dict]:
    try:
      client = get_supabase_client(access_token) if access_token else supabase
      query = (
          client.table(self.table_name)
          .select("*")
          .eq("user_id", user_id)
          .order("updated_at", desc=True)
          .range(offset, offset + limit - 1)
      )
      if tenant_id:
        query = query.eq("tenant_id", tenant_id)

      response = query.execute()
      return response.data or []
    except Exception as e:
      logger.exception(f"Failed to list sessions for user {user_id}: {e}")
      return []

  def update_session(self, session_id: str, data: dict) -> dict | None:
    try:
      response = supabase.table(self.table_name).update(
        data).eq("id", session_id).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to update session {session_id}: {e}")
      raise RuntimeError(f"Failed to update session {session_id}: {e}")

  def delete_session(self, session_id: str, user_id: str) -> bool:
    """
    Delete a session.
    This should trigger ON DELETE CASCADE for chat_messages if configured in DB.
    """
    try:
      response = (
          supabase.table(self.table_name)
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

  def get_total_sessions(self, tenant_id: str = None) -> int:
    try:
      q = supabase.table(self.table_name).select("*", count="exact", head=True)
      if tenant_id:
        q = q.eq("tenant_id", tenant_id)
      res = q.execute()
      return res.count or 0
    except Exception as e:
      logger.exception("Failed to get total sessions count")
      return 0
