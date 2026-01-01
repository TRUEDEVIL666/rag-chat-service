from app.services.supabase.supabase_client import get_supabase_client
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from datetime import datetime
from uuid import uuid4


class BotRepository:
  def create_bot(
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

    client = get_supabase_client(access_token)
    result = client.table("bots").insert(insert_data).select(
        "*, provider:ai_providers(*), model:ai_models(*)").execute()
    if result.data:
      return result.data[0]
    else:
      raise Exception("Failed to insert bot")

  def update_config(
      self,
      bot_id: str,
      tenant_id: str,
      request: BotUpdateConfigRequest,
      access_token: str = None
  ):
    client = get_supabase_client(access_token)
    existing = (
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
    client.table("bots").update(update_data).eq("id", bot_id).execute()

    # Fetch updated record to return
    updated = (
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

  def list_bots(self, tenant_id: str, access_token: str = None):
    client = get_supabase_client(access_token)
    result = (
        client.table("bots")
        .select("*, provider:ai_providers(*), model:ai_models(*)")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []

  def get_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    client = get_supabase_client(access_token)
    # print(f"Fetching bot {bot_id} for tenant {tenant_id}")
    result = (
        client.table("bots")
        .select("*, provider:ai_providers(*), model:ai_models(*)")
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .maybe_single()
        .execute()
    )
    # print(f"Bot fetch result: {result.data}")
    return result.data

  def delete_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    client = get_supabase_client(access_token)
    result = (
        client.table("bots")
        .delete()
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return result.data
