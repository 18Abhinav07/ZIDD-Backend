import copy
import hashlib
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import get_settings
from app.content import school_rebuild_content as live_content
from app.content import school_rebuild_schema as live_schema
from app.content.school_rebuild_content import (
    LIVE_CHAPTER_ROOT,
    load_approved_live_chapter,
    load_live_chapter_file,
    qa_live_content_enabled,
)
from app.content.school_v3_content import load_ncert_source_map
from app.content.school_rebuild_schema import (
    LiveChapterActivity,
    LiveChapterAssessment,
    LiveChapterAssessmentItem,
    LiveChapterChecks,
    LiveChapterLevel,
    LiveRubricCriterion,
    LiveSchoolChapter,
)


MIGRATED_CHAPTER_RUNTIME_MANIFEST = {
    "english/class_3/eng_c3_ch01.json": (
        "eng_c3_ch01",
        "33ec726a84a351116ca363c8bb8cc6f40c2f3ffeb1b73c1f9122caa04de43ea5",
    ),
    "english/class_3/eng_c3_ch02.json": (
        "eng_c3_ch02",
        "d00c3d517a5c55e6d0cc6d703dec5d1eadae403d73de9c281395636a3662136e",
    ),
    "english/class_3/eng_c3_ch03.json": (
        "eng_c3_ch03",
        "c4193ab83f3f22db4a889c1ebb2da6b02aeeb5468457548db790a74b5365a3ad",
    ),
    "english/class_3/eng_c3_ch04.json": (
        "eng_c3_ch04",
        "ce3bfd4c1e025f67a59d9d4bbdb24b91b746fc632298ef3f7f32f08b3a26d782",
    ),
    "english/class_3/eng_c3_ch05.json": (
        "eng_c3_ch05",
        "d15577c57a1526967fe80b811d45731e330c02321fba9fccec77f2a563036795",
    ),
    "english/class_3/eng_c3_ch06.json": (
        "eng_c3_ch06",
        "d074f0bd6c4fb851147dc83e5bb3054de693494982fe4dd90f1407a561210c3b",
    ),
    "english/class_3/eng_c3_ch07.json": (
        "eng_c3_ch07",
        "2c3e6e34a8ceba48833069cc67ed769ccb4f32b822c8aa099da3dafc64d721fc",
    ),
    "english/class_3/eng_c3_ch08.json": (
        "eng_c3_ch08",
        "a487c031ed6bd96407e44238a8a724a93669718fe3af128124cecadb14046ffc",
    ),
    "english/class_3/eng_c3_ch09.json": (
        "eng_c3_ch09",
        "b3507444ca2cad0ccb17aa9e407adc9d2f8527c032a94d27482fa88f9e131ca4",
    ),
    "english/class_3/eng_c3_ch10.json": (
        "eng_c3_ch10",
        "50c42df618bcd2a8e1ea1e51007f8c43c8c052b67d0ebee507ed361e72483be4",
    ),
    "english/class_3/eng_c3_ch11.json": (
        "eng_c3_ch11",
        "380c3951fc34afa0b44a00b67b57f21a4986c41659ae68ec35be21b9dc822f7c",
    ),
    "english/class_3/eng_c3_ch12.json": (
        "eng_c3_ch12",
        "4a556356c46adb5b6133c2ad7d3031ef58cdfc621a27bb66de1df3a0e1d5f014",
    ),
    "english/class_4/eng_c4_ch01.json": (
        "eng_c4_ch01",
        "294862ee0acb39b8717a2782f2de8db189dd567835f2dbf0583a32a392cbc37e",
    ),
    "english/class_4/eng_c4_ch02.json": (
        "eng_c4_ch02",
        "929d5f3696a995f90f610fe7fe521448bac1fd90ecb1e351a971f609a20c9f9e",
    ),
    "english/class_4/eng_c4_ch03.json": (
        "eng_c4_ch03",
        "a0961b4d3b7b31c3e4140329dda17f27fae01a517675afa1befc0867d72a1020",
    ),
    "english/class_4/eng_c4_ch04.json": (
        "eng_c4_ch04",
        "8e08dcaf6d64fad54f906d24198f4c916bebae458bb2a07ec0df8ef17b131d85",
    ),
    "english/class_4/eng_c4_ch05.json": (
        "eng_c4_ch05",
        "ad04138a1a7e94ae982de8d08269836ae8d0d00d0fbb1277b7301223040a2a2b",
    ),
    "english/class_4/eng_c4_ch06.json": (
        "eng_c4_ch06",
        "5d58e7e7f81b059a5e2b10875fbb343d7059c4e92ac9bc4741a7f1da8416f572",
    ),
    "english/class_4/eng_c4_ch07.json": (
        "eng_c4_ch07",
        "97a2f8ae34c98421f7ba8a44dcaed50625f2938d26854bc9aed91be48010ae42",
    ),
    "english/class_4/eng_c4_ch08.json": (
        "eng_c4_ch08",
        "c58772be3ad3894be9f3b557e0342d1a8c39e664b6d8f6ba4d443fc1f33d9f19",
    ),
    "english/class_4/eng_c4_ch09.json": (
        "eng_c4_ch09",
        "d6b2f1f900b167bf50696b265f53b598917b86a838ee24ee32fbf3dc64868253",
    ),
    "english/class_4/eng_c4_ch10.json": (
        "eng_c4_ch10",
        "80546d8cc82575341e2a4e3a79d04dd2423889418ea3094d29fbe4fa9920c111",
    ),
    "english/class_4/eng_c4_ch11.json": (
        "eng_c4_ch11",
        "de18819f2562e69c9af2641abfa8eba98ddf60c8d0d106ed7f3a115353f9b67b",
    ),
    "english/class_4/eng_c4_ch12.json": (
        "eng_c4_ch12",
        "c477fbcc6840493b305e970adacd06f08b04860a4a96f0d578df710ec34f04e8",
    ),
    "english/class_5/eng_c5_ch01.json": (
        "eng_c5_ch01",
        "be28deba1238c24a781403c723676d2ad13d050bed450f6ab222966f9af332a3",
    ),
    "english/class_5/eng_c5_ch02.json": (
        "eng_c5_ch02",
        "47d3ff1f5c63a1658e47e3e6d3fe29e5696a593ca93593e7274e8894caaca7b1",
    ),
    "english/class_5/eng_c5_ch03.json": (
        "eng_c5_ch03",
        "0924975cad21faede8df61aecdd2326bd97c922da5eebf96bb2685fdcad74bdb",
    ),
    "english/class_5/eng_c5_ch04.json": (
        "eng_c5_ch04",
        "00a93446f07dd715f68cbc748b76572e36d5e5551f4a25cfc647a078e7345e95",
    ),
    "english/class_5/eng_c5_ch05.json": (
        "eng_c5_ch05",
        "527447d9555b402c78dea33ffdf43301b5ebb695c0849e8fbb503ae1f93593a2",
    ),
}


