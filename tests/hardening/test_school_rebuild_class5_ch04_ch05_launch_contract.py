import json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from app.content.school.standards import locked_english_skill_ids
from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services.school_rebuild_curriculum import _public_activity
from scripts.build_school_class5_deep_chapter import (
    build_deep_chapter,
    load_manifest,
)


CHAPTER_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
MANIFEST_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_manifests"
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
CHECK_KINDS = {
    "guided_check",
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
    "independent_check",
    "transfer_check",
}
TEACHING_PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
POOLED_PHASES = set(TEACHING_PHASES[2:])
REHEARSED_ASSESSMENT_IDS = {
    "eng_c5_ch04": {
        "eng_c5_ch04_assess_a12",
        "eng_c5_ch04_assess_b06",
        "eng_c5_ch04_assess_b15",
    },
    "eng_c5_ch05": {
        "eng_c5_ch05_assess_a04",
        "eng_c5_ch05_assess_a07",
        "eng_c5_ch05_assess_a10",
        "eng_c5_ch05_assess_a14",
        "eng_c5_ch05_assess_b04",
        "eng_c5_ch05_assess_b06",
        "eng_c5_ch05_assess_b07",
        "eng_c5_ch05_assess_b13",
    },
}


def _loaded(filename: str):
    return load_live_chapter_file(CHAPTER_ROOT / filename)


def _task_text(activity: dict) -> str:
    return " ".join(
        f"{activity['passage']} {activity['prompt']}".casefold().split()
    )


def _assert_four_fresh_certifying_variants_per_level(runtime: dict) -> None:
    chapter_passages = set()

    for level in runtime["levels"]:
        activities_by_phase = {}
        for step in level["teaching_steps"]:
            activities_by_phase[step["phase"]] = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )

        for phase in ("transfer", "review"):
            variants = activities_by_phase[phase]
            assert len(variants) >= 4, (level["level_id"], phase)

            passages = [
                " ".join(item["passage"].casefold().split()) for item in variants
            ]
            prompts = [
                " ".join(item["prompt"].casefold().split()) for item in variants
            ]
            assert len(passages) == len(set(passages))
            assert len(prompts) == len(set(prompts))
            assert chapter_passages.isdisjoint(passages)
            chapter_passages.update(passages)

            for index, left in enumerate(variants):
                for right in variants[index + 1 :]:
                    assert SequenceMatcher(
                        None,
                        _task_text(left),
                        _task_text(right),
                    ).ratio() < 0.68

            other_phase_activities = [
                activity
                for other_phase, activities in activities_by_phase.items()
                if other_phase != phase
                for activity in activities
            ]
            covered_skills = set()
            for activity in variants:
                assert max(
                    SequenceMatcher(
                        None,
                        _task_text(activity),
                        _task_text(other),
                    ).ratio()
                    for other in other_phase_activities
                ) < 0.65
                claimed_skills = set(activity["knowledge_components"])
                assert claimed_skills
                assert claimed_skills <= set(level["skill_ids"])
                covered_skills.update(claimed_skills)
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["evaluation_mode"] == "llm_rubric"
                assert activity["evidence_role"] == "certifying"
                assert activity["certifying_language"] == "en"
                assert activity["pass_score"] == 0.8
                assert activity["model_answer"].strip()
                assert activity["forbidden_phrases"]
                assert len(activity["relevance_terms"]) >= 2

                criteria = activity["rubric_criteria"]
                slots = activity["concept_slots"]
                assert [criterion["id"] for criterion in criteria] == [
                    slot["id"] for slot in slots
                ]
                assert all(criterion["required"] for criterion in criteria)
                assert all(criterion["description"].strip() for criterion in criteria)
                assert all(slot["description"].strip() for slot in slots)
                assert all(slot["any_of"] for slot in slots)
            assert covered_skills == set(level["skill_ids"])


