"""Zidd engine — FastAPI entrypoint.

Health + DB-ping + the session engine (decision graph, SSE turn streaming).
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import httpx
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.routes import onboarding as onboarding_router
from app.api.routes import router as session_router
from app.api.billing_routes import router as billing_router
from app.api.school_routes import router as school_router
from app.config import get_jwt_secret, get_settings
from app.db.engine import get_engine
from app.services.session_service import load_sessions, save_sessions
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

_UI_FILE = Path(__file__).parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm settings on boot; fail fast if .env malformed.
    get_settings()
    # Fail at BOOT (not first request) if the JWT signing secret is unset.
    get_jwt_secret()
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

@app.exception_handler(httpx.RequestError)
async def httpx_request_error_handler(request: Request, exc: httpx.RequestError):
    return JSONResponse(
        status_code=503,
        content={"detail": "AI service unavailable (Ollama/Gemini down)"},
    )

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(session_router)
app.include_router(onboarding_router)
app.include_router(billing_router)
app.include_router(school_router)


@app.get("/")
async def ui() -> FileResponse:
    """Temporary single-page test harness: onboarding -> placement -> session."""
    return FileResponse(_UI_FILE)
