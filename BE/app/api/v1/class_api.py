
from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List, Optional
from pydantic import BaseModel
from app.core.factory import get_class_service
from app.services.course.class_service import ClassService
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
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  return await service.list_classes(tenant_id, semester_id, course_id, current_user.get("token"))


@router.get("/classes/dashboard")
async def get_classes_dashboard(
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  return await service.get_dashboard_stats(current_user.get("tenant_id"), current_user.get("token"))


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.get_class(class_id, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=404, detail="Class not found")
  return result


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    data: ClassCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.create_class(data, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to create class")
  return result


@router.post("/classes/{class_id}/enroll")
async def enroll_student(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  user_id = current_user.get("user_id")
  res = await service.enroll_student(class_id, user_id, tenant_id, current_user.get("token"))
  if not res:
    raise HTTPException(status_code=400, detail="Failed to enroll")
  return {"status": "enrolled"}


@router.get("/classes/{class_id}/students")
async def get_class_students(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  return await service.get_class_students(class_id, tenant_id, current_user.get("token"))


@router.post("/classes/{class_id}/students")
async def add_students_to_class(
    class_id: str,
    data: AddStudentsRequest,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.add_students_to_class(class_id, data.user_ids, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to add students")
  return {"status": "success", "added": len(data.user_ids)}


@router.get("/classes/{class_id}/bots")
async def get_class_bots(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  return await service.get_class_bots(class_id, tenant_id, current_user.get("token"))


@router.get("/classes/{class_id}/documents", summary="Get Class Documents (KB Mirror)")
async def get_class_documents(
    class_id: str = Path(..., description="Class ID"),
    service=Depends(get_class_service),
    auth=Depends(get_current_user)
):
  return await service.get_class_documents(
      class_id=class_id,
      tenant_id=auth["tenant_id"],
      access_token=auth.get("token")
  )


@router.get("/classes/{class_id}/kbs", summary="Get Class Knowledge Bases")
async def get_class_kbs(
    class_id: str = Path(..., description="Class ID"),
    service=Depends(get_class_service),
    auth=Depends(get_current_user)
):
  return await service.get_class_kbs(
      class_id=class_id,
      tenant_id=auth["tenant_id"],
      access_token=auth.get("token")
  )


@router.post("/classes/{class_id}/bots")
async def add_bots_to_class(
    class_id: str,
    data: AddBotsRequest,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.add_bots_to_class(class_id, data.bot_ids, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to add bots")
  return {"status": "success", "added": len(data.bot_ids)}


@router.get("/my-classes", response_model=List[ClassResponse])
async def get_my_classes(
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  user_id = current_user.get("user_id")
  return await service.get_my_classes(user_id, tenant_id, current_user.get("token"))


@router.get("/my-class-bots")
async def get_my_class_bots(
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  user_id = current_user.get("user_id")
  return await service.get_my_class_bots(user_id, tenant_id, current_user.get("token"))


@router.delete("/classes/{class_id}/students/{user_id}")
async def remove_student_from_class(
    class_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.remove_student_from_class(class_id, user_id, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to remove student")
  return {"status": "success"}


@router.delete("/classes/{class_id}/bots/{bot_id}")
async def remove_bot_from_class(
    class_id: str,
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    service: ClassService = Depends(get_class_service)
):
  tenant_id = current_user.get("tenant_id")
  result = await service.remove_bot_from_class(class_id, bot_id, tenant_id, current_user.get("token"))
  if not result:
    raise HTTPException(status_code=400, detail="Failed to remove bot")
  return {"status": "success"}
