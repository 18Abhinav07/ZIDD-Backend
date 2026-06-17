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
from app.graph.route import level_kind, session_phase
from app.models import (
    PlacementRequest,
    SessionStartRequest,
    SessionStartResponse,
    SessionTurnRequest,
)
from app.services import session_service as svc
from app.services.session_service import GamePrompt
from app.services.simulation_service import Speaker

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
        return await svc.place_user(
            req.module_id, req.writing_sample, req.self_report, req.grade
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"unknown module: {req.module_id}") from e
    except Exception:
        # Fallback if AI placement fails (e.g., Ollama down)
        try:
            from app.content.registry import get_module
            mod = get_module(req.module_id)
            return {"node_id": mod.nodes[0].id, "cefr_estimate": "A1"}
        except Exception:
            return {"node_id": "comm_01_self_intro", "cefr_estimate": "A1"}



def _sse(data: str, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {data}\n\n"


def _avatar_emotion(affect: str, score: float | None) -> str:
    """Map learner affect + last eval score to an avatar emotion state."""
    s = score or 0.0
    if affect == "confident":
        return "impressed" if s >= 0.7 else "skeptical"
    if affect == "frustrated":
        return "empathetic"
    if affect == "confused":
        return "patient"
    # neutral
    if s >= 0.7:
        return "engaged"
    if s < 0.5:
        return "concerned"
    return "neutral"


def _state_snapshot(state: dict) -> dict:
    diag = state.get("last_diagnosis") or {}
    affect = diag.get("affect", "neutral")
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
        # Phase 5 progression surfacing: macro lifecycle, named section, and the
        # logged weakness list so the UI can draw a "where am I" bar.
        "phase": session_phase(state),
        "level_kind": level_kind(state),
        "tester_level": state.get("tester_level", False),
        "weaknesses": state.get("weakness_context", []),
        "on_task": diag.get("on_task", True),
        "english": diag.get("english", True),
        "affect": affect,
        "avatar_emotion": _avatar_emotion(affect, state.get("last_eval_score")),
    }


@router.post("/start", response_model=SessionStartResponse)
async def start(req: SessionStartRequest) -> SessionStartResponse:
    try:
        session_id, state = await svc.start_session(
            req.user_id, req.competency_node, test_mode=req.test_mode
        )
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
            if isinstance(tok, GamePrompt):
                # Scaffold teach turn: client renders a gamified widget.
                # answer_key stays server-side — not forwarded.
                yield _sse(
                    json.dumps({
                        "type": tok.type,
                        "sentence": tok.sentence,
                        "hint": tok.hint,
                        "context": tok.context,
                        "options": tok.options,
                    }),
                    event="game_prompt",
                )
            elif isinstance(tok, svc.NodeAdvance):
                # Discrete frame between old-node feedback and new-node opening
                # so the UI renders them as separate bubbles (no level-bleed).
                yield _sse(
                    json.dumps(
                        {"from_node": tok.from_node, "to_node": tok.to_node}
                    ),
                    event="node_advance",
                )
            elif isinstance(tok, svc.ProgressUpdate):
                yield _sse(
                    json.dumps({
                        "node_id": tok.node_id,
                        "mastery": tok.mastery,
                        "clean_streak": tok.clean_streak,
                        "attempts": tok.attempts,
                    }),
                    event="progress_update",
                )
            elif isinstance(tok, svc.SessionRecap):
                yield _sse(
                    json.dumps({
                        "nodes_completed": tok.nodes_completed,
                        "weaknesses": tok.weaknesses,
                        "avg_score": tok.avg_score,
                    }),
                    event="session_recap",
                )
            elif isinstance(tok, Speaker):
                # TEST-mode simulation: a new persona block begins. Open a fresh
                # speaker bubble before its text streams (mirrors node_advance).
                yield _sse(
                    json.dumps(
                        {"speaker_id": tok.speaker_id, "name": tok.name}
                    ),
                    event="speaker",
                )
            else:
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


@router.get("/progress/{user_id}")
async def get_progress(user_id: str, module_id: str = "communication") -> list[dict]:
    return await svc.get_progression_map(user_id, module_id)


@router.post("/{session_id}/end")
async def end(session_id: str) -> dict:
    summary = await svc.end_session(session_id)
    return {"session_id": session_id, "summary": summary}
