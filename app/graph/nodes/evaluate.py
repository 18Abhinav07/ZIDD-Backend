"""evaluate node — the only structured AI call in the loop.

Reads the learner's latest answer, scores it (Flash-Lite), updates EMA mastery,
and bumps the scored-attempt counter. Routing happens in route_node off the
score/mastery this node writes. Never runs on turn 0 (entry_router sends the
opening turn straight to teach), but guards defensively anyway.
"""
import re
import logging
from dataclasses import replace

from app.ai.behaviors import behavior_for_value
from app.ai.calls import PrepEvaluationRetryRequired, evaluate_answer, evaluate_prep_answer
from app.ai.langgate import fails_language_gate
from app.ai.schemas import CriterionEval, DiagnosisEval
from app.content.registry import get_node, module_of
from app.content.task_types import TaskType
from app.graph.answer_check import grade_pending_answer, is_giveup, stuck_diagnosis
from app.graph.route import update_mastery
from app.services.rubric_engine import (
    RubricResult,
    build_evaluation_packet,
    gd_answer_is_topic_grounded,
    gd_has_direct_addressee,
    gd_invitation_clause,
    gd_prompt_participant_names,
    resolve_prompt_gd_topic,
)
from app.services.tutor_plan import build_tutor_turn_plan

logger = logging.getLogger("zidd.evaluate")


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
_GD_GATE_SCORE_CAP = 0.6
_STAR_PASS_FLOOR = 0.7


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _cap_diagnosis(diagnosis: DiagnosisEval, error: str, next_focus: str) -> DiagnosisEval:
    errors = list(diagnosis.errors or [])
    if error not in errors:
        errors.append(error)
    return diagnosis.model_copy(update={
        "score": min(float(diagnosis.score or 0.0), _GD_GATE_SCORE_CAP),
        "errors": errors,
        "next_focus": next_focus,
    })


def _has_specific_quiet_invite(text: str, active_topic: str = "", prompt: str = "") -> bool:
    invitation = gd_invitation_clause(text, gd_prompt_participant_names(prompt))
    addressed_participant = gd_has_direct_addressee(invitation)
    lowered = invitation.lower()
    invite = _contains_any(
        lowered,
        ("hear", "take", "view", "thought", "perspective", "share", "add"),
    )
    topic_link = gd_answer_is_topic_grounded(invitation, active_topic)
    optional = bool(re.search(
        r"\b(?:if\s+you(?:'d|\s+would)?\s*(?:like|want|feel\s+comfortable)|"
        r"if\s+you\s+are\s+comfortable|when\s+you(?:'re|\s+are)\s+ready|"
        r"feel\s+free|could\s+you|would\s+you)\b",
        lowered,
        re.IGNORECASE,
    ))
    coercive = bool(re.search(
        r"\b(?:must|have\s+to|right\s+now|everyone\s+needs\s+to)\b",
        lowered,
        re.IGNORECASE,
    ))
    return addressed_participant and invite and topic_link and optional and not coercive


