
import logging
from typing import List, Optional
from app.services.supabase.course_repository import CourseRepository
from app.schemas.course import CourseCreateRequest, CourseResponse

logger = logging.getLogger(__name__)


class CourseService:
  def __init__(self, repo: CourseRepository):
    self.repo = repo

  async def list_courses(self, tenant_id: str, semester_id: Optional[str] = None, access_token: str = None) -> List[CourseResponse]:
    raw_list = await self.repo.list_courses(tenant_id, semester_id, access_token)
    return [CourseResponse(**item) for item in raw_list]

  async def get_course(self, course_id: str, tenant_id: str, access_token: str = None) -> Optional[CourseResponse]:
    result = await self.repo.get_course(course_id, tenant_id, access_token)
    if result:
      return CourseResponse(**result)
    return None

  async def create_course(self, data: CourseCreateRequest, tenant_id: str, access_token: str = None) -> Optional[CourseResponse]:
    result = await self.repo.create_course(data, tenant_id, access_token)
    if result:
      return CourseResponse(**result)
    return None
