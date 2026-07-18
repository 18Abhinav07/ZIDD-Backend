from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.content.school_rebuild_schema import (
    LiveChapterActivity,
    LiveChapterAssessmentItem,
)
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    grade_typed_school_answer,
    school_open_context_from_activity,
)
from app.services import school_rebuild_curriculum as curriculum


def _activity(**overrides) -> LiveChapterActivity:
    payload = {
        "teaching_block": "Try this independently.",
        "passage": "Munni helped Gita carry the basket.",
        "prompt": "Who helped whom?",
        "options": [],
        "accepted_answers": ["Munni helped Gita"],
    }
    payload.update(overrides)
    return LiveChapterActivity(**payload)


def _open_authority() -> dict:
    return {
        "relevance_terms": ["Munni", "Gita", "basket"],
        "forbidden_phrases": ["Munni did not help Gita"],
        "model_answer": "Munni helped Gita by sharing the basket's weight.",
    }


def _ordered_activity() -> LiveChapterActivity:
    return _activity(
        grading_mode="ordered_slots",
        accepted_answers=[],
        concept_slots=[
            {
                "id": "helper",
                "description": "Names Munni as the helper.",
                "any_of": ["Munni"],
            },
            {
                "id": "help_action",
                "description": "States that help was given.",
                "any_of": ["helped", "gave help to"],
            },
            {
                "id": "receiver",
                "description": "Names Gita as the person helped.",
                "any_of": ["Gita"],
            },
        ],
        ordered_concept_slot_ids=["helper", "help_action", "receiver"],
    )


def test_legacy_activity_without_grading_mode_remains_valid():
    activity = _activity()

    assert activity.grading_mode is None
    assert "grading_mode" not in activity.runtime_dict()


@pytest.mark.parametrize(
    ("symbol", "wrong"),
    (
        ("?", "."),
        (".", "!"),
        ("!", "?"),
        (",", "."),
        ('"', "'"),
        ("“”", '"'),
    ),
)
def test_punctuation_symbol_preserves_and_grades_authored_marks(symbol, wrong):
    activity = _activity(
        grading_mode="punctuation_symbol",
        prompt="Choose the missing punctuation mark.",
        accepted_answers=[symbol],
    )

    correct = grade_typed_school_answer(activity.runtime_dict(), symbol)
    incorrect = grade_typed_school_answer(activity.runtime_dict(), wrong)

    assert correct.correct is True
    assert correct.score == 1.0
    assert correct.evidence_quote == symbol
    assert incorrect.correct is False
    assert incorrect.score == 0.0


def test_selected_option_requires_an_authored_option_not_keyword_presence():
    activity = _activity(
        grading_mode="selected_option",
        prompt="Choose the best answer.",
        options=["Munni", "Gita", "Nobody"],
        accepted_answers=["Munni"],
    )

    assert grade_typed_school_answer(activity.runtime_dict(), "  munni ").correct
    assert not grade_typed_school_answer(
        activity.runtime_dict(),
        "The answer mentions Munni but I choose Gita.",
    ).correct


def test_exact_text_is_limited_to_short_enumerated_facts():
    fact = _activity(
        grading_mode="exact_text",
        prompt="Name the helper.",
        accepted_answers=["Munni", "Munni Devi"],
    )
    assert grade_typed_school_answer(fact.runtime_dict(), "munni devi").correct

    with pytest.raises(ValidationError, match="exact_text_requires_short_facts"):
        _activity(
            grading_mode="exact_text",
            accepted_answers=[
                "Munni helped Gita because she understood that sharing work "
                "would make the difficult journey easier for everyone."
            ],
        )


def test_ordered_slots_accepts_a_concise_role_correct_paraphrase():
    result = grade_typed_school_answer(
        _ordered_activity().runtime_dict(),
        "Munni gave help to Gita.",
    )

    assert result.correct is True
    assert result.score == 1.0
    assert result.missing_criteria == ()


@pytest.mark.parametrize(
    ("answer", "blocker"),
    (
        ("Gita helped Munni.", "ordered_slot_sequence_invalid"),
        ("Munni did not help Gita.", "negated_slot_evidence"),
        ("Munni gave no help to Gita.", "negated_slot_evidence"),
        (
            "Munni helped Gita, but Munni did not actually help Gita.",
            "contradictory_response",
        ),
        (
            "Munni Gita helped Munni Gita helped.",
            "ambiguous_repeated_slot_evidence",
        ),
    ),
)
def test_ordered_slots_rejects_role_reversal_negation_and_keyword_gaming(
    answer,
    blocker,
):
    result = grade_typed_school_answer(_ordered_activity().runtime_dict(), answer)

    assert result.correct is False
    assert blocker in result.blockers


