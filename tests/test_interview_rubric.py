"""BACK-12: Interview rubric dimensions + avatar_emotion derivation.

Tests cover:
  1. SimulationReport carries the two interview rubric sub-scores.
  2. Scoring prompt requests clarity_score + confidence_score for interview sessions.
  3. _avatar_emotion derives correct emotion from affect + last_eval_score.
  4. _state_snapshot includes avatar_emotion in the done-frame payload.
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
from app.api.routes import _avatar_emotion, _state_snapshot  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402


# ---- interview rubric schema -------------------------------------------------

def test_simulation_report_has_interview_rubric_fields():
    r = SimulationReport(
        score=0.72,
        summary="Good overall.",
        strengths=["clear structure"],
        improvements=["less hedging"],
    )
    assert r.clarity_score == 0.0
    assert r.confidence_score == 0.0


def test_simulation_report_interview_rubric_round_trip():
    r = SimulationReport(
        score=0.78,
        summary="Solid interview.",
        strengths=[],
        improvements=[],
        clarity_score=0.82,
        confidence_score=0.65,
    )
    assert r.clarity_score == 0.82
    assert r.confidence_score == 0.65


def test_simulation_report_interview_rubric_bounds():
    import pydantic
    with pytest.raises((pydantic.ValidationError, ValueError)):
        SimulationReport(
            score=0.5,
            summary="",
            strengths=[],
            improvements=[],
            clarity_score=1.5,  # out of range
        )


def test_simulation_report_interview_rubric_zero_default_for_gd():
    r = SimulationReport(
        score=0.8,
        summary="GD session.",
        strengths=["spoke up"],
        improvements=[],
        participation_score=0.75,
        relevance_score=0.7,
        language_score=0.8,
    )
    # interview dims default to 0.0 for GD
    assert r.clarity_score == 0.0
    assert r.confidence_score == 0.0


# ---- scoring prompt requests interview rubric fields ------------------------

def test_scoring_prompt_requests_interview_rubric_fields():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_simulation_score_prompt
    pack = behavior_for(TaskType.INTERVIEW_TEST)
    prompt = build_simulation_score_prompt(pack, "Tell me about yourself", [])
    assert "clarity_score" in prompt
    assert "confidence_score" in prompt


def test_scoring_prompt_requests_gd_rubric_fields_still():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_simulation_score_prompt
    pack = behavior_for(TaskType.GD_TEST)
    prompt = build_simulation_score_prompt(pack, "Remote work", [])
    # GD dims still present
    assert "participation_score" in prompt
    assert "relevance_score" in prompt
    assert "language_score" in prompt
    # Interview dims also present (prompt is shared; model told to zero them for GD)
    assert "clarity_score" in prompt
    assert "confidence_score" in prompt


# ---- _avatar_emotion derivation ---------------------------------------------

@pytest.mark.parametrize("affect,score,expected", [
    ("confident", 0.85, "impressed"),
    ("confident", 0.70, "impressed"),   # boundary: 0.7 is exactly >=0.7 → impressed
    ("confident", 0.69, "skeptical"),
    ("confident", 0.0, "skeptical"),
    ("frustrated", 0.9, "empathetic"),
    ("frustrated", 0.0, "empathetic"),
    ("confused", 0.9, "patient"),
    ("confused", 0.0, "patient"),
    ("neutral", 0.75, "engaged"),
    ("neutral", 0.70, "engaged"),
    ("neutral", 0.60, "neutral"),       # 0.5 <= score < 0.7 → neutral
    ("neutral", 0.50, "neutral"),       # boundary: 0.5 is NOT < 0.5 → neutral
    ("neutral", 0.49, "concerned"),
    ("neutral", 0.0, "concerned"),
])
def test_avatar_emotion_derivation(affect, score, expected):
    assert _avatar_emotion(affect, score) == expected


def test_avatar_emotion_none_score_treated_as_zero():
    # No score yet (session just started) → neutral affect + no score → concerned
    assert _avatar_emotion("neutral", None) == "concerned"


def test_avatar_emotion_confident_none_score():
    # confident + no score → skeptical (score defaults to 0.0, which is < 0.7)
    assert _avatar_emotion("confident", None) == "skeptical"


# ---- _state_snapshot includes avatar_emotion --------------------------------

def _minimal_state(affect: str = "neutral", score: float | None = None) -> dict:
    """Minimal TutorState-shaped dict for _state_snapshot."""
    return {
        "session_id": "s1",
        "competency_node": "comm_01_self_intro",
        "current_mastery": 0.5,
        "turn_count": 1,
        "last_diagnosis": {"affect": affect, "on_task": True, "english": True},
        "last_eval_score": score,
        "weakness_context": [],
        "remediation": False,
        "module_done": False,
        "tester_level": False,
    }


def test_state_snapshot_has_avatar_emotion():
    state = _minimal_state("neutral", 0.8)
    snap = _state_snapshot(state)
    assert "avatar_emotion" in snap


def test_state_snapshot_avatar_emotion_neutral_high_score():
    state = _minimal_state("neutral", 0.8)
    snap = _state_snapshot(state)
    assert snap["avatar_emotion"] == "engaged"


def test_state_snapshot_avatar_emotion_frustrated():
    state = _minimal_state("frustrated", 0.3)
    snap = _state_snapshot(state)
    assert snap["avatar_emotion"] == "empathetic"


def test_state_snapshot_avatar_emotion_confident_low():
    state = _minimal_state("confident", 0.5)
    snap = _state_snapshot(state)
    assert snap["avatar_emotion"] == "skeptical"


def test_state_snapshot_affect_still_present():
    state = _minimal_state("confused", 0.6)
    snap = _state_snapshot(state)
    assert snap["affect"] == "confused"
    assert snap["avatar_emotion"] == "patient"
