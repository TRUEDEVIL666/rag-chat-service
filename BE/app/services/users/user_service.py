from app.services.supabase.user_repository import UserRepository


class UserService:
  def __init__(self, user_repo: UserRepository):
    self.user_repo = user_repo

  def get_all_users(self) -> list[dict]:
    return self.user_repo.get_all_users_not_admin()

  def delete_user(self, user_id: str, access_token: str) -> None:
    return self.user_repo.delete_user(user_id, access_token)

  def delete_users(self, user_ids: list[str], access_token: str) -> None:
    return self.user_repo.delete_users(user_ids, access_token)

  def get_total_users(self, access_token: str = None) -> int:
    return self.user_repo.get_total_users(access_token)
