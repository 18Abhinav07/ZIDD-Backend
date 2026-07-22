from __future__ import annotations

import importlib.util
import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

from app.content.school.standards import LOCKED_ENGLISH_TAXONOMY_ENTRIES
from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services.school_rebuild_curriculum import (
    _public_activity,
    _select_chapter_assessment_items,
)
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from scripts.build_school_deep_chapter import build_deep_chapter, load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPTER_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_3"
)
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_3"
)
EXTRACT_ROOT = Path("/tmp/zidd-ncert-class2-3")
CHAPTER_IDS = tuple(f"eng_c3_ch{chapter_no:02d}" for chapter_no in range(7, 13))
PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
VARIANT_COUNTS = {
    "guided_practice": 4,
    "independent_application": 4,
    "transfer": 4,
    "review": 4,
}
SUPPORT_CHECKS = {
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
}
SUPPORT_SEQUENCE = (
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
)
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
HIDDEN_GRADING_FIELDS = {
    "accepted_answers",
    "answer_rule",
    "concept_slots",
    "forbidden_phrases",
    "evaluation_mode",
    "model_answer",
    "ordered_concept_slot_ids",
    "pass_score",
    "preflight_rule",
    "relevance_terms",
    "rubric_criteria",
}
UNSEEN_RUNTIME_DIRECTIONS = (
    "ask a partner",
    "hear the audio",
    "listen to",
    "look at the picture",
    "read aloud",
    "say aloud",
    "study the image",
    "teacher will",
)
ABSTRACT_LEARNER_PHRASES = (
    "bounded design comparison",
    "central mood",
    "chronological evidence",
    "compresses linked events",
    "consequence",
    "dependency",
    "the reference does not support",
)
ADULT_LEVEL_LABEL_WORDS = {
    "attribute",
    "comprehend",
    "construct",
    "derive",
    "infer",
    "interpret",
    "reconstruct",
}
INTERNAL_AUTHORING_PHRASES = (
    "misconception check",
    "the learner",
    "worked reasoning",
    "next step:",
)
UNSUPPORTED_TEXT_UI_DIRECTIONS = (
    "box the",
    "circle each",
    "circle every",
    "circle the",
    "cross out",
    "draw an arrow",
    "draw arrows",
    "mark each",
    "mark one",
    "mark the",
    "underline",
)
EXPECTED_CHAPTER_CONCEPTS = {
    "eng_c3_ch07": ("poetic exaggeration", "round", "float", "festival"),
    "eng_c3_ch08": ("event sequence", "opposite", "subject-verb agreement", "procedure"),
    "eng_c3_ch09": ("story result", "character quality", "connector", "because"),
    "eng_c3_ch10": ("sky imagery", "blend", "compound word", "night"),
    "eng_c3_ch11": ("here", "there", "count", "dialogue"),
    "eng_c3_ch12": ("curiosity", "question", "ordinal", "mission"),
}


def _manifest_path(chapter_id: str) -> Path:
    return MANIFEST_ROOT / f"{chapter_id}.py"


def _chapter_path(chapter_id: str) -> Path:
    return CHAPTER_ROOT / f"{chapter_id}.json"


def _payload(chapter_id: str) -> dict:
    return json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))


def _manifest_module(chapter_id: str):
    path = _manifest_path(chapter_id)
    module_spec = importlib.util.spec_from_file_location(
        f"class3_reference_manifest_{chapter_id}",
        path,
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def _activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]
        for check_name in SUPPORT_CHECKS:
            yield level["checks"][check_name]


def _level_activities(level: dict):
    for step in level["teaching_steps"]:
        if step.get("activity") is not None:
            yield step["activity"]
        else:
            yield from step["variant_pool"]
    for check_name in SUPPORT_SEQUENCE:
        yield level["checks"][check_name]


def _all_authored_activities(payload: dict):
    yield from _activities(payload)
    yield from payload["chapter_assessment"]["items"]


def _all_runtime_activity_references(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]
        yield from level["checks"].values()
    yield from payload["chapter_assessment"]["items"]


