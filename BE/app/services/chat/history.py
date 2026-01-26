from typing import List, Sequence
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.services.supabase.chat_message_repository import ChatMessageRepository
import logging

logger = logging.getLogger(__name__)


class RepositoryChatMessageHistory(BaseChatMessageHistory):
  def __init__(self, session_id: str, message_repo: ChatMessageRepository, access_token: str = None, sender_id: str = None):
    self.session_id = session_id
    self.message_repo = message_repo
    self.access_token = access_token
    self.sender_id = sender_id
    self._messages: List[BaseMessage] = []
    self._loaded = False

  @property
  def messages(self) -> List[BaseMessage]:
    return self._messages

  @messages.setter
  def messages(self, value: List[BaseMessage]):
    self._messages = value

  async def load_messages(self):
    """
    Fetches messages from the repository asynchronously.
    """
    try:
      # Fetch from DB (asynchronously)
      db_messages = await self.message_repo.get_messages_by_session(
          session_id=self.session_id,
          limit=20,
          access_token=self.access_token
      )

      parsed_msgs = []
      for msg in reversed(db_messages):
        role = msg.get("role")
        content = msg.get("content")
        if role == "user":
          parsed_msgs.append(HumanMessage(content=content))
        elif role == "system":
          parsed_msgs.append(SystemMessage(content=content))
        else:
          parsed_msgs.append(AIMessage(content=content))

      self._messages = parsed_msgs
      self._loaded = True
    except Exception as e:
      logger.error(
        f"Failed to load chat history for session {self.session_id}: {e}")
      self._messages = []

  async def aadd_messages(self, messages: Sequence[BaseMessage]):
    """Async version of add_messages."""
    for message in messages:
      await self.aadd_message(message)

  async def aadd_message(self, message: BaseMessage):
    """
    Adds a message to the local cache and saves to DB asynchronously.
    """
    self._messages.append(message)

    # Save to DB
    try:
      # Determine role
      if isinstance(message, HumanMessage):
        role = "user"
      elif isinstance(message, AIMessage):
        role = "AI assistant"
      elif isinstance(message, SystemMessage):
        role = "system"
      else:
        role = "assistant"  # Fallback

      # Save to repository
      await self.message_repo.create_message(
          session_id=self.session_id,
          content=message.content,
          role=role,
          sender_id=self.sender_id,
          access_token=self.access_token
      )
    except Exception as e:
      logger.error(f"Failed to save message to DB: {e}")

  def clear(self):
    self._messages = []
