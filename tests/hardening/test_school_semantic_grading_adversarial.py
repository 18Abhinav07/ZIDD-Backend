from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.content.school.content_schema import SchoolRubricEvaluation
from app.services.school import open_answer_ai
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    SchoolCriterionPolicy,
    SchoolOpenAnswerRetryableError,
    SchoolOpenEvaluationContext,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services.school.open_answer_prompt import build_school_open_answer_prompt


ANSWER = "Munni supported Gita by carrying the basket, so they worked as partners."
ACTIVITY = {
    "activity_id": "relationship:independent:1",
    "grading_mode": "strict_open_rubric",
    "certifying_language": "en",
    "skill_ids": ["reading.relationship", "writing.reason_answer"],
    "prompt": "How did Munni and Gita work together? Explain in your own words.",
    "passage": "Munni lifted one side of the basket while Gita lifted the other.",
    "response_mode": "paragraph",
    "preflight_rule": "relevant_english_response",
    "pass_score": 0.8,
    "rubric_criteria": [
        {
            "id": "relationship",
            "description": "Explains how the two characters worked together.",
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": "passage_reason",
            "description": "Uses a relevant action from the passage.",
            "required": True,
            "min_quality": 0.7,
        },
    ],
    "model_answer": "Munni and Gita cooperated by sharing the basket equally.",
}


def _payload(
    *,
    answer: str = ANSWER,
    language: str = "en",
    blockers: list[str] | None = None,
) -> dict:
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": ACTIVITY["activity_id"],
        "skill_ids": list(ACTIVITY["skill_ids"]),
        "score": 0.86,
        "confidence": 0.91,
        "language_detected": language,
        "criteria": [
            {
                "id": "relationship",
                "met": True,
                "quality": 0.85,
                "evidence_quote": answer.split(",", 1)[0],
            },
            {
                "id": "passage_reason",
                "met": True,
                "quality": 0.82,
                "evidence_quote": "carrying the basket"
                if "carrying the basket" in answer
                else answer,
            },
        ],
        "misconception_tags": [],
        "blockers": blockers or [],
        "needs_human_review": False,
        "feedback_to_learner": "You connected the shared action to the relationship.",
    }


def _context(
    answer: str = ANSWER,
    *,
    relevance_terms: tuple[str, ...] = ("Munni", "Gita", "basket"),
    source_texts: tuple[str, ...] = (),
    exemplar_texts: tuple[str, ...] = (),
    certifying_language: str | None = "en",
    semantic_claim_slots: tuple[dict, ...] = (),
    ordered_semantic_claim_slot_ids: tuple[str, ...] = (),
    actor_action_receiver_slot_ids: tuple[str, str, str] | None = None,
    forbidden_phrases: tuple[str, ...] = (),
) -> SchoolOpenEvaluationContext:
    return SchoolOpenEvaluationContext(
        expected_item_id=ACTIVITY["activity_id"],
        scored_skill_ids=tuple(ACTIVITY["skill_ids"]),
        criterion_policies=tuple(
            SchoolCriterionPolicy(
                id=criterion["id"],
                required=criterion["required"],
                min_quality=criterion["min_quality"],
            )
            for criterion in ACTIVITY["rubric_criteria"]
        ),
        pass_score=0.8,
        minimum_confidence=0.65,
        learner_answer=answer,
        human_review_policy="allow",
        relevance_terms=relevance_terms,
        source_texts=source_texts,
        exemplar_texts=exemplar_texts,
        certifying_language=certifying_language,
        semantic_claim_slots=semantic_claim_slots,
        ordered_semantic_claim_slot_ids=ordered_semantic_claim_slot_ids,
        actor_action_receiver_slot_ids=actor_action_receiver_slot_ids,
        forbidden_phrases=forbidden_phrases,
    )


