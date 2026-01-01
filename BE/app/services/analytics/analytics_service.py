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

  def get_summary(self, auth_context: dict, time_range: str = "30days") -> AnalyticsSummaryResponse:
    """
    Retrieves analytics summary stats.
    Restricted to Admins. Non-admins will receive 404 Not Found to hide the endpoint.
    """
    # Enforce Admin Role
    role = auth_context.get("role")
    if role != "admin":
      # Return 404 to pretend the endpoint doesn't exist for unauthorized users
      raise HTTPException(status_code=404, detail="Not Found")

    try:
      tenant_id = auth_context.get("tenant_id")

      access_token = auth_context.get("token")

      total_users = self.user_service.get_total_users(
        access_token=access_token)
      total_chats = self.session_service.get_total_sessions(
        access_token=access_token)
      total_kbs = self.kb_service.get_total_kbs(access_token=access_token)
      total_docs = self.doc_repo.get_total_documents(access_token=access_token)
      recent_docs = self.doc_repo.list_documents(
          tenant_id=None,
          limit=5,
          cursor_timestamp=None,
          sort_column="updated_at",
          access_token=access_token
      )

      # Determine date range and interval
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
        # For 'all time', let's go back 1 year and group by month for now
        # Ideally we fetch min date from DB, but 1 year is a safe start for UI
        start_date = now - relativedelta(years=1)
        interval = "month"

      chart_data = self.chat_repo.get_analytics_counts(
          interval=interval,
          start_date=start_date.isoformat(),
          end_date=end_date.isoformat(),
          access_token=access_token
      )

      return AnalyticsSummaryResponse(
          total_users=total_users,
          total_chats=total_chats,
          total_kbs=total_kbs,
          total_documents=total_docs,
          recent_documents=recent_docs,
          chart_data=chart_data
      )
    except HTTPException:
      raise
    except Exception as e:
      logger.exception("Failed to get analytics summary")
      raise HTTPException(status_code=500, detail=str(e))
