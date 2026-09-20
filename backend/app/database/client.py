from typing import Optional

from supabase import Client, create_client

from app.config import get_settings

_client: Optional[Client] = None


class DatabaseUnavailable(RuntimeError):
    pass


def get_supabase() -> Client:
    global _client
    settings = get_settings()
    if not settings.supabase_configured:
        raise DatabaseUnavailable(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client
