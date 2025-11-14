# app/services/auth/auth_service.py
from uuid import UUID
from app.helper.auth_verifier import create_token
from app.services.supabase.tenant_repository import TenantRepository
from app.services.supabase.user_repository import UserRepository # Import UserRepository
from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase  # Import supabase client

logger = get_logger("auth_service")

tenant_repo = TenantRepository()
user_repo = UserRepository() # Instantiate UserRepository


class AuthService:
	@staticmethod
	def register_user(email: str, password: str, tenant_id: UUID | None = None, role: str | None = None) -> dict:
		try:
			response = supabase.auth.sign_up({
				"email": email,
				"password": password,
			})

			if response.user:
				user_id = response.user.id
				if tenant_id:
					user_repo.update_user_param(user_id, "tenant_id", str(tenant_id))
				if role:
					user_repo.update_user_param(user_id, "role", role)

				return {"message": "User registered successfully", "user_id": user_id}
			else:
				raise RuntimeError("Failed to register user with Supabase")
		except Exception as e:
			logger.exception("Register user failed")
			raise RuntimeError("Failed to register user")

	@staticmethod
	def login_user(email: str, password: str) -> dict:
		try:
			response = supabase.auth.sign_in_with_password({
				"email": email,
				"password": password,
			})

			if response.user and response.session:
				user_id = response.user.id
				user_details = user_repo.get_user_details(user_id) # Use user_repo to get details
				if not user_details or "tenant_id" not in user_details or not user_details["tenant_id"]:
					raise LookupError("Tenant ID not found for user in public.users")
				tenant_id = user_details["tenant_id"]
				role = user_details.get("role")

				token = create_token(user_id, tenant_id, role)
				return {
					"token": token,
					"user": {
						"id": user_id,
						"email": email,
						"tenant_id": tenant_id,
						"role": role
					}
				}
			else:
				raise PermissionError("Invalid login credentials")
		except (LookupError, PermissionError):
			raise
		except Exception as e:
			logger.exception("Login user failed")
			raise RuntimeError("Failed to login user")