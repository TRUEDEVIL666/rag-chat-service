from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.services.supabase.tenant_repository import TenantRepository
from typing import List

router = APIRouter()
tenant_repo = TenantRepository()


@router.get("/tenants")
async def get_all_tenants(current_user: dict = Depends(get_current_user)):
  # if current_user.get("role") != "admin":
  #     raise HTTPException(status_code=403, detail="Not authorized")
  # Commented out admin check for now as role might spread across tenants or be system admin
  # But usually creating users is admin task.

  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")

  try:
    tenants = tenant_repo.get_all_tenants(
      access_token=current_user.get("token"))
    return tenants
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
