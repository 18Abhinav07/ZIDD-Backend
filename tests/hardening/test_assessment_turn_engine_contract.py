import asyncio

import pytest

from app.content.task_types import TaskType


def _gd_state(personas: list[dict] | None = None) -> dict:
    from app.services import session_service as svc
    from app.services.assessment_plan import ensure_assessment_plan

    roster = personas or [
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "devils_advocate", "name": "Devil's Advocate", "role_type": "debater"},
    ]
    state = svc._new_state(
        "user-1",
        "session-gd",
        "gd_01_take_position",
        [],
        task_type=TaskType.GD_TEST.value,
        module_id="group_discussion",
        sim_topic="Should AI-native service companies be the new big startup pivot?",
        scenario_config={"topic": "Should AI-native service companies be the new big startup pivot?"},
        personas=roster,
    )
    state["messages"] = [
        {
            "role": "assistant",
            "content": "Which metric proves the pivot is more than a slogan?",
            "speaker_id": "data_driven_analyst",
            "speaker_name": "Data-Driven Analyst",
        }
    ]
    state["visible_event_ledger"] = [
        {
            "event_id": "seg_1",
            "role": "assistant",
            "speaker_id": "data_driven_analyst",
            "speaker_name": "Data-Driven Analyst",
            "content": "Which metric proves the pivot is more than a slogan?",
        }
    ]
    state["assessment_plan"] = ensure_assessment_plan(state)
    return state


def _interview_state() -> dict:
    from app.services import session_service as svc
    from app.services.assessment_plan import ensure_assessment_plan

    state = svc._new_state(
        "user-1",
        "session-int",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        sim_topic="Mixed interview for Backend Software Engineer",
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
            "pressure_level": "standard",
        },
        personas=[{"speaker_id": "interviewer", "name": "Interviewer", "role_type": "interviewer"}],
    )
    state["active_interview_probe_prompt"] = "Tell me about a project trade-off."
    state["active_interview_probe_skill_id"] = "project_tradeoff"
    state["active_interview_probe_prompt_id"] = "prompt_tradeoff"
    state["pending_coverage_event"] = {
        "event_id": "1:prompt_tradeoff",
        "task_type": TaskType.INTERVIEW_TEST.value,
        "skill_id": "project_tradeoff",
        "prompt_id": "prompt_tradeoff",
        "answered": False,
    }
    state["messages"] = [
        {"role": "assistant", "content": "Tell me about a project trade-off.", "speaker_name": "Interviewer"},
        {"role": "user", "content": "What do you mean by trade-off?"},
    ]
    state["assessment_plan"] = ensure_assessment_plan(state)
    return state


def _reload_runtime_state(state: dict) -> dict:
    from app.services import session_service as svc

    return svc._hydrate_runtime_state({
        "session_id": state["session_id"],
        "user_id": state["user_id"],
        "current_node": state["competency_node"],
        "module_id": state["module_id"],
        "task_type": state["task_type"],
        "status": state["status"],
        "state_snapshot": svc._runtime_snapshot(state),
        "pending_transition": state.get("pending_node_transition"),
    })


def test_assessment_event_ids_remain_monotonic_beyond_retention_cap_and_reload():
    from app.services.assessment_events import append_assessment_event

    state = _gd_state()
    state["assessment_events"] = []
    event_ids: list[str] = []

    for index in range(105):
        event = append_assessment_event(
            state,
            event_type="analysis",
            task_type=TaskType.GD_TEST.value,
            speaker_id="data_driven_analyst",
            content=f"Assessment {index + 1}",
        )
        event_ids.append(event["event_id"])

    state = _reload_runtime_state(state)
    for index in range(105, 110):
        event = append_assessment_event(
            state,
            event_type="analysis",
            task_type=TaskType.GD_TEST.value,
            speaker_id="data_driven_analyst",
            content=f"Assessment {index + 1}",
        )
        event_ids.append(event["event_id"])

    assert event_ids == [f"assess_{index}" for index in range(1, 111)]
    assert len(state["assessment_events"]) == 100


def test_visible_segment_ids_remain_monotonic_beyond_retention_cap_and_reload():
    from app.services import simulation_service as sim

    state = _gd_state()
    state["visible_event_ledger"] = []
    state["simulation_segments"] = []
    persona = {
        "speaker_id": "data_driven_analyst",
        "name": "Data-Driven Analyst",
    }
    event_ids: list[str] = []

    for index in range(105):
        sim._record_visible_segment(state, persona, f"Segment {index + 1}")
        event_ids.append(state["visible_event_ledger"][-1]["event_id"])

    state = _reload_runtime_state(state)
    for index in range(105, 110):
        sim._record_visible_segment(state, persona, f"Segment {index + 1}")
        event_ids.append(state["visible_event_ledger"][-1]["event_id"])

    assert event_ids == [f"seg_{index}" for index in range(1, 111)]
    assert len(state["visible_event_ledger"]) == 80
    assert len(state["simulation_segments"]) == 80


def test_interview_opening_prompt_makes_selected_role_authoritative():
    from app.ai.prompts import build_opening_prompt
    from app.content.registry import get_node

    prompt = build_opening_prompt(
        get_node("int_01_elevator_pitch"),
        memory_context=[],
        interview_test=True,
        career_context={
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer"],
            "role_family": "software_technical",
        },
        scenario_config={
            "target_role": "Platform Engineer",
            "interview_type": "technical/project",
            "pressure_level": "standard",
        },
    )

    assert "AUTHORITATIVE active interview role: Platform Engineer" in prompt
    assert "Open with Platform Engineer as the focus" in prompt
    assert "Backend Software Engineer" not in prompt.split("AUTHORITATIVE active interview role:", 1)[0]


def test_interview_probe_plan_starts_with_selected_scenario_prompt():
    from app.services import session_service as svc
    from app.services.assessment_plan import ensure_assessment_plan

    state = svc._new_state(
        "user-1",
        "session-int-scenario",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "hr",
            "pressure_level": "standard",
        },
        career_context={"role_family": "software_technical"},
        personas=[{"speaker_id": "interviewer", "name": "Interviewer", "role_type": "interviewer"}],
    )
    state["probe_items"] = [
        {
            "skill_id": "SPECIFICITY_EXAMPLES",
            "prompt": (
                "Walk me through one technical project relevant to Backend Software Engineer. "
                "What was the problem, what did you own, and what changed because of your work?"
            ),
            "aim": "Generic technical fallback.",
        }
    ]

    plan = ensure_assessment_plan(state)
    first_prompt = plan["probe_plan"][0]["prompt"]

    assert "Tell me about yourself" in first_prompt
    assert "3 to 4 sentences" in first_prompt
    assert "technical project" not in first_prompt


def test_interview_probe_plan_excludes_generated_duplicate_for_scenario_node():
    from app.services import session_service as svc
    from app.services.interview_probes import build_interview_probe_plan

    state = svc._new_state(
        "user-1",
        "session-int-elevator-pitch-diversity",
        "int_01_elevator_pitch",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        scenario_config={"target_role": "Backend Software Engineer"},
    )
    state["probe_items"] = [
        {
            "skill_id": "int_01_elevator_pitch",
            "prompt": "Tell me about yourself, focusing on your experience as a Backend Software Engineer.",
            "aim": "Summarizes relevant experience and career goals.",
        },
        {
            "skill_id": "int_02_behavioral_past_performance",
            "prompt": "Describe a time you had to work with a difficult stakeholder.",
            "aim": "Shows stakeholder management.",
        },
    ]

    plan = build_interview_probe_plan(state)

    assert plan[0]["probe_id"] == "scenario_tell_me_about_yourself"
    assert [probe["skill_id"] for probe in plan].count("int_01_elevator_pitch") == 0
    assert plan[1]["skill_id"] == "int_02_behavioral_past_performance"


def test_interview_star_scenario_defers_semantically_repeated_project_probe():
    from app.services import session_service as svc
    from app.services.interview_probes import build_interview_probe_plan

    state = svc._new_state(
        "user-1",
        "session-int-star-diversity",
        "int_04_star_behavioral",
        [],
        task_type=TaskType.INTERVIEW_TEST.value,
        module_id="interview",
        scenario_config={"target_role": "Backend Software Engineer"},
    )

    probe_ids = [probe["probe_id"] for probe in build_interview_probe_plan(state)]

    assert probe_ids[0] == "scenario_star_story"
    assert probe_ids[1] == "debugging_under_pressure"
    assert probe_ids.index("project_ownership_tradeoff") > 2


