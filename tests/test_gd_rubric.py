"""BACK-11: GD rubric dimensions.

Tests cover:
  1. SimulationReport carries the three GD rubric sub-scores.
  2. Rubric scoring prompt asks for all three dimensions.
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


# ---- scoring prompt requests rubric fields ----------------------------------

def test_scoring_prompt_requests_rubric_fields():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_simulation_score_prompt
    pack = behavior_for(TaskType.GD_TEST)
    prompt = build_simulation_score_prompt(pack, "Remote work", [])
    assert "participation_score" in prompt
    assert "relevance_score" in prompt
    assert "language_score" in prompt


def test_gd_rubric_scores_debate_moves_not_talk_time():
    """Reframe: the three GD dims are kept (schema/FE stable) but the prompt now
    grades DEBATE MOVES — initiative, rebuttal, evidence, synthesis — and folds
    concision into language. This guards against a silent revert to the old
    talk-time wording."""
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_simulation_score_prompt
    pack = behavior_for(TaskType.GD_TEST)
    prompt = build_simulation_score_prompt(pack, "Remote work", [])
    lowered = prompt.lower()
    assert "debate moves" in lowered
    assert "initiative" in lowered            # participation reframed
    assert "rebut" in lowered                 # relevance: rebuttal move
    assert "synthesise" in lowered or "synthesis" in lowered  # build-on move
    assert "concision" in lowered             # language folds in concision (GD flags)