def _apply_gd_minimum_gate(
    node_id: str,
    user_input: str,
    diagnosis: DiagnosisEval,
    *,
    active_topic: str = "",
    active_prompt: str = "",
) -> DiagnosisEval:
    """Cap GD prep scores when a node's non-negotiable behavior is absent.

    The LLM rubric is still responsible for quality, language, and coaching
    nuance. These deterministic gates only prevent obviously incomplete GD moves
    from being counted as a clean pass toward mastery.
    """
    if not (node_id or "").startswith("gd_"):
        return diagnosis
    if not diagnosis.on_task or not diagnosis.english:
        return diagnosis

    text = f" {(user_input or '').lower().strip()} "
    if node_id == "gd_01_stake_position":
        commitment = _contains_any(
            text,
            (
                " i believe ",
                " i think ",
                " my position ",
                " i support ",
                " i oppose ",
                " i agree ",
                " i disagree ",
                " in favour ",
                " in favor ",
                " against ",
                " should ",
                " must ",
                " need to ",
            ),
        )
        hedged = _contains_any(
            text,
            (" maybe ", " not sure ", " hard to say ", " both sides ", " depends "),
        )
        if not commitment or hedged:
            return _cap_diagnosis(
                diagnosis,
                "did not state one clear committed position",
                "state one side clearly before adding reasons",
            )

    if node_id == "gd_02_support_with_evidence":
        support_marker = _contains_any(
            text,
            (
                " because ",
                " for example ",
                " for instance ",
                " such as ",
                " data ",
                " study ",
                " research ",
                " survey ",
                " case ",
                " when ",
                " in my experience ",
                " at ",
            ),
        ) or bool(re.search(r"\d", text))
        if not support_marker:
            return _cap_diagnosis(
                diagnosis,
                "did not add concrete support for the stance",
                "add one fact, example, number, analogy, or experience",
            )

    if node_id == "gd_08_include_quiet" and not _has_specific_quiet_invite(
        user_input,
        active_topic,
        active_prompt,
    ):
        return _cap_diagnosis(
            diagnosis,
            "invitation was too generic and did not link the quieter speaker to the topic",
            "invite the quiet participant by name and connect the invitation to the topic",
        )

    return diagnosis


def _action_signal_count(text: str) -> int:
    actions = re.findall(
        r"\b(?:i\s+)?("
        r"mapped|added|built|created|led|explained|walked|owned|wrote|designed|"
        r"implemented|coordinated|rolled|debugged|investigated|documented|reviewed|"
        r"checked|used|made|reduced|improved|fixed"
        r")\b",
        text,
    )
    return len(set(actions))


def _has_complete_star_shape(text: str) -> bool:
    words = re.findall(r"[a-z0-9']+", text)
    if len(words) < 45:
        return False
    has_situation = _contains_any(
        text,
        (
            " project",
            " problem",
            " issue",
            " incident",
            " challenge",
            " failed ",
            " failure",
            " could see ",
            " had to ",
            " needed to ",
            " during ",
        ),
    )
    has_task = _contains_any(
        text,
        (
            " my task ",
            " i was tasked ",
            " i had to ",
            " i needed to ",
            " goal was ",
            " responsible for ",
            " asked to ",
        ),
    )
    has_actions = _action_signal_count(text) >= 2
    has_result = _contains_any(
        text,
        (
            " as a result ",
            " result ",
            " outcome ",
            " which led ",
            " reduced ",
            " increased ",
            " improved ",
            " faster ",
            " clearer ",
            " could identify ",
            " could see ",
            " shipped ",
            " delivered ",
            " saved ",
            " lowered ",
        ),
    ) or bool(re.search(r"\b\d+[%x]?\b", text))
    return has_situation and has_task and has_actions and has_result


def _apply_interview_minimum_gate(
    node_id: str,
    user_input: str,
    diagnosis: DiagnosisEval,
) -> DiagnosisEval:
    """Prevent complete interview prep answers from being under-scored by LLM noise.

    This is deliberately narrow. It only floors the STAR node when the latest
    answer has a substantial situation/task/action/result shape; partial bridge
    answers, one-line actions, off-task text, and non-English text are unchanged.
    """
    if node_id != "int_04_star_behavioral":
        return diagnosis
    if not diagnosis.on_task or not diagnosis.english:
        return diagnosis
    if float(diagnosis.score or 0.0) >= _STAR_PASS_FLOOR:
        return diagnosis

    text = f" {(user_input or '').lower().strip()} "
    if not _has_complete_star_shape(text):
        return diagnosis

    strengths = list(diagnosis.strengths or [])
    star_strength = "covered the full STAR structure with concrete Situation, Task, Action, and Result"
    if star_strength not in strengths:
        strengths.append(star_strength)
    return diagnosis.model_copy(
        update={
            "score": _STAR_PASS_FLOOR,
            "strengths": strengths,
        }
    )


