"""Readiness report builder for the rebuilt School Prep flow."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any
from uuid import uuid4

from app.content.school_rebuild_placement_bank import placement_bank_for
from app.services import school_rebuild_placement as placement
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
    evidence_summary["track_verdicts"] = placement.public_track_verdicts(state)
    # Placement track verdicts own placement. Generic readiness EMA is useful
    # longitudinally, but it cannot turn a resolved placement track into a
    # prerequisite gap or promote an unresolved track to a confirmed gap.
    blocking_skill_ids = [
        track.primary_skill_id
        for track in state.track_states.values()
        if track.status == "confirmed_weak"
    ]
    watchlist_tracks = [
        track
        for track in state.track_states.values()
        if track.status in {"ambiguous", "provisional_weak", "unresolved"}
        and track.primary_skill_id not in blocking_skill_ids
    ]

    if effective_status == "abandoned":
        placement_status = "abandoned"
        unlock_state = "locked"
        allowed_next_actions = ["start_placement"]
        blocking_skill_ids = []
    elif effective_status == "insufficient_evidence":
        placement_status = "insufficient_evidence"
        unlock_state = "locked"
        allowed_next_actions = [
            "resume_placement"
            if placement.can_resume_placement(envelope)
            else "start_placement"
        ]
    elif effective_status == "below_target":
        placement_status = "below_target"
        unlock_state = "recap_required"
        allowed_next_actions = ["start_recap"]
    elif effective_status == "target_ready":
        placement_status = "target_ready"
        unlock_state = "target_unlocked"
        allowed_next_actions = ["start_curriculum"]
    else:
        # A forward-incompatible or malformed terminal value is not evidence
        # that a learner can begin the target class. Preserve the raw session
        # for audit, but make the public navigation fail closed.
        placement_status = "insufficient_evidence"
        unlock_state = "locked"
        allowed_next_actions = ["start_placement"]

    evaluated_class_no = _evaluated_class_no(
        state=state,
        placement_status=placement_status,
    )
    blocking_skills = _public_blocking_skills(
        blocking_skill_ids=blocking_skill_ids,
        metadata=metadata,
        events=events,
    )
    watchlist_skills = (
        []
        if placement_status in {"abandoned", "insufficient_evidence"}
        else _public_watchlist_skills(
            tracks=watchlist_tracks,
            metadata=metadata,
        )
    )
    modules = (
        []
        if placement_status in {"abandoned", "insufficient_evidence"}
        else _recommended_modules_from_tracks(
            state,
            blocking_skill_ids=blocking_skill_ids,
        )
    )
    active_learning_class_no = _active_learning_class_no(
        state=state,
        placement_status=placement_status,
        evaluated_class_no=evaluated_class_no,
    )
    deviation_note = _deviation_note(
        placement_status=placement_status,
        target_class_no=state.class_no,
        watchlist_skills=watchlist_skills,
    )
    learner_summary = _learner_summary(
        placement_status,
        evaluated_class_no,
        state.class_no,
        has_watchlist=bool(watchlist_skills),
    )
    parent_summary = _parent_summary(
        placement_status,
        evidence_summary,
        modules,
        has_watchlist=bool(watchlist_skills),
    )

    return {
        "report_id": report_id or str(uuid4()),
        "user_id": user_id,
        "profile_version_id": envelope.profile_version_id,
        "placement_session_id": placement_session_id,
        "placement_status": placement_status,
        "subject_id": state.subject_id,
        "target_class_no": state.class_no,
        "evaluated_class_no": evaluated_class_no,
        "active_learning_class_no": active_learning_class_no,
        "unlock_state": unlock_state,
        "blocking_skills": blocking_skills,
        "watchlist_skills": watchlist_skills,
        "deviation_note": deviation_note,
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
        "evaluated_class_no": _optional_class_no(row.get("evaluated_class_no")),
        "active_learning_class_no": _optional_class_no(
            row.get("active_learning_class_no")
        ),
        "unlock_state": row["unlock_state"],
        "blocking_skills": list(row.get("blocking_skills") or []),
        "watchlist_skills": list(row.get("watchlist_skills") or []),
        "deviation_note": str(
            row.get("deviation_note")
            or _deviation_note(
                placement_status=str(row.get("placement_status") or ""),
                target_class_no=int(row.get("target_class_no") or 0),
                watchlist_skills=list(row.get("watchlist_skills") or []),
            )
        ),
        "evidence_summary": dict(row.get("evidence_summary") or {}),
        "track_verdicts": list(
            (row.get("evidence_summary") or {}).get("track_verdicts") or []
        ),
        "recommended_recap_modules": [
            _public_recap_module(module)
            for module in row.get("recommended_recap_modules") or []
        ],
        "learner_summary": row.get("learner_summary") or "",
        "parent_summary": row.get("parent_summary") or "",
        "allowed_next_actions": list(row.get("allowed_next_actions") or []),
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
        if _is_clear_placement_pass(event)
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
    state: placement.PlacementSessionState,
    placement_status: str,
) -> int | None:
    if placement_status == "target_ready":
        return state.class_no

    anchor_bands = sorted(
        band
        for track in state.track_states.values()
        if track.snapshot_source_band == state.class_no
        for band in [_confirmed_highest_safe_band(track, state.class_no)]
        if band is not None
    )
    agreeing_windows = [
        anchor_bands[start:end]
        for start in range(len(anchor_bands))
        for end in range(start + 3, len(anchor_bands) + 1)
        if anchor_bands[end - 1] - anchor_bands[start] <= 1
    ]
    if not agreeing_windows:
        return None
    strongest = max(agreeing_windows, key=lambda values: (len(values), -values[0]))
    return min(strongest)


def _confirmed_highest_safe_band(
    track: placement.PlacementTrackState,
    target_class_no: int,
) -> int | None:
    if track.highest_passed_band is None:
        return None
    if track.status in {"resolved_ready", "confirmed_weak"}:
        return int(track.highest_passed_band)
    if track.status != "provisional_ready":
        return None
    clean_target_anchor = any(
        evidence.stage == "snapshot"
        and evidence.source_class_no == target_class_no
        and evidence.classification == "pass"
        and evidence.evaluator_score >= 0.85
        and evidence.evaluator_confidence >= 0.85
        and not evidence.certifying_blockers
        for evidence in track.evidence
    )
    return int(track.highest_passed_band) if clean_target_anchor else None


def _active_learning_class_no(
    *,
    state: placement.PlacementSessionState,
    placement_status: str,
    evaluated_class_no: int | None,
) -> int | None:
    if placement_status in {"abandoned", "insufficient_evidence"}:
        return None
    if placement_status == "target_ready":
        return state.class_no
    confirmed_bands = [
        int(track.boundary_band)
        for track in state.track_states.values()
        if track.status == "confirmed_weak" and track.boundary_band is not None
    ]
    return evaluated_class_no if evaluated_class_no is not None else min(confirmed_bands)


def _optional_class_no(value: Any) -> int | None:
    return int(value) if value is not None else None


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
        passes = sum(
            1
            for event in attempts
            if _is_clear_placement_pass(event)
        )
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


def _is_clear_placement_pass(event: dict[str, Any]) -> bool:
    blockers = event.get("blockers") or ()
    if isinstance(blockers, (list, tuple, set)):
        certifying_blockers = tuple(str(blocker) for blocker in blockers)
    else:
        certifying_blockers = (str(blockers),)
    return placement.classify_placement_evidence(
        evaluator_score=float(event.get("score") or 0.0),
        evaluator_confidence=float(event.get("confidence") or 0.0),
        scorable=bool(event.get("scorable", True)),
        certifying_blockers=certifying_blockers,
    ) == "pass"


def _public_watchlist_skills(
    *,
    tracks: list[placement.PlacementTrackState],
    metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for track in tracks:
        info = metadata.get(track.primary_skill_id, {})
        label = info.get("learner_skill_label") or track.learner_skill_label
        source_class_no = int(
            track.boundary_band
            if track.boundary_band is not None
            else track.highest_passed_band
            if track.highest_passed_band is not None
            else info.get("source_class_no") or 2
        )
        key = (str(label), source_class_no)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "label": str(label),
                "source_class_no": source_class_no,
                "status": "needs_confirmation",
            }
        )
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
        if track.status == "confirmed_weak"
        and track.primary_skill_id in blocking_skill_ids
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


def _learner_summary(
    placement_status: str,
    evaluated_class_no: int | None,
    target_class_no: int,
    *,
    has_watchlist: bool,
) -> str:
    if placement_status == "target_ready":
        if has_watchlist:
            return (
                f"You can begin Class {target_class_no} now. We will keep a few "
                "skills in view and check them again during lessons."
            )
        return "You are ready to begin your target class chapters."
    if placement_status == "abandoned":
        return "Your readiness check stopped before a starting point was decided."
    if placement_status == "insufficient_evidence":
        return "We need a few more answers before deciding your starting point."
    if evaluated_class_no is None:
        return (
            "We will first rebuild the confirmed foundations, "
            f"then move you toward Class {target_class_no} English."
        )
    return (
        f"We will first build your Class {evaluated_class_no} foundations, "
        f"then move you toward Class {target_class_no} English."
    )


def _parent_summary(
    placement_status: str,
    evidence_summary: dict[str, Any],
    modules: list[dict[str, Any]],
    *,
    has_watchlist: bool,
) -> str:
    if placement_status == "target_ready":
        if has_watchlist:
            return (
                "No prerequisite gap was confirmed, so target-class teaching can "
                "begin now. Zidd will recheck the listed watchlist skills during lessons."
            )
        return "Placement evidence shows the learner can start target-class work."
    if placement_status == "abandoned":
        return "The readiness check ended before enough evidence was collected to set a learning path."
    if placement_status == "insufficient_evidence":
        return "The diagnostic was not long enough to make a reliable placement decision."
    return (
        f"Across {evidence_summary['total_attempts']} placement checks, Zidd found "
        f"{len(modules)} foundation areas to rebuild before regular chapter teaching."
    )


def _deviation_note(
    *,
    placement_status: str,
    target_class_no: int,
    watchlist_skills: list[dict[str, Any]],
) -> str:
    if placement_status != "target_ready" or not watchlist_skills:
        return ""
    return (
        f"Class {target_class_no} is open now. Zidd did not confirm every skill "
        "in this short check, so the watchlist will be checked again during lessons."
    )


def _reason_for_label(label: str) -> str:
    clean = label.rstrip(".")
    return f"Placement answers showed that '{clean}' needs rebuilding before class chapters."


def _label_from_skill_id(skill_id: str) -> str:
    return skill_id.split(".")[-1].replace("_", " ").title()


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")[:48]
