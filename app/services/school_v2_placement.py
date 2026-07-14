"""Bounded School V2 placement state.

Placement is diagnostic evidence. It updates practice readiness while the
completed placement verdict decides which skills get a certified-ready seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from app.services.school_v2_readiness import (
    AttemptEvidence,
    PASS_THRESHOLD,
    SkillReadinessState,
    apply_attempt_evidence,
    apply_placement_ready_seed,
)


DifficultyBand = Literal["foundational", "entry", "target", "stretch"]
PlacementOutcome = Literal["in_progress", "complete", "insufficient_evidence"]

BAND_ORDER: tuple[DifficultyBand, ...] = ("foundational", "entry", "target", "stretch")
DEFAULT_MAX_ITEMS = 18
DEFAULT_MAX_SECONDS = 12 * 60
DEFAULT_MIN_SCORABLE = 8
MISSES_BEFORE_STEP_DOWN = 2


@dataclass(frozen=True)
class PlacementItem:
    item_id: str
    skill_id: str
    difficulty_band: DifficultyBand


@dataclass(frozen=True)
class PlacementSessionState:
    subject_id: str
    target_class_no: int
    skill_states: dict[str, SkillReadinessState] = field(default_factory=dict)
    band_misses: dict[tuple[str, DifficultyBand], int] = field(default_factory=dict)
    answered_item_ids: tuple[str, ...] = ()
    total_items: int = 0
    scorable_answers: int = 0
    elapsed_seconds: int = 0


def apply_placement_attempt(
    state: PlacementSessionState,
    item: PlacementItem,
    *,
    evaluator_score: float,
    evaluator_confidence: float,
    scorable: bool = True,
    elapsed_seconds_delta: int = 0,
) -> PlacementSessionState:
    skill_states = dict(state.skill_states)
    band_misses = dict(state.band_misses)
    scorable_answers = state.scorable_answers

    if scorable:
        skill_state = skill_states.get(item.skill_id) or SkillReadinessState(skill_id=item.skill_id)
        skill_states[item.skill_id] = apply_attempt_evidence(
            skill_state,
            AttemptEvidence(
                attempt_type="placement",
                evaluator_score=evaluator_score,
                evaluator_confidence=evaluator_confidence,
                skill_ids=(item.skill_id,),
                support_level="independent",
            ),
        )
        scorable_answers += 1
        key = (item.skill_id, item.difficulty_band)
        if evaluator_score < PASS_THRESHOLD:
            band_misses[key] = band_misses.get(key, 0) + 1
        else:
            band_misses[key] = 0

    return replace(
        state,
        skill_states=skill_states,
        band_misses=band_misses,
        answered_item_ids=_append_answered_item(state.answered_item_ids, item.item_id),
        total_items=state.total_items + 1,
        scorable_answers=scorable_answers,
        elapsed_seconds=state.elapsed_seconds + max(0, elapsed_seconds_delta),
    )


def apply_ready_verdicts(
    state: PlacementSessionState,
    *,
    ready_skill_ids: tuple[str, ...],
    confidence: float,
) -> PlacementSessionState:
    skill_states = dict(state.skill_states)
    for skill_id in ready_skill_ids:
        skill_state = skill_states.get(skill_id) or SkillReadinessState(skill_id=skill_id)
        skill_states[skill_id] = apply_placement_ready_seed(skill_state, confidence=confidence)
    return replace(state, skill_states=skill_states)


def next_band_for_skill(
    state: PlacementSessionState,
    skill_id: str,
    current_band: DifficultyBand,
) -> DifficultyBand:
    misses = state.band_misses.get((skill_id, current_band), 0)
    if misses < MISSES_BEFORE_STEP_DOWN:
        return current_band
    return _step_down(current_band)


def placement_outcome(
    state: PlacementSessionState,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_seconds: int = DEFAULT_MAX_SECONDS,
    min_scorable: int = DEFAULT_MIN_SCORABLE,
) -> PlacementOutcome:
    if state.scorable_answers >= min_scorable:
        return "complete"
    if state.scorable_answers < min_scorable:
        if state.total_items < max_items and state.elapsed_seconds < max_seconds:
            return "in_progress"
        return "insufficient_evidence"
    return "complete"


def _step_down(band: DifficultyBand) -> DifficultyBand:
    index = BAND_ORDER.index(band)
    if index == 0:
        return band
    return BAND_ORDER[index - 1]


def state_to_json(state: PlacementSessionState) -> dict:
    return {
        "subject_id": state.subject_id,
        "target_class_no": state.target_class_no,
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
        "band_misses": [
            {"skill_id": skill_id, "difficulty_band": band, "misses": misses}
            for (skill_id, band), misses in state.band_misses.items()
        ],
        "answered_item_ids": list(state.answered_item_ids),
        "total_items": state.total_items,
        "scorable_answers": state.scorable_answers,
        "elapsed_seconds": state.elapsed_seconds,
    }


def state_from_json(payload: dict) -> PlacementSessionState:
    skill_states = {
        skill_id: SkillReadinessState(
            skill_id=data["skill_id"],
            practice_readiness=data.get("practice_readiness"),
            certified_readiness=data.get("certified_readiness"),
            total_attempts=int(data.get("total_attempts") or 0),
            certified_attempts=int(data.get("certified_attempts") or 0),
            independent_passes=int(data.get("independent_passes") or 0),
            transfer_passes=int(data.get("transfer_passes") or 0),
            review_passes=int(data.get("review_passes") or 0),
            chapter_passes=int(data.get("chapter_passes") or 0),
            ready_source=data.get("ready_source"),
            active_blockers=tuple(data.get("active_blockers") or ()),
            recent_hint_flags=tuple(bool(flag) for flag in data.get("recent_hint_flags") or ()),
            last_confidence=float(data.get("last_confidence") or 0.0),
        )
        for skill_id, data in dict(payload.get("skill_states") or {}).items()
    }
    band_misses = {
        (str(row.get("skill_id") or ""), str(row.get("difficulty_band") or "target")): int(
            row.get("misses") or 0
        )
        for row in list(payload.get("band_misses") or [])
    }
    return PlacementSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        target_class_no=int(payload.get("target_class_no") or 5),
        skill_states=skill_states,
        band_misses=band_misses,  # type: ignore[arg-type]
        answered_item_ids=tuple(str(item_id) for item_id in payload.get("answered_item_ids") or ()),
        total_items=int(payload.get("total_items") or 0),
        scorable_answers=int(payload.get("scorable_answers") or 0),
        elapsed_seconds=int(payload.get("elapsed_seconds") or 0),
    )


def _append_answered_item(history: tuple[str, ...], item_id: str) -> tuple[str, ...]:
    if item_id in history:
        return history
    return history + (item_id,)
