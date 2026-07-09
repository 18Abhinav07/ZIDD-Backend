"""Session routes.

Streaming turns use Server-Sent Events: each token is a `data:` frame, and a
final `event: done` frame carries the post-turn state snapshot (route taken,
mastery, current node, advance/remediation flags) so the client updates its UI
without a second request.
"""
import json
import hashlib
import logging
import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.content.registry import get_module, get_node, is_voice_node, list_modules, module_of
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
_SSE_HEARTBEAT_SECONDS = 12.0
_STREAM_SENTINEL = object()


@onboarding.get("/modules")
async def modules() -> list[dict]:
    """Module picker payload for onboarding."""
    return list_modules()


@onboarding.post("/onboarding/placement")
async def placement(req: PlacementRequest, request: Request) -> dict:
    """Estimate the learner's level and return their STARTING node."""
    user_id = await _authed_existing_user_id(request)
    try:
        return await svc.place_user(
            req.module_id, req.writing_sample, req.self_report, req.grade, user_id=user_id
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


def _accepted_frame(session_id: str, request_id: str, kind: str) -> str:
    return _sse(
        json.dumps({
            "session_id": session_id,
            "request_id": request_id,
            "kind": kind,
        }),
        event="accepted",
    )


def _heartbeat_frame(session_id: str, request_id: str, kind: str) -> str:
    return _sse(
        json.dumps({
            "session_id": session_id,
            "request_id": request_id,
            "kind": kind,
        }),
        event="heartbeat",
    )


def _opening_message_for_replay(
    state: dict,
    message_id: str | None,
    opening_key: str,
) -> str | None:
    messages = list(state.get("messages") or [])
    if message_id:
        for message in messages:
            if message.get("message_id") == message_id:
                content = message.get("content")
                return content if isinstance(content, str) else None

    current_node = state.get("competency_node")
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        if message.get("message_kind") != "opening":
            continue
        if message.get("transition_id") == opening_key:
            content = message.get("content")
            return content if isinstance(content, str) else None
        if (
            opening_key.startswith("initial:")
            and not message.get("transition_id")
            and message.get("node_id") == current_node
        ):
            content = message.get("content")
            return content if isinstance(content, str) else None
    return None


def _turn_request_hash(req: SessionTurnRequest) -> str:
    payload = {
        "session_id": req.session_id,
        "user_input": req.user_input,
        "expected_session_version": req.expected_session_version,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _start_request_hash(req: SessionStartRequest) -> str:
    payload = {
        "competency_node": req.competency_node,
        "test_mode": bool(req.test_mode),
        "confirm": bool(req.confirm),
        "reattempt_confirmed": bool(req.reattempt_confirmed),
        "simulation_config": req.simulation_config or {},
        "source_session_id": req.source_session_id,
        "source_transition_id": req.source_transition_id,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _session_start_response_payload(response: SessionStartResponse) -> dict:
    return response.model_dump()


def _replayed_start_response(row: dict, request_hash: str) -> SessionStartResponse:
    if row.get("request_hash") != request_hash:
        raise HTTPException(
            status_code=409,
            detail={"code": "client_start_id_reused_with_different_payload"},
        )
    status = row.get("status")
    if status == "completed" and isinstance(row.get("response_json"), dict):
        payload = dict(row["response_json"])
        payload["resumed"] = True
        return SessionStartResponse(**payload)
    raise HTTPException(
        status_code=409,
        detail={
            "code": "start_in_progress" if status == "in_progress" else "start_not_replayable",
        },
    )


def _replayed_source_transition_response(row: dict) -> SessionStartResponse:
    if row.get("status") == "completed" and isinstance(row.get("response_json"), dict):
        payload = dict(row["response_json"])
        payload["resumed"] = True
        return SessionStartResponse(**payload)
    raise HTTPException(
        status_code=409,
        detail={
            "code": "source_transition_starting"
            if row.get("status") == "in_progress"
            else "source_transition_not_replayable",
            "source_session_id": row.get("source_session_id"),
            "source_transition_id": row.get("source_transition_id"),
            "accepted_client_start_id": row.get("client_start_id")
            or row.get("accepted_client_start_id"),
        },
    )


def _active_node_for_progress(module_id: str, progress: list[dict]) -> str | None:
    completed = {
        row.get("node_id")
        for row in progress
        if row.get("node_id") and bool(row.get("node_completed"))
    }
    for node_id in get_module(module_id).order:
        if is_voice_node(node_id):
            continue
        if node_id not in completed:
            return node_id
    return None


def _enforce_start_node_unlocked(
    req: SessionStartRequest,
    progress: list[dict],
    existing: dict | None,
) -> None:
    if req.test_mode:
        return
    if req.source_session_id and req.source_transition_id:
        return
    if existing and bool(existing.get("node_completed")) and req.reattempt_confirmed:
        return
    try:
        module_id = module_of(req.competency_node)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown competency node") from exc
    active_node = _active_node_for_progress(module_id, progress)
    if req.competency_node != active_node:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "locked_node",
                "node_id": req.competency_node,
                "active_node_id": active_node,
                "module_id": module_id,
            },
        )


async def _validate_source_transition(req: SessionStartRequest, user_id: str) -> None:
    has_source = bool(req.source_session_id or req.source_transition_id)
    if not has_source:
        return
    if not req.source_session_id or not req.source_transition_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "source_transition_incomplete"},
        )
    source = await svc.get_session_state(req.source_session_id)
    pending = (source or {}).get("pending_node_transition")
    if (
        source is None
        or source.get("user_id") != user_id
        or not isinstance(pending, dict)
        or pending.get("transition_id") != req.source_transition_id
        or pending.get("to_node") != req.competency_node
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": "invalid_source_transition"},
        )


