from pathlib import Path

from app.content.task_types import TaskType
from app.models import SessionStartRequest
from app.services.career_context import build_career_context
from app.services.simulation_config import resolve_simulation_config


def test_career_context_is_role_aware_and_does_not_publicly_expose_resume_facts():
    profile = {
        "email": "learner@example.com",
        "career_profile": {
            "resume_text": (
                "Email: learner@example.com\n"
                "Phone: +91 98765 43210\n"
                "Built a fraud detection service in Python and React.\n"
                "Debugged production latency issues across APIs."
            ),
            "target_roles": ["Software Engineer", "Backend Developer"],
            "interview_goals": ["project deep dives", "debugging stories"],
            "custom_gd_topics": ["AI and jobs"],
        },
    }

    ctx = build_career_context(profile)

    assert ctx.role_family == "software_technical"
    assert "fraud detection" in " ".join(ctx.resume_facts).lower()
    private_block = ctx.private_prompt_block()
    assert "Software Engineer" in private_block
    assert "fraud detection" in private_block
    assert "learner@example.com" not in private_block
    assert "98765" not in private_block

    public = ctx.public_dict()
    assert public["role_family"] == "software_technical"
    assert public["target_roles"] == ["Software Engineer", "Backend Developer"]
    assert "resume_facts" not in public
    assert "resume_text" not in public


def test_persona_prompt_marks_resume_facts_as_learner_owned_not_persona_memory():
    from app.ai.prompts import build_persona_prompt

    prompt = build_persona_prompt(
        {
            "speaker_id": "quiet_expert",
            "name": "Quiet Expert",
            "role": "Expert",
            "stance": "calm technical reviewer",
        },
        "Ask the learner to define specific rotation goals.",
        "[Learner]: I support short customer-support rotations.",
        {"topic": "Should engineers rotate through support?", "phase": "probing", "tension": 0.5},
        career_context={
            "primary_role": "Backend Software Engineer",
            "resume_facts": [
                "caused a production migration lock during peak traffic",
                "wrote safer migration checklists after rollback",
            ],
        },
    )

    assert "caused a production migration lock during peak traffic" in prompt
    assert "belong to the learner" in prompt
    assert "not to you" in prompt
    assert "never claim them as your own experience" in prompt.lower()


def test_interview_persona_prompt_forbids_model_answers():
    from app.ai.prompts import build_persona_prompt

    prompt = build_persona_prompt(
        {
            "speaker_id": "interviewer",
            "name": "Interviewer",
            "role_type": "interviewer",
            "role": "Mixed interview interviewer for Backend Software Engineer",
        },
        "Ask the learner to explain a PostgreSQL versus Redis trade-off.",
        "[Learner]: I improved checkout reliability.",
        {"topic": "Mixed interview for Backend Software Engineer", "phase": "probing", "tension": 0.6},
    )

    lower = prompt.lower()
    assert "do not provide a model answer" in lower
    assert "do not say \"i would\"" in lower
    assert "as if you were the candidate" in lower


def test_gd_persona_prompt_uses_discussion_not_interview_discipline():
    from app.ai.prompts import build_persona_prompt

    prompt = build_persona_prompt(
        {
            "speaker_id": "aggressive_challenger",
            "name": "Aggressive Challenger",
            "role_type": "debater",
            "role": "risk-focused challenger",
            "stance": "strongly against the motion",
        },
        "Respond directly to the learner's remote-work point.",
        "[Learner]: Remote work should be default with guardrails.",
        {"topic": "Should remote work be the default?", "phase": "pressure", "tension": 0.7},
        task_type=TaskType.GD_TEST,
    )

    lower = prompt.lower()
    assert "live group discussion, not an interview" in lower
    assert "contribute a stance" in lower
    assert "do not ask follow-up questions" in lower
    assert "hand the floor to another panelist" in lower
    assert "interviewer discipline" not in lower
    assert "ask the learner one clear next question" not in lower


def test_gd_moderator_prompt_does_not_promise_inert_immediate_handoff():
    from app.ai.prompts import build_persona_prompt

    prompt = build_persona_prompt(
        {
            "speaker_id": "moderator_timekeeper",
            "name": "Moderator",
            "role_type": "moderator",
            "role": "facilitator",
        },
        "Pivot the discussion to implementation risk.",
        "[Learner]: Remote work should be default with guardrails.",
        {"topic": "Should remote work be the default?", "phase": "pressure", "tension": 0.7},
        task_type=TaskType.GD_TEST,
    )

    lower = prompt.lower()
    assert "live group discussion assessment, not a lesson or interview" in lower
    assert "do not promise an immediate second speaker" in lower
    assert "draw in the right panelist" not in lower


