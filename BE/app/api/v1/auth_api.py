from fastapi import APIRouter, HTTPException

from app.api.dependencies import AuthServiceDep
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.common import BaseResponse

router = APIRouter()


@router.post("/register", response_model=BaseResponse[dict])
async def register(
  data: RegisterRequest,
  auth_service: AuthServiceDep,
):
  if not data.email or not data.password:
    raise HTTPException(status_code=400, detail="Missing required fields")

  try:
    await auth_service.sign_up(
      email=data.email,
      password=data.password,
      name=data.name,
      tenant_id=data.tenant_id if data.tenant_id else None,
    )
    return BaseResponse(message="User registered successfully")
  except ValueError as ve:
    raise HTTPException(status_code=400, detail=str(ve))
  except RuntimeError as re:
    raise HTTPException(status_code=500, detail=str(re))
  except Exception:
    raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=BaseResponse[dict])
async def login(
  data: LoginRequest,
  auth_service: AuthServiceDep,
):
  if not data.email or not data.password:
    raise HTTPException(status_code=400, detail="Email and password are required")

  try:
    result = await auth_service.sign_in_with_password(
      email=data.email, password=data.password
    )
    return BaseResponse(data=result)
  except LookupError as le:
    raise HTTPException(status_code=404, detail=str(le))
  except PermissionError as pe:
    raise HTTPException(status_code=401, detail=str(pe))
  except RuntimeError as re:
    raise HTTPException(status_code=500, detail=str(re))
  except Exception:
    raise HTTPException(status_code=500, detail="Internal server error")
