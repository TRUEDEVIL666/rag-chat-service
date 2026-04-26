# app/api/v1/users_api.py
from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi_cache.decorator import cache

from app.services import auth_service_instance, user_service_instance
from app.schemas.auth import (
  BatchRegisterRequest,
  BatchRegisterResponse,
  RegisterRequest,
  UserIdRequest,
)
from app.schemas.common import BaseResponse, MessageResponse
from app.schemas.common_params import PaginationParams, UserSearchParams
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/users", response_model=BaseResponse[MessageResponse])
async def create_user(
  data: RegisterRequest,
  current_user: Annotated[dict, Depends(get_current_user)],
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  if not data.email or not data.password:
    raise HTTPException(status_code=400, detail="Missing required fields")

  try:
    await auth_service_instance.sign_up(
      email=data.email,
      password=data.password,
      name=data.name,
      tenant_id=data.tenant_id if data.tenant_id else None,
      role=data.role if data.role else "user",
    )
    return BaseResponse(data=MessageResponse(message="User created successfully"))
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except RuntimeError as re:
    raise HTTPException(status_code=500, detail=str(re))
  except Exception:
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/users/batch", response_model=BaseResponse[BatchRegisterResponse])
async def create_users_batch(
  data: BatchRegisterRequest,
  current_user: Annotated[dict, Depends(get_current_user)],
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")

  try:
    users_list = [user.dict() for user in data.users]
    result = await auth_service_instance.sign_up_batch(users_list)
    return BaseResponse(data=result)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
  req: Annotated[UserIdRequest, Depends()],
  current_user: Annotated[dict, Depends(get_current_user)],
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    await user_service_instance.delete_user(str(req.user_id))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users", status_code=204)
async def delete_users(
  user_ids: Annotated[List[str], Body()],
  current_user: Annotated[dict, Depends(get_current_user)],
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    await user_service_instance.delete_users(user_ids)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=BaseResponse[dict])
@cache(expire=60)
async def get_all_users(
  pagination: Annotated[PaginationParams, Depends()],
  search_params: Annotated[UserSearchParams, Depends()],
  current_user: Annotated[dict, Depends(get_current_user)],
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    users = await user_service_instance.get_all_users(
      limit=pagination.limit,
      cursor_timestamp=pagination.cursor_timestamp,
      search_params=search_params,
    )

    total_users = await user_service_instance.get_total_users()

    next_cursor = None
    if users:
      last_user = users[-1]
      last_created_at = last_user.get("created_at")
      if last_created_at:
        # Parse ISO format string from Supabase
        try:
          dt = datetime.fromisoformat(last_created_at.replace("Z", "+00:00"))
          next_cursor = int(dt.timestamp())
        except ValueError:
          pass  # Fail silently if date format is unexpected

    return BaseResponse(
      data={
        "items": users,
        "total": total_users,
        "next_cursor": next_cursor,
        "limit": pagination.limit,
      }
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
