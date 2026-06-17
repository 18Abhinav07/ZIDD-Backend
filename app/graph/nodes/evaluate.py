"""evaluate node — the only structured AI call in the loop.

Reads the learner's latest answer, scores it (Flash-Lite), updates EMA mastery,
and bumps the scored-attempt counter. Routing happens in route_node off the
score/mastery this node writes. Never runs on turn 0 (entry_router sends the
opening turn straight to teach), but guards defensively anyway.
"""
from app.ai.calls import evaluate_answer
from app.ai.langgate import fails_language_gate
from app.ai.schemas import DiagnosisEval
from app.content.registry import get_node, module_of
from app.graph.route import update_mastery


def _non_english_diagnosis() -> DiagnosisEval:
    """Synthesized verdict for the non-LLM language pre-gate. score=0.0 +
    english=False routes to bridge (route_node), and on_task=False keeps it off
    the fluent-but-off-task redirect path. No LLM call is made."""
    return DiagnosisEval(
        score=0.0,
        understanding="The answer was not in English.",
        errors=["answered in a language other than English"],
        strengths=[],
        next_focus="answer in English",
        on_task=False,
        english=False,
    )


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


_SWING_THRESHOLD = 0.4   # score jump larger than this triggers smoothing
_SWING_ALPHA = 0.6       # weight on current score vs prior (higher = more responsive)


async def evaluate_node(state: dict) -> dict:
    node = get_node(state["competency_node"])
    # Deterministic language pre-gate (Phase 0.2): catch non-English answers on
    # a language-gated module before the unreliable local eval LLM, and skip the
    # LLM call entirely.
    if fails_language_gate(state["user_input"], module_of(state["competency_node"])):
        diagnosis = _non_english_diagnosis()
    else:
        try:
            diagnosis = await evaluate_answer(
                node, state.get("messages", []), state["user_input"]
            )
        except Exception:
            diagnosis = _neutral_diagnosis()

    score = diagnosis.score
    prev = state.get("last_eval_score")
    # Smoothing gate: a >0.4 swing in one turn usually means the model is
    # inconsistent, not that the learner suddenly improved/collapsed. Blend
    # with the prior score to prevent single-turn mastery spikes.
    if prev is not None and prev > 0.0 and abs(score - prev) > _SWING_THRESHOLD:
        score = round(_SWING_ALPHA * score + (1 - _SWING_ALPHA) * prev, 4)

    new_mastery = update_mastery(state["current_mastery"], score)
    return {
        "last_eval_score": score,
        "last_diagnosis": diagnosis.model_dump(),
        "current_mastery": new_mastery,
        "attempts": state.get("attempts", 0) + 1,
    }
