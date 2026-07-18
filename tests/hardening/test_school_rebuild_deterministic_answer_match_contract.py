from dataclasses import replace

import pytest

from app.content.school_rebuild_placement_bank import placement_bank_for
from app.services.school_rebuild_placement_evaluator import (
    grade_deterministic_placement_item,
)


def _class_five_item(*, accepted_answer: str):
    return next(
        item
        for item in placement_bank_for("english", 5)
        if accepted_answer in item.accepted_answers
    )


def _class_two_item(*, item_id: str):
    return next(
        item
        for item in placement_bank_for("english", 2)
        if item.item_id == item_id
    )


def test_short_answer_accepts_only_an_authored_normalized_alternative():
    item = _class_five_item(accepted_answer="Tuesday")

    exact = grade_deterministic_placement_item(item, "  TUESDAY!!! ")
    expanded = grade_deterministic_placement_item(
        item, "It was collected on Tuesday."
    )

    assert exact.score == 1.0
    assert exact.criteria[0].met is True
    assert expanded.score == 0.0
    assert expanded.criteria[0].met is False


@pytest.mark.parametrize("written_time", ("10:30", "ten thirty", "10.30"))
def test_each_authored_time_alternative_is_accepted_in_a_complete_sentence(
    written_time,
):
    item = _class_five_item(accepted_answer="10:30")

    exact = grade_deterministic_placement_item(item, written_time)
    expanded = grade_deterministic_placement_item(
        item, f"The guided tour begins at {written_time}."
    )

    assert exact.score == 1.0
    assert expanded.score == 1.0


def test_authored_permission_answer_accepts_the_natural_modal_variant():
    item = _class_five_item(accepted_answer="his teacher signs the blue form")

    evaluation = grade_deterministic_placement_item(
        item,
        "His teacher must sign the blue form before Rohit can use the lab.",
    )

    assert evaluation.score == 1.0
    assert evaluation.criteria[0].met is True


def test_authored_time_answer_accepts_the_relevant_location_detail():
    item = _class_five_item(accepted_answer="10:30")

    evaluation = grade_deterministic_placement_item(
        item,
        "The guided tour begins at 10:30 near the main staircase.",
    )

    assert evaluation.score == 1.0
    assert evaluation.criteria[0].met is True


@pytest.mark.parametrize(
    "answer",
    (
        "Zoya collected the parcel on Wednesday; it reached the office on Tuesday.",
        "Zoya did not collect the parcel on Tuesday.",
        "Zoya may have collected the parcel on Tuesday.",
        "Zoya was collected by the parcel on Tuesday.",
        "Zoya was collected on Tuesday.",
        (
            "The parcel was collected by Zoya on Tuesday, a claim I reject; "
            "it was actually Wednesday."
        ),
    ),
)
def test_short_answer_rejects_conflict_negation_uncertainty_and_role_reversal(
    answer,
):
    item = _class_five_item(accepted_answer="Tuesday")

    evaluation = grade_deterministic_placement_item(item, answer)

    assert evaluation.score == 0.0
    assert evaluation.criteria[0].met is False


@pytest.mark.parametrize(
    "answer",
    (
        "The guide arrived at 10:30; the tour begins later.",
        "The guide arrived at 10:30, but the guided tour begins at 11:00.",
        "The guided tour does not begin at 10:30 near the main staircase.",
        "10:30 is incorrect; the guided tour begins at 11:00.",
        "The guided tour begins at 10:30 or 11:00 near the main staircase.",
        "The guided tour begins at 10:30 and 11:00.",
        "The guided tour ends at 10:30 near the main staircase.",
        "At 10:30 the staircase begins tour guided.",
    ),
)
def test_short_answer_rejects_negated_contradictory_or_reordered_time_answers(
    answer,
):
    item = _class_five_item(accepted_answer="10:30")

    evaluation = grade_deterministic_placement_item(item, answer)

    assert evaluation.score == 0.0
    assert evaluation.criteria[0].met is False


