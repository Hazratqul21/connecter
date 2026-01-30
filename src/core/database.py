from supabase import create_client, Client
from src.core.config import get_settings

settings = get_settings()

def get_supabase() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    if not url or not key:
        return None
    return create_client(url, key)
