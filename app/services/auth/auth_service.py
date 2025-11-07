# app/services/auth/auth_service.py
from uuid import UUID
from app.helper.auth_verifier import create_token # Removed hash_password, verify_password
from app.services.supabase.tenant_repository import TenantRepository
from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase # Import supabase client

logger = get_logger("auth_service")

tenant_repo = TenantRepository()

class AuthService:
    @staticmethod
    def register_user(email: str, password: str,tenant_id:UUID) -> dict:
        try:
            # Supabase Auth handles user existence check and password hashing
            return tenant_repo.create_user(email, password,tenant_id)
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
                # Supabase returns a session and user object on successful login
                # We can create our own token or return Supabase's session token
                # For now, let's create our own token using the user ID and tenant ID from Supabase
                user_id = response.user.id
                tenant_id = response.user.user_metadata.get("tenant_id") # Assuming tenant_id is in user_metadata
                if not tenant_id:
                    # Fallback or error if tenant_id is not found in metadata
                    # This might require fetching from public.users if tenant_id is stored there
                    # For now, raise an error
                    raise LookupError("Tenant ID not found for user")

                token = create_token(user_id, tenant_id)
                return {"access_token": token}
            else:
                # Handle cases where login fails (e.g., incorrect credentials)
                raise PermissionError("Invalid login credentials")
        except (LookupError, PermissionError): # Keep these for specific error handling
            raise
        except Exception as e:
            logger.exception("Login user failed")
            raise RuntimeError("Failed to login user")
