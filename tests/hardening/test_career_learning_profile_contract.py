import asyncio

from app.ai.schemas import CriterionEval, PrepRubricEval, ProbeItem, SimulationReport
from app.content.registry import get_module, get_node
from app.content.task_types import TaskType
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
    independent_result = {
        "pass_eligible": True,
        "mastery_eligible": False,
        "effective_score": 0.82,
        "next_focus": "Apply the skill in a different context.",
        "attempt_type": "independent",
    }
    ready_result = {
        "pass_eligible": True,
        "mastery_eligible": False,
        "effective_score": 0.82,
        "next_focus": "Try the same skill under pressure.",
        "attempt_type": "transfer",
    }

    progress = {}
    for _ in range(2):
        progress = compute_attempt_credit(progress, independent_result)
    for _ in range(3):
        progress = compute_attempt_credit(progress, ready_result, transfer=True)

    assert progress["display_status"] == "in_progress"

    progress = compute_attempt_credit(
        progress,
        {**ready_result, "attempt_type": "pressure"},
        pressure=True,
    )
    progress = compute_attempt_credit(progress, independent_result)

    assert progress["display_status"] == "ready_to_advance"
    assert progress["readiness_score"] >= 0.8
    assert progress["node_mastered"] is False


def test_attempt_credit_deduplicates_repeated_prompt_context_evidence():
    result = {
        "pass_eligible": True,
        "mastery_eligible": False,
        "effective_score": 0.84,
        "next_focus": "Apply this in a new context.",
        "attempt_type": "independent",
    }

    progress = compute_attempt_credit({}, result, evidence_id="evidence-1")
    repeated = compute_attempt_credit(progress, result, evidence_id="evidence-1")
    distinct = compute_attempt_credit(repeated, result, evidence_id="evidence-2")

    assert repeated["independent_passes"] == 1
    assert repeated["meaningful_attempts"] == 1
    assert distinct["independent_passes"] == 2
    assert distinct["meaningful_attempts"] == 2
    assert {item["evidence_id"] for item in distinct["mastery_evidence"]} == {
        "evidence-1",
        "evidence-2",
    }
    hydrated = {
        key: distinct[key]
        for key in (
            "independent_passes",
            "meaningful_attempts",
            "mastery_evidence",
        )
    }
    replayed_after_reload = compute_attempt_credit(
        hydrated,
        result,
        evidence_id="evidence-2",
    )
    assert replayed_after_reload["independent_passes"] == 2
    assert replayed_after_reload["meaningful_attempts"] == 2


def test_career_progress_evidence_identity_is_session_independent_and_context_bound():
    from app.services import session_service as svc

    def state_for(session_id: str, topic: str) -> dict:
        state = svc._new_state(
            "user-1",
            session_id,
            "gd_02_support_with_evidence",
            [],
            task_type="gd_prep",
            module_id="group_discussion",
        )
        state["messages"] = [
            {"role": "assistant", "content": "Support the motion with one grounded example."},
            {"role": "user", "content": "I would compare retention before and after the policy."},
        ]
        state["last_evaluated_task_contract"] = {
            "active_topic": topic,
            "semantic_anchors": ["retention"],
            "participant_claims": [],
        }
        return state

    result = {"attempt_type": "independent"}
    first = svc._career_progress_evidence_id(state_for("session-1", "Remote work"), result)
    replay = svc._career_progress_evidence_id(state_for("session-2", "Remote work"), result)
    new_context = svc._career_progress_evidence_id(state_for("session-3", "Four-day week"), result)

    assert first == replay
    assert first != new_context


