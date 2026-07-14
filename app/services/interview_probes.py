"""Canonical interview probe planning for scored Interview Test sessions."""
from __future__ import annotations

import zlib
from typing import Any

from app.content.skills import SkillID


DEFAULT_INTERVIEW_PROBE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "probe_id": "project_ownership_tradeoff",
        "skill_id": SkillID.SPECIFICITY_EXAMPLES.value,
        "prompt": "Walk me through one project relevant to {role}. What problem did you own, what trade-off did you make, and what changed because of your work?",
        "aim": "Gives a concrete project deep dive with ownership, trade-off, and outcome.",
        "criteria": ["specific_project", "personal_ownership", "tradeoff", "outcome"],
    },
    {
        "probe_id": "debugging_under_pressure",
        "skill_id": SkillID.ANSWER_RELEVANCE.value,
        "prompt": "Tell me about a production bug, reliability issue, or technical mistake you debugged. How did you isolate the cause and keep others updated?",
        "aim": "Explains debugging process, communication, and learning.",
        "criteria": ["specific_incident", "root_cause_process", "communication", "learning"],
    },
    {
        "probe_id": "stakeholder_disagreement",
        "skill_id": SkillID.STRUCTURE_STAR_METHOD.value,
        "prompt": "Tell me about a disagreement with a teammate or stakeholder. What did you say, how did you decide, and what changed afterward?",
        "aim": "Uses a clear situation-action-result structure for conflict.",
        "criteria": ["situation", "action", "decision_logic", "result"],
    },
    {
        "probe_id": "ambiguous_ownership",
        "skill_id": SkillID.SPECIFICITY_EXAMPLES.value,
        "prompt": "Give me an example of taking ownership when the path was ambiguous or something was going wrong. What did you personally do first?",
        "aim": "Shows initiative, prioritization, and personal agency.",
        "criteria": ["ambiguous_context", "first_action", "ownership", "impact"],
    },
    {
        "probe_id": "technical_communication",
        "skill_id": SkillID.CLARITY_CONCISENESS.value,
        "prompt": "Describe a technical or work decision you had to explain to a non-technical stakeholder. How did you make the trade-off clear?",
        "aim": "Shows clear communication without jargon.",
        "criteria": ["audience_awareness", "plain_language", "tradeoff", "stakeholder_result"],
    },
    {
        "probe_id": "measurable_impact",
        "skill_id": SkillID.SPECIFICITY_EXAMPLES.value,
        "prompt": "What is one measurable result your work created? Use a concrete metric, user outcome, reliability gain, or delivery improvement.",
        "aim": "Connects work to measurable impact.",
        "criteria": ["specific_result", "metric_or_signal", "role_in_result", "business_or_user_value"],
    },
    {
        "probe_id": "role_readiness",
        "skill_id": SkillID.CONFIDENCE_TONE.value,
        "prompt": "Why are you ready for a {role} role now? Anchor your answer in work you have actually done.",
        "aim": "Answers role fit with evidence instead of generic confidence.",
        "criteria": ["role_alignment", "evidence", "growth_edge", "concise_confidence"],
    },
    {
        "probe_id": "failure_learning",
        "skill_id": SkillID.STRUCTURE_STAR_METHOD.value,
        "prompt": "Tell me about a mistake or failure. What did you change afterward so it would not repeat?",
        "aim": "Shows accountability and concrete learning.",
        "criteria": ["specific_failure", "accountability", "change_made", "future_prevention"],
    },
    {
        "probe_id": "prioritization_tradeoff",
        "skill_id": SkillID.ANSWER_RELEVANCE.value,
        "prompt": "How do you prioritize when two important requests compete for your time? Give one real example.",
        "aim": "Demonstrates prioritization logic with a real example.",
        "criteria": ["competing_demands", "decision_rule", "communication", "outcome"],
    },
    {
        "probe_id": "candidate_questions",
        "skill_id": SkillID.CONFIDENCE_TONE.value,
        "prompt": "What question would you ask us to judge whether this {role} role is a good fit for you, and what would you listen for in the answer?",
        "aim": "Shows mature role evaluation and self-awareness.",
        "criteria": ["thoughtful_question", "role_fit_signal", "self_awareness", "follow_up_logic"],
    },
)