def _avatar_emotion(affect: str, score: float | None, *, scaffolded: bool = False) -> str:
    """Map learner affect + last eval score to an avatar emotion state."""
    s = score or 0.0
    if scaffolded:
        if affect == "frustrated":
            return "empathetic"
        return "patient"
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


def _public_personas(personas: object) -> list[dict] | None:
    if not isinstance(personas, list):
        return None
    safe: list[dict] = []
    for persona in personas:
        if not isinstance(persona, dict):
            continue
        row = {
            key: persona.get(key)
            for key in ("speaker_id", "name", "role_type", "role", "stance", "style")
            if persona.get(key) is not None
        }
        safe.append(row)
    return safe


def _public_game_prompt(prompt: object) -> dict | None:
    if not isinstance(prompt, dict):
        return None
    return {
        "type": prompt.get("type", "fill_blank"),
        "sentence": prompt.get("sentence", ""),
        "hint": prompt.get("hint", ""),
        "context": prompt.get("context", ""),
        "options": prompt.get("options"),
    }


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
        scaffolded = bool(turn_affect.get("scaffolded", False))
    else:
        diag = state.get("last_diagnosis") or {}
        affect = diag.get("affect", "neutral")
        on_task = diag.get("on_task", True)
        english = diag.get("english", True)
        disp_score = state.get("last_eval_score")
        scaffolded = bool(state.get("last_graded_bridge", False))
    # A TEST-mode simulation defers ALL scoring to the closing report, so there is
    # no per-turn score mid-session. Without this, _avatar_emotion reads the absent
    # score as 0.0 and shows a "concerned" face for the entire assessment, even
    # after strong answers. Surface a neutral-engaged assessor instead.
    in_assessment = level_kind(state) == "test"
    avatar = "engaged" if in_assessment else _avatar_emotion(affect, disp_score, scaffolded=scaffolded)
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
        "node_mastered": bool(state.get("node_mastered", False)),
        "display_status": state.get("display_status", "active"),
        "best_independent_score": float(state.get("best_independent_score") or 0.0),
        "independent_passes": int(state.get("independent_passes") or 0),
        "transfer_passes": int(state.get("transfer_passes") or 0),
        "pressure_passes": int(state.get("pressure_passes") or 0),
        "scaffold_successes": int(state.get("scaffold_successes") or 0),
        "meaningful_attempts": int(state.get("meaningful_attempts") or 0),
        "last_gap": state.get("last_gap", ""),
        "mastery_evidence": list(state.get("mastery_evidence") or []),
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
        "avatar_emotion": avatar,
        # TEST-mode persona roster (interview panel / GD debaters), fixed once per
        # session in state["personas"]. None for coaching sessions and for the
        # first simulation frame (built on the opening round). The simulator UI
        # reads this to label speaker bubbles + avatar cards with the REAL roster
        # instead of a hardcoded fallback.
        "personas": _public_personas(state.get("personas")),
        "scenario_config": state.get("scenario_config") or None,
        "status": state.get("status", "active"),
        "session_over": bool(state.get("session_over", False)),
        "simulation_round": int(
            state.get("simulation_round")
            or (state.get("blackboard") or {}).get("turn")
            or 0
        ),
        "simulation_tension": float((state.get("blackboard") or {}).get("tension") or 0.0),
        "simulation_score": state.get("simulation_score"),
        "simulation_report": state.get("simulation_report"),
        "session_version": int(state.get("session_version") or 1),
        "pending_transition": state.get("pending_node_transition"),
        "active_turn": (
            {
                "client_turn_id": state.get("active_turn_id"),
                "status": state.get("active_turn_status") or "processing",
            }
            if state.get("active_turn_id")
            else None
        ),
        "handoff_session_id": state.get("handoff_session_id"),
        "input_allowed": bool(state.get("input_allowed", True)),
        "block_reason": state.get("block_reason"),
        "opening_streamed": bool(state.get("opening_streamed", False)),
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


