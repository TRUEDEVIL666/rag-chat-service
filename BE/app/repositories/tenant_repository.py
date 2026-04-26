# app/services/supabase/tenant_repository.py
from app.core.supabase_client import get_async_supabase_client
from app.core.logger import get_logger

logger = get_logger(__name__)


class TenantRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "TenantRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self.table_name = "tenants"

  async def get_user_by_email(self, email: str) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = await (
        client.table("users")
        .select("id, email, tenant_id")
        .eq("email", email)
        .maybe_single()
        .execute()
      )
      return response.data
    except Exception:
      logger.exception("Get user by email failed")
      raise RuntimeError("Failed to get user by email")

  async def get_tenant_by_id(self, tenant_id: str) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = (
        await client.table(self.table_name)
        .select("*")
        .eq("id", tenant_id)
        .single()
        .execute()
      )
      if response.data:
        return response.data
      return None
    except Exception:
      logger.exception(f"Failed to get tenant {tenant_id}")
      return None

  async def create_tenant(self, name: str) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = await client.table(self.table_name).insert({"name": name}).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception:
      logger.exception(f"Failed to create tenant {name}")
      raise RuntimeError(f"Failed to create tenant {name}")

  async def get_all_tenants(self) -> list[dict]:
    try:
      client = await get_async_supabase_client()
      response = await client.table(self.table_name).select("*").execute()
      return response.data if response.data else []
    except Exception:
      logger.exception("Failed to get all tenants")
      return []
