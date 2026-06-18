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
import asyncio
import json
import os
import re
import uuid
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger("zidd.session")


@dataclass(frozen=True)
class GamePrompt:
    """Gamified fill-blank item yielded instead of a text stream on scaffold turns.

    The API layer maps this to an `event: game_prompt` SSE frame. `answer_key`
    is stripped from the client payload; the learner submits their fill as normal
    text on the next turn, which the graph scores via evaluate_node as usual."""

    type: str
    sentence: str
    hint: str
    context: str
    answer_key: str     # server-side only — not forwarded to the client
    options: list[str] | None = None


@dataclass(frozen=True)
class NodeAdvance:
    """Marker yielded by run_turn between old-node feedback and new-node opening.

    run_turn yields plain string tokens for the pedagogy/opening stream; on an
    advancing turn it yields exactly one NodeAdvance between the OLD-node feedback
    tokens and the NEW-node opening tokens. The API layer maps it to a discrete
    `event: node_advance` SSE frame on the same connection so the UI renders the
    two as separate bubbles (kills level-bleed)."""

    from_node: str
    to_node: str


@dataclass(frozen=True)
class ProgressUpdate:
    """Per-turn mastery signal for the UI progress bar.

    Emitted after every scored turn so the client can update mastery display
    without waiting for the `done` event. The `done` snapshot also carries this
    data — ProgressUpdate lets the UI animate the bar mid-stream."""

    node_id: str
    mastery: float          # current EMA (0-1)
    clean_streak: int       # consecutive clean passes on this node
    attempts: int           # total attempts on this node


@dataclass(frozen=True)
class SessionRecap:
    """Summary frame emitted when module_done=True (all nodes completed).

    Carries the structured recap so the UI can render a 'session complete'
    screen without a second API call. The `done` event fires immediately after."""

    nodes_completed: list   # list of node_id strings from node_history
    weaknesses: list        # weakness_context rows (skill_id, hit_count, last_raw)
    avg_score: float        # current_mastery at close


@dataclass(frozen=True)
class AdaptationCue:
    """Selector rationale surfaced to the UI when the path adapts.

    Emitted on advancing turns (ADVANCE / REMEDIATE) right after ProgressUpdate
    and before NodeAdvance, carrying the selector's decision so the UI can show a
    short 'adapting your path' cue. Read verbatim from state['last_selection'];
    suppressed on REPEAT and on module-done turns (last_selection is None there)."""

    action: str
    band: str
    rationale: str

from app.config import get_settings
from app.ai.calls import (
    GEMINI_FLASH,
    GenSpec,
    evaluate_placement,
    select_next_content,
    stream_generation,
    summarize_session,
)
from app.ai.schemas import SelectionDecision
from app.services.selector import (
    build_selection_snapshot,
    compute_valid_candidates,
    fallback_decision,
    validate_decision,
)
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_opening_prompt, coach_view
from app.ai.test_gen import generate_test_items
from app.content.registry import (
    SELF_REPORT_CEFR,
    all_node_ids,
    get_module,
    get_node,
    grade_placement_node,
    module_of,
    next_node,
    placement_node,
    uses_grade_placement,
)
from app.content.motions import motion_for_node
from app.content.skills import coerce_skill_id
from app.content.task_types import (
    TaskType,
    prep_counterpart,
    task_type_of,
    test_counterpart,
)
from app.graph.build import get_graph
from app.services.simulation_service import score_session, stream_simulation_round
from app.storage import get_storage

# Assessment ("test") task types run the multi-persona SIMULATION instead of the
# coaching graph; the contribution is scored at session end, not coached mid-turn.
_TEST_TASK_TYPES = frozenset({TaskType.INTERVIEW_TEST.value, TaskType.GD_TEST.value})

# Precomputed probe banks (Phase 4 Layer B) go stale as the learner's prep
# weaknesses shift; a bank older than this is treated as a cache miss and the
# TEST start regenerates. One week is long enough that a normal prep->test gap
# reuses the precache, short enough that drifted weaknesses don't fossilize.
TEST_ITEM_TTL = 7 * 24 * 3600  # seconds

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
INCOMPLETE_SCORE = 0.5   # neutral "couldn't assess" marker — never persist a silent 0.0
DOWN_LADDER_FAILS = 2    # this many hard fails -> scaffold HARD (down-ladder)
MAX_INPUT_CHARS = 2000   # cap learner input; protects ctx window + cost

# Short learner messages matching these end the session gracefully.
_END_PHRASES = {
    "done", "stop", "bye", "goodbye", "quit", "exit", "that's all",
    "thats all", "im done", "i'm done", "end", "finish", "no more",
    # temporal goodbye variants ("im done for today" etc.)
    "done for now", "done for today", "im done now", "i'm done now",
    "im done for today", "i'm done for today", "done here",
}