def test_interview_safe_turn_replaces_candidate_style_model_answer():
    from app.services.simulation_service import _safe_interview_turn_text

    selected_probe = (
        "Explain a technical or work decision to a non-technical stakeholder. "
        "How did you make it clear?"
    )
    state = {
        "active_interview_probe_prompt": selected_probe,
        "messages": [
            {
                "role": "assistant",
                "content": "Tell me about a debugging problem under pressure.",
            },
        ],
    }

    generated = (
        "When explaining the trade-offs between PostgreSQL schemas and Redis queues "
        "to non-technical stakeholders, I would start by framing it around key "
        "performance indicators such as transaction speed and reliability. For "
        "example, Redis can offer faster read/write speeds, but PostgreSQL has "
        "stronger persistence guarantees. How would you elaborate on these points?"
    )

    assert _safe_interview_turn_text(state, generated) == selected_probe


def test_career_context_maps_gd_topic_ids_to_human_labels():
    ctx = build_career_context(
        {
            "career_profile": {
                "target_roles": ["Backend Engineer"],
                "gd_topic_ids": ["ai-in-education", "remote-work"],
                "custom_gd_topics": ["AI in hiring"],
            }
        }
    )

    assert ctx.gd_topics == [
        "AI in hiring",
        "AI in education",
        "Remote work culture",
    ]
    prompt_block = ctx.private_prompt_block()
    assert "ai-in-education" not in prompt_block
    assert "remote-work" not in prompt_block


def test_gd_simulation_config_resolves_topic_and_stable_persona_roster():
    ctx = build_career_context(
        {
            "career_profile": {
                "target_roles": ["MBA fresher"],
                "custom_gd_topics": ["Should AI replace campus interviews?"],
            }
        }
    )

    config = resolve_simulation_config(
        TaskType.GD_TEST,
        "gd_10_case_gd_format",
        {
            "topic_mode": "custom",
            "custom_topic": "Should AI replace campus interviews?",
            "environment": "high_pressure_panel",
            "persona_ids": [
                "aggressive_challenger",
                "quiet_expert",
                "devils_advocate",
            ],
        },
        ctx,
    )

    assert config.resolved_topic == "Should AI replace campus interviews?"
    assert config.environment == "high_pressure_panel"
    assert config.public_dict()["personas"] == [
        "Aggressive Challenger",
        "Quiet Expert",
        "Devil's Advocate",
    ]
    assert [p["speaker_id"] for p in config.persona_roster] == [
        "moderator_timekeeper",
        "aggressive_challenger",
        "quiet_expert",
        "devils_advocate",
    ]
    assert config.persona_roster[0]["role_type"] == "moderator"


def test_session_start_accepts_structured_simulation_config():
    req = SessionStartRequest(
        competency_node="interview_10_full_mock",
        test_mode=True,
        simulation_config={
            "interview_type": "technical_project",
            "pressure_level": "high",
            "target_role": "Backend Engineer",
        },
    )

    assert req.simulation_config["target_role"] == "Backend Engineer"


def test_interview_setup_target_role_override_drives_role_family_when_profile_is_empty():
    ctx = build_career_context({"career_profile": {}})

    config = resolve_simulation_config(
        TaskType.INTERVIEW_TEST,
        "int_01_elevator_pitch",
        {
            "interview_type": "technical_project",
            "pressure_level": "standard",
            "target_role": "Software Engineer",
        },
        ctx,
    )

    assert config.target_role == "Software Engineer"
    assert config.role_family == "software_technical"
    assert config.public_dict()["role_family"] == "software_technical"
    assert "software_technical" in config.resolved_topic


def test_interview_probe_fallback_never_says_your_target_role():
    from app.ai import test_gen

    items = test_gen._fallback_items(
        TaskType.INTERVIEW_TEST.value,
        career_context={"role_family": "software_technical"},
        scenario_config={},
    )

    joined = " ".join(item.prompt for item in items).lower()
    assert "your target role" not in joined
    assert "selected role" in joined


def test_postgres_session_and_probe_cache_schema_are_context_aware():
    root = Path(__file__).resolve().parents[2]
    schema = (root / "app/db/schema.sql").read_text()
    repo = (root / "app/db/repo.py").read_text()
    pg_store = (root / "app/storage/pg_store.py").read_text()

    for column in (
        "career_context",
        "scenario_config",
        "persona_roster",
        "context_hash",
    ):
        assert column in schema
        assert column in repo
        assert column in pg_store

    assert "PRIMARY KEY (user_id, task_type, context_hash)" in schema


def test_interview_control_language_is_semantically_analyzed_not_regex_marked():
    from app.services import simulation_service as sim

    assert not sim.is_simulation_control_input(
        TaskType.INTERVIEW_TEST.value,
        "I don't understand what you want from me here.",
    )
    assert not sim.is_simulation_control_input(
        TaskType.INTERVIEW_TEST.value,
        "I already answered that. Please move to a different topic.",
    )
    assert not sim.is_simulation_control_input(
        TaskType.INTERVIEW_TEST.value,
        "I handled this by debugging the queue worker and explaining the trade-off.",
    )
    assert not sim.is_simulation_control_input(
        TaskType.INTERVIEW_TEST.value,
        "I was confused at first, so I clarified the API contract and aligned the team.",
    )
    assert not sim.is_simulation_control_input(
        TaskType.INTERVIEW_TEST.value,
        "We lost messages in the queue, so I added idempotency keys and replay checks.",
    )


