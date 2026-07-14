"""Pure learner-profile projection for one committed School attempt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_ATTEMPT_ALPHA = {
    "guided_check": 0.12,
    "bridge": 0.15,
    "independent_check": 0.30,
    "transfer_check": 0.35,
    "chapter_check": 0.40,
}
_CERTIFYING_ATTEMPTS = {"independent_check", "transfer_check", "chapter_check"}


def _score(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class SchoolAttemptEvidence:
    session_id: str
    chapter_id: str
    level_id: str
    module_id: str
    task_type: str
    focus: str
    skill_ids: tuple[str, ...]
    attempt_type: str
    score: float
    confidence: float
    criteria: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...]
    answer_excerpt: str
    attempt_passed: bool
    certified_skill_scores: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SchoolAttemptEvidence":
        return cls(
            session_id=str(raw.get("session_id") or ""),
            chapter_id=str(raw.get("chapter_id") or ""),
            level_id=str(raw.get("level_id") or ""),
            module_id=str(raw.get("module_id") or raw.get("chapter_id") or ""),
            task_type=str(raw.get("task_type") or "school_rebuild_curriculum"),
            focus=str(raw.get("focus") or ""),
            skill_ids=tuple(dict.fromkeys(str(value) for value in raw.get("skill_ids") or [] if str(value))),
            attempt_type=str(raw.get("attempt_type") or ""),
            score=_score(raw.get("score")),
            confidence=_score(raw.get("confidence")),
            criteria=tuple(dict(value) for value in raw.get("criteria") or [] if isinstance(value, dict)),
            blockers=tuple(str(value) for value in raw.get("blockers") or [] if str(value)),
            answer_excerpt=str(raw.get("answer_excerpt") or "")[:320],
            attempt_passed=bool(raw.get("attempt_passed")),
            certified_skill_scores={
                str(key): _score(value)
                for key, value in dict(raw.get("certified_skill_scores") or {}).items()
                if str(key)
            },
        )


def derive_school_projection_delta(
    evidence: SchoolAttemptEvidence,
    existing_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Derive profile upserts from rows locked by the caller."""

    existing = {str(row.get("skill_id") or ""): row for row in existing_rows}
    skill_ids = list(dict.fromkeys((*evidence.skill_ids, *evidence.certified_skill_scores)))
    passed_without_blockers = evidence.attempt_passed and not evidence.blockers
    certifying = evidence.attempt_type in _CERTIFYING_ATTEMPTS
    readiness_signal = (
        evidence.score
        if passed_without_blockers and certifying
        else min(evidence.score, 0.79)
        if passed_without_blockers
        else min(evidence.score, 0.59)
    )
    alpha = _ATTEMPT_ALPHA.get(evidence.attempt_type, 0.20)
    delta: list[dict[str, Any]] = []

    for skill_id in skill_ids:
        previous = existing.get(skill_id) or {}
        previous_attempts = int(previous.get("attempts") or 0)
        counts_as_attempt = skill_id in evidence.skill_ids
        previous_readiness = _score(previous.get("readiness"))
        readiness = (
            readiness_signal
            if counts_as_attempt and previous_attempts == 0
            else round((1.0 - alpha) * previous_readiness + alpha * readiness_signal, 4)
            if counts_as_attempt
            else previous_readiness
        )
        is_strong = (
            counts_as_attempt
            and certifying
            and passed_without_blockers
            and evidence.score >= 0.8
            and readiness >= 0.65
        )
        certified_score = evidence.certified_skill_scores.get(skill_id)
        has_certification_score = certified_score is not None
        chapter_mastered = certified_score is not None and certified_score >= 0.8
        previous_gaps = [str(value) for value in previous.get("gaps_json") or [] if str(value)]
        gap = "" if is_strong or chapter_mastered else previous_gaps[0] if passed_without_blockers and previous_gaps else evidence.focus
        previous_evidence = previous.get("evidence_json") if isinstance(previous.get("evidence_json"), dict) else {}
        evidence_json = {
            "session_id": evidence.session_id,
            "chapter_id": evidence.chapter_id,
            "level_id": evidence.level_id,
            "attempt_type": evidence.attempt_type,
            "latest_quote": evidence.answer_excerpt,
            "criteria": list(evidence.criteria),
            "blockers": list(evidence.blockers),
            "evaluator_score": evidence.score,
            "attempt_passed": evidence.attempt_passed,
        }
        if has_certification_score:
            certification_evidence = {
                "latest_certification": {
                    "session_id": evidence.session_id,
                    "chapter_id": evidence.chapter_id,
                    "score": certified_score,
                },
            }
            evidence_json = (
                {**previous_evidence, **certification_evidence}
                if not counts_as_attempt and previous
                else {
                    **previous_evidence,
                    **({} if previous_evidence else evidence_json),
                    **certification_evidence,
                }
            )
        strong = is_strong or chapter_mastered
        preserves_prior_metadata = not counts_as_attempt and bool(previous)
        delta.append({
            "user_id": "",
            "domain": "school",
            "skill_id": skill_id,
            "module_id": (
                previous.get("module_id")
                if preserves_prior_metadata
                else evidence.module_id or evidence.chapter_id
            ),
            "task_type": (
                previous.get("task_type")
                if preserves_prior_metadata
                else evidence.task_type
            ),
            "mastery": 1.0 if chapter_mastered else _score(previous.get("mastery")),
            "readiness": max(readiness, certified_score or 0.0) if chapter_mastered else readiness,
            "confidence": (
                previous.get("confidence")
                if preserves_prior_metadata
                else evidence.confidence
            ),
            "attempts": previous_attempts + (1 if counts_as_attempt else 0),
            "strengths_json": (
                previous.get("strengths_json") or []
                if preserves_prior_metadata
                else [evidence.focus] if strong else []
            ),
            "gaps_json": (
                previous.get("gaps_json") or []
                if preserves_prior_metadata
                else [gap] if gap else []
            ),
            "evidence_json": evidence_json,
            "recommended_next_action": (
                previous.get("recommended_next_action") or ""
                if preserves_prior_metadata
                else "Continue with a new independent example."
                if strong
                else f"Try this skill without support: {evidence.focus}."
                if passed_without_blockers
                else f"Rebuild this skill: {evidence.focus}."
            ),
            "source_summary": (
                previous.get("source_summary") or ""
                if preserves_prior_metadata
                else f"Strong {evidence.attempt_type} evidence in {evidence.chapter_id}."
                if strong
                else f"Supported improvement with {evidence.focus}."
                if passed_without_blockers
                else f"Needs more support with {evidence.focus}."
            ),
        })
    return delta


__all__ = ["SchoolAttemptEvidence", "derive_school_projection_delta"]
