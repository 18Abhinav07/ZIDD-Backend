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
    assert len(store.learning_events) == 1
    assert store.learning_events[0]["source"] == "test_report"
    assert store.learning_events[0]["gap"] == "evidence_under_pressure"
    profile = store.learner_skill_profiles[("user-1", "career", "evidence_under_pressure")]
    assert profile["recommended_next_action"] == "Add evidence under pressure"


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
