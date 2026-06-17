"""Phase 5 — gamification: bridge / review / tester levels + progress surfacing.

The engine has the mechanics (clean-pass streaks, remediation passrate, the
challenge route) but no NAMED, surfaced progression, so a UI cannot draw a
"where am I" bar. Phase 5 names the section the learner is in and exposes it on
the snapshot:

  level_kind (the finer-grained section the learner is currently in):
    test    — a TEST-mode assessment session (precedence over everything),
    bridge  — post-module remediation (module clean-rate fell below the floor),
    review  — module passed; a post-module weakness-summary section,
    tester  — advanced FAST (clean in <=2 attempts) -> harder challenge items,
    prep    — ordinary coaching, the default.

  phase (macro lifecycle, orthogonal to level_kind):
    intro    — session opened, no turn taken yet,
    active   — mid-module,
    complete — module finished.

The two derivations are pure functions (route.py); _maybe_advance flips the
tester/review/remediation flags at the advance boundary; _state_snapshot
surfaces phase, level_kind, and the weakness list for the UI.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.api.routes import _state_snapshot  # noqa: E402
from app.graph.route import level_kind, session_phase  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark_async = pytest.mark.asyncio

GD_PREP_NODE = "gd_01_stake_position"


# ---------- level_kind (pure) ----------

def test_level_kind_defaults_to_prep():
    assert level_kind({"task_type": "gd_prep"}) == "prep"


def test_level_kind_test_session():
    assert level_kind({"task_type": "gd_test"}) == "test"


def test_level_kind_test_outranks_remediation():
    # A TEST session is scored as a whole; a bridge flag must not mislabel it.
    assert level_kind({"task_type": "gd_test", "remediation": True}) == "test"


def test_level_kind_bridge_on_remediation():
    assert level_kind({"task_type": "gd_prep", "remediation": True}) == "bridge"


def test_level_kind_review_when_module_passed():
    assert level_kind({"task_type": "gd_prep", "review_level": True}) == "review"


def test_level_kind_tester_on_fast_success():
    assert level_kind({"task_type": "gd_prep", "tester_level": True}) == "tester"


def test_level_kind_bridge_outranks_tester():
    # Failing the module matters more than a prior fast streak.
    assert (
        level_kind(
            {"task_type": "gd_prep", "remediation": True, "tester_level": True}
        )
        == "bridge"
    )


# ---------- session_phase (pure) ----------

def test_phase_intro_before_first_turn():
    assert session_phase({"turn_count": 0, "module_done": False}) == "intro"


def test_phase_active_mid_module():
    assert session_phase({"turn_count": 3, "module_done": False}) == "active"


def test_phase_complete_when_module_done():
    assert session_phase({"turn_count": 9, "module_done": True}) == "complete"


# ---------- _maybe_advance flips the level flags ----------

def _advance_ready_state(node_id=GD_PREP_NODE, attempts=1, history=None):
    """A state poised to advance: clean streak met, on the given node."""
    return {
        "competency_node": node_id,
        "task_type": "gd_prep",
        "clean_streak": svc.ADVANCE_STREAK,
        "advance_streak": svc.ADVANCE_STREAK,
        "attempts": attempts,
        "node_history": history if history is not None else {},
        "remediation": False,
        "module_done": False,
        "tester_level": False,
        "review_level": False,
    }


@pytest.mark.asyncio
async def test_fast_success_triggers_tester_level():
    """Advancing with attempts <= CLEAN_PASS_MAX_ATTEMPTS sets tester_level."""
    state = _advance_ready_state(attempts=1)
    await svc._maybe_advance(state)
    assert state["tester_level"] is True
    assert level_kind(state) == "tester"


@pytest.mark.asyncio
async def test_slow_success_does_not_trigger_tester_level():
    """A grind-it-out advance (too many attempts) is not a tester level."""
    state = _advance_ready_state(attempts=svc.CLEAN_PASS_MAX_ATTEMPTS + 3)
    await svc._maybe_advance(state)
    assert state["tester_level"] is False


@pytest.mark.asyncio
async def test_module_fail_triggers_bridge_section():
    """A module whose clean-rate fell below the floor enters a bridge section."""
    # Prior nodes mostly failed -> passrate below PASSRATE_FLOOR.
    history = {
        "n1": {"attempts": 9, "clean": False},
        "n2": {"attempts": 9, "clean": False},
        "n3": {"attempts": 1, "clean": True},
    }
    state = _advance_ready_state(attempts=9, history=history)
    await svc._maybe_advance(state)
    assert state["remediation"] is True
    assert level_kind(state) == "bridge"


# ---------- snapshot surfaces the progression fields ----------

@pytest.mark.asyncio
async def test_snapshot_exposes_phase_and_level_kind(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "snap.db"))
    from app.config import get_settings
    from app.storage import reset_storage

    get_settings.cache_clear()
    reset_storage()
    state = svc._new_state(
        "u_snap", "sid_snap", GD_PREP_NODE, "", task_type="gd_prep"
    )
    snap = _state_snapshot(state)
    assert snap["phase"] == "intro"
    assert snap["level_kind"] == "prep"
    assert snap["weaknesses"] == []
    assert snap["tester_level"] is False
    reset_storage()
    get_settings.cache_clear()
