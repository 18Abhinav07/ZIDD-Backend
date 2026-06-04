"""Session orchestration — the engine's runtime.

Owns canonical state (in-memory SessionStore), drives the graph each turn,
streams the chosen generation over the AI boundary, tracks mastery/clean-pass
progression, advances nodes on completion, and flags a module for remediation
when the clean pass-rate drops below 50%.

DB is best-effort: every Postgres call is wrapped so the engine runs identically
offline (dev / CI / Layer-A tests). Memory and credits degrade to no-ops when
the DB or Ollama is unavailable. The graph and AI boundary are the only hard
dependencies, and tests monkeypatch the AI boundary.
"""
import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.config import get_settings
from app.ai.calls import (
    GEMINI_FLASH,
    GenSpec,
    evaluate_placement,
    stream_generation,
    summarize_session,
)
from app.ai.prompts import build_opening_prompt, coach_view
from app.content.registry import (
    SELF_REPORT_CEFR,
    all_node_ids,
    get_module,
    get_node,
    next_node,
    placement_node,
)
from app.graph.build import get_graph
from app.memory import store as memory_store

MASTERY_COMPLETE = 0.8       # node "mastered" (EMA) — kept for DB clean-flag only
CLEAN_PASS_MAX_ATTEMPTS = 2  # mastered in <=2 scored answers == "clean"
PASSRATE_FLOOR = 0.5         # module clean-rate below this -> remediation

# Progression is gated on a CONSECUTIVE clean-pass streak, not the EMA mastery
# value. The EMA (update_mastery, alpha 0.3) converges toward the score and a
# steady 0.8 never crosses a strict >0.8 gate, so the old mastery gate could
# softlock a learner who was answering correctly. A streak of clean passes is
# both reachable and a truer signal of "ready to move on".
PASS_SCORE = 0.7         # a single answer at/above this is a clean pass
ADVANCE_STREAK = 2       # this many consecutive clean passes -> advance node
FAIL_SCORE = 0.4         # below this counts as a hard fail at this level
DOWN_LADDER_FAILS = 2    # this many hard fails -> scaffold HARD (down-ladder)
MAX_INPUT_CHARS = 2000   # cap learner input; protects ctx window + cost

# Short learner messages matching these end the session gracefully.
_END_PHRASES = {
    "done", "stop", "bye", "goodbye", "quit", "exit", "that's all",
    "thats all", "im done", "i'm done", "end", "finish", "no more",
}
# Phrases that signal discouragement -> pivot to support on the next turn.
_FRUSTRATION_PHRASES = (
    "i can't", "i cant", "give up", "too hard", "i'm confused", "im confused",
    "i don't get", "i dont get", "this is hard", "i'm lost", "im lost",
    "i give up", "frustrated", "i can not",
)

# session_id -> TutorState dict
SessionStore: dict[str, dict] = {}

# Keys that are transient within a single turn and must NOT be persisted:
# `pending` holds a GenSpec (a frozen dataclass, not JSON-serializable, and only
# meaningful for the in-flight stream).
_TRANSIENT_KEYS = ("pending",)


def _store_path() -> str:
    """Disk path for SessionStore persistence; empty string disables it."""
    return get_settings().session_store_path


def save_sessions() -> None:
    """Snapshot the in-memory store to disk (atomic). No-op if disabled.

    Durability fix #1: lets live sessions survive a process restart. Transient
    keys are stripped; everything else in TutorState is JSON-serializable."""
    path = _store_path()
    if not path:
        return
    snapshot = {
        sid: {k: v for k, v in state.items() if k not in _TRANSIENT_KEYS}
        for sid, state in SessionStore.items()
    }
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snapshot, f)
    os.replace(tmp, path)  # atomic on POSIX — no half-written store on crash


def load_sessions() -> None:
    """Restore the store from disk. No-op if disabled or the file is absent."""
    path = _store_path()
    if not path or not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for state in data.values():
        for k in _TRANSIENT_KEYS:
            state.setdefault(k, None)
    SessionStore.update(data)


