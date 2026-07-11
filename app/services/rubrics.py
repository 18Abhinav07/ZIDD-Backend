"""Explicit rubrics for career prep nodes.

The LLM judges whether criteria are semantically met. The backend owns the
contract: required proof, missing-criterion caps, and mastery eligibility.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RubricCriterion:
    id: str
    label: str
    required: bool = False
    missing_cap: float = 0.6
    proof_required: bool = True


@dataclass(frozen=True)
class PrepRubric:
    node_id: str
    title: str
    module: str
    criteria: tuple[RubricCriterion, ...]
    pass_score: float = 0.7
    mastery_score: float = 0.85
    min_mastery_independent_passes: int = 3


R = RubricCriterion

_RUBRICS: dict[str, PrepRubric] = {
    "int_01_elevator_pitch": PrepRubric(
        node_id="int_01_elevator_pitch",
        title="Tell me about yourself",
        module="interview",
        criteria=(
            R("answers_question", "Answers the tell-me-about-yourself prompt", True, 0.55),
            R("specific_detail", "Includes concrete role-relevant detail", True, 0.62),
            R("pitch_structure", "Uses present role, proof, and direction in a tight structure", True, 0.65),
            R("future_goal", "Names the role or growth direction they are moving toward"),
        ),
    ),
    "int_02_strength_with_evidence": PrepRubric(
        node_id="int_02_strength_with_evidence",
        title="Back a strength with evidence",
        module="interview",
        criteria=(
            R("strength_claim", "Names one real professional strength", True, 0.58),
            R("specific_evidence", "Supports the strength with one concrete work example", True, 0.62),
            R("learner_action", "Shows what the learner personally did", True, 0.65),
            R("impact_signal", "Connects the example to an outcome or value"),
        ),
    ),
    "int_03_weakness_framing": PrepRubric(
        node_id="int_03_weakness_framing",
        title="Answer the weakness question",
        module="interview",
        criteria=(
            R("real_weakness", "Names a genuine non-cliche weakness", True, 0.6),
            R("mitigation_habit", "Gives a concrete habit or system used to manage it", True, 0.62),
            R("progress_evidence", "Includes a sign the weakness is improving", True, 0.68),
            R("non_self_sabotage", "Frames the weakness honestly without disqualifying the learner"),
        ),
    ),
    "gd_02_support_with_evidence": PrepRubric(
        node_id="gd_02_support_with_evidence",
        title="Support a GD stance with evidence",
        module="group_discussion",
        criteria=(
            R("clear_stance", "States a clear stance on the motion", True, 0.6),
            R(
                "concrete_evidence",
                "Supports the stance with a concrete fact, example, number, analogy, or experience",
                True,
                0.62,
            ),
            R("topic_relevance", "Stays on the active GD topic", True, 0.35),
            R("evidence_link", "Explains how the evidence supports the stance"),
        ),
    ),
    "int_04_star_behavioral": PrepRubric(
        node_id="int_04_star_behavioral",
        title="Answer behavioral questions with STAR",
        module="interview",
        criteria=(
            R("situation", "Sets the situation/context", True, 0.6),
            R("task", "Names the responsibility or goal", True, 0.6),
            R("actions", "Describes specific actions the learner took", True, 0.6),
            R("result", "States a result, impact, or learning", True, 0.6),
        ),
    ),
    "int_05_why_this_role": PrepRubric(
        node_id="int_05_why_this_role",
        title="Why this company",
        module="interview",
        criteria=(
            R("company_specific_fact", "References a concrete company or role fact", True, 0.62),
            R("personal_motivation_link", "Connects that fact to the learner's goals or values", True, 0.65),
            R("role_relevance", "Explains why the role is a fit for the learner's work", True, 0.68),
            R("non_generic", "Avoids generic reputation, stability, or flattery-only reasoning"),
        ),
    ),
    "int_06_own_a_failure": PrepRubric(
        node_id="int_06_own_a_failure",
        title="Own a failure story",
        module="interview",
        criteria=(
            R("ownership", "Takes personal ownership without blaming others", True, 0.6),
            R("impact", "Names the user, customer, business, or team impact", True, 0.65),
            R("response_action", "Explains the immediate response or repair action", True, 0.65),
            R("prevention", "Explains the prevention or process change afterward", True, 0.65),
            R("non_defensive_tone", "Avoids excuses or blame-shifting"),
        ),
    ),
    "int_07_clarify_before_answering": PrepRubric(
        node_id="int_07_clarify_before_answering",
        title="Clarify before answering",
        module="interview",
        criteria=(
            R("recognizes_ambiguity", "Identifies what is unclear in the prompt", True, 0.6),
            R("asks_targeted_question", "Asks one concise clarifying question", True, 0.62),
            R("states_answer_frame", "Shows how they would answer after clarification", True, 0.68),
            R("professional_tone", "Keeps the clarification confident and non-defensive"),
        ),
    ),
    "int_08_quantify_impact": PrepRubric(
        node_id="int_08_quantify_impact",
        title="Quantify your impact",
        module="interview",
        criteria=(
            R("impact_claim", "States the impact being claimed", True, 0.58),
            R("quantified_before_after", "Uses a number, count, percentage, time, scale, or before/after comparison", True, 0.62),
            R("learner_contribution", "Connects the result to the learner's own action", True, 0.65),
            R("business_or_user_value", "Links the metric to user, team, or business value"),
        ),
    ),
    "int_09_diplomatic_pushback": PrepRubric(
        node_id="int_09_diplomatic_pushback",
        title="Disagree with the interviewer",
        module="interview",
        criteria=(
            R("acknowledges_view", "Acknowledges the interviewer's point fairly", True, 0.6),
            R("clear_counterposition", "States a clear alternative position", True, 0.62),
            R("requirement_based_reasoning", "Ties the disagreement to requirements, constraints, or tradeoffs", True, 0.65),
            R("collaborative_tone", "Leaves room for nuance or hybrid options without sounding combative", True, 0.65),
        ),
    ),
    "int_10_close_strong": PrepRubric(
        node_id="int_10_close_strong",
        title="Close and ask sharp questions",
        module="interview",
        criteria=(
            R("specific_closing_question", "Asks a specific question about success, team, role, or priorities", True, 0.62),
            R("role_relevance", "Makes the question relevant to the target role", True, 0.65),
            R("role_fit_evidence", "Connects the close to specific value the learner can bring", True, 0.68),
            R("professional_close", "Includes a concise confident close in either natural order", True, 0.68),
            R("non_generic", "Avoids generic feedback-only or benefits-only questions", True, 0.65),
        ),
    ),
    "int_11_salary_negotiation": PrepRubric(
        node_id="int_11_salary_negotiation",
        title="Negotiate your offer",
        module="interview",
        criteria=(
            R("clear_anchor", "Gives a clear compensation range or anchor", True, 0.62),
            R("market_or_value_reason", "Justifies the ask with market data, scope, or value", True, 0.65),
            R("collaborative_flexibility", "Signals flexibility on structure without collapsing the ask", True, 0.68),
            R("calm_tone", "Keeps tone calm and direct without conceding the anchor; a courteous thank-you is not an apology", True, 0.65),
        ),
    ),
    "int_12_explain_a_gap": PrepRubric(
        node_id="int_12_explain_a_gap",
        title="Explain a gap or departure",
        module="interview",
        criteria=(
            R("brief_context", "Explains the gap or departure briefly without over-detailing", True, 0.6),
            R("non_blaming_tone", "Avoids blame, defensiveness, or gossip", True, 0.62),
            R("productive_use_or_learning", "Shows learning, recovery, or productive use of the period", True, 0.65),
            R("forward_focus", "Connects back to readiness for the target role", True, 0.68),
        ),
    ),
    "gd_01_stake_position": PrepRubric(
        node_id="gd_01_stake_position",
        title="Stake a clear position",
        module="group_discussion",
        criteria=(
            R("clear_stance", "Takes an unambiguous position on the motion", True, 0.58),
            R("topic_relevance", "Stays on the active GD topic", True, 0.35),
            R("low_hedging", "Avoids fence-sitting or excessive hedging", True, 0.65),
            R("concise_opening", "States the position before reasons in one or two sentences"),
        ),
    ),
    "gd_03_take_the_floor": PrepRubric(
        node_id="gd_03_take_the_floor",
        title="Enter the discussion",
        module="group_discussion",
        criteria=(
            R("polite_entry_phrase", "Uses a polite entry or interjection phrase", True, 0.6),
            R("links_prior_point", "Connects to what another participant just said", True, 0.62),
            R("adds_new_value", "Adds a new point rather than merely asking to speak", True, 0.65),
            R("assertive_not_rude", "Claims space without interrupting aggressively"),
        ),
    ),
    "gd_04_build_on_others": PrepRubric(
        node_id="gd_04_build_on_others",
        title="Build on another's point",
        module="group_discussion",
        criteria=(
            R("credits_prior_speaker", "Credits or clearly references the prior speaker's point", True, 0.6),
            R("extends_idea", "Adds a meaningful extension, implication, or example", True, 0.62),
            R("topic_relevance", "Keeps the extension on the active topic", True, 0.35),
            R("collaborative_tone", "Sounds collaborative rather than hijacking the point"),
        ),
    ),
    "gd_05_disagree_respectfully": PrepRubric(
        node_id="gd_05_disagree_respectfully",
        title="Disagree respectfully",
        module="group_discussion",
        criteria=(
            R("acknowledges_valid_point", "Acknowledges something fair in the other view", True, 0.6),
            R("clear_counter", "States a clear counterpoint", True, 0.62),
            R("reasoned_basis", "Gives a reason tied to the topic, not personal preference only", True, 0.65),
            R("civil_tone", "Challenges the idea without attacking the person"),
        ),
    ),
    "gd_06_balanced_view": PrepRubric(
        node_id="gd_06_balanced_view",
        title="Present a balanced view",
        module="group_discussion",
        criteria=(
            R("names_both_sides", "Names a valid point on both sides of the issue", True, 0.6),
            R("weighs_tradeoff", "Explains which tradeoff matters most", True, 0.62),
            R("returns_to_position", "Returns to a clear overall recommendation or stance", True, 0.68),
            R("topic_relevance", "Keeps both sides tied to the active GD topic", True, 0.35),
        ),
    ),
    "gd_07_steer_back": PrepRubric(
        node_id="gd_07_steer_back",
        title="Steer a derailed discussion",
        module="group_discussion",
        criteria=(
            R("identifies_derailment", "Signals that the group has drifted or needs focus", True, 0.6),
            R("redirects_to_topic", "Redirects back to the active motion or decision", True, 0.35),
            R("gives_next_step", "Suggests the next useful discussion angle or question", True, 0.65),
            R("non_controlling_tone", "Facilitates without sounding bossy"),
        ),
    ),
    "gd_08_include_quiet": PrepRubric(
        node_id="gd_08_include_quiet",
        title="Bring a quiet participant into the GD",
        module="group_discussion",
        criteria=(
            R("names_quiet_participant", "Names or clearly addresses the quiet participant", True, 0.6),
            R("topic_linked_invite", "Connects the invitation to the active topic", True, 0.6),
            R("respectful_floor_give", "Gives the floor respectfully without sounding performative", True, 0.65),
            R("non_pressuring_tone", "Invites without embarrassing or forcing the participant", True, 0.65),
        ),
    ),
    "gd_09_manage_dominator": PrepRubric(
        node_id="gd_09_manage_dominator",
        title="Manage a dominant speaker",
        module="group_discussion",
        criteria=(
            R("acknowledges_contribution", "Acknowledges the dominant speaker's contribution", True, 0.6),
            R("redistributes_floor", "Redirects speaking space to the group or another participant", True, 0.62),
            R("topic_link", "Keeps the redirection tied to the discussion topic", True, 0.35),
            R("respectful_boundary", "Sets a boundary without sounding rude", True, 0.65),
        ),
    ),
    "gd_10_drive_consensus": PrepRubric(
        node_id="gd_10_drive_consensus",
        title="Summarize and drive consensus",
        module="group_discussion",
        criteria=(
            R("summarizes_key_points", "Summarizes at least two key points from the discussion", True, 0.62),
            R("identifies_common_ground", "Names an area of agreement or emerging consensus", True, 0.65),
            R("proposes_next_step", "Proposes a final recommendation or next step", True, 0.68),
            R("balanced_credit", "Credits the group rather than presenting only a personal conclusion"),
        ),
    ),
}

# Backward-compatible alias used in older notes/tests.
_RUBRICS["int_06_failure_story"] = _RUBRICS["int_06_own_a_failure"]


def get_rubric(node_id: str) -> PrepRubric:
    if node_id in _RUBRICS:
        return _RUBRICS[node_id]
    raise KeyError(f"no prep rubric for node: {node_id}")


def is_prep_rubric_node(node_id: str) -> bool:
    return node_id.startswith(("gd_", "int_"))
