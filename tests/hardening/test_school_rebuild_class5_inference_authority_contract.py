from __future__ import annotations

import pytest

from app.content.school_rebuild_placement_bank import placement_tracks_for
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services.school_rebuild_placement_evaluator import (
    build_placement_evaluator_activity,
)


_VALID_ANSWERS_BY_PASSAGE_MARKER = {
    "wet shoes": (
        "It rained while Ira was outside because her shoes were wet."
    ),
    "crumbs remained": (
        "The puppy ate the food because only crumbs remained."
    ),
    "newspapers had collected": (
        "The people are away because newspapers collected at the door."
    ),
    "one run needed": (
        "The team was focused because only one run was needed."
    ),
    "balcony plants drooped": (
        "The plants were not watered because the soil was dry."
    ),
}


def _class_5_inference_items():
    track = next(
        item
        for item in placement_tracks_for("english", 5)
        if item.track_id == "english.c5.inference"
    )
    return (
        track.snapshot_item,
        *(item for band in track.bands for item in band.variants),
    )


def _item_for(marker: str):
    return next(
        item
        for item in _class_5_inference_items()
        if marker in item.passage.casefold()
    )


def _inflated_payload(activity: dict, answer: str) -> dict:
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": list(activity["skill_ids"]),
        "score": 1.0,
        "confidence": 0.99,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": True,
                "quality": 1.0,
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "You connected an inference to a text clue.",
    }


@pytest.mark.parametrize(
    ("passage_marker", "answer"),
    tuple(_VALID_ANSWERS_BY_PASSAGE_MARKER.items()),
)
def test_every_class_5_inference_variant_carries_authored_claim_and_clue_slots(
    passage_marker: str,
    answer: str,
) -> None:
    activity = build_placement_evaluator_activity(_item_for(passage_marker))
    context = school_open_context_from_activity(activity, answer)

    assert activity["grading_mode"] == "strict_open_rubric"
    assert tuple(slot.id for slot in context.semantic_claim_slots) == (
        "inference_claim",
        "passage_clue",
    )
    assert context.ordered_semantic_claim_slot_ids == ()

    validated = validate_school_open_evaluation(
        _inflated_payload(activity, answer),
        context=context,
    )

    assert validated.effective_blockers == ()
    assert validated.certification_eligible is True


def test_class_5_inference_accepts_clue_before_inference() -> None:
    item = _item_for("wet shoes")
    activity = build_placement_evaluator_activity(item)
    answer = "Because her shoes were wet, it probably rained while Ira was outside."

    validated = validate_school_open_evaluation(
        _inflated_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )

    assert validated.effective_blockers == ()
    assert validated.certification_eligible is True


def test_unrelated_inference_cannot_certify_from_a_real_passage_clue() -> None:
    item = _item_for("wet shoes")
    activity = build_placement_evaluator_activity(item)
    answer = "The moon is made of cheese because her wet shoes were wet."

    validated = validate_school_open_evaluation(
        _inflated_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )

    assert "semantic_required_claim_missing" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_later_rejection_of_own_inference_cannot_certify() -> None:
    item = _item_for("wet shoes")
    activity = build_placement_evaluator_activity(item)
    answer = (
        "It rained because her shoes were wet, a conclusion I reject."
    )

    validated = validate_school_open_evaluation(
        _inflated_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )

    assert "authored_contradiction" in validated.effective_blockers
    assert validated.certification_eligible is False
