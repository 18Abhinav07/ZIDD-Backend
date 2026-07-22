from __future__ import annotations

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
    / "class_4"
)
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_4"
)
EXTRACT_ROOT = Path("/tmp/zidd-ncert-class4")
CHAPTER_IDS = tuple(f"eng_c4_ch{chapter_no:02d}" for chapter_no in range(7, 13))
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
SUPPORT_SEQUENCE = (
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
)
MIN_VARIANTS = {
    "guided_practice": 4,
    "independent_application": 4,
    "transfer": 4,
    "review": 4,
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
EXPECTED_CHAPTER_CONCEPTS = {
    "eng_c4_ch07": ("active routine", "adjective", "rhyme", "balanced plan"),
    "eng_c4_ch08": ("teamwork", "event sequence", "question mark", "game procedure"),
    "eng_c4_ch09": ("inside the circle", "surrender", "past tense", "rule redesign"),
    "eng_c4_ch10": ("viewpoint", "noun and verb", "preposition", "sentence expansion"),
    "eng_c4_ch11": ("mountain journey", "body-part metaphor", "conjunction", "nature care"),
    "eng_c4_ch12": ("heritage facts", "silent letter", "article", "historical place"),
}
FORBIDDEN_AUTHORING_LANGUAGE = (
    "independent case",
    "guided case",
    "transfer case",
    "review case",
    "required concept",
    "required idea",
    "reading purpose",
    "misconception check",
    "the learner",
    "supplied clue controls",
    "evidence note",
    "authored criterion",
    "bounded record",
    "archive packet",
    "field record",
    "specific mistake described as",
    "independent task",
    "guided task",
    "transfer task",
    "review task",
    "masterclass task",
    "bounded packet",
    "bounded heritage",
    "bounded facts",
    "supplied facts",
    "supplied heritage",
    "whole record",
    "fits this account",
    "evidence limit",
    "recorded result",
)
GENERIC_DISTRACTOR_LANGUAGE = (
    "only the location matters",
    "provides no clue",
    "any outside fact is stronger",
    "changing the event order would leave",
    "opening note proves the opposite",
    "action and result can be ignored",
)
GENERATOR_PADDING_LANGUAGE = (
    "after the group made the space safe",
    "the group talked about",
    "opening condition beside the exact middle choice",
    "evidence keeps",
    "outside guess",
)
SUPPORT_TEACHING_MARKERS = {
    "bridge": "worked example:",
    "masterclass": "why it works:",
    "revision_level_1": "guided repair:",
    "revision_level_2": "short hint:",
    "revision_level_3": "independent retry:",
}
LANGUAGE_OUTCOME_LEVELS = {
    "eng_c4_ch07": {
        "fit_double_letter_spelling": (
            {"vocab.spelling"},
            ("double letter", "spelling"),
        ),
        "fit_poetic_balanced_plan": (
            {"reading.poetic_language"},
            ("rhyme",),
        ),
    },
    "eng_c4_ch08": {
        "lagori_word_unscrambling": (
            {"grammar.sentence_order"},
            ("unscramble", "scrambled"),
        ),
    },
    "eng_c4_ch09": {
        "hekko_homophones": (
            {"vocab.spelling"},
            ("homophone",),
        ),
        "hekko_clusters_and_animal_sounds": (
            {"vocab.word_formation", "reading.poetic_language"},
            ("consonant cluster", "animal sound"),
        ),
    },
}


def _manifest_path(chapter_id: str) -> Path:
    return MANIFEST_ROOT / f"{chapter_id}.py"


def _chapter_path(chapter_id: str) -> Path:
    return CHAPTER_ROOT / f"{chapter_id}.json"


def _payload(chapter_id: str) -> dict:
    return json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))


def _level_activities(level: dict):
    for step in level["teaching_steps"]:
        if step.get("activity") is not None:
            yield step["activity"]
        else:
            yield from step["variant_pool"]
    for check_name in SUPPORT_CHECKS:
        yield level["checks"][check_name]


def _activities(payload: dict):
    for level in payload["levels"]:
        yield from _level_activities(level)


