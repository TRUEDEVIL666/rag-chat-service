# app/api/v1/users.py
from datetime import datetime
from app.schemas.common_params import PaginationParams, UserSearchParams
from app.schemas.common import MessageResponse
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi_cache.decorator import cache
from app.core.factory import get_auth_service, get_user_service
from app.schemas.auth import RegisterRequest, UserIdRequest, BatchRegisterRequest, BatchRegisterResponse
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
    await auth_service.sign_up(
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


@router.post("/users/batch", response_model=BatchRegisterResponse)
async def create_users_batch(
    data: BatchRegisterRequest,
    auth_service=Depends(get_auth_service),
    current_user: dict = Depends(get_current_user),
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")

  try:
    users_list = [user.dict() for user in data.users]
    result = await auth_service.sign_up_batch(users_list)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    req: UserIdRequest = Depends(),
    user_service=Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    await user_service.delete_user(str(req.user_id), current_user.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users", status_code=204)
async def delete_users(
    user_ids: List[str] = Body(...),
    user_service=Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    await user_service.delete_users(user_ids, current_user.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=dict)
@cache(expire=60)
async def get_all_users(
    pagination: PaginationParams = Depends(),
    search_params: UserSearchParams = Depends(),
    user_service=Depends(get_user_service),
    current_user: dict = Depends(get_current_user)
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")
  try:
    users = await user_service.get_all_users(
        limit=pagination.limit,
        cursor_timestamp=pagination.cursor_timestamp,
        search_params=search_params,
        access_token=current_user.get("token")
    )

    total_users = await user_service.get_total_users(
      access_token=current_user.get("token"))

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

    return {
        "items": users,
        "total": total_users,
        "next_cursor": next_cursor,
        "limit": pagination.limit
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
