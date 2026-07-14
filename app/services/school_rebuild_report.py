"""Readiness report builder for the rebuilt School Prep flow."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any
from uuid import uuid4

from app.content.school_rebuild_placement_bank import placement_bank_for
from app.services import school_rebuild_placement as placement
from app.services.school_core.readiness import classify_skill_status
from app.services.school_rebuild_profile import school_coach_identity


def build_placement_report(
    *,
    user_id: str,
    placement_session_id: str,
    placement_row: dict[str, Any],
    learning_events: list[dict[str, Any]],
    report_id: str | None = None,
) -> dict[str, Any]:
    envelope = placement.envelope_from_json(placement_row.get("state_json") or {})
    state = envelope.state
    effective_status = placement.placement_status(envelope)
    metadata = _skill_metadata(state.subject_id, state.class_no)
    events = _placement_events(learning_events, placement_session_id)
    evidence_summary = _evidence_summary(events, len(state.answered_item_ids))
    skill_statuses = {
        skill_id: classify_skill_status(skill_state)
        for skill_id, skill_state in sorted(state.skill_states.items())
    }
    blocking_skill_ids = [
        skill_id for skill_id, status in skill_statuses.items() if status == "weak"
    ]

    if effective_status == "abandoned":
        placement_status = "abandoned"
        unlock_state = "locked"
        allowed_next_actions = ["start_placement"]
        blocking_skill_ids = []
    elif effective_status == "insufficient_evidence":
        placement_status = "insufficient_evidence"
        unlock_state = "locked"
        allowed_next_actions = ["resume_placement"]
    elif blocking_skill_ids:
        placement_status = "below_target"
        unlock_state = "recap_required"
        allowed_next_actions = ["start_recap"]
    else:
        placement_status = "target_ready"
        unlock_state = "target_unlocked"
        allowed_next_actions = ["start_curriculum"]

    evaluated_class_no = (
        state.class_no
        if placement_status == "abandoned"
        else _evaluated_class_no(
            target_class_no=state.class_no,
            blocking_skill_ids=blocking_skill_ids,
            metadata=metadata,
            placement_status=placement_status,
        )
    )
    blocking_skills = _public_blocking_skills(
        blocking_skill_ids=blocking_skill_ids,
        metadata=metadata,
        events=events,
    )
    modules = (
        []
        if placement_status in {"abandoned", "insufficient_evidence"}
        else _recommended_modules_from_tracks(
            state,
            blocking_skill_ids=blocking_skill_ids,
        )
    )
    learner_summary = _learner_summary(placement_status, evaluated_class_no, state.class_no)
    parent_summary = _parent_summary(placement_status, evidence_summary, modules)

    return {
        "report_id": report_id or str(uuid4()),
        "user_id": user_id,
        "profile_version_id": envelope.profile_version_id,
        "placement_session_id": placement_session_id,
        "placement_status": placement_status,
        "subject_id": state.subject_id,
        "target_class_no": state.class_no,
        "evaluated_class_no": evaluated_class_no,
        "active_learning_class_no": evaluated_class_no,
        "unlock_state": unlock_state,
        "blocking_skills": blocking_skills,
        "watchlist_skills": [],
        "evidence_summary": evidence_summary,
        "recommended_recap_modules": modules,
        "learner_summary": learner_summary,
        "parent_summary": parent_summary,
        "allowed_next_actions": allowed_next_actions,
    }


def public_placement_report(
    row: dict[str, Any],
    *,
    coach_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "report_id": str(row["report_id"]),
        **school_coach_identity(coach_source or row),
        "placement_session_id": str(row["placement_session_id"]),
        "profile_version_id": str(row.get("profile_version_id") or ""),
        "placement_status": row["placement_status"],
        "subject_id": row["subject_id"],
        "target_class_no": int(row["target_class_no"]),
        "evaluated_class_no": int(row["evaluated_class_no"]),
        "active_learning_class_no": int(row["active_learning_class_no"]),
        "unlock_state": row["unlock_state"],
        "blocking_skills": list(row.get("blocking_skills") or []),
        "watchlist_skills": list(row.get("watchlist_skills") or []),
        "evidence_summary": dict(row.get("evidence_summary") or {}),
        "recommended_recap_modules": [
            _public_recap_module(module)
            for module in row.get("recommended_recap_modules") or []
        ],
        "learner_summary": row.get("learner_summary") or "",
        "parent_summary": row.get("parent_summary") or "",
    }


def _placement_events(
    learning_events: list[dict[str, Any]],
    placement_session_id: str,
) -> list[dict[str, Any]]:
    return [
        event
        for event in learning_events
        if str(event.get("session_id") or "") == str(placement_session_id)
        and event.get("task_type") == "school_rebuild_placement"
    ]


def _evidence_summary(events: list[dict[str, Any]], fallback_total: int) -> dict[str, Any]:
    unique_events: dict[str, dict[str, Any]] = {}
    for event in events:
        key = str(event.get("node_id") or event.get("source_event_key") or len(unique_events))
        unique_events[key] = event
    rows = list(unique_events.values())
    stage_counts = Counter(str(event.get("attempt_type") or "unknown") for event in rows)
    total = len(rows) if rows else int(fallback_total)
    correct = sum(
        1
        for event in rows
        if float(event.get("score") or 0.0) >= 0.8
        and not event.get("blockers")
    )
    return {
        "total_attempts": total,
        "correct_attempts": correct,
        "incorrect_attempts": max(0, total - correct),
        "stage_counts": dict(stage_counts),
        "scoring_source": "committed_learning_events" if rows else "placement_session_state",
    }


def _skill_metadata(subject_id: str, target_class_no: int) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for item in placement_bank_for(subject_id, target_class_no):
        for skill_id in item.skill_ids:
            current = metadata.setdefault(
                skill_id,
                {
                    "learner_skill_label": item.learner_skill_label,
                    "source_class_no": item.source_class_no,
                    "misconception_tags": set(),
                },
            )
            current["source_class_no"] = min(int(current["source_class_no"]), item.source_class_no)
            current["misconception_tags"].update(item.misconception_tags)
    return {
        skill_id: {
            **value,
            "misconception_tags": sorted(value["misconception_tags"]),
        }
        for skill_id, value in metadata.items()
    }


def _evaluated_class_no(
    *,
    target_class_no: int,
    blocking_skill_ids: list[str],
    metadata: dict[str, dict[str, Any]],
    placement_status: str,
) -> int:
    if placement_status == "target_ready":
        return target_class_no
    source_classes = [
        int(metadata.get(skill_id, {}).get("source_class_no") or target_class_no)
        for skill_id in blocking_skill_ids
    ]
    if not source_classes:
        return max(2, target_class_no - 1)
    return max(2, min(source_classes))


def _public_blocking_skills(
    *,
    blocking_skill_ids: list[str],
    metadata: dict[str, dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attempts_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        attempts_by_skill[str(event.get("skill_id") or "")].append(event)
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for skill_id in blocking_skill_ids:
        info = metadata.get(skill_id, {})
        attempts = attempts_by_skill.get(skill_id) or []
        passes = sum(1 for event in attempts if float(event.get("score") or 0.0) >= 0.8)
        label = info.get("learner_skill_label") or _label_from_skill_id(skill_id)
        source_class_no = int(info.get("source_class_no") or 2)
        key = (label, source_class_no)
        row = merged.setdefault(
            key,
            {
                "label": label,
                "source_class_no": source_class_no,
                "status": "needs_recap",
                "attempts": 0,
                "correct_attempts": 0,
                "learner_reason": _reason_for_label(label),
            },
        )
        row["attempts"] += len(attempts)
        row["correct_attempts"] += passes
    rows = list(merged.values())
    rows.sort(key=lambda row: (row["source_class_no"], row["label"]))
    return rows


def _recommended_modules_from_tracks(
    state: placement.PlacementSessionState,
    *,
    blocking_skill_ids: list[str],
) -> list[dict[str, Any]]:
    modules = []
    weak_tracks = [
        track
        for track in state.track_states.values()
        if track.primary_skill_id in blocking_skill_ids
    ]
    weak_tracks.sort(
        key=lambda track: (
            track.highest_passed_band
            if track.highest_passed_band is not None
            else state.class_no,
            track.learner_skill_label,
        )
    )
    for index, track in enumerate(weak_tracks, start=1):
        label = track.learner_skill_label
        source_class_no = int(
            track.highest_passed_band
            if track.highest_passed_band is not None
            else track.boundary_band
            if track.boundary_band is not None
            else max(1, state.class_no - 1)
        )
        modules.append(
            {
                "module_id": f"recap_{index}_{_slug(label)}",
                "title": f"Recap: {label}",
                "source_class_no": source_class_no,
                "target_class_no": state.class_no,
                "focus": label,
                "why_this_is_first": _reason_for_label(label),
                "estimated_minutes": 8,
                "status": "locked_until_started",
                "placement_track_id": track.track_id,
                "primary_skill_id": track.primary_skill_id,
            }
        )
    return modules


def _public_recap_module(module: dict[str, Any]) -> dict[str, Any]:
    return {
        key: module[key]
        for key in (
            "module_id",
            "title",
            "source_class_no",
            "focus",
            "why_this_is_first",
            "estimated_minutes",
            "status",
        )
        if key in module
    }


def _learner_summary(placement_status: str, evaluated_class_no: int, target_class_no: int) -> str:
    if placement_status == "target_ready":
        return "You are ready to begin your target class chapters."
    if placement_status == "abandoned":
        return "Your readiness check stopped before a starting point was decided."
    if placement_status == "insufficient_evidence":
        return "We need a few more answers before deciding your starting point."
    return (
        f"We will first build your Class {evaluated_class_no} foundations, "
        f"then move you toward Class {target_class_no} English."
    )


def _parent_summary(
    placement_status: str,
    evidence_summary: dict[str, Any],
    modules: list[dict[str, Any]],
) -> str:
    if placement_status == "target_ready":
        return "Placement evidence shows the learner can start target-class work."
    if placement_status == "abandoned":
        return "The readiness check ended before enough evidence was collected to set a learning path."
    if placement_status == "insufficient_evidence":
        return "The diagnostic was not long enough to make a reliable placement decision."
    return (
        f"Across {evidence_summary['total_attempts']} placement checks, Zidd found "
        f"{len(modules)} foundation areas to rebuild before regular chapter teaching."
    )


def _reason_for_label(label: str) -> str:
    clean = label.rstrip(".")
    return f"Placement answers showed that '{clean}' needs rebuilding before class chapters."


def _label_from_skill_id(skill_id: str) -> str:
    return skill_id.split(".")[-1].replace("_", " ").title()


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")[:48]
