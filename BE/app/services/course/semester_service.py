
from app.core.logger import get_logger
from typing import List, Optional
from app.services.supabase.semester_repository import SemesterRepository
from app.schemas.course import SemesterCreateRequest, SemesterResponse

logger = get_logger(__name__)


class SemesterService:
  def __init__(self, repo: SemesterRepository):
    self.repo = repo

  async def list_semesters(self, tenant_id: str, access_token: str = None) -> List[SemesterResponse]:
    raw_list = await self.repo.list_semesters(tenant_id, access_token)
    return [SemesterResponse(**item) for item in raw_list]

  async def create_semester(self, data: SemesterCreateRequest, tenant_id: str, access_token: str = None) -> Optional[SemesterResponse]:
    result = await self.repo.create_semester(data, tenant_id, access_token)
    if result:
      return SemesterResponse(**result)
    return None