def _wise_parrot_payload() -> dict:
    source = LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    for level in payload["levels"]:
        for activity in level["checks"].values():
            if activity.get("answer_rule"):
                activity["accepted_answers"] = []
    return payload


def _activity_payload() -> dict:
    payload = _wise_parrot_payload()
    return copy.deepcopy(payload["levels"][0]["checks"]["guided_check"])


def _legacy_activity_grading_payload(payload: dict) -> dict:
    payload = copy.deepcopy(payload)
    for field in (
        "schema_version",
        "episode_kind",
        "teaching_phase",
        "interaction_type",
        "evidence_role",
        "certifying_language",
        "source_anchor_ids",
        "knowledge_components",
        "target_misconception_tags",
        "relevance_terms",
        "model_answer",
        "grading_mode",
    ):
        payload.pop(field, None)
    return payload


def _grading_model(kind: str):
    if kind == "activity":
        return LiveChapterActivity
    return LiveChapterAssessmentItem


def _grading_payload(kind: str) -> dict:
    if kind == "activity":
        return _activity_payload()
    return copy.deepcopy(_valid_assessment(_wise_parrot_payload())["items"][0])


def _concept_grading_payload(kind: str) -> dict:
    payload = _grading_payload(kind)
    if kind == "activity":
        payload = _legacy_activity_grading_payload(payload)
    payload.pop("grading_mode", None)
    payload.pop("evaluation_mode", None)
    payload.pop("certifying_language", None)
    payload.pop("relevance_terms", None)
    payload.pop("model_answer", None)
    payload["accepted_answers"] = []
    payload["answer_rule"] = " concept_slots "
    payload["concept_slots"] = [
        {
            "id": " main_idea ",
            "description": " State the main idea. ",
            "any_of": [" freedom ", " release "],
        }
    ]
    payload["forbidden_phrases"] = [" copied phrase ", " model answer "]
    return payload


def _ordered_concept_grading_payload(kind: str) -> dict:
    payload = _concept_grading_payload(kind)
    payload["concept_slots"].append(
        {
            "id": " supporting_detail ",
            "description": " Add a supporting detail. ",
            "any_of": [" reason ", " evidence "],
        }
    )
    payload["min_response_words"] = 6
    payload["ordered_concept_slot_ids"] = [
        " main_idea ",
        " supporting_detail ",
    ]
    return payload


def _llm_grading_payload(kind: str) -> dict:
    payload = _grading_payload(kind)
    if kind == "activity":
        payload = _legacy_activity_grading_payload(payload)
    payload.pop("grading_mode", None)
    payload.pop("certifying_language", None)
    payload.pop("relevance_terms", None)
    payload.pop("model_answer", None)
    payload["options"] = []
    payload["accepted_answers"] = []
    payload.pop("answer_rule", None)
    payload.update(
        {
            "response_mode": "paragraph",
            "evaluation_mode": "llm_rubric",
            "preflight_rule": " Require a relevant complete sentence. ",
            "pass_score": 0.7,
            "rubric_criteria": [
                {
                    "id": " relevance ",
                    "description": " The answer addresses the prompt. ",
                }
            ],
        }
    )
    return payload


def _taught_skill_ids(payload: dict) -> list[str]:
    return list(
        dict.fromkeys(
            skill_id
            for level in payload["levels"]
            for skill_id in level["skill_ids"]
        )
    )


def _valid_assessment(payload: dict) -> dict:
    skill_ids = _taught_skill_ids(payload)
    items_per_attempt = max(12, len(skill_ids))
    max_attempts = 2
    items = []
    for index in range(items_per_attempt * max_attempts):
        answer = f"answer {index + 1}"
        item = {
            "item_id": f"wise_parrot_assessment_{index + 1:02d}",
            "passage": f"Assessment passage {index + 1}.",
            "prompt": f"Assessment prompt {index + 1}?",
            "skill_ids": [skill_ids[index % len(skill_ids)]],
            "options": [answer, f"distractor {index + 1}"] if index < 4 else [],
            "accepted_answers": [answer],
        }
        if index == 4:
            item.update(
                {
                    "accepted_answers": [],
                    "response_mode": "paragraph",
                    "evaluation_mode": "llm_rubric",
                    "preflight_rule": "Require a relevant complete sentence.",
                    "pass_score": 0.7,
                    "rubric_criteria": [
                        {
                            "id": "relevance",
                            "description": "The answer addresses the prompt.",
                        }
                    ],
                }
            )
        elif index == 5:
            item.update(
                {
                    "accepted_answers": [],
                    "answer_rule": "wise_parrot_reason",
                }
            )
        items.append(item)
    return {
        "items_per_attempt": items_per_attempt,
        "max_attempts": max_attempts,
        "items": items,
    }


