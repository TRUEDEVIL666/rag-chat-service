from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.repositories import tenant_repo_instance

router = APIRouter()


@router.get("/tenants")
async def get_all_tenants(current_user: dict = Depends(get_current_user)):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")

  try:
    tenants = await tenant_repo_instance.get_all_tenants()
    return tenants
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
