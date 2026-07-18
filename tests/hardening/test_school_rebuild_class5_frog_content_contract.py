import hashlib
import json
from collections import Counter
from pathlib import Path

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services.school_rebuild_curriculum import (
    _evaluate_deterministic_answer,
    _select_chapter_assessment_items,
)
from scripts.build_school_class5_deep_chapter import (
    build_deep_chapter,
    load_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_PATH = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
    / "eng_c5_ch05.json"
)
MANIFEST_PATH = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_5"
    / "eng_c5_ch05.py"
)
TEACHING_PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
POOLED_PHASES = set(TEACHING_PHASES[2:])
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
EXPECTED_LEVEL_SKILLS = {
    "frog_poem_meaning": {
        "reading.poetic_language",
        "reading.sentence_comprehension",
    },
    "frog_life_stage_and_words": {
        "reading.event_sequence",
        "reading.word_meaning_context",
    },
    "frog_adaptation_reasoning": {
        "reading.inference_reason",
        "writing.reason_answer",
    },
    "frog_comparison": {
        "reading.sentence_comprehension",
        "writing.compare_contrast",
    },
    "frog_calls_and_connectors": {
        "grammar.connectors_because_and_but",
        "writing.complete_sentence",
    },
    "frog_sentence_sequence": {
        "grammar.sentence_order",
        "grammar.adverbs",
    },
    "frog_friendly_reply": {
        "reading.sentence_comprehension",
        "writing.friendly_message",
        "writing.complete_sentence",
    },
    "frog_instruction_and_research": {
        "writing.procedure",
        "research.information_selection",
    },
}
EXPECTED_EPISODE_KINDS = {
    "frog_poem_meaning": "meaning_encounter",
    "frog_life_stage_and_words": "comprehension_studio",
    "frog_adaptation_reasoning": "comprehension_studio",
    "frog_comparison": "expression_workshop",
    "frog_calls_and_connectors": "language_lab",
    "frog_sentence_sequence": "language_lab",
    "frog_friendly_reply": "expression_workshop",
    "frog_instruction_and_research": "application_mission",
}
EXPECTED_SECTIONS = {
    "Let us Recite",
    "Let us Think",
    "Let us Learn",
    "Let us Speak",
    "Let us Listen",
    "Let us Write",
    "Let us Do",
    "Let us Explore",
}
REQUIRED_CERTIFICATION_ANCHORS = {
    "eng_c5_ch05:think:2",
    "eng_c5_ch05:learn:3-4",
    "eng_c5_ch05:write:7",
    "eng_c5_ch05:explore:10",
}
COMPANION_TREATMENTS = {
    "guided_only",
    "textbook_companion",
    "offline_group_activity",
}
FALSE_MODALITY_PREFIXES = ("listening.", "speaking.", "oral.", "drawing.")


def _runtime() -> dict:
    return load_live_chapter_file(LIVE_PATH).runtime_dict()


