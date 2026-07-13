import pytest
from pydantic import ValidationError

from app.content.school_v3_schema import SchoolV3AssessmentItem
from app.services.school_v3_evaluator import (
    SchoolV3RubricEvaluation,
    criterion_scores,
    grade_deterministic_item,
    parse_school_v3_rubric_json,
    to_attempt_evidence,
)


VALID_RUBRIC_PAYLOAD = {
    "schema_version": "school-v3-rubric-1",
    "item_id": "chapter_reason_1",
    "skill_ids": ["writing.reason_answer"],
    "score": 0.86,
    "confidence": 0.92,
    "language_detected": "en",
    "criteria": [
        {
            "id": "answers_question",
            "met": True,
            "quality": 0.90,
            "evidence_quote": "because everyone helped",
        },
        {
            "id": "uses_reason_marker",
            "met": True,
            "quality": 0.82,
            "evidence_quote": "because",
        },
    ],
    "misconception_tags": [],
    "blockers": [],
    "needs_human_review": False,
    "feedback_to_learner": "Good reason. Keep naming the clue.",
}


def test_rubric_schema_accepts_strict_school_v3_fields():
    evaluation = SchoolV3RubricEvaluation.model_validate(VALID_RUBRIC_PAYLOAD)

    assert evaluation.schema_version == "school-v3-rubric-1"
    assert evaluation.item_id == "chapter_reason_1"
    assert criterion_scores(evaluation) == {
        "answers_question": 0.90,
        "uses_reason_marker": 0.82,
    }


def test_rubric_schema_rejects_extra_model_owned_decisions():
    payload = {**VALID_RUBRIC_PAYLOAD, "mastered": True}

    with pytest.raises(ValidationError):
        SchoolV3RubricEvaluation.model_validate(payload)


def test_parse_school_v3_rubric_json_rejects_invalid_json():
    with pytest.raises(ValueError, match="invalid_school_v3_rubric_json"):
        parse_school_v3_rubric_json("not json")


def test_deterministic_grader_scores_answer_key_items_without_model_calls():
    item = SchoolV3AssessmentItem(
        item_id="bridge_vocab_1",
        stage="bridge",
        item_type="multiple_choice",
        prompt="Gentle means __.",
        skill_ids=["reading.word_meaning_context"],
        answer_key="kind",
        options=["kind", "loud", "late"],
    )

    correct = grade_deterministic_item(item, "  Kind ")
    incorrect = grade_deterministic_item(item, "loud")

    assert correct.score == 1.0
    assert correct.confidence == 1.0
    assert correct.criteria[0].id == "answer_key_match"
    assert correct.criteria[0].met is True
    assert incorrect.score == 0.0
    assert incorrect.criteria[0].met is False


def test_to_attempt_evidence_preserves_open_answer_evidence_for_readiness_layer():
    evaluation = SchoolV3RubricEvaluation.model_validate(
        {
            **VALID_RUBRIC_PAYLOAD,
            "blockers": ["copied_exemplar"],
            "needs_human_review": True,
            "language_detected": "hi",
        }
    )

    evidence = to_attempt_evidence(
        evaluation,
        attempt_type="chapter_check",
        support_level="independent",
        language_required="en",
    )

    assert evidence.skill_ids == ("writing.reason_answer",)
    assert evidence.evaluator_score == 0.86
    assert evidence.evaluator_confidence == 0.92
    assert evidence.attempt_type == "chapter_check"
    assert evidence.language_detected == "hi"
    assert evidence.language_required == "en"
    assert evidence.blockers == ("copied_exemplar", "needs_human_review")
