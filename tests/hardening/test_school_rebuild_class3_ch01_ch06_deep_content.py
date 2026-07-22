from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.content.school_v3_taxonomy import locked_english_skill_ids
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services import school_rebuild_curriculum as curriculum
from app.services.school_rebuild_curriculum import _select_chapter_assessment_items
from scripts.build_school_class5_deep_chapter import build_deep_chapter, load_manifest
from app.content.school_rebuild_manifests.english.class_3.eng_c3_ch01 import (
    _class3_text,
)


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
CHAPTER_IDS = tuple(f"eng_c3_ch{number:02d}" for number in range(1, 7))
ALL_CLASS3_CHAPTER_IDS = tuple(
    f"eng_c3_ch{number:02d}" for number in range(1, 13)
)
PHASES = (
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
PRODUCTIVE_SKILL_PREFIXES = ("writing.", "speaking.", "oral.")
TEXT_UNOBSERVABLE_SKILLS = {
    "speaking.recitation",
    "speaking.multilingual_expression",
    "listening.sound_discrimination",
}
COMPANION_TREATMENTS = {
    "textbook_companion",
    "guided_only",
    "optional_creative",
    "offline_group_activity",
}
PAGE_RANGES = {
    "eng_c3_ch01": (1, 14),
    "eng_c3_ch02": (15, 24),
    "eng_c3_ch03": (25, 35),
    "eng_c3_ch04": (36, 43),
    "eng_c3_ch05": (44, 55),
    "eng_c3_ch06": (56, 67),
}
SECTION_WORDS = {
    "eng_c3_ch01": ("picture", "recite", "think", "speak", "learn", "arrange", "do"),
    "eng_c3_ch02": ("read", "think", "learn", "listen", "speak", "write", "do"),
    "eng_c3_ch03": ("read", "think", "speak", "learn", "write", "do", "explore", "fun with words"),
    "eng_c3_ch04": ("picture", "recite", "think", "speak", "learn", "do"),
    "eng_c3_ch05": ("read", "think", "learn", "listen", "write", "do"),
    "eng_c3_ch06": ("read", "think", "speak", "learn", "do", "write", "explore", "self assessment"),
}
OFFLINE_MODALITY_WORDS = {
    "picture",
    "listen",
    "speak",
    "draw",
    "craft",
    "explore",
    "self assessment",
}
TOKEN_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")
BANNED_LEARNER_PHRASES = {
    "a new based on the card",
    "attribute",
    "central-idea",
    "inference",
    "one or two based on the card",
    "say who speaks in",
    "evidence-based",
    "meaning boundary",
    "merely related detail",
    "natural helper-subject order",
    "precise clue",
    "requested position",
    "response logic",
}
UNSUPPORTED_UI_ACTION_PATTERN = re.compile(
    r"\b(?:underline|highlight|circle|box)\s+"
    r"(?:a|an|the|each|every|its|only|one|two|what)\b|"
    r"\bdraw\s+(?:a|an|one|two|pronoun)?\s*"
    r"(?:arrow|arrows|timeline|line|lines|box|boxes)\b|"
    r"\b(?:cross|check)\s+off\b|"
    r"\bmark\s+(?:n|v|d|p|c|a|r|one|more|step)\b|"
    r"\blabel\s+(?:each|every|the|four|five|it|one)\b|"
    r"\bnumber\s+(?:each|every|the|those|all|four|five)\b",
    flags=re.IGNORECASE,
)
PARAPHRASE_PROBES = {
    "eng_c3_ch01:assessment:02": (
        "Bright shelf tags made the corner welcoming and showed where each "
        "book belonged."
    ),
    "eng_c3_ch02:assessment:02": (
        "The guard used the bright name tag to bring the lost puppy back to "
        "its family."
    ),
    "eng_c3_ch03:assessment:02": (
        "By measuring and mixing two designs, the children made a border that "
        "matched the open space."
    ),
    "eng_c3_ch04:assessment:02": (
        "The relay is about waiting for the start, running hard, and cheering "
        "every teammate."
    ),
    "eng_c3_ch05:assessment:02": (
        "The toy spun well after the class spotted the uneven peg, fixed it, "
        "and tested it again."
    ),
    "eng_c3_ch06:assessment:02": (
        "The quarrel ended when the child honoured the owner's request, gave "
        "back the raft, and helped fix it."
    ),
}


def _chapter_path(chapter_id: str) -> Path:
    return CHAPTER_ROOT / f"{chapter_id}.json"


def _manifest_path(chapter_id: str) -> Path:
    return MANIFEST_ROOT / f"{chapter_id}.py"


def _payload(chapter_id: str) -> dict:
    return json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))


