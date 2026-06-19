"""Centralized settings loaded from .env. Single source of config truth."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # AI providers
    groq_api_key: str
    gemini_api_key: str

    # AI backend switch: "local" (Ollama, no quota — dev/build) | "cloud"
    # (Gemini + Groq — XPRIZE submission). Flip via AI_BACKEND in .env.
    ai_backend: str = "local"
    ollama_model: str = "qwen2.5:14b"

    # Supabase pooler
    supabase_pooler_url: str
    supabase_db_password: str = ""
    supabase_anon_key: str = ""

    # App
    app_env: str = "dev"
    log_level: str = "info"
    zidd_jwt_secret: str = ""

    # Durability: path to disk-persist the in-memory SessionStore so live
    # sessions survive a process restart. Empty = disabled (pure in-memory).
    # Set SESSION_STORE_PATH in .env to enable (e.g. .zidd_sessions.json).
    session_store_path: str = ""

    # Local-first SQLite storage backend path (profiles/turns/weaknesses/memory).
    # Distinct from session_store_path (which is the JSON SessionStore snapshot).
    # Used only when ai_backend == "local". Override LOCAL_STORE_PATH for tests.
    local_store_path: str = ".zidd_local.db"

    # ---------- payments (Razorpay) ----------
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Credits granted once on signup, recorded as a "welcome" ledger row.
    welcome_credits: int = 50

    @property
    def async_database_url(self) -> str:
        """Convert raw pooler URL to asyncpg driver form with SSL.

        Supabase gives `postgresql://...`; SQLAlchemy async needs
        `postgresql+asyncpg://...`. SSL required on the pooler.
        """
        url = self.supabase_pooler_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "ssl=" not in url and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}ssl=require"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_jwt_secret() -> str:
    """Single source of truth for the JWT signing secret.

    Read from the environment; fail at boot if unset/empty so the app never
    runs with a forgeable, committed secret. Sign and verify both call this,
    so the secret VALUE is guaranteed identical across the process.
    """
    secret = os.environ.get("ZIDD_JWT_SECRET") or get_settings().zidd_jwt_secret
    if not secret:
        raise RuntimeError(
            "ZIDD_JWT_SECRET is not set; refusing to start without a JWT signing secret."
        )
    # In production, refuse a weak secret. A short HMAC key is brute-forceable, so
    # enforce a 32-byte floor when APP_ENV=prod. Non-prod (dev/test/ci) is left
    # permissive so the suite can run with a short fixture secret.
    if os.environ.get("APP_ENV", "dev").lower() == "prod" and len(secret) < 32:
        raise RuntimeError(
            "ZIDD_JWT_SECRET must be at least 32 characters in production "
            f"(APP_ENV=prod); got {len(secret)}."
        )
    return secret
