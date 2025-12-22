# app/services/supabase/user_repository.py
from uuid import UUID
from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger
from typing import Any, Dict, Optional

logger = get_logger("user_repository")


class UserRepository:
  def __init__(self):
    self.table_name = "users"

  def update_user_param(self, user_id: str, param_name: str, param_value: Any) -> dict | None:
    try:
      response = supabase.table(self.table_name).update(
        {param_name: param_value}).eq("id", user_id).execute()
      if response.data:
        logger.info(f"Updated user {user_id} {param_name} to {param_value}")
        return response.data[0]
      return None
    except Exception as e:
      logger.exception(f"Failed to update user {user_id} {param_name}")
      raise RuntimeError(f"Failed to update user {user_id} {param_name}")

  def get_all_users_not_admin(self) -> list[dict] | None:
    try:
      response = supabase.table(self.table_name).select(
        "*").neq("role", "admin").execute()
      if response.data:
        return response.data
      return []
    except Exception as e:
      logger.exception("Failed to get all non-admin users")
      raise RuntimeError("Failed to get all non-admin users")

  def delete_user(self, user_id: str) -> None:
    try:
      supabase.table(self.table_name).delete().eq("id", user_id).execute()
    except Exception as e:
      logger.exception(f"Failed to delete user {user_id}")
      raise RuntimeError(f"Failed to delete user {user_id}")

  def get_user_details(self, user_id: str) -> dict | None:
    try:
      response = supabase.from_(self.table_name).select(
        "*").eq("id", user_id).single().execute()
      if response.data:
        return response.data
      return None
    except Exception as e:
      logger.exception(
        f"Failed to get user details from public.users for user_id: {user_id}")
      raise RuntimeError(
        f"Failed to get user details from public.users for user_id: {user_id}")

  def get_total_users(self) -> int:
    try:
      res = supabase.table(self.table_name).select(
        "*", count="exact", head=True).execute()
      return res.count or 0
    except Exception as e:
      logger.exception("Failed to get total users count")
      return 0