def test_school_open_v1_accepts_valid_concise_paraphrase():
    validated = validate_school_open_evaluation(_payload(), context=_context())

    assert OPEN_RUBRIC_SCHEMA_VERSION == "school.open.v1"
    assert validated.certification_eligible is True
    assert validated.effective_blockers == ()


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        ({"schema_version": "school-v3-rubric-1"}, "unsupported_school_open_schema"),
        ({"item_id": "wrong"}, "rubric_item_id_mismatch"),
        ({"skill_ids": ["writing.invented"]}, "rubric_scored_skill_ids_mismatch"),
        (
            {
                "criteria": [
                    {
                        "id": "relationship",
                        "met": True,
                        "quality": 0.9,
                        "evidence_quote": "Munni supported Gita",
                    }
                ]
            },
            "rubric_criterion_ids_mismatch",
        ),
    ),
)
def test_school_open_v1_rejects_wrong_authority_and_missing_criteria(mutation, error):
    with pytest.raises(ValueError, match=error):
        validate_school_open_evaluation(
            {**_payload(), **mutation},
            context=_context(),
        )


def test_school_open_v1_rejects_extra_fields_and_ungrounded_quotes():
    with pytest.raises(ValidationError):
        validate_school_open_evaluation(
            {**_payload(), "mastered": True},
            context=_context(),
        )

    criterion_extra = _payload()
    criterion_extra["criteria"][0]["explanation"] = "model-owned prose"
    with pytest.raises(ValidationError):
        validate_school_open_evaluation(
            criterion_extra,
            context=_context(),
        )

    payload = _payload()
    payload["criteria"][0]["evidence_quote"] = "invented learner evidence"
    with pytest.raises(ValueError, match="rubric_evidence_quote_untraceable"):
        validate_school_open_evaluation(payload, context=_context())

    wrong_case = _payload()
    wrong_case["criteria"][0]["evidence_quote"] = "munni supported gita"
    with pytest.raises(ValueError, match="rubric_evidence_quote_untraceable"):
        validate_school_open_evaluation(wrong_case, context=_context())


def test_irrelevant_fluent_prose_is_not_certifying_evidence():
    answer = "Education is important and this is a beautifully written story with a good moral."
    payload = _payload(answer=answer)

    validated = validate_school_open_evaluation(payload, context=_context(answer))

    assert "answer_not_relevant" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_one_generic_relevance_word_cannot_certify_unrelated_prose():
    answer = (
        "Education matters because every learner should work hard and stay "
        "positive throughout the school year."
    )
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("because", "Munni", "basket"),
        ),
    )

    assert "answer_not_relevant" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_two_generic_relevance_phrases_cannot_certify_unrelated_prose():
    answer = (
        "I would paint the classroom because bright colours make everyone "
        "feel cheerful today."
    )
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("I would", "because", "spectacles"),
        ),
    )

    assert "answer_not_relevant" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_one_specific_relevance_anchor_allows_a_valid_creative_response():
    answer = "A pair of muddy shoes waited beside the front door."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("pair of", "location", "sentence"),
        ),
    )

    assert "answer_not_relevant" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_multiple_source_anchors_allow_a_valid_paraphrase_of_narrow_relevance_terms():
    passage = (
        "A card went missing. Ria retraced her route, found it near the atlas, "
        "and returned it."
    )
    answer = (
        "Ria traced her path, discovered the missing card by the atlas, and "
        "returned it."
    )
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("lost card", "searched her path", "gave it back"),
            source_texts=(passage,),
        ),
    )

    assert "answer_not_relevant" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_one_source_word_cannot_certify_unrelated_fluent_prose():
    passage = (
        "A card went missing. Ria retraced her route, found it near the atlas, "
        "and returned it."
    )
    answer = (
        "The card proves that education matters and every learner should stay "
        "positive throughout the year."
    )
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("lost card", "searched her path", "gave it back"),
            source_texts=(passage,),
        ),
    )

    assert "answer_not_relevant" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_relevance_terms_require_word_or_phrase_boundaries():
    answer = "The train arrived on time, and the learner described it clearly."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(answer, relevance_terms=("rain",)),
    )

    assert "answer_not_relevant" in validated.effective_blockers


