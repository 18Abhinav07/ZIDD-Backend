"""Non-certifying English-production confidence for School scaffolding."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.school_core.readiness import AttemptEvidence, language_mismatch


LANGUAGE_CONFIDENCE_ALPHA = 0.20
_ENGLISH_LANGUAGE_CODES = frozenset({"en", "eng", "english"})
_UNTRUSTED_EVALUATION_BLOCKERS = frozenset(
    {
        "needs_human_review",
        "human_review_required",
        "untrusted_evaluation",
        "evaluator_untrusted",
    }
)


@dataclass(frozen=True)
class LanguageConfidenceState:
    user_id: str
    en_production_confidence: float = 0.0
    total_signals: int = 0


def apply_language_signal(
    state: LanguageConfidenceState,
    evidence: AttemptEvidence,
) -> LanguageConfidenceState:
    """Update only the language scaffold signal from committed attempt evidence."""

    detected_language = str(evidence.language_detected or "").strip().casefold()
    normalized_blockers = {
        str(blocker).strip().casefold() for blocker in evidence.blockers
    }
    has_untrusted_blocker = bool(
        _UNTRUSTED_EVALUATION_BLOCKERS & normalized_blockers
    ) or any(
        "human_review" in blocker or "untrusted" in blocker
        for blocker in normalized_blockers
    )
    trusted_english = (
        detected_language in _ENGLISH_LANGUAGE_CODES
        and not has_untrusted_blocker
    )
    score = (
        _clamp(evidence.evaluator_score) * _clamp(evidence.evaluator_confidence)
        if trusted_english
        else 0.0
    )
    hint_penalty = min(0.5, max(0, evidence.hint_count) * 0.10)
    scaffold_penalty = 0.20 if evidence.support_level != "independent" else 0.0
    mismatch_penalty = (
        0.35
        if language_mismatch(evidence.language_required, evidence.language_detected)
        else 0.0
    )
    signal = _clamp(score - hint_penalty - scaffold_penalty - mismatch_penalty)
    previous = _clamp(state.en_production_confidence)
    updated = previous + LANGUAGE_CONFIDENCE_ALPHA * (signal - previous)
    return LanguageConfidenceState(
        user_id=state.user_id,
        en_production_confidence=round(_clamp(updated), 4),
        total_signals=state.total_signals + 1,
    )


def apply_curriculum_language_signal(
    state: LanguageConfidenceState,
    evaluation: dict,
) -> LanguageConfidenceState:
    kind = str(evaluation.get("kind") or "guided_check")
    if kind == "guided_check":
        attempt_type = "guided"
        support_level = "guided"
    elif kind in {"independent_check", "transfer_check", "chapter_check"}:
        attempt_type = kind
        support_level = "independent"
    else:
        attempt_type = "bridge"
        support_level = "bridge"
    certifying = attempt_type in {
        "independent_check",
        "transfer_check",
        "chapter_check",
    }
    return apply_language_signal(
        state,
        AttemptEvidence(
            attempt_type=attempt_type,
            evaluator_score=float(evaluation.get("score") or 0.0),
            evaluator_confidence=float(evaluation.get("confidence") or 0.0),
            skill_ids=tuple(evaluation.get("skill_ids") or ()),
            support_level=support_level,
            language_required="en" if certifying else None,
            language_detected=str(evaluation.get("language_detected") or "") or None,
            blockers=tuple(evaluation.get("blockers") or ()),
            hint_count=int(evaluation.get("hint_count") or 0),
        ),
    )


def curriculum_language_evaluation(
    activity: dict,
    evaluation: dict,
) -> dict | None:
    """Return real English-production evidence, never tutor-supplied choices.

    Curriculum correctness and English production are separate signals. A
    learner can demonstrate comprehension through a selected option, but the
    option's wording belongs to the authored tutor rather than the learner.
    Language confidence therefore accepts only unscaffolded, certifying text
    responses in the English subject; readiness remains independent of this
    preference signal.
    """

    if not bool(evaluation.get("scored", True)):
        return None
    if str(activity.get("evidence_role") or "") != "certifying":
        return None
    if str(activity.get("certifying_language") or "").casefold() not in _ENGLISH_LANGUAGE_CODES:
        return None
    if str(activity.get("interaction_type") or "") not in {
        "short_text",
        "paragraph_text",
    }:
        return None
    if activity.get("options"):
        return None
    return evaluation


async def persist_language_confidence(store, state: LanguageConfidenceState) -> None:
    await store.upsert_school_language_confidence(
        user_id=state.user_id,
        en_production_confidence=state.en_production_confidence,
        total_signals=state.total_signals,
    )


async def load_language_confidence(store, user_id: str) -> LanguageConfidenceState:
    row = await store.get_school_language_confidence(user_id)
    if not row:
        return LanguageConfidenceState(user_id=user_id)
    return LanguageConfidenceState(
        user_id=user_id,
        en_production_confidence=float(row.get("en_production_confidence") or 0.0),
        total_signals=int(row.get("total_signals") or 0),
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


__all__ = [
    "LANGUAGE_CONFIDENCE_ALPHA",
    "LanguageConfidenceState",
    "apply_curriculum_language_signal",
    "apply_language_signal",
    "curriculum_language_evaluation",
    "load_language_confidence",
    "persist_language_confidence",
]
