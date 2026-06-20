"""E24 (Test-fix-01): run_turn must serialize concurrent turns on one session.

Defect: run_turn reads canonical state, awaits the graph/stream, then writes
state back — with no per-session lock. Two turns racing on the same session_id
interleave their read-modify-write and corrupt messages / counters.

RED: with two run_turn coroutines launched concurrently on the SAME session,
the body must never run concurrently (max in-flight == 1). Without a lock the
two streams overlap (max in-flight == 2) and this test fails.

Different sessions must still run concurrently (the lock is per-session, not a
global mutex) — otherwise we'd serialize the whole server.

The in-flight tracker hangs off the persona token stream (the awaited body of a
TEST-mode round); the Director seam is patched to a fast deterministic decision
so the only meaningful await inside the lock is the tracked persona stream.
"""
import asyncio
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DirectorDecision  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation import director as director_mod  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"


def _seed_state(sid: str) -> str:
    svc.SessionStore[sid] = {
        "user_id": "u1",
        "session_id": sid,
        "competency_node": GD_NODE,
        "task_type": TaskType.GD_TEST.value,
        "user_input": "",
        "messages": [],
        "turn_count": 1,
        "current_mastery": 0.0,
        "sim_topic": "Is remote work good for teams?",
        "personas": None,
        "blackboard": None,
        "session_over": False,
        "module_done": False,
        "last_diagnosis": {},
        "last_eval_score": 0.0,
    }
    return sid


class _Tracker:
    """Records max concurrent in-flight run_turn bodies."""

    def __init__(self) -> None:
        self.now = 0
        self.max = 0


@pytest.fixture
def tracker(monkeypatch):
    t = _Tracker()
    raw = "Remote work boosts output."

    # Director seam: fast deterministic decision so the lock-held await that
    # matters is the persona stream below (which carries the in-flight tracker).
    async def _direct(bb, personas, task_type, transcript, probe_items=None):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker=personas[0]["speaker_id"],
            intent="React.",
            tension=0.5,
            answer_quality=0.6,
            should_close=False,
        )

    monkeypatch.setattr(director_mod, "direct_simulation", _direct)

    async def _persona(persona, intent, transcript, bb, roster=None):
        t.now += 1
        t.max = max(t.max, t.now)
        # Hold the body open so a racing turn would overlap if unserialized.
        await asyncio.sleep(0.05)
        t.now -= 1
        for i in range(0, len(raw), 5):
            yield raw[i : i + 5]

    monkeypatch.setattr(sim, "stream_persona_turn", _persona)
    yield t
    svc.SessionStore.clear()


async def _drain(agen):
    async for _ in agen:
        pass


async def test_same_session_turns_serialize(tracker):
    sid = _seed_state("race-sess")
    await asyncio.gather(
        _drain(svc.run_turn(sid, "first answer")),
        _drain(svc.run_turn(sid, "second answer")),
    )
    assert tracker.max == 1, (
        f"run_turn bodies overlapped on one session (max in-flight="
        f"{tracker.max}); a per-session lock is missing"
    )


async def test_different_sessions_run_concurrently(tracker):
    a = _seed_state("sess-a")
    b = _seed_state("sess-b")
    await asyncio.gather(
        _drain(svc.run_turn(a, "answer a")),
        _drain(svc.run_turn(b, "answer b")),
    )
    assert tracker.max == 2, (
        f"different sessions were serialized (max in-flight={tracker.max}); "
        f"the lock must be per-session, not global"
    )