def _diagnosis_from_rubric(result: RubricResult) -> DiagnosisEval:
    return DiagnosisEval(
        score=float(result.effective_score),
        understanding=result.understanding,
        errors=list(result.errors or []),
        strengths=list(result.strengths or []),
        next_focus=result.next_focus,
        on_task=result.on_task,
        english=result.english,
        affect=result.affect,
        goodbye=result.goodbye,
    )


def _rubric_from_diagnosis(diagnosis: DiagnosisEval, *, attempt_type: str) -> RubricResult:
    """Wrap a deterministic prep diagnosis as rubric evidence.

    Bridge/card fills are not open-ended enough for Qwen. They still need to be
    visible to the new evidence ledger as scaffolded recovery, and must never
    count as independent mastery.
    """
    score = round(max(0.0, min(1.0, float(diagnosis.score or 0.0))), 4)
    pass_eligible = (
        score >= _STAR_PASS_FLOOR
        and bool(diagnosis.on_task)
        and bool(diagnosis.english)
    )
    blockers: list[str] = []
    if not pass_eligible:
        blockers.append("scaffold_incorrect" if attempt_type == "scaffolded" else "not_pass_eligible")
    return RubricResult(
        raw_score=score,
        effective_score=score,
        understanding=diagnosis.understanding,
        criteria=[],
        required_missing=[],
        blockers=blockers,
        strengths=list(diagnosis.strengths or []),
        errors=list(diagnosis.errors or []),
        next_focus=diagnosis.next_focus,
        on_task=bool(diagnosis.on_task),
        english=bool(diagnosis.english),
        affect=diagnosis.affect,
        goodbye=bool(diagnosis.goodbye),
        pass_eligible=pass_eligible,
        mastery_eligible=False,
        attempt_type=attempt_type,
    )


def _fallback_rubric_failure(
    state: dict,
    node,
    diagnosis: DiagnosisEval,
    *,
    blocker: str,
) -> RubricResult:
    """Fail closed with auditable rubric evidence when semantic eval is unavailable."""
    packet = build_evaluation_packet(state, node, state.get("user_input", ""))
    criteria: list[CriterionEval] = []
    required_missing: list[str] = []
    blockers = [blocker]
    for criterion in packet.criteria:
        criterion_id = str(criterion.get("id") or "")
        required = bool(criterion.get("required"))
        if required and criterion_id:
            required_missing.append(criterion_id)
            blockers.append(f"missing_required:{criterion_id}")
        criteria.append(
            CriterionEval(
                id=criterion_id,
                met=False,
                quality=0.0,
                evidence_quote="",
                reason="not evaluated for pass credit" if blocker == "structured_eval_unavailable" else blocker,
            )
        )
    return RubricResult(
        raw_score=float(diagnosis.score or 0.0),
        effective_score=min(float(diagnosis.score or 0.0), 0.2),
        understanding=diagnosis.understanding,
        criteria=criteria,
        required_missing=required_missing,
        blockers=blockers,
        strengths=list(diagnosis.strengths or []),
        errors=list(diagnosis.errors or []),
        next_focus=diagnosis.next_focus,
        on_task=bool(diagnosis.on_task),
        english=bool(diagnosis.english),
        affect=diagnosis.affect,
        goodbye=bool(diagnosis.goodbye),
        pass_eligible=False,
        mastery_eligible=False,
        attempt_type=packet.attempt_type,
    )


def _sync_rubric_with_diagnosis(result: RubricResult, diagnosis: DiagnosisEval) -> RubricResult:
    """Mirror deterministic caps/floors back into the auditable rubric result."""
    effective = round(max(0.0, min(1.0, float(diagnosis.score or 0.0))), 4)
    blockers = list(result.blockers or [])
    if effective < float(result.effective_score or 0.0) and "minimum_gate_cap" not in blockers:
        blockers.append("minimum_gate_cap")
    pass_eligible = (
        effective >= _STAR_PASS_FLOOR
        and not result.required_missing
        and not blockers
        and bool(diagnosis.on_task)
        and bool(diagnosis.english)
    )
    mastery_eligible = (
        bool(result.mastery_eligible)
        and pass_eligible
        and effective >= 0.85
        and result.attempt_type != "scaffolded"
    )
    return replace(
        result,
        effective_score=effective,
        understanding=diagnosis.understanding,
        errors=list(diagnosis.errors or []),
        strengths=list(diagnosis.strengths or []),
        next_focus=diagnosis.next_focus,
        on_task=bool(diagnosis.on_task),
        english=bool(diagnosis.english),
        affect=diagnosis.affect,
        goodbye=bool(diagnosis.goodbye),
        blockers=blockers,
        pass_eligible=pass_eligible,
        mastery_eligible=mastery_eligible,
    )