async def _authed_existing_user_id(request: Request) -> str:
    user_id = _authed_user_id(request)
    if not await get_storage().get_profile(user_id):
        raise HTTPException(status_code=401, detail="Profile not found; sign in again")
    return user_id


async def _owned_state(session_id: str, request: Request) -> dict:
    """Return a session's state, enforcing that the caller owns it.

    404 when the session is unknown, 403 when it belongs to another user. This
    is the single ownership gate behind every per-session route so an
    authenticated user can never drive or read another user's session by
    guessing its id (IDOR).
    """
    user_id = await _authed_existing_user_id(request)
    state = await svc.get_session_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="no active session")
    if state.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="not your session")
    if state.get("status") == "expired":
        raise HTTPException(
            status_code=410,
            detail={"code": "session_expired", "session_id": session_id},
        )
    await svc.touch_session_async(session_id)
    return state


@router.post("/start", response_model=SessionStartResponse)
async def start(req: SessionStartRequest, request: Request) -> SessionStartResponse:
    # Bind to the AUTHENTICATED identity (JWT sub via middleware), never the
    # spoofable body field. The middleware guarantees an identity on this route
    # (or 401s), so there is no body fallback to spoof.
    user_id = await _authed_existing_user_id(request)
    if not req.client_start_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "client_start_id_required"},
        )
    store = get_storage()
    await svc.cleanup_sessions()
    start_hash = _start_request_hash(req)

    start_latch = None
    if req.client_start_id and hasattr(store, "get_start_request"):
        existing_start = await store.get_start_request(user_id, req.client_start_id)
        if existing_start:
            if existing_start.get("request_hash") != start_hash:
                return _replayed_start_response(existing_start, start_hash)
            if existing_start.get("status") == "failed" and hasattr(store, "reset_start_request"):
                start_latch = await store.reset_start_request(
                    user_id,
                    req.client_start_id,
                    start_hash,
                    source_session_id=req.source_session_id,
                    source_transition_id=req.source_transition_id,
                )
            else:
                return _replayed_start_response(existing_start, start_hash)

    if (
        req.source_session_id
        and req.source_transition_id
        and hasattr(store, "get_start_request_for_source_transition")
    ):
        source_start = await store.get_start_request_for_source_transition(
            req.source_session_id,
            req.source_transition_id,
        )
        if source_start:
            return _replayed_source_transition_response(source_start)

    try:
        progress = await store.get_progression(user_id)
    except Exception as e:
        logger.exception("progression storage unavailable before session start for user=%s", user_id)
        raise HTTPException(
            status_code=503,
            detail={"code": "progression_unavailable", "node_id": req.competency_node},
        ) from e
    existing = next((p for p in progress if p.get("node_id") == req.competency_node), None)
    if existing and bool(existing.get("node_completed")) and not req.test_mode:
        if not req.reattempt_confirmed:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "completed_node",
                    "message": "This level is already completed. Confirm to start a new attempt.",
                    "node_id": req.competency_node,
                },
            )

    _enforce_start_node_unlocked(req, progress, existing)
    await _validate_source_transition(req, user_id)

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

    if start_latch is None and req.client_start_id and hasattr(store, "begin_start_request"):
        start_latch = await store.begin_start_request(
            user_id,
            req.client_start_id,
            start_hash,
            source_session_id=req.source_session_id,
            source_transition_id=req.source_transition_id,
        )
        if start_latch.get("request_mismatch"):
            raise HTTPException(
                status_code=409,
                detail={"code": "client_start_id_reused_with_different_payload"},
            )
        if not start_latch.get("accepted"):
            if start_latch.get("status") == "source_transition_consumed":
                consumed = dict(start_latch)
                consumed["status"] = consumed.get("consumed_status") or "in_progress"
                return _replayed_source_transition_response(consumed)
            return _replayed_start_response(start_latch, start_hash)

    charged_ok = False
    if not decision.free:
        balance = await store.get_credits(user_id)
        charged_ok = await charge(store, user_id, decision)
        if not charged_ok:
            if req.client_start_id and hasattr(store, "complete_start_request") and start_latch:
                await store.complete_start_request(
                    user_id,
                    req.client_start_id,
                    "failed",
                    error_code="insufficient_credits",
                )
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
        start_kwargs = {
            "test_mode": req.test_mode,
            "reattempt": req.reattempt_confirmed and bool(existing),
        }
        if req.simulation_config:
            start_kwargs["simulation_config"] = req.simulation_config
        session_id, state = await svc.start_session(
            user_id,
            req.competency_node,
            **start_kwargs,
        )
        if req.source_session_id and req.source_transition_id:
            await svc.handoff_transition_to_session(
                req.source_session_id,
                req.source_transition_id,
                session_id,
                req.competency_node,
                user_id,
            )
    except Exception as e:
        # We already charged for a session that never started. Refund on ANY
        # failure, not just ValueError: a downstream KeyError / storage / TypeError
        # must NOT silently burn the learner's wallet. Free decisions were never
        # charged, so they get no refund. The compensation is best-effort and
        # logged so it never masks the original error.
        if charged_ok:
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
        if req.client_start_id and hasattr(store, "complete_start_request") and start_latch:
            await store.complete_start_request(
                user_id,
                req.client_start_id,
                "failed",
                error_code=(
                    "progression_unavailable"
                    if isinstance(e, svc.ProgressionUnavailableError)
                    else "session_start_failed"
                ),
            )
        # A brain-side rejection is a 400 (bad request); anything else is a real
        # server fault — re-raise it unchanged so it surfaces as a 500.
        if isinstance(e, svc.ProgressionUnavailableError):
            raise HTTPException(
                status_code=503,
                detail={"code": "progression_unavailable", "node_id": req.competency_node},
            ) from e
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e)) from e
        raise
    node = get_node(state["competency_node"])
    response = SessionStartResponse(
        session_id=session_id,
        node_title=node.title,
        first_message="",  # opening is streamed via GET /session/{id}/opening
        current_mastery=state["current_mastery"],
    )
    if req.client_start_id and hasattr(store, "complete_start_request") and start_latch:
        await store.complete_start_request(
            user_id,
            req.client_start_id,
            "completed",
            session_id=session_id,
            response_json=_session_start_response_payload(response),
        )
    return response


