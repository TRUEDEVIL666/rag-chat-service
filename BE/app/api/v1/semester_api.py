
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.factory import get_semester_service
from app.services.course.semester_service import SemesterService
from app.schemas.course import SemesterResponse, SemesterCreateRequest

from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/semesters", response_model=List[SemesterResponse])
async def list_semesters(
    current_user: dict = Depends(get_current_user),
    service: SemesterService = Depends(get_semester_service)
):
  tenant_id = current_user.get("tenant_id")
  return await service.list_semesters(tenant_id, current_user.get("token"))


@router.post("/semesters", response_model=SemesterResponse)
async def create_semester(
    data: SemesterCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: SemesterService = Depends(get_semester_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.create_semester(data, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to create semester")
  return result
