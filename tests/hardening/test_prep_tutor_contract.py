import asyncio
import json
import re
from datetime import datetime, timezone

from app.ai.schemas import CriterionEval, PrepRubricEval
from app.services import session_service as svc
from app.services.rubric_engine import apply_caps, build_evaluation_packet, compute_attempt_credit
from app.services.content_personalization import render_gd_bridge_exercise
from app.services.tutor_plan import build_tutor_turn_plan
from app.graph.nodes.bridge import personalize_bridge_exercise, select_bridge_exercise


def _run(coro):
    return asyncio.run(coro)


async def _collect_async(stream):
    items = []
    async for item in stream:
        items.append(item)
    return items


def test_missing_required_criterion_caps_score_and_blocks_pass():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because it helps students get jobs faster."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="clear_stance", met=True, quality=0.8, evidence_quote="I support AI"),
            CriterionEval(
                id="concrete_evidence",
                met=False,
                quality=0.2,
                reason="No example, data, case, comparison, or concrete observation is provided.",
            ),
            CriterionEval(
                id="topic_relevance",
                met=True,
                quality=0.9,
                evidence_quote="AI in campus placements",
            ),
        ],
        required_missing=["concrete_evidence"],
        strengths=["clear stance"],
        errors=["missing evidence"],
        next_focus="Add one concrete example or data-backed reason.",
        on_task=True,
        english=True,
        affect="neutral",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.effective_score <= 0.62
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert "concrete_evidence" in result.required_missing
    assert "missing_required:concrete_evidence" in result.blockers


def test_bridge_node_targets_missing_star_result_criterion():
    from app.graph.nodes.bridge import bridge_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["last_eval_score"] = 0.54
    state["last_rubric_result"] = {
        "required_missing": ["result"],
        "blockers": ["missing_required:result"],
        "next_focus": "Add the result or measurable impact.",
        "criteria": [
            {"id": "action", "met": True, "quality": 0.7, "evidence_quote": "added alerts"},
            {"id": "result", "met": False, "quality": 0.1, "reason": "No outcome named."},
        ],
    }

    updates = _run(bridge_node(state))

    assert updates["pending_game"]["id"] == "int_04_star_behavioral_bx4"
    assert "outcome" in updates["pending_game"]["context"].lower()
    assert updates["active_prompt_attempt_type"] == "scaffolded"


def test_bridge_node_targets_weakness_progress_evidence_criterion():
    from app.graph.nodes.bridge import bridge_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["last_eval_score"] = 0.58
    state["last_rubric_result"] = {
        "required_missing": ["progress_evidence"],
        "blockers": ["missing_required:progress_evidence"],
        "next_focus": "Add a recent sign it is improving.",
        "criteria": [
            {"id": "real_weakness", "met": True, "quality": 0.7, "evidence_quote": "over-explain"},
            {"id": "mitigation_habit", "met": True, "quality": 0.7, "evidence_quote": "start with criteria"},
            {"id": "progress_evidence", "met": False, "quality": 0.1, "reason": "No progress signal."},
        ],
    }

    updates = _run(bridge_node(state))

    assert updates["pending_game"]["id"] == "int_03_weakness_framing_bx4"
    assert "improving" in updates["pending_game"]["sentence"].lower()


def test_bridge_selector_uses_missing_gd_evidence_gap_within_target_band():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="stance-standard",
            type="multiple_choice",
            sentence="Which opening commits to a side?",
            hint="clear side first",
            context="Practises taking a clear stance.",
            answer_key="I support it with one condition.",
            options=[
                "I support it with one condition.",
                "It depends on many things.",
            ],
            band="standard",
        ),
        BridgeExercise(
            id="evidence-standard",
            type="multiple_choice",
            sentence="Which reply adds concrete evidence to the GD point?",
            hint="look for an example, fact, or metric",
            context="Targets the concrete evidence gap instead of repeating a stance.",
            answer_key="For instance, the pilot cut turnaround time by 20%.",
            options=[
                "For instance, the pilot cut turnaround time by 20%.",
                "I strongly believe this is correct.",
            ],
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.55,
        gap_context={
            "required_missing": ["concrete_evidence"],
            "blockers": ["missing_required:concrete_evidence"],
            "next_focus": "Add one concrete example or data-backed reason.",
        },
    )

    assert selected.id == "evidence-standard"


def test_bridge_selector_skips_served_targeted_exercise_before_fallback():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="evidence-standard-a",
            type="fill_blank",
            sentence="For instance, the pilot cut ___ by 20%.",
            hint="a metric",
            context="Targets the concrete evidence gap.",
            answer_key="turnaround time",
            band="standard",
        ),
        BridgeExercise(
            id="stance-standard",
            type="fill_blank",
            sentence="I ___ this policy.",
            hint="commit to a side",
            context="Targets a clear stance.",
            answer_key="support",
            band="standard",
        ),
        BridgeExercise(
            id="evidence-standard-b",
            type="multiple_choice",
            sentence="Which sentence adds evidence?",
            hint="pick the one with data",
            context="A second concrete evidence drill.",
            answer_key="A trial across 300 users reduced wait time.",
            options=[
                "A trial across 300 users reduced wait time.",
                "I feel this is better.",
            ],
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=["evidence-standard-a"],
        score=0.55,
        gap_context={"required_missing": ["concrete_evidence"]},
    )

    assert selected.id == "evidence-standard-b"


def test_bridge_selector_without_gap_context_preserves_severity_order():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="first-standard",
            type="fill_blank",
            sentence="I ___ this policy.",
            hint="commit to a side",
            context="First standard exercise.",
            answer_key="support",
            band="standard",
        ),
        BridgeExercise(
            id="second-standard",
            type="fill_blank",
            sentence="For instance, the pilot cut ___ by 20%.",
            hint="a metric",
            context="Second standard exercise.",
            answer_key="turnaround time",
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.55,
    )

    assert selected.id == "first-standard"


def test_bridge_selector_preserves_foundational_scaffold_for_very_weak_answer():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="foundation-stem",
            type="fill_blank",
            sentence="I ___ this policy.",
            hint="commit to a side",
            context="Foundational stance stem.",
            answer_key="support",
            band="foundational",
        ),
        BridgeExercise(
            id="evidence-standard",
            type="fill_blank",
            sentence="For instance, the pilot cut ___ by 20%.",
            hint="a metric",
            context="Targets the concrete evidence gap.",
            answer_key="turnaround time",
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.1,
        gap_context={"required_missing": ["concrete_evidence"]},
    )

    assert selected.id == "foundation-stem"


def test_interview_pitch_future_goal_evidence_is_reconciled_before_caps():
    answer = (
        "I'm a backend engineer focused on reliable APIs, payment flows, and production debugging. "
        "In a payment service, I traced retry/idempotency gaps and added safer transaction logging. "
        "My next goal is to own larger distributed systems and mentor engineers on operational discipline."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.86,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.8, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.8, evidence_quote="payment service"),
            CriterionEval(id="pitch_structure", met=False, quality=0.2, evidence_quote="", reason="missing direction"),
            CriterionEval(id="future_goal", met=False, quality=0.2, evidence_quote="", reason="missing future goal"),
        ],
        required_missing=["pitch_structure"],
        errors=["missing required rubric proof: pitch_structure"],
        next_focus="add a clear future goal",
        pass_eligible=True,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["future_goal"].met is True
    assert rows["pitch_structure"].met is True
    assert result.required_missing == []
    assert result.effective_score >= packet.pass_score
    assert result.pass_eligible is True
    assert result.mastery_eligible is False
    assert "future goal" not in result.next_focus.lower()


def test_interview_weakness_shape_evidence_is_reconciled_before_caps():
    answer = (
        "Earlier, I tended to explain technical implementation before business impact. "
        "I now start with the decision criteria, explain the tradeoff in plain language, "
        "and prove the outcome. In a payment rollout, that meant catching two retry edge "
        "cases early, avoiding a full rollback, and giving product a clear revenue-protection "
        "reason to expand gradually."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.78,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.6, evidence_quote="technical implementation"),
            CriterionEval(id="mitigation_habit", met=False, quality=0.2, reason="habit is too implicit"),
            CriterionEval(id="progress_evidence", met=False, quality=0.2, reason="progress evidence is not explicit"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.8, evidence_quote="I now start"),
        ],
        required_missing=["mitigation_habit", "progress_evidence"],
        errors=["missing required rubric proof: mitigation_habit, progress_evidence"],
        next_focus="Add the corrective habit and concrete progress evidence.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["real_weakness"].met is True
    assert rows["mitigation_habit"].met is True
    assert rows["progress_evidence"].met is True
    assert result.required_missing == []
    assert result.effective_score >= packet.pass_score
    assert result.pass_eligible is True
    assert result.mastery_eligible is False
    assert "progress evidence" not in result.next_focus.lower()
    assert "three-part weakness answer" not in result.next_focus.lower()
    assert "pressure-test" in result.next_focus.lower()