def _result(state: dict, diagnosis: DiagnosisEval, *, smooth: bool,
            clear_pending: bool = False, graded_bridge: bool = False,
            rubric_result: RubricResult | None = None) -> dict:
    """Fold a diagnosis into the per-turn state update.

    `smooth` applies the single-turn swing damper (only for LLM/heuristic scores
    that can be noisy); deterministic grades (a checked answer key, a give-up)
    pass smooth=False because their score is exact and must not be blended away."""
    raw_score = diagnosis.score
    score = raw_score
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
    non_scorable_integrity = bool(
        rubric_result
        and "minimum_gate:transfer_context" in set(rubric_result.blockers or [])
    )
    mastery_candidate = update_mastery(state["current_mastery"], score)
    if non_scorable_integrity:
        new_mastery = state["current_mastery"]
    elif rubric_result is not None and not rubric_result.pass_eligible:
        new_mastery = min(state["current_mastery"], mastery_candidate)
    else:
        new_mastery = mastery_candidate
    # `attempts` counts only GENUINE attempts at the skill. A non-English answer
    # (clarify) or a fluent off-task one (redirect) is not an attempt at this
    # competency — counting it would inflate the count that drives the clean-pass
    # determination (a language/topic detour wrongly marking a later pass "not
    # clean") and bury the ceiling-escape (session_attempts>1 on the learner's
    # first genuine strong answer). Give-up and graded bridge items are on-task
    # English attempts, so they still count. mastery needs no such guard: a 0.0
    # score is already flat under update_mastery's raise-floor.
    scored = diagnosis.english and diagnosis.on_task and not non_scorable_integrity
    out = {
        "evaluation_retry_required": False,
        "evaluation_integrity_failure": None,
        "last_eval_score": score,
        "last_clean_pass_score": raw_score,
        "last_diagnosis": diagnosis.model_dump(),
        "last_rubric_result": rubric_result.model_dump() if rubric_result else None,
        "tutor_turn_plan": (
            build_tutor_turn_plan(
                rubric_result,
                state,
                scaffolded=graded_bridge,
            ).model_dump()
            if rubric_result
            else None
        ),
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
        "active_prompt_attempt_type": None,
    }
    if clear_pending:
        out["pending_answer_key"] = None   # graded exactly once
    return out


def _is_career_prep_state(state: dict) -> bool:
    return state.get("task_type") in {
        TaskType.INTERVIEW_PREP.value,
        TaskType.GD_PREP.value,
    }


