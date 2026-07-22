"""Centralized settings loaded from .env. Single source of config truth."""
import os
from datetime import datetime
from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qsl, urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


def _postgres_url(
    template: str,
    password: str,
    *,
    async_driver: bool = True,
) -> str:
    """Rebuild a Supabase DSN without trusting an embedded raw password."""

    if not template.strip():
        return ""
    parsed = urlsplit(template.strip())
    if not parsed.hostname or not parsed.username:
        raise ValueError("invalid_supabase_database_url")
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("sslmode", None)
    query.pop("ssl", None)
    url = URL.create(
        "postgresql+asyncpg" if async_driver else "postgresql",
        username=parsed.username,
        password=password or parsed.password,
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path.lstrip("/") or "postgres",
        query=query,
    )
    return url.render_as_string(hide_password=False)


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
    gemini_api_key_1: str | None = None
    gemini_api_key_2: str | None = None
    gemini_api_key_3: str | None = None
    gemini_api_key_4: str | None = None
    gemini_api_key_5: str | None = None

    # AI backend switch: "local" (Ollama, no quota — dev/build) | "cloud"
    # (Gemini + Groq — XPRIZE submission). Flip via AI_BACKEND in .env.
    ai_backend: Literal["local", "cloud", "gemini"] = "local"
    ollama_model: str = "qwen2.5:14b"
    ollama_base_url: str = "http://localhost:11434"
    # 3.1 Flash-Lite is the verified cloud default for the configured beta
    # projects. Keeping the default fallback identical intentionally collapses
    # the chain to one model; deployments can opt into a distinct, verified
    # fallback through environment configuration.
    gemini_text_model: str = "gemini-3.1-flash-lite"
    gemini_text_fallback_model: str = "gemini-3.1-flash-lite"
    gemini_structured_model: str = "gemini-3.1-flash-lite"
    gemini_structured_fallback_model: str = "gemini-3.1-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-2"
    # Cloud calls must not hold a learner turn indefinitely. This budget is
    # provider-wide across a model chain; local Qwen remains unbounded.
    gemini_request_timeout_seconds: float = 30.0
    # A single credential must leave time for a healthy rotated key within the
    # caller's overall Gemini deadline. This does not apply to local Qwen.
    gemini_credential_attempt_timeout_seconds: float = Field(default=8.0, gt=0)
    # School cloud evaluation is bounded independently of Career model calls.
    # Local Qwen stays unbounded at the route layer.
    school_open_answer_timeout_seconds: float = 20.0

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
    data_region: Literal["default", "india"] = "default"
    supabase_pooler_url: str = ""
    supabase_db_password: str = ""
    supabase_anon_key: str = ""
    supabase_direct_url_ind: str = ""
    supabase_session_pooler_url_ind: str = ""
    supabase_transaction_pooler_url_ind: str = ""
    supabase_db_password_ind: str = ""

    # App
    app_env: str = "dev"
    log_level: str = "info"
    zidd_jwt_secret: str = ""
    zidd_jwt_secret_ind: str = ""
    school_enabled: bool = True
    # Pinned by deployment configuration after human review. Production School
    # remains unavailable unless this matches the exact 47-chapter release.
    school_release_attestation_sha256: str = ""

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
    billing_mode: Literal["enabled", "disabled"] = "enabled"
    # `legacy` preserves the pre-beta tariff for existing deployments. New beta
    # and production launches use `journey`: permanent skill/chapter unlocks
    # plus separately metered assessment attempts.
    billing_policy: Literal["legacy", "journey"] = "legacy"
    # During beta the wallet and debits remain real, but purchasing is hidden.
    # It is enabled only once packs are ready for public sale.
    credit_purchases_enabled: bool = True
    beta_credit_grant_enabled: bool = False
    beta_credit_grant_credits: int = 300
    beta_credit_grant_campaign_id: str = "india-beta-2026"
    beta_credit_grant_expires_at: datetime | None = None
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    @field_validator("billing_mode", mode="before")
    @classmethod
    def normalize_billing_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("billing_policy", mode="before")
    @classmethod
    def normalize_billing_policy(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def validate_beta_credit_grant(self) -> "Settings":
        """Keep a beta grant explicitly bounded before it can reach a wallet."""
        if not self.beta_credit_grant_enabled:
            return self
        if self.beta_credit_grant_credits <= 0:
            raise ValueError("beta_credit_grant_credits_must_be_positive")
        if not self.beta_credit_grant_campaign_id.strip():
            raise ValueError("beta_credit_grant_campaign_id_required")
        expiry = self.beta_credit_grant_expires_at
        if expiry is None:
            raise ValueError("beta_credit_grant_expiry_required")
        if expiry.tzinfo is None or expiry.utcoffset() is None:
            raise ValueError("beta_credit_grant_expiry_must_be_timezone_aware")
        if expiry <= datetime.now(expiry.tzinfo):
            raise ValueError("beta_credit_grant_expiry_must_be_future")
        return self

    # Credits granted once on signup, recorded as a "welcome" ledger row.
    welcome_credits: int = 50

    # Explicit local-dev escape hatch for testing credit flows without Razorpay.
    # APP_ENV != prod is not enough: preview/staging deployments are also non-prod.
    enable_dev_credit_grant: bool = False

    @property
    def async_database_url(self) -> str:
        """Runtime DSN: transaction pooler in the selected data region."""

        if self.data_region == "india":
            return _postgres_url(
                self.supabase_transaction_pooler_url_ind,
                self.supabase_db_password_ind,
            )
        return _postgres_url(self.supabase_pooler_url, self.supabase_db_password)

    @property
    def migration_async_database_url(self) -> str:
        """Migration DSN: direct India endpoint, legacy endpoint otherwise."""

        if self.data_region == "india":
            return _postgres_url(
                self.supabase_direct_url_ind,
                self.supabase_db_password_ind,
            )
        return _postgres_url(self.supabase_pooler_url, self.supabase_db_password)

    @property
    def runtime_database_configured(self) -> bool:
        if self.data_region == "india":
            return bool(
                self.supabase_transaction_pooler_url_ind.strip()
                and self.supabase_db_password_ind
            )
        return bool(self.supabase_pooler_url.strip())

    @property
    def migration_database_configured(self) -> bool:
        if self.data_region == "india":
            return bool(
                self.supabase_direct_url_ind.strip()
                and self.supabase_db_password_ind
            )
        return bool(self.supabase_pooler_url.strip())


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
    settings = get_settings()
    data_region = (
        os.environ.get("DATA_REGION") or settings.data_region
    ).strip().lower()
    if data_region == "india":
        secret_name = "ZIDD_JWT_SECRET_IND"
        secret = (
            os.environ.get(secret_name)
            or settings.zidd_jwt_secret_ind
        )
    else:
        secret_name = "ZIDD_JWT_SECRET"
        secret = os.environ.get(secret_name) or settings.zidd_jwt_secret
    if not secret:
        raise RuntimeError(
            f"{secret_name} is not set; refusing to start without a JWT signing secret."
        )
    # In production, refuse a weak secret. A short HMAC key is brute-forceable, so
    # enforce a 32-byte floor when APP_ENV=prod. Non-prod (dev/test/ci) is left
    # permissive so the suite can run with a short fixture secret.
    if (
        os.environ.get("APP_ENV", settings.app_env).lower() == "prod"
        or data_region == "india"
    ) and len(secret) < 32:
        raise RuntimeError(
            f"{secret_name} must be at least 32 characters in production or India beta "
            f"(APP_ENV=prod or DATA_REGION=india); got {len(secret)}."
        )
    return secret