def test_interview_weakness_reconciliation_rewrites_old_delivery_focus_when_core_already_met():
    answer = (
        "Earlier, I tended to explain technical implementation before business impact. "
        "I now start with the decision criteria, explain the tradeoff in plain language, "
        "and prove the outcome. In a payment rollout, that meant catching two retry edge "
        "cases early, avoiding a full rollback, and giving product a clear revenue-protection "
        "reason to expand gradually."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.76, evidence_quote="technical implementation"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.76, evidence_quote="decision criteria"),
            CriterionEval(id="progress_evidence", met=True, quality=0.76, evidence_quote="two retry edge cases"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.8, evidence_quote="I now start"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Practise delivering the three-part weakness answer concisely.",
        pass_eligible=True,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is True
    assert "three-part weakness answer" not in result.next_focus.lower()
    assert "practise delivering" not in result.next_focus.lower()
    assert "pressure-test" in result.next_focus.lower()


def test_interview_weakness_shape_reconciliation_does_not_credit_generic_claims():
    answer = (
        "My weakness is jumping straight into technical details before business impact. "
        "I manage it with decision criteria first and a habit of comparing options. "
        "The result should be better outcomes, but I have not named a real case yet."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.7,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.65, evidence_quote="jumping straight"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.65, evidence_quote="decision criteria"),
            CriterionEval(id="progress_evidence", met=False, quality=0.1, reason="no real case"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.7, evidence_quote="I manage it"),
        ],
        required_missing=["progress_evidence"],
        errors=["missing required rubric proof: progress_evidence"],
        next_focus="Add a real progress example.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_weakness_shape_reconciliation_rejects_loose_meeting_claim():
    answer = (
        "I used to over-explain technical trade-offs. Now I use decision criteria first, "
        "and it helped in a meeting."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.72,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.65, evidence_quote="over-explain"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.65, evidence_quote="decision criteria"),
            CriterionEval(id="progress_evidence", met=False, quality=0.2, reason="too generic"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.7, evidence_quote="Now I use"),
        ],
        required_missing=["progress_evidence"],
        errors=["missing required rubric proof: progress_evidence"],
        next_focus="Add a real progress example.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_weakness_overcredit_is_capped_without_concrete_progress():
    answer = (
        "I used to over-explain technical trade-offs. Now I use decision criteria first, "
        "and it helped in a meeting."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="helped in a meeting"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert "minimum_gate:progress_evidence" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_pitch_overcredit_is_capped_without_specific_proof():
    answer = "I'm a backend engineer. I improved things. Now I want to own larger systems."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.88,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="improved things"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own larger systems"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_pitch_detail_gate_does_not_match_api_inside_word():
    answer = "I'm a backend engineer. I improved capital planning. Now I want to lead platform work."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.88,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="capital planning"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="lead platform work"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_gate_requires_direction_for_pitch_structure():
    answer = "I'm a backend engineer. I built FastAPI payment APIs."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote=""),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:pitch_structure" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False


