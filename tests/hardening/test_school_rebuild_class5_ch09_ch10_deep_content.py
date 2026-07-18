from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services import school_rebuild_curriculum as curriculum
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services import school_rebuild_masterclass as masterclass
from app.services.school_rebuild_curriculum import _select_chapter_assessment_items
from scripts.build_school_deep_chapter import build_deep_chapter, load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPTER_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_5"
)
CHAPTER_IDS = ("eng_c5_ch09", "eng_c5_ch10")
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
GENERIC_SEED_FRAGMENTS = {
    "in santoor chapter 9",
    "in santoor chapter 10",
    "use the sample sentence to practise",
    "bridge support for",
    "chapter check 1 for class 5",
}
PHASE_DEPTH = {
    "guided_practice": 4,
    "independent_application": 4,
    "transfer": 4,
    "review": 4,
}
GROUNDING_MARKERS = (
    "evidence",
    "passage",
    "note",
    "packet",
    "text",
    "sentence",
    "facts",
    "details",
)
GENERATED_STAGE_LABEL = re.compile(
    r"\b(?:opening|worked example|"
    r"(?:first|second|third|fourth) (?:guided example|solo practice|new situation|recap task)|"
    r"bridge hint|focused practice|(?:first|second|third) repair) note\b",
    re.IGNORECASE,
)
RUBRIC_FACING_INSTRUCTIONS = (
    "test each required claim",
    "check each rubric claim",
)
MALFORMED_LEARNER_FRAGMENTS = (
    "use the evidence in the who controls the verb?",
)
REPEATED_GENERATOR_BOILERPLATE = (
    "make the evidence visible without relying on options",
)
CORE_TOKEN_STOPWORDS = {
    "about",
    "after",
    "before",
    "both",
    "card",
    "details",
    "every",
    "from",
    "into",
    "later",
    "note",
    "only",
    "passage",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "through",
    "using",
    "when",
    "where",
    "which",
    "while",
    "with",
}
SUBSTANTIVE_PASSAGE_MARKERS = (
    "a learner kept",
    "in an original reflective verse",
    "a class studied",
    "context clue card:",
    "editing board:",
    "language repair card:",
    "fact card:",
    "planning notes:",
    "bounded fact card:",
    "production process notes:",
    "design record:",
    "community impact note:",
    "semantic association card:",
    "unedited line:",
    "two past events:",
    "procedure fact packet:",
    "recount planner:",
    "bounded inquiry packet:",
)
RECYCLED_SUPPORT_IDS = {
    "eng_c5_ch09_perceived_freedom-bridge",
    "eng_c5_ch09_work_realities-bridge",
    "eng_c5_ch09_vocation_paragraph-bridge",
    "eng_c5_ch09_vocation_paragraph-masterclass",
    "eng_c5_ch10_tradition_innovation-bridge",
    "eng_c5_ch10_community_effects-bridge",
    "eng_c5_ch10_procedure_writer-bridge",
    "eng_c5_ch10_festival_recount-bridge",
    "eng_c5_ch10_craft_and_savings-bridge",
}


