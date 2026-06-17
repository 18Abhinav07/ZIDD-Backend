"""BACK-11: GD rubric dimensions + tension signal.

Tests cover:
  1. SimulationReport carries the three GD rubric sub-scores.
  2. Tension level increases correctly with gd_turn_count.
  3. Prompt content changes at each tension level.
  4. gd_turn_count is incremented by stream_simulation_round.
  5. Rubric scoring prompt asks for all three dimensions.
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
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation_service import (  # noqa: E402
    _gd_tension_level,
    _tension_block,
    build_personas,
    build_simulation_prompt,
    stream_simulation_round,
)

pytestmark = pytest.mark.asyncio


# ---- rubric schema ----------------------------------------------------------

def test_simulation_report_has_rubric_fields():
    r = SimulationReport(
        score=0.72,
        summary="Good overall.",
        strengths=["clear stance"],
        improvements=["more evidence"],
    )
    # defaults to 0.0 — no KeyError, no crash
    assert r.participation_score == 0.0
    assert r.relevance_score == 0.0
    assert r.language_score == 0.0


def test_simulation_report_rubric_fields_are_validated():
    r = SimulationReport(
        score=0.72,
        summary="Good overall.",
        strengths=[],
        improvements=[],
        participation_score=0.8,
        relevance_score=0.6,
        language_score=0.75,
    )
    assert r.participation_score == 0.8
    assert r.relevance_score == 0.6
    assert r.language_score == 0.75


def test_simulation_report_rubric_bounds():
    import pydantic
    with pytest.raises((pydantic.ValidationError, ValueError)):
        SimulationReport(
            score=0.5,
            summary="",
            strengths=[],
            improvements=[],
            participation_score=1.5,  # out of range
        )


# ---- tension level derivation -----------------------------------------------

@pytest.mark.parametrize("gd_turn_count,expected_level", [
    (0, 0),
    (1, 0),
    (2, 1),
    (3, 1),
    (4, 2),
    (5, 2),
    (10, 2),   # capped at 2
    (100, 2),  # capped at 2
])
def test_tension_level_from_turn_count(gd_turn_count, expected_level):
    state = {"gd_turn_count": gd_turn_count}
    assert _gd_tension_level(state) == expected_level


def test_tension_level_zero_when_no_count():
    assert _gd_tension_level({}) == 0


# ---- tension block content --------------------------------------------------

def test_tension_block_level_0_independent():
    block = _tension_block(0)
    # level 0: personas react independently, no cross-persona challenge
    assert "independently" in block.lower() or "each participant" in block.lower()
    assert "challenge" not in block.lower() or "cross" not in block.lower()


def test_tension_block_level_1_has_direct_challenge():
    block = _tension_block(1)
    # level 1 must instruct at least one persona to challenge another by name
    assert "challenge" in block.lower() or "disagree" in block.lower()
    assert "name" in block.lower() or "by name" in block


def test_tension_block_level_2_heated():
    block = _tension_block(2)
    assert "heated" in block.lower() or "intense" in block.lower()
    assert "firm" in block.lower() or "reasoned" in block.lower()


def test_tension_block_levels_differ():
    b0 = _tension_block(0)
    b1 = _tension_block(1)
    b2 = _tension_block(2)
    assert b0 != b1
    assert b1 != b2
    assert b0 != b2


# ---- prompt carries tension level -------------------------------------------

def test_prompt_level_0_no_cross_fire():
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    prompt = build_simulation_prompt(
        TaskType.GD_TEST, personas, "Remote work", [], "I think so.", tension_level=0
    )
    assert "heated" not in prompt.lower()
    assert "cross-fire" not in prompt.lower()


def test_prompt_level_1_mentions_challenge_by_name():
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    prompt = build_simulation_prompt(
        TaskType.GD_TEST, personas, "Remote work", [], "I think so.", tension_level=1
    )
    assert "name" in prompt.lower() or "by name" in prompt


def test_prompt_level_2_mentions_heated():
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    prompt = build_simulation_prompt(
        TaskType.GD_TEST, personas, "Remote work", [], "I think so.", tension_level=2
    )
    assert "heated" in prompt.lower() or "intense" in prompt.lower()


def test_prompt_default_tension_is_zero():
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    prompt_default = build_simulation_prompt(
        TaskType.GD_TEST, personas, "Remote work", [], "ok"
    )
    prompt_explicit = build_simulation_prompt(
        TaskType.GD_TEST, personas, "Remote work", [], "ok", tension_level=0
    )
    assert prompt_default == prompt_explicit


# ---- gd_turn_count increments after round -----------------------------------

def _chunked(text: str, size: int = 4):
    async def gen(spec):
        for i in range(0, len(text), size):
            yield text[i : i + size]
    return gen


async def test_turn_count_starts_at_zero():
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Topic",
        "messages": [],
        "user_input": "ok",
    }
    assert state.get("gd_turn_count", 0) == 0


async def test_turn_count_increments_after_round(monkeypatch):
    monkeypatch.setattr(sim, "stream_generation", _chunked("[Aarav]: hi.\n[Meera]: hi too."))
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Topic",
        "messages": [],
        "user_input": "ok",
    }
    async for _ in stream_simulation_round(state):
        pass
    assert state["gd_turn_count"] == 1


async def test_turn_count_accumulates_across_rounds(monkeypatch):
    monkeypatch.setattr(sim, "stream_generation", _chunked("[Aarav]: hi."))
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Topic",
        "messages": [],
        "user_input": "ok",
    }
    for _ in range(3):
        async for _ in stream_simulation_round(state):
            pass
    assert state["gd_turn_count"] == 3


async def test_tension_level_used_in_prompt_across_rounds(monkeypatch):
    captured_prompts = []

    def fake_gen(spec):
        captured_prompts.append(spec.prompt)

        async def gen():
            yield "[Aarav]: point."
        return gen()

    monkeypatch.setattr(sim, "stream_generation", fake_gen)
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Topic",
        "messages": [],
        "user_input": "ok",
        "gd_turn_count": 0,
    }
    # Round 1 — turn_count=0, tension_level=0
    async for _ in stream_simulation_round(state):
        pass
    # Round 2 — turn_count=1, still tension_level=0
    async for _ in stream_simulation_round(state):
        pass
    # Round 3 — turn_count=2, tension_level=1 now
    state["user_input"] = "updated"
    async for _ in stream_simulation_round(state):
        pass

    assert len(captured_prompts) == 3
    # Prompt 3 (round 3) must have the level-1 tension wording
    assert "name" in captured_prompts[2].lower() or "challenge" in captured_prompts[2].lower()
    # Prompt 1 must NOT have heated/challenge-by-name wording (level 0)
    assert "heated" not in captured_prompts[0].lower()


# ---- scoring prompt requests rubric fields ----------------------------------

def test_scoring_prompt_requests_rubric_fields():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_simulation_score_prompt
    pack = behavior_for(TaskType.GD_TEST)
    prompt = build_simulation_score_prompt(pack, "Remote work", [])
    assert "participation_score" in prompt
    assert "relevance_score" in prompt
    assert "language_score" in prompt