def test_gd_assessment_plan_projects_scoped_deduped_focus_plan():
    from app.services.assessment_plan import build_assessment_plan

    def focus(skill_id: str, repeat_count: int, **overrides) -> dict:
        item = {
            "focus_id": skill_id,
            "skill_id": skill_id,
            "gap": f"Improve {skill_id}.",
            "repeat_count": repeat_count,
            "latest_evidence": f"Recent evidence for {skill_id}.",
        }
        item.update(overrides)
        return item

    state = {
        "task_type": TaskType.GD_TEST.value,
        "scenario_config": {"topic": "Should remote work be the default?"},
        "career_context": {
            "career_memory_context": {
                "active_gaps": [
                    focus(
                        "int_04_star_behavioral", 500,
                        module_id="interview", task_type="interview_test",
                    ),
                    focus(
                        "gd_01_take_position", 2,
                        focus_id="gd-position",
                        module_id="group_discussion",
                        task_type="gd_prep",
                        private_report={"raw_transcript": "must not leave private context"},
                    ),
                    focus(
                        "gd_01_take_position", 8,
                        focus_id="gd-position-newer", module_id="group_discussion",
                        task_type="gd_test", gap="Lead with a clear stance.",
                    ),
                    focus("rebuttal_quality", 4, focus_id="gd-rebuttal", task_type="gd_test"),
                    focus(
                        "gd_active_listening", 3,
                        focus_id="gd-listening", module_id="interview", task_type="interview_prep",
                    ),
                    focus(
                        "gd_evidence", 1,
                        focus_id="gd-evidence", module_id="group_discussion", task_type="gd_prep",
                    ),
                ],
                "improving_gaps": [
                    focus(
                        "gd_01_take_position", 999,
                        focus_id="gd-position-improving", module_id="group_discussion",
                        task_type="gd_prep",
                    ),
                    focus(
                        "collaborative_synthesis", 100,
                        focus_id="gd-synthesis", module_id="group_discussion",
                    ),
                ],
                "recent_reports": [
                    {"status": "invalid_simulation", "summary": "Raw invalid report content."},
                    {"status": "insufficient_evidence", "summary": "Raw insufficient report content."},
                ],
            }
        },
    }

    plan = build_assessment_plan(state)
    dumped = plan.model_dump(mode="json")
    focus_plan = dumped["focus_plan"]

    assert [item["skill_id"] for item in focus_plan] == [
        "gd_01_take_position",
        "rebuttal_quality",
        "gd_evidence",
        "collaborative_synthesis",
    ]
    assert [item["status"] for item in focus_plan] == [
        "active_gap",
        "active_gap",
        "active_gap",
        "improving",
    ]
    assert focus_plan[0]["focus_id"] == "gd-position-newer"
    assert focus_plan[0]["gap"] == "Lead with a clear stance."
    assert len(focus_plan) == 4
    assert isinstance(plan.focus_plan, tuple)
    assert all(set(item) == {
        "focus_id",
        "skill_id",
        "status",
        "gap",
        "repeat_count",
        "latest_evidence",
    } for item in focus_plan)
    assert "int_04_star_behavioral" not in {item["skill_id"] for item in focus_plan}
    assert "recent_reports" not in dumped
    assert "private_report" not in str(dumped)
    assert "Raw invalid report content" not in str(dumped)
    assert "Raw insufficient report content" not in str(dumped)


def test_gd_focus_id_is_validated_against_immutable_plan():
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services.assessment_policy import authorize_assessment_turn

    state = _gd_state()
    state["assessment_plan"]["focus_plan"] = [{
        "focus_id": "gd-evidence",
        "skill_id": "gd_02_support_with_evidence",
        "status": "active_gap",
        "gap": "Ground claims in evidence.",
        "repeat_count": 2,
        "latest_evidence": "The prior claim had no source.",
    }]
    state["messages"].append({"role": "user", "content": "I would track retention and delivery quality."})

    def authorize(focus_id: str):
        return authorize_assessment_turn(
            state,
            state["assessment_plan"],
            AssessmentTurnCall(
                analysis=GDAnalysis(
                    focus_id=focus_id,
                    quality_score=0.72,
                    evidence_points=["retention and delivery quality"],
                ),
                next_action=NextAction(
                    speaker_id="devils_advocate",
                    action_type="challenge",
                    intent="Challenge whether the metrics capture trust.",
                ),
                visible_response=VisibleResponse(
                    speaker_id="devils_advocate",
                    text="Retention is useful, but it can hide whether new hires build trust quickly.",
                ),
            ),
        )

    assert authorize("gd-evidence").analysis["focus_id"] == "gd-evidence"
    assert authorize("invented-focus").analysis["focus_id"] == ""