def test_gd_speaker_requests_are_semantically_analyzed_not_regex_marked():
    from app.services import simulation_service as sim

    assert not sim.is_simulation_control_input(
        TaskType.GD_TEST.value,
        "Can we hear from the Quiet Expert now?",
    )
    assert not sim.is_simulation_control_input(
        TaskType.GD_TEST.value,
        "Please let the Data-Driven Analyst respond before I continue.",
    )
    assert not sim.is_simulation_control_input(
        TaskType.GD_TEST.value,
        "I agree with the expert because the hiring process needs human review and clear appeal rules.",
    )
    assert not sim.is_simulation_control_input(
        TaskType.GD_TEST.value,
        "The data shows remote work can improve retention when teams set explicit communication norms.",
    )


def test_gd_control_decision_does_not_route_on_argument_mention():
    from app.services import simulation_service as sim

    personas = [
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "quiet_expert", "name": "Quiet Expert", "role_type": "debater"},
    ]
    bb = {"tension": 0.5, "last_quality": 0.6}
    normal_state = {
        "task_type": TaskType.GD_TEST.value,
        "messages": [
            {"role": "user", "content": "I agree with the expert because AI hiring still needs appeal rules."},
        ],
    }
    request_state = {
        "task_type": TaskType.GD_TEST.value,
        "messages": [
            {"role": "user", "content": "Can we hear from the Quiet Expert now?"},
        ],
    }

    assert sim._gd_control_decision(normal_state, personas, bb) is None
    routed = sim._gd_control_decision(request_state, personas, bb)
    assert routed is not None
    assert routed.next_speaker == "quiet_expert"


def test_gd_control_decision_explains_when_requested_persona_is_not_in_panel():
    from app.services import simulation_service as sim

    personas = [
        {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
        {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "role_type": "debater"},
        {"speaker_id": "consensus_builder", "name": "Consensus Builder", "role_type": "debater"},
    ]
    state = {
        "task_type": TaskType.GD_TEST.value,
        "messages": [
            {"role": "user", "content": "Can we hear from the Quiet Expert before I continue?"},
        ],
    }

    decision = sim._gd_control_decision(state, personas, {"tension": 0.6, "last_quality": 0.5})

    assert decision is not None
    assert decision.next_speaker == "moderator_timekeeper"
    assert "quiet expert" in decision.intent.lower()
    assert "not in this panel" in decision.intent.lower()
    assert "aggressive challenger" in decision.intent.lower()
    assert "consensus builder" in decision.intent.lower()


def test_moderator_persona_prompt_does_not_inherit_debater_stance_instructions():
    from app.ai.prompts import build_persona_prompt

    prompt = build_persona_prompt(
        {
            "speaker_id": "moderator_timekeeper",
            "name": "Moderator",
            "role_type": "moderator",
            "role": "neutral facilitator",
        },
        "Explain that the requested speaker is not in the panel and invite the learner to continue.",
        "[Learner]: Can we hear from Quiet Expert?",
        {"topic": "AI in hiring", "phase": "probing", "tension": 0.5},
        roster=[
            {"speaker_id": "aggressive_challenger", "name": "Aggressive Challenger", "stance": "forceful skeptic"},
            {"speaker_id": "consensus_builder", "name": "Consensus Builder", "stance": "collaborative synthesizer"},
        ],
    )

    lower = prompt.lower()
    assert "neutral facilitator" in lower
    assert "hold your stance" not in lower
    assert "push back" not in lower
    assert "do not argue a side" in lower


def test_interview_safe_turn_uses_fresh_fallback_when_selected_probe_is_also_repeated():
    from app.services.simulation_service import _safe_interview_turn_text

    repeated = "Can you explain Singleton and Factory with examples from your backend work?"
    state = {
        "active_interview_probe_prompt": repeated,
        "used_probe_prompts": [repeated],
        "career_context": {"primary_role": "Backend Software Engineer"},
        "messages": [
            {"role": "assistant", "content": repeated},
            {"role": "user", "content": "I already answered Singleton and Factory with payment providers."},
        ],
    }

    generated = "Can you explain Singleton and Factory with examples from your backend work?"
    safe = _safe_interview_turn_text(state, generated)

    assert safe != repeated
    assert "singleton" not in safe.lower()
    assert "factory" not in safe.lower()
    assert "Backend Software Engineer" in safe


def test_interview_control_decision_clarifies_confused_candidate():
    from app.services import simulation_service as sim

    state = {
        "task_type": TaskType.INTERVIEW_TEST.value,
        "messages": [
            {"role": "assistant", "content": "Walk me through a project trade-off."},
            {"role": "user", "content": "I am confused. What are you asking me to do?"},
        ],
        "career_context": {"primary_role": "Backend Engineer"},
    }
    personas = [{"speaker_id": "interviewer", "name": "Interviewer"}]
    decision = sim._interview_control_decision(state, personas, {"tension": 0.7, "last_quality": 0.4})

    assert decision is not None
    assert decision.next_speaker == "interviewer"
    assert "explain" in decision.intent.lower()
    assert "one simple" in decision.intent.lower()
    assert decision.tension < 0.7
