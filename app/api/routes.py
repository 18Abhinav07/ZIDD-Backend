"""Session routes.

Streaming turns use Server-Sent Events: each token is a `data:` frame, and a
final `event: done` frame carries the post-turn state snapshot (route taken,
mastery, current node, advance/remediation flags) so the client updates its UI
without a second request.
"""
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
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
from app.storage import get_storage
from app.billing.gate import resolve_gate, charge
from app.billing.pricing import pack_list
from app.services.session_service import GamePrompt
from app.services.simulation_service import Speaker, SimulationState

logger = logging.getLogger(__name__)

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
        # AI placement failed (e.g. Ollama down). Do NOT swallow silently — that
        # masks real placement defects and misroutes the learner with no trace.
        # Log with the stack, then fall back to the module's first node at A1 so
        # a new learner can still start.
        logger.warning(
            "placement failed for module=%s; using new-learner default",
            req.module_id,
            exc_info=True,
        )
        try:
            from app.content.registry import get_module
            mod = get_module(req.module_id)
            return {"node_id": mod.nodes[0].id, "cefr_estimate": "A1"}
        except Exception:
            logger.warning(
                "placement fallback get_module failed for module=%s",
                req.module_id,
                exc_info=True,
            )
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
    # Affect-display fields (FIX #4): on an ADVANCING turn, _maybe_advance clears
    # last_diagnosis/last_eval_score BEFORE this done frame is built, so reading
    # them live would show neutral/0.0 instead of the answer that advanced. They
    # are stashed pre-advance in _track_turn as last_turn_affect (which advance does
    # NOT clear), so source the 5 display fields from there when present. The
    # opening frame has no scored turn yet → fall back to live last_diagnosis.
    turn_affect = state.get("last_turn_affect")
    if turn_affect:
        affect = turn_affect.get("affect", "neutral")
        on_task = turn_affect.get("on_task", True)
        english = turn_affect.get("english", True)
        disp_score = turn_affect.get("last_eval_score")
    else:
        diag = state.get("last_diagnosis") or {}
        affect = diag.get("affect", "neutral")
        on_task = diag.get("on_task", True)
        english = diag.get("english", True)
        disp_score = state.get("last_eval_score")
    return {
        "session_id": state["session_id"],
        "competency_node": state["competency_node"],
        "node_title": get_node(state["competency_node"]).title,
        "current_mastery": round(state["current_mastery"], 4),
        "turn_count": state["turn_count"],
        "last_route": state.get("last_route"),
        "last_eval_score": disp_score,
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
        "on_task": on_task,
        "english": english,
        "affect": affect,
        "avatar_emotion": _avatar_emotion(affect, disp_score),
        # TEST-mode persona roster (interview panel / GD debaters), fixed once per
        # session in state["personas"]. None for coaching sessions and for the
        # first simulation frame (built on the opening round). The simulator UI
        # reads this to label speaker bubbles + avatar cards with the REAL roster
        # instead of a hardcoded fallback.
        "personas": state.get("personas"),
    }


def _done_frame(session_id: str) -> str:
    """The terminal SSE frame that releases the client's streaming lock.

    Emitted at the END of every stream — including one that died mid-token — so
    the UI is never stranded "streaming". If the session has vanished we still
    send a minimal done rather than nothing, because the ABSENCE of this frame is
    exactly what locks the simulator forever.
    """
    state = svc.get_state(session_id)
    if state is None:
        return _sse(json.dumps({"session_id": session_id}), event="done")
    return _sse(json.dumps(_state_snapshot(state)), event="done")