@router.get("/{session_id}/opening")
async def opening(
    session_id: str,
    request: Request,
    transition_id: str | None = None,
) -> StreamingResponse:
    st = await _owned_state(session_id, request)
    pending = st.get("pending_node_transition")
    if isinstance(pending, dict):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "next_skill_requires_session_start",
                "session_id": session_id,
                "source_transition_id": pending.get("transition_id"),
                "next_node": pending.get("to_node"),
            },
        )
    block_code = svc.opening_block_reason(st)
    if block_code:
        raise HTTPException(
            status_code=409,
            detail={"code": block_code, "session_id": session_id},
        )
    resolved_transition_id = transition_id or (
        pending.get("transition_id") if isinstance(pending, dict) else None
    )
    opening_key = resolved_transition_id or f"initial:{st.get('competency_node')}"
    store = get_storage()
    opening_latch = None
    if hasattr(store, "begin_opening_request"):
        opening_latch = await store.begin_opening_request(session_id, opening_key)
        if not opening_latch.get("accepted"):
            status = opening_latch.get("status")
            if status == "completed":
                replay_text = _opening_message_for_replay(
                    st,
                    opening_latch.get("message_id"),
                    opening_key,
                )
                if replay_text is None:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "code": "opening_replay_unavailable",
                            "session_id": session_id,
                        },
                    )

                async def replay_completed() -> AsyncIterator[str]:
                    yield _sse(json.dumps(replay_text))
                    yield _done_frame(session_id)

                return StreamingResponse(replay_completed(), media_type="text/event-stream")
            if status == "in_progress":
                raise HTTPException(
                    status_code=409,
                    detail={"code": "opening_in_progress", "session_id": session_id},
                )
            if status not in {"failed"}:
                raise HTTPException(
                    status_code=409,
                    detail={"code": "opening_not_replayable", "session_id": session_id},
                )

    async def gen() -> AsyncIterator[str]:
        queue: asyncio.Queue[str | object] = asyncio.Queue()
        accepted = _accepted_frame(session_id, opening_key, "opening")

        async def complete_latch_best_effort(status: str, last_error: str | None = None) -> None:
            if (
                opening_latch
                and opening_latch.get("accepted")
                and hasattr(store, "complete_opening_request")
            ):
                try:
                    current_state = svc.get_state(session_id) or {}
                    await store.complete_opening_request(
                        session_id,
                        opening_key,
                        status,
                        message_id=current_state.get("last_opening_message_id"),
                        last_error=last_error,
                    )
                except Exception:
                    logger.exception(
                        "opening latch completion failed for session=%s transition=%s status=%s",
                        session_id,
                        opening_key,
                        status,
                    )

        async def producer() -> None:
            completion_status = "completed"
            completion_error: str | None = None
            try:
                async for tok in svc.stream_opening(
                    session_id,
                    transition_id=resolved_transition_id,
                ):
                    await queue.put(_sse(json.dumps(tok)))
            except Exception:
                completion_status = "failed"
                completion_error = "stream_failed"
                # The opening stream died mid-token (e.g. the local LLM dropped the
                # connection). The 200 + headers are already on the wire, so we
                # cannot change the status; surface an explicit error frame instead
                # of a silently-truncated bubble, then fall through to the terminal
                # done frame so the client's streaming lock is always released.
                logger.exception("opening stream failed for session=%s", session_id)
                await queue.put(_sse(json.dumps({"error": "stream_failed"}), event="error"))
            await complete_latch_best_effort(completion_status, completion_error)
            await queue.put(_done_frame(session_id))
            await queue.put(_STREAM_SENTINEL)

        task = asyncio.create_task(producer())

        def _consume_task_result(done_task: asyncio.Task) -> None:
            try:
                done_task.result()
            except Exception:
                logger.exception(
                    "opening producer failed after disconnect for session=%s transition=%s",
                    session_id,
                    opening_key,
                )

        task.add_done_callback(_consume_task_result)
        yield accepted
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=_SSE_HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield _heartbeat_frame(session_id, opening_key, "opening")
                continue
            if item is _STREAM_SENTINEL:
                break
            yield item  # type: ignore[misc]

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/turn")
async def turn(req: SessionTurnRequest, request: Request) -> StreamingResponse:
    # Ownership gate: the SessionTurnRequest body carries NO user_id, so identity
    # comes from the JWT and must match the session's owner — otherwise any
    # authenticated user could drive another user's session by id (IDOR).
    st = await _owned_state(req.session_id, request)
    if not req.client_turn_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "client_turn_id_required", "session_id": req.session_id},
        )
    if req.expected_session_version is None:
        raise HTTPException(
            status_code=400,
            detail={"code": "expected_session_version_required", "session_id": req.session_id},
        )
    store = get_storage()
    turn_latch = None
    if hasattr(store, "begin_turn_request"):
        turn_latch = await store.begin_turn_request(
            req.session_id,
            req.client_turn_id,
            _turn_request_hash(req),
            req.expected_session_version,
        )
        if turn_latch.get("request_mismatch"):
            raise HTTPException(
                status_code=409,
                detail={"code": "client_turn_id_reused_with_different_payload"},
            )
        if not turn_latch.get("accepted"):
            status = turn_latch.get("status")
            if status == "completed":
                frames = [
                    item.get("frame")
                    for item in list(turn_latch.get("transcript_delta") or [])
                    if isinstance(item, dict) and item.get("frame")
                ]

                async def replay() -> AsyncIterator[str]:
                    for frame in frames:
                        yield frame
                    if not any("event: done" in frame for frame in frames):
                        done = turn_latch.get("done_snapshot") or _state_snapshot(st)
                        yield _sse(json.dumps(done), event="done")

                return StreamingResponse(replay(), media_type="text/event-stream")
            if status == "version_consumed":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "turn_version_consumed",
                        "session_id": req.session_id,
                        "accepted_client_turn_id": turn_latch.get("accepted_client_turn_id"),
                    },
                )
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "turn_in_progress" if status == "in_progress" else "turn_not_replayable",
                    "session_id": req.session_id,
                },
            )

    block_code = svc.turn_block_reason(st)
    if block_code:
        if hasattr(store, "complete_turn_request") and turn_latch and turn_latch.get("accepted"):
            await store.complete_turn_request(
                req.session_id,
                req.client_turn_id,
                "failed",
                [],
                _state_snapshot(st),
                block_code,
            )
        raise HTTPException(
            status_code=409,
            detail={"code": block_code, "session_id": req.session_id},
        )
    if (
        req.expected_session_version is not None
        and req.expected_session_version != int(st.get("session_version") or 1)
    ):
        if hasattr(store, "complete_turn_request") and turn_latch and turn_latch.get("accepted"):
            await store.complete_turn_request(
                req.session_id,
                req.client_turn_id,
                "failed",
                [],
                _state_snapshot(st),
                "session_version_conflict",
            )
        raise HTTPException(
            status_code=409,
            detail={
                "code": "session_version_conflict",
                "session_id": req.session_id,
                "session_version": int(st.get("session_version") or 1),
            },
        )

    async def gen() -> AsyncIterator[str]:
        queue: asyncio.Queue[str | object] = asyncio.Queue()
        accepted = _accepted_frame(req.session_id, req.client_turn_id, "turn")
        frames: list[str] = [accepted]

        async def producer() -> None:
            error_code: str | None = None
            try:
                async for tok in svc.run_turn(
                    req.session_id,
                    req.user_input,
                    client_turn_id=req.client_turn_id,
                ):
                    frame = _turn_frame(tok)
                    frames.append(frame)
                    await queue.put(frame)
            except svc.AwaitingNextSkillError:
                error_code = "awaiting_next_skill"
                frame = _sse(json.dumps({"code": "awaiting_next_skill"}), event="error")
                frames.append(frame)
                await queue.put(frame)
            except svc.SessionNotActiveError as exc:
                error_code = str(exc) or "session_not_active"
                frame = _sse(json.dumps({"code": error_code}), event="error")
                frames.append(frame)
                await queue.put(frame)
            except Exception:
                # The turn stream died mid-token (e.g. the local LLM dropped the
                # connection). The 200 + headers are already on the wire, so we
                # cannot change the status; surface an explicit error frame instead
                # of a silently-truncated bubble, then fall through to the terminal
                # done frame so the client's streaming lock is always released.
                logger.exception("turn stream failed for session=%s", req.session_id)
                error_code = "stream_failed"
                frame = _sse(json.dumps({"error": "stream_failed"}), event="error")
                frames.append(frame)
                await queue.put(frame)

            current_state = svc.get_state(req.session_id) or st
            if error_code and hasattr(svc, "_finish_active_turn"):
                try:
                    svc._finish_active_turn(current_state, req.client_turn_id, "failed")
                    await svc._persist_runtime_state(current_state)
                except Exception:
                    logger.exception(
                        "active turn finalization failed for session=%s client_turn_id=%s",
                        req.session_id,
                        req.client_turn_id,
                    )
            done = _done_frame(req.session_id)
            frames.append(done)
            if hasattr(store, "complete_turn_request"):
                try:
                    await store.complete_turn_request(
                        req.session_id,
                        req.client_turn_id,
                        "failed" if error_code else "completed",
                        [{"frame": frame} for frame in frames],
                        _state_snapshot(svc.get_state(req.session_id) or current_state),
                        error_code,
                    )
                except Exception:
                    logger.exception(
                        "turn latch completion failed for session=%s client_turn_id=%s",
                        req.session_id,
                        req.client_turn_id,
                    )
            await queue.put(done)
            await queue.put(_STREAM_SENTINEL)

        task = asyncio.create_task(producer())

        def _consume_task_result(done_task: asyncio.Task) -> None:
            try:
                done_task.result()
            except Exception:
                logger.exception(
                    "turn producer failed after disconnect for session=%s client_turn_id=%s",
                    req.session_id,
                    req.client_turn_id,
                )

        task.add_done_callback(_consume_task_result)
        yield accepted
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=_SSE_HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                yield _heartbeat_frame(req.session_id, req.client_turn_id, "turn")
                continue
            if item is _STREAM_SENTINEL:
                break
            yield item  # type: ignore[misc]

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{session_id}/state")
async def state(session_id: str, request: Request) -> dict:
    st = await _owned_state(session_id, request)
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
    st = await _owned_state(session_id, request)
    messages = [
        {
            "id": f"{session_id}-{i}",
            "role": m.get("role", "assistant"),
            "content": m.get("content", ""),
            "speaker_name": m.get("speaker_name"),
            "speaker_id": m.get("speaker_id"),
            "node_id": m.get("node_id"),
            "transition_id": m.get("transition_id"),
            "message_kind": m.get("message_kind"),
            "status": m.get("status"),
        }
        for i, m in enumerate(st.get("messages", []))
    ]
    return {
        "messages": messages,
        "state": _state_snapshot(st),
        "pending_transition": st.get("pending_node_transition"),
        "active_turn": (
            {
                "client_turn_id": st.get("active_turn_id"),
                "status": st.get("active_turn_status") or "processing",
            }
            if st.get("active_turn_id")
            else None
        ),
        "game_prompt": _public_game_prompt(st.get("active_game_prompt")),
        "input_allowed": bool(st.get("input_allowed", True)),
        "block_reason": st.get("block_reason"),
        "session_version": int(st.get("session_version") or 1),
        "opening_streamed": bool(st.get("opening_streamed", False)),
    }


