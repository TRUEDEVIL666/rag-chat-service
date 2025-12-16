from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger

logger = get_logger("SessionRepository")


class SessionRepository:
  def __init__(self):
    self.table_name = "chat_sessions"

  def create_session(self, user_id: str, bot_id: str, tenant_id: str = None) -> dict | None:
    try:
      # Start the query builder
      payload = {
          "user_id": user_id,
          "bot_id": bot_id
      }
      if tenant_id:
        payload["tenant_id"] = tenant_id

      query = supabase.table(self.table_name).insert(payload)

      result = query.execute()
      if result.data:
        return result.data[0]

      return None
    except Exception as e:
      logger.exception("Failed to create session: " + str(e))
      raise Exception("Failed to create session: " + str(e))

  def get_session(self, session_id: str) -> dict | None:
    try:
      response = (
          supabase.table(self.table_name)
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

  def list_sessions(self, user_id: str, tenant_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    try:
      query = (
          supabase.table(self.table_name)
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
