from fastapi import APIRouter, HTTPException
from typing import List
from app.services import course_service_instance
from app.schemas.course import SemesterResponse, SemesterCreateRequest

router = APIRouter()


@router.get("/semesters", response_model=List[SemesterResponse])
async def list_semesters():
  return await course_service_instance.list_semesters()


@router.post("/semesters", response_model=SemesterResponse)
async def create_semester(
  data: SemesterCreateRequest,
):
  result = await course_service_instance.create_semester(data)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to create semester")
  return result
