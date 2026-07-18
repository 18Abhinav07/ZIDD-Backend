from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from scripts.build_school_deep_chapter import OpenActivitySpec, load_manifest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_ROOT = (
    ROOT / "app/content/school_rebuild_manifests/english/class_2"
)
RUNTIME_ROOT = ROOT / "app/content/school_rebuild_chapters/english/class_2"
CHAPTER_IDS = tuple(f"eng_c2_ch{chapter_no:02d}" for chapter_no in range(1, 8))
BANNED_LEARNER_COPY = (
    "check every requested part",
    "evidence target",
    "rubric criterion",
    "concept slot",
    "model answer",
)


ATOMIC_CONTRACTS = {
    "eng_c2_ch01": {
        "bicycle_detail_detectives:transfer:1": (
            "What does the mechanic fix, and when?",
            ("repair", "time"),
        ),
        "bicycle_detail_detectives:transfer:2": (
            "State Sara's helmet colour, the item in her basket, and the basket colour.",
            ("helmet_colour", "basket_item", "basket_colour"),
        ),
        "bicycle_detail_detectives:transfer:4": (
            "Report the helmet colour, borrowing time, and return place.",
            ("helmet_colour", "borrowing_time", "return_place"),
        ),
        "bicycle_detail_detectives:review:3": (
            "Tell which rack and place belong to each group.",
            ("visitor_rack", "visitor_place", "staff_rack", "staff_place"),
        ),
        "bicycle_safe_order:transfer:1": (
            "Write the preparation steps from first to last.",
            ("bottle", "strap", "bicycle"),
        ),
        "bicycle_safe_order:review:2": (
            "Retell the riders' actions in the correct order.",
            ("stop", "wait", "move"),
        ),
        "bicycle_word_classes:transfer:2": (
            "Write one new sentence using bell, rings, and cheerful.",
            ("noun", "verb", "adjective"),
        ),
        "eng_c2_ch01:assessment:06": (
            "State when Esha checks each part.",
            ("front_light", "bell"),
        ),
    },
    "eng_c2_ch02": {
        "game_scene_details:independent:1": (
            "When does each round begin?",
            ("first_round", "second_round"),
        ),
        "game_scene_details:independent:2": (
            "State what each child brings.",
            ("mira", "dev", "ali"),
        ),
        "game_scene_details:independent:3": (
            "Describe the colour, number, and place of both hoop groups.",
            (
                "blue_colour",
                "blue_number",
                "blue_place",
                "green_colour",
                "green_number",
                "green_place",
            ),
        ),
        "game_scene_details:transfer:4": (
            "Report the number, material, and time for each group.",
            (
                "group_a_number",
                "group_a_material",
                "group_a_time",
                "group_b_number",
                "group_b_material",
                "group_b_time",
            ),
        ),
        "game_scene_details:review:3": (
            "Tell the shape and storage place for both teams.",
            ("blue_shape", "blue_place", "yellow_shape", "yellow_place"),
        ),
        "game_scene_details:review:4": (
            "State who carries each item, how many, and where.",
            (
                "neel",
                "neel_item",
                "neel_count",
                "neel_place",
                "sia",
                "sia_item",
                "sia_count",
                "sia_place",
            ),
        ),
        "game_problem_sequence:independent:2": (
            "Write the three ending actions in sequence.",
            ("freeze", "count", "clear"),
        ),
        "game_problem_sequence:transfer:2": (
            "How does Vivek solve the score problem?",
            ("notice", "check", "return"),
        ),
        "game_opposite_words:transfer:4": (
            "Name the opposite pair and connect each word to its bowl.",
            ("pair", "full_bowl", "empty_bowl"),
        ),
    },
    "eng_c2_ch03": {
        "animal_clue_comprehension:independent:2": (
            "What can the kitten reach, and what can it not reach?",
            ("reachable", "unreachable"),
        ),
        "animal_clue_comprehension:transfer:4": (
            "State the snail's place and the two ends of its trail.",
            ("place", "trail_start", "trail_end"),
        ),
        "animal_clue_comprehension:review:2": (
            "What action follows the parent's return?",
            ("action",),
        ),
        "animal_clue_comprehension:review:3": (
            "Name both things the squirrel carries and where it climbs.",
            ("peanut", "leaves", "place"),
        ),
        "animal_clue_comprehension:review:4": (
            "Give the puppy's two markings and exact waiting place.",
            ("brown", "white_ear", "place"),
        ),
        "animal_action_sequence:review:2": (
            "Retell the cat's settling actions.",
            ("circle", "fold", "close"),
        ),
        "animal_complete_sentences:masterclass:2": (
            "Write one complete instruction sentence from the card.",
            ("bend", "rise", "spread"),
        ),
        "eng_c2_ch03:assessment:12": (
            "Write Arun's care steps from first to last.",
            ("empty", "rinse", "fill"),
        ),
    },
    "eng_c2_ch04": {
        "sense_clue_comprehension:independent:1": (
            "Describe how the two cards differ.",
            ("raised_card", "star_card"),
        ),
        "sense_clue_comprehension:independent:3": (
            "State the texture and box for both objects.",
            ("scarf_texture", "scarf_box", "mat_texture", "mat_box"),
        ),
        "sense_clue_comprehension:transfer:4": (
            "Name the sound, its cause, and the source of the smell.",
            ("sound", "cause", "smell_source"),
        ),
        "sense_clue_comprehension:review:4": (
            "State both sounds and where each begins.",
            ("hum", "hum_source", "beep", "beep_source"),
        ),
        "sense_evidence_sequence:transfer:1": (
            "Give the labelling steps from first to last.",
            ("clean", "print", "raised_shape"),
        ),
        "eng_c2_ch04:assessment:06": (
            "Describe both card textures.",
            ("north", "south"),
        ),
        "eng_c2_ch04:assessment:22": (
            "Write one complete sentence describing both labels.",
            ("printed_label", "raised_label"),
        ),
    },
    "eng_c2_ch05": {
        "transport_detail_comprehension:independent:1": (
            "State the outward vehicle and destination, then the return vehicle and day.",
            ("outward_vehicle", "destination", "return_vehicle", "day"),
        ),
        "transport_detail_comprehension:independent:3": (
            "State the destination and time for both vehicles.",
            (
                "ferry_destination",
                "ferry_time",
                "bus_destination",
                "bus_time",
            ),
        ),
        "transport_detail_comprehension:transfer:4": (
            "Report the bus, seat, departure time, and destination.",
            ("bus", "seat", "departure", "destination"),
        ),
        "transport_detail_comprehension:review:4": (
            "Give the train name, track, leaving time, and return time.",
            ("train", "track", "leaving", "returning"),
        ),
        "journey_event_sequence:independent:1": (
            "Retell Sia's departure steps in order.",
            ("lock", "walk", "board"),
        ),
        "journey_event_sequence:review:1": (
            "Retell the return preparation.",
            ("gather", "count", "board"),
        ),
        "journey_event_sequence:review:2": (
            "Write the rider's route sequence.",
            ("follow", "turn", "return"),
        ),
        "journey_complete_sentences:review:1": (
            "Write both sentences using train and bus.",
            ("outward", "return"),
        ),
        "journey_complete_sentences:revision_level_2:4": (
            "Write the arrival and return as two complete sentences.",
            ("arrival", "return"),
        ),
        "eng_c2_ch05:assessment:23": (
            "Name your vehicle, explain how it fits the narrow lane, and tell how it protects the books.",
            ("vehicle", "lane_fit", "book_protection"),
        ),
    },
    "eng_c2_ch06": {
        "route_detail_comprehension:independent:1": (
            "State the two landmarks in order.",
            ("first_landmark", "second_landmark"),
        ),
        "route_detail_comprehension:review:4": (
            "State the gate and time for each class.",
            ("class2_gate", "class2_time", "class3_gate", "class3_time"),
        ),
    },
    "eng_c2_ch07": {
        "town_nested_details:review:3": (
            "State the floor and landmark for both book groups.",
            (
                "picture_floor",
                "picture_landmark",
                "nature_floor",
                "nature_landmark",
            ),
        ),
        "town_nested_details:review:4": (
            "Give the stall, food, colour, and container for each seller.",
            (
                "seller1_stall",
                "seller1_food",
                "seller1_colour",
                "seller1_container",
                "seller2_stall",
                "seller2_food",
                "seller2_colour",
                "seller2_container",
            ),
        ),
        "town_route_sequence:independent:1": (
            "Retell the town route in order.",
            ("start", "theatre", "turn", "end"),
        ),
    },
}


