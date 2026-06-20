"""Phase 3.2 — run_turn dispatches TEST-mode sessions to the simulation path.

For assessment task types (interview_test, gd_test) a turn is NOT scored/coached
through the graph ladder. Instead the learner's contribution is recorded and the
writers'-room simulation streams the next round: a Director picks WHO speaks, a
single Persona executor streams that one speaker's turn. Per round run_turn
forwards exactly one `Speaker` marker, one `SimulationState` snapshot, then that
persona's text tokens. Scoring is deferred to session end (score_session), never
mid-stream.

Fully offline: the two LLM seams are patched — the Director
(`app.services.simulation.director.direct_simulation`) and the persona token
stream (`stream_persona_turn`, imported into simulation_service). The coaching
graph must never be invoked on a test turn (get_graph is rigged to explode).
"""
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
from app.services.simulation_service import (  # noqa: E402
    SimulationState,
    Speaker,
    build_personas,
)

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"

# The Director will pick this speaker; "gd_a" maps to Aarav in the GD roster.
_CHOSEN_SPEAKER = "gd_a"
_CHOSEN_NAME = "Aarav"
_PERSONA_TEXT = "Remote work boosts output."


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
        "blackboard": None,
        "session_over": False,
        "module_done": False,
        "last_diagnosis": {},
        "last_eval_score": 0.0,
    }
    svc.SessionStore[sid] = state
    return sid


@pytest.fixture(autouse=True)
def _patch_sim(monkeypatch):
    # Director seam: deterministic decision picking a known speaker.
    async def _direct(bb, personas, task_type, transcript, probe_items=None):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker=_CHOSEN_SPEAKER,
            intent="React to the learner's point.",
            tension=0.5,
            answer_quality=0.6,
            should_close=False,
        )

    monkeypatch.setattr(director_mod, "direct_simulation", _direct)

    # Persona token stream: emit the chosen speaker's turn in small chunks.
    async def _persona(persona, intent, transcript, bb, roster=None):
        for i in range(0, len(_PERSONA_TEXT), 5):
            yield _PERSONA_TEXT[i : i + 5]

    monkeypatch.setattr(sim, "stream_persona_turn", _persona)

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


async def test_gd_test_turn_streams_one_persona_not_graph():
    sid = _seed_state(TaskType.GD_TEST.value)
    out = await _collect(svc.run_turn(sid, "I think it depends on the team."))

    # exactly one Director-chosen speaker this round (not the whole panel)
    speakers = [t for t in out if isinstance(t, Speaker)]
    assert len(speakers) == 1
    assert speakers[0].speaker_id == _CHOSEN_SPEAKER
    assert speakers[0].name == _CHOSEN_NAME

    # that speaker's turn streamed as text; get_graph never fired (else _boom)
    text = "".join(t for t in out if isinstance(t, str))
    assert _PERSONA_TEXT in text


async def test_gd_test_turn_forwards_simulation_state():
    sid = _seed_state(TaskType.GD_TEST.value)
    out = await _collect(svc.run_turn(sid, "I think it depends on the team."))

    states = [t for t in out if isinstance(t, SimulationState)]
    assert len(states) == 1
    assert states[0].speaker_id == _CHOSEN_SPEAKER
    # SimulationState is forwarded untouched (neither Speaker nor str)
    assert not isinstance(states[0], (Speaker, str))


async def test_gd_test_turn_does_not_score_midstream():
    sid = _seed_state(TaskType.GD_TEST.value)
    await _collect(svc.run_turn(sid, "I think it depends on the team."))
    state = svc.SessionStore[sid]
    # no scoring side effects on a test turn (deferred to score_session)
    assert state["last_eval_score"] == 0.0
    assert state["last_diagnosis"] == {}


async def test_gd_test_turn_records_learner_and_personas_in_messages():
    sid = _seed_state(TaskType.GD_TEST.value)
    await _collect(svc.run_turn(sid, "I think it depends on the team."))
    state = svc.SessionStore[sid]

    # learner input recorded first as a user turn ...
    assert state["messages"][0]["role"] == "user"
    assert state["messages"][0]["content"] == "I think it depends on the team."

    # ... immediately followed by the assistant turn carrying the spoken text,
    # prefixed with the persona name marker the runner builds from Speaker.
    assert state["messages"][1]["role"] == "assistant"
    assistant_text = state["messages"][1]["content"]
    assert f"[{_CHOSEN_NAME}]:" in assistant_text
    assert _PERSONA_TEXT in assistant_text


async def test_roster_speaker_id_maps_to_expected_name():
    # guards the assumption baked into the Director patch above
    personas = build_personas(TaskType.GD_TEST, "Is remote work good for teams?")
    by_id = {p["speaker_id"]: p["name"] for p in personas}
    assert by_id[_CHOSEN_SPEAKER] == _CHOSEN_NAME
