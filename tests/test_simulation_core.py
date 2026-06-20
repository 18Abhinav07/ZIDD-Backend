"""P1: Pure simulation core — DirectorDecision schema, Blackboard, director helpers.

Tests cover:
  1. DirectorDecision schema: constructs, all 4 action literals accepted.
  2. new_blackboard: correct shape and all default values.
  3. apply_decision: turn increment, tension clamping, phase mapping, last_quality,
     intent appended to covered, value semantics (original bb NOT mutated).
  4. note_turn: appends text to open_threads, sets positions[speaker_id], value semantics.
  5. _fallback_decision: valid DirectorDecision, next_speaker, tension, should_close=False,
     .get fallbacks for empty dict.
  6. _snap_speaker: valid id returned unchanged; unknown id snaps to first persona.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.ai.schemas import DirectorDecision
from app.services.simulation.blackboard import Blackboard, apply_decision, new_blackboard, note_turn
from app.services.simulation.director import _fallback_decision, _snap_speaker


# ---------------------------------------------------------------------------
# DirectorDecision schema
# ---------------------------------------------------------------------------

def test_director_decision_constructs_valid():
    dd = DirectorDecision(
        action="probe_deeper",
        next_speaker="s1",
        intent="Ask for a concrete example.",
        tension=0.5,
        answer_quality=0.7,
        should_close=False,
    )
    assert dd.action == "probe_deeper"
    assert dd.next_speaker == "s1"
    assert dd.tension == 0.5
    assert dd.answer_quality == 0.7
    assert dd.should_close is False


@pytest.mark.parametrize("action", ["probe_deeper", "pivot_topic", "escalate_pressure", "wind_down"])
def test_director_decision_all_four_actions_accepted(action):
    dd = DirectorDecision(
        action=action,
        next_speaker="persona_a",
        intent="Some instruction.",
        tension=0.4,
        answer_quality=0.5,
        should_close=False,
    )
    assert dd.action == action


def test_director_decision_invalid_action_raises():
    import pydantic
    with pytest.raises((pydantic.ValidationError, ValueError)):
        DirectorDecision(
            action="invalid_action",
            next_speaker="s1",
            intent="x",
            tension=0.5,
            answer_quality=0.5,
            should_close=False,
        )


def test_director_decision_tension_allows_out_of_range():
    # tension is plain float — out-of-range should NOT raise (clamped downstream)
    dd = DirectorDecision(
        action="probe_deeper",
        next_speaker="s1",
        intent="x",
        tension=1.7,
        answer_quality=-0.3,
        should_close=False,
    )
    assert dd.tension == 1.7
    assert dd.answer_quality == -0.3


def test_director_decision_should_close_true():
    dd = DirectorDecision(
        action="wind_down",
        next_speaker="s1",
        intent="Wrap it up.",
        tension=0.2,
        answer_quality=0.8,
        should_close=True,
    )
    assert dd.should_close is True


# ---------------------------------------------------------------------------
# new_blackboard
# ---------------------------------------------------------------------------

def test_new_blackboard_correct_shape_and_defaults():
    bb = new_blackboard("Remote work")
    assert bb["topic"] == "Remote work"
    assert bb["phase"] == "opening"
    assert bb["tension"] == 0.3
    assert bb["turn"] == 0
    assert bb["covered"] == []
    assert bb["open_threads"] == []
    assert bb["positions"] == {}
    assert bb["last_quality"] == 0.5


def test_new_blackboard_different_topics():
    bb = new_blackboard("Leadership")
    assert bb["topic"] == "Leadership"


def test_new_blackboard_returns_independent_lists():
    bb1 = new_blackboard("Topic A")
    bb2 = new_blackboard("Topic B")
    bb1["covered"].append("x")
    assert bb2["covered"] == []


# ---------------------------------------------------------------------------
# apply_decision
# ---------------------------------------------------------------------------

def _make_bb(**overrides) -> Blackboard:
    base = new_blackboard("Test topic")
    base.update(overrides)
    return base


def _make_decision(**overrides) -> DirectorDecision:
    defaults = dict(
        action="probe_deeper",
        next_speaker="s1",
        intent="Expand on your answer.",
        tension=0.5,
        answer_quality=0.6,
        should_close=False,
    )
    defaults.update(overrides)
    return DirectorDecision(**defaults)


def test_apply_decision_turn_increments():
    bb = _make_bb(turn=3)
    decision = _make_decision()
    result = apply_decision(bb, decision)
    assert result["turn"] == 4


def test_apply_decision_turn_starts_from_zero():
    bb = new_blackboard("T")
    decision = _make_decision()
    result = apply_decision(bb, decision)
    assert result["turn"] == 1


def test_apply_decision_tension_clamped_high():
    bb = _make_bb()
    decision = _make_decision(tension=1.7)
    result = apply_decision(bb, decision)
    assert result["tension"] == 1.0


def test_apply_decision_tension_clamped_low():
    bb = _make_bb()
    decision = _make_decision(tension=-0.5)
    result = apply_decision(bb, decision)
    assert result["tension"] == 0.0


def test_apply_decision_tension_in_range_unchanged():
    bb = _make_bb()
    decision = _make_decision(tension=0.65)
    result = apply_decision(bb, decision)
    assert result["tension"] == pytest.approx(0.65)


def test_apply_decision_phase_probe_deeper():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(action="probe_deeper"))
    assert result["phase"] == "probing"


def test_apply_decision_phase_pivot_topic():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(action="pivot_topic"))
    assert result["phase"] == "probing"


def test_apply_decision_phase_escalate_pressure():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(action="escalate_pressure"))
    assert result["phase"] == "pressure"


def test_apply_decision_phase_wind_down():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(action="wind_down"))
    assert result["phase"] == "winddown"


def test_apply_decision_last_quality_set():
    bb = _make_bb()
    decision = _make_decision(answer_quality=0.88)
    result = apply_decision(bb, decision)
    assert result["last_quality"] == pytest.approx(0.88)


def test_apply_decision_intent_appended_to_covered():
    bb = _make_bb(covered=["prior subtopic"])
    decision = _make_decision(intent="New intent here")
    result = apply_decision(bb, decision)
    assert "prior subtopic" in result["covered"]
    assert "New intent here" in result["covered"]
    assert len(result["covered"]) == 2


def test_apply_decision_other_keys_carried_over():
    bb = _make_bb(topic="Unique topic", open_threads=["pending question"])
    decision = _make_decision()
    result = apply_decision(bb, decision)
    assert result["topic"] == "Unique topic"
    assert result["open_threads"] == ["pending question"]


def test_apply_decision_does_not_mutate_original():
    bb = _make_bb(open_threads=["existing thread"], positions={"s1": "stance A"})
    original_turn = bb["turn"]
    original_covered = list(bb["covered"])
    original_tension = bb["tension"]
    before_threads = list(bb["open_threads"])
    before_positions = dict(bb["positions"])
    decision = _make_decision(tension=0.9, intent="Check immutability")
    apply_decision(bb, decision)
    # Original bb must be unchanged
    assert bb["turn"] == original_turn
    assert bb["covered"] == original_covered
    assert bb["tension"] == original_tension
    assert bb["open_threads"] == before_threads
    assert bb["positions"] == before_positions


# ---------------------------------------------------------------------------
# note_turn
# ---------------------------------------------------------------------------

def test_note_turn_appends_to_open_threads():
    bb = new_blackboard("T")
    result = note_turn(bb, "alice", "I think remote work is great.")
    assert "I think remote work is great." in result["open_threads"]


def test_note_turn_accumulates_multiple():
    bb = new_blackboard("T")
    r1 = note_turn(bb, "alice", "First point.")
    r2 = note_turn(r1, "bob", "Second point.")
    assert "First point." in r2["open_threads"]
    assert "Second point." in r2["open_threads"]


def test_note_turn_sets_positions():
    bb = new_blackboard("T")
    result = note_turn(bb, "alice", "Remote work is productive.")
    assert result["positions"]["alice"] == "Remote work is productive."


def test_note_turn_overwrites_same_speaker_position():
    bb = new_blackboard("T")
    r1 = note_turn(bb, "alice", "First stance.")
    r2 = note_turn(r1, "alice", "Revised stance.")
    assert r2["positions"]["alice"] == "Revised stance."


def test_note_turn_does_not_mutate_original():
    bb = new_blackboard("T")
    original_threads = list(bb["open_threads"])
    original_positions = dict(bb["positions"])
    note_turn(bb, "alice", "Some text")
    assert bb["open_threads"] == original_threads
    assert bb["positions"] == original_positions


def test_note_turn_other_keys_unchanged():
    bb = _make_bb(tension=0.7, turn=5)
    result = note_turn(bb, "s1", "text")
    assert result["tension"] == 0.7
    assert result["turn"] == 5


def test_note_turn_caps_open_threads_to_rolling_window():
    """open_threads is a bounded rolling window, not an unbounded archive: past
    _MAX_OPEN_THREADS, the OLDEST thread drops off so the director prompt's
    'Open threads' line stays bounded over a long GD (regression: it used to grow
    one entry per turn for the whole session)."""
    from app.services.simulation.blackboard import _MAX_OPEN_THREADS

    bb = new_blackboard("T")
    for i in range(_MAX_OPEN_THREADS + 5):
        bb = note_turn(bb, "alice", f"thread {i}")
    assert len(bb["open_threads"]) == _MAX_OPEN_THREADS
    assert bb["open_threads"][-1] == f"thread {_MAX_OPEN_THREADS + 4}"  # newest kept
    assert "thread 0" not in bb["open_threads"]                        # oldest dropped


def test_persona_block_dead_helper_removed():
    """The orphaned _persona_block roster renderer was removed — build_director_prompt
    renders the roster inline (the canonical path, covered by test_director_prompts).
    Guard against the dead helper creeping back."""
    import app.services.simulation_service as sim_service

    assert not hasattr(sim_service, "_persona_block")


# ---------------------------------------------------------------------------
# _fallback_decision
# ---------------------------------------------------------------------------

PERSONAS = [
    {"speaker_id": "aarav", "name": "Aarav"},
    {"speaker_id": "meera", "name": "Meera"},
]


def test_fallback_decision_returns_valid_director_decision():
    bb = new_blackboard("Leadership")
    dd = _fallback_decision(bb, PERSONAS)
    assert isinstance(dd, DirectorDecision)


def test_fallback_decision_next_speaker_is_first_persona():
    bb = new_blackboard("Leadership")
    dd = _fallback_decision(bb, PERSONAS)
    assert dd.next_speaker == "aarav"


def test_fallback_decision_tension_matches_blackboard():
    bb = _make_bb(tension=0.65)
    dd = _fallback_decision(bb, PERSONAS)
    assert dd.tension == pytest.approx(0.65)


def test_fallback_decision_should_close_false():
    bb = new_blackboard("T")
    dd = _fallback_decision(bb, PERSONAS)
    assert dd.should_close is False


def test_fallback_decision_action_is_probe_deeper():
    bb = new_blackboard("T")
    dd = _fallback_decision(bb, PERSONAS)
    assert dd.action == "probe_deeper"


def test_fallback_decision_empty_bb_tension_default():
    # .get fallback: empty dict -> tension defaults to 0.3
    bb: Blackboard = {}  # type: ignore[assignment]
    dd = _fallback_decision(bb, PERSONAS)
    assert dd.tension == pytest.approx(0.3)


def test_fallback_decision_empty_bb_quality_default():
    # .get fallback: empty dict -> answer_quality defaults to 0.5
    bb: Blackboard = {}  # type: ignore[assignment]
    dd = _fallback_decision(bb, PERSONAS)
    assert dd.answer_quality == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# _snap_speaker
# ---------------------------------------------------------------------------

def test_snap_speaker_valid_id_returned_unchanged():
    result = _snap_speaker("meera", PERSONAS)
    assert result == "meera"


def test_snap_speaker_first_valid_id_returned_unchanged():
    result = _snap_speaker("aarav", PERSONAS)
    assert result == "aarav"


def test_snap_speaker_unknown_id_snaps_to_first():
    result = _snap_speaker("unknown_persona", PERSONAS)
    assert result == "aarav"


def test_snap_speaker_empty_string_snaps_to_first():
    result = _snap_speaker("", PERSONAS)
    assert result == "aarav"


def test_snap_speaker_single_persona_roster():
    personas = [{"speaker_id": "solo", "name": "Solo"}]
    assert _snap_speaker("solo", personas) == "solo"
    assert _snap_speaker("nobody", personas) == "solo"


# ---------------------------------------------------------------------------
# apply_decision — exact-boundary clamp tests (tension and answer_quality)
# ---------------------------------------------------------------------------

def test_apply_decision_tension_boundary_zero():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(tension=0.0))
    assert result["tension"] == pytest.approx(0.0)


def test_apply_decision_tension_boundary_one():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(tension=1.0))
    assert result["tension"] == pytest.approx(1.0)


def test_apply_decision_answer_quality_boundary_zero():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(answer_quality=0.0))
    assert result["last_quality"] == pytest.approx(0.0)


def test_apply_decision_answer_quality_boundary_one():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(answer_quality=1.0))
    assert result["last_quality"] == pytest.approx(1.0)


def test_apply_decision_answer_quality_clamped_high():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(answer_quality=1.7))
    assert result["last_quality"] == pytest.approx(1.0)


def test_apply_decision_answer_quality_clamped_low():
    bb = _make_bb()
    result = apply_decision(bb, _make_decision(answer_quality=-0.5))
    assert result["last_quality"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Empty-roster guard tests for _snap_speaker and _fallback_decision
# ---------------------------------------------------------------------------

def test_snap_speaker_empty_roster_raises():
    with pytest.raises(ValueError):
        _snap_speaker("anything", [])


def test_fallback_decision_empty_roster_raises():
    bb = new_blackboard("Guard test")
    with pytest.raises(ValueError):
        _fallback_decision(bb, [])
