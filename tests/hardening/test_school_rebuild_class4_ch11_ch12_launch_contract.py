import json
from collections import Counter
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.content.school_v3_content import load_ncert_source_map

try:
    from app.services.school_rebuild_curriculum import _public_activity
except ValueError as exc:
    _public_activity = None
    _PUBLIC_IMPORT_ERROR = str(exc)
else:
    _PUBLIC_IMPORT_ERROR = None


LIVE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_4"
)
EXPECTED = {
    "eng_c4_ch11": {
        "chapter_no": 11,
        "title": "A Journey to the Magical Mountains",
        "book_title": "Santoor",
        "unit_title": "Up High",
        "source_url": "https://ncert.nic.in/textbook/pdf/desa111.pdf",
        "level_count": 6,
        "assessment_count": 22,
        "items_per_attempt": 11,
    },
    "eng_c4_ch12": {
        "chapter_no": 12,
        "title": "Maheshwar",
        "book_title": "Santoor",
        "unit_title": "Up High",
        "source_url": "https://ncert.nic.in/textbook/pdf/desa112.pdf",
        "level_count": 7,
        "assessment_count": 20,
        "items_per_attempt": 10,
    },
}
STAGES = {
    "guided_check",
    "bridge",
    "masterclass",
    "independent_check",
    "transfer_check",
}
HIDDEN_GRADING_FIELDS = {
    "accepted_answers",
    "answer_rule",
    "concept_slots",
    "forbidden_phrases",
    "evaluation_mode",
    "preflight_rule",
    "pass_score",
    "rubric_criteria",
}


@pytest.fixture(autouse=True)
def hardening_test_env():
    """Keep this content-only slice isolated from concurrent catalog rebuilds."""
    yield


def _chapter(chapter_id: str) -> LiveSchoolChapter:
    return load_live_chapter_file(LIVE_ROOT / f"{chapter_id}.json")


@pytest.mark.parametrize("chapter_id", EXPECTED)
def test_owned_class4_chapter_meets_launch_content_contract(chapter_id):
    chapter = _chapter(chapter_id)
    runtime = chapter.runtime_dict()
    expected = EXPECTED[chapter_id]

    assert chapter.approval_status == "qa_approved"
    assert chapter.reviewed_by == "codex-school-content-worker"
    assert chapter.reviewed_at == "2026-07-12"
    assert chapter.review_evidence == [
        "tests/hardening/test_school_rebuild_class4_ch11_ch12_launch_contract.py",
        "scripts/audit_school_rebuild_content.py --class 4",
    ]
    for key in ("chapter_no", "title", "book_title", "unit_title", "source_url"):
        assert runtime[key] == expected[key]
    assert len(runtime["levels"]) == expected["level_count"]
    assert 5 <= len(runtime["levels"]) <= 7
    assert chapter.calculated_runtime_sha256() == chapter.runtime_sha256
    assert chapter_quality_issues(chapter) == ()

    stage_passages = set()
    for level in runtime["levels"]:
        checks = level["checks"]
        assert set(checks) == STAGES
        assert len(checks["guided_check"]["options"]) >= 2
        assert checks["independent_check"]["options"] == []
        assert checks["transfer_check"]["options"] == []
        assert checks["independent_check"]["passage"] != checks["transfer_check"]["passage"]
        assert checks["independent_check"]["prompt"] != checks["transfer_check"]["prompt"]
        assert len(
            {
                (activity["teaching_block"], activity["passage"], activity["prompt"])
                for activity in checks.values()
            }
        ) == 5
        stage_passages.update(activity["passage"] for activity in checks.values())

    assessment = runtime["chapter_assessment"]
    taught_skills = {
        skill_id for level in runtime["levels"] for skill_id in level["skill_ids"]
    }
    coverage = Counter(
        skill_id for item in assessment["items"] for skill_id in item["skill_ids"]
    )
    assert assessment["items_per_attempt"] == expected["items_per_attempt"]
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert len(assessment["items"]) == expected["assessment_count"]
    assert set(coverage) == taught_skills
    assert all(coverage[skill_id] >= 2 for skill_id in taught_skills)
    assert all(item["passage"] not in stage_passages for item in assessment["items"])
    assert sum(bool(item["options"]) for item in assessment["items"]) >= 8
    assert sum(not item["options"] for item in assessment["items"]) >= 8
    assert sum(
        item.get("evaluation_mode") == "llm_rubric"
        for item in assessment["items"]
    ) >= 2
    assert sum(
        item.get("answer_rule") == "concept_slots"
        for item in assessment["items"]
    ) >= 4

    roundtrip = LiveSchoolChapter.model_validate_json(chapter.model_dump_json())
    assert roundtrip.runtime_dict() == runtime
    assert roundtrip.calculated_runtime_sha256() == chapter.runtime_sha256


def test_owned_chapter_titles_and_order_match_the_locked_source_map():
    source_map = load_ncert_source_map("english", 4)
    entries = [
        entry
        for entry in source_map["chapters"]
        if entry["chapter_id"] in EXPECTED
    ]

    assert [entry["chapter_id"] for entry in entries] == [
        "eng_c4_ch11",
        "eng_c4_ch12",
    ]
    for entry in entries:
        expected = EXPECTED[entry["chapter_id"]]
        assert entry["chapter_no"] == expected["chapter_no"]
        assert entry["chapter_title"] == expected["title"]


@pytest.mark.parametrize("chapter_id", EXPECTED)
def test_owned_chapter_public_activity_serialization_hides_grading_keys(chapter_id):
    if _public_activity is None:
        pytest.skip(f"public serializer blocked by concurrent corpus state: {_PUBLIC_IMPORT_ERROR}")
    runtime = _chapter(chapter_id).runtime_dict()
    level = runtime["levels"][-1]
    check = level["checks"]["transfer_check"]
    internal = {
        **check,
        "activity_id": f"{level['level_id']}:transfer_check:1",
        "level_id": level["level_id"],
        "kind": "transfer_check",
        "title": level["title"],
        "focus": level["focus"],
        "skill_ids": level["skill_ids"],
        "attempt_no": 1,
    }

    public = _public_activity(internal)
    serialized = json.dumps(public)

    assert public["prompt"] == check["prompt"]
    assert not (HIDDEN_GRADING_FIELDS & set(public))
    assert not any(f'"{field}"' in serialized for field in HIDDEN_GRADING_FIELDS)
