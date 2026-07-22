from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.content.school_v3_taxonomy import locked_english_skill_ids
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services.school_rebuild_curriculum import _select_chapter_assessment_items
from app.services import school_rebuild_curriculum as curriculum
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
CHAPTER_IDS = tuple(f"eng_c4_ch{number:02d}" for number in range(1, 7))
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
    "eng_c4_ch01": (1, 8),
    "eng_c4_ch02": (9, 24),
    "eng_c4_ch03": (25, 34),
    "eng_c4_ch04": (35, 42),
    "eng_c4_ch05": (43, 54),
    "eng_c4_ch06": (55, 66),
}
SECTION_WORDS = {
    "eng_c4_ch01": ("recite", "think", "speak", "learn", "write", "do"),
    "eng_c4_ch02": (
        "read",
        "think",
        "learn",
        "listen",
        "speak",
        "write",
        "do",
        "matchsticks",
        "explore",
    ),
    "eng_c4_ch03": ("read", "think", "learn", "do", "write"),
    "eng_c4_ch04": (
        "recite",
        "think",
        "learn",
        "speak",
        "listen",
        "write",
        "do",
    ),
    "eng_c4_ch05": ("read", "think", "learn", "write", "speak", "do"),
    "eng_c4_ch06": (
        "read",
        "think",
        "speak",
        "listen",
        "write",
        "do",
        "explore",
        "assessment",
    ),
}
OFFLINE_MODALITY_WORDS = {
    "recite",
    "listen",
    "speak",
    "draw",
    "do",
    "explore",
    "assessment",
    "matchsticks",
}
CHAPTER_LEXICON = {
    "eng_c4_ch01": ("team", "together", "cooperate", "preposition"),
    "eng_c4_ch02": ("bell", "honest", "change", "dialogue"),
    "eng_c4_ch03": ("road", "crossing", "safety", "pedestrian"),
    "eng_c4_ch04": ("focus", "routine", "work", "play"),
    "eng_c4_ch05": ("stag", "grass", "share", "adverb"),
    "eng_c4_ch06": ("braille", "raised", "access", "inclusive"),
}
PARAPHRASE_PROBES = {
    "eng_c4_ch01": (
        "The synchronized rowing shows the crew working as a team. Their "
        "cooperation keeps the boat straight, and it helps them reach one "
        "common aim."
    ),
    "eng_c4_ch02": (
        "The shopper locates the lost wallet and follows the address clue; "
        "after that, the market office rings its owner."
    ),
    "eng_c4_ch03": (
        "A walker stops beside the driveway and watches for cars coming from "
        "the street as well as vehicles backing out through the gate."
    ),
    "eng_c4_ch04": (
        "Steady focus on one brush finishes the border, but jumping between "
        "brushes leaves the painting incomplete."
    ),
    "eng_c4_ch05": (
        "At first the parrots take every mango; after noticing the animals "
        "below have none, they begin giving fruit away before eating."
    ),
    "eng_c4_ch06": (
        "The machine first gains spoken directions, but testers still cannot "
        "find its opening button, so a touch marker is added before another "
        "complete trial."
    ),
}
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def _chapter_path(chapter_id: str) -> Path:
    return CHAPTER_ROOT / f"{chapter_id}.json"


def _manifest_path(chapter_id: str) -> Path:
    return MANIFEST_ROOT / f"{chapter_id}.py"


def _payload(chapter_id: str) -> dict:
    return json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))


def _teaching_activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]


def _all_activities(payload: dict):
    yield from _teaching_activities(payload)
    for level in payload["levels"]:
        yield from level["checks"].values()
    yield from payload["chapter_assessment"]["items"]


def _activity_strings(activity: dict):
    for field in ("teaching_block", "passage", "prompt", "model_answer"):
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


def _normalize(text: str) -> str:
    return " ".join(TOKEN_PATTERN.findall(text.casefold()))


def _ten_word_ngrams(text: str) -> set[tuple[str, ...]]:
    tokens = TOKEN_PATTERN.findall(text.casefold())
    return {
        tuple(tokens[index : index + 10])
        for index in range(max(0, len(tokens) - 9))
    }