def test_interview_pitch_domain_noun_without_proof_is_not_specific_detail():
    answer = "I'm a backend engineer. I want to own payment systems."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="payment systems"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own payment systems"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_gate_accepts_non_software_specific_proof():
    answer = (
        "I'm a sales manager focused on enterprise renewals. "
        "I led a renewal process that reduced churn by 12%. "
        "I want to grow into revenue leadership."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Sales Manager"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="sales manager"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="reduced churn by 12%"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="sales manager"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="revenue leadership"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_pitch_identity_gate_rejects_project_without_role_identity():
    answer = "In a project, I built FastAPI payment APIs, and I want to own platform reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="project"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="project"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own platform reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:answers_question" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_accepts_nurse_with_specific_proof():
    answer = (
        "I'm a nurse focused on safer ward handoffs. "
        "I reduced medication errors by 20% with a checklist. "
        "I want to grow into ward leadership."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Nurse"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="nurse"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="medication errors by 20%"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="nurse focused on safer ward handoffs"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="ward leadership"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_pitch_identity_gate_rejects_future_leader_without_current_role():
    answer = "I built FastAPI payment APIs, and I want to grow as a leader."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="leader"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="grow as a leader"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="grow as a leader"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_rejects_future_known_role_without_current_identity():
    answer = "I built FastAPI payment APIs, and I want to grow as a backend engineer."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="grow as a backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="grow as a backend engineer"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_rejects_future_role_before_marker():
    answer = "Backend engineer is my next role. I built FastAPI payment APIs."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="Backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="Backend engineer is my next role"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="next role"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_accepts_lead_backend_engineering_phrasing():
    answer = (
        "I lead backend engineering for payment reliability. "
        "I reduced checkout incidents by 30%. "
        "I want to own platform reliability."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineering"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="reduced checkout incidents by 30%"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="lead backend engineering"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own platform reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_pitch_negated_proof_is_capped():
    answer = "I'm a backend engineer. I haven't built FastAPI payment APIs yet, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="haven't built FastAPI payment APIs yet"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_did_not_work_on_negated_proof_is_capped():
    answer = "I'm a backend engineer. I did not work on payment APIs, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="did not work on payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_do_not_work_on_negated_proof_is_capped():
    answer = "I'm a backend engineer. I don't work on payment APIs yet, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="don't work on payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_no_project_where_built_negated_proof_is_capped():
    answer = "I'm a backend engineer. I don't have a project where I built payment APIs yet, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="project where I built payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_generic_customer_progress_is_capped():
    answer = (
        "I used to over-explain technical trade-offs. "
        "Now I use decision criteria first. "
        "This helped a customer and improved stakeholder confidence."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="helped a customer"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert "minimum_gate:progress_evidence" in result.blockers
    assert result.pass_eligible is False


def test_interview_weakness_customer_meeting_vague_progress_is_capped():
    answer = (
        "I used to over-explain technical trade-offs. "
        "Now I use decision criteria first. "
        "In a customer meeting, this helped the customer and improved stakeholder confidence."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="improved stakeholder confidence"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert "minimum_gate:progress_evidence" in result.blockers
    assert result.pass_eligible is False


def test_interview_weakness_no_concrete_example_negation_is_capped():
    answer = (
        "I used to over-explain technical trade-offs. "
        "Now I use decision criteria first. "
        "I don't have a concrete example yet, but in a customer meeting this helped the customer."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="customer meeting"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_real_gate_rejects_sometimes_without_weakness():
    answer = (
        "Sometimes I help customers. "
        "I now use decision criteria first. "
        "In a customer escalation, that resolved the issue."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="Sometimes"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="resolved the issue"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="I now"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "real_weakness" in result.required_missing
    assert "minimum_gate:real_weakness" in result.blockers
    assert result.pass_eligible is False


def test_interview_weakness_real_gate_rejects_used_to_without_weak_behavior():
    answer = (
        "I used to help customers. "
        "I now use decision criteria first. "
        "In a customer escalation, that resolved the issue."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="used to"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="resolved the issue"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="I now"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "real_weakness" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_real_gate_accepts_jump_to_implementation_phrasing():
    answer = (
        "I tend to jump straight into implementation before explaining business impact. "
        "I now lead with decision criteria first. "
        "In a payment rollout, that helped the team catch two retry edge cases and avoid a rollback."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="jump straight into implementation"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="catch two retry edge cases"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="I now"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_prep_rubric_schema_uses_plan_field_names_but_accepts_legacy_aliases():
    schema = PrepRubricEval.model_json_schema()

    assert "raw_score" in schema["properties"]
    assert "required_missing" in schema["properties"]
    assert "score" not in schema["properties"]
    criterion_props = schema["$defs"]["CriterionEval"]["properties"]
    assert "id" in criterion_props
    assert "quality" in criterion_props
    assert "criterion_id" not in criterion_props

    parsed = PrepRubricEval.model_validate(
        {
            "score": 0.72,
            "missing_required_criteria": ["concrete_evidence"],
            "criteria": [
                {
                    "criterion_id": "clear_stance",
                    "met": True,
                    "score": 0.7,
                    "rationale": "Stance is present.",
                    "evidence_quote": "AI is useful",
                }
            ],
            "next_focus": "Add evidence.",
        }
    )

    assert parsed.raw_score == 0.72
    assert parsed.required_missing == ["concrete_evidence"]
    assert parsed.criteria[0].id == "clear_stance"
    assert parsed.criteria[0].quality == 0.7
    assert parsed.criteria[0].reason == "Stance is present."


def test_required_criterion_marked_met_without_quote_is_not_valid_proof():
    state = svc._new_state("user-1", "session-1", "int_06_own_a_failure", [], task_type="interview_prep")
    answer = "I made a migration mistake and I learned to test more carefully."
    packet = build_evaluation_packet(state, svc.get_node("int_06_own_a_failure"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.86,
        criteria=[
            CriterionEval(id="ownership", met=True, quality=0.8, evidence_quote="I made a migration mistake"),
            CriterionEval(id="impact", met=True, quality=0.7, evidence_quote="migration mistake"),
            CriterionEval(id="response_action", met=True, quality=0.8, evidence_quote=""),
            CriterionEval(id="prevention", met=True, quality=0.8, evidence_quote="test more carefully"),
        ],
        required_missing=[],
        strengths=["owns the mistake"],
        errors=[],
        next_focus="Add the immediate response action.",
        on_task=True,
        english=True,
        affect="neutral",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert "response_action" in result.required_missing
    assert "invalid_proof:response_action" in result.blockers


def test_tutor_plan_for_partial_answer_disallows_mastery_praise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "I think AI is useful because it helps.",
    )
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.72,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.7, evidence_quote="AI is useful"),
                CriterionEval(id="concrete_evidence", met=False, quality=0.1),
                CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="AI"),
            ],
            required_missing=["concrete_evidence"],
            strengths=["clear stance"],
            errors=["missing evidence"],
            next_focus="Add one concrete example.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=False,
        ),
    )

    plan = build_tutor_turn_plan(result, state)

    assert plan.verdict == "partial"
    assert plan.next_action == "rewrite"
    assert plan.allowed_praise is False
    assert plan.tone_policy == "direct_no_praise"
    assert plan.focus == "Add one concrete example."


def test_tutor_plan_escalates_repeated_hot_gap_without_mastery_praise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state["session_learning_delta"] = {
        "strengths": [],
        "active_gaps": ["Add the result or measurable impact."],
        "repeated_issue_counts": {"criterion:result": 1},
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": ["In a payment outage, I traced retries."],
    }
    result = {
        "english": True,
        "on_task": True,
        "required_missing": ["result"],
        "pass_eligible": False,
        "mastery_eligible": False,
        "next_focus": "Show the business impact.",
    }

    plan = build_tutor_turn_plan(result, state)

    assert plan.verdict == "repeat_gap"
    assert plan.next_action == "micro_drill_then_rewrite"
    assert plan.allowed_praise is False
    assert plan.tone_policy == "direct_no_praise_supportive"
    assert "repeated 2x this session" in plan.focus


def test_hot_session_delta_records_missing_criterion_repeat_keys(store):
    state = svc._new_state(
        "user-1",
        "session-hot-delta-criterion",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["user_input"] = "In a payment outage, I traced retries and shipped a fix."
    state["last_eval_score"] = 0.49
    state["last_diagnosis"] = {"on_task": True, "english": True, "affect": "neutral", "next_focus": "Add the measurable result."}
    state["last_rubric_result"] = {
        "raw_score": 0.49,
        "effective_score": 0.49,
        "strengths": ["specific situation"],
        "next_focus": "Add the measurable result.",
        "required_missing": ["result"],
        "criteria": [{"id": "result", "met": False, "evidence_quote": ""}],
        "blockers": ["missing_required:result"],
        "pass_eligible": False,
        "mastery_eligible": False,
        "attempt_type": "independent",
    }
    state["tutor_turn_plan"] = {"next_action": "rewrite"}

    _run(svc._track_turn(state, "int_04_star_behavioral"))

    repeated = state["session_learning_delta"]["repeated_issue_counts"]
    assert repeated["Add the measurable result."] == 1
    assert repeated["criterion:result"] == 1
    assert state["session_learning_delta"]["task_type"] == "interview_prep"
    assert state["session_learning_delta"]["module_id"] == "interview"


def test_tutor_plan_disallows_celebratory_praise_for_scaffolded_and_borderline_passes():
    scaffolded_plan = build_tutor_turn_plan(
        {
            "english": True,
            "on_task": True,
            "required_missing": [],
            "pass_eligible": True,
            "mastery_eligible": False,
            "next_focus": "Try it without the scaffold.",
        },
        {},
        scaffolded=True,
    )
    borderline_plan = build_tutor_turn_plan(
        {
            "english": True,
            "on_task": True,
            "required_missing": [],
            "pass_eligible": True,
            "mastery_eligible": False,
            "next_focus": "Make the answer more concrete.",
        },
        {},
    )

    assert scaffolded_plan.allowed_praise is False
    assert scaffolded_plan.tone_policy == "warm_but_not_mastery"
    assert borderline_plan.allowed_praise is False
    assert borderline_plan.tone_policy == "measured_no_celebration"


def test_coach_block_surfaces_hot_session_delta_as_private_prompt_context():
    from app.ai.prompts import _coach_block, build_opening_prompt, coach_view
    from app.content.registry import get_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["session_learning_delta"] = {
        "strengths": ["clear stance"],
        "active_gaps": ["Add a concrete metric."],
        "repeated_issue_counts": {"Add a concrete metric.": 2},
        "module_id": "group_discussion",
        "task_type": "gd_prep",
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": ["Remote default improves hiring reach."],
    }

    coach = coach_view(state)
    block = _coach_block(coach)
    prompt = build_opening_prompt(
        get_node("gd_02_support_with_evidence"),
        memory_context=[],
        coach=coach,
        career_context=state["career_context"],
    )

    for text in (block, prompt):
        assert "Hot session learning delta" in text
        assert "Add a concrete metric." in text
        assert "repeated gaps: Add a concrete metric. x2" in text
        assert "Remote default improves hiring reach." in text
        assert "do not call this mastery" in text


def test_hot_session_delta_is_not_rendered_when_mode_scope_mismatches():
    from app.ai.prompts import _coach_block, coach_view

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["session_learning_delta"] = {
        "module_id": "group_discussion",
        "task_type": "gd_prep",
        "active_gaps": ["Add a concrete GD metric."],
        "repeated_issue_counts": {"Add a concrete GD metric.": 2},
        "latest_evidence_quotes": ["Remote work default improves hiring reach."],
    }

    block = _coach_block(coach_view(state))

    assert "Hot session learning delta" not in block
    assert "concrete GD metric" not in block


def test_interview_prep_prompt_strips_gd_topic_preferences_from_context():
    from app.ai.prompts import build_teach_prompt
    from app.content.registry import get_node

    prompt = build_teach_prompt(
        get_node("int_04_star_behavioral"),
        messages=[
            {
                "role": "user",
                "content": "In a payment outage, I traced retries and shipped an idempotency fix.",
            }
        ],
        diagnosis={"next_focus": "Add the result."},
        memory_context=[],
        career_context={
            "primary_role": "Backend Engineer",
            "role_family": "software_technical",
            "gd_topics": ["Should remote work be the default?"],
        },
    )

    assert "Backend Engineer" in prompt
    assert "Should remote work be the default?" not in prompt
    assert "preferred GD topics" not in prompt
    assert "GD topic lock" not in prompt


def test_low_mastery_sanitizer_removes_all_right_points_overpraise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["last_eval_score"] = 0.26
    state["last_clean_pass_score"] = 0.26
    state["current_mastery"] = 0.26

    cleaned = svc._sanitize_coaching_response(
        "Great job — you've hit all the right points. Now add one security objection.",
        state,
        "strengthen",
    )

    assert "Great job" not in cleaned
    assert "all the right points" not in cleaned
    assert cleaned.startswith("Let's tighten this.") or cleaned.startswith("That answer is on the right track.")
    assert "security objection" in cleaned


def test_low_mastery_sanitizer_removes_browser_caught_overpraise_and_topic_drift():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["last_eval_score"] = 0.48
    state["last_rubric_result"] = {"effective_score": 0.48}
    raw = (
        "You've done well by addressing security concerns proactively. Imagine you're arguing "
        "that digital payments should be mandatory for all businesses. You could start with a "
        "clear position like, \"I believe all businesses should adopt digital payment methods.\" "
        "Try restating your support for remote work as the default."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You've done well" not in cleaned
    assert "Imagine you're arguing" not in cleaned
    assert "digital payments" not in cleaned
    assert "adopt digital payment" not in cleaned
    assert "remote work" in cleaned


def test_low_mastery_sanitizer_removes_strong_answer_overpraise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["last_eval_score"] = 0.41
    state["last_clean_pass_score"] = 0.41
    state["current_mastery"] = 0.24
    raw = (
        "Strong answer — you covered the main concerns clearly. "
        "Now add one concrete metric that would prove remote work is succeeding."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert not lowered.startswith("strong answer")
    assert "you covered the main concerns" not in lowered
    assert cleaned.startswith("Let's tighten this.")
    assert "one concrete metric" in lowered


def test_farewell_is_evidence_calibrated_for_weak_or_frustrated_prep_session():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["learner_name"] = "Raptor"
    state["clean_streak"] = 0
    state["last_eval_score"] = 0.34
    state["current_mastery"] = 0.22
    state["needs_support"] = True
    state["last_diagnosis"] = {"next_focus": "Add measurable result evidence."}

    text = svc._farewell(state)
    lowered = text.lower()

    assert not lowered.startswith("great session")
    assert "master" not in lowered
    assert "ready" not in lowered
    assert "result evidence" in lowered
    assert "raptor" in lowered


def test_summary_prompt_blocks_generic_praise_and_mastery_claims_in_memory_notes():
    from app.ai.prompts import build_summary_prompt

    prompt = build_summary_prompt(
        svc.get_node("int_04_star_behavioral"),
        [
            {
                "role": "user",
                "content": "In a payment outage, I traced retries and shipped an idempotency fix.",
            }
        ],
    )
    lowered = prompt.lower()

    for phrase in (
        "do not use generic praise",
        "do not claim readiness",
        "do not claim mastery",
        "great job",
        "great session",
        "strong answer",
        "mastered",
    ):
        assert phrase in lowered


def test_end_session_sanitizes_generated_summary_before_persisting(monkeypatch, store):
    state = svc._new_state(
        "user-1",
        "session-summary-sanitize",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["messages"] = [{"role": "user", "content": "I traced payment retries."}]
    svc.SessionStore["session-summary-sanitize"] = state
    captured: dict[str, str] = {}

    async def unsafe_summary(*_args, **_kwargs):
        return (
            "Strengths: Great job — strong answer, you are ready and mastered this. "
            "A better version would be: \"I reduced duplicate charges by 30%.\"\n"
            "Watch: none\n"
            "Next focus: ready for the next level"
        )

    async def capture_end_session(session_id, final_summary="", avg_score=0.0):
        captured["final_summary"] = final_summary

    async def capture_memory(user_id, session_id, node_id, raw, task_type, score=0.0):
        captured["memory_raw"] = raw

    monkeypatch.setattr(svc, "summarize_session", unsafe_summary)
    monkeypatch.setattr(store, "end_session", capture_end_session)
    monkeypatch.setattr(store, "write_memory", capture_memory)

    result = _run(svc.end_session("session-summary-sanitize"))
    combined = "\n".join(
        captured.get(key, "") for key in ("final_summary", "memory_raw")
    ).lower()

    for forbidden in (
        "great job",
        "strong answer",
        "you are ready",
        "mastered this",
        "a better version would be",
        "reduced duplicate charges by 30%",
        "ready for the next level",
    ):
        assert forbidden not in combined
    assert "learner's own facts" in combined
    assert result == captured["final_summary"] == captured["memory_raw"]


def test_career_memory_context_block_sanitizes_raw_report_and_evidence_text():
    from app.ai.prompts import _career_context_block

    rendered = _career_context_block(
        {
            "primary_role": "Backend Engineer",
            "career_memory_context": {
                "active_gaps": [
                    {
                        "skill_id": "star_result",
                        "recommended_next_action": "A better version would be: \"I cut payment failures by 30%.\"",
                        "latest_evidence": "Great job — strong answer, you are ready and mastered this.",
                        "missing_criteria": ["result"],
                        "blockers": ["ready for the next level"],
                    }
                ],
                "repeated_issue_counts": {
                    "Great session — you hit all the right points.": 2
                },
                "recent_reports": [
                    {
                        "summary": (
                            "Strong interview close. You are ready and mastered it. "
                            "Try saying: \"I reduced duplicate charges by 30%.\""
                        )
                    }
                ],
            },
        }
    )
    lowered = rendered.lower()

    for forbidden in (
        "great job",
        "great session",
        "strong answer",
        "strong interview close",
        "you are ready",
        "mastered this",
        "mastered it",
        "ready for the next level",
        "a better version would be",
        "try saying",
        "i cut payment failures by 30%",
        "i reduced duplicate charges by 30%",
    ):
        assert forbidden not in lowered
    assert "learner's own facts" in lowered
    assert "keep re-testing" in lowered


def test_career_feedback_sanitizer_removes_better_version_model_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "In a payment outage, I traced retry failures, coordinated with support, "
                "and shipped an idempotency fix."
            ),
        }
    ]
    state["last_eval_score"] = 0.58
    raw = (
        "A better version would be: \"I owned the payment outage, reduced duplicate charges "
        "by 30%, and restored customer trust.\" Now rewrite it in that structure."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert "a better version would be" not in lowered
    assert "reduced duplicate charges by 30%" not in lowered
    assert "payment outage" in lowered
    assert "idempotency" in lowered


def test_prior_session_memory_block_sanitizes_overpraise_and_copyable_answers():
    from app.ai.prompts import _memory_block

    rendered = _memory_block([
        {
            "node_id": "int_04_star_behavioral",
            "score": 0.42,
            "strengths": "Great job — you hit all the right points in your payment answer.",
            "watch": "Missing result evidence from the payment outage.",
            "next_focus": (
                "A better version would be: \"I reduced duplicate charges by 30% "
                "and restored customer trust.\""
            ),
            "date": "2026-07-11",
        }
    ])
    lowered = rendered.lower()

    assert "great job" not in lowered
    assert "all the right points" not in lowered
    assert "a better version would be" not in lowered
    assert "reduced duplicate charges by 30%" not in lowered
    assert "missing result evidence from the payment outage" in lowered
    assert "prior session memory" in lowered


def test_career_feedback_sanitizer_preserves_concrete_example_revision_task():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": "I traced retry failures in a payment outage and shipped an idempotency fix.",
        }
    ]
    state["last_eval_score"] = 0.58
    raw = (
        "Let's tighten this. For example, add one concrete example from your payment outage "
        "that shows the result of the idempotency fix."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert "for example, add one concrete example" in lowered
    assert "payment outage" in lowered
    assert "idempotency fix" in lowered
    assert "keep it in your own words" not in lowered


def test_high_score_challenge_uses_measured_feedback_not_celebratory_praise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["last_eval_score"] = 0.9
    state["last_clean_pass_score"] = 0.9
    raw = (
        "Strong answer - the situation, action, and result are clear. "
        "Now pressure-test it by cutting the setup to one sentence."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "challenge")

    assert cleaned.startswith("That answer is on the right track.")
    assert "Strong answer" not in cleaned
    assert "pressure-test" in cleaned


def test_challenge_praise_sanitizer_preserves_same_sentence_task():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["last_eval_score"] = 0.9
    state["last_clean_pass_score"] = 0.9

    cleaned = svc._sanitize_coaching_response(
        "Strong answer: now pressure-test it by cutting the setup to one sentence.",
        state,
        "challenge",
    )

    assert cleaned.startswith("That answer is on the right track.")
    assert "Strong answer" not in cleaned
    assert "pressure-test it by cutting the setup to one sentence" in cleaned


def test_career_teach_prompt_requires_learner_anchored_feedback():
    from app.ai.prompts import build_teach_prompt
    from app.content.registry import get_node

    prompt = build_teach_prompt(
        get_node("gd_01_stake_position"),
        messages=[{"role": "user", "content": "I support remote work as default with security guardrails."}],
        diagnosis={"next_focus": "State the stance without softening it."},
        memory_context=[],
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )

    assert "anchor to the learner's actual answer" in prompt
    assert "Do not introduce a different domain" in prompt


def test_coach_block_uses_tutor_plan_for_independent_pass_not_revision_loop():
    from app.ai.prompts import _coach_block, coach_view

    coach = coach_view({
        "last_diagnosis": {"score": 0.78, "affect": "neutral"},
        "last_eval_score": 0.78,
        "last_clean_pass_score": 0.78,
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "tighten_one_gap",
            "tone_policy": "measured_no_celebration",
            "focus": "Practise delivering the three-part weakness answer concisely.",
            "stage": "practice",
        },
    })

    block = _coach_block(coach).lower()

    assert "latest enforced tutor plan" in block
    assert "required criteria are already covered" in block
    assert "ask the learner to revise" not in block
    assert "another same-skill rewrite" in block


def test_career_feedback_sanitizer_anchors_generic_unrelated_examples_to_learner_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "I improved our payment webhook flow by adding idempotency keys, "
                "retry dashboards, and reconciliation jobs."
            ),
        }
    ]
    state["last_eval_score"] = 0.52
    raw = (
        "Good job. For example, you could talk about improving technical documentation. "
        "Now add more evidence of progress."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "technical documentation" not in cleaned
    assert "payment webhook flow" in cleaned
    assert "add more evidence of progress" in cleaned.lower()


def test_deterministic_coach_repair_uses_measured_language_for_weak_answers():
    forbidden = ("usable", "your point is present", "great job", "all the right points")
    cases = [
        svc._new_state(
            "user-1",
            "session-int",
            "int_04_star_behavioral",
            [],
            task_type="interview_prep",
        ),
        svc._new_state(
            "user-1",
            "session-gd",
            "gd_01_stake_position",
            [],
            task_type="gd_prep",
            career_context={"gd_topics": ["Should remote work be the default?"]},
        ),
    ]
    for state in cases:
        state["last_eval_score"] = 0.32
        state["current_mastery"] = 0.24
        text = svc._deterministic_coach_repair_text(state).lower()
        for phrase in forbidden:
            assert phrase not in text


def test_career_feedback_sanitizer_removes_live_progress_overpraise_and_generic_example():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "The result was that the team found two retry edge cases early, "
                "avoided a full rollback, and explained the tradeoff in business terms."
            ),
        }
    ]
    state["last_eval_score"] = 0.73
    raw = (
        "You’ve done well in addressing your weakness. You’ve made good progress by outlining a specific scenario. However, include "
        "a concrete example of an outcome. This could be something like identifying "
        "a critical issue early in the phased rollout. For your next response, focus "
        "on adding a specific outcome."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You’ve done well" not in cleaned
    assert "You’ve made good progress" not in cleaned
    assert "This could be something like" not in cleaned
    assert "two retry edge cases" in cleaned
    assert "For your next response" in cleaned


def test_career_feedback_sanitizer_removes_unrelated_role_anchored_sample_domain():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "In a payment reliability project, I traced retry failures, fixed an idempotency bug, "
                "and reduced duplicate charge risk before rollout."
            ),
        }
    ]
    state["last_eval_score"] = 0.74
    raw = (
        "As a Backend Software Engineer, you could strengthen this with a customer churn dashboard "
        "example where sales and marketing teams improved retention. Now revise your story with that "
        "kind of business impact."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert "customer churn" not in lowered
    assert "sales" not in lowered
    assert "marketing" not in lowered
    assert "payment reliability" in lowered
    assert "idempotency" in lowered


def test_career_feedback_sanitizer_does_not_repeat_outcome_gap_when_answer_has_result():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "The phased rollout found two retry edge cases in the first week, "
                "avoided a full rollback, reduced support risk, and gave product "
                "confidence to expand safely."
            ),
        }
    ]
    state["last_eval_score"] = 0.69
    raw = (
        "You’ve effectively outlined your approach, but there’s still room for "
        "including a specific instance where this strategy led to tangible results. "
        "To meet our goal, focus on adding concrete evidence of how addressing your "
        "weakness improved project outcomes."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You’ve effectively outlined" not in cleaned
    assert "still room for including a specific instance" not in cleaned
    assert "focus on adding concrete evidence" not in cleaned
    assert "two retry edge cases" in cleaned
    assert "tighten" in cleaned.lower() or "make that outcome" in cleaned.lower()


def test_weakness_prep_sanitizer_does_not_repeat_initial_weakness_when_present():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "One weakness I am actively improving is that under pressure I sometimes "
                "explain the technical tradeoff before making the business impact clear. "
                "I manage it by opening with the decision criteria first."
            ),
        },
        {
            "role": "user",
            "content": (
                "In a phased payment rollout, we found two retry edge cases in week one, "
                "avoided a full rollback, reduced support risk, and gave product confidence "
                "to expand safely."
            ),
        },
    ]
    state["last_eval_score"] = 0.76
    raw = (
        "You’ve done well in addressing your weakness and demonstrating progress through "
        "a specific example of a phased payment rollout. However, ensure you explicitly "
        "state the initial weakness before detailing how you addressed it and the outcomes "
        "that followed. Your next step is to start by naming your original tendency to jump "
        "into technical details without considering business impacts, then clearly outline "
        "the steps you’ve taken to improve this, including identifying a specific instance "
        "where early detection of issues led to better project management and stakeholder "
        "communication. How will you revise your answer to include these elements?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You’ve done well" not in cleaned
    assert "initial weakness" not in cleaned
    assert "original tendency" not in cleaned
    assert "How will you revise" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_catches_repeated_contrast_loop():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier in my work, I sometimes led with technical implementation before "
                "making the business impact clear. I have changed that by starting with "
                "the decision criteria, then naming the tradeoff, then proving the result. "
                "In a payment rollout, this meant choosing a phased migration, catching "
                "two retry edge cases in week one, avoiding a full rollback, and giving "
                "product a clear revenue-protection reason for expanding gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.76
    raw = (
        "Your approach is clear and shows a solid understanding of how to address your "
        "weakness by demonstrating progress through specific actions and outcomes. "
        "However, ensure you explicitly contrast your initial tendency with the improved "
        "method in a more direct way at the beginning. This will strengthen the narrative "
        "arc of your answer. For your next response, reframe the opening statement to "
        "directly name your original behavior and then clearly outline how it has evolved. "
        "Focus on making this transition clear and impactful. How would you revise the "
        "opening to highlight this contrast?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "solid understanding" not in cleaned
    assert "explicitly contrast" not in cleaned
    assert "directly name your original behavior" not in cleaned
    assert "How would you revise" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_catches_repeated_original_behavior_loop():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I led with technical implementation before business impact in "
                "tradeoff discussions. I changed that by starting with decision criteria, "
                "explaining the tradeoff in plain language, and then proving the result. "
                "In a payment rollout, that approach helped the team catch two retry edge "
                "cases in week one, avoid a full rollback, and give product a clear "
                "revenue-protection reason for expanding gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.76
    raw = (
        "Ryuk, you’ve got a strong handle on framing your weakness and showing how "
        "you’ve evolved, but let’s refine it further for an interview setting. Ensure "
        "each component of your answer—weakness, mitigation habit, and progress evidence—"
        "is crisp and distinct. Your next step is to revise the opening to name your "
        "original behavior more directly before moving into how you’ve improved. Focus "
        "on making that transition as clear and impactful as possible. Revisit your "
        "opening statement to make it sharper and more direct."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "strong handle" not in cleaned
    assert "original behavior" not in cleaned
    assert "opening statement" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_uses_rubric_pass_to_stop_same_gap_loop():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "I used to over-explain technical trade-offs before giving the business recommendation. "
                "Now I lead with the recommendation, then give only the technical detail needed for the decision. "
                "Recently that helped a product review finish in one meeting instead of three email threads."
            ),
        },
    ]
    state["last_eval_score"] = 0.78
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "This is clearer, but revisit your opening statement to make it sharper and more direct. "
        "Name your original behavior more directly before moving into how you improved. "
        "How would you revise the opening to highlight this contrast?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "opening statement" not in cleaned
    assert "original behavior" not in cleaned
    assert "How would you revise" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_moves_forward_after_complete_live_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I tended to explain technical implementation before business impact. "
                "I now start with the decision criteria, explain the tradeoff in plain language, "
                "and prove the outcome. In a payment rollout, that meant catching two retry edge "
                "cases early, avoiding a full rollback, and giving product a clear "
                "revenue-protection reason to expand gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.79
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        'In your answer, you said "Earlier, I tended to explain technical implementation before business impact. '
        "I now start with the decision criteria, explain the...\". Ryuk, your answer clearly outlines your past "
        "tendency and how you've improved, but there's still room for tightening up each segment to ensure a "
        "smooth flow. Focus on making sure that when you transition from stating your weakness to describing "
        "the mitigation habit, and then to providing evidence of progress, there are no overlaps or redundancies. "
        "Your next task is to deliver this three-part answer in under 45 seconds with clear transitions between "
        "points--no setup, just the core message."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "still room" not in cleaned
    assert "tightening up each segment" not in cleaned
    assert "smooth flow" not in cleaned
    assert "overlaps or redundancies" not in cleaned
    assert "deliver this three-part answer" not in cleaned
    assert "under 45 seconds" not in cleaned
    assert "pressure-test" in cleaned


