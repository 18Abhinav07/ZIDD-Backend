from app.services.school_v2_readiness import (
    AttemptEvidence,
    SkillReadinessState,
    apply_attempt_evidence,
    apply_placement_ready_seed,
    classify_skill_status,
    next_review_interval_days,
)


def test_bridge_success_updates_practice_without_deflating_score_or_certifying():
    state = apply_attempt_evidence(
        SkillReadinessState(skill_id="eng.c3.vocab.context"),
        AttemptEvidence(
            attempt_type="bridge",
            evaluator_score=0.92,
            evaluator_confidence=1.0,
            skill_ids=("eng.c3.vocab.context",),
        ),
    )

    assert state.practice_readiness == 0.92
    assert state.certified_readiness is None
    assert state.certified_attempts == 0
    assert classify_skill_status(state) == "practice_ready"


def test_placement_ready_seed_unlocks_ready_but_not_mastery():
    state = apply_attempt_evidence(
        SkillReadinessState(skill_id="eng.c5.inference.reason"),
        AttemptEvidence(
            attempt_type="placement",
            evaluator_score=0.88,
            evaluator_confidence=1.0,
            skill_ids=("eng.c5.inference.reason",),
        ),
    )

    seeded = apply_placement_ready_seed(state, confidence=0.92)

    assert seeded.practice_readiness == 0.88
    assert seeded.certified_readiness == 0.80
    assert seeded.ready_source == "placement"
    assert seeded.independent_passes == 0
    assert classify_skill_status(seeded) == "ready"


def test_two_strong_independent_passes_certify_readiness_from_cold_start():
    state = SkillReadinessState(skill_id="eng.c4.sentence.answer")
    for _ in range(2):
        state = apply_attempt_evidence(
            state,
            AttemptEvidence(
                attempt_type="independent_check",
                evaluator_score=0.86,
                evaluator_confidence=1.0,
                skill_ids=("eng.c4.sentence.answer",),
                support_level="independent",
            ),
        )

    assert state.certified_readiness >= 0.80
    assert state.independent_passes == 2
    assert classify_skill_status(state) == "ready"


def test_language_mismatch_on_certifying_attempt_updates_practice_only():
    state = apply_attempt_evidence(
        SkillReadinessState(skill_id="eng.c5.answer.english"),
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=0.90,
            evaluator_confidence=1.0,
            skill_ids=("eng.c5.answer.english",),
            support_level="independent",
            language_required="en",
            language_detected="hi",
        ),
    )

    assert state.practice_readiness == 0.90
    assert state.certified_readiness is None
    assert state.independent_passes == 0
    assert "language_mismatch" in state.active_blockers
    assert classify_skill_status(state) == "practice_ready"


def test_mastery_requires_transfer_retention_and_low_hint_dependency():
    state = SkillReadinessState(skill_id="eng.c5.infer.theme")
    for _ in range(3):
        state = apply_attempt_evidence(
            state,
            AttemptEvidence(
                attempt_type="independent_check",
                evaluator_score=0.94,
                evaluator_confidence=1.0,
                skill_ids=("eng.c5.infer.theme",),
                support_level="independent",
                hint_count=0,
            ),
        )

    assert classify_skill_status(state) == "ready"

    state = apply_attempt_evidence(
        state,
        AttemptEvidence(
            attempt_type="transfer_check",
            evaluator_score=0.93,
            evaluator_confidence=1.0,
            skill_ids=("eng.c5.infer.theme",),
            support_level="independent",
            hint_count=0,
        ),
    )

    assert state.certified_readiness >= 0.90
    assert state.transfer_passes == 1
    assert classify_skill_status(state) == "ready"

    state = apply_attempt_evidence(
        state,
        AttemptEvidence(
            attempt_type="review_check",
            evaluator_score=0.93,
            evaluator_confidence=1.0,
            skill_ids=("eng.c5.infer.theme",),
            support_level="independent",
            hint_count=0,
        ),
    )

    assert state.review_passes == 1
    assert classify_skill_status(state) == "mastered"


def test_retention_interval_is_defined_for_ready_mastered_and_failed_review():
    ready = apply_placement_ready_seed(
        SkillReadinessState(skill_id="eng.c5.vocab.context"),
        confidence=0.90,
    )
    assert next_review_interval_days(ready) == 3

    mastered = SkillReadinessState(
        skill_id="eng.c5.infer.theme",
        certified_readiness=0.93,
        independent_passes=3,
        transfer_passes=1,
        review_passes=1,
        recent_hint_flags=(False, False, False, False),
    )
    assert classify_skill_status(mastered) == "mastered"
    assert next_review_interval_days(mastered) == 7
    assert next_review_interval_days(mastered, previous_interval_days=7) == 14
    assert next_review_interval_days(mastered, previous_interval_days=20) == 30
    assert next_review_interval_days(mastered, review_passed=False) == 1