@pytest.mark.parametrize(
    "answer",
    (
        "His teacher must not sign the blue form before Rohit uses the lab.",
        "His teacher must sign the blue form after Rohit uses the lab.",
        "Rohit must sign the blue form before his teacher can use the lab.",
        "The blue form must sign his teacher before Rohit can use the lab.",
    ),
)
def test_short_answer_rejects_negated_or_role_reversed_content(answer):
    item = _class_five_item(accepted_answer="his teacher signs the blue form")

    evaluation = grade_deterministic_placement_item(item, answer)

    assert evaluation.score == 0.0
    assert evaluation.criteria[0].met is False


@pytest.mark.parametrize("item_type", ("multiple_choice", "fill_blank"))
def test_non_short_answer_types_remain_exact_match_only(item_type):
    short_answer_item = _class_five_item(accepted_answer="10:30")
    item = replace(short_answer_item, item_type=item_type)

    exact = grade_deterministic_placement_item(item, "  10:30!!! ")
    contained = grade_deterministic_placement_item(
        item,
        "The answer is 10:30.",
    )

    assert exact.score == 1.0
    assert contained.score == 0.0


def test_deterministic_matcher_cannot_certify_role_reversal():
    source = _class_five_item(accepted_answer="Tuesday")
    item = replace(
        source,
        prompt="Who helps Mira?",
        passage="Ravi helped Mira.",
        accepted_answers=("Ravi helps Mira",),
        answer_key="Ravi helps Mira",
    )

    correct = grade_deterministic_placement_item(item, "Ravi helps Mira")
    reversed_roles = grade_deterministic_placement_item(item, "Mira helps Ravi")

    assert correct.score == 1.0
    assert reversed_roles.score == 0.0


@pytest.mark.parametrize(
    ("item_id", "complete_answer", "wrong_answer"),
    (
        ("spv_c02_t01_v01", "The kite is in the sky.", "The kite is under the bed."),
        ("spv_c02_t01_v02", "The cat sleeps on a rug.", "The cat sleeps in the sky."),
        ("spv_c02_t01_v03", "Mina's cup is on the table.", "Mina's cup is under the bed."),
        (
            "spv_c02_t01_v04",
            "Arun put the lunch box beside the school bag.",
            "Arun put the lunch box under the bed.",
        ),
        (
            "spv_c02_t01_v05",
            "Ria's shoes are under the bed.",
            "Ria's shoes are in the sky.",
        ),
        ("spv_c02_t02_v01", "Ravi runs to the gate.", "Asha runs to the gate."),
        (
            "spv_c02_t02_v02",
            "Asha sweeps the classroom floor.",
            "Ravi sweeps the classroom floor.",
        ),
        ("spv_c02_t02_v03", "Kabir waters the plant.", "Neha waters the plant."),
        (
            "spv_c02_t02_v04",
            "The teacher opens the blue book.",
            "The blue book opens the teacher.",
        ),
        (
            "spv_c02_t02_v05",
            "Neha carries the basket.",
            "The basket carries Neha.",
        ),
    ),
)
def test_class_two_direct_detail_items_accept_complete_english_answers_only(
    item_id,
    complete_answer,
    wrong_answer,
):
    item = _class_two_item(item_id=item_id)

    correct = grade_deterministic_placement_item(item, complete_answer)
    wrong = grade_deterministic_placement_item(item, wrong_answer)

    assert correct.score == 1.0
    assert correct.criteria[0].met is True
    assert wrong.score == 0.0
    assert wrong.criteria[0].met is False


@pytest.mark.parametrize(
    ("item_id", "answer"),
    (
        ("spv_c02_t01_v01", "The kite is not in the sky."),
        ("spv_c02_t01_v02", "The cat might sleep on a rug."),
        ("spv_c02_t02_v01", "Ravi does not run to the gate."),
        ("spv_c02_t02_v02", "The classroom floor sweeps Asha."),
    ),
)
def test_class_two_complete_answers_reject_negation_uncertainty_and_role_reversal(
    item_id,
    answer,
):
    item = _class_two_item(item_id=item_id)

    evaluation = grade_deterministic_placement_item(item, answer)

    assert evaluation.score == 0.0
    assert evaluation.criteria[0].met is False
