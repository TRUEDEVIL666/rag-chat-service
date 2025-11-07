# app/services/supabase/supabase_client.py
from app.config.config import settings
from supabase import create_client, Client

if not settings.supabase_url or not settings.supabase_key:
    raise Exception("Supabase credentials not found in environment variables.")

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