def _words(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z]+(?:'[a-z]+)?", value.casefold()))


def _windows(value: str, size: int = 10) -> set[tuple[str, ...]]:
    words = _words(value)
    return {
        words[index : index + size]
        for index in range(max(0, len(words) - size + 1))
    }


def _normalise(value: str) -> str:
    return " ".join(_words(value))


def _content_words(value: str) -> set[str]:
    ignored = {
        "about",
        "after",
        "answer",
        "before",
        "because",
        "details",
        "example",
        "from",
        "passage",
        "response",
        "their",
        "there",
        "these",
        "they",
        "this",
        "through",
        "using",
        "visible",
        "which",
        "while",
        "with",
        "write",
    }
    return {word for word in _words(value) if len(word) >= 4 and word not in ignored}


def _semantic_jaccard(left: str, right: str) -> float:
    left_words = _content_words(left)
    right_words = _content_words(right)
    union = left_words | right_words
    return len(left_words & right_words) / len(union) if union else 1.0


def _positive_open_payload(activity: dict, answer: str) -> dict:
    item_id = activity.get("activity_id") or activity.get("item_id")
    evidence_quotes = []
    for slot in activity["concept_slots"]:
        evidence_quotes.append(
            next(
                (alias for alias in slot["any_of"] if alias in answer),
                answer,
            )
        )
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": item_id,
        "skill_ids": list(
            activity.get("skill_ids") or activity["knowledge_components"]
        ),
        "score": 0.92,
        "confidence": 0.94,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": True,
                "quality": 0.9,
                "evidence_quote": evidence_quotes[index],
            }
            for index, criterion in enumerate(activity["rubric_criteria"])
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The response uses the needed ideas from the card.",
    }


def _assert_strict_open(activity: dict) -> None:
    assert activity["options"] == []
    assert activity["grading_mode"] == "strict_open_rubric"
    assert activity["evaluation_mode"] == "llm_rubric"
    assert activity["min_response_words"] >= 8
    assert len(activity["rubric_criteria"]) >= 2
    assert [criterion["id"] for criterion in activity["rubric_criteria"]] == [
        slot["id"] for slot in activity["concept_slots"]
    ]
    assert all(
        criterion["required"] and criterion["min_quality"] >= 0.65
        for criterion in activity["rubric_criteria"]
    )
    assert len(activity["relevance_terms"]) >= 2
    assert activity["forbidden_phrases"]
    assert len(_words(activity["model_answer"])) >= activity["min_response_words"]


def _learner_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _learner_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key not in {"source_url", "source_anchor_ids"}:
                yield from _learner_strings(item)