SCENARIO_INITIAL_PROBE_TEMPLATES: dict[str, dict[str, Any]] = {
    "int_01_elevator_pitch": {
        "probe_id": "scenario_tell_me_about_yourself",
        "skill_id": SkillID.CLARITY_CONCISENESS.value,
        "prompt": (
            "Tell me about yourself in 3 to 4 sentences for a {role} interview. "
            "Cover your current role, one concrete strength with proof, and the direction you want next."
        ),
        "aim": "Gives a concise professional pitch with role, proof, and direction.",
        "criteria": ["current_role", "concrete_strength", "proof_point", "future_direction", "concise_structure"],
    },
    "int_02_strength_with_evidence": {
        "probe_id": "scenario_strength_with_evidence",
        "skill_id": SkillID.SPECIFICITY_EXAMPLES.value,
        "prompt": "What is one strength you would bring to a {role} role? Prove it with one specific example and result.",
        "aim": "Backs a strength with a specific example and result.",
        "criteria": ["named_strength", "specific_example", "personal_action", "result"],
    },
    "int_03_weakness_framing": {
        "probe_id": "scenario_weakness_framing",
        "skill_id": SkillID.ANSWER_RELEVANCE.value,
        "prompt": "What is one real weakness you are actively improving? Name the habit you use now and one sign it is getting better.",
        "aim": "Frames a genuine weakness with mitigation and progress evidence.",
        "criteria": ["genuine_weakness", "corrective_habit", "progress_signal", "role_safe_framing"],
    },
    "int_04_star_behavioral": {
        "probe_id": "scenario_star_story",
        "skill_id": SkillID.STRUCTURE_STAR_METHOD.value,
        "prompt": (
            "Tell me about one specific {role} project or work situation using STAR. "
            "What was the situation, what was your task, what action did you personally take, and what changed as a result?"
        ),
        "aim": "Uses Situation, Task, Action, and Result with emphasis on personal action.",
        "criteria": ["situation", "task", "personal_action", "result"],
    },
    "int_05_why_this_role": {
        "probe_id": "scenario_why_this_role",
        "skill_id": SkillID.ANSWER_RELEVANCE.value,
        "prompt": "Why are you interested in this {role} opportunity? Connect the company or team to your actual experience and next goal.",
        "aim": "Connects motivation to role fit, evidence, and direction.",
        "criteria": ["role_specific_reason", "company_or_team_signal", "experience_link", "next_goal"],
    },
    "int_06_own_a_failure": {
        "probe_id": "scenario_own_a_failure",
        "skill_id": SkillID.STRUCTURE_STAR_METHOD.value,
        "prompt": "Tell me about a real failure or mistake. What went wrong, what did you own, and what changed afterward?",
        "aim": "Shows accountability and concrete learning after a failure.",
        "criteria": ["specific_failure", "accountability", "change_made", "learning"],
    },
    "int_07_clarify_before_answering": {
        "probe_id": "scenario_clarify_ambiguous_question",
        "skill_id": SkillID.CLARITY_CONCISENESS.value,
        "prompt": "Here is an intentionally broad question: what makes you a strong fit for this {role} role? Before answering, ask one clarifying question.",
        "aim": "Clarifies the interviewer intent before answering a broad prompt.",
        "criteria": ["clarifying_question", "scope_control", "relevance"],
    },
    "int_08_quantify_impact": {
        "probe_id": "scenario_quantify_impact",
        "skill_id": SkillID.SPECIFICITY_EXAMPLES.value,
        "prompt": "What is one measurable result your work created? Use a metric, user outcome, reliability signal, or delivery improvement.",
        "aim": "Quantifies impact instead of describing effort only.",
        "criteria": ["measurable_result", "metric_or_signal", "personal_role", "impact_context"],
    },
    "int_09_diplomatic_pushback": {
        "probe_id": "scenario_diplomatic_pushback",
        "skill_id": SkillID.CONFIDENCE_TONE.value,
        "prompt": "Suppose I challenge your approach and say it was too slow. Push back diplomatically using evidence from the situation.",
        "aim": "Disagrees respectfully while defending a decision with evidence.",
        "criteria": ["acknowledges_view", "clear_counterposition", "requirement_based_reasoning", "collaborative_tone"],
    },
    "int_10_close_strong": {
        "probe_id": "scenario_close_strong",
        "skill_id": SkillID.CONFIDENCE_TONE.value,
        "prompt": "We are near the end. Ask one sharp question about this {role} role and give a concise closing statement that names the value you would bring. Use either natural order.",
        "aim": "Closes with role-fit evidence and asks a thoughtful candidate question.",
        "criteria": ["specific_closing_question", "role_relevance", "role_fit_evidence", "professional_close", "non_generic"],
    },
    "int_11_salary_negotiation": {
        "probe_id": "scenario_salary_negotiation",
        "skill_id": SkillID.CONFIDENCE_TONE.value,
        "prompt": "If the offer is lower than expected, how would you negotiate while staying collaborative and evidence-based?",
        "aim": "Negotiates with composure, evidence, and a constructive ask.",
        "criteria": ["clear_anchor", "market_or_value_reason", "collaborative_flexibility", "calm_tone"],
    },
    "int_12_explain_a_gap": {
        "probe_id": "scenario_explain_gap",
        "skill_id": SkillID.ANSWER_RELEVANCE.value,
        "prompt": "Explain a career gap, transition, or departure in a way that is honest, brief, and brings the focus back to readiness for {role}.",
        "aim": "Explains the gap without over-sharing and returns to current readiness.",
        "criteria": ["brief_context", "non_blaming_tone", "productive_use_or_learning", "forward_focus"],
    },
}

