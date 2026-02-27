from app.services.supabase.supabase_client import get_async_supabase_client
from app.core.logger import get_logger

logger = get_logger(__name__)


class AiModelRepository:
  async def list_providers(self, is_active: bool = True, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    query = client.table("ai_providers").select("*")
    if is_active:
      query = query.eq("is_active", True)

    result = await query.execute()
    return result.data or []

  async def get_models_by_provider(self, provider_id: str, model_type: str = None, is_active: bool = True, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    query = client.table("ai_models").select(
      "*").eq("provider_id", provider_id)
    if model_type:
      query = query.eq("model_type", model_type)
    if is_active:
      query = query.eq("is_active", True)

    result = await query.execute()
    return result.data or []

  async def list_models_by_type(self, model_type: str, is_active: bool = True, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    query = client.table("ai_models").select("*").eq("model_type", model_type)
    if is_active:
      query = query.eq("is_active", True)

    result = await query.execute()
    return result.data or []

  async def list_all_models(self, is_active: bool = True, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    query = client.table("ai_models").select(
      "*, ai_providers(name, display_name)")
    if is_active:
      query = query.eq("is_active", True)

    result = await query.execute()
    return result.data or []

  async def get_model_by_id(self, model_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_models").select(
      "*, ai_providers(*)").eq("id", model_id).maybe_single().execute()

    data = result.data
    if data and isinstance(data.get("ai_providers"), list):
      data["ai_providers"] = data["ai_providers"][0] if data["ai_providers"] else None

    return data

  async def get_provider_by_id(self, provider_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_providers").select(
      "*").eq("id", provider_id).maybe_single().execute()
    return result.data

  async def create_provider(self, provider_data: dict, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    # Use secure RPC to handle vault insertion
    result = await client.rpc("create_ai_provider_secure", {
      "p_name": provider_data.get("name"),
      "p_display_name": provider_data.get("display_name"),
      "p_base_url": provider_data.get("base_url"),
      "p_api_key": provider_data.get("api_key"),
      "p_is_active": provider_data.get("is_active", True)
    }).execute()
    return result.data if result.data else None

  async def update_provider(self, provider_id: str, update_data: dict, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    # Use secure RPC to handle vault update
    result = await client.rpc("update_provider_secure", {
        "p_provider_id": provider_id,
        "p_name": update_data.get("name"),
        "p_display_name": update_data.get("display_name"),
        "p_base_url": update_data.get("base_url"),
        "p_api_key": update_data.get("api_key"),
        "p_is_active": update_data.get("is_active")
    }).execute()
    return result.data if result.data else None

  async def delete_provider(self, provider_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_providers").delete().eq(
      "id", provider_id).execute()
    return result.data

  async def create_model(self, model_data: dict, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_models").insert(model_data).execute()
    return result.data[0] if result.data else None

  async def update_model(self, model_id: str, update_data: dict, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_models").update(
      update_data).eq("id", model_id).execute()
    return result.data[0] if result.data else None

  async def delete_model(self, model_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_models").delete().eq("id", model_id).execute()
    return result.data

  async def get_decrypted_key(self, provider_id: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    try:
      result = await client.rpc("get_decrypted_provider_key", {
          "p_provider_id": provider_id
      }).execute()
      return result.data
    except Exception as e:
      logger.error(f"Error fetching decrypted key: {e}")
      return None

  async def get_provider_by_name(self, provider_name: str, access_token: str = None):
    client = await get_async_supabase_client(access_token)
    result = await client.table("ai_providers").select("*").ilike(
        "name", provider_name).eq("is_active", True).maybe_single().execute()
    return result.data

  async def resolve_model_config(self, provider_name: str, model_name: str = None, access_token: str = None):
    """
    Resolves configuration (base_url, api_key) for a given provider/model.
    Tries to find the active provider and returns the decrypted key.
    """
    provider = await self.get_provider_by_name(provider_name, access_token)
    if not provider:
      return None, None, None

    provider_id = provider["id"]
    base_url = provider.get("base_url")

    # Fetch decrypted key
    api_key = await self.get_decrypted_key(provider_id, access_token)

    # Use default models if not specified (optional logic, kept simple for now)
    # If model_name provided, verify it exists? Or just pass it through.
    # For now, just return what we found.

    return api_key, base_url, model_name
