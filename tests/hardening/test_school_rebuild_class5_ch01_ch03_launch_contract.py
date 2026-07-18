import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services import school_rebuild_curriculum as curriculum


CLASS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
SOURCE_MAP_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "ncert_source_map"
    / "english"
    / "class_5.json"
)
CHAPTERS = {
    "eng_c5_ch01": (1, "Papa's Spectacles", 9, 16),
    "eng_c5_ch02": (2, "Gone with the Scooter", 7, 14),
    "eng_c5_ch03": (3, "The Rainbow", 7, 13),
}
CHECK_STAGES = {
    "guided_check",
    "bridge",
    "masterclass",
    "independent_check",
    "transfer_check",
}
DEEP_CHECK_STAGES = CHECK_STAGES | {
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
}
HIDDEN_GRADING_KEYS = {
    "accepted_answers",
    "answer_rule",
    "concept_slots",
    "forbidden_phrases",
    "ordered_concept_slot_ids",
    "preflight_rule",
    "pass_score",
    "rubric_criteria",
}


@pytest.fixture(autouse=True)
def hardening_test_env():
    """Keep this content-only slice isolated from concurrent catalog rebuilds."""
    yield


def _source_entries() -> dict[str, dict]:
    payload = json.loads(SOURCE_MAP_PATH.read_text(encoding="utf-8"))
    return {entry["chapter_id"]: entry for entry in payload["chapters"]}


