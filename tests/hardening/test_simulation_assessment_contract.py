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


def test_gd_test_probe_generation_prompt_uses_gd_context_without_scenario_topic():
    from app.ai.behaviors import behavior_for
    from app.ai.prompts import build_test_gen_prompt

    prompt = build_test_gen_prompt(
        behavior_for(TaskType.GD_TEST),
        weaknesses=[],
        task_type=TaskType.GD_TEST,
        scenario_config={},
        career_context={
            "primary_role": "Backend Software Engineer",
            "gd_topics": ["Should remote work be the default?"],
            "resume_facts": ["Built FastAPI payments systems"],
        },
    )

    assert "Scored GD assessment context" in prompt
    assert "active GD motion" in prompt
    assert "Scored interview assessment context" not in prompt
    assert "Backend Software Engineer" not in prompt


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


def test_safe_gd_turn_rewrites_self_label_meta_prompt():
    from app.services import simulation_service as sim

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "personas": [
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        ],
        "messages": [
            {"role": "user", "content": "Remote work should be default with guardrails."}
        ],
    }
    persona = {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"}

    text = sim._safe_gd_turn_text(
        state,
        persona,
        "Data-Driven Analyst, could you ask the learner to provide company examples?",
    )

    assert "Data-Driven Analyst, could you ask" not in text
    assert "remote work" in text.lower()
    assert state["assessment_validity_flags"][0]["code"] == "self_label_or_meta_response"


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
                "code": "fatal_simulator_state_corruption",
                "message": "The simulator committed a transcript event that cannot be reconciled with assessment state.",
                "severity": "invalid",
            }
        ],
        "messages": messages,
    })

    assert report.validity_status == "invalid_simulation"
    assert report.score == 0.0
    assert any("simulator" in caveat.lower() or "transcript" in caveat.lower() for caveat in report.assessment_caveats)


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
async def test_score_session_fails_closed_when_typed_assessment_events_under_count(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        raise AssertionError("typed-event under-count must not be repaired from transcript messages")

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)

    messages = []
    for idx in range(10):
        messages.append({
            "role": "assistant",
            "content": f"Panel prompt {idx + 1}",
            "speaker_name": "Data-Driven Analyst",
        })
        message = {
            "role": "user",
            "content": f"I answered round {idx + 1} with a concrete remote-work argument.",
            "message_kind": "learner_answer",
        }
        if idx in {1, 4, 7}:
            message["assessment_action"] = {
                "kind": "ask_panelist",
                "speaker_id": "aggressive_challenger",
            }
        messages.append(message)

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "blackboard": {"qualities": [0.72, 0.75, 0.78]},
        "assessment_events": [
            {
                "event_type": "analysis",
                "task_type": TaskType.GD_TEST.value,
                "speaker_id": "data_driven_analyst",
                "scorable": True,
                "analysis": {"quality_score": 0.72},
                "content": "Only one persisted typed event survived.",
            },
        ],
        "messages": messages,
    })

    assert report.validity_status == "insufficient_evidence"
    assert report.scorable_turn_count == 1
    assert report.coverage_map["event_count"] == 1
    assert report.score == 0


def test_effective_scorable_count_uses_event_truth_when_events_cover_transcript():
    from app.services.simulation_service import _effective_scorable_turn_count

    messages = [
        {
            "role": "user",
            "content": f"turn {index}",
            "message_kind": "learner_answer",
        }
        for index in range(10)
    ]
    events = [
        {
            "event_type": "analysis",
            "scorable": index < 5,
            "analysis": {"control_intent": "none" if index < 5 else "clarify"},
        }
        for index in range(10)
    ]

    assert _effective_scorable_turn_count({"assessment_events": events}, messages) == 5


def test_effective_scorable_count_does_not_upgrade_non_scorable_events_from_messages():
    from app.services.simulation_service import _effective_scorable_turn_count

    messages = [
        {
            "role": "user",
            "content": f"turn {index}",
            "message_kind": "learner_answer",
        }
        for index in range(10)
    ]
    events = [
        {
            "event_type": "analysis",
            "scorable": index < 5,
            "analysis": {"control_intent": "none"},
        }
        for index in range(10)
    ]

    assert _effective_scorable_turn_count({"assessment_events": events}, messages) == 5


