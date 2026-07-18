"""Provenance-first growth-report data for rebuilt School sessions.

This module deliberately treats committed School learning events as the only
source of rendered claims. Learner skill profiles are useful projections, but
they do not carry enough immutable activity and timestamp lineage to establish
a learner-facing claim on their own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any, Literal, TypedDict


SCHOOL_DOMAIN = "school"
SCHOOL_REBUILD_API_VERSION = "rebuild"
MAX_EVIDENCE_EXCERPT_LENGTH = 320
MAX_FOCUS_LENGTH = 160

SchoolGrowthReportAudience = Literal["learner", "parent"]
SchoolGrowthClaimScope = Literal["current_chapter", "historical_context"]
SchoolGrowthReportStatus = Literal["ready", "insufficient_evidence"]


class SchoolGrowthReportScope(TypedDict):
    session_id: str
    chapter_id: str


class SchoolGrowthClaim(TypedDict):
    scope: SchoolGrowthClaimScope
    message: str
    source_event_ids: list[str]
    session_id: str
    chapter_id: str
    activity_id: str
    skill_id: str
    occurred_at: str
    learner_safe_evidence_excerpt: str


class SchoolGrowthInsufficientEvidence(TypedDict):
    reason: str


class SchoolGrowthReport(TypedDict):
    audience: SchoolGrowthReportAudience
    current_scope: SchoolGrowthReportScope
    status: SchoolGrowthReportStatus
    insufficient_evidence: SchoolGrowthInsufficientEvidence | None
    current_chapter_claims: list[SchoolGrowthClaim]
    historical_context: list[SchoolGrowthClaim]


def build_school_growth_report(
    *,
    learning_events: Sequence[Mapping[str, Any]],
    school_profiles: Sequence[Mapping[str, Any]],
    school_sessions: Sequence[Mapping[str, Any]],
    current_scope: SchoolGrowthReportScope,
    audience: SchoolGrowthReportAudience,
) -> SchoolGrowthReport:
    """Build JSON-ready report data without storage or model calls.

    ``school_profiles`` is accepted with the graph inputs intentionally, but
    profile rows never establish a rendered claim. A profile can retain a
    historical latest quote for a generic skill, so using it as current-chapter
    evidence would permit the false relabeling this builder prevents.
    """

    if audience not in {"learner", "parent"}:
        raise ValueError("unsupported_school_growth_report_audience")

    session_id = _text(current_scope.get("session_id"))
    chapter_id = _text(current_scope.get("chapter_id"))
    normalized_scope: SchoolGrowthReportScope = {
        "session_id": session_id,
        "chapter_id": chapter_id,
    }
    if not session_id or not chapter_id or not _has_school_scope_session(
        school_sessions,
        session_id,
    ):
        return _insufficient_report(
            audience=audience,
            current_scope=normalized_scope,
            reason="invalid_current_scope",
        )

    # Profiles are projections, not immutable event evidence. Keeping this
    # argument in the public builder makes a future route able to pass the
    # complete learning graph without granting profile rows claim authority.
    del school_profiles

    current_claims: list[SchoolGrowthClaim] = []
    historical_claims: list[SchoolGrowthClaim] = []
    seen_claims: set[tuple[str, str]] = set()
    for raw_event in learning_events:
        if not _is_school_row(raw_event):
            continue
        for claim in _claims_from_event(
            raw_event,
            audience=audience,
            current_scope=normalized_scope,
        ):
            identity = (claim["source_event_ids"][0], claim["skill_id"])
            if identity in seen_claims:
                continue
            seen_claims.add(identity)
            if claim["scope"] == "current_chapter":
                current_claims.append(claim)
            else:
                historical_claims.append(claim)

    current_claims.sort(key=_claim_sort_key, reverse=True)
    historical_claims.sort(key=_claim_sort_key, reverse=True)
    if not current_claims:
        return {
            "audience": audience,
            "current_scope": normalized_scope,
            "status": "insufficient_evidence",
            "insufficient_evidence": {"reason": "no_current_chapter_evidence"},
            "current_chapter_claims": [],
            "historical_context": historical_claims,
        }
    return {
        "audience": audience,
        "current_scope": normalized_scope,
        "status": "ready",
        "insufficient_evidence": None,
        "current_chapter_claims": current_claims,
        "historical_context": historical_claims,
    }


def _insufficient_report(
    *,
    audience: SchoolGrowthReportAudience,
    current_scope: SchoolGrowthReportScope,
    reason: str,
) -> SchoolGrowthReport:
    return {
        "audience": audience,
        "current_scope": current_scope,
        "status": "insufficient_evidence",
        "insufficient_evidence": {"reason": reason},
        "current_chapter_claims": [],
        "historical_context": [],
    }


def _has_school_scope_session(
    school_sessions: Sequence[Mapping[str, Any]],
    session_id: str,
) -> bool:
    return any(
        _is_school_session(session)
        and _text(session.get("session_id")) == session_id
        for session in school_sessions
    )


def _is_school_session(session: Mapping[str, Any]) -> bool:
    if _text(session.get("domain")) not in {"", SCHOOL_DOMAIN}:
        return False
    api_version = _text(session.get("api_version"))
    return api_version in {"", SCHOOL_REBUILD_API_VERSION}


def _is_school_row(row: Mapping[str, Any]) -> bool:
    return _text(row.get("domain")) == SCHOOL_DOMAIN


def _claims_from_event(
    event: Mapping[str, Any],
    *,
    audience: SchoolGrowthReportAudience,
    current_scope: SchoolGrowthReportScope,
) -> list[SchoolGrowthClaim]:
    evidence = _mapping(event.get("evidence_json"))
    event_id = _text(event.get("source_event_key") or event.get("event_id"))
    session_id = _text(event.get("session_id"))
    chapter_id = _text(evidence.get("chapter_id") or event.get("chapter_id"))
    activity_id = _text(
        evidence.get("activity_id")
        or event.get("activity_id")
        or event.get("node_id")
    )
    occurred_at = _occurred_at(event.get("occurred_at"))
    excerpt = _learner_safe_excerpt(event, evidence)
    if not all((event_id, session_id, chapter_id, activity_id, occurred_at, excerpt)):
        return []

    focus = _focus(evidence, event)
    is_current = (
        session_id == current_scope["session_id"]
        and chapter_id == current_scope["chapter_id"]
    )
    claims: list[SchoolGrowthClaim] = []
    for skill_id in _skill_ids(event, evidence):
        claims.append(
            {
                "scope": "current_chapter" if is_current else "historical_context",
                "message": _message(
                    audience=audience,
                    focus=focus,
                    historical=not is_current,
                ),
                "source_event_ids": [event_id],
                "session_id": session_id,
                "chapter_id": chapter_id,
                "activity_id": activity_id,
                "skill_id": skill_id,
                "occurred_at": occurred_at,
                "learner_safe_evidence_excerpt": excerpt,
            }
        )
    return claims


def _skill_ids(
    event: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> list[str]:
    values = evidence.get("skill_ids")
    raw_skill_ids = values if isinstance(values, (list, tuple, set)) else ()
    candidates = [*raw_skill_ids, event.get("skill_id")]
    return list(
        dict.fromkeys(
            skill_id
            for value in candidates
            if (skill_id := _text(value))
        )
    )


def _learner_safe_excerpt(
    event: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> str:
    candidates: list[Any] = [
        evidence.get("learner_response_excerpt"),
        evidence.get("answer_excerpt"),
        event.get("answer_excerpt"),
    ]
    criteria = event.get("criteria_json")
    if isinstance(criteria, list):
        candidates.extend(
            criterion.get("evidence_quote")
            for criterion in criteria
            if isinstance(criterion, Mapping)
        )
    for candidate in candidates:
        excerpt = _text(candidate)
        if excerpt and excerpt.lower() not in {"(empty answer)", "empty answer"}:
            return excerpt[:MAX_EVIDENCE_EXCERPT_LENGTH]
    return ""


def _focus(evidence: Mapping[str, Any], event: Mapping[str, Any]) -> str:
    return (
        _text(evidence.get("focus") or event.get("focus"))[:MAX_FOCUS_LENGTH]
        or "the recorded skill"
    )


def _message(
    *,
    audience: SchoolGrowthReportAudience,
    focus: str,
    historical: bool,
) -> str:
    if historical:
        if audience == "parent":
            return f"Earlier evidence records work on {focus}."
        return f"Earlier, you worked on {focus}."
    if audience == "parent":
        return f"Current chapter evidence records work on {focus}."
    return f"You worked on {focus} in this chapter."


def _claim_sort_key(claim: SchoolGrowthClaim) -> tuple[str, str, str]:
    return (
        claim["occurred_at"],
        claim["source_event_ids"][0],
        claim["skill_id"],
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _occurred_at(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return _text(value)


def _text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


__all__ = [
    "SchoolGrowthClaim",
    "SchoolGrowthInsufficientEvidence",
    "SchoolGrowthReport",
    "SchoolGrowthReportAudience",
    "SchoolGrowthReportScope",
    "build_school_growth_report",
]
