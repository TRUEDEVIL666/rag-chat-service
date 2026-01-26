from app.services.supabase.supabase_client import get_async_supabase_client
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class BotRepository:
  async def create_bot(
      self,
      data: BotCreateRequest,
      tenant_id: str,
      user_id: str,
      access_token: str = None
  ):
    bot_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    insert_data = {
        "id": bot_id,
        "tenant_id": tenant_id,
        "name": data.name,
        "description": data.description,
        "config_prompt": data.config_prompt,
        "config_model": data.config_model.dict() if data.config_model else None,
        "provider_id": str(data.provider_id) if data.provider_id else None,
        "model_id": str(data.model_id) if data.model_id else None,
        "kb_ids": None,
        "created_at": now,
    }

    client = await get_async_supabase_client(access_token)
    result = await client.table("bots").insert(insert_data).select(
        "*, provider:ai_providers(*), model:ai_models(*)").execute()
    if result.data:
      return result.data[0]
    else:
      raise Exception("Failed to insert bot")

  async def update_config(
      self,
      bot_id: str,
      tenant_id: str,
      request: BotUpdateConfigRequest,
      access_token: str = None
  ):
    client = await get_async_supabase_client(access_token)
    existing = await (
        client.table("bots")
        .select("*")
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
      raise ValueError("Bot not found or not owned by tenant")

    update_data = {}
    if request.name is not None:
      update_data["name"] = request.name
    if request.description is not None:
      update_data["description"] = request.description
    if request.config_prompt is not None:
      update_data["config_prompt"] = request.config_prompt
    if request.config_model is not None:
      update_data["config_model"] = request.config_model.dict()
    if request.provider_id is not None:
      update_data["provider_id"] = str(request.provider_id)
    if request.model_id is not None:
      update_data["model_id"] = str(request.model_id)
    if request.kb_ids is not None:
      update_data["kb_ids"] = [str(uid) for uid in request.kb_ids]

    # Execute update
    await client.table("bots").update(update_data).eq("id", bot_id).execute()

    # Fetch updated record to return
    updated = await (
        client.table("bots")
        .select("*, provider:ai_providers(*), model:ai_models(*)")
        .eq("id", bot_id)
        .single()
        .execute()
    )
    if updated.data:
      return updated.data
    else:
      raise ValueError("Failed to update bot")

  async def _hydrate_bots_with_kbs(self, bots: list, client):
    """
    Helper to fetch and attach KB details to a list of bots.
    """
    if not bots:
      return bots

    # 1. Collect all unique KB IDs
    all_kb_ids = set()
    for bot in bots:
      if bot.get("kb_ids"):
        all_kb_ids.update(bot["kb_ids"])

    if not all_kb_ids:
      return bots

    # 2. Fetch details for these KBs
    kb_res = await client.table("knowledgebases").select(
      "id, name").in_("id", list(all_kb_ids)).execute()
    kb_map = {kb["id"]: kb for kb in kb_res.data} if kb_res.data else {}

    # 3. Attach to bots
    for bot in bots:
      if bot.get("kb_ids"):
        bot["knowledge_bases"] = [
            kb_map.get(kb_id) for kb_id in bot["kb_ids"] if kb_map.get(kb_id)
        ]
      else:
        bot["knowledge_bases"] = []

    return bots

  async def list_bots(self, tenant_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await (
        client.table("bots")
        .select("*, provider:ai_providers(*), model:ai_models(*)")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )

    bots = result.data or []
    return await self._hydrate_bots_with_kbs(bots, client)

  async def get_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    try:
      result = await (
          client.table("bots")
          .select("*, provider:ai_providers(*), model:ai_models(*)")
          .eq("id", bot_id)
          .eq("tenant_id", tenant_id)
          .maybe_single()
          .execute()
      )

      data = result.data
      if data:
        # Flatten joined objects if they are returned as lists
        if isinstance(data.get("provider"), list):
          data["provider"] = data["provider"][0] if data["provider"] else None
        if isinstance(data.get("model"), list):
          data["model"] = data["model"][0] if data["model"] else None

        # Hydrate KBs
        hydrated_list = await self._hydrate_bots_with_kbs([data], client)
        return hydrated_list[0]

      return data
    except Exception as e:
      logger.error(f"Error fetching bot {bot_id}: {e}")
      return None

  async def delete_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await (
        client.table("bots")
        .delete()
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return result.data
