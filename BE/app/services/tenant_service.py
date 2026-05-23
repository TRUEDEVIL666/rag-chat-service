from typing import Optional


class TenantService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "TenantService":
    if cls._instance is None:
      from app.repositories import TenantRepository

      cls._instance = cls(tenant_repo_instance=TenantRepository.get_instance())
    return cls._instance

  def __init__(self, tenant_repo_instance):
    self.tenant_repo_instance = tenant_repo_instance

  async def get_user_by_email(self, email: str) -> Optional[dict]:
    return await self.tenant_repo_instance.get_user_by_email(email)

  async def get_tenant_by_id(self, tenant_id: str) -> Optional[dict]:
    return await self.tenant_repo_instance.get_tenant_by_id(tenant_id)

  async def create_tenant(self, name: str) -> Optional[dict]:
    return await self.tenant_repo_instance.create_tenant(name)

  async def get_all_tenants(self) -> list[dict]:
    return await self.tenant_repo_instance.get_all_tenants()
