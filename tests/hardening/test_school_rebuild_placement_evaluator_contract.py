import pytest

from app.content.school_rebuild_placement_bank import placement_bank_for
from app.content.school_rebuild_placement_validation import (
    STRICT_RUBRIC_CRITERIA_BY_REF,
)
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    SchoolOpenAnswerRetryableError,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services.school_rebuild_placement_evaluator import (
    EVALUATOR_UNAVAILABLE_CODE,
    SchoolPlacementEvaluatorUnavailableError,
    build_placement_evaluator_activity,
    evaluate_school_placement_item,
    grade_deterministic_placement_item,
)


def _item(mode: str):
    return next(
        item
        for item in placement_bank_for("english", 3)
        if item.evaluation_mode == mode
    )


def _class_five_item(*, passage_starts_with: str):
    return next(
        item
        for item in placement_bank_for("english", 5)
        if item.passage.startswith(passage_starts_with)
    )


def _provider_payload(item, *, language="en", missing_id=None, human_review=False):
    criterion_ids = STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref]
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": item.item_id,
        "skill_ids": [item.primary_skill_id],
        "score": 1.0,
        "confidence": 0.96,
        "language_detected": language,
        "criteria": [
            {
                "id": criterion_id,
                "met": criterion_id != missing_id,
                "quality": 0.0 if criterion_id == missing_id else 1.0,
                "evidence_quote": "because the room was dark",
            }
            for criterion_id in criterion_ids
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": human_review,
        "feedback_to_learner": "Evidence recorded.",
    }


def test_deterministic_items_match_every_accepted_alternative_after_normalization():
    item = next(
        candidate
        for candidate in placement_bank_for("english", 3)
        if candidate.evaluation_mode == "deterministic"
        and len(candidate.accepted_answers) > 1
    )

    evaluation = grade_deterministic_placement_item(
        item,
        f"  {item.accepted_answers[-1].upper()}!!!  ",
    )

    assert evaluation.item_id == item.item_id
    assert evaluation.skill_ids == (item.primary_skill_id,)
    assert evaluation.score == 1.0
    assert evaluation.criteria[0].met is True
    assert evaluation.needs_human_review is False


@pytest.mark.parametrize(
    ("passage_starts_with", "complete_answer"),
    (
        (
            "The morning train to Jaipur",
            "The Jaipur train leaves from platform three.",
        ),
        (
            "Rohit may use the lab",
            "His teacher must sign the blue form before Rohit uses the lab.",
        ),
        (
            "The parcel reached the office",
            "Zoya collected the parcel on Tuesday.",
        ),
        (
            "The museum opens at ten",
            "The guided tour begins at ten thirty.",
        ),
        (
            "Entries must be emailed by Friday",
            "The entries must be sent by Friday.",
        ),
        (
            "Entries must be emailed by Friday",
            "The entries must be emailed by Friday.",
        ),
    ),
)
def test_class_five_detail_items_accept_the_complete_response_the_prompt_requests(
    passage_starts_with,
    complete_answer,
):
    item = _class_five_item(passage_starts_with=passage_starts_with)

    evaluation = grade_deterministic_placement_item(item, complete_answer)

    assert evaluation.criteria[0].met is True
    assert evaluation.score == 1.0


@pytest.mark.asyncio
async def test_authored_inference_recovers_from_malformed_provider_json():
    item = _class_five_item(passage_starts_with="Newspapers had collected")
    answer = (
        "The people are probably away because newspapers collected at the door "
        "and no lights appeared."
    )

    async def provider(_activity, _answer):
        raise SchoolOpenAnswerRetryableError("school_open_schema_failure")

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers
    assert evaluation.needs_human_review is False


