"""ease node — graceful off-ramp after a long run of hard fails.

Council fix #3: once the bridge cap AND the give-up threshold (route.GIVE_UP_FAILS)
are both hit, drilling harder only demoralizes. This node reassures, drops the
pressure, and offers a tiny win or the choice to move on — instead of teaching
the same wall forever.
"""
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.prompts import build_ease_prompt, coach_view
from app.content.registry import get_node


async def ease_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    prompt = build_ease_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="ease"
    )
    return {"pending": spec, "last_route": "ease"}
