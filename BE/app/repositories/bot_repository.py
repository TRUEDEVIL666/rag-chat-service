from typing import List, Optional

from app.repositories.base_repository import BaseRepository


class BotRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="bots")

  async def get_bot_kb_ids(self, bot_id: str) -> List[str]:
    """Get all Knowledge Base IDs associated with a bot."""
    client = await self._get_client()
    result = (
      await client.table("bot_knowledge_bases")
      .select("kb_id")
      .eq("bot_id", bot_id)
      .execute()
    )
    return [row["kb_id"] for row in result.data]

  async def get_bot_config(self, bot_id: str) -> Optional[dict]:
    """Get bot configuration."""
    client = await self._get_client()
    result = (
      await client.table(self.table_name)
      .select("*")
      .eq("id", bot_id)
      .maybe_single()
      .execute()
    )
    return result.data

  async def get_bot_with_kbs(self, bot_id: str) -> Optional[dict]:
    """Get bot data along with its linked knowledge bases."""
    bot = await self.get_bot_config(bot_id)
    if not bot:
      return None

    kb_ids = await self.get_bot_kb_ids(bot_id)
    if kb_ids:
      client = await self._get_client()
      kbs_result = (
        await client.table("knowledgebases").select("*").in_("id", kb_ids).execute()
      )
      bot["knowledge_bases"] = kbs_result.data
    else:
      bot["knowledge_bases"] = []

    return bot
