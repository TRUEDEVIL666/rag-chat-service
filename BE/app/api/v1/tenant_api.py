from fastapi import APIRouter, HTTPException

from app.api.dependencies import CurrentUser, TenantServiceDep

router = APIRouter()


@router.get("/tenants")
async def get_all_tenants(
  tenant_service: TenantServiceDep,
  current_user: CurrentUser,
):
  if current_user.get("role") != "admin":
    raise HTTPException(status_code=403, detail="Not authorized")

  try:
    tenants = await tenant_service.get_all_tenants()
    return tenants
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