def test_typed_scorable_projection_keeps_alignment_across_control_turns():
    from app.services.simulation_service import _typed_scorable_messages

    messages = [
        {"role": "assistant", "content": "Question one"},
        {"role": "user", "content": "Answer one"},
        {"role": "assistant", "content": "Question two"},
        {"role": "user", "content": "Clarify", "message_kind": "simulation_control"},
        {"role": "assistant", "content": "Clarified question two"},
        {"role": "user", "content": "Answer two"},
    ]
    events = [
        {"event_type": "analysis", "scorable": True},
        {"event_type": "analysis", "scorable": False, "analysis": {"control_intent": "clarify"}},
        {"event_type": "analysis", "scorable": True},
    ]

    projected = _typed_scorable_messages(messages, events)

    assert [message["content"] for message in projected if message["role"] == "user"] == [
        "Answer one",
        "Answer two",
    ]
    assert projected[-2]["content"] == "Clarified question two"


def test_typed_scorable_projection_drops_legacy_prefix_after_reload():
    from app.services.simulation_service import _typed_scorable_messages

    messages = [
        {"role": "assistant", "content": "Legacy prompt"},
        {"role": "user", "content": "Legacy answer"},
        {"role": "assistant", "content": "Typed prompt"},
        {"role": "user", "content": "Typed answer", "turn_id": "turn-2"},
    ]
    events = [{
        "event_type": "analysis",
        "scorable": True,
        "learner_turn_id": "turn-2",
    }]

    projected = _typed_scorable_messages(messages, events)

    assert [message["content"] for message in projected if message["role"] == "user"] == [
        "Typed answer"
    ]


def test_assessment_progress_does_not_double_count_typed_control_messages():
    from app.services.simulation_service import assessment_progress_snapshot

    snapshot = assessment_progress_snapshot({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "assessment_events": [{
            "event_type": "analysis",
            "scorable": False,
            "analysis": {"control_intent": "clarify"},
        }],
        "messages": [{
            "role": "user",
            "content": "Could you clarify?",
            "message_kind": "simulation_control",
        }],
    })

    assert snapshot["control_turn_count"] == 1


def test_round_qualities_use_only_scorable_typed_event_values():
    from app.services.simulation_service import _normalized_round_qualities

    state = {
        "blackboard": {"qualities": [0.9, 0.9, 0.1]},
        "assessment_events": [
            {
                "event_type": "analysis",
                "scorable": True,
                "analysis": {"quality_score": 0.8},
            },
            {
                "event_type": "analysis",
                "scorable": False,
                "analysis": {
                    "quality_score": 0.1,
                    "score_excluded_reason": "simulator_integrity_repair",
                },
            },
        ],
    }

    assert _normalized_round_qualities(state) == [0.8]


def test_insufficient_report_exposes_excluded_turn_count():
    from app.services.simulation_service import _insufficient_evidence_report

    state = {
        "assessment_events": [
            *[{"event_type": "analysis", "scorable": True} for _ in range(3)],
            *[
                {
                    "event_type": "analysis",
                    "scorable": False,
                    "analysis": {"score_excluded_reason": "simulator_integrity_repair"},
                }
                for _ in range(2)
            ],
        ],
        "messages": [],
    }

    report = _insufficient_evidence_report(
        state,
        TaskType.INTERVIEW_TEST,
        3,
        {"unique_covered": 2, "required_unique": 4},
    )

    assert report.score_breakdown["excluded_turn_count"] == 2


def test_gd_focus_coverage_is_recorded_only_after_answered_prompt():
    from app.ai.schemas import DirectorDecision
    from app.services import simulation_service as sim

    state = {
        "task_type": TaskType.GD_TEST.value,
        "assessment_plan": {
            "focus_plan": [
                {"focus_id": "gd-evidence"},
                {"focus_id": "gd-synthesis"},
            ],
        },
        "coverage_events": [],
        "blackboard": {"turn": 0, "phase": "opening"},
    }
    persona = {"speaker_id": "devils_advocate", "name": "Devil's Advocate"}
    decision = DirectorDecision(
        action="probe_deeper",
        next_speaker="devils_advocate",
        intent="Challenge the evidence.",
        tension=0.4,
        answer_quality=0.72,
        should_close=False,
    )

    sim._stage_prompt_coverage_event(
        state,
        TaskType.GD_TEST,
        persona,
        decision,
        "A metric can still hide trust erosion.",
    )
    assert state["pending_coverage_event"]["focus_id"] == "gd-evidence"
    assert state["coverage_events"] == []

    state["messages"] = [{"role": "user", "content": "I would also track onboarding trust."}]
    sim._settle_pending_coverage_event(state, decision, control_turn=False)
    assert state["coverage_events"][0]["focus_id"] == "gd-evidence"

    sim._stage_prompt_coverage_event(
        state,
        TaskType.GD_TEST,
        persona,
        decision,
        "Now reconcile access and trust.",
    )
    assert state["pending_coverage_event"]["focus_id"] == "gd-synthesis"


