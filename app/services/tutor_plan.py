"""Deterministic tutor planning from the latest enforced rubric result."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TutorTurnPlan:
    verdict: str
    next_action: str
    tone_policy: str
    allowed_praise: bool
    focus: str
    stage: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Int01NextTaskDecision:
    attempt_type: str
    kind: str
    next_action: str
    focus: str
    visible_text: str


def attempt_type_for_tutor_plan(plan: Any) -> str | None:
    """Translate the backend-owned next action into the next scored attempt type."""
    action = str(_get(plan, "next_action", "") or "").strip()
    if action in {"request_fresh_independent", "request_consolidation"}:
        return "independent"
    if action in {"request_transfer", "raise_transfer_or_pressure"}:
        return "transfer"
    if action == "request_pressure":
        return "pressure"
    return None


def qualified_core_evidence(state: dict | None, node_id: str | None = None) -> dict | None:
    """Return the authenticated independent parent evidence for pressure work."""
    if not isinstance(state, dict):
        return None
    evidence = state.get("core_qualification_evidence")
    source_id = str(state.get("core_qualification_turn_id") or "")
    expected_node = str(node_id or state.get("competency_node") or "")
    if not isinstance(evidence, dict) or not source_id or not expected_node:
        return None
    if not (
        state.get("core_qualified") is True
        and str(evidence.get("evaluation_id") or "") == source_id
        and evidence.get("user_id") == state.get("user_id")
        and evidence.get("node_id") == expected_node
        and state.get("competency_node") == expected_node
        and evidence.get("attempt_type") == "independent"
        and evidence.get("pass_eligible") is True
        and not evidence.get("blockers")
        and str(evidence.get("learner_answer") or "").strip()
    ):
        return None
    if expected_node.startswith("gd_") and not str(evidence.get("active_topic") or "").strip():
        return None
    return evidence


def validated_tutor_next_action(plan: Any, state: dict | None) -> str:
    """Authorize a planned stage transition against its persisted parent evidence."""
    action = str(_get(plan, "next_action", "") or "").strip()
    allowed = {
        "request_fresh_independent",
        "request_transfer",
        "request_pressure",
        "request_consolidation",
        "raise_transfer_or_pressure",
    }
    if action not in allowed:
        return action
    if action in {"request_pressure", "request_consolidation"} and not qualified_core_evidence(state):
        return "request_fresh_independent"
    return action


def validated_attempt_type_for_tutor_plan(plan: Any, state: dict | None) -> str | None:
    if not isinstance(plan, dict) or not str(_get(plan, "next_action", "") or "").strip():
        return None
    return attempt_type_for_tutor_plan({"next_action": validated_tutor_next_action(plan, state)})


def _int01_requalification_decision() -> Int01NextTaskDecision:
    return Int01NextTaskDecision(
        attempt_type="independent",
        kind="fresh_independent",
        next_action="request_fresh_independent",
        focus="re-establish a qualified core pitch before pressure",
        visible_text=(
            "Your current answer is complete, but I need one grounded pitch before I can "
            "challenge the evidence. Introduce yourself again using a different real "
            "achievement, with your role, proof, and direction all clear."
        ),
    )


def int01_decision_for_planned_action(
    result: Any,
    state: dict | None,
    plan: Any,
) -> Int01NextTaskDecision | None:
    """Resolve the evaluator's pre-credit int01 plan without projecting counters again."""
    state = state or {}
    if (
        state.get("task_type") != "interview_prep"
        or state.get("competency_node") != "int_01_elevator_pitch"
        or not _get(result, "english", True)
        or not _get(result, "on_task", True)
        or not _get(result, "pass_eligible", False)
        or list(_get(result, "required_missing", []) or [])
        or list(_get(result, "blockers", []) or [])
    ):
        return None

    if str(_get(plan, "verdict", "") or "") != "independent_pass":
        return _int01_requalification_decision()
    requested_action = str(_get(plan, "next_action", "") or "")
    action = validated_tutor_next_action(plan, state)
    if action == "request_fresh_independent" and requested_action != action:
        return _int01_requalification_decision()
    decisions = {
        "request_fresh_independent": Int01NextTaskDecision(
            attempt_type="independent",
            kind="fresh_independent",
            next_action="request_fresh_independent",
            focus="use a fresh achievement without changing the existing pitch",
            visible_text=(
                "Your role, proof, and direction are covered. Keep the existing pitch. "
                "Next task: Introduce yourself again using a different real achievement "
                "from your own experience."
            ),
        ),
        "request_transfer": Int01NextTaskDecision(
            attempt_type="transfer",
            kind="transfer",
            next_action="request_transfer",
            focus="use a different achievement for a different audience",
            visible_text=(
                "Your role, proof, and direction are covered. Keep the existing pitch "
                "unchanged. Next task: Create a second 30-second introduction for a "
                "non-technical hiring manager in a different context. Use a different "
                "achievement from your own experience while preserving the "
                "role-proof-direction structure."
            ),
        ),
        "request_pressure": Int01NextTaskDecision(
            attempt_type="pressure",
            kind="pressure",
            next_action="request_pressure",
            focus="answer one repeatability or scaling pushback from your own evidence",
            visible_text=(
                "Your role, proof, and direction are covered. Return to the earlier pitch "
                "you established before the audience-change version. Next task: "
                "A skeptical interviewer asks, 'How do I know this result "
                "would repeat or scale beyond one situation?' Answer that one pushback "
                "using only evidence from your own experience."
            ),
        ),
        "request_consolidation": Int01NextTaskDecision(
            attempt_type="independent",
            kind="consolidation",
            next_action="request_consolidation",
            focus="complete one bounded delivery check without changing the pitch",
            visible_text=(
                "Your role, proof, and direction are covered. Keep the existing pitch. "
                "Next task: Deliver the existing pitch once without changing it, then "
                "identify the single piece of your own evidence that makes it credible."
            ),
        ),
    }
    return decisions.get(action) or _int01_requalification_decision()


