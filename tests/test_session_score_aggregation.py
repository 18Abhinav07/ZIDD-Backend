"""P1 — the whole-session TEST score is grounded in the per-round director reads.

A TEST simulation's final score used to be a SINGLE end-of-session LLM pass over a
truncated tail of the transcript. The Director already reads the learner every
round (answer_quality), but only the last value survived. The blackboard now
accumulates EVERY round's answer_quality in `qualities`, and score_session blends
the LLM pass (primary, 0.6) with the per-round mean (0.4) so the score reflects the
whole session instead of one high-variance pass over the tail. Only rounds that
actually ran count; the rubric sub-scores are never blended.
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
from app.services.simulation.blackboard import (  # noqa: E402
    apply_decision, new_blackboard, note_turn,
)


def _decision(quality: float) -> DirectorDecision:
    return DirectorDecision(
        action="probe_deeper", next_speaker="s1", intent="probe",
        tension=0.4, answer_quality=quality, should_close=False,
    )


def _report(score: float) -> SimulationReport:
    return SimulationReport(
        score=score, summary="s", strengths=["a"], improvements=["b"],
        participation_score=0.5, relevance_score=0.5, language_score=0.5,
    )


def _patch_eval(monkeypatch, report: SimulationReport) -> None:
    async def _fake(*a, **k):
        return report
    monkeypatch.setattr(sim, "evaluate_simulation", _fake)


def _state(qualities) -> dict:
    bb = new_blackboard("topic")
    for q in qualities:
        bb = apply_decision(bb, _decision(q))
    return {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "topic",
        "messages": [{"role": "user", "content": "hi"}],
        "blackboard": bb,
    }


# ---------- the blackboard accumulates every round's quality ----------

def test_new_blackboard_starts_with_empty_qualities():
    assert new_blackboard("T")["qualities"] == []


def test_apply_decision_appends_clamped_quality():
    bb = new_blackboard("T")
    bb = apply_decision(bb, _decision(0.8))
    bb = apply_decision(bb, _decision(1.4))    # out-of-range clamps to 1.0
    bb = apply_decision(bb, _decision(-0.2))   # clamps to 0.0
    assert bb["qualities"] == [0.8, 1.0, 0.0]
    assert bb["last_quality"] == 0.0           # last value still tracked separately


def test_note_turn_preserves_qualities():
    bb = apply_decision(new_blackboard("T"), _decision(0.6))
    carried = note_turn(bb, "s1", "something said")
    assert carried["qualities"] == [0.6]       # a reactor turn never drops the series


# ---------- score_session blends the LLM pass with the per-round mean ----------

@pytest.mark.asyncio
async def test_blend_grounds_an_inflated_pass_downward(monkeypatch):
    # LLM pass 0.9, but the learner scored weakly every round (mean 0.5):
    # 0.6*0.9 + 0.4*0.5 = 0.74. The single high pass is pulled toward reality.
    _patch_eval(monkeypatch, _report(0.9))
    report = await sim.score_session(_state([0.4, 0.6, 0.5]))
    assert report.score == pytest.approx(0.74)


@pytest.mark.asyncio
async def test_blend_lifts_a_deflated_pass_upward(monkeypatch):
    # LLM pass 0.4 over a truncated tail, but rounds were strong (mean 0.9):
    # 0.6*0.4 + 0.4*0.9 = 0.6. The truncated low pass is corrected up.
    _patch_eval(monkeypatch, _report(0.4))
    report = await sim.score_session(_state([0.9, 0.9, 0.9]))
    assert report.score == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_sub_scores_survive_the_blend(monkeypatch):
    _patch_eval(monkeypatch, _report(0.9))
    report = await sim.score_session(_state([0.5]))
    # only the top-line blends; the rubric dimensions stay exactly as scored
    assert report.participation_score == pytest.approx(0.5)
    assert report.relevance_score == pytest.approx(0.5)
    assert report.summary == "s"
    assert report.strengths == ["a"]


@pytest.mark.asyncio
async def test_no_rounds_keeps_pure_llm_score(monkeypatch):
    # No director rounds (fallback-only session): the LLM score stands alone.
    _patch_eval(monkeypatch, _report(0.82))
    report = await sim.score_session(_state([]))
    assert report.score == pytest.approx(0.82)


@pytest.mark.asyncio
async def test_missing_blackboard_keeps_pure_llm_score(monkeypatch):
    _patch_eval(monkeypatch, _report(0.82))
    state = {"task_type": TaskType.GD_TEST.value, "sim_topic": "t", "messages": []}
    report = await sim.score_session(state)
    assert report.score == pytest.approx(0.82)


# ---------- LLM-outage fallback rounds must NOT contaminate the blend ----------

def test_apply_decision_fallback_round_skips_quality_series():
    # count_quality=False (a fallback round): the round still advances and tracks
    # last_quality, but its placeholder is kept OUT of the blend series.
    bb = apply_decision(new_blackboard("T"), _decision(0.9))     # one genuine read
    fb = apply_decision(bb, _decision(0.5), count_quality=False)  # outage placeholder
    assert fb["qualities"] == [0.9]      # the 0.5 placeholder did NOT enter the series
    assert fb["turn"] == 2               # round still counts toward the cap
    assert fb["last_quality"] == 0.5     # most-recent still tracked separately


@pytest.mark.asyncio
async def test_decide_round_fallback_does_not_grow_qualities(monkeypatch):
    # The integration guard: when the Director LLM call raises, decide_round must
    # use the fallback decision WITHOUT appending its placeholder quality.
    personas = [{"speaker_id": "s1", "name": "Aarav"}]

    async def _boom(*a, **k):
        raise RuntimeError("Gemini 503 under load")

    monkeypatch.setattr(director_mod, "direct_simulation", _boom)
    bb = apply_decision(new_blackboard("T"), _decision(0.85))     # one real round
    assert bb["qualities"] == [0.85]
    new_bb, _persona, _dec = await director_mod.decide_round(
        bb, personas, TaskType.GD_TEST, "transcript", None
    )
    assert new_bb["qualities"] == [0.85]   # outage round added nothing
    assert new_bb["turn"] == bb["turn"] + 1  # but the round still advanced


@pytest.mark.asyncio
async def test_outage_only_session_keeps_pure_llm_score(monkeypatch):
    # End-to-end regression for the HIGH defect: a session whose every Director
    # round fell back must NOT be down-scored. Previously qualities=[0.5,0.5,...]
    # dragged a strong 0.85 holistic pass down to 0.71; now the blend is skipped.
    personas = [{"speaker_id": "s1", "name": "Aarav"}]

    async def _boom(*a, **k):
        raise RuntimeError("sustained outage")

    monkeypatch.setattr(director_mod, "direct_simulation", _boom)
    bb = new_blackboard("topic")
    for _ in range(4):
        bb, _p, _dec = await director_mod.decide_round(
            bb, personas, TaskType.GD_TEST, "t", None
        )
    assert bb["qualities"] == []           # four fallback rounds, zero contamination
    _patch_eval(monkeypatch, _report(0.85))
    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value, "sim_topic": "topic",
        "messages": [{"role": "user", "content": "hi"}], "blackboard": bb,
    })
    assert report.score == pytest.approx(0.85)   # not 0.71 — outage no longer deflates