def test_weakness_prep_sanitizer_rejects_old_three_part_delivery_focus():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I tended to explain technical implementation before business impact. "
                "I now start with the decision criteria, explain the tradeoff in plain language, "
                "and prove the outcome. In a payment rollout, that meant catching two retry edge "
                "cases early, avoiding a full rollback, and giving product a clear "
                "revenue-protection reason to expand gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.8
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "You have the weakness, mitigation habit, and result. "
        "Practise delivering the three-part weakness answer concisely."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "three-part weakness answer" not in cleaned.lower()
    assert "practise delivering" not in cleaned.lower()
    assert "under 45 seconds" not in cleaned
    assert "pressure-test" in cleaned


def test_weakness_prep_sanitizer_does_not_reset_after_pressure_followup_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I tended to explain technical implementation before business impact. "
                "I now start with the decision criteria, explain the tradeoff in plain language, "
                "and prove the outcome. In a payment rollout, that meant catching two retry edge "
                "cases early, avoiding a full rollback, and giving product a clear "
                "revenue-protection reason to expand gradually."
            ),
        },
        {
            "role": "user",
            "content": (
                "If a stakeholder pushed back on the slower rollout, I would say the phased "
                "approach protected revenue while we validated failure rate, latency, "
                "reconciliation mismatches, and support-ticket trends before expanding."
            ),
        },
    ]
    state["last_eval_score"] = 0.58
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "required_missing": ["real_weakness"],
        "blockers": ["missing_required:real_weakness"],
        "criteria": [
            {"id": "real_weakness", "met": False},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "Ryuk, you provided a strong defense of your decision-making process during "
        "the payment rollout. However, let's revisit the original task: name a real "
        "weakness of yours and pair it with specific steps you've taken to manage it. "
        "Try that out now."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "revisit the original task" not in cleaned.lower()
    assert "name a real weakness" not in cleaned.lower()
    assert "try that out now" not in cleaned.lower()
    assert "pressure-test" in cleaned


def test_weakness_history_sanitizer_does_not_mask_missing_real_weakness():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "In payment work, business impact and technical details both matter. "
                "I used a phased rollout, tracked latency, found a retry issue, and "
                "avoided a rollback."
            ),
        },
    ]
    state["last_eval_score"] = 0.58
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "required_missing": ["real_weakness"],
        "blockers": ["missing_required:real_weakness"],
        "criteria": [
            {"id": "real_weakness", "met": False},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "Let's revisit the original task: name a real weakness of yours and pair it "
        "with specific steps you've taken to manage it. Try that out now."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "name a real weakness" in cleaned.lower()
    assert "try that out now" in cleaned.lower()
    assert "pressure-test" not in cleaned


def test_weakness_prep_sanitizer_respects_rubric_missing_core_criterion():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "My weakness is jumping straight into technical details before business impact. "
                "I manage it with decision criteria first and a habit of comparing options. "
                "The result should be better outcomes, but I have not named a real case yet."
            ),
        },
    ]
    state["last_eval_score"] = 0.61
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "required_missing": ["progress_evidence"],
        "blockers": ["missing_required:progress_evidence"],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": False},
        ],
    }
    raw = (
        "However, ensure you explicitly state the initial weakness and include the concrete progress evidence. "
        "How will you revise your answer to include these elements?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "initial weakness" in cleaned
    assert "concrete progress evidence" in cleaned
    assert "three-part shape" not in cleaned


def test_completed_but_not_mastered_progress_does_not_display_done_or_100(store):
    _run(store.ensure_profile("user-1"))
    _run(
        store.upsert_mastery(
            "user-1",
            "gd_02_support_with_evidence",
            0.43,
            5,
            clean_pass=True,
            node_completed=True,
            node_mastered=False,
            display_status="ready_to_advance",
            independent_passes=2,
            last_gap="Needs one concrete evidence-backed transfer answer.",
        )
    )

    rows = _run(svc.get_progression_map("user-1", "group_discussion"))
    node = next(row for row in rows if row["node_id"] == "gd_02_support_with_evidence")

    assert node["completed"] is True
    assert node["mastered"] is False
    assert node["status"] == "ready_to_advance"
    assert node["display_status"] == "ready_to_advance"
    assert node["display_mastery"] == 0.43
    assert node["last_gap"] == "Needs one concrete evidence-backed transfer answer."


def test_legacy_school_completed_rows_still_render_mastered(store):
    _run(store.ensure_profile("user-1"))
    _run(
        store.upsert_mastery(
            "user-1",
            "comm_00_greetings",
            0.0,
            2,
            clean_pass=False,
            node_completed=True,
            node_mastered=False,
            display_status="active",
        )
    )

    rows = _run(svc.get_progression_map("user-1", "communication"))
    node = next(row for row in rows if row["node_id"] == "comm_00_greetings")

    assert node["completed"] is True
    assert node["mastered"] is True
    assert node["status"] == "mastered"
    assert node["display_mastery"] == 1.0


def test_legacy_career_completed_rows_render_ready_not_mastered(store):
    _run(store.ensure_profile("user-1"))
    _run(
        store.upsert_mastery(
            "user-1",
            "int_01_elevator_pitch",
            0.0,
            2,
            clean_pass=False,
            node_completed=True,
            node_mastered=False,
            display_status="active",
        )
    )

    rows = _run(svc.get_progression_map("user-1", "interview"))
    node = next(row for row in rows if row["node_id"] == "int_01_elevator_pitch")

    assert node["completed"] is True
    assert node["mastered"] is False
    assert node["status"] == "ready_to_advance"
    assert node["display_mastery"] == 0.0


def test_two_good_independent_attempts_cannot_mark_ready_or_mastered():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because a pilot can compare interview time and shortlist accuracy before full rollout."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.88,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.85, evidence_quote="I support AI"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.85, evidence_quote="a pilot can compare interview time and shortlist accuracy"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="AI in campus placements"),
            ],
            strengths=["clear stance with concrete evidence"],
            errors=[],
            next_focus="Prove this under pressure.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )

    progress = {}
    for _ in range(2):
        progress = compute_attempt_credit(progress, result)

    assert progress["independent_passes"] == 2
    assert progress["meaningful_attempts"] == 2
    assert progress["display_status"] == "in_progress"
    assert progress["node_mastered"] is False


