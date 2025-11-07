# app/services/supabase/tenant_repository.py
from uuid import UUID
from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger
from datetime import datetime

logger = get_logger("tenant_repository")


class TenantRepository:
	def __init__(self):
		# self.table_name = "users" # No longer directly inserting into 'users' table
		pass

	def get_user_by_email(self, email: str) -> dict | None:
		try:
			# For checking user existence before signup, or fetching user details after login
			# Supabase Auth provides admin functions for this from the backend
			user_response = supabase.auth.admin.get_user_by_email(email)
			if user_response and user_response.user:
				return {"id": user_response.user.id, "email": user_response.user.email,
				        "tenant_id": user_response.user.user_metadata.get("tenant_id")}
			return None
		except Exception as e:
			logger.exception("Get user by email failed")
			raise RuntimeError("Failed to get user by email")

	def create_user(self, email: str, password: str, tenant_id: UUID) -> dict:
		try:
			response = supabase.auth.sign_up({
				"email": email,
				"password": password,
				"options": {
					"data": {"tenant_id": str(tenant_id)}
				}
			})

			if response.user:
				# Explicitly insert into public.users with tenant_id after successful signup
				logger.info(f"Attempting to insert user {response.user.id} with tenant_id: {tenant_id}")
				return {"user_id": response.user.id, "tenant_id": tenant_id}
			else:
				# Handle cases where signup fails but no explicit error is raised by the client
				error_message = response.session.user.identities[0].identity_data[
					'email'] if response.session and response.session.user and response.session.user.identities else "Unknown error"
				raise RuntimeError(f"Failed to sign up user: {error_message}")
		except Exception as e:
			logger.exception("Create user failed")
			raise RuntimeError("Failed to create user")