def test_ordered_slots_requires_every_authored_role_in_one_declared_order():
    with pytest.raises(ValidationError, match="ordered_slots_require_all_slot_ids"):
        _activity(
            grading_mode="ordered_slots",
            accepted_answers=[],
            concept_slots=[
                {
                    "id": "helper",
                    "description": "Names the helper.",
                    "any_of": ["Munni"],
                },
                {
                    "id": "action",
                    "description": "Names the action.",
                    "any_of": ["helped"],
                },
                {
                    "id": "receiver",
                    "description": "Names the receiver.",
                    "any_of": ["Gita"],
                },
            ],
            ordered_concept_slot_ids=["helper", "action"],
        )


@pytest.mark.parametrize(
    "semantic_skill",
    (
        "reading.inference_reason",
        "writing.reason_answer",
        "writing.summary_own_words",
        "reading.relationship",
        "reading.comparison",
    ),
)
def test_new_semantic_assessment_items_require_strict_open_rubric(semantic_skill):
    common = {
        "item_id": "semantic-1",
        "passage": "Munni shared the work with Gita.",
        "prompt": "Explain the relationship in your own words.",
        "skill_ids": [semantic_skill],
        "options": [],
        "accepted_answers": ["friends"],
        "response_mode": "paragraph",
    }

    with pytest.raises(ValidationError, match="semantic_activity_requires_strict_open"):
        LiveChapterAssessmentItem(**common, grading_mode="exact_text")

    role_authority = {}
    if semantic_skill == "reading.relationship":
        role_authority = {
            "concept_slots": [
                {
                    "id": "helper",
                    "description": "Names Munni as the helper.",
                    "any_of": ["Munni"],
                },
                {
                    "id": "help_action",
                    "description": "States that help was given.",
                    "any_of": ["helped", "supported"],
                },
                {
                    "id": "receiver",
                    "description": "Names Gita as the person helped.",
                    "any_of": ["Gita"],
                },
            ],
            "ordered_concept_slot_ids": [
                "helper",
                "help_action",
                "receiver",
            ],
        }
    item = LiveChapterAssessmentItem(
        **{**common, "accepted_answers": []},
        **_open_authority(),
        **role_authority,
        grading_mode="strict_open_rubric",
        certifying_language="en",
        preflight_rule="relevant_english_response",
        pass_score=0.8,
        rubric_criteria=[
            {
                "id": "explains_relationship",
                "description": "Explains the relationship using passage evidence.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
    )

    assert item.grading_mode == "strict_open_rubric"
    assert item.evaluation_mode == "llm_rubric"


def test_relationship_open_item_requires_authored_role_order():
    with pytest.raises(
        ValidationError,
        match="role_sensitive_open_requires_ordered_slots",
    ):
        LiveChapterAssessmentItem(
            item_id="relationship-without-roles",
            passage="Munni shared the basket with Gita.",
            prompt="Explain the relationship in your own words.",
            skill_ids=["reading.relationship"],
            options=[],
            accepted_answers=[],
            grading_mode="strict_open_rubric",
            certifying_language="en",
            response_mode="paragraph",
            preflight_rule="relevant_english_response",
            pass_score=0.8,
            rubric_criteria=[
                {
                    "id": "explains_relationship",
                    "description": "Explains who helped whom.",
                    "required": True,
                    "min_quality": 0.7,
                }
            ],
            **_open_authority(),
        )


def test_new_semantic_lesson_activity_requires_strict_open_rubric():
    typed_metadata = {
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": "independent_application",
        "interaction_type": "paragraph_text",
        "evidence_role": "certifying",
        "certifying_language": "en",
        "source_anchor_ids": ["official-page-1"],
        "knowledge_components": ["writing.reason_answer"],
    }
    with pytest.raises(ValidationError, match="semantic_activity_requires_strict_open"):
        _activity(
            **typed_metadata,
            grading_mode="exact_text",
            accepted_answers=["They shared the work"],
        )

    with pytest.raises(ValidationError, match="typed_activity_requires_grading_mode"):
        _activity(
            **typed_metadata,
            accepted_answers=["They shared the work"],
        )

    activity = _activity(
        **typed_metadata,
        **_open_authority(),
        grading_mode="strict_open_rubric",
        accepted_answers=[],
        response_mode="paragraph",
        preflight_rule="relevant_english_response",
        pass_score=0.8,
        rubric_criteria=[
            {
                "id": "uses_reason",
                "description": "Explains why sharing the work helped.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
    )

    assert activity.grading_mode == "strict_open_rubric"
    assert activity.evaluation_mode == "llm_rubric"


@pytest.mark.parametrize(
    "missing_field",
    ("relevance_terms", "forbidden_phrases", "model_answer"),
)
def test_strict_open_activity_requires_authored_semantic_authority(missing_field):
    authority = _open_authority()
    authority.pop(missing_field)

    with pytest.raises(
        ValidationError,
        match="strict_open_requires_semantic_authority",
    ):
        _activity(
            **authority,
            grading_mode="strict_open_rubric",
            accepted_answers=[],
            response_mode="paragraph",
            preflight_rule="relevant_english_response",
            pass_score=0.8,
            rubric_criteria=[
                {
                    "id": "uses_reason",
                    "description": "Explains why sharing the work helped.",
                    "required": True,
                    "min_quality": 0.7,
                }
            ],
        )


@pytest.mark.parametrize(
    "missing_field",
    ("relevance_terms", "forbidden_phrases", "model_answer"),
)
def test_strict_open_assessment_requires_authored_semantic_authority(
    missing_field,
):
    authority = _open_authority()
    authority.pop(missing_field)

    with pytest.raises(
        ValidationError,
        match="strict_open_requires_semantic_authority",
    ):
        LiveChapterAssessmentItem(
            item_id="semantic-authority-1",
            passage="Munni shared the basket with Gita.",
            prompt="Explain how Munni helped Gita.",
            skill_ids=["writing.reason_answer"],
            options=[],
            accepted_answers=[],
            grading_mode="strict_open_rubric",
            certifying_language="en",
            response_mode="paragraph",
            preflight_rule="relevant_english_response",
            pass_score=0.8,
            rubric_criteria=[
                {
                    "id": "uses_reason",
                    "description": "Explains why sharing the basket helped.",
                    "required": True,
                    "min_quality": 0.7,
                }
            ],
            **authority,
        )


def test_strict_open_assessment_runtime_carries_hidden_semantic_authority():
    item = LiveChapterAssessmentItem(
        item_id="semantic-authority-2",
        passage="Munni shared the basket with Gita.",
        prompt="Explain how Munni helped Gita.",
        skill_ids=["writing.reason_answer"],
        options=[],
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        certifying_language="en",
        response_mode="paragraph",
        preflight_rule="relevant_english_response",
        pass_score=0.8,
        rubric_criteria=[
            {
                "id": "uses_reason",
                "description": "Explains why sharing the basket helped.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
        **_open_authority(),
    )

    runtime = item.runtime_dict()
    assert runtime["relevance_terms"] == ["Munni", "Gita", "basket"]
    assert runtime["model_answer"].startswith("Munni helped")

    context = school_open_context_from_activity(
        {**runtime, "activity_id": "chapter_check:1:semantic-authority-2"},
        runtime["model_answer"],
    )
    assert context.relevance_terms == ("Munni", "Gita", "basket")
    assert context.exemplar_texts == ()

    exposed_context = school_open_context_from_activity(
        {
            **runtime,
            "activity_id": "guided:1:semantic-authority-2",
            "exemplar_texts": [runtime["model_answer"]],
        },
        runtime["model_answer"],
    )
    assert exposed_context.exemplar_texts == (runtime["model_answer"],)


def test_public_activity_never_leaks_semantic_authority():
    public = curriculum._public_activity(
        {
            "activity_id": "reason:independent:1",
            "level_id": "reason",
            "kind": "independent_check",
            "title": "Explain your reason",
            "focus": "reasoning",
            "skill_ids": ["writing.reason_answer"],
            "teaching_block": "Answer independently.",
            "passage": "Munni shared the basket with Gita.",
            "prompt": "Explain why this helped.",
            "options": [],
            "response_mode": "paragraph",
            "model_answer": _open_authority()["model_answer"],
            "relevance_terms": _open_authority()["relevance_terms"],
            "forbidden_phrases": _open_authority()["forbidden_phrases"],
            "rubric_criteria": [{"id": "uses_reason"}],
            "accepted_answers": [],
        }
    )

    assert public is not None
    for hidden_field in (
        "model_answer",
        "relevance_terms",
        "forbidden_phrases",
        "rubric_criteria",
        "accepted_answers",
    ):
        assert hidden_field not in public


def test_open_answer_preflight_uses_the_closed_unknown_language_code():
    failure = curriculum._open_answer_preflight_failure(
        {
            "rubric_criteria": [
                {"id": "uses_reason", "required": True},
            ]
        }
    )

    assert failure["language_detected"] == "unknown"


def test_open_answer_preflight_enforces_authored_min_response_words():
    activity = {
        "preflight_rule": "relevant_english_response",
        "min_response_words": 6,
    }

    assert curriculum._open_answer_preflight(
        activity,
        "Munni helped Gita.",
    ) is False
    assert curriculum._open_answer_preflight(
        activity,
        "Munni helped Gita because her basket was heavy.",
    ) is True


def test_runtime_typed_grader_revalidates_authoring_authority():
    with pytest.raises(ValueError, match="selected_option_requires_authored_options"):
        grade_typed_school_answer(
            {
                "grading_mode": "selected_option",
                "options": ["Munni", "Gita"],
                "accepted_answers": ["Nobody"],
            },
            "Nobody",
        )

    with pytest.raises(ValueError, match="semantic_activity_requires_strict_open"):
        grade_typed_school_answer(
            {
                "grading_mode": "exact_text",
                "options": [],
                "accepted_answers": ["friends"],
                "skill_ids": ["reading.relationship"],
            },
            "friends",
        )


def test_production_curriculum_uses_typed_deterministic_grader():
    evaluation = curriculum.evaluate_deterministic_answer(
        {
            "grading_mode": "selected_option",
            "options": ["Munni", "Gita"],
            "accepted_answers": ["Munni"],
        },
        "I mention Munni, but I choose Gita.",
    )

    assert evaluation["correct"] is False
    assert evaluation["score"] == 0.0


def test_production_curriculum_activity_preserves_authored_grading_authority():
    state = {
        "status": "active",
        "phase": "learning",
        "current_level_index": 0,
        "preferred_teaching_language": "en",
        "levels": [
            {
                "level_id": "relationship-level",
                "title": "Who helped whom?",
                "focus": "Track the helper and receiver.",
                "skill_ids": ["reading.relationship"],
                "status": "in_progress",
                "current_step": "independent_check",
                "attempts": [],
                "checks": {
                    "independent_check": {
                        "teaching_block": "Read the roles carefully.",
                        "passage": "Munni helped Gita.",
                        "prompt": "Who helped whom?",
                        "options": ["Munni helped Gita", "Gita helped Munni"],
                        "accepted_answers": ["Munni helped Gita"],
                        "grading_mode": "selected_option",
                    }
                },
            }
        ],
    }

    activity = curriculum._current_activity(state)

    assert activity is not None
    assert activity["grading_mode"] == "selected_option"


def test_production_curriculum_revalidates_strict_open_backend_blockers():
    activity = {
        "activity_id": "relationship:independent:1",
        "grading_mode": "strict_open_rubric",
        "evaluation_mode": "llm_rubric",
        "skill_ids": ["reading.relationship"],
        "prompt": "How did Munni help Gita?",
        "passage": "Munni lifted one side of Gita's basket.",
        "pass_score": 0.8,
        "certifying_language": "en",
        "forbidden_phrases": ["did not help Gita"],
        "rubric_criteria": [
            {
                "id": "relationship",
                "description": "Explains the helpful relationship.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
    }
    answer = "Munni did not help Gita, though the basket is mentioned."
    raw = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.95,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": "relationship",
                "met": True,
                "quality": 0.95,
                "evidence_quote": "Munni did not help Gita",
            }
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "You named both characters.",
    }

    evaluation = curriculum.decide_open_answer_evaluation(
        activity,
        raw,
        answer=answer,
    )

    assert evaluation["correct"] is False
    assert "authored_contradiction" in evaluation["blockers"]