def _iter_teaching_activities(runtime: dict):
    for level in runtime["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            yield from step.get("variant_pool") or []


def _iter_gradable_activities(runtime: dict):
    for level in runtime["levels"]:
        yield from level["checks"].values()
    yield from _iter_teaching_activities(runtime)
    yield from runtime["chapter_assessment"]["items"]


def _signature(activity: dict) -> tuple[str, str, str]:
    return tuple(
        " ".join(activity[field].split())
        for field in ("teaching_block", "passage", "prompt")
    )


def test_frog_manifest_builds_agent_reviewed_original_runtime_without_drift():
    manifest_payload = load_manifest(MANIFEST_PATH).model_dump(mode="json")
    authorship = manifest_payload["chapter"]["authorship"]
    reviewed = load_live_chapter_file(LIVE_PATH)
    runtime = reviewed.runtime_dict()
    raw_runtime = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    built = LiveSchoolChapter.model_validate(
        build_deep_chapter(None, load_manifest(MANIFEST_PATH))
    )

    assert manifest_payload["schema_version"] == "school-class5-deep-manifest-v1"
    assert authorship["zidd_authored_original"] is True
    assert authorship["textbook_body_or_questions_copied"] is False
    assert authorship["source_analysis_reference"]
    assert reviewed.approval_status == "agent_reviewed"
    assert reviewed.reviewed_by
    assert reviewed.reviewed_at
    assert reviewed.review_evidence
    assert any("manifest" in evidence.lower() for evidence in reviewed.review_evidence)
    manifest_hash = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    assert (
        f"Manifest hash SHA-256: {manifest_hash}" in reviewed.review_evidence
    )
    assert runtime["chapter_id"] == "eng_c5_ch05"
    assert runtime["chapter_no"] == 5
    assert runtime["title"] == "The Frog"
    assert runtime["book_title"] == "Santoor"
    assert runtime["unit_title"] == "Water"
    assert runtime["source_url"] == "https://ncert.nic.in/textbook/pdf/eesa105.pdf"
    assert runtime["content_version"] == manifest_payload["chapter"]["content_version"]
    assert runtime["certification_version"] == manifest_payload["chapter"][
        "certification_version"
    ]
    assert len(runtime["levels"]) == 8
    assert built.runtime_dict() == runtime
    assert built.runtime_sha256 == reviewed.runtime_sha256
    assert raw_runtime["runtime_sha256"] == reviewed.runtime_sha256
    assert reviewed.calculated_runtime_sha256() == reviewed.runtime_sha256


def test_frog_levels_cover_chapter_semantics_sources_and_six_phase_loops():
    runtime = _runtime()
    levels = runtime["levels"]
    taught_skills = {
        skill_id for level in levels for skill_id in level["skill_ids"]
    }

    assert tuple(level["level_id"] for level in levels) == tuple(
        EXPECTED_LEVEL_SKILLS
    )
    assert taught_skills == set().union(*EXPECTED_LEVEL_SKILLS.values())
    assert len(taught_skills) == 14

    teaching_signatures = []
    for level in levels:
        level_id = level["level_id"]
        assert set(level["skill_ids"]) == EXPECTED_LEVEL_SKILLS[level_id]
        assert level["episode_kind"] == EXPECTED_EPISODE_KINDS[level_id]
        assert level["source_anchor_ids"]
        assert set(level["checks"]) == CHECK_KINDS
        assert len({_signature(check) for check in level["checks"].values()}) == len(
            CHECK_KINDS
        )

        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == TEACHING_PHASES
        for step in steps:
            variants = step.get("variant_pool") or []
            if step["phase"] in POOLED_PHASES:
                assert len(variants) >= 2
        teaching_signatures.extend(
            _signature(activity)
            for activity in _iter_teaching_activities({"levels": [level]})
        )

    assert len(teaching_signatures) == len(set(teaching_signatures))

    anchors = runtime["source_anchors"]
    anchor_ids = {anchor["anchor_id"] for anchor in anchors}
    certifying_anchor_ids = {
        anchor_id
        for level in levels
        for anchor_id in level["source_anchor_ids"]
    }
    companion_anchor_ids = {
        anchor_id
        for level in levels
        for anchor_id in level.get("companion_source_anchor_ids", [])
    }
    assert {anchor["section_label"] for anchor in anchors} == EXPECTED_SECTIONS
    required_anchor_ids = {
        anchor["anchor_id"]
        for anchor in anchors
        if anchor["required_for_chapter_certification"]
    }
    optional_anchor_ids = anchor_ids - required_anchor_ids
    assert certifying_anchor_ids == required_anchor_ids
    assert companion_anchor_ids == optional_anchor_ids
    assert certifying_anchor_ids | companion_anchor_ids == anchor_ids
    assert required_anchor_ids == REQUIRED_CERTIFICATION_ANCHORS
    for level in levels:
        companions = set(level.get("companion_source_anchor_ids", []))
        if not companions:
            continue
        connect = next(
            step for step in level["teaching_steps"] if step["phase"] == "connect"
        )["activity"]
        assert companions <= set(connect["source_anchor_ids"])
        for activity in _iter_teaching_activities({"levels": [level]}):
            if activity.get("evidence_role") == "certifying":
                assert not companions.intersection(activity["source_anchor_ids"])
    assert all(
        not anchor["required_for_chapter_certification"]
        for anchor in anchors
        if anchor["coverage_treatment"] in COMPANION_TREATMENTS
    )


def test_frog_strict_open_items_have_complete_llm_rubric_contracts():
    gradable = [
        activity
        for activity in _iter_gradable_activities(_runtime())
        if activity.get("grading_mode")
    ]
    strict_open = [activity for activity in gradable if not activity["options"]]
    selected = [activity for activity in gradable if activity["options"]]

    assert strict_open
    assert selected
    assert all(
        activity.get("evaluation_mode") == "llm_rubric"
        and activity["grading_mode"] == "strict_open_rubric"
        for activity in strict_open
    )
    assert all(
        activity.get("evaluation_mode") != "llm_rubric"
        and activity["grading_mode"] == "selected_option"
        for activity in selected
    )

    for activity in strict_open:
        criteria = activity["rubric_criteria"]
        concept_slots = activity["concept_slots"]
        criterion_ids = [criterion["id"] for criterion in criteria]
        concept_slot_ids = [slot["id"] for slot in concept_slots]

        assert activity["accepted_answers"] == []
        assert activity["preflight_rule"] == "relevant_english_response"
        assert activity["pass_score"] == 0.8
        if "certifying_language" in activity:
            assert activity["certifying_language"] == "en"
        else:
            assert activity.get("evidence_role") == "supported"
        assert activity["model_answer"].strip()
        assert activity["relevance_terms"]
        assert activity["forbidden_phrases"]
        assert activity["min_response_words"] > 0
        assert criterion_ids == concept_slot_ids
        assert len(criterion_ids) == len(set(criterion_ids))
        assert all(criterion["required"] is True for criterion in criteria)
        assert all(criterion["min_quality"] >= 0.7 for criterion in criteria)
        assert all(slot["description"] and slot["any_of"] for slot in concept_slots)
        assert set(activity.get("ordered_concept_slot_ids") or []) <= set(
            concept_slot_ids
        )


def test_frog_deterministic_assessment_items_accept_only_the_authored_choice():
    assessment_items = _runtime()["chapter_assessment"]["items"]
    deterministic_items = [item for item in assessment_items if item["options"]]

    assert len(deterministic_items) == 18
    assert all(
        item.get("evaluation_mode") != "llm_rubric"
        and item["grading_mode"] == "selected_option"
        for item in deterministic_items
    )

    for item in deterministic_items:
        assert len(item["options"]) == 4
        assert len(item["accepted_answers"]) == 1
        accepted = item["accepted_answers"][0]
        assert accepted in item["options"]
        assert _evaluate_deterministic_answer(item, accepted)["correct"] is True
        for distractor in set(item["options"]) - {accepted}:
            assert (
                _evaluate_deterministic_answer(item, distractor)["correct"]
                is False
            )
        assert (
            _evaluate_deterministic_answer(
                item,
                "unrelated words that are not an authored option",
            )["correct"]
            is False
        )


def test_frog_assessment_forms_are_fresh_complete_and_bound_llm_cost():
    runtime = _runtime()
    assessment = runtime["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id
        for level in runtime["levels"]
        for skill_id in level["skill_ids"]
    }
    coverage = Counter(
        skill_id for item in items for skill_id in item["skill_ids"]
    )
    first = _select_chapter_assessment_items(
        items,
        item_count=assessment["items_per_attempt"],
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=assessment["items_per_attempt"],
        attempt_no=2,
        used_item_ids=first_ids,
    )
    second_ids = {item["item_id"] for item in second}

    assert assessment["items_per_attempt"] == 16
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert len(items) == 32
    assert len({item["item_id"] for item in items}) == 32
    assert set(coverage) == taught_skills
    assert all(coverage[skill_id] >= 2 for skill_id in taught_skills)
    assert len(first) == len(second) == 16
    assert first_ids.isdisjoint(second_ids)
    assert first_ids | second_ids == {item["item_id"] for item in items}

    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills
        assert sum(bool(item["options"]) for item in form) == 9
        assert sum(
            item.get("evaluation_mode") == "llm_rubric" for item in form
        ) == 7
        assert sum(
            "writing.compare_contrast" in item["skill_ids"] for item in form
        ) == 1
        assert sum(
            "writing.friendly_message" in item["skill_ids"] for item in form
        ) == 1

    teaching_passages = {
        " ".join(activity["passage"].split())
        for activity in _iter_teaching_activities(runtime)
    }
    assert all(" ".join(item["passage"].split()) not in teaching_passages for item in items)
    assert len({(item["passage"], item["prompt"]) for item in items}) == 32


def test_frog_certification_does_not_claim_unobserved_modalities():
    runtime = _runtime()
    certifying = [
        activity
        for activity in _iter_gradable_activities(runtime)
        if activity.get("evidence_role") == "certifying"
    ]
    assessed_skills = {
        skill_id
        for item in runtime["chapter_assessment"]["items"]
        for skill_id in item["skill_ids"]
    }

    assert certifying
    for activity in certifying:
        assert activity["interaction_type"] in {
            "dialogue",
            "evidence_text",
            "paragraph_text",
        }
        assert activity["certifying_language"] == "en"
        assert activity["knowledge_components"]
        assert not any(
            skill_id.startswith(FALSE_MODALITY_PREFIXES)
            for skill_id in activity["knowledge_components"]
        )

    assert not any(
        skill_id.startswith(FALSE_MODALITY_PREFIXES)
        for skill_id in assessed_skills
    )
    source_by_label = {
        anchor["section_label"]: anchor for anchor in runtime["source_anchors"]
    }
    assert not source_by_label["Let us Listen"][
        "required_for_chapter_certification"
    ]
    assert not source_by_label["Let us Speak"][
        "required_for_chapter_certification"
    ]
