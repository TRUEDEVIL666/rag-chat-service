from fastapi import HTTPException
from app.services.users.user_service import UserService
from app.services.session.session_service import SessionService
from app.services.knowledge_base.knowledge_base_service import KnowledgeBaseService
from app.schemas.analytics import AnalyticsSummaryResponse
from app.core.logger import get_logger
from typing import Any

logger = get_logger("analytics_service")


class AnalyticsService:
  def __init__(
      self,
      user_service: UserService,
      session_service: SessionService,
      kb_service: KnowledgeBaseService,
      doc_repo: Any,  # Avoid circular import type hint if possible, or use simplified type
      chat_repo: Any  # Added chat message repo
  ):
    self.user_service = user_service
    self.session_service = session_service
    self.kb_service = kb_service
    self.doc_repo = doc_repo
    self.chat_repo = chat_repo

  def get_summary_stats(self, auth_context: dict) -> dict:
    role = auth_context.get("role")
    if role != "admin":
      raise HTTPException(status_code=404, detail="Not Found")

    access_token = auth_context.get("token")

    return {
        "total_users": self.user_service.get_total_users(access_token=access_token),
        "total_chats": self.session_service.get_total_sessions(access_token=access_token),
        "total_kbs": self.kb_service.get_total_kbs(access_token=access_token),
        "total_documents": self.doc_repo.get_total_documents(access_token=access_token),
        "recent_documents": self.doc_repo.list_documents(
            tenant_id=None,
            limit=5,
            cursor_timestamp=None,
            sort_column="updated_at",
            access_token=access_token
        )
    }

  def get_chart_data(self, auth_context: dict, time_range: str = "30days") -> list:
    role = auth_context.get("role")
    if role != "admin":
      raise HTTPException(status_code=404, detail="Not Found")

    access_token = auth_context.get("token")

    import datetime
    from dateutil.relativedelta import relativedelta

    now = datetime.datetime.now(datetime.timezone.utc)
    interval = "day"
    start_date = now - datetime.timedelta(days=30)
    end_date = now

    if time_range == "7days":
      start_date = now - datetime.timedelta(days=7)
      interval = "day"
    elif time_range == "30days":
      start_date = now - datetime.timedelta(days=30)
      interval = "day"
    elif time_range == "all":
      start_date = now - relativedelta(years=1)
      interval = "month"

    return self.chat_repo.get_analytics_counts(
        interval=interval,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        access_token=access_token
    )
