"""TEST-mode multi-persona simulation (Phase 3.2).

The coaching ("prep") modes run the tutor ladder. The assessment ("test") modes
— interview_test, gd_test — run a *simulation* instead: distinct personas (GD
participants with stances, or an interview panel) speak, the learner responds,
and the contribution is scored, not coached mid-stream.

Cost shape (Challenge guard against N serialized 14B calls): qwen emits ALL
persona turns in ONE streaming pass, each turn line-tagged `[Name]: ...`. This
module's `split_persona_stream` parses those tags *incrementally* — a tag may be
split across stream chunks — and re-emits a discrete `Speaker` marker as each
tagged block begins, then forwards that block's text tokens unchanged. The API
layer maps a `Speaker` to an `event: speaker` SSE frame, mirroring how run_turn
maps `NodeAdvance` to `event: node_advance`.
"""
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.behaviors import behavior_for
from app.ai.calls import (
    GEMINI_FLASH,
    GenSpec,
    evaluate_simulation,
    stream_generation,
)
from app.ai.schemas import SimulationReport
from app.content.task_types import TaskType

# The generic tag regex is kept for documentation / flush usage.
# The per-call parser now builds a known-names regex instead, so it can find
# [Name]: tags *anywhere* in the stream — not only at line-starts. This fixes
# the core bug where the LLM emits multiple personas on one line without \n.
_TAG_RE = re.compile(r"[ \t]*(?:\*\*)*\[([^\]\n]+)\](?:\*\*)*:[ \t]?")

# Maximum length of a speaker tag (e.g. `[Moderator]: ` = ~15 chars).
# We hold back this many chars from the buffer end so a tag split across two
# stream chunks is never mistakenly emitted as raw text.
_TAG_LOOKBEHIND = 50


@dataclass(frozen=True)
class Speaker:
    """Marker yielded by split_persona_stream when a new persona block begins.

    Mirrors NodeAdvance: the simulation stream is a single sequence of plain
    string tokens interleaved with these markers; the API maps each to an
    `event: speaker` SSE frame so the UI opens a new speaker bubble."""

    speaker_id: str
    name: str


async def split_persona_stream(
    token_iter: AsyncIterator[str], personas: list[dict]
) -> AsyncIterator[object]:
    """Parse a persona-tagged token stream into Speaker markers + text tokens.

    Works for both well-formed output (one `[Name]:` per line) AND the
    degenerate case where the LLM runs all personas on a single line with no
    intervening newlines (the root cause of the 'mashed bubble' bug).

    Strategy:
      1. Build a session-scoped regex that matches `[KnownName]:` ANYWHERE.
      2. As tokens accumulate in the buffer, search for the earliest match.
      3. Yield all text before the match, emit a Speaker marker, then continue.
      4. Hold back the last _TAG_LOOKBEHIND chars so a tag split across two
         stream chunks is never prematurely emitted as plain text.
    """
    # Case-insensitive lookup so the LLM capitalisation can't break routing.
    name_to_id_ci: dict[str, str] = {
        p["name"].lower(): p.get("speaker_id", p["name"]) for p in personas
    }
    name_display: dict[str, str] = {
        p["name"].lower(): p["name"] for p in personas
    }

    # Build a regex that matches [Name]: for any known persona, anywhere in text.
    names_alt = "|".join(re.escape(n) for n in name_to_id_ci)
    _known_tag = re.compile(
        rf"[ \t]*(?:\*\*)*\[({names_alt})\](?:\*\*)*:[ \t]?",
        re.IGNORECASE,
    )

    buf = ""

    async for tok in token_iter:
        buf += tok

        # Process all complete speaker segments in the buffer.
        # We keep _TAG_LOOKBEHIND chars at the end as a safety holdback so a
        # tag straddling a chunk boundary doesn't get emitted prematurely.
        while True:
            search_end = max(0, len(buf) - _TAG_LOOKBEHIND)
            m = _known_tag.search(buf, 0, len(buf))  # search whole buf
            if m is None:
                # No tag found — flush everything except the safety window.
                if len(buf) > _TAG_LOOKBEHIND:
                    safe = buf[: len(buf) - _TAG_LOOKBEHIND]
                    if safe:
                        yield safe
                    buf = buf[len(buf) - _TAG_LOOKBEHIND :]
                break

            if m.start() >= len(buf) - _TAG_LOOKBEHIND:
                # Tag found but entirely inside the safety window — wait.
                if m.start() > 0:
                    safe = buf[: m.start()]
                    if safe:
                        yield safe
                    buf = buf[m.start():]
                break

            # Tag found in the safe zone — emit preceding text, then Speaker.
            before = buf[: m.start()]
            if before:
                yield before
            raw_name = m.group(1).strip()
            lower_name = raw_name.lower()
            resolved_id = name_to_id_ci.get(lower_name, raw_name)
            display_name = name_display.get(lower_name, raw_name)
            yield Speaker(speaker_id=resolved_id, name=display_name)
            buf = buf[m.end():]

    # Flush: one last search on whatever remains (no holdback needed).
    if buf:
        m = _known_tag.search(buf)
        if m:
            before = buf[: m.start()]
            if before:
                yield before
            raw_name = m.group(1).strip()
            lower_name = raw_name.lower()
            resolved_id = name_to_id_ci.get(lower_name, raw_name)
            display_name = name_display.get(lower_name, raw_name)
            yield Speaker(speaker_id=resolved_id, name=display_name)
            buf = buf[m.end():]
        if buf:
            yield buf


