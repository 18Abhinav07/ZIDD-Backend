"""Blackboard: shared group memory for the writers'-room simulation.

All functions are pure — they return a NEW Blackboard dict and never mutate
their input. Callers can rely on value semantics.
"""
from typing import TypedDict

from app.ai.schemas import DirectorDecision

_DEFAULT_TENSION = 0.3
_DEFAULT_QUALITY = 0.5
# Group memory is a rolling window, not an archive: only the most recent
# unresolved threads ride into the director prompt. Without this bound the list
# (and the rendered "Open threads" prompt line) grows one entry per turn for the
# whole session, bloating the context every round of a long GD.
_MAX_OPEN_THREADS = 8


class Blackboard(TypedDict):
    topic: str
    phase: str              # opening | probing | pressure | winddown
    tension: float          # current, 0.0-1.0
    turn: int               # director turns taken
    covered: list[str]      # subtopics / competencies probed
    open_threads: list[str] # raised, not yet resolved
    positions: dict[str, str]   # GD-only: speaker_id -> stance (empty in interview)
    last_quality: float     # last answer_quality from the director
    qualities: list[float]  # EVERY round's answer_quality, for the whole-session score blend
    last_speaker: str       # speaker_id of the voice that last spoke (anti-repetition)


_ACTION_TO_PHASE: dict[str, str] = {
    "probe_deeper": "probing",
    "pivot_topic": "probing",
    "escalate_pressure": "pressure",
    "wind_down": "winddown",
}


def new_blackboard(topic: str) -> Blackboard:
    """Return a fresh Blackboard for the given topic."""
    return Blackboard(
        topic=topic,
        phase="opening",
        tension=_DEFAULT_TENSION,
        turn=0,
        covered=[],
        open_threads=[],
        positions={},
        last_quality=_DEFAULT_QUALITY,
        qualities=[],
        last_speaker="",
    )


def apply_decision(
    bb: Blackboard,
    decision: DirectorDecision,
    count_quality: bool = True,
    count_turn: bool = True,
) -> Blackboard:
    """Return a new Blackboard reflecting the Director's decision.

    - phase mapped from decision.action
    - tension clamped to [0.0, 1.0]; answer_quality (stored as last_quality) also clamped to [0.0, 1.0]
    - turn incremented by 1 only when count_turn is True
    - intent appended to covered
    - the clamped answer_quality appended to `qualities` (the per-round series the
      whole-session score blends over) ONLY when `count_quality` is True;
      `last_quality` holds only the most recent
    - all other keys carried over unchanged

    `count_quality` exists for the LLM-outage path: when the Director call fails,
    decide_round substitutes a `_fallback_decision` whose answer_quality is a
    static placeholder (the last real read carried forward, or 0.5), NOT a fresh
    read of the learner. Appending that placeholder to `qualities` would let a
    transient outage drag the whole-session score blend toward 0.5 and silently
    down-score a strong learner. The caller passes count_quality=False for a
    fallback round so only GENUINE Director reads enter the blend; the round still
    advances `turn` (so the cap counts it) and carries `last_quality` through.

    Runtime-control turns (confusion, move-on, speaker requests) are different:
    they are not learner answers and scoring excludes them, so callers pass
    count_turn=False as well. The blackboard can still carry the updated phase,
    tension, and intent so the simulation stays coherent without burning a
    scored round.
    """
    quality = max(0.0, min(1.0, decision.answer_quality))
    prior_qualities = bb.get("qualities", [])
    turn = bb["turn"] + (1 if count_turn else 0)
    return Blackboard(
        topic=bb["topic"],
        phase=_ACTION_TO_PHASE[decision.action],
        tension=max(0.0, min(1.0, decision.tension)),
        turn=turn,
        covered=bb["covered"] + [decision.intent],
        open_threads=list(bb["open_threads"]),
        positions=dict(bb["positions"]),
        last_quality=quality,
        qualities=prior_qualities + [quality] if count_quality else list(prior_qualities),
        last_speaker=bb.get("last_speaker", ""),
    )


def note_turn(bb: Blackboard, speaker_id: str, text: str) -> Blackboard:
    """Return a new Blackboard recording what speaker_id just said.

    - text appended to open_threads, capped to the most recent _MAX_OPEN_THREADS
      (a rolling window: older threads drop off so the director prompt stays bounded)
    - positions[speaker_id] set to text (captures GD stances; harmless in interview)
    - last_speaker set to speaker_id so the next round can avoid repeating it
    - all other keys carried over unchanged
    """
    new_positions = dict(bb["positions"])
    new_positions[speaker_id] = text
    return Blackboard(
        topic=bb["topic"],
        phase=bb["phase"],
        tension=bb["tension"],
        turn=bb["turn"],
        covered=list(bb["covered"]),
        open_threads=(bb["open_threads"] + [text])[-_MAX_OPEN_THREADS:],
        positions=new_positions,
        last_quality=bb["last_quality"],
        qualities=list(bb.get("qualities", [])),
        last_speaker=speaker_id,
    )
