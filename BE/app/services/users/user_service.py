from app.services.supabase.user_repository import UserRepository
from app.schemas.common_params import UserSearchParams
from typing import Optional


class UserService:
  def __init__(self, user_repo: UserRepository):
    self.user_repo = user_repo

  async def get_all_users(self, limit: int = 20, cursor_timestamp: int = None, search_params: Optional["UserSearchParams"] = None, access_token: str = None) -> list[dict]:
    return await self.user_repo.get_users(limit=limit, cursor_timestamp=cursor_timestamp, search_params=search_params, access_token=access_token)

  async def delete_user(self, user_id: str, access_token: str) -> None:
    return await self.user_repo.delete_user(user_id, access_token)

  async def delete_users(self, user_ids: list[str], access_token: str) -> None:
    return await self.user_repo.delete_users(user_ids, access_token)

  async def get_total_users(self, access_token: str = None) -> int:
    return await self.user_repo.get_total_users(access_token)

  async def get_users_by_ids(self, user_ids: list[str], access_token: str = None) -> list[dict]:
    return await self.user_repo.get_users_by_ids(user_ids, access_token)
