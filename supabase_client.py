from functools import lru_cache

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL, require_supabase_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    require_supabase_settings()
    return create_client(SUPABASE_URL, SUPABASE_KEY)