def test_assessment_turn_call_failure_is_not_learner_score_evidence():
    from app.services.simulation_service import (
        _assessment_evidence_quotes,
        _coverage_events_from_analysis_events,
        _effective_scorable_turn_count,
    )

    messages = [
        {
            "role": "user",
            "content": "I support remote work by default because it expands access and should be checked with retention and onboarding metrics.",
            "message_kind": "learner_answer",
        }
        for _ in range(5)
    ]
    state = {
        "assessment_events": [
            {
                "event_type": "analysis",
                "task_type": TaskType.GD_TEST.value,
                "speaker_id": "data_driven_analyst",
                "scorable": False,
                "analysis": {
                    "routing_case": "point_only",
                    "scorable": False,
                    "score_excluded_reason": "assessment_turn_call_failed",
                    "evidence_points": ["remote work expands access and needs retention/onboarding metrics"],
                },
                "content": "Deterministic repair response.",
                "validity_flags": [{"code": "assessment_turn_call_failed", "severity": "partial"}],
            }
            for _ in range(5)
        ],
    }

    assert _effective_scorable_turn_count(state, messages) == 0
    assert _coverage_events_from_analysis_events(state) == []
    assert _assessment_evidence_quotes(state) == []


@pytest.mark.asyncio
async def test_score_session_marks_all_excluded_gd_turns_invalid(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        raise AssertionError("excluded GD answers must not reach the final scorer")

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)
    messages = []
    assessment_events = []
    for index in range(5):
        answer = (
            f"I support remote work by default in round {index + 1} because it expands access, "
            "but I would monitor onboarding speed, delivery quality, retention, and decision latency."
        )
        messages.append({
            "role": "assistant",
            "content": f"Panel prompt {index + 1}",
            "speaker_name": "Data-Driven Analyst",
        })
        messages.append({
            "role": "user",
            "content": answer,
            "message_kind": "learner_answer",
        })
        assessment_events.append({
            "event_type": "analysis",
            "task_type": TaskType.GD_TEST.value,
            "speaker_id": "data_driven_analyst",
            "scorable": False,
            "analysis": {
                "routing_case": "point_only",
                "topic_angle": f"gd_angle_{index % 3}",
                "scorable": False,
                "score_excluded_reason": "simulator_integrity_repair",
                "evidence_points": [answer],
                "quality_score": 0.76,
            },
            "content": "Repaired panel contribution.",
            "validity_flags": [{"code": "gd_panelist_ask_only_repaired", "severity": "partial"}],
        })

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "assessment_plan": {"mode": TaskType.GD_TEST.value, "topic": "Should remote work be the default?"},
        "blackboard": {"qualities": []},
        "assessment_events": assessment_events,
        "assessment_validity_flags": [
            {
                "code": "gd_panelist_ask_only_repaired",
                "message": "A GD panelist asked only a question instead of contributing to the discussion.",
                "severity": "partial",
            }
        ],
        "messages": messages,
    })

    assert report.validity_status == "invalid_simulation"
    assert report.scorable_turn_count == 0
    assert report.coverage_map["unique_covered"] == 0
    assert report.evidence_quotes == []
    learner_text = "\n".join(report.learner_assessment_caveats).lower()
    assert "not enough answered turns" not in learner_text
    assert report.simulator_integrity_notes
    assert report.score_breakdown["validity_cap"] == 0.0
    assert report.score_breakdown["excluded_turn_count"] == 5


