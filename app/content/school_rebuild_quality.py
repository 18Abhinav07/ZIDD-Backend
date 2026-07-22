"""Focused pedagogy quality checks for approved School chapter content."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any

from app.content.school.content_schema import SchoolRubricEvaluation
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)


_STAGE_NAMES = (
    "guided_check",
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
    "independent_check",
    "transfer_check",
)
_SUPPORT_STAGE_NAMES = (
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
)
_MIN_VARIANTS_BY_PHASE = {
    "guided_practice": 4,
    "independent_application": 4,
    "transfer": 4,
    "review": 4,
}
_PARALLEL_DRILL_MODES = {"exact_text", "punctuation_symbol"}
_WORD_ORDER_DIRECTIONS = (
    "put the words in order",
    "arrange the words",
    "reorder the words",
    "unscramble",
)
_BANNED_PROMPT_FRAMES = (
    "find the clear clue in this scene",
    "use the support steps",
    "check the whole scene before you decide",
    "answer this scene without choices",
    "carry the idea into this fresh situation",
)
_INTERNAL_LEARNER_COPY_MARKERS = (
    "independent check:",
    "independent checkpoint",
    "transfer check:",
    "transfer checkpoint",
    "independent case",
    "misconception check:",
    "required concept",
    "reading purpose",
    "does not certify",
    "before certifying",
    "certification check",
    "certifiable text task",
    "browser evidence",
    "typed evidence can",
    "can and cannot certify",
    "offline completion",
    "performance claims",
    "learner boundary",
    "bounded fact report",
    "supplied clue controls the response",
)


def _normalized_text(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _normalized_answer(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", _normalized_text(value)).strip()


def _word_count(value: str) -> int:
    return len(re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", _normalized_text(value)))


def _alias_matches(value: str, alias: str) -> bool:
    normalized_value = _normalized_text(value)
    normalized_alias = _normalized_text(alias)
    if not normalized_alias:
        return False
    prefix = r"(?<!\w)" if normalized_alias[0].isalnum() else ""
    suffix = r"(?!\w)" if normalized_alias[-1].isalnum() else ""
    return re.search(
        f"{prefix}{re.escape(normalized_alias)}{suffix}",
        normalized_value,
    ) is not None


def _near_duplicate_text(left: str, right: str, *, threshold: float = 0.92) -> bool:
    normalized_left = _normalized_text(left)
    normalized_right = _normalized_text(right)
    if min(len(normalized_left), len(normalized_right)) < 32:
        return False
    return (
        SequenceMatcher(None, normalized_left, normalized_right).ratio()
        >= threshold
    )


def _assessment_rehearses_teaching_case(assessment, teaching) -> bool:
    assessment_passage = _normalized_text(assessment.passage)
    teaching_passage = _normalized_text(teaching.passage)
    assessment_tokens = set(re.findall(r"[a-z0-9]+", assessment_passage))
    teaching_tokens = set(re.findall(r"[a-z0-9]+", teaching_passage))
    if min(len(assessment_tokens), len(teaching_tokens)) < 7:
        return False
    token_overlap = len(assessment_tokens & teaching_tokens) / len(
        assessment_tokens | teaching_tokens
    )
    return (
        token_overlap >= 0.50
        and SequenceMatcher(
            None,
            assessment_passage,
            teaching_passage,
        ).ratio()
        >= 0.66
    )


def _activities_are_near_duplicates(
    left,
    right,
    *,
    include_prompt: bool = False,
) -> bool:
    left_mode = getattr(left, "grading_mode", None)
    right_mode = getattr(right, "grading_mode", None)
    if left_mode in _PARALLEL_DRILL_MODES and right_mode in _PARALLEL_DRILL_MODES:
        left_answers = {
            _normalized_answer(answer)
            for answer in getattr(left, "accepted_answers", ())
        }
        right_answers = {
            _normalized_answer(answer)
            for answer in getattr(right, "accepted_answers", ())
        }
        if left_answers and right_answers and left_answers.isdisjoint(right_answers):
            return False
    left_text = left.passage
    right_text = right.passage
    if include_prompt:
        left_text = f"{left_text}\n{left.prompt}"
        right_text = f"{right_text}\n{right.prompt}"
    return _near_duplicate_text(left_text, right_text)


def _iter_stage_activities(chapter) -> Iterable[tuple[str, tuple[str, ...], str, object]]:
    for level in chapter.levels:
        for stage_name in _STAGE_NAMES:
            activity = getattr(level.checks, stage_name, None)
            if activity is not None:
                yield level.level_id, tuple(level.skill_ids), stage_name, activity


def _iter_teaching_activities(
    chapter,
) -> Iterable[tuple[str, tuple[str, ...], str, object]]:
    for level in chapter.levels:
        for step in getattr(level, "teaching_steps", None) or ():
            activities = (
                [step.activity]
                if getattr(step, "activity", None) is not None
                else list(getattr(step, "variant_pool", None) or ())
            )
            for index, activity in enumerate(activities, start=1):
                yield (
                    level.level_id,
                    tuple(level.skill_ids),
                    f"teaching_{step.phase}_{index}",
                    activity,
                )


def _strict_open_issues(activity, *, context: str) -> list[str]:
    if getattr(activity, "grading_mode", None) != "strict_open_rubric":
        return []

    issues: list[str] = []
    concept_slots = tuple(getattr(activity, "concept_slots", None) or ())
    if (
        getattr(activity, "evidence_role", "certifying") == "certifying"
        and not concept_slots
    ):
        issues.append(
            f"strict_open_certifying_missing_concept_slots:{context}"
        )
    model_answer = str(getattr(activity, "model_answer", None) or "").strip()
    min_response_words = getattr(activity, "min_response_words", None)
    if model_answer and min_response_words is not None:
        model_words = _word_count(model_answer)
        if model_words < min_response_words:
            issues.append(
                f"strict_open_model_below_word_floor:{context}:"
                f"{model_words}:{min_response_words}"
            )

    alias_slots: dict[str, list[str]] = defaultdict(list)
    for slot in concept_slots:
        for alias in getattr(slot, "any_of", ()):
            normalized_alias = _normalized_text(alias)
            if slot.id not in alias_slots[normalized_alias]:
                alias_slots[normalized_alias].append(slot.id)
        if not any(
            _alias_matches(model_answer, alias)
            for alias in getattr(slot, "any_of", ())
        ):
            issues.append(
                f"strict_open_model_missing_slot:{context}:{slot.id}"
            )
    for alias, slot_ids in alias_slots.items():
        if len(slot_ids) > 1:
            issues.append(
                f"strict_open_alias_shared_across_slots:{context}:"
                f"{alias}:{','.join(sorted(slot_ids))}"
            )
    return issues


def _field_value(value: object, field_name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _strict_open_runtime_issues(
    activity,
    *,
    context: str,
    skill_ids: Iterable[str],
) -> list[str]:
    """Verify that an authored model answer survives the production evaluator."""

    if getattr(activity, "grading_mode", None) != "strict_open_rubric":
        return []

    model_answer = str(getattr(activity, "model_answer", "") or "").strip()
    rubric_criteria = tuple(getattr(activity, "rubric_criteria", None) or ())
    if not model_answer or not rubric_criteria:
        # Schema validation owns malformed strict-open contracts. This quality
        # gate validates fully authored contracts with their actual evaluator.
        return []

    criterion_payloads = [
        {
            "id": str(_field_value(criterion, "id", "")).strip(),
            "required": bool(_field_value(criterion, "required", True)),
            "min_quality": float(_field_value(criterion, "min_quality", 0.6)),
        }
        for criterion in rubric_criteria
    ]
    if any(not criterion["id"] for criterion in criterion_payloads):
        return []

    concept_slot_payloads = [
        {
            "id": str(_field_value(slot, "id", "")).strip(),
            "description": str(_field_value(slot, "description", "")).strip(),
            "any_of": list(_field_value(slot, "any_of", ()) or ()),
        }
        for slot in (getattr(activity, "concept_slots", None) or ())
    ]
    activity_id = (
        getattr(activity, "variant_id", None)
        or getattr(activity, "item_id", None)
        or f"quality:{context}"
    )
    activity_payload = {
        "activity_id": str(activity_id),
        "grading_mode": "strict_open_rubric",
        "passage": str(getattr(activity, "passage", "") or ""),
        "prompt": str(getattr(activity, "prompt", "") or ""),
        "skill_ids": list(skill_ids),
        "rubric_criteria": criterion_payloads,
        "pass_score": float(getattr(activity, "pass_score", 0.8) or 0.8),
        "certifying_language": getattr(activity, "certifying_language", None),
        "concept_slots": concept_slot_payloads,
        "ordered_concept_slot_ids": list(
            getattr(activity, "ordered_concept_slot_ids", None) or ()
        ),
        "actor_action_receiver_slot_ids": list(
            getattr(activity, "actor_action_receiver_slot_ids", None) or ()
        ),
        "forbidden_phrases": list(
            getattr(activity, "forbidden_phrases", None) or ()
        ),
        "relevance_terms": list(getattr(activity, "relevance_terms", None) or ()),
        "semantic_validator_id": getattr(activity, "semantic_validator_id", None),
        "semantic_evidence_policy": getattr(
            activity, "semantic_evidence_policy", None
        ),
    }
    try:
        evaluation = SchoolRubricEvaluation(
            schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
            item_id=activity_payload["activity_id"],
            skill_ids=tuple(activity_payload["skill_ids"]),
            score=1.0,
            confidence=1.0,
            language_detected="en",
            criteria=tuple(
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": model_answer,
                }
                for criterion in criterion_payloads
            ),
            misconception_tags=(),
            blockers=(),
            needs_human_review=False,
            feedback_to_learner="Recorded.",
        )
        validated = validate_school_open_evaluation(
            evaluation,
            context=school_open_context_from_activity(
                activity_payload,
                model_answer,
            ),
        )
    except (TypeError, ValueError) as exc:
        return [
            "strict_open_model_runtime_contract_error:"
            f"{context}:{type(exc).__name__}:{exc}"
        ]
    return [
        f"strict_open_model_runtime_blocker:{context}:{blocker}"
        for blocker in validated.effective_blockers
    ]


def _activity_quality_issues(
    activity,
    *,
    context: str,
    skill_ids: Iterable[str],
) -> list[str]:
    issues: list[str] = []
    for field_name in ("teaching_block", "passage", "prompt"):
        value = _normalized_text(getattr(activity, field_name, "") or "")
        for marker in _INTERNAL_LEARNER_COPY_MARKERS:
            if marker in value:
                issues.append(
                    f"learner_copy_exposes_engine_label:{context}:"
                    f"{field_name}:{marker}"
                )
                break
    prompt = _normalized_text(activity.prompt)
    for frame in _BANNED_PROMPT_FRAMES:
        if frame in prompt:
            issues.append(f"generic_prompt_frame:{context}:{frame}")
            break
    if _is_brittle_constructed_exact_answer(activity, skill_ids):
        issues.append(f"brittle_constructed_exact_answer:{context}")
    issues.extend(_strict_open_issues(activity, context=context))
    issues.extend(
        _strict_open_runtime_issues(
            activity,
            context=context,
            skill_ids=skill_ids,
        )
    )
    return issues


def _is_brittle_constructed_exact_answer(activity, skill_ids: Iterable[str]) -> bool:
    if activity.options or activity.answer_rule or not activity.accepted_answers:
        return False
    if "grammar.sentence_order" in set(skill_ids):
        return False
    prompt = _normalized_text(activity.prompt)
    if any(direction in prompt for direction in _WORD_ORDER_DIRECTIONS):
        return False
    normalized_answers = {
        _normalized_answer(answer) for answer in activity.accepted_answers
    }
    normalized_answers.discard("")
    if len(normalized_answers) != 1:
        return False
    answer = next(iter(normalized_answers))
    return len(answer.split()) >= 5


def chapter_quality_issues(chapter) -> tuple[str, ...]:
    """Return actionable issues missed by structural schema validation."""

    issues: list[str] = []
    stage_passages: set[str] = set()
    for level_id, skill_ids, stage_name, activity in _iter_stage_activities(chapter):
        stage_passages.add(_normalized_text(activity.passage))
        issues.extend(
            _activity_quality_issues(
                activity,
                context=f"{level_id}:{stage_name}",
                skill_ids=skill_ids,
            )
        )

    teaching_passages_by_level: dict[str, set[str]] = defaultdict(set)
    teaching_activities_by_level: dict[str, list[object]] = defaultdict(list)
    all_teaching_activities: list[object] = []
    for level_id, skill_ids, stage_name, activity in _iter_teaching_activities(chapter):
        normalized_passage = _normalized_text(activity.passage)
        stage_passages.add(normalized_passage)
        teaching_passages_by_level[level_id].add(normalized_passage)
        teaching_activities_by_level[level_id].append(activity)
        all_teaching_activities.append(activity)
        issues.extend(
            _activity_quality_issues(
                activity,
                context=f"{level_id}:{stage_name}",
                skill_ids=skill_ids,
            )
        )

    for level in chapter.levels:
        teaching_steps = getattr(level, "teaching_steps", None)
        if teaching_steps is None:
            continue
        phase_counts: dict[str, int] = defaultdict(int)
        authored_cases: list[tuple[str, int, object]] = []
        for step in teaching_steps:
            activities = (
                [step.activity]
                if getattr(step, "activity", None) is not None
                else list(getattr(step, "variant_pool", None) or ())
            )
            phase_counts[step.phase] += len(activities)
            if step.phase in _MIN_VARIANTS_BY_PHASE:
                authored_cases.extend(
                    (step.phase, index, activity)
                    for index, activity in enumerate(activities, start=1)
                )
        for phase, minimum in _MIN_VARIANTS_BY_PHASE.items():
            actual = phase_counts[phase]
            if actual < minimum:
                issues.append(
                    f"insufficient_teaching_variants:{level.level_id}:"
                    f"{phase}:{actual}:{minimum}"
                )

        for left, right in combinations(authored_cases, 2):
            left_phase, left_index, left_activity = left
            right_phase, right_index, right_activity = right
            if _activities_are_near_duplicates(left_activity, right_activity):
                issues.append(
                    f"near_duplicate_teaching_case:{level.level_id}:"
                    f"{left_phase}:{left_index}:{right_phase}:{right_index}"
                )

        teaching_passages = teaching_passages_by_level[level.level_id]
        for stage_name in _SUPPORT_STAGE_NAMES:
            activity = getattr(level.checks, stage_name, None)
            if activity is None:
                continue
            normalized_support_passage = _normalized_text(activity.passage)
            if normalized_support_passage in teaching_passages:
                issues.append(
                    f"support_reuses_teaching_passage:{level.level_id}:{stage_name}"
                )
            elif any(
                _activities_are_near_duplicates(activity, teaching_activity)
                for teaching_activity in teaching_activities_by_level[level.level_id]
            ):
                issues.append(
                    f"support_near_reuses_teaching_passage:"
                    f"{level.level_id}:{stage_name}"
                )

    assessment = getattr(chapter, "chapter_assessment", None)
    if assessment is not None:
        seen_tasks: dict[tuple[str, str], str] = {}
        previous_tasks: list[tuple[str, object]] = []
        for item in assessment.items:
            assessment_passage = _normalized_text(item.passage)
            if assessment_passage in stage_passages:
                issues.append(f"assessment_reuses_teaching_passage:{item.item_id}")
            elif any(
                _assessment_rehearses_teaching_case(item, teaching_activity)
                for teaching_activity in all_teaching_activities
            ):
                issues.append(
                    f"assessment_near_reuses_teaching_passage:{item.item_id}"
                )
            issues.extend(
                _activity_quality_issues(
                    item,
                    context=f"assessment:{item.item_id}",
                    skill_ids=item.skill_ids,
                )
            )
            fingerprint = (
                _normalized_text(item.passage),
                _normalized_text(item.prompt),
            )
            previous_item_id = seen_tasks.get(fingerprint)
            if previous_item_id is not None:
                issues.append(
                    f"duplicate_assessment_task:{previous_item_id}:{item.item_id}"
                )
            else:
                seen_tasks[fingerprint] = item.item_id
                near_duplicate_id = next(
                    (
                        previous_id
                        for previous_id, previous_item in previous_tasks
                        if _activities_are_near_duplicates(
                            item,
                            previous_item,
                            include_prompt=True,
                        )
                    ),
                    None,
                )
                if near_duplicate_id is not None:
                    issues.append(
                        f"near_duplicate_assessment_task:"
                        f"{near_duplicate_id}:{item.item_id}"
                    )
                previous_tasks.append((item.item_id, item))

    return tuple(issues)


def corpus_quality_issues(chapters, *, reuse_threshold: int = 4) -> tuple[str, ...]:
    """Detect exact prompt templates copied across several different chapters."""

    prompt_chapters: dict[str, set[str]] = defaultdict(set)
    display_prompt: dict[str, str] = {}
    for chapter in chapters:
        activities = tuple(_iter_stage_activities(chapter)) + tuple(
            _iter_teaching_activities(chapter)
        )
        for _, _, _, activity in activities:
            normalized = _normalized_text(activity.prompt)
            prompt_chapters[normalized].add(chapter.chapter_id)
            display_prompt.setdefault(normalized, activity.prompt.strip())

    issues = [
        f"cross_chapter_prompt_template:{display_prompt[prompt]}:{len(chapter_ids)}"
        for prompt, chapter_ids in prompt_chapters.items()
        if len(chapter_ids) >= reuse_threshold
    ]
    return tuple(sorted(issues))