def test_inflated_model_cannot_certify_an_authored_denial():
    answer = "Munni did not support Gita, although the basket is mentioned."
    payload = _payload(answer=answer)

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            forbidden_phrases=("did not support Gita",),
        ),
    )

    assert "authored_contradiction" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_inflated_model_cannot_certify_reversed_authored_roles():
    answer = "Gita helped Munni carry the basket."
    payload = _payload(answer=answer)

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            semantic_claim_slots=(
                {"id": "helper", "aliases": ("Munni",)},
                {"id": "action", "aliases": ("helped", "supported")},
                {"id": "receiver", "aliases": ("Gita",)},
            ),
            ordered_semantic_claim_slot_ids=("helper", "action", "receiver"),
            actor_action_receiver_slot_ids=("helper", "action", "receiver"),
        ),
    )

    assert "semantic_role_order_mismatch" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_inflated_model_cannot_certify_passive_role_reversal():
    answer = "Munni was helped by Gita while carrying the basket."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            semantic_claim_slots=(
                {"id": "helper", "aliases": ("Munni",)},
                {"id": "action", "aliases": ("helped", "supported")},
                {"id": "receiver", "aliases": ("Gita",)},
            ),
            ordered_semantic_claim_slot_ids=("helper", "action", "receiver"),
            actor_action_receiver_slot_ids=("helper", "action", "receiver"),
        ),
    )

    assert "semantic_passive_role_reversal" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_ordered_procedure_does_not_infer_actor_action_receiver_roles():
    answer = "First wash the bowl. Next place it by the window."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("bowl", "window"),
            semantic_claim_slots=(
                {"id": "wash", "aliases": ("wash",)},
                {"id": "place", "aliases": ("place",)},
                {"id": "window", "aliases": ("window",)},
            ),
            ordered_semantic_claim_slot_ids=("wash", "place", "window"),
        ),
    )

    assert "semantic_role_order_mismatch" not in validated.effective_blockers
    assert "semantic_passive_role_reversal" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_ordered_composite_slot_does_not_create_a_false_order_mismatch():
    answer = "They will refill it when it is empty."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=("refill", "empty"),
            semantic_claim_slots=(
                {"id": "expansion", "aliases": ("They will",)},
                {"id": "sentence", "aliases": (answer,)},
            ),
            ordered_semantic_claim_slot_ids=("expansion", "sentence"),
        ),
    )

    assert "semantic_role_order_mismatch" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_inflated_model_cannot_certify_missing_required_semantic_action():
    answer = "Munni and Gita are characters in this story with a basket."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            semantic_claim_slots=(
                {"id": "helper", "aliases": ("Munni",)},
                {"id": "action", "aliases": ("helped", "supported")},
                {"id": "receiver", "aliases": ("Gita",)},
            ),
            ordered_semantic_claim_slot_ids=("helper", "action", "receiver"),
            actor_action_receiver_slot_ids=("helper", "action", "receiver"),
        ),
    )

    assert "semantic_required_claim_missing" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_complete_evidence_can_satisfy_a_composite_semantic_claim():
    answer = "Munni carried the basket and reached the kitchen safely."
    payload = _payload(answer=answer)
    payload["criteria"][0].update(
        met=True,
        quality=0.9,
        evidence_quote=answer,
    )

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            relevance_terms=("Munni", "basket", "kitchen"),
            semantic_claim_slots=(
                {
                    "id": "relationship",
                    "description": "Uses both the helpful action and its result.",
                    "aliases": (
                        "carried the basket and reached the kitchen",
                    ),
                },
            ),
        ),
    )

    assert "semantic_required_claim_missing" not in validated.effective_blockers


