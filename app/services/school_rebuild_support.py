"""Public read contract for parent-backed and linked School support plans."""

from __future__ import annotations

from typing import Any

from app.services.school_rebuild_profile import school_coach_identity


SUPPORT_PARENT_FLOWS = frozenset({"curriculum", "recap", "readiness"})
SUPPORT_PLAN_STATUSES = frozenset({"needs_support", "capped_support"})


def parent_support_plan(
    session_row: dict[str, Any],
) -> tuple[str, dict[str, Any]] | None:
    flow_type = str(session_row.get("flow_type") or "")
    if flow_type not in SUPPORT_PARENT_FLOWS:
        return None
    state = session_row.get("state_json")
    if not isinstance(state, dict):
        return None
    status = str(
        state.get("phase")
        if flow_type == "curriculum"
        else state.get("status") or session_row.get("status") or ""
    )
    support_required = state.get("support_required")
    if status not in SUPPORT_PLAN_STATUSES or not isinstance(
        support_required,
        dict,
    ):
        return None
    return status, support_required


def public_support_response(
    session_row: dict[str, Any],
    *,
    parent_session: dict[str, Any],
) -> dict[str, Any]:
    state = dict(session_row.get("state_json") or {})
    flow_type = str(session_row.get("flow_type") or "")
    if flow_type == "support":
        status = str(state.get("status") or session_row.get("status") or "")
        details = state
    else:
        parent_plan = parent_support_plan(session_row)
        if parent_plan is None or str(parent_session.get("session_id")) != str(
            session_row.get("session_id")
        ):
            raise ValueError("school_support_parent_state_invalid")
        status, details = parent_plan
    cap = details.get("cap")
    history = details.get("history")
    return {
        "session_id": str(session_row["session_id"]),
        "flow_type": "support",
        "status": status,
        "profile_version_id": str(session_row.get("profile_version_id") or ""),
        "source_placement_report_id": (
            str(session_row["source_placement_report_id"])
            if session_row.get("source_placement_report_id")
            else None
        ),
        "parent_session_id": str(parent_session["session_id"]),
        "parent_flow_type": str(parent_session.get("flow_type") or ""),
        "subject_id": str(session_row.get("subject_id") or ""),
        "target_class_no": int(session_row.get("class_no") or 0),
        **school_coach_identity(state),
        "reason": str(details.get("reason") or "support_required"),
        "focus": str(details.get("focus") or ""),
        "cap": dict(cap) if isinstance(cap, dict) else {},
        "history": list(history) if isinstance(history, list) else [],
    }


__all__ = [
    "SUPPORT_PARENT_FLOWS",
    "parent_support_plan",
    "public_support_response",
]