@pytest.mark.asyncio
async def test_authored_inference_accepts_natural_resident_paraphrase():
    item = _class_five_item(passage_starts_with="Newspapers had collected")
    answer = (
        "The residents are probably away because papers piled up at the door "
        "and no lights came on for several evenings."
    )

    async def provider(_activity, _answer):
        raise SchoolOpenAnswerRetryableError("school_open_schema_failure")

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
async def test_authored_inference_fallback_accepts_natural_possessive_before_clue():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside because her shoes were wet "
        "and the closed umbrella was dripping by the door."
    )

    async def provider(_activity, _answer):
        raise SchoolOpenAnswerRetryableError("school_open_schema_failure")

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
async def test_authored_inference_fallback_accepts_cause_then_named_clues():
    item = _class_five_item(passage_starts_with="The balcony plants drooped")
    answer = (
        "The plants probably drooped because they had not been watered; the dry "
        "soil and empty watering can are the clues."
    )

    async def provider(_activity, _answer):
        raise SchoolOpenAnswerRetryableError("school_open_schema_failure")

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer", "inference_quote", "clue_quote"),
    (
        (
            "Only crumbs remained",
            "The puppy probably ate the food because only crumbs remained and it "
            "was licking its lips.",
            "The puppy probably ate the food",
            "only crumbs remained and it was licking its lips",
        ),
        (
            "Newspapers had collected",
            "The people are probably away because newspapers piled up and no "
            "lights came on for several evenings.",
            "The people are probably away",
            "newspapers piled up and no lights came on",
        ),
        (
            "The balcony plants drooped",
            "The plants lacked water because the soil was dry and the watering "
            "can had been empty for days.",
            "The plants lacked water",
            "the soil was dry and the watering can had been empty for days",
        ),
        (
            "The scoreboard showed",
            "They became quiet because the scoreboard showed that only one run "
            "was needed and the bowler was about to begin, so everyone watched "
            "closely.",
            "everyone watched closely",
            "the scoreboard showed that only one run was needed",
        ),
    ),
)
async def test_grounded_inference_paraphrase_survives_shared_validation(
    passage_starts_with,
    answer,
    inference_quote,
    clue_quote,
):
    item = _class_five_item(passage_starts_with=passage_starts_with)

    async def provider(activity, _answer):
        payload = _provider_payload(item)
        evidence_by_criterion = {
            "plausible_inference": inference_quote,
            "relevant_text_clue": clue_quote,
            "clue_supports_inference": answer,
            "complete_response": answer,
            "english_response": answer,
        }
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = evidence_by_criterion[criterion["id"]]
        validated = validate_school_open_evaluation(
            payload,
            context=school_open_context_from_activity(activity, answer),
        )
        return validated.evaluation.model_copy(
            update={"blockers": validated.effective_blockers}
        )

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.score == 1.0
    assert "semantic_required_claim_missing" not in evaluation.blockers
    assert not evaluation.blockers


@pytest.mark.asyncio
async def test_authored_inference_fallback_cannot_certify_a_negated_claim():
    item = _class_five_item(passage_starts_with="Newspapers had collected")
    answer = (
        "The people are not away because newspapers collected at the door and "
        "no lights appeared."
    )

    async def provider(_activity, _answer):
        raise SchoolOpenAnswerRetryableError("school_open_schema_failure")

    with pytest.raises(SchoolPlacementEvaluatorUnavailableError):
        await evaluate_school_placement_item(
            item,
            answer,
            provider=provider,
        )


def test_strict_activity_uses_authored_rubric_and_only_the_primary_skill():
    item = _item("strict_rubric")

    activity = build_placement_evaluator_activity(item)

    assert activity["activity_id"] == item.item_id
    assert activity["grading_mode"] == "strict_open_rubric"
    assert activity["rubric_ref"] == item.rubric_ref
    assert activity["skill_ids"] == [item.primary_skill_id]
    assert [criterion["id"] for criterion in activity["rubric_criteria"]] == list(
        STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref]
    )


@pytest.mark.asyncio
async def test_backend_score_and_blocker_override_an_inflated_provider_score():
    item = _item("strict_rubric")
    missing_id = STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref][0]

    async def provider(_activity, _answer):
        return _provider_payload(item, missing_id=missing_id)

    evaluation = await evaluate_school_placement_item(
        item,
        "because the room was dark",
        provider=provider,
    )

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers
    assert evaluation.criteria[0].evidence_quote == "because the room was dark"


@pytest.mark.asyncio
async def test_unmet_criterion_may_have_no_learner_evidence_without_failing_provider():
    item = _item("strict_rubric")
    missing_id = STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref][0]

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id=missing_id)
        payload["criteria"][0]["evidence_quote"] = "(empty answer)"
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        "because the room was dark",
        provider=provider,
    )

    assert evaluation.criteria[0].met is False
    assert evaluation.criteria[0].evidence_quote == "(empty answer)"
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_english_production_language_mismatch_is_unscorable_not_incorrect():
    item = _item("strict_rubric")

    async def provider(_activity, _answer):
        return _provider_payload(item, language="hi")

    evaluation = await evaluate_school_placement_item(
        item,
        "because the room was dark",
        provider=provider,
    )

    assert evaluation.blockers == ["language_mismatch"]
    assert "answer_incorrect" not in evaluation.misconception_tags


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        "provider",
        "wrong_item",
        "wrong_skill",
        "wrong_criteria",
        "human_review",
    ],
)
async def test_provider_schema_and_human_review_failures_share_stable_error(failure):
    item = _item("strict_rubric")

    async def provider(_activity, _answer):
        if failure == "provider":
            raise RuntimeError("provider detail must not escape")
        payload = _provider_payload(item, human_review=failure == "human_review")
        if failure == "wrong_item":
            payload["item_id"] = "wrong-item"
        elif failure == "wrong_skill":
            payload["skill_ids"] = ["writing.some_other_skill"]
        elif failure == "wrong_criteria":
            payload["criteria"].pop()
        return payload

    with pytest.raises(SchoolPlacementEvaluatorUnavailableError) as exc_info:
        await evaluate_school_placement_item(
            item,
            "because the room was dark",
            provider=provider,
        )

    assert str(exc_info.value) == EVALUATOR_UNAVAILABLE_CODE


