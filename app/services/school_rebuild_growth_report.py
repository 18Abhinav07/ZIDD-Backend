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
SCHOOL_REBUILD_TASK_TYPES = frozenset(
    {
        "school_rebuild_curriculum",
        "school_rebuild_masterclass",
        "school_rebuild_placement",
        "school_rebuild_recap",
    }
)
SAFE_EVIDENCE_LABEL = "recorded_learning_activity"

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
    skill_ids: list[str]
    occurred_at: str
    evidence_label: str
    evidence_count: int


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
    normalized_scope = _canonical_current_scope(school_sessions, session_id)
    if normalized_scope is None:
        return _insufficient_report(
            audience=audience,
            current_scope={"session_id": session_id, "chapter_id": ""},
            reason="invalid_current_scope",
        )

    # Profiles are projections, not immutable event evidence. Keeping this
    # argument in the public builder makes a future route able to pass the
    # complete learning graph without granting profile rows claim authority.
    del school_profiles

    current_claims: list[SchoolGrowthClaim] = []
    historical_claims: list[SchoolGrowthClaim] = []
    valid_session_ids = _valid_school_session_ids(school_sessions)
    seen_event_ids: set[str] = set()
    for raw_event in learning_events:
        if not _is_school_rebuild_event(raw_event):
            continue
        if _text(raw_event.get("session_id")) not in valid_session_ids:
            continue
        claim = _claim_from_event(
            raw_event,
            audience=audience,
            current_scope=normalized_scope,
        )
        if claim is None:
            continue
        event_id = claim["source_event_ids"][0]
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)
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


def _canonical_current_scope(
    school_sessions: Sequence[Mapping[str, Any]],
    session_id: str,
) -> SchoolGrowthReportScope | None:
    for session in school_sessions:
        if (
            not _is_school_session(session)
            or _text(session.get("session_id")) != session_id
            or _text(session.get("flow_type")) != "curriculum"
        ):
            continue
        state = _mapping(session.get("state_json"))
        chapter = _mapping(state.get("chapter"))
        chapter_id = _text(chapter.get("chapter_id"))
        if chapter_id:
            return {"session_id": session_id, "chapter_id": chapter_id}
    return None


def _valid_school_session_ids(
    school_sessions: Sequence[Mapping[str, Any]],
) -> set[str]:
    return {
        session_id
        for session in school_sessions
        if _is_school_session(session)
        if (session_id := _text(session.get("session_id")))
    }


def _is_school_session(session: Mapping[str, Any]) -> bool:
    return (
        _text(session.get("domain")) == SCHOOL_DOMAIN
        and _text(session.get("api_version")) == SCHOOL_REBUILD_API_VERSION
    )


def _is_school_rebuild_event(event: Mapping[str, Any]) -> bool:
    return (
        _text(event.get("domain")) == SCHOOL_DOMAIN
        and _text(event.get("task_type")) in SCHOOL_REBUILD_TASK_TYPES
    )


def _claim_from_event(
    event: Mapping[str, Any],
    *,
    audience: SchoolGrowthReportAudience,
    current_scope: SchoolGrowthReportScope,
) -> SchoolGrowthClaim | None:
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
    skill_ids = _skill_ids(event, evidence)
    if not all((event_id, session_id, chapter_id, activity_id, occurred_at, skill_ids)):
        return None

    is_current = (
        session_id == current_scope["session_id"]
        and chapter_id == current_scope["chapter_id"]
    )
    return {
        "scope": "current_chapter" if is_current else "historical_context",
        "message": _message(audience=audience, historical=not is_current),
        "source_event_ids": [event_id],
        "session_id": session_id,
        "chapter_id": chapter_id,
        "activity_id": activity_id,
        "skill_ids": skill_ids,
        "occurred_at": occurred_at,
        "evidence_label": SAFE_EVIDENCE_LABEL,
        "evidence_count": 1,
    }


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


def _message(
    *,
    audience: SchoolGrowthReportAudience,
    historical: bool,
) -> str:
    if historical:
        if audience == "parent":
            return "Earlier evidence records one learning activity."
        return "Earlier, you completed one learning activity."
    if audience == "parent":
        return "Current chapter evidence records one learning activity."
    return "You completed one learning activity in this chapter."


def _claim_sort_key(claim: SchoolGrowthClaim) -> tuple[str, str]:
    return (
        claim["occurred_at"],
        claim["source_event_ids"][0],
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