def _words(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z]+(?:'[a-z]+)?", value.casefold()))


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
        "explain",
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


def _claim_signature(value: str) -> set[str]:
    normalized = value.casefold()
    for alternate, canonical in (
        ("the central message is", "the main idea is"),
        ("refers to", "means"),
        ("since", "because"),
        ("at the beginning", "first"),
        ("after that", "next"),
        ("at the end", "finally"),
        ("demonstrates", "shows"),
        ("demonstrating", "showing"),
        ("applies", "uses"),
        ("states", "writes"),
        ("supports", "helps"),
        ("supported", "helped"),
        ("as a group", "together"),
        ("low-risk", "safe"),
        ("outcome", "result"),
    ):
        normalized = normalized.replace(alternate, canonical)
    ignored = {
        "a",
        "an",
        "and",
        "according",
        "are",
        "at",
        "confirms",
        "for",
        "in",
        "is",
        "of",
        "on",
        "or",
        "record",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
    }
    return {word for word in _words(normalized) if word not in ignored}


def _windows(value: str, size: int = 10) -> set[tuple[str, ...]]:
    words = _words(value)
    return {
        words[index : index + size]
        for index in range(max(0, len(words) - size + 1))
    }


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


def _all_authored_activities(payload: dict):
    yield from _activities(payload)
    for item in payload["chapter_assessment"]["items"]:
        yield item


def _activity_skills(activity: dict) -> set[str]:
    return set(activity.get("knowledge_components") or activity.get("skill_ids") or ())


def _named_story(activity: dict) -> str:
    match = re.search(
        r"\b(?:read|try) the (.+?) story\b",
        activity["prompt"].casefold(),
    )
    assert match, activity["prompt"]
    return _normalise(match.group(1))


def _activity_identifier(activity: dict) -> str:
    item_id = (
        activity.get("activity_id")
        or activity.get("variant_id")
        or activity.get("item_id")
    )
    if item_id:
        return str(item_id)
    slots = activity.get("concept_slots") or ()
    assert slots, activity
    return f"focused-contract:{slots[0]['id']}"


def _positive_open_payload(activity: dict, answer: str) -> dict:
    item_id = _activity_identifier(activity)
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": item_id,
        "skill_ids": list(activity.get("skill_ids") or activity["knowledge_components"]),
        "score": 0.92,
        "confidence": 0.94,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": True,
                "quality": 0.9,
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The response addresses the required ideas.",
    }


def _open_context(activity: dict, answer: str):
    internal = {
        **activity,
        "activity_id": _activity_identifier(activity),
        "skill_ids": list(
            activity.get("skill_ids") or activity.get("knowledge_components") or ()
        ),
    }
    return school_open_context_from_activity(internal, answer)


