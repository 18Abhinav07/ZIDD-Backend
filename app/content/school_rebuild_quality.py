"""Focused pedagogy quality checks for approved School chapter content."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable


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


def _normalized_text(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _normalized_answer(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", _normalized_text(value)).strip()


def _iter_stage_activities(chapter) -> Iterable[tuple[str, tuple[str, ...], str, object]]:
    for level in chapter.levels:
        for stage_name in _STAGE_NAMES:
            activity = getattr(level.checks, stage_name, None)
            if activity is not None:
                yield level.level_id, tuple(level.skill_ids), stage_name, activity


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
        prompt = _normalized_text(activity.prompt)
        for frame in _BANNED_PROMPT_FRAMES:
            if frame in prompt:
                issues.append(f"generic_prompt_frame:{level_id}:{stage_name}:{frame}")
                break
        if _is_brittle_constructed_exact_answer(activity, skill_ids):
            issues.append(f"brittle_constructed_exact_answer:{level_id}:{stage_name}")

    assessment = getattr(chapter, "chapter_assessment", None)
    if assessment is not None:
        for item in assessment.items:
            if _normalized_text(item.passage) in stage_passages:
                issues.append(f"assessment_reuses_teaching_passage:{item.item_id}")
            if _is_brittle_constructed_exact_answer(item, item.skill_ids):
                issues.append(f"brittle_constructed_exact_answer:assessment:{item.item_id}")

    return tuple(issues)


def corpus_quality_issues(chapters, *, reuse_threshold: int = 4) -> tuple[str, ...]:
    """Detect exact prompt templates copied across several different chapters."""

    prompt_chapters: dict[str, set[str]] = defaultdict(set)
    display_prompt: dict[str, str] = {}
    for chapter in chapters:
        for _, _, _, activity in _iter_stage_activities(chapter):
            normalized = _normalized_text(activity.prompt)
            prompt_chapters[normalized].add(chapter.chapter_id)
            display_prompt.setdefault(normalized, activity.prompt.strip())

    issues = [
        f"cross_chapter_prompt_template:{display_prompt[prompt]}:{len(chapter_ids)}"
        for prompt, chapter_ids in prompt_chapters.items()
        if len(chapter_ids) >= reuse_threshold
    ]
    return tuple(sorted(issues))