_SCENARIO_DEFERRED_DEFAULT_PROBES: dict[str, set[str]] = {
    "scenario_star_story": {"project_ownership_tradeoff"},
    "scenario_quantify_impact": {"measurable_impact"},
    "scenario_own_a_failure": {"failure_learning"},
    "scenario_close_strong": {"candidate_questions"},
    "scenario_why_this_role": {"role_readiness"},
}


def _prompt_id(text: str, fallback: str) -> str:
    clean = " ".join((text or fallback).split())
    return f"prompt_{zlib.crc32(clean.encode('utf-8')):08x}"


def _inferred_probe_criteria(prompt: str, skill_id: str) -> list[str]:
    """Convert authored/generated probe prose into auditable criterion ids."""
    lowered = " ".join(str(prompt or "").lower().split())
    if any(term in lowered for term in ("production bug", "latency issue", "technical mistake", "debugged")):
        criteria = ["specific_incident", "root_cause_process"]
        if any(term in lowered for term in ("updated", "communicat")):
            criteria.append("communication")
        return criteria
    if "trade-off" in lowered or "tradeoff" in lowered or " versus " in lowered:
        return ["specific_context", "tradeoff", "decision_logic", "outcome"]
    if "why are you ready" in lowered or "right now" in lowered and "role" in lowered:
        return ["role_alignment", "evidence", "concise_confidence"]
    if "project" in lowered and any(term in lowered for term in ("what did you own", "problem did you own")):
        criteria = ["specific_project", "personal_ownership"]
        if any(term in lowered for term in ("what changed", "result", "outcome")):
            criteria.append("outcome")
        return criteria
    if skill_id == SkillID.CLARITY_CONCISENESS.value:
        return ["clear_structure", "relevance", "conciseness"]
    if skill_id == SkillID.CONFIDENCE_TONE.value:
        return ["specific_evidence", "role_alignment", "composed_delivery"]
    if skill_id == SkillID.STRUCTURE_STAR_METHOD.value:
        return ["situation", "personal_action", "result"]
    if skill_id == SkillID.SPECIFICITY_EXAMPLES.value:
        return ["specific_example", "personal_ownership", "outcome"]
    return ["direct_answer", "specific_evidence"]


