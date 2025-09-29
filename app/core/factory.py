# app/core/factory.py
import logging
from app.services.auth.auth_service import AuthService

logger = logging.getLogger("service_factory")

_auth_service_instance: AuthService | None = None

def get_auth_service() -> AuthService:
    global _auth_service_instance
    if _auth_service_instance is None:
        try:
            _auth_service_instance = AuthService()
            logger.info("Initialized AuthService")
        except Exception as e:
            logger.exception("Failed to initialize AuthService")
            raise
    return _auth_service_instance