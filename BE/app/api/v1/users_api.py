# app/api/v1/users.py
from app.schemas.common import MessageResponse
from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
from app.core.factory import get_auth_service, get_user_service
from app.schemas.auth import RegisterRequest, User, UserIdRequest
from typing import List
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/users", response_model=MessageResponse)
async def create_user(
    data: RegisterRequest,
    auth_service=Depends(get_auth_service),
    current_user: dict = Depends(get_current_user),
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  if not data.email or not data.password:
    raise HTTPException(status_code=400, detail="Missing required fields")

  try:
    auth_service.sign_up(
      email=data.email,
      password=data.password,
      name=data.name,
      tenant_id=data.tenant_id if data.tenant_id else None,
      role=data.role if data.role else "user",
    )
    return {
      "message": "User created successfully",
    }
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except RuntimeError as re:
    raise HTTPException(status_code=500, detail=str(re))
  except Exception:
    raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    req: UserIdRequest = Depends(),
    user_service=Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    user_service.delete_user(str(req.user_id), current_user.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users", status_code=204)
async def delete_users(
    user_ids: List[str],
    user_service=Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    user_service.delete_users(user_ids, current_user.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[User])
@cache(expire=60)
async def get_all_users(user_service=Depends(get_user_service), current_user: dict = Depends(get_current_user)):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    users = user_service.get_all_users()
    return users
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
