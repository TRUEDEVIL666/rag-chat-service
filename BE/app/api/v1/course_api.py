from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services import course_service_instance
from app.schemas.course import CourseResponse, CourseCreateRequest


router = APIRouter()


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(
  semester_id: Optional[str] = None,
):
  return await course_service_instance.list_courses(semester_id)


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str):
  result = await course_service_instance.get_course(course_id)
  if not result:
    raise HTTPException(status_code=404, detail="Course not found")
  return result


@router.post("/courses", response_model=CourseResponse)
async def create_course(data: CourseCreateRequest):
  result = await course_service_instance.create_course(data)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to create course")
  return result
