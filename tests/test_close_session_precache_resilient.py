"""close_session must never 500 because of the best-effort probe precache.

After a PREP (coaching) session is scored and persisted, close_session warms the
TEST sibling's probe bank via _precache_test_items — an LLM call. Under shared
local-model load that call can raise. The session is already summarised and
persisted by then, so a precache failure must NOT propagate out of /end and lose
the learner's closing payload. It is swallowed and logged instead.

Fully offline: summarize_session is patched, storage is best-effort no-op.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"


def _seed_prep(sid: str = "precache-prep-1") -> str:
    svc.SessionStore[sid] = {
        "user_id": "u1",
        "session_id": sid,
        "competency_node": GD_NODE,
        "task_type": TaskType.GD_PREP.value,  # PREP -> precache path runs
        "current_mastery": 0.3,
        "messages": [
            {"role": "user", "content": "I think remote work helps focus."},
            {"role": "assistant", "content": "Good point — say more about why."},
        ],
    }
    return sid


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    async def _sum(node, messages):
        return "coaching summary"

    monkeypatch.setattr(svc, "summarize_session", _sum)
    yield
    svc.SessionStore.clear()


async def test_precache_failure_does_not_500_or_lose_payload(monkeypatch):
    async def _boom(state):
        raise RuntimeError("local model overloaded")

    monkeypatch.setattr(svc, "_precache_test_items", _boom)

    sid = _seed_prep()
    # Must NOT raise even though the precache blows up.
    result = await svc.close_session(sid)

    assert result["summary"] == "coaching summary"
    assert result["report"] is None  # coaching sessions are summarised, not scored
    # The session is still torn down cleanly despite the precache failure.
    assert svc.get_state(sid) is None


async def test_precache_success_still_closes(monkeypatch):
    calls = []

    async def _ok(state):
        calls.append(state["session_id"])

    monkeypatch.setattr(svc, "_precache_test_items", _ok)

    sid = _seed_prep("precache-prep-2")
    result = await svc.close_session(sid)

    assert result["summary"] == "coaching summary"
    assert calls == ["precache-prep-2"]  # precache still runs on the happy path
    assert svc.get_state(sid) is None
