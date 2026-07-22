import pytest

from app.services.school_core.readiness import (
    AttemptEvidence,
    SkillReadinessState,
    classify_skill_status,
)
from app.services.school.language_confidence import (
    LanguageConfidenceState,
    apply_language_signal,
    curriculum_language_evaluation,
    load_language_confidence,
    persist_language_confidence,
)


def test_language_confidence_does_not_affect_readiness_classification():
    ready = SkillReadinessState(
        skill_id="writing.reason_answer",
        certified_readiness=0.82,
        independent_passes=2,
    )
    weak = SkillReadinessState(
        skill_id="writing.reason_answer",
        practice_readiness=0.42,
        total_attempts=3,
    )

    for confidence in (0.0, 0.25, 0.75, 1.0):
        _ = LanguageConfidenceState(
            user_id="learner",
            en_production_confidence=confidence,
            total_signals=10,
        )
        assert classify_skill_status(ready) == "ready"
        assert classify_skill_status(weak) == "weak"


def test_language_confidence_uses_hints_scaffold_and_mismatch_as_penalties():
    state = LanguageConfidenceState(user_id="learner", en_production_confidence=0.5)
    strong = apply_language_signal(
        state,
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=1.0,
            evaluator_confidence=1.0,
            skill_ids=("writing.reason_answer",),
            support_level="independent",
            language_required="en",
            language_detected="en",
            hint_count=0,
        ),
    )
    scaffolded = apply_language_signal(
        state,
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=1.0,
            evaluator_confidence=1.0,
            skill_ids=("writing.reason_answer",),
            support_level="guided",
            language_required="en",
            language_detected="hi",
            hint_count=3,
        ),
    )

    assert strong.en_production_confidence > state.en_production_confidence
    assert scaffolded.en_production_confidence < strong.en_production_confidence


def test_curriculum_language_confidence_only_uses_certifying_free_english_work():
    """Tutor choices are assessment evidence, not learner English production."""

    evaluation = {
        "scored": True,
        "kind": "independent_check",
        "score": 1.0,
        "confidence": 1.0,
        "language_detected": "en",
    }
    selected_option = {
        "interaction_type": "single_choice",
        "evidence_role": "certifying",
        "certifying_language": "en",
        "options": ["one", "two"],
        "grading_mode": "selected_option",
    }
    supported_free_response = {
        "interaction_type": "paragraph_text",
        "evidence_role": "supported",
        "certifying_language": "en",
        "options": [],
        "grading_mode": "strict_open_rubric",
    }
    certifying_free_response = {
        "interaction_type": "paragraph_text",
        "evidence_role": "certifying",
        "certifying_language": "en",
        "options": [],
        "grading_mode": "strict_open_rubric",
    }

    assert curriculum_language_evaluation(selected_option, evaluation) is None
    assert curriculum_language_evaluation(supported_free_response, evaluation) is None
    assert (
        curriculum_language_evaluation(certifying_free_response, evaluation)
        == evaluation
    )


@pytest.mark.asyncio
async def test_language_confidence_round_trips_through_store(store):
    state = LanguageConfidenceState(
        user_id="learner",
        en_production_confidence=0.64,
        total_signals=7,
    )

    await persist_language_confidence(store, state)
    loaded = await load_language_confidence(store, "learner")

    assert loaded == state
