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
