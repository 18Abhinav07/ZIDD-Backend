from app.services.school_v2_placement import (
    PlacementItem,
    PlacementSessionState,
    apply_placement_attempt,
    apply_ready_verdicts,
    next_band_for_skill,
    placement_outcome,
)


def test_placement_attempts_update_practice_but_do_not_certify_before_verdict():
    state = apply_placement_attempt(
        PlacementSessionState(subject_id="english", target_class_no=5),
        PlacementItem(
            item_id="plc_eng_c5_inference_1",
            skill_id="eng.inference.reason",
            difficulty_band="target",
        ),
        evaluator_score=0.88,
        evaluator_confidence=1.0,
    )

    skill_state = state.skill_states["eng.inference.reason"]
    assert skill_state.practice_readiness == 0.88
    assert skill_state.certified_readiness is None
    assert skill_state.certified_attempts == 0
    assert placement_outcome(state) == "in_progress"


def test_two_misses_step_down_only_for_same_skill_and_difficulty_band():
    state = PlacementSessionState(subject_id="english", target_class_no=5)
    item = PlacementItem(
        item_id="plc_eng_c5_vocab_1",
        skill_id="eng.vocab.context",
        difficulty_band="target",
    )

    state = apply_placement_attempt(state, item, evaluator_score=0.30, evaluator_confidence=1.0)
    assert next_band_for_skill(state, "eng.vocab.context", "target") == "target"

    state = apply_placement_attempt(state, item, evaluator_score=0.40, evaluator_confidence=1.0)
    assert next_band_for_skill(state, "eng.vocab.context", "target") == "entry"
    assert next_band_for_skill(state, "eng.sentence.answer", "target") == "target"


def test_placement_has_hard_item_and_evidence_bounds():
    state = PlacementSessionState(subject_id="english", target_class_no=5)
    for index in range(18):
        state = apply_placement_attempt(
            state,
            PlacementItem(
                item_id=f"plc_{index}",
                skill_id="eng.vocab.context",
                difficulty_band="entry",
            ),
            evaluator_score=0.70,
            evaluator_confidence=1.0,
            scorable=index < 7,
        )

    assert state.total_items == 18
    assert state.scorable_answers == 7
    assert placement_outcome(state) == "insufficient_evidence"


def test_ready_verdicts_seed_certified_readiness_for_confirmed_skills():
    state = PlacementSessionState(subject_id="english", target_class_no=5)
    state = apply_placement_attempt(
        state,
        PlacementItem(
            item_id="plc_eng_c5_inference_ready",
            skill_id="eng.inference.reason",
            difficulty_band="target",
        ),
        evaluator_score=0.91,
        evaluator_confidence=1.0,
    )

    state = apply_ready_verdicts(state, ready_skill_ids=("eng.inference.reason",), confidence=0.90)

    skill_state = state.skill_states["eng.inference.reason"]
    assert skill_state.practice_readiness == 0.91
    assert skill_state.certified_readiness == 0.80
    assert skill_state.ready_source == "placement"
    assert skill_state.independent_passes == 0
