import pytest

from app.ai.schemas import SimulationReport
from app.content.task_types import TaskType


def _answered_interview_messages(count: int) -> list[dict]:
    messages: list[dict] = []
    for idx in range(count):
        messages.append({
            "role": "assistant",
            "content": f"[Interviewer]: Prompt {idx + 1}",
            "speaker_name": "Interviewer",
        })
        messages.append({
            "role": "user",
            "content": f"I answered prompt {idx + 1} with a specific backend example.",
            "message_kind": "learner_answer",
        })
    return messages


def test_gd_test_director_prompt_uses_active_topic_without_profile_leakage():
    from app.ai.prompts import build_director_prompt

    prompt = build_director_prompt(
        {
            "topic": "Should AI-native service companies be the new big startup pivot?",
            "phase": "probing",
            "tension": 0.4,
            "covered": [],
            "open_threads": [],
            "last_speaker": "",
        },
        [
            {
                "speaker_id": "moderator",
                "name": "Moderator",
                "stance": "neutral facilitator",
            },
            {
                "speaker_id": "data_driven_analyst",
                "name": "Data-Driven Analyst",
                "stance": "evidence-first analyst",
            },
        ],
        TaskType.GD_TEST,
        "[Learner]: AI-native service companies could scale faster.",
        scenario_config={
            "topic": "Should AI-native service companies be the new big startup pivot?",
            "environment": "Business school GD",
        },
        career_context={
            "primary_role": "Backend Software Engineer",
            "gd_topics": ["Remote work should be permanent"],
            "resume_facts": ["Built FastAPI payments systems"],
        },
    )

    assert "AI-native service companies" in prompt
    assert "Remote work should be permanent" not in prompt
    assert "FastAPI payments" not in prompt
    assert "preferred GD topics" not in prompt


def test_interview_test_director_prompt_excludes_gd_topic_preferences():
    from app.ai.prompts import build_director_prompt

    prompt = build_director_prompt(
        {
            "topic": "Mixed interview for Backend Software Engineer",
            "phase": "probing",
            "tension": 0.4,
            "covered": [],
            "open_threads": [],
            "last_speaker": "",
        },
        [{"speaker_id": "interviewer", "name": "Interviewer", "stance": "interviewer"}],
        TaskType.INTERVIEW_TEST,
        "[Learner]: I built a backend migration flow.",
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
            "pressure": "high",
        },
        career_context={
            "primary_role": "Backend Software Engineer",
            "gd_topics": ["AI in campus placements"],
            "resume_facts": ["Built FastAPI payments systems"],
        },
    )

    assert "Backend Software Engineer" in prompt
    assert "FastAPI payments" in prompt
    assert "AI in campus placements" not in prompt
    assert "preferred GD topics" not in prompt


def test_interview_test_opening_prompt_excludes_gd_topic_preferences():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_opening_prompt
    from app.content.registry import get_node

    prompt = build_opening_prompt(
        get_node("int_01_elevator_pitch"),
        [],
        behavior=behavior_for(TaskType.INTERVIEW_TEST),
        interview_test=True,
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
        career_context={
            "primary_role": "Backend Software Engineer",
            "gd_topics": ["AI in campus placements"],
            "resume_facts": ["Built FastAPI payments systems"],
        },
    )

    assert "Backend Software Engineer" in prompt
    assert "AI in campus placements" not in prompt
    assert "preferred GD topics" not in prompt


def test_interview_test_probe_generation_prompt_excludes_gd_topic_preferences():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_test_gen_prompt

    prompt = build_test_gen_prompt(
        behavior_for(TaskType.INTERVIEW_TEST),
        weaknesses=[],
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
        career_context={
            "primary_role": "Backend Software Engineer",
            "gd_topics": ["AI in campus placements"],
            "resume_facts": ["Built FastAPI payments systems"],
        },
    )

    assert "Backend Software Engineer" in prompt
    assert "FastAPI payments" in prompt
    assert "AI in campus placements" not in prompt
    assert "preferred GD topics" not in prompt