def test_assessment_turn_prompt_separates_gd_visible_response_rules():
    from app.ai.prompts import build_assessment_turn_prompt

    gd_prompt = build_assessment_turn_prompt(
        plan={
            "mode": TaskType.GD_TEST.value,
            "topic": "Should remote work be the default?",
            "active_personas": [
                {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
                {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
            ],
        },
        visible_ledger=[],
        transcript="[Learner]: Remote work should be default with guardrails.",
        learner_turn="Remote work should be default with guardrails.",
        turn_context={},
    )
    interview_prompt = build_assessment_turn_prompt(
        plan={
            "mode": TaskType.INTERVIEW_TEST.value,
            "role": "Backend Engineer",
            "active_personas": [
                {"speaker_id": "interviewer", "name": "Interviewer", "role_type": "interviewer"},
            ],
        },
        visible_ledger=[],
        transcript="[Learner]: I built a checkout reliability dashboard.",
        learner_turn="I built a checkout reliability dashboard.",
        turn_context={
            "answered_probe": {"prompt_id": "probe_1"},
            "next_probe": {"prompt_id": "probe_2"},
        },
    )

    assert "GD panelist text must first contribute" in gd_prompt
    assert "must not turn into learner-facing evidence demands" in gd_prompt
    assert "must not ask direct follow-up questions" in gd_prompt
    assert "hand the floor to another panelist" in gd_prompt
    assert "must not introduce external studies, reports, dates, percentages" in gd_prompt
    assert "Interviewer text must ask or clarify one question" not in gd_prompt
    assert "Interviewer text must ask or clarify one question" in interview_prompt
    for prompt in (gd_prompt, interview_prompt):
        assert "warm, sharp personal communication coach" not in prompt
        assert "teacher who remembers a learner" not in prompt
        assert "celebrates small wins" not in prompt


def test_assessment_turn_schema_normalizes_percent_scale_scores():
    from app.ai.schemas import AssessmentTurnCall

    parsed = AssessmentTurnCall.model_validate(
        {
            "analysis": {
                "mode": "gd_test",
                "routing_case": "reply_and_request",
                "scorable": True,
                "requested_next_speaker": "data_driven_analyst",
                "request_confidence": 94,
                "question_to_requested_speaker": "Which metrics matter most?",
                "evidence_points": ["onboarding speed"],
                "quality_score": 38,
            },
            "next_action": {
                "speaker_id": "data_driven_analyst",
                "action_type": "answer_requested_question",
                "intent": "Answer the metrics question.",
            },
            "visible_response": {
                "speaker_id": "data_driven_analyst",
                "text": "The metric angle matters most when it connects onboarding speed with delivery quality.",
            },
        }
    )

    assert parsed.analysis.request_confidence == 0.94
    assert parsed.analysis.quality_score == 0.38

    parsed_ten_point = AssessmentTurnCall.model_validate(
        {
            "analysis": {
                "mode": "gd_test",
                "routing_case": "point_only",
                "scorable": True,
                "evidence_points": ["mentoring metric"],
                "quality_score": 3,
            },
            "next_action": {
                "speaker_id": "data_driven_analyst",
                "action_type": "probe_deeper",
                "intent": "Add a metric contribution.",
            },
            "visible_response": {
                "speaker_id": "data_driven_analyst",
                "text": "The mentoring metric matters because remote-first needs early-career support evidence.",
            },
        }
    )

    assert parsed_ten_point.analysis.quality_score == 0.3


def test_test_mode_persona_requests_are_not_regex_marked_as_control():
    from app.services.simulation_service import is_simulation_control_input

    assert (
        is_simulation_control_input(
            TaskType.GD_TEST.value,
            "I agree with the Data-Driven Analyst. Devil's Advocate, what is the strongest privacy risk?",
        )
        is False
    )
    assert (
        is_simulation_control_input(
            TaskType.INTERVIEW_TEST.value,
            "Can we move to a teammate disagreement?",
        )
        is False
    )


def test_gd_explicit_request_parser_ignores_plain_persona_mentions():
    from app.services.assessment_validity import explicit_requested_speaker_id

    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    plan = state["assessment_plan"]

    assert (
        explicit_requested_speaker_id(
            plan,
            "The metrics can be checked monthly. Aggressive Challenger, what is the strongest risk here?",
        )
        == "aggressive_challenger"
    )
    assert (
        explicit_requested_speaker_id(
            plan,
            "I disagree with Aggressive Challenger risk framing because attrition is the real signal.",
        )
        == ""
    )
    assert (
        explicit_requested_speaker_id(
            plan,
            "I disagree with Aggressive Challenger's risk framing because attrition is the real signal.",
        )
        == ""
    )


@pytest.mark.asyncio
async def test_gd_structured_turn_honors_reply_and_requested_panelist(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="reply_and_request",
                scorable=True,
                addressed_personas=["data_driven_analyst"],
                addressed_event_ids=["seg_1"],
                requested_next_speaker="devils_advocate",
                request_confidence=0.94,
                question_to_requested_speaker="What is the strongest privacy risk here?",
                stance="conditional_support",
                evidence_points=["delivery time reduction", "human review"],
                missing=["named company example"],
                quality_score=0.76,
            ),
            next_action=NextAction(
                speaker_id="devils_advocate",
                action_type="answer_requested_question",
                intent="Challenge privacy and client trust risk from the opposing angle.",
            ),
            visible_response=VisibleResponse(
                speaker_id="devils_advocate",
                text="The strongest privacy risk is that client data leaks into a service workflow before safeguards are proven.",
                move_type="challenge",
                new_contribution="client data leaks into a service workflow",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state()
    state["messages"].append({
        "role": "user",
        "content": "I agree with the Data-Driven Analyst that metrics matter. Devil's Advocate, what is the strongest privacy risk here?",
    })

    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == ["Devil's Advocate"]
    assert "privacy risk" in " ".join(text)
    assert state["assessment_events"][-1]["analysis"]["routing_case"] == "reply_and_request"
    assert state["pending_coverage_event"]["speaker_id"] == "devils_advocate"


@pytest.mark.asyncio
async def test_gd_ask_panelist_quick_action_keeps_substantive_answer_scorable(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="conditional_support",
                evidence_points=["remote expands hiring access", "monthly trust metrics"],
                quality_score=0.74,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="build_on_point",
                intent="Build on the evidence point.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="The evidence angle is useful: hiring reach and trust metrics let the group compare remote work against office visibility.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state()
    state["client_assessment_action"] = {
        "kind": "ask_panelist",
        "speaker_id": "devils_advocate",
        "speaker_name": "Devil's Advocate",
        "source": "quick_action",
    }
    state["messages"].append({
        "role": "user",
        "content": (
            "I support remote work as the default because it expands hiring access "
            "and can be governed with monthly trust metrics. Devil's Advocate, respond."
        ),
    })

    speakers: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)

    event = state["assessment_events"][-1]
    assert speakers == ["Devil's Advocate"]
    assert event["scorable"] is True
    assert event["analysis"]["routing_case"] == "reply_and_request"


@pytest.mark.asyncio
async def test_gd_structured_turn_forces_requested_panelist_when_model_speaker_mismatches(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="reply_and_request",
                scorable=True,
                addressed_personas=["data_driven_analyst"],
                addressed_event_ids=["seg_1"],
                requested_next_speaker="aggressive_challenger",
                request_confidence=0.96,
                question_to_requested_speaker="What is your strongest challenge?",
                stance="conditional_support",
                evidence_points=["human review", "speed"],
                quality_score=0.72,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Ask for metrics again.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="Aggressive Challenger, you raise a useful objection, but I still need metrics.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["messages"].append({
        "role": "user",
        "content": "I agree with the Data-Driven Analyst on metrics. Aggressive Challenger, what is your strongest challenge?",
    })

    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == ["Aggressive Challenger"]
    rendered = " ".join(text)
    assert "Aggressive Challenger, you raise" not in rendered
    assert state["pending_coverage_event"]["speaker_id"] == "aggressive_challenger"
    assert any(flag["code"] == "requested_speaker_mismatch" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_gd_requested_panelist_must_answer_not_echo_question(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="reply_and_request",
                scorable=True,
                requested_next_speaker="aggressive_challenger",
                request_confidence=0.96,
                question_to_requested_speaker="What is the strongest risk in making remote work the default?",
                stance="conditional_support",
                evidence_points=["remote default with guardrails"],
                quality_score=0.72,
            ),
            next_action=NextAction(
                speaker_id="aggressive_challenger",
                action_type="answer_requested_question",
                intent="Answer from the challenger stance.",
            ),
            visible_response=VisibleResponse(
                speaker_id="aggressive_challenger",
                text="What is the strongest risk in making remote work the default that you would address?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["messages"].append({
        "role": "user",
        "content": "I support it with guardrails. Aggressive Challenger, what is the strongest risk in making remote work the default?",
    })

    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert speakers == ["Aggressive Challenger"]
    assert "What is the strongest risk" not in rendered
    assert "push back" in rendered.lower()
    assert "remote" in rendered.lower()
    assert "junior employees" in rendered
    assert "mentoring" in rendered
    assert any(flag["code"] == "requested_speaker_question_echo" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_gd_requested_panelist_must_answer_not_ask_fresh_question(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="reply_and_request",
                scorable=True,
                requested_next_speaker="aggressive_challenger",
                request_confidence=0.95,
                question_to_requested_speaker="What is the strongest risk in making remote work the default?",
                stance="conditional_support",
                evidence_points=["remote default with safeguards"],
                quality_score=0.72,
            ),
            next_action=NextAction(
                speaker_id="aggressive_challenger",
                action_type="answer_requested_question",
                intent="Answer from the challenger stance.",
            ),
            visible_response=VisibleResponse(
                speaker_id="aggressive_challenger",
                text="Can you provide a concrete metric that proves remote work will not hurt collaboration?",
                move_type="challenge",
                new_contribution="concrete metric",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["messages"].append({
        "role": "user",
        "content": "I support it with guardrails. Aggressive Challenger, what is the strongest risk in making remote work the default?",
    })

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert "Can you provide" not in rendered
    assert "push back" in rendered.lower()
    assert "remote" in rendered.lower()
    assert "quieter contributors" in rendered
    assert "mentoring" in rendered


@pytest.mark.asyncio
async def test_structured_gd_authorized_intent_does_not_preserve_interview_followup(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services.assessment_turn import run_assessment_turn

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="reply_and_request",
                scorable=True,
                requested_next_speaker="aggressive_challenger",
                request_confidence=0.95,
                question_to_requested_speaker="What is your strongest challenge?",
                evidence_points=["remote default with safeguards"],
                quality_score=0.72,
            ),
            next_action=NextAction(
                speaker_id="aggressive_challenger",
                action_type="answer_requested_question",
                intent="Ask the learner one clear follow-up about collaboration metrics.",
            ),
            visible_response=VisibleResponse(
                speaker_id="aggressive_challenger",
                text="I would challenge the collaboration risk: remote default needs a clear signal for when trust or decision speed is slipping.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["messages"].append({
        "role": "user",
        "content": "I support it with guardrails. Aggressive Challenger, what is your strongest challenge?",
    })

    authorized = await run_assessment_turn(state)

    intent = authorized.decision.intent.lower()
    assert "ask the learner" not in intent
    assert "follow-up" not in intent
    assert "contribute as aggressive challenger" in intent


@pytest.mark.asyncio
async def test_gd_panelist_substantive_contribution_with_followup_is_preserved(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="conditional_support",
                evidence_points=["remote default with safeguards"],
                quality_score=0.72,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="build_on_point",
                intent="Add a concrete rollout constraint.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text=(
                    "A remote-work pilot needs a named owner and stop rule. What threshold "
                    "would you use?"
                ),
                move_type="challenge",
                new_contribution="A remote-work pilot needs a named owner and stop rule.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["pending_coverage_event"] = {
        "event_id": "gd:previous_formulaic_prompt",
        "task_type": TaskType.GD_TEST.value,
        "skill_id": "gd_discussion",
        "prompt_id": "previous_formulaic_prompt",
        "answered": False,
    }
    state["messages"].append({
        "role": "user",
        "content": "Remote should be default only when onboarding and delivery quality are reviewed.",
    })

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert "A remote-work pilot needs a named owner and stop rule." in rendered
    assert not any(
        flag["code"] == "gd_panelist_ask_only_repaired"
        for flag in state["assessment_validity_flags"]
    )


@pytest.mark.asyncio
async def test_gd_non_moderator_ask_only_visible_response_is_repaired(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="support",
                evidence_points=["remote default with safeguards"],
                quality_score=0.7,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Ask for evidence.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="What metric would prove this policy is working?",
                move_type="evidence",
                new_contribution="metric",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["pending_coverage_event"] = {
        "event_id": "gd:previous_prompt",
        "task_type": TaskType.GD_TEST.value,
        "skill_id": "gd_discussion",
        "prompt_id": "previous_prompt",
        "answered": False,
    }
    state["messages"].append({
        "role": "user",
        "content": "Remote should be default only when onboarding and delivery quality are reviewed.",
    })

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert "What metric would prove" not in rendered
    assert "remote work being the default" in rendered
    assert any(flag["code"] == "gd_panelist_ask_only_repaired" for flag in state["assessment_validity_flags"])
    assert state["assessment_events"][-1]["scorable"] is True
    assert state["assessment_events"][-1]["analysis"]["scorable"] is True
    assert state["coverage_events"][0]["answered"] is True
    assert state["coverage_events"][0]["skip_reason"] is None
    assert state["coverage_events"][0]["skipped_by_user"] is False


@pytest.mark.asyncio
async def test_gd_formulaic_panelist_meta_visible_response_is_repaired(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="conditional_support",
                evidence_points=["remote default with safeguards"],
                quality_score=0.74,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="pivot_topic",
                intent="Shift the angle.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text=(
                    "A new angle is to compare remote-first with hybrid work and ask "
                    "which side has better safeguards."
                ),
                move_type="challenge",
                new_contribution="compare remote-first with hybrid work",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["pending_coverage_event"] = {
        "event_id": "gd:previous_formulaic_prompt",
        "task_type": TaskType.GD_TEST.value,
        "skill_id": "gd_discussion",
        "prompt_id": "previous_formulaic_prompt",
        "answered": False,
    }
    state["messages"].append({
        "role": "user",
        "content": "Remote should be default only when onboarding and delivery quality are reviewed.",
    })

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert "A new angle is" not in rendered
    assert "remote" in rendered.lower()
    assert any(flag["code"] == "gd_panelist_formulaic_meta_repaired" for flag in state["assessment_validity_flags"])
    assert state["assessment_events"][-1]["scorable"] is True
    assert state["assessment_events"][-1]["analysis"]["scorable"] is True
    assert state["coverage_events"][0]["answered"] is True
    assert state["coverage_events"][0]["skip_reason"] is None


@pytest.mark.asyncio
async def test_gd_visible_safety_repair_updates_event_before_scoring(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="support",
                evidence_points=["remote default with safeguards"],
                quality_score=0.8,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Build from the learner's metrics point.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="As Quiet Expert said earlier, mentoring is the central risk; the group should track onboarding speed.",
                move_type="evidence",
                new_contribution="track onboarding speed",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "probing",
        "tension": 0.35,
        "turn": 3,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.62,
        "qualities": [0.62],
        "last_speaker": "moderator_timekeeper",
    }
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["pending_coverage_event"] = {
        "event_id": "gd:previous_prompt",
        "task_type": TaskType.GD_TEST.value,
        "skill_id": "gd_discussion",
        "prompt_id": "previous_prompt",
        "answered": False,
    }
    state["messages"].append({
        "role": "user",
        "content": "I would track onboarding speed, delivery quality, and retention before defending remote as default.",
    })

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    event = state["assessment_events"][-1]
    assert "Quiet Expert said" not in rendered
    assert "Quiet Expert said" not in event["content"]
    assert event["scorable"] is True
    assert event["analysis"]["scorable"] is True
    assert "score_excluded_reason" not in event["analysis"]
    assert event["analysis"]["visible_response_repaired"] is True
    assert "hidden_speaker_reference" in event["analysis"]["visible_response_repair_codes"]
    assert sim._effective_scorable_turn_count(state, state["messages"]) == 1
    assert state["blackboard"]["qualities"] == [0.62, 0.8]
    assert state["coverage_events"][0]["answered"] is True
    assert state["coverage_events"][0]["skip_reason"] is None
    assert state["coverage_events"][0]["skipped_by_user"] is False


@pytest.mark.asyncio
async def test_gd_structured_turn_repairs_unverified_external_claim_before_persisting(
    monkeypatch,
):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="support",
                evidence_points=["supervised AI use"],
                quality_score=0.8,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Add an evidence-oriented discussion contribution.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text=(
                    "A 2023 study on automated grading systems showed teachers spend "
                    "nearly 30% less time on routine marking."
                ),
                move_type="evidence",
                new_contribution="Compare independent teacher review with AI-assisted review.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should AI be used in education?",
        "phase": "probing",
        "tension": 0.35,
        "turn": 3,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.62,
        "qualities": [0.62],
        "last_speaker": "moderator_timekeeper",
    }
    state["sim_topic"] = "Should AI be used in education?"
    state["scenario_config"]["topic"] = "Should AI be used in education?"
    state["assessment_plan"]["topic"] = "Should AI be used in education?"
    state["pending_coverage_event"] = {
        "event_id": "gd:external-claim",
        "task_type": TaskType.GD_TEST.value,
        "skill_id": "gd_discussion",
        "prompt_id": "external-claim",
        "answered": False,
    }
    state["messages"].append({
        "role": "user",
        "content": "AI should help teachers review patterns, but teachers must remain accountable.",
    })

    rendered_parts: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            rendered_parts.append(item)

    rendered = " ".join(rendered_parts)
    event = state["assessment_events"][-1]
    assert "2023" not in rendered
    assert "30%" not in rendered
    assert "2023" not in event["content"]
    assert "30%" not in event["content"]
    assert event["analysis"].get("visible_response_repaired") is True, event
    assert "gd_panelist_unverified_external_claim_repaired" in event["analysis"]["visible_response_repair_codes"]
    assert any(
        flag["code"] == "gd_panelist_unverified_external_claim_repaired"
        for flag in state["assessment_validity_flags"]
    )


@pytest.mark.asyncio
async def test_gd_structured_turn_detects_explicit_panelist_request_when_model_misses_it(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                requested_next_speaker="",
                request_confidence=0.0,
                stance="conditional_support",
                evidence_points=["remote work needs guardrails"],
                quality_score=0.71,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Ask for metrics again.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="Which metrics prove that remote work is working?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"]["topic"] = "Should remote work be the default?"
    state["assessment_plan"]["topic"] = "Should remote work be the default?"
    state["messages"].append({
        "role": "user",
        "content": "The metrics can be checked monthly. Aggressive Challenger, what is the strongest risk in making remote the default?",
    })

    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == ["Aggressive Challenger"]
    assert "remote" in " ".join(text).lower()
    assert state["assessment_events"][-1]["analysis"]["requested_next_speaker"] == "aggressive_challenger"
    assert state["pending_coverage_event"]["speaker_id"] == "aggressive_challenger"


@pytest.mark.asyncio
async def test_gd_structured_call_failure_uses_single_repair_not_legacy_crosstalk(monkeypatch, caplog):
    import logging

    from app.services import simulation_service as sim

    async def broken_turn_model(*_args, **_kwargs):
        raise RuntimeError("structured JSON parse failed")

    async def should_not_use_legacy_director(*_args, **_kwargs):
        raise AssertionError("assessment tests must not fall back to legacy multi-speaker director")

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", broken_turn_model)
    monkeypatch.setattr(sim, "decide_round", should_not_use_legacy_director)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "pressure",
        "tension": 0.6,
        "turn": 4,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.68,
        "qualities": [0.7, 0.66, 0.68],
        "last_speaker": "data_driven_analyst",
    }
    state["messages"].append({
        "role": "user",
        "content": "Aggressive Challenger, what is the strongest risk in making remote work the default?",
    })

    caplog.set_level(logging.WARNING, logger="app.services.simulation_service")
    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == ["Aggressive Challenger"]
    assert len(text) == 1
    assert state["assessment_events"][-1]["scorable"] is False
    assert state["assessment_events"][-1]["analysis"]["requested_next_speaker"] == "aggressive_challenger"
    assert any(flag["code"] == "assessment_turn_call_failed" for flag in state["assessment_validity_flags"])
    assert "Structured assessment turn failed" in caplog.text
    assert "gd_test" in caplog.text


@pytest.mark.asyncio
async def test_gd_structured_turn_timeout_uses_single_repair(monkeypatch):
    from app.services import simulation_service as sim

    async def slow_turn_model(*_args, **_kwargs):
        await asyncio.sleep(1)
        raise AssertionError("slow structured call should have timed out")

    monkeypatch.setattr(sim, "ASSESSMENT_TURN_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", slow_turn_model)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "consensus_builder", "name": "Consensus Builder", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "opening",
        "tension": 0.2,
        "turn": 1,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.62,
        "qualities": [0.62],
        "last_speaker": "data_driven_analyst",
    }
    state["messages"].append({
        "role": "user",
        "content": "Consensus Builder, what compromise would keep remote work as the default without losing trust?",
    })

    async def collect_round():
        speakers: list[str] = []
        text: list[str] = []
        async for item in sim.stream_simulation_round(state):
            if isinstance(item, sim.Speaker):
                speakers.append(item.name)
            elif isinstance(item, str):
                text.append(item)
        return speakers, text

    speakers, text = await asyncio.wait_for(collect_round(), timeout=0.2)

    assert speakers == ["Consensus Builder"]
    assert len(text) == 1
    assert state["assessment_events"][-1]["scorable"] is False
    assert state["assessment_events"][-1]["analysis"]["requested_next_speaker"] == "consensus_builder"
    assert any(flag["code"] == "assessment_turn_call_failed" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_interview_assessment_failure_preserves_substantive_answer_evidence(monkeypatch):
    from app.services import simulation_service as sim

    async def slow_turn_model(*_args, **_kwargs):
        await asyncio.sleep(1)
        raise AssertionError("slow structured call should have timed out")

    monkeypatch.setattr(sim, "ASSESSMENT_TURN_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", slow_turn_model)
    state = _interview_state()
    state["messages"][-1]["content"] = (
        "In a payments platform migration, webhook failures were creating manual reconciliation work. "
        "My task was to make settlement reliable without slowing checkout. I added idempotency keys, "
        "moved reconciliation into a background job, and built dashboards for failed states. The result "
        "was fewer manual escalations, faster recovery, and a cleaner finance audit trail."
    )
    state["blackboard"] = {
        "topic": "Mixed interview for Backend Software Engineer",
        "phase": "probing",
        "tension": 0.3,
        "turn": 1,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.5,
        "qualities": [],
        "last_speaker": "interviewer",
    }

    async def collect_round():
        text: list[str] = []
        async for item in sim.stream_simulation_round(state):
            if isinstance(item, str):
                text.append(item)
        return text

    text = await asyncio.wait_for(collect_round(), timeout=0.2)

    assert text
    event = state["assessment_events"][-1]
    assert event["scorable"] is False
    assert event["analysis"]["scorable"] is False
    assert event["analysis"]["assessment_source"] == "deterministic_fallback"
    assert event["analysis"]["score_excluded_reason"] == "assessment_turn_call_failed"
    assert event["analysis"]["quality_score"] > 0
    assert any(flag["code"] == "assessment_turn_call_failed" for flag in event["validity_flags"])
    coverage = state["coverage_events"][-1]
    assert coverage["answered"] is False
    assert coverage["source"] == "deterministic_fallback"
    assert coverage["integrity_note"] == "assessment_turn_call_failed"
    assert coverage["skip_reason"] == "assessment_turn_call_failed"
    assert coverage["score_evidence"] is None


def test_assessment_turn_timeout_is_bounded_for_live_test_ux():
    from app.services import simulation_service as sim

    assert sim.ASSESSMENT_TURN_TIMEOUT_SECONDS <= 60.0


def test_gd_deterministic_repairs_do_not_leak_remote_work_topic_language():
    from app.services import simulation_service as sim
    from app.services.assessment_policy import _response_text_or_fallback

    forbidden = ("remote", "hiring", "onboarding", "mentorship", "in-person")
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Digital payments",
        "scenario_config": {"topic": "Digital payments"},
    }
    plan = {
        "mode": TaskType.GD_TEST.value,
        "topic": "Digital payments",
        "active_personas": [
            {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
            {"speaker_id": "consensus_builder", "name": "Consensus Builder", "role_type": "debater"},
            {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
            {"speaker_id": "devils_advocate", "name": "Devil's Advocate", "role_type": "debater"},
        ],
    }
    personas = plan["active_personas"]

    generated = []
    for persona in personas:
        generated.append(sim._assessment_repair_text(state, TaskType.GD_TEST, persona))
        generated.append(_response_text_or_fallback(state, plan, persona))

    combined = "\n".join(generated).lower()
    assert "digital payments" in combined
    for word in forbidden:
        assert word not in combined


def test_gd_panel_repeat_fallbacks_are_discussion_contributions_not_interview_questions():
    from app.services import simulation_service as sim
    from app.services.assessment_validity import gd_panelist_ask_only_text
    from app.services.gd_discussion_text import gd_repeat_fallbacks

    persona = {
        "speaker_id": "aggressive_challenger",
        "name": "Aggressive Challenger",
        "role_type": "debater",
    }
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Digital payments",
        "scenario_config": {"topic": "Digital payments"},
    }
    recent: list[set[str]] = []
    used: list[str] = []

    generated = [
        sim._gd_repeat_fallback_text(state, persona, recent, used)
        for _ in range(len(gd_repeat_fallbacks("Digital payments", is_moderator=False)))
    ]

    assert generated
    for text in generated:
        assert "Digital payments" in text
        assert not gd_panelist_ask_only_text(text, persona)
        assert not text.strip().endswith("?")


def test_gd_fallbacks_avoid_formulaic_interview_like_panel_phrasing():
    from app.services import simulation_service as sim
    from app.services.assessment_policy import _response_text_or_fallback
    from app.services.gd_discussion_text import gd_repeat_fallbacks

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
    }
    personas = [
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "consensus_builder", "name": "Consensus Builder", "role_type": "debater"},
        {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
        {"speaker_id": "devils_advocate", "name": "Devil's Advocate", "role_type": "debater"},
    ]
    plan = {
        "mode": TaskType.GD_TEST.value,
        "topic": "Should remote work be the default?",
        "active_personas": personas,
    }
    forbidden = (
        "a new angle on",
        "the strongest middle ground on",
        "the defensible side",
        "your point is well-taken",
        "can you provide",
        "could you provide",
        "what concrete evidence",
        "the floor needs",
        "the trade-off i would separate",
        "the metric lens matters here",
        "a practical compromise on",
    )

    generated = []
    for persona in personas:
        generated.append(sim._assessment_repair_text(state, TaskType.GD_TEST, persona))
        generated.append(_response_text_or_fallback(state, plan, persona))
    generated.extend(gd_repeat_fallbacks("Should remote work be the default?", is_moderator=False))

    combined = "\n".join(generated).lower()
    for phrase in forbidden:
        assert phrase not in combined


