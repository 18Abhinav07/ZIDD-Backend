"""Backend authorization for one-call assessment turn output."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.ai.schemas import AssessmentTurnCall, DirectorDecision
from app.content.task_types import TaskType
from app.services.assessment_events import append_validity_flag
from app.services.assessment_validity import (
    available_debater_names,
    explicit_requested_speaker_id,
    first_debater,
    gd_panelist_ask_only_text,
    gd_panelist_formulaic_meta_text,
    interview_model_answer_leak,
    low_confidence_persona_request,
    moderator_persona,
    next_active_debater,
    roster_by_id,
    self_label_or_meta_text,
    speaker_is_active,
)
from app.services.gd_discussion_text import gd_persona_fallback_text
from app.services.simulation_config import GD_PERSONA_LIBRARY


@dataclass(frozen=True)
class AuthorizedAssessmentTurn:
    persona: dict[str, Any]
    decision: DirectorDecision
    text: str
    scorable: bool
    repaired: bool
    flags: list[dict[str, Any]]
    analysis: dict[str, Any]


def _speaker_display_name(speaker_id: str) -> str:
    if speaker_id in GD_PERSONA_LIBRARY:
        return GD_PERSONA_LIBRARY[speaker_id]["name"]
    return " ".join(part.capitalize() for part in speaker_id.replace("_", " ").split()) or "that speaker"


def _active_topic(state: dict[str, Any], plan: dict[str, Any]) -> str:
    scenario = state.get("scenario_config") or {}
    return (
        str(plan.get("topic") or scenario.get("topic") or scenario.get("resolved_topic") or state.get("sim_topic") or "").strip()
        or "this topic"
    )


def _latest_learner_text(state: dict[str, Any]) -> str:
    text = str(state.get("user_input") or "").strip()
    if text:
        return text
    for message in reversed(state.get("messages") or []):
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def _latest_learner_has_scorable_substance(state: dict[str, Any]) -> bool:
    text = " ".join(_latest_learner_text(state).split())
    if not text:
        return False
    words = [
        part.strip(".,;:!?\"'()[]{}").lower()
        for part in text.split()
        if any(ch.isalpha() for ch in part)
    ]
    if len(words) < 14:
        return False
    lowered = f" {text.lower()} "
    has_marker = any(
        marker in lowered
        for marker in (
            " because ",
            " evidence",
            " metric",
            " measure",
            " result",
            " impact",
            " risk",
            " support",
            " oppose",
            " guardrail",
            " trade",
        )
    )
    question_only = text.endswith("?") and len(words) < 18 and not has_marker
    return not question_only and (has_marker or len(words) >= 24)


def _map_action(action_type: str, *, should_close: bool) -> str:
    if should_close or action_type == "wind_down":
        return "wind_down"
    if action_type in {"move_to_next_probe", "clarify_current_probe", "repair_unavailable_speaker"}:
        return "pivot_topic"
    if action_type in {"escalate_pressure", "challenge_answer"}:
        return "escalate_pressure"
    return "probe_deeper"


def _gd_intent_looks_interview_like(intent: str) -> bool:
    lowered = f" {intent.lower()} "
    if any(
        phrase in lowered
        for phrase in (" follow-up", " follow up", " can you provide", " could you provide")
    ):
        return True
    return bool(
        re.search(r"\b(?:ask|question|prompt|probe|press|challenge)\s+(?:the\s+)?learner\b", lowered)
        or re.search(r"\b(?:ask|question|prompt|probe|press|challenge)\s+(?:the\s+)?learner\s+(?:to|for|about)\b", lowered)
        or re.search(r"\b(?:ask|prompt|probe|press)\s+(?:for|about)\s+(?:evidence|metrics?|proof|examples?)\b", lowered)
        or re.search(r"\blearner\s+(?:to\s+)?(?:provide|justify|prove|explain|answer|respond)\b", lowered)
    )


def _safe_gd_action_intent(
    state: dict[str, Any],
    plan: dict[str, Any],
    persona: dict[str, Any],
    proposed_intent: str,
) -> str:
    intent = " ".join(str(proposed_intent or "").split())
    if intent and not _gd_intent_looks_interview_like(intent):
        return intent
    speaker = str(persona.get("name") or _speaker_display_name(str(persona.get("speaker_id") or ""))).strip()
    topic = _active_topic(state, plan)
    return (
        f"Contribute as {speaker}: respond directly on {topic}, take a stance, "
        "and add one concrete counterpoint, metric, or synthesis move. Do not "
        "interview the learner."
    )


def _response_text_or_fallback(state: dict[str, Any], plan: dict[str, Any], persona: dict[str, Any]) -> str:
    if plan.get("mode") == TaskType.INTERVIEW_TEST.value:
        selected = str(state.get("active_interview_probe_prompt") or "").strip()
        if selected:
            return selected
        role = str(plan.get("role") or "this role").strip()
        return f"Tell me about one specific example from your work that shows ownership for {role}."
    topic = _active_topic(state, plan)
    role = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "")
    return gd_persona_fallback_text(topic, speaker_id, role)


def _important_words(value: str) -> set[str]:
    stop = {
        "a", "an", "and", "are", "be", "can", "could", "do", "does", "for",
        "here", "how", "in", "is", "it", "of", "on", "or", "that", "the",
        "this", "to", "what", "why", "would", "you", "your",
    }
    return {
        word
        for word in "".join(ch.lower() if ch.isalnum() else " " for ch in value).split()
        if len(word) > 2 and word not in stop
    }


def _requested_gd_response_echoes_question(text: str, analysis: dict[str, Any]) -> bool:
    response = " ".join((text or "").split())
    if not response:
        return False
    response_lower = response.lower()
    question = str(analysis.get("question_to_requested_speaker") or "").strip()
    if not question:
        return response.endswith("?") and response_lower.startswith(("what ", "how ", "why ", "can ", "could ", "would "))
    response_words = _important_words(response)
    question_words = _important_words(question)
    if len(question_words) < 3:
        return False
    overlap = len(response_words & question_words) / max(len(question_words), 1)
    return response.endswith("?") and overlap >= 0.55


_INTERVIEW_ACTION_VERBS = (
    "added", "aligned", "analyzed", "backfilled", "built", "changed", "chose",
    "compared", "coordinated", "created", "debugged", "deployed", "designed",
    "disabled", "documented", "drained", "explained", "fixed", "framed",
    "implemented", "introduced", "isolated", "led", "migrated", "monitored",
    "moved", "owned", "posted", "prioritized", "proposed", "rebuilt", "reduced",
    "replayed", "resolved", "rolled out", "shipped", "simplified", "tested",
    "traced", "translated", "updated",
)
_INTERVIEW_OUTCOME_VERBS = (
    "dropped", "eliminated", "fell", "grew", "improved", "increased",
    "reached", "reduced", "remained", "rose", "saved", "stayed", "went to zero",
)
_INTERVIEW_RESULT_CRITERIA = {
    "result", "outcome", "impact", "specific_result", "measurable_result",
    "metric_or_signal", "impact_context", "stakeholder_result",
    "business_or_user_value",
}


def _interview_answer_signals(text: str) -> dict[str, bool]:
    """Return only high-confidence evidence signals from the learner's answer.

    These signals authorize obvious evidence the model omitted; they do not try
    to replace semantic evaluation for judgment-heavy rubric criteria.
    """
    normalized = " ".join(str(text or "").split())
    lowered = f" {normalized.lower()} "
    has_number = bool(
        re.search(
            r"\b(?:zero|\d+(?:\.\d+)?\s*(?:%|percent|hours?|minutes?|days?|weeks?|months?|x\b))",
            lowered,
        )
    )
    has_outcome_verb = any(f" {verb} " in lowered for verb in _INTERVIEW_OUTCOME_VERBS)
    has_explicit_result = bool(
        re.search(r"\b(?:the\s+)?(?:result|outcome|impact)\s+(?:was|were|is|included)\b", lowered)
    )
    result_is_negated = bool(
        re.search(r"\b(?:result|outcome|impact)\s+(?:was\s+)?(?:not|never)\s+(?:measured|known|tracked)\b", lowered)
    )
    action_hits = sum(f" {verb} " in lowered for verb in _INTERVIEW_ACTION_VERBS)
    action_pattern = "|".join(re.escape(verb) for verb in _INTERVIEW_ACTION_VERBS)
    has_personal_action = bool(
        re.search(
            rf"\bI\s+(?:(?:personally|first|then)\s+)?(?:{action_pattern})\b",
            normalized,
            re.IGNORECASE,
        )
    )
    has_situation = bool(
        re.search(r"\b(?:in my|at my|during|when|while|on a|on the|our team|the team)\b", lowered)
    ) and len(normalized.split()) >= 18
    has_task = bool(
        re.search(
            r"\b(?:I owned|I was responsible|my task|I needed|I had to|I was asked|I took ownership)\b",
            normalized,
            re.IGNORECASE,
        )
    )
    return {
        "situation": has_situation,
        "task": has_task,
        "personal_action": has_personal_action,
        "result": not result_is_negated and has_outcome_verb and (has_number or has_explicit_result),
        "metric": has_number,
        "process": action_hits >= 2,
    }


def _interview_evidence_excerpts(text: str) -> list[str]:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return []
    if len(normalized) <= 480:
        return [normalized]
    excerpts = [normalized[:235].rstrip()]
    tail = normalized[-235:].lstrip()
    if tail and tail not in excerpts:
        excerpts.append(tail)
    return excerpts


def _interview_evidence_is_grounded(evidence: str, learner_text: str) -> bool:
    evidence_words = _important_words(evidence)
    learner_words = _important_words(learner_text)
    if len(evidence_words) < 3:
        return False
    return len(evidence_words & learner_words) / len(evidence_words) >= 0.78


def _interview_criterion_has_minimum_evidence(
    criterion: str,
    text: str,
    signals: dict[str, bool],
) -> bool | None:
    lowered = f" {' '.join(str(text or '').lower().split())} "
    audience = bool(re.search(r"\b(?:stakeholder|customer|client|product|operations|executive|manager|non-technical)\b", lowered))
    communication = bool(
        re.search(r"\b(?:briefed|communicated|explained|framed|presented|showed|told|translated|updated|walked\s+.+\s+through)\b", lowered)
    )
    if criterion in {"situation", "specific_context", "ambiguous_context"}:
        return signals.get("situation", False)
    if criterion == "task":
        return signals.get("task", False)
    if criterion in {"action", "personal_action", "personal_ownership", "ownership", "first_action", "role_in_result", "personal_role"}:
        return signals.get("personal_action", False)
    if criterion in {"result", "outcome", "impact", "specific_result", "measurable_result"}:
        return signals.get("result", False)
    if criterion == "metric_or_signal":
        return signals.get("metric", False)
    if criterion == "tradeoff":
        return bool(re.search(r"\b(?:trade-?off|versus|instead of|choice between|chose|option|prioritized)\b", lowered))
    if criterion == "audience_awareness":
        return audience and communication
    if criterion == "plain_language":
        return communication and bool(
            re.search(r"\b(?:analogy|avoided jargon|customer impact|plain language|simple terms|framed it as)\b", lowered)
        )
    if criterion == "stakeholder_result":
        return audience and communication and signals.get("result", False)
    if criterion == "communication":
        return communication
    if criterion == "root_cause_process":
        return bool(
            re.search(r"\b(?:compared|correlated|heap profile|isolated|narrowed|profiled|replayed|reproduced|root cause|traced)\b", lowered)
        )
    if criterion == "specific_incident":
        return signals.get("situation", False) and bool(
            re.search(r"\b(?:bug|error|failure|incident|latency|outage|restart|timeout)\b", lowered)
        )
    return None


def _explicit_gd_question(text: str) -> str:
    normalized = " ".join(str(text or "").split())
    end = normalized.rfind("?")
    if end < 0:
        return ""
    start = max(normalized.rfind(".", 0, end), normalized.rfind("!", 0, end))
    question = normalized[start + 1:end + 1].strip()
    return question if len(question) >= 6 else ""


def _repair_gd_analysis_grounding(state: dict[str, Any], analysis: dict[str, Any]) -> bool:
    latest = " ".join(_latest_learner_text(state).split())
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", latest)
    if not latest or len(words) < 14 or str(analysis.get("control_intent") or "none") != "none":
        return False
    lowered = f" {latest.lower()} "
    has_stance = bool(
        re.search(r"\b(?:I\s+(?:support|oppose|believe|favor)|we\s+should|should|must|should not|must not)\b", latest, re.IGNORECASE)
    )
    has_reason = bool(re.search(r"\b(?:because|since|so that|therefore|the reason)\b", lowered))
    concrete_terms = {
        "accountability", "audit", "bias", "complaint", "data", "error", "evidence",
        "impact", "limit", "metric", "outcome", "publish", "remediation", "review",
        "risk", "safeguard", "threshold", "transparency",
    }
    concrete_count = len(concrete_terms & set(word.lower() for word in words))
    has_number = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:%|percent|days?|hours?|weeks?|months?)?\b", latest))
    has_specifics = concrete_count >= 2 or has_number
    has_tradeoff = bool(re.search(r"\b(?:but|however|unless|while|without|rather than|trade-?off|risk)\b", lowered))
    has_engagement = bool(analysis.get("requested_next_speaker")) or bool(_explicit_gd_question(latest))
    evidence = [
        " ".join(str(value).split())
        for value in analysis.get("evidence_points") or []
        if str(value).strip() and _interview_evidence_is_grounded(str(value), latest)
    ]
    for excerpt in _interview_evidence_excerpts(latest):
        if not any(excerpt in item or item in excerpt for item in evidence):
            evidence.append(excerpt)
    repaired = False
    if evidence != list(analysis.get("evidence_points") or []):
        analysis["evidence_points"] = evidence[-3:]
        analysis["evidence_source"] = "model_plus_latest_learner_turn"
        repaired = True
    if has_stance and not str(analysis.get("stance") or "").strip():
        analysis["stance"] = (
            "oppose"
            if re.search(r"\b(?:I\s+oppose|I\s+do\s+not\s+support)\b", latest, re.IGNORECASE)
            else "support"
        )
        repaired = True
    if has_specifics:
        for key in ("missing", "missing_criteria"):
            current = [str(value) for value in analysis.get(key) or []]
            filtered = [
                value for value in current
                if not ("specific" in value.lower() or "evidence" in value.lower())
            ]
            if filtered != current:
                analysis[key] = filtered
                repaired = True
    derived = 0.44
    derived += 0.06 if len(words) >= 28 else 0.02
    derived += 0.08 if has_stance else 0.0
    derived += 0.07 if has_reason else 0.0
    derived += 0.08 if has_specifics else 0.0
    derived += 0.05 if has_tradeoff else 0.0
    derived += 0.03 if has_engagement else 0.0
    grounded_quality = round(min(0.82, derived), 4)
    if grounded_quality > float(analysis.get("quality_score") or 0.0):
        analysis["quality_score"] = grounded_quality
        analysis["quality_source"] = "grounded_gd_discussion_evidence"
        repaired = True
    if bool(analysis.get("scorable", True)) is False and grounded_quality >= 0.55:
        analysis["scorable"] = True
        repaired = True
    return repaired


def _derived_interview_quality(text: str, signals: dict[str, bool], analysis: dict[str, Any]) -> float:
    words = len(re.findall(r"[A-Za-z][A-Za-z0-9'-]*", text or ""))
    if words < 14:
        return 0.0
    score = 0.46
    score += 0.07 if words >= 35 else 0.03
    score += 0.08 if signals.get("personal_action") else 0.0
    score += 0.07 if signals.get("process") else 0.0
    score += 0.09 if signals.get("result") else 0.0
    score += 0.05 if signals.get("metric") else 0.0
    score += min(0.08, 0.02 * len(analysis.get("criteria_met") or []))
    if not signals.get("personal_action"):
        score = min(score, 0.66)
    if not signals.get("result"):
        score = min(score, 0.72)
    return round(min(0.84, max(0.5, score)), 4)


def _explicit_interview_control_kind(text: str) -> str:
    lowered = " ".join(str(text or "").lower().split())
    if re.search(r"\b(?:end|stop|finish)\s+(?:the\s+)?(?:test|interview|assessment)\b", lowered):
        return "end_request"
    if re.search(r"\b(?:move on|skip this|another (?:question|topic)|different (?:question|topic))\b", lowered):
        return "move_on_request"
    if "?" in str(text or "") and re.search(
        r"\b(?:what do you mean|can you clarify|could you clarify|clarify the question|rephrase the question)\b",
        lowered,
    ):
        return "clarification_request"
    return ""


def _repair_interview_analysis_grounding(
    state: dict[str, Any],
    analysis: dict[str, Any],
    flags: list[dict[str, Any]],
) -> bool:
    context = state.get("assessment_turn_context") if isinstance(state.get("assessment_turn_context"), dict) else {}
    answered = context.get("answered_probe") if isinstance(context.get("answered_probe"), dict) else {}
    expected_probe_id = str(answered.get("prompt_id") or answered.get("probe_id") or "").strip()
    expected_criteria = {
        str(value).strip()
        for value in answered.get("criteria") or []
        if str(value).strip()
    }
    repaired = False
    latest = " ".join(_latest_learner_text(state).split())
    explicit_control = _explicit_interview_control_kind(latest)
    model_kind = str(analysis.get("answer_kind") or "answer")
    control_intent = str(analysis.get("control_intent") or "none")
    clarification_is_assessed_skill = "clarifying_question" in expected_criteria
    if clarification_is_assessed_skill and explicit_control == "clarification_request":
        analysis["answer_kind"] = "answer"
        analysis["control_intent"] = "none"
        analysis["scorable"] = True
        analysis["answer_kind_source"] = "assessed_clarification_skill"
        repaired = True
    elif (
        not explicit_control
        and model_kind in {"clarification_request", "move_on_request", "end_request"}
        and len(re.findall(r"[A-Za-z][A-Za-z0-9'-]*", latest)) >= 14
    ):
        analysis["answer_kind"] = "answer"
        analysis["control_intent"] = "none"
        analysis["scorable"] = True
        analysis["answer_kind_source"] = "obvious_non_control_learner_turn"
        repaired = True
    if expected_probe_id and str(analysis.get("active_probe_id") or "").strip() != expected_probe_id:
        analysis["active_probe_id"] = expected_probe_id
        analysis["active_probe_id_source"] = "backend_authorized"
        repaired = True
    if bool(analysis.get("scorable", True)):
        signals = _interview_answer_signals(latest)
        criteria_met = {
            str(value).strip()
            for value in analysis.get("criteria_met") or []
            if str(value).strip()
        }
        missing = {
            str(value).strip()
            for value in analysis.get("missing_criteria") or []
            if str(value).strip()
        }
        if expected_criteria:
            criteria_met.intersection_update(expected_criteria)
            missing.intersection_update(expected_criteria)
        obvious_met: set[str] = set()
        if "situation" in expected_criteria and signals["situation"]:
            obvious_met.add("situation")
        if "task" in expected_criteria and signals["task"]:
            obvious_met.add("task")
        if ({"personal_action", "action"} & expected_criteria) and signals["personal_action"]:
            obvious_met.update({"personal_action", "action"} & expected_criteria)
        if signals["result"]:
            obvious_met.update(
                expected_criteria
                & {"result", "outcome", "impact", "specific_result", "measurable_result", "stakeholder_result"}
            )
        if signals["metric"]:
            obvious_met.update(expected_criteria & {"metric_or_signal"})
        criteria_changed = bool(obvious_met - criteria_met)
        if criteria_changed:
            criteria_met.update(obvious_met)
            missing.difference_update(obvious_met)
            analysis["criteria_source"] = "model_plus_obvious_learner_evidence"
            repaired = True
        unsupported = {
            criterion
            for criterion in criteria_met
            if _interview_criterion_has_minimum_evidence(criterion, latest, signals) is False
        }
        if unsupported:
            criteria_met.difference_update(unsupported)
            missing.update(unsupported)
            analysis["criteria_source"] = "backend_minimum_evidence_gate"
            repaired = True
        if expected_criteria:
            undeclared = expected_criteria - criteria_met - missing
            missing.update(undeclared)
        normalized_met = sorted(criteria_met)
        normalized_missing = sorted(missing)
        if (
            normalized_met != list(analysis.get("criteria_met") or [])
            or normalized_missing != list(analysis.get("missing_criteria") or [])
        ):
            analysis["criteria_met"] = normalized_met
            analysis["missing_criteria"] = normalized_missing
            analysis["criteria_source"] = analysis.get("criteria_source") or "backend_probe_contract"
            repaired = True
        excerpts = _interview_evidence_excerpts(latest)
        evidence = [
            " ".join(str(value).split())
            for value in analysis.get("evidence_points") or []
            if str(value).strip() and _interview_evidence_is_grounded(str(value), latest)
        ]
        for excerpt in excerpts:
            if not any(excerpt in item or item in excerpt for item in evidence):
                evidence.append(excerpt)
        if evidence != list(analysis.get("evidence_points") or []):
            analysis["evidence_points"] = evidence[-3:]
            analysis["evidence_source"] = "model_plus_latest_learner_turn"
            repaired = True
        if float(analysis.get("quality_score") or 0.0) <= 0.0:
            grounded_quality = _derived_interview_quality(latest, signals, analysis)
            if grounded_quality > 0.0:
                analysis["quality_score"] = grounded_quality
                analysis["quality_source"] = "grounded_learner_evidence"
                repaired = True
        if expected_criteria and float(analysis.get("quality_score") or 0.0) > 0.0:
            coverage = len(criteria_met) / len(expected_criteria)
            evidence_cap = round(0.55 + (0.4 * coverage), 4)
            if float(analysis["quality_score"]) > evidence_cap:
                analysis["quality_score"] = evidence_cap
                analysis["quality_source"] = "backend_criterion_coverage_cap"
                repaired = True
        if latest:
            return repaired
        flag = append_validity_flag(
            state,
            "interview_missing_evidence_repaired",
            "The assessment model marked the answer scorable without evidence, and no learner turn was available to attach as evidence.",
            severity="partial",
            target_speaker_id=expected_probe_id,
        )
        flags.append(flag)
        analysis["scorable"] = False
        repaired = True
    return repaired


def _inactive_persona_repair(
    state: dict[str, Any],
    plan: dict[str, Any],
    requested_id: str,
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    moderator = moderator_persona(plan)
    requested_name = _speaker_display_name(requested_id)
    available = available_debater_names(plan)
    available_text = ", ".join(available) if available else "the current panel"
    flag = append_validity_flag(
        state,
        "inactive_requested_speaker",
        f"The learner requested {requested_name}, but that speaker is not active in this assessment roster.",
        severity="partial",
        target_speaker_id=requested_id,
    )
    text = (
        f"{requested_name} is not in this panel. Available voices are {available_text}. "
        "Pick one of those voices, or answer the current topic directly."
    )
    return moderator, text, flag


def authorize_assessment_turn(
    state: dict[str, Any],
    plan: dict[str, Any],
    turn_call: AssessmentTurnCall,
) -> AuthorizedAssessmentTurn:
    """Validate and, where possible, deterministically repair a model turn."""
    analysis = turn_call.analysis.model_dump()
    action = turn_call.next_action
    visible = turn_call.visible_response
    flags: list[dict[str, Any]] = []
    repaired = False
    roster = roster_by_id(plan)
    requested_id = str(analysis.get("requested_next_speaker") or "").strip()
    explicit_requested_id = ""
    if plan.get("mode") == TaskType.GD_TEST.value:
        valid_focus_ids = {
            str(item.get("focus_id") or "").strip()
            for item in plan.get("focus_plan") or []
            if isinstance(item, dict) and str(item.get("focus_id") or "").strip()
        }
        if str(analysis.get("focus_id") or "").strip() not in valid_focus_ids:
            analysis["focus_id"] = ""
        explicit_requested_id = explicit_requested_speaker_id(
            plan,
            _latest_learner_text(state),
        )
        if explicit_requested_id:
            requested_id = explicit_requested_id
            analysis["requested_next_speaker"] = explicit_requested_id
            analysis["routing_case"] = (
                "reply_and_request"
                if str(analysis.get("routing_case") or "") in {"reply_only", "point_only"}
                else str(analysis.get("routing_case") or "request_only")
            )
            analysis["request_confidence"] = max(
                float(analysis.get("request_confidence") or 0.0),
                1.0,
            )
            if not str(analysis.get("question_to_requested_speaker") or "").strip():
                analysis["question_to_requested_speaker"] = _explicit_gd_question(
                    _latest_learner_text(state)
                )
    client_action = state.get("client_assessment_action")
    client_ask_has_substantive_answer = False
    if isinstance(client_action, dict) and client_action.get("kind") == "ask_panelist":
        client_speaker_id = str(client_action.get("speaker_id") or "").strip()
        if client_speaker_id:
            client_ask_has_substantive_answer = _latest_learner_has_scorable_substance(state)
            requested_id = client_speaker_id
            analysis["requested_next_speaker"] = client_speaker_id
            analysis["routing_case"] = (
                "reply_and_request" if client_ask_has_substantive_answer else "request_only"
            )
            analysis["request_confidence"] = 1.0
            analysis["client_action"] = dict(client_action)
            if client_ask_has_substantive_answer:
                analysis["scorable"] = bool(analysis.get("scorable", True))
                if not analysis.get("evidence_points"):
                    analysis["evidence_points"] = [_latest_learner_text(state)[:220]]
    proposed_speaker_id = str(visible.speaker_id or action.speaker_id or "").strip()
    action_speaker_id = str(action.speaker_id or "").strip()
    visible_speaker_id = str(visible.speaker_id or "").strip()

    if action_speaker_id and visible_speaker_id and action_speaker_id != visible_speaker_id:
        flag = append_validity_flag(
            state,
            "speaker_output_mismatch",
            "The structured turn proposed one speaker but drafted the visible response for another speaker.",
            severity="partial",
            speaker_id=visible_speaker_id,
            target_speaker_id=action_speaker_id,
        )
        flags.append(flag)
        repaired = True

    if requested_id and not speaker_is_active(plan, requested_id):
        persona, text, flag = _inactive_persona_repair(state, plan, requested_id)
        flags.append(flag)
        repaired = True
    elif plan.get("mode") == TaskType.GD_TEST.value and low_confidence_persona_request(analysis):
        flag = append_validity_flag(
            state,
            "low_confidence_persona_request",
            "The model treated an ambiguous role phrase as a persona request; the turn stayed as a normal scorable point.",
            severity="partial",
            target_speaker_id=requested_id,
        )
        flags.append(flag)
        persona = first_debater(plan, avoid=requested_id)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True
    elif (
        plan.get("mode") == TaskType.GD_TEST.value
        and requested_id
        and speaker_is_active(plan, requested_id)
        and requested_id != proposed_speaker_id
        and float(analysis.get("request_confidence") or 0.0) >= 0.7
    ):
        flag = append_validity_flag(
            state,
            "requested_speaker_mismatch",
            "The learner requested an active panelist, but the model proposed a different next speaker.",
            severity="partial",
            speaker_id=proposed_speaker_id,
            target_speaker_id=requested_id,
        )
        flags.append(flag)
        persona = roster[requested_id]
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True
    elif (
        plan.get("mode") == TaskType.GD_TEST.value
        and proposed_speaker_id
        and proposed_speaker_id == str((state.get("blackboard") or {}).get("last_speaker") or "")
        and not requested_id
    ):
        flag = append_validity_flag(
            state,
            "repeated_speaker_repaired",
            "The assessment model repeated the same panelist without a learner request, so the backend rotated the floor.",
            severity="partial",
            speaker_id=proposed_speaker_id,
        )
        flags.append(flag)
        persona = next_active_debater(plan, after=proposed_speaker_id)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True
    elif not speaker_is_active(plan, proposed_speaker_id):
        persona, text, flag = _inactive_persona_repair(state, plan, proposed_speaker_id or requested_id)
        flags.append(flag)
        repaired = True
    else:
        persona = roster[proposed_speaker_id]
        text = str(visible.text or "").strip()

    if not text:
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True

    if (
        plan.get("mode") == TaskType.GD_TEST.value
        and requested_id
        and requested_id == str(persona.get("speaker_id") or "")
        and _requested_gd_response_echoes_question(text, analysis)
    ):
        flag = append_validity_flag(
            state,
            "requested_speaker_question_echo",
            "The requested panelist echoed the learner's question instead of answering it, so the backend replaced the response.",
            severity="partial",
            speaker_id=persona.get("speaker_id"),
            target_speaker_id=requested_id,
        )
        flags.append(flag)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True

    if self_label_or_meta_text(text, persona):
        flag = append_validity_flag(
            state,
            "self_label_or_meta_response",
            f"{persona.get('name') or persona.get('speaker_id')} produced self-label or meta handoff text.",
            severity="partial",
            speaker_id=persona.get("speaker_id"),
        )
        flags.append(flag)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True

    if plan.get("mode") == TaskType.GD_TEST.value and gd_panelist_ask_only_text(text, persona):
        flag = append_validity_flag(
            state,
            "gd_panelist_ask_only_repaired",
            "A GD panelist asked only a question instead of contributing to the discussion, so the backend replaced the response.",
            severity="partial",
            speaker_id=persona.get("speaker_id"),
        )
        flags.append(flag)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True

    if plan.get("mode") == TaskType.GD_TEST.value and gd_panelist_formulaic_meta_text(text, persona):
        flag = append_validity_flag(
            state,
            "gd_panelist_formulaic_meta_repaired",
            "A GD panelist used formulaic facilitator framing instead of contributing to the discussion, so the backend replaced the response.",
            severity="partial",
            speaker_id=persona.get("speaker_id"),
        )
        flags.append(flag)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True

    if plan.get("mode") == TaskType.INTERVIEW_TEST.value and interview_model_answer_leak(text):
        flag = append_validity_flag(
            state,
            "interviewer_model_answer_leak",
            "The interviewer started answering the candidate's question, so the prompt was replaced.",
            severity="partial",
            speaker_id=persona.get("speaker_id"),
        )
        flags.append(flag)
        text = _response_text_or_fallback(state, plan, persona)
        repaired = True

    if plan.get("mode") == TaskType.INTERVIEW_TEST.value:
        repaired = _repair_interview_analysis_grounding(state, analysis, flags) or repaired
    elif plan.get("mode") == TaskType.GD_TEST.value:
        repaired = _repair_gd_analysis_grounding(state, analysis) or repaired

    quality = float(analysis.get("quality_score") or 0.0)
    control_intent = str(analysis.get("control_intent") or "none")
    client_kind = (
        str(client_action.get("kind") or "")
        if isinstance(client_action, dict)
        else ""
    )
    scorable = (
        bool(analysis.get("scorable", True))
        and control_intent == "none"
        and client_kind not in {"clarify", "new_angle", "move_on"}
        and (client_kind != "ask_panelist" or client_ask_has_substantive_answer)
    )
    if scorable and quality <= 0.0 and (analysis.get("criteria_met") or analysis.get("evidence_points")):
        flag = append_validity_flag(
            state,
            "assessment_quality_score_repaired",
            "The assessment model marked the answer scorable but returned an unusable quality score, so the backend applied a conservative repaired score.",
            severity="partial",
            speaker_id=persona.get("speaker_id"),
        )
        flags.append(flag)
        repaired = True
        quality = float((state.get("blackboard") or {}).get("last_quality") or 0.5)
        analysis["quality_score"] = quality
    if scorable and quality <= 0.0:
        scorable = False
        analysis["scorable"] = False
    should_close = bool(action.should_close or control_intent == "end")
    proposed_intent = str(action.intent or "")
    if plan.get("mode") == TaskType.GD_TEST.value:
        safe_intent = _safe_gd_action_intent(state, plan, persona, proposed_intent)
        if safe_intent != " ".join(proposed_intent.split()):
            repaired = True
    else:
        safe_intent = proposed_intent
    decision = DirectorDecision(
        action=_map_action(str(action.action_type or ""), should_close=should_close),
        next_speaker=str(persona.get("speaker_id") or ""),
        intent=safe_intent,
        tension=float((state.get("blackboard") or {}).get("tension") or 0.35),
        answer_quality=quality,
        should_close=should_close,
    )
    return AuthorizedAssessmentTurn(
        persona=persona,
        decision=decision,
        text=text,
        scorable=scorable,
        repaired=repaired,
        flags=flags,
        analysis=analysis,
    )