def _activities(payload: dict):
    for level in payload["levels"]:
        for activity in level["checks"].values():
            yield activity
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]
    yield from payload["chapter_assessment"]["items"]


def _unique_activities(payload: dict):
    seen: set[tuple[str, str, str, str]] = set()
    for activity in _activities(payload):
        signature = (
            activity.get("grading_mode", ""),
            activity.get("passage", ""),
            activity.get("prompt", ""),
            activity.get("model_answer", ""),
        )
        if signature in seen:
            continue
        seen.add(signature)
        yield activity


def _open_validation(activity: dict, answer: str, *, probe_id: str):
    skill_ids = list(
        activity.get("skill_ids") or activity.get("knowledge_components") or ()
    )
    authority = {
        **activity,
        "activity_id": probe_id,
        "skill_ids": skill_ids,
    }
    slots_by_id = {
        slot["id"]: slot for slot in activity.get("concept_slots") or ()
    }
    criterion_evidence: dict[str, str | None] = {}
    for criterion in activity["rubric_criteria"]:
        slot = slots_by_id[criterion["id"]]
        evidence_quote = None
        for alias in slot["any_of"]:
            pattern = re.escape(alias).replace(r"\ ", r"\s+")
            match = re.search(pattern, answer, flags=re.IGNORECASE)
            if match:
                evidence_quote = answer[match.start() : match.end()]
                break
        criterion_evidence[criterion["id"]] = evidence_quote
    evaluation = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": probe_id,
        "skill_ids": skill_ids,
        "score": 1.0,
        "confidence": 1.0,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": criterion_evidence[criterion["id"]] is not None,
                "quality": (
                    1.0
                    if criterion_evidence[criterion["id"]] is not None
                    else 0.0
                ),
                "evidence_quote": criterion_evidence[criterion["id"]] or answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The answer includes every required part.",
    }
    return validate_school_open_evaluation(
        evaluation,
        context=school_open_context_from_activity(authority, answer),
    )


def _activity_strings(activity: dict):
    for field in (
        "teaching_block",
        "passage",
        "prompt",
        "model_answer",
    ):
        value = activity.get(field)
        if value:
            yield value
    for field in ("options", "accepted_answers", "forbidden_phrases"):
        yield from activity.get(field) or ()
    for criterion in activity.get("rubric_criteria") or ():
        yield criterion["description"]
    for slot in activity.get("concept_slots") or ():
        yield slot["description"]
        yield from slot["any_of"]


def _learner_facing_strings(payload: dict):
    for level in payload["levels"]:
        for field in ("title", "focus", "teaching_goal"):
            value = level.get(field)
            if value:
                yield value
    for activity in _activities(payload):
        yield from _activity_strings(activity)


def _ten_word_ngrams(text: str) -> set[tuple[str, ...]]:
    tokens = TOKEN_PATTERN.findall(text.casefold())
    return {
        tuple(tokens[index : index + 10])
        for index in range(max(0, len(tokens) - 9))
    }


def _content_words(text: str) -> set[str]:
    ignored = {
        "about",
        "after",
        "answer",
        "before",
        "because",
        "card",
        "details",
        "from",
        "passage",
        "their",
        "there",
        "these",
        "they",
        "this",
        "through",
        "using",
        "which",
        "while",
        "with",
        "write",
    }
    return {
        token
        for token in TOKEN_PATTERN.findall(text.casefold())
        if len(token) >= 4 and token not in ignored
    }


def _semantic_jaccard(left: str, right: str) -> float:
    left_words = _content_words(left)
    right_words = _content_words(right)
    union = left_words | right_words
    if len(union) < 4:
        return 0.0
    return len(left_words & right_words) / len(union)


