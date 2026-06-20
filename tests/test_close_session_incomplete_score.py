"""P1 — a TEST session that can't be scored never persists a silent 0.0.

TEST-mode sessions are scored once at close via score_session; they never run the
per-skill EMA, so state["current_mastery"] sits at ~0.0 the whole time. The old
close_session left avg_score == current_mastery on the scoring-failure path, so a
score_session throw (model/JSON fault) or a quit-before-scorable-transcript
branded the learner with a permanent 0.0 they never earned. The fix falls back to
the director's grounded read (blackboard last_quality) when rounds actually ran,
else a neutral INCOMPLETE_SCORE marker.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import SimulationReport  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402
from app.services import simulation_service as sim  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"


def _seed(sid: str, *, blackboard=None) -> str:
    state = {
        "user_id": "u1",
        "session_id": sid,
        "competency_node": GD_NODE,
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Is remote work good for teams?",
        "current_mastery": 0.0,   # TEST sessions never raise this off the floor
        "messages": [
            {"role": "user", "content": "I think it depends on the team."},
        ],
    }
    if blackboard is not None:
        state["blackboard"] = blackboard
    svc.SessionStore[sid] = state
    return sid


class _RecordingStore:
    """Captures exactly what avg_score close_session persists to the session row."""

    def __init__(self):
        self.end_args = None

    async def end_session(self, session_id, final_summary="", avg_score=0.0):
        self.end_args = {"summary": final_summary, "avg_score": avg_score}

    async def write_memory(self, *a, **k):
        pass


@pytest.fixture
def _store(monkeypatch):
    store = _RecordingStore()
    monkeypatch.setattr(svc, "get_storage", lambda: store)
    yield store
    svc.SessionStore.clear()


def _raise(*a, **k):
    raise RuntimeError("scorer down")


async def test_throw_with_rounds_falls_back_to_blackboard_quality(monkeypatch, _store):
    # A real run that fails to SCORE: use the director's last grounded read, not 0.0.
    monkeypatch.setattr(sim, "evaluate_simulation", _raise)
    sid = _seed("inc-1", blackboard={"turn": 3, "last_quality": 0.64})

    result = await svc.close_session(sid)

    assert result["score"] == pytest.approx(0.64)
    assert result["report"] is None          # nothing scored to surface
    assert _store.end_args["avg_score"] == pytest.approx(0.64)  # persisted, not 0.0


async def test_quit_early_no_rounds_uses_incomplete_marker(monkeypatch, _store):
    # Quit before any scorable round (no blackboard): neutral marker, never 0.0.
    monkeypatch.setattr(sim, "evaluate_simulation", _raise)
    sid = _seed("inc-2")  # no blackboard

    result = await svc.close_session(sid)

    assert result["score"] == pytest.approx(svc.INCOMPLETE_SCORE)
    assert result["score"] != 0.0
    assert _store.end_args["avg_score"] == pytest.approx(svc.INCOMPLETE_SCORE)


async def test_zero_turn_blackboard_uses_incomplete_marker(monkeypatch, _store):
    # A blackboard that exists but recorded no director turn is still "no data".
    monkeypatch.setattr(sim, "evaluate_simulation", _raise)
    sid = _seed("inc-3", blackboard={"turn": 0, "last_quality": 0.5})

    result = await svc.close_session(sid)

    assert result["score"] == pytest.approx(svc.INCOMPLETE_SCORE)


async def test_successful_scoring_is_unchanged(monkeypatch, _store):
    # Regression: the happy path still persists the real report score.
    async def _ok(task_type, topic, messages):
        return SimulationReport(
            score=0.82, summary="strong", strengths=["s"], improvements=["i"],
        )

    monkeypatch.setattr(sim, "evaluate_simulation", _ok)
    sid = _seed("inc-4", blackboard={"turn": 2, "last_quality": 0.3})

    result = await svc.close_session(sid)

    assert result["score"] == pytest.approx(0.82)   # report wins, not last_quality
    assert result["report"] is not None
    assert _store.end_args["avg_score"] == pytest.approx(0.82)
