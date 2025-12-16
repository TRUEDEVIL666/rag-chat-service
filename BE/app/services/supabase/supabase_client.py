# app/services/supabase/supabase_client.py
from app.config.config import settings
from supabase import create_client, Client

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
  raise Exception("Supabase credentials not found in environment variables.")

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
