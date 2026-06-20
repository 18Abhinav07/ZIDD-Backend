"""Spec A — TEST-mode writers'-room simulation (director loop).

The TEST behavior (interview_test / gd_test) runs a *simulation*: per round a
structured Director decision over the shared Blackboard picks WHO speaks and with
WHAT intent, then a single Persona executor STREAMS that one speaker's turn. A
round yields, in order: exactly ONE `Speaker` marker, exactly ONE
`SimulationState` snapshot, then the persona's text tokens. Scoring is deferred
to session end (`score_session`), never mid-stream.

These tests pin the new contract entirely offline by patching the two LLM seams:
the Director (`app.services.simulation.director.direct_simulation`) and the
persona token stream (`stream_persona_turn` on the simulation_service module).
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DirectorDecision, SimulationReport  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation import director as director_mod  # noqa: E402
from app.services.simulation.blackboard import new_blackboard  # noqa: E402
from app.services.simulation_service import (  # noqa: E402
    Speaker,
    SimulationState,
    build_personas,
    score_session,
    stream_simulation_round,
)

pytestmark = pytest.mark.asyncio


# ---- helpers ----------------------------------------------------------------


async def _collect(stream):
    out = []
    async for item in stream:
        out.append(item)
    return out


def _gd_state(messages=None, **overrides):
    """Minimal TEST-mode state the way _new_state seeds it (relevant keys only)."""
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Remote work",
        "messages": messages if messages is not None else [],
        "personas": None,
        "blackboard": None,
    }
    state.update(overrides)
    return state


def _decision(next_speaker: str, *, intent="Expand on the last point.") -> DirectorDecision:
    return DirectorDecision(
        action="probe_deeper",
        next_speaker=next_speaker,
        intent=intent,
        tension=0.5,
        answer_quality=0.6,
        should_close=False,
    )


def _patch_director(monkeypatch, decision: DirectorDecision):
    """Patch the LLM Director seam so decide_round/apply_decision run for real."""

    async def fake(bb, personas, task_type, transcript, probe_items=None):
        return decision

    monkeypatch.setattr(director_mod, "direct_simulation", fake)


def _patch_persona(monkeypatch, *tokens: str):
    """Patch the persona token stream at its call site in simulation_service."""

    async def fake(persona, intent, transcript, bb, roster=None):
        for tok in tokens:
            yield tok

    monkeypatch.setattr(sim, "stream_persona_turn", fake)


# ---- roster -----------------------------------------------------------------


async def test_gd_test_roster_has_distinct_named_personas():
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    names = [p["name"] for p in personas]
    assert len(personas) >= 2
    assert len(set(names)) == len(names)              # distinct names
    assert all(p["speaker_id"] for p in personas)     # every persona addressable
    assert all(p.get("stance") for p in personas)     # GD voices carry a stance


async def test_interview_test_roster_is_interviewer():
    personas = build_personas(TaskType.INTERVIEW_TEST, "Backend role")
    assert len(personas) >= 1
    assert all(p["speaker_id"] for p in personas)


# ---- round runner (director loop, both LLM seams patched) -------------------


async def test_round_yields_speaker_then_state_then_text(monkeypatch):
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    chosen = personas[2]["speaker_id"]  # Director picks WHO speaks (not personas[0])
    _patch_director(monkeypatch, _decision(chosen))
    _patch_persona(monkeypatch, "Remote ", "work ", "boosts output.")

    state = _gd_state(personas=personas)
    out = await _collect(stream_simulation_round(state))

    # exactly one Speaker, exactly one SimulationState, then plain str tokens
    speakers = [i for i in out if isinstance(i, Speaker)]
    states = [i for i in out if isinstance(i, SimulationState)]
    assert len(speakers) == 1
    assert len(states) == 1

    # order: first item Speaker, second item SimulationState, remainder str
    assert isinstance(out[0], Speaker)
    assert isinstance(out[1], SimulationState)
    assert all(isinstance(i, str) for i in out[2:])

    # the Speaker is the Director-chosen next_speaker
    assert out[0].speaker_id == chosen
    assert states[0].speaker_id == chosen
    text = "".join(out[2:])
    assert "Remote work boosts output." in text


async def test_round_persists_roster_and_blackboard(monkeypatch):
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    _patch_director(monkeypatch, _decision(personas[0]["speaker_id"]))
    _patch_persona(monkeypatch, "A point.")

    state = _gd_state()
    fresh = new_blackboard("Remote work")
    await _collect(stream_simulation_round(state))

    # roster cached so speaker_ids stay stable across rounds
    assert state.get("personas")
    again = build_personas(TaskType.GD_TEST, "Remote work")
    assert [p["speaker_id"] for p in state["personas"]] == [
        p["speaker_id"] for p in again
    ]

    # blackboard persisted as a dict with turn advanced vs. a fresh blackboard
    bb = state.get("blackboard")
    assert isinstance(bb, dict)
    assert bb["turn"] == fresh["turn"] + 1


async def test_round_does_not_score_midstream(monkeypatch):
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    _patch_director(monkeypatch, _decision(personas[1]["speaker_id"]))
    _patch_persona(monkeypatch, "point.", " counter.")

    state = _gd_state(personas=personas)
    out = await _collect(stream_simulation_round(state))

    # only Speaker, SimulationState, and str mid-stream; never a SimulationReport
    assert all(isinstance(i, (Speaker, SimulationState, str)) for i in out)
    assert not any(isinstance(i, SimulationReport) for i in out)


async def test_round_director_failure_falls_back(monkeypatch):
    personas = build_personas(TaskType.GD_TEST, "Remote work")

    async def boom(bb, personas, task_type, transcript, probe_items=None):
        raise RuntimeError("director model unavailable")

    monkeypatch.setattr(director_mod, "direct_simulation", boom)
    _patch_persona(monkeypatch, "Falling back cleanly.")

    state = _gd_state(personas=personas)
    out = await _collect(stream_simulation_round(state))

    # decide_round caught the failure and used _fallback_decision (personas[0])
    speakers = [i for i in out if isinstance(i, Speaker)]
    assert len(speakers) == 1
    assert speakers[0].speaker_id == personas[0]["speaker_id"]
    text = "".join(i for i in out if isinstance(i, str))
    assert "Falling back cleanly." in text  # the round still streamed text


async def test_round_empty_persona_turn_falls_back(monkeypatch):
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    _patch_director(monkeypatch, _decision(personas[0]["speaker_id"]))
    _patch_persona(monkeypatch)  # persona stream yields NOTHING

    state = _gd_state(personas=personas)
    out = await _collect(stream_simulation_round(state))

    fallback = "Let's stay with that — can you say more?"
    text = "".join(i for i in out if isinstance(i, str))
    assert fallback in text  # yielded
    # and recorded into the blackboard (note_turn appends the spoken text)
    assert fallback in state["blackboard"]["open_threads"]


async def test_decide_round_empty_roster_raises_before_llm(monkeypatch):
    # An empty roster is a caller contract violation, not a runtime degradation:
    # decide_round must fail fast at the boundary and NEVER waste an LLM
    # round-trip. Spy on the Director seam to prove the guard fires first — a
    # guard placed inside the try block would be swallowed into the fallback
    # (which re-raises the same error) AND would run only after the LLM call.
    called = {"llm": False}

    async def spy(bb, personas, task_type, transcript):
        called["llm"] = True
        return _decision("anyone")

    monkeypatch.setattr(director_mod, "direct_simulation", spy)

    bb = new_blackboard("Remote work")
    with pytest.raises(ValueError, match="non-empty personas roster"):
        await director_mod.decide_round(bb, [], TaskType.GD_TEST, "")
    assert called["llm"] is False  # guard fired before any LLM call


# ---- scoring at end (test sessions scored, not coached mid-stream) ----------


async def test_interview_test_scores_at_end(monkeypatch):
    captured = {}

    async def fake_eval(task_type, topic, messages):
        captured["args"] = (task_type, topic, messages)
        return SimulationReport(
            score=0.72,
            summary="Structured, concrete answers.",
            strengths=["clear ownership"],
            improvements=["quantify impact"],
        )

    # score_session calls the module-global `evaluate_simulation`
    # (imported into simulation_service at module load).
    monkeypatch.setattr(sim, "evaluate_simulation", fake_eval)
    state = {
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Backend role",
        "messages": [{"role": "user", "content": "I led a DB migration."}],
    }
    report = await score_session(state)

    assert isinstance(report, SimulationReport)
    assert report.score == 0.72
    assert report.improvements
    tt, topic, msgs = captured["args"]
    assert tt == TaskType.INTERVIEW_TEST
    assert topic == "Backend role"
    assert msgs == state["messages"]