async def evaluate_node(state: dict) -> dict:
    node = get_node(state["competency_node"])

    pending = state.get("pending_answer_key")
    rubric_result: RubricResult | None = None

    # (P0-3a / M2) A short give-up / "idk" is a STUCK learner, not a fluent
    # off-task one — and it MUST be caught before the pending-key grade below. An
    # "idk" on a served bridge fill is a non-attempt, not a wrong fill: route it
    # stuck->bridge (scaffold down) and CLEAR the pending key so the learner is
    # re-scaffolded, instead of being graded 0.3 wrong on an item they never
    # attempted. The evaluator LLM also over-flags these as off-task, so without
    # this deterministic catch they were misrouted to a HARDER task.
    if is_giveup(state["user_input"]):
        diagnosis = stuck_diagnosis()
        rubric_result = (
            _fallback_rubric_failure(state, node, diagnosis, blocker="learner_stuck")
            if _is_career_prep_state(state)
            else None
        )
        return _result(state, diagnosis, smooth=False,
                       clear_pending=bool(pending), rubric_result=rubric_result)

    # (P0-3b) The learner is answering a served pre-authored bridge item
    # (fill_blank / MCQ): grade it deterministically against the answer key. The
    # general LLM rubric never sees the key, so a one-correct-answer item was
    # being fuzzily mis-scored. This branch skips the LLM and the language gate
    # (a one-word fill would otherwise trip langdetect).
    if pending:
        diagnosis = grade_pending_answer(pending, state["user_input"])
        rubric_result = (
            _rubric_from_diagnosis(diagnosis, attempt_type="scaffolded")
            if _is_career_prep_state(state)
            else None
        )
        return _result(
            state,
            diagnosis,
            smooth=False,
            clear_pending=True,
            graded_bridge=True,
            rubric_result=rubric_result,
        )

    # Deterministic language pre-gate (Phase 0.2): catch non-English answers on
    # a language-gated module before the unreliable local eval LLM, and skip the
    # LLM call entirely.
    if fails_language_gate(state["user_input"], module_of(state["competency_node"])):
        diagnosis = _non_english_diagnosis()
        rubric_result = (
            _fallback_rubric_failure(state, node, diagnosis, blocker="non_english")
            if _is_career_prep_state(state)
            else None
        )
    else:
        try:
            # Thread the per-TaskType grading stance so the evaluator holds a HIGH
            # bar for assessment sims (interview_test/gd_test) and is lenient for a
            # young SCHOOL_ENGLISH learner — the strictness gate was dead until now.
            if _is_career_prep_state(state):
                rubric_result = await evaluate_prep_answer(
                    node,
                    state.get("messages", []),
                    state["user_input"],
                    behavior=behavior_for_value(state.get("task_type", "")),
                    career_context=state.get("career_context") or {},
                    state=state,
                )
                diagnosis = _diagnosis_from_rubric(rubric_result)
            else:
                rubric_result = None
                diagnosis = await evaluate_answer(
                    node,
                    state.get("messages", []),
                    state["user_input"],
                    behavior=behavior_for_value(state.get("task_type", "")),
                    career_context=state.get("career_context") or {},
                )
        except PrepEvaluationRetryRequired as exc:
            logger.warning(
                "prep evaluation integrity retry required node=%s session=%s criteria=%s",
                node.id,
                state.get("session_id"),
                ",".join(exc.criterion_ids),
            )
            return {
                "evaluation_retry_required": True,
                "evaluation_integrity_failure": {
                    "code": "required_criteria_omitted",
                    "criterion_ids": list(exc.criterion_ids),
                },
                "pending": None,
                "pending_game": None,
            }
        except Exception as exc:
            if _is_career_prep_state(state):
                logger.exception(
                    "prep structured evaluation failed node=%s session=%s: %s",
                    node.id,
                    state.get("session_id"),
                    exc,
                )
                return {
                    "evaluation_retry_required": True,
                    "evaluation_integrity_failure": {
                        "code": "structured_evaluator_unavailable",
                        "criterion_ids": [],
                    },
                    "pending": None,
                    "pending_game": None,
                }
            diagnosis = _neutral_diagnosis()
            rubric_result = None

    diagnosis = _apply_interview_minimum_gate(node.id, state["user_input"], diagnosis)
    active_prompt = next((
        str(message.get("content") or "")
        for message in reversed(state.get("messages") or [])
        if str(message.get("role") or "") == "assistant"
        and str(message.get("node_id") or "") == node.id
    ), "")
    diagnosis = _apply_gd_minimum_gate(
        node.id,
        state["user_input"],
        diagnosis,
        active_topic=resolve_prompt_gd_topic(state),
        active_prompt=active_prompt,
    )
    if rubric_result is not None:
        rubric_result = _sync_rubric_with_diagnosis(rubric_result, diagnosis)
    return _result(state, diagnosis, smooth=True, rubric_result=rubric_result)
