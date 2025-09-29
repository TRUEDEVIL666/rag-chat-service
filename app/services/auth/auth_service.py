# app/services/auth/auth_service.py
from app.helper.auth_verifier import hash_password, verify_password, create_token
from app.services.supabase.tenant_repository import TenantRepository
from app.core.logger import get_logger

logger = get_logger("auth_service")

tenant_repo = TenantRepository()

class AuthService:
    @staticmethod
    def register_user(email: str, password: str,tenant_id:str) -> dict:
        try:
            if tenant_repo.get_user_by_email(email):
                raise ValueError("Email already exists")

            hashed_pw = hash_password(password)
            return tenant_repo.create_user(email, hashed_pw,tenant_id)
        except ValueError:
            raise
        except Exception as e:
            logger.exception("Register user failed")
            raise RuntimeError("Failed to register user")

    @staticmethod
    def login_user(email: str, password: str) -> dict:
        try:
            user = tenant_repo.get_user_by_email(email)
            if not user:
                raise LookupError("User with given email not found")

            if not verify_password(password, user["password_hash"]):
                raise PermissionError("Incorrect password")

            token = create_token(user["id"], user["tenant_id"])
            return {"access_token": token}
        except (LookupError, PermissionError):
            raise
        except Exception as e:
            logger.exception("Login user failed")
            raise RuntimeError("Failed to login user")
