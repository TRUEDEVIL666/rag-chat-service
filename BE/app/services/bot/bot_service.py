from app.core.logger import get_logger

from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest

# Import Repositories
from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.bot_kb_repository import BotKnowledgeBaseRepository
from app.services.supabase.session_repository import SessionRepository

logger = get_logger(__name__)


class BotService:
  def __init__(
      self,
      bot_repo: BotRepository,
      bot_kb_repo: BotKnowledgeBaseRepository,
      session_repo: SessionRepository
  ):
    self.bot_repo = bot_repo
    self.bot_kb_repo = bot_kb_repo
    self.session_repo = session_repo

  # ----------------------------------------------------------------------
  # BOT MANAGEMENT (CRUD) - Now Async to avoid blocking
  # ----------------------------------------------------------------------
  async def create_bot(self, data: BotCreateRequest, tenant_id: str, user_id: str, access_token: str = None):
    bot = await self.bot_repo.create_bot(data, tenant_id, user_id, access_token)

    if data.kb_ids:
      await self.bot_kb_repo.upsert_bot_kbs(str(data.id), [str(uid) for uid in data.kb_ids], access_token)
      bot["kb_ids"] = [str(uid) for uid in data.kb_ids]
    else:
      bot["kb_ids"] = []

    return bot

  async def update_config(self, bot_id: str, tenant_id: str, request: BotUpdateConfigRequest, access_token: str = None):
    # Update the bot record
    bot = await self.bot_repo.update_config(bot_id, tenant_id, request, access_token)

    # Update KB relationships in junction table if provided
    if request.kb_ids is not None:
      await self.bot_kb_repo.upsert_bot_kbs(bot_id, [str(uid) for uid in request.kb_ids], access_token)
      bot["kb_ids"] = [str(uid) for uid in request.kb_ids]

    return bot

  async def list_bots(self, tenant_id: str, access_token: str = None):
    return await self.bot_repo.list_bots(tenant_id, access_token)

  async def get_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    return await self.bot_repo.get_bot(bot_id, tenant_id, access_token)

  async def delete_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    return await self.bot_repo.delete_bot(bot_id, tenant_id, access_token)
