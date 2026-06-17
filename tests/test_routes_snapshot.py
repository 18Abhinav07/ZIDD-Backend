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


# ---- update_mastery score-smoothing gate ------------------------------------

def test_update_mastery_below_floor_stays_flat():
    assert update_mastery(0.5, 0.3) == 0.5


def test_update_mastery_normal_ema():
    result = update_mastery(0.5, 0.7)
    assert abs(result - (0.5 + 0.3 * (0.7 - 0.5))) < 1e-9


def test_update_mastery_swing_gate_dampens_spike():
    # old=0.3, score=0.9 → swing=0.6 > 0.4 → dampen to midpoint (0.6) before EMA
    result = update_mastery(0.3, 0.9)
    dampened_score = (0.9 + 0.3) / 2  # 0.6
    expected = 0.3 + 0.3 * (dampened_score - 0.3)
    assert abs(result - expected) < 1e-9


def test_update_mastery_swing_gate_dampens_drop():
    # old=0.9, score=0.3 → swing=0.6 > 0.4 → dampen to midpoint (0.6) before EMA
    # dampened_score=0.6 >= MASTERY_RAISE_FLOOR so EMA applies
    result = update_mastery(0.9, 0.3)
    dampened_score = (0.3 + 0.9) / 2  # 0.6
    expected = 0.9 + 0.3 * (dampened_score - 0.9)
    assert abs(result - expected) < 1e-9


def test_update_mastery_swing_exactly_at_gate_not_dampened():
    # swing == 0.4 exactly → NOT > 0.4 → no dampening
    result = update_mastery(0.3, 0.7)
    expected = 0.3 + 0.3 * (0.7 - 0.3)
    assert abs(result - expected) < 1e-9


def test_update_mastery_swing_dampened_below_floor_stays_flat():
    # old=0.8, score=0.0 → swing=0.8 > 0.4, old > 0 → dampen to 0.4 → below floor → flat
    result = update_mastery(0.8, 0.0)
    dampened_score = (0.0 + 0.8) / 2  # 0.4
    # 0.4 < MASTERY_RAISE_FLOOR(0.6) → mastery unchanged
    assert result == 0.8


def test_update_mastery_cold_start_perfect_score_not_dampened():
    # old=0.0 (session start) → gate does NOT apply (old == 0) → normal EMA
    result = update_mastery(0.0, 1.0)
    assert abs(result - 0.3) < 1e-9