@pytest.mark.asyncio
async def test_untraceable_met_quote_is_replaced_with_exact_learner_evidence():
    item = _item("strict_rubric")
    answer = "because the room was dark"

    async def provider(_activity, _answer):
        payload = _provider_payload(item)
        payload["criteria"][0]["evidence_quote"] = "invented or passage text"
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.criteria[0].met is True
    assert evaluation.criteria[0].evidence_quote == answer


@pytest.mark.asyncio
async def test_backend_accepts_clear_summary_paraphrase_when_model_calls_it_copied():
    item = _class_five_item(passage_starts_with="A storm broke two branches")
    answer = (
        "After storm damage made the road unusable, neighbours chopped up the "
        "fallen wood and opened a way through."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="own_words")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = (
                "(empty answer)" if criterion["id"] == "own_words" else answer
            )
            if criterion["id"] == "own_words":
                criterion["quality"] = 0.0
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    own_words = next(row for row in evaluation.criteria if row.id == "own_words")
    assert own_words.met is True
    assert own_words.quality == 1.0
    assert "required_criteria_missing" not in evaluation.blockers


@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "A storm broke two branches",
            "After storm damage made the road unusable, neighbours chopped up "
            "the fallen wood and opened a way through.",
        ),
        (
            "The school compared electricity bills",
            "After reviewing its power costs, the school put up solar panels "
            "and spent the resulting savings on library books.",
        ),
        (
            "Children found an injured bird",
            "The children contacted rescuers and kept the surroundings calm "
            "until assistance arrived.",
        ),
        (
            "Students mapped unsafe bus stops",
            "Students investigated risky bus stops, consulted commuters, and "
            "sent the transport office three practical safety improvements.",
        ),
        (
            "Two water samples looked equally clear",
            "Testing found dangerous bacteria in one clear-looking sample, so "
            "that water required treatment.",
        ),
    ),
)
@pytest.mark.asyncio
async def test_backend_authored_class_five_summary_claims_recover_model_detail_miss(
    passage_starts_with,
    answer,
):
    item = _class_five_item(passage_starts_with=passage_starts_with)

    assert len(item.semantic_claim_slots) >= 2

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="essential_details")
        payload["blockers"] = ["semantic_required_claim_missing"]
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = (
                "(empty answer)"
                if criterion["id"] == "essential_details"
                else answer
            )
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert "required_criteria_missing" not in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_copied_summary_when_model_calls_it_own_words():
    item = _class_five_item(passage_starts_with="A storm broke two branches")
    answer = (
        "A storm broke two branches and blocked the lane. In response to this "
        "problem, residents cut the branches into smaller pieces and cleared "
        "a path, which solved the issue for everyone."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item)
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = answer
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    own_words = next(row for row in evaluation.criteria if row.id == "own_words")
    assert own_words.met is False
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_source_tokens_padded_with_insertions():
    item = _class_five_item(passage_starts_with="A storm broke two branches")
    answer = (
        "A storm suddenly broke two large branches and completely blocked the "
        "narrow lane. Residents quickly cut the fallen branches into much "
        "smaller pieces and then cleared a safe path."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item)
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = answer
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    own_words = next(row for row in evaluation.criteria if row.id == "own_words")
    assert own_words.met is False
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_reordered_source_copy():
    item = _class_five_item(passage_starts_with="A storm broke two branches")
    answer = (
        "Residents first cut the branches into smaller pieces and then cleared "
        "a path. A storm earlier broke two branches and then blocked the lane."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="own_words")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = answer
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    own_words = next(row for row in evaluation.criteria if row.id == "own_words")
    assert own_words.met is False
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_accepts_explicit_inference_to_clue_link_model_missed():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside because her shoes were wet "
        "and her umbrella was dripping."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": (
                    "her shoes were wet and her umbrella was dripping"
                ),
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
            if criterion["id"] == "clue_supports_inference":
                criterion["quality"] = 0.0
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    linkage = next(
        row for row in evaluation.criteria if row.id == "clue_supports_inference"
    )
    assert linkage.met is True
    assert linkage.quality == 1.0
    assert "required_criteria_missing" not in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_provider_positive_linkage_that_answer_denies():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained. Her shoes were wet, but this clue does not support "
        "that inference."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item)
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained",
                "relevant_text_clue": "Her shoes were wet",
                "clue_supports_inference": answer,
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_negated_because_linkage():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside, but not because her shoes "
        "were wet."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": "her shoes were wet",
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_negated_due_to_linkage():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside, but not due to her wet "
        "shoes."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": "her wet shoes",
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_rejects_unrelated_because_clause_linkage():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside because I guessed, while her "
        "shoes were wet."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": "her shoes were wet",
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answer,inference_quote,clue_quote",
    (
        (
            "Because her shoes were wet and her umbrella was dripping, it "
            "probably rained while Ira was outside.",
            "it probably rained while Ira was outside",
            "her shoes were wet and her umbrella was dripping",
        ),
        (
            "Her wet shoes and dripping umbrella show that it probably rained "
            "while Ira was outside.",
            "it probably rained while Ira was outside",
            "Her wet shoes and dripping umbrella",
        ),
        (
            "Her shoes were wet and her umbrella was dripping; this shows that "
            "it probably rained while Ira was outside.",
            "it probably rained while Ira was outside",
            "Her shoes were wet and her umbrella was dripping",
        ),
        (
            "Her shoes were wet and her umbrella was dripping, indicating that "
            "it probably rained while Ira was outside.",
            "it probably rained while Ira was outside",
            "Her shoes were wet and her umbrella was dripping",
        ),
        (
            "Her shoes were wet and her umbrella was dripping, showing that it "
            "probably rained while Ira was outside.",
            "it probably rained while Ira was outside",
            "Her shoes were wet and her umbrella was dripping",
        ),
    ),
)
async def test_backend_accepts_clue_first_explicit_linkage(
    answer,
    inference_quote,
    clue_quote,
):
    item = _class_five_item(passage_starts_with="The sky was clear")

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": inference_quote,
                "relevant_text_clue": clue_quote,
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" not in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_canonicalizes_evidence_quote_punctuation_before_linkage_check():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside because her shoes were wet "
        "and her umbrella was dripping."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside.",
                "relevant_text_clue": "her shoes were wet and her umbrella was dripping",
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" not in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_allows_terminal_punctuation_on_linked_clue_quote():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside because her wet shoes and "
        "dripping umbrella are clear clues."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": (
                    "her wet shoes and dripping umbrella are clear clues."
                ),
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    linkage = next(
        row for row in evaluation.criteria if row.id == "clue_supports_inference"
    )
    assert linkage.met is True
    assert "required_criteria_missing" not in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_does_not_invent_inference_link_without_connection_word():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = "It probably rained. Her shoes were wet."

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = (
                "(empty answer)"
                if criterion["id"] == "clue_supports_inference"
                else answer
            )
            if criterion["id"] == "clue_supports_inference":
                criterion["quality"] = 0.0
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_ignores_connector_outside_inference_and_clue_spans():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside. Her shoes were wet. "
        "I was so surprised."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": "Her shoes were wet",
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
            if criterion["id"] == "clue_supports_inference":
                criterion["quality"] = 0.0
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_backend_ignores_unrelated_connector_between_evidence_sentences():
    item = _class_five_item(passage_starts_with="The sky was clear")
    answer = (
        "It probably rained while Ira was outside. "
        "I stayed home because I was tired. Her shoes were wet."
    )

    async def provider(_activity, _answer):
        payload = _provider_payload(item, missing_id="clue_supports_inference")
        for criterion in payload["criteria"]:
            criterion["evidence_quote"] = {
                "plausible_inference": "It probably rained while Ira was outside",
                "relevant_text_clue": "Her shoes were wet",
                "clue_supports_inference": "(empty answer)",
            }.get(criterion["id"], answer)
            if criterion["id"] == "clue_supports_inference":
                criterion["quality"] = 0.0
        return payload

    evaluation = await evaluate_school_placement_item(
        item,
        answer,
        provider=provider,
    )

    assert "required_criteria_missing" in evaluation.blockers


def test_clause_order_accepts_authored_equivalent_object_noun():
    item = _class_five_item(
        passage_starts_with="Parts: the result / although the first trial failed"
    )

    evaluation = grade_deterministic_placement_item(
        item,
        "Although the first trial failed, the team repeated the test to verify the result.",
    )

    assert evaluation.score == 1.0
    assert evaluation.criteria[0].met is True
