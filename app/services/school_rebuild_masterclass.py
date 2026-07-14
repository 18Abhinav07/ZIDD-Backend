"""Linked focused-practice session for a paused School curriculum level."""

from __future__ import annotations

from typing import Any

from app.services import school_rebuild_curriculum as curriculum


ENGINE_VERSION = "school-rebuild-masterclass-1"


def new_masterclass_state(
    *,
    curriculum_session_id: str,
    curriculum_state: dict[str, Any],
) -> dict[str, Any]:
    interrupt = curriculum_state.get("active_interrupt")
    if (
        curriculum_state.get("status") != "paused_for_masterclass"
        or curriculum_state.get("phase") != "paused_for_masterclass"
        or not isinstance(interrupt, dict)
    ):
        raise ValueError("curriculum_not_paused_for_masterclass")
    level_id = str(interrupt.get("level_id") or "")
    level = next(
        (
            candidate
            for candidate in curriculum_state.get("levels") or []
            if str(candidate.get("level_id") or "") == level_id
        ),
        None,
    )
    if not isinstance(level, dict):
        raise ValueError("masterclass_level_not_found")
    check = dict((level.get("checks") or {}).get("masterclass") or {})
    if not check or not (
        check.get("accepted_answers")
        or check.get("answer_rule") == "concept_slots"
    ):
        raise ValueError("masterclass_deterministic_content_required")
    return {
        "engine_version": ENGINE_VERSION,
        "status": "active",
        "curriculum_session_id": curriculum_session_id,
        "chapter_id": str(
            (curriculum_state.get("chapter") or {}).get("chapter_id") or ""
        ),
        "interrupt_id": str(interrupt.get("interrupt_id") or ""),
        "level_id": level_id,
        "focus": str(level.get("focus") or ""),
        "skill_ids": list(level.get("skill_ids") or []),
        "trigger_count": int(interrupt.get("trigger_count") or 0),
        "check": check,
        "attempts": [],
        "last_feedback": None,
    }


def current_activity(state: dict[str, Any]) -> dict[str, Any] | None:
    if state.get("status") != "active":
        return None
    attempts = list(state.get("attempts") or [])
    attempt_no = len(attempts) + 1
    check = dict(state.get("check") or {})
    if not check:
        raise ValueError("masterclass_content_not_authored")
    return {
        **check,
        "activity_id": f"{state['interrupt_id']}:attempt:{attempt_no}",
        "kind": "masterclass",
        "level_id": state["level_id"],
        "focus": state["focus"],
        "skill_ids": list(state.get("skill_ids") or []),
        "chapter_id": str(state.get("chapter_id") or ""),
        "title": f"Focused practice: {state['focus']}",
        "attempt_no": attempt_no,
        "can_answer": True,
    }


def apply_masterclass_answer(
    state: dict[str, Any],
    *,
    activity_id: str,
    answer: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    activity = current_activity(state)
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_masterclass_activity")
    answer_evaluation = curriculum.evaluate_deterministic_answer(activity, answer)
    correct = bool(answer_evaluation["correct"])
    attempt = {
        "activity_id": activity_id,
        "attempt_no": int(activity["attempt_no"]),
        "answer": answer,
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
    }
    updated = {
        **state,
        "attempts": list(state.get("attempts") or []) + [attempt],
        "status": "complete" if correct else "active",
        "last_feedback": {
            "activity_id": activity_id,
            "correct": correct,
            "message": (
                "Good. You rebuilt the skill. Return to the chapter and show it independently."
                if correct
                else "Not yet. Use the teaching clue, then try this focused example again."
            ),
        },
    }
    return updated, {
        "activity_id": activity_id,
        "kind": "masterclass",
        "level_id": state["level_id"],
        "focus": state["focus"],
        "skill_ids": list(state.get("skill_ids") or []),
        "chapter_id": str(state.get("chapter_id") or ""),
        "attempt_no": int(activity["attempt_no"]),
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
        "misconception_tags": list(answer_evaluation["misconception_tags"]),
        "language_detected": answer_evaluation["language_detected"],
    }


def public_masterclass_response(session_row: dict[str, Any]) -> dict[str, Any]:
    state = dict(session_row.get("state_json") or {})
    activity = current_activity(state)
    return {
        "session_id": str(session_row["session_id"]),
        "flow_type": "masterclass",
        "status": state.get("status") or session_row.get("status"),
        "linked_curriculum_session_id": str(
            state.get("curriculum_session_id")
            or session_row.get("linked_session_id")
            or ""
        ),
        "interrupt_id": str(state.get("interrupt_id") or ""),
        "level_id": str(state.get("level_id") or ""),
        "focus": str(state.get("focus") or ""),
        "trigger_count": int(state.get("trigger_count") or 0),
        "current_activity": _public_activity(activity),
        "last_feedback": state.get("last_feedback"),
    }


def _public_activity(activity: dict[str, Any] | None) -> dict[str, Any] | None:
    if not activity:
        return None
    return {
        "activity_id": activity["activity_id"],
        "kind": "masterclass",
        "level_id": activity["level_id"],
        "focus": activity["focus"],
        "title": activity["title"],
        "teaching_block": activity["teaching_block"],
        "passage": activity["passage"],
        "prompt": activity["prompt"],
        "options": list(activity.get("options") or []) or None,
        "attempt_no": int(activity["attempt_no"]),
        "can_answer": True,
    }