def _remove_authored_revision_levels(checks: dict) -> None:
    for revision_no in range(1, 4):
        checks.pop(f"revision_level_{revision_no}", None)


def _author_three_revision_levels(payload: dict) -> None:
    for level in payload["levels"]:
        _remove_authored_revision_levels(level["checks"])
        for revision_no in range(1, 4):
            revision = copy.deepcopy(level["checks"]["masterclass"])
            revision["passage"] = (
                f"{level['level_id']} revision passage {revision_no}."
            )
            revision["prompt"] = (
                f"{level['level_id']} revision prompt {revision_no}?"
            )
            level["checks"][f"revision_level_{revision_no}"] = revision


def _three_attempt_assessment(payload: dict) -> dict:
    assessment = _valid_assessment(payload)
    assessment["max_attempts"] = 3
    skill_ids = _taught_skill_ids(payload)
    required_item_count = (
        assessment["items_per_attempt"] * assessment["max_attempts"]
    )
    for index in range(len(assessment["items"]), required_item_count):
        answer = f"answer {index + 1}"
        assessment["items"].append(
            {
                "item_id": f"wise_parrot_assessment_{index + 1:02d}",
                "passage": f"Assessment passage {index + 1}.",
                "prompt": f"Assessment prompt {index + 1}?",
                "skill_ids": [skill_ids[index % len(skill_ids)]],
                "options": [],
                "accepted_answers": [answer],
            }
        )
    return assessment


def _write_hashed_chapter(tmp_path, payload: dict):
    chapter = LiveSchoolChapter.model_validate(payload)
    payload["runtime_sha256"] = chapter.calculated_runtime_sha256()
    path = tmp_path / "chapter-with-assessment.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _runtime_sha256(runtime: dict) -> str:
    canonical = json.dumps(
        runtime,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def test_wise_parrot_approved_file_round_trips_live_runtime_exactly():
    path = LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"

    loaded = load_approved_live_chapter("english", 5, "eng_c5_ch04")

    assert path.exists()
    authored = load_live_chapter_file(path)
    expected = authored.runtime_dict()
    expected.setdefault("content_version", authored.runtime_sha256)
    expected.setdefault(
        "certification_version",
        authored.certification_version or expected["content_version"],
    )
    assert loaded == expected
    assert _runtime_sha256(loaded) == authored.runtime_sha256


def test_all_source_map_chapters_are_live_and_hash_verified():
    actual_paths = {
        str(path.relative_to(LIVE_CHAPTER_ROOT))
        for path in LIVE_CHAPTER_ROOT.rglob("*.json")
    }
    expected_paths = {
        f"english/class_{class_no}/{chapter['chapter_id']}.json"
        for class_no in (2, 3, 4, 5)
        for chapter in load_ncert_source_map("english", class_no)["chapters"]
    }
    assert actual_paths == expected_paths

    counts: dict[int, int] = {}
    for relative_path in sorted(expected_paths):
        chapter = load_live_chapter_file(LIVE_CHAPTER_ROOT / relative_path)
        class_no = int(relative_path.split("/")[1].removeprefix("class_"))
        counts[class_no] = counts.get(class_no, 0) + 1

        assert chapter.chapter_id == relative_path.rsplit("/", 1)[-1].removesuffix(".json")
        assert chapter.approval_status in {
            "qa_approved",
            "agent_reviewed",
            "release_approved",
            "human_approved",
        }
        assert _runtime_sha256(chapter.runtime_dict()) == chapter.runtime_sha256
        assert chapter.chapter_assessment is not None
        assert len(chapter.chapter_assessment.items) >= 20
        assert all(level.checks.transfer_check is not None for level in chapter.levels)

    assert counts == {2: 13, 3: 12, 4: 12, 5: 10}


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_valid_concept_slot_grading_round_trips_cleaned_runtime(kind):
    parsed = _grading_model(kind).model_validate(_concept_grading_payload(kind))

    runtime = parsed.runtime_dict()

    assert runtime["answer_rule"] == "concept_slots"
    assert runtime["concept_slots"] == [
        {
            "id": "main_idea",
            "description": "State the main idea.",
            "any_of": ["freedom", "release"],
        }
    ]
    assert runtime["forbidden_phrases"] == ["copied phrase", "model answer"]


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_concept_slot_authoring_constraints_round_trip_in_runtime(kind):
    parsed = _grading_model(kind).model_validate(
        _ordered_concept_grading_payload(kind)
    )

    runtime = parsed.runtime_dict()

    assert runtime["min_response_words"] == 6
    assert runtime["ordered_concept_slot_ids"] == [
        "main_idea",
        "supporting_detail",
    ]


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_constructed_concept_response_requires_authored_minimum_words(kind):
    payload = _concept_grading_payload(kind)
    payload["options"] = []

    with pytest.raises(
        ValidationError,
        match="live_constructed_concept_response_requires_min_words",
    ):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_option_backed_concept_response_may_omit_minimum_words(kind):
    payload = _concept_grading_payload(kind)

    parsed = _grading_model(kind).model_validate(payload)

    assert parsed.options
    assert parsed.min_response_words is None


@pytest.mark.parametrize(
    ("kind", "expected_sha256"),
    [
        pytest.param(
            "activity",
            "79c81079af163c4f02d5b745217cf31349c9fc1caff7c353427893fd47786ff9",
            id="activity",
        ),
        pytest.param(
            "assessment_item",
            "a930c4eb2dc6c5436244eee393befc42ffa9c2b49a2b089a68290e6dcf40beb7",
            id="assessment-item",
        ),
    ],
)
def test_absent_concept_slot_authoring_constraints_preserve_runtime_hash(
    kind,
    expected_sha256,
):
    payload = _concept_grading_payload(kind)
    runtime = _grading_model(kind).model_validate(payload).runtime_dict()

    assert "min_response_words" not in runtime
    assert "ordered_concept_slot_ids" not in runtime
    assert _runtime_sha256(runtime) == expected_sha256


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(1, id="below-minimum"),
        pytest.param(101, id="above-maximum"),
        pytest.param("2", id="string"),
        pytest.param(2.0, id="float"),
        pytest.param(True, id="boolean"),
    ],
)
def test_min_response_words_is_strict_and_bounded(kind, value):
    payload = _concept_grading_payload(kind)
    payload["min_response_words"] = value

    with pytest.raises(ValidationError):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
