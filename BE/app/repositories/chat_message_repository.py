# app/repositories/chat_message_repository.py
from typing import List, Optional, Sequence

import json
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
  AIMessage,
  BaseMessage,
  HumanMessage,
  SystemMessage,
  message_to_dict,
  messages_from_dict,
)
from langchain_postgres import PGEngine
from sqlalchemy import text

from app.core.database import postgres_engine
from app.core.logger import get_logger
from app.core.supabase_client import get_async_supabase_client

logger = get_logger(__name__)


class CustomPostgresChatMessageHistory(BaseChatMessageHistory):
  """
  Pool-aware history class using langchain_postgres.PGEngine.
  Handles project-specific metadata like sender_id.
  """

  def __init__(
    self,
    table_name: str,
    session_id: str,
    pg_engine: "PGEngine",
    user_id: Optional[str] = None,
    bot_id: Optional[str] = None,
  ):
    self.table_name = table_name
    self.session_id = session_id
    self.pg_engine = pg_engine
    self.current_user_id = user_id
    self.current_bot_id = bot_id

  async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
    """Add messages using PGEngine and inject sender_id."""
    for message in messages:
      if "sender_id" not in message.additional_kwargs:
        if isinstance(message, HumanMessage):
          message.additional_kwargs["sender_id"] = self.current_user_id
        elif isinstance(message, AIMessage):
          message.additional_kwargs["sender_id"] = self.current_bot_id

    # Prepare values for bulk insertion
    values = [
      {"session_id": self.session_id, "message": json.dumps(message_to_dict(msg))}
      for msg in messages
    ]

    # OPTIMIZATION: Using RETURNING isn't strictly needed here since LangChain doesn't use the result,
    # but we use the same pool-based logic for consistent performance.
    sql = f'INSERT INTO "{self.table_name}" (session_id, message) VALUES (:session_id, :message)'

    async with self.pg_engine._pool.begin() as conn:
      for val in values:
        await conn.execute(text(sql), val)

  async def aget_messages(self) -> List[BaseMessage]:
    """Retrieve messages using PGEngine."""
    sql = f'SELECT message FROM "{self.table_name}" WHERE session_id = :session_id ORDER BY id'

    async with self.pg_engine._pool.connect() as conn:
      result = await conn.execute(text(sql), {"session_id": self.session_id})
      rows = result.fetchall()
      items = [row[0] for row in rows]

    # Robust parsing to handle legacy flat formats
    for i, item in enumerate(items):
      if isinstance(item, dict) and "data" not in item:
        items[i] = {"type": item.get("type", "human"), "data": item}

    return messages_from_dict(items)

  async def aclear(self) -> None:
    """Clear history using PGEngine."""
    sql = f'DELETE FROM "{self.table_name}" WHERE session_id = :session_id'
    async with self.pg_engine._pool.begin() as conn:
      await conn.execute(text(sql), {"session_id": self.session_id})

  @property
  def messages(self) -> List[BaseMessage]:
    """Sync property required by BaseChatMessageHistory."""
    return self._run_sync(self.aget_messages())

  def add_messages(self, messages: Sequence[BaseMessage]) -> None:
    """Sync method required by BaseChatMessageHistory."""
    self._run_sync(self.aadd_messages(messages))

  def clear(self) -> None:
    """Sync method required by BaseChatMessageHistory."""
    self._run_sync(self.aclear())

  def _run_sync(self, coro):
    """Bridge to run async coroutines in a synchronous context."""
    import asyncio

    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

    if loop.is_running():
      import nest_asyncio

      nest_asyncio.apply(loop)

    return loop.run_until_complete(coro)


class ChatMessageRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "ChatMessageRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self.table_name = "chat_messages"

  def get_history(
    self,
    session_id: str,
    user_id: Optional[str] = None,
    bot_id: Optional[str] = None,
  ) -> CustomPostgresChatMessageHistory:
    """Synchronous factory method for RunnableWithMessageHistory."""
    engine = postgres_engine._engine
    if engine is None:
      raise RuntimeError(
        "PostgresEngine must be initialized before calling get_history"
      )

    return CustomPostgresChatMessageHistory(
      table_name=self.table_name,
      session_id=session_id,
      user_id=user_id,
      bot_id=bot_id,
      pg_engine=engine,
    )

  async def create_message(
    self, session_id: str, content: str, role: str, sender_id: Optional[str] = None
  ) -> dict | None:
    """
    Saves a message using direct SQL with RETURNING for single-trip performance.
    """
    try:
      # Map role to LangChain message type
      if role.lower() == "user":
        msg = HumanMessage(content=content, additional_kwargs={"sender_id": sender_id})
      elif "bot" in role.lower() or "assistant" in role.lower():
        msg = AIMessage(content=content, additional_kwargs={"sender_id": sender_id})
      else:
        msg = SystemMessage(content=content, additional_kwargs={"sender_id": sender_id})

      # OPTIMIZATION: Single trip to DB with RETURNING
      sql = f"""
        INSERT INTO "{self.table_name}" (session_id, message) 
        VALUES (:session_id, :message) 
        RETURNING id, session_id, created_at
      """

      engine = await postgres_engine.get_engine()
      async with engine._pool.begin() as conn:
        result = await conn.execute(
          text(sql),
          {
            "session_id": session_id,
            "message": json.dumps(message_to_dict(msg)),
          },
        )
        row = result.fetchone()

      if row:
        return {
          "id": row[0],
          "session_id": row[1],
          "content": content,
          "role": role,
          "sender_id": sender_id,
          "created_at": row[2].isoformat() if hasattr(row[2], "isoformat") else row[2],
        }
      return None
    except Exception as e:
      logger.error(
        f"[ChatMessageRepository] Failed to create chat message. Session: {session_id}. Error: {e}"
      )
      raise RuntimeError(f"Failed to create chat message: {e}")

  async def get_messages_by_session(
    self,
    session_id: str,
    limit: int = 50,
    cursor_timestamp: int = None,
    sort_column: str = "created_at",
    sort_desc: bool = True,
  ) -> List[dict]:
    """Retrieves messages from the unified JSONB table."""
    try:
      client = await get_async_supabase_client()
      query = (
        client.table(self.table_name)
        .select("id, session_id, message, created_at")
        .eq("session_id", session_id)
        .order(sort_column, desc=sort_desc)
        .limit(limit)
      )

      if cursor_timestamp:
        from datetime import datetime, timezone

        dt_cursor = datetime.fromtimestamp(
          cursor_timestamp, tz=timezone.utc
        ).isoformat()
        if sort_desc:
          query = query.lt(sort_column, dt_cursor)
        else:
          query = query.gt(sort_column, dt_cursor)

      response = await query.execute()
      raw_messages = response.data or []

      # Convert JSONB structure back to flat dict for compatibility with FE
      results = []
      for row in raw_messages:
        msg_blob = row.get("message") or {}

        if "data" in msg_blob and isinstance(msg_blob["data"], dict):
          msg_blob = msg_blob["data"]

        kwargs = msg_blob.get("additional_kwargs") or {}

        # Safety check for "None" string poisoned UUIDs
        sender_id = kwargs.get("sender_id")
        if sender_id and str(sender_id) == "None":
          sender_id = None

        # Map role based on LangChain type
        msg_type = msg_blob.get("type")
        role = "assistant"
        if msg_type == "human":
          role = "user"
        elif msg_type == "system":
          role = "system"

        results.append(
          {
            "id": row["id"],
            "session_id": row["session_id"],
            "content": msg_blob.get("content") or "",
            "role": role,
            "sender_id": sender_id,
            "rating": kwargs.get("rating"),
            "created_at": row["created_at"],
          }
        )

      return results
    except Exception as e:
      logger.exception(
        f"[ChatMessageRepository] Failed to get messages for session {session_id}: {e}"
      )
      return []

  async def get_analytics_counts(
    self, interval: str, start_date: str, end_date: str
  ) -> List[dict]:
    """Queries the updated RPC which now handles JSONB types."""
    try:
      client = await get_async_supabase_client()
      response = await client.rpc(
        "get_message_counts_by_period",
        {
          "interval_type": interval,
          "start_date": start_date,
          "end_date": end_date,
        },
      ).execute()
      return response.data or []
    except Exception as e:
      logger.exception(f"[ChatMessageRepository] Failed to get analytics counts: {e}")
      return []

  async def get_message_count_by_bot(
    self, bot_id: str, filter_user_ids: List[str] = None
  ) -> int:
    """Updated to query JSONB 'type' field."""
    try:
      client = await get_async_supabase_client()
      query = (
        client.table(self.table_name)
        .select("id, chat_sessions!inner(bot_id, user_id)", count="exact", head=True)
        .eq("message->>type", "human")
        .eq("chat_sessions.bot_id", bot_id)
      )

      if filter_user_ids is not None:
        if not filter_user_ids:
          return 0
        query = query.in_("chat_sessions.user_id", filter_user_ids)

      response = await query.execute()
      return response.count if hasattr(response, "count") else 0
    except Exception as e:
      logger.error(
        f"[ChatMessageRepository] Failed to get message count for bot {bot_id}: {e}"
      )
      return 0

  async def get_top_active_user_ids(self, limit_messages: int = 2000) -> List[dict]:
    """Identifies top users by extracting sender_id from JSONB additional_kwargs."""
    try:
      client = await get_async_supabase_client()

      response = (
        await client.table(self.table_name)
        .select("id, message, chat_sessions!inner(user_id)")
        .eq("message->>type", "human")
        .order("created_at", desc=True)
        .limit(limit_messages)
        .execute()
      )

      messages = response.data or []
      from collections import Counter

      user_counts = Counter()

      for msg in messages:
        session = msg.get("chat_sessions")
        metadata = msg.get("message", {}).get("additional_kwargs", {})
        uid = metadata.get("sender_id")

        if not uid and session:
          uid = (
            session.get("user_id")
            if isinstance(session, dict)
            else session[0].get("user_id")
          )

        if uid:
          user_counts[uid] += 1

      return [
        {"user_id": uid, "count": count} for uid, count in user_counts.most_common(5)
      ]
    except Exception as e:
      logger.error(f"[ChatMessageRepository] Failed to get top active users: {e}")
      return []

  async def update_message_rating(self, message_id: str, rating: Optional[str]) -> bool:
    """Updates the nested 'rating' field inside the JSONB blob using jsonb_set."""
    try:
      sql = """
    UPDATE chat_messages 
    SET message = jsonb_set(
          COALESCE(message, '{}'::jsonb), 
          '{additional_kwargs, rating}', 
          :rating::jsonb
    )
    WHERE id = :id
      """
      rating_json = f'"{rating}"' if rating is not None else "null"

      async with (await postgres_engine.get_engine())._pool.begin() as conn:
        await conn.execute(text(sql), {"rating": rating_json, "id": message_id})
        return True
    except Exception as e:
      logger.error(
        f"[ChatMessageRepository] Failed to update message rating for {message_id}: {e}"
      )
      return False
