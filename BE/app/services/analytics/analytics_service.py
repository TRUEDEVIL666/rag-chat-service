from fastapi import HTTPException
from app.services.users.user_service import UserService
from app.services.session.session_service import SessionService
from app.services.knowledge_base.knowledge_base_service import KnowledgeBaseService
from app.schemas.analytics import AnalyticsSummaryResponse
from app.core.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class AnalyticsService:
  def __init__(
      self,
      user_service: UserService,
      session_service: SessionService,
      kb_service: KnowledgeBaseService,
      doc_repo: Any,
      chat_repo: Any,
      class_repo: Any = None
  ):
    self.user_service = user_service
    self.session_service = session_service
    self.kb_service = kb_service
    self.doc_repo = doc_repo
    self.chat_repo = chat_repo
    self.class_repo = class_repo

  async def get_summary_stats(self, auth_context: dict) -> dict:
    role = auth_context.get("role")
    if role != "admin":
      raise HTTPException(status_code=404, detail="Not Found")

    access_token = auth_context.get("token")

    # Parallelize these calls if needed, but sequential await is fine for now
    total_users = await self.user_service.get_total_users(access_token=access_token)
    total_chats = await self.session_service.get_total_sessions(access_token=access_token)
    total_kbs = await self.kb_service.get_total_kbs(access_token=access_token)
    total_docs = await self.doc_repo.get_total_documents(access_token=access_token)
    recent_docs = await self.doc_repo.list_documents(
        tenant_id=None,
        limit=7,
        cursor_timestamp=None,
        sort_column="updated_at",
        access_token=access_token
    )

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "total_kbs": total_kbs,
        "total_documents": total_docs,
        "recent_documents": recent_docs
    }

  async def get_chart_data(self, auth_context: dict, time_range: str = "30days") -> list:
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

    return await self.chat_repo.get_analytics_counts(
        interval=interval,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        access_token=access_token
    )

  async def get_chart_data_custom(self, auth_context: dict, start_date: str, end_date: str, interval: str = "day") -> list:
    role = auth_context.get("role")
    if role != "admin":
      raise HTTPException(status_code=404, detail="Not Found")

    access_token = auth_context.get("token")

    return await self.chat_repo.get_analytics_counts(
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        access_token=access_token
    )

  def _format_time_ago(self, timestamp_str: str) -> str:
    if not timestamp_str:
      return "Unknown"
    from datetime import datetime, timezone
    try:
      # Handle ISO format with Z or offset
      dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
      now = datetime.now(timezone.utc)
      diff = now - dt

      seconds = diff.total_seconds()
      if seconds < 60:
        return "Just now"
      elif seconds < 3600:
        return f"{int(seconds // 60)} mins ago"
      elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
      else:
        return f"{int(seconds // 86400)} days ago"
    except Exception:
      return timestamp_str

  async def get_recent_activity(self, auth_context: dict) -> list[dict]:
    # Fetch recent USER messages as activity feed
    access_token = auth_context.get("token")
    messages = await self.session_service.session_repo.get_recent_global_messages(
      limit=5, access_token=access_token)

    activity = []
    for msg in messages:
      # Convert message to activity item
      # Extract bot name from nested chat_sessions -> bots
      bot_name = "Unknown Bot"
      sessions_data = msg.get("chat_sessions")
      if sessions_data and "bots" in sessions_data:
        bot_name = sessions_data["bots"].get("name", "Unknown Bot")

      activity.append({
          "id": f"msg-{msg.get('id')}",
          "type": "query",
          "user": "User",  # Placeholder until we join user table or have user_id
          "bot": bot_name,
          "message": msg.get("content") or "Sent a message",
          "time": self._format_time_ago(msg.get("created_at"))
      })
    return activity

  async def get_trending_topics(self, auth_context: dict) -> list[dict]:
    access_token = auth_context.get("token")
    # Repo method filters by role='user'
    messages = await self.session_service.session_repo.get_recent_messages_for_topics(
      limit=50, access_token=access_token)

    # Simple keyword extraction (naive split)
    from collections import Counter
    import re

    words = []
    stopwords = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "but", "in", "to", "of", "for", "with", "what", "how", "why", "i", "you",
        "it", "this", "that", "my", "me", "we", "us", "be", "are", "do", "does", "did", "have", "has", "had", "can", "could", "will", "would",
        "don", "not", "your", "from", "about", "there", "their", "they", "just", "like", "so"
    }

    for msg in messages:
      if not msg:
        continue

      # 1. Remove Code Blocks (``` ... ```)
      # This handles multi-line code blocks which were the source of the "noise"
      clean_msg = re.sub(r'```[\s\S]*?```', '', msg)

      # 2. Remove Inline Code (` ... `)
      clean_msg = re.sub(r'`[^`]*`', '', clean_msg)

      # 3. Tokenize remaining text
      tokens = re.findall(r'\w+', clean_msg.lower())

      filtered = [w for w in tokens if len(
        w) >= 3 and w not in stopwords and not w.isdigit()]
      words.extend(filtered)

    counts = Counter(words).most_common(50)
    # Scale value for UI
    return [{"text": word.title(), "value": count * 10} for word, count in counts]

  async def get_engagement_stats(self, auth_context: dict) -> dict:
    access_token = auth_context.get("token")
    # For MVP, listing classes from existing service or mock
    # Implementing At-Risk Logic using real UserRepo

    at_risk = await self.user_service.user_repo.get_at_risk_users(days_threshold=7)
    at_risk_list = []
    for u in at_risk:
      at_risk_list.append({
          "id": u.get("id"),
          "name": u.get("email"),  # Use email as name fallback
          "last_active": "7+ days ago"  # formatting simplified
      })

    # Most Engaging Users - Real Data Implementation
    top_users = []

    # 1. Get Top Active User IDs from Chat Repo
    # We fetch top 5 users based on message volume
    active_user_stats = await self.chat_repo.get_top_active_user_ids(limit_messages=2000, access_token=access_token)

    if active_user_stats:
      user_ids = [u["user_id"] for u in active_user_stats]

      # 2. Fetch User Details
      users_details = await self.user_service.get_users_by_ids(user_ids, access_token=access_token)
      users_map = {u["id"]: u for u in users_details}

      # 3. Combine Data
      for stat in active_user_stats:
        uid = stat["user_id"]
        user = users_map.get(uid)

        # Fallback if user not in public.users
        if not user:
          user = {"id": uid, "email": None, "full_name": "Unknown Student"}

        # Use name or email or fallback
        name = user.get("full_name") or user.get("email") or "Unknown Student"
        # Strip email domain for privacy/brevity if it's an email
        if name and "@" in name and not user.get("full_name"):
          name = name.split("@")[0]

        top_users.append({
            "name": name,
            "email": user.get("email") or "No Email",
            "queries": stat["count"],
            "avatar": user.get("avatar_url")
        })

    return {
        "top_users": top_users,
        "at_risk_students": at_risk_list
    }

  async def get_feedback_summary(self, auth_context: dict) -> dict:
    access_token = auth_context.get("token")
    return await self.session_service.session_repo.get_feedback_stats(access_token=access_token)