def _all_learning_activities(runtime: dict):
    for level in runtime["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]
        yield from level["checks"].values()


def test_owned_manifests_compile_to_the_reviewed_runtime_without_drift():
    for filename, chapter_id, *_ in CHAPTERS:
        built = LiveSchoolChapter.model_validate(
            build_deep_chapter(
                None,
                load_manifest(MANIFEST_ROOT / f"{chapter_id}.py"),
            )
        )
        reviewed = _loaded(filename)

        assert built.runtime_dict() == reviewed.runtime_dict()
        assert built.runtime_sha256 == reviewed.runtime_sha256


def test_owned_class5_chapters_keep_source_order_and_deep_launch_depth():
    for filename, chapter_id, chapter_no, title, unit_title, source_url in CHAPTERS:
        chapter = _loaded(filename)
        runtime = chapter.runtime_dict()

        assert chapter.approval_status == "agent_reviewed"
        assert chapter.reviewed_by
        assert chapter.reviewed_at
        assert chapter.review_evidence
        assert runtime["chapter_id"] == chapter_id
        assert runtime["chapter_no"] == chapter_no
        assert runtime["title"] == title
        assert runtime["book_title"] == "Santoor"
        assert runtime["unit_title"] == unit_title
        assert runtime["source_url"] == source_url
        assert 7 <= len(runtime["levels"]) <= 9
        taught_skills = {
            skill_id
            for level in runtime["levels"]
            for skill_id in level["skill_ids"]
        }
        assert len(taught_skills) <= 16
        assert taught_skills <= set(locked_english_skill_ids())

        anchors = runtime["source_anchors"]
        anchor_ids = {anchor["anchor_id"] for anchor in anchors}
        referenced_anchor_ids = {
            anchor_id
            for level in runtime["levels"]
            for anchor_id in level["source_anchor_ids"]
        }
        required_anchor_ids = {
            anchor["anchor_id"]
            for anchor in anchors
            if anchor["required_for_chapter_certification"]
        }
        assert referenced_anchor_ids == required_anchor_ids
        assert referenced_anchor_ids <= anchor_ids
        for anchor in anchors:
            if anchor["coverage_treatment"] in {
                "guided_only",
                "textbook_companion",
                "offline_group_activity",
            }:
                assert not anchor["required_for_chapter_certification"]
        assert not chapter_quality_issues(chapter)


def test_every_level_has_six_phase_loop_two_fresh_variants_and_five_supports():
    for filename, *_ in CHAPTERS:
        runtime = _loaded(filename).runtime_dict()
        for level in runtime["levels"]:
            checks = level["checks"]
            assert set(checks) == CHECK_KINDS
            signatures = {
                (check["teaching_block"], check["passage"], check["prompt"])
                for check in checks.values()
            }
            assert len(signatures) == len(CHECK_KINDS)

            steps = level["teaching_steps"]
            assert tuple(step["phase"] for step in steps) == TEACHING_PHASES
            for step in steps:
                variants = step.get("variant_pool") or []
                if step["phase"] in POOLED_PHASES:
                    assert len(variants) >= 2
                    variant_ids = [variant["variant_id"] for variant in variants]
                    assert len(variant_ids) == len(set(variant_ids))
                    variant_signatures = {
                        (
                            variant["teaching_block"],
                            variant["passage"],
                            variant["prompt"],
                        )
                        for variant in variants
                    }
                    assert len(variant_signatures) == len(variants)

            independent = checks["independent_check"]
            transfer = checks["transfer_check"]
            assert independent["options"] == transfer["options"] == []
            assert independent["passage"] != transfer["passage"]
            assert independent["prompt"] != transfer["prompt"]


def test_chapter_assessments_have_two_fresh_complete_sixteen_item_forms():
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

        assert assessment["items_per_attempt"] == 16
        assert assessment["pass_score"] == 0.8
        assert assessment["max_attempts"] == 2
        assert len(assessment["items"]) == 32
        assert set(coverage) == taught
        assert all(coverage[skill_id] >= 2 for skill_id in taught)
        assert len(taught) <= assessment["items_per_attempt"]

        for form in (
            assessment["items"][:16],
            assessment["items"][16:],
        ):
            form_skills = {
                skill_id for item in form for skill_id in item["skill_ids"]
            }
            assert form_skills == taught
            assert sum(bool(item["options"]) for item in form) >= 4
            assert sum(not item["options"] for item in form) >= 4

        assert any(
            item.get("evaluation_mode") == "llm_rubric"
            for item in assessment["items"]
        )
        assert all(
            not skill_id.startswith(("listening.", "speaking.", "oral.", "drawing."))
            for skill_id in taught
        )


def test_reviewed_chapter_four_and_five_assessments_use_fresh_transfer_cases():
    for filename, chapter_id, *_ in CHAPTERS:
        runtime = _loaded(filename).runtime_dict()
        teaching_tasks = [
            _task_text(activity) for activity in _all_learning_activities(runtime)
        ]
        reviewed = {
            item["item_id"]: item
            for item in runtime["chapter_assessment"]["items"]
            if item["item_id"] in REHEARSED_ASSESSMENT_IDS[chapter_id]
        }

        assert set(reviewed) == REHEARSED_ASSESSMENT_IDS[chapter_id]
        for item in reviewed.values():
            assessment_task = _task_text(item)
            assert max(
                SequenceMatcher(None, assessment_task, teaching_task).ratio()
                for teaching_task in teaching_tasks
            ) < 0.65


def test_owned_chapters_have_four_fresh_transfer_and_review_variants_per_level():
    for filename, *_ in CHAPTERS:
        _assert_four_fresh_certifying_variants_per_level(
            _loaded(filename).runtime_dict()
        )


def test_wise_parrot_bird_care_keeps_procedural_sequencing_through_transfer():
    runtime = _loaded("eng_c5_ch04.json").runtime_dict()
    level = next(
        level
        for level in runtime["levels"]
        if level["level_id"] == "wise_parrot_bird_care_procedure"
    )
    activities_by_phase = {
        step["phase"]: step["variant_pool"]
        for step in level["teaching_steps"]
        if step.get("variant_pool") is not None
    }
    sequence_markers = ("first", "order", "sequence", "step", "procedure")

    for phase in ("guided_practice", "independent_application", "transfer"):
        for activity in activities_by_phase[phase]:
            task_text = _task_text(activity)
            assert activity.get("ordered_concept_slot_ids") or any(
                marker in task_text for marker in sequence_markers
            ), (phase, activity["variant_id"])

    transfer = level["checks"]["transfer_check"]
    assert transfer["grading_mode"] == "strict_open_rubric"
    assert "writing.procedure" in transfer["knowledge_components"]
    assert transfer["ordered_concept_slot_ids"] == [
        criterion["id"] for criterion in transfer["rubric_criteria"]
    ]
    assert "report" not in _task_text(transfer)


def test_wise_parrot_story_support_rebuilds_paragraph_construction():
    runtime = _loaded("eng_c5_ch04.json").runtime_dict()
    level = next(
        level
        for level in runtime["levels"]
        if level["level_id"] == "wise_parrot_story_continuation"
    )

    for check_name in (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    ):
        check = level["checks"][check_name]
        assert "writing.paragraph" in check["knowledge_components"]
        assert check["grading_mode"] == "strict_open_rubric"
        assert check["interaction_type"] in {
            "paragraph_text",
            "creative_continuation",
        }
        assert check["min_response_words"] >= 18


def test_authored_files_validate_hash_round_trip_and_public_activity_is_safe():
    hidden_fields = {
        "accepted_answers",
        "answer_rule",
        "concept_slots",
        "evaluation_mode",
        "forbidden_phrases",
        "model_answer",
        "ordered_concept_slot_ids",
        "pass_score",
        "preflight_rule",
        "relevance_terms",
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
