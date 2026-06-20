"""_state_snapshot must surface the new diagnosis flags + redirect/ease routes.

The client cannot render a "redirecting" / "easing off" turn or show affect
unless the snapshot carries last_diagnosis's on_task/english/affect. Pure
function — no network, no DB.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.api.routes import _state_snapshot  # noqa: E402
from app.graph.route import update_mastery  # noqa: E402


def _state(**over):
    s = {
        "session_id": "s1",
        "competency_node": "comm_01_self_intro",
        "current_mastery": 0.5,
        "turn_count": 3,
        "last_route": "redirect",
        "last_eval_score": 0.0,
        "last_diagnosis": {"on_task": False, "english": True, "affect": "frustrated"},
    }
    s.update(over)
    return s


def test_snapshot_exposes_diagnosis_flags():
    snap = _state_snapshot(_state())
    assert snap["on_task"] is False
    assert snap["english"] is True
    assert snap["affect"] == "frustrated"


def test_snapshot_carries_redirect_route():
    assert _state_snapshot(_state())["last_route"] == "redirect"


def test_snapshot_defaults_when_no_diagnosis():
    snap = _state_snapshot(_state(last_diagnosis=None))
    assert snap["on_task"] is True
    assert snap["english"] is True
    assert snap["affect"] == "neutral"


# ---- FIX #4: advancing-turn done frame must carry the REAL affect/score ------

def test_snapshot_uses_last_turn_affect_after_advance():
    # Simulate a post-advance state: _maybe_advance has CLEARED last_diagnosis and
    # last_eval_score, but _track_turn (which ran first) stashed last_turn_affect.
    # The done frame must surface that real affect/score, not the cleared neutral/0.0.
    state = _state(
        last_turn_affect={
            "affect": "frustrated",
            "on_task": False,
            "english": True,
            "last_eval_score": 0.8,
        },
        last_diagnosis={},
        last_eval_score=0.0,
    )
    snap = _state_snapshot(state)
    assert snap["affect"] == "frustrated"
    assert snap["last_eval_score"] == 0.8
    assert snap["on_task"] is False
    assert snap["english"] is True
    assert snap["avatar_emotion"] == "empathetic"  # frustrated → empathetic


def test_snapshot_carries_personas_roster():
    # TEST-mode: the cached roster must ride the done frame so the simulator UI
    # labels speaker bubbles + avatar cards with the REAL names (not a fallback).
    roster = [
        {"speaker_id": "interviewer", "name": "Interviewer", "role": "panel interviewer"},
    ]
    snap = _state_snapshot(_state(personas=roster))
    assert snap["personas"] == roster


def test_snapshot_personas_none_for_coaching_session():
    # No simulation roster (coaching session, or first frame before round 1):
    # the key is present and None so the FE falls back deterministically.
    snap = _state_snapshot(_state())
    assert snap["personas"] is None


def test_snapshot_falls_back_to_diagnosis_when_no_turn_affect():
    # Opening frame: no scored turn yet, so no last_turn_affect key. Fall back to
    # live last_diagnosis / last_eval_score.
    state = _state(
        last_diagnosis={"affect": "confident", "on_task": True, "english": True},
        last_eval_score=0.7,
    )
    assert "last_turn_affect" not in state
    snap = _state_snapshot(state)
    assert snap["affect"] == "confident"
    assert snap["last_eval_score"] == 0.7
    assert snap["on_task"] is True


# ---- update_mastery score-smoothing gate ------------------------------------

def test_update_mastery_sustained_high_climbs_no_freeze():
    # A recovering learner giving repeated genuine 0.9s MUST climb above the
    # cold-start step. The old route-level swing gate blended score against the
    # slow MASTERY itself ((0.9+0.27)/2 = 0.585 < 0.6 floor), freezing them at
    # the cold-start value forever. Single-turn spikes are smoothed upstream in
    # evaluate_node against the prior SCORE, so this route-level gate was wrong.
    m = 0.0
    m = update_mastery(m, 0.9)   # cold start, old==0 so no dampening: 0.27
    m = update_mastery(m, 0.9)   # must keep climbing, not freeze at 0.27
    m = update_mastery(m, 0.9)
    assert m > 0.30


def test_update_mastery_below_floor_stays_flat():
    assert update_mastery(0.5, 0.3) == 0.5


def test_update_mastery_normal_ema():
    result = update_mastery(0.5, 0.7)
    assert abs(result - (0.5 + 0.3 * (0.7 - 0.5))) < 1e-9


def test_update_mastery_high_score_pure_ema():
    # old=0.3, score=0.9 → no route-level swing gate anymore: 0.9 >= floor → pure
    # EMA. 0.3 + 0.3*(0.9-0.3) = 0.48. (Spike calibration is handled upstream in
    # evaluate_node against the prior score, not here against mastery.)
    result = update_mastery(0.3, 0.9)
    expected = 0.3 + 0.3 * (0.9 - 0.3)  # 0.48
    assert abs(result - expected) < 1e-9


def test_update_mastery_low_score_below_floor_stays_flat():
    # old=0.9, score=0.3 → no swing gate: 0.3 < 0.6 floor → mastery unchanged.
    # (A single low score never drags mastery down; it just doesn't raise it.)
    result = update_mastery(0.9, 0.3)
    assert result == 0.9


def test_update_mastery_above_floor_pure_ema():
    # score 0.7 ≥ MASTERY_RAISE_FLOOR(0.6) → pure EMA, no extra gate. (The old
    # route-level swing gate that special-cased a 0.4 swing here is gone.)
    result = update_mastery(0.3, 0.7)
    expected = 0.3 + 0.3 * (0.7 - 0.3)
    assert abs(result - expected) < 1e-9


def test_update_mastery_zero_score_below_floor_stays_flat():
    # score 0.0 < MASTERY_RAISE_FLOOR(0.6) → mastery unchanged, full stop. No
    # dampening step exists at this layer anymore; the sub-floor guard alone
    # holds a recovering learner's mastery flat against a single zero.
    result = update_mastery(0.8, 0.0)
    assert result == 0.8


def test_update_mastery_cold_start_perfect_score_pure_ema():
    # cold start old=0.0, score=1.0 ≥ floor → pure EMA: 0.0 + 0.3*(1.0-0.0) = 0.3.
    result = update_mastery(0.0, 1.0)
    assert abs(result - 0.3) < 1e-9


# ---- evaluate_node spike smoothing — DOWNWARD-only (the ONE correct smoothing) ----
# The route-level swing gate was removed (it double-smoothed against mastery and
# froze recovering learners). Spike dampening still lives upstream in evaluate_node,
# blending the raw score against the PRIOR SCORE — but only on a DOWNWARD swing
# (noise that would wrongly crash a learner). An UPWARD swing is honored at face
# value so a genuine recovery reaches a clean pass. These pure tests mirror the
# evaluate.py blend; the real fold is exercised in test_swing_downward_only.py.

def _smooth(score: float, prev: float | None) -> float:
    from app.graph.nodes.evaluate import _SWING_THRESHOLD, _SWING_ALPHA
    if prev is not None and prev > 0.0 and prev - score > _SWING_THRESHOLD:
        return round(_SWING_ALPHA * score + (1 - _SWING_ALPHA) * prev, 4)
    return score


def test_evaluate_downward_collapse_is_dampened_against_prior_score():
    from app.graph.nodes.evaluate import _SWING_ALPHA
    # prior score 0.9, sudden 0.2 (downward swing 0.7 > 0.4) → blended toward the
    # prior, NOT taken at face value: 0.6*0.2 + 0.4*0.9 = 0.48, softening one noisy
    # low score up out of bridge territory.
    smoothed = _smooth(0.2, 0.9)
    expected = round(_SWING_ALPHA * 0.2 + (1 - _SWING_ALPHA) * 0.9, 4)
    assert abs(smoothed - expected) < 1e-9
    assert smoothed > 0.2  # the dip was pulled up


def test_evaluate_upward_recovery_is_not_dampened():
    # The sign-blind bug: a genuine 0.2 -> 0.9 recovery used to be pulled to 0.62,
    # below PASS, blocking the clean pass / cap refund / challenge. Upward swings
    # now pass through at face value.
    assert _smooth(0.9, 0.2) == 0.9


def test_evaluate_sustained_high_is_not_dampened():
    # A learner already at 0.85 answering 0.9 (swing 0.05 <= 0.4) is NOT a spike —
    # the score passes through untouched, so sustained high performance is honored.
    assert _smooth(0.9, 0.85) == 0.9
