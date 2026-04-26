from typing import List, Optional
from app.core.supabase_client import get_async_supabase_client
from app.core.logger import get_logger

logger = get_logger(__name__)


class BotRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "BotRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  async def get_bot_kb_ids(self, bot_id: str) -> List[str]:
    """
    Get all Knowledge Base IDs associated with a bot.
    """
    client = await get_async_supabase_client()
    result = (
      await client.table("bot_knowledge_bases")
      .select("kb_id")
      .eq("bot_id", bot_id)
      .execute()
    )
    return [row["kb_id"] for row in result.data]

  async def get_bot_config(self, bot_id: str) -> Optional[dict]:
    """
    Get bot configuration.
    """
    client = await get_async_supabase_client()
    result = (
      await client.table("bots").select("*").eq("id", bot_id).maybe_single().execute()
    )
    return result.data

  async def get_bot_with_kbs(self, bot_id: str) -> Optional[dict]:
    """
    Get bot data along with its linked knowledge bases.
    """
    client = await get_async_supabase_client()
    # First get the bot
    bot = await self.get_bot_config(bot_id)
    if not bot:
      return None

    # Then get the KBs
    kb_ids = await self.get_bot_kb_ids(bot_id)
    if kb_ids:
      kbs_result = (
        await client.table("knowledgebases").select("*").in_("id", kb_ids).execute()
      )
      bot["knowledge_bases"] = kbs_result.data
    else:
      bot["knowledge_bases"] = []

    return bot