@pytest.mark.parametrize(
    ("ordered_ids", "error"),
    [
        pytest.param(
            ["main_idea"],
            "too_short",
            id="fewer-than-two",
        ),
        pytest.param(
            ["main_idea", "main_idea"],
            "duplicate_live_ordered_concept_slot_id",
            id="duplicate",
        ),
        pytest.param(
            ["main_idea", "unknown_slot"],
            "unknown_live_ordered_concept_slot_id",
            id="unknown-slot",
        ),
    ],
)
def test_ordered_concept_slot_ids_reject_invalid_sequences(kind, ordered_ids, error):
    payload = _ordered_concept_grading_payload(kind)
    payload["ordered_concept_slot_ids"] = ordered_ids

    with pytest.raises(ValidationError, match=error):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_concept_slot_rule_rejects_missing_slots(kind):
    payload = _concept_grading_payload(kind)
    payload.pop("concept_slots")
    payload.pop("forbidden_phrases")

    with pytest.raises(
        ValidationError,
        match="live_concept_slots_rule_requires_slots",
    ):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_concept_slot_rule_rejects_duplicate_slot_ids(kind):
    payload = _concept_grading_payload(kind)
    payload["concept_slots"].append(
        {
            "id": "main_idea",
            "description": "Repeat the main idea.",
            "any_of": ["liberty"],
        }
    )

    with pytest.raises(ValidationError, match="duplicate_live_concept_slot_id"):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
@pytest.mark.parametrize(
    "phrases",
    [
        pytest.param([""], id="empty"),
        pytest.param(["copied phrase", " copied phrase "], id="duplicate"),
    ],
)
def test_concept_slot_rule_rejects_invalid_forbidden_phrases(kind, phrases):
    payload = _concept_grading_payload(kind)
    payload["forbidden_phrases"] = phrases

    with pytest.raises(
        ValidationError,
        match="invalid_live_concept_forbidden_phrases",
    ):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
@pytest.mark.parametrize(
    "field",
    [
        "concept_slots",
        "forbidden_phrases",
        "min_response_words",
        "ordered_concept_slot_ids",
    ],
)
def test_accepted_answer_grading_rejects_concept_fields(kind, field):
    payload = _grading_payload(kind)
    payload[field] = _ordered_concept_grading_payload(kind)[field]

    with pytest.raises(
        ValidationError,
        match="live_concept_fields_require_concept_slots_rule",
    ):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
@pytest.mark.parametrize(
    "field",
    [
        "concept_slots",
        "forbidden_phrases",
        "min_response_words",
        "ordered_concept_slot_ids",
    ],
)
def test_llm_rubric_grading_rejects_concept_fields(kind, field):
    payload = _llm_grading_payload(kind)
    payload[field] = _ordered_concept_grading_payload(kind)[field]

    with pytest.raises(
        ValidationError,
        match="live_concept_fields_require_concept_slots_rule",
    ):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
@pytest.mark.parametrize(
    "field",
    [
        "concept_slots",
        "forbidden_phrases",
        "min_response_words",
        "ordered_concept_slot_ids",
    ],
)
def test_non_concept_answer_rule_rejects_concept_fields(kind, field):
    payload = _grading_payload(kind)
    payload["accepted_answers"] = []
    payload["answer_rule"] = "wise_parrot_reason"
    payload[field] = _ordered_concept_grading_payload(kind)[field]

    with pytest.raises(
        ValidationError,
        match="live_concept_fields_require_concept_slots_rule",
    ):
        _grading_model(kind).model_validate(payload)


def test_bridge_and_masterclass_allow_constructed_response_without_options():
    checks = copy.deepcopy(_wise_parrot_payload()["levels"][0]["checks"])
    for stage in ("bridge", "masterclass"):
        checks[stage]["options"] = []
        checks[stage]["interaction_type"] = "short_text"
        checks[stage]["grading_mode"] = "exact_text"
        checks[stage]["response_mode"] = "short"
        checks[stage].pop("evaluation_mode", None)

    parsed = LiveChapterChecks.model_validate(checks)

    assert parsed.bridge.options == []
    assert parsed.masterclass.options == []
    assert parsed.bridge.interaction_type == "short_text"
    assert parsed.masterclass.interaction_type == "short_text"


@pytest.mark.parametrize("stage", ["bridge", "masterclass"])
def test_bridge_and_masterclass_reject_exactly_one_option(stage):
    checks = copy.deepcopy(_wise_parrot_payload()["levels"][0]["checks"])
    checks[stage] = _legacy_activity_grading_payload(checks[stage])
    checks[stage]["options"] = ["only option"]

    with pytest.raises(
        ValidationError,
        match="supported_stage_options_must_be_empty_or_multiple",
    ):
        LiveChapterChecks.model_validate(checks)


def test_guided_check_still_requires_at_least_two_options():
    checks = copy.deepcopy(_wise_parrot_payload()["levels"][0]["checks"])
    checks["guided_check"] = _legacy_activity_grading_payload(
        checks["guided_check"]
    )
    checks["guided_check"]["options"] = []

    with pytest.raises(ValidationError, match="guided_check_requires_options"):
        LiveChapterChecks.model_validate(checks)


