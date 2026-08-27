import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def normalize_supabase_url(url: str) -> str:
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith("/rest/v1"):
        cleaned = cleaned[: -len("/rest/v1")]
    return cleaned


SUPABASE_URL = normalize_supabase_url(os.getenv("SUPABASE_URL", ""))


def require_supabase_settings() -> None:
    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_KEY", SUPABASE_KEY),
        )
        if not value or value.startswith("your-")
    ]
    if missing:
        raise RuntimeError(
            "Missing Supabase settings in .env: " + ", ".join(missing)
        )

    parsed = urlparse(SUPABASE_URL)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(
            "SUPABASE_URL must be the project base URL, e.g. "
            "https://your-project-id.supabase.co"
        )