# Pure farewell tokens — they appear ONLY as goodbyes, never inside a real answer,
# so a single occurrence anywhere in the message ends the session (no length gate).
_FAREWELL_TOKENS = {"bye", "goodbye", "ciao", "tata"}
# Ambiguous end words — also ordinary CONTENT words ("I had to quit my last job",
# "we should exit that market segment"), so they only signal a farewell in a SHORT
# message. A bare "quit"/"exit" is still caught by the exact-match _END_PHRASES tier.
_AMBIGUOUS_END_TOKENS = {"quit", "exit"}
# Phrases that signal discouragement -> pivot to support on the next turn.
_FRUSTRATION_PHRASES = (
    "i can't", "i cant", "give up", "too hard", "i'm confused", "im confused",
    "i don't get", "i dont get", "this is hard", "i'm lost", "im lost",
    "i give up", "frustrated", "i can not",
)
# Positive / negated idioms that CONTAIN a frustration phrase but are NOT
# discouragement ("I can't wait", "I'm not frustrated", "hard work pays off").
# These veto a match so the support pivot never patronises a confident learner.
_FRUSTRATION_OVERRIDES = (
    "can't wait", "cant wait", "can not wait", "cannot wait",
    "not frustrated", "n't frustrated", "not confused", "n't confused",
    "not lost", "n't lost", "not hard", "n't hard", "not that hard",
    "not so hard", "not too hard", "n't too hard", "n't so hard",
    "n't that hard", "never give up", "not giving up",
    "won't give up", "wont give up", "don't give up", "dont give up",
    "do not give up", "hard work",
)

# session_id -> TutorState dict
SessionStore: dict[str, dict] = {}

# E24 fix: per-session lock so concurrent turns on ONE session serialize their
# read-modify-write of canonical state (race corrupts messages/counters).
# Per-session, NOT global — different sessions still run concurrently.
_SESSION_LOCKS: dict[str, asyncio.Lock] = {}


def _lock_for(session_id: str) -> asyncio.Lock:
    lock = _SESSION_LOCKS.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _SESSION_LOCKS[session_id] = lock
    return lock

# Keys that are transient within a single turn and must NOT be persisted:
# `pending` holds a GenSpec (a frozen dataclass, not JSON-serializable, and only
# meaningful for the in-flight stream). `pending_game` holds a FillBlankGame dict
# for scaffold turns — consumed this turn, never written to disk. `last_selection`
# is the Spec B selector's read of the most recent advance (action/band/rationale),
# meaningful only for the current turn's adaptation cues — not persisted.
_TRANSIENT_KEYS = ("pending", "pending_game", "last_selection")


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
            state.setdefault(k, None)   # restore transient keys stripped at save
    SessionStore.update(data)


def _new_state(
    user_id: str,
    session_id: str,
    node_id: str,
    memory_context: list,
    learner_name: str = "",
    weakness_context: list | None = None,
    task_type: str = "",
    sim_topic: str = "",
) -> dict:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "competency_node": node_id,
        "task_type": task_type,
        "user_input": "",
        # TEST-mode simulation state (empty/None for coaching sessions): the topic
        # the panel debates, and the persona roster cached after the first round.
        "sim_topic": sim_topic,
        "personas": None,
        "blackboard": None,
        # Precomputed/loaded assessment probe bank (list[dict]); empty for
        # coaching sessions. Hydrated at TEST start from the precache or a
        # synchronous regeneration. Persisted (not a transient key).
        "probe_items": [],
        "current_mastery": 0.0,
        "turn_count": 0,
        "messages": [],
        # True once the fresh-session opening has been streamed (stream_opening).
        # The transcript endpoint surfaces it so a browser reload restores the
        # existing transcript instead of replaying a second opening.
        "opening_streamed": False,
        "last_diagnosis": {},
        "last_eval_score": 0.0,
        "bridge_attempts": 0,
        "clarify_attempts": 0,
        "redirect_attempts": 0,
        "attempts": 0,
        # session-scoped attempt counter (NOT restored from storage) so the
        # ceiling-escape (first strong answer -> challenge) is reachable for a
        # returning learner whose lifetime `attempts` was loaded from disk.
        "session_attempts": 0,
        # pre-authored bridge bookkeeping (deterministic grading + no-repeat)
        "pending_answer_key": None,
        "served_bridge_ids": [],
        # set per eval turn; True only when a bridge fill was graded (H1 gate)
        "last_graded_bridge": False,
        "memory_context": memory_context,
        # aggregated prior weaknesses (list of dicts: skill_id/hit_count/last_raw)
        # hydrated at start_session; Phase 1.3 threads it into _memory_block.
        "weakness_context": weakness_context or [],
        "session_summary": None,
        "pending": None,
        "pending_game": None,
        # Spec B: the selector's read of the most recent advance (transient).
        "last_selection": None,
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
        "frustration_turns": 0,   # consecutive turns flagged as frustrated/confused
        "session_over": False,
        # service-only bookkeeping (not consumed by the graph)
        "node_history": {},     # node_id -> {"attempts": int, "clean": bool}
        "remediation": False,
        "module_done": False,
        # Phase 5 gamification level flags (set at the advance boundary):
        "tester_level": False,  # last advance was fast/clean -> harder challenge
        "review_level": False,  # module finished clean -> weakness-summary section
    }


def _seed_sim_topic(node_id: str, weaknesses: list) -> str:
    """Build the assessment simulation topic for a TEST session.

    GROUP DISCUSSION (P0-4): return a CONCRETE debate motion from the motion bank
    — never the node's teach_focus, which is a teaching instruction, not a
    debatable proposition. The motion is stored once and shared verbatim by the
    opening brief, the director, and every persona, so the learner argues exactly
    the motion the panel debates. Weakness pressing for GD now rides probe_items
    (threaded into the director), so it is intentionally NOT folded in here — that
    would leak "probe their weakness: X" into the learner-facing opening.

    INTERVIEW: anchored on the node's teach_focus; the top logged prep weakness is
    folded in as a probe target so the interviewer presses exactly there. Falls
    back to the bare focus when no prep history exists.
    """
    if module_of(node_id) == "group_discussion":
        return motion_for_node(node_id)
    focus = get_node(node_id).teach_focus
    if weaknesses:
        top = weaknesses[0]
        cue = (top.get("last_raw") or top.get("skill_id") or "").strip()
        if cue:
            return f"{focus} Probe the learner's known weakness: {cue}."
    return focus


