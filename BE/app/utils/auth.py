# app/utils/auth.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from app.config.config import settings
from app.core.logger import get_logger


logger = get_logger("auth")
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
  """
  Decode and validate JWT token from Authorization header.

  Returns:
    dict: Contains 'user_id' and 'tenant_id' from token payload.

  Raises:
    HTTPException: If token is invalid or cannot be decoded.
  """
  token = credentials.credentials
  try:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"verify_aud": False}
    )

    user_id = payload.get("sub")

    # Fetch tenant_id and role from DB since they are not in the standard Supabase token
    from app.services.supabase.user_repository import UserRepository
    user_repo = UserRepository()
    user_details = user_repo.get_user_details(user_id)

    tenant_id = user_details.get("tenant_id") if user_details else None
    role = user_details.get("role") if user_details else payload.get("role")

    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "token": token
    }
  except JWTError as e:
    logger.warning(f"[Auth] JWT decoding failed: {str(e)}")
    raise HTTPException(status_code=401, detail="Invalid or expired token")