def test_safe_gd_turn_rewrites_unseen_speaker_reference_and_records_validity_flag():
    from app.services import simulation_service as sim

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should AI-native service companies be the new big startup pivot?",
        "scenario_config": {
            "topic": "Should AI-native service companies be the new big startup pivot?",
        },
        "personas": [
            {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        ],
        "messages": [
            {"role": "user", "content": "AI-native service companies can scale faster."}
        ],
    }
    persona = {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"}

    text = sim._safe_gd_turn_text(
        state,
        persona,
        "Aggressive Challenger, you raise valid points about needing evidence. Can we also explore metrics?",
    )

    assert "Aggressive Challenger, you raise valid points" not in text
    assert "AI-native service companies" in text
    assert state["assessment_validity_flags"][0]["code"] == "hidden_speaker_reference"


def test_safe_gd_turn_invalidates_handoff_that_claims_unseen_prior_speech():
    from app.services import simulation_service as sim

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should AI-native service companies be the new big startup pivot?",
        "scenario_config": {
            "topic": "Should AI-native service companies be the new big startup pivot?",
        },
        "personas": [
            {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        ],
        "messages": [{"role": "user", "content": "AI-native services can scale faster."}],
    }

    text = sim._safe_gd_turn_text(
        state,
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        "Aggressive Challenger, could you expand on what you said earlier about trust?",
    )

    assert "what you said earlier" not in text
    assert state["assessment_validity_flags"][0]["code"] == "hidden_speaker_reference"
    assert not state.get("floor_handoff_queue")


@pytest.mark.asyncio
async def test_gd_moderator_handoff_forces_target_persona_next(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services import simulation_service as sim

    async def fake_decide_round(bb, personas, *_args, **_kwargs):
        decision = DirectorDecision(
            action="pivot_topic",
            next_speaker="moderator",
            intent="Ask Devil's Advocate to take the opposite view.",
            tension=0.4,
            answer_quality=0.72,
            should_close=False,
        )
        moderator = next(p for p in personas if p["speaker_id"] == "moderator")
        return sim.apply_decision(bb, decision), moderator, decision

    async def fake_speaker_turn(persona, *_args, **_kwargs):
        if persona["speaker_id"] == "moderator":
            yield "Devil's Advocate, could you take the opposite view here?"
        elif persona["speaker_id"] == "devils_advocate":
            yield "The opposite view is that the pivot could overpromise automation before clients trust it."
        else:
            yield "General panel response."

    monkeypatch.setattr(sim, "decide_round", fake_decide_round)
    monkeypatch.setattr(sim, "_stream_speaker_turn", fake_speaker_turn)

    state = svc._new_state(
        "user-1",
        "session-gd",
        "gd_01_take_position",
        [],
        task_type=TaskType.GD_TEST.value,
        module_id="group_discussion",
        sim_topic="Should AI-native service companies be the new big startup pivot?",
        scenario_config={"topic": "Should AI-native service companies be the new big startup pivot?"},
        personas=[
            {"speaker_id": "moderator", "name": "Moderator", "role_type": "moderator"},
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
            {"speaker_id": "devils_advocate", "name": "Devil's Advocate", "role_type": "debater"},
        ],
    )
    state["messages"] = [
        {"role": "user", "content": "AI-native service companies can scale, but client trust is fragile."}
    ]

    speaker_names: list[str] = []
    text_parts: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speaker_names.append(item.name)
        elif isinstance(item, str):
            text_parts.append(item)

    assert speaker_names[:2] == ["Moderator", "Devil's Advocate"]
    assert "opposite view" in " ".join(text_parts)


@pytest.mark.asyncio
async def test_score_session_invalidates_gd_report_with_simulator_validity_flags(monkeypatch):
    from app.services import simulation_service as sim

    async def generous_model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.91,
            summary="The discussion was strong.",
            strengths=["specific evidence"],
            improvements=["tighten conclusion"],
            participation_score=0.9,
            relevance_score=0.9,
            language_score=0.9,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", generous_model_report)

    messages = []
    for idx in range(5):
        messages.append({
            "role": "assistant",
            "content": f"Panel prompt {idx + 1}",
            "speaker_name": "Data-Driven Analyst",
        })
        messages.append({
            "role": "user",
            "content": f"I answered with evidence point {idx + 1}.",
            "message_kind": "learner_answer",
        })

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should AI-native service companies be the new big startup pivot?",
        "scenario_config": {"topic": "Should AI-native service companies be the new big startup pivot?"},
        "blackboard": {"qualities": [0.8, 0.8, 0.8, 0.8, 0.8]},
        "coverage_events": [
            {"topic_angle": f"angle-{idx}", "answered": True, "score_evidence": 0.8}
            for idx in range(5)
        ],
        "assessment_validity_flags": [
            {
                "code": "hidden_speaker_reference",
                "message": "A panelist referenced a speaker who had not visibly spoken.",
                "severity": "invalid",
            }
        ],
        "messages": messages,
    })

    assert report.validity_status == "invalid_simulation"
    assert report.score == 0.0
    assert any("speaker" in caveat.lower() for caveat in report.assessment_caveats)


