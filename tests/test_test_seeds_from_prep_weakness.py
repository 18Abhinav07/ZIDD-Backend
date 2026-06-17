"""Phase 3.3 — a TEST session seeds its simulation from PREP weaknesses.

The learner coaches in prep (gd_prep) where per-skill weaknesses accumulate. The
assessment (gd_test) logs none of its own, so start_session must read the prep
sibling's weaknesses (via prep_counterpart) and fold the top one into sim_topic
so the persona panel probes exactly what the learner struggled with. A PREP
session is unaffected: prep_counterpart is a no-op for it.

Fully offline: get_storage is patched with a fake store; no sqlite, no AI.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.registry import get_node  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"
_PREP_WEAKNESS = {
    "user_id": "u1",
    "task_type": TaskType.GD_PREP.value,
    "skill_id": "stance_clarity",
    "hit_count": 3,
    "last_score": 0.3,
    "last_seen": 1.0,
    "last_raw": "rambled without taking a clear stance",
}


class _FakeStore:
    def __init__(self, by_task_type):
        self._by = by_task_type
        self.queried: list[str] = []

    async def ensure_profile(self, *a, **k):
        return None

    async def create_session(self, *a, **k):
        return None

    async def load_context(self, user_id, task_type):
        return []

    async def get_weaknesses(self, user_id, task_type=None):
        self.queried.append(task_type)
        return list(self._by.get(task_type, []))


@pytest.fixture(autouse=True)
def _clear():
    svc.SessionStore.clear()
    yield
    svc.SessionStore.clear()


async def test_test_session_reads_prep_weaknesses(monkeypatch):
    store = _FakeStore({TaskType.GD_PREP.value: [_PREP_WEAKNESS]})
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", GD_NODE, test_mode=True)

    # weaknesses pulled from the PREP sibling, not the (empty) test task type
    assert TaskType.GD_PREP.value in store.queried
    assert state["weakness_context"] == [_PREP_WEAKNESS]


async def test_sim_topic_folds_in_top_prep_weakness(monkeypatch):
    store = _FakeStore({TaskType.GD_PREP.value: [_PREP_WEAKNESS]})
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", GD_NODE, test_mode=True)

    topic = state["sim_topic"]
    # still anchored on the node's focus, now sharpened by the logged weakness
    assert get_node(GD_NODE).teach_focus in topic
    assert "rambled without taking a clear stance" in topic


async def test_test_session_with_no_prep_weakness_keeps_plain_topic(monkeypatch):
    store = _FakeStore({})  # learner never coached -> no prep weaknesses
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", GD_NODE, test_mode=True)

    assert state["sim_topic"] == get_node(GD_NODE).teach_focus
    assert state["weakness_context"] == []


async def test_prep_session_unaffected(monkeypatch):
    store = _FakeStore({TaskType.GD_PREP.value: [_PREP_WEAKNESS]})
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", GD_NODE, test_mode=False)

    assert state["task_type"] == TaskType.GD_PREP.value
    assert state["sim_topic"] == ""
    # prep still queries its own task type (prep_counterpart no-op)
    assert store.queried == [TaskType.GD_PREP.value]
