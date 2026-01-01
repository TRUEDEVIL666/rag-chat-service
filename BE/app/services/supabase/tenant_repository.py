# app/services/supabase/tenant_repository.py
from uuid import UUID
from app.services.supabase.supabase_client import get_supabase_client
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger("tenant_repository")


class TenantRepository:
  def __init__(self):
    self.table_name = "tenants"

  def get_user_by_email(self, email: str) -> dict | None:
    try:
      client = get_supabase_client()
      response = (
          client.table("users")
          .select("id, email, tenant_id")
          .eq("email", email)
          .maybe_single()
          .execute()
      )
      return response.data
    except Exception as e:
      logger.exception("Get user by email failed")
      raise RuntimeError("Failed to get user by email")

  def get_tenant_by_id(self, tenant_id: str) -> dict | None:
    try:
      client = get_supabase_client()
      response = client.table(self.table_name).select(
        "*").eq("id", tenant_id).single().execute()
      if response.data:
        return response.data
      return None
    except Exception as e:
      logger.exception(f"Failed to get tenant {tenant_id}")
      return None

  def create_tenant(self, name: str) -> dict | None:
    try:
      client = get_supabase_client()
      response = client.table(self.table_name).insert({
          "name": name}).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to create tenant {name}")
      raise RuntimeError(f"Failed to create tenant {name}")
