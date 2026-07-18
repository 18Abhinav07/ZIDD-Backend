from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.content.school_rebuild_schema import LiveSchoolChapter
from scripts.build_school_deep_chapter import (
    OpenActivitySpec,
    build_deep_chapter,
    load_manifest,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_ROOT = (
    ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_5"
)
RUNTIME_ROOT = (
    ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)

EXPECTED_SLOT_SUFFIXES = {
    "eng_c5_ch03": {
        "eng_c5_ch03:assessment:02": ("shape", "boundary"),
        "eng_c5_ch03:assessment:04": ("emphasis", "rhyme"),
        "eng_c5_ch03:assessment:06": ("change", "response"),
        "eng_c5_ch03:assessment:08": ("he", "them", "she"),
        "eng_c5_ch03:assessment:10": ("meaning", "contrast"),
        "eng_c5_ch03:assessment:12": ("pair", "change"),
        "eng_c5_ch03:assessment:14": ("compound", "bases", "definition"),
        "eng_c5_ch03:assessment:16": ("action_use", "naming_use"),
        "eng_c5_ch03:assessment:18": (
            "soil",
            "seeds",
            "water",
            "label",
            "reason",
        ),
        "eng_c5_ch03:assessment:19": ("correction", "after", "before"),
        "eng_c5_ch03:assessment:20": ("swap", "corrected_order"),
        "eng_c5_ch03:assessment:22": ("boarded", "saw", "reached"),
        "eng_c5_ch03:assessment:23": (
            "opening",
            "movement",
            "sensory",
            "tense",
            "arrival",
            "reflection",
        ),
        "eng_c5_ch03:assessment:24": (
            "problem",
            "resolution",
            "sensory",
            "tense",
            "arrival",
            "lesson",
        ),
        "eng_c5_ch03:assessment:25": (
            "similarity",
            "duration",
            "function",
        ),
        "eng_c5_ch03:assessment:26": (
            "shared_effect",
            "origin",
            "movement",
        ),
        "eng_c5_ch03:assessment:28": ("source", "facts", "limit"),
        "eng_c5_ch03:assessment:29": ("image", "boundary"),
        "rainbow_natural_and_built:independent:1": (
            "builder",
            "crossing",
            "inspection",
            "limit",
        ),
        "rainbow_natural_and_built:independent:3": (
            "source",
            "form",
            "setting",
            "movement",
            "capacity",
        ),
        "rainbow_natural_and_built:transfer:1": (
            "source",
            "form",
            "setting",
            "movement",
            "restraint",
        ),
        "rainbow_natural_and_built:review:2": (
            "similarity",
            "origin",
            "control",
        ),
        "rainbow_natural_and_built:review:4": (
            "similarity",
            "material",
            "reuse",
            "limit",
        ),
        "rainbow_journey_paragraph:transfer:4": (
            "departure",
            "obstacle",
            "route",
            "arrival",
            "tense",
            "sensory",
            "reflection",
        ),
        "rainbow_journey_paragraph:review:3": (
            "problem",
            "repair",
            "resumed",
            "arrival",
            "sensory",
            "tense",
            "reflection",
        ),
    },
    "eng_c5_ch04": {
        "wise_parrot_freedom_reason:independent:3": ("timing", "risk"),
        "wise_parrot_bird_sanctuary:independent:1": (
            "main",
            "action_one",
            "action_two",
        ),
        "wise_parrot_bird_sanctuary:independent:4": (
            "habitat",
            "trail",
            "loudspeaker",
            "limit",
        ),
        "wise_parrot_bird_sanctuary:transfer:3": (
            "litter",
            "branches",
            "dogs",
        ),
        "wise_parrot_bird_sanctuary:transfer:4": (
            "island",
            "boundary",
            "counting",
            "limit",
        ),
        "wise_parrot_bird_sanctuary:review:2": (
            "pond",
            "reeds",
            "result",
            "caution",
        ),
        "wise_parrot_bird_sanctuary:review:3": (
            "access",
            "nesting",
            "limit",
        ),
        "wise_parrot_bird_sanctuary:review:4": (
            "cavity",
            "food",
            "limit",
        ),
        "wise_parrot_bird_care_procedure:guided:4": (
            "clean",
            "adult",
            "place",
            "check",
        ),
        "wise_parrot_bird_care_procedure:review:2": (
            "tray",
            "water",
            "brush",
            "clean",
            "rinse",
            "refill",
            "shade",
        ),
        "wise_parrot_bird_care_procedure:review:3": (
            "placement",
            "edge",
            "cleaning",
            "refill",
            "observation",
            "soap",
        ),
        "wise_parrot_bird_care_procedure:review:4": (
            "setup",
            "watch",
            "tally",
            "evidence",
            "weather",
            "unchanged",
            "handoff",
        ),
        "eng_c5_ch04_assess_a15": (
            "adult",
            "arrow",
            "eraser",
            "outdoors",
            "record",
        ),
        "eng_c5_ch04_assess_b15": (
            "rinse",
            "pebbles",
            "sprig",
            "mark",
            "shade",
            "record",
        ),
    },
    "eng_c5_ch05": {
        "frog_life_stage_and_words:independent:2": (
            "meaning",
            "tail",
            "legs",
        ),
        "frog_life_stage_and_words:independent:3": (
            "eggs",
            "tadpoles",
            "legs",
            "froglets",
            "boundary",
        ),
        "frog_life_stage_and_words:transfer:4": (
            "eggs",
            "larva",
            "pupa",
            "adult",
            "meaning",
            "limit",
        ),
        "frog_comparison:transfer:4": (
            "similarity",
            "feeding",
            "habitat_use",
        ),
        "frog_friendly_reply:transfer:4": (
            "action",
            "no_touch",
            "reason",
            "question",
            "close",
        ),
        "frog_friendly_reply:review:3": (
            "job",
            "reason",
            "question",
            "close",
        ),
        "frog_friendly_reply:review:4": (
            "stripe",
            "place",
            "time",
            "limit",
            "next_step",
            "question",
            "close",
        ),
        "frog_instruction_and_research:guided:2": (
            "setup",
            "frog",
            "labels",
            "sentence",
        ),
        "frog_instruction_and_research:transfer:4": (
            "label",
            "fill",
            "compare",
            "record",
            "safety",
            "return",
        ),
        "frog_instruction_and_research:review:3": (
            "fixed",
            "times",
            "labels",
            "measure",
            "limit",
        ),
        "frog_instruction_and_research:review:4": (
            "animal",
            "cards",
            "titles",
            "facts",
            "disagreement",
            "approval",
            "report",
        ),
        "eng_c5_ch05_assess_a12": (
            "greeting",
            "answer",
            "detail",
            "question",
            "closing",
            "name",
        ),
        "eng_c5_ch05_assess_a13": (
            "cut",
            "funnel",
            "marks",
            "placement",
            "measure",
            "record",
            "reason",
        ),
        "eng_c5_ch05_assess_b12": (
            "greeting",
            "answer",
            "detail",
            "question",
            "closing",
            "name",
        ),
        "eng_c5_ch05_assess_b13": (
            "fold",
            "dampen",
            "bean",
            "pouch",
            "seal",
            "date",
            "observe",
        ),
    },
}


def _manifest(chapter_id: str):
    return load_manifest(MANIFEST_ROOT / f"{chapter_id}.py")


def _activities(manifest):
    for level in manifest.levels:
        yield level.co_construct
        yield from level.guided_variants
        yield from level.independent_variants
        yield from level.transfer_variants
        yield from level.review_variants
        yield from level.support_checks.activities().values()
    yield from manifest.chapter_assessment.items


def _activity_index(chapter_id: str):
    return {
        activity.activity_id: activity
        for activity in _activities(_manifest(chapter_id))
    }


def _guidance_for(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


@pytest.mark.parametrize("chapter_id", EXPECTED_SLOT_SUFFIXES)
def test_explicit_prompt_parts_have_independent_evidence_slots(chapter_id: str):
    activities = _activity_index(chapter_id)

    for activity_id, suffixes in EXPECTED_SLOT_SUFFIXES[chapter_id].items():
        activity = activities[activity_id]
        assert isinstance(activity, OpenActivitySpec)
        expected_ids = [f"{activity_id}:{suffix}" for suffix in suffixes]

        assert [item.id for item in activity.rubric_criteria] == expected_ids
        assert [item.id for item in activity.concept_slots] == expected_ids
        assert _guidance_for(len(expected_ids)) in activity.teaching_block.casefold()


@pytest.mark.parametrize("chapter_id", EXPECTED_SLOT_SUFFIXES)
def test_every_repaired_slot_has_distinct_model_answer_authority(chapter_id: str):
    activities = _activity_index(chapter_id)

    for activity_id in EXPECTED_SLOT_SUFFIXES[chapter_id]:
        activity = activities[activity_id]
        assert isinstance(activity, OpenActivitySpec)
        model_answer = " ".join(activity.model_answer.casefold().split())
        seen_aliases: set[str] = set()
        for slot in activity.concept_slots:
            matching_aliases = {
                " ".join(alias.casefold().split())
                for alias in slot.any_of
                if " ".join(alias.casefold().split()) in model_answer
            }
            assert matching_aliases, (activity_id, slot.id)
            assert seen_aliases.isdisjoint(matching_aliases), (activity_id, slot.id)
            seen_aliases.update(matching_aliases)


def test_chapter_four_explains_the_silent_signal_inside_the_visible_passage():
    activity = _activity_index("eng_c5_ch04")[
        "wise_parrot_story_sequence:guided:4"
    ]

    assert "forest bird became still" in activity.passage.casefold()
    assert "copied that action" in activity.passage.casefold()
    assert activity.accepted_answers == [
        "how the bird understood and used the silent signal"
    ]


def test_review_tasks_add_new_reasoning_instead_of_repeating_prior_templates():
    chapter_four = _activity_index("eng_c5_ch04")[
        "wise_parrot_bird_sanctuary:review:3"
    ]
    chapter_five = _activity_index("eng_c5_ch05")[
        "frog_friendly_reply:review:4"
    ]

    assert "visitor notice" in chapter_four.prompt.casefold()
    assert "missing outcome evidence" in chapter_four.prompt.casefold()
    assert "cannot identify the species" in chapter_five.prompt.casefold()
    assert "safe verification step" in chapter_five.prompt.casefold()


def test_repaired_copy_does_not_expose_internal_reference_evidence_scaffolding():
    for chapter_id in EXPECTED_SLOT_SUFFIXES:
        activities = _activity_index(chapter_id)
        for activity_id in EXPECTED_SLOT_SUFFIXES[chapter_id]:
            activity = activities[activity_id]
            assert isinstance(activity, OpenActivitySpec)
            assert not re.search(
                r"\breference evidence states\s*:",
                activity.model_answer,
                flags=re.IGNORECASE,
            ), activity_id


@pytest.mark.parametrize("chapter_id", EXPECTED_SLOT_SUFFIXES)
def test_repaired_manifest_and_owned_runtime_have_no_semantic_drift(
    chapter_id: str,
):
    built = LiveSchoolChapter.model_validate(
        build_deep_chapter(None, _manifest(chapter_id))
    )
    runtime = LiveSchoolChapter.model_validate(
        json.loads(
            (RUNTIME_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
        )
    )

    assert built.runtime_dict() == runtime.runtime_dict()
    assert built.runtime_sha256 == runtime.runtime_sha256