def _jaccard(left: str, right: str) -> float:
    left_tokens = set(TOKEN_PATTERN.findall(left.casefold()))
    right_tokens = set(TOKEN_PATTERN.findall(right.casefold()))
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union) if union else 1.0


def _open_validation(activity: dict, answer: str, *, probe_id: str):
    skill_ids = list(
        activity.get("skill_ids") or activity.get("knowledge_components") or ()
    )
    authority = {
        **activity,
        "activity_id": probe_id,
        "skill_ids": skill_ids,
    }
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
                "met": True,
                "quality": 1.0,
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The answer addresses the visible task.",
    }
    return validate_school_open_evaluation(
        evaluation,
        context=school_open_context_from_activity(authority, answer),
    )


def test_class4_bridge_paraphrase_can_use_one_sentence_per_authored_component():
    chapter = _payload("eng_c4_ch01")
    activity = {
        **chapter["levels"][0]["checks"]["independent_check"],
        "activity_id": "eng_c4_ch01:together_poem_message:independent:1",
        "skill_ids": [
            "reading.poetic_language",
            "reading.paragraph_main_idea",
        ],
    }
    assert len(activity["rubric_criteria"]) == 2
    assert len(activity["concept_slots"]) == 2
    answer = (
        "The bridge shows that people can do difficult work together. "
        "The message is that teamwork helps a whole village cross problems."
    )
    first_sentence, second_sentence = answer.split(". ", maxsplit=1)
    first_sentence += "."
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 0.9,
                    "evidence_quote": (
                        first_sentence
                        if "planks" in criterion["description"].casefold()
                        else second_sentence
                    ),
                }
                for index, criterion in enumerate(activity["rubric_criteria"])
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer explains the image and message.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert decision["missing_criteria"] == []
    assert "semantic_evidence_span_reused" not in decision["blockers"]