@pytest.mark.parametrize("chapter_id", CHAPTERS)
def test_owned_class5_chapter_meets_launch_structure_and_source_contract(chapter_id):
    chapter_no, title, expected_levels, _ = CHAPTERS[chapter_id]
    chapter = load_live_chapter_file(CLASS_ROOT / f"{chapter_id}.json")
    runtime = chapter.runtime_dict()
    source = _source_entries()[chapter_id]

    if chapter_id == "eng_c5_ch01":
        assert chapter.approval_status == "agent_reviewed"
        assert chapter.reviewed_by == "Codex School content and browser review"
        reviewed_at = datetime.fromisoformat(chapter.reviewed_at)
        assert reviewed_at.tzinfo is not None
        evidence = "\n".join(chapter.review_evidence).lower()
        assert "official" in evidence
        assert "browser qa" in evidence
        assert "test_school_rebuild_class5_ch1_gold_slice.py" in evidence
        assert "semantic claim slots" in evidence
    else:
        assert chapter.approval_status == "agent_reviewed"
        assert chapter.reviewed_by
        assert chapter.reviewed_at
        assert chapter.review_evidence
        assert any(
            "manifest" in evidence.lower() for evidence in chapter.review_evidence
        )
        assert any(
            "official" in evidence.lower() for evidence in chapter.review_evidence
        )
    assert runtime["chapter_id"] == chapter_id
    assert runtime["chapter_no"] == chapter_no == source["chapter_no"]
    assert runtime["title"] == title == source["chapter_title"]
    assert runtime["source_url"] == source["pdf_url"]
    assert runtime["book_title"] == "Santoor"
    assert len(runtime["levels"]) == expected_levels

    for level in runtime["levels"]:
        check_stages = set(level["checks"])
        assert DEEP_CHECK_STAGES <= check_stages
        assert check_stages - DEEP_CHECK_STAGES <= {"revision_level_4"}
        independent = level["checks"]["independent_check"]
        transfer = level["checks"]["transfer_check"]
        assert independent["options"] == transfer["options"] == []
        assert (independent["passage"], independent["prompt"]) != (
            transfer["passage"],
            transfer["prompt"],
        )

    reparsed = LiveSchoolChapter.model_validate(
        json.loads((CLASS_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8"))
    )
    assert reparsed.runtime_dict() == runtime
    assert reparsed.calculated_runtime_sha256() == chapter.runtime_sha256


@pytest.mark.parametrize(
    "chapter_id",
    ("eng_c5_ch02", "eng_c5_ch03", "eng_c5_ch04", "eng_c5_ch05"),
)
def test_certifying_activity_provenance_uses_only_certifying_source_anchors(
    chapter_id,
):
    runtime = load_live_chapter_file(CLASS_ROOT / f"{chapter_id}.json").runtime_dict()
    certifying_anchor_ids = {
        anchor["anchor_id"]
        for anchor in runtime["source_anchors"]
        if anchor["required_for_chapter_certification"]
    }
    non_certifying_anchor_ids = {
        anchor["anchor_id"]
        for anchor in runtime["source_anchors"]
        if not anchor["required_for_chapter_certification"]
    }

    assert non_certifying_anchor_ids
    for level in runtime["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
            for activity in activities:
                if activity.get("evidence_role") != "certifying":
                    continue
                assert set(activity["source_anchor_ids"]) <= certifying_anchor_ids
        for check in level["checks"].values():
            if check.get("evidence_role") == "certifying":
                assert set(check["source_anchor_ids"]) <= certifying_anchor_ids


@pytest.mark.parametrize("chapter_id", CHAPTERS)
def test_owned_class5_chapter_assessment_is_diverse_and_covers_taught_skills(chapter_id):
    _, _, _, expected_skill_count = CHAPTERS[chapter_id]
    runtime = load_live_chapter_file(CLASS_ROOT / f"{chapter_id}.json").runtime_dict()
    taught_skills = {
        skill_id
        for level in runtime["levels"]
        for skill_id in level["skill_ids"]
    }
    assessment = runtime["chapter_assessment"]
    coverage = Counter(
        skill_id
        for item in assessment["items"]
        for skill_id in item["skill_ids"]
    )

    assert len(taught_skills) == expected_skill_count
    assert assessment["items_per_attempt"] == 16
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert len(assessment["items"]) == 32
    assert set(coverage) == taught_skills
    assert all(count >= 2 for count in coverage.values())
    assert sum(bool(item["options"]) for item in assessment["items"]) >= 8
    assert sum(not item["options"] for item in assessment["items"]) >= 8
    if chapter_id == "eng_c5_ch01":
        assert sum(
            item.get("grading_mode") == "strict_open_rubric"
            for item in assessment["items"]
        ) >= 4
        assert all(item.get("grading_mode") for item in assessment["items"])
    else:
        open_items = [item for item in assessment["items"] if not item["options"]]
        selected_items = [item for item in assessment["items"] if item["options"]]
        assert all(
            item.get("grading_mode") == "strict_open_rubric"
            and item.get("evaluation_mode") == "llm_rubric"
            for item in open_items
        )
        assert all(
            item.get("grading_mode") == "selected_option"
            and item.get("evaluation_mode") != "llm_rubric"
            for item in selected_items
        )


def test_chapter_one_word_floors_allow_concise_complete_answers():
    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    authored_floors: list[tuple[str, int]] = []
    for level in runtime["levels"]:
        authored_floors.extend(
            (level["level_id"], int(check["min_response_words"]))
            for check in level["checks"].values()
            if check.get("min_response_words") is not None
        )
        authored_floors.extend(
            (level["level_id"], int(activity["min_response_words"]))
            for step in level.get("teaching_steps") or []
            for activity in step.get("variant_pool") or []
            if activity.get("min_response_words") is not None
        )

    assert authored_floors
    assert max(floor for _, floor in authored_floors) <= 12
    assert all(
        floor <= 10
        for level_id, floor in authored_floors
        if level_id != "papas_spectacles_sound_lab"
    )
    assert max(
        int(item["min_response_words"])
        for item in runtime["chapter_assessment"]["items"]
        if item.get("min_response_words") is not None
    ) <= 8
    assert max(
        int(activity["min_response_words"])
        for step in runtime["levels"][3]["teaching_steps"]
        for activity in step.get("variant_pool") or []
        if activity.get("min_response_words") is not None
    ) <= 6


def test_school_public_activity_allowlist_hides_authored_grading_contract():
    public = curriculum._public_activity(
        {
            "activity_id": "chapter-1:independent:1",
            "level_id": "chapter-1",
            "kind": "independent_check",
            "title": "Explain the clue",
            "focus": "inference",
            "skill_ids": ["reading.inference_reason"],
            "teaching_block": "Answer independently.",
            "passage": "Mira carried an umbrella under a bright sky.",
            "prompt": "What did Mira expect?",
            "options": [],
            "response_mode": "paragraph",
            "pass_score": 0.8,
            "rubric_criteria": [{"id": "uses_clue"}],
            "forbidden_phrases": ["Mira expected no rain"],
            "relevance_terms": ["Mira", "umbrella", "rain"],
            "model_answer": "Mira expected rain because she carried an umbrella.",
            "accepted_answers": [],
            "can_answer": True,
        }
    )
    assert public is not None
    public_keys = set(public)

    assert {"passage", "prompt", "options", "can_answer"} <= public_keys
    assert HIDDEN_GRADING_KEYS.isdisjoint(public_keys)