def _remember_strong_path_activity(
    state: dict,
    activity: dict,
) -> None:
    memory = curriculum._normalize_hot_session_memory(
        state.get("hot_session_memory")
    )
    for field, activity_field in (
        ("passage_fingerprints", "passage"),
        ("prompt_fingerprints", "prompt"),
    ):
        fingerprint = curriculum._content_fingerprint(activity.get(activity_field))
        if fingerprint:
            memory[field] = list(
                dict.fromkeys([*memory[field], fingerprint])
            )[-40:]
    state["hot_session_memory"] = memory


@pytest.mark.parametrize("chapter_id", ALL_CLASS3_CHAPTER_IDS)
def test_strong_path_can_select_a_fresh_activity_for_every_phase(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    state = {"hot_session_memory": {}}
    cross_phase_fingerprints: dict[tuple[str, str], tuple[str, str, str]] = {}

    for raw_level in payload["levels"]:
        for step in raw_level["teaching_steps"]:
            activities = step.get("variant_pool") or [step["activity"]]
            for activity in activities:
                for field in ("passage", "prompt"):
                    fingerprint = curriculum._content_fingerprint(
                        activity.get(field)
                    )
                    key = (field, fingerprint)
                    previous = cross_phase_fingerprints.get(key)
                    assert previous is None or previous[1] == step["phase"], (
                        chapter_id,
                        field,
                        previous,
                        (
                            raw_level["level_id"],
                            step["phase"],
                            activity.get("variant_id"),
                        ),
                    )
                    cross_phase_fingerprints[key] = (
                        raw_level["level_id"],
                        step["phase"],
                        str(activity.get("variant_id") or "single"),
                    )

                if chapter_id in CHAPTER_IDS and step.get("variant_pool"):
                    passage_terms = _content_words(activity["passage"])
                    prompt_terms = _content_words(activity["prompt"])
                    assert len(passage_terms & prompt_terms) >= min(
                        3,
                        len(passage_terms),
                    ), (
                        chapter_id,
                        raw_level["level_id"],
                        step["phase"],
                        activity.get("variant_id"),
                    )

    for raw_level in payload["levels"]:
        level = {**raw_level, "used_variant_ids": []}
        selected_phases: list[str] = []
        for step in level["teaching_steps"]:
            memory = curriculum._normalize_hot_session_memory(
                state.get("hot_session_memory")
            )
            activity, variant_id, fresh = curriculum._v2_step_activity(
                state,
                level,
                step,
            )
            collisions = [
                {
                    "variant_id": candidate.get("variant_id"),
                    "passage_seen": curriculum._content_fingerprint(
                        candidate.get("passage")
                    )
                    in memory["passage_fingerprints"],
                    "prompt_seen": curriculum._content_fingerprint(
                        candidate.get("prompt")
                    )
                    in memory["prompt_fingerprints"],
                }
                for candidate in step.get("variant_pool") or []
            ]
            assert activity is not None and variant_id and fresh, (
                chapter_id,
                level["level_id"],
                step["phase"],
                collisions,
            )

            level["used_variant_ids"] = [
                *level["used_variant_ids"],
                variant_id,
            ]
            _remember_strong_path_activity(state, activity)
            selected_phases.append(step["phase"])

        assert tuple(selected_phases) == PHASES


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_manifest_compiles_without_runtime_or_hash_drift(chapter_id: str) -> None:
    manifest_path = _manifest_path(chapter_id)
    chapter_path = _chapter_path(chapter_id)

    assert manifest_path.is_file()
    manifest = load_manifest(manifest_path)
    reviewed = load_live_chapter_file(chapter_path)
    built = LiveSchoolChapter.model_validate(build_deep_chapter(None, manifest))
    raw_runtime = json.loads(chapter_path.read_text(encoding="utf-8"))

    assert manifest.chapter.chapter_id == chapter_id
    assert manifest.chapter.authorship.zidd_authored_original is True
    assert manifest.chapter.authorship.textbook_body_or_questions_copied is False
    assert built.runtime_dict() == reviewed.runtime_dict()
    assert built.runtime_sha256 == reviewed.runtime_sha256
    assert raw_runtime["runtime_sha256"] == reviewed.runtime_sha256
    assert reviewed.calculated_runtime_sha256() == reviewed.runtime_sha256


def test_class3_text_helper_does_not_rewrite_context_sensitive_words() -> None:
    text = (
        "An attribute can describe a shape, a speaker can attribute a line, "
        "and an evidence-based profile can use an inference."
    )

    assert _class3_text(text) == text


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_runtime_is_agent_reviewed_but_never_release_approved(chapter_id: str) -> None:
    chapter = load_live_chapter_file(_chapter_path(chapter_id))

    assert chapter.approval_status == "agent_reviewed"
    assert chapter.approval_status != "release_approved"
    assert chapter.reviewed_by
    assert chapter.reviewed_at
    assert any("manifest" in evidence.casefold() for evidence in chapter.review_evidence)
    assert any("official" in evidence.casefold() for evidence in chapter.review_evidence)
    assert any("originality" in evidence.casefold() for evidence in chapter.review_evidence)
    assert not chapter_quality_issues(chapter)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_levels_use_closed_taxonomy_and_exact_deep_phase_roles(chapter_id: str) -> None:
    payload = _payload(chapter_id)
    canonical_skills = set(locked_english_skill_ids())
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }

    assert 6 <= len(payload["levels"]) <= 8
    assert 1 <= len(taught_skills) <= 14
    assert taught_skills <= canonical_skills
    assert not taught_skills.intersection(TEXT_UNOBSERVABLE_SKILLS)

    chapter_signatures: list[tuple[str, str, str]] = []
    for level in payload["levels"]:
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == PHASES
        by_phase = {step["phase"]: step for step in steps}

        connect = by_phase["connect"]["activity"]
        assert connect["interaction_type"] == "continue"
        assert connect["evidence_role"] == "experience"
        co_construct = by_phase["co_construct"]["activity"]
        assert co_construct["evidence_role"] == "formative"

        for phase, role, expected_count in (
            ("guided_practice", "supported", 4),
            ("independent_application", "certifying", 4),
            ("transfer", "certifying", 4),
            ("review", "certifying", 4),
        ):
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) == expected_count
            assert all(activity["evidence_role"] == role for activity in variants)
            signatures = {
                (
                    activity["teaching_block"],
                    activity["passage"],
                    activity["prompt"],
                )
                for activity in variants
            }
            assert len(signatures) == expected_count
            passage_pairs = [
                (left["passage"].casefold(), right["passage"].casefold())
                for left_index, left in enumerate(variants)
                for right in variants[left_index + 1 :]
            ]
            assert all(
                SequenceMatcher(None, left, right, autojunk=False).ratio() < 0.82
                for left, right in passage_pairs
            )
            if role == "certifying":
                for activity in variants:
                    assert activity["options"] == []
                    assert activity["grading_mode"] == "strict_open_rubric"
                    assert activity["certifying_language"] == "en"
                    assert not set(activity["knowledge_components"]).intersection(
                        TEXT_UNOBSERVABLE_SKILLS
                    )

        for step in steps:
            activities = step.get("variant_pool") or [step["activity"]]
            chapter_signatures.extend(
                (
                    activity["teaching_block"],
                    activity["passage"],
                    activity["prompt"],
                )
                for activity in activities
            )

    assert len(chapter_signatures) == len(set(chapter_signatures))


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_source_anchors_cover_official_structure_with_honest_modalities(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    start_page, end_page = PAGE_RANGES[chapter_id]
    anchors = payload["source_anchors"]
    labels = " ".join(anchor["section_label"].casefold() for anchor in anchors)
    anchor_ids = {anchor["anchor_id"] for anchor in anchors}

    assert len(anchors) >= len(SECTION_WORDS[chapter_id])
    assert all(word in labels for word in SECTION_WORDS[chapter_id])
    assert all(anchor["source_url"].startswith("https://ncert.nic.in/") for anchor in anchors)
    assert all(start_page <= anchor["page_start"] <= anchor["page_end"] <= end_page for anchor in anchors)
    assert all(
        set(level["source_anchor_ids"]) <= anchor_ids for level in payload["levels"]
    )

    companion_anchors = []
    for anchor in anchors:
        label = anchor["section_label"].casefold()
        if any(word in label for word in OFFLINE_MODALITY_WORDS):
            companion_anchors.append(anchor)
            assert anchor["coverage_treatment"] in COMPANION_TREATMENTS
            assert anchor["required_for_chapter_certification"] is False
    assert companion_anchors


def test_poetry_certification_uses_text_reading_source_authority() -> None:
    expected = {
        "eng_c3_ch01": (
            "poetic_pattern_and_short_answer",
            "eng_c3_ch01:recite:4",
            {"eng_c3_ch01:assessment:11", "eng_c3_ch01:assessment:25"},
        ),
        "eng_c3_ch04": (
            "garden_verse_and_idea",
            "eng_c3_ch04:recite:39-40",
            {"eng_c3_ch04:assessment:01", "eng_c3_ch04:assessment:15"},
        ),
    }

    for chapter_id, (level_id, anchor_id, assessment_ids) in expected.items():
        payload = _payload(chapter_id)
        anchors = {item["anchor_id"]: item for item in payload["source_anchors"]}
        level = next(item for item in payload["levels"] if item["level_id"] == level_id)
        assessments = {
            item["item_id"]: item for item in payload["chapter_assessment"]["items"]
        }

        assert anchors[anchor_id]["coverage_treatment"] == "zidd_equivalent"
        assert anchors[anchor_id]["required_for_chapter_certification"] is True
        assert anchor_id in level["source_anchor_ids"]
        assert all(
            assessments[item_id]["skill_ids"] == ["reading.poetic_language"]
            for item_id in assessment_ids
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_certifying_activities_use_only_certification_eligible_anchors(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    anchors = {
        anchor["anchor_id"]: anchor for anchor in payload["source_anchors"]
    }

    for level in payload["levels"]:
        certifying = [
            activity
            for step in level["teaching_steps"]
            for activity in (step.get("variant_pool") or [step["activity"]])
            if activity.get("evidence_role") == "certifying"
        ]
        assert certifying
        for activity in certifying:
            for anchor_id in activity["source_anchor_ids"]:
                anchor = anchors[anchor_id]
                assert anchor["required_for_chapter_certification"] is True
                assert anchor["coverage_treatment"] not in COMPANION_TREATMENTS


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_misconceptions_and_assessment_skills_have_authored_remediation(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    manifest = load_manifest(_manifest_path(chapter_id))
    runtime_levels = {level["level_id"]: level for level in payload["levels"]}
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }
    remediated_skills: set[str] = set()

    for level in manifest.levels:
        runtime_level = runtime_levels[level.level_id]
        assert set(runtime_level["checks"]) == SUPPORT_CHECKS | {
            "guided_check",
            "independent_check",
            "transfer_check",
        }
        support_ids = {
            activity.activity_id
            for activity in level.support_checks.activities().values()
        }
        referenced_support: set[str] = set()
        level_remediation: set[str] = set()
        for cluster in level.misconception_clusters:
            assert len(cluster.misconception.split()) >= 6
            assert len(cluster.remediation.split()) >= 8
            level_remediation.update(cluster.skill_ids)
            referenced_support.update(cluster.support_check_ids)
        assert level_remediation == set(level.skill_ids)
        assert referenced_support == support_ids
        remediated_skills.update(level_remediation)
        for check_name in SUPPORT_CHECKS:
            check = runtime_level["checks"][check_name]
            assert check["target_misconception_tags"]
            assert set(check["knowledge_components"]) <= set(level.skill_ids)

    assessment = payload["chapter_assessment"]
    assessed_skills = {
        skill_id for item in assessment["items"] for skill_id in item["skill_ids"]
    }
    assert assessed_skills == taught_skills == remediated_skills


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_has_two_disjoint_complete_fourteen_item_forms(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }

    assert assessment["items_per_attempt"] == 14
    assert assessment["max_attempts"] == 2
    assert len(items) == 28
    assert len({item["item_id"] for item in items}) == 28
    assert all(
        sum(skill_id in item["skill_ids"] for item in items) >= 2
        for skill_id in taught_skills
    )

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
        for item in form:
            if item["options"]:
                assert not any(
                    skill_id.startswith(PRODUCTIVE_SKILL_PREFIXES)
                    for skill_id in item["skill_ids"]
                )
            else:
                assert item["grading_mode"] == "strict_open_rubric"
                assert item["rubric_criteria"]
                assert item["concept_slots"]
                assert item["model_answer"]


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_stimuli_are_separate_from_learning_and_each_other(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    learning_passages = []
    for level in payload["levels"]:
        learning_passages.extend(
            activity["passage"] for activity in level["checks"].values()
        )
        for step in level["teaching_steps"]:
            learning_passages.extend(
                activity["passage"]
                for activity in (step.get("variant_pool") or [step["activity"]])
            )

    items = payload["chapter_assessment"]["items"]
    first = _select_chapter_assessment_items(
        items,
        item_count=14,
        attempt_no=1,
        used_item_ids=set(),
    )
    second = _select_chapter_assessment_items(
        items,
        item_count=14,
        attempt_no=2,
        used_item_ids={item["item_id"] for item in first},
    )
    first_passages = [item["passage"] for item in first]
    second_passages = [item["passage"] for item in second]

    assert len(set(first_passages)) == len(first_passages) == 14
    assert len(set(second_passages)) == len(second_passages) == 14
    assert set(first_passages).isdisjoint(second_passages)
    assert set(first_passages + second_passages).isdisjoint(learning_passages)

    learning_ngrams = set().union(
        *(_ten_word_ngrams(passage) for passage in learning_passages)
    )
    first_ngrams = set().union(
        *(_ten_word_ngrams(passage) for passage in first_passages)
    )
    second_ngrams = set().union(
        *(_ten_word_ngrams(passage) for passage in second_passages)
    )
    assert not learning_ngrams.intersection(first_ngrams | second_ngrams)
    assert not first_ngrams.intersection(second_ngrams)

    for item in items:
        for learning_passage in learning_passages:
            assert _semantic_jaccard(item["passage"], learning_passage) < 0.65, (
                item["item_id"],
                item["passage"],
                learning_passage,
            )

    for left_index, left in enumerate(items):
        for right in items[left_index + 1 :]:
            assert _semantic_jaccard(left["passage"], right["passage"]) < 0.65, (
                left["item_id"],
                right["item_id"],
            )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_facing_content_has_no_ten_word_extract_overlap(
    chapter_id: str,
) -> None:
    extract_path = EXTRACT_ROOT / f"{chapter_id}.txt"
    if not extract_path.is_file():
        pytest.skip("official Class 3 structural extract is not available")

    source_ngrams = _ten_word_ngrams(extract_path.read_text(encoding="utf-8"))
    overlaps: set[tuple[str, ...]] = set()
    for activity in _activities(_payload(chapter_id)):
        for learner_string in _activity_strings(activity):
            overlaps.update(_ten_word_ngrams(learner_string) & source_ngrams)

    assert not overlaps, "copied 10-word sequence: " + " ".join(sorted(overlaps)[0])


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_strict_open_authority_closes_and_rejects_irrelevant_prose(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    open_activities = [
        activity
        for activity in _unique_activities(payload)
        if activity.get("grading_mode") == "strict_open_rubric"
    ]
    assert open_activities

    irrelevant = (
        "Education is important, and every learner should work hard because "
        "good habits make the whole school year successful."
    )
    for index, activity in enumerate(open_activities, start=1):
        model_result = _open_validation(
            activity,
            activity["model_answer"],
            probe_id=f"{chapter_id}:model-probe:{index}",
        )
        assert model_result.effective_blockers == (), (
            activity.get("item_id") or activity.get("variant_id"),
            model_result.effective_blockers,
        )
        assert model_result.certification_eligible is True

        irrelevant_result = _open_validation(
            activity,
            irrelevant,
            probe_id=f"{chapter_id}:irrelevant-probe:{index}",
        )
        assert irrelevant_result.certification_eligible is False
        if activity.get("semantic_evidence_policy") != "traceable_rubric":
            assert "semantic_required_claim_missing" in (
                irrelevant_result.effective_blockers
            )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_authored_paraphrase_probe_passes_without_using_the_model_answer(
    chapter_id: str,
) -> None:
    item_id = f"{chapter_id}:assessment:02"
    item = next(
        item
        for item in _payload(chapter_id)["chapter_assessment"]["items"]
        if item["item_id"] == item_id
    )
    paraphrase = PARAPHRASE_PROBES[item_id]

    assert paraphrase.casefold() != item["model_answer"].casefold()
    result = _open_validation(item, paraphrase, probe_id=item_id)

    assert result.effective_blockers == ()
    assert result.certification_eligible is True


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_strict_open_slots_do_not_share_aliases_or_certify_one_required_claim(
    chapter_id: str,
) -> None:
    open_activities = [
        activity
        for activity in _unique_activities(_payload(chapter_id))
        if activity.get("grading_mode") == "strict_open_rubric"
    ]
    multi_slot_activities = 0
    for index, activity in enumerate(open_activities, start=1):
        model_answer = " ".join(activity["model_answer"].casefold().split())
        alias_owners: dict[str, str] = {}
        slots = activity["concept_slots"]
        for slot in slots:
            for alias in slot["any_of"]:
                normalized_alias = " ".join(alias.casefold().split())
                assert normalized_alias != model_answer
                assert normalized_alias not in alias_owners, (
                    activity.get("item_id") or activity.get("variant_id"),
                    normalized_alias,
                    alias_owners.get(normalized_alias),
                    slot["id"],
                )
                alias_owners[normalized_alias] = slot["id"]

        if len(slots) < 2:
            continue
        multi_slot_activities += 1
        one_claim_only = (
            f'{slots[0]["any_of"][0]}. Education matters, and learners '
            "should work hard throughout the school year."
        )
        result = _open_validation(
            activity,
            one_claim_only,
            probe_id=f"{chapter_id}:one-claim-probe:{index}",
        )
        assert result.certification_eligible is False
        if activity.get("semantic_evidence_policy") != "traceable_rubric":
            assert "semantic_required_claim_missing" in result.effective_blockers

    assert multi_slot_activities


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_sequence_choices_name_the_exact_requested_position(chapter_id: str) -> None:
    position_pattern = re.compile(
        r"\b(?:first|second|third|fourth|last|immediately before|"
        r"immediately after)\b",
        flags=re.IGNORECASE,
    )
    sequence_choices = []
    for activity in _unique_activities(_payload(chapter_id)):
        skills = activity.get("skill_ids") or activity.get(
            "knowledge_components"
        ) or ()
        if (
            activity.get("grading_mode") == "selected_option"
            and "reading.event_sequence" in skills
        ):
            sequence_choices.append(activity)

    for activity in sequence_choices:
        visible_question = f'{activity["passage"]} {activity["prompt"]}'
        assert position_pattern.search(visible_question), visible_question


def test_chapter_2_capitalization_evidence_is_never_casefolded_choice() -> None:
    payload = _payload("eng_c3_ch02")
    capitalization_items = []
    for activity in _unique_activities(payload):
        skills = activity.get("skill_ids") or activity.get(
            "knowledge_components"
        ) or ()
        if (
            "grammar.punctuation_capitalization" in skills
            and activity.get("grading_mode")
        ):
            capitalization_items.append(activity)

    assert capitalization_items
    assessment_by_id = {
        item["item_id"]: item for item in payload["chapter_assessment"]["items"]
    }
    assert {
        assessment_by_id["eng_c3_ch02:assessment:09"]["grading_mode"],
        assessment_by_id["eng_c3_ch02:assessment:23"]["grading_mode"],
    } == {"strict_open_rubric"}
    for activity in capitalization_items:
        assert activity["grading_mode"] == "strict_open_rubric"
        rubric_text = " ".join(
            criterion["description"]
            for criterion in activity["rubric_criteria"]
        ).casefold()
        assert "capital" in rubric_text
        assert any(mark in rubric_text for mark in ("punctuation", "mark", "stop"))


def test_chapter_4_assessment_sentence_parts_are_actually_scrambled() -> None:
    assessment_by_id = {
        item["item_id"]: item
        for item in _payload("eng_c3_ch04")["chapter_assessment"]["items"]
    }
    for item_id in (
        "eng_c3_ch04:assessment:08",
        "eng_c3_ch04:assessment:22",
    ):
        item = assessment_by_id[item_id]
        parts = [
            part.strip().casefold()
            for part in item["passage"].removeprefix("Parts:").split("/")
        ]
        answer = item["model_answer"].casefold()
        answer_positions = [answer.index(part) for part in parts]

        assert answer_positions != sorted(answer_positions), item["passage"]


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_support_is_misconception_specific_reteaching(chapter_id: str) -> None:
    payload = _payload(chapter_id)
    manifest = load_manifest(_manifest_path(chapter_id))
    manifest_levels = {level.level_id: level for level in manifest.levels}

    for runtime_level in payload["levels"]:
        manifest_level = manifest_levels[runtime_level["level_id"]]
        remediation = " ".join(
            cluster.remediation for cluster in manifest_level.misconception_clusters
        ).casefold()
        remediation_tokens = {
            token
            for token in TOKEN_PATTERN.findall(remediation)
            if len(token) >= 5
        }
        support = [
            runtime_level["checks"][name]
            for name in sorted(SUPPORT_CHECKS)
        ]
        teaching_blocks = [activity["teaching_block"] for activity in support]

        assert len(teaching_blocks) == len(set(teaching_blocks)) == 5
        for teaching_block in teaching_blocks:
            lowered = teaching_block.casefold()
            assert "worked example" in lowered
            assert "new card" in lowered or "another case" in lowered
            assert len(
                remediation_tokens.intersection(TOKEN_PATTERN.findall(lowered))
            ) >= 4


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_instructions_use_class_3_language(chapter_id: str) -> None:
    payload = _payload(chapter_id)
    for activity in _activities(payload):
        learner_instructions = " ".join(
            str(activity.get(field) or "")
            for field in ("teaching_block", "prompt")
        ).casefold()
        for banned_phrase in BANNED_LEARNER_PHRASES:
            assert banned_phrase not in learner_instructions

    all_learner_text = " ".join(_learner_facing_strings(payload)).casefold()
    for banned_phrase in BANNED_LEARNER_PHRASES:
        assert banned_phrase not in all_learner_text


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_public_support_copy_never_requires_unavailable_annotation_tools(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        for support_name in SUPPORT_CHECKS:
            teaching_block = level["checks"][support_name]["teaching_block"]
            _, separator, remediation = teaching_block.partition("Fix it this way:")
            assert separator
            assert not UNSUPPORTED_UI_ACTION_PATTERN.search(remediation), (
                level["level_id"],
                support_name,
                remediation,
            )


def test_reported_copy_corruptions_have_clear_authored_replacements() -> None:
    chapter_1 = _payload("eng_c3_ch01")
    chapter_3 = _payload("eng_c3_ch03")
    levels_1 = {level["level_id"]: level for level in chapter_1["levels"]}
    levels_3 = {level["level_id"]: level for level in chapter_3["levels"]}

    assert levels_1["poetic_pattern_and_short_answer"]["teaching_goal"] == (
        "Explain how a repeated word or colour image shapes a short poem and "
        "answer a focused question in one or two clear sentences using poem clues."
    )
    assert levels_3["shape_attribute_order"]["title"] == (
        "Order shapes by one stated feature"
    )
    assert levels_3["clear_pronouns_and_traits"]["teaching_goal"] == (
        "Connect each pronoun to one clear person or object and use a given "
        "cooperation trait in a fresh profile sentence supported by the card."
    )

    assessment_1 = {
        item["item_id"]: item
        for item in chapter_1["chapter_assessment"]["items"]
    }
    assert assessment_1["eng_c3_ch01:assessment:01"]["prompt"] == (
        "What does pale green mean in this sentence?"
    )
    assert assessment_1["eng_c3_ch01:assessment:15"]["prompt"] == (
        "What does vivid blue mean in this sentence?"
    )
