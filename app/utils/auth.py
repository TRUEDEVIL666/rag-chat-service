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
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return {
            "user_id": payload.get("sub"),
            "tenant_id": payload.get("tenant_id")
        }
    except JWTError as e:
        logger.warning(f"[Auth] JWT decoding failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
