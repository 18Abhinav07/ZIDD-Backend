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

    # 2. Check the ACTIVE persistence backend. Previously this always probed the
    #    Supabase pooler engine via get_engine(), so a local build — whose real
    #    store is the SQLite LocalStore — reported sqlite_writable:false even
    #    though every credit/purchase/grant persists fine. Ask the active store
    #    (LocalStore under AI_BACKEND=local, else Postgres) about itself instead.
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
        "sqlite_writable": db_ok, # Supabase / sqlite dependent on get_engine
        "active_sessions": active_sessions
    }
