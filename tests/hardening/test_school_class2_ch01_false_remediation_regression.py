import json
from pathlib import Path

import pytest

from app.content.school.content_schema import SchoolRubricEvaluation
from app.services import school_rebuild_curriculum as curriculum
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION


CHAPTER_PATH = (
    Path(__file__).resolve().parents[2]
    / "app/content/school_rebuild_chapters/english/class_2/eng_c2_ch01.json"
)
ACTIVITY_ID = "bicycle_words_in_action:review:1"
REQUIREMENT_1 = f"{ACTIVITY_ID}:requirement:1"
REQUIREMENT_2 = f"{ACTIVITY_ID}:requirement:2"
LIVE_ANSWER = (
    "A tyre is the rubber wheel part with tread, and Isha wipes mud off the "
    "back tyre after the rain."
)


def _review_activity() -> dict:
    chapter = json.loads(CHAPTER_PATH.read_text(encoding="utf-8"))
    authored = next(
        variant
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        for variant in step.get("variant_pool") or []
        if variant.get("variant_id") == ACTIVITY_ID
    )
    return {
        **authored,
        "activity_id": authored["variant_id"],
        "skill_ids": authored["knowledge_components"],
    }


def _first_pass_evaluation(
    activity: dict,
    answer: str,
    *,
    blockers: tuple[str, ...] = ("semantic_required_claim_missing",),
) -> SchoolRubricEvaluation:
    first_evidence, _, second_evidence = answer.partition(", and ")
    return SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.8,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": REQUIREMENT_1,
                    "met": True,
                    "quality": 0.9,
                    "evidence_quote": first_evidence,
                },
                {
                    "id": REQUIREMENT_2,
                    "met": True,
                    "quality": 0.7,
                    "evidence_quote": second_evidence or answer,
                },
            ],
            "misconception_tags": [],
            "blockers": list(blockers),
            "needs_human_review": False,
            "feedback_to_learner": "The response includes both scene details.",
        }
    )


def test_live_tyre_answer_recovers_below_authored_quality_without_false_remediation():
    activity = _review_activity()

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(activity, LIVE_ANSWER),
        answer=LIVE_ANSWER,
    )

    criteria = {criterion["id"]: criterion for criterion in decision["criteria"]}
    assert [
        criterion["min_quality"] for criterion in activity["rubric_criteria"]
    ] == [0.8, 0.8]
    assert criteria[REQUIREMENT_1]["quality"] == 0.9
    assert criteria[REQUIREMENT_2] == {
        "id": REQUIREMENT_2,
        "met": True,
        "quality": 1.0,
        "evidence_quote": "wipes mud",
    }
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []
    assert decision["correct"] is True


def test_canonical_recovery_preserves_a_genuine_provider_blocker():
    activity = _review_activity()

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(
            activity,
            LIVE_ANSWER,
            blockers=(
                "semantic_required_claim_missing",
                "provider_policy_blocker",
            ),
        ),
        answer=LIVE_ANSWER,
    )

    assert decision["missing_criteria"] == []
    assert decision["blockers"] == ["provider_policy_blocker"]
    assert decision["correct"] is False


@pytest.mark.parametrize(
    ("answer", "expected_evidence"),
    (
        (
            "A tyre is a rubber wheel part, and I wipe mud off its tread.",
            "wipe mud",
        ),
        (
            "A tyre is a rubber wheel part, and Isha wiped mud off its tread.",
            "wiped mud",
        ),
        (
            "A tyre is a rubber wheel part, and Isha wipes mud off its tread.",
            "wipes mud",
        ),
        (
            "A tyre is a rubber wheel part, and Isha is wiping mud off its tread.",
            "wiping mud",
        ),
    ),
)
def test_wipe_inflections_are_semantically_equivalent_to_clean(
    answer,
    expected_evidence,
):
    activity = _review_activity()

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(activity, answer),
        answer=answer,
    )

    requirement = next(
        criterion
        for criterion in decision["criteria"]
        if criterion["id"] == REQUIREMENT_2
    )
    assert requirement["quality"] == 1.0
    assert requirement["evidence_quote"] == expected_evidence
    assert decision["correct"] is True


