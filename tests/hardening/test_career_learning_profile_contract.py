import asyncio

from app.ai.schemas import CriterionEval, PrepRubricEval, SimulationReport
from app.content.registry import get_module
from app.services import session_service as svc
from app.services.rubric_engine import apply_caps, build_evaluation_packet, compute_attempt_credit
from app.services.rubrics import get_rubric


def _run(coro):
    return asyncio.run(coro)


def _career_prep_node_ids() -> list[str]:
    return [
        node.id
        for module_id in ("interview", "group_discussion")
        for node in get_module(module_id).nodes
        if node.level_type != "voice"
    ]


def test_every_career_prep_node_has_node_specific_rubric():
    missing = []
    for node_id in _career_prep_node_ids():
        rubric = get_rubric(node_id)
        if rubric.node_id != node_id:
            missing.append((node_id, rubric.node_id))

    assert missing == []


def test_readiness_requires_eighty_percent_not_just_attempt_count():
    weak_result = {
        "pass_eligible": True,
        "mastery_eligible": False,
        "effective_score": 0.63,
        "next_focus": "Add specific evidence.",
        "attempt_type": "independent",
    }

    progress = {}
    for _ in range(5):
        progress = compute_attempt_credit(progress, weak_result)

    assert progress["meaningful_attempts"] == 5
    assert progress["independent_passes"] == 5
    assert progress["display_status"] == "in_progress"
    assert progress["node_mastered"] is False


def test_eighty_percent_readiness_creates_advance_state_without_mastery():
    ready_result = {
        "pass_eligible": True,
        "mastery_eligible": False,
        "effective_score": 0.82,
        "next_focus": "Try the same skill under pressure.",
        "attempt_type": "transfer",
    }

    progress = {}
    for _ in range(5):
        progress = compute_attempt_credit(progress, ready_result, transfer=True)

    assert progress["display_status"] == "ready_to_advance"
    assert progress["readiness_score"] >= 0.8
    assert progress["node_mastered"] is False


def test_prep_turn_evaluation_updates_global_learning_profile(store):
    from app.services.learning_profile import CareerLearningProfileService

    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because a pilot can compare shortlist accuracy before rollout."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.84,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.82, evidence_quote="I support AI"),
                CriterionEval(
                    id="concrete_evidence",
                    met=True,
                    quality=0.84,
                    evidence_quote="a pilot can compare shortlist accuracy",
                ),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="AI in campus placements"),
            ],
            strengths=["clear stance with concrete evidence"],
            errors=[],
            next_focus="Pressure-test this with a counterargument.",
            on_task=True,
            english=True,
            pass_eligible=True,
            mastery_eligible=False,
        ),
    )

    _run(
        CareerLearningProfileService(store).record_prep_turn_evaluation(
            evaluation_id="eval-1",
            state=state,
            rubric_result=result.model_dump(),
            tutor_plan={"next_action": "pressure"},
            user_answer=answer,
            attempt_index=3,
        )
    )

    assert len(store.learning_events) == 1
    event = store.learning_events[0]
    assert event["source_event_key"] == "turn_evaluation:eval-1"
    assert event["task_type"] == "gd_prep"
    assert event["skill_id"] == "gd_02_support_with_evidence"
    assert event["evidence_json"]["criteria"][1]["evidence_quote"] == "a pilot can compare shortlist accuracy"

    profile = store.learner_skill_profiles[("user-1", "career", "gd_02_support_with_evidence")]
    assert profile["readiness"] == result.effective_score
    assert profile["recommended_next_action"] == "Pressure-test this with a counterargument."


def test_prep_turn_evaluation_feeds_exact_missing_criteria_and_quote_to_memory(store):
    from app.ai.prompts import _career_context_block
    from app.services.learning_profile import CareerLearningProfileService

    state = svc._new_state(
        "user-1",
        "session-criteria-memory",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
        career_context={"primary_role": "Backend Engineer"},
    )
    answer = "In a payment outage, I traced retries and shipped an idempotency fix."
    rubric_result = {
        "raw_score": 0.52,
        "effective_score": 0.52,
        "criteria": [
            {"id": "situation", "met": True, "quality": 0.7, "evidence_quote": "payment outage"},
            {"id": "action", "met": True, "quality": 0.7, "evidence_quote": "traced retries"},
            {"id": "result", "met": False, "quality": 0.1, "reason": "No business or user impact."},
        ],
        "required_missing": ["result"],
        "blockers": ["missing_required:result"],
        "strengths": ["specific situation and action"],
        "errors": ["missing required rubric proof: result"],
        "next_focus": "Add the result or measurable impact.",
        "pass_eligible": False,
        "mastery_eligible": False,
        "attempt_type": "independent",
    }

    _run(
        CareerLearningProfileService(store).record_prep_turn_evaluation(
            evaluation_id="eval-criteria-memory",
            state=state,
            rubric_result=rubric_result,
            tutor_plan={"next_action": "rewrite", "focus": "result"},
            user_answer=answer,
            attempt_index=2,
        )
    )

    context = _run(CareerLearningProfileService(store).get_career_memory_context("user-1"))
    active = context["active_gaps"][0]

    assert active["skill_id"] == "int_04_star_behavioral"
    assert active["missing_criteria"] == ["result"]
    assert active["blockers"] == ["missing_required:result"]
    assert "payment outage" in active["latest_evidence"]

    prompt_block = _career_context_block({
        "primary_role": "Backend Engineer",
        "career_memory_context": context,
    })

    assert "missing: result" in prompt_block
    assert "blockers: missing_required:result" in prompt_block
    assert "payment outage" in prompt_block


