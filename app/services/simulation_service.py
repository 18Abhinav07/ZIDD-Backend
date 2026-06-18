"""TEST-mode multi-persona simulation (writers'-room loop).

The coaching ("prep") modes run the tutor ladder. The assessment ("test") modes
— interview_test, gd_test — run a *simulation* instead: distinct personas (GD
participants with stances, or an interview panel) speak, the learner responds,
and the contribution is scored, not coached mid-stream.

Each round is a writers'-room beat: the Director (a structured LLM decision over
the shared Blackboard) picks WHO speaks and with WHAT intent, then a single
Persona executor STREAMS that one speaker's turn. The round yields a `Speaker`
marker, a `SimulationState` marker (turn/tension snapshot), then the persona's
text tokens. The API layer maps `Speaker` -> `event: speaker`, `SimulationState`
-> `event: simulation_state`, and plain string tokens -> `event: message`,
mirroring how run_turn maps `NodeAdvance` to `event: node_advance`.
"""
import zlib
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.calls import evaluate_simulation
from app.ai.schemas import SimulationReport
from app.content.task_types import TaskType
from app.services.simulation.blackboard import new_blackboard, note_turn
from app.services.simulation.director import _next_in_rotation, decide_round
from app.services.simulation.persona import stream_persona_turn


@dataclass(frozen=True)
class Speaker:
    """Marker yielded when a new persona begins speaking.

    Mirrors NodeAdvance: the simulation stream is a single sequence of plain
    string tokens interleaved with these markers; the API maps each to an
    `event: speaker` SSE frame so the UI opens a new speaker bubble."""

    speaker_id: str
    name: str


@dataclass(frozen=True)
class SimulationState:
    """Marker yielded once per round with the Director's post-decision snapshot.

    The API maps it to an `event: simulation_state` SSE frame so the UI can show
    round count and tension. Carried alongside the stream like Speaker; the
    session runner forwards it untouched (it is neither a Speaker nor a str).

    `should_close` surfaces the Director's wind-down signal (or the hard round
    cap) to the client so the UI can prompt the learner to finish — previously
    the Director decided this every round and nothing ever read it."""

    turn: int
    speaker_id: str
    tension: float
    should_close: bool = False


# A live simulation must self-terminate even if the Director never calls close.
# After this many rounds the round runner forces should_close and flags the
# session over so a learner cannot loop a TEST sim indefinitely.
MAX_SIM_ROUNDS = 10

# Cross-talk schedule (GD only): how many EXTRA panelists react after the
# Director's chosen speaker, keyed on the phase the discussion is currently in
# (read BEFORE the Director's decision). A GD opens with a single voice so the
# learner isn't dogpiled on their first contribution, then the panel argues with
# itself as it heats up. Interview is always single-voice (one interviewer).
_GD_EXCHANGE_BY_PHASE: dict[str, int] = {
    "opening": 0,
    "probing": 1,
    "pressure": 2,
    "winddown": 0,
}

_EMPTY_TURN_FALLBACK = "Let's stay with that — can you say more?"


def _extra_speakers(prev_phase: str, should_close: bool, task_type: TaskType) -> int:
    """How many reactor turns follow the primary speaker this round.

    Only GD assessments cross-talk; everything else stays single-voice. We never
    pile reactors onto a closing round (the panel should be winding down, not
    escalating)."""
    if task_type != TaskType.GD_TEST or should_close:
        return 0
    return _GD_EXCHANGE_BY_PHASE.get(prev_phase, 1)


def _reactor_intent(prev_name: str) -> str:
    """Templated intent for a reactor jumping in on the previous speaker.

    No extra Director LLM call per reactor — the intent is fixed: react to the
    voice that just spoke, by name, so the turn is genuine panel cross-talk
    rather than another speech aimed at the learner."""
    return (
        f"Jump straight in and react to what {prev_name} just said — address "
        f"{prev_name} by name and either push back hard from your own stance or "
        "sharpen their point, then add one new angle. This is panel cross-talk "
        "between you two, not a reply to the learner."
    )


def _reactor_pool(personas: list[dict]) -> list[dict]:
    """The roster a cross-talk reactor may be drawn from: debaters only.

    Cross-talk is debater-to-debater. The Moderator still reaches the floor as
    the Director's PRIMARY speaker (to facilitate / transition phases), but must
    never be picked as a REACTOR — _reactor_intent ("push back from your stance,
    add one new angle") is a debater move, out of character for a neutral
    facilitator. Without this filter, rotating off the last debater (gd_c) wraps
    to personas[0] == the Moderator, so the facilitator would "jump in" to argue.
    Falls back to the full roster if filtering would leave nothing to rotate
    through (a degenerate roster), since _next_in_rotation rejects an empty list.
    """
    debaters = [p for p in personas if p.get("speaker_id") != "moderator"]
    return debaters or personas