def test_five_independent_attempts_are_not_ready_without_transfer_or_pressure():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because a pilot can compare interview time and shortlist accuracy before full rollout."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.88,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.85, evidence_quote="I support AI"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.85, evidence_quote="a pilot can compare interview time and shortlist accuracy"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="AI in campus placements"),
            ],
            strengths=["clear stance with concrete evidence"],
            errors=[],
            next_focus="Try a transfer example.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )

    progress = {}
    for _ in range(5):
        progress = compute_attempt_credit(progress, result)

    assert progress["display_status"] == "in_progress"
    assert progress["node_mastered"] is False


def test_track_turn_records_enforced_rubric_ledger(store):
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I think AI is useful because it helps."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.72,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.7, evidence_quote="AI is useful"),
                CriterionEval(id="concrete_evidence", met=False, quality=0.1),
                CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="AI"),
            ],
            required_missing=["concrete_evidence"],
            strengths=["clear stance"],
            errors=["missing evidence"],
            next_focus="Add one concrete example.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=False,
        ),
    )
    plan = build_tutor_turn_plan(result, state)
    state.update(
        {
            "user_input": answer,
            "last_diagnosis": {
                "on_task": True,
                "english": True,
                "affect": "neutral",
                "next_focus": result.next_focus,
            },
            "last_eval_score": result.effective_score,
            "last_rubric_result": result.model_dump(),
            "tutor_turn_plan": plan.model_dump(),
            "active_turn_id": "turn-1",
            "attempts": 3,
        }
    )

    _run(svc._track_turn(state, "gd_02_support_with_evidence"))

    assert len(store.turn_evaluations) == 1
    row = store.turn_evaluations[0]
    assert row["evaluation_id"] == "session-1:turn-1:gd_02_support_with_evidence"
    assert row["effective_score"] <= 0.62
    assert row["pass_eligible"] is False
    assert row["blockers"] == ["missing_required:concrete_evidence"]


