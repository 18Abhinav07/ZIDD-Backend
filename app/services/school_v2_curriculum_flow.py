"""Authored School V2 target-curriculum chapter flow."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from app.services.school_v2_learning import SchoolLearningProfileService
from app.services.school_v2_readiness import (
    AttemptEvidence,
    SkillReadinessState,
    apply_attempt_evidence,
    classify_skill_status,
)


ChapterItemType = Literal["fill_blank", "multiple_choice", "short_answer"]


@dataclass(frozen=True)
class ChapterCheckItem:
    item_id: str
    skill_id: str
    item_type: ChapterItemType
    prompt: str
    answer_key: str
    feedback_correct: str
    feedback_incorrect: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class TargetChapter:
    chapter_id: str
    subject_id: str
    target_class_no: int
    book_title: str
    chapter_title: str
    curriculum_version: str
    source_url: str
    support_status: Literal["pilot"]
    teaching_points: tuple[str, ...]
    example: str
    items: tuple[ChapterCheckItem, ...]


@dataclass(frozen=True)
class ChapterResult:
    item_id: str
    score: float
    correct: bool
    feedback: str
    skill_status: str


@dataclass(frozen=True)
class CurriculumSessionState:
    subject_id: str
    target_class_no: int
    chapter_id: str
    skill_states: dict[str, SkillReadinessState] = field(default_factory=dict)
    answered_item_ids: tuple[str, ...] = ()
    last_result: ChapterResult | None = None


TARGET_CHAPTERS: dict[str, TargetChapter] = {
    "eng_c5_pilot_reading_reason": TargetChapter(
        chapter_id="eng_c5_pilot_reading_reason",
        subject_id="english",
        target_class_no=5,
        book_title="Class 5 English pilot",
        chapter_title="Reading With Care",
        curriculum_version="school-v2-pilot-2026-07",
        source_url="https://ncert.nic.in/textbook.php",
        support_status="pilot",
        teaching_points=(
            "Read the question first so you know what evidence to look for.",
            "Use nearby words to understand unfamiliar vocabulary.",
            "For why questions, answer with the reason rather than repeating only the event.",
        ),
        example=(
            "The children cleaned the playground together. They finished quickly because "
            "everyone helped. The reason is: because everyone helped."
        ),
        items=(
            ChapterCheckItem(
                item_id="chapter_vocab_check_1",
                skill_id="eng.c5.vocab.context",
                item_type="multiple_choice",
                prompt="In 'Anu read the notice carefully before answering', carefully means __.",
                answer_key="carefully",
                feedback_correct="Correct. The sentence shows Anu read with attention.",
                feedback_incorrect="Carefully means with attention.",
                options=("carefully", "loudly", "late", "hungrily"),
            ),
            ChapterCheckItem(
                item_id="chapter_event_check_1",
                skill_id="eng.c5.comprehension.event",
                item_type="short_answer",
                prompt="The children cleaned the playground before the game. What happened?",
                answer_key="the children cleaned the playground",
                feedback_correct="Correct. You identified the event.",
                feedback_incorrect="Name the event: the children cleaned the playground.",
            ),
            ChapterCheckItem(
                item_id="chapter_reason_check_1",
                skill_id="eng.c5.answer.reason",
                item_type="short_answer",
                prompt="Why did the work finish quickly?",
                answer_key="because everyone helped",
                feedback_correct="Correct. You gave the reason.",
                feedback_incorrect="The reason is: because everyone helped.",
            ),
        ),
    )
}


def chapter_for_id(chapter_id: str) -> TargetChapter | None:
    return TARGET_CHAPTERS.get(chapter_id)


def find_chapter_item(chapter_id: str, item_id: str) -> ChapterCheckItem | None:
    chapter = chapter_for_id(chapter_id)
    if chapter is None:
        return None
    for item in chapter.items:
        if item.item_id == item_id:
            return item
    return None


def first_chapter_for_class(target_class_no: int) -> TargetChapter | None:
    for chapter in TARGET_CHAPTERS.values():
        if chapter.target_class_no == target_class_no and chapter.subject_id == "english":
            return chapter
    return None


def public_chapter(chapter: TargetChapter) -> dict:
    return {
        "chapter_id": chapter.chapter_id,
        "subject_id": chapter.subject_id,
        "target_class_no": chapter.target_class_no,
        "book_title": chapter.book_title,
        "chapter_title": chapter.chapter_title,
        "curriculum_version": chapter.curriculum_version,
        "source_url": chapter.source_url,
        "support_status": chapter.support_status,
    }


def public_chapter_lesson(chapter: TargetChapter) -> dict:
    return {
        "chapter_id": chapter.chapter_id,
        "title": chapter.chapter_title,
        "teaching_points": list(chapter.teaching_points),
        "example": chapter.example,
    }


def public_chapter_item(item: ChapterCheckItem) -> dict:
    return {
        "item_id": item.item_id,
        "skill_id": item.skill_id,
        "stage": "chapter_check",
        "type": item.item_type,
        "prompt": item.prompt,
        "options": list(item.options) if item.options else None,
    }


def next_chapter_item(state: CurriculumSessionState) -> ChapterCheckItem | None:
    chapter = chapter_for_id(state.chapter_id)
    if chapter is None:
        return None
    answered = set(state.answered_item_ids)
    for item in chapter.items:
        if item.item_id not in answered:
            return item
    return None


def curriculum_status(state: CurriculumSessionState) -> str:
    return "in_progress" if next_chapter_item(state) else "complete"


def chapter_score(state: CurriculumSessionState) -> float:
    chapter = chapter_for_id(state.chapter_id)
    if chapter is None or not chapter.items:
        return 0.0
    return _answered_score(state, chapter.items)


def apply_chapter_answer(
    state: CurriculumSessionState,
    item: ChapterCheckItem,
    answer: str,
) -> CurriculumSessionState:
    score = score_chapter_answer(item, answer)
    previous = state.skill_states.get(item.skill_id) or SkillReadinessState(skill_id=item.skill_id)
    evidence = AttemptEvidence(
        attempt_type="chapter_check",
        evaluator_score=score,
        evaluator_confidence=1.0,
        skill_ids=(item.skill_id,),
        support_level="independent",
        language_required="en",
        language_detected="en",
    )
    skill_state = apply_attempt_evidence(previous, evidence)
    skill_states = dict(state.skill_states)
    skill_states[item.skill_id] = skill_state
    correct = score >= 0.80
    return replace(
        state,
        skill_states=skill_states,
        answered_item_ids=_append_answered_item(state.answered_item_ids, item.item_id),
        last_result=ChapterResult(
            item_id=item.item_id,
            score=score,
            correct=correct,
            feedback=item.feedback_correct if correct else item.feedback_incorrect,
            skill_status=classify_skill_status(skill_state),
        ),
    )


def score_chapter_answer(item: ChapterCheckItem, answer: str) -> float:
    expected = _normalize(item.answer_key)
    actual = _normalize(answer)
    if item.item_type == "short_answer":
        return 1.0 if expected in actual else 0.0
    return 1.0 if actual == expected else 0.0


async def record_chapter_attempt(
    store,
    *,
    curriculum_session_id: str,
    user_id: str,
    state: CurriculumSessionState,
    item: ChapterCheckItem,
) -> None:
    skill_state = state.skill_states[item.skill_id]
    status = classify_skill_status(skill_state)
    service = SchoolLearningProfileService(store)
    await service.record_attempt(
        attempt_id=f"{curriculum_session_id}:{item.item_id}",
        user_id=user_id,
        subject_id=state.subject_id,
        class_no=state.target_class_no,
        session_id=curriculum_session_id,
        chapter_id=state.chapter_id,
        node_id=item.item_id,
        skill_state=skill_state,
        evidence=AttemptEvidence(
            attempt_type="chapter_check",
            evaluator_score=state.last_result.score if state.last_result else 0.0,
            evaluator_confidence=1.0,
            skill_ids=(item.skill_id,),
            support_level="independent",
            language_required="en",
            language_detected="en",
        ),
        criteria_json=[],
        evidence_json={
            "curriculum_session_id": curriculum_session_id,
            "chapter_id": state.chapter_id,
            "item_id": item.item_id,
            "stage": "chapter_check",
            "feedback": state.last_result.feedback if state.last_result else "",
        },
        source="chapter_check",
        task_type="school_chapter",
        gap="" if status in {"ready", "mastered"} else "chapter_gap_detected",
    )


def state_from_profiles(
    *,
    subject_id: str,
    target_class_no: int,
    chapter_id: str,
    profiles: list[dict],
) -> CurriculumSessionState:
    skill_states: dict[str, SkillReadinessState] = {}
    for profile in profiles:
        skill_id = str(profile.get("skill_id") or "")
        if not skill_id:
            continue
        evidence = dict(profile.get("evidence_json") or {})
        skill_states[skill_id] = SkillReadinessState(
            skill_id=skill_id,
            practice_readiness=evidence.get("practice_readiness") or profile.get("readiness"),
            certified_readiness=evidence.get("certified_readiness") or profile.get("readiness"),
            total_attempts=int(profile.get("attempts") or 0),
            certified_attempts=int(evidence.get("certified_attempts") or 0),
            independent_passes=int(evidence.get("independent_passes") or 0),
            transfer_passes=int(evidence.get("transfer_passes") or 0),
            review_passes=int(evidence.get("review_passes") or 0),
            chapter_passes=int(evidence.get("chapter_passes") or 0),
            ready_source=evidence.get("ready_source") or None,
            active_blockers=tuple(evidence.get("active_blockers") or ()),
            recent_hint_flags=tuple(bool(flag) for flag in evidence.get("recent_hint_flags") or ()),
            last_confidence=float(profile.get("confidence") or 0.0),
        )
    return CurriculumSessionState(
        subject_id=subject_id,
        target_class_no=target_class_no,
        chapter_id=chapter_id,
        skill_states=skill_states,
    )


def state_to_json(state: CurriculumSessionState) -> dict:
    return {
        "subject_id": state.subject_id,
        "target_class_no": state.target_class_no,
        "chapter_id": state.chapter_id,
        "skill_states": {
            skill_id: {
                "skill_id": skill.skill_id,
                "practice_readiness": skill.practice_readiness,
                "certified_readiness": skill.certified_readiness,
                "total_attempts": skill.total_attempts,
                "certified_attempts": skill.certified_attempts,
                "independent_passes": skill.independent_passes,
                "transfer_passes": skill.transfer_passes,
                "review_passes": skill.review_passes,
                "chapter_passes": skill.chapter_passes,
                "ready_source": skill.ready_source,
                "active_blockers": list(skill.active_blockers),
                "recent_hint_flags": list(skill.recent_hint_flags),
                "last_confidence": skill.last_confidence,
            }
            for skill_id, skill in state.skill_states.items()
        },
        "answered_item_ids": list(state.answered_item_ids),
        "last_result": None if state.last_result is None else {
            "item_id": state.last_result.item_id,
            "score": state.last_result.score,
            "correct": state.last_result.correct,
            "feedback": state.last_result.feedback,
            "skill_status": state.last_result.skill_status,
        },
    }


def state_from_json(payload: dict) -> CurriculumSessionState:
    raw_skills = dict(payload.get("skill_states") or {})
    last = payload.get("last_result")
    return CurriculumSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        target_class_no=int(payload.get("target_class_no") or 5),
        chapter_id=str(payload.get("chapter_id") or ""),
        skill_states={
            str(skill_id): SkillReadinessState(
                skill_id=str(raw.get("skill_id") or skill_id),
                practice_readiness=raw.get("practice_readiness"),
                certified_readiness=raw.get("certified_readiness"),
                total_attempts=int(raw.get("total_attempts") or 0),
                certified_attempts=int(raw.get("certified_attempts") or 0),
                independent_passes=int(raw.get("independent_passes") or 0),
                transfer_passes=int(raw.get("transfer_passes") or 0),
                review_passes=int(raw.get("review_passes") or 0),
                chapter_passes=int(raw.get("chapter_passes") or 0),
                ready_source=raw.get("ready_source"),
                active_blockers=tuple(raw.get("active_blockers") or ()),
                recent_hint_flags=tuple(bool(flag) for flag in raw.get("recent_hint_flags") or ()),
                last_confidence=float(raw.get("last_confidence") or 0.0),
            )
            for skill_id, raw in raw_skills.items()
        },
        answered_item_ids=tuple(str(item_id) for item_id in payload.get("answered_item_ids") or ()),
        last_result=None if not last else ChapterResult(
            item_id=str(last.get("item_id") or ""),
            score=float(last.get("score") or 0.0),
            correct=bool(last.get("correct")),
            feedback=str(last.get("feedback") or ""),
            skill_status=str(last.get("skill_status") or "weak"),
        ),
    )


def _answered_score(state: CurriculumSessionState, items: tuple[ChapterCheckItem, ...]) -> float:
    if not items:
        return 0.0
    answered = set(state.answered_item_ids)
    if not answered:
        return 0.0
    score = 0.0
    for item in items:
        if item.item_id in answered:
            skill = state.skill_states.get(item.skill_id)
            if skill and (skill.certified_readiness or 0.0) >= 0.80:
                score += 1.0
    return round(score / len(items), 4)


def _append_answered_item(history: tuple[str, ...], item_id: str) -> tuple[str, ...]:
    if item_id in history:
        return history
    return history + (item_id,)


def _normalize(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())
