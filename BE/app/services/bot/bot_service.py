
import asyncio
from app.core.logger import get_logger
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from pydantic import BaseModel
import json

from app.config.config import settings
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from app.schemas.llm import LLMConfig

# Import Repositories
from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.session_repository import SessionRepository

logger = get_logger(__name__)


class BotService:
  def __init__(
      self,
      bot_repo: BotRepository,
      session_repo: SessionRepository
  ):
    self.bot_repo = bot_repo
    self.session_repo = session_repo

  # ----------------------------------------------------------------------
  # BOT MANAGEMENT (CRUD) - Now Async to avoid blocking
  # ----------------------------------------------------------------------
  async def create_bot(self, data: BotCreateRequest, tenant_id: str, user_id: str, access_token: str = None):
    return await self.bot_repo.create_bot(data, tenant_id, user_id, access_token)

  async def update_config(self, bot_id: str, tenant_id: str, request: BotUpdateConfigRequest, access_token: str = None):
    return await self.bot_repo.update_config(bot_id, tenant_id, request, access_token)

  async def list_bots(self, tenant_id: str, access_token: str = None):
    return await self.bot_repo.list_bots(tenant_id, access_token)

  async def get_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    return await self.bot_repo.get_bot(bot_id, tenant_id, access_token)

  async def delete_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    return await self.bot_repo.delete_bot(bot_id, tenant_id, access_token)
