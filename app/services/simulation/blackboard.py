"""Blackboard: shared group memory for the writers'-room simulation.

All functions are pure — they return a NEW Blackboard dict and never mutate
their input. Callers can rely on value semantics.
"""
from typing import TypedDict

from app.ai.schemas import DirectorDecision


class Blackboard(TypedDict):
    topic: str
    phase: str              # opening | probing | pressure | winddown
    tension: float          # current, 0.0-1.0
    turn: int               # director turns taken
    covered: list[str]      # subtopics / competencies probed
    open_threads: list[str] # raised, not yet resolved
    positions: dict[str, str]   # GD-only: speaker_id -> stance (empty in interview)
    last_quality: float     # last answer_quality from the director


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
        tension=0.3,
        turn=0,
        covered=[],
        open_threads=[],
        positions={},
        last_quality=0.5,
    )


def apply_decision(bb: Blackboard, decision: DirectorDecision) -> Blackboard:
    """Return a new Blackboard reflecting the Director's decision.

    - phase mapped from decision.action
    - tension clamped to [0.0, 1.0]
    - turn incremented by 1
    - last_quality set from decision.answer_quality
    - intent appended to covered
    - all other keys carried over unchanged
    """
    return Blackboard(
        topic=bb["topic"],
        phase=_ACTION_TO_PHASE[decision.action],
        tension=max(0.0, min(1.0, decision.tension)),
        turn=bb["turn"] + 1,
        covered=bb["covered"] + [decision.intent],
        open_threads=list(bb["open_threads"]),
        positions=dict(bb["positions"]),
        last_quality=decision.answer_quality,
    )


def note_turn(bb: Blackboard, speaker_id: str, text: str) -> Blackboard:
    """Return a new Blackboard recording what speaker_id just said.

    - text appended to open_threads
    - positions[speaker_id] set to text (captures GD stances; harmless in interview)
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
        open_threads=bb["open_threads"] + [text],
        positions=new_positions,
        last_quality=bb["last_quality"],
    )
