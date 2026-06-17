"""Phase 3.2 — run_turn dispatches TEST-mode sessions to the simulation path.

For assessment task types (interview_test, gd_test) a turn is NOT scored/coached
through the graph ladder. Instead the learner's contribution is recorded and the
multi-persona simulation streams the next round: Speaker markers interleaved with
each persona's text. Scoring is deferred to session end (score_session), never
mid-stream.

Fully offline: the AI boundary the simulation calls (stream_generation, imported
into simulation_service) is patched to emit a persona-tagged single pass; the
coaching graph must never be invoked on a test turn.
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
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation_service import Speaker  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"


def _seed_state(task_type: str) -> str:
    sid = "sim-sess-1"
    state = {
        "user_id": "u1",
        "session_id": sid,
        "competency_node": GD_NODE,
        "task_type": task_type,
        "user_input": "",
        "messages": [],
        "turn_count": 1,
        "current_mastery": 0.0,
        "sim_topic": "Is remote work good for teams?",
        "personas": None,
        "session_over": False,
        "module_done": False,
        "last_diagnosis": {},
        "last_eval_score": 0.0,
    }
    svc.SessionStore[sid] = state
    return sid


@pytest.fixture(autouse=True)
def _patch_sim(monkeypatch):
    raw = (
        "[Aarav]: Remote work boosts output.\n"
        "[Meera]: It isolates teams, though.\n"
    )

    async def _gen(spec):
        for i in range(0, len(raw), 5):
            yield raw[i : i + 5]

    monkeypatch.setattr(sim, "stream_generation", _gen)

    # the coaching graph must NOT run on a test turn — make it explode if called.
    def _boom():
        raise AssertionError("coaching graph invoked on a TEST-mode turn")

    monkeypatch.setattr("app.services.session_service.get_graph", _boom)
    yield
    svc.SessionStore.clear()


async def _collect(agen):
    out = []
    async for item in agen:
        out.append(item)
    return out


async def test_gd_test_turn_streams_personas_not_graph():
    sid = _seed_state(TaskType.GD_TEST.value)
    out = await _collect(svc.run_turn(sid, "I think it depends on the team."))

    speakers = [t for t in out if isinstance(t, Speaker)]
    assert [s.name for s in speakers] == ["Aarav", "Meera"]
    text = "".join(t for t in out if isinstance(t, str))
    assert "Remote work boosts output." in text
    assert "It isolates teams" in text


async def test_gd_test_turn_does_not_score_midstream():
    sid = _seed_state(TaskType.GD_TEST.value)
    await _collect(svc.run_turn(sid, "I think it depends on the team."))
    state = svc.SessionStore[sid]
    # no scoring side effects on a test turn
    assert state["last_eval_score"] == 0.0
    assert state["last_diagnosis"] == {}


async def test_gd_test_turn_records_learner_and_personas_in_messages():
    sid = _seed_state(TaskType.GD_TEST.value)
    await _collect(svc.run_turn(sid, "I think it depends on the team."))
    state = svc.SessionStore[sid]
    roles = [m["role"] for m in state["messages"]]
    assert roles[0] == "user"
    assert state["messages"][0]["content"] == "I think it depends on the team."
    # the simulation's spoken text is captured as an assistant turn
    assert any(
        m["role"] == "assistant" and "Remote work boosts output." in m["content"]
        for m in state["messages"]
    )
