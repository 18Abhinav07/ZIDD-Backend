from fastapi import APIRouter
import httpx
from app.db.engine import get_engine
from sqlalchemy import text
from app.services.session_service import SessionStore

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
    
    # 2. Check DB
    db_ok = False
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            db_ok = result.scalar() == 1
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