def _turn_frame(tok: object) -> str:
    """Map one run_turn token/marker to its SSE frame.

    String tokens stream as plain `data:` (message) frames; each typed marker
    becomes its own `event:` frame so the UI renders discrete bubbles/widgets.
    """
    if isinstance(tok, GamePrompt):
        # Scaffold teach turn: client renders a gamified widget. answer_key
        # stays server-side — not forwarded.
        return _sse(
            json.dumps({
                "type": tok.type,
                "sentence": tok.sentence,
                "hint": tok.hint,
                "context": tok.context,
                "options": tok.options,
            }),
            event="game_prompt",
        )
    if isinstance(tok, svc.NodeAdvance):
        # Discrete frame between old-node feedback and new-node opening so the
        # UI renders them as separate bubbles (no level-bleed).
        return _sse(
            json.dumps({"from_node": tok.from_node, "to_node": tok.to_node}),
            event="node_advance",
        )
    if isinstance(tok, svc.ProgressUpdate):
        return _sse(
            json.dumps({
                "node_id": tok.node_id,
                "mastery": tok.mastery,
                "clean_streak": tok.clean_streak,
                "attempts": tok.attempts,
            }),
            event="progress_update",
        )
    if isinstance(tok, svc.AdaptationCue):
        # Selector rationale: why the path just adapted. Fires on advancing
        # turns, after progress_update, before node_advance.
        return _sse(
            json.dumps({
                "action": tok.action,
                "band": tok.band,
                "rationale": tok.rationale,
            }),
            event="adaptation_cue",
        )
    if isinstance(tok, svc.SessionRecap):
        return _sse(
            json.dumps({
                "nodes_completed": tok.nodes_completed,
                "weaknesses": tok.weaknesses,
                "avg_score": tok.avg_score,
            }),
            event="session_recap",
        )
    if isinstance(tok, Speaker):
        # TEST-mode simulation: a new persona block begins. Open a fresh speaker
        # bubble before its text streams (mirrors node_advance).
        return _sse(
            json.dumps({"speaker_id": tok.speaker_id, "name": tok.name}),
            event="speaker",
        )
    if isinstance(tok, SimulationState):
        # TEST-mode simulation: Director's post-decision snapshot for this round
        # (turn count + tension), emitted right after the speaker frame and
        # before that speaker's token stream.
        return _sse(
            json.dumps({
                "turn": tok.turn,
                "speaker_id": tok.speaker_id,
                "tension": tok.tension,
                "should_close": tok.should_close,
            }),
            event="simulation_state",
        )
    return _sse(json.dumps(tok))


def _authed_user_id(request: Request) -> str:
    """The authenticated identity the JWT middleware stamped on this request.

    Every /session route except the public ones is auth-gated, so a missing
    identity means the auth chain was bypassed — refuse rather than fall back
    to a spoofable request-body field (the identity-spoofing chain).
    """
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return uid


def _owned_state(session_id: str, request: Request) -> dict:
    """Return a session's state, enforcing that the caller owns it.

    404 when the session is unknown, 403 when it belongs to another user. This
    is the single ownership gate behind every per-session route so an
    authenticated user can never drive or read another user's session by
    guessing its id (IDOR).
    """
    state = svc.get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="no active session")
    if state.get("user_id") != _authed_user_id(request):
        raise HTTPException(status_code=403, detail="not your session")
    return state


@router.post("/start", response_model=SessionStartResponse)
async def start(req: SessionStartRequest, request: Request) -> SessionStartResponse:
    # Bind to the AUTHENTICATED identity (JWT sub via middleware), never the
    # spoofable body field. The middleware guarantees an identity on this route
    # (or 401s), so there is no body fallback to spoof.
    user_id = _authed_user_id(request)
    store = get_storage()

    # Gate BEFORE the brain runs. The brain stays credit-blind.
    try:
        decision = await resolve_gate(store, user_id, req.competency_node)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown competency node") from e

    if not decision.free:
        balance = await store.get_credits(user_id)
        if not req.confirm:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "confirm_required",
                    "cost": decision.cost,
                    "balance": balance,
                    "scope": decision.scope,
                    "ref_id": decision.ref_id,
                },
            )
        charged = await charge(store, user_id, decision)
        if not charged:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "cost": decision.cost,
                    "balance": balance,
                    "packs": [p.model_dump() for p in pack_list()],
                },
            )

    try:
        session_id, state = await svc.start_session(
            user_id, req.competency_node, test_mode=req.test_mode
        )
    except Exception as e:
        # We already charged for a session that never started. Refund on ANY
        # failure, not just ValueError: a downstream KeyError / sqlite / TypeError
        # must NOT silently burn the learner's wallet. Free decisions were never
        # charged, so they get no refund. The compensation is best-effort and
        # logged so it never masks the original error.
        if not decision.free:
            try:
                await store.grant_credits(user_id, decision.cost, "refund")
                # ACCESS decisions also persisted a content_unlocks row in
                # charge(); without removing it the learner would keep permanent
                # free (owned) access AND get the credits back. Undo the unlock.
                if decision.record_unlock:
                    await store.remove_unlock(user_id, decision.scope, decision.ref_id)
            except Exception:
                logger.exception(
                    "refund after failed start did not complete for user=%s node=%s",
                    user_id,
                    req.competency_node,
                )
        # A brain-side rejection is a 400 (bad request); anything else is a real
        # server fault — re-raise it unchanged so it surfaces as a 500.
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e)) from e
        raise
    node = get_node(state["competency_node"])
    return SessionStartResponse(
        session_id=session_id,
        node_title=node.title,
        first_message="",  # opening is streamed via GET /session/{id}/opening
        current_mastery=state["current_mastery"],
    )


