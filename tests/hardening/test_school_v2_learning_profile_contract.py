import asyncio

from app.services.school_v2_evaluator import SchoolOpenAnswerEvaluation, to_attempt_evidence
from app.services.school_v2_learning import SCHOOL_DOMAIN, SchoolLearningProfileService
from app.services.school_v2_readiness import (
    SkillReadinessState,
    apply_attempt_evidence,
    apply_placement_ready_seed,
)


def _run(coro):
    return asyncio.run(coro)


def test_school_attempt_updates_global_learning_event_and_school_profile(store):
    evaluation = SchoolOpenAnswerEvaluation.model_validate(
        {
            "skill_ids": ["eng.c5.inference.reason"],
            "score": 0.86,
            "confidence": 0.90,
            "language_detected": "en",
            "criteria": [
                {
                    "criterion_id": "clear_reason",
                    "passed": True,
                    "score": 0.86,
                    "evidence_quote": "because the character helped",
                }
            ],
            "misconception_tags": [],
            "blockers": [],
            "feedback_to_learner": "Add one exact event next.",
        }
    )
    evidence = to_attempt_evidence(
        evaluation,
        attempt_type="independent_check",
        support_level="independent",
        language_required="en",
    )
    state = apply_attempt_evidence(
        SkillReadinessState(skill_id="eng.c5.inference.reason"),
        evidence,
    )

    _run(
        SchoolLearningProfileService(store).record_attempt(
            attempt_id="attempt-1",
            user_id="user-1",
            subject_id="english",
            class_no=5,
            session_id="school-session-1",
            chapter_id="eng_c5_pilot",
            node_id="eng_c5_pilot_l1",
            skill_state=state,
            evidence=evidence,
            criteria_json=[criterion.model_dump() for criterion in evaluation.criteria],
            evidence_json={"answer_excerpt": "because the character helped"},
            gap="use_text_evidence",
        )
    )

    assert len(store.learning_events) == 1
    event = store.learning_events[0]
    assert event["source_event_key"] == "school_v2_attempt:attempt-1:eng.c5.inference.reason"
    assert event["domain"] == SCHOOL_DOMAIN
    assert event["task_type"] == "school_lesson"
    assert event["skill_id"] == "eng.c5.inference.reason"
    assert event["scenario_json"] == {
        "subject_id": "english",
        "class_no": 5,
        "chapter_id": "eng_c5_pilot",
    }
    assert event["evidence_json"]["certified_readiness"] == state.certified_readiness

    profile = store.learner_skill_profiles[("user-1", SCHOOL_DOMAIN, "eng.c5.inference.reason")]
    assert profile["readiness"] == state.certified_readiness
    assert profile["mastery"] == 0.0
    assert profile["evidence_json"]["status"] == "practice_ready"


def test_school_placement_seed_profile_records_ready_without_mastery(store):
    evidence = to_attempt_evidence(
        SchoolOpenAnswerEvaluation.model_validate(
            {
                "skill_ids": ["eng.c5.vocab.context"],
                "score": 0.91,
                "confidence": 0.88,
                "language_detected": "en",
                "criteria": [
                    {
                        "criterion_id": "understands_word",
                        "passed": True,
                        "score": 0.91,
                        "evidence_quote": "The answer names a valid meaning.",
                    }
                ],
                "misconception_tags": [],
                "blockers": [],
                "feedback_to_learner": "Ready for the chapter.",
            }
        ),
        attempt_type="placement",
        support_level="independent",
    )
    state = apply_attempt_evidence(SkillReadinessState(skill_id="eng.c5.vocab.context"), evidence)
    state = apply_placement_ready_seed(state, confidence=0.88)

    _run(
        SchoolLearningProfileService(store).record_attempt(
            attempt_id="placement-1",
            user_id="user-1",
            subject_id="english",
            class_no=5,
            session_id="placement-session-1",
            chapter_id="",
            node_id="placement",
            skill_state=state,
            evidence=evidence,
            criteria_json=[],
            evidence_json={},
            source="placement_attempt",
            task_type="school_placement",
        )
    )

    profile = store.learner_skill_profiles[("user-1", SCHOOL_DOMAIN, "eng.c5.vocab.context")]
    assert profile["readiness"] == 0.80
    assert profile["mastery"] == 0.0
    assert profile["evidence_json"]["ready_source"] == "placement"
    assert profile["evidence_json"]["status"] == "ready"


def test_school_learning_event_is_idempotent_by_attempt_and_skill(store):
    evidence = to_attempt_evidence(
        SchoolOpenAnswerEvaluation.model_validate(
            {
                "skill_ids": ["eng.c3.answer.reason"],
                "score": 0.70,
                "confidence": 0.80,
                "language_detected": "en",
                "criteria": [
                    {
                        "criterion_id": "clear_reason",
                        "passed": False,
                        "score": 0.70,
                        "evidence_quote": "The answer is incomplete.",
                    }
                ],
                "misconception_tags": ["thin_reason"],
                "blockers": [],
                "feedback_to_learner": "Tell why, not only what happened.",
            }
        ),
        attempt_type="guided",
        support_level="guided",
    )
    state = apply_attempt_evidence(SkillReadinessState(skill_id="eng.c3.answer.reason"), evidence)
    service = SchoolLearningProfileService(store)

    for _ in range(2):
        _run(
            service.record_attempt(
                attempt_id="dup-attempt",
                user_id="user-1",
                subject_id="english",
                class_no=3,
                session_id="school-session-2",
                chapter_id="eng_c3_pilot",
                node_id="eng_c3_pilot_l1",
                skill_state=state,
                evidence=evidence,
                criteria_json=[],
                evidence_json={},
            )
        )

    assert len(store.learning_events) == 1
