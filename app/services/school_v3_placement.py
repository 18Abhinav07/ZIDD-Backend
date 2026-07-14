"""Bounded School V3 placement runtime state.

Placement only gathers diagnostic evidence. It updates practice readiness from
attempts, moves through bounded runtime stages, and can seed confirmed-ready
skills without granting mastery.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from app.services.school_core.readiness import (
    AttemptEvidence,
    PASS_THRESHOLD,
    SkillReadinessState,
    apply_attempt_evidence,
    apply_placement_ready_seed,
)


PlacementStage = Literal["snapshot", "targeted_diagnostic", "confirmatory"]
PlacementOutcome = Literal["in_progress", "complete", "insufficient_evidence"]

SNAPSHOT_MAX_ITEMS = 8
SNAPSHOT_MAX_SECONDS = 240
SNAPSHOT_MIN_ITEMS_FOR_TRANSITION = 2
TARGETED_MAX_OVERALL_ITEMS = 18
TARGETED_MAX_OVERALL_SECONDS = 300
TARGETED_PASSES_FOR_CONFIRMATORY = 2
CONFIRMATORY_MAX_SECONDS = 180
CONFIRMATORY_PASSES_FOR_READY = 1


@dataclass(frozen=True)
class PlacementItem:
    item_id: str
    skill_id: str
    skill_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillPlacementAttempts:
    skill_id: str
    attempts: int = 0
    passes: int = 0
    misses: int = 0
    snapshot_attempts: int = 0
    snapshot_passes: int = 0
    targeted_attempts: int = 0
    targeted_passes: int = 0
    confirmatory_attempts: int = 0
    confirmatory_passes: int = 0
    last_score: float | None = None


@dataclass(frozen=True)
class PlacementSessionState:
    subject_id: str
    class_no: int
    stage: PlacementStage = "snapshot"
    required_skill_ids: tuple[str, ...] = ()
    skill_states: dict[str, SkillReadinessState] = field(default_factory=dict)
    skill_attempts: dict[str, SkillPlacementAttempts] = field(default_factory=dict)
    answered_item_ids: tuple[str, ...] = ()
    total_items: int = 0
    scorable_answers: int = 0
    elapsed_seconds: int = 0
    stage_items: int = 0
    stage_elapsed_seconds: int = 0
    targeted_skill_ids: tuple[str, ...] = ()
    confirmatory_skill_ids: tuple[str, ...] = ()


def apply_placement_attempt(
    state: PlacementSessionState,
    item: PlacementItem,
    *,
    evaluator_score: float,
    evaluator_confidence: float,
    scorable: bool = True,
    elapsed_seconds_delta: int = 0,
) -> PlacementSessionState:
    if is_duplicate_item_attempt(state, item.item_id):
        return state

    skill_ids = _item_skill_ids(item)
    skill_states = dict(state.skill_states)
    skill_attempts = dict(state.skill_attempts)
    scorable_answers = state.scorable_answers

    if scorable:
        for skill_id in skill_ids:
            skill_state = skill_states.get(skill_id) or SkillReadinessState(skill_id=skill_id)
            skill_states[skill_id] = apply_attempt_evidence(
                skill_state,
                AttemptEvidence(
                    attempt_type="placement",
                    evaluator_score=evaluator_score,
                    evaluator_confidence=evaluator_confidence,
                    skill_ids=(skill_id,),
                    support_level="independent",
                ),
            )
            skill_attempts[skill_id] = _record_skill_attempt(
                skill_attempts.get(skill_id) or SkillPlacementAttempts(skill_id=skill_id),
                stage=state.stage,
                passed=evaluator_score >= PASS_THRESHOLD,
                score=evaluator_score,
            )
        scorable_answers += 1

    elapsed_delta = max(0, int(elapsed_seconds_delta))
    updated = replace(
        state,
        skill_states=skill_states,
        skill_attempts=skill_attempts,
        answered_item_ids=_append_answered_item(state.answered_item_ids, item.item_id),
        total_items=state.total_items + 1,
        scorable_answers=scorable_answers,
        elapsed_seconds=state.elapsed_seconds + elapsed_delta,
        stage_items=state.stage_items + 1,
        stage_elapsed_seconds=state.stage_elapsed_seconds + elapsed_delta,
    )
    return _apply_stage_transition(updated)


def apply_confirmed_ready_seed(
    state: PlacementSessionState,
    *,
    ready_skill_ids: tuple[str, ...],
    confidence: float,
) -> PlacementSessionState:
    skill_states = dict(state.skill_states)
    for skill_id in _unique_non_empty(ready_skill_ids):
        skill_state = skill_states.get(skill_id) or SkillReadinessState(skill_id=skill_id)
        skill_states[skill_id] = apply_placement_ready_seed(skill_state, confidence=confidence)
    return replace(state, skill_states=skill_states)


def confirmed_ready_skill_ids(state: PlacementSessionState) -> tuple[str, ...]:
    ready: list[str] = []
    for skill_id in state.confirmatory_skill_ids:
        attempts = state.skill_attempts.get(skill_id)
        if attempts and attempts.confirmatory_passes >= CONFIRMATORY_PASSES_FOR_READY:
            ready.append(skill_id)
    return tuple(ready)


def is_duplicate_item_attempt(state: PlacementSessionState, item_id: str) -> bool:
    return item_id in state.answered_item_ids


def placement_outcome(state: PlacementSessionState) -> PlacementOutcome:
    if _current_stage_cap_reached(state):
        return "insufficient_evidence"
    if state.stage == "confirmatory" and _confirmatory_complete(state):
        return "complete"
    return "in_progress"


def _apply_stage_transition(state: PlacementSessionState) -> PlacementSessionState:
    next_stage = _next_stage(state)
    if next_stage == state.stage:
        return state
    if next_stage == "targeted_diagnostic":
        return replace(
            state,
            stage=next_stage,
            stage_items=0,
            stage_elapsed_seconds=0,
            targeted_skill_ids=_targeted_candidates(state),
        )
    return replace(
        state,
        stage=next_stage,
        stage_items=0,
        stage_elapsed_seconds=0,
        confirmatory_skill_ids=_confirmatory_candidates(state),
    )


def _next_stage(state: PlacementSessionState) -> PlacementStage:
    if state.stage == "snapshot":
        if not _snapshot_has_enough_signal_to_transition(state):
            return "snapshot"
        if _targeted_candidates(state):
            return "targeted_diagnostic"
        return "confirmatory"

    if state.stage == "targeted_diagnostic":
        if not state.targeted_skill_ids:
            return "confirmatory"
        if all(_targeted_skill_ready_for_confirmation(state, skill_id) for skill_id in state.targeted_skill_ids):
            return "confirmatory"
        return "targeted_diagnostic"

    return "confirmatory"


def _snapshot_has_enough_signal_to_transition(state: PlacementSessionState) -> bool:
    if state.stage_items >= SNAPSHOT_MAX_ITEMS:
        return True
    if state.stage_elapsed_seconds >= SNAPSHOT_MAX_SECONDS:
        return state.stage_items >= SNAPSHOT_MIN_ITEMS_FOR_TRANSITION
    if state.required_skill_ids:
        covered = {
            skill_id
            for skill_id, attempts in state.skill_attempts.items()
            if attempts.snapshot_attempts > 0
        }
        return all(skill_id in covered for skill_id in state.required_skill_ids)
    return state.stage_items >= SNAPSHOT_MIN_ITEMS_FOR_TRANSITION


def _targeted_candidates(state: PlacementSessionState) -> tuple[str, ...]:
    candidates: list[str] = []
    for skill_id, attempts in state.skill_attempts.items():
        if attempts.snapshot_attempts and attempts.snapshot_passes == 0:
            candidates.append(skill_id)
    return tuple(candidates)


def _confirmatory_candidates(state: PlacementSessionState) -> tuple[str, ...]:
    if state.stage == "targeted_diagnostic":
        return tuple(
            skill_id
            for skill_id in state.targeted_skill_ids
            if _targeted_skill_ready_for_confirmation(state, skill_id)
        )
    return tuple(
        skill_id
        for skill_id, attempts in state.skill_attempts.items()
        if attempts.snapshot_passes > 0
    )


def _targeted_skill_ready_for_confirmation(state: PlacementSessionState, skill_id: str) -> bool:
    attempts = state.skill_attempts.get(skill_id)
    return bool(
        attempts
        and attempts.targeted_attempts >= TARGETED_PASSES_FOR_CONFIRMATORY
        and attempts.targeted_passes >= TARGETED_PASSES_FOR_CONFIRMATORY
    )


def _confirmatory_complete(state: PlacementSessionState) -> bool:
    if not state.confirmatory_skill_ids:
        return False
    return all(
        (state.skill_attempts.get(skill_id) or SkillPlacementAttempts(skill_id=skill_id)).confirmatory_passes
        >= CONFIRMATORY_PASSES_FOR_READY
        for skill_id in state.confirmatory_skill_ids
    )


def _current_stage_cap_reached(state: PlacementSessionState) -> bool:
    if state.stage == "snapshot":
        return state.stage_items >= SNAPSHOT_MAX_ITEMS or state.stage_elapsed_seconds >= SNAPSHOT_MAX_SECONDS
    if state.stage == "targeted_diagnostic":
        return (
            state.total_items >= TARGETED_MAX_OVERALL_ITEMS
            or state.elapsed_seconds >= TARGETED_MAX_OVERALL_SECONDS
        )
    return state.stage_elapsed_seconds >= CONFIRMATORY_MAX_SECONDS


def _record_skill_attempt(
    attempts: SkillPlacementAttempts,
    *,
    stage: PlacementStage,
    passed: bool,
    score: float,
) -> SkillPlacementAttempts:
    total_passes = attempts.passes + int(passed)
    total_misses = attempts.misses + int(not passed)
    if stage == "snapshot":
        return replace(
            attempts,
            attempts=attempts.attempts + 1,
            passes=total_passes,
            misses=total_misses,
            snapshot_attempts=attempts.snapshot_attempts + 1,
            snapshot_passes=attempts.snapshot_passes + int(passed),
            last_score=float(score),
        )
    if stage == "targeted_diagnostic":
        return replace(
            attempts,
            attempts=attempts.attempts + 1,
            passes=total_passes,
            misses=total_misses,
            targeted_attempts=attempts.targeted_attempts + 1,
            targeted_passes=attempts.targeted_passes + int(passed),
            last_score=float(score),
        )
    return replace(
        attempts,
        attempts=attempts.attempts + 1,
        passes=total_passes,
        misses=total_misses,
        confirmatory_attempts=attempts.confirmatory_attempts + 1,
        confirmatory_passes=attempts.confirmatory_passes + int(passed),
        last_score=float(score),
    )


def _item_skill_ids(item: PlacementItem) -> tuple[str, ...]:
    return _unique_non_empty((item.skill_id,) + item.skill_ids)


def _unique_non_empty(values: tuple[str, ...]) -> tuple[str, ...]:
    unique: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("placement_skill_id_required")
        if cleaned not in unique:
            unique.append(cleaned)
    return tuple(unique)


def _append_answered_item(history: tuple[str, ...], item_id: str) -> tuple[str, ...]:
    cleaned = item_id.strip()
    if not cleaned:
        raise ValueError("placement_item_id_required")
    if cleaned in history:
        return history
    return history + (cleaned,)