# ---------- public API ----------

async def start_session(
    user_id: str, node_id: str, learner_name: str = "", test_mode: bool = False
) -> tuple[str, dict]:
    """Create a session, return (session_id, state). Opening msg streamed via
    stream_opening(). Loads prior memory for this node (best-effort).

    `learner_name` (optional) personalizes the coaching directives so the tutor
    addresses the learner by name.

    `test_mode` selects the assessment ("test") TaskType variant for modules
    that have a prep/test split (interview, group_discussion); it is a no-op for
    modules without one. The strict assessment variant then keys behavior pack,
    memory, and weaknesses for this session."""
    if node_id not in all_node_ids():
        raise ValueError(f"unknown competency node: {node_id}")
    session_id = uuid.uuid4().hex
    # task_type is the pedagogy axis (TaskType value) storage keys memory and
    # weaknesses on; module_id is the registry module that owns the node. They
    # diverge for interview/group_discussion (prep vs. test); test_mode picks the
    # assessment variant where one exists, else the coaching variant.
    task_type = task_type_of(node_id, test_mode=test_mode).value
    module_id = module_of(node_id)
    is_test = task_type in _TEST_TASK_TYPES
    # A TEST session logs no per-skill weaknesses of its own — it reads the prep
    # sibling's (gd_test -> gd_prep). For prep/single-mode, prep_counterpart is a
    # no-op, so this keeps the coaching path's behavior unchanged.
    weakness_key = prep_counterpart(task_type)

    memory_context: list = []
    weakness_context: list = []
    current_mastery = 0.0
    attempts = 0

    # Storage dispatcher: LOCAL SQLite when ai_backend=="local" (works OFFLINE,
    # the qwen-dev default), Postgres otherwise. Best-effort: storage hiccups
    # must never block a session from starting.
    try:
        store = get_storage()
        await store.ensure_profile(user_id, learner_name)
        await store.create_session(
            session_id, user_id, task_type, module_id, node_id
        )
        memory_context = await store.load_context(user_id, task_type)
        weakness_context = await store.get_weaknesses(user_id, weakness_key)
        
        # Load progress to continue session
        progression = await store.get_progression(user_id)
        for p in progression:
            if p["node_id"] == node_id:
                current_mastery = p["ema"]
                attempts = p["attempts"]
                break
    except Exception:
        # Best-effort: a storage hiccup must never block a session from starting.
        # But do NOT swallow it silently — that hides store/load failures and
        # runs the assessment with no prior-session memory or weakness targeting.
        # Log with the stack so the degradation is observable, then continue with
        # empty context.
        logger.warning(
            "start_session: storage load failed for user=%s node=%s; "
            "continuing with empty memory/weakness context",
            user_id,
            node_id,
            exc_info=True,
        )
        memory_context = []
        weakness_context = []

    # Source the learner's display name from their stored profile (set at
    # registration) so the coach can address them by name. Isolated + best-effort:
    # a missing or failed profile read must NEVER abort the session or the
    # memory/weakness load above — the coach simply stays nameless. ensure_profile
    # is non-clobbering on an empty name, so a returning learner keeps their name.
    if not learner_name:
        try:
            prof = await get_storage().get_profile(user_id)
            if prof and prof.get("name"):
                learner_name = prof["name"]
        except Exception:
            logger.debug(
                "start_session: profile name lookup failed for user=%s", user_id, exc_info=True
            )

    last_summary = ""
    if attempts > 0:
        for mem in memory_context:
            if mem.get("node_id") == node_id and mem.get("raw"):
                last_summary = mem.get("raw")
                break

    # Seed the assessment topic from the node, sharpened by the learner's top
    # prep weakness so the persona panel probes exactly where they struggled.
    sim_topic = _seed_sim_topic(node_id, weakness_context) if is_test else ""

    state = _new_state(
        user_id,
        session_id,
        node_id,
        memory_context,
        learner_name,
        weakness_context,
        task_type,
        sim_topic,
    )
    
    # Apply loaded progress
    state["current_mastery"] = current_mastery
    state["attempts"] = attempts
    # clean_streak deliberately starts at 0 even for a returning learner who
    # clean-passed this node before. Pre-crediting half of ADVANCE_STREAK let ONE
    # clean answer this session re-advance them (or a single borderline 0.7 trip
    # the clean_streak>=1 challenge gate) without re-proving anything. Retained
    # mastery is still honored: current_mastery loads the prior EMA, and a genuinely
    # strong return (score >= CEILING_SCORE on the first session attempt) still
    # routes straight to challenge via route_node's session_attempts escape,
    # independent of the streak. The learner just re-proves the streak in-session.


    if last_summary:
        state["messages"].append({
            "role": "assistant",
            "content": f"Welcome back! Here is a summary of your previous session on this level:\n\n{last_summary}"
        })
        
    # A TEST session needs its probe bank ready before the first round. Read the
    # precache (computed at the PREP sibling's end_session); on a miss or stale
    # entry, regenerate synchronously so the session still opens with a real bank.
    if is_test:
        state["probe_items"] = await _load_or_generate_probe_items(user_id, task_type)
    SessionStore[session_id] = state
    save_sessions()
    return session_id, state


