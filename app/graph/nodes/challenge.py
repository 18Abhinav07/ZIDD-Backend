"""challenge node — near-mastery: push a harder, realistic variant."""
from app.ai.calls import GROQ_70B, GenSpec
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_challenge_prompt, coach_view
from app.content.registry import get_node


async def challenge_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    prompt = build_challenge_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
    )
    spec = GenSpec(provider="groq", model=GROQ_70B, prompt=prompt, kind="challenge")
    return {"pending": spec, "last_route": "challenge"}
