# app/services/supabase/tenant_repository.py
from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger("tenant_repository")

class TenantRepository:
    def __init__(self):
        self.table_name = "users"

    def get_user_by_email(self, email: str) -> dict | None:
        try:
            result = (
                supabase.table(self.table_name)
                .select("id, email, password_hash, tenant_id")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.exception("Get user by email failed")
            raise RuntimeError("Failed to get user by email")

    def create_user(self, email: str, hashed_pw: str,tenant_id:str) -> dict:
        try:
            user_data = {
                "email": email,
                "password_hash": hashed_pw,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = supabase.table(self.table_name).insert(user_data).execute()
            user_id = response.data[0]["id"] if response.data else None
            return {"user_id": user_id, "tenant_id": tenant_id}
        except Exception as e:
            logger.exception("Create user failed")
            raise RuntimeError("Failed to create user")