def _new_state(
    user_id: str,
    session_id: str,
    node_id: str,
    memory_context: str,
    learner_name: str = "",
) -> dict:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "competency_node": node_id,
        "user_input": "",
        "current_mastery": 0.0,
        "turn_count": 0,
        "messages": [],
        "last_diagnosis": {},
        "last_eval_score": 0.0,
        "bridge_attempts": 0,
        "attempts": 0,
        "memory_context": memory_context,
        "session_summary": None,
        "pending": None,
        "last_route": None,
        # personalization / progression bookkeeping (service-owned; coach_view
        # projects a subset of these into the private coaching directive block)
        "learner_name": learner_name,
        "clean_streak": 0,        # consecutive clean passes at current node
        "advance_streak": ADVANCE_STREAK,
        "level_fails": 0,         # consecutive hard fails at current node
        "strengthen_attempts": 0, # consecutive strengthens in the 0.4-0.6 plateau
        "scaffold": 0,            # >=1 -> scaffold HARD (down-ladder)
        "needs_support": False,   # set per-turn from frustration detection
        "session_over": False,
        # service-only bookkeeping (not consumed by the graph)
        "node_history": {},     # node_id -> {"attempts": int, "clean": bool}
        "remediation": False,
        "module_done": False,
    }


@asynccontextmanager
async def _db():
    """Yield an AsyncSession, or None if the DB is unreachable (offline)."""
    try:
        from app.db.engine import get_sessionmaker

        maker = get_sessionmaker()
    except Exception:
        yield None
        return
    session = maker()
    try:
        yield session
    except Exception:
        yield None
    finally:
        try:
            await session.close()
        except Exception:
            pass


# ---------- public API ----------

async def start_session(
    user_id: str, node_id: str, learner_name: str = ""
) -> tuple[str, dict]:
    """Create a session, return (session_id, state). Opening msg streamed via
    stream_opening(). Loads prior memory for this node (best-effort).

    `learner_name` (optional) personalizes the coaching directives so the tutor
    addresses the learner by name."""
    if node_id not in all_node_ids():
        raise ValueError(f"unknown competency node: {node_id}")
    session_id = uuid.uuid4().hex

    memory_context = ""
    async with _db() as session:
        if session is not None:
            try:
                from app.db import repo

                await repo.ensure_profile(session, user_id)
                await repo.create_session(session, session_id, user_id, node_id)
                memory_context = await memory_store.load_context(
                    session, user_id, node_id
                )
            except Exception:
                memory_context = ""

    state = _new_state(user_id, session_id, node_id, memory_context, learner_name)
    SessionStore[session_id] = state
    save_sessions()
    return session_id, state


async def stream_opening(session_id: str) -> AsyncIterator[str]:
    """Stream the lesson opening for a fresh session (turn 0)."""
    state = _require(session_id)
    node = get_node(state["competency_node"])
    prompt = build_opening_prompt(
        node, state.get("memory_context", ""), coach_view(state)
    )
    spec = GenSpec(provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="opening")
    full = []
    async for tok in stream_generation(spec):
        full.append(tok)
        yield tok
    text = "".join(full)
    state["messages"].append({"role": "assistant", "content": text})
    state["turn_count"] += 1
    save_sessions()


async def _stream_node_opening(state: dict) -> AsyncIterator[str]:
    """Stream a lesson opening for state's CURRENT node, append it, bump turn.

    Shared by stream_opening (fresh session) and the advance-transition in
    run_turn (desync fix). Falls back to a plain transition line if the stream
    yields nothing so an advance never ends on silence."""
    node = get_node(state["competency_node"])
    prompt = build_opening_prompt(
        node, state.get("memory_context", ""), coach_view(state)
    )
    spec = GenSpec(provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="opening")
    full = []
    try:
        async for tok in stream_generation(spec):
            full.append(tok)
            yield tok
    except Exception:
        full = []
    text = "".join(full).strip()
    if not text:
        text = "Nice work — let's move on to the next skill. Ready?"
        yield text
    state["messages"].append({"role": "assistant", "content": text})
    state["turn_count"] += 1


