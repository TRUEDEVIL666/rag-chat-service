# app/services/supabase/user_repository.py
from typing import TYPE_CHECKING, Any, Optional

from app.repositories.base_repository import BaseRepository

if TYPE_CHECKING:
  from app.schemas.common_params import UserSearchParams


class UserRepository(BaseRepository):
  def __init__(self):
    super().__init__(table_name="users")

  async def update_user_param(
    self, user_id: str, param_name: str, param_value: Any
  ) -> dict | None:
    try:
      result = await self.update("id", user_id, {param_name: param_value})
      if result:
        self.logger.info(f"Updated user {user_id} {param_name} to {param_value}")
        return result[0]
      return None
    except Exception:
      self.logger.exception(f"Failed to update user {user_id} {param_name}")
      raise RuntimeError(f"Failed to update user {user_id} {param_name}")

  async def get_users(
    self,
    limit: int = 20,
    cursor_timestamp: int = None,
    search_params: Optional["UserSearchParams"] = None,
  ) -> list[dict] | None:
    try:
      client = await self._get_client()
      query = client.table(self.table_name).select("*, tenants(name)")

      if search_params:
        if search_params.query:
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
        from datetime import datetime, timezone

        dt_cursor = datetime.fromtimestamp(cursor_timestamp, tz=timezone.utc)
        query = query.lt("created_at", dt_cursor.isoformat())

      query = query.order("created_at", desc=True).limit(limit)

      response = await query.execute()
      if response.data:
        return response.data
      return []
    except Exception:
      self.logger.exception("Failed to get all non-admin users")
      raise RuntimeError("Failed to get all non-admin users")

  async def delete_users(self, user_ids: list[str]) -> None:
    try:
      from app.core.context import get_current_token

      client = await self._get_client()
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
          self.logger.error(f"Some users failed to delete: {res.get('errors')}")

      # Manual cleanup in public.users just in case (optional if cascade exists)
      client = await self._get_client()
      await client.table(self.table_name).delete().in_("id", user_ids).execute()

    except Exception as e:
      self.logger.exception(f"Failed to delete users {user_ids}")
      raise RuntimeError(f"Failed to delete users: {str(e)}")

  async def delete_user(self, user_id: str) -> None:
    return await self.delete_users([user_id])

  async def get_user_details(self, user_id: str) -> dict | None:
    try:
      return await self.find_by_id("id", user_id)
    except Exception:
      self.logger.exception(
        f"Failed to get user details from public.users for user_id: {user_id}"
      )
      raise RuntimeError(
        f"Failed to get user details from public.users for user_id: {user_id}"
      )

  async def get_users_by_ids(self, user_ids: list[str]) -> list[dict]:
    try:
      return await self.find_by_ids(user_ids)
    except Exception as e:
      self.logger.error(f"Failed to get users by ids: {e}")
      return []

  async def get_total_users(self) -> int:
    try:
      client = await self._get_client()
      res = (
        await client.table(self.table_name)
        .select("*", count="exact", head=True)
        .execute()
      )
      return res.count or 0
    except Exception:
      self.logger.exception("Failed to get total users count")
      return 0

  async def get_at_risk_users(self, days_threshold: int = 7) -> list[dict]:
    try:
      client = await self._get_client()
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
      self.logger.warning(f"Failed to get at-risk users (Column might be missing): {e}")
      return []
