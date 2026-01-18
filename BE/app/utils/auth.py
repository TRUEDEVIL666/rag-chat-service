# app/utils/auth.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from app.config.config import settings
from app.core.logger import get_logger


logger = get_logger("auth")
security = HTTPBearer()


def validate_token(token: str) -> dict:
  """
  Validate a raw JWT token string.
  """
  try:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"verify_aud": False}
    )

    user_id = payload.get("sub")
    app_metadata = payload.get("app_metadata", {})

    tenant_id = app_metadata.get("tenant_id")
    role = app_metadata.get("role")

    if not tenant_id:
      from app.services.supabase.user_repository import UserRepository
      user_repo = UserRepository()
      user_details = user_repo.get_user_details(user_id)

      if user_details:
        tenant_id = user_details.get("tenant_id")
        if not role:
          role = user_details.get("role")

    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "token": token
    }
  except JWTError as e:
    logger.warning(f"[Auth] JWT decoding failed: {str(e)}")
    raise HTTPException(status_code=401, detail="Invalid or expired token")
  except Exception as e:
    print(f"CRITICAL AUTH ERROR: {e}")
    import traceback
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Auth Error: {str(e)}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
  """
  Decode and validate JWT token from Authorization header.
  """
  return validate_token(credentials.credentials)