def test_interview_move_on_control_replaces_active_probe_identity():
    from app.services import simulation_service as sim

    state = {
        "task_type": TaskType.INTERVIEW_TEST.value,
        "messages": [
            {"role": "assistant", "content": "Explain Singleton and Factory."},
            {"role": "user", "content": "I already answered that. Move to a teammate disagreement."},
        ],
        "active_interview_probe_prompt": "Explain Singleton and Factory.",
        "active_interview_probe_skill_id": "design_patterns",
        "active_interview_probe_prompt_id": "prompt_design_patterns",
    }

    decision = sim._interview_control_decision(
        state,
        [{"speaker_id": "interviewer", "name": "Interviewer"}],
        {"tension": 0.5, "last_quality": 0.6},
    )

    assert decision is not None
    assert "teammate" in state["active_interview_probe_prompt"].lower()
    assert state["active_interview_probe_skill_id"] == "interview_collaboration_pivot"
    assert state["active_interview_probe_prompt_id"] != "prompt_design_patterns"


@pytest.mark.asyncio
async def test_score_session_returns_insufficient_evidence_without_minimum_scorable_turns(monkeypatch):
    from app.services import simulation_service as sim

    async def should_not_call_model(*_args, **_kwargs):
        raise AssertionError("thin simulations should not call the final model scorer")

    monkeypatch.setattr(sim, "evaluate_simulation", should_not_call_model)

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Backend Software Engineer",
        "scenario_config": {"target_role": "Backend Software Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "blackboard": {"qualities": [0.74]},
        "messages": _answered_interview_messages(1),
    })

    assert report.validity_status == "insufficient_evidence"
    assert report.scorable_turn_count == 1
    assert report.score == 0.0
    assert any("not enough answered turns" in caveat.lower() for caveat in report.assessment_caveats)


@pytest.mark.asyncio
async def test_score_session_caps_final_report_when_coverage_is_too_narrow(monkeypatch):
    from app.services import simulation_service as sim

    async def generous_model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.94,
            summary="The candidate gave strong answers.",
            strengths=["Clear backend examples"],
            improvements=["Add more stakeholder detail"],
            clarity_score=0.93,
            confidence_score=0.91,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", generous_model_report)

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Backend Software Engineer",
        "scenario_config": {"target_role": "Backend Software Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "blackboard": {"qualities": [0.9, 0.88, 0.87, 0.86, 0.86, 0.85]},
        "coverage_events": [
            {
                "skill_id": "design_patterns",
                "prompt_id": "same-design-pattern-prompt",
                "answered": True,
                "score_evidence": 0.86,
            }
            for _ in range(6)
        ],
        "messages": _answered_interview_messages(6),
    })

    assert report.validity_status == "partial"
    assert report.scorable_turn_count == 6
    assert report.score <= 0.72
    assert report.coverage_map["unique_covered"] == 1
    assert report.coverage_map["required_unique"] >= 4
    assert any("coverage" in caveat.lower() for caveat in report.assessment_caveats)


