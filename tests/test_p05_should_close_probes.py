"""P0-5 — the Director's `should_close` is consumed and `probe_items` reach it.

Two dead signals this pins:
  * should_close was decided every round and never read, so a TEST sim never
    self-terminated. It now rides the SimulationState marker, and a hard round
    cap forces it (and flags the session over) as a deterministic backstop.
  * probe_items (the prep-weakness bank) were generated/cached/persisted then
    never passed to the Director, so the candidate's weaknesses were never
    pressed. They now thread into decide_round -> direct_simulation -> the prompt.
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
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation import director as director_mod  # noqa: E402
from app.services.simulation.blackboard import new_blackboard  # noqa: E402
from app.services.simulation_service import (  # noqa: E402
    MAX_SIM_ROUNDS,
    SimulationState,
    build_personas,
    stream_simulation_round,
)

def _decision(should_close=False):
    return DirectorDecision(
        action="probe_deeper",
        next_speaker="gd_a",
        intent="Press the stance.",
        tension=0.5,
        answer_quality=0.6,
        should_close=should_close,
    )


def _patch(monkeypatch, decision):
    async def _direct(bb, personas, task_type, transcript, probe_items=None):
        return decision

    async def _persona(persona, intent, transcript, bb, roster=None):
        yield "a line"

    monkeypatch.setattr(director_mod, "direct_simulation", _direct)
    monkeypatch.setattr(sim, "stream_persona_turn", _persona)


def _gd_state(**over):
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Remote work",
        "personas": personas,
        "blackboard": None,
        "messages": [{"role": "user", "content": "I take a clear stance."}],
        "probe_items": [],
    }
    state.update(over)
    return state


async def _collect(agen):
    return [t async for t in agen]


@pytest.mark.asyncio
async def test_director_should_close_surfaces_on_marker(monkeypatch):
    _patch(monkeypatch, _decision(should_close=True))
    state = _gd_state()
    out = await _collect(stream_simulation_round(state))
    ss = [i for i in out if isinstance(i, SimulationState)][0]
    assert ss.should_close is True
    # one round in, well below the cap, so the session is NOT force-ended
    assert state.get("session_over") is not True


@pytest.mark.asyncio
async def test_hard_cap_forces_close_and_session_over(monkeypatch):
    # Director itself says keep going, but the round cap is reached.
    _patch(monkeypatch, _decision(should_close=False))
    bb = new_blackboard("Remote work")
    bb["turn"] = MAX_SIM_ROUNDS - 1   # apply_decision bumps to the cap this round
    state = _gd_state(blackboard=bb)
    out = await _collect(stream_simulation_round(state))
    ss = [i for i in out if isinstance(i, SimulationState)][0]
    assert ss.should_close is True
    assert state["session_over"] is True


@pytest.mark.asyncio
async def test_probe_items_reach_the_director(monkeypatch):
    captured = {}

    async def _direct(bb, personas, task_type, transcript, probe_items=None):
        captured["probe_items"] = probe_items
        return _decision()

    async def _persona(persona, intent, transcript, bb, roster=None):
        yield "a line"

    monkeypatch.setattr(director_mod, "direct_simulation", _direct)
    monkeypatch.setattr(sim, "stream_persona_turn", _persona)

    probes = [{"skill_id": "GD_REBUTTAL", "prompt": "Rebut the remote-work claim.", "aim": "directly rebuts"}]
    state = _gd_state(probe_items=probes)
    await _collect(stream_simulation_round(state))
    assert captured["probe_items"] == probes


def test_director_prompt_renders_probe_bank():
    from app.ai.prompts import build_director_prompt
    bb = new_blackboard("Remote work")
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    probes = [{"skill_id": "GD_REBUTTAL", "prompt": "Rebut the claim that remote work hurts culture.", "aim": "directly rebuts"}]
    prompt = build_director_prompt(bb, personas, TaskType.GD_TEST, "transcript", probes)
    assert "Probe bank" in prompt
    assert "Rebut the claim that remote work hurts culture." in prompt


def test_director_prompt_no_probe_section_when_empty():
    from app.ai.prompts import build_director_prompt
    bb = new_blackboard("Remote work")
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    prompt = build_director_prompt(bb, personas, TaskType.GD_TEST, "transcript", [])
    assert "Probe bank" not in prompt