def test_named_composite_connectors_accept_all_required_relations():
    answer = (
        "Sana regularly wears a helmet, but today she did not ride "
        "because the buckle broke."
    )
    payload = _payload(answer=answer)
    payload["criteria"][0].update(
        met=True,
        quality=1.0,
        evidence_quote="but today she did not ride because the buckle broke",
    )

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            relevance_terms=("Sana", "helmet", "buckle"),
            semantic_claim_slots=(
                {
                    "id": "relationship",
                    "description": "Uses but for contrast and because for cause.",
                    "aliases": (
                        "but she did not ride",
                        "because the buckle broke",
                    ),
                },
            ),
        ),
    )

    assert "semantic_required_claim_missing" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_named_composite_connectors_reject_one_missing_relation():
    answer = "Sana regularly wears a helmet, but today she did not ride."
    payload = _payload(answer=answer)
    payload["criteria"][0].update(
        met=True,
        quality=1.0,
        evidence_quote="but today she did not ride",
    )

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            relevance_terms=("Sana", "helmet"),
            semantic_claim_slots=(
                {
                    "id": "relationship",
                    "description": "Uses but for contrast and because for cause.",
                    "aliases": (
                        "but she did not ride",
                        "because the buckle broke",
                    ),
                },
            ),
        ),
    )

    assert "semantic_required_claim_missing" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_all_words_alias_variants_form_one_semantic_evidence_group():
    answer = "The wind spins the dry leaves."
    payload = _payload(answer=answer)
    payload["criteria"][0].update(
        met=True,
        quality=1.0,
        evidence_quote=answer,
    )

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            relevance_terms=("wind", "spins", "leaves"),
            semantic_claim_slots=(
                {
                    "id": "relationship",
                    "description": "Uses all words in sensible order.",
                    "aliases": (
                        "wind spins the dry leaves",
                        "that is, wind spins the dry leaves",
                    ),
                },
            ),
        ),
    )

    assert "semantic_required_claim_missing" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_punctuation_semantic_alias_matches_natural_sentence_ending():
    answer = "Where is the basket?"
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            relevance_terms=(),
            semantic_claim_slots=(
                {"id": "question_mark", "aliases": ("?",)},
            ),
        ),
    )

    assert "semantic_required_claim_missing" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_grounded_rubric_evidence_can_certify_a_valid_unlisted_paraphrase():
    answer = (
        "Ravi gave the heavy parcel to Mina, so she could carry it home safely."
    )
    context = SchoolOpenEvaluationContext(
        expected_item_id="paraphrase:independent:1",
        scored_skill_ids=("writing.reason_answer",),
        criterion_policies=(
            SchoolCriterionPolicy(id="help", required=True, min_quality=0.7),
            SchoolCriterionPolicy(id="result", required=True, min_quality=0.7),
        ),
        pass_score=0.8,
        minimum_confidence=0.65,
        learner_answer=answer,
        human_review_policy="allow",
        relevance_terms=("Ravi", "Mina", "parcel"),
        certifying_language="en",
        semantic_claim_slots=(
            {"id": "help", "aliases": ("shared the weight",)},
            {"id": "result", "aliases": ("reached home with it",)},
        ),
    )
    payload = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": "paraphrase:independent:1",
        "skill_ids": ["writing.reason_answer"],
        "score": 0.9,
        "confidence": 0.92,
        "language_detected": "en",
        "criteria": [
            {
                "id": "help",
                "met": True,
                "quality": 0.9,
                "evidence_quote": "Ravi gave the heavy parcel to Mina",
            },
            {
                "id": "result",
                "met": True,
                "quality": 0.86,
                "evidence_quote": "she could carry it home safely",
            },
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "You explained the helpful action and its result.",
    }

    validated = validate_school_open_evaluation(payload, context=context)

    assert "semantic_required_claim_missing" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_one_grounded_quote_cannot_certify_two_distinct_semantic_claims():
    answer = "Ravi gave the heavy parcel to Mina before he left."
    shared_quote = "Ravi gave the heavy parcel to Mina"
    context = SchoolOpenEvaluationContext(
        expected_item_id="paraphrase:independent:2",
        scored_skill_ids=("writing.reason_answer",),
        criterion_policies=(
            SchoolCriterionPolicy(id="help", required=True, min_quality=0.7),
            SchoolCriterionPolicy(id="result", required=True, min_quality=0.7),
        ),
        pass_score=0.8,
        minimum_confidence=0.65,
        learner_answer=answer,
        human_review_policy="allow",
        relevance_terms=("Ravi", "Mina", "parcel"),
        certifying_language="en",
        semantic_claim_slots=(
            {"id": "help", "aliases": ("shared the weight",)},
            {"id": "result", "aliases": ("reached home with it",)},
        ),
    )
    payload = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": "paraphrase:independent:2",
        "skill_ids": ["writing.reason_answer"],
        "score": 0.9,
        "confidence": 0.92,
        "language_detected": "en",
        "criteria": [
            {
                "id": "help",
                "met": True,
                "quality": 0.9,
                "evidence_quote": shared_quote,
            },
            {
                "id": "result",
                "met": True,
                "quality": 0.9,
                "evidence_quote": shared_quote,
            },
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The response needs a distinct result.",
    }

    validated = validate_school_open_evaluation(payload, context=context)

    assert "semantic_evidence_span_reused" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_one_grounded_sentence_can_prove_claims_from_the_same_authored_component():
    answer = "Silver means the lake reflected the weak light at dawn."
    shared_quote = "Silver means the lake reflected the weak light at dawn"
    context = SchoolOpenEvaluationContext(
        expected_item_id="colours:independent:1",
        scored_skill_ids=("reading.word_meaning_context",),
        criterion_policies=(
            SchoolCriterionPolicy(id="meaning", required=True, min_quality=0.7),
            SchoolCriterionPolicy(id="clue", required=True, min_quality=0.7),
        ),
        pass_score=0.8,
        minimum_confidence=0.65,
        learner_answer=answer,
        human_review_policy="allow",
        relevance_terms=("silver", "lake", "reflected", "light"),
        source_texts=(
            "At dawn, the lake looked silver because it reflected the first weak light.",
        ),
        certifying_language="en",
        semantic_claim_slots=(
            {
                "id": "meaning",
                "description": (
                    "Explains the target colour expression from a specific nearby clue. "
                    "Required part 1."
                ),
                "aliases": ("softly shining",),
            },
            {
                "id": "clue",
                "description": (
                    "Explains the target colour expression from a specific nearby clue. "
                    "Required part 2."
                ),
                "aliases": ("reflected first light",),
            },
        ),
    )
    payload = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": "colours:independent:1",
        "skill_ids": ["reading.word_meaning_context"],
        "score": 0.95,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": "meaning",
                "met": True,
                "quality": 1.0,
                "evidence_quote": shared_quote,
            },
            {
                "id": "clue",
                "met": True,
                "quality": 0.9,
                "evidence_quote": shared_quote,
            },
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "You explained the expression from its nearby clue.",
    }

    validated = validate_school_open_evaluation(payload, context=context)

    assert "semantic_evidence_span_reused" not in validated.effective_blockers
    assert validated.certification_eligible is True