def _payload(chapter_id: str) -> dict:
    return json.loads(
        (CHAPTER_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )


def _manifest_payload(chapter_id: str) -> dict:
    return json.loads(
        (MANIFEST_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )


def _manifest_activities(payload: dict):
    for level in payload["levels"]:
        yield level["connect"]
        yield level["co_construct"]
        for pool_name in (
            "guided_variants",
            "independent_variants",
            "transfer_variants",
            "review_variants",
        ):
            yield from level[pool_name]
        yield from level["support_checks"].values()
    yield from payload["chapter_assessment"]["items"]


def _activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]


def _remember_activity(state: dict, activity: dict) -> None:
    memory = curriculum._normalize_hot_session_memory(
        state.get("hot_session_memory")
    )
    for memory_key, activity_key in (
        ("passage_fingerprints", "passage"),
        ("prompt_fingerprints", "prompt"),
    ):
        fingerprint = curriculum._content_fingerprint(activity.get(activity_key))
        if fingerprint:
            memory[memory_key] = list(
                dict.fromkeys([*memory[memory_key], fingerprint])
            )[-40:]
    state["hot_session_memory"] = memory


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _substantive_passage(activity: dict) -> str:
    passage = _normalized(activity.get("passage", ""))
    marker_positions = [
        position
        for marker in SUBSTANTIVE_PASSAGE_MARKERS
        if (position := passage.find(marker)) >= 0
    ]
    if marker_positions:
        passage = passage[min(marker_positions) :]
    return passage


def _core_token_overlap(left: str, right: str) -> float:
    def core_tokens(value: str) -> Counter[str]:
        return Counter(
            token
            for token in re.findall(r"[a-z0-9]+", _normalized(value))
            if len(token) >= 4 and token not in CORE_TOKEN_STOPWORDS
        )

    left_tokens = core_tokens(left)
    right_tokens = core_tokens(right)
    smaller_count = min(sum(left_tokens.values()), sum(right_tokens.values()))
    if smaller_count == 0:
        return 0.0
    return sum((left_tokens & right_tokens).values()) / smaller_count


def _answer_signature(activity: dict) -> tuple[str, ...]:
    answers = activity.get("accepted_answers") or activity.get("model_answers") or []
    if not answers and activity.get("model_answer"):
        answers = [activity["model_answer"]]
    return tuple(sorted(_normalized(answer) for answer in answers))


def _positive_open_payload(activity: dict, answer: str) -> dict:
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity.get("activity_id") or activity["item_id"],
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
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The answer addresses the task.",
    }


def _alias_matches(value: str, alias: str) -> bool:
    normalized_value = _normalized(value)
    normalized_alias = _normalized(alias)
    prefix = r"(?<!\w)" if normalized_alias[0].isalnum() else ""
    suffix = r"(?!\w)" if normalized_alias[-1].isalnum() else ""
    return re.search(
        f"{prefix}{re.escape(normalized_alias)}{suffix}",
        normalized_value,
    ) is not None