def test_invalid_rubric_proof_does_not_persist_unsupported_strength(store):
    from app.services.learning_profile import CareerLearningProfileService

    state = svc._new_state(
        "user-1",
        "session-invalid-proof",
        "int_06_own_a_failure",
        [],
        task_type="interview_prep",
    )
    answer = "I made a migration mistake and learned to test more carefully."
    packet = build_evaluation_packet(state, svc.get_node("int_06_own_a_failure"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.86,
            criteria=[
                CriterionEval(id="ownership", met=True, quality=0.8, evidence_quote="I made a migration mistake"),
                CriterionEval(id="impact", met=True, quality=0.7, evidence_quote="migration mistake"),
                CriterionEval(id="response_action", met=True, quality=0.8, evidence_quote=""),
                CriterionEval(id="prevention", met=True, quality=0.8, evidence_quote="test more carefully"),
            ],
            strengths=["owns the mistake strongly"],
            errors=[],
            next_focus="Add the immediate response action.",
            on_task=True,
            english=True,
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )

    _run(
        CareerLearningProfileService(store).record_prep_turn_evaluation(
            evaluation_id="eval-invalid-proof",
            state=state,
            rubric_result=result.model_dump(),
            tutor_plan={"next_action": "revise"},
            user_answer=answer,
            attempt_index=1,
        )
    )

    profile = store.learner_skill_profiles[("user-1", "career", "int_06_own_a_failure")]
    assert profile["strengths_json"] == []
    assert profile["recommended_next_action"] == "Add the immediate response action."
    assert profile["source_summary"] == "Add the immediate response action."


def test_simulation_report_updates_global_learning_profile_before_next_session(store):
    from app.services.learning_profile import CareerLearningProfileService

    report = SimulationReport(
        score=0.71,
        summary="The learner answered clearly but missed evidence under pressure.",
        strengths=["Clear backend examples"],
        improvements=["Add evidence under pressure", "Avoid repeating the same design-pattern answer"],
        clarity_score=0.75,
        confidence_score=0.68,
        role_focus="Backend Software Engineer",
        observed_skill_gaps=["evidence_under_pressure"],
        recommended_next_nodes=["gd_02_support_with_evidence"],
        assessment_caveats=["Only six scorable turns."],
        evidence_quotes=["I reduced checkout failures by adding retry dashboards."],
    )

    _run(
        CareerLearningProfileService(store).record_session_report(
            user_id="user-1",
            session_id="sim-1",
            report_type="interview_test",
            task_type="interview_test",
            module_id="interview",
            report=report.model_dump(),
        )
    )

    assert store.session_reports[("user-1", "sim-1")]["status"] == "partial"
    assert store.session_reports[("user-1", "sim-1")]["evidence_json"]["evidence_quotes"] == [
        "I reduced checkout failures by adding retry dashboards."
    ]
    assert len(store.learning_events) == 1
    assert store.learning_events[0]["source"] == "test_report"
    assert store.learning_events[0]["gap"] == "evidence_under_pressure"
    assert store.learning_events[0]["evidence_json"]["strengths"] == []
    profile = store.learner_skill_profiles[("user-1", "career", "evidence_under_pressure")]
    assert profile["recommended_next_action"] == "Add evidence under pressure"
    assert profile["strengths_json"] == []


def test_simulation_report_validity_status_is_preserved_in_learning_profile(store):
    from app.services.learning_profile import CareerLearningProfileService

    report = SimulationReport(
        score=0.0,
        summary="Not enough scorable evidence.",
        strengths=[],
        improvements=["Complete more rounds."],
        observed_skill_gaps=["insufficient_assessment_evidence"],
        assessment_caveats=["Only one answered turn."],
        validity_status="insufficient_evidence",
        scorable_turn_count=1,
        coverage_map={"unique_covered": 1, "required_unique": 4},
    )

    _run(
        CareerLearningProfileService(store).record_session_report(
            user_id="user-1",
            session_id="sim-2",
            report_type="interview_test",
            task_type="interview_test",
            module_id="interview",
            report=report.model_dump(),
        )
    )

    stored = store.session_reports[("user-1", "sim-2")]
    assert stored["status"] == "insufficient_evidence"
    assert stored["validity_json"]["status"] == "insufficient_evidence"
    assert stored["validity_json"]["scorable_turn_count"] == 1
    assert stored["validity_json"]["coverage_map"]["required_unique"] == 4
    profile = store.learner_skill_profiles[("user-1", "career", "insufficient_assessment_evidence")]
    assert profile["evidence_json"]["validity_status"] == "insufficient_evidence"
    assert profile["evidence_json"]["coverage_map"]["unique_covered"] == 1
    assert profile["evidence_json"]["scorable_turn_count"] == 1


def test_split_report_caveats_prevent_strength_promotion_to_memory(store):
    from app.services.learning_profile import CareerLearningProfileService

    report = SimulationReport(
        score=0.72,
        summary="The learner had useful examples, but the simulator repaired panel turns.",
        strengths=["Clear remote-work metrics"],
        improvements=["Add stakeholder tradeoff evidence"],
        observed_skill_gaps=["stakeholder_tradeoff_evidence"],
        learner_assessment_caveats=["Coverage was narrow."],
        simulator_integrity_notes=["A panelist response was repaired."],
        evidence_quotes=["I would track mentoring quality and decision latency."],
    )

    _run(
        CareerLearningProfileService(store).record_session_report(
            user_id="user-1",
            session_id="sim-split-caveats",
            report_type="gd_test",
            task_type="gd_test",
            module_id="group_discussion",
            report=report.model_dump(),
        )
    )

    stored = store.session_reports[("user-1", "sim-split-caveats")]
    assert stored["status"] == "partial"
    assert store.learning_events[0]["evidence_json"]["strengths"] == []
    profile = store.learner_skill_profiles[("user-1", "career", "stakeholder_tradeoff_evidence")]
    assert profile["strengths_json"] == []
    assert profile["evidence_json"]["validity_status"] == "partial"


def test_career_memory_context_groups_active_improving_and_repeated_gaps(store):
    from app.services.learning_profile import CareerLearningProfileService

    _run(store.upsert_learner_skill_profile(
        user_id="user-1",
        domain="career",
        skill_id="evidence_under_pressure",
        module_id="interview",
        task_type="interview_test",
        readiness=0.42,
        mastery=0.0,
        confidence=0.7,
        attempts=3,
        strengths_json=[],
        gaps_json=["Add quantified impact under pressure"],
        evidence_json={"latest_quote": "I improved reliability but did not quantify impact."},
        recommended_next_action="Quantify the impact in the next answer.",
        source_summary="Repeatedly missed impact evidence.",
    ))
    _run(store.upsert_learner_skill_profile(
        user_id="user-1",
        domain="career",
        skill_id="clear_stance",
        module_id="group_discussion",
        task_type="gd_prep",
        readiness=0.78,
        mastery=0.0,
        confidence=0.8,
        attempts=5,
        strengths_json=["Clear stance"],
        gaps_json=["Add counter-risk"],
        evidence_json={"latest_quote": "Remote default with guardrails."},
        recommended_next_action="Add the strongest objection.",
        source_summary="Stance is improving.",
    ))
    for index in range(2):
        _run(store.record_learning_event(
            source_event_key=f"repeat-gap-{index}",
            user_id="user-1",
            domain="career",
            task_type="interview_test",
            module_id="interview",
            skill_id="evidence_under_pressure",
            source="test_report",
            score=0.4,
            confidence=0.7,
            evidence_json={"evidence_quotes": ["I improved reliability."]},
            gap="evidence_under_pressure",
            caveats=[],
        ))

    context = _run(CareerLearningProfileService(store).get_career_memory_context("user-1"))

    assert context["active_gaps"][0]["skill_id"] == "evidence_under_pressure"
    assert context["improving_gaps"][0]["skill_id"] == "clear_stance"
    assert context["repeated_issue_counts"]["evidence_under_pressure"] == 2
    assert "reliability" in context["active_gaps"][0]["latest_evidence"]


def test_high_readiness_without_mastery_stays_improving_not_resolved(store):
    from app.services.learning_profile import CareerLearningProfileService

    _run(store.upsert_learner_skill_profile(
        user_id="user-1",
        domain="career",
        skill_id="star_result_evidence",
        module_id="interview",
        task_type="interview_prep",
        readiness=0.91,
        mastery=0.0,
        confidence=0.9,
        attempts=4,
        strengths_json=["Clear situation and action"],
        gaps_json=["Still needs independent result evidence"],
        evidence_json={"latest_quote": "I fixed the outage but still did not quantify the result."},
        recommended_next_action="Add the measurable result without being prompted.",
        source_summary="High readiness, not yet mastered.",
    ))

    context = _run(CareerLearningProfileService(store).get_career_memory_context("user-1"))

    assert context["resolved_gaps"] == []
    assert context["mastered_skills"] == []
    assert context["improving_gaps"][0]["skill_id"] == "star_result_evidence"
    assert context["improving_gaps"][0]["status"] == "improving"


def test_new_career_prep_session_receives_career_memory_context(store):
    from app.services import session_service as svc

    _run(store.ensure_profile("user-1"))
    _run(store.upsert_learner_skill_profile(
        user_id="user-1",
        domain="career",
        skill_id="evidence_under_pressure",
        module_id="interview",
        task_type="interview_test",
        readiness=0.38,
        mastery=0.0,
        confidence=0.75,
        attempts=2,
        strengths_json=[],
        gaps_json=["Add quantified impact under pressure"],
        evidence_json={"latest_quote": "The answer named a project but missed measurable impact."},
        recommended_next_action="Add metric and result.",
        source_summary="Missing measurable result.",
    ))

    _session_id, state = _run(svc.start_session("user-1", "int_01_elevator_pitch"))

    memory = state["career_context"]["career_memory_context"]
    assert memory["active_gaps"][0]["skill_id"] == "evidence_under_pressure"
    assert state["session_learning_delta"]["active_gaps"] == []


def test_career_memory_context_uses_progression_rows_when_profile_row_missing(store):
    from app.services.learning_profile import CareerLearningProfileService

    _run(
        store.upsert_mastery(
            "user-1",
            "int_04_star_behavioral",
            0.51,
            attempts=4,
            node_completed=False,
            last_gap="Add a measurable result to the STAR answer.",
            mastery_evidence=["I handled the outage but did not show the result."],
        )
    )
    _run(
        store.upsert_mastery(
            "user-1",
            "gd_01_stake_position",
            0.96,
            attempts=9,
            node_completed=True,
            node_mastered=True,
            display_status="mastered",
            best_independent_score=0.91,
            independent_passes=4,
            transfer_passes=2,
            pressure_passes=2,
            last_gap="Keep stance direct under pressure.",
            mastery_evidence=["Remote should be default with explicit guardrails."],
        )
    )

    context = _run(CareerLearningProfileService(store).get_career_memory_context("user-1"))

    assert context["active_gaps"][0]["skill_id"] == "int_04_star_behavioral"
    assert context["active_gaps"][0]["module_id"] == "interview"
    assert context["active_gaps"][0]["latest_evidence"] == "I handled the outage but did not show the result."
    assert context["mastered_skills"][0]["skill_id"] == "gd_01_stake_position"
    assert context["mastered_skills"][0]["module_id"] == "group_discussion"
    assert context["mastered_skills"][0]["latest_evidence"] == "Remote should be default with explicit guardrails."


def test_prep_turn_updates_hot_session_learning_delta(store):
    from app.services import session_service as svc

    state = svc._new_state(
        "user-1",
        "session-hot-delta",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["user_input"] = "I built payment retries but did not measure the result."
    state["last_eval_score"] = 0.48
    state["last_diagnosis"] = {"on_task": True, "english": True, "affect": "neutral", "next_focus": "Add quantified impact."}
    state["last_rubric_result"] = {
        "raw_score": 0.48,
        "effective_score": 0.48,
        "strengths": ["specific project context"],
        "next_focus": "Add quantified impact.",
        "criteria": [{"id": "impact", "met": False, "evidence_quote": "did not measure the result"}],
        "blockers": ["missing_result"],
        "pass_eligible": False,
        "mastery_eligible": False,
        "attempt_type": "independent",
    }
    state["tutor_turn_plan"] = {"next_action": "revise"}

    _run(svc._track_turn(state, "int_01_elevator_pitch"))

    delta = state["session_learning_delta"]
    assert delta["strengths"] == ["specific project context"]
    assert delta["active_gaps"] == ["Add quantified impact."]
    assert delta["repeated_issue_counts"]["Add quantified impact."] == 1
    assert "did not measure the result" in delta["latest_evidence_quotes"][0]
