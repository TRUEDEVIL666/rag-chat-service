# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends
from app.core.factory import get_auth_service
from app.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter()


@router.post("/register")
async def register(data: RegisterRequest, auth_service=Depends(get_auth_service)):
  if not data.email or not data.password:
    raise HTTPException(status_code=400, detail="Missing required fields")

  try:
    await auth_service.sign_up(
      email=data.email,
      password=data.password,
      name=data.name,
      tenant_id=data.tenant_id if data.tenant_id else None
    )
    return {
      "message": "User registered successfully",
    }
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except RuntimeError as re:
    raise HTTPException(status_code=500, detail=str(re))
  except Exception:
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
async def login(data: LoginRequest, auth_service=Depends(get_auth_service)):
  if not data.email or not data.password:
    raise HTTPException(
      status_code=400, detail="Email and password are required")

  try:
    result = await auth_service.sign_in_with_password(
      email=data.email, password=data.password)
    return result
  except LookupError as le:
    raise HTTPException(status_code=404, detail=str(le))
  except PermissionError as pe:
    raise HTTPException(status_code=401, detail=str(pe))
  except RuntimeError as re:
    raise HTTPException(status_code=500, detail=str(re))
  except Exception:
    raise HTTPException(status_code=500, detail="Internal server error")
