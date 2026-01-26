from app.services.supabase.session_repository import SessionRepository
from app.services.supabase.chat_message_repository import ChatMessageRepository


class SessionService:
  def __init__(self, session_repo: SessionRepository, chat_message_repo: ChatMessageRepository):
    self.session_repo = session_repo
    self.chat_message_repo = chat_message_repo

  async def create_session(self, user_id: str, bot_id: str, tenant_id: str = None, access_token: str = None):
    return await self.session_repo.create_session(user_id, bot_id, tenant_id, access_token=access_token)

  async def list_sessions(
      self,
      user_id: str,
      tenant_id: str,
      limit: int = 20,
      cursor_timestamp: int = None,
      access_token: str = None,
      bot_id: str = None,
      search: str = None,
      start_date=None,
      end_date=None
  ) -> list[dict]:
    return await self.session_repo.list_sessions(user_id, tenant_id, limit, cursor_timestamp, access_token, bot_id, search, start_date, end_date)

  async def get_session(self, session_id: str, access_token: str = None) -> dict | None:
    return await self.session_repo.get_session(session_id, access_token)

  async def delete_session(self, session_id: str, user_id: str, access_token: str = None) -> bool:
    return await self.session_repo.delete_session(session_id, user_id, access_token=access_token)

  async def get_total_sessions(self, tenant_id: str = None, access_token: str = None) -> int:
    return await self.session_repo.get_total_sessions(tenant_id, access_token)

  async def get_chat_messages(self, session_id: str, limit: int = 50, cursor_timestamp: int = None, sort_column: str = "created_at", sort_desc: bool = True, access_token: str = None) -> list[dict]:
    return await self.chat_message_repo.get_messages_by_session(session_id, limit, cursor_timestamp, sort_column, sort_desc, access_token)