@router.get("/{session_id}/opening")
async def opening(session_id: str, request: Request) -> StreamingResponse:
    _owned_state(session_id, request)

    async def gen() -> AsyncIterator[str]:
        try:
            async for tok in svc.stream_opening(session_id):
                yield _sse(json.dumps(tok))
        except Exception:
            # The opening stream died mid-token (e.g. the local LLM dropped the
            # connection). The 200 + headers are already on the wire, so we
            # cannot change the status; surface an explicit error frame instead
            # of a silently-truncated bubble, then fall through to the terminal
            # done frame so the client's streaming lock is always released.
            logger.exception("opening stream failed for session=%s", session_id)
            yield _sse(json.dumps({"error": "stream_failed"}), event="error")
        yield _done_frame(session_id)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/turn")
async def turn(req: SessionTurnRequest, request: Request) -> StreamingResponse:
    # Ownership gate: the SessionTurnRequest body carries NO user_id, so identity
    # comes from the JWT and must match the session's owner — otherwise any
    # authenticated user could drive another user's session by id (IDOR).
    _owned_state(req.session_id, request)

    async def gen() -> AsyncIterator[str]:
        try:
            async for tok in svc.run_turn(req.session_id, req.user_input):
                yield _turn_frame(tok)
        except Exception:
            # The turn stream died mid-token (e.g. the local LLM dropped the
            # connection). The 200 + headers are already on the wire, so we
            # cannot change the status; surface an explicit error frame instead
            # of a silently-truncated bubble, then fall through to the terminal
            # done frame so the client's streaming lock is always released.
            logger.exception("turn stream failed for session=%s", req.session_id)
            yield _sse(json.dumps({"error": "stream_failed"}), event="error")
        yield _done_frame(req.session_id)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{session_id}/state")
async def state(session_id: str, request: Request) -> dict:
    st = _owned_state(session_id, request)
    return _state_snapshot(st)


@router.get("/{session_id}/transcript")
async def transcript(session_id: str, request: Request) -> dict:
    """Persisted conversation for a live session so a browser reload rehydrates
    the full transcript instead of wiping it back to the opening.

    Ownership-gated like every other per-session route (404 unknown, 403 not the
    owner's). `state` is the same snapshot the done frame carries (node title,
    mastery, persona roster, phase) so the UI restores its chrome too, and
    `opening_streamed` lets the client decide whether to replay the streamed
    opening (a fresh session) or just restore what's already there (a reload)."""
    st = _owned_state(session_id, request)
    messages = [
        {
            "id": f"{session_id}-{i}",
            "role": m.get("role", "assistant"),
            "content": m.get("content", ""),
            "speaker_name": m.get("speaker_name"),
        }
        for i, m in enumerate(st.get("messages", []))
    ]
    return {
        "messages": messages,
        "state": _state_snapshot(st),
        "opening_streamed": bool(st.get("opening_streamed", False)),
    }


@router.get("/progress/{user_id}")
async def get_progress(
    user_id: str, request: Request, module_id: str = "communication"
) -> list[dict]:
    # A user may only read their OWN progression. The path user_id must match
    # the authenticated identity (the FE sends the JWT sub), else it is an IDOR
    # read of another learner's mastery map.
    if _authed_user_id(request) != user_id:
        raise HTTPException(status_code=403, detail="not your progress")
    return await svc.get_progression_map(user_id, module_id)


@router.post("/{session_id}/end")
async def end(session_id: str, request: Request) -> dict:
    # Ownership gate before terminating — otherwise an authenticated attacker
    # could end another user's live session by id (IDOR).
    _owned_state(session_id, request)
    # close_session returns the FULL closing payload. For a TEST-mode simulation
    # `report` carries the five rubric sub-scores + strengths + improvements that
    # were deferred during the streamed rounds; for coaching sessions it is None.
    # Previously this route returned only the one-line summary, so the entire
    # scored report the engine computed never reached the learner.
    result = await svc.close_session(session_id)
    return {
        "session_id": session_id,
        "summary": result["summary"],
        "report": result["report"],
        "score": result["score"],
    }