@pytest.mark.asyncio
async def test_score_session_does_not_cap_safe_visible_response_repairs(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.86,
            summary="The learner gave enough evidence across the GD.",
            strengths=["Used metrics and trade-offs"],
            improvements=["Add one stronger counterexample"],
            participation_score=0.86,
            relevance_score=0.84,
            language_score=0.82,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)
    messages = []
    for index in range(5):
        messages.extend([
            {"role": "assistant", "content": f"Panel prompt {index + 1}", "speaker_name": "Data-Driven Analyst"},
            {
                "role": "user",
                "content": (
                    f"In round {index + 1}, I support remote default with onboarding metrics, "
                    "decision latency, retention, and delivery quality as safeguards."
                ),
                "message_kind": "learner_answer",
            },
        ])
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "blackboard": {"qualities": [0.8, 0.82, 0.84, 0.83, 0.85]},
        "coverage_events": [
            {"topic_angle": f"angle-{index % 3}", "answered": True, "score_evidence": 0.82}
            for index in range(5)
        ],
        "assessment_validity_flags": [
            {
                "code": "gd_panelist_ask_only_repaired",
                "message": "A GD panelist asked a follow-up question or controlled the floor instead of contributing to the discussion.",
                "severity": "partial",
            },
            {
                "code": "gd_panelist_formulaic_meta_repaired",
                "message": "A GD panelist used formulaic facilitator framing instead of contributing as a panelist.",
                "severity": "partial",
            },
            {
                "code": "hidden_speaker_reference",
                "message": "A panelist referenced a speaker who had not visibly spoken.",
                "severity": "invalid",
            },
        ],
        "messages": messages,
    }

    report = await sim.score_session(state)

    assert report.validity_status == "final"
    assert report.score > 0.72
    assert report.score_breakdown["validity_cap"] is None
    assert report.simulator_integrity_notes
    assert any("follow-up question" in note for note in report.simulator_integrity_notes)
    assert any("had not visibly spoken" in note for note in report.simulator_integrity_notes)


@pytest.mark.asyncio
async def test_score_session_scores_only_usable_answers_and_marks_mixed_run_partial(monkeypatch):
    from app.services import simulation_service as sim

    scored_messages = []

    async def model_report(_task_type, _topic, messages, **_kwargs):
        scored_messages.extend(messages)
        return SimulationReport(
            score=0.84,
            summary="The interview had enough learner answers, but simulator repairs capped confidence.",
            strengths=["Concrete backend evidence"],
            improvements=["Further refine the ability to synthesize multiple viewpoints into a cohesive argument"],
            clarity_score=0.86,
            confidence_score=0.82,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)
    messages = _answered_interview_messages(10)
    repair_flags = [
        {
            "code": "interview_missing_evidence_repaired",
            "message": "The assessment model marked the answer scorable without explicit evidence.",
            "severity": "partial",
        },
        {
            "code": "assessment_quality_score_repaired",
            "message": "The assessment model returned an unusable quality score.",
            "severity": "partial",
        },
    ]

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Backend Engineer",
        "scenario_config": {"target_role": "Backend Engineer"},
        "blackboard": {"qualities": [0.72, 0.74, 0.76]},
        "coverage_events": [
            {
                "skill_id": f"skill-{idx % 5}",
                "prompt_id": f"prompt-{idx}",
                "answered": True,
                "score_evidence": 0.72,
            }
            for idx in range(10)
        ],
        "assessment_events": [
            {
                "event_type": "analysis",
                "task_type": TaskType.INTERVIEW_TEST.value,
                "speaker_id": "interviewer",
                "scorable": index < 6,
                "analysis": (
                    {"scorable": True, "quality_score": 0.74}
                    if index < 6
                    else {"scorable": False, "score_excluded_reason": "simulator_integrity_repair"}
                ),
                "content": "Repair-continuation prompt.",
                "validity_flags": [] if index < 6 else repair_flags,
            }
            for index in range(10)
        ],
        "assessment_validity_flags": repair_flags,
        "messages": messages,
    })

    assert report.validity_status == "partial"
    assert report.scorable_turn_count == 6
    assert report.score_breakdown["validity_cap"] == 0.72
    assert sum(1 for message in scored_messages if message.get("role") == "user") == 6
    assert not any("not enough" in caveat.lower() for caveat in report.learner_assessment_caveats)
    assert all("multiple viewpoints" not in item.lower() for item in report.improvements)
    assert any("situation" in item.lower() and "measured result" in item.lower() for item in report.improvements)


