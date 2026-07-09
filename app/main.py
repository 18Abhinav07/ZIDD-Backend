"""Zidd engine — FastAPI entrypoint.

Health + DB-ping + the session engine (decision graph, SSE turn streaming).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.me_routes import router as me_router
from app.api.onboarding_routes import router as profile_onboarding_router
from app.api.routes import onboarding as onboarding_router
from app.api.routes import router as session_router
from app.api.billing_routes import router as billing_router
from app.api.school_routes import router as school_router
from app.config import get_jwt_secret, get_settings
from app.db.engine import get_engine
from app.db.schema_guard import validate_runtime_schema
from app.storage import get_storage
from app.services.session_service import load_sessions, save_sessions
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm settings on boot; fail fast if .env malformed.
    settings = get_settings()
    # Fail at BOOT (not first request) if the JWT signing secret is unset.
    get_jwt_secret()
    if settings.app_env.lower() != "test":
        if not settings.supabase_pooler_url:
            raise RuntimeError(
                "SUPABASE_POOLER_URL is required for app runtime storage. "
                "Qwen/Ollama may run locally, but product data is cloud-only."
            )
        if not await get_storage().ping_writable():
            raise RuntimeError("Supabase/Postgres is not writable; refusing to boot.")
        await validate_runtime_schema()
    # Durability #1: restore any disk-persisted live sessions (no-op if disabled).
    load_sessions()
    yield
    # Flush once more so a clean shutdown never loses the latest turn.
    save_sessions()
    engine = get_engine()
    await engine.dispose()


app = FastAPI(title="Zidd Engine", version="0.0.1", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(JWTAuthMiddleware)
# Added LAST so it becomes the OUTERMOST middleware (Starlette applies
# add_middleware() calls in reverse order) — CORS preflight OPTIONS requests
# must be answered before hitting auth/rate-limit logic, or browsers get a
# same-origin-looking 401/429 instead of a proper CORS response. Explicit
# allow-list only: CORSMiddleware itself refuses "*" with allow_credentials=True,
# and a wildcard would be unacceptable anyway for an app carrying bearer tokens.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.exception_handler(httpx.RequestError)
async def httpx_request_error_handler(request: Request, exc: httpx.RequestError):
    return JSONResponse(
        status_code=503,
        content={"detail": "AI service unavailable (Ollama/Gemini down)"},
    )

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(me_router)
app.include_router(profile_onboarding_router)
app.include_router(session_router)
app.include_router(onboarding_router)
app.include_router(billing_router)
app.include_router(school_router)


@app.get("/")
async def root() -> dict:
    return {"service": "zidd-engine", "status": "ok"}
