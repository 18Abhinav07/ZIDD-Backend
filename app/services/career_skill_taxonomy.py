"""Closed, durable skill identity for Career simulation reports."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable


INTERVIEW_MODULE = "interview"
GD_MODULE = "group_discussion"
INTERVIEW_FALLBACK_ID = "int_00_general_communication"
GD_FALLBACK_ID = "gd_00_general_communication"


@dataclass(frozen=True)
class CareerSkill:
    skill_id: str
    label: str
    module: str
    recommended_node_id: str
    criterion_aliases: tuple[str, ...] = ()
    phrase_aliases: tuple[str, ...] = ()


CAREER_SKILLS: tuple[CareerSkill, ...] = (
    CareerSkill(INTERVIEW_FALLBACK_ID, "General interview communication", INTERVIEW_MODULE, "int_01_elevator_pitch", phrase_aliases=("general interview communication", "interview communication")),
    CareerSkill("int_01_elevator_pitch", "Tell me about yourself", INTERVIEW_MODULE, "int_01_elevator_pitch", ("answers_question", "specific_detail", "pitch_structure", "future_goal"), ("elevator pitch", "self introduction", "introduce yourself", "tell me about yourself")),
    CareerSkill("int_02_strength_with_evidence", "Back a strength with evidence", INTERVIEW_MODULE, "int_02_strength_with_evidence", ("strength_claim", "specific_evidence", "learner_action", "impact_signal"), ("strength with evidence", "prove a strength", "back a strength", "evidence under pressure")),
    CareerSkill("int_03_weakness_framing", "Frame a weakness constructively", INTERVIEW_MODULE, "int_03_weakness_framing", ("real_weakness", "mitigation_habit", "progress_evidence", "non_self_sabotage"), ("weakness framing", "answer the weakness question", "constructive weakness")),
    CareerSkill("int_04_star_behavioral", "Tell a structured STAR story", INTERVIEW_MODULE, "int_04_star_behavioral", ("situation", "task", "actions", "result"), ("star story", "star answer", "behavioral story", "structured example")),
    CareerSkill("int_05_why_this_role", "Explain why this company and role", INTERVIEW_MODULE, "int_05_why_this_role", ("company_specific_fact", "personal_motivation_link", "role_relevance", "non_generic"), ("why this company", "why this role", "company motivation", "role motivation")),
    CareerSkill("int_06_own_a_failure", "Own a failure and show learning", INTERVIEW_MODULE, "int_06_own_a_failure", ("ownership", "impact", "response_action", "prevention", "non_defensive_tone"), ("own a failure", "failure story", "take ownership", "learn from failure")),
    CareerSkill("int_07_clarify_before_answering", "Clarify before answering", INTERVIEW_MODULE, "int_07_clarify_before_answering", ("recognizes_ambiguity", "asks_targeted_question", "states_answer_frame", "professional_tone"), ("clarify the question", "ambiguous question", "ask a clarifying question", "clarify before answering")),
    CareerSkill("int_08_quantify_impact", "Quantify your impact", INTERVIEW_MODULE, "int_08_quantify_impact", ("impact_claim", "quantified_before_after", "learner_contribution"), ("quantify impact", "quantified impact", "measurable result", "add a number", "add a metric", "use a number", "before and after metric", "missing metrics")),
    CareerSkill("int_09_diplomatic_pushback", "Disagree with the interviewer diplomatically", INTERVIEW_MODULE, "int_09_diplomatic_pushback", ("acknowledges_view", "clear_counterposition", "requirement_based_reasoning", "collaborative_tone"), ("diplomatic pushback", "disagree with interviewer", "push back respectfully", "counter the interviewer")),
    CareerSkill("int_10_close_strong", "Close with sharp questions", INTERVIEW_MODULE, "int_10_close_strong", ("specific_closing_question", "role_relevance", "role_fit_evidence", "professional_close", "non_generic"), ("close strong", "closing question", "sharp question", "questions for interviewer", "weak closing question")),
    CareerSkill("int_11_salary_negotiation", "Negotiate an offer calmly", INTERVIEW_MODULE, "int_11_salary_negotiation", ("clear_anchor", "market_or_value_reason", "collaborative_flexibility", "calm_tone"), ("salary negotiation", "negotiate offer", "compensation discussion", "salary anchor")),
    CareerSkill("int_12_explain_a_gap", "Explain a gap or departure", INTERVIEW_MODULE, "int_12_explain_a_gap", ("brief_context", "non_blaming_tone", "productive_use_or_learning", "forward_focus"), ("explain a gap", "employment gap", "career gap", "explain departure", "why did you leave")),
    CareerSkill(GD_FALLBACK_ID, "General group discussion communication", GD_MODULE, "gd_01_stake_position", phrase_aliases=("general group discussion communication", "group discussion communication")),
    CareerSkill("gd_01_stake_position", "Stake a clear position", GD_MODULE, "gd_01_stake_position", ("clear_stance", "topic_relevance", "low_hedging", "concise_opening"), ("clear position", "stake a position", "state a stance", "take a stance", "hedging")),
    CareerSkill("gd_02_support_with_evidence", "Support your point with evidence", GD_MODULE, "gd_02_support_with_evidence", ("concrete_evidence", "evidence_link"), ("support with evidence", "add evidence", "concrete example", "add a number", "add data", "use evidence", "measurable result")),
    CareerSkill("gd_03_take_the_floor", "Enter the discussion effectively", GD_MODULE, "gd_03_take_the_floor", ("polite_entry_phrase", "links_prior_point", "adds_new_value", "assertive_not_rude"), ("take the floor", "enter the discussion", "interject", "claim the floor", "entry phrase")),
    CareerSkill("gd_04_build_on_others", "Build on another person's point", GD_MODULE, "gd_04_build_on_others", ("credits_prior_speaker", "extends_idea", "collaborative_tone"), ("build on others", "extend another point", "credit prior speaker", "build on a point")),
    CareerSkill("gd_05_disagree_respectfully", "Disagree respectfully", GD_MODULE, "gd_05_disagree_respectfully", ("acknowledges_valid_point", "clear_counter", "reasoned_basis", "civil_tone"), ("disagree respectfully", "civil disagreement", "respectful counter", "counterargument")),
    CareerSkill("gd_06_balanced_view", "Present a balanced view", GD_MODULE, "gd_06_balanced_view", ("names_both_sides", "weighs_tradeoff", "returns_to_position"), ("balanced view", "both sides", "weigh tradeoffs", "tradeoff")),
    CareerSkill("gd_07_steer_back", "Steer a derailed discussion back", GD_MODULE, "gd_07_steer_back", ("identifies_derailment", "redirects_to_topic", "gives_next_step", "non_controlling_tone"), ("steer back", "refocus discussion", "topic drift", "derailed discussion", "redirect to topic")),
    CareerSkill("gd_08_include_quiet", "Bring quieter voices into the discussion", GD_MODULE, "gd_08_include_quiet", ("names_quiet_participant", "topic_linked_invite", "respectful_floor_give", "non_pressuring_tone"), ("include quiet voices", "invite quiet participant", "bring in quieter voices", "include others")),
    CareerSkill("gd_09_manage_dominator", "Manage a dominant speaker", GD_MODULE, "gd_09_manage_dominator", ("acknowledges_contribution", "redistributes_floor", "topic_link", "respectful_boundary"), ("manage dominator", "dominant speaker", "redistribute the floor", "set a respectful boundary")),
    CareerSkill("gd_10_drive_consensus", "Summarize and drive consensus", GD_MODULE, "gd_10_drive_consensus", ("summarizes_key_points", "identifies_common_ground", "proposes_next_step", "balanced_credit"), ("drive consensus", "summarize discussion", "common ground", "propose next step", "reach consensus")),
)


_BY_ID = {skill.skill_id: skill for skill in CAREER_SKILLS}


def _normalize(value: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())


def module_for_mode(mode: Any) -> str:
    raw = getattr(mode, "value", mode)
    text = str(raw or "").strip().lower()
    if text in {"interview", "interview_prep", "interview_test"}:
        return INTERVIEW_MODULE
    if text in {"group_discussion", "gd_prep", "gd_test"}:
        return GD_MODULE
    return ""


def fallback_skill_id(mode: Any) -> str:
    return GD_FALLBACK_ID if module_for_mode(mode) == GD_MODULE else INTERVIEW_FALLBACK_ID


def skills_for_mode(mode: Any) -> tuple[CareerSkill, ...]:
    module = module_for_mode(mode)
    return tuple(skill for skill in CAREER_SKILLS if skill.module == module)


def allowed_skill_ids(mode: Any) -> tuple[str, ...]:
    return tuple(skill.skill_id for skill in skills_for_mode(mode))


def skill_for_id(skill_id: str) -> CareerSkill | None:
    return _BY_ID.get(str(skill_id or "").strip())


def _matching_skill_ids(mode: Any, value: Any) -> tuple[str, ...]:
    module = module_for_mode(mode)
    raw = str(value or "").strip()
    exact = _BY_ID.get(raw)
    if exact is not None:
        return (exact.skill_id,) if exact.module == module else ()
    normalized = _normalize(raw)
    if not normalized:
        return ()
    matches: list[tuple[int, str]] = []
    for skill in skills_for_mode(mode):
        aliases = (skill.label, *skill.criterion_aliases, *skill.phrase_aliases)
        for alias in aliases:
            normalized_alias = _normalize(alias)
            if normalized == normalized_alias or (
                len(normalized_alias) >= 5 and normalized_alias in normalized
            ):
                matches.append((len(normalized_alias), skill.skill_id))
    if not matches:
        return ()
    best_length = max(length for length, _skill_id in matches)
    return tuple(sorted({skill_id for length, skill_id in matches if length == best_length}))


def canonical_skill_id(mode: Any, value: Any) -> str:
    matches = _matching_skill_ids(mode, value)
    return matches[0] if len(matches) == 1 else fallback_skill_id(mode)


def focus_node_for_observation(mode: Any, *values: Any) -> str:
    """Resolve a practice target only when an observation has one unique owner."""
    for value in values:
        matches = _matching_skill_ids(mode, value)
        if len(matches) != 1:
            continue
        skill = _BY_ID.get(matches[0])
        if skill is not None:
            return skill.recommended_node_id
    return ""


def taxonomy_prompt_lines(mode: Any) -> str:
    return "\n".join(
        f"- {skill.skill_id}: {skill.label} (recommended node: {skill.recommended_node_id})"
        for skill in skills_for_mode(mode)
    )


def _clean(value: Any, limit: int = 320) -> str:
    return " ".join(str(value or "").split())[:limit]


def _at(values: Iterable[Any] | None, index: int) -> str:
    items = list(values or [])
    return _clean(items[index]) if index < len(items) else ""


def _report_gap_rows(
    *,
    skill_gaps: Iterable[Any] | None = None,
    observed_skill_gaps: Iterable[Any] | None = None,
    recommended_next_nodes: Iterable[Any] | None = None,
    improvements: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    typed = list(skill_gaps or [])
    if typed:
        rows: list[dict[str, Any]] = []
        for item in typed:
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            if isinstance(item, dict):
                rows.append(dict(item))
        return rows

    legacy_gaps = list(observed_skill_gaps or [])
    legacy_recommendations = list(recommended_next_nodes or [])
    improvement_list = list(improvements or [])
    rows = []
    for index, gap in enumerate(legacy_gaps or improvement_list):
        recommendation = _at(legacy_recommendations, index)
        action = _at(improvement_list, index)
        if not action and recommendation not in _BY_ID:
            action = recommendation
        rows.append({
            "skill_id": gap,
            "label": gap,
            "evidence_quote": "",
            "recommended_action": action,
            "recommended_node_id": recommendation,
            "status": "active_gap",
        })
    return rows


def _report_row_skill_id(mode: Any, row: dict[str, Any]) -> str:
    """Resolve only a row-owned skill identity.

    A recommendation is an action target, not evidence that an unknown observed
    behavior belongs to that target. Exact fallback IDs remain valid because the
    model explicitly selected them; unknown and cross-mode rows remain unmapped.
    """
    candidate = row.get("skill_id") or row.get("label")
    matches = _matching_skill_ids(mode, candidate)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        requested_matches = _matching_skill_ids(mode, row.get("recommended_node_id"))
        if len(requested_matches) == 1 and requested_matches[0] in matches:
            return requested_matches[0]
    if row.get("label") and row.get("label") != candidate:
        label_matches = _matching_skill_ids(mode, row.get("label"))
        if len(label_matches) == 1:
            return label_matches[0]
    return ""


def unmapped_report_observations(
    mode: Any,
    *,
    skill_gaps: Iterable[Any] | None = None,
    observed_skill_gaps: Iterable[Any] | None = None,
    recommended_next_nodes: Iterable[Any] | None = None,
    improvements: Iterable[Any] | None = None,
) -> list[dict[str, str]]:
    """Preserve raw report observations that cannot own a durable skill card."""
    rows = _report_gap_rows(
        skill_gaps=skill_gaps,
        observed_skill_gaps=observed_skill_gaps,
        recommended_next_nodes=recommended_next_nodes,
        improvements=improvements,
    )
    unmapped: list[dict[str, str]] = []
    for row in rows:
        if _report_row_skill_id(mode, row):
            continue
        unmapped.append({
            "raw_skill_id": _clean(row.get("skill_id")),
            "label": _clean(row.get("label") or row.get("skill_id")),
            "evidence_quote": _clean(row.get("evidence_quote")),
            "recommended_action": _clean(row.get("recommended_action")),
            "recommended_node_id": _clean(row.get("recommended_node_id")),
            "status": _clean(row.get("status")) or "active_gap",
        })
    return unmapped


def canonicalize_report_gaps(
    mode: Any,
    *,
    skill_gaps: Iterable[Any] | None = None,
    observed_skill_gaps: Iterable[Any] | None = None,
    recommended_next_nodes: Iterable[Any] | None = None,
    improvements: Iterable[Any] | None = None,
) -> list[dict[str, str]]:
    """Canonicalize typed or legacy report gaps without losing row ownership."""
    rows = _report_gap_rows(
        skill_gaps=skill_gaps,
        observed_skill_gaps=observed_skill_gaps,
        recommended_next_nodes=recommended_next_nodes,
        improvements=improvements,
    )

    canonical: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        skill_id = _report_row_skill_id(mode, row)
        if not skill_id:
            continue
        raw_requested_node = str(row.get("recommended_node_id") or "").strip()
        if skill_id in seen:
            continue
        seen.add(skill_id)
        skill = _BY_ID[skill_id]
        requested_node = canonical_skill_id(mode, raw_requested_node)
        if not raw_requested_node or requested_node == fallback_skill_id(mode):
            requested_node = skill.recommended_node_id
        status = str(row.get("status") or "active_gap").strip()
        if status not in {"active_gap", "improving", "resolved"}:
            status = "active_gap"
        canonical_row: dict[str, Any] = {
            "skill_id": skill_id,
            "label": skill.label,
            "evidence_quote": _clean(row.get("evidence_quote")),
            "recommended_action": _clean(row.get("recommended_action")) or f"Practice {skill.label.lower()}.",
            "recommended_node_id": requested_node,
            "status": status,
        }
        if row.get("skill_score") is not None:
            canonical_row["skill_score"] = row.get("skill_score")
        if row.get("attempt_type") is not None:
            canonical_row["attempt_type"] = str(row.get("attempt_type") or "")
        canonical.append(canonical_row)
    return canonical
