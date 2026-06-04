"""Session routes.

Streaming turns use Server-Sent Events: each token is a `data:` frame, and a
final `event: done` frame carries the post-turn state snapshot (route taken,
mastery, current node, advance/remediation flags) so the client updates its UI
without a second request.
"""
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.content.registry import get_node, list_modules
from app.models import (
    PlacementRequest,
    SessionStartRequest,
    SessionStartResponse,
    SessionTurnRequest,
)
from app.services import session_service as svc

router = APIRouter(prefix="/session", tags=["session"])
onboarding = APIRouter(tags=["onboarding"])


@onboarding.get("/modules")
async def modules() -> list[dict]:
    """Module picker payload for onboarding."""
    return list_modules()


@onboarding.post("/onboarding/placement")
async def placement(req: PlacementRequest) -> dict:
    """Estimate the learner's level and return their STARTING node."""
    try:
        return await svc.place_user(req.module_id, req.writing_sample, req.self_report)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"unknown module: {req.module_id}") from e


def _sse(data: str, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {data}\n\n"


def _state_snapshot(state: dict) -> dict:
    diag = state.get("last_diagnosis") or {}
    return {
        "session_id": state["session_id"],
        "competency_node": state["competency_node"],
        "node_title": get_node(state["competency_node"]).title,
        "current_mastery": round(state["current_mastery"], 4),
        "turn_count": state["turn_count"],
        "last_route": state.get("last_route"),
        "last_eval_score": state.get("last_eval_score"),
        "bridge_attempts": state.get("bridge_attempts", 0),
        "strengthen_attempts": state.get("strengthen_attempts", 0),
        "attempts": state.get("attempts", 0),
        "clean_streak": state.get("clean_streak", 0),
        "scaffold": state.get("scaffold", 0),
        "remediation": state.get("remediation", False),
        "module_done": state.get("module_done", False),
        "on_task": diag.get("on_task", True),
        "english": diag.get("english", True),
        "affect": diag.get("affect", "neutral"),
    }


@router.post("/start", response_model=SessionStartResponse)
async def start(req: SessionStartRequest) -> SessionStartResponse:
    try:
        session_id, state = await svc.start_session(req.user_id, req.competency_node)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    node = get_node(state["competency_node"])
    return SessionStartResponse(
        session_id=session_id,
        node_title=node.title,
        first_message="",  # opening is streamed via GET /session/{id}/opening
        current_mastery=state["current_mastery"],
    )


@router.get("/{session_id}/opening")
async def opening(session_id: str) -> StreamingResponse:
    if svc.get_state(session_id) is None:
        raise HTTPException(status_code=404, detail="no active session")

    async def gen() -> AsyncIterator[str]:
        async for tok in svc.stream_opening(session_id):
            yield _sse(json.dumps(tok))
        state = svc.get_state(session_id)
        yield _sse(json.dumps(_state_snapshot(state)), event="done")

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/turn")
async def turn(req: SessionTurnRequest) -> StreamingResponse:
    if svc.get_state(req.session_id) is None:
        raise HTTPException(status_code=404, detail="no active session")

    async def gen() -> AsyncIterator[str]:
        async for tok in svc.run_turn(req.session_id, req.user_input):
            yield _sse(json.dumps(tok))
        state = svc.get_state(req.session_id)
        yield _sse(json.dumps(_state_snapshot(state)), event="done")

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{session_id}/state")
async def state(session_id: str) -> dict:
    st = svc.get_state(session_id)
    if st is None:
        raise HTTPException(status_code=404, detail="no active session")
    return _state_snapshot(st)


@router.post("/{session_id}/end")
async def end(session_id: str) -> dict:
    summary = await svc.end_session(session_id)
    return {"session_id": session_id, "summary": summary}