async def run_turn(session_id: str, user_input: str) -> AsyncIterator[str]:
    """Process one learner answer: evaluate -> route -> stream the response.

    Hardened: caps oversized input, ends the session gracefully on a goodbye,
    pivots to support when the learner sounds discouraged, and falls back to a
    plain message if the stream yields nothing (backend hiccup) so the turn
    never dies silently."""
    state = _require(session_id)
    user_input = (user_input or "")[:MAX_INPUT_CHARS]
    state["user_input"] = user_input

    # Graceful exit: a short "done / bye / stop" ends the session with a warm
    # farewell instead of being scored as an off-task answer.
    if _is_session_end(user_input):
        state["session_over"] = True
        farewell = _farewell(state)
        state["messages"].append({"role": "user", "content": user_input})
        state["messages"].append({"role": "assistant", "content": farewell})
        save_sessions()
        yield farewell
        return

    state["messages"].append({"role": "user", "content": user_input})
    # Sentiment pivot: flag support BEFORE the graph builds its prompt so the
    # coaching directives (via coach_view) reflect it this turn.
    state["needs_support"] = _detect_frustration(user_input)

    # turn 0 was the opening (assistant-only), so turn_count>=1 means there is a
    # real learner answer to score this turn. Capture before the graph runs.
    did_eval = state["turn_count"] >= 1

    # Graph = decision brain: evaluate the answer, pick the pedagogy move,
    # build its prompt. Returns partial-state updates we merge back.
    graph = get_graph()
    updates = await graph.ainvoke(state)
    state.update(updates)

    spec: GenSpec | None = state.get("pending")
    full = []
    if spec is not None:
        try:
            async for tok in stream_generation(spec):
                full.append(tok)
                yield tok
        except Exception:
            full = []  # discard partial; emit the fallback below
    text = "".join(full).strip()
    if not text:
        text = (
            "Sorry — I lost my train of thought for a second there. "
            "Could you try that once more for me?"
        )
        yield text
    state["messages"].append({"role": "assistant", "content": text})
    state["turn_count"] += 1
    state["pending"] = None

    if did_eval:
        prev_node = state["competency_node"]
        _update_progress(state)
        # Persist CURRENT node mastery before any advance mutates the pointer.
        await _persist_mastery(state)
        await _maybe_advance(state)
        # Desync fix: if the answer advanced us to a new node, the pedagogy text
        # just streamed was for the OLD node while the snapshot now points at the
        # new one. Stream a short opening for the NEW node in the SAME turn so the
        # tutor's words match the node the learner is now on.
        if (
            not state["module_done"]
            and state["competency_node"] != prev_node
        ):
            async for tok in _stream_node_opening(state):
                yield tok

    save_sessions()


async def end_session(session_id: str) -> str:
    """Summarize the session for long-term memory and close it out."""
    state = SessionStore.get(session_id)
    if state is None:
        return ""
    node = get_node(state["competency_node"])
    try:
        summary = await summarize_session(node, state["messages"])
    except Exception:
        summary = ""

    async with _db() as session:
        if session is not None and summary:
            try:
                from app.db import repo

                await repo.end_session(
                    session,
                    session_id,
                    state["turn_count"],
                    state["current_mastery"],
                    summary,
                )
                await memory_store.write_memory(
                    session,
                    state["user_id"],
                    session_id,
                    state["competency_node"],
                    summary,
                )
            except Exception:
                pass

    state["session_summary"] = summary
    SessionStore.pop(session_id, None)
    save_sessions()
    return summary


def get_state(session_id: str) -> dict | None:
    return SessionStore.get(session_id)


async def place_user(
    module_id: str,
    writing_sample: str | None = None,
    self_report: str | None = None,
) -> dict:
    """Onboarding placement: estimate CEFR, pick the STARTING node in a module.

    A writing sample drives a Flash-Lite CEFR estimate; otherwise the learner's
    self-report bucket (beginner/intermediate/advanced/fluent) maps to a band.
    Falls back to B1 if neither is usable. Returns the starting node so the UI
    can show what was placed and why before starting the session.
    """
    module = get_module(module_id)  # raises KeyError on unknown module

    estimated_cefr = "B1"
    rationale = "Default placement — no sample or self-report provided."
    if writing_sample and writing_sample.strip():
        try:
            result = await evaluate_placement(module.title, writing_sample)
            # local model under-scores samples; one band of headroom corrects it
            estimated_cefr = _bump_band(result.cefr)
            rationale = result.rationale
        except Exception:
            # AI offline -> degrade to self-report / default, never block onboarding
            if self_report:
                estimated_cefr = SELF_REPORT_CEFR.get(self_report.lower(), "B1")
                rationale = f"Estimated from self-report: {self_report}."
    elif self_report:
        estimated_cefr = SELF_REPORT_CEFR.get(self_report.lower(), "B1")
        rationale = f"Estimated from self-report: {self_report}."

    node = placement_node(module_id, estimated_cefr)
    return {
        "module_id": module_id,
        "module_title": module.title,
        "starting_node": node.id,
        "node_title": node.title,
        "node_cefr": node.cefr,
        "estimated_cefr": estimated_cefr,
        "rationale": rationale,
    }


# ---------- internals ----------

def _require(session_id: str) -> dict:
    state = SessionStore.get(session_id)
    if state is None:
        raise KeyError(f"no active session: {session_id}")
    return state


