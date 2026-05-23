from typing import List

from pydantic import BaseModel

from app.schemas.document import DocumentItem


class AnalyticsSummaryResponse(BaseModel):
  # Replaced total_students with total_users to match service, alias if needed
  total_users: int = 0
  total_chats: int = 0
  total_kbs: int = 0
  total_documents: int = 0
  recent_documents: List[DocumentItem] = []
  chart_data: List[dict] = []