@pytest.mark.asyncio
async def test_score_session_does_not_mark_full_max_round_gd_as_unanswered_tail(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.76,
            summary="The discussion had enough evidence.",
            strengths=["Clear stance"],
            improvements=["Add sharper examples"],
            participation_score=0.76,
            relevance_score=0.8,
            language_score=0.74,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)

    messages = []
    for idx in range(10):
        messages.append({
            "role": "assistant",
            "content": f"Panel prompt {idx + 1}",
            "speaker_name": "Data-Driven Analyst",
        })
        messages.append({
            "role": "user",
            "content": f"I answered round {idx + 1} with a concrete remote-work argument.",
            "message_kind": "learner_answer",
        })
    messages.append({
        "role": "assistant",
        "content": "What would have to be true for this to work responsibly?",
        "speaker_name": "Consensus Builder",
    })

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "blackboard": {"turn": sim.MAX_SIM_ROUNDS, "qualities": [0.75] * 10},
        "coverage_events": [
            {"topic_angle": f"angle-{idx}", "answered": True, "score_evidence": 0.75}
            for idx in range(10)
        ],
        "messages": messages,
    })

    assert report.validity_status != "insufficient_evidence"
    assert report.scorable_turn_count == 10
    assert not any("latest interviewer or panel prompt" in caveat for caveat in report.assessment_caveats)


@pytest.mark.asyncio
async def test_score_session_deduplicates_repeated_simulator_caveats(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.73,
            summary="The discussion had enough evidence.",
            strengths=["Clear stance"],
            improvements=["Add sharper examples"],
            participation_score=0.73,
            relevance_score=0.76,
            language_score=0.72,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)

    repeated_message = (
        "The structured assessment turn call failed, so the backend used a single "
        "deterministic repair turn instead of legacy multi-speaker routing."
    )
    messages = []
    for idx in range(5):
        messages.append({
            "role": "assistant",
            "content": f"Panel prompt {idx + 1}",
            "speaker_name": "Data-Driven Analyst",
        })
        messages.append({
            "role": "user",
            "content": f"I answered round {idx + 1} with concrete evidence.",
            "message_kind": "learner_answer",
        })

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "blackboard": {"qualities": [0.75] * 5},
        "coverage_events": [
            {"topic_angle": f"angle-{idx}", "answered": True, "score_evidence": 0.75}
            for idx in range(5)
        ],
        "assessment_validity_flags": [
            {"code": "assessment_turn_call_failed", "message": repeated_message, "severity": "partial"},
            {"code": "assessment_turn_call_failed", "message": repeated_message, "severity": "partial"},
            {"code": "assessment_turn_call_failed", "message": repeated_message, "severity": "partial"},
        ],
        "messages": messages,
    })

    matching = [caveat for caveat in report.assessment_caveats if repeated_message in caveat]
    assert len(matching) == 1


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
async def test_score_session_sanitizes_generic_overpraise_in_report_summary(monkeypatch):
    from app.services import simulation_service as sim

    async def overpraising_model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.82,
            summary=(
                "Strong interview close. Excellent work — you are interview-ready and mastered this. "
                "Use this answer: \"I reduced duplicate charges by 30%.\""
            ),
            strengths=["Clear backend examples"],
            improvements=["Add quantified impact"],
            clarity_score=0.84,
            confidence_score=0.8,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", overpraising_model_report)

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Backend Software Engineer",
        "scenario_config": {"target_role": "Backend Software Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "blackboard": {"qualities": [0.8, 0.82, 0.84, 0.81, 0.83, 0.82]},
        "coverage_events": [
            {
                "skill_id": f"skill-{idx}",
                "prompt_id": f"prompt-{idx}",
                "answered": True,
                "learner_answer_excerpt": "payment retries and idempotency fix",
            }
            for idx in range(6)
        ],
        "messages": _answered_interview_messages(6),
    })
    lowered = report.summary.lower()

    for forbidden in (
        "strong interview close",
        "excellent work",
        "interview-ready",
        "mastered this",
        "use this answer",
        "reduced duplicate charges by 30%",
    ):
        assert forbidden not in lowered
    assert "6 answered turns" in lowered
    assert "coverage breadth" in lowered
    assert "payment retries and idempotency fix" not in lowered


@pytest.mark.asyncio
async def test_planned_interview_coverage_does_not_inflate_from_transcript_fallback(monkeypatch):
    from app.services import simulation_service as sim

    async def generous_model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.91,
            summary="The candidate answered several rounds.",
            strengths=["Clear communication"],
            improvements=["Cover more dimensions"],
            clarity_score=0.9,
            confidence_score=0.88,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", generous_model_report)

    state = {
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Platform Engineer",
        "scenario_config": {"target_role": "Platform Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "assessment_plan": {
            "mode": TaskType.INTERVIEW_TEST.value,
            "role": "Platform Engineer",
            "required_unique_coverage": 4,
        },
        "blackboard": {"qualities": [0.82] * 6},
        "coverage_events": [
            {
                "skill_id": "project_tradeoff",
                "prompt_id": f"tradeoff-{idx}",
                "answered": True,
                "score_evidence": 0.82,
                "learner_answer_excerpt": "I chose reliability over speed.",
            }
            for idx in range(2)
        ],
        "messages": _answered_interview_messages(6),
    }

    report = await sim.score_session(state)

    assert report.scorable_turn_count == 6
    assert report.coverage_map["source"] == "typed_events"
    assert report.coverage_map["event_count"] == 2
    assert report.coverage_map["unique_covered"] == 1
    assert report.validity_status == "partial"
    assert report.score <= 0.72