def test_private_credit_ids_do_not_enter_prompt_or_public_mastery_evidence():
    from app.services import session_service as svc
    from app.services.learning_profile import _progression_evidence

    private = [{
        "evidence_id": "private-hash",
        "attempt_type": "independent",
        "score": 0.84,
    }]
    assert _progression_evidence({
        "mastery_evidence": private,
        "last_gap": "Add a clearer result.",
    }) == "Add a clearer result."
    assert svc.public_mastery_evidence({
        "node_mastered": False,
        "mastery_evidence": private,
    }) == []

    mastered = [{
        **private[0],
        "criteria": [{"id": "result", "evidence_quote": "reduced failures by 20%"}],
    }]
    public = svc.public_mastery_evidence({
        "node_mastered": True,
        "mastery_evidence": mastered,
    })
    assert public[0]["criteria"][0]["evidence_quote"] == "reduced failures by 20%"
    assert "evidence_id" not in public[0]


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
    answer = (
        "I support AI in campus placements. As a hypothetical, a pilot could compare "
        "shortlist accuracy before rollout."
    )
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
                    evidence_quote="a pilot could compare shortlist accuracy",
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
    assert "a pilot could compare shortlist accuracy" in event["evidence_json"]["criteria"][1]["evidence_quote"]

    profile = store.learner_skill_profiles[("user-1", "career", "gd_02_support_with_evidence")]
    assert profile["readiness"] == result.effective_score
    assert profile["recommended_next_action"] == ""


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
    skill_id = store.learning_events[0]["skill_id"]
    profile = store.learner_skill_profiles[("user-1", "career", skill_id)]
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
    assert store.learning_events == []
    assert store.learner_skill_profiles == {}


def test_invalid_and_insufficient_reports_are_excluded_from_adaptive_memory_context():
    from app.services.learning_profile import build_career_memory_context

    context = build_career_memory_context({
        "profiles": [],
        "events": [],
        "progression": [],
        "reports": [
            {"task_type": "gd_test", "status": "invalid_simulation", "summary": "broken simulator"},
            {"task_type": "interview_test", "status": "insufficient_evidence", "summary": "too few turns"},
            {"task_type": "interview_test", "status": "partial", "summary": "usable gaps only"},
        ],
    })

    assert context["recent_reports"] == [{
        "task_type": "interview_test",
        "status": "partial",
        "score": 0.0,
        "summary": "usable gaps only",
        "recommended_actions": [],
    }]


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
    skill_id = store.learning_events[0]["skill_id"]
    profile = store.learner_skill_profiles[("user-1", "career", skill_id)]
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


