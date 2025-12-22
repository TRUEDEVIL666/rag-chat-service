from app.services.supabase.user_repository import UserRepository


class UserService:
  def __init__(self, user_repo: UserRepository):
    self.user_repo = user_repo

  def get_all_users(self) -> list[dict]:
    return self.user_repo.get_all_users_not_admin()

  def delete_user(self, user_id: str) -> None:
    return self.user_repo.delete_user(user_id)

  def delete_users(self, user_ids: list[str]) -> None:
    for user_id in user_ids:
      self.user_repo.delete_user(user_id)

  def get_total_users(self) -> int:
    return self.user_repo.get_total_users()
