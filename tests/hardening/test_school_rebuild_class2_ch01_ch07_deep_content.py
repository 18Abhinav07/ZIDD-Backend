from __future__ import annotations

import json
import re
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_v3_taxonomy import (
    locked_english_skill_ids,
    locked_english_taxonomy,
)
from app.services.school_rebuild_curriculum import _select_chapter_assessment_items
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from scripts.build_school_deep_chapter import load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPTER_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_2"
)
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_2"
)
EXTRACT_ROOT = Path("/tmp/zidd-ncert-class2-3")
CHAPTER_IDS = tuple(f"eng_c2_ch{chapter_no:02d}" for chapter_no in range(1, 8))
CHAPTER_PAGES = {
    "eng_c2_ch01": (1, 7),
    "eng_c2_ch02": (8, 17),
    "eng_c2_ch03": (18, 26),
    "eng_c2_ch04": (27, 36),
    "eng_c2_ch05": (37, 41),
    "eng_c2_ch06": (42, 47),
    "eng_c2_ch07": (48, 53),
}
CHAPTER_LEXICON = {
    "eng_c2_ch01": {"bicycle", "helmet", "wheel", "brake"},
    "eng_c2_ch02": {"game", "playground", "team", "handmade"},
    "eng_c2_ch03": {"animal", "movement", "action", "can"},
    "eng_c2_ch04": {"sense", "touch", "sound", "respectful"},
    "eng_c2_ch05": {"journey", "vehicle", "travel", "return"},
    "eng_c2_ch06": {"route", "landmark", "school", "direction"},
    "eng_c2_ch07": {"town", "street", "place", "position"},
}
COMPACT_PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
SUPPORT_CHECKS = {
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
}
COMPANION_TREATMENTS = {
    "guided_only",
    "optional_creative",
    "offline_group_activity",
    "textbook_companion",
}
UNOBSERVABLE_TEXT_ONLY_SKILLS = {
    "speaking.recitation",
    "speaking.multilingual_expression",
    "listening.sound_discrimination",
}
PRODUCTIVE_PREFIXES = ("writing.", "speaking.", "oral.")
WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
MIN_VARIANTS = {
    "guided_practice": 4,
    "independent_application": 4,
    "transfer": 4,
    "review": 4,
}
AUTHORING_JARGON_RE = re.compile(
    r"\b(?:in\s+)?(?:guided|independent|transfer|review|masterclass|assessment|"
    r"co construct|revision level [1-3])\s+example(?:\s+\d+)?\b|"
    r"\bco construct\b|\brevision level [1-3]\b|(?:^|[.!?]\s+)transfer\b",
    re.IGNORECASE,
)
BANNED_IMPLAUSIBLE_DISTRACTORS = {
    "the bicycle has no wheels.",
    "the road is made of glass.",
    "the light needs water.",
    "the game ends forever.",
    "the teams leave before the tear.",
    "the cotton becomes a whistle.",
    "bea starts a new race.",
    "bea hides the rope.",
    "bea unties every shoe.",
    "the barn follows the calf.",
    "the calf flies away.",
    "the pier boards first.",
    "the family flies away.",
    "the clinic crosses first.",
    "the path ends at home.",
    "the centre crosses first.",
    "it returns home.",
    "the street leaves town.",
    "the fountain crosses the road.",
    "the seed drinks first.",
}


def _payload(chapter_id: str) -> dict:
    return json.loads(
        (CHAPTER_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )


def _manifest_path(chapter_id: str) -> Path:
    candidates = [
        MANIFEST_ROOT / f"{chapter_id}.py",
        MANIFEST_ROOT / f"{chapter_id}.json",
    ]
    existing = [path for path in candidates if path.is_file()]
    assert len(existing) == 1, f"expected one manifest for {chapter_id}: {existing}"
    return existing[0]


def _activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]