def test_inflated_model_cannot_certify_participial_passive_role_reversal():
    answer = "Munni, helped by Gita, carried the basket home."
    validated = validate_school_open_evaluation(
        _payload(answer=answer),
        context=_context(
            answer,
            semantic_claim_slots=(
                {"id": "helper", "aliases": ("Munni",)},
                {"id": "action", "aliases": ("helped", "supported")},
                {"id": "receiver", "aliases": ("Gita",)},
            ),
            ordered_semantic_claim_slot_ids=("helper", "action", "receiver"),
            actor_action_receiver_slot_ids=("helper", "action", "receiver"),
        ),
    )

    assert "semantic_passive_role_reversal" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_semantic_claim_aliases_reject_empty_or_duplicate_authority():
    with pytest.raises(ValidationError, match="school_open_semantic_claim_alias_invalid"):
        _context(
            semantic_claim_slots=(
                {"id": "helper", "aliases": ("Munni", "Munni")},
            ),
            ordered_semantic_claim_slot_ids=("helper",),
        )

    with pytest.raises(ValidationError, match="school_open_semantic_claim_alias_invalid"):
        _context(
            semantic_claim_slots=(
                {"id": "helper", "aliases": (" ",)},
            ),
            ordered_semantic_claim_slot_ids=("helper",),
        )


