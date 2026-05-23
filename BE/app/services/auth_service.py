from datetime import datetime, timedelta
from uuid import UUID

from jose import jwt

from app.config.config import settings
from app.core.logger import get_logger
from app.core.supabase_client import get_async_supabase_client
from app.repositories import UserRepository

logger = get_logger(__name__)


class AuthService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "AuthService":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  @staticmethod
  async def sign_up(
    email: str,
    password: str,
    name: str,
    tenant_id: UUID | None = None,
    role: str | None = None,
  ) -> dict:
    try:
      client = await get_async_supabase_client()
      response = await client.auth.sign_up(
        {
          "email": email,
          "password": password,
        }
      )

      if response.user:
        user_id = response.user.id

        if tenant_id:
          t_id = str(tenant_id) if tenant_id and str(tenant_id) != "None" else None
          if t_id:
            await UserRepository.get_instance().update_user_param(
              user_id, "tenant_id", t_id
            )
        if name:
          await UserRepository.get_instance().update_user_param(user_id, "name", name)
        if role:
          await UserRepository.get_instance().update_user_param(user_id, "role", role)

        return {"message": "User registered successfully", "user_id": user_id}
      else:
        raise RuntimeError("Failed to register user with Supabase")
    except Exception as e:
      logger.exception("Register user failed")
      raise RuntimeError(f"Failed to register user: {str(e)}")

  @staticmethod
  async def sign_up_batch(users: list[dict]) -> dict:
    created_count = 0
    skipped_count = 0
    errors = []

    for user in users:
      try:
        await AuthService.sign_up(
          email=user.get("email"),
          password=user.get("password"),
          name=user.get("name"),
          tenant_id=user.get("tenant_id"),
          role=user.get("role"),
        )
        created_count += 1
      except Exception as e:
        err_msg = str(e)
        if "User already registered" in err_msg or "already exists" in err_msg:
          skipped_count += 1
          errors.append(
            {
              "email": user.get("email"),
              "error": "User already registered (Skipped)",
            }
          )
        else:
          errors.append({"email": user.get("email"), "error": err_msg})

    return {
      "created_count": created_count,
      "skipped_count": skipped_count,
      "errors": errors,
    }

  @staticmethod
  async def sign_in_with_password(email: str, password: str) -> dict:
    try:
      client = await get_async_supabase_client()
      response = await client.auth.sign_in_with_password(
        {
          "email": email,
          "password": password,
        }
      )

      if response.user and response.session:
        user_id = response.user.id
        # user_repo_instance has been converted to async, so use await
        user_details = await UserRepository.get_instance().get_user_details(user_id)
        if (
          not user_details
          or "tenant_id" not in user_details
          or not user_details["tenant_id"]
        ):
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
          "username": user_details.get("name"),
          "app_metadata": {
            "provider": "email",
            "tenant_id": tenant_id,
            "role": role,
          },
        }

        custom_token = jwt.encode(
          payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        # Update last_sign_in_at
        try:
          await UserRepository.get_instance().update_user_param(
            user_id, "last_sign_in_at", datetime.now().isoformat()
          )
        except Exception as e:
          logger.warning(f"Failed to update last_sign_in_at for {user_id}: {e}")

        return {
          "token": custom_token,
          "refresh_token": response.session.refresh_token,
        }
      else:
        raise PermissionError("Invalid login credentials")
    except (LookupError, PermissionError):
      raise
    except Exception:
      logger.exception("Login user failed")
      raise RuntimeError("Failed to login user")