def test_gd_remote_work_fallbacks_use_remote_work_discussion_dimensions():
    from app.services import simulation_service as sim
    from app.services.assessment_policy import _response_text_or_fallback
    from app.services.gd_discussion_text import gd_persona_fallback_text

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
    }
    personas = [
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "consensus_builder", "name": "Consensus Builder", "role_type": "debater"},
        {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
        {"speaker_id": "devils_advocate", "name": "Devil's Advocate", "role_type": "debater"},
    ]
    plan = {
        "mode": TaskType.GD_TEST.value,
        "topic": "Should remote work be the default?",
        "active_personas": personas,
    }
    forbidden_generic_rollout_terms = (
        "fraud",
        "fallback access",
        "convenience can hide risk",
        "user education",
    )
    required_remote_work_terms = (
        "mentoring",
        "time-to-productivity",
        "decision latency",
        "documentation",
        "trust",
    )

    generated = []
    for persona in personas:
        generated.append(sim._assessment_repair_text(state, TaskType.GD_TEST, persona))
        generated.append(_response_text_or_fallback(state, plan, persona))
    generated.append(sim._gd_integrity_fallback(state, personas[0]))
    generated.append(sim._gd_repeat_fallback_text(state, personas[0], [], []))

    combined = "\n".join(generated).lower()
    for phrase in forbidden_generic_rollout_terms:
        assert phrase not in combined
    for phrase in required_remote_work_terms:
        assert phrase in combined

    for topic in ("Should companies be remote-first?", "Should distributed work be the norm?"):
        text = gd_persona_fallback_text(topic, "data_driven_analyst", "debater").lower()
        assert "time-to-productivity" in text
        assert "decision latency" in text

    office_payment = gd_persona_fallback_text(
        "Should offices use digital payments for cafeteria purchases?",
        "aggressive_challenger",
        "debater",
    ).lower()
    assert "digital payments" in office_payment
    assert "junior employees" not in office_payment
    assert "mentoring" not in office_payment