@pytest.mark.asyncio
async def test_model_classified_text_controls_do_not_count_as_final_evidence(monkeypatch):
    from app.services import simulation_service as sim

    async def should_not_score(*_args, **_kwargs):
        raise AssertionError("control-only interview should remain insufficient evidence")

    monkeypatch.setattr(sim, "evaluate_simulation", should_not_score)

    messages = []
    assessment_events = []
    for idx in range(6):
        messages.extend([
            {"role": "assistant", "content": f"Interview prompt {idx}", "speaker_name": "Interviewer"},
            {"role": "user", "content": "What do you mean by that question?", "message_kind": "learner_answer"},
        ])
        assessment_events.append({
            "event_type": "analysis",
            "task_type": TaskType.INTERVIEW_TEST.value,
            "speaker_id": "interviewer",
            "scorable": False,
            "analysis": {"answer_kind": "clarification_request", "control_intent": "clarify"},
        })

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Platform Engineer",
        "scenario_config": {"target_role": "Platform Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "assessment_plan": {"mode": TaskType.INTERVIEW_TEST.value, "role": "Platform Engineer"},
        "blackboard": {"qualities": []},
        "assessment_events": assessment_events,
        "messages": messages,
    })

    assert report.validity_status == "insufficient_evidence"
    assert report.scorable_turn_count == 0


@pytest.mark.asyncio
async def test_empty_gd_ask_panelist_controls_do_not_count_as_final_evidence(monkeypatch):
    from app.services import simulation_service as sim

    async def should_not_score(*_args, **_kwargs):
        raise AssertionError("floor-routing-only GD controls should remain insufficient evidence")

    monkeypatch.setattr(sim, "evaluate_simulation", should_not_score)

    messages = []
    assessment_events = []
    for idx in range(5):
        messages.extend([
            {"role": "assistant", "content": f"Panel prompt {idx}", "speaker_name": "Data-Driven Analyst"},
            {
                "role": "user",
                "content": "Aggressive Challenger, what is your strongest challenge here?",
                "message_kind": "simulation_control",
                "assessment_action": {"kind": "ask_panelist", "speaker_id": "aggressive_challenger"},
            },
        ])
        assessment_events.append({
            "event_type": "analysis",
            "task_type": TaskType.GD_TEST.value,
            "speaker_id": "aggressive_challenger",
            "scorable": False,
            "analysis": {"client_action": {"kind": "ask_panelist"}},
        })

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "assessment_plan": {"mode": TaskType.GD_TEST.value, "topic": "Should remote work be the default?"},
        "blackboard": {"qualities": []},
        "assessment_events": assessment_events,
        "messages": messages,
    })

    assert report.validity_status == "insufficient_evidence"
    assert report.scorable_turn_count == 0


@pytest.mark.asyncio
async def test_interview_overall_rubric_gap_is_explained(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.52,
            summary="The candidate was clear but narrow.",
            strengths=["Spoke clearly"],
            improvements=["Add stronger evidence"],
            clarity_score=0.93,
            confidence_score=0.87,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for Platform Engineer",
        "scenario_config": {"target_role": "Platform Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "blackboard": {"qualities": [0.55] * 6},
        "coverage_events": [
            {"skill_id": f"skill-{idx}", "prompt_id": f"prompt-{idx}", "answered": True, "score_evidence": 0.55}
            for idx in range(6)
        ],
        "messages": _answered_interview_messages(6),
    })

    assert report.score_explanations
    assert any(
        "overall" in caveat.lower() and "rubric" in caveat.lower()
        for caveat in report.assessment_caveats
    )


