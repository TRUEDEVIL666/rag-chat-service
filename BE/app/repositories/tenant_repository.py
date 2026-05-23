# app/services/supabase/tenant_repository.py
from app.repositories.base_repository import BaseRepository


class TenantRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="tenants")

  async def get_user_by_email(self, email: str) -> dict | None:
    try:
      client = await self._get_client()
      response = await (
        client.table("users")
        .select("id, email, tenant_id")
        .eq("email", email)
        .maybe_single()
        .execute()
      )
      return response.data
    except Exception:
      self.logger.exception("Get user by email failed")
      raise RuntimeError("Failed to get user by email")

  async def get_tenant_by_id(self, tenant_id: str) -> dict | None:
    try:
      return await self.find_by_id("id", tenant_id)
    except Exception:
      self.logger.exception(f"Failed to get tenant {tenant_id}")
      return None

  async def create_tenant(self, name: str) -> dict | None:
    try:
      result = await self.insert({"name": name})
      return result[0] if result else None
    except Exception:
      self.logger.exception(f"Failed to create tenant {name}")
      raise RuntimeError(f"Failed to create tenant {name}")

  async def get_all_tenants(self) -> list[dict]:
    try:
      return await self.find_all()
    except Exception:
      self.logger.exception("Failed to get all tenants")
      return []