def _gd_sim_topic(state: dict) -> str:
    """The concrete GD motion to brief in the opening — only for GD assessment
    sessions. For interview/coaching, sim_topic is an instruction/focus, not a
    debatable motion, so the opening stays generic."""
    if state.get("task_type") == TaskType.GD_TEST.value:
        return state.get("sim_topic", "")
    return ""


async def stream_opening(session_id: str) -> AsyncIterator[str]:
    """Stream the lesson opening for a fresh session (turn 0)."""
    state = _require(session_id)
    node = get_node(state["competency_node"])
    prompt = build_opening_prompt(
        node,
        state.get("memory_context", []),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
        sim_topic=_gd_sim_topic(state),
    )
    spec = GenSpec(provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="opening")
    full = []
    async for tok in stream_generation(spec):
        full.append(tok)
        yield tok
    text = "".join(full)
    state["messages"].append({"role": "assistant", "content": text})
    state["turn_count"] += 1
    # Mark the opening as streamed so a reload rehydrates instead of replaying it.
    state["opening_streamed"] = True
    save_sessions()


async def _stream_node_opening(state: dict) -> AsyncIterator[str]:
    """Stream a lesson opening for state's CURRENT node, append it, bump turn.

    Shared by stream_opening (fresh session) and the advance-transition in
    run_turn (desync fix). Falls back to a plain transition line if the stream
    yields nothing so an advance never ends on silence."""
    node = get_node(state["competency_node"])
    prompt = build_opening_prompt(
        node,
        state.get("memory_context", []),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
        sim_topic=_gd_sim_topic(state),
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

    Serializes per session (E24): the whole turn — including the streamed
    generation — runs under a per-session lock so a second turn on the same
    session can't interleave its state read-modify-write with this one. The lock
    is held across yields, so concurrent turns on ONE session queue; different
    sessions are unaffected."""
    async with _lock_for(session_id):
        async for tok in _run_turn_locked(session_id, user_input):
            yield tok


async def _run_turn_locked(session_id: str, user_input: str) -> AsyncIterator[str]:
    """run_turn body — always invoked under the session lock (see run_turn).

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

    # TEST-mode (assessment) turns run a multi-persona SIMULATION, not the
    # coaching graph: record the learner's contribution, stream the panel's next
    # round (Speaker markers + text), capture the spoken text as one assistant
    # turn, and DEFER scoring to end_session (score_session) — no eval, no
    # progression, no advance here.
    if state.get("task_type") in _TEST_TASK_TYPES:
        from app.services.simulation_service import Speaker
        # The sim self-terminated on a prior round (Director close or the hard
        # round cap set session_over). Don't run another round — wind down and
        # point the learner at their scored recap (via /end).
        if state.get("session_over"):
            closing = (
                "That's where we'll close the session. Tap finish to see your "
                "scored feedback and where to focus next."
            )
            state["messages"].append({"role": "assistant", "content": closing})
            save_sessions()
            yield closing
            return
        spoken: list[str] = []
        async for item in stream_simulation_round(state):
            if isinstance(item, Speaker):
                spoken.append(f"\n[{item.name}]: ")
            elif isinstance(item, str):
                spoken.append(item)
            yield item
        text = "".join(spoken).strip()
        if text:
            state["messages"].append({"role": "assistant", "content": text})
        state["turn_count"] += 1
        save_sessions()
        return

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

    # Post-graph affect: LLM diagnosis is more reliable than regex. Upgrade
    # needs_support if the eval flagged frustration/confusion this turn.
    diag_affect = state.get("last_diagnosis", {}).get("affect", "neutral")
    if diag_affect in ("frustrated", "confused"):
        state["needs_support"] = True
        state["frustration_turns"] = state.get("frustration_turns", 0) + 1
    else:
        state["frustration_turns"] = 0

    # Post-graph goodbye: natural farewells ("I need to head out") evade the
    # pre-graph exact-match gate. Check LLM diagnosis and close gracefully.
    if state.get("last_diagnosis", {}).get("goodbye", False):
        state["session_over"] = True
        farewell = _farewell(state)
        state["messages"].append({"role": "assistant", "content": farewell})
        save_sessions()
        yield farewell
        return

    # Gamified path: teach_node produced a FillBlankGame instead of a GenSpec.
    # Yield the game frame directly and skip text streaming for this turn.
    # The learner's next input (filling the blank) is scored by evaluate_node
    # as a normal answer, so no special handling is needed downstream.
    game: dict | None = state.get("pending_game")
    if game is not None:
        yield GamePrompt(
            type=game.get("type", "fill_blank"),
            sentence=game.get("sentence", ""),
            hint=game.get("hint", ""),
            context=game.get("context", ""),
            answer_key=game.get("answer_key", ""),
            options=game.get("options"),
        )
        # Record a minimal assistant turn so conversation history stays valid.
        state["messages"].append({
            "role": "assistant",
            "content": f"[Fill in the blank] {game.get('sentence', '')}",
        })
        state["turn_count"] += 1
        state["pending_game"] = None
    else:
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
        # Fine-grained activity log + weakness aggregation through the dispatcher
        # (LOCAL SQLite offline). Best-effort: never let a tracking write break a
        # turn. Logs the answer at the node it was SCORED on (before advance).
        await _track_turn(state, prev_node)
        _update_progress(state)
        # BACK-07: after exactly DOWN_LADDER_FAILS consecutive hard fails, re-query
        # weaknesses live so the NEXT turn's coach prompt surfaces fresh weak spots.
        # Only fires at the threshold (not every fail after it) to avoid repeated DB
        # round-trips. best-effort — storage failure must not break the turn.
        if state.get("level_fails", 0) == DOWN_LADDER_FAILS:
            await _maybe_refresh_weaknesses(state)
        # Persist CURRENT node mastery before any advance mutates the pointer.
        await _persist_mastery(state)
        await _maybe_advance(state)

        # Emit per-turn mastery update so the UI progress bar animates mid-stream.
        yield ProgressUpdate(
            node_id=prev_node,
            mastery=round(state["current_mastery"], 4),
            clean_streak=state.get("clean_streak", 0),
            attempts=state.get("attempts", 0),
        )

        # Selector rationale cue: surface WHY the path adapted, on advancing
        # turns only. last_selection is None on REPEAT and module-done turns,
        # so this naturally suppresses there. Fires after progress_update and
        # before node_advance so the UI can show the cue then open the new node.
        sel = state.get("last_selection")
        if sel and sel.get("action") in ("ADVANCE", "REMEDIATE"):
            yield AdaptationCue(
                action=sel["action"],
                band=sel.get("band", "standard"),
                rationale=sel.get("rationale", ""),
            )

        if state["module_done"]:
            yield SessionRecap(
                nodes_completed=list(state.get("node_history", {}).keys()),
                weaknesses=state.get("weakness_context", []),
                avg_score=round(state["current_mastery"], 4),
            )
        elif state["competency_node"] != prev_node:
            # Desync fix: the answer advanced us to a new node.
            # We yield NodeAdvance to signal the frontend, but we NO LONGER
            # auto-stream the new opening. The frontend will present a "Next Skill"
            # break and call /opening manually.
            yield NodeAdvance(
                from_node=prev_node, to_node=state["competency_node"]
            )

    save_sessions()


async def end_session(session_id: str) -> str:
    """Back-compat wrapper: close the session and return its closing summary.

    Many callers (scripts, the older tests) depend on the bare-string return.
    `close_session` is the full-payload entry point the /end route uses to also
    surface the scored simulation report."""
    return (await close_session(session_id))["summary"]


async def close_session(session_id: str) -> dict:
    """Summarize/score the session, persist memory, close it out, and return the
    full closing payload: ``{summary, report, score}``.

    For TEST-mode (assessment) sessions the whole transcript is scored once via
    `score_session`, and `report` is the full `SimulationReport` dict — the five
    sub-scores plus strengths and improvements, i.e. the deferred feedback the
    learner earned across the simulation. For coaching ("prep") sessions `report`
    is None and only the summary applies. Returning the report here is the fix for
    the recap that previously discarded every score but the one-line summary."""
    state = SessionStore.get(session_id)
    if state is None:
        return {"summary": "", "report": None, "score": 0.0}
    node = get_node(state["competency_node"])
    # TEST-mode sessions are scored once over the whole transcript (deferred from
    # the streamed rounds); the report's summary is the closing summary and its
    # score is the persisted result. PREP sessions summarise the coaching dialog.
    is_test = state.get("task_type") in _TEST_TASK_TYPES
    avg_score = state.get("current_mastery", 0.0)
    report_dict: dict | None = None
    if is_test:
        try:
            report = await score_session(state)
            summary = report.summary
            avg_score = report.score
            # The full report (sub-scores + strengths + improvements) is the
            # learner-facing payload — persisted to memory below and returned to
            # the /end route so it actually reaches the learner.
            report_dict = report.model_dump()
        except Exception:
            # score_session failed (model/JSON fault) or the learner quit before a
            # scorable transcript existed. Do NOT fall through with avg_score still
            # equal to current_mastery: a TEST session never runs the per-skill EMA,
            # so current_mastery is ~0.0 and persisting it would silently brand the
            # learner with a zero they never earned. Fall back to the director's
            # grounded read (blackboard last_quality) if any round actually ran,
            # else a neutral incomplete marker (mirrors _neutral_diagnosis's 0.5).
            summary = ""
            bb = state.get("blackboard") or {}
            avg_score = (
                bb["last_quality"] if bb.get("turn", 0) > 0 else INCOMPLETE_SCORE
            )
    else:
        try:
            summary = await summarize_session(node, state["messages"])
        except Exception:
            summary = ""

    # Close + persist long-term memory through the dispatcher (LOCAL SQLite
    # offline). Best-effort so a storage hiccup never blocks session teardown.
    try:
        store = get_storage()
        await store.end_session(
            session_id,
            final_summary=summary,
            avg_score=avg_score,
        )
        if summary:
            await store.write_memory(
                state["user_id"],
                session_id,
                state["competency_node"],
                summary,
                state.get("task_type", ""),
                score=avg_score,
            )
    except Exception:
        pass

    # Precache the TEST sibling's probe bank now that this PREP module is done,
    # so a later TEST start opens instantly instead of blocking on generation.
    # No-op for TEST sessions and single-mode modules (no distinct test sibling).
    if not is_test:
        # Best-effort optimization that warms the TEST sibling's probe bank by
        # calling the LLM. Under shared-model load that call can raise — but the
        # session is already scored and persisted above, so a precache failure must
        # NEVER 500 the /end response and lose the learner's report. Swallow + log.
        try:
            await _precache_test_items(state)
        except Exception:
            logger.warning(
                "close_session: probe precache failed for session=%s; "
                "report still returned",
                session_id,
                exc_info=True,
            )

    logger.info(
        "session_end_analytics",
        extra={
            "session_id": session_id,
            "user_id": state.get("user_id"),
            "task_type": state.get("task_type"),
            "node_id": state.get("competency_node"),
            "turn_count": state.get("turn_count", 0),
            "avg_score": avg_score,
            "module_done": state.get("module_done", False)
        }
    )

    state["session_summary"] = summary
    SessionStore.pop(session_id, None)
    _SESSION_LOCKS.pop(session_id, None)  # E24: don't leak a lock per closed session
    save_sessions()
    return {"summary": summary, "report": report_dict, "score": avg_score}


def get_state(session_id: str) -> dict | None:
    return SessionStore.get(session_id)


async def get_progression_map(user_id: str, module_id: str = "communication") -> list[dict]:
    """Progression map for the user for a specific module.
    Returns the full ordered list of nodes with locked/active/mastered status.
    """
    try:
        from app.content.registry import get_module
        module = get_module(module_id)
        
        store = get_storage()
        # db progress
        prog = await store.get_progression(user_id)
        prog_by_node = {p["node_id"]: p for p in prog}
        
        # Check active session
        active = [s for s in SessionStore.values() if s.get("user_id") == user_id]
        curr_node = active[0].get("competency_node") if active else None
        curr_streak = active[0].get("clean_streak", 0) if active else 0

        out = []
        found_active = False

        for node in module.nodes:
            p = prog_by_node.get(node.id)
            mastery = p["ema"] if p else 0.0
            is_complete = bool(p["clean_pass"]) if p else False
            streak = curr_streak if node.id == curr_node else 0

            status = "locked"
            if is_complete:
                status = "mastered"
            elif not found_active:
                status = "active"
                found_active = True
                
            out.append({
                "node_id": node.id,
                "title": node.title,
                "mastery": mastery,
                "clean_streak": streak,
                "status": status,
            })
        
        return out
    except Exception as e:
        import logging
        logging.getLogger("zidd.session").error(f"Error in progression map: {e}")
        return []


async def place_user(
    module_id: str,
    writing_sample: str | None = None,
    self_report: str | None = None,
    grade: int | None = None,
) -> dict:
    """Onboarding placement: pick the STARTING node in a module.

    school_english places by school grade (2-5), not CEFR — a primary ladder,
    not a proficiency continuum (Phase 0.3). For comm/interview/gd, a writing
    sample drives a Flash-Lite CEFR estimate; otherwise the learner's
    self-report bucket (beginner/intermediate/advanced/fluent) maps to a band.
    Falls back to B1 if neither is usable. Returns the starting node so the UI
    can show what was placed and why before starting the session.
    """
    module = get_module(module_id)  # raises KeyError on unknown module

    if uses_grade_placement(module_id):
        g = grade if grade is not None else 2
        node = grade_placement_node(g)
        return {
            "module_id": module_id,
            "module_title": module.title,
            "starting_node": node.id,
            "node_title": node.title,
            "node_cefr": node.cefr,
            "grade": max(2, min(5, g)),
            "rationale": f"Placed by school grade {g}.",
        }

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
    # Non-struggle guards — turns that score 0.0 but are NOT skill failures must
    # not break the clean streak or trip level_fails/scaffold:
    #   * fluent-but-off-task (council fix #1/#6): graph routes to redirect.
    #   * non-English / gibberish (B11/B12, Test-fix-01): graph routes to clarify;
    #     not producing English is a comprehension gap, not a failed attempt.
    diag = state.get("last_diagnosis", {})
    if not diag.get("english", True):
        return
    # Competent English again: the consecutive non-English run that drives the
    # clarify cap is broken, so refund clarify_attempts (P1, mirrors the redirect
    # refund below). This sits ABOVE the on_task guard on purpose — producing
    # English ends the clarify streak whether or not the answer is on-task — and it
    # cannot defeat the cap, because an english=True turn never routes through
    # clarify (clarify only fires, and increments, when english is False, on which
    # turns this function early-returns above without touching the counter).
    state["clarify_attempts"] = 0
    if not diag.get("on_task", True):
        return
    # Back on-task: the fluent-off-task streak is over, so refund the redirect cap
    # (P0-6) — a learner who strayed then returned is not penalized on their next
    # stray.
    state["redirect_attempts"] = 0
    score = state.get("last_eval_score", 0.0)
    if score >= PASS_SCORE:
        # A correct BRIDGE fill (graded deterministically against its answer key,
        # BRIDGE_CORRECT_SCORE == PASS_SCORE) is a scaffolded sub-step, NOT a clean
        # pass at this node: it still breaks the fail streak and refunds the bridge
        # cap (below), but must NOT accrue toward the advance streak — else two
        # scaffolded-down fills would promote a struggling learner to harder
        # content (H1). `last_route` is the wrong signal here (route_node has
        # already moved it past "bridge" for a >= PASS score), so gate on the
        # bridge-grade flag evaluate_node set THIS turn.
        if not state.get("last_graded_bridge"):
            state["clean_streak"] = state.get("clean_streak", 0) + 1
        state["level_fails"] = 0
        state["strengthen_attempts"] = 0
        # Clean pass: the learner climbed out of bridge (sub-0.4) territory, so the
        # consecutive-bridge run is over — refund the bridge cap (P1). Gated on a
        # full PASS, NOT merely score >= FAIL_SCORE: route_node runs BEFORE this
        # fold (graph.ainvoke precedes _update_progress in the turn) and increments
        # bridge_attempts on the same turn it picks bridge, and a >= PASS answer
        # provably never routes to bridge — so resetting here can never wipe a fresh
        # increment and re-open the infinite-bridge soft-lock. Mirrors level_fails /
        # strengthen_attempts, the sibling down-ladder counters that also clear only
        # on a clean pass.
        state["bridge_attempts"] = 0
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
    remediation, then runs the Spec B two-stage selector to pick the next node
    and resets every per-node counter for it.

    Spec B selector (advancement primitive): the deterministic stage
    (`compute_valid_candidates`) narrows the valid next-content set; only when it
    leaves more than one candidate does the single LLM call (`select_next_content`)
    decide. In the linear MVP module there is exactly ONE candidate (the linear
    next node), so the fast path below synthesizes the same ADVANCE decision the
    old `next_node` block produced — no model call — and the reset is byte-for-byte
    the previous behavior. That is why the existing advance tests stay green."""
    # Clear any stale read from a prior turn before the gate so a non-advancing
    # turn reports no selection (transient; never persisted).
    state["last_selection"] = None
    if state.get("clean_streak", 0) < state.get("advance_streak", ADVANCE_STREAK):
        return

    node_id = state["competency_node"]
    clean = state["attempts"] <= CLEAN_PASS_MAX_ATTEMPTS
    state["node_history"][node_id] = {"attempts": state["attempts"], "clean": clean}
    state["remediation"] = _passrate_below_floor(state)

    # Stage 1: deterministic valid candidates. Empty -> module finished.
    candidates = compute_valid_candidates(state)
    if not candidates:
        state["module_done"] = True
        # Module finished above the clean-rate floor -> surface a review section.
        state["review_level"] = not state["remediation"]
        return

    if len(candidates) == 1:
        # Fast path: single valid candidate. Reproduces the old linear advance
        # exactly — no LLM call (Spec B: never call the model with one candidate).
        cand = candidates[0]
        decision = SelectionDecision(
            action=cand["action"],
            next_ref=cand["next_ref"],
            band=cand.get("band", "standard"),
            rationale="single valid candidate",
        )
    else:
        # Stage 2: more than one candidate -> one structured LLM call, then
        # validate/backstop. A model/transport failure never blocks the advance.
        snapshot = build_selection_snapshot(state)
        try:
            decision = await select_next_content(snapshot, candidates)
        except Exception:
            decision = fallback_decision(state, candidates)
        decision = validate_decision(decision, candidates, state)

    # Surface the selector's read for this turn's adaptation cues (transient).
    state["last_selection"] = {
        "action": decision.action,
        "band": decision.band,
        "rationale": decision.rationale,
    }

    # REPEAT keeps the learner on the current node: hold position, reset the
    # streak so they must earn the next advance again.
    if decision.action == "REPEAT":
        state["clean_streak"] = 0
        return

    # Fast clean advance (cleared the node within the clean-pass cap) earns a
    # harder tester stretch on the next node; a grind-it-out advance does not.
    state["tester_level"] = clean
    # `review_level` is a per-node SECTION flag set only when a module finishes
    # (above). It is NOT auto-cleared, and level_kind reads it BEFORE tester_level,
    # so a value leaking in from a prior finished module would mask every node in
    # the next module as "review". Reset it here with the rest of the per-node
    # slate so a normal advance always starts the new node section-clean.
    state["review_level"] = False
    # advance: fresh mastery/attempt/streak counters for the next node
    state["competency_node"] = decision.next_ref
    state["current_mastery"] = 0.0
    state["attempts"] = 0
    state["session_attempts"] = 0   # re-arm ceiling-escape at the new node
    state["bridge_attempts"] = 0
    state["clarify_attempts"] = 0
    state["redirect_attempts"] = 0
    state["served_bridge_ids"] = []
    state["pending_answer_key"] = None
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


async def _track_turn(state: dict, node_id: str) -> None:
    """Log the scored answer + aggregate a weakness, through the dispatcher.

    Best-effort: a storage hiccup must never abort a learner's turn. Works
    OFFLINE — get_storage() returns the LOCAL SQLite backend on qwen-dev, so
    turns/weaknesses accumulate even with Postgres down. This is the
    felt-personalization fix: the old _db() path was a silent no-op offline."""
    diag = state.get("last_diagnosis", {})
    score = state.get("last_eval_score", 0.0)
    on_task = diag.get("on_task", True)
    english = diag.get("english", True)
    affect = diag.get("affect", "neutral")
    # Stash the affect/score of THIS scored answer (FIX #4). On an advancing turn,
    # _maybe_advance (called after _track_turn) clears last_diagnosis/last_eval_score
    # BEFORE the SSE "done" frame is built, so the done frame would otherwise show
    # neutral/0.0 instead of the real affect of the answer that advanced. This field
    # is NOT cleared on advance, so _state_snapshot can source the display values here.
    state["last_turn_affect"] = {
        "affect": affect,
        "on_task": on_task,
        "english": english,
        "last_eval_score": score,
    }
    try:
        store = get_storage()
        await store.record_turn(
            state["session_id"],
            state["user_id"],
            node_id,
            score,
            on_task=on_task,
            english=english,
            affect=affect,
        )
        # A genuinely weak answer aggregates a weakness row keyed by SkillID.
        # Skip the fluent-but-off-task case (competent English to the wrong
        # question is not a skill weakness — mirrors _update_progress's guard).
        if score < FAIL_SCORE and not (english and not on_task):
            # Non-English answers are a language weakness regardless of next_focus;
            # otherwise coerce the model's focus hint onto the closed taxonomy.
            skill_id = (
                "LANGUAGE_NOT_ENGLISH"
                if not english
                else coerce_skill_id(diag.get("next_focus", ""))
            )
            await store.bump_weakness(
                state["user_id"],
                state.get("task_type", ""),
                skill_id,
                score,
                raw=diag.get("next_focus", ""),
            )
    except Exception:
        pass


async def _load_or_generate_probe_items(user_id: str, task_type: str) -> list[dict]:
    """Probe bank for a TEST session: precache first, else regenerate (sync).

    Reads the bank precomputed at the PREP sibling's end_session, honouring the
    TTL so a drifted entry counts as a miss. On miss/stale, generates inline and
    writes it back so a later start in the same window is fast. Best-effort: any
    storage/generation hiccup degrades to the deterministic fallback bank rather
    than blocking the session from opening. Returns list[dict] (JSON-persistable
    on TutorState); ProbeItem objects are projected via model_dump()."""
    try:
        store = get_storage()
        cached = await store.get_cached_test_items(
            user_id, task_type, max_age=TEST_ITEM_TTL
        )
        if cached:
            return cached
    except Exception:
        store = None
    items = await generate_test_items(user_id, task_type)
    dicts = [it.model_dump() for it in items]
    if store is not None:
        try:
            await store.cache_test_items(user_id, task_type, dicts)
        except Exception:
            pass
    return dicts


async def _precache_test_items(state: dict) -> None:
    """At PREP end, precompute + cache the TEST sibling's probe bank.

    Resolves the distinct test sibling via test_counterpart; value-equality means
    the module has no assessment variant (single-mode / already a test value), so
    there is nothing to precache and we skip. Best-effort: never let a precache
    miss break session teardown."""
    prep_tt = state.get("task_type", "")
    test_tt = test_counterpart(prep_tt)
    if test_tt == prep_tt:
        return  # no distinct TEST sibling -> nothing to precache
    try:
        items = await generate_test_items(state["user_id"], test_tt)
        await get_storage().cache_test_items(
            state["user_id"], test_tt, [it.model_dump() for it in items]
        )
    except Exception:
        pass


async def _maybe_refresh_weaknesses(state: dict) -> None:
    """Re-query the weakness table and update state at the hard-fail threshold.

    Called once per node when level_fails first reaches DOWN_LADDER_FAILS.
    Refreshing here means the NEXT turn's coach prompt gets a live weakness
    snapshot (new bumps from THIS session included), not just the session-start
    load. prep_counterpart normalises test sessions to their prep sibling's key."""
    try:
        store = get_storage()
        task_type = state.get("task_type", "")
        weakness_key = prep_counterpart(task_type)
        fresh = await store.get_weaknesses(state["user_id"], weakness_key)
        if fresh:
            state["weakness_context"] = fresh
    except Exception:
        pass


async def _persist_mastery(state: dict) -> None:
    """Persist current-node mastery via the dispatcher (best-effort, offline-ok)."""
    try:
        clean = state["attempts"] <= CLEAN_PASS_MAX_ATTEMPTS and (
            state["current_mastery"] >= MASTERY_COMPLETE
        )
        await get_storage().upsert_mastery(
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
    """True when the learner's message is a farewell, not an answer.

    Three-tier detection:
    1. Exact-match against _END_PHRASES (≤5-word gate kept for weak tokens
       like "done"/"stop" that appear in real answers).
    2. Token-scan for PURE farewell tokens ("bye", "goodbye", "ciao", "tata") —
       these never appear inside a real answer, so no length gate is needed.
    3. Length-gated scan for AMBIGUOUS end words ("quit", "exit"): they are also
       ordinary content words, so they only end a SHORT message. A substantive
       answer like "I had to quit my previous job because of a relocation" must
       still reach scoring, not be silently discarded as a farewell.
    """
    text = (user_input or "").strip().lower().rstrip(".!,")
    if not text:
        return False

    # Exact-match path (original behaviour, guards against "done with homework")
    if len(text.split()) <= 5 and text in _END_PHRASES:
        return True

    # Token-scan: split on whitespace + strip punctuation from each word
    words = {re.sub(r"[^a-z']", "", w) for w in text.split()}
    if words & _FAREWELL_TOKENS:
        return True
    # "quit"/"exit" only signal a farewell when the whole message is short.
    if len(text.split()) <= 3 and words & _AMBIGUOUS_END_TOKENS:
        return True
    return False


def _detect_frustration(user_input: str) -> bool:
    """True when the learner's message carries a discouragement signal.

    A HIGH-PRECISION pre-gate, not the only signal: the LLM affect read upgrades
    needs_support after the graph runs, so a borderline case this misses is still
    caught next turn. We therefore favour precision. A naive substring scan fired
    support on upbeat messages like "I can't wait to start, this is fun!" and
    "I'm not frustrated at all" — patronising a confident learner. We veto known
    positive/negated idioms (_FRUSTRATION_OVERRIDES) and match phrases on word
    boundaries. Deeply ambiguous literal content (e.g. "I gave up smoking") is
    intentionally left to the LLM affect backstop rather than chased with brittle
    rules.
    """
    text = (user_input or "").lower()
    if any(ov in text for ov in _FRUSTRATION_OVERRIDES):
        return False
    return any(
        re.search(r"\b" + re.escape(p) + r"\b", text) for p in _FRUSTRATION_PHRASES
    )


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
