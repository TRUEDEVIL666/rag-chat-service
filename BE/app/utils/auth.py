from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config.config import settings
from app.core.context import set_auth_context
from app.core.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer()


async def validate_token(token: str) -> dict:
  """
  Validate a raw JWT token string.
  """
  try:
    payload = jwt.decode(
      token,
      settings.SECRET_KEY,
      algorithms=[settings.ALGORITHM],
      options={"verify_aud": False},
    )

    user_id = payload.get("sub")
    app_metadata = payload.get("app_metadata", {})

    tenant_id = app_metadata.get("tenant_id")
    role = app_metadata.get("role")

    if not tenant_id or tenant_id == "None":
      from app.repositories import UserRepository

      user_details = await UserRepository.get_instance().get_user_details(user_id)

      if user_details:
        tenant_id = user_details.get("tenant_id")
        if not role:
          role = user_details.get("role")

    # Final safety check for "None" string coming from DB/Context
    if tenant_id == "None":
      tenant_id = None

    return {
      "user_id": user_id,
      "tenant_id": tenant_id,
      "role": role,
      "token": token,
    }
  except JWTError as e:
    logger.warning(f"[Auth]: JWT decoding failed: {str(e)}")
    raise HTTPException(status_code=401, detail="Invalid or expired token")
  except Exception as e:
    logger.error(f"CRITICAL AUTH ERROR: {e}")
    import traceback

    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Auth Error: {str(e)}")


async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
  """
  Decode and validate JWT token from Authorization header.
  """
  user_data = await validate_token(credentials.credentials)
  set_auth_context(user_data)
  return user_data