def test_named_reference_nouns_have_visible_reference_content():
    unresolved: list[tuple[str, str, str]] = []

    for chapter_id in CHAPTER_IDS:
        module = _manifest_module(chapter_id)
        reference_cases: dict[str, set[str]] = {}
        for level in module.SPEC["levels"]:
            for case in (*level["cases"], *level["fresh_cases"]):
                reference_cases.setdefault(str(case["label"]), set()).add(
                    str(case["passage"])
                )
        for activity in _all_runtime_activity_references(_payload(chapter_id)):
            activity_id = activity.get("activity_id") or activity.get("item_id")
            instruction = f"{activity.get('teaching_block', '')} {activity['prompt']}"
            visible = " ".join(
                (
                    activity.get("teaching_block", ""),
                    activity["passage"],
                    activity["prompt"],
                )
            )
            for label, reference_passages in reference_cases.items():
                named_reference = re.compile(
                    rf"\b{re.escape(label)}\s+"
                    r"(?:card|notice|schedule|table|chart|poster|menu|sign)\b",
                    re.IGNORECASE,
                )
                if named_reference.search(instruction) and not any(
                    passage in visible for passage in reference_passages
                ):
                    unresolved.append((chapter_id, str(activity_id), label))

    assert not unresolved, (
        f"{len(unresolved)} named references omit their visible source content: "
        f"{unresolved[:12]}"
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_manifest_compiles_to_a_deep_hash_stable_runtime(chapter_id):
    manifest_path = _manifest_path(chapter_id)
    assert manifest_path.is_file()
    manifest = load_manifest(manifest_path)
    payload = _payload(chapter_id)
    chapter = load_live_chapter_file(_chapter_path(chapter_id))
    rebuilt = LiveSchoolChapter.model_validate(build_deep_chapter(None, manifest))

    assert manifest.chapter.chapter_id == chapter_id
    assert manifest.chapter.authorship.zidd_authored_original is True
    assert manifest.chapter.authorship.textbook_body_or_questions_copied is False
    assert 6 <= len(manifest.levels) <= 8
    assert len(payload["levels"]) == len(manifest.levels)
    assert chapter.runtime_dict() == rebuilt.runtime_dict()
    assert chapter.calculated_runtime_sha256() == payload["runtime_sha256"]
    assert not chapter_quality_issues(chapter)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_review_status_is_agent_reviewed_but_never_release_approved(chapter_id):
    chapter = load_live_chapter_file(_chapter_path(chapter_id))

    assert chapter.approval_status == "agent_reviewed"
    assert chapter.approval_status != "release_approved"
    assert chapter.reviewed_by
    assert chapter.reviewed_at
    assert any("manifest" in item.casefold() for item in chapter.review_evidence)
    assert any("official" in item.casefold() for item in chapter.review_evidence)
    assert any("originality" in item.casefold() for item in chapter.review_evidence)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_taxonomy_progression_is_class_three_bounded_and_varied(chapter_id):
    payload = _payload(chapter_id)
    taxonomy = {entry.skill_id: entry for entry in LOCKED_ENGLISH_TAXONOMY_ENTRIES}
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }

    assert 6 <= len(payload["levels"]) <= 8
    assert 6 <= len(taught_skills) <= 14
    assert taught_skills <= set(taxonomy)
    assert all(
        taxonomy[skill_id].class_min <= 3 <= taxonomy[skill_id].class_max
        for skill_id in taught_skills
    )
    assert not taught_skills.intersection(UNOBSERVABLE_TEXT_ONLY_SKILLS)
    assert any(skill_id.startswith("reading.") for skill_id in taught_skills)
    assert any(skill_id.startswith("vocab.") for skill_id in taught_skills)
    assert any(skill_id.startswith("grammar.") for skill_id in taught_skills)
    assert any(skill_id.startswith("writing.") for skill_id in taught_skills)
    assert taught_skills.intersection(
        {"reading.inference_reason", "writing.reason_answer"}
    )
    assert len({level["episode_kind"] for level in payload["levels"]}) >= 4


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_source_anchors_cover_structure_without_certifying_offline_modalities(
    chapter_id,
):
    payload = _payload(chapter_id)
    anchors = payload["source_anchors"]
    required_ids = {
        anchor["anchor_id"]
        for anchor in anchors
        if anchor["required_for_chapter_certification"]
    }
    referenced_ids = {
        anchor_id
        for level in payload["levels"]
        for anchor_id in level["source_anchor_ids"]
    }
    modality_words = ("picture", "listen", "speak", "recite", "draw", "do", "project")
    modality_anchors = [
        anchor
        for anchor in anchors
        if any(word in anchor["section_label"].casefold() for word in modality_words)
    ]

    assert len(anchors) >= 6
    assert required_ids <= referenced_ids
    assert modality_anchors
    assert all(
        anchor["coverage_treatment"] in COMPANION_TREATMENTS
        and not anchor["required_for_chapter_certification"]
        for anchor in modality_anchors
    )
    assert all(
        anchor["source_url"].startswith(
            f"https://ncert.nic.in/textbook/pdf/cesa1{chapter_id[-2:]}.pdf#page="
        )
        for anchor in anchors
    )


