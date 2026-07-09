"""Persona executor — streams the chosen persona's spoken turn.

This is the STREAMED half of a writers'-room round (the Director already decided
who speaks and with what intent). LLM I/O is delegated to app.ai.calls; this
module only assembles the GenSpec and forwards the token stream.
"""
from app.ai.calls import GEMINI_FLASH, GenSpec, stream_generation
from app.ai.prompts import build_persona_prompt


def stream_persona_turn(
    persona: dict,
    intent: str,
    transcript: str,
    bb: dict,
    roster: list[dict] | None = None,
    scenario_config: dict | None = None,
    career_context: dict | None = None,
    task_type=None,
):
    """Return the async token stream for `persona` speaking toward `intent`.

    `roster` (the full panel) is forwarded to the prompt so the persona can
    address the OTHER voices by name (GD cross-talk); omit it for a one-voice
    interview and the prompt is unchanged.

    Note: a plain `def` (not `async def`) that RETURNS the async generator from
    stream_generation — callers do `async for tok in stream_persona_turn(...)`.
    """
    spec = GenSpec(
        provider="gemini",
        model=GEMINI_FLASH,
        prompt=build_persona_prompt(
            persona,
            intent,
            transcript,
            bb,
            roster,
            scenario_config=scenario_config,
            career_context=career_context,
            task_type=task_type,
        ),
        kind="simulation",
    )
    return stream_generation(spec)