def test_gd_four_day_workweek_fallbacks_use_workweek_tradeoffs():
    from app.services.gd_discussion_text import gd_persona_fallback_text

    topic = "Should companies adopt a four-day workweek?"
    generated = {
        speaker_id: gd_persona_fallback_text(topic, speaker_id, "debater").lower()
        for speaker_id in (
            "data_driven_analyst",
            "consensus_builder",
            "devils_advocate",
            "quiet_expert",
        )
    }

    assert "overtime" in generated["data_driven_analyst"]
    assert "pilot" in generated["consensus_builder"]
    assert "compressed" in generated["devils_advocate"]
    assert "handoff" in generated["quiet_expert"]


def test_gd_fallbacks_normalize_should_motion_grammar():
    from app.services import simulation_service as sim
    from app.services.gd_discussion_text import gd_persona_fallback_text

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should companies use AI in hiring?",
        "scenario_config": {"topic": "Should companies use AI in hiring?"},
    }
    persona = {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"}

    generated = [
        gd_persona_fallback_text("Should companies use AI in hiring?", "data_driven_analyst", "debater"),
        gd_persona_fallback_text("Should companies use AI in hiring?", "aggressive_challenger", "debater"),
        gd_persona_fallback_text("Should schools ban phones?", "consensus_builder", "debater"),
        sim._gd_repeat_fallback_text(state, persona, [], []),
    ]
    combined = "\n".join(generated).lower()

    assert "companies using ai in hiring" in combined
    assert "schools banning phones" in combined
    for bad in ("for should", "on should", "challenge should", "push back on should"):
        assert bad not in combined


def test_gd_fallbacks_normalize_should_motion_with_multi_word_subjects():
    from app.services.gd_discussion_text import gd_persona_fallback_text, gd_topic_phrase

    phrase = gd_topic_phrase("Should the government regulate social media?")
    text = gd_persona_fallback_text(
        "Should the government regulate social media?",
        "aggressive_challenger",
        "debater",
    ).lower()

    assert phrase == "the government regulating social media"
    assert "the government regulate social media" not in text
    assert "the government regulating social media" in text


def test_gd_requested_speaker_control_intent_is_discussion_not_interview_followup():
    from app.services import simulation_service as sim

    personas = [
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ]
    state = _gd_state(personas)
    state["messages"].append({
        "role": "user",
        "content": "Aggressive Challenger, what is the strongest risk in making remote work the default?",
    })

    decision = sim._gd_control_decision(
        state,
        personas,
        {"tension": 0.35, "last_quality": 0.5},
    )

    assert decision is not None
    assert decision.next_speaker == "aggressive_challenger"
    intent = decision.intent.lower()
    assert "give your view directly" in intent
    assert "ask the learner" not in intent
    assert "follow-up" not in intent


def test_gd_moderator_request_control_intent_stays_facilitator_only():
    from app.services import simulation_service as sim

    personas = [
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ]
    state = _gd_state(personas)
    state["messages"].append({
        "role": "user",
        "content": "Moderator, what do you think is the right angle now?",
    })

    decision = sim._gd_control_decision(
        state,
        personas,
        {"tension": 0.35, "last_quality": 0.5},
    )

    assert decision is not None
    assert decision.next_speaker == "moderator_timekeeper"
    intent = decision.intent.lower()
    assert "facilitate" in intent
    assert "give your view directly" not in intent
    assert "take one side clearly" not in intent
    assert "taking a side yourself" in intent


def test_legacy_gd_moderator_control_intents_are_not_interview_prompts():
    from app.services import simulation_service as sim

    personas = [
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ]
    cases = [
        "Quiet Expert, what do you think?",
        "I am confused. What is happening in this discussion?",
        "Can we move to a different angle on this topic?",
    ]
    for user_text in cases:
        state = _gd_state(personas)
        state["messages"].append({"role": "user", "content": user_text})
        decision = sim._gd_control_decision(
            state,
            personas,
            {"tension": 0.35, "last_quality": 0.5},
        )
        assert decision is not None
        assert decision.next_speaker == "moderator_timekeeper"
        intent = decision.intent.lower()
        assert "ask the learner" not in intent
        assert "next question" not in intent
        assert "case-study" not in intent
        assert "discussion" in intent or "motion" in intent or "stakeholder" in intent


def test_gd_action_intent_sanitizer_catches_interview_style_variants():
    from app.services.assessment_policy import _safe_gd_action_intent

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
    }
    plan = {
        "mode": TaskType.GD_TEST.value,
        "topic": "Should remote work be the default?",
    }
    persona = {
        "speaker_id": "aggressive_challenger",
        "name": "Aggressive Challenger",
        "role_type": "debater",
    }
    bad_intents = [
        "Question the learner about collaboration metrics.",
        "Prompt the learner for evidence about mentorship.",
        "Challenge the learner to justify the remote-first claim.",
        "Press the learner for proof before moving on.",
    ]

    for bad_intent in bad_intents:
        sanitized = _safe_gd_action_intent(state, plan, persona, bad_intent).lower()
        assert "contribute as aggressive challenger" in sanitized
        assert "question the learner" not in sanitized
        assert "prompt the learner" not in sanitized
        assert "challenge the learner" not in sanitized
        assert "press the learner" not in sanitized

    safe = _safe_gd_action_intent(
        state,
        plan,
        persona,
        "Challenge the policy assumption with one concrete collaboration risk.",
    )
    assert safe == "Challenge the policy assumption with one concrete collaboration risk."


def test_gd_panelist_only_questions_and_floor_control_are_repaired():
    from app.services.assessment_validity import gd_panelist_ask_only_text

    persona = {
        "speaker_id": "aggressive_challenger",
        "name": "Aggressive Challenger",
        "role_type": "debater",
    }

    assert not gd_panelist_ask_only_text(
        (
            "The trust risk is not only productivity; remote defaults can weaken "
            "onboarding and informal escalation. What happens to juniors? Where "
            "do new hires learn judgment without observation?"
        ),
        persona,
    )
    assert not gd_panelist_ask_only_text(
        (
            "The trust risk is not only productivity; remote defaults can weaken "
            "onboarding and informal escalation. What is your strongest safeguard "
            "against juniors becoming invisible?"
        ),
        persona,
    )
    assert not gd_panelist_ask_only_text(
        (
            "The trust risk is not only productivity; remote defaults can weaken "
            "onboarding and informal escalation. What is the one safeguard that "
            "would make that risk acceptable?"
        ),
        persona,
    )
    assert gd_panelist_ask_only_text(
        (
            "The trust risk is not only productivity; remote defaults can weaken "
            "onboarding and informal escalation. Devil's Advocate, how would you "
            "challenge the mentorship claim?"
        ),
        persona,
    )
    assert gd_panelist_ask_only_text(
        "The mentoring risk is real. Quiet Expert, what do you think?",
        persona,
    )
    assert gd_panelist_ask_only_text(
        "That rollout risk matters. What trade-off makes that acceptable?",
        persona,
    )
    assert not gd_panelist_ask_only_text(
        (
            "The mentoring risk is real because junior employees lose informal "
            "learning first. I would make remote default only where manager cadence, "
            "peer review, and escalation data show those weak ties are protected."
        ),
        persona,
    )


