import pytest
from pydantic import ValidationError

from app.services.school_v2_evaluator import (
    SchoolOpenAnswerEvaluation,
    criterion_scores,
    parse_open_answer_evaluation,
    to_attempt_evidence,
)


VALID_OPEN_ANSWER_PAYLOAD = {
    "skill_ids": ["eng.c5.inference.reason"],
    "score": 0.84,
    "confidence": 0.91,
    "language_detected": "en",
    "criteria": [
        {
            "criterion_id": "answers_question",
            "passed": True,
            "score": 0.90,
            "evidence_quote": "The learner gives a clear reason.",
        },
        {
            "criterion_id": "uses_text_evidence",
            "passed": False,
            "score": 0.55,
            "evidence_quote": "No specific event is named.",
        },
    ],
    "misconception_tags": ["missing_text_evidence"],
    "blockers": [],
    "feedback_to_learner": "Good reason. Next, add one event from the story.",
}


def test_open_answer_evaluation_accepts_strict_evidence_schema():
    evaluation = SchoolOpenAnswerEvaluation.model_validate(VALID_OPEN_ANSWER_PAYLOAD)

    assert evaluation.skill_ids == ["eng.c5.inference.reason"]
    assert evaluation.score == 0.84
    assert criterion_scores(evaluation) == {
        "answers_question": 0.90,
        "uses_text_evidence": 0.55,
    }


def test_open_answer_evaluation_rejects_model_advancement_claims():
    payload = {**VALID_OPEN_ANSWER_PAYLOAD, "mastered": True}

    with pytest.raises(ValidationError):
        SchoolOpenAnswerEvaluation.model_validate(payload)


def test_open_answer_evaluation_requires_criterion_evidence_quote():
    payload = {
        **VALID_OPEN_ANSWER_PAYLOAD,
        "criteria": [
            {
                "criterion_id": "answers_question",
                "passed": True,
                "score": 0.90,
            }
        ],
    }

    with pytest.raises(ValidationError):
        SchoolOpenAnswerEvaluation.model_validate(payload)


def test_parse_open_answer_evaluation_rejects_invalid_json():
    with pytest.raises(ValueError, match="invalid_open_answer_json"):
        parse_open_answer_evaluation("not json")


def test_to_attempt_evidence_preserves_evaluator_evidence_without_certifying_decision():
    evaluation = SchoolOpenAnswerEvaluation.model_validate(
        {
            **VALID_OPEN_ANSWER_PAYLOAD,
            "blockers": ["copied_exemplar"],
            "language_detected": "hi",
        }
    )

    evidence = to_attempt_evidence(
        evaluation,
        attempt_type="independent_check",
        support_level="independent",
        language_required="en",
    )

    assert evidence.skill_ids == ("eng.c5.inference.reason",)
    assert evidence.evaluator_score == 0.84
    assert evidence.evaluator_confidence == 0.91
    assert evidence.blockers == ("copied_exemplar",)
    assert evidence.language_detected == "hi"
    assert evidence.language_required == "en"
