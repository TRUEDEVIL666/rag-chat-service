# app/services/supabase/tenant_repository.py
from uuid import UUID
from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger("tenant_repository")


class TenantRepository:
	def __init__(self):
		pass

	def get_user_by_email(self, email: str) -> dict | None:
		try:
			user_response = supabase.auth.admin.get_user_by_email(email)
			if user_response and user_response.user:
				return {"id": user_response.user.id, "email": user_response.user.email}
			return None
		except Exception as e:
			logger.exception("Get user by email failed")
			raise RuntimeError("Failed to get user by email")
