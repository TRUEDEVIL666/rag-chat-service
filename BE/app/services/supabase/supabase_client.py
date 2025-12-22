# app/services/supabase/supabase_client.py
from app.config.config import settings
from supabase import create_client, Client

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
  raise Exception("Supabase credentials not found in environment variables.")

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_client(access_token: str = None) -> Client:
  """
  Returns a Supabase client.
  If access_token is provided, returns a new client authenticated with that token (RLS).
  Otherwise, returns the global (service/admin) client.
  """
  if access_token:
    # Create a new client instance for this request to ensure thread safety with the specific auth token
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    client.postgrest.auth(access_token)
    return client
  return supabase