# ===== persona roster ========================================================
#
# A roster is fixed once per session (persisted in state["personas"]) so a
# speaker_id maps to the same voice across rounds — the UI keeps stable bubbles.
# GD participants carry a `stance` so qwen renders genuinely opposed voices in
# the single pass; the interview panel is one neutral interviewer.

_GD_PANEL = [
    {"speaker_id": "moderator", "name": "Moderator", "role": "system moderator who directs the conversation and transitions speakers"},
    {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"},
    {"speaker_id": "gd_b", "name": "Meera", "stance": "strongly against"},
    {"speaker_id": "gd_c", "name": "Kabir", "stance": "pragmatic middle ground"},
]

_INTERVIEWER = [
    {"speaker_id": "interviewer", "name": "Interviewer", "role": "panel interviewer"},
]


def build_personas(task_type: TaskType, topic: str) -> list[dict]:
    """Deterministic persona roster for a test-mode simulation.

    `topic` is accepted so a future variant can specialise voices to the topic;
    today the roster is fixed per task_type and the topic rides in the prompt.
    """
    if task_type == TaskType.GD_TEST:
        return [dict(p) for p in _GD_PANEL]
    if task_type == TaskType.INTERVIEW_TEST:
        return [dict(p) for p in _INTERVIEWER]
    # non-simulation task types still get one neutral voice so the runner is total
    return [{"speaker_id": "examiner", "name": "Examiner", "role": "examiner"}]


def _persona_block(personas: list[dict]) -> str:
    lines = []
    for p in personas:
        trait = p.get("stance") or p.get("role") or ""
        tail = f" — {trait}" if trait else ""
        lines.append(f"- {p['name']}{tail}")
    return "\n".join(lines)


def _tension_block(tension_level: int) -> str:
    """Escalating cross-persona conflict instructions.

    Level 0: personas each react independently to the learner.
    Level 1: at least one persona directly challenges another's point —
             they disagree and say so, forcing the learner to pick a side.
    Level 2+: cross-fire — personas openly argue with each other, talk over
              ideas, demand the learner mediate or take a firm stand. Heat is
              high but stays civil (no personal attacks).
    """
    if tension_level <= 0:
        return (
            "React to the learner's last point — agree, rebut, or probe. "
            "Each participant responds independently."
        )
    if tension_level == 1:
        return (
            "React to the learner's last point and to each other. At least one "
            "participant must directly challenge another's point by name "
            "(e.g. 'Meera, that's not right because...'). Force the learner to "
            "engage with the disagreement."
        )
    return (
        "The discussion is heated now. Participants openly argue — challenge "
        "each other by name, push back hard on weak points, and demand the "
        "learner take a firm, reasoned position. Keep it civil but intense. "
        "The learner must navigate competing claims, not just answer questions."
    )


def build_simulation_prompt(
    task_type: TaskType,
    personas: list[dict],
    topic: str,
    messages: list[dict],
    user_input: str,
    tension_level: int = 0,
) -> str:
    """Render the single-pass multi-persona prompt.

    All persona turns come back in ONE streaming generation, each line tagged
    `[Name]: ...` so split_persona_stream can attribute text without N calls.
    The behavior pack supplies the assessment voice (strict, no coaching).
    `tension_level` (0-2+) escalates cross-persona conflict across rounds.
    """
    pack = behavior_for(task_type)
    history = _sim_history(messages)
    persona_names = ", ".join(p["name"] for p in personas)
    return (
        f"{pack.persona}\n\n"
        f"This is a live assessment, not coaching. {pack.pedagogy}\n\n"
        f"Topic under discussion: {topic}\n\n"
        f"IDENTITY RULE — you play ONLY these named participants: {persona_names}.\n"
        f"The human learner (marked [Learner] in the transcript) is a SEPARATE person. "
        f"You MUST NOT speak for them, rename them, or merge their words with a persona's words.\n\n"
        f"Participants and their positions:\n{_persona_block(personas)}\n\n"
        f"Conversation so far (DO NOT re-emit this history — only produce the NEXT round):\n{history}\n\n"
        f"The learner just said: {user_input}\n\n"
        f"{_tension_block(tension_level)}\n\n"
        f"CRITICAL OUTPUT FORMAT — follow this exactly:\n"
        f"- Every participant response MUST start on its OWN LINE\n"
        f"- Each line MUST begin with [PersonaName]: (square brackets, colon, space)\n"
        f"- One participant per line — NEVER run two personas into the same paragraph\n"
        f"- DO NOT produce a [Learner]: line — the learner speaks separately\n\n"
        f"Example of correct output:\n"
        f"[Moderator]: Good point. Aarav, what is your take?\n"
        f"[Aarav]: I strongly believe remote work reduces cohesion because...\n"
        f"[Meera]: I disagree — in fact remote work has been shown to...\n\n"
        f"Produce ONLY the next round. Do not re-state the learner's words. Do not give coaching or feedback."
    )


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


def _gd_tension_level(state: dict) -> int:
    """Derive tension level from completed GD rounds (capped at 2).

    0-1 rounds: level 0 — independent reactions.
    2-3 rounds: level 1 — direct cross-persona challenge.
    4+ rounds:  level 2 — heated cross-fire, learner must mediate.
    """
    return min(state.get("gd_turn_count", 0) // 2, 2)


async def stream_simulation_round(state: dict) -> AsyncIterator[object]:
    """Run one simulation round: one model pass, parsed into Speaker + text.

    The roster is built once and cached in `state["personas"]`; the prompt is
    rendered from the topic + learner's latest input; the single streamed
    generation is split into per-persona Speaker markers and text tokens.
    `gd_turn_count` increments each round so tension escalates over time.
    """
    task_type = TaskType(state["task_type"])
    personas = state.get("personas") or build_personas(
        task_type, state.get("sim_topic", "")
    )
    state["personas"] = personas

    tension = _gd_tension_level(state)
    prompt = build_simulation_prompt(
        task_type,
        personas,
        state.get("sim_topic", ""),
        state.get("messages", []),
        state.get("user_input", ""),
        tension_level=tension,
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="simulation"
    )
    async for item in split_persona_stream(stream_generation(spec), personas):
        yield item
    # increment after yielding so the current round's level is already in the prompt
    state["gd_turn_count"] = state.get("gd_turn_count", 0) + 1


async def score_session(state: dict) -> SimulationReport:
    """Score a finished TEST simulation over its whole transcript.

    Called at session end (never mid-stream): delegates to the AI boundary's
    evaluate_simulation with the task's strict behavior pack."""
    task_type = TaskType(state["task_type"])
    return await evaluate_simulation(
        task_type, state.get("sim_topic", ""), state.get("messages", [])
    )
