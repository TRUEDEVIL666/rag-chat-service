# app/services/supabase/supabase_client.py
from app.config.config import settings
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
  raise Exception("Supabase credentials not found in environment variables.")

# Set a long timeout for Edge Functions (5 minutes) to handle batch operations
client_options = ClientOptions(function_client_timeout=300)

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY,
    options=client_options
)


def get_supabase_client(access_token: str = None) -> Client:
  """
  Returns a Supabase client.
  If access_token is provided, returns a new client authenticated with that token (RLS).
  Otherwise, returns the global (service/admin) client.
  """
  if access_token:
    # Create a new client instance for this request to ensure thread safety with the specific auth token
    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=client_options
    )
    client.postgrest.auth(access_token)
    return client
  return supabase
