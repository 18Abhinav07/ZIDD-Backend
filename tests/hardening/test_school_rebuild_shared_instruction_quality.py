from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_school_deep_chapter import (
    ChoiceActivitySpec,
    OpenActivitySpec,
    load_manifest,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_ROOT = ROOT / "app/content/school_rebuild_manifests/english"
RUNTIME_ROOT = ROOT / "app/content/school_rebuild_chapters/english"
GENERIC_DIRECTION = "check every requested part"
BANNED_DIRECTION_FRAGMENTS = (
    GENERIC_DIRECTION,
    "evidence target",
)

SOURCE_BUILDERS = (
    MANIFEST_ROOT / "class_4/eng_c4_ch01.py",
    MANIFEST_ROOT / "class_4/eng_c4_ch07.py",
    MANIFEST_ROOT / "class_5/eng_c5_ch02.py",
)
CHAPTER_IDS = (
    *(f"eng_c4_ch{chapter_no:02d}" for chapter_no in range(1, 13)),
    *(f"eng_c5_ch{chapter_no:02d}" for chapter_no in range(2, 9)),
)
CLASS4_EARLY_TARGET_COUNTS = {
    f"eng_c4_ch{chapter_no:02d}": 119 for chapter_no in range(1, 7)
}
CLASS4_LATE_TARGET_COUNTS = {
    "eng_c4_ch07": 8,
    "eng_c4_ch08": 8,
    "eng_c4_ch09": 9,
    "eng_c4_ch10": 7,
    "eng_c4_ch11": 7,
    "eng_c4_ch12": 7,
}
CLASS5_TARGET_COUNTS = {
    "eng_c5_ch02": 135,
    "eng_c5_ch03": 129,
    "eng_c5_ch04": 20,
    "eng_c5_ch05": 24,
    "eng_c5_ch06": 91,
    "eng_c5_ch07": 91,
    "eng_c5_ch08": 117,
}
CLASS5_CH04_TRANSFER_LEVEL_IDS = {
    "wise_parrot_present_perfect",
    "wise_parrot_bird_sanctuary",
    "wise_parrot_story_continuation",
    "wise_parrot_bird_care_procedure",
}
CH2_EXPLICIT_PARTS = {
    "scooter_event_sequence:independent:2": (
        "State the main event and two details that build it.",
        ("main", "wind", "discovery"),
    ),
    "scooter_event_sequence:independent:4": (
        "Write the central event in one sentence, then name the first and final locations.",
        ("main", "start", "end"),
    ),
    "scooter_event_sequence:transfer:2": (
        "Put the three events in order and state what links them.",
        ("loosen", "carry", "stop", "link"),
    ),
    "scooter_event_sequence:review:1": (
        "Give the three events in order and one sentence stating the main event.",
        ("fall", "trolley", "stop", "main"),
    ),
    "scooter_event_sequence:review:4": (
        "Separate the cause, movement, and outcome, then express the central event in your own words.",
        ("cause", "movement", "outcome", "main"),
    ),
    "scooter_event_sequence:review:3": (
        "Explain the packet's route by naming what moved it at each stage, then state the main event.",
        ("fall", "ride", "arrival", "main"),
    ),
    "scooter_event_sequence:bridge:1": (
        "Name the start, middle, and ending in order.",
        ("start", "middle", "end"),
    ),
    "scooter_event_sequence:revision_level_3:5": (
        "State the main event, then support it with the cause and final place.",
        ("main", "cause", "final"),
    ),
    "scooter_dialogue_and_speaker:independent:1": (
        "Identify both speakers, the listener in the first line, and Ravi's contribution.",
        ("first_speaker", "second_speaker", "listener", "contribution"),
    ),
    "scooter_dialogue_and_speaker:guided:1": (
        "Name each speaker and explain how the clerk's reply responds to Jia.",
        ("first_speaker", "second_speaker", "response"),
    ),
    "scooter_dialogue_and_speaker:guided:4": (
        "Write a three-turn exchange that reaches that plan without changing speakers mid-line.",
        ("report", "response", "plan"),
    ),
    "scooter_dialogue_and_speaker:independent:2": (
        "Write a four-line dialogue in which Priya asks, the guard advises, and Priya confirms the plan.",
        ("question", "advice", "confirmation", "instruction"),
    ),
    "scooter_dialogue_and_speaker:independent:3": (
        "Explain the purpose of each line and how the reply addresses the warning.",
        ("warning", "alternative", "link"),
    ),
    "scooter_dialogue_and_speaker:independent:4": (
        "Turn the information into a three-speaker exchange with correct question marks and a logical unanswered final question.",
        ("first_question", "answer", "final_question"),
    ),
    "scooter_dialogue_and_speaker:transfer:1": (
        "Write a short dialogue that includes the problem, clarifying question, answer, and promised action.",
        ("problem", "question", "answer", "action"),
    ),
    "scooter_dialogue_and_speaker:transfer:2": (
        "Identify speaker, listener, and the practical purpose of the guide's reply.",
        ("speaker", "listener", "purpose"),
    ),
    "scooter_dialogue_and_speaker:transfer:3": (
        "Create the three-turn exchange and punctuate the customer's question.",
        ("report", "question", "action"),
    ),
    "scooter_dialogue_and_speaker:review:3": (
        "Identify she, then rewrite the exchange as two labelled turns without changing the advice.",
        ("identity", "observation", "advice"),
    ),
    "scooter_dialogue_and_speaker:review:4": (
        "Create the four-turn exchange so each reply answers the line before it and the final action is clear.",
        ("report", "question", "answer", "action"),
    ),
    "scooter_dialogue_and_speaker:bridge:1": (
        "Name both speakers and state what new information Uma adds.",
        ("first_speaker", "second_speaker", "information"),
    ),
    "scooter_dialogue_and_speaker:masterclass:2": (
        "Write the three-turn exchange with a relevant question and action.",
        ("report", "question", "action"),
    ),
    "scooter_dialogue_and_speaker:revision_level_3:5": (
        "State the purpose of each turn and the safe action chosen.",
        ("first_purpose", "second_purpose", "action"),
    ),
    "scooter_inference_and_fair_choice:independent:1": (
        "What should Naman do, and which two details support that decision?",
        ("action", "route", "register"),
    ),
    "scooter_inference_and_fair_choice:independent:2": (
        "Infer the risk and explain the safer action using both details.",
        ("risk", "strap", "breaker", "action"),
    ),
    "scooter_inference_and_fair_choice:transfer:1": (
        "Decide what Iqra should do and justify the decision with both clues.",
        ("action", "stall", "desk"),
    ),
    "scooter_inference_and_fair_choice:review:1": (
        "State the best return action and link both clues to your reason.",
        ("action", "label", "list"),
    ),
    "scooter_inference_and_fair_choice:review:4": (
        "Infer the risk and give the safest plan using the bridge, rope, and guide clues.",
        ("risk", "bridge", "rope", "guide", "plan"),
    ),
    "scooter_inference_and_fair_choice:bridge:1": (
        "Choose the return action and use both clues.",
        ("action", "name", "lists"),
    ),
    "scooter_context_vocabulary:transfer:2": (
        "Break the word into its bases and explain the combined meaning.",
        ("foot", "path", "meaning"),
    ),
    "scooter_context_vocabulary:review:2": (
        "Form the compound, explain it, and use it in a sentence.",
        ("form", "meaning", "use"),
    ),
    "scooter_context_vocabulary:review:4": (
        "Build the compound, explain how both bases shape its meaning, and write a fresh sentence with it.",
        ("form", "book", "case", "use"),
    ),
    "scooter_context_vocabulary:revision_level_1:3": (
        "Build the compound and explain why both bases matter.",
        ("form", "sun", "light"),
    ),
    "scooter_connectors_and_adverbs:guided:3": (
        "Write one complete sentence showing frequency, time, and result.",
        ("frequency", "time", "result"),
    ),
    "scooter_connectors_and_adverbs:independent:1": (
        "Write one complete sentence using a frequency adverb, but, and because.",
        ("frequency", "contrast", "cause"),
    ),
    "scooter_connectors_and_adverbs:independent:4": (
        "Write one sentence that preserves frequency, time, manner, and cause.",
        ("frequency", "time", "manner", "cause"),
    ),
    "scooter_connectors_and_adverbs:transfer:1": (
        "Combine the facts using usually, late, and because correctly.",
        ("frequency", "time", "cause"),
    ),
    "scooter_connectors_and_adverbs:transfer:2": (
        "Explain which words show frequency, time, and manner.",
        ("frequency", "time", "manner"),
    ),
    "scooter_connectors_and_adverbs:transfer:3": (
        "Join the ideas with but and because while keeping quickly beside the action it describes.",
        ("contrast", "cause", "manner"),
    ),
    "scooter_connectors_and_adverbs:review:1": (
        "Name the frequency, time, and manner adverbs and explain both connectors.",
        ("frequency", "time", "manner", "cause", "contrast"),
    ),
    "scooter_connectors_and_adverbs:review:3": (
        "Classify normally, today, patiently, and later, then explain the jobs of because and but.",
        ("normally", "today", "patiently", "later", "cause", "contrast"),
    ),
    "scooter_connectors_and_adverbs:bridge:1": (
        "Label usually and today, then explain but and because.",
        ("frequency", "time", "contrast", "cause"),
    ),
    "scooter_connectors_and_adverbs:masterclass:2": (
        "Explain carefully, because, and but by their jobs.",
        ("manner", "cause", "contrast"),
    ),
    "scooter_connectors_and_adverbs:revision_level_1:3": (
        "Build a sentence using often, today, and but.",
        ("frequency", "time", "contrast"),
    ),
    "scooter_precise_grammar:review:4": (
        "Write one natural sentence that shows the goodbye happened before the walk, then explain the two verb forms.",
        ("sequence", "waved", "walked"),
    ),
    "scooter_precise_grammar:masterclass:2": (
        "Rebuild the sentence and mark who, action, object, and time.",
        ("sentence", "who", "action", "object", "time"),
    ),
    "scooter_summary_and_profile:guided:1": (
        "Write a three-sentence paragraph in your own words, with an opening, connected action detail, and outcome.",
        ("opening", "action", "outcome", "own_words"),
    ),
    "scooter_summary_and_profile:independent:4": (
        "Write an own-words paragraph with a topic sentence, two connected details, and a closing result.",
        ("opening", "indoor", "schedule", "closing"),
    ),
    "scooter_summary_and_profile:transfer:2": (
        "Write a sourced profile that selects the three most relevant facts for a school sports display.",
        ("role", "achievement", "service", "source"),
    ),
}
CH2_COMPOSITE_PART_COUNTS = {
    "scooter_summary_and_profile:guided:2": (
        "Write a short factual profile using three supported facts and name the source.",
        4,
    ),
}


def _class_dir(chapter_id: str) -> str:
    return f"class_{chapter_id.split('_')[1].removeprefix('c')}"


def _manifest_path(chapter_id: str) -> Path:
    base = MANIFEST_ROOT / _class_dir(chapter_id) / chapter_id
    python_manifest = base.with_suffix(".py")
    return python_manifest if python_manifest.is_file() else base.with_suffix(".json")


def _runtime_path(chapter_id: str) -> Path:
    return RUNTIME_ROOT / _class_dir(chapter_id) / f"{chapter_id}.json"


def _count_phrase(value: object, phrase: str) -> int:
    if isinstance(value, str):
        return value.casefold().count(phrase)
    if isinstance(value, list):
        return sum(_count_phrase(item, phrase) for item in value)
    if isinstance(value, dict):
        return sum(_count_phrase(item, phrase) for item in value.values())
    return 0


def _walk_dicts(value: object):
    if isinstance(value, list):
        for item in value:
            yield from _walk_dicts(item)
    elif isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_dicts(item)


def _core_level_activities(level: object) -> list[object]:
    return [
        level.co_construct,
        *level.guided_variants,
        *level.independent_variants,
        *level.transfer_variants,
        *level.review_variants,
    ]


def _all_level_activities(level: object) -> list[object]:
    return [
        *_core_level_activities(level),
        *level.support_checks.activities().values(),
    ]


def _skill_construct(skill_ids: list[str]) -> str:
    return " and ".join(
        skill_id.split(".", 1)[-1].replace("_", " ")
        for skill_id in skill_ids
    )


def _child_detail_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _assert_open_direction_has_child_guidance(
    activity: OpenActivitySpec,
    *,
    expected_count: int | None = None,
) -> str:
    direction = activity.teaching_block.strip()
    assert direction
    assert "evidence target" not in direction.casefold()
    guidance = _child_detail_guidance(
        expected_count or len(activity.rubric_criteria)
    )
    assert guidance in direction.casefold()
    assert activity.model_answer.casefold() not in direction.casefold()
    return direction


def _assert_open_direction_names_construct(
    activity: OpenActivitySpec,
    *,
    construct: str,
    expected_count: int | None = None,
) -> None:
    direction = _assert_open_direction_has_child_guidance(
        activity,
        expected_count=expected_count,
    )
    assert construct.casefold() in direction.casefold()


def _class5_target_activities(chapter_id: str, level: object) -> list[OpenActivitySpec]:
    if chapter_id in {"eng_c5_ch02", "eng_c5_ch03"}:
        candidates = _all_level_activities(level)
    elif chapter_id == "eng_c5_ch04":
        candidates = [
            *(
                level.transfer_variants[3:]
                if level.level_id in CLASS5_CH04_TRANSFER_LEVEL_IDS
                else []
            ),
            *level.review_variants[2:],
        ]
    elif chapter_id == "eng_c5_ch05":
        candidates = [*level.transfer_variants[3:], *level.review_variants[2:]]
    else:
        candidates = [
            *level.guided_variants[2:],
            *level.independent_variants[2:],
            *level.transfer_variants[2:],
            *level.review_variants[2:],
            *level.support_checks.activities().values(),
        ]
    return [
        activity for activity in candidates if isinstance(activity, OpenActivitySpec)
    ]


def test_banned_shared_instruction_copy_is_absent_from_sources_and_runtime(
) -> None:
    offenders: dict[str, int] = {}
    for source_path in SOURCE_BUILDERS:
        source_text = source_path.read_text(encoding="utf-8").casefold()
        for fragment in BANNED_DIRECTION_FRAGMENTS:
            count = source_text.count(fragment)
            if count:
                offenders[f"{source_path.relative_to(ROOT)}:{fragment}"] = count

    for chapter_id in CHAPTER_IDS:
        manifest_path = _manifest_path(chapter_id)
        manifest_payload = load_manifest(manifest_path).model_dump(mode="json")
        runtime_path = _runtime_path(chapter_id)
        runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        for fragment in BANNED_DIRECTION_FRAGMENTS:
            manifest_count = _count_phrase(manifest_payload, fragment)
            runtime_count = _count_phrase(runtime_payload, fragment)
            if manifest_count:
                offenders[f"{manifest_path.relative_to(ROOT)}:{fragment}"] = (
                    manifest_count
                )
            if runtime_count:
                offenders[f"{runtime_path.relative_to(ROOT)}:{fragment}"] = (
                    runtime_count
                )

    assert offenders == {}


@pytest.mark.parametrize(
    ("activity_id", "expected_prompt", "expected_suffixes"),
    [
        (activity_id, prompt, suffixes)
        for activity_id, (prompt, suffixes) in CH2_EXPLICIT_PARTS.items()
    ],
)
def test_ch2_tasks_have_one_slot_for_each_explicit_part(
    activity_id: str,
    expected_prompt: str,
    expected_suffixes: tuple[str, ...],
) -> None:
    manifest = load_manifest(_manifest_path("eng_c5_ch02"))
    manifest_activity = next(
        activity
        for level in manifest.levels
        for activity in _all_level_activities(level)
        if activity.activity_id == activity_id
    )

    assert isinstance(manifest_activity, OpenActivitySpec)
    assert manifest_activity.prompt == expected_prompt
    expected_ids = [
        f"{activity_id}:{suffix}" for suffix in expected_suffixes
    ]
    assert [
        criterion.id for criterion in manifest_activity.rubric_criteria
    ] == expected_ids
    assert [slot.id for slot in manifest_activity.concept_slots] == expected_ids
    assert (
        f"include all {len(expected_ids)} details"
        in manifest_activity.teaching_block.casefold()
    )
    assert (
        manifest_activity.model_answer.casefold()
        not in manifest_activity.teaching_block.casefold()
    )

    runtime_payload = json.loads(
        _runtime_path("eng_c5_ch02").read_text(encoding="utf-8")
    )
    runtime_activities = [
        item
        for item in _walk_dicts(runtime_payload)
        if item.get("prompt") == expected_prompt
    ]
    assert runtime_activities
    for activity in runtime_activities:
        assert [
            criterion["id"] for criterion in activity["rubric_criteria"]
        ] == expected_ids
        assert [slot["id"] for slot in activity["concept_slots"]] == expected_ids
        assert (
            f"include all {len(expected_ids)} details"
            in activity["teaching_block"].casefold()
        )


@pytest.mark.parametrize(
    ("activity_id", "expected_prompt", "expected_count"),
    [
        (activity_id, prompt, count)
        for activity_id, (prompt, count) in CH2_COMPOSITE_PART_COUNTS.items()
    ],
)
def test_ch2_composite_rubrics_have_honest_learner_part_counts(
    activity_id: str,
    expected_prompt: str,
    expected_count: int,
) -> None:
    manifest = load_manifest(_manifest_path("eng_c5_ch02"))
    manifest_activity = next(
        activity
        for level in manifest.levels
        for activity in _all_level_activities(level)
        if activity.activity_id == activity_id
    )

    assert isinstance(manifest_activity, OpenActivitySpec)
    assert manifest_activity.prompt == expected_prompt
    assert [
        criterion.id.rsplit(":", 1)[-1]
        for criterion in manifest_activity.rubric_criteria
    ] == ["facts", "source"]
    assert f"include all {expected_count} details" in (
        manifest_activity.teaching_block.casefold()
    )
    assert (
        manifest_activity.model_answer.casefold()
        not in manifest_activity.teaching_block.casefold()
    )

    runtime_payload = json.loads(
        _runtime_path("eng_c5_ch02").read_text(encoding="utf-8")
    )
    runtime_activities = [
        item
        for item in _walk_dicts(runtime_payload)
        if item.get("variant_id") == activity_id
    ]
    assert runtime_activities
    for activity in runtime_activities:
        assert f"include all {expected_count} details" in (
            activity["teaching_block"].casefold()
        )


@pytest.mark.parametrize("chapter_id", CLASS4_EARLY_TARGET_COUNTS)
def test_class4_early_directions_name_the_activity_construct(chapter_id: str) -> None:
    manifest = load_manifest(_manifest_path(chapter_id))
    targets = [
        (level, activity)
        for level in manifest.levels
        for activity in _core_level_activities(level)
    ]

    assert len(targets) == CLASS4_EARLY_TARGET_COUNTS[chapter_id]
    for level, activity in targets:
        if isinstance(activity, OpenActivitySpec):
            _assert_open_direction_names_construct(
                activity,
                construct=level.focus,
            )
            continue
        assert isinstance(activity, ChoiceActivitySpec)
        direction = activity.teaching_block.strip()
        assert direction
        assert level.focus.casefold() in direction.casefold()
        assert "compare each option" in direction.casefold()


@pytest.mark.parametrize("chapter_id", CLASS4_EARLY_TARGET_COUNTS)
def test_class4_assessment_directions_use_child_facing_detail_counts(
    chapter_id: str,
) -> None:
    manifest = load_manifest(_manifest_path(chapter_id))
    targets = [
        activity
        for activity in manifest.chapter_assessment.items
        if isinstance(activity, OpenActivitySpec)
    ]

    assert len(targets) == 18
    for activity in targets:
        direction = _assert_open_direction_has_child_guidance(activity)
        matching_focuses = [
            level.focus
            for level in manifest.levels
            if set(activity.skill_ids).issubset(level.skill_ids)
        ]
        assert matching_focuses
        assert any(
            focus.casefold() in direction.casefold()
            for focus in matching_focuses
        )


@pytest.mark.parametrize("chapter_id", CLASS4_LATE_TARGET_COUNTS)
def test_class4_late_retry_directions_use_child_facing_detail_counts(
    chapter_id: str,
) -> None:
    manifest = load_manifest(_manifest_path(chapter_id))
    targets = [
        (level, level.support_checks.revision_level_3)
        for level in manifest.levels
    ]

    assert len(targets) == CLASS4_LATE_TARGET_COUNTS[chapter_id]
    for level, activity in targets:
        assert isinstance(activity, OpenActivitySpec)
        _assert_open_direction_names_construct(
            activity,
            construct=level.focus,
        )


@pytest.mark.parametrize("chapter_id", CLASS5_TARGET_COUNTS)
def test_class5_shared_directions_use_child_facing_detail_counts(
    chapter_id: str,
) -> None:
    manifest = load_manifest(_manifest_path(chapter_id))
    targets = [
        activity
        for level in manifest.levels
        for activity in _class5_target_activities(chapter_id, level)
    ]

    assert len(targets) == CLASS5_TARGET_COUNTS[chapter_id]
    for activity in targets:
        expected_count = None
        if chapter_id == "eng_c5_ch02":
            composite_contract = CH2_COMPOSITE_PART_COUNTS.get(
                activity.activity_id
            )
            if composite_contract is not None:
                expected_count = composite_contract[1]
        _assert_open_direction_names_construct(
            activity,
            construct=_skill_construct(activity.skill_ids),
            expected_count=expected_count,
        )
