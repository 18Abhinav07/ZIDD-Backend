"""strengthen node — skill shaky but present: reinforce, ask a close variant."""
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.prompts import build_strengthen_prompt, coach_view
from app.content.registry import get_node


async def strengthen_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    prompt = build_strengthen_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="strengthen"
    )
    return {
        "pending": spec,
        "last_route": "strengthen",
        "strengthen_attempts": state.get("strengthen_attempts", 0) + 1,
    }
