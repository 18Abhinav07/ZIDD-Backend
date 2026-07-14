"""Pure learner-profile projection for one committed School attempt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.school_core.readiness import (
    AttemptEvidence,
    apply_attempt_evidence,
    apply_placement_ready_seed,
    from_profile_row,
    to_profile_upsert,
)


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
    placement_ready_skill_confidence: dict[str, float] = field(default_factory=dict)
    preserve_latest_evidence: bool = False

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
            placement_ready_skill_confidence={
                str(key): _score(value)
                for key, value in dict(
                    raw.get("placement_ready_skill_confidence") or {}
                ).items()
                if str(key)
            },
            preserve_latest_evidence=bool(raw.get("preserve_latest_evidence")),
        )


def derive_school_projection_delta(
    evidence: SchoolAttemptEvidence,
    existing_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Derive profile upserts from rows locked by the caller."""

    existing = {str(row.get("skill_id") or ""): row for row in existing_rows}
    skill_ids = list(dict.fromkeys((
        *evidence.skill_ids,
        *evidence.certified_skill_scores,
        *evidence.placement_ready_skill_confidence,
    )))
    passed_without_blockers = evidence.attempt_passed and not evidence.blockers
    effective_blockers = tuple(dict.fromkeys((
        *evidence.blockers,
        *(() if evidence.attempt_passed else ("attempt_not_passed",)),
    )))
    delta: list[dict[str, Any]] = []

    for skill_id in skill_ids:
        previous = existing.get(skill_id) or {}
        previous_attempts = int(previous.get("attempts") or 0)
        counts_as_attempt = skill_id in evidence.skill_ids
        certified_score = evidence.certified_skill_scores.get(skill_id)
        placement_seed_confidence = evidence.placement_ready_skill_confidence.get(
            skill_id
        )
        state = from_profile_row(previous, skill_id=skill_id)
        if counts_as_attempt:
            state = apply_attempt_evidence(
                state,
                AttemptEvidence(
                    attempt_type=_canonical_attempt_type(evidence.attempt_type),
                    evaluator_score=(
                        certified_score
                        if certified_score is not None
                        else evidence.score
                    ),
                    evaluator_confidence=evidence.confidence,
                    skill_ids=(skill_id,),
                    support_level=_support_level(evidence.attempt_type),
                    language_required="en"
                    if _canonical_attempt_type(evidence.attempt_type)
                    in {"independent_check", "transfer_check", "chapter_check"}
                    else None,
                    language_detected="en",
                    blockers=effective_blockers,
                ),
            )
        if placement_seed_confidence is not None:
            state = apply_placement_ready_seed(
                state,
                confidence=placement_seed_confidence,
            )
        profile_fields = to_profile_upsert(state)
        status = str(profile_fields["skill_status"])
        readiness = float(profile_fields["readiness"])
        is_strong = status in {"ready", "mastered"}
        previous_gaps = [str(value) for value in previous.get("gaps_json") or [] if str(value)]
        gap = (
            ""
            if is_strong
            else previous_gaps[0]
            if evidence.attempt_passed and previous_gaps
            else evidence.focus
        )
        previous_evidence = previous.get("evidence_json") if isinstance(previous.get("evidence_json"), dict) else {}
        state_changed = counts_as_attempt or placement_seed_confidence is not None
        preserves_prior_metadata = (
            bool(previous)
            and (not counts_as_attempt or evidence.preserve_latest_evidence)
        )
        if preserves_prior_metadata and not state_changed:
            evidence_json = dict(previous_evidence)
        elif preserves_prior_metadata:
            evidence_json = {
                **previous_evidence,
                "school_readiness_state": profile_fields["school_readiness_state"],
                "skill_status": status,
            }
        else:
            evidence_json = {
                **previous_evidence,
                "session_id": evidence.session_id,
                "chapter_id": evidence.chapter_id,
                "level_id": evidence.level_id,
                "attempt_type": evidence.attempt_type,
                "latest_quote": evidence.answer_excerpt,
                "criteria": list(evidence.criteria),
                "blockers": list(effective_blockers),
                "evaluator_score": evidence.score,
                "attempt_passed": evidence.attempt_passed,
                "school_readiness_state": profile_fields["school_readiness_state"],
                "skill_status": status,
            }
        if certified_score is not None:
            evidence_json.update({
                "latest_certification": {
                    "session_id": evidence.session_id,
                    "chapter_id": evidence.chapter_id,
                    "score": certified_score,
                },
            })
        strong = is_strong
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
            "mastery": float(profile_fields["mastery"]),
            "readiness": (
                previous.get("readiness")
                if preserves_prior_metadata and not state_changed
                else readiness
            ),
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


def _canonical_attempt_type(attempt_type: str) -> str:
    if attempt_type == "guided_check" or attempt_type.startswith("revision_level_"):
        return "guided"
    if attempt_type in {"snapshot", "targeted_diagnostic", "confirmatory"}:
        return "placement"
    if attempt_type in {
        "bridge",
        "guided",
        "placement",
        "independent_check",
        "transfer_check",
        "review_check",
        "chapter_check",
    }:
        return attempt_type
    return "guided"


def _support_level(attempt_type: str) -> str:
    canonical = _canonical_attempt_type(attempt_type)
    if canonical == "bridge":
        return "bridge"
    if canonical in {
        "independent_check",
        "transfer_check",
        "review_check",
        "chapter_check",
        "placement",
    }:
        return "independent"
    return "guided"


__all__ = ["SchoolAttemptEvidence", "derive_school_projection_delta"]