def test_gd_panelist_substantive_contribution_with_followup_question_is_not_ask_only():
    from app.services.assessment_validity import gd_panelist_ask_only_text

    debater = {
        "speaker_id": "data_driven_analyst",
        "name": "Data-Driven Analyst",
        "role_type": "debater",
    }
    moderator = {
        "speaker_id": "moderator_timekeeper",
        "name": "Moderator",
        "role_type": "moderator",
    }

    assert not gd_panelist_ask_only_text(
        "A pilot needs a named owner and stop rule. What threshold would you use?",
        debater,
    )
    assert gd_panelist_ask_only_text("What threshold would you use?", debater)
    assert not gd_panelist_ask_only_text("What threshold would you use?", moderator)


def test_gd_panelist_formulaic_meta_framing_is_invalid_but_moderator_pivots_are_allowed():
    from app.services.assessment_validity import gd_panelist_formulaic_meta_text

    debater = {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"}
    moderator = {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"}

    assert gd_panelist_formulaic_meta_text(
        "A new angle is to compare remote work with hybrid work before deciding.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "The strongest middle ground is remote-first with planned office rituals.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "I'll shift the angle. The key trade-off on Should remote work be the default? is speed versus safeguards.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "I agree with the access point, but a new angle is whether remote work weakens mentorship.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "To synthesize the floor, the strongest middle ground is remote-first with planned trust resets.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "The real issue here is whether remote work weakens mentorship.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "A balanced way to see this is remote-first with some office rituals.",
        debater,
    )
    assert gd_panelist_formulaic_meta_text(
        "The practical lens is whether managers can measure trust remotely.",
        debater,
    )
    assert not gd_panelist_formulaic_meta_text(
        "The trade-off I would separate is flexibility versus weak ties: mentoring must be deliberate.",
        debater,
    )
    assert not gd_panelist_formulaic_meta_text(
        "Let's pivot the frame. The motion remains remote work as default; compare access with mentoring risk.",
        moderator,
    )


def test_gd_panelist_handoff_text_is_repaired_without_queueing_floor_control():
    from app.services import simulation_service as sim
    from app.services.assessment_validity import gd_panelist_ask_only_text

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "messages": [],
        "assessment_validity_flags": [],
        "floor_handoff_queue": [],
        "personas": [
            {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
            {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
            {"speaker_id": "moderator", "name": "Moderator", "role_type": "moderator"},
        ],
    }
    persona = state["personas"][0]
    bad_text = "The mentoring risk is real. Quiet Expert should weigh in."

    safe = sim._safe_gd_turn_text(state, persona, bad_text)

    assert gd_panelist_ask_only_text(bad_text, persona)
    assert "remote" in safe.lower()
    assert "quiet expert" not in safe.lower()
    assert not safe.strip().endswith("?")
    assert state["floor_handoff_queue"] == []
    assert state["assessment_validity_flags"][-1]["code"] == "gd_panelist_ask_only_repaired"


def test_gd_panelist_unverified_external_claim_is_repaired_before_visibility():
    from app.services import simulation_service as sim
    from app.services.assessment_validity import (
        gd_panelist_unverified_external_claim,
    )

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should AI be used in education?",
        "scenario_config": {"topic": "Should AI be used in education?"},
        "messages": [],
        "assessment_validity_flags": [],
        "floor_handoff_queue": [],
        "personas": [
            {
                "speaker_id": "data_driven_analyst",
                "name": "Data-Driven Analyst",
                "role_type": "debater",
            }
        ],
    }
    persona = state["personas"][0]
    generated = (
        "A 2023 study on automated grading systems showed teachers spend nearly "
        "30% less time on routine marking."
    )

    assert gd_panelist_unverified_external_claim(generated)
    assert not gd_panelist_unverified_external_claim(
        generated,
        learner_text=generated,
    )
    assert not gd_panelist_unverified_external_claim(
        "We should compare teacher workload before and after a supervised pilot."
    )

    safe = sim._safe_gd_turn_text(state, persona, generated)

    assert safe != generated
    assert "2023" not in safe
    assert "30%" not in safe
    assert state["assessment_validity_flags"][-1]["code"] == (
        "gd_panelist_unverified_external_claim_repaired"
    )


def test_structured_gd_moderator_text_queues_visible_floor_handoff():
    from app.services import simulation_service as sim

    moderator = {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"}
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "assessment_plan": {
            "mode": TaskType.GD_TEST.value,
            "topic": "Should remote work be the default?",
            "active_personas": [
                moderator,
                {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
            ],
        },
        "messages": [],
        "assessment_validity_flags": [],
        "floor_handoff_queue": [],
        "personas": [
            moderator,
            {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
        ],
    }

    safe = sim._safe_gd_turn_text(
        state,
        moderator,
        "Aggressive Challenger, respond to the access argument from the risk side.",
    )

    assert "Aggressive Challenger" in safe
    assert state["floor_handoff_queue"] == [{
        "speaker_id": "aggressive_challenger",
        "speaker_name": "Aggressive Challenger",
        "source_speaker_id": "moderator_timekeeper",
        "reason": "visible_handoff",
    }]


def test_gd_assessment_repair_text_is_participant_contribution_not_tutor_prompt():
    from app.services import simulation_service as sim
    from app.services.assessment_policy import _response_text_or_fallback
    from app.services.assessment_validity import gd_panelist_ask_only_text

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
    }
    debaters = [
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "consensus_builder", "name": "Consensus Builder", "role_type": "debater"},
        {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
        {"speaker_id": "devils_advocate", "name": "Devil's Advocate", "role_type": "debater"},
    ]
    plan = {
        "mode": TaskType.GD_TEST.value,
        "topic": "Should remote work be the default?",
        "active_personas": debaters,
    }

    forbidden_tutor_phrases = (
        "let's test",
        "your point needs",
        "can you",
        "could you",
        "provide evidence",
        "what concrete evidence",
        "ryuk",
    )

    for persona in debaters:
        generated = [
            sim._assessment_repair_text(state, TaskType.GD_TEST, persona),
            _response_text_or_fallback(state, plan, persona),
            sim._gd_integrity_fallback(state, persona),
        ]
        for text in generated:
            normalized = text.lower()
            assert "remote work" in normalized
            assert not gd_panelist_ask_only_text(text, persona)
            assert not text.strip().endswith("?")
            for phrase in forbidden_tutor_phrases:
                assert phrase not in normalized


def test_empty_gd_visible_text_uses_participant_repair_not_interview_prompt():
    from app.services import simulation_service as sim
    from app.services.assessment_validity import gd_panelist_ask_only_text

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Should remote work be the default?",
        "scenario_config": {"topic": "Should remote work be the default?"},
        "messages": [],
        "assessment_validity_flags": [],
        "visible_event_ledger": [],
    }
    persona = {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"}

    text = sim._safe_gd_turn_text(state, persona, "")

    assert "remote work" in text.lower()
    assert "can you say more" not in text.lower()
    assert not text.strip().endswith("?")
    assert not gd_panelist_ask_only_text(text, persona)


@pytest.mark.asyncio
async def test_legacy_gd_empty_moderator_stream_repairs_before_shared_empty_prompt(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services import simulation_service as sim

    async def fake_decide_round(bb, personas, *_args, **_kwargs):
        decision = DirectorDecision(
            action="pivot_topic",
            next_speaker="moderator",
            intent="Refocus the discussion.",
            tension=0.35,
            answer_quality=0.7,
            should_close=False,
        )
        moderator = next(p for p in personas if p["speaker_id"] == "moderator")
        return sim.apply_decision(bb, decision), moderator, decision

    async def empty_persona_stream(*_args, **_kwargs):
        if False:
            yield ""

    monkeypatch.setattr(sim, "decide_round", fake_decide_round)
    monkeypatch.setattr(sim, "stream_persona_turn", empty_persona_stream)

    state = svc._new_state(
        "user-1",
        "session-gd-empty-legacy",
        "gd_01_take_position",
        [],
        task_type=TaskType.GD_TEST.value,
        module_id="group_discussion",
        sim_topic="Should remote work be the default?",
        scenario_config={"topic": "Should remote work be the default?"},
        personas=[
            {"speaker_id": "moderator", "name": "Moderator", "role_type": "moderator"},
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        ],
    )
    state.pop("assessment_plan", None)
    state["messages"] = [{"role": "user", "content": "Remote work should be the default with guardrails."}]

    rendered: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            rendered.append(item)

    text = " ".join(rendered)
    assert "remote work" in text.lower()
    assert "can you say more" not in text.lower()
    assert not text.strip().endswith("?")
    assert any(flag["code"] == "empty_gd_visible_response_repaired" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_score_session_drops_stale_insufficient_turn_caveat_when_backend_evidence_is_sufficient(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.services import simulation_service as sim

    async def fake_evaluate(*_args, **_kwargs):
        return SimulationReport(
            score=0.85,
            summary="Strong full-session interview performance.",
            strengths=["Clear examples"],
            improvements=["Sharpen quantified impact"],
            clarity_score=0.9,
            confidence_score=0.85,
            learner_assessment_caveats=["Insufficient answered turns to fully assess all skills"],
            assessment_caveats=["Insufficient answered turns to fully assess all skills"],
            evidence_quotes=[],
        )

    monkeypatch.setattr("app.services.simulation_service.evaluate_simulation", fake_evaluate)
    state = _interview_state()
    state["messages"] = []
    state["assessment_events"] = []
    for index in range(10):
        prompt = f"Prompt {index}"
        answer = f"Specific backend answer {index} with evidence, trade-off, and result."
        state["messages"].extend([
            {"role": "assistant", "content": prompt, "speaker_name": "Interviewer"},
            {"role": "user", "content": answer},
        ])
        state["assessment_events"].append({
            "event_type": "analysis",
            "scorable": True,
            "speaker_id": "interviewer",
            "analysis": {
                "scorable": True,
                "active_probe_id": f"probe_{index % 8}",
                "skill_id": f"skill_{index % 8}",
                "evidence_points": [answer],
                "quality_score": 0.75,
            },
        })
    state["blackboard"] = {"qualities": [0.75] * 10, "turn": sim.MAX_SIM_ROUNDS}

    report = await sim.score_session(state)

    assert report.scorable_turn_count == 10
    assert report.coverage_map["unique_covered"] >= report.coverage_map["required_unique"]
    assert report.validity_status == "final"
    joined = "\n".join([
        *report.learner_assessment_caveats,
        *report.assessment_caveats,
    ]).lower()
    assert "insufficient answered turns" not in joined


@pytest.mark.asyncio
async def test_gd_max_round_completion_does_not_emit_unanswered_panel_prompt(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="support",
                evidence_points=["remote default with safeguards"],
                quality_score=0.78,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Ask another evidence prompt.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="What additional evidence would prove this?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "closing",
        "tension": 0.55,
        "turn": sim.MAX_SIM_ROUNDS - 1,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.75,
        "qualities": [0.75] * (sim.MAX_SIM_ROUNDS - 1),
        "last_speaker": "aggressive_challenger",
    }
    state["messages"].append({
        "role": "user",
        "content": "My final position is remote by default with safeguards for onboarding, mentorship, and delivery quality.",
    })

    speakers: list[str] = []
    states: list[sim.SimulationState] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, sim.SimulationState):
            states.append(item)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == []
    assert text == []
    assert states and states[-1].should_close is True
    assert state["blackboard"]["turn"] == sim.MAX_SIM_ROUNDS
    assert state.get("pending_coverage_event") is None


@pytest.mark.asyncio
async def test_gd_max_round_repair_failure_closes_without_repair_prompt(monkeypatch):
    from app.services import simulation_service as sim

    async def broken_turn_model(*_args, **_kwargs):
        raise RuntimeError("structured JSON parse failed")

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", broken_turn_model)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "closing",
        "tension": 0.55,
        "turn": sim.MAX_SIM_ROUNDS - 1,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.75,
        "qualities": [0.75] * (sim.MAX_SIM_ROUNDS - 1),
        "last_speaker": "data_driven_analyst",
    }
    state["messages"].append({
        "role": "user",
        "content": "My final position is remote by default with safeguards and measured outcomes.",
    })

    speakers: list[str] = []
    states: list[sim.SimulationState] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, sim.SimulationState):
            states.append(item)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == []
    assert text == []
    assert states and states[-1].should_close is True
    assert state["assessment_events"][-1]["scorable"] is False
    assert state["assessment_validity_flags"][-1]["code"] == "assessment_turn_call_failed"


@pytest.mark.asyncio
async def test_gd_low_confidence_persona_false_positive_is_not_routed(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="request_only",
                scorable=True,
                requested_next_speaker="quiet_expert",
                request_confidence=0.35,
                question_to_requested_speaker="senior expert can review drafts",
                stance="support",
                evidence_points=["senior expert review"],
                quality_score=0.64,
            ),
            next_action=NextAction(
                speaker_id="quiet_expert",
                action_type="answer_requested_question",
                intent="Let Quiet Expert answer.",
            ),
            visible_response=VisibleResponse(
                speaker_id="quiet_expert",
                text="The expert view is that quality review matters.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
    ])
    state["messages"].append({
        "role": "user",
        "content": "A senior expert can review drafts before the client sees them.",
    })

    speakers: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)

    assert speakers
    assert speakers[0] != "Quiet Expert"
    assert any(flag["code"] == "low_confidence_persona_request" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_gd_structured_turn_rotates_repeated_speaker_without_request(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="point_only",
                scorable=True,
                stance="support",
                evidence_points=["clear remote-work guardrails"],
                quality_score=0.7,
            ),
            next_action=NextAction(
                speaker_id="data_driven_analyst",
                action_type="probe_deeper",
                intent="Ask for metrics again.",
            ),
            visible_response=VisibleResponse(
                speaker_id="data_driven_analyst",
                text="Which metrics prove this remote-work policy is working?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state([
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
    ])
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "probing",
        "tension": 0.45,
        "turn": 3,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.7,
        "qualities": [0.7],
        "last_speaker": "data_driven_analyst",
    }
    state["messages"].append({
        "role": "user",
        "content": "Remote should be default only when onboarding and trust metrics are reviewed.",
    })

    speakers: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)

    assert speakers == ["Aggressive Challenger"]
    assert any(flag["code"] == "repeated_speaker_repaired" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_gd_inactive_persona_request_routes_moderator_repair(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, GDAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=GDAnalysis(
                routing_case="request_only",
                scorable=True,
                requested_next_speaker="quiet_expert",
                request_confidence=0.91,
                question_to_requested_speaker="What do you think?",
                quality_score=0.5,
            ),
            next_action=NextAction(
                speaker_id="quiet_expert",
                action_type="answer_requested_question",
                intent="Let Quiet Expert answer.",
            ),
            visible_response=VisibleResponse(
                speaker_id="quiet_expert",
                text="I think the strongest risk is execution.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _gd_state()
    state["messages"].append({"role": "user", "content": "Quiet Expert, what do you think?"})

    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    assert speakers == ["Moderator"]
    rendered = " ".join(text)
    assert "Quiet Expert" in rendered
    assert "Data-Driven Analyst" in rendered
    assert any(flag["code"] == "inactive_requested_speaker" for flag in state["assessment_validity_flags"])


@pytest.mark.asyncio
async def test_interview_clarification_turn_is_not_scored(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, InterviewAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=InterviewAnalysis(
                answer_kind="clarification_request",
                control_intent="clarify",
                scorable=False,
                active_probe_id="prompt_tradeoff",
                criteria_met=[],
                missing_criteria=[],
                follow_up_focus="explain trade-off plainly",
                quality_score=0.0,
            ),
            next_action=NextAction(
                speaker_id="interviewer",
                action_type="clarify_current_probe",
                intent="Restate the active probe in simpler terms.",
            ),
            visible_response=VisibleResponse(
                speaker_id="interviewer",
                text="By trade-off, I mean a choice where you gave up one benefit to protect another. What choice did you make?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _interview_state()

    async for _item in sim.stream_simulation_round(state):
        pass

    assert state["coverage_events"][0]["answered"] is False
    assert state["coverage_events"][0]["skip_reason"] == "simulation_control"
    assert state["assessment_events"][-1]["analysis"]["answer_kind"] == "clarification_request"


@pytest.mark.asyncio
async def test_structured_interview_turn_uses_backend_selected_next_probe(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, InterviewAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(state, plan):
        context = state.get("assessment_turn_context") or {}
        assert context["answered_probe"]["skill_id"] == "project_tradeoff"
        assert context["next_probe"]["skill_id"] == "collaboration"
        return AssessmentTurnCall(
            analysis=InterviewAnalysis(
                answer_kind="answer",
                scorable=True,
                active_probe_id="prompt_tradeoff",
                criteria_met=["tradeoff_named"],
                missing_criteria=["stakeholder_impact"],
                evidence_points=["chose Postgres for transaction safety"],
                quality_score=0.76,
            ),
            next_action=NextAction(
                speaker_id="interviewer",
                action_type="move_to_next_probe",
                intent="Move to the selected collaboration probe.",
            ),
            visible_response=VisibleResponse(
                speaker_id="interviewer",
                text="Can you repeat the same project trade-off and explain the outcome again?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _interview_state()
    state["probe_items"] = [
        {
            "skill_id": "project_tradeoff",
            "prompt_id": "prompt_tradeoff",
            "prompt": "Tell me about a project trade-off.",
            "aim": "Names a trade-off and explains ownership.",
        },
        {
            "skill_id": "collaboration",
            "prompt_id": "prompt_collaboration",
            "prompt": "Tell me about a disagreement with a teammate. What did you say, and what changed?",
            "aim": "Shows collaboration under disagreement.",
        },
    ]
    state["probe_cursor"] = 1
    state["used_probe_prompts"] = ["Tell me about a project trade-off."]
    state["messages"] = [
        {"role": "assistant", "content": "Tell me about a project trade-off.", "speaker_name": "Interviewer"},
        {"role": "user", "content": "I chose Postgres over NoSQL because transaction safety mattered."},
    ]

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert "disagreement with a teammate" in rendered
    assert "repeat the same project trade-off" not in rendered.lower()
    assert state["coverage_events"][0]["skill_id"] == "project_tradeoff"
    assert state["coverage_events"][0]["answered"] is True
    assert state["pending_coverage_event"]["skill_id"] == "collaboration"
    assert state["pending_coverage_event"]["prompt_id"] == "prompt_collaboration"


@pytest.mark.asyncio
async def test_structured_interview_commits_round_state_before_visible_text(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, InterviewAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=InterviewAnalysis(
                answer_kind="answer",
                scorable=True,
                active_probe_id="prompt_tradeoff",
                criteria_met=["tradeoff_named"],
                missing_criteria=[],
                evidence_points=["transaction safety"],
                quality_score=0.78,
            ),
            next_action=NextAction(
                speaker_id="interviewer",
                action_type="move_to_next_probe",
                intent="Move to the next probe.",
            ),
            visible_response=VisibleResponse(
                speaker_id="interviewer",
                text="Tell me about a disagreement with a teammate. What did you say, and what changed?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _interview_state()
    state["blackboard"] = {
        "topic": "Mixed interview for Backend Software Engineer",
        "phase": "probing",
        "tension": 0.35,
        "turn": 4,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.7,
        "qualities": [0.7],
        "last_speaker": "interviewer",
    }
    state["messages"] = [
        {"role": "assistant", "content": "Tell me about a project trade-off.", "speaker_name": "Interviewer"},
        {"role": "user", "content": "I chose Postgres over NoSQL because transaction safety mattered."},
    ]

    saw_visible_text = False
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            assert state["blackboard"]["turn"] == 5
            assert state["assessment_events"][-1]["content"] == item
            saw_visible_text = True
    assert saw_visible_text


@pytest.mark.asyncio
async def test_structured_interview_missing_quality_or_evidence_does_not_poison_score(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, InterviewAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=InterviewAnalysis(
                answer_kind="answer",
                scorable=True,
                active_probe_id="prompt_tradeoff",
                criteria_met=["tradeoff_named"],
                missing_criteria=["impact_metric"],
                quality_score=0.0,
            ),
            next_action=NextAction(
                speaker_id="interviewer",
                action_type="move_to_next_probe",
                intent="Move to the selected collaboration probe.",
            ),
            visible_response=VisibleResponse(
                speaker_id="interviewer",
                text="Tell me about a disagreement with a teammate. What did you say, and what changed?",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _interview_state()
    state["blackboard"] = {
        "topic": "Mixed interview for Backend Software Engineer",
        "phase": "probing",
        "tension": 0.35,
        "turn": 3,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.64,
        "qualities": [0.62, 0.66],
        "last_speaker": "interviewer",
    }
    state["messages"] = [
        {"role": "assistant", "content": "Tell me about a project trade-off.", "speaker_name": "Interviewer"},
        {"role": "user", "content": "I chose asynchronous processing to protect checkout latency and added reconciliation dashboards."},
    ]

    async for _item in sim.stream_simulation_round(state):
        pass

    assert state["blackboard"]["qualities"] == [0.62, 0.66]
    event = state["assessment_events"][-1]
    assert event["scorable"] is False
    assert event["analysis"]["scorable"] is False
    assert event["analysis"]["score_excluded_reason"] == "simulator_integrity_repair"
    assert event["analysis"]["evidence_points"]
    assert event["analysis"]["evidence_source"] == "latest_learner_turn"
    assert state["coverage_events"][0]["answered"] is False
    assert state["coverage_events"][0]["skip_reason"] == "simulator_integrity_repair"
    assert state["coverage_events"][0]["skipped_by_user"] is False
    assert any(
        flag.get("code") == "interview_missing_evidence_repaired"
        for flag in state.get("assessment_validity_flags") or []
    )
    assert any(
        flag.get("code") == "assessment_quality_score_repaired"
        for flag in state.get("assessment_validity_flags") or []
    )


@pytest.mark.asyncio
async def test_structured_interview_turn_replaces_off_plan_visible_question(monkeypatch):
    from app.ai.schemas import AssessmentTurnCall, InterviewAnalysis, NextAction, VisibleResponse
    from app.services import simulation_service as sim

    async def fake_call(*_args, **_kwargs):
        return AssessmentTurnCall(
            analysis=InterviewAnalysis(
                answer_kind="answer",
                scorable=True,
                active_probe_id="prompt_tradeoff",
                criteria_met=["tradeoff_named"],
                missing_criteria=[],
                evidence_points=["transaction safety"],
                quality_score=0.74,
            ),
            next_action=NextAction(
                speaker_id="interviewer",
                action_type="move_to_next_probe",
                intent="Move to the selected collaboration probe.",
            ),
            visible_response=VisibleResponse(
                speaker_id="interviewer",
                text="Tell me about your salary expectation and notice period.",
            ),
        )

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", fake_call)
    state = _interview_state()
    state["probe_items"] = [
        {
            "skill_id": "project_tradeoff",
            "prompt_id": "prompt_tradeoff",
            "prompt": "Tell me about a project trade-off.",
            "aim": "Names a trade-off and explains ownership.",
        },
        {
            "skill_id": "collaboration",
            "prompt_id": "prompt_collaboration",
            "prompt": "Tell me about a disagreement with a teammate. What did you say, and what changed?",
            "aim": "Shows collaboration under disagreement.",
        },
    ]
    state["probe_cursor"] = 1
    state["messages"] = [
        {"role": "assistant", "content": "Tell me about a project trade-off.", "speaker_name": "Interviewer"},
        {"role": "user", "content": "I chose Postgres because transaction safety mattered."},
    ]

    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert "disagreement with a teammate" in rendered
    assert "salary expectation" not in rendered.lower()


@pytest.mark.asyncio
async def test_typed_gd_new_angle_control_is_not_scored_or_sent_to_model(monkeypatch):
    from app.services import simulation_service as sim

    async def should_not_call_model(*_args, **_kwargs):
        raise AssertionError("typed GD controls should be deterministic and should not call the turn model")

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", should_not_call_model)
    state = _gd_state()
    state["client_assessment_action"] = {"kind": "new_angle", "source": "quick_action"}
    state["blackboard"] = {
        "topic": "Should AI-native service companies be the new big startup pivot?",
        "phase": "pressure",
        "tension": 0.72,
        "turn": 4,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.65,
        "qualities": [0.65],
        "last_speaker": "data_driven_analyst",
    }
    state["pending_coverage_event"] = {
        "event_id": "4:prompt_previous",
        "task_type": TaskType.GD_TEST.value,
        "skill_id": "gd_probe_deeper_data_driven_analyst",
        "prompt_id": "prompt_previous",
        "answered": False,
    }
    state["messages"].append({"role": "user", "content": "Can we move to a different angle on this topic?"})

    turns: list[int] = []
    speakers: list[str] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.SimulationState):
            turns.append(item.turn)
        elif isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    assert turns == [4]
    assert speakers == ["Moderator"]
    rendered = " ".join(text)
    assert "hold the motion steady" in rendered.lower()
    assert "stakeholder" in rendered.lower()
    assert "?." not in rendered
    assert "ask one active panelist" not in rendered.lower()
    assert "take one side clearly" not in rendered.lower()
    assert "commit to a side" not in rendered.lower()
    assert state["coverage_events"][0]["answered"] is False
    assert state["coverage_events"][0]["skip_reason"] == "simulation_control"
    assert state["assessment_events"][-1]["scorable"] is False
    assert state["assessment_events"][-1]["analysis"]["control_intent"] == "new_angle"


@pytest.mark.asyncio
async def test_repeated_typed_gd_new_angle_uses_clean_moderator_pivot(monkeypatch):
    from app.services import simulation_service as sim

    async def should_not_call_model(*_args, **_kwargs):
        raise AssertionError("typed GD controls should remain deterministic even when repeated")

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", should_not_call_model)
    from app.services.assessment_plan import ensure_assessment_plan

    state = _gd_state()
    state["sim_topic"] = "Should remote work be the default?"
    state["scenario_config"] = {"topic": "Should remote work be the default?"}
    state["assessment_plan"] = ensure_assessment_plan(state)
    repeated_pivot = (
        "Hold the motion steady: The motion remains: Should remote work be the default? "
        "Put the stakeholder who gains the most beside the stakeholder carrying the biggest "
        "cost, then continue from that tension instead of repeating the same proof demand."
    )
    state["client_assessment_action"] = {"kind": "new_angle", "source": "quick_action"}
    state["blackboard"] = {
        "topic": "Should remote work be the default?",
        "phase": "pressure",
        "tension": 0.72,
        "turn": 5,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.65,
        "qualities": [0.65],
        "last_speaker": "data_driven_analyst",
    }
    state["messages"].append({"role": "assistant", "speaker_name": "Moderator", "content": repeated_pivot})
    state["used_gd_prompts"] = [repeated_pivot]
    state["messages"].append({"role": "user", "content": "Moderator, can we pivot to a different angle on this topic?"})

    text: list[str] = []
    speakers: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.Speaker):
            speakers.append(item.name)
        elif isinstance(item, str):
            text.append(item)

    rendered = " ".join(text)
    assert speakers == ["Moderator"]
    assert "Hold the motion steady:" not in rendered
    assert "Keep the motion visible:" in rendered
    assert "Should remote work be the default?" in rendered
    assert "implementation risk" in rendered
    assert "safeguard" in rendered
    assert "?." not in rendered
    assert "Let's shift" not in rendered
    assert "new angle" not in rendered.lower()
    assert "Which stakeholder is most affected" not in rendered
    assert "ask one active panelist" not in rendered.lower()
    assert "take one side clearly" not in rendered.lower()
    assert "commit to a side" not in rendered.lower()
    assert state["assessment_events"][-1]["scorable"] is False


@pytest.mark.asyncio
async def test_typed_interview_move_on_control_pivots_without_scoring_or_model(monkeypatch):
    from app.services import simulation_service as sim

    async def should_not_call_model(*_args, **_kwargs):
        raise AssertionError("typed interview move-on should be deterministic and should not call the turn model")

    monkeypatch.setattr("app.services.assessment_turn.call_assessment_turn", should_not_call_model)
    state = _interview_state()
    state["client_assessment_action"] = {"kind": "move_on", "source": "quick_action"}
    state["probe_items"] = [
        {"skill_id": "project_tradeoff", "prompt": "Tell me about a project trade-off.", "aim": "names a tradeoff"},
        {"skill_id": "collaboration", "prompt": "Tell me about a disagreement with a teammate.", "aim": "shows collaboration"},
    ]
    state["blackboard"] = {
        "topic": "Mixed interview for Backend Software Engineer",
        "phase": "probing",
        "tension": 0.5,
        "turn": 3,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.6,
        "qualities": [0.6],
        "last_speaker": "interviewer",
    }
    state["messages"][-1] = {"role": "user", "content": "Can we move to a different topic?"}

    turns: list[int] = []
    text: list[str] = []
    async for item in sim.stream_simulation_round(state):
        if isinstance(item, sim.SimulationState):
            turns.append(item.turn)
        elif isinstance(item, str):
            text.append(item)

    assert turns == [3]
    assert state["coverage_events"][0]["answered"] is False
    assert state["coverage_events"][0]["skip_reason"] == "simulation_control"
    assert state["assessment_events"][-1]["scorable"] is False
    assert state["active_interview_probe_prompt"] != "Tell me about a project trade-off."
    assert "different" in " ".join(text).lower() or "move" in " ".join(text).lower()