SUPPORTED_MODEL_CONTRACTS = {
    ("eng_c2_ch01", "bicycle_detail_detectives:transfer:4"): (
        "The library cycle log says: Tara borrows the blue helmet at two o'clock and returns it at four o'clock beside the reading room.",
        "Tara borrows the blue helmet at two o'clock and returns it beside the reading room.",
    ),
    ("eng_c2_ch02", "game_sentence_order:independent:4"): (
        "Word cards: our team / carefully / stacks / six cups.",
        "Our team carefully stacks six cups.",
    ),
    ("eng_c2_ch03", "animal_sentence_order:independent:4"): (
        "Word cards: a green frog / quickly / catches / one fly.",
        "A green frog quickly catches one fly.",
    ),
    ("eng_c2_ch05", "transport_detail_comprehension:transfer:4"): (
        "Nikhil's ticket says Bus 14, Seat 6, departure at eight fifteen, and arrival at River Market at nine o'clock.",
        "Nikhil has Seat 6 on Bus 14, which leaves at eight fifteen for River Market.",
    ),
    ("eng_c2_ch05", "journey_complete_sentences:review:1"): (
        "The class travels from school to the science centre by train and returns to school by bus.",
        "The class travels to the science centre by train. It returns to school by bus.",
    ),
    ("eng_c2_ch05", "journey_complete_sentences:revision_level_2:4"): (
        "Travel card facts: take the green bus to Tree Park Gate at ten; return on the same bus from Gate B at four.",
        "Take the green bus to Tree Park Gate at ten. Return on the same bus from Gate B at four.",
    ),
    ("eng_c2_ch06", "route_sentence_order:independent:4"): (
        "Word cards: our path / carefully / crosses / the busy lane.",
        "Our path carefully crosses the busy lane.",
    ),
}