def decide_int01_next_task(
    result: Any,
    state: dict | None = None,
) -> Int01NextTaskDecision | None:
    state = state or {}
    if (
        state.get("task_type") != "interview_prep"
        or state.get("competency_node") != "int_01_elevator_pitch"
        or not _get(result, "english", True)
        or not _get(result, "on_task", True)
        or not _get(result, "pass_eligible", False)
        or list(_get(result, "required_missing", []) or [])
        or list(_get(result, "blockers", []) or [])
    ):
        return None

    current_attempt = str(_get(result, "attempt_type", "independent") or "independent")
    if current_attempt not in {"independent", "transfer", "pressure"}:
        return None

    projected_independent = int(state.get("independent_passes") or 0) + (
        1 if current_attempt == "independent" else 0
    )
    projected_transfer = int(state.get("transfer_passes") or 0) + (
        1 if current_attempt == "transfer" else 0
    )
    projected_pressure = int(state.get("pressure_passes") or 0) + (
        1 if current_attempt == "pressure" else 0
    )
    projected_core_qualified = bool(state.get("core_qualified")) or projected_independent >= 2

    if current_attempt == "independent" and not projected_core_qualified:
        return int01_decision_for_planned_action(
            result,
            state,
            {"verdict": "independent_pass", "next_action": "request_fresh_independent"},
        )
    if current_attempt == "independent":
        return int01_decision_for_planned_action(
            result,
            state,
            {"verdict": "independent_pass", "next_action": "request_transfer"},
        )
    if current_attempt == "transfer" and projected_transfer >= 1:
        if not qualified_core_evidence(state, "int_01_elevator_pitch"):
            return _int01_requalification_decision()
        return int01_decision_for_planned_action(
            result,
            state,
            {"verdict": "independent_pass", "next_action": "request_pressure"},
        )
    if current_attempt == "pressure" and projected_pressure >= 1:
        if not qualified_core_evidence(state, "int_01_elevator_pitch"):
            return _int01_requalification_decision()
        return int01_decision_for_planned_action(
            result,
            state,
            {"verdict": "independent_pass", "next_action": "request_consolidation"},
        )
    return None


def _get(result: Any, key: str, default: Any = None) -> Any:
    if isinstance(result, dict):
        if key == "required_missing":
            return result.get("required_missing", result.get("missing_required_criteria", default))
        return result.get(key, default)
    return getattr(result, key, default)


def _hot_repeat_count(state: dict | None, focus: str) -> int:
    if not state or not focus:
        return 0
    delta = state.get("session_learning_delta")
    if not isinstance(delta, dict):
        return 0
    repeated = delta.get("repeated_issue_counts")
    if not isinstance(repeated, dict):
        return 0
    exact = repeated.get(focus)
    if exact is not None:
        try:
            return int(exact)
        except (TypeError, ValueError):
            return 0
    focus_key = focus.strip().lower()
    for key, value in repeated.items():
        if str(key or "").strip().lower() != focus_key:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    return 0


def _missing_criterion_repeat_count(state: dict | None, required_missing: list[Any]) -> int:
    counts: list[int] = []
    for criterion in required_missing:
        criterion_id = str(criterion or "").strip()
        if criterion_id:
            counts.append(_hot_repeat_count(state, f"criterion:{criterion_id}"))
    return max(counts) if counts else 0