def test_assessment_evidence_quotes_are_display_safe():
    from app.services import simulation_service as sim

    state = {
        "assessment_events": [
            {
                "event_type": "analysis",
                "scorable": True,
                "analysis": {
                    "evidence_points": [
                        "This is a deliberately long evidence sentence about a platform migration where the candidate explained ownership, trade-offs, incident recovery, stakeholder communication, measurable reliability impact, and follow-up safeguards in detail."
                    ]
                },
            }
        ],
        "coverage_events": [],
    }

    quotes = sim._assessment_evidence_quotes(state)

    assert quotes == []


def test_simulation_report_exposes_learner_caveats_integrity_notes_and_score_breakdown():
    report = SimulationReport(
        score=0.72,
        summary="Enough evidence for a partial score.",
        strengths=["Clear stance"],
        improvements=["Add sharper evidence"],
        assessment_caveats=["legacy caveat kept for backward compatibility"],
        learner_assessment_caveats=["Coverage was narrow."],
        simulator_integrity_notes=["A panelist response was repaired."],
        score_breakdown={
            "model_score": 0.8,
            "round_quality_mean": 0.6,
            "round_quality_weight": 0.4,
            "final_score": 0.72,
        },
    )

    dumped = report.model_dump()

    assert dumped["learner_assessment_caveats"] == ["Coverage was narrow."]
    assert dumped["simulator_integrity_notes"] == ["A panelist response was repaired."]
    assert dumped["score_breakdown"]["round_quality_weight"] == 0.4
    assert dumped["assessment_caveats"] == ["legacy caveat kept for backward compatibility"]


def test_repeated_unanswered_prompt_counter_ignores_answered_similar_panel_turns():
    from app.services import simulation_service as sim

    messages = []
    for idx in range(5):
        messages.append({
            "role": "assistant",
            "content": "Which metrics prove remote work is working for onboarding and delivery quality?",
            "speaker_name": "Data-Driven Analyst",
        })
        messages.append({
            "role": "user",
            "content": f"My answer {idx} gives onboarding speed, attrition, and delivery quality evidence.",
            "message_kind": "learner_answer",
        })

    assert sim._repeated_unanswered_prompt_count(messages) == 0


def test_coverage_summary_uses_repeated_unanswered_prompt_count_for_report_display():
    from app.services import simulation_service as sim

    messages = []
    for idx in range(6):
        messages.append({
            "role": "assistant",
            "content": "Which metrics prove remote work is working for onboarding and delivery quality?",
            "speaker_name": "Data-Driven Analyst",
        })
        messages.append({
            "role": "user",
            "content": f"My answer {idx} gives onboarding speed, attrition, and delivery quality evidence.",
            "message_kind": "learner_answer",
        })
    state = {
        "assessment_plan": {
            "required_unique_coverage": 3,
        },
        "messages": messages,
        "coverage_events": [
            {"topic_angle": "metrics", "answered": True, "score_evidence": 0.7}
            for _ in range(6)
        ],
    }

    coverage = sim._coverage_summary(state, TaskType.GD_TEST, messages)

    assert coverage["repeated_prompt_count"] == 0


@pytest.mark.asyncio
async def test_score_session_separates_integrity_notes_from_learner_caveats_and_adds_breakdown(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.8,
            summary="The discussion had enough evidence.",
            strengths=["Clear stance"],
            improvements=["Add sharper examples"],
            participation_score=0.8,
            relevance_score=0.82,
            language_score=0.78,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)
    messages = []
    for idx in range(5):
        messages.extend([
            {"role": "assistant", "content": f"Panel prompt {idx}", "speaker_name": "Data-Driven Analyst"},
            {"role": "user", "content": f"I answered round {idx} with evidence.", "message_kind": "learner_answer"},
        ])

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "blackboard": {"qualities": [0.6] * 5},
        "coverage_events": [
            {"topic_angle": f"angle-{idx}", "answered": True, "score_evidence": 0.6}
            for idx in range(2)
        ],
        "assessment_validity_flags": [
            {
                "code": "requested_speaker_mismatch",
                "message": "The learner requested an active panelist, but the model proposed a different next speaker.",
                "severity": "partial",
            }
        ],
        "messages": messages,
    })

    assert report.validity_status == "final"
    assert not report.learner_assessment_caveats
    assert report.simulator_integrity_notes
    assert "different next speaker" in report.simulator_integrity_notes[0]
    assert report.score_breakdown["model_score"] == 0.8
    assert report.score_breakdown["round_quality_mean"] == 0.6
    assert report.score_breakdown["round_quality_weight"] == 0.4
    assert report.score_breakdown["validity_cap"] is None
    assert report.score_breakdown["final_score"] == report.score


