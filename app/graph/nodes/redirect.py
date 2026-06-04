"""redirect node — fluent answer aimed at the WRONG question.

Council fix #1/#6: a competent English answer that does not attempt the assessed
skill scores 0.0 by the ruthless rubric, but the learner is clearly capable, so
scaffolding down (bridge) is wrong. Steer them back to the actual task instead.

Does NOT touch bridge_attempts / level_fails — being off-task is not struggling.
"""
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.prompts import build_redirect_prompt, coach_view
from app.content.registry import get_node


async def redirect_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    prompt = build_redirect_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="redirect"
    )
    return {"pending": spec, "last_route": "redirect"}