def test_live_checks_preserve_three_distinct_authored_revision_levels():
    checks = copy.deepcopy(_wise_parrot_payload()["levels"][0]["checks"])
    for revision_no in range(1, 4):
        revision = copy.deepcopy(checks["masterclass"])
        revision["passage"] = f"Distinct revision passage {revision_no}."
        revision["prompt"] = f"Distinct revision prompt {revision_no}."
        checks[f"revision_level_{revision_no}"] = revision

    parsed = LiveChapterChecks.model_validate(checks)
    runtime = parsed.runtime_dict()

    assert [runtime[f"revision_level_{index}"]["prompt"] for index in range(1, 4)] == [
        "Distinct revision prompt 1.",
        "Distinct revision prompt 2.",
        "Distinct revision prompt 3.",
    ]


def test_live_checks_reject_a_partial_authored_revision_sequence():
    checks = copy.deepcopy(_wise_parrot_payload()["levels"][0]["checks"])
    _remove_authored_revision_levels(checks)
    revision = copy.deepcopy(checks["masterclass"])
    revision["passage"] = "Only one revision passage."
    revision["prompt"] = "Only one revision prompt."
    checks["revision_level_1"] = revision

    with pytest.raises(ValidationError, match="authored_revision_sequence_incomplete"):
        LiveChapterChecks.model_validate(checks)


def test_third_chapter_check_requires_authored_revision_levels_for_every_level():
    payload = copy.deepcopy(_wise_parrot_payload())
    for level in payload["levels"]:
        _remove_authored_revision_levels(level["checks"])
    payload["chapter_assessment"] = _three_attempt_assessment(payload)

    with pytest.raises(
        ValidationError,
        match="third_attempt_requires_authored_revision_levels",
    ):
        LiveSchoolChapter.model_validate(payload)


def test_activity_deterministic_grading_rejects_both_mechanisms():
    payload = _activity_payload()
    payload["answer_rule"] = "wise_parrot_reason"

    with pytest.raises(
        ValidationError,
        match="live_activity_deterministic_grading_requires_exactly_one",
    ):
        LiveChapterActivity.model_validate(payload)


def test_activity_deterministic_grading_rejects_neither_mechanism():
    payload = _activity_payload()
    payload["accepted_answers"] = []
    payload.pop("answer_rule", None)

    with pytest.raises(
        ValidationError,
        match="live_activity_deterministic_grading_requires_exactly_one",
    ):
        LiveChapterActivity.model_validate(payload)


def test_selected_option_rejects_productive_skill_evidence():
    activity = _activity_payload()
    activity["knowledge_components"] = ["writing.summary_own_words"]

    with pytest.raises(
        ValidationError,
        match="selected_option_cannot_evidence_productive_skill",
    ):
        LiveChapterActivity.model_validate(activity)

    assessment = next(
        item
        for item in _valid_assessment(_wise_parrot_payload())["items"]
        if item["options"]
    )
    assessment["grading_mode"] = "selected_option"
    assessment["skill_ids"] = ["writing.summary_own_words"]

    with pytest.raises(
        ValidationError,
        match="selected_option_cannot_evidence_productive_skill",
    ):
        LiveChapterAssessmentItem.model_validate(assessment)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("preflight_rule", "Require a sentence.", id="preflight"),
        pytest.param("pass_score", 0.7, id="pass-score"),
        pytest.param(
            "rubric_criteria",
            [{"id": "relevance", "description": "Answer the prompt."}],
            id="rubric",
        ),
    ],
)
def test_activity_deterministic_grading_rejects_llm_only_fields(field, value):
    payload = _activity_payload()
    payload[field] = value

    with pytest.raises(
        ValidationError,
        match="live_activity_deterministic_forbids_llm_fields",
    ):
        LiveChapterActivity.model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_llm_rubric_grading_cleans_optional_text(kind):
    parsed = _grading_model(kind).model_validate(_llm_grading_payload(kind))

    assert parsed.preflight_rule == "Require a relevant complete sentence."
    assert parsed.rubric_criteria[0].id == "relevance"


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_llm_rubric_runtime_preserves_default_criterion_contract(kind):
    parsed = _grading_model(kind).model_validate(_llm_grading_payload(kind))

    runtime = parsed.runtime_dict()

    assert runtime["rubric_criteria"] == [
        {
            "id": "relevance",
            "description": "The answer addresses the prompt.",
            "required": True,
            "min_quality": 0.6,
        }
    ]


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_deterministic_grading_rejects_unsupported_answer_rule(kind):
    payload = _grading_payload(kind)
    payload["accepted_answers"] = []
    payload["answer_rule"] = "contains_expected_idea"

    with pytest.raises(ValidationError, match="literal_error"):
        _grading_model(kind).model_validate(payload)


@pytest.mark.parametrize("kind", ["activity", "assessment_item"])
def test_rubric_criteria_reject_duplicate_ids(kind):
    payload = _llm_grading_payload(kind)
    payload["rubric_criteria"].append(
        {
            "id": "relevance",
            "description": "Duplicate relevance criterion.",
        }
    )

    with pytest.raises(ValidationError, match="duplicate_live_rubric_criterion_id"):
        _grading_model(kind).model_validate(payload)


def test_all_live_authoring_models_are_strict():
    models = (
        LiveRubricCriterion,
        live_schema.LiveConceptSlot,
        LiveChapterActivity,
        LiveChapterAssessmentItem,
        LiveChapterAssessment,
        LiveChapterChecks,
        LiveChapterLevel,
        LiveSchoolChapter,
    )

    assert all(model.model_config.get("strict") is True for model in models)


