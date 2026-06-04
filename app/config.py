"""Centralized settings loaded from .env. Single source of config truth."""
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

    # Durability: path to disk-persist the in-memory SessionStore so live
    # sessions survive a process restart. Empty = disabled (pure in-memory).
    # Set SESSION_STORE_PATH in .env to enable (e.g. .zidd_sessions.json).
    session_store_path: str = ""

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
