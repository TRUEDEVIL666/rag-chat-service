from app.services.supabase.session_repository import SessionRepository


class SessionService:
  def __init__(self, session_repo: SessionRepository):
    self.session_repo = session_repo

  def create_session(self, user_id: str, bot_id: str, tenant_id: str = None):
    return self.session_repo.create_session(user_id, bot_id, tenant_id)

  def list_sessions(self, user_id: str, tenant_id: str, limit: int = 20, offset: int = 0, access_token: str = None) -> list[dict]:
    return self.session_repo.list_sessions(user_id, tenant_id, limit, offset, access_token)

  def delete_session(self, session_id: str, user_id: str) -> bool:
    return self.session_repo.delete_session(session_id, user_id)

  def get_total_sessions(self, tenant_id: str = None) -> int:
    return self.session_repo.get_total_sessions(tenant_id)