def build_tutor_turn_plan(result: Any, state: dict | None = None, *, scaffolded: bool = False) -> TutorTurnPlan:
    if not _get(result, "english", True):
        return TutorTurnPlan(
            verdict="clarify_language",
            next_action="ask_for_english_retry",
            tone_policy="supportive_direct",
            allowed_praise=False,
            focus="answer in English",
            stage="repair",
        )
    if not _get(result, "on_task", True):
        return TutorTurnPlan(
            verdict="redirect",
            next_action="bring_back_to_task",
            tone_policy="neutral_corrective",
            allowed_praise=False,
            focus=_get(result, "next_focus", "") or "answer the active prompt",
            stage="redirect",
        )
    required_missing = list(_get(result, "required_missing", []) or [])
    if required_missing:
        focus = _get(result, "next_focus", "") or "fix the missing required criterion"
        prior_repeats = max(
            _hot_repeat_count(state, str(focus)),
            _missing_criterion_repeat_count(state, required_missing),
        )
        if prior_repeats >= 1:
            return TutorTurnPlan(
                verdict="repeat_gap",
                next_action="micro_drill_then_rewrite",
                tone_policy="direct_no_praise_supportive",
                allowed_praise=False,
                focus=f"{focus} (repeated {prior_repeats + 1}x this session)",
                stage="adaptive_repair",
            )
        return TutorTurnPlan(
            verdict="partial",
            next_action="rewrite",
            tone_policy="direct_no_praise",
            allowed_praise=False,
            focus=focus,
            stage="guided_revision",
        )
    if scaffolded and _get(result, "pass_eligible", False):
        return TutorTurnPlan(
            verdict="guided_success",
            next_action="retry_without_scaffold",
            tone_policy="warm_but_not_mastery",
            allowed_praise=False,
            focus=_get(result, "next_focus", "") or "repeat independently",
            stage="scaffold",
        )
    int01_decision = decide_int01_next_task(result, state)
    if int01_decision is not None:
        return TutorTurnPlan(
            verdict="independent_pass",
            next_action=int01_decision.next_action,
            tone_policy="measured_forward",
            allowed_praise=False,
            focus=int01_decision.focus,
            stage=(
                "practice"
                if int01_decision.focus.startswith("re-establish a qualified core")
                else "challenge"
            ),
        )
    if _get(result, "pass_eligible", False):
        current_attempt = str(_get(result, "attempt_type", "independent") or "independent")
        if current_attempt == "independent":
            projected_independent = int((state or {}).get("independent_passes") or 0) + 1
            if projected_independent < 2:
                return TutorTurnPlan(
                    verdict="independent_pass",
                    next_action="request_fresh_independent",
                    tone_policy="measured_no_celebration",
                    allowed_praise=False,
                    focus="demonstrate the same skill with a different learner-owned example",
                    stage="practice",
                )
            return TutorTurnPlan(
                verdict="independent_pass",
                next_action="request_transfer",
                tone_policy="measured_no_celebration",
                allowed_praise=False,
                focus="apply the same skill in a meaningfully different realistic context",
                stage="challenge",
            )
        if current_attempt == "transfer":
            if not qualified_core_evidence(state):
                return TutorTurnPlan(
                    verdict="independent_pass",
                    next_action="request_fresh_independent",
                    tone_policy="measured_forward",
                    allowed_praise=False,
                    focus="re-establish a qualified core answer before pressure",
                    stage="practice",
                )
            return TutorTurnPlan(
                verdict="independent_pass",
                next_action="request_pressure",
                tone_policy="stretch",
                allowed_praise=False,
                focus="defend the qualified core answer against one realistic pushback using learner-owned evidence",
                stage="challenge",
            )
        if current_attempt == "pressure":
            if not qualified_core_evidence(state):
                return TutorTurnPlan(
                    verdict="independent_pass",
                    next_action="request_fresh_independent",
                    tone_policy="measured_forward",
                    allowed_praise=False,
                    focus="re-establish a qualified core answer before consolidation",
                    stage="practice",
                )
            return TutorTurnPlan(
                verdict="independent_pass",
                next_action="request_consolidation",
                tone_policy="measured_forward",
                allowed_praise=bool(_get(result, "mastery_eligible", False)),
                focus="consolidate the skill once without changing the proven answer",
                stage="consolidation",
            )
    if _get(result, "mastery_eligible", False):
        return TutorTurnPlan(
            verdict="independent_pass",
            next_action="raise_transfer_or_pressure",
            tone_policy="stretch",
            allowed_praise=True,
            focus=_get(result, "next_focus", "") or "prove transfer",
            stage="challenge",
        )
    return TutorTurnPlan(
        verdict="not_yet",
        next_action="reteach_required_gap",
        tone_policy="corrective_supportive",
        allowed_praise=False,
        focus=_get(result, "next_focus", "") or "meet the required rubric criterion",
        stage="repair",
    )
