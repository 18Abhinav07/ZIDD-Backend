import json
from collections import Counter
from pathlib import Path

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services.school_rebuild_curriculum import _public_activity


CHAPTER_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
CHAPTERS = (
    (
        "eng_c5_ch04.json",
        "eng_c5_ch04",
        4,
        "The Wise Parrot",
        "My Colourful World",
        "https://ncert.nic.in/textbook/pdf/eesa104.pdf",
    ),
    (
        "eng_c5_ch05.json",
        "eng_c5_ch05",
        5,
        "The Frog",
        "Water",
        "https://ncert.nic.in/textbook/pdf/eesa105.pdf",
    ),
)
STAGES = (
    "guided_check",
    "bridge",
    "masterclass",
    "independent_check",
    "transfer_check",
)


def _loaded(filename: str):
    return load_live_chapter_file(CHAPTER_ROOT / filename)


def test_owned_class5_chapters_keep_source_order_and_launch_depth():
    for filename, chapter_id, chapter_no, title, unit_title, source_url in CHAPTERS:
        chapter = _loaded(filename)
        runtime = chapter.runtime_dict()

        assert chapter.approval_status == "qa_approved"
        assert chapter.reviewed_by
        assert chapter.reviewed_at
        assert chapter.review_evidence
        assert runtime["chapter_id"] == chapter_id
        assert runtime["chapter_no"] == chapter_no
        assert runtime["title"] == title
        assert runtime["book_title"] == "Santoor"
        assert runtime["unit_title"] == unit_title
        assert runtime["source_url"] == source_url
        assert 5 <= len(runtime["levels"]) <= 7
        assert not chapter_quality_issues(chapter)


def test_every_level_has_five_distinct_stages_and_fresh_transfer_evidence():
    for filename, *_ in CHAPTERS:
        runtime = _loaded(filename).runtime_dict()
        for level in runtime["levels"]:
            checks = level["checks"]
            assert tuple(checks) == STAGES
            signatures = {
                (check["teaching_block"], check["passage"], check["prompt"])
                for check in checks.values()
            }
            assert len(signatures) == 5

            independent = checks["independent_check"]
            transfer = checks["transfer_check"]
            assert independent["options"] == transfer["options"] == []
            assert independent["passage"] != transfer["passage"]
            assert independent["prompt"] != transfer["prompt"]


def test_chapter_assessments_are_balanced_and_cover_each_taught_skill_twice():
    for filename, *_ in CHAPTERS:
        runtime = _loaded(filename).runtime_dict()
        assessment = runtime["chapter_assessment"]
        taught = {
            skill_id
            for level in runtime["levels"]
            for skill_id in level["skill_ids"]
        }
        coverage = Counter(
            skill_id
            for item in assessment["items"]
            for skill_id in item["skill_ids"]
        )

        assert 10 <= assessment["items_per_attempt"] <= 20
        assert assessment["pass_score"] == 0.8
        assert len(assessment["items"]) >= 20
        assert set(coverage) == taught
        assert all(coverage[skill_id] >= 2 for skill_id in taught)
        assert sum(bool(item["options"]) for item in assessment["items"]) >= 4
        assert sum(not item["options"] for item in assessment["items"]) >= 4
        assert any(
            item.get("evaluation_mode") == "llm_rubric"
            for item in assessment["items"]
        )
        assert any(
            item.get("answer_rule") == "concept_slots"
            for item in assessment["items"]
        )


def test_authored_files_validate_hash_round_trip_and_public_activity_is_safe():
    hidden_fields = {
        "accepted_answers",
        "answer_rule",
        "concept_slots",
        "evaluation_mode",
        "forbidden_phrases",
        "ordered_concept_slot_ids",
        "pass_score",
        "preflight_rule",
        "rubric_criteria",
    }

    for filename, *_ in CHAPTERS:
        path = CHAPTER_ROOT / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        chapter = LiveSchoolChapter.model_validate(payload)
        assert chapter.calculated_runtime_sha256() == payload["runtime_sha256"]
        assert chapter.runtime_dict() == _loaded(filename).runtime_dict()

        check = chapter.runtime_dict()["levels"][0]["checks"]["transfer_check"]
        public = _public_activity(
            {
                "activity_id": "safe-transfer:1",
                "level_id": "safe-transfer",
                "kind": "transfer_check",
                "title": "Transfer",
                "focus": "fresh evidence",
                "skill_ids": ["reading.sentence_comprehension"],
                "attempt_no": 1,
                **check,
            }
        )
        assert public is not None
        assert hidden_fields.isdisjoint(public)
        assert hidden_fields.isdisjoint(json.loads(json.dumps(public)))
