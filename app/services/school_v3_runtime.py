"""School V3 runtime helpers for API routes.

The router owns auth and persistence. This module owns deterministic selection,
grading, state serialization, and pause/resume decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

from app.content.school_v3_content import (
    approved_chapters_for_class,
    chapter_for_id,
    load_ncert_source_map,
    public_school_v3_chapter,
    public_school_v3_item,
    supported_classes,
)
from app.content.school_v3_schema import SchoolV3AssessmentItem, SchoolV3ChapterBlueprint
from app.content.school_v3_taxonomy import locked_english_taxonomy
from app.services.school_core.readiness import (
    SkillReadinessState,
    apply_attempt_evidence,
    classify_skill_status,
)
from app.services.school_v3_evaluator import grade_deterministic_item, to_attempt_evidence
from app.services.school_v3_placement import (
    PlacementItem,
    PlacementSessionState,
    SkillPlacementAttempts,
    apply_confirmed_ready_seed,
    apply_placement_attempt,
    confirmed_ready_skill_ids,
    placement_outcome,
)


MASTERCLASS_CAP = 2


@dataclass(frozen=True)
class CurriculumSessionState:
    subject_id: str
    class_no: int
    chapter_id: str
    status: str = "active"
    skill_states: dict[str, SkillReadinessState] = field(default_factory=dict)
    answered_item_ids: tuple[str, ...] = ()
    watchlist_skill_ids: tuple[str, ...] = ()
    active_interrupt: dict[str, Any] | None = None
    interrupt_history: tuple[dict[str, Any], ...] = ()
    interrupt_counts: dict[str, int] = field(default_factory=dict)
    last_result: dict[str, Any] | None = None


@dataclass(frozen=True)
class MasterclassSessionState:
    subject_id: str
    class_no: int
    chapter_id: str
    skill_id: str
    linked_curriculum_session_id: str
    answered_item_ids: tuple[str, ...] = ()
    status: str = "active"
    last_result: dict[str, Any] | None = None


def school_v3_classes_payload(subject_id: str = "english") -> dict[str, Any]:
    classes = []
    for class_no in supported_classes(subject_id):
        source_map = load_ncert_source_map(subject_id, class_no)
        chapters = approved_chapters_for_class(subject_id, class_no)
        first_chapter = chapters[0] if chapters else None
        has_seed_chapters = any(chapter.approval_status == "seed" for chapter in chapters)
        classes.append(
            {
                "subject_id": subject_id,
                "class_no": class_no,
                "book_title": source_map["book_title"],
                "book_code": source_map["book_code"],
                "chapter_count": len(source_map["chapters"]),
                "first_chapter_id": first_chapter.chapter_id if first_chapter else None,
                "support_status": "engineering_seed" if has_seed_chapters else "available",
            }
        )
    return {"subject_id": subject_id, "classes": classes}


def required_skill_ids(class_no: int, *, limit: int | None = None) -> tuple[str, ...]:
    taxonomy = locked_english_taxonomy()
    ordered = [
        entry.skill_id
        for entry in taxonomy.entries
        if entry.subject_id == "english" and entry.class_min <= class_no <= entry.class_max
    ]
    return tuple(ordered[:limit] if limit else ordered)


def new_placement_state(subject_id: str, class_no: int) -> PlacementSessionState:
    available_required_skills = tuple(
        skill_id
        for skill_id in required_skill_ids(class_no)
        if _first_matching_item(
            subject_id=subject_id,
            class_no=class_no,
            skill_ids=(skill_id,),
            stages=("independent_check", "bridge", "chapter_check"),
            answered=set(),
            include_prerequisite_classes=True,
        )
        is not None
    )
    return PlacementSessionState(
        subject_id=subject_id,
        class_no=class_no,
        required_skill_ids=available_required_skills[:8],
    )


def placement_state_to_json(state: PlacementSessionState) -> dict[str, Any]:
    return {
        "subject_id": state.subject_id,
        "class_no": state.class_no,
        "stage": state.stage,
        "required_skill_ids": list(state.required_skill_ids),
        "skill_states": {
            skill_id: asdict(skill_state)
            for skill_id, skill_state in state.skill_states.items()
        },
        "skill_attempts": {
            skill_id: asdict(attempts)
            for skill_id, attempts in state.skill_attempts.items()
        },
        "answered_item_ids": list(state.answered_item_ids),
        "total_items": state.total_items,
        "scorable_answers": state.scorable_answers,
        "elapsed_seconds": state.elapsed_seconds,
        "stage_items": state.stage_items,
        "stage_elapsed_seconds": state.stage_elapsed_seconds,
        "targeted_skill_ids": list(state.targeted_skill_ids),
        "confirmatory_skill_ids": list(state.confirmatory_skill_ids),
    }


def placement_state_from_json(payload: dict[str, Any]) -> PlacementSessionState:
    return PlacementSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        class_no=int(payload.get("class_no") or 2),
        stage=payload.get("stage") or "snapshot",
        required_skill_ids=tuple(payload.get("required_skill_ids") or ()),
        skill_states={
            skill_id: SkillReadinessState(**state)
            for skill_id, state in dict(payload.get("skill_states") or {}).items()
        },
        skill_attempts={
            skill_id: SkillPlacementAttempts(**attempts)
            for skill_id, attempts in dict(payload.get("skill_attempts") or {}).items()
        },
        answered_item_ids=tuple(payload.get("answered_item_ids") or ()),
        total_items=int(payload.get("total_items") or 0),
        scorable_answers=int(payload.get("scorable_answers") or 0),
        elapsed_seconds=int(payload.get("elapsed_seconds") or 0),
        stage_items=int(payload.get("stage_items") or 0),
        stage_elapsed_seconds=int(payload.get("stage_elapsed_seconds") or 0),
        targeted_skill_ids=tuple(payload.get("targeted_skill_ids") or ()),
        confirmatory_skill_ids=tuple(payload.get("confirmatory_skill_ids") or ()),
    )


def next_placement_item(state: PlacementSessionState) -> SchoolV3AssessmentItem | None:
    if placement_outcome(state) != "in_progress":
        return None
    answered = set(state.answered_item_ids)
    candidates = _placement_skill_candidates(state)
    stages = {
        "snapshot": ("independent_check",),
        "targeted_diagnostic": ("bridge", "independent_check"),
        "confirmatory": ("chapter_check",),
    }[state.stage]
    return _first_matching_item(
        subject_id=state.subject_id,
        class_no=state.class_no,
        skill_ids=candidates,
        stages=stages,
        answered=answered,
        include_prerequisite_classes=True,
    )


def apply_placement_answer_to_state(
    state: PlacementSessionState,
    item: SchoolV3AssessmentItem,
    answer: str,
    *,
    elapsed_seconds_delta: int,
) -> PlacementSessionState:
    evaluation = grade_deterministic_item(item, answer)
    primary_skill = item.skill_ids[0]
    updated = apply_placement_attempt(
        state,
        PlacementItem(item_id=item.item_id, skill_id=primary_skill, skill_ids=tuple(item.skill_ids[1:])),
        evaluator_score=evaluation.score,
        evaluator_confidence=evaluation.confidence,
        scorable=True,
        elapsed_seconds_delta=elapsed_seconds_delta,
    )
    if placement_outcome(updated) == "complete":
        ready = confirmed_ready_skill_ids(updated)
        if ready:
            updated = apply_confirmed_ready_seed(updated, ready_skill_ids=ready, confidence=1.0)
    return updated


def placement_summary(state: PlacementSessionState) -> dict[str, Any]:
    statuses = {
        skill_id: classify_skill_status(skill_state)
        for skill_id, skill_state in sorted(state.skill_states.items())
    }
    return {
        "stage": state.stage,
        "status": placement_outcome(state),
        "required_skill_ids": list(state.required_skill_ids),
        "ready_skill_ids": [skill_id for skill_id, status in statuses.items() if status in {"ready", "mastered"}],
        "weak_skill_ids": [skill_id for skill_id, status in statuses.items() if status == "weak"],
        "skill_statuses": statuses,
    }


def placement_response_state(state: PlacementSessionState) -> dict[str, Any]:
    item = next_placement_item(state)
    return {
        "stage": state.stage,
        "status": placement_outcome(state),
        "answered_count": len(state.answered_item_ids),
        "total_items": state.total_items,
        "scorable_answers": state.scorable_answers,
        "max_items": 18,
        "readiness_summary": placement_summary(state),
        "next_item": public_school_v3_item(item) if item else None,
    }


def find_placement_item(state: PlacementSessionState, item_id: str) -> SchoolV3AssessmentItem:
    for chapter in _chapters_for_scope(
        subject_id=state.subject_id,
        class_no=state.class_no,
        include_prerequisite_classes=True,
    ):
        for outcome in chapter.outcomes:
            for item in outcome.items:
                if item.item_id == item_id:
                    return item
    raise KeyError(item_id)


def new_curriculum_state(
    subject_id: str,
    class_no: int,
    chapter_id: str,
    watchlist_skill_ids: tuple[str, ...] = (),
) -> CurriculumSessionState:
    return CurriculumSessionState(
        subject_id=subject_id,
        class_no=class_no,
        chapter_id=chapter_id,
        watchlist_skill_ids=watchlist_skill_ids,
    )


def curriculum_state_to_json(state: CurriculumSessionState) -> dict[str, Any]:
    return {
        "subject_id": state.subject_id,
        "class_no": state.class_no,
        "chapter_id": state.chapter_id,
        "status": state.status,
        "skill_states": {
            skill_id: asdict(skill_state)
            for skill_id, skill_state in state.skill_states.items()
        },
        "answered_item_ids": list(state.answered_item_ids),
        "watchlist_skill_ids": list(state.watchlist_skill_ids),
        "active_interrupt": state.active_interrupt,
        "interrupt_history": list(state.interrupt_history),
        "interrupt_counts": dict(state.interrupt_counts),
        "last_result": state.last_result,
    }


def curriculum_state_from_json(payload: dict[str, Any]) -> CurriculumSessionState:
    return CurriculumSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        class_no=int(payload.get("class_no") or 2),
        chapter_id=str(payload.get("chapter_id") or ""),
        status=str(payload.get("status") or "active"),
        skill_states={
            skill_id: SkillReadinessState(**state)
            for skill_id, state in dict(payload.get("skill_states") or {}).items()
        },
        answered_item_ids=tuple(payload.get("answered_item_ids") or ()),
        watchlist_skill_ids=tuple(payload.get("watchlist_skill_ids") or ()),
        active_interrupt=payload.get("active_interrupt"),
        interrupt_history=tuple(dict(row) for row in payload.get("interrupt_history") or ()),
        interrupt_counts={
            str(skill_id): int(count)
            for skill_id, count in dict(payload.get("interrupt_counts") or {}).items()
        },
        last_result=payload.get("last_result"),
    )


def curriculum_response_state(state: CurriculumSessionState) -> dict[str, Any]:
    chapter = chapter_for_id(state.subject_id, state.chapter_id)
    item = next_curriculum_item(state)
    return {
        "status": state.status,
        "chapter": public_school_v3_chapter(chapter) if chapter else None,
        "answered_count": len(state.answered_item_ids),
        "watchlist_skill_ids": list(state.watchlist_skill_ids),
        "active_interrupt": state.active_interrupt,
        "interrupt_history": list(state.interrupt_history),
        "last_result": state.last_result,
        "skill_statuses": {
            skill_id: classify_skill_status(skill_state)
            for skill_id, skill_state in sorted(state.skill_states.items())
        },
        "next_item": public_school_v3_item(item) if item else None,
    }


def next_curriculum_item(state: CurriculumSessionState) -> SchoolV3AssessmentItem | None:
    if state.status != "active":
        return None
    chapter = chapter_for_id(state.subject_id, state.chapter_id)
    if chapter is None:
        return None
    return _first_unanswered_item(chapter, set(state.answered_item_ids))


def find_curriculum_item(state: CurriculumSessionState, item_id: str) -> SchoolV3AssessmentItem:
    chapter = chapter_for_id(state.subject_id, state.chapter_id)
    if chapter is None:
        raise KeyError(item_id)
    for outcome in chapter.outcomes:
        for item in outcome.items:
            if item.item_id == item_id:
                return item
    raise KeyError(item_id)


def apply_curriculum_answer_to_state(
    state: CurriculumSessionState,
    item: SchoolV3AssessmentItem,
    answer: str,
    *,
    masterclass_session_id: str | None = None,
    masterclass_next_item: dict[str, Any] | None = None,
) -> CurriculumSessionState:
    evaluation = grade_deterministic_item(item, answer)
    skill_states = dict(state.skill_states)
    for skill_id in item.skill_ids:
        previous = skill_states.get(skill_id) or SkillReadinessState(skill_id=skill_id)
        skill_states[skill_id] = apply_attempt_evidence(
            previous,
            to_attempt_evidence(
                evaluation,
                attempt_type=item.stage,
                support_level=_support_level_for_stage(item.stage),
                language_required="en" if item.stage in {"independent_check", "transfer_check", "review_check", "chapter_check"} else None,
            ),
        )
    primary_skill = item.skill_ids[0]
    primary_state = skill_states[primary_skill]
    correct = evaluation.score >= 0.80
    next_state = replace(
        state,
        skill_states=skill_states,
        answered_item_ids=_append_once(state.answered_item_ids, item.item_id),
        last_result={
            "item_id": item.item_id,
            "score": evaluation.score,
            "correct": correct,
            "feedback": evaluation.feedback_to_learner,
            "skill_id": primary_skill,
            "skill_status": classify_skill_status(primary_state),
        },
    )
    if correct:
        return next_state
    return _maybe_pause_for_masterclass(
        next_state,
        primary_skill,
        masterclass_session_id=masterclass_session_id,
        masterclass_next_item=masterclass_next_item,
    )


def masterclass_state_to_json(state: MasterclassSessionState) -> dict[str, Any]:
    return {
        "subject_id": state.subject_id,
        "class_no": state.class_no,
        "chapter_id": state.chapter_id,
        "skill_id": state.skill_id,
        "linked_curriculum_session_id": state.linked_curriculum_session_id,
        "answered_item_ids": list(state.answered_item_ids),
        "status": state.status,
        "last_result": state.last_result,
    }


def masterclass_state_from_json(payload: dict[str, Any]) -> MasterclassSessionState:
    return MasterclassSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        class_no=int(payload.get("class_no") or 2),
        chapter_id=str(payload.get("chapter_id") or ""),
        skill_id=str(payload.get("skill_id") or ""),
        linked_curriculum_session_id=str(payload.get("linked_curriculum_session_id") or ""),
        answered_item_ids=tuple(payload.get("answered_item_ids") or ()),
        status=str(payload.get("status") or "active"),
        last_result=payload.get("last_result"),
    )


def new_masterclass_state(
    *,
    linked_curriculum_session_id: str,
    curriculum_state: CurriculumSessionState,
    skill_id: str,
) -> MasterclassSessionState:
    return MasterclassSessionState(
        subject_id=curriculum_state.subject_id,
        class_no=curriculum_state.class_no,
        chapter_id=curriculum_state.chapter_id,
        skill_id=skill_id,
        linked_curriculum_session_id=linked_curriculum_session_id,
    )


def next_masterclass_item(state: MasterclassSessionState) -> SchoolV3AssessmentItem | None:
    if state.status != "active":
        return None
    answered = set(state.answered_item_ids)
    return _first_matching_item(
        subject_id=state.subject_id,
        class_no=state.class_no,
        skill_ids=(state.skill_id,),
        stages=("bridge", "independent_check"),
        answered=answered,
        chapter_id=state.chapter_id,
    )


def masterclass_response_state(state: MasterclassSessionState) -> dict[str, Any]:
    item = next_masterclass_item(state)
    return {
        "status": state.status,
        "skill_id": state.skill_id,
        "linked_curriculum_session_id": state.linked_curriculum_session_id,
        "answered_count": len(state.answered_item_ids),
        "last_result": state.last_result,
        "next_item": public_school_v3_item(item) if item else None,
    }


def apply_masterclass_answer_to_state(
    state: MasterclassSessionState,
    item: SchoolV3AssessmentItem,
    answer: str,
) -> MasterclassSessionState:
    evaluation = grade_deterministic_item(item, answer)
    complete = evaluation.score >= 0.80
    return replace(
        state,
        status="complete" if complete else "active",
        answered_item_ids=_append_once(state.answered_item_ids, item.item_id),
        last_result={
            "item_id": item.item_id,
            "score": evaluation.score,
            "correct": complete,
            "feedback": evaluation.feedback_to_learner,
        },
    )


def resolve_curriculum_interrupt(
    state: CurriculumSessionState,
    *,
    resolution: str,
) -> CurriculumSessionState:
    if not state.active_interrupt:
        return state
    history = state.interrupt_history + (
        {
            **state.active_interrupt,
            "resolution": resolution,
        },
    )
    return replace(
        state,
        status="active",
        active_interrupt=None,
        interrupt_history=history,
    )


def _placement_skill_candidates(state: PlacementSessionState) -> tuple[str, ...]:
    if state.stage == "snapshot":
        covered = {
            skill_id
            for skill_id, attempts in state.skill_attempts.items()
            if attempts.snapshot_attempts > 0
        }
        uncovered = tuple(skill_id for skill_id in state.required_skill_ids if skill_id not in covered)
        return uncovered or state.required_skill_ids
    if state.stage == "targeted_diagnostic":
        return state.targeted_skill_ids or state.required_skill_ids
    return state.confirmatory_skill_ids or state.required_skill_ids


def _first_matching_item(
    *,
    subject_id: str,
    class_no: int,
    skill_ids: tuple[str, ...],
    stages: tuple[str, ...],
    answered: set[str],
    chapter_id: str | None = None,
    include_prerequisite_classes: bool = False,
) -> SchoolV3AssessmentItem | None:
    chapters = (
        (chapter_for_id(subject_id, chapter_id),)
        if chapter_id
        else _chapters_for_scope(
            subject_id=subject_id,
            class_no=class_no,
            include_prerequisite_classes=include_prerequisite_classes,
        )
    )
    skill_set = set(skill_ids)
    for chapter in chapters:
        if chapter is None:
            continue
        for outcome in chapter.outcomes:
            for item in outcome.items:
                if item.item_id in answered or item.stage not in stages:
                    continue
                if skill_set.intersection(item.skill_ids):
                    return item
    return None


def _chapters_for_scope(
    *,
    subject_id: str,
    class_no: int,
    include_prerequisite_classes: bool,
) -> tuple[SchoolV3ChapterBlueprint, ...]:
    if not include_prerequisite_classes:
        return approved_chapters_for_class(subject_id, class_no)
    chapters: list[SchoolV3ChapterBlueprint] = []
    for source_class_no in supported_classes(subject_id):
        if source_class_no <= class_no:
            chapters.extend(approved_chapters_for_class(subject_id, source_class_no))
    return tuple(chapters)


def _first_unanswered_item(
    chapter: SchoolV3ChapterBlueprint,
    answered: set[str],
) -> SchoolV3AssessmentItem | None:
    for outcome in chapter.outcomes:
        for item in outcome.items:
            if item.item_id not in answered:
                return item
    return None


def _support_level_for_stage(stage: str) -> str:
    if stage == "bridge":
        return "bridge"
    if stage == "guided":
        return "guided"
    return "independent"


def _maybe_pause_for_masterclass(
    state: CurriculumSessionState,
    skill_id: str,
    *,
    masterclass_session_id: str | None,
    masterclass_next_item: dict[str, Any] | None,
) -> CurriculumSessionState:
    skill_state = state.skill_states[skill_id]
    if classify_skill_status(skill_state) != "weak":
        return state
    counts = dict(state.interrupt_counts)
    next_count = int(counts.get(skill_id) or 0) + 1
    counts[skill_id] = next_count
    if next_count > MASTERCLASS_CAP:
        blocked_state = replace(
            skill_state,
            active_blockers=tuple(sorted(set(skill_state.active_blockers + ("masterclass_cap_exceeded",)))),
        )
        skill_states = dict(state.skill_states)
        skill_states[skill_id] = blocked_state
        return replace(
            state,
            skill_states=skill_states,
            interrupt_counts=counts,
            interrupt_history=state.interrupt_history
            + (
                {
                    "trigger_skill_id": skill_id,
                    "trigger_count": next_count,
                    "resolution": "capped_out",
                },
            ),
        )
    if skill_id not in state.watchlist_skill_ids and next_count == 1:
        return replace(state, interrupt_counts=counts)
    if not masterclass_session_id or masterclass_next_item is None:
        return replace(state, interrupt_counts=counts)
    return replace(
        state,
        status="paused_for_masterclass",
        interrupt_counts=counts,
        active_interrupt={
            "trigger_skill_id": skill_id,
            "trigger_count": next_count,
            "masterclass_session_id": masterclass_session_id,
            "next_item": masterclass_next_item,
        },
    )


def _append_once(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("school_v3_item_id_required")
    if cleaned in values:
        return values
    return values + (cleaned,)
