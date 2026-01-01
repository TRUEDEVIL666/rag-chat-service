from uuid import UUID
from datetime import datetime, timedelta
from jose import jwt

from app.services.supabase.tenant_repository import TenantRepository
from app.services.supabase.user_repository import UserRepository
from app.config.config import settings
from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase

logger = get_logger("auth_service")

tenant_repo = TenantRepository()
user_repo = UserRepository()


class AuthService:
  @staticmethod
  def sign_up(email: str, password: str, name: str, tenant_id: UUID | None = None, role: str | None = None) -> dict:
    try:
      response = supabase.auth.sign_up({
        "email": email,
        "password": password,
      })

      if response.user:
        user_id = response.user.id
        if tenant_id:
          user_repo.update_user_param(user_id, "tenant_id", str(tenant_id))
        if name:
          user_repo.update_user_param(user_id, "name", name)
        if role:
          user_repo.update_user_param(user_id, "role", role)

        return {"message": "User registered successfully", "user_id": user_id}
      else:
        raise RuntimeError("Failed to register user with Supabase")
    except Exception as e:
      logger.exception("Register user failed")
      raise RuntimeError("Failed to register user")

  @staticmethod
  def sign_in_with_password(email: str, password: str) -> dict:
    try:
      response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
      })

      if response.user and response.session:
        user_id = response.user.id
        user_details = user_repo.get_user_details(user_id)
        if not user_details or "tenant_id" not in user_details or not user_details["tenant_id"]:
          raise LookupError("Tenant ID not found for user in public.users")
        tenant_id = user_details["tenant_id"]
        role = user_details.get("role")

        # Determine JWT role based on user role
        # If user is admin, use 'service_role' to bypass RLS (since 'admin' role might not exist in Postgres)
        # Otherwise use 'authenticated'
        jwt_role = "service_role" if role == "admin" else "authenticated"

        payload = {
          "sub": user_id,
          "aud": "authenticated",
          "role": jwt_role,
          "exp": datetime.utcnow() + timedelta(days=1),  # 1 day expiration
          "app_metadata": {
            "provider": "email",
            "tenant_id": tenant_id,
            "role": role
          },
        }

        custom_token = jwt.encode(
          payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        return {
          "token": custom_token,
          "refresh_token": response.session.refresh_token,
          # "user": {
          #   "id": user_id,
          #   "email": email,
          #   "name": user_details.get("name"),
          #   "tenant_id": tenant_id,
          #   "role": role
          # }
        }
      else:
        raise PermissionError("Invalid login credentials")
    except (LookupError, PermissionError):
      raise
    except Exception as e:
      logger.exception("Login user failed")
      raise RuntimeError("Failed to login user")
