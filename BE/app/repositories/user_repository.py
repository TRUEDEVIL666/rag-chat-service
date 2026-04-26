# app/services/supabase/user_repository.py
from app.core.supabase_client import get_async_supabase_client
from app.core.logger import get_logger
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
  from app.schemas.common_params import UserSearchParams

logger = get_logger(__name__)


class UserRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "UserRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self.table_name = "users"

  async def update_user_param(
    self, user_id: str, param_name: str, param_value: Any
  ) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = (
        await client.table(self.table_name)
        .update({param_name: param_value})
        .eq("id", user_id)
        .execute()
      )
      if response.data:
        logger.info(f"Updated user {user_id} {param_name} to {param_value}")
        return response.data[0]
      return None
    except Exception:
      logger.exception(f"Failed to update user {user_id} {param_name}")
      raise RuntimeError(f"Failed to update user {user_id} {param_name}")

  async def get_users(
    self,
    limit: int = 20,
    cursor_timestamp: int = None,
    search_params: Optional["UserSearchParams"] = None,
  ) -> list[dict] | None:
    try:
      client = await get_async_supabase_client()
      # Fetch users + tenant name
      query = client.table(self.table_name).select("*, tenants(name)")

      # Apply Search Filters
      if search_params:
        if search_params.query:
          # Search by email or Name (if name exists in metadata or column)
          # Assuming 'email' column check for now as 'exact' or 'ilike'
          query = query.ilike("email", f"%{search_params.query}%")

        if search_params.role:
          query = query.eq("role", search_params.role)

        if search_params.tenant_id:
          query = query.eq("tenant_id", search_params.tenant_id)

        if search_params.date_from:
          query = query.gte("created_at", search_params.date_from.isoformat())

        if search_params.date_to:
          query = query.lte("created_at", search_params.date_to.isoformat())

      if cursor_timestamp:
        # Cursor logic: created_at < cursor
        from datetime import datetime, timezone

        dt_cursor = datetime.fromtimestamp(cursor_timestamp, tz=timezone.utc)
        query = query.lt("created_at", dt_cursor.isoformat())

      # Apply sorting and limit
      query = query.order("created_at", desc=True).limit(limit)

      response = await query.execute()
      if response.data:
        return response.data
      return []
    except Exception:
      logger.exception("Failed to get all non-admin users")
      raise RuntimeError("Failed to get all non-admin users")

  async def delete_users(self, user_ids: list[str]) -> None:
    try:
      from app.core.context import get_current_token

      # Invoke the Edge Function to delete users from auth.users
      client = await get_async_supabase_client()
      res = await client.functions.invoke(
        "delete-users",
        invoke_options={
          "body": {"user_ids": user_ids},
          "headers": {"Authorization": f"Bearer {get_current_token()}"},
        },
      )

      if isinstance(res, dict):
        if res.get("error"):
          raise RuntimeError(f"Edge Function Error: {res.get('error')}")
        if res.get("errors") and len(res.get("errors")) > 0:
          logger.error(f"Some users failed to delete: {res.get('errors')}")

      # Manual cleanup in public.users just in case (optional if cascade exists)
      client = await get_async_supabase_client()
      await client.table(self.table_name).delete().in_("id", user_ids).execute()

    except Exception as e:
      logger.exception(f"Failed to delete users {user_ids}")
      raise RuntimeError(f"Failed to delete users: {str(e)}")

  async def delete_user(self, user_id: str) -> None:
    return await self.delete_users([user_id])

  async def get_user_details(self, user_id: str) -> dict | None:
    try:
      client = await get_async_supabase_client()
      response = (
        await client.from_(self.table_name)
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
      )
      if response.data:
        return response.data
      return None
    except Exception:
      logger.exception(
        f"Failed to get user details from public.users for user_id: {user_id}"
      )
      raise RuntimeError(
        f"Failed to get user details from public.users for user_id: {user_id}"
      )

  async def get_users_by_ids(self, user_ids: list[str]) -> list[dict]:
    try:
      if not user_ids:
        return []
      client = await get_async_supabase_client()
      response = (
        await client.table(self.table_name).select("*").in_("id", user_ids).execute()
      )
      return response.data or []
    except Exception as e:
      logger.error(f"Failed to get users by ids: {e}")
      return []

  async def get_total_users(self) -> int:
    try:
      client = await get_async_supabase_client()
      res = (
        await client.table(self.table_name)
        .select("*", count="exact", head=True)
        .execute()
      )
      return res.count or 0
    except Exception:
      logger.exception("Failed to get total users count")
      return 0

  async def get_at_risk_users(self, days_threshold: int = 7) -> list[dict]:
    try:
      client = await get_async_supabase_client()
      from datetime import datetime, timedelta, timezone

      cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
      response = (
        await client.table(self.table_name)
        .select("*")
        .lt("last_sign_in_at", cutoff_date.isoformat())
        .limit(10)
        .execute()
      )

      if response.data:
        return response.data
      return []
    except Exception as e:
      logger.warning(f"Failed to get at-risk users (Column might be missing): {e}")
      return []
