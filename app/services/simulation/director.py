"""Director pure helpers — no LLM calls, no I/O.

These helpers are used by the future decide_round() function that will call
the LLM; they are kept pure so they can be unit-tested in isolation.
"""
from app.ai.calls import direct_simulation
from app.ai.schemas import DirectorDecision
from app.services.simulation.blackboard import (
    Blackboard,
    _DEFAULT_TENSION,
    _DEFAULT_QUALITY,
    apply_decision,
)


def _next_in_rotation(personas: list[dict], last_speaker: str) -> str:
    """Return the speaker_id AFTER last_speaker in roster order (round-robin).

    The anti-repetition primitive: a degraded round used to default to
    personas[0] (the Moderator in the GD roster), so every fallback round handed
    the floor back to the same voice — the panel read as the Moderator talking to
    itself. Rotating off the last speaker spreads the floor instead. When
    last_speaker is unknown/empty (the very first round), open with personas[0].
    """
    if not personas:
        raise ValueError("personas roster must not be empty")
    ids = [p["speaker_id"] for p in personas]
    if last_speaker in ids:
        return ids[(ids.index(last_speaker) + 1) % len(ids)]
    return ids[0]


def _fallback_decision(bb: Blackboard, personas: list[dict]) -> DirectorDecision:
    """Return a safe default DirectorDecision when the LLM call fails or is unavailable."""
    if not personas:
        raise ValueError("personas roster must not be empty")
    return DirectorDecision(
        action="probe_deeper",
        next_speaker=_next_in_rotation(personas, bb.get("last_speaker", "")),
        intent="Ask the learner to expand on their last point with a concrete example.",
        tension=bb.get("tension", _DEFAULT_TENSION),
        answer_quality=bb.get("last_quality", _DEFAULT_QUALITY),
        should_close=False,
    )


def _snap_speaker(
    next_speaker: str, personas: list[dict], last_speaker: str = ""
) -> str:
    """Return next_speaker if it matches a roster speaker_id, else rotate.

    A valid Director pick is honored as-is (even if it repeats — the Director may
    have a real reason). An invalid/hallucinated speaker_id falls back by ROTATING
    off last_speaker rather than always snapping to personas[0], so a stream of
    bad picks doesn't pin the floor to one voice."""
    if not personas:
        raise ValueError("personas roster must not be empty")
    for persona in personas:
        if persona["speaker_id"] == next_speaker:
            return next_speaker
    return _next_in_rotation(personas, last_speaker)


async def decide_round(
    bb: Blackboard,
    personas: list[dict],
    task_type,
    transcript: str,
    probe_items: list | None = None,
    scenario_config: dict | None = None,
    career_context: dict | None = None,
) -> tuple[Blackboard, dict, DirectorDecision]:
    """Run the Director's beat for one round: decide, snap, apply, resolve.

    The LLM call is the only fallible step; on ANY failure it degrades to a
    deterministic `_fallback_decision` so a round never dead-ends. Returns the
    advanced Blackboard, the resolved speaking persona dict, and the decision
    (its `intent` drives the persona's streamed turn).

    `probe_items` (prep-weakness bank) threads through to the director prompt so
    the panel presses exactly where the learner struggled.
    """
    # Fail fast on an empty roster BEFORE the LLM round-trip. Both
    # _fallback_decision and _snap_speaker raise on an empty roster, but only
    # after the (now-wasted) call — and the except clause would swallow this
    # very ValueError into the fallback, which then re-raises it confusingly.
    # Guard here so the contract violation surfaces cleanly at the boundary.
    if not personas:
        raise ValueError("decide_round requires a non-empty personas roster")
    fell_back = False
    try:
        decision = await direct_simulation(
            bb,
            personas,
            task_type,
            transcript,
            probe_items,
            scenario_config=scenario_config,
            career_context=career_context,
        )
    except Exception:
        decision = _fallback_decision(bb, personas)
        fell_back = True
    speaker_id = _snap_speaker(
        decision.next_speaker, personas, bb.get("last_speaker", "")
    )
    # A fallback decision's answer_quality is a static placeholder, not a real
    # read of the learner — keep it OUT of the score-blend series so an LLM outage
    # cannot deflate the whole-session score (the round still advances `turn`).
    new_bb = apply_decision(bb, decision, count_quality=not fell_back)
    persona = next(p for p in personas if p["speaker_id"] == speaker_id)
    return new_bb, persona, decision