@pytest.mark.asyncio
async def test_stream_simulation_round_records_typed_coverage_events(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services import simulation_service as sim

    decisions = iter([
        DirectorDecision(
            action="probe_deeper",
            next_speaker="interviewer",
            intent="Ask the project-depth prompt.",
            tension=0.4,
            answer_quality=0.77,
            should_close=False,
        ),
        DirectorDecision(
            action="pivot_topic",
            next_speaker="interviewer",
            intent="Ask the collaboration prompt.",
            tension=0.5,
            answer_quality=0.83,
            should_close=False,
        ),
    ])

    async def fake_director(*_args, **_kwargs):
        return next(decisions)

    async def fake_speaker_turn(*_args, **_kwargs):
        yield "Tell me about a project tradeoff."

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", fake_director)
    monkeypatch.setattr(sim, "_stream_speaker_turn", fake_speaker_turn)

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        sim_topic="Mixed interview for Backend Software Engineer",
        scenario_config={"target_role": "Backend Software Engineer"},
        personas=[{"speaker_id": "interviewer", "name": "Interviewer", "role_type": "interviewer"}],
    )
    state["probe_items"] = [
        {"skill_id": "project_tradeoff", "prompt": "Tell me about a project tradeoff.", "aim": "names a tradeoff"},
        {"skill_id": "collaboration", "prompt": "Tell me about a disagreement.", "aim": "shows collaboration"},
    ]
    state["messages"] = [{"role": "user", "content": "Opening answer."}]

    async for _item in sim.stream_simulation_round(state):
        pass

    assert state["pending_coverage_event"]["skill_id"] == "project_tradeoff"
    assert state["coverage_events"] == []

    state["messages"].append({"role": "user", "content": "I chose Postgres over NoSQL for transaction safety."})
    async for _item in sim.stream_simulation_round(state):
        pass

    assert len(state["coverage_events"]) == 1
    event = state["coverage_events"][0]
    assert event["skill_id"] == "project_tradeoff"
    assert event["answered"] is True
    assert event["score_evidence"] == 0.83
    assert "transaction safety" in event["learner_answer_excerpt"]


@pytest.mark.asyncio
async def test_closed_test_report_uses_module_id_for_learning_profile(monkeypatch):
    from app.services import session_service as svc

    async def fake_score_session(_state):
        return SimulationReport(
            score=0.74,
            summary="Interview scored.",
            strengths=["specific example"],
            improvements=["add quantified impact"],
            clarity_score=0.74,
            confidence_score=0.7,
            validity_status="final",
            scorable_turn_count=6,
        )

    captured = {}

    async def fake_record_session_report(self, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    monkeypatch.setattr(
        "app.services.session_service.CareerLearningProfileService.record_session_report",
        fake_record_session_report,
    )

    state = svc._new_state(
        "user-1",
        "session-2",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        sim_topic="Mixed interview for Backend Software Engineer",
    )
    svc.SessionStore["session-2"] = state

    await svc.close_session("session-2")

    assert captured["module_id"] == "interview"
    assert captured["task_type"] == TaskType.INTERVIEW_TEST.value


@pytest.mark.asyncio
async def test_invalid_simulation_report_does_not_update_learning_profile(monkeypatch):
    from app.services import session_service as svc

    async def fake_score_session(_state):
        return SimulationReport(
            score=0.0,
            summary="Invalid simulator transcript.",
            strengths=[],
            improvements=["Retry the assessment"],
            validity_status="invalid_simulation",
            scorable_turn_count=6,
            assessment_caveats=["Simulator caveat: hidden speaker reference."],
        )

    async def should_not_record(*_args, **_kwargs):
        raise AssertionError("invalid simulator reports must not update the learner profile")

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    monkeypatch.setattr(
        "app.services.session_service.CareerLearningProfileService.record_session_report",
        should_not_record,
    )

    state = svc._new_state(
        "user-1",
        "session-invalid",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.GD_TEST.value,
        module_id="group_discussion",
        sim_topic="Should AI-native service companies be the new big startup pivot?",
    )
    svc.SessionStore["session-invalid"] = state

    result = await svc.close_session("session-invalid")

    assert result["report"]["validity_status"] == "invalid_simulation"