def _grounding_signature(activity: dict) -> tuple:
    return tuple(
        (
            slot["id"],
            tuple(sorted(_normalized(alias) for alias in slot["any_of"])),
        )
        for slot in activity["concept_slots"]
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_chapter_is_manifest_authored_and_agent_reviewed(chapter_id):
    manifest_path = MANIFEST_ROOT / f"{chapter_id}.json"
    assert manifest_path.is_file()

    manifest = load_manifest(manifest_path)
    chapter_path = CHAPTER_ROOT / f"{chapter_id}.json"
    chapter = load_live_chapter_file(chapter_path)

    assert manifest.chapter.chapter_id == chapter_id
    assert manifest.chapter.unit_title == "Work is Worship"
    assert chapter.unit_title == "Work is Worship"
    assert manifest.chapter.authorship.zidd_authored_original is True
    assert manifest.chapter.authorship.textbook_body_or_questions_copied is False
    assert chapter.approval_status == "agent_reviewed"
    assert chapter.reviewed_by
    assert chapter.reviewed_at
    assert any("manifest" in item.lower() for item in chapter.review_evidence)
    assert any("official" in item.lower() for item in chapter.review_evidence)
    assert not chapter_quality_issues(chapter)
    assert 8 <= len(chapter.levels) <= 9
    assert len(chapter.levels) == len(manifest.levels)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_chapter_has_deep_distinct_loop_and_honest_modality(chapter_id):
    payload = _payload(chapter_id)
    signatures = []
    choice_positions = []
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }

    assert not taught_skills.intersection(UNOBSERVABLE_TEXT_ONLY_SKILLS)
    companion_anchors = [
        anchor
        for anchor in payload["source_anchors"]
        if anchor["coverage_treatment"] in COMPANION_TREATMENTS
    ]
    assert companion_anchors
    assert all(
        not anchor["required_for_chapter_certification"]
        for anchor in companion_anchors
    )
    section_labels = " ".join(
        anchor["section_label"].lower() for anchor in companion_anchors
    )
    assert "listen" in section_labels
    assert "speak" in section_labels
    assert any(
        word in section_labels for word in ("visual", "picture", "do", "craft")
    )

    for level in payload["levels"]:
        assert set(level["checks"]) == SUPPORT_CHECKS | {
            "guided_check",
            "independent_check",
            "transfer_check",
        }
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == COMPACT_PHASES
        by_phase = {step["phase"]: step for step in steps}
        for phase, minimum in PHASE_DEPTH.items():
            assert len(by_phase[phase]["variant_pool"]) >= minimum

        for phase in ("independent_application", "transfer", "review"):
            for activity in by_phase[phase]["variant_pool"]:
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["certifying_language"] == "en"

        for check_name in SUPPORT_CHECKS:
            support = level["checks"][check_name]
            assert support.get("target_misconception_tags")
            if support["options"]:
                assert support["prompt"].startswith("Which")

        for activity in _activities({"levels": [level]}):
            normalized = " ".join(activity["prompt"].lower().split())
            assert not any(fragment in normalized for fragment in GENERIC_SEED_FRAGMENTS)
            signatures.append(
                (
                    activity["teaching_block"],
                    activity["passage"],
                    activity["prompt"],
                )
            )
            if activity["options"]:
                assert activity["prompt"].startswith("Which")
                productive = {
                    skill_id
                    for skill_id in activity["knowledge_components"]
                    if skill_id.startswith(("writing.", "speaking.", "oral."))
                }
                assert not productive
                choice_positions.append(
                    activity["options"].index(activity["accepted_answers"][0])
                )

    assert len(signatures) == len(set(signatures))
    assert len(set(choice_positions)) >= 3
    assert Counter(choice_positions)[0] / len(choice_positions) < 0.6


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_manifest_transfer_and_review_variants_are_launch_grade(chapter_id):
    manifest = json.loads(
        (MANIFEST_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )
    issues = []

    for level in manifest["levels"]:
        expected_skills = set(level["skill_ids"])
        prior_signatures = {
            _grounding_signature(activity)
            for activity in level["independent_variants"]
        }

        for pool_name in ("transfer_variants", "review_variants"):
            variants = level[pool_name]
            phase = pool_name.removesuffix("_variants")
            signatures = [_grounding_signature(activity) for activity in variants]
            covered_skills = {
                skill_id
                for activity in variants
                for skill_id in activity["skill_ids"]
            }

            if len(variants) < 4:
                issues.append(
                    f"{level['level_id']}:{phase}:count={len(variants)}"
                )
            if len(signatures) != len(set(signatures)):
                issues.append(f"{level['level_id']}:{phase}:duplicate_scenario")
            if set(signatures).intersection(prior_signatures):
                issues.append(f"{level['level_id']}:{phase}:reused_earlier_scenario")
            if covered_skills != expected_skills:
                issues.append(
                    f"{level['level_id']}:{phase}:skill_coverage="
                    f"{sorted(covered_skills)}"
                )

            for activity in variants:
                criteria = activity["rubric_criteria"]
                slots = activity["concept_slots"]
                if (
                    activity["kind"] != "open_response"
                    or len(criteria) < 2
                    or not all(
                        criterion["required"]
                        and criterion["min_quality"] >= 0.7
                        for criterion in criteria
                    )
                    or [criterion["id"] for criterion in criteria]
                    != [slot["id"] for slot in slots]
                    or [criterion["description"] for criterion in criteria]
                    != [slot["description"] for slot in slots]
                ):
                    issues.append(f"{activity['activity_id']}:weak_rubric")
                if not any(
                    marker in _normalized(activity["prompt"])
                    for marker in GROUNDING_MARKERS
                ):
                    issues.append(f"{activity['activity_id']}:ungrounded_prompt")

            prior_signatures.update(signatures)

    assert not issues, "\n".join(issues)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_manifest_compiles_without_runtime_or_hash_drift(chapter_id):
    manifest = load_manifest(MANIFEST_ROOT / f"{chapter_id}.json")
    built = LiveSchoolChapter.model_validate(build_deep_chapter(None, manifest))
    reviewed = load_live_chapter_file(CHAPTER_ROOT / f"{chapter_id}.json")

    assert built.runtime_dict() == reviewed.runtime_dict()
    assert built.runtime_sha256 == reviewed.runtime_sha256
    assert reviewed.calculated_runtime_sha256() == reviewed.runtime_sha256


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_every_open_model_answer_satisfies_distinct_semantic_claims(chapter_id):
    payload = _payload(chapter_id)
    activities = [*_activities(payload)]
    activities.extend(
        check
        for level in payload["levels"]
        for check in level["checks"].values()
    )
    activities.extend(payload["chapter_assessment"]["items"])

    for activity in activities:
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        aliases_by_slot = {
            slot["id"]: {_normalized(alias) for alias in slot["any_of"]}
            for slot in activity["concept_slots"]
        }
        flattened = [
            (slot_id, alias)
            for slot_id, aliases in aliases_by_slot.items()
            for alias in aliases
        ]
        assert len({alias for _slot_id, alias in flattened}) == len(flattened)
        assert all(
            any(
                _alias_matches(activity["model_answer"], alias)
                for alias in slot["any_of"]
            )
            for slot in activity["concept_slots"]
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_linked_masterclass_has_deep_fresh_pools_for_every_level(chapter_id):
    payload = _payload(chapter_id)
    for raw_level in payload["levels"]:
        pools = masterclass._deep_phase_activity_pools(
            raw_level,
            curriculum_state={"hot_session_memory": {}},
            trigger_skill_ids=list(raw_level["skill_ids"]),
        )
        assert len(pools["supported_practice"]) >= 3
        assert len(pools["misconception_rebuild"]) >= 3
        assert len(pools["independent_check"]) >= 3
        assert len(pools["transfer_check"]) >= 2


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_sequential_strong_path_stays_fresh_for_every_level(chapter_id):
    payload = _payload(chapter_id)
    state = {"hot_session_memory": {}}

    for raw_level in payload["levels"]:
        level = {**raw_level, "used_variant_ids": []}
        selected_phases = []
        for step in level["teaching_steps"]:
            activity, variant_id, fresh = curriculum._v2_step_activity(
                state,
                level,
                step,
            )
            assert activity is not None and variant_id and fresh
            level["used_variant_ids"] = [
                *level["used_variant_ids"],
                variant_id,
            ]
            _remember_activity(state, activity)
            selected_phases.append(step["phase"])

        assert tuple(selected_phases) == COMPACT_PHASES


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_chapter_assessment_is_mixed_fresh_and_fully_remediable(chapter_id):
    payload = _payload(chapter_id)
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }
    assessed_skills = {
        skill_id for item in items for skill_id in item["skill_ids"]
    }
    teaching_passages = {
        " ".join(activity["passage"].lower().split())
        for activity in _activities(payload)
    }

    assert assessment["items_per_attempt"] == 16
    assert assessment["max_attempts"] == 2
    assert len(items) == 32
    assert assessed_skills == taught_skills
    assert sum(bool(item["options"]) for item in items) >= 12
    assert sum(not item["options"] for item in items) >= 12
    assert len({item["item_id"] for item in items}) == 32
    assert len(
        {
            (tuple(item["skill_ids"]), item["passage"])
            for item in items
        }
    ) == 32
    assert all(
        " ".join(item["passage"].lower().split()) not in teaching_passages
        for item in items
    )
    assert all(
        item["grading_mode"] == "selected_option"
        if item["options"]
        else item["grading_mode"] == "strict_open_rubric"
        for item in items
    )
    assert all(
        item["prompt"].startswith("Which")
        for item in items
        if item["options"]
    )

    remediated_skills = {
        skill_id
        for level in payload["levels"]
        for activity_name in SUPPORT_CHECKS
        for skill_id in level["checks"][activity_name]["knowledge_components"]
    }
    assert assessed_skills <= remediated_skills


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_both_chapter_assessment_forms_are_fresh_and_cover_every_skill(chapter_id):
    items = _payload(chapter_id)["chapter_assessment"]["items"]
    taught_skills = {
        skill_id for item in items for skill_id in item["skill_ids"]
    }
    first = _select_chapter_assessment_items(
        items,
        item_count=16,
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=16,
        attempt_no=2,
        used_item_ids=first_ids,
    )

    assert len(first) == len(second) == 16
    assert first_ids.isdisjoint(item["item_id"] for item in second)
    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills


def test_vocation_and_glass_bangles_preserve_chapter_specific_truth():
    vocation = _payload("eng_c5_ch09")
    bangles = _payload("eng_c5_ch10")

    vocation_text = json.dumps(vocation, ensure_ascii=False).lower()
    bangles_text = json.dumps(bangles, ensure_ascii=False).lower()

    for concept in (
        "time sequence",
        "perceived freedom",
        "dignity of work",
        "wh question",
        "topic sentence",
    ):
        assert concept in vocation_text
    for concept in (
        "production process",
        "tradition and innovation",
        "community effect",
        "had + past participle",
        "festival",
        "saving",
    ):
        assert concept in bangles_text
    assert "has/have + past participle" not in bangles_text
    assert "aarav" not in bangles_text
    assert "arjun" not in bangles_text


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_guided_and_independent_pools_use_four_substantively_distinct_facts(
    chapter_id,
):
    payload = _manifest_payload(chapter_id)

    for level in payload["levels"]:
        for pool_name in ("guided_variants", "independent_variants"):
            pool = level[pool_name]
            signatures = [_substantive_passage(activity) for activity in pool]
            assert len(pool) == 4
            assert len(set(signatures)) == 4, (
                level["level_id"],
                pool_name,
                signatures,
            )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_second_transfer_uses_fresh_passage_evidence_and_representation(chapter_id):
    payload = _manifest_payload(chapter_id)
    violations = []

    for level in payload["levels"]:
        transfer_twos = [
            activity
            for activity in level["transfer_variants"]
            if activity["activity_id"].endswith("-transfer-2")
        ]
        assert len(transfer_twos) == 1, level["level_id"]
        transfer = transfer_twos[0]
        transfer_passage = _normalized(transfer["passage"])
        transfer_core = _substantive_passage(transfer)

        for guided in level["guided_variants"]:
            guided_passage = _normalized(guided["passage"])
            guided_core = _substantive_passage(guided)
            overlap = _core_token_overlap(transfer_core, guided_core)
            if (
                guided_passage in transfer_passage
                or transfer_passage in guided_passage
                or overlap >= 0.8
            ):
                violations.append(
                    (
                        transfer["activity_id"],
                        guided["activity_id"],
                        round(overlap, 3),
                    )
                )

    assert not violations, violations


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_copy_has_no_generated_stage_labels_or_rubric_instructions(
    chapter_id,
):
    for activity in _manifest_activities(_manifest_payload(chapter_id)):
        for field_name in ("teaching_block", "passage", "prompt"):
            learner_copy = activity.get(field_name, "")
            assert GENERATED_STAGE_LABEL.search(learner_copy) is None, (
                activity.get("activity_id") or activity.get("item_id"),
                field_name,
                learner_copy,
            )
            normalized_copy = _normalized(learner_copy)
            assert not any(
                instruction in normalized_copy
                for instruction in RUBRIC_FACING_INSTRUCTIONS
            ), (
                activity.get("activity_id") or activity.get("item_id"),
                field_name,
                learner_copy,
            )
            assert not any(
                fragment in normalized_copy
                for fragment in MALFORMED_LEARNER_FRAGMENTS
            ), (
                activity.get("activity_id") or activity.get("item_id"),
                field_name,
                learner_copy,
            )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_copy_has_no_repeated_generator_boilerplate(chapter_id):
    activity_groups = (
        _manifest_activities(_manifest_payload(chapter_id)),
        _activities(_payload(chapter_id)),
    )

    for activities in activity_groups:
        for activity in activities:
            for field_name in ("teaching_block", "passage", "prompt"):
                learner_copy = _normalized(activity.get(field_name, ""))
                assert not any(
                    phrase in learner_copy
                    for phrase in REPEATED_GENERATOR_BOILERPLATE
                ), (
                    activity.get("activity_id") or activity.get("item_id"),
                    field_name,
                    learner_copy,
                )


def test_strict_open_language_repairs_never_grade_hidden_sentence_content():
    payload = _manifest_payload("eng_c5_ch09")

    for activity in _manifest_activities(payload):
        if activity.get("kind") != "open_response":
            continue
        passage = activity.get("passage", "")
        if "Language repair card:" not in passage:
            continue
        visible_stimulus = passage.split("Language repair card:", 1)[1].strip()
        has_completion_scaffold = (
            "___" in visible_stimulus
            and "use the verb" in visible_stimulus.casefold()
        )
        has_complete_sentence = (
            visible_stimulus.endswith((".", "?", "!"))
            and len(re.findall(r"[A-Za-z]+", visible_stimulus)) >= 4
        )
        assert has_completion_scaffold or has_complete_sentence, (
            activity.get("activity_id") or activity.get("item_id"),
            visible_stimulus,
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_bridge_and_masterclass_use_fresh_substantive_tasks(chapter_id):
    payload = _manifest_payload(chapter_id)

    for level in payload["levels"]:
        teaching = [
            level["co_construct"],
            *level["guided_variants"],
            *level["independent_variants"],
            *level["transfer_variants"],
            *level["review_variants"],
        ]
        teaching_passages = {_substantive_passage(activity) for activity in teaching}
        teaching_answers = {
            signature
            for activity in teaching
            if (signature := _answer_signature(activity))
        }

        for support_name in ("bridge", "masterclass"):
            support = level["support_checks"][support_name]
            teaching_block = _normalized(support["teaching_block"])
            if support_name == "bridge":
                assert "clearest clue" in teaching_block
                assert "one short answer" in teaching_block
            else:
                assert "tempting answer" in teaching_block
                assert "mistake" in teaching_block

            if support["activity_id"] not in RECYCLED_SUPPORT_IDS:
                continue
            assert _substantive_passage(support) not in teaching_passages, (
                level["level_id"],
                support_name,
                "reused passage",
            )
            answer_signature = _answer_signature(support)
            assert not answer_signature or answer_signature not in teaching_answers, (
                level["level_id"],
                support_name,
                "reused answer",
            )


@pytest.mark.parametrize(
    ("chapter_id", "activity_id", "answer"),
    (
        (
            "eng_c5_ch09",
            "eng_c5_ch09_work_realities-independent-1",
            "The central contribution shows dignity of work and effort. "
            "This is a fair and important job for the whole community.",
        ),
        (
            "eng_c5_ch10",
            "eng_c5_ch10_tradition_innovation-independent-1",
            "The makers retained one feature and changed another feature. "
            "This is an example of tradition and innovation in a design.",
        ),
    ),
)
def test_generic_labels_cannot_certify_missing_passage_evidence(
    chapter_id,
    activity_id,
    answer,
):
    activity = next(
        item
        for item in _manifest_activities(_manifest_payload(chapter_id))
        if item.get("activity_id") == activity_id
    )

    validated = validate_school_open_evaluation(
        _positive_open_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )

    assert validated.certification_eligible is False
    assert {
        "answer_not_relevant",
        "semantic_evidence_span_reused",
        "semantic_required_claim_missing",
    }.intersection(validated.effective_blockers)
