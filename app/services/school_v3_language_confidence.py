"""English-production confidence for School V3 scaffolding.

This is intentionally not a readiness or mastery signal. It only helps the
frontend/tutor decide how much Hindi/Hinglish support to offer before a learner
attempts English work.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.school_core.readiness import AttemptEvidence, language_mismatch


LANGUAGE_CONFIDENCE_ALPHA = 0.20


@dataclass(frozen=True)
class LanguageConfidenceState:
    user_id: str
    en_production_confidence: float = 0.0
    total_signals: int = 0


def apply_language_signal(
    state: LanguageConfidenceState,
    evidence: AttemptEvidence,
) -> LanguageConfidenceState:
    """Update confidence from real attempt evidence.

    High unscaffolded English success increases the signal. Hint-heavy attempts
    and certifying language mismatches reduce it. This value must not be read by
    readiness classification.
    """

    score = _clamp(evidence.evaluator_score)
    hint_penalty = min(0.5, max(0, evidence.hint_count) * 0.10)
    scaffold_penalty = 0.20 if evidence.support_level != "independent" else 0.0
    mismatch_penalty = 0.35 if language_mismatch(evidence.language_required, evidence.language_detected) else 0.0
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
    """Adapt a curriculum evaluation into the language-only evidence contract."""

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
