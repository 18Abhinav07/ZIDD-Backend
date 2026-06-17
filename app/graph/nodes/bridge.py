"""bridge node — learner struggling: scaffold DOWN to a smaller sub-step.

Increments bridge_attempts. route_node enforces the 3-attempt cap (council fix
for the infinite-bridge loop): after BRIDGE_ATTEMPT_CAP failed bridges it routes
to teach instead, so this node never runs a 4th consecutive time.
"""
import random
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_bridge_prompt, coach_view
from app.content.registry import get_node


async def bridge_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    
    # Pre-authored scaffolding: if curriculum defines specific bridge exercises,
    # pull one and skip the LLM generation.
    if node.bridge_exercises:
        exercise = random.choice(node.bridge_exercises)
        return {
            "pending_game": exercise.model_dump(),
            "last_route": "bridge",
            "bridge_attempts": state.get("bridge_attempts", 0) + 1,
        }

    # Fallback: prompt the LLM to generate a bridge step on the fly.
    prompt = build_bridge_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="bridge"
    )
    return {
        "pending": spec,
        "last_route": "bridge",
        "bridge_attempts": state.get("bridge_attempts", 0) + 1,
    }