def test_reviewed_source_forms_are_required_and_really_taught():
    chapter_7 = _payload("eng_c3_ch07")
    chapter_9 = _payload("eng_c3_ch09")
    chapter_12 = _payload("eng_c3_ch12")

    def required_anchor(payload: dict, *words: str) -> dict:
        matches = [
            anchor
            for anchor in payload["source_anchors"]
            if all(word in anchor["section_label"].casefold() for word in words)
        ]
        assert len(matches) == 1
        assert matches[0]["required_for_chapter_certification"] is True
        assert matches[0]["coverage_treatment"] == "taught_and_assessed"
        return matches[0]

    animal_pair = required_anchor(chapter_7, "animal", "pair")
    connector = required_anchor(chapter_9, "and", "but", "because")
    continuation = required_anchor(chapter_9, "story", "continuation")
    blend_writing = required_anchor(chapter_12, "blend", "writ")

    for payload, anchor in (
        (chapter_7, animal_pair),
        (chapter_9, connector),
        (chapter_9, continuation),
        (chapter_12, blend_writing),
    ):
        assert any(
            anchor["anchor_id"] in level["source_anchor_ids"]
            for level in payload["levels"]
        )

    chapter_7_text = json.dumps(chapter_7, ensure_ascii=True).casefold()
    assert "animal word pair" in chapter_7_text

    chapter_9_text = json.dumps(chapter_9, ensure_ascii=True).casefold()
    assert all(connector_word in chapter_9_text for connector_word in ("and", "but", "because"))
    assert any(
        activity.get("interaction_type") == "creative_continuation"
        and "story" in f"{activity['passage']} {activity['prompt']}".casefold()
        for activity in _all_authored_activities(chapter_9)
    )

    chapter_12_text = json.dumps(chapter_12, ensure_ascii=True).casefold()
    assert all(
        fact in chapter_12_text
        for fact in (
            "india",
            "rocket",
            "landed on the moon",
            "23 august 2023",
            "chandra means moon",
            "yaan means vehicle",
        )
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_every_level_has_the_exact_deep_authored_loop(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == PHASES
        by_phase = {step["phase"]: step for step in steps}
        connect = by_phase["connect"]["activity"]
        co_construct = by_phase["co_construct"]["activity"]

        assert connect["interaction_type"] == "continue"
        assert connect["evidence_role"] == "experience"
        assert co_construct["evidence_role"] == "formative"
        for phase in (
            "guided_practice",
            "independent_application",
            "transfer",
            "review",
        ):
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) == VARIANT_COUNTS[phase]
            assert len(
                {(item["passage"], item["prompt"]) for item in variants}
            ) == VARIANT_COUNTS[phase]
            expected_role = "supported" if phase == "guided_practice" else "certifying"
            assert all(item["evidence_role"] == expected_role for item in variants)
        for phase in ("independent_application", "transfer", "review"):
            for activity in by_phase[phase]["variant_pool"]:
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["certifying_language"] == "en"
                assert activity["interaction_type"] in {
                    "short_text",
                    "evidence_text",
                    "paragraph_text",
                    "creative_continuation",
                    "reflection",
                }


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_transfer_and_review_use_fresh_answer_authority(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        by_phase = {step["phase"]: step for step in level["teaching_steps"]}
        earlier = [by_phase["co_construct"]["activity"]]
        earlier.extend(by_phase["guided_practice"]["variant_pool"])
        earlier.extend(by_phase["independent_application"]["variant_pool"])
        later = [
            *by_phase["transfer"]["variant_pool"],
            *by_phase["review"]["variant_pool"],
        ]

        assert len(earlier) == 9
        assert len(later) == 8
        assert len({_normalise(item["passage"]) for item in [*earlier, *later]}) == 17
        for certifying in later:
            authority = f"{certifying['passage']} {certifying['prompt']}"
            assert all(
                _semantic_jaccard(authority, f"{prior['passage']} {prior['prompt']}")
                < 0.72
                for prior in earlier
            )
            assert all(
                not _windows(authority, 6).intersection(
                    _windows(f"{prior['passage']} {prior['prompt']}", 6)
                )
                for prior in earlier
            )

        for left, right in combinations(later, 2):
            assert _normalise(left["passage"]) != _normalise(right["passage"])


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_five_misconception_specific_support_checks_remediate_every_skill(
    chapter_id,
):
    payload = _payload(chapter_id)
    manifest = load_manifest(_manifest_path(chapter_id))

    for raw_level, authored_level in zip(payload["levels"], manifest.levels, strict=True):
        assert set(raw_level["checks"]) == SUPPORT_CHECKS | {
            "guided_check",
            "independent_check",
            "transfer_check",
        }
        support = [raw_level["checks"][name] for name in SUPPORT_SEQUENCE]
        assert all(item["target_misconception_tags"] for item in support)
        assert len(
            {(item["teaching_block"], item["passage"], item["prompt"]) for item in support}
        ) == 5
        assert all(
            "here is an example from" in item["teaching_block"].casefold()
            for item in support
        )
        assert all(
            "for the new card" in item["teaching_block"].casefold()
            for item in support
        )
        assert all(
            "type your answer first" in item["teaching_block"].casefold()
            for item in support
        )
        assert all("use the new card" in item["prompt"].casefold() for item in support)
        assert all(
            "type your answer and one clue" in item["prompt"].casefold()
            for item in support
        )
        for item in support:
            visible_support = " ".join(
                (item["teaching_block"], item["passage"], item["prompt"])
            ).casefold()
            support_instructions = " ".join(
                (item["teaching_block"], item["prompt"])
            ).casefold()
            assert not any(
                phrase in visible_support for phrase in INTERNAL_AUTHORING_PHRASES
            )
            assert not any(
                direction in support_instructions
                for direction in UNSUPPORTED_TEXT_UI_DIRECTIONS
            )
        assert [item["min_response_words"] for item in support] == [8, 9, 10, 11, 12]

        core_passages = {
            activity["passage"]
            for step in raw_level["teaching_steps"]
            for activity in (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
        }
        for item in support:
            _assert_strict_open(item)
            assert item["passage"] not in core_passages
            assert all(
                _semantic_jaccard(item["passage"], core_passage) < 0.72
                for core_passage in core_passages
            )
        remediated_skills = {
            skill_id
            for cluster in authored_level.misconception_clusters
            for skill_id in cluster.skill_ids
        }
        assert remediated_skills == set(raw_level["skill_ids"])
        assert {
            check_id
            for cluster in authored_level.misconception_clusters
            for check_id in cluster.support_check_ids
        } == {
            authored_level.support_checks.activities()[name].activity_id
            for name in SUPPORT_CHECKS
        }
        for cluster in authored_level.misconception_clusters:
            remediation = cluster.remediation.casefold()
            assert "first" in remediation
            assert "then" in remediation
            assert "finally" in remediation


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_has_two_disjoint_balanced_forms_with_full_coverage(chapter_id):
    payload = _payload(chapter_id)
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }
    teaching_passages = [activity["passage"] for activity in _activities(payload)]

    assert assessment["items_per_attempt"] == 14
    assert assessment["max_attempts"] == 2
    assert len(items) == 28
    assert len({item["item_id"] for item in items}) == 28
    assert 10 <= sum(bool(item["options"]) for item in items) <= 18
    assert 10 <= sum(not item["options"] for item in items) <= 18
    assert len({_normalise(item["passage"]) for item in items}) == 28
    for item in items:
        assert len(item["skill_ids"]) == 1
        assert not any(
            direction in f"{item['passage']} {item['prompt']}".casefold()
            for direction in UNSEEN_RUNTIME_DIRECTIONS
        )
        productive = any(
            skill_id.startswith(PRODUCTIVE_PREFIXES)
            for skill_id in item["skill_ids"]
        )
        if productive:
            assert not item["options"]
        if not item["options"]:
            _assert_strict_open(item)

    first = _select_chapter_assessment_items(
        items,
        item_count=14,
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=14,
        attempt_no=2,
        used_item_ids=first_ids,
    )
    assert len(first) == len(second) == 14
    assert first_ids.isdisjoint(item["item_id"] for item in second)
    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills
        assert sum(bool(item["options"]) for item in form) >= 5
        assert sum(not item["options"] for item in form) >= 5

    for item in items:
        item_authority = f"{item['passage']} {item['prompt']}"
        assert all(
            _semantic_jaccard(item_authority, teaching_passage) < 0.72
            for teaching_passage in teaching_passages
        )
        assert all(
            not _windows(item_authority, 6).intersection(_windows(teaching_passage, 6))
            for teaching_passage in teaching_passages
        )
        assert all(
            _semantic_jaccard(item["passage"], teaching_passage) < 0.65
            for teaching_passage in teaching_passages
        )

    for left, right in combinations(items, 2):
        left_authority = f"{left['passage']} {left['prompt']}"
        right_authority = f"{right['passage']} {right['prompt']}"
        assert _semantic_jaccard(left_authority, right_authority) < 0.72
        assert not _windows(left_authority, 6).intersection(
            _windows(right_authority, 6)
        )
        assert _semantic_jaccard(left["passage"], right["passage"]) < 0.65


def test_chapter7_animal_writing_assessment_uses_an_unseen_pair():
    payload = _payload("eng_c3_ch07")
    item = next(
        item
        for item in payload["chapter_assessment"]["items"]
        if item["item_id"] == "eng_c3_ch07:assessment:25"
    )
    pair = {"dog", "puppy"}

    assert pair.issubset(_words(f"{item['passage']} {item['prompt']}"))
    for activity in _activities(payload):
        assert pair.isdisjoint(_words(activity["passage"]))


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_choice_distractors_are_item_specific(chapter_id):
    payload = _payload(chapter_id)
    assessment_distractors: list[str] = []
    generic_fragments = (
        "the reference does not support",
        "it is not true that",
        "the card gives a different result",
        "the needed detail is not shown",
    )

    for activity in _all_authored_activities(payload):
        if not activity.get("options"):
            continue
        accepted = set(activity.get("accepted_answers") or ())
        distractors = [option for option in activity["options"] if option not in accepted]
        assert len(distractors) == len(set(distractors)) == 2
        assert all(
            fragment not in distractor.casefold()
            for distractor in distractors
            for fragment in generic_fragments
        )
        if activity.get("item_id"):
            assessment_distractors.extend(distractors)

    assert len(assessment_distractors) == len(set(assessment_distractors))


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_open_rubric_slots_are_independent_and_paraphrase_friendly(chapter_id):
    payload = _payload(chapter_id)

    for activity in _all_authored_activities(payload):
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        model_answer = _normalise(activity["model_answer"])
        alias_sets = []
        for slot in activity["concept_slots"]:
            raw_aliases = slot["any_of"]
            aliases = {_normalise(alias) for alias in raw_aliases}
            assert len(aliases) >= 2
            assert all(len(_words(alias)) >= 2 for alias in aliases)
            assert model_answer not in aliases
            assert not any(alias.startswith("in my own words") for alias in aliases)
            assert len(raw_aliases) == 2
            if slot["id"].endswith(":fact"):
                first_claim = raw_aliases[0].split("my answer is:", 1)[1]
                second_claim = raw_aliases[1].split(
                    " That is my answer for ", 1
                )[0]
            else:
                assert slot["id"].endswith(":reason")
                first_claim = raw_aliases[0]
                second_claim = raw_aliases[1].split(
                    " This clue supports my answer.", 1
                )[0]
            assert _normalise(first_claim) == _normalise(second_claim)
            alias_sets.append(aliases)
        for left, right in combinations(alias_sets, 2):
            assert left.isdisjoint(right)


def test_all_runtime_slot_aliases_are_unique_to_one_complete_claim():
    slot_occurrences = 0
    slots_by_id: dict[str, dict] = {}
    alias_owners: dict[str, set[str]] = {}

    for chapter_id in CHAPTER_IDS:
        for activity in _all_runtime_activity_references(_payload(chapter_id)):
            for slot in activity.get("concept_slots", []):
                slot_occurrences += 1
                if slot["id"] in slots_by_id:
                    assert slots_by_id[slot["id"]] == slot
                else:
                    slots_by_id[slot["id"]] = slot
                for alias in slot["any_of"]:
                    alias_owners.setdefault(_normalise(alias), set()).add(slot["id"])

    assert slot_occurrences == 1768
    assert len(slots_by_id) == 1624
    assert all(len(owner_ids) == 1 for owner_ids in alias_owners.values())


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_authored_paraphrase_passes_real_open_evaluator(chapter_id):
    payload = _payload(chapter_id)
    activity = next(
        item
        for item in payload["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    )
    answer = ". ".join(
        slot["any_of"][-1] for slot in activity["concept_slots"]
    )
    if len(_words(answer)) < activity["min_response_words"]:
        answer += " These details fit the task on the card."

    assert _normalise(answer) != _normalise(activity["model_answer"])
    validated = validate_school_open_evaluation(
        _positive_open_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )
    assert validated.effective_blockers == ()
    assert validated.certification_eligible is True


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_one_required_semantic_slot_cannot_certify(chapter_id):
    payload = _payload(chapter_id)
    activity = next(
        item
        for item in payload["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    )
    fact = activity["concept_slots"][0]["any_of"][-1]
    answer = f"{fact} This sentence only repeats that one answer clearly."
    if len(_words(answer)) < activity["min_response_words"]:
        answer += " It does not add a clue from the card."

    evaluation = _positive_open_payload(activity, answer)
    evaluation["score"] = 0.45
    evaluation["criteria"][1].update(
        met=False,
        quality=0.0,
        evidence_quote=answer,
    )
    validated = validate_school_open_evaluation(
        evaluation,
        context=school_open_context_from_activity(activity, answer),
    )
    assert "semantic_required_claim_missing" in validated.effective_blockers
    assert validated.certification_eligible is False


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_positive_typed_result_cannot_certify_irrelevant_prose(chapter_id):
    payload = _payload(chapter_id)
    activity = next(
        item
        for item in payload["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    )
    answer = (
        "School is useful, kindness matters, and children can stay cheerful "
        "while they work carefully every day."
    )
    validated = validate_school_open_evaluation(
        _positive_open_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )
    assert {
        "answer_not_relevant",
        "semantic_required_claim_missing",
    }.intersection(validated.effective_blockers)
    assert validated.certification_eligible is False


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_public_runtime_never_leaks_answer_authority(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        for index, activity in enumerate(_level_activities(level), start=1):
            internal = {
                **activity,
                "activity_id": f"{level['level_id']}:public:{index}",
                "level_id": level["level_id"],
                "kind": "independent_check",
                "title": level["title"],
                "focus": level["focus"],
                "skill_ids": level["skill_ids"],
                "attempt_no": 1,
            }
            public = _public_activity(internal)
            assert public is not None
            assert not (HIDDEN_GRADING_FIELDS & set(public))

    for item in payload["chapter_assessment"]["items"]:
        internal = {
            **item,
            "activity_id": f"chapter_check:1:{item['item_id']}",
            "level_id": "chapter_assessment",
            "kind": "chapter_check",
            "title": "Chapter check",
            "focus": "show chapter learning",
            "teaching_block": "Work alone from the words shown in this task.",
            "attempt_no": 1,
        }
        public = _public_activity(internal)
        assert public is not None
        assert not (HIDDEN_GRADING_FIELDS & set(public))


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_copy_uses_clear_class_three_language(chapter_id):
    payload = _payload(chapter_id)
    visible_strings: list[str] = []
    instruction_strings: list[str] = []
    for level in payload["levels"]:
        visible_strings.extend((level["title"], level["focus"], level["teaching_goal"]))
        level_labels = " ".join(
            (level["title"], level["focus"], level["teaching_goal"])
        ).casefold()
        assert not ADULT_LEVEL_LABEL_WORDS.intersection(_words(level_labels))
        for activity in _level_activities(level):
            visible_strings.extend(
                (
                    activity["teaching_block"],
                    activity["passage"],
                    activity["prompt"],
                )
            )
            instruction_strings.extend(
                (activity["teaching_block"], activity["prompt"])
            )
    for item in payload["chapter_assessment"]["items"]:
        visible_strings.extend((item["passage"], item["prompt"]))

    learner_text = " ".join(visible_strings).casefold()
    instruction_text = " ".join(instruction_strings).casefold()
    assert not any(phrase in learner_text for phrase in ABSTRACT_LEARNER_PHRASES)
    assert not any(phrase in learner_text for phrase in INTERNAL_AUTHORING_PHRASES)
    assert not any(direction in learner_text for direction in UNSEEN_RUNTIME_DIRECTIONS)
    assert not any(
        direction in instruction_text
        for direction in UNSUPPORTED_TEXT_UI_DIRECTIONS
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_all_learner_authority_is_original_at_ten_word_window(chapter_id):
    extract_path = EXTRACT_ROOT / f"{chapter_id}.txt"
    if not extract_path.is_file():
        pytest.skip("official Class 3 structural extract is not available")
    source_windows = _windows(extract_path.read_text(encoding="utf-8"))
    payload = _payload(chapter_id)
    authored_root = {
        "levels": payload["levels"],
        "chapter_assessment": payload["chapter_assessment"],
    }

    overlaps = [
        value
        for value in _learner_strings(authored_root)
        if _windows(value).intersection(source_windows)
    ]
    assert not overlaps, f"{chapter_id} has {len(overlaps)} copied 10-word windows"


def test_chapters_are_not_interchangeable_templates():
    prompts: list[str] = []
    signatures: list[tuple[str, str, str]] = []

    for chapter_id in CHAPTER_IDS:
        payload = _payload(chapter_id)
        chapter_text = json.dumps(payload, ensure_ascii=True).casefold()
        for concept in EXPECTED_CHAPTER_CONCEPTS[chapter_id]:
            assert concept in chapter_text
        for activity in _activities(payload):
            prompts.append(" ".join(activity["prompt"].casefold().split()))
            signatures.append(
                (
                    " ".join(activity["teaching_block"].casefold().split()),
                    " ".join(activity["passage"].casefold().split()),
                    " ".join(activity["prompt"].casefold().split()),
                )
            )

    assert len(prompts) == len(set(prompts))
    assert len(signatures) == len(set(signatures))
    assert Counter(prompt.split()[0] for prompt in prompts).most_common(1)[0][1] < (
        len(prompts) * 0.7
    )