def _update_progress(state: dict) -> None:
    """Fold the latest score into the clean-pass streak + down-ladder counters.

    Called once per scored turn, before _maybe_advance. A clean pass extends the
    streak and clears the struggle counters; a non-pass breaks the streak, and a
    run of hard fails turns on the scaffold so the next pedagogy turn drops to an
    almost-automatic task."""
    # Fluent-but-off-task guard (council fix #1/#6): a competent English answer
    # to the wrong question scores 0.0, but it is NOT a struggle signal — it must
    # not break the clean streak or trip level_fails/scaffold. The graph routes
    # it to redirect; progress bookkeeping simply ignores the turn.
    diag = state.get("last_diagnosis", {})
    if diag.get("english", True) and not diag.get("on_task", True):
        return
    score = state.get("last_eval_score", 0.0)
    if score >= PASS_SCORE:
        state["clean_streak"] = state.get("clean_streak", 0) + 1
        state["level_fails"] = 0
        state["strengthen_attempts"] = 0
        state["scaffold"] = 0
        return
    state["clean_streak"] = 0
    if score < FAIL_SCORE:
        state["level_fails"] = state.get("level_fails", 0) + 1
    if state.get("level_fails", 0) >= DOWN_LADDER_FAILS:
        state["scaffold"] = 1


async def _maybe_advance(state: dict) -> None:
    """Advance the node on a consecutive clean-pass streak (NOT EMA mastery).

    Records the just-finished node's clean flag, recomputes module pass-rate for
    remediation, then resets every per-node counter for the next node."""
    if state.get("clean_streak", 0) < state.get("advance_streak", ADVANCE_STREAK):
        return

    node_id = state["competency_node"]
    clean = state["attempts"] <= CLEAN_PASS_MAX_ATTEMPTS
    state["node_history"][node_id] = {"attempts": state["attempts"], "clean": clean}
    state["remediation"] = _passrate_below_floor(state)

    nxt = next_node(node_id)
    if nxt is None:
        state["module_done"] = True
        return
    # advance: fresh mastery/attempt/streak counters for the next node
    state["competency_node"] = nxt
    state["current_mastery"] = 0.0
    state["attempts"] = 0
    state["bridge_attempts"] = 0
    state["clean_streak"] = 0
    state["level_fails"] = 0
    state["strengthen_attempts"] = 0
    state["scaffold"] = 0
    state["needs_support"] = False
    state["last_diagnosis"] = {}
    state["last_eval_score"] = 0.0


def _passrate_below_floor(state: dict) -> bool:
    history = state["node_history"]
    if not history:
        return False
    clean = sum(1 for h in history.values() if h["clean"])
    return (clean / len(history)) < PASSRATE_FLOOR


async def _persist_mastery(state: dict) -> None:
    async with _db() as session:
        if session is None:
            return
        try:
            from app.db import repo

            clean = state["attempts"] <= CLEAN_PASS_MAX_ATTEMPTS and (
                state["current_mastery"] >= MASTERY_COMPLETE
            )
            await repo.upsert_mastery(
                session,
                state["user_id"],
                state["competency_node"],
                state["current_mastery"],
                state["attempts"],
                clean,
            )
        except Exception:
            pass


# ---------- conversational helpers (teacher-feel) ----------

def _is_session_end(user_input: str) -> bool:
    """True for a short message that reads as a goodbye, not an answer.

    Length-gated (<=5 words) so a sentence that merely contains 'done' (e.g. an
    actual answer about being done with homework) is not misread as an exit."""
    text = (user_input or "").strip().lower().rstrip(".!")
    if not text or len(text.split()) > 5:
        return False
    return text in _END_PHRASES


def _detect_frustration(user_input: str) -> bool:
    """True when the learner's message carries a discouragement signal."""
    text = (user_input or "").lower()
    return any(p in text for p in _FRUSTRATION_PHRASES)


def _farewell(state: dict) -> str:
    """Warm sign-off naming the learner and a micro-win, no scoring."""
    name = (state.get("learner_name") or "").strip()
    who = f", {name}" if name else ""
    streak = state.get("clean_streak", 0)
    win = (
        f" You strung together {streak} clean passes today — that's real progress."
        if streak >= 1
        else " You showed up and put in the work today, and that's how it starts."
    )
    return (
        f"Great session{who}.{win} Come back when you're ready and we'll pick up "
        "right where we left off. 👋"
    )


def _bump_band(cefr: str) -> str:
    """Nudge a CEFR estimate up one band (cap C2).

    The local qwen model under-scores writing samples, so a raw placement tends
    to under-place a capable learner into trivially easy early nodes. One band of
    headroom corrects this; capped at C2 so it can never overshoot the ladder."""
    order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    try:
        i = order.index(cefr)
    except ValueError:
        return cefr
    return order[min(i + 1, len(order) - 1)]