def test_prep_bridge_fill_records_scaffold_credit_and_not_independent_pass(store):
    from app.graph.nodes import evaluate as eval_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    state["pending_answer_key"] = {"type": "fill_blank", "answer_key": "for example"}
    state["user_input"] = "for example"
    state["active_turn_id"] = "turn-bridge"

    updates = _run(eval_node.evaluate_node(state))
    state.update(updates)
    svc._update_progress(state)
    _run(svc._track_turn(state, "gd_02_support_with_evidence"))

    assert state["scaffold_successes"] == 1
    assert state["independent_passes"] == 0
    assert state["node_mastered"] is False
    assert state["clean_streak"] == 0
    assert state["last_rubric_result"]["attempt_type"] == "scaffolded"
    assert len(store.turn_evaluations) == 1
    assert store.turn_evaluations[0]["attempt_type"] == "scaffolded"


def test_closed_bridge_correct_answer_uses_fast_deterministic_feedback(monkeypatch, store):
    from app.ai.calls import GenSpec

    class FakeGraph:
        async def ainvoke(self, state):
            return {
                "last_eval_score": 0.7,
                "last_clean_pass_score": 0.7,
                "last_diagnosis": {
                    "score": 0.7,
                    "understanding": "Got the scaffolded step right.",
                    "errors": [],
                    "strengths": ["produced the target form correctly"],
                    "next_focus": "build back up to the full skill",
                    "on_task": True,
                    "english": True,
                    "affect": "confident",
                    "goodbye": False,
                },
                "last_rubric_result": {
                    "raw_score": 0.7,
                    "effective_score": 0.7,
                    "criteria": [
                        {
                            "id": "scaffolded_step",
                            "met": True,
                            "quality": 0.7,
                            "evidence_quote": "remote work",
                        }
                    ],
                    "strengths": ["produced the target form correctly"],
                    "errors": [],
                    "next_focus": "build back up to the full skill",
                    "attempt_type": "scaffolded",
                    "pass_eligible": False,
                    "mastery_eligible": False,
                    "blockers": [],
                    "required_missing": [],
                    "understanding": "Got the scaffolded step right.",
                    "on_task": True,
                    "english": True,
                    "affect": "confident",
                    "goodbye": False,
                },
                "last_graded_bridge": True,
                "pending_answer_key": None,
                "pending_game": None,
                "pending": GenSpec(provider="groq", model="fake", prompt="would be slow", kind="teach"),
            }

    async def forbidden_stream(*_args, **_kwargs):
        raise AssertionError("closed bridge feedback must not call the model")
        yield ""  # pragma: no cover

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "_stream_coaching_generation", forbidden_stream)
    state = svc._new_state(
        "user-1",
        "session-bridge-fast",
        "gd_01_stake_position",
        [{"role": "assistant", "content": "Pick the clearest stance."}],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["turn_count"] = 1
    state["opening_streamed"] = True
    state["pending_answer_key"] = {
        "type": "multiple_choice",
        "answer_key": "I believe remote work should be the default.",
        "options": [
            "I believe remote work should be the default.",
            "Maybe remote work is good and bad.",
        ],
    }
    svc.SessionStore["session-bridge-fast"] = state

    items = _run(
        _collect_async(
            svc.run_turn(
                "session-bridge-fast",
                "I believe remote work should be the default.",
                client_turn_id="turn-bridge-fast",
            )
        )
    )

    text = "".join(str(item) for item in items)
    assert "scaffolded step is in place - not the whole skill yet" in text
    assert "remote work being the default" in text
    assert "Great job" not in text
    assert svc.SessionStore["session-bridge-fast"]["pending"] is None
    assert svc.SessionStore["session-bridge-fast"]["last_turn_status"] == "completed"


def test_open_bridge_prompt_marker_classifies_next_answer_as_scaffolded():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Remote work policy"]},
    )
    state["active_prompt_attempt_type"] = "scaffolded"
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "Remote work helps because it saves commute time.",
    )

    assert packet.attempt_type == "scaffolded"

    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.9, evidence_quote="Remote work helps"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.9, evidence_quote="saves commute time"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="Remote work"),
            ],
            strengths=["clear answer"],
            errors=[],
            next_focus="Try the same move without a scaffold.",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )
    progress = compute_attempt_credit({}, result)

    assert progress["scaffold_successes"] == 1
    assert progress["independent_passes"] == 0
    assert progress["node_mastered"] is False


