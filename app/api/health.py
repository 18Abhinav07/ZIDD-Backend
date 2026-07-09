from fastapi import APIRouter
import httpx
from app.services.session_service import SessionStore
from app.storage import get_storage

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health() -> dict:
    """Check if the backend is reachable and its dependencies."""

    # 1. Check Ollama
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/")
            if resp.status_code == 200:
                ollama_ok = True
    except Exception:
        pass

    # 2. Check the cloud persistence backend.
    db_ok = False
    try:
        db_ok = await get_storage().ping_writable()
    except Exception:
        pass

    # 3. Active Sessions
    active_sessions = len(SessionStore)

    return {
        "status": "ok", 
        "service": "zidd-engine",
        "ollama_reachable": ollama_ok,
        "storage_writable": db_ok,
        "active_sessions": active_sessions
    }
