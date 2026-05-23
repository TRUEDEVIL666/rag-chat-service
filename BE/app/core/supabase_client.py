import asyncio
from typing import Optional

import httpx
from supabase import AsyncClient, create_async_client
from supabase.lib.client_options import AsyncClientOptions

from app.config.config import settings
from app.core.context import get_current_token
from app.core.logger import get_logger

logger = get_logger(__name__)

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
  raise Exception("Supabase credentials not found in environment variables.")

# 1. Singleton HTTP client to share connection pool
_shared_http_client: Optional[httpx.AsyncClient] = None
_shared_http_client_loop: Optional[asyncio.AbstractEventLoop] = None

# 2. Base client (Service Role / Public)
_base_supabase_client: Optional[AsyncClient] = None
_base_supabase_client_loop: Optional[asyncio.AbstractEventLoop] = None


def get_shared_http_client() -> httpx.AsyncClient:
  """
  Returns a singleton HTTPX client configured for high throughput.
  """
  global _shared_http_client, _shared_http_client_loop
  try:
    current_loop = asyncio.get_running_loop()
  except RuntimeError:
    current_loop = None

  if _shared_http_client is None or _shared_http_client_loop != current_loop:
    logger.info("[Supabase] Initializing shared HTTPX client pool")
    _shared_http_client = httpx.AsyncClient(
      timeout=httpx.Timeout(300.0, connect=10.0),
      limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
      follow_redirects=True,
    )
    _shared_http_client_loop = current_loop
  return _shared_http_client


async def get_async_supabase_client(access_token: str = None) -> AsyncClient:
  """
  Returns an Async Supabase client using a shared connection pool.
  If access_token is provided, returns an authenticated client wrapper.
  """
  global _base_supabase_client, _base_supabase_client_loop

  http_client = get_shared_http_client()

  try:
    current_loop = asyncio.get_running_loop()
  except RuntimeError:
    current_loop = None

  # Lazy init the base client
  if _base_supabase_client is None or _base_supabase_client_loop != current_loop:
    logger.info("[Supabase] Initializing base async client")
    _base_supabase_client = await create_async_client(
      settings.SUPABASE_URL,
      settings.SUPABASE_KEY,
      options=AsyncClientOptions(httpx_client=http_client),
    )
    _base_supabase_client_loop = current_loop

  if not access_token:
    access_token = get_current_token()

  if access_token:
    client = await create_async_client(
      settings.SUPABASE_URL,
      settings.SUPABASE_KEY,
      options=AsyncClientOptions(httpx_client=http_client),
    )
    client.postgrest.auth(access_token)
    return client

  return _base_supabase_client
