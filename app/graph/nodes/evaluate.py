"""evaluate node — the only structured AI call in the loop.

Reads the learner's latest answer, scores it (Flash-Lite), updates EMA mastery,
and bumps the scored-attempt counter. Routing happens in route_node off the
score/mastery this node writes. Never runs on turn 0 (entry_router sends the
opening turn straight to teach), but guards defensively anyway.
"""
from app.ai.calls import evaluate_answer
from app.ai.schemas import DiagnosisEval
from app.content.registry import get_node
from app.graph.route import update_mastery


def _neutral_diagnosis() -> DiagnosisEval:
    """Fallback when the structured eval call fails (timeout / bad JSON /
    backend down). A neutral 0.5 keeps the loop alive: route_node sends it to
    teach (not bridge/challenge), so a transient model fault never softlocks the
    session or fakes an advance."""
    return DiagnosisEval(
        score=0.5,
        understanding="(could not assess this turn)",
        errors=[],
        strengths=[],
        next_focus="continue practicing",
    )


async def evaluate_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    try:
        diagnosis = await evaluate_answer(
            node, state.get("messages", []), state["user_input"]
        )
    except Exception:
        diagnosis = _neutral_diagnosis()
    new_mastery = update_mastery(state["current_mastery"], diagnosis.score)
    return {
        "last_eval_score": diagnosis.score,
        "last_diagnosis": diagnosis.model_dump(),
        "current_mastery": new_mastery,
        "attempts": state.get("attempts", 0) + 1,
    }
