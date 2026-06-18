"""evaluate node — the only structured AI call in the loop.

Reads the learner's latest answer, scores it (Flash-Lite), updates EMA mastery,
and bumps the scored-attempt counter. Routing happens in route_node off the
score/mastery this node writes. Never runs on turn 0 (entry_router sends the
opening turn straight to teach), but guards defensively anyway.
"""
from app.ai.behaviors import behavior_for_value
from app.ai.calls import evaluate_answer
from app.ai.langgate import fails_language_gate
from app.ai.schemas import DiagnosisEval
from app.content.registry import get_node, module_of
from app.graph.answer_check import grade_pending_answer, is_giveup, stuck_diagnosis
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


def _result(state: dict, diagnosis: DiagnosisEval, *, smooth: bool,
            clear_pending: bool = False, graded_bridge: bool = False) -> dict:
    """Fold a diagnosis into the per-turn state update.

    `smooth` applies the single-turn swing damper (only for LLM/heuristic scores
    that can be noisy); deterministic grades (a checked answer key, a give-up)
    pass smooth=False because their score is exact and must not be blended away."""
    score = diagnosis.score
    if smooth:
        prev = state.get("last_eval_score")
        # The damper absorbs LLM scoring NOISE, and noise only needs damping in the
        # DOWNWARD direction here: one spuriously low score must not crash a strong
        # learner into bridge/remediation. An UPWARD swing is left at face value — a
        # learner who genuinely recovers (a real 0.2 -> 0.9) has to get full credit
        # this turn (clean pass / cap refund / challenge), and a one-off lucky 0.9
        # still can't fake *sustained* mastery because update_mastery's EMA moves
        # mastery only 30% of the gap per turn (that EMA is the guard, not this).
        # Smoothing BOTH directions used to pull a genuine 0.2 -> 0.9 down to 0.62,
        # permanently below PASS — the sign-blind bug this fixes.
        if prev is not None and prev > 0.0 and prev - score > _SWING_THRESHOLD:
            score = round(_SWING_ALPHA * score + (1 - _SWING_ALPHA) * prev, 4)
    new_mastery = update_mastery(state["current_mastery"], score)
    # `attempts` counts only GENUINE attempts at the skill. A non-English answer
    # (clarify) or a fluent off-task one (redirect) is not an attempt at this
    # competency — counting it would inflate the count that drives the clean-pass
    # determination (a language/topic detour wrongly marking a later pass "not
    # clean") and bury the ceiling-escape (session_attempts>1 on the learner's
    # first genuine strong answer). Give-up and graded bridge items are on-task
    # English attempts, so they still count. mastery needs no such guard: a 0.0
    # score is already flat under update_mastery's raise-floor.
    scored = diagnosis.english and diagnosis.on_task
    out = {
        "last_eval_score": score,
        "last_diagnosis": diagnosis.model_dump(),
        "current_mastery": new_mastery,
        "attempts": state.get("attempts", 0) + (1 if scored else 0),
        # session-scoped sibling of `attempts` (reset on advance, never loaded
        # from storage) — lets the ceiling-escape fire on a returning learner's
        # first strong answer at a node instead of being buried by lifetime count.
        "session_attempts": state.get("session_attempts", 0) + (1 if scored else 0),
        # Set EVERY eval turn (never goes stale): True only when THIS turn graded
        # a served bridge fill, so _update_progress can keep a correct scaffolded
        # fill from accruing toward the advance streak (H1).
        "last_graded_bridge": graded_bridge,
    }
    if clear_pending:
        out["pending_answer_key"] = None   # graded exactly once
    return out


async def evaluate_node(state: dict) -> dict:
    node = get_node(state["competency_node"])

    pending = state.get("pending_answer_key")

    # (P0-3a / M2) A short give-up / "idk" is a STUCK learner, not a fluent
    # off-task one — and it MUST be caught before the pending-key grade below. An
    # "idk" on a served bridge fill is a non-attempt, not a wrong fill: route it
    # stuck->bridge (scaffold down) and CLEAR the pending key so the learner is
    # re-scaffolded, instead of being graded 0.3 wrong on an item they never
    # attempted. The evaluator LLM also over-flags these as off-task, so without
    # this deterministic catch they were misrouted to a HARDER task.
    if is_giveup(state["user_input"]):
        return _result(state, stuck_diagnosis(), smooth=False,
                       clear_pending=bool(pending))

    # (P0-3b) The learner is answering a served pre-authored bridge item
    # (fill_blank / MCQ): grade it deterministically against the answer key. The
    # general LLM rubric never sees the key, so a one-correct-answer item was
    # being fuzzily mis-scored. This branch skips the LLM and the language gate
    # (a one-word fill would otherwise trip langdetect).
    if pending:
        return _result(state, grade_pending_answer(pending, state["user_input"]),
                       smooth=False, clear_pending=True, graded_bridge=True)

    # Deterministic language pre-gate (Phase 0.2): catch non-English answers on
    # a language-gated module before the unreliable local eval LLM, and skip the
    # LLM call entirely.
    if fails_language_gate(state["user_input"], module_of(state["competency_node"])):
        diagnosis = _non_english_diagnosis()
    else:
        try:
            # Thread the per-TaskType grading stance so the evaluator holds a HIGH
            # bar for assessment sims (interview_test/gd_test) and is lenient for a
            # young SCHOOL_ENGLISH learner — the strictness gate was dead until now.
            diagnosis = await evaluate_answer(
                node,
                state.get("messages", []),
                state["user_input"],
                behavior=behavior_for_value(state.get("task_type", "")),
            )
        except Exception:
            diagnosis = _neutral_diagnosis()

    return _result(state, diagnosis, smooth=True)
