from app.config.config import settings
from supabase import create_async_client, AsyncClient
from supabase.lib.client_options import AsyncClientOptions

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
  raise Exception("Supabase credentials not found in environment variables.")

# Set a long timeout for Edge Functions (5 minutes) to handle batch operations
client_options = AsyncClientOptions(function_client_timeout=300)

_async_supabase: AsyncClient = None


async def get_async_supabase_client(access_token: str = None) -> AsyncClient:
  """
  Returns an Async Supabase client.
  """
  global _async_supabase

  # Initialize global client if needed (lazy init pattern for async)
  if _async_supabase is None:
    _async_supabase = await create_async_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=client_options
    )

  if access_token:
    # Create a new client for authenticated requests to ensure isolation (thread-safety/context-safety).
    # This prevents the access token from leaking into other concurrent requests.
    client = await create_async_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=client_options
    )
    client.postgrest.auth(access_token)
    return client

  return _async_supabase

# Legacy sync accessor is removed to force migration errors
