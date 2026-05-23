from typing import Optional

from app.repositories import (
  ChatMessageRepository,
  SessionRepository,
)


class SessionService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "SessionService":
    if cls._instance is None:
      from app.repositories import (
        ChatMessageRepository,
        SessionRepository,
      )

      cls._instance = cls(
        session_repo_instance=SessionRepository.get_instance(),
        chat_message_repo_instance=ChatMessageRepository.get_instance(),
      )
    return cls._instance

  def __init__(
    self,
    session_repo_instance: SessionRepository,
    chat_message_repo_instance: ChatMessageRepository,
  ):
    self.session_repo_instance = session_repo_instance
    self.chat_message_repo_instance = chat_message_repo_instance

  async def create_session(self, bot_id: str):
    return await self.session_repo_instance.create_session(bot_id)

  async def list_sessions(
    self,
    limit: int = 20,
    cursor_timestamp: int = None,
    bot_id: str = None,
    search: str = None,
    start_date=None,
    end_date=None,
  ) -> list[dict]:
    return await self.session_repo_instance.list_sessions(
      limit, cursor_timestamp, bot_id, search, start_date, end_date
    )

  async def get_session(self, session_id: str) -> dict | None:
    return await self.session_repo_instance.get_session(session_id)

  async def delete_session(self, session_id: str) -> bool:
    return await self.session_repo_instance.delete_session(session_id)

  async def get_total_sessions(self) -> int:
    return await self.session_repo_instance.get_total_sessions()

  async def get_chat_messages(
    self,
    session_id: str,
    limit: int = 50,
    cursor_timestamp: int = None,
    sort_column: str = "created_at",
    sort_desc: bool = True,
  ) -> list[dict]:
    return await self.chat_message_repo_instance.get_messages_by_session(
      session_id, limit, cursor_timestamp, sort_column, sort_desc
    )

  async def update_message_rating(self, message_id: str, rating: Optional[str]) -> bool:
    return await self.chat_message_repo_instance.update_message_rating(
      message_id, rating
    )
