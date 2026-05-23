from app.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="chat_sessions")

  async def create_session(self, bot_id: str) -> dict | None:
    try:
      from app.core.context import get_current_tenant_id, get_current_user_id

      user_id = get_current_user_id()
      tenant_id = get_current_tenant_id()
      user_id = str(user_id) if user_id and str(user_id) != "None" else None
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      payload = {"user_id": user_id, "bot_id": bot_id}
      if tenant_id:
        payload["tenant_id"] = tenant_id

      result = await self.insert(payload)
      return result[0] if result else None
    except Exception as e:
      self.logger.exception("Failed to create session: " + str(e))
      raise Exception("Failed to create session: " + str(e))

  async def get_session(self, session_id: str) -> dict | None:
    try:
      client = await self._get_client()
      response = await (
        client.table(self.table_name)
        .select("*, bots:bot_id(name)")
        .eq("id", session_id)
        .maybe_single()
        .execute()
      )
      if response and response.data:
        return response.data
      if not response:
        self.logger.error(f"Supabase execute() returned None for session {session_id}")
      return None
    except Exception as e:
      self.logger.exception(f"Failed to get session {session_id}: {e}")
      return None

  async def list_sessions(
    self,
    limit: int = 20,
    cursor_timestamp: int = None,
    bot_id: str = None,
    search: str = None,
    start_date=None,
    end_date=None,
  ) -> list[dict]:
    try:
      from app.core.context import get_current_tenant_id, get_current_user_id

      user_id = get_current_user_id()
      tenant_id = get_current_tenant_id()
      user_id = str(user_id) if user_id and str(user_id) != "None" else None
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
      query = (
        client.table(self.table_name)
        .select("*, bots:bot_id(name)")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(limit)
      )

      from datetime import datetime

      if cursor_timestamp:
        from datetime import datetime, timezone

        dt_cursor = datetime.fromtimestamp(
          cursor_timestamp, tz=timezone.utc
        ).isoformat()
        query = query.lt("updated_at", dt_cursor)

      if tenant_id:
        query = query.eq("tenant_id", tenant_id)
      if bot_id:
        query = query.eq("bot_id", bot_id)

      if search:
        search_filter = f"summary_text.ilike.%{search}%,title.ilike.%{search}%"
        query = query.or_(search_filter)

      if start_date:
        query = query.gte(
          "updated_at",
          start_date.isoformat() if isinstance(start_date, datetime) else start_date,
        )

      if end_date:
        query = query.lte(
          "updated_at",
          end_date.isoformat() if isinstance(end_date, datetime) else end_date,
        )

      response = await query.execute()
      return response.data or []
    except Exception as e:
      self.logger.exception(f"Failed to list sessions for user {user_id}: {e}")
      return []

  async def update_session(self, session_id: str, data: dict) -> dict | None:
    try:
      result = await self.update("id", session_id, data)
      return result[0] if result else None
    except Exception as e:
      self.logger.exception(f"Failed to update session {session_id}: {e}")
      raise RuntimeError(f"Failed to update session {session_id}: {e}")

  async def delete_session(self, session_id: str) -> bool:
    try:
      from app.core.context import get_current_user_id

      user_id = get_current_user_id()
      user_id = str(user_id) if user_id and str(user_id) != "None" else None
      client = await self._get_client()
      response = await (
        client.table(self.table_name)
        .delete()
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
      )
      if response.data:
        self.logger.info(f"Deleted session {session_id}")
        return True
      self.logger.warning(f"Session {session_id} not found or permission denied")
      return False
    except Exception as e:
      self.logger.exception(f"Failed to delete session {session_id}: {e}")
      return False

  async def get_total_sessions(self) -> int:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      tenant_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
      client = await self._get_client()
      q = client.table(self.table_name).select("*", count="exact", head=True)
      if tenant_id:
        q = q.eq("tenant_id", tenant_id)
      res = await q.execute()
      return res.count or 0
    except Exception:
      self.logger.exception("Failed to get total sessions count")
      return 0

  async def get_recent_global_sessions(self, limit: int = 10) -> list[dict]:
    try:
      client = await self._get_client()
      query = (
        client.table(self.table_name)
        .select("*, bots(name)")
        .order("updated_at", desc=True)
        .limit(limit)
      )
      response = await query.execute()
      return response.data or []
    except Exception as e:
      self.logger.exception(f"Failed to get global sessions: {e}")
      return []

  async def get_feedback_stats(self) -> dict:
    try:
      client = await self._get_client()
      response = await (
        client.table("chat_messages")
        .select("message->additional_kwargs->>rating")
        .not_.is_("message->additional_kwargs->>rating", "null")
        .limit(1000)
        .execute()
      )

      positive = 0
      negative = 0
      if response.data:
        for msg in response.data:
          r = msg.get("rating")
          if r == "thumbs_up" or r is True or r == 1:
            positive += 1
          elif r == "thumbs_down" or r is False or r == 0:
            negative += 1

      return {
        "positive": positive,
        "negative": negative,
        "total": positive + negative,
      }
    except Exception as e:
      self.logger.warning(f"Failed to get feedback stats: {e}")
      return {"positive": 0, "negative": 0, "total": 0}

  async def get_recent_messages_for_topics(self, limit: int = 100) -> list[str]:
    try:
      client = await self._get_client()
      response = await (
        client.table("chat_messages")
        .select("message->>content")
        .eq("message->>type", "human")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
      )
      return [msg["content"] for msg in response.data] if response.data else []
    except Exception as e:
      self.logger.warning(f"Failed to get recent messages for topics: {e}")
      return []

  async def get_recent_global_messages(self, limit: int = 10) -> list[dict]:
    try:
      client = await self._get_client()
      query = (
        client.table("chat_messages")
        .select("*, chat_sessions(bots(name))")
        .eq("message->>type", "human")
        .order("created_at", desc=True)
        .limit(limit)
      )
      response = await query.execute()
      return response.data or []
    except Exception as e:
      self.logger.warning(f"Failed to get recent global messages: {e}")
      return []
