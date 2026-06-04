"""teach node — default move: fix the top error, set next production task."""
from app.ai.calls import GROQ_70B, GenSpec
from app.ai.prompts import build_teach_prompt, coach_view
from app.content.registry import get_node


async def teach_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    prompt = build_teach_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
    )
    spec = GenSpec(provider="groq", model=GROQ_70B, prompt=prompt, kind="teach")
    return {"pending": spec, "last_route": "teach"}
