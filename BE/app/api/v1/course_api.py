
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.core.factory import get_course_service
from app.services.course.course_service import CourseService
from app.schemas.course import CourseResponse, CourseCreateRequest

from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(
    semester_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: CourseService = Depends(get_course_service)
):
  tenant_id = current_user.get("tenant_id")
  return await service.list_courses(tenant_id, semester_id, current_user.get("token"))


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    service: CourseService = Depends(get_course_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.get_course(course_id, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=404, detail="Course not found")
  return result


@router.post("/courses", response_model=CourseResponse)
async def create_course(
    data: CourseCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: CourseService = Depends(get_course_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.create_course(data, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to create course")
  return result