def test_hot_session_learning_delta_is_idempotent_by_evaluation_id():
    from app.services import session_service as svc

    state = svc._new_state(
        "user-1",
        "session-delta-idempotent",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    result = {
        "effective_score": 0.42,
        "next_focus": "Add quantified impact.",
        "criteria": [{"id": "impact", "met": False, "evidence_quote": "no measured result"}],
        "required_missing": ["impact"],
        "pass_eligible": False,
        "mastery_eligible": False,
    }

    svc._update_session_learning_delta(state, result, "There was no measured result.", "eval-1")
    svc._update_session_learning_delta(state, result, "There was no measured result.", "eval-1")

    delta = state["session_learning_delta"]
    assert delta["repeated_issue_counts"]["Add quantified impact."] == 1
    assert delta["repeated_issue_counts"]["criterion:impact"] == 1
    assert delta["applied_evaluation_ids"] == ["eval-1"]


def test_career_memory_context_scopes_all_structural_rows_to_interview():
    from app.services.learning_profile import build_career_memory_context

    context = build_career_memory_context(
        {
            "profiles": [
                {
                    "domain": "career",
                    "skill_id": "interview_feedback_integration",
                    "module_id": "interview",
                    "task_type": "interview_prep",
                    "readiness": 0.4,
                    "confidence": 0.7,
                    "gaps_json": ["Build on others' feedback in an interview answer."],
                },
                {
                    "domain": "career",
                    "skill_id": "gd_stance",
                    "module_id": "group_discussion",
                    "task_type": "gd_prep",
                    "readiness": 0.4,
                    "confidence": 0.7,
                    "gaps_json": ["State a clear position."],
                },
            ],
            "events": [
                {
                    "domain": "career",
                    "skill_id": "interview_feedback_integration",
                    "module_id": "interview",
                    "task_type": "interview_prep",
                    "gap": "interview-gap",
                    "score": 0.3,
                },
                {
                    "domain": "career",
                    "skill_id": "gd_stance",
                    "module_id": "group_discussion",
                    "task_type": "gd_prep",
                    "gap": "gd-gap",
                    "score": 0.3,
                },
            ],
            "progression": [
                {"node_id": "int_04_star_behavioral", "ema": 0.35, "last_gap": "Add a result."},
                {"node_id": "gd_01_stake_position", "ema": 0.35, "last_gap": "Commit early."},
            ],
            "reports": [
                {"task_type": "interview_test", "status": "final", "summary": "Interview report."},
                {"task_type": "gd_test", "status": "final", "summary": "GD report."},
            ],
        },
        module_id="interview",
    )

    items = [
        item
        for key in ("active_gaps", "improving_gaps", "resolved_gaps", "mastered_skills")
        for item in context[key]
    ]
    assert {item["skill_id"] for item in items} == {
        "interview_feedback_integration",
        "int_04_star_behavioral",
    }
    assert all(item["module_id"] == "interview" for item in items)
    assert "Build on others' feedback" in items[0]["gap"]
    assert set(context["repeated_issue_counts"]) == {
        "interview_feedback_integration",
        "interview-gap",
    }
    assert [report["task_type"] for report in context["recent_reports"]] == ["interview_test"]


def test_career_context_for_node_scopes_nested_memory_without_mutating_source():
    from app.ai.prompts import _career_context_for_node

    source = {
        "primary_role": "Backend Engineer",
        "gd_topics": ["Remote work"],
        "career_memory_context": {
            "active_gaps": [
                {
                    "skill_id": "interview_gap",
                    "module_id": "interview",
                    "task_type": "interview_prep",
                    "gap": "Add impact.",
                },
                {
                    "skill_id": "gd_gap",
                    "module_id": "group_discussion",
                    "task_type": "gd_prep",
                    "gap": "State a position.",
                },
            ],
            "improving_gaps": [],
            "resolved_gaps": [],
            "mastered_skills": [],
            "repeated_issue_counts": {
                "interview_gap": 2,
                "gd_gap": 3,
                "Add evidence.": 9,
            },
            "recent_reports": [
                {"task_type": "interview_test", "summary": "Interview report."},
                {"task_type": "gd_test", "summary": "GD report."},
            ],
        },
    }

    scoped = _career_context_for_node(get_node("int_01_elevator_pitch"), source)

    memory = scoped["career_memory_context"]
    assert [item["skill_id"] for item in memory["active_gaps"]] == ["interview_gap"]
    assert memory["repeated_issue_counts"] == {"interview_gap": 2}
    assert [report["task_type"] for report in memory["recent_reports"]] == ["interview_test"]
    assert len(source["career_memory_context"]["active_gaps"]) == 2


def test_interview_test_history_combines_exact_test_and_matching_prep_only(monkeypatch, store):
    calls: list[tuple[str, int]] = []
    histories = {
        "interview_test": [
            {"session_id": "test-1", "node_id": "int_01_elevator_pitch", "raw": "test one"},
            {"session_id": "shared", "node_id": "int_02_strength_with_evidence", "raw": "shared"},
            {"session_id": "wrong-mode", "node_id": "gd_01_stake_position", "raw": "gd"},
        ],
        "interview_prep": [
            {"session_id": "shared", "node_id": "int_02_strength_with_evidence", "raw": "shared"},
            {"session_id": "prep-1", "node_id": "int_04_star_behavioral", "raw": "prep one"},
            {"session_id": "prep-2", "node_id": "int_05_why_this_role", "raw": "prep two"},
        ],
        "gd_prep": [{"session_id": "gd-1", "node_id": "gd_01_stake_position", "raw": "gd"}],
    }

    async def load_context(_user_id: str, task_type: str, k: int = 3):
        calls.append((task_type, k))
        return histories.get(task_type, [])[:k]

    async def no_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(store, "load_context", load_context)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", no_probe_items)

    _session_id, state = _run(
        svc.start_session(
            "user-1",
            "int_01_elevator_pitch",
            test_mode=True,
            persist=False,
        )
    )

    assert calls == [("interview_test", 3), ("interview_prep", 3)]
    assert [row["session_id"] for row in state["memory_context"]] == [
        "test-1",
        "shared",
        "prep-1",
        "prep-2",
    ]
    assert len(state["memory_context"]) <= 6


def test_prep_precache_carries_hot_delta_without_mutating_session_context(monkeypatch):
    generated: dict = {}
    cached: dict = {}

    async def fake_generate_test_items(user_id, task_type, **kwargs):
        generated.update({"user_id": user_id, "task_type": task_type, **kwargs})
        return [ProbeItem(skill_id="impact", prompt="Show the result.", aim="Specific impact")]

    class CacheStore:
        async def cache_test_items(self, user_id, task_type, items, context_hash="default"):
            cached.update(
                user_id=user_id,
                task_type=task_type,
                items=items,
                context_hash=context_hash,
            )

    state = svc._new_state(
        "user-1",
        "prep-session",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
        career_context={"primary_role": "Backend Engineer"},
        context_hash="role-context",
    )
    state["session_learning_delta"] = {
        "module_id": "interview",
        "task_type": "interview_prep",
        "active_gaps": ["Add quantified impact."],
        "repeated_issue_counts": {
            "Add quantified impact.": 2,
            "criterion:result": 2,
        },
        "latest_evidence_quotes": ["I fixed it but did not measure the result."],
    }
    monkeypatch.setattr(svc, "generate_test_items", fake_generate_test_items)
    monkeypatch.setattr(svc, "get_storage", lambda: CacheStore())

    _run(svc._precache_test_items(state))

    assert generated["task_type"] == "interview_test"
    assert generated["career_context"]["session_learning_delta"] == state["session_learning_delta"]
    assert generated["career_context"]["session_learning_delta"] is not state["session_learning_delta"]
    assert "session_learning_delta" not in state["career_context"]
    assert cached["items"][0]["prompt"] == "Show the result."


def test_test_generation_prompt_uses_only_matching_prep_hot_delta():
    from app.ai.prompts import build_test_gen_prompt

    career_context = {
        "session_learning_delta": {
            "module_id": "interview",
            "task_type": "interview_prep",
            "active_gaps": ["Add quantified impact."],
            "repeated_issue_counts": {
                "Add quantified impact.": 2,
                "criterion:result": 2,
            },
            "latest_evidence_quotes": ["I fixed it but did not measure the result."],
        }
    }

    interview_prompt = build_test_gen_prompt(
        None,
        [],
        career_context=career_context,
        task_type=TaskType.INTERVIEW_TEST,
    )
    gd_prompt = build_test_gen_prompt(
        None,
        [],
        career_context=career_context,
        task_type=TaskType.GD_TEST,
    )

    assert "result" in interview_prompt
    assert "seen 2x" in interview_prompt
    assert "Add quantified impact." not in interview_prompt
    assert "I fixed it but did not measure the result." not in interview_prompt
    assert "Add quantified impact." not in gd_prompt


def test_pgvector_career_history_uses_durable_task_scope(monkeypatch):
    from app.memory import store as memory_store

    seen: dict = {}

    class MappingResult:
        def mappings(self):
            return self

        def all(self):
            return [{
                "session_id": "session-1",
                "node_id": "int_04_star_behavioral",
                "content": "Strengths: clear action",
                "task_type": "interview_test",
                "module_id": "interview",
            }]

    class FakeSession:
        async def execute(self, statement, params):
            seen["sql"] = str(statement)
            seen["params"] = dict(params)
            return MappingResult()

    async def fake_embed(_text):
        return [0.0, 1.0]

    monkeypatch.setattr(memory_store, "embed", fake_embed)

    rows = _run(memory_store.load_context(
        FakeSession(),
        "user-1",
        "interview_test",
        3,
    ))

    assert "LEFT JOIN sessions" in seen["sql"]
    assert "s.task_type = :task_type" in seen["sql"]
    assert "CASE WHEN s.task_type = :task_type THEN 0 ELSE 1 END" in seen["sql"]
    assert seen["params"]["task_type"] == "interview_test"
    assert seen["params"]["legacy_prefix"] == ""
    assert rows[0]["task_type"] == "interview_test"

    _run(memory_store.load_context(
        FakeSession(),
        "user-1",
        "interview_prep",
        3,
    ))
    assert seen["params"]["legacy_prefix"] == "int\\_%"
    assert "ESCAPE '\\'" in seen["sql"]
