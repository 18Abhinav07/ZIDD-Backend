"""teach node — two paths: gamified widget (scaffold) or conversational stream."""
from app.ai.calls import GROQ_70B, GenSpec, generate_game_item
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_teach_prompt, coach_view
from app.content.registry import get_node

# scaffold depth at which the gamified fill-blank path fires instead of prose.
# scaffold=1 means the learner has triggered DOWN_LADDER_FAILS; giving them a
# concrete, win-able widget replaces open-ended prose which they just failed at.
_GAME_SCAFFOLD_THRESHOLD = 1


async def teach_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    coach = coach_view(state)

    if state.get("scaffold", 0) >= _GAME_SCAFFOLD_THRESHOLD:
        # Gamified path: structured fill-blank, no streaming text this turn.
        # Falls back to conversational if the structured call fails.
        try:
            game = await generate_game_item(
                node, state.get("last_diagnosis", {}), coach
            )
            return {"pending_game": game.model_dump(), "last_route": "teach"}
        except Exception:
            pass  # fall through to conversational on any model failure

    # Conversational path (default): prose recast sandwich, streamed token-by-token.
    prompt = build_teach_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach,
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
    )
    spec = GenSpec(provider="groq", model=GROQ_70B, prompt=prompt, kind="teach")
    return {"pending": spec, "last_route": "teach"}
