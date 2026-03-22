from typing import List
from app.core.logger import get_logger
from app.services.supabase.supabase_client import get_async_supabase_client

logger = get_logger(__name__)


class BotKnowledgeBaseRepository:
  """
  Handles storing and querying the many-to-many junction table 'bot_knowledge_bases'.
  """

  def __init__(self, table_name: str = "bot_knowledge_bases"):
    self.table_name = table_name

  async def upsert_bot_kbs(self, bot_id: str, kb_ids: List[str], access_token: str = None) -> None:
    """
    Deletes all existing knowledge base mappings for a bot, and inserts the new ones.
    If kb_ids is empty or None, it only deletes the old mappings.
    """
    try:
      client = await get_async_supabase_client(access_token)

      # Step 1: Delete existing mappings
      await client.table(self.table_name).delete().eq("bot_id", bot_id).execute()

      # Step 2: Bulk insert new mappings if any are provided
      if kb_ids:
        kb_inserts = [
          {"bot_id": bot_id, "kb_id": str(kb_id)} for kb_id in kb_ids]
        response = await client.table(self.table_name).insert(kb_inserts).execute()

        if hasattr(response, "error") and response.error:
          logger.error(
            f"[BotKBRepo]: Upsert error: {response.error.get('message')}")
        else:
          logger.info(
            f"[BotKBRepo]: Linked {len(kb_ids)} KBs to bot {bot_id}.")
    except Exception as e:
      logger.exception(
        f"[BotKBRepo]: Failed to upsert bot knowledge bases: {e}")
      raise
