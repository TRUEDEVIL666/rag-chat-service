from app.services.supabase.session_repository import SessionRepository


class SessionService:
  def __init__(self, session_repo: SessionRepository):
    self.session_repo = session_repo

  def create_session(self, user_id: str, bot_id: str, tenant_id: str = None):
    return self.session_repo.create_session(user_id, bot_id, tenant_id)

  def list_sessions(self, user_id: str, tenant_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    return self.session_repo.list_sessions(user_id, tenant_id, limit, offset)
