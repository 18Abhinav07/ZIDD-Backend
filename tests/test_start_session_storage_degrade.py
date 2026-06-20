"""Finding #12 — a storage failure during start_session must be LOGGED, not
swallowed silently while the session runs with empty memory/weakness context.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.services import session_service as svc


class _FailingStore:
    async def ensure_profile(self, *a, **k):
        return None

    async def create_session(self, *a, **k):
        return None

    async def load_context(self, *a, **k):
        raise RuntimeError("store down")

    async def get_weaknesses(self, *a, **k):
        return []

    async def get_progression(self, *a, **k):
        return []


@pytest.mark.asyncio
async def test_start_session_logs_storage_failure_and_degrades(monkeypatch, caplog):
    monkeypatch.setattr(svc, "get_storage", lambda: _FailingStore())
    monkeypatch.setattr(svc, "save_sessions", lambda: None)

    with caplog.at_level("WARNING", logger="zidd.session"):
        session_id, state = await svc.start_session("u1", "comm_01_self_intro")

    # Session still starts (degrade-gracefully) but with empty context...
    assert session_id
    assert state["memory_context"] == []
    assert state["weakness_context"] == []
    # ...and the failure is observable, not silently swallowed.
    assert any("storage load failed" in r.getMessage() for r in caplog.records)