# ===== persona roster ========================================================
#
# A roster is fixed once per session (persisted in state["personas"]) so a
# speaker_id maps to the same voice across rounds — the UI keeps stable bubbles.
# GD participants carry a `stance` so qwen renders genuinely opposed voices in
# the single pass; the interview panel is one neutral interviewer.

_GD_PANEL = [
    {"speaker_id": "moderator", "name": "Moderator", "stance": "neutral facilitator who directs the conversation and transitions speakers"},
    {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"},
    {"speaker_id": "gd_b", "name": "Meera", "stance": "strongly against"},
    {"speaker_id": "gd_c", "name": "Kabir", "stance": "pragmatic middle ground"},
]

_INTERVIEWER = [
    {"speaker_id": "interviewer", "name": "Interviewer", "role": "panel interviewer"},
]

# Per-session interviewer manner so repeat interview sessions don't feel
# identical. One interviewer, varied delivery: the manner is picked
# deterministically from the topic (stable within a session, varies across
# topics) and injected into the persona's speaking prompt by build_persona_prompt.
_INTERVIEWER_STYLES = [
    "warm and encouraging — put the candidate at ease, but still probe for substance",
    "neutral and businesslike — brisk and professional, neither warm nor cold",
    "probing and skeptical — politely press every claim for specifics and evidence",
    "rapid-fire and high-tempo — short, quick follow-ups that test composure under pace",
]


def _interviewer_style(topic: str) -> str:
    """Deterministic per-session interviewer manner from the topic string.

    crc32 (not the salted built-in hash()) so the same topic maps to the same
    manner across processes — a session's interviewer tone stays stable on
    reload, while a different topic can draw a different tone."""
    idx = zlib.crc32((topic or "").encode("utf-8")) % len(_INTERVIEWER_STYLES)
    return _INTERVIEWER_STYLES[idx]


def build_personas(task_type: TaskType, topic: str) -> list[dict]:
    """Deterministic persona roster for a test-mode simulation.

    GD returns the fixed debater panel. INTERVIEW returns the single interviewer
    with a per-session `style` (tonal manner) drawn deterministically from the
    `topic`, so repeat interviews vary in delivery without adding new personas or
    avatars; build_persona_prompt renders that style into the speaking prompt.
    """
    if task_type == TaskType.GD_TEST:
        return [dict(p) for p in _GD_PANEL]
    if task_type == TaskType.INTERVIEW_TEST:
        persona = dict(_INTERVIEWER[0])
        persona["style"] = _interviewer_style(topic)
        return [persona]
    # non-simulation task types still get one neutral voice so the runner is total
    return [{"speaker_id": "examiner", "name": "Examiner", "role": "examiner"}]


def _sim_history(messages: list[dict], limit: int = 8) -> str:
    """Build a readable conversation history for the simulation prompt.

    Critically: label user messages as '[Learner]' so the LLM cannot confuse
    the learner's contributions with one of the named GD personas (e.g. Aarav).
    Assistant-side messages already carry the [Name]: prefix in their stored
    content, so they render cleanly as-is.
    """
    if not messages:
        return "(discussion just opened)"
    # exclude the very last message if it's the current user turn
    m_list = messages[:-1] if messages and messages[-1].get("role") == "user" else messages
    if not m_list:
        return "(discussion just opened)"
    recent = m_list[-limit:]
    lines = []
    for m in recent:
        if m.get("role") == "user":
            lines.append(f"[Learner]: {m['content']}")
        else:
            # assistant content already has [Name]: prefixes from prior rounds
            lines.append(m["content"])
    return "\n".join(lines)


async def _stream_speaker_turn(persona, intent, transcript, bb, roster):
    """Stream one persona's spoken turn, guaranteeing non-empty output.

    Yields the persona's text tokens; if the model returns nothing (a backend
    hiccup) it yields a single re-prompt line so a turn never dead-ends. The
    caller accumulates the yielded tokens to recover the full text."""
    produced = False
    async for tok in stream_persona_turn(persona, intent, transcript, bb, roster):
        produced = produced or bool(tok.strip())
        yield tok
    if not produced:
        yield _EMPTY_TURN_FALLBACK


async def stream_simulation_round(state: dict) -> AsyncIterator[object]:
    """Run one writers'-room round: Director decides, one Persona streams.

    The roster is built once and cached in `state["personas"]`; the Blackboard
    (shared group memory) is created lazily and persisted in `state["blackboard"]`.
    The Director picks WHO speaks and WHAT intent; this round yields a `Speaker`
    marker, a `SimulationState` snapshot, then that speaker's streamed text. A
    director failure falls back to a safe decision inside `decide_round`, and an
    empty persona turn falls back to a single re-prompt line so a round never
    dead-ends.
    """
    messages = state.get("messages", [])
    task_type = TaskType(state["task_type"])
    personas = state.get("personas") or build_personas(
        task_type, state.get("sim_topic", "")
    )
    state["personas"] = personas
    topic = state.get("sim_topic", "")
    transcript = _sim_history(messages, limit=8)
    bb = state.get("blackboard") or new_blackboard(topic)

    # Phase the discussion is in BEFORE the Director moves — drives how many
    # panelists cross-talk this round (a fresh round opens single-voice).
    prev_phase = bb.get("phase", "opening")

    new_bb, persona, decision = await decide_round(
        bb, personas, task_type, transcript, state.get("probe_items")
    )
    speaker_id = persona["speaker_id"]
    # Consume the Director's close signal (or the hard round cap) — previously
    # decided every round and never read, so the sim never self-terminated. On
    # the cap, flag the session over so the runner can wind down.
    should_close = bool(decision.should_close) or new_bb["turn"] >= MAX_SIM_ROUNDS
    if new_bb["turn"] >= MAX_SIM_ROUNDS:
        state["session_over"] = True

    # ----- primary speaker: the Director's chosen voice + intent -----
    # One SimulationState per round (the round snapshot) is emitted here with the
    # primary speaker; reactors below add only Speaker markers + text.
    yield Speaker(speaker_id=speaker_id, name=persona["name"])
    yield SimulationState(
        turn=new_bb["turn"],
        speaker_id=speaker_id,
        tension=new_bb["tension"],
        should_close=should_close,
    )
    running_transcript = transcript
    chunks: list[str] = []
    async for tok in _stream_speaker_turn(
        persona, decision.intent, running_transcript, new_bb, personas
    ):
        chunks.append(tok)
        yield tok
    last_name = persona["name"]
    full_text = "".join(chunks).strip()
    new_bb = note_turn(new_bb, speaker_id, full_text)
    running_transcript = f"{running_transcript}\n[{last_name}]: {full_text}"

    # ----- reactor exchange (GD cross-talk): bounded + deterministic -----
    # Each reactor is a DIFFERENT voice (rotation off whoever just spoke), told
    # to engage the previous speaker by name. Reactors use note_turn only (no
    # apply_decision), so they don't inflate the round count that drives the cap.
    # Rotation is over the debater pool only — the Moderator facilitates as a
    # primary speaker but never jumps in as a cross-talk reactor.
    reactor_pool = _reactor_pool(personas)
    for _ in range(_extra_speakers(prev_phase, should_close, task_type)):
        reactor_id = _next_in_rotation(reactor_pool, new_bb["last_speaker"])
        reactor = next(p for p in personas if p["speaker_id"] == reactor_id)
        yield Speaker(speaker_id=reactor_id, name=reactor["name"])
        r_chunks: list[str] = []
        async for tok in _stream_speaker_turn(
            reactor, _reactor_intent(last_name), running_transcript, new_bb, personas
        ):
            r_chunks.append(tok)
            yield tok
        r_text = "".join(r_chunks).strip()
        new_bb = note_turn(new_bb, reactor_id, r_text)
        running_transcript = f"{running_transcript}\n[{reactor['name']}]: {r_text}"
        last_name = reactor["name"]

    state["blackboard"] = new_bb


_ROUND_QUALITY_WEIGHT = 0.4   # weight on the per-round director reads in the score blend


async def score_session(state: dict) -> SimulationReport:
    """Score a finished TEST simulation over its whole transcript.

    Called at session end (never mid-stream): delegates to the AI boundary's
    evaluate_simulation with the task's strict behavior pack, then GROUNDS that
    single end-of-session pass in the Director's per-round reads of the learner.

    The holistic pass sees only a truncated TAIL of the transcript and is a single
    high-variance sample; the blackboard's `qualities` series carries one
    answer_quality per round across the WHOLE session. We blend LLM-primary
    (weight 1 - _ROUND_QUALITY_WEIGHT) so the rubric-aware score still leads and the
    round mean only corrects truncation/variance — and only when rounds actually
    ran. A fallback-only session (no director rounds) keeps the LLM score alone.
    Only the top-line `score` is blended; the rubric sub-scores stay as scored."""
    task_type = TaskType(state["task_type"])
    report = await evaluate_simulation(
        task_type, state.get("sim_topic", ""), state.get("messages", [])
    )
    qualities = (state.get("blackboard") or {}).get("qualities", [])
    if qualities:
        round_mean = sum(qualities) / len(qualities)
        blended = round(
            (1 - _ROUND_QUALITY_WEIGHT) * report.score
            + _ROUND_QUALITY_WEIGHT * round_mean,
            4,
        )
        report = report.model_copy(update={"score": blended})
    return report
