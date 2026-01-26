from typing import Optional, List, Any, Dict
from app.services.supabase.supabase_client import get_async_supabase_client
from app.schemas.course import SemesterCreateRequest
import logging

logger = logging.getLogger(__name__)


class SemesterRepository:
  def __init__(self, supabase_client=None):
    # supabase_client arg kept for compatibility if needed, but we rely on get_async_supabase_client
    self.table_name = "semesters"

  async def list_semesters(self, tenant_id: str, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.table(self.table_name)\
          .select("*")\
          .eq("tenant_id", tenant_id)\
          .order("start_date", desc=True)\
          .execute()
      return response.data or []
    except Exception as e:
      logger.error(f"Error listing semesters: {e}")
      return []

  async def create_semester(self, data: SemesterCreateRequest, tenant_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      payload = data.model_dump()
      payload["tenant_id"] = tenant_id
      # payload["is_active"] defaults to False in DB, but we can set it if passed

      response = await client.table(self.table_name).insert(payload).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.error(f"Error creating semester: {e}")
      return None
