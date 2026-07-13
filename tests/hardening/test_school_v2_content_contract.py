import pytest

from app.content.school_v2_schema import (
    ContentGateError,
    SchoolV2AssessmentItem,
    SchoolV2ChapterBlueprint,
    SchoolV2LessonOutcome,
    SkillTaxonomy,
    SkillTaxonomyEntry,
    validate_pilot_content_gate,
)


def _taxonomy() -> SkillTaxonomy:
    return SkillTaxonomy(
        entries=[
            SkillTaxonomyEntry(
                skill_id="eng.c3.vocab.context",
                subject_id="english",
                class_min=3,
                class_max=5,
                name="Use context for vocabulary",
                description="Infer a word meaning from the sentence or passage context.",
            ),
            SkillTaxonomyEntry(
                skill_id="eng.c3.comprehension.event",
                subject_id="english",
                class_min=3,
                class_max=5,
                name="Track events",
                description="Identify important events in a chapter.",
            ),
            SkillTaxonomyEntry(
                skill_id="eng.c3.answer.reason",
                subject_id="english",
                class_min=3,
                class_max=5,
                name="Give a reason",
                description="Answer why/how questions with a reason.",
            ),
        ]
    )


def _items(prefix: str, skill_id: str) -> list[SchoolV2AssessmentItem]:
    return [
        SchoolV2AssessmentItem(
            item_id=f"{prefix}_guided",
            stage="guided",
            item_type="short_answer",
            prompt="What clue helps you understand the word?",
            skill_ids=[skill_id],
        ),
        SchoolV2AssessmentItem(
            item_id=f"{prefix}_bridge",
            stage="bridge",
            item_type="fill_blank",
            prompt="The word means __.",
            skill_ids=[skill_id],
            answer_key="kind",
        ),
        SchoolV2AssessmentItem(
            item_id=f"{prefix}_independent",
            stage="independent_check",
            item_type="short_answer",
            prompt="Answer in your own words.",
            skill_ids=[skill_id],
        ),
        SchoolV2AssessmentItem(
            item_id=f"{prefix}_transfer",
            stage="transfer_check",
            item_type="short_answer",
            prompt="Use the same idea in a new sentence.",
            skill_ids=[skill_id],
        ),
    ]


def _pilot_blueprint() -> SchoolV2ChapterBlueprint:
    return SchoolV2ChapterBlueprint(
        subject_id="english",
        class_no=3,
        book_title="Pilot English",
        curriculum_version="pilot-v1",
        chapter_id="eng_c3_pilot_01",
        chapter_title="Pilot Chapter",
        source_url="https://example.com/source-map",
        outcomes=[
            SchoolV2LessonOutcome(
                outcome_id="outcome_vocab",
                title="Use clues for words",
                skill_ids=["eng.c3.vocab.context"],
                items=_items("vocab", "eng.c3.vocab.context"),
            ),
            SchoolV2LessonOutcome(
                outcome_id="outcome_events",
                title="Track events",
                skill_ids=["eng.c3.comprehension.event"],
                items=_items("events", "eng.c3.comprehension.event"),
            ),
            SchoolV2LessonOutcome(
                outcome_id="outcome_reason",
                title="Give a reason",
                skill_ids=["eng.c3.answer.reason"],
                items=_items("reason", "eng.c3.answer.reason"),
            ),
        ],
    )


def test_chapter_blueprint_must_reference_shared_taxonomy_skill_ids():
    blueprint = _pilot_blueprint()
    blueprint.outcomes[0].skill_ids = ["eng.c3.invented.skill"]

    with pytest.raises(ContentGateError, match="unknown_skill_id"):
        validate_pilot_content_gate(blueprint, _taxonomy())


def test_pilot_gate_accepts_small_slice_that_exercises_every_learning_state():
    result = validate_pilot_content_gate(_pilot_blueprint(), _taxonomy())

    assert result.outcome_count == 3
    assert result.item_count == 12
    assert result.required_stages == {
        "guided",
        "bridge",
        "independent_check",
        "transfer_check",
    }


def test_pilot_gate_fails_when_slice_cannot_exercise_transfer():
    blueprint = _pilot_blueprint()
    blueprint.outcomes[0].items = [
        item for item in blueprint.outcomes[0].items if item.stage != "transfer_check"
    ]

    with pytest.raises(ContentGateError, match="missing_stage"):
        validate_pilot_content_gate(blueprint, _taxonomy())


def test_taxonomy_rejects_duplicate_skill_ids():
    entry = _taxonomy().entries[0]

    with pytest.raises(ValueError, match="duplicate_skill_id"):
        SkillTaxonomy(entries=[entry, entry])
