"""One-call structured turn engine for Interview Test and GD Test."""
from __future__ import annotations

from typing import Any

from app.ai.calls import evaluate_assessment_turn
from app.ai.schemas import AssessmentTurnCall
from app.services.assessment_events import ensure_assessment_runtime
from app.services.assessment_plan import ensure_assessment_plan
from app.services.assessment_policy import AuthorizedAssessmentTurn, authorize_assessment_turn


def _history(messages: list[dict[str, Any]], limit: int = 10) -> str:
    if not messages:
        return "(no visible transcript yet)"
    lines: list[str] = []
    for message in messages[-limit:]:
        role = message.get("role")
        content = str(message.get("content") or "")
        if role == "user":
            lines.append(f"[Learner]: {content}")
        else:
            speaker = str(message.get("speaker_name") or "Assistant")
            lines.append(f"[{speaker}]: {content}")
    return "\n".join(lines)


def _last_user_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


async def call_assessment_turn(
    state: dict[str, Any],
    plan: dict[str, Any],
) -> AssessmentTurnCall:
    """Call the structured model boundary. Split for monkeypatchable tests."""
    return await evaluate_assessment_turn(
        plan=plan,
        visible_ledger=list(state.get("visible_event_ledger") or []),
        transcript=_history(list(state.get("messages") or []), limit=10),
        learner_turn=_last_user_message(list(state.get("messages") or [])),
        turn_context=dict(state.get("assessment_turn_context") or {}),
    )


async def run_assessment_turn(state: dict[str, Any]) -> AuthorizedAssessmentTurn:
    """Analyze and authorize one normal assessment turn.

    The simulation streamer appends the assessment event after final visible text
    validation so scoring, report evidence, and the transcript stay aligned.
    """
    ensure_assessment_runtime(state)
    plan = ensure_assessment_plan(state)
    if not isinstance(plan, dict):
        raise ValueError("assessment_plan_missing")
    turn_call = await call_assessment_turn(state, plan)
    return authorize_assessment_turn(state, plan, turn_call)