def _slot_specific_positive_payload(
    activity: dict,
    answer: str,
    *,
    alias_index: int,
) -> dict:
    payload = _positive_open_payload(activity, answer)
    slots = {slot["id"]: slot for slot in activity["concept_slots"]}
    payload["criteria"] = [
        {
            "id": criterion["id"],
            "met": True,
            "quality": 0.9,
            "evidence_quote": slots[criterion["id"]]["any_of"][alias_index],
        }
        for criterion in activity["rubric_criteria"]
    ]
    return payload


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
    assert len(activity["model_answer"].split()) >= activity["min_response_words"]


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
    assert 7 <= len(manifest.levels) <= 9
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
def test_taxonomy_and_learning_breadth_are_class_four_calibrated(chapter_id):
    payload = _payload(chapter_id)
    taxonomy = {entry.skill_id: entry for entry in LOCKED_ENGLISH_TAXONOMY_ENTRIES}
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }

    assert 7 <= len(payload["levels"]) <= 9
    assert 8 <= len(taught_skills) <= 15
    assert taught_skills <= set(taxonomy)
    assert all(
        taxonomy[skill_id].class_min <= 4 <= taxonomy[skill_id].class_max
        for skill_id in taught_skills
    )
    assert not taught_skills.intersection(UNOBSERVABLE_TEXT_ONLY_SKILLS)
    assert {
        "reading.word_meaning_context",
        "reading.paragraph_main_idea",
        "reading.event_sequence",
        "reading.inference_reason",
        "vocab.chapter_word_usage",
        "writing.complete_sentence",
        "writing.reason_answer",
    } <= taught_skills
    assert any(skill_id.startswith("grammar.") for skill_id in taught_skills)
    assert any(
        skill_id in taught_skills
        for skill_id in {
            "writing.paragraph",
            "writing.procedure",
            "writing.summary_own_words",
        }
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
    companion_ids = {anchor["anchor_id"] for anchor in modality_anchors}
    for activity in _activities(payload):
        if activity["evidence_role"] == "certifying":
            assert set(activity["source_anchor_ids"]).isdisjoint(companion_ids)
    assert all(
        anchor["source_url"].startswith(
            f"https://ncert.nic.in/textbook/pdf/desa1{chapter_id[-2:]}.pdf#page="
        )
        for anchor in anchors
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_every_level_has_the_exact_deep_authored_loop(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == PHASES
        by_phase = {step["phase"]: step for step in steps}
        assert by_phase["connect"]["activity"]["interaction_type"] == "continue"
        assert by_phase["co_construct"]["activity"]["evidence_role"] == "formative"

        for phase in (
            "guided_practice",
            "independent_application",
            "transfer",
            "review",
        ):
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) >= MIN_VARIANTS[phase]
            assert len({(item["passage"], item["prompt"]) for item in variants}) == len(
                variants
            )
            expected_role = "supported" if phase == "guided_practice" else "certifying"
            assert all(item["evidence_role"] == expected_role for item in variants)

        for phase in ("independent_application", "transfer", "review"):
            for activity in by_phase[phase]["variant_pool"]:
                _assert_strict_open(activity)
                assert activity["certifying_language"] == "en"

        for phase in ("independent_application", "transfer", "review"):
            for activity in by_phase[phase]["variant_pool"]:
                if any(
                    skill_id.startswith("reading.")
                    for skill_id in activity["knowledge_components"]
                ):
                    assert 18 <= len(_words(activity["passage"])) <= 160

        for activity in _level_activities(level):
            visible_text = " ".join(
                str(activity.get(key, "")).casefold()
                for key in ("teaching_block", "passage", "prompt")
            )
            assert not any(direction in visible_text for direction in UNSEEN_RUNTIME_DIRECTIONS)
            if activity["interaction_type"] == "continue":
                assert activity["evidence_role"] == "experience"
                continue
            if activity["options"]:
                assert not any(
                    skill_id.startswith(PRODUCTIVE_PREFIXES)
                    for skill_id in activity["knowledge_components"]
                )
            else:
                _assert_strict_open(activity)


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
            item["teaching_block"].casefold().startswith(
                SUPPORT_TEACHING_MARKERS[name]
            )
            for name, item in zip(SUPPORT_SEQUENCE, support, strict=True)
        )
        assert all("try the" in item["prompt"].casefold() for item in support)
        assert [item["min_response_words"] for item in support] == sorted(
            item["min_response_words"] for item in support
        )
        assert len({item["min_response_words"] for item in support}) == 5

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
def test_named_scenarios_and_semantic_answers_are_fresh_across_phases(chapter_id):
    payload = _payload(chapter_id)
    phase_names = (
        "guided_practice",
        "independent_application",
        "transfer",
        "review",
        "masterclass",
    )

    for level in payload["levels"]:
        by_phase = {
            step["phase"]: step["variant_pool"]
            for step in level["teaching_steps"]
            if step.get("variant_pool") is not None
        }
        by_phase["masterclass"] = [level["checks"]["masterclass"]]
        for left_phase, right_phase in combinations(phase_names, 2):
            for left in by_phase[left_phase]:
                left_answer = left.get("model_answer") or left["accepted_answers"][0]
                for right in by_phase[right_phase]:
                    right_answer = right.get("model_answer") or right["accepted_answers"][0]
                    assert _named_story(left) != _named_story(right), (
                        level["level_id"],
                        left_phase,
                        right_phase,
                    )
                    assert _semantic_jaccard(left_answer, right_answer) < 0.72, (
                        level["level_id"],
                        left_phase,
                        right_phase,
                        left_answer,
                        right_answer,
                    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_transfer_and_review_have_four_distinct_grounded_scenarios(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        by_phase = {
            step["phase"]: step["variant_pool"]
            for step in level["teaching_steps"]
            if step.get("variant_pool") is not None
        }
        launch_activities = [*by_phase["transfer"], *by_phase["review"]]

        assert len(by_phase["transfer"]) == 4
        assert len(by_phase["review"]) == 4
        assert len({_named_story(activity) for activity in launch_activities}) == 8
        for left_index, left in enumerate(launch_activities):
            for right in launch_activities[left_index + 1 :]:
                assert _semantic_jaccard(left["passage"], right["passage"]) < 0.72, (
                    chapter_id,
                    level["level_id"],
                    left["activity_id"],
                    right["activity_id"],
                )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_child_facing_copy_contains_no_authoring_or_evaluator_jargon(chapter_id):
    payload = _payload(chapter_id)

    for activity in _all_authored_activities(payload):
        visible = " ".join(
            str(activity.get(field, "")).casefold()
            for field in ("teaching_block", "passage", "prompt")
        )
        assert not any(phrase in visible for phrase in FORBIDDEN_AUTHORING_LANGUAGE), (
            activity.get("activity_id") or activity.get("item_id"),
            visible,
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_copy_has_no_focus_labels_padding_or_overlong_prompts(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        focus = _normalise(level["focus"])
        for activity in _level_activities(level):
            activity_label = (
                activity.get("activity_id")
                or activity.get("variant_id")
                or activity.get("item_id")
                or f"{level['level_id']}:{activity['prompt']}"
            )
            passage_and_prompt = _normalise(
                f"{activity['passage']} {activity['prompt']}"
            )
            assert focus not in passage_and_prompt, activity_label
            assert len(_words(activity["prompt"])) <= 30, (
                activity_label,
                activity["prompt"],
            )
            visible = f"{activity['passage']} {activity['prompt']}".casefold()
            assert not any(
                phrase in visible for phrase in GENERATOR_PADDING_LANGUAGE
            ), (activity_label, visible)
            assert ".." not in activity.get("model_answer", "")

    for item in payload["chapter_assessment"]["items"]:
        assert len(_words(item["prompt"])) <= 30, (item["item_id"], item["prompt"])
        visible = f"{item['passage']} {item['prompt']}".casefold()
        assert not any(phrase in visible for phrase in GENERATOR_PADDING_LANGUAGE), (
            item["item_id"],
            visible,
        )
        assert ".." not in item.get("model_answer", "")


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_semantic_slots_never_use_dangling_transition_fragments(chapter_id):
    payload = _payload(chapter_id)
    dangling_end = re.compile(r"\.\s*(?:next|then|finally)\s*$", re.IGNORECASE)

    for activity in _all_authored_activities(payload):
        for slot in activity.get("concept_slots") or ():
            values = [slot["description"], *slot["any_of"]]
            for value in values:
                normalized = value.strip()
                assert not dangling_end.search(normalized), (
                    _activity_identifier(activity),
                    normalized,
                )
                assert not normalized.casefold().startswith("and "), (
                    _activity_identifier(activity),
                    normalized,
                )
                assert "shows that and " not in normalized.casefold(), (
                    _activity_identifier(activity),
                    normalized,
                )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_support_roles_are_distinct_and_scaffolds_fade(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        checks = level["checks"]
        support = [checks[name] for name in SUPPORT_SEQUENCE]
        for name, activity in zip(SUPPORT_SEQUENCE, support, strict=True):
            assert activity["teaching_block"].casefold().startswith(
                SUPPORT_TEACHING_MARKERS[name]
            ), (level["level_id"], name, activity["teaching_block"])
        assert "two clues" in checks["revision_level_1"]["teaching_block"].casefold()
        assert "one clue" in checks["revision_level_2"]["teaching_block"].casefold()
        assert "without a hint" in checks["revision_level_3"]["teaching_block"].casefold()
        assert len(_words(checks["bridge"]["prompt"])) <= 22
        assert (
            checks["independent_check"]["teaching_block"]
            != checks["transfer_check"]["teaching_block"]
        )
        assert "new setting" in checks["transfer_check"]["teaching_block"].casefold()


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_has_two_disjoint_fifteen_item_forms_with_full_coverage(
    chapter_id,
):
    payload = _payload(chapter_id)
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }
    teaching_passages = [activity["passage"] for activity in _activities(payload)]

    assert assessment["items_per_attempt"] == 15
    assert assessment["max_attempts"] == 2
    assert len(items) == 30
    assert len({item["item_id"] for item in items}) == 30
    assert all(
        _normalise(item["passage"])
        not in {_normalise(passage) for passage in teaching_passages}
        for item in items
    )
    assert all(
        not any(
            direction in f"{item['passage']} {item['prompt']}".casefold()
            for direction in UNSEEN_RUNTIME_DIRECTIONS
        )
        for item in items
    )
    for item in items:
        productive = any(
            skill_id.startswith(PRODUCTIVE_PREFIXES)
            for skill_id in item["skill_ids"]
        )
        if productive:
            assert not item["options"]
        if not item["options"]:
            _assert_strict_open(item)
        if any(skill_id.startswith("reading.") for skill_id in item["skill_ids"]):
            assert 18 <= len(_words(item["passage"])) <= 160

    first = _select_chapter_assessment_items(
        items,
        item_count=15,
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=15,
        attempt_no=2,
        used_item_ids=first_ids,
    )
    assert len(first) == len(second) == 15
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
            not _windows(item_authority, 10).intersection(_windows(teaching_passage, 10))
            for teaching_passage in teaching_passages
        )

    for left, right in ((left, right) for left in first for right in second):
        left_authority = f"{left['passage']} {left['prompt']}"
        right_authority = f"{right['passage']} {right['prompt']}"
        assert _semantic_jaccard(left_authority, right_authority) < 0.72
        assert not _windows(left_authority, 10).intersection(
            _windows(right_authority, 10)
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_selected_options_use_plausible_story_specific_distractors(chapter_id):
    payload = _payload(chapter_id)
    items = payload["chapter_assessment"]["items"]
    first = _select_chapter_assessment_items(
        items,
        item_count=15,
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=15,
        attempt_no=2,
        used_item_ids=first_ids,
    )

    for form in (first, second):
        positions = []
        for item in form:
            if not item["options"]:
                continue
            correct = item["accepted_answers"][0]
            positions.append(item["options"].index(correct))
            passage_words = _content_words(item["passage"])
            assert len(item["options"]) == len(set(item["options"])) == 4
            for distractor in item["options"]:
                if distractor == correct:
                    continue
                normalized = distractor.casefold()
                assert not any(
                    phrase in normalized for phrase in GENERIC_DISTRACTOR_LANGUAGE
                )
                assert len(_content_words(distractor) & passage_words) >= 2, (
                    item["item_id"],
                    distractor,
                )
        assert len(set(positions)) >= 3


@pytest.mark.parametrize(
    ("chapter_id", "level_id", "expected_skills", "markers"),
    [
        (chapter_id, level_id, expected_skills, markers)
        for chapter_id, levels in LANGUAGE_OUTCOME_LEVELS.items()
        for level_id, (expected_skills, markers) in levels.items()
    ],
)
def test_declared_language_outcomes_are_taught_and_certified(
    chapter_id,
    level_id,
    expected_skills,
    markers,
):
    payload = _payload(chapter_id)
    level = next(level for level in payload["levels"] if level["level_id"] == level_id)
    assert expected_skills <= set(level["skill_ids"])

    by_phase = {step["phase"]: step for step in level["teaching_steps"]}
    for phase in ("independent_application", "transfer", "review"):
        phase_text = " ".join(
            " ".join(
                str(activity.get(field, "")).casefold()
                for field in ("teaching_block", "passage", "prompt", "model_answer")
            )
            for activity in by_phase[phase]["variant_pool"]
        )
        assert all(marker in phase_text for marker in markers)

    assessment_items = [
        item
        for item in payload["chapter_assessment"]["items"]
        if expected_skills.intersection(item["skill_ids"])
    ]
    assessment_text = " ".join(
        " ".join(
            str(item.get(field, "")).casefold()
            for field in ("passage", "prompt", "model_answer")
        )
        for item in assessment_items
    )
    assert len(assessment_items) >= 2
    assert all(marker in assessment_text for marker in markers)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_open_rubric_claims_are_independent_and_paraphrase_friendly(chapter_id):
    payload = _payload(chapter_id)

    for activity in _all_authored_activities(payload):
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        model_answer = _normalise(activity["model_answer"])
        slots = activity["concept_slots"]
        criterion_ids = {
            criterion["id"] for criterion in activity["rubric_criteria"]
        }
        assert len(criterion_ids) == len(activity["rubric_criteria"])
        assert criterion_ids == {slot["id"] for slot in slots}
        assert all(criterion["required"] for criterion in activity["rubric_criteria"])
        alias_sets = []
        for slot in slots:
            aliases = {_normalise(alias) for alias in slot["any_of"]}
            assert len(aliases) >= 2
            assert model_answer not in aliases
            canonical_claim = _claim_signature(slot["any_of"][0])
            assert canonical_claim
            assert all(
                canonical_claim <= _claim_signature(alias)
                for alias in slot["any_of"]
            )
            alias_sets.append(aliases)
        for left, right in combinations(alias_sets, 2):
            assert left.isdisjoint(right)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_every_strict_open_model_closes_its_own_semantic_contract(chapter_id):
    payload = _payload(chapter_id)

    for activity in _all_authored_activities(payload):
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        answer = activity["model_answer"]
        context = _open_context(activity, answer)
        validated = validate_school_open_evaluation(
            _slot_specific_positive_payload(activity, answer, alias_index=0),
            context=context,
        )
        assert validated.effective_blockers == (), (
            _activity_identifier(activity),
            validated.effective_blockers,
        )
        assert validated.certification_eligible is True


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_model_answers_are_grounded_and_grammatically_well_formed(chapter_id):
    payload = _payload(chapter_id)
    malformed = (
        r"\brecord record\b",
        r"\bpacket packet\b",
        r"\bexample of (?:interpret|use|order)\b",
        r"\bshould\s+(?:listed|assigned|saw|introduced|heard|selected|described|kept)\b",
        r"\baction that produced the (?:the\s+)?[a-z]+\s+(?:ended|finished|began|returned|remained)\b",
    )

    for activity in _all_authored_activities(payload):
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        answer = activity["model_answer"]
        normalized = answer.casefold()
        assert not any(re.search(pattern, normalized) for pattern in malformed), (
            activity.get("activity_id") or activity.get("item_id"),
            answer,
        )
        assert len(
            _content_words(answer)
            & _content_words(f"{activity['passage']} {activity['prompt']}")
        ) >= 2
        if {
            "reading.inference_reason",
            "writing.reason_answer",
        }.intersection(_activity_skills(activity)):
            assert not re.search(r"\bbecause\s+[a-z]+ed\b", answer)
        if {
            "writing.paragraph",
            "writing.procedure",
        }.intersection(_activity_skills(activity)):
            assert not any(
                phrase in normalized
                for phrase in (
                    "bounded record",
                    "supplied result",
                    "packet",
                    "authored criterion",
                )
            )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_paragraph_and_procedure_tasks_certify_real_class_four_writing(chapter_id):
    payload = _payload(chapter_id)
    found = {"writing.paragraph": 0, "writing.procedure": 0}

    for activity in _all_authored_activities(payload):
        skills = _activity_skills(activity)
        writing_skill = next(
            (skill for skill in found if skill in skills),
            None,
        )
        if writing_skill is None:
            continue
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        found[writing_skill] += 1
        _assert_strict_open(activity)
        answer = activity["model_answer"]
        descriptions = " ".join(
            criterion["description"].casefold()
            for criterion in activity["rubric_criteria"]
        )
        assert len(activity["rubric_criteria"]) >= 4

        is_support = any(
            activity.get("teaching_block", "").casefold().startswith(marker)
            for marker in SUPPORT_TEACHING_MARKERS.values()
        )
        if writing_skill == "writing.paragraph":
            assert activity["min_response_words"] >= (28 if is_support else 45)
            assert len(re.findall(r"[.!?](?:\s|$)", answer)) >= 4
            assert all(
                marker in descriptions
                for marker in ("opening", "support", "link", "closing")
            )
            assert "paragraph" in activity["prompt"].casefold()
        else:
            assert activity["min_response_words"] >= (30 if is_support else 50)
            assert all(
                marker in answer.casefold()
                for marker in (
                    "materials:",
                    "first,",
                    "next,",
                    "then,",
                    "finally,",
                    "safety",
                )
            )
            assert all(
                marker in descriptions
                for marker in ("materials", "ordered", "safety", "punctuation")
            )
            assert activity["ordered_concept_slot_ids"] == [
                slot["id"] for slot in activity["concept_slots"]
            ]

    assert any(found.values())


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
            "teaching_block": "Work independently from the visible passage.",
            "attempt_no": 1,
        }
        public = _public_activity(internal)
        assert public is not None
        assert not (HIDDEN_GRADING_FIELDS & set(public))


def test_authored_paraphrase_passes_the_real_open_evaluator_contract():
    payload = _payload("eng_c4_ch07")
    activity = next(
        activity
        for activity in payload["chapter_assessment"]["items"]
        if activity.get("grading_mode") == "strict_open_rubric"
        and activity["min_response_words"] <= 20
    )
    paraphrase_parts = [slot["any_of"][-1] for slot in activity["concept_slots"]]
    answer = ". ".join(paraphrase_parts)
    if len(_words(answer)) < activity["min_response_words"]:
        answer += " The supplied details make both ideas clear."

    assert _normalise(answer) != _normalise(activity["model_answer"])
    context = _open_context(activity, answer)
    validated = validate_school_open_evaluation(
        _slot_specific_positive_payload(activity, answer, alias_index=-1),
        context=context,
    )

    assert validated.effective_blockers == ()
    assert validated.certification_eligible is True


def test_positive_typed_llm_result_cannot_certify_irrelevant_prose():
    payload = _payload("eng_c4_ch07")
    activity = next(
        activity
        for activity in payload["chapter_assessment"]["items"]
        if activity.get("grading_mode") == "strict_open_rubric"
    )
    answer = (
        "School is valuable, kindness is important, and every learner should "
        "stay cheerful while working hard throughout the year."
    )
    context = _open_context(activity, answer)
    validated = validate_school_open_evaluation(
        _positive_open_payload(activity, answer),
        context=context,
    )

    assert validated.aggregate_score >= context.pass_score
    assert validated.meets_required_criteria is True
    assert validated.evaluation.blockers == ()
    assert validated.backend_blockers
    assert validated.certification_eligible is False


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_single_detail_cannot_certify_a_composite_assessment(chapter_id):
    payload = _payload(chapter_id)
    activity = next(
        item
        for item in payload["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    )
    answer = (
        f"{activity['concept_slots'][0]['any_of'][0]}. This sentence contains "
        "enough extra words to pass the response length check but no other "
        "required detail."
    )
    validated = validate_school_open_evaluation(
        _positive_open_payload(activity, answer),
        context=_open_context(activity, answer),
    )

    assert validated.certification_eligible is False
    assert any(
        blocker.startswith("semantic_")
        for blocker in validated.effective_blockers
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_all_learner_authority_is_original_at_ten_word_window(chapter_id):
    extract_path = EXTRACT_ROOT / f"{chapter_id}.txt"
    if not extract_path.is_file():
        pytest.skip("official Class 4 structural extract is not available")
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


def test_chapters_are_specific_and_not_interchangeable_templates():
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
        len(prompts) * 0.75
    )


def _level(payload: dict, level_id: str) -> dict:
    return next(level for level in payload["levels"] if level["level_id"] == level_id)


def _visible_and_grading_text(activity: dict) -> tuple[str, str]:
    visible = " ".join(
        str(activity.get(field, ""))
        for field in ("teaching_block", "passage", "prompt", "model_answer")
    ).casefold()
    grading = " ".join(
        criterion["description"]
        for criterion in activity.get("rubric_criteria") or ()
    ).casefold()
    return visible, grading


def _answer_authority(activity: dict) -> str:
    return activity.get("model_answer") or activity["accepted_answers"][0]


def test_chapter_nine_separates_animal_sound_matching_from_cluster_analysis():
    payload = _payload("eng_c4_ch09")
    level = _level(payload, "hekko_clusters_and_animal_sounds")
    level_text = json.dumps(level, ensure_ascii=False).casefold()

    assert "consonant cluster chr" not in level_text
    assert "chirrup begins with the consonant cluster" not in level_text
    assert "a owl" not in level_text
    assert "a elephant" not in level_text

    for activity in _level_activities(level):
        visible, grading = _visible_and_grading_text(activity)
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        assert "animal" in visible and "sound" in visible
        assert "cluster" in visible
        assert "animal" in grading and "sound" in grading
        assert "cluster" in grading


def test_chapter_eleven_body_part_metaphor_is_required_and_graded_every_time():
    payload = _payload("eng_c4_ch11")
    level = _level(payload, "mountain_metaphor_care_paragraph")
    body_parts = {"foot", "mouth", "arm", "heart", "shoulder"}

    for activity in _level_activities(level):
        visible, grading = _visible_and_grading_text(activity)
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        assert body_parts.intersection(_words(visible)), _activity_identifier(activity)
        assert "metaphor" in visible
        assert "metaphor" in grading
        assert any(marker in grading for marker in ("shared feature", "nonliteral"))
        assert "care" in grading

    metaphor_items = [
        item
        for item in payload["chapter_assessment"]["items"]
        if "reading.poetic_language" in item["skill_ids"]
    ]
    assert len(metaphor_items) >= 2
    for item in metaphor_items:
        visible, grading = _visible_and_grading_text(item)
        assert body_parts.intersection(_words(visible))
        assert "metaphor" in visible
        if item.get("grading_mode") == "strict_open_rubric":
            assert "metaphor" in grading
        else:
            assert "metaphor" in _answer_authority(item).casefold()


def test_chapter_twelve_article_decisions_are_required_and_graded_every_time():
    payload = _payload("eng_c4_ch12")
    level = _level(payload, "maheshwar_article_place_paragraph")

    for activity in _level_activities(level):
        visible, grading = _visible_and_grading_text(activity)
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        assert "article" in visible
        assert all(article in _words(visible) for article in ("a", "an", "the"))
        assert "article" in grading
        assert all(article in _words(grading) for article in ("a", "an", "the"))
        assert "first mention" in grading and "later mention" in grading

    article_items = [
        item
        for item in payload["chapter_assessment"]["items"]
        if "grammar.sentence_order" in item["skill_ids"]
    ]
    assert len(article_items) >= 2
    for item in article_items:
        visible, grading = _visible_and_grading_text(item)
        assert "article" in visible
        assert all(article in _words(visible) for article in ("a", "an", "the"))
        if item.get("grading_mode") == "strict_open_rubric":
            assert "article" in grading
        else:
            assert all(
                article in _words(_answer_authority(item))
                for article in ("a", "an", "the")
            )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_no_known_broken_template_prose_or_implausible_distractors(chapter_id):
    payload = _payload(chapter_id)
    broken_copy = (
        "used the for each known object later",
        "after the activity began",
        "reach a useful ending",
        "the name of the",
        "the opposite of the clue",
        "describes only how",
        "specific mistake described as",
    )

    for activity in _all_authored_activities(payload):
        learner_copy = " ".join(_learner_strings(activity)).casefold()
        assert not any(phrase in learner_copy for phrase in broken_copy), (
            _activity_identifier(activity),
            learner_copy,
        )


def test_critical_assessments_use_fresh_target_examples():
    chapter_nine = _payload("eng_c4_ch09")["chapter_assessment"]["items"]
    cluster_items = [
        item
        for item in chapter_nine
        if {"vocab.word_formation", "reading.poetic_language"}.intersection(
            item["skill_ids"]
        )
    ]
    assert len(cluster_items) >= 4
    assert len({item["passage"] for item in cluster_items}) == len(cluster_items)
    assert len({_answer_authority(item) for item in cluster_items}) == len(cluster_items)

    chapter_twelve = _payload("eng_c4_ch12")["chapter_assessment"]["items"]
    article_items = [
        item
        for item in chapter_twelve
        if "grammar.sentence_order" in item["skill_ids"]
    ]
    assert len(article_items) >= 2
    assert len({_answer_authority(item) for item in article_items}) == len(article_items)
    assert all(
        _normalise(_answer_authority(item)) not in _normalise(item["passage"])
        for item in article_items
    )
