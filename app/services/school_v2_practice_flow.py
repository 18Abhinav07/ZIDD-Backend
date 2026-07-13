"""Authored School V2 catch-up practice flow."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from app.services.school_v2_learning import SchoolLearningProfileService
from app.services.school_v2_readiness import (
    AttemptEvidence,
    AttemptType,
    SkillReadinessState,
    apply_attempt_evidence,
    classify_skill_status,
)


PracticeStage = Literal["guided", "bridge", "independent_check", "transfer_check"]
PracticeItemType = Literal["fill_blank", "multiple_choice", "short_answer"]


@dataclass(frozen=True)
class PracticeItem:
    item_id: str
    skill_id: str
    stage: PracticeStage
    item_type: PracticeItemType
    prompt: str
    answer_key: str
    feedback_correct: str
    feedback_incorrect: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class PracticeLesson:
    skill_id: str
    title: str
    teaching_points: tuple[str, ...]
    example: str
    items: tuple[PracticeItem, ...]


@dataclass(frozen=True)
class PracticeResult:
    item_id: str
    score: float
    correct: bool
    feedback: str
    skill_status: str


@dataclass(frozen=True)
class PracticeSessionState:
    subject_id: str
    target_class_no: int
    skill_id: str
    skill_state: SkillReadinessState
    answered_item_ids: tuple[str, ...] = ()
    last_result: PracticeResult | None = None


PRACTICE_LESSONS: dict[str, PracticeLesson] = {
    "eng.c5.answer.reason": PracticeLesson(
        skill_id="eng.c5.answer.reason",
        title="Answer why questions with a clear reason",
        teaching_points=(
            "A why answer should name the cause, not just repeat the event.",
            "Use because when it helps connect the event to the reason.",
            "A strong answer can stand alone without the reader guessing the missing part.",
        ),
        example="Why did the plant grow well? Because Riya watered it every day.",
        items=(
            PracticeItem(
                item_id="practice_reason_guided_1",
                skill_id="eng.c5.answer.reason",
                stage="guided",
                item_type="short_answer",
                prompt="Why did the plant grow well? Start with because.",
                answer_key="because she watered it every day",
                feedback_correct="Good. You connected the result to the cause.",
                feedback_incorrect="Name the cause clearly: because she watered it every day.",
            ),
            PracticeItem(
                item_id="practice_reason_bridge_1",
                skill_id="eng.c5.answer.reason",
                stage="bridge",
                item_type="fill_blank",
                prompt="A reason answer often begins with __.",
                answer_key="because",
                feedback_correct="Correct. Because is a useful signal for reasons.",
                feedback_incorrect="The missing word is because.",
            ),
            PracticeItem(
                item_id="practice_reason_independent_1",
                skill_id="eng.c5.answer.reason",
                stage="independent_check",
                item_type="short_answer",
                prompt="Why was Arjun late for school?",
                answer_key="because he missed the bus",
                feedback_correct="Correct. You gave the reason for being late.",
                feedback_incorrect="The answer needs the cause: because he missed the bus.",
            ),
            PracticeItem(
                item_id="practice_reason_independent_2",
                skill_id="eng.c5.answer.reason",
                stage="independent_check",
                item_type="short_answer",
                prompt="Why did Sara win the recitation?",
                answer_key="because she practiced daily",
                feedback_correct="Correct. This is an independent reason answer.",
                feedback_incorrect="Use the cause: because she practiced daily.",
            ),
            PracticeItem(
                item_id="practice_reason_transfer_1",
                skill_id="eng.c5.answer.reason",
                stage="transfer_check",
                item_type="short_answer",
                prompt="Mohan lent Ravi his book. Why was Ravi thankful?",
                answer_key="because he shared his book",
                feedback_correct="Good transfer. You used the same reason pattern in a new situation.",
                feedback_incorrect="A strong reason is: because he shared his book.",
            ),
        ),
    ),
    "eng.c5.vocab.context": PracticeLesson(
        skill_id="eng.c5.vocab.context",
        title="Use sentence clues to understand words",
        teaching_points=(
            "Look at nearby words before guessing a meaning.",
            "Check whether your meaning fits the whole sentence.",
            "Do not choose a meaning only because the word sounds familiar.",
        ),
        example="The tiny seed was hard to see. Tiny means small because the seed was hard to see.",
        items=(
            PracticeItem("practice_vocab_guided_1", "eng.c5.vocab.context", "guided", "short_answer", "In 'The tiny seed was hard to see', what does tiny mean?", "small", "Correct. The clue is hard to see.", "Tiny means small here."),
            PracticeItem("practice_vocab_bridge_1", "eng.c5.vocab.context", "bridge", "multiple_choice", "Gentle with the puppy means __.", "kind", "Correct.", "Gentle means kind here.", ("kind", "late", "loud", "heavy")),
            PracticeItem("practice_vocab_independent_1", "eng.c5.vocab.context", "independent_check", "multiple_choice", "Cheerful after helping means __.", "happy", "Correct.", "Cheerful means happy.", ("happy", "hungry", "afraid", "tired")),
            PracticeItem("practice_vocab_independent_2", "eng.c5.vocab.context", "independent_check", "multiple_choice", "A narrow lane is a __ lane.", "thin", "Correct.", "Narrow means thin or not wide.", ("thin", "noisy", "bright", "soft")),
            PracticeItem("practice_vocab_transfer_1", "eng.c5.vocab.context", "transfer_check", "short_answer", "In 'The room was silent, so we whispered', what does silent mean?", "quiet", "Good transfer.", "Silent means quiet."),
        ),
    ),
    "eng.c5.comprehension.event": PracticeLesson(
        skill_id="eng.c5.comprehension.event",
        title="Track what happened in a passage",
        teaching_points=(
            "An event is something that happens in the story.",
            "Use who, where, and what happened to identify the event.",
            "Do not replace the event with a feeling unless the question asks for it.",
        ),
        example="Riya planted flowers in the garden. The event is that Riya planted flowers.",
        items=(
            PracticeItem("practice_event_guided_1", "eng.c5.comprehension.event", "guided", "short_answer", "Riya planted flowers in the garden. What happened?", "riya planted flowers", "Correct. You named the event.", "The event is that Riya planted flowers."),
            PracticeItem("practice_event_bridge_1", "eng.c5.comprehension.event", "bridge", "fill_blank", "The children borrowed books from the __.", "library", "Correct.", "They borrowed books from the library."),
            PracticeItem("practice_event_independent_1", "eng.c5.comprehension.event", "independent_check", "fill_blank", "Arjun packed his bag before going to __.", "school", "Correct.", "He was going to school."),
            PracticeItem("practice_event_independent_2", "eng.c5.comprehension.event", "independent_check", "short_answer", "Meena fed the puppy and gave it water. What did Meena do?", "fed the puppy", "Correct. You identified the event.", "Name what happened: Meena fed the puppy."),
            PracticeItem("practice_event_transfer_1", "eng.c5.comprehension.event", "transfer_check", "short_answer", "The class cleaned the board before the teacher arrived. What happened first?", "cleaned the board", "Good transfer.", "The first event was that the class cleaned the board."),
        ),
    ),
}


def lesson_for_skill(skill_id: str) -> PracticeLesson | None:
    return PRACTICE_LESSONS.get(skill_id)


def public_practice_item(item: PracticeItem) -> dict:
    return {
        "item_id": item.item_id,
        "skill_id": item.skill_id,
        "stage": item.stage,
        "type": item.item_type,
        "prompt": item.prompt,
        "options": list(item.options) if item.options else None,
    }


def public_lesson(lesson: PracticeLesson) -> dict:
    return {
        "skill_id": lesson.skill_id,
        "title": lesson.title,
        "teaching_points": list(lesson.teaching_points),
        "example": lesson.example,
    }


def next_practice_item(state: PracticeSessionState) -> PracticeItem | None:
    lesson = lesson_for_skill(state.skill_id)
    if lesson is None:
        return None
    answered = set(state.answered_item_ids)
    for item in lesson.items:
        if item.item_id not in answered:
            return item
    return None


def practice_status(state: PracticeSessionState) -> str:
    return "in_progress" if next_practice_item(state) else "complete"


def score_practice_answer(item: PracticeItem, answer: str) -> float:
    expected = _normalize(item.answer_key)
    actual = _normalize(answer)
    if item.item_type == "short_answer":
        return 1.0 if expected in actual else 0.0
    return 1.0 if actual == expected else 0.0


def apply_practice_answer(state: PracticeSessionState, item: PracticeItem, answer: str) -> PracticeSessionState:
    score = score_practice_answer(item, answer)
    evidence = AttemptEvidence(
        attempt_type=_attempt_type_for_stage(item.stage),
        evaluator_score=score,
        evaluator_confidence=1.0,
        skill_ids=(state.skill_id,),
        support_level="independent" if item.stage in {"independent_check", "transfer_check"} else item.stage,
        language_required="en",
        language_detected="en",
    )
    skill_state = apply_attempt_evidence(state.skill_state, evidence)
    status = classify_skill_status(skill_state)
    correct = score >= 0.80
    return replace(
        state,
        skill_state=skill_state,
        answered_item_ids=_append_answered_item(state.answered_item_ids, item.item_id),
        last_result=PracticeResult(
            item_id=item.item_id,
            score=score,
            correct=correct,
            feedback=item.feedback_correct if correct else item.feedback_incorrect,
            skill_status=status,
        ),
    )


async def record_practice_attempt(
    store,
    *,
    practice_session_id: str,
    user_id: str,
    state: PracticeSessionState,
    item: PracticeItem,
) -> None:
    service = SchoolLearningProfileService(store)
    status = classify_skill_status(state.skill_state)
    await service.record_attempt(
        attempt_id=f"{practice_session_id}:{item.item_id}",
        user_id=user_id,
        subject_id=state.subject_id,
        class_no=state.target_class_no,
        session_id=practice_session_id,
        chapter_id="catch_up",
        node_id=item.item_id,
        skill_state=state.skill_state,
        evidence=AttemptEvidence(
            attempt_type=_attempt_type_for_stage(item.stage),
            evaluator_score=state.last_result.score if state.last_result else 0.0,
            evaluator_confidence=1.0,
            skill_ids=(state.skill_id,),
            support_level="independent" if item.stage in {"independent_check", "transfer_check"} else item.stage,
            language_required="en",
            language_detected="en",
        ),
        criteria_json=[],
        evidence_json={
            "practice_session_id": practice_session_id,
            "item_id": item.item_id,
            "stage": item.stage,
            "feedback": state.last_result.feedback if state.last_result else "",
        },
        source="practice_attempt",
        task_type="school_practice",
        gap="" if status in {"ready", "mastered"} else "catch_up_required",
    )


def state_from_profile(
    *,
    subject_id: str,
    target_class_no: int,
    skill_id: str,
    profile: dict | None,
) -> PracticeSessionState:
    evidence = dict((profile or {}).get("evidence_json") or {})
    skill_state = SkillReadinessState(
        skill_id=skill_id,
        practice_readiness=evidence.get("practice_readiness") or (profile or {}).get("readiness"),
        certified_readiness=evidence.get("certified_readiness"),
        total_attempts=int((profile or {}).get("attempts") or 0),
        independent_passes=int(evidence.get("independent_passes") or 0),
        transfer_passes=int(evidence.get("transfer_passes") or 0),
        ready_source=evidence.get("ready_source") or None,
        last_confidence=float((profile or {}).get("confidence") or 0.0),
    )
    return PracticeSessionState(
        subject_id=subject_id,
        target_class_no=target_class_no,
        skill_id=skill_id,
        skill_state=skill_state,
    )


def state_to_json(state: PracticeSessionState) -> dict:
    return {
        "subject_id": state.subject_id,
        "target_class_no": state.target_class_no,
        "skill_id": state.skill_id,
        "skill_state": {
            "skill_id": state.skill_state.skill_id,
            "practice_readiness": state.skill_state.practice_readiness,
            "certified_readiness": state.skill_state.certified_readiness,
            "total_attempts": state.skill_state.total_attempts,
            "certified_attempts": state.skill_state.certified_attempts,
            "independent_passes": state.skill_state.independent_passes,
            "transfer_passes": state.skill_state.transfer_passes,
            "review_passes": state.skill_state.review_passes,
            "chapter_passes": state.skill_state.chapter_passes,
            "ready_source": state.skill_state.ready_source,
            "active_blockers": list(state.skill_state.active_blockers),
            "recent_hint_flags": list(state.skill_state.recent_hint_flags),
            "last_confidence": state.skill_state.last_confidence,
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


def state_from_json(payload: dict) -> PracticeSessionState:
    raw_skill = dict(payload.get("skill_state") or {})
    last = payload.get("last_result")
    return PracticeSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        target_class_no=int(payload.get("target_class_no") or 5),
        skill_id=str(payload.get("skill_id") or raw_skill.get("skill_id") or ""),
        skill_state=SkillReadinessState(
            skill_id=str(raw_skill.get("skill_id") or payload.get("skill_id") or ""),
            practice_readiness=raw_skill.get("practice_readiness"),
            certified_readiness=raw_skill.get("certified_readiness"),
            total_attempts=int(raw_skill.get("total_attempts") or 0),
            certified_attempts=int(raw_skill.get("certified_attempts") or 0),
            independent_passes=int(raw_skill.get("independent_passes") or 0),
            transfer_passes=int(raw_skill.get("transfer_passes") or 0),
            review_passes=int(raw_skill.get("review_passes") or 0),
            chapter_passes=int(raw_skill.get("chapter_passes") or 0),
            ready_source=raw_skill.get("ready_source"),
            active_blockers=tuple(raw_skill.get("active_blockers") or ()),
            recent_hint_flags=tuple(bool(flag) for flag in raw_skill.get("recent_hint_flags") or ()),
            last_confidence=float(raw_skill.get("last_confidence") or 0.0),
        ),
        answered_item_ids=tuple(str(item_id) for item_id in payload.get("answered_item_ids") or ()),
        last_result=None if not last else PracticeResult(
            item_id=str(last.get("item_id") or ""),
            score=float(last.get("score") or 0.0),
            correct=bool(last.get("correct")),
            feedback=str(last.get("feedback") or ""),
            skill_status=str(last.get("skill_status") or "weak"),
        ),
    )


def _attempt_type_for_stage(stage: PracticeStage) -> AttemptType:
    return stage


def _append_answered_item(history: tuple[str, ...], item_id: str) -> tuple[str, ...]:
    if item_id in history:
        return history
    return history + (item_id,)


def _normalize(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())