@pytest.mark.parametrize(
    "case",
    [
        "rubric_boolean",
        "rubric_number",
        "concept_slot_string",
        "activity_number",
        "assessment_item_number",
        "assessment_bank_number",
        "chapter_number",
    ],
)
def test_live_authoring_rejects_coerced_string_booleans_and_numbers(case):
    if case == "rubric_boolean":
        model = LiveRubricCriterion
        payload = {"id": "relevance", "description": "Relevant.", "required": "true"}
    elif case == "rubric_number":
        model = LiveRubricCriterion
        payload = {"id": "relevance", "description": "Relevant.", "min_quality": "0.6"}
    elif case == "concept_slot_string":
        model = live_schema.LiveConceptSlot
        payload = {"id": "idea", "description": "Idea.", "any_of": [1]}
    elif case == "activity_number":
        model = LiveChapterActivity
        payload = _llm_grading_payload("activity")
        payload["pass_score"] = "0.7"
    elif case == "assessment_item_number":
        model = LiveChapterAssessmentItem
        payload = _llm_grading_payload("assessment_item")
        payload["pass_score"] = "0.7"
    elif case == "assessment_bank_number":
        model = LiveChapterAssessment
        payload = _valid_assessment(_wise_parrot_payload())
        payload["items_per_attempt"] = "12"
    else:
        model = LiveSchoolChapter
        payload = _wise_parrot_payload()
        payload["chapter_no"] = "4"

    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_valid_chapter_assessment_round_trips_hidden_grading_and_hash(tmp_path):
    payload = _wise_parrot_payload()
    payload["chapter_assessment"] = _valid_assessment(payload)
    expected_items_per_attempt = len(_taught_skill_ids(payload))
    path = _write_hashed_chapter(tmp_path, payload)

    chapter = load_live_chapter_file(path)
    runtime = chapter.runtime_dict()
    assessment = runtime["chapter_assessment"]

    assert assessment["items_per_attempt"] == expected_items_per_attempt
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert assessment["items"][0]["accepted_answers"] == ["answer 1"]
    assert assessment["items"][4]["preflight_rule"] == (
        "Require a relevant complete sentence."
    )
    assert assessment["items"][4]["rubric_criteria"][0]["id"] == "relevance"
    assert assessment["items"][5]["answer_rule"] == "wise_parrot_reason"
    assert _runtime_sha256(runtime) == payload["runtime_sha256"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("items_per_attempt", 9, id="items-per-attempt-below"),
        pytest.param("items_per_attempt", 21, id="items-per-attempt-above"),
        pytest.param("pass_score", 0.59, id="pass-score-below"),
        pytest.param("pass_score", 1.01, id="pass-score-above"),
        pytest.param("max_attempts", 0, id="max-attempts-below"),
        pytest.param("max_attempts", 4, id="max-attempts-above"),
    ],
)
def test_live_chapter_assessment_rejects_every_bank_bound(field, value):
    assessment = _valid_assessment(_wise_parrot_payload())
    assessment[field] = value

    with pytest.raises(ValidationError):
        LiveChapterAssessment.model_validate(assessment)


def test_live_chapter_assessment_rejects_nested_unknown_item_field():
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    assessment["items"][0]["unexpected_grading_hint"] = "hidden"
    payload["chapter_assessment"] = assessment

    with pytest.raises(ValidationError, match="extra_forbidden"):
        LiveSchoolChapter.model_validate(payload)


def test_deterministic_assessment_item_rejects_both_grading_mechanisms():
    item = _valid_assessment(_wise_parrot_payload())["items"][0]
    item["answer_rule"] = "wise_parrot_reason"

    with pytest.raises(
        ValidationError,
        match="live_assessment_deterministic_grading_requires_exactly_one",
    ):
        LiveChapterAssessmentItem.model_validate(item)


def test_deterministic_assessment_item_rejects_neither_grading_mechanism():
    item = _valid_assessment(_wise_parrot_payload())["items"][0]
    item["accepted_answers"] = []
    item.pop("answer_rule", None)

    with pytest.raises(
        ValidationError,
        match="live_assessment_deterministic_grading_requires_exactly_one",
    ):
        LiveChapterAssessmentItem.model_validate(item)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param(
            "preflight_rule",
            "Require a complete sentence.",
            id="preflight-rule",
        ),
        pytest.param("pass_score", 0.7, id="pass-score"),
        pytest.param(
            "rubric_criteria",
            [{"id": "relevance", "description": "Answer the prompt."}],
            id="rubric-criteria",
        ),
    ],
)
def test_deterministic_assessment_item_rejects_llm_only_fields(field, value):
    item = _valid_assessment(_wise_parrot_payload())["items"][0]
    item[field] = value

    with pytest.raises(
        ValidationError,
        match="live_assessment_deterministic_forbids_llm_fields",
    ):
        LiveChapterAssessmentItem.model_validate(item)


def test_live_chapter_assessment_item_rejects_one_option():
    item = _valid_assessment(_wise_parrot_payload())["items"][0]
    item["options"] = ["answer 1"]

    with pytest.raises(
        ValidationError,
        match="live_assessment_item_options_require_two",
    ):
        LiveChapterAssessmentItem.model_validate(item)


def test_live_chapter_assessment_rejects_fewer_than_twenty_items(tmp_path):
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    assessment["items"] = assessment["items"][:19]
    payload["chapter_assessment"] = assessment
    malformed = tmp_path / "short-assessment.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="live_chapter_assessment_requires_20_items",
    ):
        load_live_chapter_file(malformed)


def test_live_chapter_assessment_rejects_duplicate_item_ids(tmp_path):
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    assessment["items"][1]["item_id"] = assessment["items"][0]["item_id"]
    payload["chapter_assessment"] = assessment
    malformed = tmp_path / "duplicate-assessment-item.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="duplicate_live_chapter_assessment_item_id",
    ):
        load_live_chapter_file(malformed)


