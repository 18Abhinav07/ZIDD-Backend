"""#1 durability: SessionStore survives a process restart via disk persistence.

In-memory only meant a crash mid-demo lost every live session. Disk-backed
store is opt-in (session_store_path); transient `pending` (a GenSpec, not JSON
serializable and only valid within one turn) is never persisted.
"""
import json
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.calls import GEMINI_FLASH, GenSpec  # noqa: E402
from app.services import session_service as svc  # noqa: E402


def _sample():
    return {
        "session_id": "sX",
        "competency_node": "comm_01_self_intro",
        "turn_count": 4,
        "current_mastery": 0.62,
        "clean_streak": 1,
        "messages": [{"role": "user", "content": "hi"}],
        "last_diagnosis": {"on_task": True, "english": True, "affect": "neutral"},
        "pending": None,
    }


def test_sessions_survive_reload(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "_store_path", lambda: str(tmp_path / "s.json"))
    svc.SessionStore.clear()
    svc.SessionStore["sX"] = _sample()
    svc.save_sessions()

    svc.SessionStore.clear()
    svc.load_sessions()

    assert svc.SessionStore["sX"]["turn_count"] == 4
    assert svc.SessionStore["sX"]["current_mastery"] == 0.62
    assert svc.SessionStore["sX"]["last_diagnosis"]["affect"] == "neutral"


def test_pending_not_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "_store_path", lambda: str(tmp_path / "s.json"))
    svc.SessionStore.clear()
    st = _sample()
    st["pending"] = GenSpec(provider="gemini", model=GEMINI_FLASH, prompt="x", kind="teach")
    svc.SessionStore["sX"] = st
    svc.save_sessions()

    svc.SessionStore.clear()
    svc.load_sessions()

    assert svc.SessionStore["sX"]["pending"] is None


def test_disabled_when_no_path(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "_store_path", lambda: "")
    svc.SessionStore.clear()
    svc.SessionStore["sX"] = _sample()
    svc.save_sessions()          # no-op, must not write or raise
    svc.SessionStore.clear()
    svc.load_sessions()          # no-op, store stays empty
    assert "sX" not in svc.SessionStore


# ---- wiring: real flow persists/removes without an explicit save call ----
import asyncio  # noqa: E402


def test_start_session_persists_to_disk(tmp_path, monkeypatch):
    path = tmp_path / "s.json"
    monkeypatch.setattr(svc, "_store_path", lambda: str(path))
    svc.SessionStore.clear()

    sid, _ = asyncio.run(svc.start_session("u1", "comm_01_self_intro"))

    assert path.exists()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert sid in data


def test_end_session_persists_removal(tmp_path, monkeypatch):
    path = tmp_path / "s.json"
    monkeypatch.setattr(svc, "_store_path", lambda: str(path))

    async def _no_summary(node, messages):
        return ""

    monkeypatch.setattr(svc, "summarize_session", _no_summary)
    svc.SessionStore.clear()

    sid, _ = asyncio.run(svc.start_session("u1", "comm_01_self_intro"))
    asyncio.run(svc.end_session(sid))

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert sid not in data
