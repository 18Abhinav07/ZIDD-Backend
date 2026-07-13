from app.services.school_core.readiness import classify_skill_status
from app.services.school_v3_placement import (
    PlacementItem,
    PlacementSessionState,
    apply_confirmed_ready_seed,
    apply_placement_attempt,
    is_duplicate_item_attempt,
    placement_outcome,
)


def test_school_v3_placement_transitions_from_snapshot_to_targeted_to_confirmatory():
    state = PlacementSessionState(
        subject_id="math",
        class_no=7,
        required_skill_ids=("fraction.compare", "decimal.place_value"),
    )

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_fraction_1", skill_id="fraction.compare"),
        evaluator_score=0.82,
        evaluator_confidence=1.0,
    )
    assert state.stage == "snapshot"

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_decimal_1", skill_id="decimal.place_value"),
        evaluator_score=0.40,
        evaluator_confidence=1.0,
    )
    assert state.stage == "targeted_diagnostic"
    assert state.targeted_skill_ids == ("decimal.place_value",)

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="target_decimal_1", skill_id="decimal.place_value"),
        evaluator_score=0.86,
        evaluator_confidence=1.0,
    )
    assert state.stage == "targeted_diagnostic"

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="target_decimal_2", skill_id="decimal.place_value"),
        evaluator_score=0.90,
        evaluator_confidence=1.0,
    )
    assert state.stage == "confirmatory"
    assert state.confirmatory_skill_ids == ("decimal.place_value",)

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="confirm_decimal_1", skill_id="decimal.place_value"),
        evaluator_score=0.92,
        evaluator_confidence=1.0,
    )
    assert placement_outcome(state) == "complete"


def test_snapshot_stage_waits_for_required_skill_coverage_before_targeting():
    state = PlacementSessionState(
        subject_id="english",
        class_no=5,
        required_skill_ids=(
            "reading.word_meaning_context",
            "reading.sentence_comprehension",
            "writing.reason_answer",
        ),
    )

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_vocab", skill_id="reading.word_meaning_context"),
        evaluator_score=0.92,
        evaluator_confidence=1.0,
    )
    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_sentence", skill_id="reading.sentence_comprehension"),
        evaluator_score=0.91,
        evaluator_confidence=1.0,
    )

    assert state.stage == "snapshot"

    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_reason", skill_id="writing.reason_answer"),
        evaluator_score=0.40,
        evaluator_confidence=1.0,
    )

    assert state.stage == "targeted_diagnostic"
    assert state.targeted_skill_ids == ("writing.reason_answer",)


def test_school_v3_placement_elapsed_caps_are_stage_specific_and_server_side():
    state = PlacementSessionState(subject_id="science", class_no=8)
    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_force_1", skill_id="force.motion"),
        evaluator_score=0.70,
        evaluator_confidence=1.0,
        elapsed_seconds_delta=241,
    )

    assert state.elapsed_seconds == 241
    assert placement_outcome(state) == "insufficient_evidence"

    state = PlacementSessionState(
        subject_id="science",
        class_no=8,
        stage="targeted_diagnostic",
        total_items=17,
        targeted_skill_ids=("force.motion",),
    )
    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="target_force_18", skill_id="force.motion"),
        evaluator_score=0.42,
        evaluator_confidence=1.0,
        elapsed_seconds_delta=300,
    )

    assert state.total_items == 18
    assert state.elapsed_seconds == 300
    assert placement_outcome(state) == "insufficient_evidence"

    state = PlacementSessionState(
        subject_id="science",
        class_no=8,
        stage="confirmatory",
        confirmatory_skill_ids=("force.motion",),
    )
    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="confirm_force_1", skill_id="force.motion"),
        evaluator_score=0.91,
        evaluator_confidence=1.0,
        elapsed_seconds_delta=181,
    )

    assert state.stage_elapsed_seconds == 181
    assert placement_outcome(state) == "insufficient_evidence"


def test_confirmed_ready_seed_unlocks_ready_without_mastery():
    state = PlacementSessionState(subject_id="history", class_no=6)
    state = apply_placement_attempt(
        state,
        PlacementItem(item_id="snap_source_1", skill_id="source.inference"),
        evaluator_score=0.93,
        evaluator_confidence=1.0,
    )

    state = apply_confirmed_ready_seed(
        state,
        ready_skill_ids=("source.inference",),
        confidence=0.95,
    )

    skill_state = state.skill_states["source.inference"]
    assert skill_state.certified_readiness == 0.80
    assert skill_state.ready_source == "placement"
    assert skill_state.independent_passes == 0
    assert classify_skill_status(skill_state) == "ready"


def test_duplicate_item_attempt_is_detected_and_idempotent():
    item = PlacementItem(item_id="snap_atom_1", skill_id="atom.structure")
    state = PlacementSessionState(subject_id="science", class_no=6)
    state = apply_placement_attempt(
        state,
        item,
        evaluator_score=0.20,
        evaluator_confidence=1.0,
    )

    assert is_duplicate_item_attempt(state, item.item_id) is True
    replayed = apply_placement_attempt(
        state,
        item,
        evaluator_score=1.0,
        evaluator_confidence=1.0,
    )

    assert replayed is state
    assert replayed.total_items == 1
    assert replayed.skill_attempts["atom.structure"].attempts == 1
    assert replayed.skill_states["atom.structure"].practice_readiness == 0.20
