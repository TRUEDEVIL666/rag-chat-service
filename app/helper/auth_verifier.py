# app/helper/auth_verifier.py
from passlib.context import CryptContext
from app.config.config import settings
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
	return pwd_context.hash(password)


def create_token(user_id: str, tenant_id: str) -> str:
	payload = {
		"sub": str(user_id),
		"tenant_id": tenant_id,
		"exp": datetime.utcnow() + timedelta(minutes=60),
	}
	return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> dict:
	try:
		decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
		return {"valid": True, "user_id": decoded.get("sub"), "tenant_id": decoded.get("tenant_id")}
	except JWTError:
		return {"valid": False, "message": "Invalid or expired token"}