def test_run_turn_preserves_spoken_bridge_marker_until_evaluation(monkeypatch):
    seen = {}

    class FakeGraph:
        async def ainvoke(self, state):
            seen["attempt_type"] = state.get("active_prompt_attempt_type")
            return {"pending": None, "pending_game": None}

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    state = svc._new_state(
        "user-1",
        "session-spoken-bridge",
        "int_04_star_behavioral",
        [{"role": "assistant", "content": "Tell a smaller STAR step."}],
        task_type="interview_prep",
    )
    state["active_prompt_attempt_type"] = "scaffolded"
    state["active_game_prompt"] = None
    state["pending_answer_key"] = None
    state["opening_streamed"] = True
    state["turn_count"] = 0
    svc.SessionStore["session-spoken-bridge"] = state

    _run(_collect_async(svc.run_turn("session-spoken-bridge", "I mapped the outage and reduced triage time.")))

    assert seen["attempt_type"] == "scaffolded"


def test_stale_last_graded_bridge_does_not_classify_next_open_answer_as_scaffolded():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Remote work policy"]},
    )
    state["last_graded_bridge"] = True
    state["active_prompt_attempt_type"] = None
    state["pending_answer_key"] = None
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "Remote work helps because it saves commute time.",
    )

    assert packet.attempt_type == "independent"


def test_langgraph_preserves_prep_rubric_result_channel(monkeypatch):
    from app.graph import build as graph_build
    from app.graph.nodes import evaluate as eval_node

    async def fake_prep_eval(node, messages, user_input, **kwargs):
        packet = build_evaluation_packet(kwargs["state"], node, user_input)
        return apply_caps(
            packet,
                PrepRubricEval(
                    raw_score=0.9,
                    criteria=[
                            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
                            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
                            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer using FastAPI payment APIs"),
                        ],
                strengths=["specific backend detail"],
                errors=[],
                next_focus="Try a pressure version.",
                pass_eligible=True,
                mastery_eligible=True,
            ),
        )

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", fake_prep_eval)
    graph_build.get_graph.cache_clear()
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [{"role": "assistant", "content": "opening"}],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["turn_count"] = 1
    state["user_input"] = (
        "I am a backend engineer using FastAPI payment APIs, and I want to own "
        "reliability for larger production services."
    )

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    assert updates["last_rubric_result"]["pass_eligible"] is True
    assert updates["tutor_turn_plan"]["verdict"] in {"independent_pass", "partial"}
    assert updates["last_diagnosis"]["score"] == updates["last_rubric_result"]["effective_score"]


def test_prep_eval_exception_fails_closed_with_rubric_result(monkeypatch):
    from app.graph import build as graph_build
    from app.graph.nodes import evaluate as eval_node

    async def broken_prep_eval(*_args, **_kwargs):
        raise RuntimeError("structured model unavailable")

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", broken_prep_eval)
    graph_build.get_graph.cache_clear()
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [{"role": "assistant", "content": "opening"}],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["turn_count"] = 1
    state["user_input"] = "I am a backend engineer using FastAPI."

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    rubric = updates["last_rubric_result"]
    assert rubric["pass_eligible"] is False
    assert rubric["mastery_eligible"] is False
    assert "structured_eval_unavailable" in rubric["blockers"]
    assert "answers_question" in rubric["required_missing"]
    assert updates["tutor_turn_plan"]["allowed_praise"] is False


def test_evaluation_packet_recent_messages_are_json_serializable():
    packet = build_evaluation_packet(
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": "opening",
                    "created_at": datetime.now(timezone.utc),
                    "message_kind": "opening",
                },
                {
                    "role": "user",
                    "content": "I build FastAPI systems.",
                    "created_at": datetime.now(timezone.utc),
                    "message_kind": "learner_answer",
                },
            ],
            "career_context": {"primary_role": "Backend Software Engineer"},
        },
        svc.get_node("int_01_elevator_pitch"),
        "I build FastAPI systems.",
    )

    dumped = packet.model_dump()
    assert "created_at" not in dumped["recent_messages"][0]
    assert dumped["recent_messages"][1]["message_kind"] == "learner_answer"
    json.dumps(dumped)