@router.get("/progress/me")
async def get_my_progress(request: Request, module_id: str = "communication") -> list[dict]:
    try:
        return await svc.get_progression_map(await _authed_existing_user_id(request), module_id)
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": "unknown_module", "module_id": module_id},
        ) from e
    except svc.ProgressionUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={"code": "progression_unavailable", "module_id": module_id},
        ) from e


@router.get("/progress/{user_id}")
async def get_progress(
    user_id: str, request: Request, module_id: str = "communication"
) -> list[dict]:
    # A user may only read their OWN progression. The path user_id must match
    # the authenticated identity (the FE sends the JWT sub), else it is an IDOR
    # read of another learner's mastery map.
    if await _authed_existing_user_id(request) != user_id:
        raise HTTPException(status_code=403, detail="not your progress")
    try:
        return await svc.get_progression_map(user_id, module_id)
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": "unknown_module", "module_id": module_id},
        ) from e
    except svc.ProgressionUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={"code": "progression_unavailable", "module_id": module_id},
        ) from e


def _closing_payload(session_id: str, result: dict, status: str = "completed") -> dict:
    return {
        "status": status,
        "session_id": session_id,
        "summary": result["summary"],
        "report": result["report"],
        "score": result["score"],
    }


async def _score_session_end_request(session_id: str) -> None:
    store = get_storage()
    try:
        result = await svc.close_session(session_id)
        payload = _closing_payload(session_id, result)
        if hasattr(store, "complete_end_request"):
            await store.complete_end_request(session_id, "completed", payload, None)
    except Exception:
        logger.exception("async session scoring failed for session=%s", session_id)
        if hasattr(store, "complete_end_request"):
            await store.complete_end_request(
                session_id,
                "failed",
                None,
                "simulation_scoring_unavailable",
            )


