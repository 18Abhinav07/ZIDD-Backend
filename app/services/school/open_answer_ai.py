"""Isolated provider boundary for canonical School open-answer evaluation."""

from __future__ import annotations

from app.ai.clients import get_gemini_client
from app.ai.local import ollama_structured
from app.ai.structured import call_with_structured_output
from app.config import get_settings
from app.content.school.content_schema import SchoolRubricEvaluation
from app.middleware.rate_limit import llm_semaphore
from app.services.school.open_answer_prompt import build_school_open_answer_prompt


def _local() -> bool:
    return get_settings().ai_backend == "local"


async def evaluate_school_open_answer(
    activity: dict,
    answer: str,
) -> SchoolRubricEvaluation:
    """Evaluate one School long-writing answer with one provider call."""

    item_id = activity.get("activity_id") or activity.get("item_id")
    if not item_id:
        raise ValueError("school_open_answer_requires_item_id")
    prompt = build_school_open_answer_prompt(
        item_id=item_id,
        skill_ids=activity["skill_ids"],
        task_prompt=activity.get("task_prompt") or activity.get("prompt") or "",
        passage=activity.get("passage"),
        learner_answer=answer,
        rubric_criteria=activity["rubric_criteria"],
    )
    async with llm_semaphore:
        if _local():
            return await ollama_structured(
                prompt,
                SchoolRubricEvaluation,
                timeout=None,
            )
        client = get_gemini_client()
        return await call_with_structured_output(
            client,
            prompt,
            SchoolRubricEvaluation,
        )


__all__ = ["build_school_open_answer_prompt", "evaluate_school_open_answer"]
