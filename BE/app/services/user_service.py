from typing import Optional

from app.repositories import UserRepository
from app.schemas.common_params import UserSearchParams


class UserService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "UserService":
    if cls._instance is None:
      from app.repositories import (
        UserRepository,
      )

      cls._instance = cls(user_repo_instance=UserRepository.get_instance())
    return cls._instance

  def __init__(self, user_repo_instance: UserRepository):
    self.user_repo_instance = user_repo_instance

  async def get_all_users(
    self,
    limit: int = 20,
    cursor_timestamp: int = None,
    search_params: Optional["UserSearchParams"] = None,
  ) -> list[dict]:
    return await self.user_repo_instance.get_users(
      limit=limit, cursor_timestamp=cursor_timestamp, search_params=search_params
    )

  async def delete_user(self, user_id: str) -> None:
    return await self.user_repo_instance.delete_user(user_id)

  async def delete_users(self, user_ids: list[str]) -> None:
    return await self.user_repo_instance.delete_users(user_ids)

  async def get_total_users(self) -> int:
    return await self.user_repo_instance.get_total_users()

  async def get_users_by_ids(self, user_ids: list[str]) -> list[dict]:
    return await self.user_repo_instance.get_users_by_ids(user_ids)
