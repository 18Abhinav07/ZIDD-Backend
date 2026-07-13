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


def _repair_interview_analysis_grounding(
    state: dict[str, Any],
    analysis: dict[str, Any],
    flags: list[dict[str, Any]],
) -> bool:
    context = state.get("assessment_turn_context") if isinstance(state.get("assessment_turn_context"), dict) else {}
    answered = context.get("answered_probe") if isinstance(context.get("answered_probe"), dict) else {}
    expected_probe_id = str(answered.get("prompt_id") or answered.get("probe_id") or "").strip()
    repaired = False
    if expected_probe_id and str(analysis.get("active_probe_id") or "").strip() != expected_probe_id:
        flag = append_validity_flag(
            state,
            "interview_active_probe_repaired",
            "The assessment model did not ground analysis in the backend-authorized answered probe, so the backend repaired the probe id.",
            severity="partial",
            target_speaker_id=expected_probe_id,
        )
        flags.append(flag)
        analysis["active_probe_id"] = expected_probe_id
        repaired = True
    if bool(analysis.get("scorable", True)) and not analysis.get("evidence_points"):
        latest = " ".join(_latest_learner_text(state).split())
        if latest:
            analysis["evidence_points"] = [latest[:220]]
            analysis["evidence_source"] = "latest_learner_turn"
            flag = append_validity_flag(
                state,
                "interview_missing_evidence_repaired",
                "The assessment model marked the answer scorable without explicit evidence, so the backend attached the latest learner turn as conservative evidence.",
                severity="partial",
                target_speaker_id=expected_probe_id,
            )
            flags.append(flag)
            return True
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
