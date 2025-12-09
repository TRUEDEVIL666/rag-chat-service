from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger

logger = get_logger("SessionRepository")


class SessionRepository:
  def create_session(self, user_id: str, bot_id: str, tenant_id: str = None):
    try:
      # Start the query builder
      payload = {
          "user_id": user_id,
          "bot_id": bot_id
      }
      if tenant_id:
        payload["tenant_id"] = tenant_id

      query = supabase.table("chat_sessions").insert(payload)

      result = query.execute()
      if result.data:
        return result.data[0]

      return None
    except Exception as e:
      logger.exception("Failed to create session: " + str(e))
      raise Exception("Failed to create session: " + str(e))