@router.post("/{session_id}/end")
async def end(session_id: str, request: Request, background_tasks: BackgroundTasks):
    # Ownership gate before terminating — otherwise an authenticated attacker
    # could end another user's live session by id (IDOR).
    st = await _owned_state(session_id, request)
    # close_session returns the FULL closing payload. For a TEST-mode simulation
    # `report` carries the five rubric sub-scores + strengths + improvements that
    # were deferred during the streamed rounds; for coaching sessions it is None.
    # Previously this route returned only the one-line summary, so the entire
    # scored report the engine computed never reached the learner.
    is_test = st.get("task_type") in svc._TEST_TASK_TYPES
    if is_test and st.get("status") == "ended" and st.get("simulation_report"):
        return _closing_payload(
            session_id,
            {
                "summary": st.get("session_summary") or "",
                "report": st.get("simulation_report"),
                "score": float(st.get("simulation_score") or 0.0),
            },
        )
    if is_test:
        store = get_storage()
        if hasattr(store, "begin_end_request"):
            end_latch = await store.begin_end_request(session_id)
            if not end_latch.get("accepted"):
                status = end_latch.get("status")
                if status == "completed" and end_latch.get("response_json"):
                    return end_latch["response_json"]
                if status == "failed":
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "code": end_latch.get("error_code") or "simulation_scoring_unavailable",
                            "session_id": session_id,
                        },
                    )
                return JSONResponse(
                    {"status": "processing", "session_id": session_id},
                    status_code=202,
                )
        background_tasks.add_task(_score_session_end_request, session_id)
        return JSONResponse(
            {"status": "processing", "session_id": session_id},
            status_code=202,
        )

    try:
        result = await svc.close_session(session_id)
    except svc.SessionScoringUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={"code": "simulation_scoring_unavailable", "session_id": session_id},
        ) from e
    return _closing_payload(session_id, result)


@router.get("/{session_id}/report")
async def report(session_id: str, request: Request):
    st = await _owned_state(session_id, request)
    if st.get("status") == "ended" and st.get("simulation_report"):
        return _closing_payload(
            session_id,
            {
                "summary": st.get("session_summary") or "",
                "report": st.get("simulation_report"),
                "score": float(st.get("simulation_score") or 0.0),
            },
        )
    store = get_storage()
    if hasattr(store, "get_end_request"):
        end_latch = await store.get_end_request(session_id)
        if end_latch:
            status = end_latch.get("status")
            if status == "completed" and end_latch.get("response_json"):
                return end_latch["response_json"]
            if status == "failed":
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": end_latch.get("error_code") or "simulation_scoring_unavailable",
                        "session_id": session_id,
                    },
                )
            return JSONResponse(
                {"status": "processing", "session_id": session_id},
                status_code=202,
            )
    return JSONResponse(
        {"status": "not_started", "session_id": session_id},
        status_code=404,
    )
