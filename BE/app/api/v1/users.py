# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.factory import get_auth_service, get_user_repository
from app.schemas.auth import RegisterRequest, User
from typing import List
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/users", response_model=dict)
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
		auth_service.register_user(
			email=data.email,
			password=data.password,
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
		user_id: str,
		user_repository=Depends(get_user_repository),
		current_user: dict = Depends(get_current_user),
):
	if current_user.get("role") != "admin":
		raise HTTPException(status_code=403, detail="Not authorized")
	try:
		user_repository.delete_user(user_id)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
		user_id: str,
		user_repository=Depends(get_user_repository),
		current_user: dict = Depends(get_current_user),
):
	if current_user.get("role") != "admin":
		raise HTTPException(status_code=403, detail="Not authorized")
	try:
		user_repository.delete_user(user_id)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users", status_code=204)
async def delete_users(
		user_ids: List[str],
		user_repository=Depends(get_user_repository),
		current_user: dict = Depends(get_current_user),
):
	if current_user.get("role") != "admin":
		raise HTTPException(status_code=403, detail="Not authorized")
	try:
		for user_id in user_ids:
			user_repository.delete_user(user_id)
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[User])
async def get_all_users(user_repository=Depends(get_user_repository), current_user: dict = Depends(get_current_user)):
	if current_user.get("role") != "admin":
		raise HTTPException(status_code=403, detail="Not authorized")
	try:
		users = user_repository.get_all_users_not_admin()
		return users
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