def _all_runtime_activities(payload: dict):
    chapter_id = payload["chapter_id"]
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
            for index, activity in enumerate(activities, start=1):
                probe_id = activity.get("variant_id") or (
                    f"{chapter_id}:{level['level_id']}:{step['phase']}:{index}"
                )
                yield probe_id, activity
        for check_name in SUPPORT_CHECKS:
            yield (
                f"{chapter_id}:{level['level_id']}:{check_name}",
                level["checks"][check_name],
            )
    for item in payload["chapter_assessment"]["items"]:
        yield item["item_id"], item


def _validate_model_answer(activity: dict, *, probe_id: str):
    answer = activity["model_answer"]
    skill_ids = list(
        activity.get("skill_ids")
        or activity.get("knowledge_components")
        or ()
    )
    authority = {
        **activity,
        "activity_id": probe_id,
        "skill_ids": skill_ids,
    }
    aliases_by_id = {
        slot["id"]: [
            alias
            for alias in slot["any_of"]
            if _alias_spans(answer, alias)
        ]
        for slot in activity["concept_slots"]
    }
    evaluation = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": probe_id,
        "skill_ids": skill_ids,
        "score": 0.95,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": bool(aliases_by_id[criterion["id"]]),
                "quality": 0.9 if aliases_by_id[criterion["id"]] else 0.0,
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The answer uses every required detail.",
    }
    return validate_school_open_evaluation(
        evaluation,
        context=school_open_context_from_activity(authority, answer),
    )


def _words(value: str) -> list[str]:
    return WORD_RE.findall(value.casefold())


def _word_count(value: str) -> int:
    return len(_words(value))


def _jaccard(left: str, right: str) -> float:
    left_words = set(_words(left))
    right_words = set(_words(right))
    if not left_words and not right_words:
        return 1.0
    return len(left_words & right_words) / len(left_words | right_words)


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _alias_spans(value: str, alias: str) -> set[tuple[int, int]]:
    normalized_value = _normalized(value)
    normalized_alias = _normalized(alias)
    if not normalized_alias:
        return set()
    prefix = r"(?<!\w)" if normalized_alias[0].isalnum() else ""
    suffix = r"(?!\w)" if normalized_alias[-1].isalnum() else ""
    return {
        match.span()
        for match in re.finditer(
            f"{prefix}{re.escape(normalized_alias)}{suffix}",
            normalized_value,
        )
    }


def _has_disjoint_slot_spans(model_answer: str, slots: list[dict]) -> bool:
    candidates = [
        set().union(
            *(_alias_spans(model_answer, alias) for alias in slot["any_of"])
        )
        for slot in slots
    ]
    if any(not spans for spans in candidates):
        return False

    def assign(slot_index: int, used: tuple[tuple[int, int], ...]) -> bool:
        if slot_index == len(candidates):
            return True
        for span in candidates[slot_index]:
            if any(span[0] < other[1] and other[0] < span[1] for other in used):
                continue
            if assign(slot_index + 1, (*used, span)):
                return True
        return False

    return assign(0, ())


def _ngrams(value: str, size: int = 10) -> set[tuple[str, ...]]:
    words = _words(value)
    return {
        tuple(words[index : index + size])
        for index in range(len(words) - size + 1)
    }


def _scenario_text(activity: dict) -> str:
    return _normalized(
        " ".join(
            (
                activity["passage"],
                activity["prompt"],
                activity.get("model_answer", ""),
            )
        )
    )