def _manifest(chapter_id: str):
    return load_manifest(MANIFEST_ROOT / f"{chapter_id}.py")


def _runtime(chapter_id: str) -> dict:
    return json.loads(
        (RUNTIME_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )


def _level_activities(level: object) -> list[object]:
    return [
        level.co_construct,
        *level.guided_variants,
        *level.independent_variants,
        *level.transfer_variants,
        *level.review_variants,
        *level.support_checks.activities().values(),
    ]


def _manifest_activity(manifest: object, activity_id: str) -> OpenActivitySpec:
    matches = [
        activity
        for level in manifest.levels
        for activity in _level_activities(level)
        if activity.activity_id == activity_id
    ]
    matches.extend(
        activity
        for activity in manifest.chapter_assessment.items
        if activity.activity_id == activity_id
    )
    assert len(matches) == 1, (activity_id, len(matches))
    assert isinstance(matches[0], OpenActivitySpec)
    return matches[0]


def _runtime_activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
            yield from activities
        yield from level["checks"].values()
    yield from payload["chapter_assessment"]["items"]


def _runtime_matches(payload: dict, activity: OpenActivitySpec) -> list[dict]:
    return [
        candidate
        for candidate in _runtime_activities(payload)
        if candidate.get("variant_id") == activity.activity_id
        or candidate.get("item_id") == activity.activity_id
        or (
            candidate.get("prompt") == activity.prompt
            and candidate.get("passage") == activity.passage
        )
    ]


def _child_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _card_parts(passage: str) -> list[str]:
    _, raw_parts = passage.split(":", 1)
    delimiter = ";" if ";" in raw_parts else "/"
    return [part.strip().rstrip(".") for part in raw_parts.split(delimiter)]


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


@pytest.mark.parametrize(
    ("chapter_id", "activity_id", "expected_prompt", "expected_suffixes"),
    [
        (chapter_id, activity_id, prompt, suffixes)
        for chapter_id, contracts in ATOMIC_CONTRACTS.items()
        for activity_id, (prompt, suffixes) in contracts.items()
    ],
)
def test_explicit_multipart_prompts_have_one_authored_slot_per_atomic_part(
    chapter_id: str,
    activity_id: str,
    expected_prompt: str,
    expected_suffixes: tuple[str, ...],
) -> None:
    activity = _manifest_activity(_manifest(chapter_id), activity_id)
    expected_ids = [f"{activity_id}:{suffix}" for suffix in expected_suffixes]

    assert activity.prompt == expected_prompt
    assert [criterion.id for criterion in activity.rubric_criteria] == expected_ids
    assert [slot.id for slot in activity.concept_slots] == expected_ids
    assert _child_guidance(len(expected_ids)) in activity.teaching_block.casefold()
    assert activity.model_answer.casefold() not in activity.teaching_block.casefold()

    runtime_matches = _runtime_matches(_runtime(chapter_id), activity)
    assert runtime_matches
    for runtime_activity in runtime_matches:
        assert [
            criterion["id"] for criterion in runtime_activity["rubric_criteria"]
        ] == expected_ids
        assert [slot["id"] for slot in runtime_activity["concept_slots"]] == expected_ids
        if "teaching_block" in runtime_activity:
            assert _child_guidance(len(expected_ids)) in (
                runtime_activity["teaching_block"].casefold()
            )


@pytest.mark.parametrize("chapter_id", ("eng_c2_ch02", "eng_c2_ch03", "eng_c2_ch06"))
def test_sentence_order_tasks_score_every_visible_card_once(chapter_id: str) -> None:
    manifest = _manifest(chapter_id)
    levels = [level for level in manifest.levels if level.level_id.endswith("sentence_order")]
    assert len(levels) == 1
    activities = [
        activity
        for activity in _level_activities(levels[0])
        if isinstance(activity, OpenActivitySpec)
    ]
    assert len(activities) == 12

    for activity in activities:
        parts = _card_parts(activity.passage)
        expected_ids = [
            f"{activity.activity_id}:card_{index}"
            for index in range(1, len(parts) + 1)
        ]
        assert [criterion.id for criterion in activity.rubric_criteria] == expected_ids
        assert [slot.id for slot in activity.concept_slots] == expected_ids
        assert sorted(
            _normalized(slot.any_of[0]) for slot in activity.concept_slots
        ) == sorted(_normalized(part) for part in parts)
        assert activity.ordered_concept_slot_ids == expected_ids
        assert _child_guidance(len(parts)) in activity.teaching_block.casefold()

        runtime_matches = _runtime_matches(_runtime(chapter_id), activity)
        assert runtime_matches
        for runtime_activity in runtime_matches:
            assert [
                criterion["id"]
                for criterion in runtime_activity["rubric_criteria"]
            ] == expected_ids
            assert [
                slot["id"] for slot in runtime_activity["concept_slots"]
            ] == expected_ids


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_all_open_directions_are_child_facing_count_aware_and_construct_specific(
    chapter_id: str,
) -> None:
    manifest = _manifest(chapter_id)
    open_count = 0
    level_focus_by_skill = [
        (tuple(level.skill_ids), level.focus.casefold()) for level in manifest.levels
    ]

    for level in manifest.levels:
        for activity in _level_activities(level):
            if not isinstance(activity, OpenActivitySpec):
                continue
            open_count += 1
            direction = activity.teaching_block.casefold()
            assert direction
            assert f"to {level.focus.casefold()}" in direction
            assert _child_guidance(len(activity.rubric_criteria)) in direction
            assert activity.model_answer.casefold() not in direction
            assert not any(fragment in direction for fragment in BANNED_LEARNER_COPY)

    for activity in manifest.chapter_assessment.items:
        if not isinstance(activity, OpenActivitySpec):
            continue
        open_count += 1
        direction = activity.teaching_block.casefold()
        matching_focuses = [
            focus
            for skills, focus in level_focus_by_skill
            if set(activity.skill_ids).issubset(skills)
        ]
        assert matching_focuses
        assert any(f"to {focus}" in direction for focus in matching_focuses)
        assert _child_guidance(len(activity.rubric_criteria)) in direction
        assert activity.model_answer.casefold() not in direction
        assert not any(fragment in direction for fragment in BANNED_LEARNER_COPY)

    assert open_count >= 90

    runtime_open = [
        activity
        for activity in _runtime_activities(_runtime(chapter_id))
        if activity.get("grading_mode") == "strict_open_rubric"
        and activity.get("teaching_block")
    ]
    assert runtime_open
    for activity in runtime_open:
        direction = activity["teaching_block"].casefold()
        assert direction
        assert _child_guidance(len(activity["rubric_criteria"])) in direction
        assert activity["model_answer"].casefold() not in direction
        assert not any(fragment in direction for fragment in BANNED_LEARNER_COPY)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_task_directions_are_not_exact_copies_within_a_chapter(chapter_id: str) -> None:
    manifest = _manifest(chapter_id)
    directions = [
        activity.teaching_block.strip().casefold()
        for level in manifest.levels
        for activity in _level_activities(level)
    ]
    directions.extend(
        activity.teaching_block.strip().casefold()
        for activity in manifest.chapter_assessment.items
    )
    duplicates = {
        direction: count
        for direction, count in Counter(directions).items()
        if count > 1
    }
    assert duplicates == {}


@pytest.mark.parametrize(
    ("chapter_id", "activity_id", "expected_passage", "expected_model"),
    [
        (chapter_id, activity_id, passage, model)
        for (chapter_id, activity_id), (passage, model) in SUPPORTED_MODEL_CONTRACTS.items()
    ],
)
def test_model_answers_do_not_require_unasked_or_model_only_details(
    chapter_id: str,
    activity_id: str,
    expected_passage: str,
    expected_model: str,
) -> None:
    activity = _manifest_activity(_manifest(chapter_id), activity_id)
    assert activity.passage == expected_passage
    assert activity.model_answer == expected_model
    assert activity.model_answer.casefold() not in activity.teaching_block.casefold()


def test_contract_inventory_is_bounded_to_confirmed_class2_defects() -> None:
    assert sum(len(contracts) for contracts in ATOMIC_CONTRACTS.values()) == 47
    assert set(ATOMIC_CONTRACTS) == set(CHAPTER_IDS)
    assert len(SUPPORTED_MODEL_CONTRACTS) == 7
    assert not re.search(r"eng_c(?!2)_", json.dumps(ATOMIC_CONTRACTS))