def test_class4_kitchen_collaboration_paraphrase_passes_strict_evaluation():
    """A fluent answer about shared lunch work must not trigger remediation."""

    chapter = _payload("eng_c4_ch01")
    level = next(
        item
        for item in chapter["levels"]
        if item["level_id"] == "together_words_in_context"
    )
    transfer = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "transfer"
    )
    activity = next(
        item
        for item in transfer["variant_pool"]
        if "team of cooks collaborated on lunch" in item["passage"].casefold()
    )
    answer = (
        "Collaborated means the cooks worked together by doing different jobs "
        "for lunch. Team is a collective noun because it names all the cooks "
        "as one group."
    )
    activity = {
        **activity,
        "activity_id": str(activity["variant_id"]),
        "skill_ids": list(activity["knowledge_components"]),
    }

    assert len(activity["concept_slots"]) == 2
    evaluator_activity = curriculum.evaluator_activity_for_answer(activity, answer)
    assert evaluator_activity is not None
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer explains both ideas.",
        }
    )
    decision = curriculum.decide_open_answer_evaluation(
        evaluator_activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert decision["missing_criteria"] == []
    assert "semantic_required_claim_missing" not in decision["blockers"]


def test_class4_kite_unity_paraphrase_is_not_false_remediation():
    chapter = _payload("eng_c4_ch01")
    level = next(
        item
        for item in chapter["levels"]
        if item["level_id"] == "together_poem_message"
    )
    review = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "review"
    )
    activity = {
        **next(
            item
            for item in review["variant_pool"]
            if item["variant_id"].endswith(":review:1")
        ),
        "activity_id": "eng_c4_ch01:together_poem_message:review:1",
        "skill_ids": level["skill_ids"],
    }
    answer = (
        "The ribbons are separate, but together they keep the kite steady. "
        "It shows that people can join their different strengths to solve a "
        "problem as one team."
    )
    criteria = []
    for criterion in activity["rubric_criteria"]:
        is_unity_message = "united effort" in criterion["description"].casefold()
        criteria.append(
            {
                "id": criterion["id"],
                "met": True,
                "quality": 0.6 if is_unity_message else 1.0,
                "evidence_quote": answer,
            }
        )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.8667,
            "confidence": 0.9,
            "language_detected": "en",
            "criteria": criteria,
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer explains the image and message.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert decision["missing_criteria"] == []


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_manifest_compiles_without_runtime_or_hash_drift(chapter_id: str) -> None:
    manifest_path = _manifest_path(chapter_id)
    chapter_path = _chapter_path(chapter_id)

    assert manifest_path.is_file()
    assert chapter_path.is_file()
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


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_support_copy_is_child_facing_and_keeps_targeted_reteaching(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)

    support_activities = [
        level["checks"][support_name]
        for level in payload["levels"]
        for support_name in SUPPORT_SEQUENCE
    ]

    assert len(support_activities) == 35
    for activity in support_activities:
        teaching_block = activity["teaching_block"]
        assert "Check your answer:" in teaching_block
        assert "Misconception check:" not in teaching_block
        visible_check = teaching_block.casefold().partition("check your answer:")[2]
        assert not visible_check.lstrip().startswith("the learner ")


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

    assert 7 <= len(payload["levels"]) <= 9
    assert 1 <= len(taught_skills) <= 15
    assert taught_skills <= canonical_skills
    assert taught_skills.isdisjoint(TEXT_UNOBSERVABLE_SKILLS)

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

        for phase, role in (
            ("guided_practice", "supported"),
            ("independent_application", "certifying"),
            ("transfer", "certifying"),
            ("review", "certifying"),
        ):
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) == MIN_VARIANTS[phase]
            assert all(activity["evidence_role"] == role for activity in variants)
            signatures = {
                (activity["passage"], activity["prompt"]) for activity in variants
            }
            assert len(signatures) == len(variants)
            for left_index, left in enumerate(variants):
                for right in variants[left_index + 1 :]:
                    assert _jaccard(
                        left["passage"] + " " + left["prompt"],
                        right["passage"] + " " + right["prompt"],
                    ) < 0.78
            if role == "certifying":
                for activity in variants:
                    assert activity["options"] == []
                    assert activity["grading_mode"] == "strict_open_rubric"
                    assert activity["certifying_language"] == "en"
                    assert set(activity["knowledge_components"]).isdisjoint(
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
def test_transfer_and_review_have_four_distinct_grounded_scenarios(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        by_phase = {step["phase"]: step for step in level["teaching_steps"]}
        launch_activities = [
            *by_phase["transfer"]["variant_pool"],
            *by_phase["review"]["variant_pool"],
        ]

        assert len(by_phase["transfer"]["variant_pool"]) == 4
        assert len(by_phase["review"]["variant_pool"]) == 4
        assert len({activity["passage"] for activity in launch_activities}) == 8
        for left_index, left in enumerate(launch_activities):
            for right in launch_activities[left_index + 1 :]:
                assert _jaccard(left["passage"], right["passage"]) < 0.55, (
                    chapter_id,
                    level["level_id"],
                    left.get("activity_id") or left["variant_id"],
                    right.get("activity_id") or right["variant_id"],
                )


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
    assert all(
        start_page <= anchor["page_start"] <= anchor["page_end"] <= end_page
        for anchor in anchors
    )
    assert all(
        set(level["source_anchor_ids"]) <= anchor_ids for level in payload["levels"]
    )

    companion_ids = set()
    required_ids = set()
    for anchor in anchors:
        label = anchor["section_label"].casefold()
        if any(word in label for word in OFFLINE_MODALITY_WORDS):
            companion_ids.add(anchor["anchor_id"])
            assert anchor["coverage_treatment"] in COMPANION_TREATMENTS
            assert anchor["required_for_chapter_certification"] is False
        elif anchor["required_for_chapter_certification"]:
            required_ids.add(anchor["anchor_id"])
    assert companion_ids
    assert required_ids

    for activity in _teaching_activities(payload):
        if activity["evidence_role"] == "certifying":
            assert set(activity["source_anchor_ids"]).isdisjoint(companion_ids)


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
    assessment_passages = {
        item["passage"] for item in payload["chapter_assessment"]["items"]
    }

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
            remediation = cluster.remediation.casefold()
            assert all(marker in remediation for marker in ("first", "then", "finally"))
            level_remediation.update(cluster.skill_ids)
            referenced_support.update(cluster.support_check_ids)
        assert level_remediation == set(level.skill_ids)
        assert referenced_support == support_ids
        remediated_skills.update(level_remediation)
        core_passages = {
            activity["passage"]
            for step in runtime_level["teaching_steps"]
            for activity in (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
        }
        support = [runtime_level["checks"][name] for name in SUPPORT_SEQUENCE]
        assert len(
            {
                (check["teaching_block"], check["passage"], check["prompt"])
                for check in support
            }
        ) == 5
        for check_name in SUPPORT_SEQUENCE:
            check = runtime_level["checks"][check_name]
            assert check["target_misconception_tags"]
            assert set(check["knowledge_components"]) <= set(level.skill_ids)
            teaching = check["teaching_block"].casefold()
            assert "worked reasoning:" in teaching
            assert "check your answer:" in teaching
            visible_check = teaching.partition("check your answer:")[2].partition(
                "next step:"
            )[0]
            assert len(TOKEN_PATTERN.findall(visible_check)) >= 12
            assert "misconception check:" not in teaching
            assert not visible_check.lstrip().startswith("the learner ")
            assert "next step:" in teaching
            assert check["passage"] not in core_passages
            assert check["passage"] not in assessment_passages
            assert all(
                _jaccard(check["passage"], passage) < 0.72
                for passage in core_passages
            )
            assert len(TOKEN_PATTERN.findall(check["model_answer"].casefold())) >= check[
                "min_response_words"
            ]
            assert "build the response in two linked sentences" not in check[
                "prompt"
            ].casefold()

    assessed_skills = {
        skill_id
        for item in payload["chapter_assessment"]["items"]
        for skill_id in item["skill_ids"]
    }
    assert assessed_skills == taught_skills == remediated_skills


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_has_two_disjoint_complete_fifteen_item_forms(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    manifest = load_manifest(_manifest_path(chapter_id))
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }
    teaching_passages = {
        activity["passage"] for activity in _teaching_activities(payload)
    }
    support_passages = {
        level["checks"][name]["passage"]
        for level in payload["levels"]
        for name in SUPPORT_CHECKS
    }
    protected_passages = teaching_passages | support_passages

    assert assessment["items_per_attempt"] == 15
    assert assessment["max_attempts"] == 2
    assert len(items) == 30
    assert len({item["item_id"] for item in items}) == 30
    assert len({item["passage"] for item in items}) == 30
    assert all(item["passage"] not in protected_passages for item in items)
    assert all(
        _jaccard(item["passage"], protected) < 0.72
        for item in items
        for protected in protected_passages
    )
    assert all(
        sum(skill_id in item["skill_ids"] for item in items) >= 2
        for skill_id in taught_skills
    )

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
    assert all(
        _jaccard(left["passage"], right["passage"]) < 0.72
        for left in first
        for right in second
    )
    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills
        assert sum(bool(item["options"]) for item in form) >= 4
        assert sum(not item["options"] for item in form) >= 4
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

    strand_skills = {
        skill_id
        for strand in manifest.chapter_assessment.strands
        for skill_id in strand.skill_ids
    }
    assert strand_skills == taught_skills


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_open_rubrics_are_strict_and_visible_prompts_do_not_leak_keys(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    required_asset_phrases = {
        "look at the image",
        "look at the picture",
        "listen to the audio",
        "listen to the recording",
        "watch the video",
        "read the textbook",
        "on the previous page",
    }
    choice_positions = []

    for activity in _all_activities(payload):
        visible = _normalize(
            " ".join(
                (
                    activity.get("teaching_block", ""),
                    activity.get("passage", ""),
                    activity.get("prompt", ""),
                )
            )
        )
        assert not any(phrase in visible for phrase in required_asset_phrases)
        if activity.get("options"):
            accepted = activity["accepted_answers"]
            assert len(accepted) == 1
            assert _normalize(accepted[0]) not in _normalize(activity["prompt"])
            choice_positions.append(activity["options"].index(accepted[0]))
            continue

        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        assert activity["accepted_answers"] == []
        assert activity["options"] == []
        assert activity["pass_score"] >= 0.8
        assert activity["min_response_words"] >= 8
        assert len(activity["relevance_terms"]) >= 2
        assert activity["model_answer"]
        assert len(TOKEN_PATTERN.findall(activity["model_answer"].casefold())) >= activity[
            "min_response_words"
        ]
        normalized_model = _normalize(activity["model_answer"])
        if normalized_model in visible:
            normalized_prompt = _normalize(activity["prompt"])
            assert normalized_model == _normalize(activity["passage"])
            assert any(
                marker in normalized_prompt
                for marker in ("capital", "comma", "punctuat")
            )
        criteria = activity["rubric_criteria"]
        slots = activity["concept_slots"]
        assert [criterion["id"] for criterion in criteria] == [
            slot["id"] for slot in slots
        ]
        assert all(criterion["required"] for criterion in criteria)
        assert all(criterion["min_quality"] >= 0.7 for criterion in criteria)
        alias_sets = []
        for slot in slots:
            aliases = {_normalize(alias) for alias in slot["any_of"]}
            assert len(aliases) >= 2
            assert _normalize(activity["model_answer"]) not in aliases
            alias_sets.append(aliases)
        for left_index, left in enumerate(alias_sets):
            for right in alias_sets[left_index + 1 :]:
                assert left.isdisjoint(right)

    assert len(set(choice_positions)) >= 3
    assert Counter(choice_positions).most_common(1)[0][1] / len(choice_positions) < 0.6


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_strict_open_authority_closes_and_rejects_irrelevant_prose(
    chapter_id: str,
) -> None:
    irrelevant = (
        "Education matters, kindness is valuable, and every student should "
        "work hard because good habits help throughout the school year."
    )
    assessment_items = _payload(chapter_id)["chapter_assessment"]["items"]
    open_activities = [
        next(
            item
            for item in assessment_items
            if f":assessment-{form}-" in item["item_id"]
            and item.get("grading_mode") == "strict_open_rubric"
        )
        for form in ("a", "b")
    ]
    for index, activity in enumerate(open_activities, start=1):
        model_result = _open_validation(
            activity,
            activity["model_answer"],
            probe_id=f"{chapter_id}:model-closure:{index}",
        )
        assert model_result.effective_blockers == (), (
            activity.get("item_id") or activity.get("activity_id"),
            model_result.effective_blockers,
        )
        assert model_result.certification_eligible is True

        irrelevant_result = _open_validation(
            activity,
            irrelevant,
            probe_id=f"{chapter_id}:irrelevant-closure:{index}",
        )
        assert irrelevant_result.certification_eligible is False
        assert any(
            blocker == "answer_not_relevant" or blocker.startswith("semantic_")
            for blocker in irrelevant_result.effective_blockers
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_original_paraphrase_probe_passes_real_open_evaluator(chapter_id: str) -> None:
    item = next(
        item
        for item in _payload(chapter_id)["chapter_assessment"]["items"]
        if not item["options"]
    )
    answer = PARAPHRASE_PROBES[chapter_id]

    assert _normalize(answer) != _normalize(item["model_answer"])
    result = _open_validation(
        item,
        answer,
        probe_id=f"{chapter_id}:authored-paraphrase",
    )

    assert result.effective_blockers == ()
    assert result.certification_eligible is True


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_co_required_assessment_details_are_separate_semantic_slots(
    chapter_id: str,
) -> None:
    item = next(
        item
        for item in _payload(chapter_id)["chapter_assessment"]["items"]
        if not item["options"]
    )
    slots = item["concept_slots"]
    assert len(slots) >= 2

    alias_sets = [{_normalize(alias) for alias in slot["any_of"]} for slot in slots]
    for left_index, left in enumerate(alias_sets):
        for right in alias_sets[left_index + 1 :]:
            assert left.isdisjoint(right)

    one_detail = (
        f"{slots[0]['any_of'][0]}. This sentence contains enough extra words "
        "to pass the response length check but no other required detail."
    )
    result = _open_validation(
        item,
        one_detail,
        probe_id=f"{chapter_id}:single-detail-adversary",
    )
    assert result.certification_eligible is False
    assert any(
        blocker.startswith("semantic_") for blocker in result.effective_blockers
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_class_four_wording_and_language_examples_are_well_formed(
    chapter_id: str,
) -> None:
    payload = _payload(chapter_id)
    learner_text = json.dumps(
        {
            "levels": payload["levels"],
            "assessment": payload["chapter_assessment"],
        },
        ensure_ascii=False,
    ).casefold()

    assert "programmatic text label" not in learner_text
    assert "itselfs" not in learner_text
    assert "a frogs' nursery" not in learner_text
    assert "a frogs’ nursery" not in learner_text
    assert "build the response in two linked sentences and justify the link" not in (
        learner_text
    )
    assert "first separate the two required ideas before drafting" not in learner_text
    assert "begin by naming the first required idea from the passage" not in learner_text
    assert "is checking yesterday" not in learner_text

    for activity in _all_activities(payload):
        if not activity.get("options"):
            continue
        for option in activity["options"]:
            assert not re.search(
                r"\b(?:is|are)\s+\w+ing\s+(?:yesterday|last\s+\w+)\b",
                option.casefold(),
            )


def test_chapter_one_collective_nouns_are_taught_and_certified() -> None:
    payload = _payload("eng_c4_ch01")
    level = next(
        level
        for level in payload["levels"]
        if level["level_id"] == "together_words_in_context"
    )
    assert "grammar.noun_verb_adjective" in level["skill_ids"]

    by_phase = {step["phase"]: step for step in level["teaching_steps"]}
    for phase in ("independent_application", "transfer", "review"):
        phase_text = " ".join(
            " ".join(
                str(activity.get(field, "")).casefold()
                for field in ("teaching_block", "passage", "prompt", "model_answer")
            )
            for activity in by_phase[phase]["variant_pool"]
        )
        assert "collective noun" in phase_text
        assert len(
            {"team", "class", "flock", "herd", "swarm", "bunch"}
            & set(TOKEN_PATTERN.findall(phase_text))
        ) >= 2

    assessment_items = [
        item
        for item in payload["chapter_assessment"]["items"]
        if "grammar.noun_verb_adjective" in item["skill_ids"]
    ]
    assert len(assessment_items) >= 2
    assert all(
        "collective noun"
        in " ".join(
            str(item.get(field, "")).casefold()
            for field in ("passage", "prompt", "model_answer")
        )
        for item in assessment_items
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_facing_content_has_no_ten_word_extract_overlap(
    chapter_id: str,
) -> None:
    extract_path = EXTRACT_ROOT / f"{chapter_id}.txt"
    if not extract_path.is_file():
        pytest.skip("official Class 4 structural extract is not available")

    source_ngrams = _ten_word_ngrams(extract_path.read_text(encoding="utf-8"))
    overlaps: set[tuple[str, ...]] = set()
    for activity in _all_activities(_payload(chapter_id)):
        for learner_string in _activity_strings(activity):
            overlaps.update(_ten_word_ngrams(learner_string) & source_ngrams)

    assert not overlaps, "copied 10-word sequence: " + " ".join(sorted(overlaps)[0])


def test_chapters_are_specific_not_interchangeable_templates() -> None:
    chapter_texts = {}
    teaching_signatures = []
    prompts = []
    for chapter_id in CHAPTER_IDS:
        payload = _payload(chapter_id)
        activities = list(_teaching_activities(payload))
        assessment = payload["chapter_assessment"]["items"]
        chapter_texts[chapter_id] = json.dumps(
            {"activities": activities, "assessment": assessment},
            ensure_ascii=False,
        ).casefold()
        teaching_signatures.extend(
            (activity["passage"], activity["prompt"]) for activity in activities
        )
        prompts.extend(activity["prompt"] for activity in activities)

    for chapter_id, required_words in CHAPTER_LEXICON.items():
        assert all(word in chapter_texts[chapter_id] for word in required_words)
    assert len(teaching_signatures) == len(set(teaching_signatures))
    assert len(prompts) == len(set(prompts))