def _all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _all_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_strings(child)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_runtime_is_hash_valid_agent_reviewed_and_manifest_authored(chapter_id):
    manifest = load_manifest(_manifest_path(chapter_id))
    chapter = load_live_chapter_file(CHAPTER_ROOT / f"{chapter_id}.json")

    assert manifest.chapter.chapter_id == chapter_id
    assert manifest.chapter.authorship.zidd_authored_original is True
    assert manifest.chapter.authorship.textbook_body_or_questions_copied is False
    assert chapter.runtime_sha256 == chapter.calculated_runtime_sha256()
    assert chapter.approval_status == "agent_reviewed"
    assert chapter.approval_status != "release_approved"
    assert chapter.reviewed_by
    assert chapter.reviewed_at
    assert any("manifest" in item.casefold() for item in chapter.review_evidence)
    assert any("official" in item.casefold() for item in chapter.review_evidence)
    assert any("originality" in item.casefold() for item in chapter.review_evidence)
    assert any("pedagogy" in item.casefold() for item in chapter.review_evidence)
    assert any("language" in item.casefold() for item in chapter.review_evidence)
    assert any("runtime" in item.casefold() for item in chapter.review_evidence)
    assert not chapter_quality_issues(chapter)
    assert 5 <= len(chapter.levels) <= 7
    assert len(manifest.levels) == len(chapter.levels)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_source_anchors_cover_structure_and_keep_companion_modalities_honest(chapter_id):
    payload = _payload(chapter_id)
    anchors = payload["source_anchors"]
    anchor_ids = {anchor["anchor_id"] for anchor in anchors}
    page_start, page_end = CHAPTER_PAGES[chapter_id]

    assert len(anchors) >= 5
    assert len(anchor_ids) == len(anchors)
    assert all(
        anchor["source_url"].startswith("https://ncert.nic.in/")
        for anchor in anchors
    )
    assert all(
        page_start <= anchor["page_start"] <= anchor["page_end"] <= page_end
        for anchor in anchors
    )
    assert all(
        set(level["source_anchor_ids"]).issubset(anchor_ids)
        for level in payload["levels"]
    )
    assert any(anchor["required_for_chapter_certification"] for anchor in anchors)

    companion_anchors = [
        anchor
        for anchor in anchors
        if anchor["coverage_treatment"] in COMPANION_TREATMENTS
    ]
    assert companion_anchors
    assert all(
        not anchor["required_for_chapter_certification"]
        for anchor in companion_anchors
    )
    assert any(
        term in anchor["section_label"].casefold()
        for anchor in companion_anchors
        for term in ("listen", "speak", "draw", "oral", "perform", "picture", "offline")
    )
    for anchor in anchors:
        label = anchor["section_label"].casefold()
        if any(
            term in label
            for term in ("listen", "speak", "draw", "oral", "perform", "picture", "image")
        ):
            assert anchor["coverage_treatment"] in COMPANION_TREATMENTS
            assert anchor["required_for_chapter_certification"] is False


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_each_level_has_six_deep_phases_authored_8plus_pools_and_targeted_support(chapter_id):
    payload = _payload(chapter_id)
    all_signatures = []
    prompts = []
    teaching_blocks = []
    choice_positions = []

    for level in payload["levels"]:
        assert set(level["checks"]) == SUPPORT_CHECKS | {
            "guided_check",
            "independent_check",
            "transfer_check",
        }
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == COMPACT_PHASES
        by_phase = {step["phase"]: step for step in steps}

        connect = by_phase["connect"]["activity"]
        assert connect["interaction_type"] == "continue"
        assert connect["evidence_role"] == "experience"
        assert connect["options"] == []
        assert connect["accepted_answers"] == []

        co_construct = by_phase["co_construct"]["activity"]
        assert co_construct["evidence_role"] == "formative"

        phase_roles = {
            "guided_practice": "supported",
            "independent_application": "certifying",
            "transfer": "certifying",
            "review": "certifying",
        }
        for phase, role in phase_roles.items():
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) >= MIN_VARIANTS[phase]
            assert all(activity["evidence_role"] == role for activity in variants)
            assert len({activity["variant_id"] for activity in variants}) == len(
                variants
            )
            assert len({_normalized(activity["passage"]) for activity in variants}) == len(
                variants
            )
            for left, right in combinations(variants, 2):
                assert _jaccard(
                    left["passage"] + " " + left["prompt"],
                    right["passage"] + " " + right["prompt"],
                ) < 0.75

        for phase in ("transfer", "review"):
            variants = by_phase[phase]["variant_pool"]
            assert all(
                set(activity["knowledge_components"]) == set(level["skill_ids"])
                for activity in variants
            )
            for left, right in combinations(variants, 2):
                left_scenario = _scenario_text(left)
                right_scenario = _scenario_text(right)
                assert SequenceMatcher(
                    None,
                    left_scenario,
                    right_scenario,
                ).ratio() < 0.68
                assert not _ngrams(left_scenario, 10).intersection(
                    _ngrams(right_scenario, 10)
                )

        for phase in ("independent_application", "transfer", "review"):
            for activity in by_phase[phase]["variant_pool"]:
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["evaluation_mode"] == "llm_rubric"
                assert activity["certifying_language"] == "en"

        teaching_passages = {
            _normalized(activity["passage"])
            for step in steps
            for activity in (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
        }
        support_passages = set()
        for check_name in SUPPORT_CHECKS:
            support = level["checks"][check_name]
            assert support["evidence_role"] == "supported"
            assert support["target_misconception_tags"]
            assert set(support["knowledge_components"]).issubset(level["skill_ids"])
            support_passages.add(_normalized(support["passage"]))
        assert len(support_passages) == 5
        assert support_passages.isdisjoint(teaching_passages)

        for activity in _activities({"levels": [level]}):
            assert 5 <= _word_count(activity["teaching_block"]) <= 55
            assert 4 <= _word_count(activity["passage"]) <= 60
            assert 3 <= _word_count(activity["prompt"]) <= 30
            all_signatures.append(
                (
                    activity["teaching_block"],
                    activity["passage"],
                    activity["prompt"],
                )
            )
            prompts.append(activity["prompt"])
            teaching_blocks.append(activity["teaching_block"])
            if activity["interaction_type"] == "continue":
                continue
            if activity["options"]:
                assert not any(
                    skill_id.startswith(PRODUCTIVE_PREFIXES)
                    for skill_id in activity["knowledge_components"]
                )
                choice_positions.append(
                    activity["options"].index(activity["accepted_answers"][0])
                )
            else:
                assert _word_count(activity["model_answer"]) <= 45
                assert activity["min_response_words"] <= 25

    assert len(all_signatures) == len(set(all_signatures))
    assert len(prompts) == len(set(prompts))
    assert len(teaching_blocks) == len(set(teaching_blocks))
    assert len(set(choice_positions)) >= 3
    assert Counter(choice_positions)[0] / len(choice_positions) < 0.6


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_strict_open_authority_has_word_floor_and_disjoint_authored_slot_spans(chapter_id):
    payload = _payload(chapter_id)
    activities = list(_activities(payload))
    activities.extend(
        level["checks"][check_name]
        for level in payload["levels"]
        for check_name in SUPPORT_CHECKS
    )
    activities.extend(payload["chapter_assessment"]["items"])

    strict_open = [
        activity
        for activity in activities
        if activity.get("grading_mode") == "strict_open_rubric"
    ]
    assert strict_open
    for activity in strict_open:
        assert _word_count(activity["model_answer"]) >= activity["min_response_words"]
        assert [criterion["id"] for criterion in activity["rubric_criteria"]] == [
            slot["id"] for slot in activity["concept_slots"]
        ]
        assert all(slot["any_of"] for slot in activity["concept_slots"])
        assert _has_disjoint_slot_spans(
            activity["model_answer"], activity["concept_slots"]
        ), activity.get("variant_id") or activity.get("item_id")


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_certifying_cases_are_fresh_and_use_only_required_english_anchors(chapter_id):
    payload = _payload(chapter_id)
    required_anchor_ids = {
        anchor["anchor_id"]
        for anchor in payload["source_anchors"]
        if anchor["required_for_chapter_certification"]
    }
    companion_anchor_ids = {
        anchor["anchor_id"]
        for anchor in payload["source_anchors"]
        if not anchor["required_for_chapter_certification"]
    }
    certifying = []
    noncertifying_passages = set()
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
            for activity in activities:
                if activity["evidence_role"] == "certifying":
                    certifying.append(activity)
                else:
                    noncertifying_passages.add(_normalized(activity["passage"]))
        noncertifying_passages.update(
            _normalized(level["checks"][check_name]["passage"])
            for check_name in SUPPORT_CHECKS
        )

    certifying_passages = [_normalized(activity["passage"]) for activity in certifying]
    assert len(certifying_passages) == len(set(certifying_passages))
    assert set(certifying_passages).isdisjoint(noncertifying_passages)
    for activity in certifying:
        anchors = set(activity["source_anchor_ids"])
        assert anchors
        assert anchors <= required_anchor_ids
        assert anchors.isdisjoint(companion_anchor_ids)
        assert activity["certifying_language"] == "en"
        assert not any(
            skill_id in UNOBSERVABLE_TEXT_ONLY_SKILLS
            for skill_id in activity["knowledge_components"]
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_taxonomy_assessment_forms_coverage_and_remediation_are_complete(chapter_id):
    payload = _payload(chapter_id)
    manifest = load_manifest(_manifest_path(chapter_id))
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    assessed_skills = {
        skill_id for item in items for skill_id in item["skill_ids"]
    }

    assert 5 <= len(taught_skills) <= 12
    taxonomy = {
        entry.skill_id: entry for entry in locked_english_taxonomy().entries
    }
    assert taught_skills <= set(locked_english_skill_ids())
    assert all(
        taxonomy.get(skill_id).class_min <= 2 <= taxonomy.get(skill_id).class_max
        for skill_id in taught_skills
    )
    assert taught_skills.isdisjoint(UNOBSERVABLE_TEXT_ONLY_SKILLS)
    assert assessment["items_per_attempt"] == 12
    assert assessment["max_attempts"] == 2
    assert len(items) == 24
    assert assessed_skills == taught_skills
    assert all(
        sum(skill_id in item["skill_ids"] for item in items) >= 4
        for skill_id in taught_skills
    )
    assert len({item["item_id"] for item in items}) == 24
    assert len({item["passage"] for item in items}) == 24

    teaching_passages = {activity["passage"] for activity in _activities(payload)}
    assert all(item["passage"] not in teaching_passages for item in items)
    assert all(
        item["grading_mode"] == (
            "selected_option" if item["options"] else "strict_open_rubric"
        )
        for item in items
    )

    first = _select_chapter_assessment_items(
        items,
        item_count=12,
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=12,
        attempt_no=2,
        used_item_ids=first_ids,
    )
    assert len(first) == len(second) == 12
    assert first_ids.isdisjoint(item["item_id"] for item in second)
    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills
        assert sum(bool(item["options"]) for item in form) >= 3
        assert sum(not item["options"] for item in form) >= 3

    remediated_skills = {
        skill_id
        for level in payload["levels"]
        for check_name in SUPPORT_CHECKS
        for skill_id in level["checks"][check_name]["knowledge_components"]
    }
    assert assessed_skills <= remediated_skills
    strand_skills = {
        skill_id
        for strand in manifest.chapter_assessment.strands
        for skill_id in strand.skill_ids
    }
    assert strand_skills == assessed_skills
    known_level_ids = {level.level_id for level in manifest.levels}
    assert all(
        set(strand.remediation_level_ids).issubset(known_level_ids)
        for strand in manifest.chapter_assessment.strands
    )
    for level in manifest.levels:
        support_ids = {
            activity.activity_id
            for activity in level.support_checks.activities().values()
        }
        assert len(support_ids) == 5
        assert {
            skill_id
            for cluster in level.misconception_clusters
            for skill_id in cluster.skill_ids
        } == set(level.skill_ids)
        assert {
            check_id
            for cluster in level.misconception_clusters
            for check_id in cluster.support_check_ids
        } == support_ids


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_authored_content_has_no_ten_word_overlap_with_official_extract(chapter_id):
    extract_path = EXTRACT_ROOT / f"{chapter_id}.txt"
    if not extract_path.is_file():
        pytest.skip("official Class 2 structural extract is not available")
    source_ngrams = _ngrams(extract_path.read_text(encoding="utf-8"))
    manifest = load_manifest(_manifest_path(chapter_id))
    authored_payload = {
        "levels": [level.model_dump(mode="json") for level in manifest.levels],
        "assessment": manifest.chapter_assessment.model_dump(mode="json"),
    }

    overlaps = []
    for authored_text in _all_strings(authored_payload):
        shared = _ngrams(authored_text) & source_ngrams
        if shared:
            overlaps.append(" ".join(next(iter(shared))))
    assert not overlaps, f"10-word source overlap in {chapter_id}: {overlaps[:3]}"


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_every_strict_open_model_answer_passes_real_semantic_validator(chapter_id):
    strict_open_count = 0
    for probe_id, activity in _all_runtime_activities(_payload(chapter_id)):
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        strict_open_count += 1
        validated = _validate_model_answer(activity, probe_id=probe_id)
        assert validated.effective_blockers == (), (
            probe_id,
            validated.effective_blockers,
        )
        assert validated.certification_eligible is True, probe_id
    assert strict_open_count >= 60


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_teaching_blocks_do_not_expose_authoring_labels(chapter_id):
    for probe_id, activity in _all_runtime_activities(_payload(chapter_id)):
        teaching_block = activity.get("teaching_block") or ""
        assert not AUTHORING_JARGON_RE.search(teaching_block), (
            probe_id,
            teaching_block,
        )


def test_reviewed_choice_distractors_are_plausible_misconceptions():
    activities = {
        probe_id: activity
        for chapter_id in CHAPTER_IDS
        for probe_id, activity in _all_runtime_activities(_payload(chapter_id))
    }
    for activity in activities.values():
        distractors = set(activity.get("options") or ()) - set(
            activity.get("accepted_answers") or ()
        )
        assert not {
            _normalized(distractor) for distractor in distractors
        }.intersection(BANNED_IMPLAUSIBLE_DISTRACTORS)

    expected_options = {
        "eng_c2_ch03:assessment:11": {
            "The calf enters the barn.",
            "The calf follows the path.",
            "The calf enters the barn before following the path.",
            "The calf stops on the path instead of entering the barn.",
        },
        "eng_c2_ch05:assessment:11": {
            "The family boards the ferry.",
            "The family reaches the pier.",
            "The family boards before reaching the pier.",
            "The family waits at the pier instead of boarding.",
        },
        "eng_c2_ch06:assessment:11": {
            "The path reaches the clinic.",
            "The path crosses Oak Street.",
            "The path reaches the clinic before crossing Oak Street.",
            "The path stops at Oak Street instead of reaching the clinic.",
        },
        "eng_c2_ch07:assessment:11": {
            "The path reaches the sports centre.",
            "The path crosses Hill Road.",
            "The path reaches the sports centre before crossing Hill Road.",
            "The path stops at Hill Road instead of reaching the sports centre.",
        },
    }
    for item_id, expected in expected_options.items():
        assert set(activities[item_id]["options"]) == expected

    bicycle_inference = next(
        activity
        for level in _payload("eng_c2_ch01")["levels"]
        if level["level_id"] == "bicycle_clue_inference"
        for step in level["teaching_steps"]
        if step["phase"] == "co_construct"
        for activity in [step["activity"]]
    )
    assert set(bicycle_inference["options"]) == {
        "The sky is becoming dark.",
        "He thinks the tyres need checking before the ride.",
        "He wants to test the bell before leaving.",
        "He plans to adjust the seat before riding.",
    }


def test_preposition_assessments_use_three_distinct_task_shapes():
    items = {
        item["item_id"]: item
        for chapter_id in ("eng_c2_ch05", "eng_c2_ch06", "eng_c2_ch07")
        for item in _payload(chapter_id)["chapter_assessment"]["items"]
    }
    reviewed = {
        item_id: items[item_id]
        for item_id in (
            "eng_c2_ch05:assessment:16",
            "eng_c2_ch06:assessment:14",
            "eng_c2_ch07:assessment:14",
        )
    }
    assert all("using beside" not in item["prompt"].casefold() for item in reviewed.values())
    assert len({item["passage"] for item in reviewed.values()}) == 3
    assert len({item["model_answer"] for item in reviewed.values()}) == 3
    assert "under the berth" in reviewed["eng_c2_ch05:assessment:16"]["model_answer"]
    assert "inside the suitcase" in reviewed["eng_c2_ch05:assessment:16"]["model_answer"]
    assert "opposite the clinic" in reviewed["eng_c2_ch06:assessment:14"]["model_answer"]
    assert "across Cedar Road" in reviewed["eng_c2_ch06:assessment:14"]["model_answer"]
    assert "behind the bank" in reviewed["eng_c2_ch07:assessment:14"]["model_answer"]
    assert "opposite the park" in reviewed["eng_c2_ch07:assessment:14"]["model_answer"]


def test_ch06_complete_route_sentence_is_natural_and_precise():
    item = next(
        item
        for item in _payload("eng_c2_ch06")["chapter_assessment"]["items"]
        if item["item_id"] == "eng_c2_ch06:assessment:22"
    )
    assert item["model_answer"] == (
        "Cross Oak Road at the signal, follow the footpath, and stop at the "
        "library gate."
    )
    assert "beside its end" not in item["model_answer"].casefold()


def test_ch06_across_assessment_uses_a_fresh_application_context():
    item = next(
        item
        for item in _payload("eng_c2_ch06")["chapter_assessment"]["items"]
        if item["item_id"] == "eng_c2_ch06:assessment:16"
    )

    assert item["passage"] == (
        "Meera is beside the library. The sports gate is on the far side of "
        "Lake Street."
    )
    assert item["model_answer"] == (
        "Walk from the library across Lake Street to reach the sports gate."
    )
    assert "route passes" not in item["model_answer"].casefold()


def test_class2_inference_uses_clue_language_without_invalid_taxonomy_tags():
    payload = _payload("eng_c2_ch01")
    inference_level = next(
        level for level in payload["levels"]
        if level["level_id"] == "bicycle_clue_inference"
    )
    assert inference_level["skill_ids"] == ["reading.sentence_comprehension"]
    certifying = [
        activity
        for step in inference_level["teaching_steps"]
        if step["phase"] in {"independent_application", "transfer", "review"}
        for activity in step["variant_pool"]
    ]
    assert certifying
    assert all(
        re.search(r"\b(?:why|infer|clue|probably|likely|show)\b", activity["prompt"], re.I)
        for activity in certifying
    )
    assert all(
        re.search(r"\b(?:because|so|may|probably|likely)\b", activity["model_answer"], re.I)
        for activity in certifying
    )
    assert all(
        "reading.inference_reason" not in (
            activity.get("skill_ids")
            or activity.get("knowledge_components")
            or ()
        )
        for _, activity in _all_runtime_activities(payload)
    )


def test_chapters_are_not_interchangeable_templates():
    chapter_texts = {}
    all_signatures = []
    all_prompts = []
    for chapter_id in CHAPTER_IDS:
        payload = _payload(chapter_id)
        activities = list(_activities(payload))
        assessment = payload["chapter_assessment"]["items"]
        chapter_text = json.dumps(
            {"activities": activities, "assessment": assessment},
            ensure_ascii=False,
        ).casefold()
        chapter_texts[chapter_id] = chapter_text
        all_signatures.extend(
            (activity["passage"], activity["prompt"])
            for activity in activities
        )
        all_prompts.extend(activity["prompt"] for activity in activities)

    for chapter_id, required_words in CHAPTER_LEXICON.items():
        assert all(word in chapter_texts[chapter_id] for word in required_words)
    assert len(all_signatures) == len(set(all_signatures))
    assert len(all_prompts) == len(set(all_prompts))
