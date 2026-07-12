"""Typed event ledger helpers for scored assessment simulations."""
from __future__ import annotations

from typing import Any


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _highest_event_sequence(events: Any, prefix: str) -> int:
    highest = 0
    for event in events or []:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("event_id") or "")
        if not event_id.startswith(prefix):
            continue
        suffix = event_id[len(prefix):]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return highest


def ensure_assessment_runtime(state: dict[str, Any]) -> None:
    state.setdefault("assessment_events", [])
    state.setdefault("visible_event_ledger", [])
    state.setdefault("assessment_validity_flags", [])
    state.setdefault("floor_handoff_queue", [])
    state.setdefault("simulation_segments", [])
    state["assessment_event_sequence"] = max(
        _nonnegative_int(state.get("assessment_event_sequence")),
        _highest_event_sequence(state["assessment_events"], "assess_"),
    )
    state["visible_event_sequence"] = max(
        _nonnegative_int(state.get("visible_event_sequence")),
        _highest_event_sequence(state["visible_event_ledger"], "seg_"),
        _highest_event_sequence(state["simulation_segments"], "seg_"),
    )


def _next_event_id(state: dict[str, Any], counter_key: str, prefix: str) -> str:
    ensure_assessment_runtime(state)
    sequence = _nonnegative_int(state.get(counter_key)) + 1
    state[counter_key] = sequence
    return f"{prefix}{sequence}"


def next_visible_event_id(state: dict[str, Any]) -> str:
    return _next_event_id(state, "visible_event_sequence", "seg_")


def append_validity_flag(
    state: dict[str, Any],
    code: str,
    message: str,
    *,
    severity: str = "partial",
    speaker_id: str | None = None,
    target_speaker_id: str | None = None,
) -> dict[str, Any]:
    ensure_assessment_runtime(state)
    flag: dict[str, Any] = {
        "code": code,
        "message": message,
        "severity": severity,
    }
    if speaker_id:
        flag["speaker_id"] = speaker_id
    if target_speaker_id:
        flag["target_speaker_id"] = target_speaker_id
    flags = list(state.get("assessment_validity_flags") or [])
    if not any(
        item.get("code") == flag["code"]
        and item.get("message") == flag["message"]
        and item.get("speaker_id") == flag.get("speaker_id")
        and item.get("target_speaker_id") == flag.get("target_speaker_id")
        for item in flags
        if isinstance(item, dict)
    ):
        flags.append(flag)
    state["assessment_validity_flags"] = flags[-30:]
    return flag


def append_assessment_event(
    state: dict[str, Any],
    *,
    event_type: str,
    task_type: str,
    speaker_id: str = "",
    scorable: bool = True,
    analysis: dict[str, Any] | None = None,
    content: str = "",
    validity_flags: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ensure_assessment_runtime(state)
    events = list(state.get("assessment_events") or [])
    latest_user = next((
        message
        for message in reversed(state.get("messages") or [])
        if isinstance(message, dict) and message.get("role") == "user"
    ), {})
    event = {
        "event_id": _next_event_id(state, "assessment_event_sequence", "assess_"),
        "event_type": event_type,
        "task_type": task_type,
        "speaker_id": speaker_id,
        "scorable": bool(scorable),
        "analysis": dict(analysis or {}),
        "content": content,
        "validity_flags": list(validity_flags or []),
    }
    learner_turn_id = str(
        latest_user.get("turn_id")
        or latest_user.get("client_turn_id")
        or latest_user.get("message_id")
        or ""
    ).strip()
    if learner_turn_id:
        event["learner_turn_id"] = learner_turn_id
    events.append(event)
    state["assessment_events"] = events[-100:]
    return event


def append_visible_event(
    state: dict[str, Any],
    *,
    speaker_id: str,
    speaker_name: str,
    content: str,
    kind: str = "simulation_segment",
) -> dict[str, Any]:
    ensure_assessment_runtime(state)
    ledger = list(state.get("visible_event_ledger") or [])
    segment = {
        "event_id": next_visible_event_id(state),
        "role": "assistant",
        "kind": kind,
        "speaker_id": speaker_id,
        "speaker_name": speaker_name,
        "content": content,
    }
    ledger.append(segment)
    state["visible_event_ledger"] = ledger[-100:]
    state["simulation_segments"] = [*(state.get("simulation_segments") or []), segment][-100:]
    return segment
