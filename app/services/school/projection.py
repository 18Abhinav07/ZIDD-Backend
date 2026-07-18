"""Pure learner-profile projection for one committed School attempt."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from app.services.school_core.readiness import (
    AttemptEvidence,
    apply_attempt_evidence,
    apply_placement_ready_seed,
    from_profile_row,
    to_profile_upsert,
)


_RECONCILIATION_CERTIFICATION_LEDGER_KEY = "reconciliation_certification_ledger"
_RECONCILIATION_CERTIFICATION_LEDGER_LIMIT = 64


def _score(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def _certification_identity(
    *,
    session_id: str,
    chapter_id: str,
    score: float,
) -> dict[str, str | float]:
    return {
        "session_id": session_id,
        "chapter_id": chapter_id,
        "score": _score(score),
    }


def _certification_identity_key(*, session_id: str, chapter_id: str) -> str:
    return f"{session_id}:{chapter_id}"


def _reconciliation_certification_ledger(
    evidence_json: dict[str, Any],
    identity: dict[str, str | float],
) -> dict[str, dict[str, str | float]]:
    raw_ledger = evidence_json.get(_RECONCILIATION_CERTIFICATION_LEDGER_KEY)
    ledger = {
        str(key): {
            "session_id": str(value.get("session_id") or ""),
            "chapter_id": str(value.get("chapter_id") or ""),
            "score": _score(value.get("score")),
        }
        for key, value in (raw_ledger.items() if isinstance(raw_ledger, dict) else [])
        if isinstance(value, dict)
        and str(value.get("session_id") or "")
        and str(value.get("chapter_id") or "")
    }
    key = _certification_identity_key(
        session_id=str(identity["session_id"]),
        chapter_id=str(identity["chapter_id"]),
    )
    ledger.pop(key, None)
    ledger[key] = identity
    while len(ledger) > _RECONCILIATION_CERTIFICATION_LEDGER_LIMIT:
        ledger.pop(next(iter(ledger)))
    return ledger


def enrich_school_projection_evidence(
    raw: dict[str, Any],
    *,
    learning_event: dict[str, Any],
    user_id: str,
    session_id: str,
    activity_id: str | None,
    answer_hash: str | None,
) -> dict[str, Any]:
    """Join the profile projection to the immutable committed-event identity."""

    event_evidence = (
        learning_event.get("evidence_json")
        if isinstance(learning_event.get("evidence_json"), dict)
        else {}
    )
    event_identity = str(learning_event.get("source_event_key") or "")
    identity_material = {
        "user_id": str(user_id),
        "session_id": str(session_id),
        "activity_id": str(activity_id or ""),
        "answer_hash": str(answer_hash or ""),
        "task_type": str(learning_event.get("task_type") or raw.get("task_type") or ""),
        "event_identity": event_identity,
    }
    request_identity_hash = hashlib.sha256(
        json.dumps(
            identity_material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    explicit_support = list(raw.get("support_used") or [])
    support_mode = str(event_evidence.get("support_mode") or "").strip()
    if support_mode and support_mode not in explicit_support:
        explicit_support.append(support_mode)
    return {
        **raw,
        "event_identity": event_identity,
        "request_identity_hash": request_identity_hash,
        "misconception_tags": list(
            raw.get("misconception_tags")
            or event_evidence.get("misconception_tags")
            or []
        ),
        "support_used": explicit_support,
        "language_detected": (
            raw.get("language_detected")
            or event_evidence.get("language_detected")
        ),
    }


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
    event_identity: str = ""
    request_identity_hash: str = ""
    misconception_tags: tuple[str, ...] = ()
    support_used: tuple[str, ...] = ()
    language_detected: str | None = None
    certified_skill_scores: dict[str, float] = field(default_factory=dict)
    placement_ready_skill_confidence: dict[str, float] = field(default_factory=dict)
    preserve_latest_evidence: bool = False
    reconciliation_certification: bool = False

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
            event_identity=str(
                raw.get("event_identity")
                or raw.get("source_event_key")
                or ""
            ),
            request_identity_hash=str(raw.get("request_identity_hash") or ""),
            misconception_tags=tuple(
                dict.fromkeys(
                    str(value)
                    for value in raw.get("misconception_tags") or []
                    if str(value)
                )
            ),
            support_used=tuple(
                dict.fromkeys(
                    str(value)
                    for value in raw.get("support_used") or []
                    if str(value)
                )
            ),
            language_detected=(
                str(raw.get("language_detected") or "").strip() or None
            ),
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
            reconciliation_certification=bool(raw.get("reconciliation_certification")),
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
                    language_detected=evidence.language_detected,
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
                "misconception_tags": list(evidence.misconception_tags),
                "blockers": list(effective_blockers),
                "support_used": list(evidence.support_used),
                "language_detected": evidence.language_detected,
                "event_identity": evidence.event_identity,
                "request_identity_hash": evidence.request_identity_hash,
                "evaluator_score": evidence.score,
                "attempt_passed": evidence.attempt_passed,
                "school_readiness_state": profile_fields["school_readiness_state"],
                "skill_status": status,
            }
        if certified_score is not None:
            certification = _certification_identity(
                session_id=evidence.session_id,
                chapter_id=evidence.chapter_id,
                score=certified_score,
            )
            if evidence.reconciliation_certification:
                evidence_json[_RECONCILIATION_CERTIFICATION_LEDGER_KEY] = (
                    _reconciliation_certification_ledger(
                        previous_evidence,
                        certification,
                    )
                )
                previous_latest = previous_evidence.get("latest_certification")
                if not isinstance(previous_latest, dict) or previous_latest == certification:
                    evidence_json["latest_certification"] = certification
            else:
                evidence_json["latest_certification"] = certification
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
    v2_attempt_types = {
        "v2_independent_application": "independent_check",
        "v2_transfer": "transfer_check",
        "v2_review": "review_check",
        "v2_support": "bridge",
    }
    if attempt_type in v2_attempt_types:
        return v2_attempt_types[attempt_type]
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


__all__ = [
    "SchoolAttemptEvidence",
    "derive_school_projection_delta",
    "enrich_school_projection_evidence",
]