def _normalise_probe(raw: dict[str, Any], *, index: int, role: str) -> dict[str, Any] | None:
    prompt = str(raw.get("prompt") or "").strip()
    if not prompt:
        return None
    try:
        prompt = prompt.format(role=role)
    except Exception:
        pass
    probe_id = str(raw.get("probe_id") or raw.get("id") or raw.get("prompt_id") or f"probe_{index}").strip()
    prompt_id = str(raw.get("prompt_id") or _prompt_id(prompt, probe_id)).strip()
    skill_id = str(raw.get("skill_id") or raw.get("skill") or probe_id or prompt_id).strip()
    criteria = [
        str(item).strip()
        for item in (raw.get("criteria") or [])
        if str(item).strip()
    ]
    aim = str(raw.get("aim") or "").strip()
    if not criteria or all(" " in item for item in criteria):
        criteria = _inferred_probe_criteria(prompt, skill_id)
    return {
        "probe_id": probe_id or prompt_id,
        "prompt_id": prompt_id,
        "skill_id": skill_id,
        "prompt": prompt,
        "aim": aim,
        "criteria": criteria,
        "phase": str(raw.get("phase") or "probing"),
    }


def normalize_interview_probe(raw: dict[str, Any], *, role: str) -> dict[str, Any]:
    """Normalize a persisted probe built before criterion ids were enforced."""
    return _normalise_probe(raw, index=0, role=role) or dict(raw)


def default_interview_probes_for_role(role: str) -> list[dict[str, Any]]:
    active_role = str(role or "the target role").strip() or "the target role"
    probes: list[dict[str, Any]] = []
    for index, raw in enumerate(DEFAULT_INTERVIEW_PROBE_TEMPLATES):
        probe = _normalise_probe(raw, index=index, role=active_role)
        if probe:
            probes.append(probe)
    return probes


def _scenario_initial_probe(state: dict[str, Any], role: str) -> dict[str, Any] | None:
    node_id = str(state.get("competency_node") or "").strip()
    raw = SCENARIO_INITIAL_PROBE_TEMPLATES.get(node_id)
    if not raw:
        return None
    return _normalise_probe(raw, index=-1, role=role)


def _has_visible_learner_turn(state: dict[str, Any]) -> bool:
    for message in state.get("messages") or []:
        if not isinstance(message, dict):
            continue
        if str(message.get("role") or "").strip().lower() != "user":
            continue
        if str(message.get("content") or "").strip():
            return True
    return False


def _should_prepend_scenario_initial_probe(state: dict[str, Any]) -> bool:
    return (
        not _has_visible_learner_turn(state)
        and not str(state.get("active_interview_probe_prompt") or "").strip()
        and not state.get("pending_coverage_event")
    )


def build_interview_probe_plan(state: dict[str, Any]) -> list[dict[str, Any]]:
    scenario = state.get("scenario_config") or {}
    career = state.get("career_context") or {}
    role = (
        str(
            scenario.get("target_role")
            or career.get("primary_role")
            or (career.get("target_roles") or [""])[0]
            or "the target role"
        ).strip()
        or "the target role"
    )
    probes: list[dict[str, Any]] = []
    deferred_probes: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()
    if _should_prepend_scenario_initial_probe(state):
        scenario_probe = _scenario_initial_probe(state, role)
    else:
        scenario_probe = None
    if scenario_probe:
        probes.append(scenario_probe)
        seen_prompts.add(" ".join(scenario_probe["prompt"].lower().split()))
    deferred_probe_ids = _SCENARIO_DEFERRED_DEFAULT_PROBES.get(
        str((scenario_probe or {}).get("probe_id") or ""),
        set(),
    )
    for index, raw in enumerate(list(state.get("probe_items") or []) + default_interview_probes_for_role(role)):
        if not isinstance(raw, dict):
            continue
        probe = _normalise_probe(raw, index=index, role=role)
        if not probe:
            continue
        key = " ".join(probe["prompt"].lower().split())
        if key in seen_prompts:
            continue
        seen_prompts.add(key)
        if probe["probe_id"] in deferred_probe_ids:
            deferred_probes.append(probe)
        else:
            probes.append(probe)
    probes.extend(deferred_probes)
    return probes
