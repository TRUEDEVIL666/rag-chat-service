from typing import Optional, List, Any, Dict
from app.core.supabase_client import get_async_supabase_client
from app.schemas.course import CourseCreateRequest
from app.core.logger import get_logger

logger = get_logger(__name__)


class CourseRepository:
  _instance = None

  @classmethod
  def get_instance(cls) -> "CourseRepository":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self, supabase_client=None):
    self.table_name = "courses"

  async def list_courses(
    self, semester_id: Optional[str] = None
  ) -> List[Dict[str, Any]]:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      client = await get_async_supabase_client()
      query = client.table(self.table_name).select("*").eq("tenant_id", tenant_id)

      if semester_id:
        query = query.eq("semester_id", semester_id)

      response = await query.order("code", desc=False).execute()
      return response.data or []
    except Exception as e:
      logger.error(f"Error listing courses: {e}")
      return []

  async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      client = await get_async_supabase_client()
      response = (
        await client.table(self.table_name)
        .select("*, semesters(name)")
        .eq("id", course_id)
        .eq("tenant_id", tenant_id)
        .single()
        .execute()
      )

      data = response.data
      if data and "semesters" in data and data["semesters"]:
        data["semester_name"] = data["semesters"]["name"]

      return data
    except Exception as e:
      logger.error(f"Error getting course {course_id}: {e}")
      return None

  async def create_course(self, data: CourseCreateRequest) -> Optional[Dict[str, Any]]:
    try:
      from app.core.context import get_current_tenant_id

      tenant_id = get_current_tenant_id()
      client = await get_async_supabase_client()
      payload = data.model_dump()
      payload["tenant_id"] = tenant_id

      response = await client.table(self.table_name).insert(payload).execute()
      if response.data:
        return response.data[0]
      return None
    except Exception as e:
      logger.error(f"Error creating course: {e}")
      return None