def test_interview_bridge_role_personalization_does_not_duplicate_backend_label():
    node = svc.get_node("int_01_elevator_pitch")
    exercise = next(item for item in node.bridge_exercises if item.id == "int_01_elevator_pitch_bx2")

    personalized = personalize_bridge_exercise(
        exercise,
        {
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
            "role_family": "software_technical",
        },
        "interview",
    )

    joined = " ".join([personalized.sentence, *(personalized.options or [])])
    assert "Backend Backend Software Engineer" not in joined
    assert "Backend Software Engineer" in joined


def test_career_prep_without_rubric_result_fails_closed_no_legacy_advance():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["last_diagnosis"] = {"english": True, "on_task": True}
    state["last_clean_pass_score"] = 0.95
    state["last_eval_score"] = 0.95
    state["last_rubric_result"] = None

    for _ in range(3):
        svc._update_progress(state)

    assert state["clean_streak"] == 0
    assert state["display_status"] == "active"
    assert state["node_mastered"] is False


def test_prep_minimum_gate_caps_rubric_result_for_weak_gd_answer(monkeypatch):
    from app.graph.nodes import evaluate as eval_node

    async def overly_generous_eval(*_args, **_kwargs):
        return apply_caps(
            build_evaluation_packet(
                _args[-1] if _args and isinstance(_args[-1], dict) else {},
                svc.get_node("gd_02_support_with_evidence"),
                "I support this. It is good.",
            ),
            PrepRubricEval(
                raw_score=0.9,
                criteria=[
                    CriterionEval(id="clear_stance", met=True, quality=0.8, evidence_quote="I support this"),
                    CriterionEval(id="concrete_evidence", met=True, quality=0.8, evidence_quote="It is good"),
                    CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="this"),
                ],
                strengths=["clear stance"],
                errors=[],
                next_focus="Try a stronger example.",
                on_task=True,
                english=True,
                pass_eligible=True,
                mastery_eligible=True,
            ),
        )

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", overly_generous_eval)
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    state["user_input"] = "I support this. It is good."

    updates = _run(eval_node.evaluate_node(state))

    assert updates["last_eval_score"] == 0.6
    assert updates["last_rubric_result"]["effective_score"] == 0.6
    assert updates["last_rubric_result"]["pass_eligible"] is False
    assert "minimum_gate_cap" in updates["last_rubric_result"]["blockers"]


def test_gd_bridge_rendering_uses_active_topic_without_stock_topic_residue():
    stock_terms = [
        "remote work",
        "bike lanes",
        "single-use plastics",
        "social media",
        "electric cars",
        "homework",
        "four-day work week",
        "minimum wage",
    ]
    context = {"gd_topics": ["AI in campus placements"]}
    for node_id in [
        "gd_01_stake_position",
        "gd_02_support_with_evidence",
        "gd_03_take_the_floor",
        "gd_04_build_on_others",
        "gd_05_disagree_respectfully",
        "gd_06_balanced_view",
        "gd_07_steer_back",
        "gd_08_include_quiet",
        "gd_09_manage_dominator",
        "gd_10_drive_consensus",
    ]:
        node = svc.get_node(node_id)
        rendered = [
            render_gd_bridge_exercise(exercise, node_id, context)
            for exercise in node.bridge_exercises
        ]
        parts = []
        for item in rendered:
            parts.extend([item.sentence, item.context, item.answer_key, " ".join(item.options or [])])
        combined = " ".join(parts).lower()

        assert "ai in campus placements" in combined
        for term in stock_terms:
            assert term not in combined


def test_gd_bridge_rendering_uses_generic_context_for_non_campus_topics():
    context = {"gd_topics": ["Should remote work be the default?"]}
    node = svc.get_node("gd_02_support_with_evidence")
    rendered = [
        render_gd_bridge_exercise(exercise, "gd_02_support_with_evidence", context)
        for exercise in node.bridge_exercises
    ]
    parts = []
    for item in rendered:
        parts.extend([item.sentence, item.context, item.answer_key, " ".join(item.options or [])])
    combined = " ".join(parts).lower()

    assert "remote work being the default" in combined
    for residue in ["college", "campus", "placement", "student", "weaker students"]:
        assert residue not in combined


def test_gd_topic_phrase_handles_auxiliary_should_motions():
    from app.graph.nodes.bridge import _gd_topic_phrase as bridge_topic_phrase
    from app.services.session_service import _gd_topic_phrase_for_state

    context = {"gd_topics": ["Should remote work be the default?"]}
    node = svc.get_node("gd_02_support_with_evidence")
    rendered = [
        render_gd_bridge_exercise(exercise, "gd_02_support_with_evidence", context)
        for exercise in node.bridge_exercises
    ]
    parts = []
    for item in rendered:
        parts.extend([item.sentence, item.answer_key, " ".join(item.options or [])])
    combined = " ".join(parts).lower()

    assert "remote work being the default" in combined

    context = {"gd_topics": ["Should companies be allowed to use AI in hiring?"]}
    rendered = [
        render_gd_bridge_exercise(exercise, "gd_02_support_with_evidence", context)
        for exercise in node.bridge_exercises
    ]
    parts = []
    for item in rendered:
        parts.extend([item.sentence, item.answer_key, " ".join(item.options or [])])
    combined = " ".join(parts).lower()

    assert "companies being allowed to use ai in hiring" in combined
    assert bridge_topic_phrase("Should remote work be the default?") == "remote work being the default"
    assert bridge_topic_phrase("Should companies be allowed to use AI in hiring?") == "companies being allowed to use AI in hiring"
    assert _gd_topic_phrase_for_state({"competency_node": "gd_02_support_with_evidence", "career_context": context}) == "companies being allowed to use AI in hiring"


def test_browser_qa_prep_nodes_have_five_supportive_bridge_exercises():
    required_nodes = [
        "int_01_elevator_pitch",
        "int_03_weakness_framing",
        "int_04_star_behavioral",
        "gd_01_stake_position",
        "gd_05_disagree_respectfully",
        "gd_08_include_quiet",
        "gd_09_manage_dominator",
    ]

    for node_id in required_nodes:
        node = svc.get_node(node_id)
        assert len(node.bridge_exercises) >= 5, node_id
        bands = {exercise.band for exercise in node.bridge_exercises}
        assert {"foundational", "standard", "stretch"}.issubset(bands), node_id
        assert any(exercise.type == "spoken" for exercise in node.bridge_exercises), node_id


def test_career_spoken_bridge_answer_keys_are_guidance_not_copyable_answers():
    from app.content.registry import MODULES

    copyable_answer = re.compile(
        r"(^|\s)(i'm|i am|i'd|i would|i've|i have|i used|i support|i believe|"
        r"one of my|my task|our biggest|we launched|we agreed|you('| are| have))\b",
        re.IGNORECASE,
    )
    offenders = []

    for module in MODULES:
        if module.id not in {"interview", "group_discussion"}:
            continue
        for node in module.nodes:
            for exercise in node.bridge_exercises:
                if exercise.type != "spoken":
                    continue
                key = exercise.answer_key.strip()
                if not key.startswith("Expected elements:") or copyable_answer.search(key):
                    offenders.append(f"{module.id}/{node.id}/{exercise.id}: {key}")

    assert offenders == []


def test_rendered_gd_spoken_bridge_keeps_guidance_answer_key():
    context = {"gd_topics": ["Should companies use AI in hiring?"]}
    copyable_answer = re.compile(
        r"(^|\s)(i'm|i am|i'd|i would|i've|i have|i support|i believe|"
        r"you're|you are|we agreed|to sum up)\b",
        re.IGNORECASE,
    )
    offenders = []

    for node_id in [
        "gd_01_stake_position",
        "gd_02_support_with_evidence",
        "gd_03_take_the_floor",
        "gd_04_build_on_others",
        "gd_05_disagree_respectfully",
        "gd_06_balanced_view",
        "gd_07_steer_back",
        "gd_08_include_quiet",
        "gd_09_manage_dominator",
        "gd_10_drive_consensus",
    ]:
        node = svc.get_node(node_id)
        for exercise in node.bridge_exercises:
            if exercise.type != "spoken":
                continue
            rendered = render_gd_bridge_exercise(exercise, node_id, context)
            key = rendered.answer_key.strip()
            if not key.startswith("Expected elements:") or copyable_answer.search(key):
                offenders.append(f"{node_id}/{exercise.id}: {key}")
            assert "AI in hiring" in rendered.sentence or "companies using AI in hiring" in rendered.sentence

    assert offenders == []
