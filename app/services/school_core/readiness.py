"""Shared school readiness and mastery contract.

The model can evaluate an answer, but it does not decide advancement. This
module owns the deterministic state update that placement, tutor turns, chapter
checks, and reports must share across School V2 and School V3.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal


AttemptType = Literal[
    "bridge",
    "guided",
    "placement",
    "independent_check",
    "transfer_check",
    "review_check",
    "chapter_check",
]

SkillStatus = Literal["unseen", "weak", "practice_ready", "ready", "mastered"]

PRACTICE_ATTEMPT_TYPES: set[str] = {"bridge", "guided", "placement"}
CERTIFYING_ATTEMPT_TYPES: set[str] = {
    "independent_check",
    "transfer_check",
    "review_check",
    "chapter_check",
}
BASE_ALPHA: dict[str, float] = {
    "bridge": 0.15,
    "guided": 0.25,
    "placement": 0.30,
    "independent_check": 0.45,
    "transfer_check": 0.50,
    "review_check": 0.40,
    "chapter_check": 0.55,
}
PASS_THRESHOLD = 0.80
READY_THRESHOLD = 0.80
MASTERY_THRESHOLD = 0.90
PLACEMENT_READY_SEED = 0.80
MAX_HINT_WINDOW = 5
READY_REVIEW_DAYS = 3
MASTERED_REVIEW_DAYS = 7
FAILED_REVIEW_DAYS = 1
MAX_REVIEW_DAYS = 30


@dataclass(frozen=True)
class SkillReadinessState:
    skill_id: str
    practice_readiness: float | None = None
    certified_readiness: float | None = None
    total_attempts: int = 0
    certified_attempts: int = 0
    independent_passes: int = 0
    transfer_passes: int = 0
    review_passes: int = 0
    chapter_passes: int = 0
    ready_source: str | None = None
    active_blockers: tuple[str, ...] = ()
    recent_hint_flags: tuple[bool, ...] = ()
    last_confidence: float = 0.0


@dataclass(frozen=True)
class AttemptEvidence:
    attempt_type: AttemptType
    evaluator_score: float
    evaluator_confidence: float
    skill_ids: tuple[str, ...]
    support_level: Literal["independent", "guided", "bridge", "scaffolded"] = "guided"
    language_required: str | None = None
    language_detected: str | None = None
    blockers: tuple[str, ...] = ()
    hint_count: int = 0


def apply_attempt_evidence(
    state: SkillReadinessState,
    evidence: AttemptEvidence,
) -> SkillReadinessState:
    """Apply one evaluated attempt to one skill.

    `evaluator_score` stays the learner's real performance signal. Attempt type
    only changes how much the running estimate moves and whether certification
    is eligible.
    """

    _validate_attempt(state, evidence)
    score = _clamp(evidence.evaluator_score)
    confidence = _clamp(evidence.evaluator_confidence)
    blockers = _attempt_blockers(evidence)
    practice_readiness = _ema(
        previous=state.practice_readiness,
        score=score,
        attempt_type=evidence.attempt_type,
        confidence=confidence,
    )
    recent_hint_flags = _append_hint_flag(
        state.recent_hint_flags,
        evidence.hint_count > 0 or evidence.support_level != "independent",
    )

    certified_readiness = state.certified_readiness
    certified_attempts = state.certified_attempts
    independent_passes = state.independent_passes
    transfer_passes = state.transfer_passes
    review_passes = state.review_passes
    chapter_passes = state.chapter_passes

    certifying = _is_certifying_attempt(evidence, blockers)
    passed = score >= PASS_THRESHOLD
    if certifying:
        certified_readiness = _ema(
            previous=state.certified_readiness,
            score=score,
            attempt_type=evidence.attempt_type,
            confidence=confidence,
        )
        certified_attempts += 1
        if passed:
            if evidence.attempt_type == "independent_check":
                independent_passes += 1
            elif evidence.attempt_type == "transfer_check":
                transfer_passes += 1
            elif evidence.attempt_type == "review_check":
                review_passes += 1
            elif evidence.attempt_type == "chapter_check":
                chapter_passes += 1

    return replace(
        state,
        practice_readiness=practice_readiness,
        certified_readiness=certified_readiness,
        total_attempts=state.total_attempts + 1,
        certified_attempts=certified_attempts,
        independent_passes=independent_passes,
        transfer_passes=transfer_passes,
        review_passes=review_passes,
        chapter_passes=chapter_passes,
        active_blockers=blockers,
        recent_hint_flags=recent_hint_flags,
        last_confidence=confidence,
    )


def apply_placement_ready_seed(
    state: SkillReadinessState,
    *,
    confidence: float,
) -> SkillReadinessState:
    """Convert a completed placement-ready verdict into unlock evidence.

    This seed lets a target-ready learner unlock curriculum from bounded
    placement, but it is not an independent pass and can never create mastery by
    itself.
    """

    _ = _clamp(confidence)
    seeded = max(state.certified_readiness or 0.0, PLACEMENT_READY_SEED)
    return replace(
        state,
        certified_readiness=seeded,
        ready_source="placement",
        last_confidence=_clamp(confidence),
    )


def classify_skill_status(state: SkillReadinessState) -> SkillStatus:
    if _is_mastered(state):
        return "mastered"
    if _is_ready(state):
        return "ready"
    if (state.practice_readiness or 0.0) >= READY_THRESHOLD:
        return "practice_ready"
    if state.total_attempts == 0:
        return "unseen"
    return "weak"


def hint_dependency(state: SkillReadinessState) -> float:
    if not state.recent_hint_flags:
        return 0.0
    return sum(1 for flag in state.recent_hint_flags if flag) / len(state.recent_hint_flags)


def next_review_interval_days(
    state: SkillReadinessState,
    *,
    previous_interval_days: int | None = None,
    review_passed: bool = True,
) -> int:
    """Return the next retention interval.

    A failed review collapses the interval. A passed review starts at the
    status baseline and then doubles up to the cap.
    """

    if not review_passed:
        return FAILED_REVIEW_DAYS
    if previous_interval_days is not None:
        return min(MAX_REVIEW_DAYS, max(FAILED_REVIEW_DAYS, previous_interval_days * 2))
    status = classify_skill_status(state)
    if status == "mastered":
        return MASTERED_REVIEW_DAYS
    if status == "ready":
        return READY_REVIEW_DAYS
    return FAILED_REVIEW_DAYS


def language_mismatch(required: str | None, detected: str | None) -> bool:
    return _language_mismatch(required, detected)


def _is_ready(state: SkillReadinessState) -> bool:
    if (state.certified_readiness or 0.0) < READY_THRESHOLD:
        return False
    return state.ready_source == "placement" or state.independent_passes >= 2


def _is_mastered(state: SkillReadinessState) -> bool:
    return (
        (state.certified_readiness or 0.0) >= MASTERY_THRESHOLD
        and state.independent_passes >= 3
        and state.transfer_passes >= 1
        and not state.active_blockers
        and hint_dependency(state) < 0.25
    )


def _is_certifying_attempt(evidence: AttemptEvidence, blockers: tuple[str, ...]) -> bool:
    return (
        evidence.attempt_type in CERTIFYING_ATTEMPT_TYPES
        and evidence.support_level == "independent"
        and not blockers
    )


def _attempt_blockers(evidence: AttemptEvidence) -> tuple[str, ...]:
    blockers = set(evidence.blockers)
    if _language_mismatch(evidence.language_required, evidence.language_detected):
        blockers.add("language_mismatch")
    return tuple(sorted(blockers))


def _language_mismatch(required: str | None, detected: str | None) -> bool:
    if not required or not detected:
        return False
    return _normalize_language(required) != _normalize_language(detected)


def _normalize_language(language: str) -> str:
    cleaned = language.strip().lower()
    if cleaned in {"en", "eng", "english"}:
        return "en"
    if cleaned in {"hi", "hin", "hindi"}:
        return "hi"
    if cleaned in {"hi_en", "hinglish", "hindi_english"}:
        return "hi_en"
    return cleaned


def _ema(
    *,
    previous: float | None,
    score: float,
    attempt_type: str,
    confidence: float,
) -> float:
    if previous is None:
        return score
    alpha = BASE_ALPHA[attempt_type] * confidence
    return _clamp(previous + alpha * (score - previous))


def _append_hint_flag(history: tuple[bool, ...], flag: bool) -> tuple[bool, ...]:
    return (tuple(history) + (flag,))[-MAX_HINT_WINDOW:]


def _validate_attempt(state: SkillReadinessState, evidence: AttemptEvidence) -> None:
    if evidence.attempt_type not in BASE_ALPHA:
        raise ValueError(f"unknown school attempt_type: {evidence.attempt_type}")
    if state.skill_id not in evidence.skill_ids:
        raise ValueError(f"attempt does not include skill_id {state.skill_id}")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


__all__ = [
    "AttemptEvidence",
    "AttemptType",
    "BASE_ALPHA",
    "CERTIFYING_ATTEMPT_TYPES",
    "FAILED_REVIEW_DAYS",
    "MASTERY_THRESHOLD",
    "MASTERED_REVIEW_DAYS",
    "MAX_HINT_WINDOW",
    "MAX_REVIEW_DAYS",
    "PASS_THRESHOLD",
    "PLACEMENT_READY_SEED",
    "PRACTICE_ATTEMPT_TYPES",
    "READY_REVIEW_DAYS",
    "READY_THRESHOLD",
    "SkillReadinessState",
    "SkillStatus",
    "apply_attempt_evidence",
    "apply_placement_ready_seed",
    "classify_skill_status",
    "hint_dependency",
    "language_mismatch",
    "next_review_interval_days",
]
