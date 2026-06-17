"""Director pure helpers — no LLM calls, no I/O.

These helpers are used by the future decide_round() function that will call
the LLM; they are kept pure so they can be unit-tested in isolation.
"""
from app.ai.schemas import DirectorDecision


def _fallback_decision(bb, personas) -> DirectorDecision:
    """Return a safe default DirectorDecision when the LLM call fails or is unavailable."""
    return DirectorDecision(
        action="probe_deeper",
        next_speaker=personas[0]["speaker_id"],
        intent="Ask the learner to expand on their last point with a concrete example.",
        tension=bb.get("tension", 0.3),
        answer_quality=bb.get("last_quality", 0.5),
        should_close=False,
    )


def _snap_speaker(next_speaker: str, personas) -> str:
    """Return next_speaker if it matches a roster speaker_id, else the first persona's id."""
    for persona in personas:
        if persona["speaker_id"] == next_speaker:
            return next_speaker
    return personas[0]["speaker_id"]
