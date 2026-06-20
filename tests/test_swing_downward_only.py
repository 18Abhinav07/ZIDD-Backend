"""P1 — the single-turn swing damper smooths DOWNWARD swings only.

The damper exists to absorb LLM scoring NOISE, not to penalize real change. A
genuine recovery (a run of low scores then a real 0.9) was being pulled down just
as hard as a noisy collapse: 0.2 -> 0.9 smoothed to 0.62, below PASS_SCORE, so a
recovered learner could never reach a clean pass / cap refund / challenge.

Fix: blend only when the new score is more than _SWING_THRESHOLD BELOW the prior
(a downward swing). An upward swing passes through at face value. A single noisy
0.9 still can't fake *sustained* mastery, because update_mastery's EMA (alpha 0.3)
moves mastery only 30% of the gap per turn — the EMA, not this damper, is the
guard against a one-off high score masquerading as mastery.

These tests drive the REAL fold (evaluate._result), not a re-implemented copy, so
they pin the production blend end-to-end.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.graph.nodes.evaluate import _result, _SWING_ALPHA  # noqa: E402


def _diag(score: float) -> DiagnosisEval:
    return DiagnosisEval(
        score=score, understanding="x",
        errors=[] if score >= 0.6 else ["e"],
        strengths=["s"] if score >= 0.6 else [],
        next_focus="n", on_task=True, english=True,
    )


def _folded_score(prev, score: float) -> float:
    """The score evaluate._result writes after the swing damper, given a prior."""
    state = {"current_mastery": 0.3}
    if prev is not None:
        state["last_eval_score"] = prev
    return _result(state, _diag(score), smooth=True)["last_eval_score"]


def test_upward_recovery_is_not_damped():
    # 0.2 -> 0.9 (a +0.7 upward swing) must pass through at face value so a real
    # recovery reaches a clean PASS (>= 0.7), not the old 0.62 limbo.
    assert _folded_score(0.2, 0.9) == 0.9


def test_downward_collapse_is_still_damped():
    # 0.9 -> 0.2 (a -0.7 downward swing) is still blended toward the prior so one
    # noisy bad score doesn't slam a strong learner straight into bridge: the raw
    # 0.2 would route to bridge (< 0.4); the damped 0.48 lands in strengthen.
    expected = round(_SWING_ALPHA * 0.2 + (1 - _SWING_ALPHA) * 0.9, 4)  # 0.48
    assert _folded_score(0.9, 0.2) == expected
    assert _folded_score(0.9, 0.2) >= 0.4  # softened out of bridge territory


def test_sub_threshold_moves_pass_through_both_directions():
    # Swings <= _SWING_THRESHOLD (0.4) are never blended, up or down.
    assert _folded_score(0.5, 0.85) == 0.85   # +0.35 up
    assert _folded_score(0.85, 0.5) == 0.5    # -0.35 down


def test_no_prior_score_passes_through():
    # Cold start (no prior, or a 0.0 prior) never smooths — nothing to blend.
    assert _folded_score(None, 0.9) == 0.9
    assert _folded_score(0.0, 0.2) == 0.2
