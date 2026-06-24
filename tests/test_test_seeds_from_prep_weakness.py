"""Phase 3.3 — a TEST session seeds its simulation from PREP weaknesses.

The learner coaches in prep where per-skill weaknesses accumulate. The assessment
logs none of its own, so start_session must read the prep sibling's weaknesses
(via prep_counterpart) into weakness_context. A PREP session is unaffected:
prep_counterpart is a no-op for it.

How the weakness is USED diverges by module (P0-4):
  * INTERVIEW: the top weakness is folded into sim_topic (the interviewer's focus)
    so the panel probes exactly what the learner struggled with.
  * GROUP DISCUSSION: sim_topic is a concrete debate MOTION (shared verbatim by
    opening/director/personas), so the weakness must NOT be folded in there — it
    is pressed via probe_items (threaded into the director) instead.

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
INT_NODE = "int_01_elevator_pitch"
_PREP_WEAKNESS = {
    "user_id": "u1",
    "task_type": TaskType.GD_PREP.value,
    "skill_id": "stance_clarity",
    "hit_count": 3,
    "last_score": 0.3,
    "last_seen": 1.0,
    "last_raw": "rambled without taking a clear stance",
}
_INT_PREP_WEAKNESS = {
    "user_id": "u1",
    "task_type": TaskType.INTERVIEW_PREP.value,
    "skill_id": "structure_star_method",
    "hit_count": 3,
    "last_score": 0.3,
    "last_seen": 1.0,
    "last_raw": "rambled without a crisp, structured pitch",
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

    async def get_progression(self, user_id):
        # No prior mastery rows for this fresh test user; matches the real
        # store's list[dict] shape so start_session's progress loop is a no-op
        # instead of raising and wiping weakness_context.
        return []


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


async def test_interview_sim_topic_does_not_leak_prep_weakness(monkeypatch):
    # D3 (Wave 2.2): the weakness must NOT be folded into sim_topic — that string
    # becomes the interviewer's spoken subject and leaked the prep instruction for
    # a returning learner. The weakness is pressed via probe_items -> the director
    # instead; sim_topic stays the neutral teach_focus even with a prep weakness.
    store = _FakeStore({TaskType.INTERVIEW_PREP.value: [_INT_PREP_WEAKNESS]})
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", INT_NODE, test_mode=True)

    topic = state["sim_topic"]
    assert topic == get_node(INT_NODE).teach_focus
    assert "rambled without a crisp, structured pitch" not in topic


async def test_interview_no_prep_weakness_keeps_plain_topic(monkeypatch):
    store = _FakeStore({})  # learner never coached -> no prep weaknesses
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", INT_NODE, test_mode=True)

    assert state["sim_topic"] == get_node(INT_NODE).teach_focus
    assert state["weakness_context"] == []


async def test_gd_weakness_not_leaked_into_motion(monkeypatch):
    # GD (P0-4): the weakness is still loaded into weakness_context (it drives
    # probe_items), but the sim_topic stays a clean concrete motion — the weakness
    # text must NOT leak into the learner-facing debate motion.
    from app.content.motions import GD_MOTIONS

    store = _FakeStore({TaskType.GD_PREP.value: [_PREP_WEAKNESS]})
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", GD_NODE, test_mode=True)

    assert state["weakness_context"] == [_PREP_WEAKNESS]   # still loaded for probes
    assert state["sim_topic"] in GD_MOTIONS
    assert "rambled without taking a clear stance" not in state["sim_topic"]


async def test_prep_session_unaffected(monkeypatch):
    store = _FakeStore({TaskType.GD_PREP.value: [_PREP_WEAKNESS]})
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    _, state = await svc.start_session("u1", GD_NODE, test_mode=False)

    assert state["task_type"] == TaskType.GD_PREP.value
    assert state["sim_topic"] == ""
    # prep still queries its own task type (prep_counterpart no-op)
    assert store.queried == [TaskType.GD_PREP.value]
