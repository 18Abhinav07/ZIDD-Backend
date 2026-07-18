import pytest

from app.content.school_rebuild_placement_bank import placement_bank_for
from app.content.school_rebuild_placement_validation import (
    STRICT_RUBRIC_CRITERIA_BY_REF,
)
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION
from app.services.school_rebuild_placement_evaluator import (
    evaluate_school_placement_item,
    grade_deterministic_placement_item,
)


def _item(class_no: int, passage_starts_with: str):
    return next(
        item
        for item in placement_bank_for("english", class_no)
        if item.passage.startswith(passage_starts_with)
    )


def _provider_payload(
    item,
    answer: str,
    *,
    missed_ids=(),
    blockers=(),
    score=1.0,
):
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": item.item_id,
        "skill_ids": [item.primary_skill_id],
        "score": score,
        "confidence": 0.96,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion_id,
                "met": criterion_id not in missed_ids,
                "quality": 0.0 if criterion_id in missed_ids else 1.0,
                "evidence_quote": answer,
            }
            for criterion_id in STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref]
        ],
        "misconception_tags": [],
        "blockers": list(blockers),
        "needs_human_review": False,
        "feedback_to_learner": "Evidence recorded.",
    }


@pytest.mark.parametrize(
    ("class_no", "passage_starts_with", "answer"),
    (
        (3, "Rina sat", "Rina sat on the mat near the window."),
        (3, "Nila put", "Nila put three mangoes in a basket."),
        (3, "Nila put", "Nila put three mangoes in the basket."),
        (3, "Mira found", "Mira found a shell beside the river."),
        (3, "Farah carried", "Farah carried a yellow umbrella to school."),
        (
            3,
            "The conductor gave",
            "The conductor gave Mohan a blue ticket.",
        ),
        (4, "Tara placed", "Tara placed her silver medal inside a wooden box."),
        (4, "Tara placed", "Tara placed her silver medal inside the wooden box."),
        (4, "The guard left", "Meena's neighbour received the parcel."),
        (4, "After science class", "Dev returned the green notebook."),
        (4, "The eco-club meeting", "The eco-club meeting will happen on Thursday."),
        (4, "Bus 12 stops", "Bus 12 reaches the museum first."),
    ),
)
def test_sentence_detail_items_accept_authored_complete_sentence_answers(
    class_no,
    passage_starts_with,
    answer,
):
    evaluation = grade_deterministic_placement_item(
        _item(class_no, passage_starts_with),
        answer,
    )

    assert evaluation.score == 1.0
    assert evaluation.criteria[0].met is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer", "missed_ids"),
    (
        (
            "A bird rests",
            "A bird rests on a branch and watches the garden below.",
            ("relevant_detail",),
        ),
        (
            "A bird rests",
            "The bird watches the garden from a branch.",
            ("relevant_detail",),
        ),
        (
            "The market became",
            "The market became busy after sunrise.",
            ("relevant_detail",),
        ),
        (
            "The children moved",
            "The children moved under a tree because the afternoon sun became hot.",
            ("relevant_detail", "complete_response"),
        ),
        (
            "The seedlings bent",
            "The gardener tied each seedling to a thin stick.",
            ("relevant_detail", "complete_response"),
        ),
        (
            "Aarav reached",
            "Aarav missed the bus and called his uncle for help.",
            ("relevant_detail", "complete_response"),
        ),
    ),
)
async def test_authored_class3_claims_override_provider_false_negatives(
    passage_starts_with,
    answer,
    missed_ids,
):
    item = _item(3, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer, missed_ids=missed_ids)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        ("A bird rests", "The bird watches the garden from the branch."),
        ("The market became", "After sunrise, the market became busy."),
        (
            "The children moved",
            "Because it was hot, the children went under the tree.",
        ),
        (
            "The seedlings bent",
            "The gardener tied every seedling to a thin stick.",
        ),
        (
            "Aarav reached",
            "Aarav missed his bus and called his uncle for help.",
        ),
        (
            "The children moved",
            "The children went under the tree because it was hot, not because of rain.",
        ),
    ),
)
async def test_provider_positive_defensible_paraphrases_remain_passing(
    passage_starts_with,
    answer,
):
    item = _item(3, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer", "missed_ids"),
    (
        (
            "A bird rests",
            "A bird rests on a branch, and the garden watches the bird.",
            ("relevant_detail",),
        ),
        (
            "The market became",
            "The market became busy after sunrise, and sunrise became busy.",
            ("relevant_detail",),
        ),
        (
            "The children moved",
            "The children moved under a tree because it was hot, and the tree moved under the children.",
            ("relevant_detail", "complete_response"),
        ),
        (
            "The seedlings bent",
            "The gardener tied each seedling to a thin stick, and the seedling tied the gardener.",
            ("relevant_detail", "complete_response"),
        ),
        (
            "Aarav reached",
            "Aarav missed the bus and called his uncle for help, but his uncle had left the stop.",
            ("relevant_detail", "complete_response"),
        ),
    ),
)
async def test_provider_false_authored_clause_with_bad_extra_is_not_promoted(
    passage_starts_with,
    answer,
    missed_ids,
):
    item = _item(3, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer, missed_ids=missed_ids)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)
    criteria = {criterion.id: criterion for criterion in evaluation.criteria}

    assert evaluation.score < 1.0
    assert all(not criteria[criterion_id].met for criterion_id in missed_ids)
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        ("A bird rests", "A bird on a branch."),
        ("A bird rests", "A bird rests on a branch"),
        ("A bird rests", "A dog rests on a branch and watches the garden below."),
        ("A bird rests", "A bird does not rest on a branch."),
        ("The market became", "The station became busy after sunrise."),
        (
            "The children moved",
            "The children moved under a tree for shelter from the rain.",
        ),
        ("The seedlings bent", "The seedling had two green leaves."),
        ("Aarav reached", "Aarav missed the bus because he left home late."),
        (
            "A bird rests",
            "A bird rests on a branch. My bicycle is blue and I like long stories.",
        ),
    ),
)
async def test_authored_class3_correction_rejects_semantic_near_misses(
    passage_starts_with,
    answer,
):
    item = _item(3, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)
    criteria = {criterion.id: criterion for criterion in evaluation.criteria}

    assert evaluation.score < 0.8
    assert list(evaluation.blockers) == ["required_criteria_missing"]
    assert any(
        not criteria[criterion_id].met
        for criterion_id in ("relevant_detail", "complete_response")
        if criterion_id in criteria
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "Nitin dropped",
            "Reva picked up the baton and passed it back, so the relay could continue.",
        ),
        (
            "The sapling's leaves",
            "Omar moved the sapling to protect it because its leaves were drying in the harsh sun.",
        ),
        (
            "Lata practised",
            "Lata played the tune without stopping because she practised it each day.",
        ),
        (
            "The old footbridge",
            "The bridge was unsafe because cracks appeared in two wooden boards.",
        ),
    ),
)
async def test_authored_class4_inference_recovers_provider_false_negative(
    passage_starts_with,
    answer,
):
    item = _item(4, passage_starts_with)
    criterion_ids = STRICT_RUBRIC_CRITERIA_BY_REF[item.rubric_ref]

    async def provider(_activity, _answer):
        return _provider_payload(
            item,
            answer,
            missed_ids=criterion_ids,
            blockers=("evaluator_evidence_untraceable", "required_criteria_missing"),
            score=0.75,
        )

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "Nitin dropped",
            "The relay could continue, but Reva never picked up or returned the baton.",
        ),
        (
            "The old footbridge",
            "The bridge was unsafe, but the cracks in the boards did not support that conclusion.",
        ),
        (
            "Lata practised",
            "Lata played without stopping. She practised each day.",
        ),
    ),
)
async def test_authored_class4_inference_does_not_promote_contradictory_or_unlinked_answer(
    passage_starts_with,
    answer,
):
    item = _item(4, passage_starts_with)
    missing_id = "clue_supports_inference"

    async def provider(_activity, _answer):
        return _provider_payload(item, answer, missed_ids=(missing_id,), score=0.75)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_authored_class4_inference_does_not_certify_locally_negated_alias():
    item = _item(4, "Nitin dropped")
    answer = (
        "Reva never picked up the baton and passed it back, "
        "so the relay could continue."
    )

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)
    criteria = {criterion.id: criterion for criterion in evaluation.criteria}

    assert evaluation.score < 1.0
    assert criteria["relevant_text_clue"].met is False
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "A seed split",
            "After the seed split, a root grew down and a shoot moved toward the light.",
        ),
        (
            "Residents removed plastic",
            "Residents cared for the pond by removing plastic, planting reeds, and putting up signs against littering.",
        ),
        (
            "A model bridge collapsed",
            "The group widened the bridge base, retested it, and made it strong enough to hold the weights.",
        ),
    ),
)
async def test_authored_class4_summary_recovers_traceability_false_negative(
    passage_starts_with,
    answer,
):
    item = _item(4, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(
            item,
            answer,
            missed_ids=("essential_details", "own_words"),
            blockers=("evaluator_evidence_untraceable", "required_criteria_missing"),
            score=0.75,
        )

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "A seed split",
            "A seed split after rain reached the soil. A small root grew downward and a shoot moved toward the light.",
        ),
        (
            "Residents removed plastic",
            "Residents removed plastic from the pond.",
        ),
    ),
)
async def test_authored_class4_summary_does_not_promote_copy_or_partial_response(
    passage_starts_with,
    answer,
):
    item = _item(4, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(
            item,
            answer,
            missed_ids=("essential_details", "own_words"),
            score=0.75,
        )

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_copied_accurate_summary_fails_only_own_words_evidence():
    item = _item(4, "A seed split")
    answer = (
        "A seed split after rain reached the soil, a small root grew downward, "
        "and a shoot moved toward the light."
    )

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)
    criteria = {criterion.id: criterion for criterion in evaluation.criteria}

    assert criteria["own_words"].met is False
    assert all(
        criteria[criterion_id].met
        for criterion_id in (
            "main_idea_or_event",
            "essential_details",
            "concise_complete_response",
            "english_response",
        )
    )
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_provider_positive_summary_paraphrase_survives_one_unmatched_alias():
    item = _item(4, "A seed split")
    answer = (
        "After the seed split, a root descended into the soil and a shoot moved "
        "toward the light."
    )

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "A seed split",
            "The seed failed to split, a root grew down, and a shoot moved toward the light.",
        ),
        (
            "A seed split",
            "The seed split, a root grew down, and a shoot moved toward the light, but it became a giant tree overnight.",
        ),
        (
            "A seed split",
            "The seed split and a root grew down.",
        ),
    ),
)
async def test_authored_class4_summary_rejects_negation_extra_claim_and_missing_event(
    passage_starts_with,
    answer,
):
    item = _item(4, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "A model bridge collapsed",
            "The group widened the bridge base, retested it, and never held the weights.",
        ),
        (
            "Residents removed plastic",
            "Residents cared for the pond by removing plastic, planting reeds, "
            "and putting up signs against littering, while visitors planted plastic.",
        ),
    ),
)
async def test_authored_summary_aliases_do_not_certify_negated_or_unsupported_clause(
    passage_starts_with,
    answer,
):
    item = _item(4, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)
    criteria = {criterion.id: criterion for criterion in evaluation.criteria}

    assert evaluation.score < 1.0
    assert criteria["essential_details"].met is False
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answer",
    (
        "Reva picked up the baton and passed it back, so the relay could continue because the moon is made of cheese.",
        "Reva picked up the baton and passed it back, so the relay could continue. Later the relay stopped.",
    ),
)
async def test_authored_class4_inference_does_not_override_provider_for_extra_claims(
    answer,
):
    item = _item(4, "Nitin dropped")

    async def provider(_activity, _answer):
        return _provider_payload(
            item,
            answer,
            missed_ids=("plausible_inference",),
            score=0.75,
        )

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_authored_class3_short_answer_missing_reason_cannot_inherit_provider_pass():
    item = _item(3, "The children moved")
    answer = "The children moved under a tree."

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("passage_starts_with", "answer"),
    (
        (
            "The children moved",
            "The children moved under a tree to escape the heat.",
        ),
        (
            "Aarav reached",
            "Aarav missed the bus and phoned a family member for assistance.",
        ),
    ),
)
async def test_provider_positive_natural_paraphrase_survives_partial_authored_match(
    passage_starts_with,
    answer,
):
    item = _item(3, passage_starts_with)

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score == 1.0
    assert all(criterion.met for criterion in evaluation.criteria)
    assert not evaluation.blockers


@pytest.mark.asyncio
async def test_authored_class3_sentence_with_dangling_connector_is_not_complete():
    item = _item(3, "A bird rests")
    answer = "A bird rests on a branch but."

    async def provider(_activity, _answer):
        return _provider_payload(item, answer)

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert evaluation.score < 1.0
    assert "required_criteria_missing" in evaluation.blockers


@pytest.mark.asyncio
async def test_untraceable_provider_evidence_stays_blocked_without_authored_proof():
    item = _item(3, "The room was dark")
    answer = "Kabir switched on the lamp for a reason that is not stated here."

    async def provider(_activity, _answer):
        return _provider_payload(
            item,
            answer,
            blockers=("evaluator_evidence_untraceable",),
        )

    evaluation = await evaluate_school_placement_item(item, answer, provider=provider)

    assert "evaluator_evidence_untraceable" in evaluation.blockers