@pytest.mark.asyncio
async def test_score_session_normalizes_legacy_tiny_round_quality_values(monkeypatch):
    from app.services import simulation_service as sim

    async def model_report(*_args, **_kwargs):
        return SimulationReport(
            score=0.85,
            summary="The discussion had enough evidence.",
            strengths=["Clear stance"],
            improvements=["Use more industry examples"],
            participation_score=0.85,
            relevance_score=0.9,
            language_score=0.85,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", model_report)
    messages = []
    for idx in range(6):
        messages.extend([
            {"role": "assistant", "content": f"Panel contribution {idx}", "speaker_name": "Data-Driven Analyst"},
            {
                "role": "user",
                "content": f"I answered round {idx} with metrics, trade-offs, and safeguards.",
                "message_kind": "learner_answer",
            },
        ])

    report = await sim.score_session({
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "blackboard": {"qualities": [0.03, 0.03, 0.63, 0.7, 0.3]},
        "coverage_events": [
            {"topic_angle": f"angle-{idx}", "answered": True, "score_evidence": 0.7}
            for idx in range(3)
        ],
        "messages": messages,
    })

    assert report.score_breakdown["round_quality_mean"] == pytest.approx(0.446, abs=0.001)
    assert report.score > 0.65


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
    state.pop("assessment_plan", None)
    state["messages"] = [{"role": "user", "content": "Opening answer."}]

    async for _item in sim.stream_simulation_round(state):
        pass

    assert state["pending_coverage_event"]["skill_id"] == "project_tradeoff"
    assert state["coverage_events"] == []

    state.pop("assessment_plan", None)
    state["messages"].append({"role": "user", "content": "I chose Postgres over NoSQL for transaction safety."})
    async for _item in sim.stream_simulation_round(state):
        pass

    assert len(state["coverage_events"]) == 1
    event = state["coverage_events"][0]
    assert event["skill_id"] == "project_tradeoff"
    assert event["answered"] is True
    assert 0.0 <= event["score_evidence"] <= 1.0
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
async def test_closed_partial_and_insufficient_test_reports_update_learning_profile(monkeypatch):
    from app.services import session_service as svc

    captured: list[dict] = []

    async def fake_record_session_report(self, **kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(
        "app.services.session_service.CareerLearningProfileService.record_session_report",
        fake_record_session_report,
    )

    async def partial_score_session(_state):
        return SimulationReport(
            score=0.61,
            summary="Partial evidence.",
            strengths=["clear stance"],
            improvements=["add evidence"],
            validity_status="partial",
            scorable_turn_count=4,
            learner_assessment_caveats=["Assessment caveat: competency coverage was too narrow."],
        )

    monkeypatch.setattr(svc, "score_session", partial_score_session)
    partial_state = svc._new_state(
        "user-1",
        "session-partial",
        "gd_01_stake_position",
        [],
        task_type=TaskType.GD_TEST.value,
        module_id="group_discussion",
        sim_topic="Should remote work be the default?",
    )
    svc.SessionStore["session-partial"] = partial_state

    await svc.close_session("session-partial")

    async def insufficient_score_session(_state):
        return SimulationReport(
            score=0.0,
            summary="Not enough evidence.",
            strengths=[],
            improvements=["complete more rounds"],
            validity_status="insufficient_evidence",
            scorable_turn_count=1,
            learner_assessment_caveats=["Assessment caveat: not enough answered turns."],
        )

    monkeypatch.setattr(svc, "score_session", insufficient_score_session)
    insufficient_state = svc._new_state(
        "user-1",
        "session-insufficient",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        sim_topic="Mixed interview for Backend Software Engineer",
    )
    svc.SessionStore["session-insufficient"] = insufficient_state

    await svc.close_session("session-insufficient")

    assert [item["report"]["validity_status"] for item in captured] == [
        "partial",
        "insufficient_evidence",
    ]


@pytest.mark.asyncio
async def test_invalid_simulation_report_is_audited_without_adaptive_memory(monkeypatch, store):
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

    adaptive_memory_writes = []

    async def capture_memory(*args, **kwargs):
        adaptive_memory_writes.append((args, kwargs))

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    monkeypatch.setattr(store, "write_memory", capture_memory)

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
    assert store.session_reports[("user-1", "session-invalid")]["status"] == "invalid_simulation"
    assert store.learning_events == []
    assert store.learner_skill_profiles == {}
    assert adaptive_memory_writes == []
