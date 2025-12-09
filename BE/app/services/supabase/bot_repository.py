from app.services.supabase.supabase_client import supabase
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from datetime import datetime
from uuid import uuid4


class BotRepository:
  def create_bot(self, data: BotCreateRequest, tenant_id: str, user_id: str):
    bot_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    insert_data = {
        "id": bot_id,
        "tenant_id": tenant_id,
        "name": data.name,
        "description": data.description,
        "config_prompt": None,
        "config_model": None,
        "kb_ids": None,
        "created_at": now,
    }

    result = supabase.table("bots").insert(insert_data).execute()
    if result.data:
      return result.data[0]
    else:
      raise Exception("Failed to insert bot")

  def update_config(self, bot_id: str, tenant_id: str, request: BotUpdateConfigRequest):
    existing = (
        supabase.table("bots")
        .select("*")
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
      raise ValueError("Bot not found or not owned by tenant")

    update_data = {}
    if request.config_prompt is not None:
      update_data["config_prompt"] = request.config_prompt
    if request.config_model is not None:
      update_data["config_model"] = request.config_model.dict()
    if request.kb_ids is not None:
      update_data["kb_ids"] = request.kb_ids

    updated = (
        supabase.table("bots")
        .update(update_data)
        .eq("id", bot_id)
        .execute()
    )
    if updated.data:
      return updated.data[0]
    else:
      raise ValueError("Failed to update bot")

  def list_bots(self, tenant_id: str):
    result = (
        supabase.table("bots")
        .select("*")
        # .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []

  def get_bot(self, bot_id: str, tenant_id: str):
    print(f"Fetching bot {bot_id} for tenant {tenant_id}")
    result = (
        supabase.table("bots")
        .select("*")
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .single()
        .execute()
    )
    print(f"Bot fetch result: {result.data}")
    return result.data

  def delete_bot(self, bot_id: str, tenant_id: str):
    result = (
        supabase.table("bots")
        .delete()
        .eq("id", bot_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return result.data
