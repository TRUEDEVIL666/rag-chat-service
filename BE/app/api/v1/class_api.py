from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List, Optional
from pydantic import BaseModel
from app.services import course_service_instance
from app.schemas.course import ClassResponse, ClassCreateRequest

from app.utils.auth import get_current_user

router = APIRouter()


class AddBotsRequest(BaseModel):
  bot_ids: List[str]


class AddStudentsRequest(BaseModel):
  user_ids: List[str]


@router.get("/classes", response_model=List[ClassResponse])
async def list_classes(
  semester_id: Optional[str] = None,
  course_id: Optional[str] = None,
):
  return await course_service_instance.list_classes(semester_id, course_id)


@router.get("/classes/dashboard")
async def get_classes_dashboard():
  return await course_service_instance.get_dashboard_stats()


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str):
  result = await course_service_instance.get_class(class_id)
  if not result:
    raise HTTPException(status_code=404, detail="Class not found")
  return result


@router.post("/classes", response_model=ClassResponse)
async def create_class(data: ClassCreateRequest):
  result = await course_service_instance.create_class(data)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to create class")
  return result


@router.post("/classes/{class_id}/enroll")
async def enroll_student(
  class_id: str,
  current_user: dict = Depends(get_current_user),
):
  user_id = current_user.get("user_id")
  res = await course_service_instance.enroll_student(class_id, user_id)
  if not res:
    raise HTTPException(status_code=400, detail="Failed to enroll")
  return {"status": "enrolled"}


@router.get("/classes/{class_id}/students")
async def get_class_students(class_id: str):
  return await course_service_instance.get_class_students(class_id)


@router.post("/classes/{class_id}/students")
async def add_students_to_class(
  class_id: str,
  data: AddStudentsRequest,
):
  result = await course_service_instance.add_students_to_class(class_id, data.user_ids)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to add students")
  return {"status": "success", "added": len(data.user_ids)}


@router.get("/classes/{class_id}/bots")
async def get_class_bots(class_id: str):
  return await course_service_instance.get_class_bots(class_id)


@router.get("/classes/{class_id}/documents", summary="Get Class Documents (KB Mirror)")
async def get_class_documents(
  class_id: str = Path(..., description="Class ID"),
):
  return await course_service_instance.get_class_documents(class_id=class_id)


@router.get("/classes/{class_id}/kbs", summary="Get Class Knowledge Bases")
async def get_class_kbs(
  class_id: str = Path(..., description="Class ID"),
):
  return await course_service_instance.get_class_kbs(class_id=class_id)


@router.post("/classes/{class_id}/bots")
async def add_bots_to_class(
  class_id: str,
  data: AddBotsRequest,
):
  result = await course_service_instance.add_bots_to_class(class_id, data.bot_ids)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to add bots")
  return {"status": "success", "added": len(data.bot_ids)}


@router.get("/my-classes", response_model=List[ClassResponse])
async def get_my_classes():
  return await course_service_instance.get_my_classes()


@router.get("/my-class-bots")
async def get_my_class_bots():
  return await course_service_instance.get_my_class_bots()


@router.delete("/classes/{class_id}/students/{user_id}")
async def remove_student_from_class(class_id: str, user_id: str):
  result = await course_service_instance.remove_student_from_class(class_id, user_id)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to remove student")
  return {"status": "success"}


@router.delete("/classes/{class_id}/bots/{bot_id}")
async def remove_bot_from_class(class_id: str, bot_id: str):
  result = await course_service_instance.remove_bot_from_class(class_id, bot_id)
  if not result:
    raise HTTPException(status_code=400, detail="Failed to remove bot")
  return {"status": "success"}
