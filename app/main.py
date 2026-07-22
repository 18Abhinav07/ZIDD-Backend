"""Zidd engine — FastAPI entrypoint.

Health + DB-ping + the session engine (decision graph, SSE turn streaming).
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.ai.provider import warm_gemini_provider
from app.api.me_routes import router as me_router
from app.api.onboarding_routes import router as profile_onboarding_router
from app.api.routes import onboarding as onboarding_router
from app.api.routes import router as session_router
from app.api.billing_routes import router as billing_router
from app.api.school_retirement_routes import router as school_retirement_router
from app.config import get_jwt_secret, get_settings
from app.db.engine import get_engine
from app.db.schema_guard import validate_runtime_schema
from app.storage import get_storage
from app.services.school.authority import validate_canonical_school_routes
from app.services.school.availability import school_availability
from app.services.school.evaluation_jobs import (
    notify_school_evaluation_job_enqueued,
    run_school_evaluation_worker,
)
from app.services.school.evaluation_policy import school_evaluation_policy
from app.services.session_service import load_sessions, save_sessions
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


_school_runtime_enabled = school_availability().available
if _school_runtime_enabled:
    from app.api.school_rebuild_routes import router as school_router
else:
    from app.api.school_availability_routes import router as school_router

_STORAGE_BOOT_PROBE_ATTEMPTS = 5
_STORAGE_BOOT_PROBE_INITIAL_DELAY_SECONDS = 0.5


async def _storage_is_writable_for_boot(storage) -> bool:
    """Absorb a brief pooler handshake failure without hiding a real outage."""

    for attempt in range(_STORAGE_BOOT_PROBE_ATTEMPTS):
        try:
            if await storage.ping_writable():
                return True
        except Exception:
            # The final false result preserves the existing fail-closed boot
            # contract. Individual probe errors are intentionally not allowed
            # to bring the process up with an unknown persistence state.
            pass
        if attempt < _STORAGE_BOOT_PROBE_ATTEMPTS - 1:
            await asyncio.sleep(
                _STORAGE_BOOT_PROBE_INITIAL_DELAY_SECONDS * (2**attempt)
            )
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm settings on boot; fail fast if .env malformed.
    settings = get_settings()
    # Fail at BOOT (not first request) if the JWT signing secret is unset.
    get_jwt_secret()
    if settings.app_env.lower() != "test":
        if not settings.runtime_database_configured:
            raise RuntimeError(
                "A runtime Supabase transaction-pooler URL is required. "
                "Qwen/Ollama may run locally, but product data is cloud-only."
            )
        if not await _storage_is_writable_for_boot(get_storage()):
            raise RuntimeError("Supabase/Postgres is not writable; refusing to boot.")
        await validate_runtime_schema(
            school_runtime_enabled=_school_runtime_enabled,
        )
        if getattr(settings, "ai_backend", "local") in {"gemini", "cloud"}:
            # A configured key can still lack access to the selected model.
            # Record a bounded, real readiness result before learner traffic.
            await warm_gemini_provider(
                timeout=min(
                    5.0,
                    float(getattr(settings, "gemini_request_timeout_seconds", 30.0)),
                ),
            )
    # Durability #1: restore any disk-persisted live sessions (no-op if disabled).
    load_sessions()
    evaluation_worker_stop: asyncio.Event | None = None
    evaluation_worker_task: asyncio.Task | None = None
    if _school_runtime_enabled and settings.app_env.lower() != "test":
        from app.api.school_rebuild_routes import process_school_evaluation_job

        evaluation_policy = school_evaluation_policy(settings)
        evaluation_worker_stop = asyncio.Event()
        evaluation_worker_task = asyncio.create_task(
            run_school_evaluation_worker(
                store=get_storage(),
                processor=process_school_evaluation_job,
                max_attempts=evaluation_policy.max_worker_attempts,
                stop_event=evaluation_worker_stop,
                processor_timeout_seconds=(
                    evaluation_policy.worker_stall_timeout_seconds
                ),
            ),
            name="school-evaluation-worker",
        )
    try:
        yield
    finally:
        if evaluation_worker_stop is not None and evaluation_worker_task is not None:
            evaluation_worker_stop.set()
            notify_school_evaluation_job_enqueued()
            try:
                await asyncio.wait_for(evaluation_worker_task, timeout=5.0)
            except TimeoutError:
                evaluation_worker_task.cancel()
                await asyncio.gather(evaluation_worker_task, return_exceptions=True)
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
app.include_router(school_retirement_router)
validate_canonical_school_routes(
    app.routes,
    school_enabled=_school_runtime_enabled,
)


@app.get("/")
async def root() -> dict:
    return {"service": "zidd-engine", "status": "ok"}
