import pytest

from app.content.school_rebuild_placement_bank import placement_bank_for
from app.content.school_rebuild_placement_validation import (
    STRICT_RUBRIC_CRITERIA_BY_REF,
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


def _provider_payload(item, *, language="en", missing_id=None, human_review=False):
    criterion_ids = STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref]
    return {
        "schema_version": "school-v3-rubric-1",
        "item_id": item.item_id,
        "skill_ids": [item.primary_skill_id],
        "score": 1.0,
        "confidence": 0.96,
        "language_detected": language,
        "criteria": [
            {
                "id": criterion_id,
                "met": criterion_id != missing_id,
                "quality": 1.0,
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


def test_strict_activity_uses_authored_rubric_and_only_the_primary_skill():
    item = _item("strict_rubric")

    activity = build_placement_evaluator_activity(item)

    assert activity["activity_id"] == item.item_id
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