def test_three_attempt_assessment_requires_one_fresh_full_form_per_attempt():
    payload = _wise_parrot_payload()
    _author_three_revision_levels(payload)
    assessment = _valid_assessment(payload)
    assessment["max_attempts"] = 3
    payload["chapter_assessment"] = assessment

    authored_item_count = len({item["item_id"] for item in assessment["items"]})
    required_item_count = (
        assessment["max_attempts"] * assessment["items_per_attempt"]
    )
    assert authored_item_count == assessment["items_per_attempt"] * 2
    assert required_item_count == assessment["items_per_attempt"] * 3
    with pytest.raises(
        ValidationError,
        match="third_attempt_requires_fresh_assessment_item_bank",
    ):
        LiveSchoolChapter.model_validate(payload)


def test_three_attempt_assessment_requires_fresh_item_for_each_taught_skill():
    payload = _wise_parrot_payload()
    _author_three_revision_levels(payload)
    assessment = _three_attempt_assessment(payload)
    taught_skill_ids = _taught_skill_ids(payload)
    undercovered_skill_id = taught_skill_ids[0]
    third_attempt_start = assessment["items_per_attempt"] * 2
    third_item = next(
        item
        for item in assessment["items"][third_attempt_start:]
        if undercovered_skill_id in item["skill_ids"]
    )
    third_item["skill_ids"] = [taught_skill_ids[1]]
    payload["chapter_assessment"] = assessment

    assert sum(
        undercovered_skill_id in item["skill_ids"]
        for item in assessment["items"]
    ) == 2
    with pytest.raises(
        ValidationError,
        match="undercovered_live_chapter_assessment_skill",
    ):
        LiveSchoolChapter.model_validate(payload)


@pytest.mark.parametrize("max_attempts", [1, 2])
def test_existing_one_and_two_attempt_assessment_banks_remain_compatible(
    max_attempts,
):
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    assessment["max_attempts"] = max_attempts
    payload["chapter_assessment"] = assessment

    parsed = LiveSchoolChapter.model_validate(payload)

    assert parsed.chapter_assessment is not None
    assert parsed.chapter_assessment.max_attempts == max_attempts


def test_live_chapter_assessment_rejects_untaught_skill(tmp_path):
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    assessment["items"][0]["skill_ids"] = ["writing.short_answer"]
    payload["chapter_assessment"] = assessment
    malformed = tmp_path / "untaught-assessment-skill.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="untaught_live_chapter_assessment_skill",
    ):
        load_live_chapter_file(malformed)


def test_live_chapter_assessment_rejects_undercovered_taught_skill(tmp_path):
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    taught_skill_ids = _taught_skill_ids(payload)
    assessment["items"][0]["skill_ids"] = [taught_skill_ids[1]]
    payload["chapter_assessment"] = assessment
    malformed = tmp_path / "undercovered-assessment-skill.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="undercovered_live_chapter_assessment_skill",
    ):
        load_live_chapter_file(malformed)


def test_live_chapter_assessment_form_must_cover_all_taught_skills():
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    additional_taught_skill = "writing.short_answer"
    assert additional_taught_skill not in _taught_skill_ids(payload)
    payload["levels"][0]["skill_ids"].append(additional_taught_skill)
    assessment["items_per_attempt"] = 10
    assessment["items"][0]["skill_ids"].append(additional_taught_skill)
    assessment["items"][1]["skill_ids"].append(additional_taught_skill)
    payload["chapter_assessment"] = assessment

    with pytest.raises(
        ValidationError,
        match="live_chapter_assessment_form_cannot_cover_skills",
    ):
        LiveSchoolChapter.model_validate(payload)


def test_live_chapter_assessment_requires_mixed_bank(tmp_path):
    payload = _wise_parrot_payload()
    assessment = _valid_assessment(payload)
    for item in assessment["items"]:
        item["options"] = []
    payload["chapter_assessment"] = assessment
    malformed = tmp_path / "non-mixed-assessment.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="mixed_live_chapter_assessment_bank_required",
    ):
        load_live_chapter_file(malformed)


def test_live_chapter_assessment_rejects_only_three_option_items():
    assessment = _valid_assessment(_wise_parrot_payload())
    assessment["items"][3]["options"] = []

    with pytest.raises(
        ValidationError,
        match="mixed_live_chapter_assessment_bank_required",
    ):
        LiveChapterAssessment.model_validate(assessment)


def test_live_chapter_assessment_rejects_only_three_no_option_items():
    assessment = _valid_assessment(_wise_parrot_payload())
    no_option_indexes = {4, 5, 6}
    for index, item in enumerate(assessment["items"]):
        if index not in no_option_indexes and not item["options"]:
            item["options"] = [f"answer {index + 1}", f"distractor {index + 1}"]

    with pytest.raises(
        ValidationError,
        match="mixed_live_chapter_assessment_bank_required",
    ):
        LiveChapterAssessment.model_validate(assessment)


def test_authored_skill_collection_includes_assessment_items_directly():
    chapter = SimpleNamespace(
        levels=[SimpleNamespace(skill_ids=["reading.sentence_comprehension"])],
        chapter_assessment=SimpleNamespace(
            items=[SimpleNamespace(skill_ids=["writing.short_answer"])]
        ),
    )

    assert live_content._collect_authored_skill_ids(chapter) == {
        "reading.sentence_comprehension",
        "writing.short_answer",
    }


