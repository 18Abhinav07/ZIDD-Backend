"""Zidd engine — FastAPI entrypoint.

Health + DB-ping + the session engine (decision graph, SSE turn streaming).
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.api.routes import onboarding as onboarding_router
from app.api.routes import router as session_router
from app.config import get_settings
from app.db.engine import get_engine
from app.services.session_service import load_sessions, save_sessions

_UI_FILE = Path(__file__).parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm settings on boot; fail fast if .env malformed.
    get_settings()
    # Durability #1: restore any disk-persisted live sessions (no-op if disabled).
    load_sessions()
    yield
    # Flush once more so a clean shutdown never loses the latest turn.
    save_sessions()
    engine = get_engine()
    await engine.dispose()


app = FastAPI(title="Zidd Engine", version="0.0.1", lifespan=lifespan)
app.include_router(session_router)
app.include_router(onboarding_router)


@app.get("/")
async def ui() -> FileResponse:
    """Temporary single-page test harness: onboarding -> placement -> session."""
    return FileResponse(_UI_FILE)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "zidd-engine"}


@app.get("/health/db")
async def health_db() -> dict:
    """Verify the Supabase transaction-pooler connection is live."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        ok = result.scalar() == 1
    return {"status": "ok" if ok else "fail", "db": "supabase-pooler"}
