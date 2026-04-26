from typing import Optional, List, Any, Dict
from app.core.supabase_client import get_async_supabase_client
from app.schemas.course import SemesterCreateRequest
from app.core.logger import get_logger

logger = get_logger(__name__)


class SemesterRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "SemesterRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self, supabase_client=None):
    # supabase_client arg kept for compatibility if needed, but we rely on get_async_supabase_client
    self.table_name = "semesters"

  async def list_semesters(self) -> List[Dict[str, Any]]:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      client = await get_async_supabase_client()
      response = (
        await client.table(self.table_name)
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("start_date", desc=True)
        .execute()
      )
      return response.data or []
    except Exception as e:
      logger.error(f"Error listing semesters: {e}")
      return []

  async def create_semester(
    self, data: SemesterCreateRequest
  ) -> Optional[Dict[str, Any]]:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      client = await get_async_supabase_client()
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
