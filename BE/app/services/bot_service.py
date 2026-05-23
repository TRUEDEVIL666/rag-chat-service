from typing import List, Optional


class BotService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "BotService":
    if cls._instance is None:
      from app.repositories import BotRepository

      cls._instance = cls(bot_repo_instance=BotRepository.get_instance())
    return cls._instance

  def __init__(self, bot_repo_instance):
    self.bot_repo_instance = bot_repo_instance

  async def get_bot_kb_ids(self, bot_id: str) -> List[str]:
    return await self.bot_repo_instance.get_bot_kb_ids(bot_id)

  async def get_bot_config(self, bot_id: str) -> Optional[dict]:
    return await self.bot_repo_instance.get_bot_config(bot_id)

  async def get_bot_with_kbs(self, bot_id: str) -> Optional[dict]:
    return await self.bot_repo_instance.get_bot_with_kbs(bot_id)