def test_inflated_model_cannot_certify_repeated_keyword_gaming():
    answer = "Munni Gita basket Munni Gita basket Munni Gita basket."
    payload = _payload(answer=answer)

    validated = validate_school_open_evaluation(payload, context=_context(answer))

    assert "repeated_keyword_gaming" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_ordinary_repeated_function_words_do_not_look_like_keyword_gaming():
    answer = (
        "The parrot crossed the river, and the parrot warned the birds that "
        "the trader was near, so the birds moved away from the danger."
    )
    payload = _payload(answer=answer)

    validated = validate_school_open_evaluation(
        payload,
        context=_context(answer, relevance_terms=("parrot", "birds")),
    )

    assert "repeated_keyword_gaming" not in validated.effective_blockers


def test_unconfigured_lexical_relevance_does_not_reject_a_valid_paraphrase():
    activity = {
        **ACTIVITY,
        "prompt": "Why did Mina carry an umbrella?",
        "passage": "Mina carried an umbrella although the sky was bright.",
    }
    answer = "She expected wet weather."
    context = school_open_context_from_activity(activity, answer)
    payload = {
        **_payload(answer=answer),
        "criteria": [
            {
                "id": "relationship",
                "met": True,
                "quality": 0.85,
                "evidence_quote": answer,
            },
            {
                "id": "passage_reason",
                "met": True,
                "quality": 0.82,
                "evidence_quote": answer,
            },
        ],
    }

    validated = validate_school_open_evaluation(payload, context=context)

    assert context.relevance_terms == ()
    assert "answer_not_relevant" not in validated.effective_blockers


def test_authored_order_can_cover_a_subset_of_semantic_claims():
    context = _context(
        semantic_claim_slots=(
            {"id": "helper", "aliases": ("Munni",)},
            {"id": "action", "aliases": ("helped",)},
            {"id": "receiver", "aliases": ("Gita",)},
        ),
        ordered_semantic_claim_slot_ids=("helper", "receiver"),
    )

    assert context.ordered_semantic_claim_slot_ids == ("helper", "receiver")


def test_copied_exemplar_is_a_best_effort_backend_blocker():
    answer = ACTIVITY["model_answer"]
    payload = _payload(answer=answer)
    context = _context(
        answer,
        relevance_terms=("Munni", "Gita", "basket"),
        exemplar_texts=(ACTIVITY["model_answer"],),
    )

    validated = validate_school_open_evaluation(payload, context=context)

    assert "copied_exemplar" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_hindi_only_answer_cannot_certify_an_english_item():
    answer = (
        "मुन्नी और गीता ने मिलकर "
        "टोकरी उठाई "
        "इसलिए वे साथी थीं।"
    )
    payload = _payload(answer=answer, language="hi")

    validated = validate_school_open_evaluation(
        payload,
        context=_context(
            answer,
            relevance_terms=(),
            certifying_language="en",
        ),
    )

    assert "language_mismatch" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_strict_prompt_names_exact_schema_and_never_includes_model_answer():
    prompt = build_school_open_answer_prompt(
        item_id=ACTIVITY["activity_id"],
        skill_ids=ACTIVITY["skill_ids"],
        task_prompt=ACTIVITY["prompt"],
        passage=ACTIVITY["passage"],
        learner_answer=ANSWER,
        rubric_criteria=ACTIVITY["rubric_criteria"],
        schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
    )

    assert "school.open.v1" in prompt
    assert "SchoolOpenRubricEvaluation" in prompt
    assert ACTIVITY["model_answer"] not in prompt
    assert "answer mentions a fact and then denies it" in prompt
    assert "irrelevant fluent prose" in prompt
    assert "When met is false, quality must be 0.0" in prompt


