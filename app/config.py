"""Centralized settings loaded from .env. Single source of config truth."""
import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # AI providers. Optional at the Settings level: only the provider actually
    # selected by ai_backend needs a key, and local/Ollama dev needs neither.
    # The client factories in app/ai/clients.py raise at first real use if the
    # selected provider's key is missing, so a missing key never surfaces as a
    # boot-time crash — only as a clear error when that provider is actually called.
    groq_api_key: str | None = None
    gemini_api_key: str | None = None

    # AI backend switch: "local" (Ollama, no quota — dev/build) | "cloud"
    # (Gemini + Groq — XPRIZE submission). Flip via AI_BACKEND in .env.
    ai_backend: Literal["local", "cloud"] = "local"
    ollama_model: str = "qwen2.5:14b"

    @field_validator("ai_backend", mode="before")
    @classmethod
    def normalize_ai_backend(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    # Product data source. Supabase/Postgres is the only runtime store.
    # qwen/Ollama may be local, but product data must not use local files.

    # Google OAuth: client ID only (audience for verifying Google-issued
    # id_tokens server-side). The client SECRET is never used by this backend —
    # it stays server-only inside the Next.js NextAuth process, never here.
    google_client_id: str = ""

    # Comma-separated explicit allow-list of origins permitted for CORS.
    # NEVER "*" — CORSMiddleware rejects "*" combined with allow_credentials=True
    # anyway, but even without credentials a wildcard would be too permissive
    # for an app that carries bearer tokens. Set CORS_ALLOWED_ORIGINS in .env.
    cors_allowed_origins: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    # Supabase pooler
    supabase_pooler_url: str = ""
    supabase_db_password: str = ""
    supabase_anon_key: str = ""

    # App
    app_env: str = "dev"
    log_level: str = "info"
    zidd_jwt_secret: str = ""

    # Product data is cloud-only. SessionStore is a live-process cache; durable
    # session metadata belongs in Supabase, never a local JSON snapshot.
    session_store_path: str = ""
    session_ttl_seconds: int = 7 * 24 * 60 * 60
    max_active_sessions_per_user: int = 20
    session_turn_limit_per_day: int = 100
    auth_google_limit_per_minute: int = 20

    # Small client-side pool to reuse the TLS/auth connection to Supabase's
    # transaction pooler. Keep it bounded so multi-instance deployments do not
    # exhaust the free-tier connection budget.
    db_pool_size: int = 5
    db_max_overflow: int = 0
    db_pool_pre_ping: bool = False

    @property
    def effective_db_pool_pre_ping(self) -> bool:
        """Use an explicit override, but keep production resilient by default."""
        return self.db_pool_pre_ping or self.app_env.lower() == "prod"

    # ---------- payments (Razorpay) ----------
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Credits granted once on signup, recorded as a "welcome" ledger row.
    welcome_credits: int = 50

    # Explicit local-dev escape hatch for testing credit flows without Razorpay.
    # APP_ENV != prod is not enough: preview/staging deployments are also non-prod.
    enable_dev_credit_grant: bool = False

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