def test_live_loader_rejects_unknown_fields_and_unreviewed_approval(tmp_path):
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["unexpected_runtime_knob"] = True
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_live_chapter_file(malformed)

    unreviewed_payload = copy.deepcopy(payload)
    unreviewed_payload.pop("unexpected_runtime_knob")
    unreviewed_payload["reviewed_by"] = None
    unreviewed_payload["reviewed_at"] = None
    unreviewed_payload["review_evidence"] = []
    unreviewed = tmp_path / "unreviewed.json"
    unreviewed.write_text(json.dumps(unreviewed_payload), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_live_chapter_file(unreviewed)


def test_live_loader_rejects_unknown_taught_level_taxonomy_skill(tmp_path):
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    unknown_skill_id = "reading.not_a_real_skill"
    payload["levels"][0]["skill_ids"].append(unknown_skill_id)
    assessment = payload["chapter_assessment"]
    for attempt_no in range(assessment["max_attempts"]):
        item_index = attempt_no * assessment["items_per_attempt"]
        assessment["items"][item_index]["skill_ids"].append(unknown_skill_id)
    malformed = tmp_path / "unknown-skill.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown_live_chapter_skill"):
        load_live_chapter_file(malformed)


def test_live_loader_requires_distinct_pedagogy_stages(tmp_path):
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    level = payload["levels"][0]
    level["checks"]["bridge"] = copy.deepcopy(level["checks"]["guided_check"])
    malformed = tmp_path / "duplicate-stage.json"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValidationError, match="duplicate_pedagogy_stage"):
        load_live_chapter_file(malformed)


def test_live_loader_rejects_content_changed_without_reviewed_hash(tmp_path):
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["levels"][0]["checks"]["guided_check"]["prompt"] = "A changed prompt"
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="live_chapter_runtime_hash_mismatch"):
        load_live_chapter_file(tampered)


def test_live_loader_rejects_model_answer_language_in_learner_content(tmp_path):
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch01.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    activity = payload["levels"][0]["teaching_steps"][0]["activity"]
    activity["passage"] += "\n\nModel answer: This must not be shown to a learner."
    malformed = _write_hashed_chapter(tmp_path, payload)

    with pytest.raises(ValueError, match="live_chapter_learner_model_answer_label"):
        load_live_chapter_file(malformed)


def test_approved_loader_rejects_valid_hashed_internal_chapter_id_mismatch(
    tmp_path,
    monkeypatch,
):
    source = LIVE_CHAPTER_ROOT / "english" / "class_3" / "eng_c3_ch01.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["chapter_id"] = "eng_c3_internal_mismatch"
    chapter = LiveSchoolChapter.model_validate(payload)
    payload["runtime_sha256"] = chapter.calculated_runtime_sha256()
    target = tmp_path / "english" / "class_3" / "eng_c3_ch01.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(live_content, "LIVE_CHAPTER_ROOT", tmp_path)

    with pytest.raises(ValueError, match="live_chapter_id_mismatch"):
        load_approved_live_chapter("english", 3, "eng_c3_ch01")


@pytest.mark.parametrize(
    "app_env",
    ["prod", "production", "staging", "preview", "unknown"],
)
def test_qa_content_defaults_fail_closed_for_explicit_deploy_envs(
    monkeypatch,
    app_env,
):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.delenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", raising=False)

    assert qa_live_content_enabled() is False


def test_qa_content_missing_app_env_uses_central_dev_default(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", raising=False)
    get_settings.cache_clear()

    try:
        assert qa_live_content_enabled() is True
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("app_env", ["dev", "development", "local", "test", "ci"])
def test_qa_content_defaults_enabled_only_for_explicit_local_envs(
    monkeypatch,
    app_env,
):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.delenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", raising=False)

    assert qa_live_content_enabled() is True


@pytest.mark.parametrize("app_env", [None, "production", "staging", "unknown"])
def test_qa_content_explicit_override_is_deliberate(monkeypatch, app_env):
    if app_env is None:
        monkeypatch.delenv("APP_ENV", raising=False)
    else:
        monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", "1")

    assert qa_live_content_enabled() is True


@pytest.mark.parametrize(
    "approval_status",
    ["qa_approved", "human_approved"],
)
def test_production_fails_closed_for_non_reviewed_chapter(
    monkeypatch,
    tmp_path,
    approval_status,
):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", raising=False)
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["approval_status"] = approval_status
    target = tmp_path / "english" / "class_5" / "eng_c5_ch04.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(live_content, "LIVE_CHAPTER_ROOT", tmp_path)

    with pytest.raises(
        ValueError,
        match="live_chapter_not_production_reviewed",
    ):
        load_approved_live_chapter("english", 5, "eng_c5_ch04")


def test_production_serves_agent_reviewed_chapter_without_human_approval(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", raising=False)
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    assert payload["approval_status"] == "agent_reviewed"
    target = tmp_path / "english" / "class_5" / "eng_c5_ch04.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(live_content, "LIVE_CHAPTER_ROOT", tmp_path)

    runtime = load_approved_live_chapter("english", 5, "eng_c5_ch04")

    assert runtime["chapter_id"] == "eng_c5_ch04"


def test_production_serves_release_approved_chapter_without_qa_override(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("SCHOOL_REBUILD_ALLOW_QA_CONTENT", raising=False)
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["approval_status"] = "release_approved"
    payload["reviewed_by"] = "school-release-review/2026-07-15"
    payload["reviewed_at"] = "2026-07-15T12:00:00+05:30"
    payload["review_evidence"] = [
        "agent content review",
        "release integrity review",
    ]
    target = tmp_path / "english" / "class_5" / "eng_c5_ch04.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(live_content, "LIVE_CHAPTER_ROOT", tmp_path)

    runtime = load_approved_live_chapter("english", 5, "eng_c5_ch04")

    assert runtime["chapter_id"] == "eng_c5_ch04"


def test_release_approved_status_requires_reviewer_timestamp_and_evidence(tmp_path):
    source = (
        LIVE_CHAPTER_ROOT / "english" / "class_5" / "eng_c5_ch04.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["approval_status"] = "release_approved"
    payload["reviewed_by"] = None
    payload["reviewed_at"] = None
    payload["review_evidence"] = []
    target = tmp_path / "release-without-evidence.json"
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValidationError,
        match="reviewed_live_chapter_requires_review_evidence",
    ):
        load_live_chapter_file(target)
