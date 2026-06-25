"""clarify node — learner's answer was not competent English (B11/B12, Test-fix-01).

route_node sends english=False here. Bridge would scaffold a competency SKILL the
learner never attempted in English (category error); redirect assumes a capable
off-task answer. Neither fits a non-English / gibberish / empty message — they
need a warm "say that in English" nudge instead.

Does NOT touch bridge_attempts / level_fails — not producing English is not the
same as failing the skill, so it must not count toward give-up / scaffold caps.
"""
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_clarify_prompt, coach_view
from app.content.registry import get_node


async def clarify_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    # 2nd consecutive clarify onward: stop re-asking and model the answer (1.2b).
    # clarify_attempts is the count BEFORE this turn, so >=1 means this is the
    # second stuck turn.
    prompt = build_clarify_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
        model_answer=state.get("clarify_attempts", 0) >= 1,
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="clarify"
    )
    return {
        "pending": spec,
        "last_route": "clarify",
        "clarify_attempts": state.get("clarify_attempts", 0) + 1,
    }