@pytest.mark.parametrize(
    "answer",
    (
        pytest.param(
            "A tyre is the rubber wheel part, and Isha did not at any point "
            "wipe mud off the back tyre.",
            id="direct-scope-negation",
        ),
        pytest.param(
            "A tyre is the rubber wheel part, and Isha did not actually try "
            "to wipe mud off the back tyre.",
            id="extended-scope-negation",
        ),
        pytest.param(
            "Isha shouldn't wipe mud off the tyre.",
            id="negative-modal-contraction",
        ),
        pytest.param(
            "Neither Isha nor Dev wiped mud off the tyre.",
            id="neither-nor-negation",
        ),
        pytest.param(
            "Isha left without wiping mud off the tyre.",
            id="without-gerund-negation",
        ),
        pytest.param(
            "The claim that Isha wiped mud off the tyre is not true.",
            id="postposed-denial",
        ),
        pytest.param(
            "Isha did not do this: wipe mud off the tyre.",
            id="colon-negation-continuation",
        ),
        pytest.param(
            "Isha did not\nwipe mud off the tyre.",
            id="newline-negation-continuation",
        ),
        pytest.param(
            "Isha did not try to wipe mud off the tyre.",
            id="negated-complement-control",
        ),
        pytest.param(
            "Isha did not wipe and clean mud off the tyre.",
            id="shared-negation-control",
        ),
        pytest.param(
            "Isha did not stop and wipe mud off the tyre.",
            id="shared-auxiliary-base-target",
        ),
        pytest.param(
            "Isha wiped no mud off the tyre.",
            id="in-span-negation",
        ),
        pytest.param(
            "Isha wiped the bicycle. Mud remained on the tyre.",
            id="sentence-crossing-concept-span",
        ),
        pytest.param(
            "Isha wiped the bicycle but the mud stayed.",
            id="contrastive-crossing-concept-span",
        ),
        pytest.param(
            "Isha wiped the bicycle, and the mud stayed on the tyre.",
            id="coordinating-subject-boundary",
        ),
        pytest.param(
            "Isha wiped the bicycle, and the mud remained on the tyre.",
            id="coordinating-subject-past-predicate",
        ),
        pytest.param(
            "Isha wiped the bicycle, and the mud was still there.",
            id="coordinating-subject-finite-auxiliary",
        ),
        pytest.param(
            "Isha wiped the bicycle while the mud stayed on the tyre.",
            id="while-subject-boundary",
        ),
        pytest.param(
            "Isha wiped the bicycle whereas the mud stayed on the tyre.",
            id="whereas-subject-boundary",
        ),
        pytest.param(
            "Isha wiped the bicycle although the mud stayed on the tyre.",
            id="although-subject-boundary",
        ),
        pytest.param(
            "Isha wiped the bicycle because the mud stayed on the tyre.",
            id="because-subject-boundary",
        ),
    ),
)
def test_negated_cleaning_claim_is_not_promoted(answer):
    activity = _review_activity()

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(activity, answer),
        answer=answer,
    )

    criteria = {criterion["id"]: criterion for criterion in decision["criteria"]}
    assert criteria[REQUIREMENT_2]["quality"] == 0.7
    assert REQUIREMENT_2 in decision["missing_criteria"]
    assert decision["blockers"] == ["semantic_required_claim_missing"]
    assert decision["correct"] is False


def test_in_span_negation_blocks_authored_concept_evidence():
    assert (
        curriculum._authored_concept_evidence_quote(
            "Isha wiped no mud off the tyre.",
            "cleans mud",
        )
        is None
    )


@pytest.mark.parametrize(
    ("answer", "expected_evidence"),
    (
        pytest.param(
            "Isha wiped dirt and mud off the tyre.",
            "wiped dirt and mud",
            id="same-clause-coordination",
        ),
        pytest.param(
            "Isha wiped dirt and mud stains off the tyre.",
            "wiped dirt and mud",
            id="coordinated-noun-phrase",
        ),
        pytest.param(
            "Isha wiped dirt and the mud off the tyre.",
            "wiped dirt and the mud",
            id="coordinated-determiner-object",
        ),
        pytest.param(
            "Isha wiped dirt and the mud-covered tyre clean.",
            "wiped dirt and the mud",
            id="hyphenated-compound-object",
        ),
        pytest.param(
            "Isha wiped the bicycle, and she later wiped mud off the tyre.",
            "wiped mud",
            id="later-explicit-cleaning-clause",
        ),
    ),
)
def test_connector_boundedness_preserves_affirmative_cleaning_clause(
    answer,
    expected_evidence,
):
    activity = _review_activity()

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(activity, answer),
        answer=answer,
    )

    criteria = {criterion["id"]: criterion for criterion in decision["criteria"]}
    assert criteria[REQUIREMENT_2]["quality"] == 1.0
    assert criteria[REQUIREMENT_2]["evidence_quote"] == expected_evidence
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []
    assert decision["correct"] is True


@pytest.mark.parametrize(
    "answer",
    (
        pytest.param(
            "A tyre is not metal: Isha wiped mud off the tyre.",
            id="colon-boundary",
        ),
        pytest.param(
            "A tyre is not metal\nIsha wiped mud off the tyre.",
            id="newline-boundary",
        ),
        pytest.param(
            "A tyre is not metal and Isha wiped mud off the tyre.",
            id="coordinating-boundary",
        ),
        pytest.param(
            "Isha did not hesitate when she saw the mud and then she wiped "
            "mud off the tyre.",
            id="negated-earlier-predicate",
        ),
        pytest.param(
            "Isha did not just look but wiped mud off the tyre.",
            id="contrastive-predicate",
        ),
        pytest.param(
            "Isha did not hesitate and wiped mud off the tyre.",
            id="coordinated-positive-predicate",
        ),
        pytest.param(
            "Isha did not hesitate, then wiped mud off the tyre.",
            id="sequential-predicate",
        ),
        pytest.param(
            "A tyre is rubber, not metal: isha wiped mud off the tyre.",
            id="lowercase-subject-after-colon",
        ),
    ),
)
def test_positive_cleaning_proposition_after_negative_clause_is_promoted(answer):
    activity = _review_activity()

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(activity, answer),
        answer=answer,
    )

    criteria = {criterion["id"]: criterion for criterion in decision["criteria"]}
    assert criteria[REQUIREMENT_2] == {
        "id": REQUIREMENT_2,
        "met": True,
        "quality": 1.0,
        "evidence_quote": "wiped mud",
    }
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []
    assert decision["correct"] is True


def test_tyre_answer_without_cleaning_claim_still_fails_requirement_two():
    activity = _review_activity()
    answer = "A tyre is the rubber wheel part with tread after the rain."

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _first_pass_evaluation(activity, answer),
        answer=answer,
    )

    criteria = {criterion["id"]: criterion for criterion in decision["criteria"]}
    assert criteria[REQUIREMENT_2]["quality"] == 0.7
    assert REQUIREMENT_2 in decision["missing_criteria"]
    assert decision["blockers"] == ["semantic_required_claim_missing"]
    assert decision["correct"] is False
