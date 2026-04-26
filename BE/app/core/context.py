from contextvars import ContextVar
from typing import Any, Dict, Optional

# The context variable to hold user information and tokens for the current request
_request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
  "request_context", default=None
)


def set_auth_context(auth_data: Dict[str, Any]) -> None:
  """
  Sets the authentication context for the current request.
  Expected keys: user_id, tenant_id, role, token
  """
  _request_context.set(auth_data)


def get_auth_context() -> Optional[Dict[str, Any]]:
  """
  Retrieves the full authentication context.
  """
  return _request_context.get()


def get_current_user_id() -> Optional[str]:
  """
  Helper to get the user ID from context.
  """
  ctx = _request_context.get()
  if not ctx:
    return None
  val = ctx.get("user_id")
  return str(val) if val and str(val) != "None" else None


def get_current_tenant_id() -> Optional[str]:
  """
  Helper to get the tenant ID from context.
  """
  ctx = _request_context.get()
  if not ctx:
    return None
  val = ctx.get("tenant_id")
  return str(val) if val and str(val) != "None" else None


def get_current_token() -> Optional[str]:
  """
  Helper to get the access token from context.
  """
  ctx = _request_context.get()
  return ctx.get("token") if ctx else None


def get_current_role() -> Optional[str]:
  """
  Helper to get the user role from context.
  """
  ctx = _request_context.get()
  return ctx.get("role") if ctx else None


def clear_context() -> None:
  """
  Clears the current request context.
  """
  _request_context.set(None)