def test_wire_schema_rejects_unknown_version_and_unmet_positive_quality():
    with pytest.raises(ValidationError):
        SchoolRubricEvaluation.model_validate(
            {**_payload(), "schema_version": "school.open.future"}
        )

    invalid = _payload()
    invalid["criteria"][0].update({"met": False, "quality": 0.4})
    with pytest.raises(ValidationError, match="rubric_unmet_criterion_has_quality"):
        SchoolRubricEvaluation.model_validate(invalid)


@pytest.mark.asyncio
async def test_typed_provider_schema_failure_is_retryable_and_returns_no_evidence(
    monkeypatch,
    caplog,
):
    evaluation = SchoolRubricEvaluation.model_validate(_payload())

    async def fake_provider(*args, **kwargs):
        return evaluation

    def reject_contract(*args, **kwargs):
        raise ValueError(f"private learner-derived feedback: {ANSWER}")

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_provider)
    monkeypatch.setattr(
        open_answer_ai,
        "validate_school_open_evaluation",
        reject_contract,
    )

    with pytest.raises(SchoolOpenAnswerRetryableError) as raised:
        await open_answer_ai.evaluate_school_open_answer(ACTIVITY, ANSWER)

    assert raised.value.retryable is True
    assert raised.value.code == "school_open_schema_failure"
    assert raised.value.evidence is None
    assert "private learner-derived feedback" not in caplog.text
    assert ANSWER not in caplog.text


@pytest.mark.asyncio
async def test_typed_provider_failure_is_retryable_and_returns_no_evidence(monkeypatch):
    async def failed_provider(*args, **kwargs):
        raise TimeoutError("local model unavailable")

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", failed_provider)

    with pytest.raises(SchoolOpenAnswerRetryableError) as raised:
        await open_answer_ai.evaluate_school_open_answer(ACTIVITY, ANSWER)

    assert raised.value.retryable is True
    assert raised.value.code == "school_open_provider_failure"
    assert raised.value.evidence is None


@pytest.mark.asyncio
async def test_typed_provider_returns_only_context_validated_evaluation(monkeypatch):
    evaluation = SchoolRubricEvaluation.model_validate(_payload())
    captured = []

    async def fake_provider(prompt, schema, *, timeout):
        captured.append((prompt, schema, timeout))
        return evaluation

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_provider)

    result = await open_answer_ai.evaluate_school_open_answer(ACTIVITY, ANSWER)

    assert result == evaluation
    assert len(captured) == 1
    assert captured[0][2] is None
    assert ACTIVITY["model_answer"] not in captured[0][0]


@pytest.mark.asyncio
async def test_school_open_answer_uses_provider_boundary_without_key_leak(monkeypatch):
    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    captured: list[tuple[str, str, type]] = []

    async def fake_structured(operation, prompt, schema):
        captured.append((operation, prompt, schema))
        return schema.model_validate(_payload())

    monkeypatch.setattr(open_answer_ai, "structured_generate", fake_structured)

    result = await open_answer_ai.evaluate_school_open_answer(ACTIVITY, ANSWER)

    assert result.item_id == ACTIVITY["activity_id"]
    assert captured[0][0] == "school_open_answer"
    assert ACTIVITY["model_answer"] not in captured[0][1]
