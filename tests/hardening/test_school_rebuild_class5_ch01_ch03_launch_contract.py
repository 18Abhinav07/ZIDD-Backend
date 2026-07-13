import ast
import json
from collections import Counter
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter


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
CURRICULUM_SERVICE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "services"
    / "school_rebuild_curriculum.py"
)
CHAPTERS = {
    "eng_c5_ch01": (1, "Papa's Spectacles", 6, 10),
    "eng_c5_ch02": (2, "Gone with the Scooter", 6, 12),
    "eng_c5_ch03": (3, "The Rainbow", 7, 12),
}
CHECK_STAGES = {
    "guided_check",
    "bridge",
    "masterclass",
    "independent_check",
    "transfer_check",
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

    assert chapter.approval_status == "qa_approved"
    assert chapter.reviewed_by == "Codex School English launch-content QA"
    assert chapter.reviewed_at == "2026-07-12T12:00:00+05:30"
    assert chapter.review_evidence == [
        "tests/hardening/test_school_rebuild_class5_ch01_ch03_launch_contract.py",
        "scripts/audit_school_rebuild_content.py --class 5",
        "Original Zidd-authored English content; NCERT structural alignment reviewed against the source map",
    ]
    assert runtime["chapter_id"] == chapter_id
    assert runtime["chapter_no"] == chapter_no == source["chapter_no"]
    assert runtime["title"] == title == source["chapter_title"]
    assert runtime["source_url"] == source["pdf_url"]
    assert runtime["book_title"] == "Santoor"
    assert len(runtime["levels"]) == expected_levels

    for level in runtime["levels"]:
        assert set(level["checks"]) == CHECK_STAGES
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
    assert assessment["items_per_attempt"] == 12
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert len(assessment["items"]) == 24
    assert set(coverage) == taught_skills
    assert all(count >= 2 for count in coverage.values())
    assert sum(bool(item["options"]) for item in assessment["items"]) >= 8
    assert sum(not item["options"] for item in assessment["items"]) >= 8
    assert sum(
        item.get("answer_rule") == "concept_slots"
        for item in assessment["items"]
    ) >= 6
    assert sum(
        item.get("evaluation_mode") == "llm_rubric"
        for item in assessment["items"]
    ) >= 2


def test_school_public_activity_allowlist_hides_authored_grading_contract():
    tree = ast.parse(CURRICULUM_SERVICE_PATH.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_public_activity"
    )
    returned_dict = next(
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
    )
    public_keys = {
        key.value
        for key in returned_dict.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    }

    assert {"passage", "prompt", "options", "can_answer"} <= public_keys
    assert HIDDEN_GRADING_KEYS.isdisjoint(public_keys)
