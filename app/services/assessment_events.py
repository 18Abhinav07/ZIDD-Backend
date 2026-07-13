"""Typed event ledger helpers for scored assessment simulations."""
from __future__ import annotations

from typing import Any


def ensure_assessment_runtime(state: dict[str, Any]) -> None:
    state.setdefault("assessment_events", [])
    state.setdefault("visible_event_ledger", [])
    state.setdefault("assessment_validity_flags", [])
    state.setdefault("floor_handoff_queue", [])
    state.setdefault("simulation_segments", [])


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
    event = {
        "event_id": f"assess_{len(events) + 1}",
        "event_type": event_type,
        "task_type": task_type,
        "speaker_id": speaker_id,
        "scorable": bool(scorable),
        "analysis": dict(analysis or {}),
        "content": content,
        "validity_flags": list(validity_flags or []),
    }
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
        "event_id": f"seg_{len(ledger) + 1}",
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
