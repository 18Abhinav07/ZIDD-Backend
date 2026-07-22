from fastapi import APIRouter
import httpx

from app.ai.clients import configured_gemini_api_keys
from app.ai.provider import gemini_runtime_status
from app.config import get_settings
from app.services.session_service import SessionStore
from app.storage import get_storage

router = APIRouter(prefix="/health", tags=["health"])


async def _ollama_reachable(base_url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{base_url.rstrip('/')}/")
        return response.status_code == 200
    except Exception:
        return False


def _model_chain(primary: object, fallback: object) -> list[str]:
    models: list[str] = []
    for value in (primary, fallback):
        model = str(value or "").strip()
        if model and model not in models:
            models.append(model)
    return models


def _ai_diagnostics(settings) -> dict[str, object]:
    backend = settings.ai_backend
    if backend == "local":
        return {"backend": "local", "ready": False}

    gemini_keys = configured_gemini_api_keys()
    runtime = gemini_runtime_status()
    diagnostics: dict[str, object] = {
        "backend": backend,
        # Configuration alone is not a readiness signal: an API key may not
        # have access to the configured model. Startup performs a small real
        # probe and normal calls keep this process-local state current.
        "ready": bool(gemini_keys) and bool(runtime["ready"]),
        "runtime_state": runtime["state"],
        "gemini_credential_count": len(gemini_keys),
        "text_models": _model_chain(
            getattr(settings, "gemini_text_model", ""),
            getattr(settings, "gemini_text_fallback_model", ""),
        ),
        "structured_models": _model_chain(
            getattr(settings, "gemini_structured_model", ""),
            getattr(settings, "gemini_structured_fallback_model", ""),
        ),
    }
    if runtime.get("last_model"):
        diagnostics["last_successful_or_attempted_model"] = runtime["last_model"]
    if runtime.get("last_failure"):
        diagnostics["last_failure"] = runtime["last_failure"]
    if backend == "cloud":
        diagnostics["groq_configured"] = bool(getattr(settings, "groq_api_key", ""))
        diagnostics["ready"] = bool(
            diagnostics["ready"] or diagnostics["groq_configured"]
        )
    return diagnostics


@router.get("")
async def health() -> dict:
    """Check if the backend is reachable and its dependencies."""

    settings = get_settings()
    ollama_ok: bool | None = None
    ai = _ai_diagnostics(settings)
    if settings.ai_backend == "local":
        ollama_ok = await _ollama_reachable(settings.ollama_base_url)
        ai["ready"] = ollama_ok

    # Check the cloud persistence backend.
    db_ok = False
    try:
        db_ok = await get_storage().ping_writable()
    except Exception:
        pass

    # Active sessions are process-local only; durable state remains in Supabase.
    active_sessions = len(SessionStore)

    return {
        "status": "ok",
        "service": "zidd-engine",
        "ollama_reachable": ollama_ok,
        "ai": ai,
        "storage_writable": db_ok,
        "active_sessions": active_sessions,
    }
