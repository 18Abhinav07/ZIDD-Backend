"""Spec B selector — pure unit tests (no network, no disk).

Covers the deterministic stage and the validation/fallback backstops:
  - compute_valid_candidates: terminal node -> []; mid node -> one ADVANCE.
  - build_selection_snapshot: compact, expected keys.
  - fallback_decision: forward candidate -> advance; none -> repeat.
  - validate_decision: snaps out-of-set action/ref; pins REPEAT to current node;
    defaults a blank band.
  - build_selector_prompt: names every candidate's next_ref.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import build_selector_prompt  # noqa: E402
from app.ai.schemas import SelectionDecision  # noqa: E402
from app.content.registry import next_node  # noqa: E402
from app.services.selector import (  # noqa: E402
    build_selection_snapshot,
    compute_valid_candidates,
    fallback_decision,
    validate_decision,
)

MID_NODE = "comm_01_self_intro"
TERMINAL_NODE = "comm_10_voice_pressure"


# ---------- compute_valid_candidates (Stage 1) ----------

def test_terminal_node_yields_no_candidates():
    assert next_node(TERMINAL_NODE) is None  # guard: still the terminal node
    assert compute_valid_candidates({"competency_node": TERMINAL_NODE}) == []


def test_mid_node_yields_single_advance_candidate():
    nxt = next_node(MID_NODE)
    assert nxt is not None  # guard: still a mid node
    cands = compute_valid_candidates({"competency_node": MID_NODE})
    assert cands == [{"action": "ADVANCE", "next_ref": nxt, "band": "standard"}]


def test_single_candidate_targets_linear_next_node():
    # The fast-path target MUST equal the old next_node advance exactly.
    cands = compute_valid_candidates({"competency_node": MID_NODE})
    assert len(cands) == 1
    assert cands[0]["next_ref"] == next_node(MID_NODE)


# ---------- build_selection_snapshot ----------

def test_snapshot_has_expected_keys_and_values():
    state = {
        "competency_node": MID_NODE,
        "current_mastery": 0.42,
        "clean_streak": 2,
        "attempts": 3,
        "weakness_context": [{"skill_id": "tense"}],
    }
    snap = build_selection_snapshot(state)
    assert set(snap) == {
        "current_node",
        "mastery",
        "clean_streak",
        "attempts",
        "weaknesses",
    }
    assert snap["current_node"] == MID_NODE
    assert snap["mastery"] == 0.42
    assert snap["clean_streak"] == 2
    assert snap["attempts"] == 3
    assert snap["weaknesses"] == [{"skill_id": "tense"}]


def test_snapshot_tolerates_sparse_state():
    snap = build_selection_snapshot({"competency_node": MID_NODE})
    assert snap["current_node"] == MID_NODE
    assert snap["mastery"] == 0.0
    assert snap["clean_streak"] == 0
    assert snap["attempts"] == 0
    assert snap["weaknesses"] == []


# ---------- fallback_decision ----------

def test_fallback_advances_to_first_forward_candidate():
    state = {"competency_node": MID_NODE}
    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "SKIP", "next_ref": "comm_03_past_event", "band": "standard"},
    ]
    decision = fallback_decision(state, cands)
    assert isinstance(decision, SelectionDecision)
    assert decision.action == "ADVANCE"
    assert decision.next_ref == "comm_02_describe_routine"
    assert decision.band == "standard"


def test_fallback_repeats_when_no_forward_candidate():
    state = {"competency_node": MID_NODE}
    cands = [{"action": "REPEAT", "next_ref": MID_NODE, "band": "standard"}]
    decision = fallback_decision(state, cands)
    assert decision.action == "REPEAT"
    assert decision.next_ref == MID_NODE


def test_fallback_repeats_when_candidates_empty():
    state = {"competency_node": MID_NODE}
    decision = fallback_decision(state, [])
    assert decision.action == "REPEAT"
    assert decision.next_ref == MID_NODE


# ---------- validate_decision ----------

def _cands():
    return [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
    ]


def test_validate_passes_through_in_set_decision():
    state = {"competency_node": MID_NODE}
    d = SelectionDecision(
        action="ADVANCE",
        next_ref="comm_02_describe_routine",
        band="stretch",
        rationale="strong pass",
    )
    out = validate_decision(d, _cands(), state)
    assert out.action == "ADVANCE"
    assert out.next_ref == "comm_02_describe_routine"
    assert out.band == "stretch"
    assert out.rationale == "strong pass"


def test_validate_snaps_out_of_set_next_ref_to_first_candidate():
    state = {"competency_node": MID_NODE}
    d = SelectionDecision(
        action="ADVANCE",
        next_ref="invented_node_999",
        band="standard",
        rationale="hallucinated ref",
    )
    out = validate_decision(d, _cands(), state)
    assert out.next_ref == "comm_02_describe_routine"


def test_validate_snaps_out_of_set_action_to_first_candidate():
    state = {"competency_node": MID_NODE}
    d = SelectionDecision(
        action="SKIP",  # not in candidate action set {ADVANCE}
        next_ref="comm_02_describe_routine",
        band="standard",
        rationale="action not offered",
    )
    out = validate_decision(d, _cands(), state)
    assert out.action == "ADVANCE"


def test_validate_pins_repeat_to_current_node():
    state = {"competency_node": MID_NODE}
    d = SelectionDecision(
        action="REPEAT",
        next_ref="comm_02_describe_routine",  # must be overwritten
        band="standard",
        rationale="hold here",
    )
    out = validate_decision(d, _cands(), state)
    assert out.action == "REPEAT"
    assert out.next_ref == MID_NODE


def test_validate_defaults_blank_band_to_standard():
    state = {"competency_node": MID_NODE}
    d = SelectionDecision(
        action="ADVANCE",
        next_ref="comm_02_describe_routine",
        band="standard",
        rationale="ok",
    )
    # Pydantic enforces the band Literal, so simulate a blank by clearing it
    # post-construction (the validator treats falsy band as missing).
    object.__setattr__(d, "band", "")
    out = validate_decision(d, _cands(), state)
    assert out.band == "standard"


# ---------- build_selector_prompt ----------

def test_selector_prompt_names_every_candidate_ref():
    snapshot = build_selection_snapshot({"competency_node": MID_NODE})
    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "REMEDIATE", "next_ref": "comm_01b_recap", "band": "foundational"},
    ]
    prompt = build_selector_prompt(snapshot, cands)
    for c in cands:
        assert c["next_ref"] in prompt
    # the snapshot's current node and the band vocabulary must be present
    assert MID_NODE in prompt
    assert "foundational" in prompt and "standard" in prompt and "stretch" in prompt
