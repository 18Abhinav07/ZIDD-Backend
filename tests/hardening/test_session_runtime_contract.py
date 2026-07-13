import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app

AUTH = {"Authorization": "Bearer test_token"}


async def _collect_stream(stream):
    chunks = []
    async for item in stream:
        chunks.append(item)
    return chunks


def _passing_prep_rubric_result(attempt_type: str = "independent") -> dict:
    return {
        "raw_score": 0.86,
        "effective_score": 0.86,
        "understanding": "Specific, relevant answer.",
        "criteria": [
            {
                "id": "answers_question",
                "met": True,
                "quality": 0.9,
                "evidence_quote": "strong answer",
                "reason": "",
            },
            {
                "id": "specific_detail",
                "met": True,
                "quality": 0.86,
                "evidence_quote": "strong answer",
                "reason": "",
            },
            {
                "id": "pitch_structure",
                "met": True,
                "quality": 0.86,
                "evidence_quote": "strong answer",
                "reason": "",
            },
        ],
        "required_missing": [],
        "blockers": [],
        "strengths": ["specific enough to practise independently"],
        "errors": [],
        "next_focus": "try a harder follow-up",
        "on_task": True,
        "english": True,
        "affect": "confident",
        "goodbye": False,
        "pass_eligible": True,
        "mastery_eligible": False,
        "attempt_type": attempt_type,
    }


@pytest.mark.asyncio
async def test_downward_smoothing_cannot_promote_partial_answer_to_clean_pass(monkeypatch):
    from app.ai.schemas import DiagnosisEval
    from app.graph.nodes import evaluate as eval_node
    from app.services import session_service as svc

    async def partial_answer(*_args, **_kwargs):
        return DiagnosisEval(
            score=0.5,
            understanding="Partial answer.",
            errors=["missing the specific evidence required"],
            strengths=["attempted the skill"],
            next_focus="add a concrete example",
            on_task=True,
            english=True,
        )

    monkeypatch.setattr(eval_node, "evaluate_answer", partial_answer)
    state = svc._new_state("user-1", "clean-pass-state", "gd_08_include_quiet", [])
    state["user_input"] = "Rahul, what do you think?"
    state["last_eval_score"] = 1.0
    state["current_mastery"] = 0.8

    updates = await eval_node.evaluate_node(state)
    state.update(updates)
    svc._update_progress(state)

    assert state["last_eval_score"] == 0.7
    assert state["last_clean_pass_score"] == 0.5
    assert state["clean_streak"] == 0


def test_correct_bridge_fill_does_not_increment_clean_streak_current_hardening_suite():
    from app.graph.nodes import evaluate as eval_node
    from app.services import session_service as svc

    state = svc._new_state("user-1", "bridge-state", "int_06_failure_story", [])
    state["current_mastery"] = 0.2
    state["pending_answer_key"] = {"type": "fill_blank", "answer_key": "owned"}
    state["user_input"] = "owned"

    updates = eval_node._result(
        state,
        eval_node.grade_pending_answer(state["pending_answer_key"], state["user_input"]),
        smooth=False,
        clear_pending=True,
        graded_bridge=True,
    )
    state.update(updates)
    svc._update_progress(state)

    assert state["last_eval_score"] == 0.7
    assert state["last_clean_pass_score"] == 0.7
    assert state["last_graded_bridge"] is True
    assert state["clean_streak"] == 0


def test_gd_prep_generic_quiet_invite_cannot_clean_pass():
    from app.ai.schemas import DiagnosisEval
    from app.graph.nodes import evaluate as eval_node

    diagnosis = DiagnosisEval(
        score=0.9,
        understanding="The learner invited someone.",
        errors=[],
        strengths=["named a participant"],
        next_focus="keep inviting quiet voices",
        on_task=True,
        english=True,
    )

    gated = eval_node._apply_gd_minimum_gate(
        "gd_08_include_quiet",
        "Rahul, what do you think?",
        diagnosis,
    )

    assert gated.score == 0.6
    assert any("too generic" in error for error in gated.errors)


def test_gd_prep_stake_position_question_back_cannot_clean_pass():
    from app.ai.schemas import DiagnosisEval
    from app.graph.nodes import evaluate as eval_node

    diagnosis = DiagnosisEval(
        score=0.85,
        understanding="The learner responded.",
        errors=[],
        strengths=[],
        next_focus="state a position",
        on_task=True,
        english=True,
    )

    gated = eval_node._apply_gd_minimum_gate(
        "gd_01_stake_position",
        "Rahul, what do you think about this topic?",
        diagnosis,
    )

    assert gated.score == 0.6
    assert any("clear committed position" in error for error in gated.errors)


def test_gd_prep_support_requires_concrete_support_marker():
    from app.ai.schemas import DiagnosisEval
    from app.graph.nodes import evaluate as eval_node

    diagnosis = DiagnosisEval(
        score=0.8,
        understanding="The learner repeated a stance.",
        errors=[],
        strengths=["had a stance"],
        next_focus="add evidence",
        on_task=True,
        english=True,
    )

    gated = eval_node._apply_gd_minimum_gate(
        "gd_02_support_with_evidence",
        "I support remote work. It is very good and I feel strongly about it.",
        diagnosis,
    )

    assert gated.score == 0.6
    assert any("concrete support" in error for error in gated.errors)


def test_simulation_message_append_collapses_adjacent_duplicate_persona_turns():
    from app.services import session_service as svc

    state = {
        "messages": [
            {
                "role": "assistant",
                "content": "I would prioritize safeguards before speed.",
                "speaker_id": "consensus_builder",
                "speaker_name": "Consensus Builder",
                "message_kind": "simulation_turn",
            }
        ]
    }

    appended = svc._append_simulation_messages_once(
        state,
        [
            {
                "role": "assistant",
                "content": "I would prioritize safeguards before speed.",
                "speaker_id": "consensus_builder",
                "speaker_name": "Consensus Builder",
                "message_kind": "simulation_turn",
            },
            {
                "role": "assistant",
                "content": "The metric should be decision latency.",
                "speaker_id": "data_driven_analyst",
                "speaker_name": "Data-Driven Analyst",
                "message_kind": "simulation_turn",
            },
        ],
    )

    assert appended == 1
    assert len(state["messages"]) == 2
    assert state["messages"][-1]["speaker_id"] == "data_driven_analyst"


def test_interview_star_complete_answer_gets_clean_pass_floor():
    from app.ai.schemas import DiagnosisEval
    from app.graph.nodes import evaluate as eval_node

    diagnosis = DiagnosisEval(
        score=0.55,
        understanding="The learner gave a concrete project story.",
        errors=["make the transition to result clearer"],
        strengths=["specific backend project"],
        next_focus="connect action to result",
        on_task=True,
        english=True,
    )

    gated = eval_node._apply_interview_minimum_gate(
        "int_04_star_behavioral",
        (
            "In a checkout reliability project, support could see failed payments "
            "but engineering had to manually connect payment events, queue retries, "
            "and API errors. My task was to make the failure flow understandable "
            "for product and support. I mapped the failure states, added retry "
            "and error signals, built a dashboard, and walked support through the "
            "trade-offs using simple diagrams. As a result, support could identify "
            "where checkouts failed faster and engineering reduced repeat incidents."
        ),
        diagnosis,
    )

    assert gated.score == 0.7
    assert any("STAR" in strength for strength in gated.strengths)
    assert "connect action to result" in gated.next_focus


def test_interview_star_partial_action_does_not_get_clean_pass_floor():
    from app.ai.schemas import DiagnosisEval
    from app.graph.nodes import evaluate as eval_node

    diagnosis = DiagnosisEval(
        score=0.55,
        understanding="The learner gave one action detail.",
        errors=["missing situation, task, and result"],
        strengths=["specific action"],
        next_focus="build the full STAR story",
        on_task=True,
        english=True,
    )

    gated = eval_node._apply_interview_minimum_gate(
        "int_04_star_behavioral",
        "I checked regional traffic windows with on-call and used a rollback checklist.",
        diagnosis,
    )

    assert gated.score == 0.55
    assert "missing situation, task, and result" in gated.errors


def test_eval_prompt_threads_career_context_into_interview_grading():
    from app.ai.prompts import build_eval_prompt
    from app.content.registry import get_node

    prompt = build_eval_prompt(
        get_node("int_04_star_behavioral"),
        [],
        "I built a checkout reliability dashboard and explained the trade-offs.",
        career_context={
            "primary_role": "Backend Software Engineer",
            "role_family": "software_technical",
            "resume_facts": ["Built FastAPI checkout reliability dashboards"],
        },
    )

    assert "Backend Software Engineer" in prompt
    assert "FastAPI checkout reliability dashboards" in prompt
    assert "Do not under-score" in prompt


def test_coach_block_warns_against_celebratory_praise_after_weak_answer():
    from app.ai.prompts import _coach_block, coach_view

    coach = coach_view({
        "last_eval_score": 0.4,
        "last_clean_pass_score": 0.4,
        "last_diagnosis": {
            "affect": "neutral",
            "english": True,
            "on_task": True,
        },
    })

    block = _coach_block(coach)

    assert "last answer was weak" in block.lower()
    assert "do not open with celebratory praise" in block.lower()
    assert "correction first" in block.lower()


def test_coach_block_treats_correct_bridge_answer_as_scaffolded_recovery_not_mastery():
    from app.ai.prompts import _coach_block, coach_view

    coach = coach_view({
        "last_eval_score": 0.7,
        "last_clean_pass_score": 0.7,
        "last_graded_bridge": True,
        "scaffold": 2,
        "last_diagnosis": {
            "affect": "confident",
            "english": True,
            "on_task": True,
        },
    })

    block = _coach_block(coach).lower()

    assert "scaffolded bridge answer" in block
    assert "not a full clean pass" in block
    assert "do not frame it as mastery" in block
    assert "do not open with celebratory praise" in block
    assert "do not give a near-complete answer" in block
    assert "scaffold hard" not in block


def test_coaching_stream_sanitizes_celebratory_praise_after_scaffolded_recovery():
    from app.services.session_service import _sanitize_coaching_opening_praise

    text = (
        "Nice touch, Raptor! You nailed the bridge. Now try the same move "
        "without the scaffold."
    )
    state = {
        "task_type": "gd_prep",
        "last_eval_score": 0.7,
        "last_clean_pass_score": 0.7,
        "last_graded_bridge": True,
    }

    sanitized = _sanitize_coaching_opening_praise(text, state, "teach")

    assert not sanitized.lower().startswith((
        "great job",
        "good job",
        "nice",
        "well done",
        "excellent",
        "awesome",
    ))
    assert "not the whole skill yet" in sanitized
    assert "without the scaffold" in sanitized


def test_coaching_stream_sanitizes_great_start_for_borderline_pass():
    from app.services.session_service import _sanitize_coaching_response

    text = (
        "Great start, Raptor QA! You recognized both sides. For example: "
        '"While there is a valid concern that AI may miss context, on balance '
        'its consistency makes it worth using." Now try your own version.'
    )
    state = {
        "task_type": "gd_prep",
        "last_eval_score": 0.7,
        "last_clean_pass_score": 0.7,
        "last_graded_bridge": False,
    }

    sanitized = _sanitize_coaching_response(text, state, "teach")

    assert not sanitized.lower().startswith("great start")
    assert "on the right track" in sanitized.lower()
    assert "for example" not in sanitized.lower()
    assert "while there is a valid concern" not in sanitized.lower()
    assert "your own" in sanitized.lower()


def test_coaching_sanitizer_preserves_ordinary_example_word():
    from app.services.session_service import _sanitize_coaching_response

    text = (
        "Let's focus on crafting a concise pitch by including one concrete "
        "example. Keep it focused on your backend work."
    )
    state = {
        "task_type": "interview_prep",
        "last_eval_score": 0.2,
        "last_clean_pass_score": 0.2,
        "last_graded_bridge": False,
    }

    sanitized = _sanitize_coaching_response(text, state, "teach")

    assert "one concrete example" in sanitized
    assert "concrete Keep it" not in sanitized


def test_coaching_sanitizer_removes_effectively_highlighted_praise_on_weak_turn():
    from app.services.session_service import _sanitize_coaching_response

    state = {
        "task_type": "interview_prep",
        "last_eval_score": 0.5,
        "last_clean_pass_score": 0.5,
        "last_graded_bridge": False,
    }

    sanitized = _sanitize_coaching_response(
        "You effectively highlighted your strength in explaining production "
        "tradeoffs. However, let's refine how you tie this back to your career goal.",
        state,
        "teach",
    )
    pitch_sanitized = _sanitize_coaching_response(
        "Your pitch effectively highlighted your strength in explaining production "
        "tradeoffs. However, let's refine how you tie this back to your career goal.",
        state,
        "teach",
    )
    demonstrates_sanitized = _sanitize_coaching_response(
        "Your pitch effectively demonstrates your ability to turn technical signals "
        "into actionable insights. However, let's refine how you tie this back to your career goal.",
        state,
        "teach",
    )

    assert not sanitized.lower().startswith("you effectively highlighted")
    assert sanitized.startswith("Let's tighten this.")
    assert "tie this back to your career goal" in sanitized
    assert not pitch_sanitized.lower().startswith("your pitch effectively highlighted")
    assert pitch_sanitized.startswith("Let's tighten this.")
    assert not demonstrates_sanitized.lower().startswith("your pitch effectively demonstrates")
    assert demonstrates_sanitized.startswith("Let's tighten this.")


def test_interview_pitch_sanitizer_does_not_repeat_future_goal_gap_when_present():
    from app.services.session_service import _sanitize_coaching_response

    state = {
        "task_type": "interview_prep",
        "competency_node": "int_01_elevator_pitch",
        "last_eval_score": 0.43,
        "last_clean_pass_score": 0.43,
        "last_graded_bridge": False,
        "user_input": (
            "I'm a backend engineer focused on reliable APIs. My next goal is to "
            "own larger distributed systems and mentor engineers on operational discipline."
        ),
    }

    sanitized = _sanitize_coaching_response(
        "Your pitch clearly outlines your current role. However, the future goal "
        "you mentioned needs to be more clearly defined and specific. Task: Revisit "
        "your pitch and refine it so that your future goal is explicitly stated "
        "with a clear description of the role or project you wish to take on next "
        "in your career.",
        state,
        "teach",
    )

    assert "future goal you mentioned needs" not in sanitized.lower()
    assert "revisit your pitch" not in sanitized.lower()
    assert "your direction is present" in sanitized.lower()


def test_coaching_stream_removes_imagine_sample_after_scaffolded_recovery():
    from app.services.session_service import _sanitize_coaching_response

    text = (
        "You did well by sticking to the format. Imagine you improved a system's "
        "performance by optimizing database queries. Instead of saying \"I helped "
        "improve performance,\" describe how query times went from 5 seconds to "
        "under 1 second. Now, apply this approach to the checkout API timeouts."
    )
    state = {
        "task_type": "interview_prep",
        "last_eval_score": 0.7,
        "last_clean_pass_score": 0.7,
        "last_graded_bridge": True,
    }

    sanitized = _sanitize_coaching_response(text, state, "teach")

    assert "imagine you improved" not in sanitized.lower()
    assert "instead of saying" not in sanitized.lower()
    assert "5 seconds" not in sanitized.lower()
    assert "checkout API timeouts" in sanitized


def test_gd_coaching_sanitizer_replaces_generic_topic_drift():
    from app.services.session_service import _sanitize_coaching_response

    text = (
        "You did well by recognizing the drift. Here's how you might do this in a "
        "different context: \"We've wandered a bit - let's get back to our original "
        "discussion on remote work policies. What are your thoughts on implementing "
        "mandatory daily check-ins?\" Now apply this to the main topic."
    )
    state = {
        "task_type": "gd_prep",
        "competency_node": "gd_09_steer_derailed",
        "last_eval_score": 0.7,
        "last_clean_pass_score": 0.7,
        "last_graded_bridge": True,
        "career_context": {
            "gd_topics": ["Should AI replace campus placement interviews in India?"],
        },
    }

    sanitized = _sanitize_coaching_response(text, state, "teach")

    assert "remote work" not in sanitized.lower()
    assert "mandatory daily check-ins" not in sanitized.lower()
    assert "AI replacing campus placement interviews in India" in sanitized


def test_gd_topic_with_profile_forces_full_response_sanitizer():
    from app.services.session_service import _needs_full_coaching_sanitize

    assert _needs_full_coaching_sanitize(
        {
            "task_type": "gd_prep",
            "competency_node": "gd_02_support_with_evidence",
            "last_eval_score": 0.95,
            "career_context": {"gd_topics": ["AI in hiring"]},
        },
        "challenge",
    )


def test_coaching_stream_keeps_challenge_praise_measured_even_for_high_score():
    from app.services.session_service import _sanitize_coaching_opening_praise

    text = "Great job, Raptor! Now let's make this harder."
    state = {
        "task_type": "interview_prep",
        "last_eval_score": 0.92,
        "last_clean_pass_score": 0.92,
        "last_graded_bridge": False,
    }

    sanitized = _sanitize_coaching_opening_praise(text, state, "challenge")

    assert "Great job" not in sanitized
    assert sanitized.startswith("That answer is on the right track.")
    assert "make this harder" in sanitized


def test_coach_block_treats_borderline_pass_as_refinement_not_celebration():
    from app.ai.prompts import _coach_block

    block = _coach_block({"recent_score": 0.7}).lower()

    assert "borderline" in block
    assert "do not open with celebratory praise" in block
    assert "do not give a complete sample answer" in block


@pytest.mark.asyncio
async def test_node_advance_sets_pending_transition_and_blocks_stale_turns():
    from app.services import session_service as svc

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["current_mastery"] = 0.8
    state["last_eval_score"] = 0.8
    state["last_diagnosis"] = {"english": True, "on_task": True, "affect": "confident"}
    state["attempts"] = 2
    state["session_attempts"] = 2
    state["clean_streak"] = 2

    await svc._maybe_advance(state)

    transition = state.get("pending_node_transition")
    assert transition is not None
    assert transition["from_node"] == "int_01_elevator_pitch"
    assert transition["to_node"] == "int_02_strength_with_evidence"
    assert transition["to_title"]
    assert transition["status"] == "awaiting_next_opening"
    assert state["input_allowed"] is False
    assert state["block_reason"] == "awaiting_next_skill"

    with pytest.raises(svc.AwaitingNextSkillError):
        await _collect_stream(svc.run_turn(session_id, "I should not be graded yet."))


@pytest.mark.asyncio
async def test_pending_transition_opening_is_idempotent(monkeypatch, store):
    from app.services import session_service as svc

    async def fake_stream_generation(_spec):
        yield "Next skill opening."

    monkeypatch.setattr(svc, "stream_generation", fake_stream_generation)

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["current_mastery"] = 0.8
    state["last_eval_score"] = 0.8
    state["last_diagnosis"] = {"english": True, "on_task": True, "affect": "confident"}
    state["attempts"] = 2
    state["session_attempts"] = 2
    state["clean_streak"] = 2
    await svc._maybe_advance(state)
    transition_id = state["pending_node_transition"]["transition_id"]

    first = await _collect_stream(svc.stream_opening(session_id, transition_id=transition_id))
    second = await _collect_stream(svc.stream_opening(session_id, transition_id=transition_id))

    assistant_messages = [
        m for m in state["messages"]
        if m.get("role") == "assistant" and m.get("transition_id") == transition_id
    ]
    assert first == ["Next skill opening."]
    assert second == ["Next skill opening."]
    assert len(assistant_messages) == 1
    assert len(store.node_attempts) == 1
    assert store.node_attempts[session_id]["competency_node"] == "int_02_strength_with_evidence"
    assert state["pending_node_transition"] is None
    assert state["input_allowed"] is True
    assert state["block_reason"] is None


@pytest.mark.asyncio
async def test_opening_fallback_does_not_praise_without_model_text(monkeypatch):
    from app.services import session_service as svc

    async def empty_stream_generation(_spec):
        if False:
            yield ""

    monkeypatch.setattr(svc, "stream_generation", empty_stream_generation)

    session_id, _state = await svc.start_session("user-1", "int_01_elevator_pitch")
    chunks = await _collect_stream(svc.stream_opening(session_id))
    text = "".join(chunks).lower()

    assert "nice work" not in text
    assert "great job" not in text
    assert "practice" in text


@pytest.mark.asyncio
async def test_opening_stream_times_out_to_fallback_when_model_hangs(monkeypatch):
    from app.services import session_service as svc

    async def hung_stream_generation(_spec):
        await asyncio.sleep(1)
        if False:
            yield "never"

    monkeypatch.setattr(svc, "OPENING_STREAM_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr(svc, "stream_generation", hung_stream_generation)

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    chunks = await asyncio.wait_for(
        _collect_stream(svc.stream_opening(session_id)),
        timeout=0.2,
    )
    text = "".join(chunks).lower()

    assert "practice" in text
    assert state["opening_streamed"] is True


@pytest.mark.asyncio
async def test_interview_test_opening_fallback_asks_real_first_question(monkeypatch):
    from app.services import session_service as svc

    async def empty_stream_generation(_spec):
        if False:
            yield ""

    async def no_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "stream_generation", empty_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", no_probe_items)

    session_id, _state = await svc.start_session(
        "user-1",
        "int_04_star_behavioral",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "technical_project",
            "pressure": "standard",
        },
    )
    chunks = await _collect_stream(svc.stream_opening(session_id))
    text = "".join(chunks).lower()

    assert "backend software engineer" in text
    assert "star" in text
    assert "what was the situation" in text
    assert "what changed as a result" in text


@pytest.mark.asyncio
async def test_interview_test_tell_me_about_yourself_opening_uses_scenario_probe(monkeypatch):
    from app.services import session_service as svc

    async def empty_stream_generation(_spec):
        if False:
            yield ""

    async def technical_probe_items(*_args, **_kwargs):
        return [
            {
                "skill_id": "SPECIFICITY_EXAMPLES",
                "prompt": (
                    "Walk me through one technical project relevant to Backend Software Engineer. "
                    "What was the problem, what did you own, and what changed because of your work?"
                ),
                "aim": "Generic technical fallback.",
            }
        ]

    monkeypatch.setattr(svc, "stream_generation", empty_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", technical_probe_items)

    session_id, _state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "hr",
            "pressure": "standard",
        },
    )
    chunks = await _collect_stream(svc.stream_opening(session_id))
    text = "".join(chunks)

    assert "Tell me about yourself" in text
    assert "current role" in text
    assert "direction you want next" in text
    assert "technical project" not in text


@pytest.mark.asyncio
async def test_initial_opening_replay_without_committed_cache_does_not_append_duplicate(monkeypatch):
    from app.services import session_service as svc

    async def empty_stream_generation(_spec):
        if False:
            yield ""

    async def no_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "stream_generation", empty_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", no_probe_items)

    session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "hr",
            "pressure": "standard",
        },
    )

    first = await _collect_stream(svc.stream_opening(session_id))
    state["committed_openings"] = {}
    state["opening_streamed"] = False
    second = await _collect_stream(svc.stream_opening(session_id))

    opening_messages = [
        message
        for message in state["messages"]
        if message.get("role") == "assistant" and message.get("message_kind") == "opening"
    ]
    assert first == second
    assert len(opening_messages) == 1


@pytest.mark.asyncio
async def test_advancing_turn_progress_update_uses_completed_node_values(monkeypatch):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.9,
                "last_clean_pass_score": 0.9,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "last_rubric_result": _passing_prep_rubric_result("transfer"),
                "current_mastery": 0.8,
                "attempts": 5,
            }

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["clean_streak"] = 1
    state["meaningful_attempts"] = 4
    state["independent_passes"] = 2
    state["best_independent_score"] = 0.82
    state["core_qualified"] = True
    state["core_qualification_turn_id"] = "turn-core-2"

    chunks = await _collect_stream(svc.run_turn(session_id, "A strong answer."))
    progress = [item for item in chunks if isinstance(item, svc.ProgressUpdate)]

    assert len(progress) == 1
    assert progress[0].node_id == "int_01_elevator_pitch"
    assert progress[0].mastery == 0.8
    assert progress[0].readiness_score == 0.86
    assert progress[0].clean_streak == 2
    assert progress[0].attempts == 5
    assert state["competency_node"] == "int_02_strength_with_evidence"
    transition = state["pending_node_transition"]
    assert transition["from_readiness_score"] == 0.86
    assert transition["from_mastery"] == 0.8
    assert transition["from_clean_streak"] == 2
    assert transition["from_attempts"] == 5


@pytest.mark.asyncio
async def test_new_prep_session_restores_durable_career_progress_counters(store):
    from app.services import session_service as svc

    await store.ensure_profile("user-1")
    store.mastery[("user-1", "int_03_weakness_framing")] = {
        "user_id": "user-1",
        "node_id": "int_03_weakness_framing",
        "ema": 0.78,
        "best_ema": 0.82,
        "attempts": 12,
        "node_completed": False,
        "node_mastered": False,
        "display_status": "in_progress",
        "best_independent_score": 0.86,
        "independent_passes": 4,
        "transfer_passes": 1,
        "pressure_passes": 0,
        "scaffold_successes": 2,
        "meaningful_attempts": 12,
        "readiness_score": 0.84,
        "last_gap": "Defend the tradeoff under pressure.",
        "mastery_evidence": [{"attempt_type": "transfer", "score": 0.84}],
    }

    _session_id, state = await svc.start_session(
        "user-1", "int_03_weakness_framing", reattempt=True
    )

    assert state["attempts"] == 12
    assert state["independent_passes"] == 4
    assert state["transfer_passes"] == 1
    assert state["pressure_passes"] == 0
    assert state["scaffold_successes"] == 2
    assert state["meaningful_attempts"] == 12
    assert state["readiness_score"] == 0.84
    assert state["last_gap"] == "Defend the tradeoff under pressure."


@pytest.mark.asyncio
async def test_same_node_generation_failure_persists_fallback_without_progress(monkeypatch, store):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.8,
                "last_clean_pass_score": 0.8,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "current_mastery": 0.24,
                "attempts": 1,
                "session_attempts": 1,
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test-model",
                    prompt="coach the learner",
                    kind="coach",
                ),
            }

    async def failing_generation(_spec):
        raise RuntimeError("model unavailable")
        yield "never"

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", failing_generation)
    await store.ensure_profile("user-1")

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1

    chunks = await _collect_stream(svc.run_turn(session_id, "A solid answer."))

    assert any("try that once more" in item for item in chunks if isinstance(item, str))
    assert not any(isinstance(item, svc.ProgressUpdate) for item in chunks)
    assert state["competency_node"] == "int_01_elevator_pitch"
    assert state["current_mastery"] == 0.0
    assert state["attempts"] == 0
    assert state["clean_streak"] == 0
    assert state["turn_count"] == 2
    assert any(
        m.get("role") == "assistant" and "try that once more" in m.get("content", "")
        for m in state["messages"]
    )
    assert ("user-1", "int_01_elevator_pitch") not in store.mastery


@pytest.mark.asyncio
async def test_int01_visible_task_commits_marker_once_and_drives_next_evaluation(monkeypatch, store):
    from app.services import session_service as svc
    from app.services.rubric_engine import build_evaluation_packet

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.86,
                "last_clean_pass_score": 0.86,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                    "last_rubric_result": _passing_prep_rubric_result("independent"),
                    "tutor_turn_plan": {
                        "verdict": "independent_pass",
                        "next_action": "request_transfer",
                        "tone_policy": "measured_forward",
                        "allowed_praise": False,
                        "focus": "use a different achievement for a different audience",
                        "stage": "challenge",
                    },
                    "current_mastery": 0.3,
                "attempts": 1,
                "session_attempts": 1,
                "active_prompt_attempt_type": None,
                "pending_prompt_attempt_type": "transfer",
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test-model",
                    prompt="ask the transfer task",
                    kind="challenge",
                ),
            }

    marker_during_generation = []

    async def generated_response(_spec):
        marker_during_generation.append((
            state.get("active_prompt_attempt_type"),
            state.get("pending_prompt_attempt_type"),
        ))
        yield "You need to clarify the impact and refine your pitch."

    calls = {"progress": 0, "mastery": 0}
    original_update_progress = svc._update_progress
    original_persist_mastery = svc._persist_mastery

    def counted_update_progress(current_state):
        calls["progress"] += 1
        original_update_progress(current_state)

    async def counted_persist_mastery(current_state):
        calls["mastery"] += 1
        await original_persist_mastery(current_state)

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", generated_response)
    monkeypatch.setattr(svc, "_update_progress", counted_update_progress)
    monkeypatch.setattr(svc, "_persist_mastery", counted_persist_mastery)
    await store.ensure_profile("user-1")

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state.update({
        "opening_streamed": True,
        "turn_count": 1,
        "active_prompt_attempt_type": "independent",
        "independent_passes": 1,
    })

    chunks = await _collect_stream(
        svc.run_turn(session_id, "A complete role, proof, and direction pitch.", "turn-int01")
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("int_01_elevator_pitch"),
        "My transfer answer.",
    )

    assert marker_during_generation == [("independent", "transfer")]
    assert state["pending_prompt_attempt_type"] is None
    assert state["active_prompt_attempt_type"] == "transfer"
    assert packet.attempt_type == "transfer"
    assert state["independent_passes"] == 2
    assert state["readiness_score"] == 0.86
    assert calls == {"progress": 1, "mastery": 1}
    assert len([item for item in chunks if isinstance(item, svc.ProgressUpdate)]) == 1


@pytest.mark.asyncio
async def test_committed_prompt_marker_persists_reload_but_pending_marker_is_transient(store):
    from app.services import session_service as svc

    session_id = "int01-marker-reload"
    state = svc._new_state(
        "user-1",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["active_prompt_attempt_type"] = "pressure"
    state["pending_prompt_attempt_type"] = "transfer"
    svc.SessionStore[session_id] = state

    await svc._persist_runtime_state(state)
    svc.SessionStore.pop(session_id, None)
    restored = await svc.get_session_state(session_id)

    assert restored is not None
    assert restored["active_prompt_attempt_type"] == "pressure"
    assert restored["pending_prompt_attempt_type"] is None


@pytest.mark.asyncio
async def test_int01_generation_failure_preserves_previous_marker_for_uncounted_resubmit(
    monkeypatch, store
):
    from app.services import session_service as svc
    from app.services.rubric_engine import build_evaluation_packet

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.86,
                "last_clean_pass_score": 0.86,
                "last_diagnosis": {"english": True, "on_task": True, "affect": "confident"},
                "last_rubric_result": _passing_prep_rubric_result("independent"),
                "current_mastery": 0.3,
                "attempts": 1,
                "session_attempts": 1,
                "active_prompt_attempt_type": None,
                "pending_prompt_attempt_type": "transfer",
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test-model",
                    prompt="ask the transfer task",
                    kind="challenge",
                ),
            }

    marker_during_generation = []

    async def failing_generation(_spec):
        marker_during_generation.append((
            state.get("active_prompt_attempt_type"),
            state.get("pending_prompt_attempt_type"),
        ))
        raise RuntimeError("model unavailable")
        yield "never"

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", failing_generation)
    await store.ensure_profile("user-1")

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state.update({
        "opening_streamed": True,
        "turn_count": 1,
        "active_prompt_attempt_type": "independent",
        "independent_passes": 1,
    })

    chunks = await _collect_stream(
        svc.run_turn(session_id, "A complete role, proof, and direction pitch.", "turn-fail")
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("int_01_elevator_pitch"),
        "Resubmitted answer.",
    )

    assert any("try that once more" in item for item in chunks if isinstance(item, str))
    assert marker_during_generation == [("independent", "transfer")]
    assert state["active_prompt_attempt_type"] == "independent"
    assert state["pending_prompt_attempt_type"] is None
    assert packet.attempt_type == "independent"
    assert state["independent_passes"] == 1
    assert state["readiness_score"] == 0.0
    assert ("user-1", "int_01_elevator_pitch") not in store.mastery


@pytest.mark.asyncio
async def test_incomplete_career_coach_text_is_repaired_before_persist(monkeypatch, store):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.82,
                "last_clean_pass_score": 0.82,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "last_rubric_result": _passing_prep_rubric_result("independent"),
                "current_mastery": 0.72,
                "attempts": 5,
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test-model",
                    prompt="coach the learner",
                    kind="teach",
                ),
            }

    async def incomplete_generation(_spec):
        yield "Your approach is solid. For instance,"

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", incomplete_generation)
    await store.ensure_profile("user-1")

    session_id, state = await svc.start_session("user-1", "int_03_weakness_framing")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["messages"].append({
        "role": "user",
        "content": (
            "My weakness is leading with technical detail before business impact. "
            "I now use decision criteria first."
        ),
    })

    chunks = await _collect_stream(
        svc.run_turn(
            session_id,
            "A phased payment rollout caught two retry edge cases and avoided a full rollback.",
            client_turn_id="turn-1",
        )
    )
    text_chunks = [chunk for chunk in chunks if isinstance(chunk, str)]

    assert not any("For instance," in chunk for chunk in text_chunks)
    assert any("three-part shape" in chunk for chunk in text_chunks)
    assert any("pressure-test" in chunk for chunk in text_chunks)
    assert not any("under 45 seconds" in chunk for chunk in text_chunks)
    assert state["active_turn_id"] is None
    assert state["block_reason"] is None
    assert state["input_allowed"] is True
    assert any(
        m.get("role") == "assistant"
        and "three-part shape" in m.get("content", "")
        and "pressure-test" in m.get("content", "")
        and "under 45 seconds" not in m.get("content", "")
        for m in state["messages"]
    )


@pytest.mark.asyncio
async def test_same_node_generation_cancellation_persists_fallback_without_progress(monkeypatch, store):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.8,
                "last_clean_pass_score": 0.8,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "current_mastery": 0.24,
                "attempts": 1,
                "session_attempts": 1,
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test-model",
                    prompt="coach the learner",
                    kind="coach",
                ),
            }

    async def cancelled_generation(_spec):
        raise asyncio.CancelledError()
        yield "never"

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", cancelled_generation)
    await store.ensure_profile("user-1")

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1

    with pytest.raises(asyncio.CancelledError):
        await _collect_stream(svc.run_turn(session_id, "A solid answer."))

    assert state["current_mastery"] == 0.0
    assert state["attempts"] == 0
    assert state["clean_streak"] == 0
    assert state["turn_count"] == 2
    assert any(
        m.get("role") == "assistant" and "try that once more" in m.get("content", "")
        for m in state["messages"]
    )
    assert ("user-1", "int_01_elevator_pitch") not in store.mastery


@pytest.mark.asyncio
async def test_successful_same_node_turn_bumps_session_version(monkeypatch, store):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "last_eval_score": 0.8,
                "last_clean_pass_score": 0.8,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "current_mastery": 0.24,
                "attempts": 1,
                "session_attempts": 1,
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test-model",
                    prompt="coach the learner",
                    kind="coach",
                ),
            }

    async def fake_generation(_spec):
        yield "Coach response."

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", fake_generation)
    await store.ensure_profile("user-1")

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["session_version"] = 4

    await _collect_stream(svc.run_turn(session_id, "A solid answer."))

    assert state["session_version"] == 5


@pytest.mark.asyncio
async def test_advancing_turn_suppresses_stale_same_node_exercise(monkeypatch, store):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            rubric_result = _passing_prep_rubric_result("transfer")
            for criterion in rubric_result["criteria"]:
                criterion["evidence_quote"] = (
                    "I reduced checkout failures by 18% after adding retry alerts"
                )
            return {
                "last_eval_score": 0.9,
                "last_clean_pass_score": 0.9,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "last_rubric_result": rubric_result,
                "current_mastery": 0.8,
                "attempts": 5,
                "active_prompt_attempt_type": None,
                "pending_prompt_attempt_type": "pressure",
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test",
                    prompt="Ask another stale exercise.",
                    kind="teach",
                ),
            }

    async def fake_stream_generation(_spec):
        yield "This is another exercise that should not be shown."

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "stream_generation", fake_stream_generation)

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["clean_streak"] = 1
    state["meaningful_attempts"] = 4
    state["independent_passes"] = 3
    state["pressure_passes"] = 1
    state["best_independent_score"] = 0.82
    state["core_qualified"] = True
    state["core_qualification_turn_id"] = "turn-core-2"
    state["core_qualification_evidence"] = {
        "evaluation_id": "turn-core-2",
        "user_id": "user-1",
        "node_id": "int_01_elevator_pitch",
        "attempt_type": "independent",
        "pass_eligible": True,
        "blockers": [],
        "learner_answer": "A qualified core pitch.",
    }
    state["active_prompt_attempt_type"] = "transfer"

    learner_answer = (
        "I reduced checkout failures by 18% after adding retry alerts, then documented "
        "the rollout decision."
    )
    chunks = await _collect_stream(
        svc.run_turn(session_id, learner_answer, client_turn_id="turn-advance-1")
    )

    expected_feedback = (
        "Keep this version. It covers answering the question, specific detail, and pitch "
        "structure, using \"I reduced checkout failures by 18% after adding retry alerts\" "
        "as proof. No required gap remains, so this skill is ready to carry forward."
    )
    feedback_index = chunks.index(expected_feedback)
    advance_indexes = [
        index for index, item in enumerate(chunks) if isinstance(item, svc.NodeAdvance)
    ]
    progress_indexes = [
        index for index, item in enumerate(chunks) if isinstance(item, svc.ProgressUpdate)
    ]

    assert "This is another exercise that should not be shown." not in chunks
    assert all(
        "This is another exercise" not in message.get("content", "")
        for message in state["messages"]
    )
    assert len(advance_indexes) == 1
    assert len(progress_indexes) == 1
    assert feedback_index < progress_indexes[0] < advance_indexes[0]
    completion_messages = [
        message
        for message in state["messages"]
        if message.get("message_kind") == "completion_feedback"
    ]
    assert completion_messages == [{
        "role": "assistant",
        "content": expected_feedback,
        "node_id": "int_01_elevator_pitch",
        "turn_id": "turn-advance-1",
        "message_kind": "completion_feedback",
    }]
    assert completion_messages[0] in store.session_messages[session_id]
    assert state["pending_node_transition"] is not None
    assert state["pending_prompt_attempt_type"] is None
    assert state["active_prompt_attempt_type"] is None


@pytest.mark.asyncio
async def test_module_done_emits_grounded_completion_feedback_before_recap(monkeypatch, store):
    from app.services import session_service as svc

    class FakeGraph:
        async def ainvoke(self, _state):
            rubric_result = _passing_prep_rubric_result("transfer")
            for criterion in rubric_result["criteria"]:
                criterion["evidence_quote"] = ""
            return {
                "last_eval_score": 0.9,
                "last_clean_pass_score": 0.9,
                "last_diagnosis": {
                    "english": True,
                    "on_task": True,
                    "affect": "confident",
                },
                "last_rubric_result": rubric_result,
                "current_mastery": 0.8,
                "attempts": 5,
                "active_prompt_attempt_type": None,
                "pending_prompt_attempt_type": "pressure",
                "pending": svc.GenSpec(
                    provider="gemini",
                    model="test",
                    prompt="Ask another stale exercise.",
                    kind="teach",
                ),
            }

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())

    session_id, state = await svc.start_session("user-1", "int_12_explain_a_gap")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["clean_streak"] = 1
    state["meaningful_attempts"] = 4
    state["independent_passes"] = 3
    state["pressure_passes"] = 1
    state["best_independent_score"] = 0.82
    state["core_qualified"] = True
    state["core_qualification_turn_id"] = "turn-core-2"
    state["core_qualification_evidence"] = {
        "evaluation_id": "turn-core-2",
        "user_id": "user-1",
        "node_id": "int_12_explain_a_gap",
        "attempt_type": "independent",
        "pass_eligible": True,
        "blockers": [],
        "learner_answer": "A qualified core gap explanation.",
    }
    state["active_prompt_attempt_type"] = "transfer"

    learner_answer = "I explain the gap directly, then show the work I completed afterward."
    chunks = await _collect_stream(
        svc.run_turn(session_id, learner_answer, client_turn_id="turn-module-done")
    )

    expected_feedback = (
        "Keep this version. It covers answering the question, specific detail, and pitch "
        "structure, using \"I explain the gap directly, then show the work I completed "
        "afterward.\" as proof. No required gap remains, so this skill is ready to carry "
        "forward."
    )
    feedback_index = chunks.index(expected_feedback)
    recap_indexes = [
        index for index, item in enumerate(chunks) if isinstance(item, svc.SessionRecap)
    ]
    progress_indexes = [
        index for index, item in enumerate(chunks) if isinstance(item, svc.ProgressUpdate)
    ]

    assert len(recap_indexes) == 1
    assert len(progress_indexes) == 1
    assert feedback_index < progress_indexes[0] < recap_indexes[0]
    assert not any(isinstance(item, svc.NodeAdvance) for item in chunks)
    assert state["module_done"] is True
    assert state["messages"][-1] == {
        "role": "assistant",
        "content": expected_feedback,
        "node_id": "int_12_explain_a_gap",
        "turn_id": "turn-module-done",
        "message_kind": "completion_feedback",
    }
    assert state["messages"][-1] in store.session_messages[session_id]


def test_weakness_completion_feedback_uses_one_complete_progress_quote():
    from app.services import session_service as svc

    answer = (
        "A weakness I am managing is missing migration edge cases when I am moving too quickly. "
        "I now use a pre-deploy checklist covering lock risk and rollback commands. Across two "
        "schema changes, that habit prevented checkout errors and produced a tested runbook."
    )
    rubric_result = {
        "criteria": [
            {"id": "real_weakness", "met": True, "evidence_quote": answer[:93]},
            {"id": "mitigation_habit", "met": True, "evidence_quote": "I now use a pre-deploy checklist covering lock risk and rollback commands."},
            {"id": "progress_evidence", "met": True, "evidence_quote": "Across two schema changes, that habit prevented checkout errors and produced a tested runbook."},
        ],
    }

    feedback = svc._completion_feedback_text(rubric_result, answer)

    assert feedback.count('"') == 2
    assert "Across two schema changes" in feedback
    assert '"dge cases' not in feedback


@pytest.mark.asyncio
async def test_module_done_marks_session_terminal_and_blocks_more_turns():
    from app.services import session_service as svc

    session_id, state = await svc.start_session("user-1", "int_12_explain_a_gap")
    state["opening_streamed"] = True
    state["turn_count"] = 1
    state["current_mastery"] = 0.85
    state["last_eval_score"] = 0.85
    state["last_diagnosis"] = {"english": True, "on_task": True, "affect": "confident"}
    state["attempts"] = 2
    state["session_attempts"] = 2
    state["clean_streak"] = 2

    await svc._maybe_advance(state)

    assert state["module_done"] is True
    assert state["session_over"] is True
    assert state["status"] == "ended"
    assert state["input_allowed"] is False
    assert state["block_reason"] == "module_done"
    assert svc.turn_block_reason(state) == "module_done"

    with pytest.raises(svc.SessionNotActiveError) as exc:
        await _collect_stream(svc.run_turn(session_id, "Can I keep answering?"))
    assert str(exc.value) == "module_done"


@pytest.mark.asyncio
async def test_session_state_rehydrates_from_runtime_store_after_memory_loss(monkeypatch):
    from app.services import session_service as svc

    async def fake_stream_generation(_spec):
        yield "Durable opening."

    monkeypatch.setattr(svc, "stream_generation", fake_stream_generation)

    session_id, state = await svc.start_session("user-1", "int_01_elevator_pitch")
    await _collect_stream(svc.stream_opening(session_id))
    assert state["messages"][-1]["content"] == "Durable opening."

    svc.SessionStore.clear()
    restored = await svc.get_session_state(session_id)

    assert restored is not None
    assert restored["session_id"] == session_id
    assert restored["competency_node"] == "int_01_elevator_pitch"
    assert restored["opening_streamed"] is True
    assert restored["messages"][-1]["content"] == "Durable opening."


def test_turn_route_blocks_closed_simulation_before_scoring(store):
    from app.services import session_service as svc
    import asyncio

    session_id = "simulation-closed-before-end"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_test",
    )
    state["opening_streamed"] = True
    state["session_over"] = True
    state["input_allowed"] = False
    state["block_reason"] = "session_over"
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    response = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "One more answer after the panel closed.",
            "client_turn_id": "closed-sim-turn-1",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "session_over"


def test_transcript_restores_active_game_prompt_without_answer_key(store):
    from app.services import session_service as svc
    import asyncio

    session_id = "active-game-prompt-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    state["messages"] = [
        {
            "role": "user",
            "content": "I explain the weakness with a concrete example.",
            "turn_id": "game-producing-turn",
            "message_id": f"{session_id}:turn:game-producing-turn:user",
        },
        {
            "role": "assistant",
            "content": "[Fill in the blank] I owned ___.",
            "turn_id": "game-producing-turn",
        },
    ]
    state["active_game_prompt"] = {
        "type": "fill_blank",
        "sentence": "I owned ___.",
        "hint": "ownership",
        "context": "Practice specific ownership language.",
        "options": None,
        "turn_id": "game-producing-turn",
        "answer_key": "the mistake",
    }
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/transcript", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["state"]["task_type"] == "interview_prep"
    assert response.json()["state"]["module_id"] == "interview"
    assert response.json()["messages"][0]["turn_id"] == "game-producing-turn"
    assert response.json()["messages"][1]["turn_id"] == "game-producing-turn"
    prompt = response.json()["game_prompt"]
    assert prompt == {
        "type": "fill_blank",
        "sentence": "I owned ___.",
        "hint": "ownership",
        "context": "Practice specific ownership language.",
        "options": None,
        "turn_id": "game-producing-turn",
    }
    assert "answer_key" not in prompt


def test_game_prompt_sse_frame_carries_producing_turn_id():
    from app.api.routes import _turn_frame
    from app.services.session_service import GamePrompt

    frame = _turn_frame(
        GamePrompt(
            type="fill_blank",
            sentence="I owned ___.",
            hint="ownership",
            context="Practice specific ownership language.",
            answer_key="the mistake",
            turn_id="game-producing-turn",
        )
    )

    assert "event: game_prompt" in frame
    assert '"turn_id": "game-producing-turn"' in frame
    assert "answer_key" not in frame


def test_state_snapshot_includes_opening_streamed_for_retry_ui():
    from app.api.routes import _state_snapshot
    from app.services import session_service as svc

    state = svc._new_state(
        "test_user",
        "opening-state-session",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = False

    snapshot = _state_snapshot(state)

    assert snapshot["opening_streamed"] is False


def test_state_snapshot_preserves_latest_readiness_across_transcript_reload():
    from app.api.routes import _state_snapshot
    from app.services import session_service as svc

    state = svc._new_state(
        "test_user",
        "readiness-reload-session",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["current_mastery"] = 0.51
    state["readiness_score"] = 0.55

    snapshot = _state_snapshot(state)

    assert snapshot["current_mastery"] == 0.51
    assert snapshot["readiness_score"] == 0.55


def test_state_snapshot_exposes_backend_owned_assessment_progress_counts():
    from app.api.routes import _state_snapshot
    from app.services import session_service as svc
    from app.services.assessment_plan import ensure_assessment_plan

    state = svc._new_state(
        "test_user",
        "assessment-progress-state-session",
        "gd_01_stake_position",
        [],
        task_type="gd_test",
        personas=[
            {"speaker_id": "moderator_timekeeper", "name": "Moderator", "role_type": "moderator"},
            {"speaker_id": "data_driven_analyst", "name": "Data-Driven Analyst", "role_type": "debater"},
        ],
    )
    state["assessment_plan"] = ensure_assessment_plan(state)
    state["messages"] = [
        item
        for idx in range(6)
        for item in (
            {"role": "assistant", "content": f"Prompt {idx}", "speaker_name": "Data-Driven Analyst"},
            {"role": "user", "content": f"Answer {idx}", "message_kind": "learner_answer"},
        )
    ]
    state["assessment_events"] = [
        {"event_type": "analysis", "task_type": "gd_test", "scorable": True}
        for _idx in range(3)
    ]

    snapshot = _state_snapshot(state)

    progress = snapshot["assessment_state"]["progress"]
    assert progress["scorable_turn_count"] == 6
    assert progress["min_scorable_turns"] == 5
    assert progress["coverage_map"]["event_count"] == 6
    assert progress["coverage_map"]["source"] == "typed_events_with_transcript_fallback"


def test_test_mode_turn_persists_each_speaker_for_reload(monkeypatch, store):
    from app.services import session_service as svc
    from app.services.simulation_service import Speaker
    import asyncio

    async def fake_simulation_round(_state):
        yield Speaker(speaker_id="moderator_timekeeper", name="Moderator")
        yield "Let's frame the question clearly."
        yield Speaker(speaker_id="quiet_expert", name="Quiet Expert")
        yield "I would add one careful example."

    monkeypatch.setattr(svc, "stream_simulation_round", fake_simulation_round)

    session_id = "speaker-persistence-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "gd_01_stake_position",
        [],
        task_type="gd_test",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    asyncio.run(_collect_stream(svc.run_turn(session_id, "I support this topic.")))

    assistant_messages = [m for m in state["messages"] if m.get("role") == "assistant"]
    assert [m.get("speaker_name") for m in assistant_messages] == [
        "Moderator",
        "Quiet Expert",
    ]
    assert assistant_messages[0]["content"] == "Let's frame the question clearly."
    assert assistant_messages[1]["content"] == "I would add one careful example."

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/transcript", headers=AUTH)
    assert response.status_code == 200
    restored = [
        (
            m["speaker_name"],
            m.get("speaker_id"),
            m.get("message_kind"),
            m.get("node_id"),
            m["content"],
        )
        for m in response.json()["messages"]
        if m["role"] == "assistant"
    ]
    assert restored == [
        (
            "Moderator",
            "moderator_timekeeper",
            "simulation_turn",
            "gd_01_stake_position",
            "Let's frame the question clearly.",
        ),
        (
            "Quiet Expert",
            "quiet_expert",
            "simulation_turn",
            "gd_01_stake_position",
            "I would add one careful example.",
        ),
    ]


def test_gd_ask_panelist_action_persists_user_turn_as_scorable_answer(monkeypatch, store):
    from app.services import session_service as svc
    from app.services.simulation_service import Speaker
    import asyncio

    async def fake_simulation_round(_state):
        yield Speaker(speaker_id="aggressive_challenger", name="Aggressive Challenger")
        yield "The strongest risk is weaker mentorship and visibility for new hires."

    monkeypatch.setattr(svc, "stream_simulation_round", fake_simulation_round)

    session_id = "ask-panelist-scorable-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "gd_01_stake_position",
        [],
        task_type="gd_test",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    asyncio.run(_collect_stream(svc.run_turn(
        session_id,
        "Aggressive Challenger, what is the strongest risk here?",
        assessment_action={
            "kind": "ask_panelist",
            "speaker_id": "aggressive_challenger",
            "speaker_name": "Aggressive Challenger",
            "source": "quick_action",
        },
    )))

    user_message = next(message for message in state["messages"] if message.get("role") == "user")
    assert user_message["message_kind"] == "learner_answer"
    assert user_message["assessment_action"]["kind"] == "ask_panelist"


@pytest.mark.asyncio
async def test_accepted_simulation_turn_persists_user_message_before_model_failure(monkeypatch, store):
    from app.services import session_service as svc

    calls = {"count": 0}

    async def failing_simulation_round(_state):
        calls["count"] += 1
        raise RuntimeError("persona stream unavailable")
        yield "never"

    monkeypatch.setattr(svc, "stream_simulation_round", failing_simulation_round)
    await store.ensure_profile("test_user")

    session_id = "simulation-user-durable-before-failure"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_test",
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
        personas=[
            {
                "speaker_id": "interviewer",
                "name": "Interviewer",
                "role_type": "interviewer",
                "role": "Mixed interview interviewer for Backend Software Engineer",
            }
        ],
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    await svc._persist_runtime_state(state)

    with pytest.raises(RuntimeError):
        await _collect_stream(
            svc.run_turn(
                session_id,
                "I answered with a specific backend project example.",
                client_turn_id="client-turn-1",
            )
        )

    svc.SessionStore.clear()
    restored = await svc.get_session_state(session_id)

    assert restored is not None
    user_messages = [m for m in restored["messages"] if m.get("role") == "user"]
    assert [m["content"] for m in user_messages] == [
        "I answered with a specific backend project example."
    ]
    assert [m.get("turn_id") for m in user_messages] == ["client-turn-1"]

    svc.SessionStore[session_id] = restored
    with pytest.raises(RuntimeError):
        await _collect_stream(
            svc.run_turn(
                session_id,
                "I answered with a specific backend project example.",
                client_turn_id="client-turn-1",
            )
        )

    retried = await svc.get_session_state(session_id)
    retried_user_messages = [
        m for m in retried["messages"] if m.get("role") == "user"
    ]
    assert [m["content"] for m in retried_user_messages] == [
        "I answered with a specific backend project example."
    ]
    assert calls["count"] == 2
    assert restored["competency_node"] == "int_01_elevator_pitch"
    assert restored["scenario_config"]["target_role"] == "Backend Software Engineer"


@pytest.mark.asyncio
async def test_completed_interview_report_and_transcript_survive_reload(monkeypatch, store):
    from app.ai.schemas import SimulationReport
    from app.services import session_service as svc

    async def fake_score_session(_state):
        return SimulationReport(
            score=0.82,
            summary="Strong backend interview with clear trade-offs.",
            strengths=["specific project ownership", "clear debugging narrative"],
            improvements=["tighten one leadership story"],
            clarity_score=0.86,
            confidence_score=0.78,
            scenario_label="Mixed interview for Backend Software Engineer",
            role_focus="Backend Software Engineer",
            topic="Mixed interview for Backend Software Engineer",
            observed_skill_gaps=["leadership story"],
            recommended_next_nodes=["Close and Ask Sharp Questions"],
        )

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    await store.ensure_profile("test_user")

    session_id = "completed-interview-persists-after-reload"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_test",
        sim_topic="Mixed interview for Backend Software Engineer",
        scenario_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
            "pressure": "high",
        },
        personas=[
            {
                "speaker_id": "interviewer",
                "name": "Interviewer",
                "role_type": "interviewer",
                "role": "Mixed interview interviewer for Backend Software Engineer",
                "prompt_role": "RAW SYSTEM PROMPT SHOULD NOT BE PUBLIC",
            }
        ],
    )
    state["opening_streamed"] = True
    state["simulation_round"] = 6
    state["messages"] = [
        {
            "role": "assistant",
            "content": "Walk me through a backend project.",
            "speaker_name": "Interviewer",
            "speaker_id": "interviewer",
            "message_kind": "simulation_turn",
            "node_id": "int_01_elevator_pitch",
        },
        {
            "role": "user",
            "content": "I built a checkout reliability dashboard with clear trade-offs.",
        },
    ]
    svc.SessionStore[session_id] = state
    await svc._persist_runtime_state(state)

    close_result = await svc.close_session(session_id)
    assert close_result["score"] == 0.82

    svc.SessionStore.clear()
    restored = await svc.get_session_state(session_id)

    assert restored is not None
    assert restored["status"] == "ended"
    assert restored["simulation_score"] == 0.82
    assert restored["simulation_report"]["role_focus"] == "Backend Software Engineer"
    assert restored["scenario_config"]["target_role"] == "Backend Software Engineer"
    assert restored["personas"][0]["name"] == "Interviewer"
    assert restored["messages"][0]["content"] == "Walk me through a backend project."

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/transcript", headers=AUTH)
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"]["status"] == "ended"
    assert payload["state"]["node_title"] != "Learning Path"
    assert payload["state"]["simulation_report"]["role_focus"] == "Backend Software Engineer"
    assert payload["messages"][0]["content"] == "Walk me through a backend project."
    public_persona = payload["state"]["personas"][0]
    assert "prompt_role" not in public_persona
    assert "RAW SYSTEM PROMPT" not in str(public_persona)


def test_interview_public_persona_never_exposes_prompt_role():
    from app.api.routes import _public_personas

    personas = [
        {
            "speaker_id": "interviewer",
            "name": "Interviewer",
            "role_type": "interviewer",
            "role": "Mixed interview interviewer for Backend Software Engineer",
            "prompt_role": (
                "MIXED INTERVIEW INTERVIEWER FOR BACKEND SOFTWARE ENGINEER. "
                "THE INTERVIEW IS COMMUNICATION-FOCUSED: PROBE EXAMPLES."
            ),
            "style": "probing",
        }
    ]

    public = _public_personas(personas)

    assert public == [
        {
            "speaker_id": "interviewer",
            "name": "Interviewer",
            "role_type": "interviewer",
            "role": "Mixed interview interviewer for Backend Software Engineer",
            "style": "probing",
        }
    ]
    assert "prompt_role" not in public[0]
    assert "COMMUNICATION-FOCUSED" not in str(public)


def test_interview_probe_honors_explicit_move_on_request():
    from app.services.simulation_service import _interview_probe_intent

    state = {
        "task_type": "interview_test",
        "career_context": {"primary_role": "Backend Software Engineer"},
        "probe_items": [
            {
                "prompt": "Explain Singleton and Factory with examples.",
                "aim": "show design-pattern fluency",
            },
            {
                "prompt": "Describe a production failure you owned.",
                "aim": "show ownership",
            },
        ],
        "probe_cursor": 0,
        "used_probe_prompts": ["Explain Singleton and Factory with examples."],
        "messages": [
            {
                "role": "assistant",
                "content": "Explain Singleton and Factory with examples.",
            },
            {
                "role": "user",
                "content": (
                    "I already answered Singleton and Factory with examples. "
                    "Please move to a different dimension, such as a disagreement "
                    "with a teammate."
                ),
            },
        ],
    }

    intent = _interview_probe_intent(state, "Ask another design-pattern follow-up.")

    assert "disagreement with a teammate" in intent
    assert "Singleton and Factory" not in intent


@pytest.mark.asyncio
async def test_interview_stream_replaces_repeated_model_question_with_selected_probe(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import simulation_service as sim
    from app.services.simulation.blackboard import apply_decision, new_blackboard

    async def fake_decide_round(bb, personas, *_args, **_kwargs):
        decision = DirectorDecision(
            action="probe_deeper",
            next_speaker="interviewer",
            intent="Ask a next interview question.",
            tension=0.4,
            answer_quality=0.6,
            should_close=False,
        )
        return apply_decision(bb, decision), personas[0], decision

    async def repeated_persona_turn(*_args, **_kwargs):
        yield "Can you explain Singleton and Factory with specific examples?"

    monkeypatch.setattr(sim, "decide_round", fake_decide_round)
    monkeypatch.setattr(sim, "stream_persona_turn", repeated_persona_turn)

    state = {
        "task_type": "interview_test",
        "sim_topic": "Mixed interview for Backend Software Engineer",
        "career_context": {"primary_role": "Backend Software Engineer"},
        "scenario_config": {
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
        "personas": [
            {
                "speaker_id": "interviewer",
                "name": "Interviewer",
                "role_type": "interviewer",
                "role": "Mixed interview interviewer for Backend Software Engineer",
            }
        ],
        "blackboard": new_blackboard("Mixed interview for Backend Software Engineer"),
        "probe_items": [
            {
                "prompt": "Explain Singleton and Factory with examples.",
                "aim": "show design-pattern fluency",
            },
            {
                "prompt": "Describe a disagreement with a teammate or stakeholder.",
                "aim": "show collaboration and judgment",
            },
        ],
        "probe_cursor": 1,
        "used_probe_prompts": ["Explain Singleton and Factory with examples."],
        "messages": [
            {
                "role": "assistant",
                "content": "Explain Singleton and Factory with specific examples.",
            },
            {
                "role": "user",
                "content": "I already answered that. Please move to a disagreement with a teammate.",
            },
        ],
    }

    chunks = await _collect_stream(sim.stream_simulation_round(state))
    visible_text = "".join(item for item in chunks if isinstance(item, str))

    assert "disagreement with a teammate" in visible_text
    assert "Can you explain Singleton and Factory" not in visible_text


@pytest.mark.asyncio
async def test_gd_stream_replaces_repeated_panel_demand_before_delivery(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.content.task_types import TaskType
    from app.services import simulation_service as sim
    from app.services.simulation.blackboard import apply_decision, new_blackboard

    async def repeated_director(bb, personas, *_args, **_kwargs):
        decision = DirectorDecision(
            action="probe_deeper",
            next_speaker="data_driven_analyst",
            intent="Demand Indian pilot evidence again.",
            tension=0.7,
            answer_quality=0.5,
            should_close=False,
        )
        speaker = next(p for p in personas if p["speaker_id"] == "data_driven_analyst")
        return apply_decision(bb, decision), speaker, decision

    async def repeated_persona_turn(*_args, **_kwargs):
        yield "Give Indian pilot evidence and a case study before moving forward."

    monkeypatch.setattr(sim, "decide_round", repeated_director)
    monkeypatch.setattr(sim, "stream_persona_turn", repeated_persona_turn)

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "AI in hiring",
        "personas": sim.build_personas(TaskType.GD_TEST, "AI in hiring"),
        "blackboard": new_blackboard("AI in hiring") | {
            "phase": "pressure",
            "turn": 4,
            "last_speaker": "data_driven_analyst",
        },
        "messages": [
            {
                "role": "assistant",
                "speaker_name": "Data-Driven Analyst",
                "content": "Give Indian pilot evidence and a case study before moving forward.",
            },
            {
                "role": "user",
                "content": "A phased rollout would be safer because teams can compare hiring outcomes.",
            },
        ],
    }

    chunks = await _collect_stream(sim.stream_simulation_round(state))
    visible_text = "".join(item for item in chunks if isinstance(item, str)).lower()

    assert any(
        marker in visible_text
        for marker in ("rollout risk", "exception path", "adoption and harm", "promise")
    )
    assert "ai in hiring" in visible_text
    assert "new angle" not in visible_text
    assert not visible_text.strip().endswith("?")
    assert "give " not in visible_text
    assert "provide " not in visible_text
    assert "give indian pilot evidence" not in visible_text
    assert "case study before moving forward" not in visible_text


def test_turn_route_requires_and_replays_client_turn_id(monkeypatch, store):
    from app.services import session_service as svc

    async def fake_run_turn(_session_id, _user_input, **_kwargs):
        calls["count"] += 1
        yield "Coach response."

    calls = {"count": 0}
    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "turn-idempotency-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    missing_id = client.post(
        "/session/turn",
        json={"session_id": session_id, "user_input": "hello"},
        headers=AUTH,
    )
    assert missing_id.status_code == 400
    assert missing_id.json()["detail"]["code"] == "client_turn_id_required"

    missing_version = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "hello",
            "client_turn_id": "client-turn-missing-version",
        },
        headers=AUTH,
    )
    assert missing_version.status_code == 400
    assert missing_version.json()["detail"]["code"] == "expected_session_version_required"

    first = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "hello",
            "client_turn_id": "client-turn-1",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )
    second = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "hello",
            "client_turn_id": "client-turn-1",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert "Coach response." in first.text
    assert "Coach response." in second.text
    assert calls["count"] == 1


def test_turn_stream_emits_accepted_before_model_output(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_run_turn(_session_id, _user_input, **_kwargs):
        yield "Coach response after slow model."

    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "turn-accepted-first-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    response = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "hello",
            "client_turn_id": "client-turn-accepted-first",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.text.index("event: accepted") < response.text.index("Coach response after slow model.")
    assert store.turn_requests[(session_id, "client-turn-accepted-first")]["status"] == "completed"


def test_transcript_exposes_active_turn_recovery_state(store):
    from app.services import session_service as svc
    import asyncio

    session_id = "active-turn-transcript-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    state["active_turn_id"] = "client-turn-processing"
    state["active_turn_status"] = "processing"
    state["input_allowed"] = False
    state["block_reason"] = "turn_processing"
    state["messages"].append({
        "role": "user",
        "content": "My answer is already accepted.",
        "turn_id": "client-turn-processing",
        "message_kind": "learner_answer",
        "status": "accepted",
    })
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/transcript", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["active_turn"] == {
        "client_turn_id": "client-turn-processing",
        "status": "processing",
    }
    assert body["input_allowed"] is False
    assert body["block_reason"] == "turn_processing"


@pytest.mark.parametrize("route_suffix", ["state", "transcript"])
def test_read_recovery_routes_do_not_replace_runtime_messages(monkeypatch, store, route_suffix):
    from app.services import session_service as svc
    import asyncio

    session_id = f"read-only-{route_suffix}-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    state["messages"].append({
        "role": "assistant",
        "content": "Opening prompt",
        "message_kind": "opening",
    })
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    calls = {"upsert": 0, "replace": 0, "touch": 0}

    async def spy_upsert(*_args, **_kwargs):
        calls["upsert"] += 1

    async def spy_replace(*_args, **_kwargs):
        calls["replace"] += 1

    async def spy_touch(*_args, **_kwargs):
        calls["touch"] += 1

    monkeypatch.setattr(store, "upsert_session_runtime", spy_upsert)
    monkeypatch.setattr(store, "replace_session_messages", spy_replace)
    monkeypatch.setattr(store, "touch_session_runtime", spy_touch)

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/{route_suffix}", headers=AUTH)

    assert response.status_code == 200
    assert calls == {"upsert": 0, "replace": 0, "touch": 1}


def test_turn_route_rejects_different_client_turn_id_for_same_session_version(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_run_turn(session_id, _user_input, **_kwargs):
        calls["count"] += 1
        state = svc.get_state(session_id)
        assert state is not None
        state["messages"].append({"role": "assistant", "content": "Coach response."})
        state["turn_count"] += 1
        svc._bump_session_version(state)
        yield "Coach response."

    calls = {"count": 0}
    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "turn-version-slot-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    first = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "first answer",
            "client_turn_id": "client-turn-a",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )
    second = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "duplicate browser event",
            "client_turn_id": "client-turn-b",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "turn_version_consumed"
    assert second.json()["detail"]["accepted_client_turn_id"] == "client-turn-a"
    assert calls["count"] == 1


def test_turn_route_releases_orphaned_in_progress_version_latch(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio
    import time

    async def fake_run_turn(session_id, user_input, **_kwargs):
        calls["count"] += 1
        state = svc.get_state(session_id)
        assert state is not None
        state["messages"].append({"role": "user", "content": user_input})
        state["messages"].append({"role": "assistant", "content": "Recovered coach response."})
        state["turn_count"] += 1
        svc._bump_session_version(state)
        yield "Recovered coach response."

    calls = {"count": 0}
    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "turn-orphaned-version-latch-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    state["input_allowed"] = True
    state["block_reason"] = None
    state["active_turn_id"] = None
    state["active_turn_status"] = "completed"
    svc.SessionStore[session_id] = state
    store.turn_requests[(session_id, "abandoned-turn")] = {
        "session_id": session_id,
        "client_turn_id": "abandoned-turn",
        "request_hash": "old-hash",
        "expected_version": 1,
        "status": "in_progress",
        "transcript_delta": [],
        "done_snapshot": None,
        "error_code": None,
        "created_at": time.time() - 10,
        "updated_at": time.time() - 10,
    }
    asyncio.run(store.ensure_profile("test_user"))

    response = TestClient(app).post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "The weakness is leading with technical detail before business impact.",
            "client_turn_id": "fresh-turn-after-orphan",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert "Recovered coach response." in response.text
    assert calls["count"] == 1
    assert store.turn_requests[(session_id, "abandoned-turn")]["status"] == "failed"
    assert (
        store.turn_requests[(session_id, "abandoned-turn")]["error_code"]
        == "orphaned_in_progress"
    )
    assert store.turn_requests[(session_id, "fresh-turn-after-orphan")]["status"] == "completed"


def test_turn_route_does_not_release_fresh_in_progress_version_latch(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio
    import time

    async def fake_run_turn(*_args, **_kwargs):
        calls["count"] += 1
        yield "This producer must not run."

    calls = {"count": 0}
    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "turn-fresh-version-latch-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    state["input_allowed"] = True
    state["block_reason"] = None
    state["active_turn_id"] = None
    svc.SessionStore[session_id] = state
    now = time.time()
    store.turn_requests[(session_id, "accepted-but-not-started")] = {
        "session_id": session_id,
        "client_turn_id": "accepted-but-not-started",
        "request_hash": "first-hash",
        "expected_version": 1,
        "status": "in_progress",
        "transcript_delta": [],
        "done_snapshot": None,
        "error_code": None,
        "created_at": now,
        "updated_at": now,
    }
    asyncio.run(store.ensure_profile("test_user"))

    response = TestClient(app).post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "A duplicate request from the same rendered version.",
            "client_turn_id": "concurrent-second-turn",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "turn_version_consumed"
    assert calls["count"] == 0
    assert store.turn_requests[(session_id, "accepted-but-not-started")]["status"] == "in_progress"


def test_turn_route_accepts_next_turn_only_after_session_version_advances(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_run_turn(session_id, user_input, **_kwargs):
        calls["count"] += 1
        state = svc.get_state(session_id)
        assert state is not None
        state["messages"].append({"role": "user", "content": user_input})
        state["messages"].append({"role": "assistant", "content": f"Reply {calls['count']}."})
        state["turn_count"] += 1
        svc._bump_session_version(state)
        yield f"Reply {calls['count']}."

    calls = {"count": 0}
    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "turn-version-advance-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    client = TestClient(app)
    first = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "first answer",
            "client_turn_id": "turn-1",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )
    second = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "second answer",
            "client_turn_id": "turn-2",
            "expected_session_version": 2,
        },
        headers=AUTH,
    )
    stale = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "stale duplicate",
            "client_turn_id": "turn-stale",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "turn_version_consumed"
    assert calls["count"] == 2


def test_turn_latch_allows_only_one_client_turn_per_session_version(store):
    import asyncio

    first = asyncio.run(
        store.begin_turn_request(
            "same-version-session",
            "client-turn-a",
            "hash-a",
            7,
        )
    )
    second = asyncio.run(
        store.begin_turn_request(
            "same-version-session",
            "client-turn-b",
            "hash-b",
            7,
        )
    )

    assert first["accepted"] is True
    assert second["accepted"] is False
    assert second["status"] == "version_consumed"
    assert second["accepted_client_turn_id"] == "client-turn-a"


def test_stale_turn_latch_releases_session_version_for_new_client_turn(store):
    import asyncio
    import time

    store.turn_requests[("stale-turn-session", "abandoned-turn")] = {
        "session_id": "stale-turn-session",
        "client_turn_id": "abandoned-turn",
        "request_hash": "hash-old",
        "expected_version": 7,
        "status": "in_progress",
        "transcript_delta": [],
        "done_snapshot": None,
        "error_code": None,
        "updated_at": time.time() - 10_000,
    }

    retry = asyncio.run(
        store.begin_turn_request(
            "stale-turn-session",
            "fresh-turn",
            "hash-new",
            7,
        )
    )

    assert retry["accepted"] is True
    assert retry["status"] == "in_progress"
    stale_row = store.turn_requests[("stale-turn-session", "abandoned-turn")]
    assert stale_row["status"] == "failed"
    assert stale_row["error_code"] == "stale_in_progress"


def test_failed_turn_latch_does_not_consume_session_version(store):
    import asyncio

    first = asyncio.run(
        store.begin_turn_request(
            "retry-version-session",
            "client-turn-a",
            "hash-a",
            7,
        )
    )
    asyncio.run(
        store.complete_turn_request(
            "retry-version-session",
            "client-turn-a",
            "failed",
            error_code="session_proxy_timeout",
        )
    )
    second = asyncio.run(
        store.begin_turn_request(
            "retry-version-session",
            "client-turn-b",
            "hash-b",
            7,
        )
    )

    assert first["accepted"] is True
    assert second["accepted"] is True


def test_failed_turn_latch_can_retry_same_client_turn_id(store):
    import asyncio

    first = asyncio.run(
        store.begin_turn_request(
            "same-client-retry-session",
            "client-turn-a",
            "hash-a",
            7,
        )
    )
    asyncio.run(
        store.complete_turn_request(
            "same-client-retry-session",
            "client-turn-a",
            "failed",
            error_code="session_proxy_timeout",
        )
    )
    retry = asyncio.run(
        store.begin_turn_request(
            "same-client-retry-session",
            "client-turn-a",
            "hash-a",
            7,
        )
    )

    assert first["accepted"] is True
    assert retry["accepted"] is True
    assert retry["status"] == "in_progress"


def test_failed_turn_retry_respects_later_version_consumer(store):
    import asyncio

    first = asyncio.run(
        store.begin_turn_request(
            "failed-then-consumed-session",
            "client-turn-a",
            "hash-a",
            7,
        )
    )
    asyncio.run(
        store.complete_turn_request(
            "failed-then-consumed-session",
            "client-turn-a",
            "failed",
            error_code="session_proxy_timeout",
        )
    )
    consumer = asyncio.run(
        store.begin_turn_request(
            "failed-then-consumed-session",
            "client-turn-b",
            "hash-b",
            7,
        )
    )
    retry = asyncio.run(
        store.begin_turn_request(
            "failed-then-consumed-session",
            "client-turn-a",
            "hash-a",
            7,
        )
    )

    assert first["accepted"] is True
    assert consumer["accepted"] is True
    assert retry["accepted"] is False
    assert retry["status"] == "version_consumed"
    assert retry["accepted_client_turn_id"] == "client-turn-b"


def test_stale_start_request_can_retry_same_client_start_id(monkeypatch, store):
    import asyncio
    import time
    from app.api import routes
    from app.models import SessionStartRequest
    from app.services import session_service as svc

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        return "recovered-start-session", {
            "session_id": "recovered-start-session",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    payload = {
        "competency_node": "int_01_elevator_pitch",
        "client_start_id": "stale-start-id",
    }
    req = SessionStartRequest(**payload)
    store.start_requests[("test_user", "stale-start-id")] = {
        "user_id": "test_user",
        "client_start_id": "stale-start-id",
        "request_hash": routes._start_request_hash(req),
        "status": "in_progress",
        "session_id": None,
        "response_json": None,
        "error_code": None,
        "source_session_id": None,
        "source_transition_id": None,
        "updated_at": time.time() - 10_000,
    }

    client = TestClient(app)
    response = client.post("/session/start", json=payload, headers=AUTH)

    assert response.status_code == 200
    assert response.json()["session_id"] == "recovered-start-session"
    assert store.start_requests[("test_user", "stale-start-id")]["status"] == "completed"


def test_only_one_retry_can_reclaim_a_failed_start_request(store):
    import asyncio
    import time

    key = ("test_user", "failed-start-id")
    store.start_requests[key] = {
        "user_id": "test_user",
        "client_start_id": "failed-start-id",
        "request_hash": "same-hash",
        "status": "failed",
        "session_id": None,
        "response_json": None,
        "error_code": "stale_in_progress",
        "source_session_id": None,
        "source_transition_id": None,
        "created_at": time.time() - 100,
        "updated_at": time.time() - 100,
    }

    first = asyncio.run(store.reset_start_request(
        "test_user",
        "failed-start-id",
        "same-hash",
    ))
    second = asyncio.run(store.reset_start_request(
        "test_user",
        "failed-start-id",
        "same-hash",
    ))

    assert first["accepted"] is True
    assert second["accepted"] is False
    assert second["status"] == "in_progress"


def test_reclaimed_start_rejects_completion_from_old_claim(store):
    import asyncio
    import time

    first = asyncio.run(store.begin_start_request(
        "test_user",
        "fenced-start-id",
        "same-hash",
    ))
    store.start_requests[("test_user", "fenced-start-id")]["updated_at"] = time.time() - 10_000
    stale = asyncio.run(store.get_start_request("test_user", "fenced-start-id"))
    second = asyncio.run(store.reset_start_request(
        "test_user",
        "fenced-start-id",
        "same-hash",
    ))

    old_completed = asyncio.run(store.complete_start_request(
        "test_user",
        "fenced-start-id",
        "completed",
        session_id="old-worker-session",
        response_json={"session_id": "old-worker-session"},
        claim_generation=first["claim_generation"],
    ))
    current = asyncio.run(store.get_start_request("test_user", "fenced-start-id"))

    assert stale["status"] == "failed"
    assert second["claim_generation"] > first["claim_generation"]
    assert old_completed is False
    assert current["status"] == "in_progress"
    assert current["claim_generation"] == second["claim_generation"]


def test_stale_retry_after_process_loss_does_not_charge_attempt_twice(monkeypatch, store):
    from app.api import routes
    from app.billing.gate import GateDecision
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio
    import time

    asyncio.run(store.ensure_profile("test_user"))
    store.profiles["test_user"]["credits"] = 500

    async def paid_gate(*_args, **_kwargs):
        return GateDecision(False, 50, "attempt", "int_01_elevator_pitch", False, False, "attempt_meter")

    calls = {"count": 0}

    target_session_ids = []

    async def crash_then_start(user_id, node_id, session_id=None, **_kwargs):
        assert session_id
        target_session_ids.append(session_id)
        store.sessions.setdefault(session_id, {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": node_id,
            "status": "active",
        })
        calls["count"] += 1
        if calls["count"] == 1:
            raise SystemExit("simulated process loss after target persistence")
        return session_id, {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(routes, "resolve_gate", paid_gate)
    monkeypatch.setattr(svc, "start_session", crash_then_start)
    req = SessionStartRequest(
        competency_node="int_01_elevator_pitch",
        client_start_id="crash-safe-paid-start",
        confirm=True,
    )
    request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))

    with pytest.raises(SystemExit):
        asyncio.run(routes.start(req, request))
    assert store.profiles["test_user"]["credits"] == 450

    store.start_requests[("test_user", req.client_start_id)]["updated_at"] = time.time() - 10_000
    response = asyncio.run(routes.start(req, request))

    assert response.session_id == target_session_ids[0]
    assert target_session_ids == [target_session_ids[0], target_session_ids[0]]
    assert list(store.sessions) == [target_session_ids[0]]
    assert store.profiles["test_user"]["credits"] == 450
    assert ("test_user", "session_start:crash-safe-paid-start") in store.idempotent_charges


def test_live_old_start_cannot_refund_or_overwrite_reclaimed_retry(monkeypatch, store):
    from app.api import routes
    from app.billing.gate import GateDecision
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio
    import time

    async def scenario():
        await store.ensure_profile("test_user")
        store.profiles["test_user"]["credits"] = 500

        async def paid_gate(*_args, **_kwargs):
            return GateDecision(False, 50, "attempt", "int_01_elevator_pitch", False, False, "attempt_meter")

        first_started = asyncio.Event()
        release_first = asyncio.Event()
        calls = {"count": 0}

        async def slow_then_fast_start(user_id, node_id, session_id=None, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                first_started.set()
                await release_first.wait()
                return session_id, {
                    "session_id": session_id,
                    "user_id": user_id,
                    "competency_node": node_id,
                    "task_type": "interview_prep",
                    "module_id": "interview",
                    "current_mastery": 0.0,
                    "session_version": 1,
                    "status": "active",
                    "messages": [{"role": "assistant", "content": "old candidate"}],
                    "candidate_marker": "old",
                }
            return session_id, {
                "session_id": session_id,
                "user_id": user_id,
                "competency_node": node_id,
                "task_type": "interview_prep",
                "module_id": "interview",
                "current_mastery": 0.0,
                "session_version": 1,
                "status": "active",
                "messages": [{"role": "assistant", "content": "new candidate"}],
                "candidate_marker": "new",
            }

        monkeypatch.setattr(routes, "resolve_gate", paid_gate)
        monkeypatch.setattr(svc, "start_session", slow_then_fast_start)
        req = SessionStartRequest(
            competency_node="int_01_elevator_pitch",
            client_start_id="live-reclaim-start",
            confirm=True,
        )
        request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))

        old_task = asyncio.create_task(routes.start(req, request))
        await first_started.wait()
        store.start_requests[("test_user", req.client_start_id)]["updated_at"] = time.time() - 10_000
        retry_response = await routes.start(req, request)
        release_first.set()
        old_result = await asyncio.gather(old_task, return_exceptions=True)

        return retry_response, old_result[0]

    retry_response, old_result = asyncio.run(scenario())
    row = store.start_requests[("test_user", "live-reclaim-start")]

    assert retry_response.session_id
    assert old_result.session_id == retry_response.session_id
    assert row["status"] == "completed"
    assert row["session_id"] == retry_response.session_id
    runtime = store.session_runtime[retry_response.session_id]
    assert runtime["state_snapshot"]["candidate_marker"] == "new"
    assert store.session_messages[retry_response.session_id][0]["content"] == "new candidate"
    assert store.profiles["test_user"]["credits"] == 450
    assert [tx["delta"] for tx in store.credit_transactions] == [-50]


def test_claimed_session_commit_rejects_old_generation_before_any_write(store):
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    first = asyncio.run(
        store.begin_start_request("test_user", "claimed-commit", "request-hash")
    )
    store.start_requests[("test_user", "claimed-commit")]["status"] = "failed"
    current = asyncio.run(
        store.reset_start_request("test_user", "claimed-commit", "request-hash")
    )
    assert current["claim_generation"] > first["claim_generation"]

    committed = asyncio.run(
        store.commit_claimed_session_start(
            user_id="test_user",
            client_start_id="claimed-commit",
            claim_generation=first["claim_generation"],
            session_record={
                "session_id": "old-session",
                "user_id": "test_user",
                "task_type": "interview_prep",
                "module_id": "interview",
                "node_id": "int_01_elevator_pitch",
                "test_mode": False,
                "career_context": {},
                "scenario_config": {},
                "persona_roster": [],
                "context_hash": "default",
            },
            runtime_record={
                "session_id": "old-session",
                "user_id": "test_user",
                "current_node": "int_01_elevator_pitch",
                "module_id": "interview",
                "task_type": "interview_prep",
                "test_mode": False,
                "status": "active",
                "state_snapshot": {"candidate_marker": "old"},
                "pending_transition": None,
                "session_version": 1,
            },
            messages=[{"role": "assistant", "content": "old candidate"}],
            response_json={"session_id": "old-session"},
        )
    )

    assert committed is False
    assert "old-session" not in store.sessions
    assert "old-session" not in store.session_runtime
    assert "old-session" not in store.session_messages


def test_stale_generation_cannot_mutate_credit_ledger(store):
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    store.profiles["test_user"]["credits"] = 500
    first = asyncio.run(
        store.begin_start_request("test_user", "claimed-refund", "request-hash")
    )
    charged = asyncio.run(
        store.deduct_credits_once(
            "test_user",
            50,
            "attempt_meter",
            "session_start:claimed-refund",
        )
    )
    assert charged is True
    store.start_requests[("test_user", "claimed-refund")]["status"] = "failed"
    current = asyncio.run(
        store.reset_start_request("test_user", "claimed-refund", "request-hash")
    )
    assert current["claim_generation"] > first["claim_generation"]

    compensated = asyncio.run(
        store.compensate_claimed_attempt_charge(
            user_id="test_user",
            client_start_id="claimed-refund",
            claim_generation=first["claim_generation"],
            amount=50,
            charge_key="session_start:claimed-refund",
            debit_reason="attempt_meter",
            refund_reason="refund",
            error_code="session_start_failed",
        )
    )

    assert compensated is False
    assert store.profiles["test_user"]["credits"] == 450
    assert [tx["delta"] for tx in store.credit_transactions] == [-50]
    assert ("test_user", "session_start:claimed-refund") in store.idempotent_charges
    assert store.start_requests[("test_user", "claimed-refund")]["status"] == "in_progress"


def test_failed_access_start_cannot_refund_an_unlock_owned_by_another_start(monkeypatch, store):
    from app.api import routes
    from app.billing.gate import GateDecision
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    store.profiles["test_user"]["credits"] = 500
    calls = {"count": 0}

    async def access_gate(*_args, **_kwargs):
        return GateDecision(False, 40, "feature", "communication", True, False, "access_unlock")

    async def succeed_then_fail(user_id, node_id, session_id=None, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("second start failed")
        return session_id, {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": node_id,
            "task_type": "interview_prep",
            "module_id": "interview",
            "current_mastery": 0.0,
            "session_version": 1,
            "status": "active",
            "messages": [],
        }

    monkeypatch.setattr(routes, "resolve_gate", access_gate)
    monkeypatch.setattr(svc, "start_session", succeed_then_fail)
    request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))
    first = SessionStartRequest(
        competency_node="int_01_elevator_pitch",
        client_start_id="unlock-winner",
        confirm=True,
    )
    second = SessionStartRequest(
        competency_node="int_01_elevator_pitch",
        client_start_id="unlock-loser",
        confirm=True,
        reattempt_confirmed=True,
    )

    asyncio.run(routes.start(first, request))
    with pytest.raises(RuntimeError, match="second start failed"):
        asyncio.run(routes.start(second, request))

    assert store.profiles["test_user"]["credits"] == 460
    assert ("test_user", "feature", "communication") in store.unlocks
    assert [tx["delta"] for tx in store.credit_transactions] == [-40]


def test_failed_access_purchaser_keeps_unlock_after_an_uncharged_retry_succeeds(monkeypatch, store):
    from app.api import routes
    from app.billing.gate import GateDecision
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio

    async def scenario():
        await store.ensure_profile("test_user")
        store.profiles["test_user"]["credits"] = 500
        winner_started = asyncio.Event()
        release_winner = asyncio.Event()
        calls = {"count": 0}

        async def access_gate(*_args, **_kwargs):
            return GateDecision(False, 40, "feature", "communication", True, False, "access_unlock")

        async def fail_winner_then_succeed_retry(user_id, node_id, session_id=None, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                winner_started.set()
                await release_winner.wait()
                raise RuntimeError("purchasing start failed")
            return session_id, {
                "session_id": session_id,
                "user_id": user_id,
                "competency_node": node_id,
                "task_type": "interview_prep",
                "module_id": "interview",
                "current_mastery": 0.0,
                "session_version": 1,
                "status": "active",
                "messages": [],
            }

        monkeypatch.setattr(routes, "resolve_gate", access_gate)
        monkeypatch.setattr(svc, "start_session", fail_winner_then_succeed_retry)
        request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))
        winner = SessionStartRequest(
            competency_node="int_01_elevator_pitch",
            client_start_id="unlock-purchaser",
            confirm=True,
            reattempt_confirmed=True,
        )
        retry = SessionStartRequest(
            competency_node="int_01_elevator_pitch",
            client_start_id="unlock-consumer",
            confirm=True,
            reattempt_confirmed=True,
        )

        winner_task = asyncio.create_task(routes.start(winner, request))
        await winner_started.wait()
        retry_response = await routes.start(retry, request)
        release_winner.set()
        winner_result = (await asyncio.gather(winner_task, return_exceptions=True))[0]
        return retry_response, winner_result

    retry_response, winner_result = asyncio.run(scenario())

    assert retry_response.session_id in store.sessions
    assert isinstance(winner_result, RuntimeError)
    assert store.profiles["test_user"]["credits"] == 460
    assert ("test_user", "feature", "communication") in store.unlocks
    assert [tx["delta"] for tx in store.credit_transactions] == [-40]


def test_start_retry_recovers_after_process_loss_during_refund(monkeypatch, store):
    from app.api import routes
    from app.billing.gate import GateDecision
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio
    import time

    asyncio.run(store.ensure_profile("test_user"))
    store.profiles["test_user"]["credits"] = 500

    async def paid_gate(*_args, **_kwargs):
        return GateDecision(False, 50, "attempt", "int_01_elevator_pitch", False, False, "attempt_meter")

    calls = {"start": 0}

    async def fail_then_start(user_id, node_id, session_id=None, **_kwargs):
        calls["start"] += 1
        if calls["start"] == 1:
            raise RuntimeError("start failed before compensation")
        return session_id, {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    async def crash_before_refund(*_args, **_kwargs):
        raise SystemExit("process lost during refund")

    monkeypatch.setattr(routes, "resolve_gate", paid_gate)
    monkeypatch.setattr(svc, "start_session", fail_then_start)
    monkeypatch.setattr(store, "compensate_claimed_attempt_charge", crash_before_refund)
    req = SessionStartRequest(
        competency_node="int_01_elevator_pitch",
        client_start_id="refund-crash-start",
        confirm=True,
    )
    request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))

    with pytest.raises(SystemExit, match="process lost during refund"):
        asyncio.run(routes.start(req, request))

    row = store.start_requests[("test_user", req.client_start_id)]
    assert row["status"] == "in_progress"
    row["updated_at"] = time.time() - 10_000
    response = asyncio.run(routes.start(req, request))

    assert response.session_id
    assert store.start_requests[("test_user", req.client_start_id)]["status"] == "completed"
    assert store.profiles["test_user"]["credits"] == 450
    assert [tx["delta"] for tx in store.credit_transactions] == [-50]


def test_graceful_failed_paid_start_refunds_and_rearms_idempotency_key(monkeypatch, store):
    from app.api import routes
    from app.billing.gate import GateDecision
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    store.profiles["test_user"]["credits"] = 500

    async def paid_gate(*_args, **_kwargs):
        return GateDecision(False, 50, "attempt", "int_01_elevator_pitch", False, False, "attempt_meter")

    calls = {"count": 0}

    async def fail_then_start(user_id, node_id, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated start failure")
        return "retried-paid-start", {
            "session_id": "retried-paid-start",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(routes, "resolve_gate", paid_gate)
    monkeypatch.setattr(svc, "start_session", fail_then_start)
    req = SessionStartRequest(
        competency_node="int_01_elevator_pitch",
        client_start_id="refundable-paid-start",
        confirm=True,
    )
    request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))

    with pytest.raises(RuntimeError):
        asyncio.run(routes.start(req, request))
    assert store.profiles["test_user"]["credits"] == 500
    assert ("test_user", "session_start:refundable-paid-start") not in store.idempotent_charges
    assert [row["delta"] for row in store.credit_transactions] == [-50, 50]
    assert sum(row["delta"] for row in store.credit_transactions) == 0

    response = asyncio.run(routes.start(req, request))

    assert response.session_id == "retried-paid-start"
    assert store.profiles["test_user"]["credits"] == 450
    assert ("test_user", "session_start:refundable-paid-start") in store.idempotent_charges
    assert [row["delta"] for row in store.credit_transactions] == [-50, 50, -50]
    assert sum(row["delta"] for row in store.credit_transactions) == -50


def test_start_latch_rejects_second_client_for_same_source_transition(store):
    import asyncio

    first = asyncio.run(store.begin_start_request(
        "test_user",
        "source-start-a",
        "hash-a",
        source_session_id="source-session",
        source_transition_id="transition-1",
    ))
    second = asyncio.run(store.begin_start_request(
        "test_user",
        "source-start-b",
        "hash-b",
        source_session_id="source-session",
        source_transition_id="transition-1",
    ))

    assert first["accepted"] is True
    assert second["accepted"] is False
    assert second["status"] == "source_transition_consumed"
    assert second["accepted_client_start_id"] == "source-start-a"


def test_reset_start_request_reports_consumed_source_transition(store):
    import asyncio
    import time

    first = asyncio.run(store.begin_start_request(
        "test_user",
        "source-reset-winner",
        "hash-a",
        source_session_id="source-session",
        source_transition_id="transition-reset",
    ))
    store.start_requests[("test_user", "source-reset-loser")] = {
        "user_id": "test_user",
        "client_start_id": "source-reset-loser",
        "request_hash": "hash-b",
        "status": "failed",
        "session_id": None,
        "response_json": None,
        "error_code": "stale_in_progress",
        "source_session_id": "source-session",
        "source_transition_id": "transition-reset",
        "claim_generation": 1,
        "created_at": time.time() - 100,
        "updated_at": time.time() - 100,
    }

    reset = asyncio.run(store.reset_start_request(
        "test_user",
        "source-reset-loser",
        "hash-b",
        source_session_id="source-session",
        source_transition_id="transition-reset",
    ))

    assert first["accepted"] is True
    assert reset["accepted"] is False
    assert reset["status"] == "source_transition_consumed"
    assert reset["accepted_client_start_id"] == "source-reset-winner"
    assert store.start_requests[("test_user", "source-reset-loser")]["status"] == "failed"


def test_route_replays_completed_source_transition_found_during_reset(store):
    from app.api import routes
    from app.models import SessionStartRequest
    from fastapi.testclient import TestClient
    import asyncio
    import time

    asyncio.run(store.ensure_profile("test_user"))
    req = SessionStartRequest(
        competency_node="int_02_strengths",
        client_start_id="source-route-loser",
        source_session_id="source-session",
        source_transition_id="transition-route-reset",
        source_action="advance",
    )
    request_hash = routes._start_request_hash(req)
    winner = asyncio.run(store.begin_start_request(
        "test_user",
        "source-route-winner",
        request_hash,
        source_session_id=req.source_session_id,
        source_transition_id=req.source_transition_id,
    ))
    response_payload = {
        "session_id": "winner-session",
        "node_title": "Back a Strength With Evidence",
        "first_message": "",
        "current_mastery": 0.0,
        "display_status": "active",
        "node_mastered": False,
        "readiness_score": 0.0,
        "best_independent_score": 0.0,
    }
    asyncio.run(store.complete_start_request(
        "test_user",
        "source-route-winner",
        "completed",
        session_id="winner-session",
        response_json=response_payload,
        claim_generation=winner["claim_generation"],
    ))
    store.start_requests[("test_user", req.client_start_id)] = {
        "user_id": "test_user",
        "client_start_id": req.client_start_id,
        "request_hash": request_hash,
        "status": "failed",
        "session_id": None,
        "response_json": None,
        "error_code": "stale_in_progress",
        "source_session_id": req.source_session_id,
        "source_transition_id": req.source_transition_id,
        "claim_generation": 1,
        "created_at": time.time() - 100,
        "updated_at": time.time() - 100,
    }

    response = TestClient(app).post(
        "/session/start",
        json=req.model_dump(),
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "winner-session"
    assert response.json()["resumed"] is True


@pytest.mark.parametrize("consumed_branch", ["begin", "reset"])
def test_completed_different_client_replay_reconciles_pending_source_handoff(
    monkeypatch,
    store,
    consumed_branch,
):
    from app.api import routes
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    import asyncio
    import time

    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    source_session_id = f"different-client-source-{consumed_branch}"
    source_transition_id = f"different-client-transition-{consumed_branch}"
    winner_client_start_id = f"different-client-winner-{consumed_branch}"
    loser_client_start_id = f"different-client-loser-{consumed_branch}"
    winner_session_id = f"different-client-target-{consumed_branch}"
    req = SessionStartRequest(
        competency_node="int_02_strengths",
        client_start_id=loser_client_start_id,
        source_session_id=source_session_id,
        source_transition_id=source_transition_id,
        source_action="advance",
    )
    request_hash = routes._start_request_hash(req)
    winner = asyncio.run(store.begin_start_request(
        "test_user",
        winner_client_start_id,
        request_hash,
        source_session_id=source_session_id,
        source_transition_id=source_transition_id,
    ))
    response_payload = {
        "session_id": winner_session_id,
        "node_title": "Back a Strength With Evidence",
        "first_message": "",
        "current_mastery": 0.0,
        "display_status": "active",
        "node_mastered": False,
        "readiness_score": 0.0,
        "best_independent_score": 0.0,
    }
    asyncio.run(store.complete_start_request(
        "test_user",
        winner_client_start_id,
        "completed",
        session_id=winner_session_id,
        response_json=response_payload,
        claim_generation=winner["claim_generation"],
    ))

    source_state = svc._new_state(
        "test_user",
        source_session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": source_transition_id,
        "from_node": "int_01_elevator_pitch",
        "to_node": "int_02_strengths",
        "status": "awaiting_next_opening",
    }
    source_state["input_allowed"] = False
    source_state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[source_session_id] = source_state

    if consumed_branch == "reset":
        store.start_requests[("test_user", loser_client_start_id)] = {
            "user_id": "test_user",
            "client_start_id": loser_client_start_id,
            "request_hash": request_hash,
            "status": "failed",
            "session_id": None,
            "response_json": None,
            "error_code": "stale_in_progress",
            "source_session_id": source_session_id,
            "source_transition_id": source_transition_id,
            "claim_generation": 1,
            "created_at": time.time() - 100,
            "updated_at": time.time() - 100,
        }
    else:
        original_begin = store.begin_start_request

        async def begin_with_winner_row(*args, **kwargs):
            result = await original_begin(*args, **kwargs)
            if result.get("status") != "source_transition_consumed":
                return result
            winner_row = dict(store.start_requests[("test_user", winner_client_start_id)])
            winner_row.update({
                "accepted": False,
                "request_mismatch": False,
                "consumed_status": winner_row["status"],
                "status": "source_transition_consumed",
                "accepted_client_start_id": winner_client_start_id,
            })
            return winner_row

        monkeypatch.setattr(store, "begin_start_request", begin_with_winner_row)

    async def fail_if_started(*_args, **_kwargs):
        raise AssertionError("completed winner must replay without starting another session")

    monkeypatch.setattr(svc, "start_session", fail_if_started)

    response = TestClient(app).post(
        "/session/start",
        json=req.model_dump(),
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == winner_session_id
    assert response.json()["resumed"] is True
    assert source_state["pending_node_transition"] is None
    assert source_state["handoff_session_id"] == winner_session_id
    assert source_state["status"] == "ended"
    assert source_state["session_over"] is True
    assert source_state["block_reason"] == "transition_handed_off"


def test_metered_charge_fails_closed_without_idempotent_store_contract():
    from app.billing.gate import GateDecision, charge
    import asyncio

    class UnsafeStore:
        async def deduct_credits(self, *_args, **_kwargs):
            raise AssertionError("non-idempotent debit must not run")

    decision = GateDecision(
        False,
        50,
        "attempt",
        "int_01_elevator_pitch",
        False,
        False,
        "attempt_meter",
    )

    with pytest.raises(RuntimeError, match="storage_missing_idempotent_credit_debit"):
        asyncio.run(
            charge(
                UnsafeStore(),
                "test_user",
                decision,
                idempotency_key="session_start:unsafe",
            )
        )


def test_session_start_requires_client_start_id(store):
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={"competency_node": "int_01_elevator_pitch"},
        headers=AUTH,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "client_start_id_required"


def test_session_start_rejects_locked_future_node(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    calls = {"count": 0}

    async def fake_start(*_args, **_kwargs):
        calls["count"] += 1
        return "should-not-start", {"session_id": "should-not-start"}

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_03_weakness_framing",
            "client_start_id": "locked-future-node",
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "locked_node"
    assert response.json()["detail"]["active_node_id"] == "int_01_elevator_pitch"
    assert calls["count"] == 0


def test_session_start_allows_test_mode_future_scenario(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    calls = {"count": 0, "test_mode": None}

    async def fake_start(_user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        calls["count"] += 1
        calls["test_mode"] = test_mode
        return "test-mode-session", {
            "session_id": "test-mode-session",
            "user_id": "test_user",
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_03_weakness_framing",
            "test_mode": True,
            "client_start_id": "test-mode-future-node",
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "test-mode-session"
    assert calls == {"count": 1, "test_mode": True}


def test_advancing_turn_replays_after_pending_transition(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_run_turn(session_id, _user_input, **_kwargs):
        calls["count"] += 1
        state = svc.get_state(session_id)
        assert state is not None
        state["pending_node_transition"] = {
            "transition_id": "transition-1",
            "from_node": "int_01_elevator_pitch",
            "from_title": "Tell Me About Yourself",
            "to_node": "int_02_strength_with_evidence",
            "to_title": "Support Strengths With Evidence",
            "status": "awaiting_next_opening",
        }
        state["input_allowed"] = False
        state["block_reason"] = "awaiting_next_skill"
        state["session_version"] = 2
        yield svc.ProgressUpdate(
            node_id="int_01_elevator_pitch",
            mastery=0.8,
            readiness_score=0.86,
            clean_streak=2,
            attempts=2,
        )
        yield svc.NodeAdvance(
            from_node="int_01_elevator_pitch",
            to_node="int_02_strength_with_evidence",
        )

    calls = {"count": 0}
    monkeypatch.setattr(svc, "run_turn", fake_run_turn)

    session_id = "advancing-replay-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state
    asyncio.run(store.ensure_profile("test_user"))

    payload = {
        "session_id": session_id,
        "user_input": "strong answer",
        "client_turn_id": "advance-client-turn-1",
        "expected_session_version": 1,
    }
    client = TestClient(app)
    first = client.post("/session/turn", json=payload, headers=AUTH)
    second = client.post("/session/turn", json=payload, headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert "event: node_advance" in first.text
    assert "event: node_advance" in second.text
    assert calls["count"] == 1


def test_session_start_replays_duplicate_client_start_id(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    calls = {"count": 0}

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        calls["count"] += 1
        return "session-start-once", {
            "session_id": "session-start-once",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    payload = {
        "competency_node": "int_01_elevator_pitch",
        "client_start_id": "start-id-1",
    }
    client = TestClient(app)
    first = client.post("/session/start", json=payload, headers=AUTH)
    second = client.post("/session/start", json=payload, headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["session_id"] == "session-start-once"
    assert second.json()["session_id"] == "session-start-once"
    assert second.json()["resumed"] is True
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_replace_session_messages_takes_advisory_lock_before_delete():
    from app.db import repo

    class FakeSession:
        def __init__(self):
            self.sql: list[str] = []
            self.commits = 0

        async def execute(self, statement, *_args, **_kwargs):
            self.sql.append(str(statement))

        async def commit(self):
            self.commits += 1

    session = FakeSession()

    await repo.replace_session_messages(
        session,
        "deadlock-safe-session",
        [{"role": "assistant", "content": "Opening prompt"}],
    )

    assert session.commits == 1
    assert "pg_advisory_xact_lock" in session.sql[0]
    delete_index = next(index for index, sql in enumerate(session.sql) if "DELETE FROM session_messages" in sql)
    assert delete_index > 0


def test_session_start_resumes_active_same_node_after_reload(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    calls = {"count": 0}

    async def fake_start(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("active same-node sessions should be resumed, not restarted")

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    state = svc._new_state(
        "test_user",
        "active-prep-session",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["current_mastery"] = 0.42
    state["status"] = "active"
    asyncio.run(store.upsert_session_runtime(
        session_id="active-prep-session",
        user_id="test_user",
        current_node="int_01_elevator_pitch",
        module_id="interview",
        task_type="interview_prep",
        test_mode=False,
        status="active",
        state_snapshot=state,
        pending_transition=None,
        session_version=1,
    ))
    svc.SessionStore.pop("active-prep-session", None)

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": "fresh-after-reload",
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "active-prep-session"
    assert response.json()["resumed"] is True
    assert response.json()["current_mastery"] == 0.42
    assert response.json()["display_status"] == "active"
    assert response.json()["node_mastered"] is False
    assert response.json()["readiness_score"] == 0.0
    assert calls["count"] == 0
    latch = store.start_requests[("test_user", "fresh-after-reload")]
    assert latch["status"] == "completed"
    assert latch["session_id"] == "active-prep-session"

    mismatched = client.post(
        "/session/start",
        json={
            "competency_node": "int_02_strength_with_evidence",
            "client_start_id": "fresh-after-reload",
        },
        headers=AUTH,
    )
    assert mismatched.status_code == 409
    assert mismatched.json()["detail"]["code"] == "client_start_id_reused_with_different_payload"


def test_session_start_does_not_resume_stale_active_session_for_ready_career_node(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_start(*_args, **_kwargs):
        raise AssertionError("completed career nodes should require reattempt confirmation")

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    asyncio.run(store.upsert_mastery(
        user_id="test_user",
        node_id="int_01_elevator_pitch",
        ema=0.85,
        attempts=3,
        clean_pass=True,
        node_completed=True,
        node_mastered=False,
        display_status="ready_to_advance",
    ))

    state = svc._new_state(
        "test_user",
        "stale-active-prep-session",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["current_mastery"] = 0.26
    state["status"] = "active"
    asyncio.run(store.upsert_session_runtime(
        session_id="stale-active-prep-session",
        user_id="test_user",
        current_node="int_01_elevator_pitch",
        module_id="interview",
        task_type="interview_prep",
        test_mode=False,
        status="active",
        state_snapshot=state,
        pending_transition=None,
        session_version=1,
    ))
    svc.SessionStore.pop("stale-active-prep-session", None)

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": "stale-ready-start",
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "completed_node"


def test_node_resume_prefers_newer_durable_session_over_stale_process_cache(store):
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    stale_local = svc._new_state(
        "test_user",
        "stale-local-node-resume",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    stale_local["status"] = "active"
    stale_local["last_seen_at"] = 100.0
    svc.SessionStore[stale_local["session_id"]] = stale_local

    durable_newer = svc._new_state(
        "test_user",
        "newer-durable-node-resume",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    durable_newer["status"] = "active"
    durable_newer["last_seen_at"] = 200.0
    asyncio.run(store.upsert_session_runtime(
        session_id=durable_newer["session_id"],
        user_id="test_user",
        current_node=durable_newer["competency_node"],
        module_id="interview",
        task_type="interview_prep",
        test_mode=False,
        status="active",
        state_snapshot=durable_newer,
        pending_transition=None,
        session_version=1,
    ))
    store.session_runtime[durable_newer["session_id"]]["updated_at"] = 200.0

    resumed = asyncio.run(svc.get_resumable_active_session_for_start(
        "test_user",
        "int_01_elevator_pitch",
        test_mode=False,
    ))

    assert resumed is not None
    assert resumed[0] == "newer-durable-node-resume"


def test_progression_map_uses_durable_active_session_after_reload(store):
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    for node_id in ("int_01_elevator_pitch", "int_02_strength_with_evidence"):
        asyncio.run(store.upsert_mastery(
            user_id="test_user",
            node_id=node_id,
            ema=0.82,
            attempts=3,
            clean_pass=True,
            node_completed=True,
            display_status="ready_to_advance",
        ))

    state = svc._new_state(
        "test_user",
        "active-map-session",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["status"] = "active"
    asyncio.run(store.upsert_session_runtime(
        session_id="active-map-session",
        user_id="test_user",
        current_node="int_04_star_behavioral",
        module_id="interview",
        task_type="interview_prep",
        test_mode=False,
        status="active",
        state_snapshot=state,
        pending_transition=None,
        session_version=1,
    ))
    svc.SessionStore.pop("active-map-session", None)

    nodes = asyncio.run(svc.get_progression_map("test_user", "interview"))
    active_ids = [node["node_id"] for node in nodes if node["display_status"] == "active"]

    assert active_ids == ["int_04_star_behavioral"]


def test_state_snapshot_exposes_authoritative_completed_turn_id():
    from app.api import routes
    from app.services import session_service as svc

    state = svc._new_state(
        "test_user",
        "completed-turn-snapshot",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state["last_turn_id"] = "client-turn-completed"
    state["last_turn_status"] = "completed"
    state["active_turn_id"] = None
    state["active_turn_status"] = "completed"

    snapshot = routes._state_snapshot(state)

    assert snapshot["last_turn"] == {
        "client_turn_id": "client-turn-completed",
        "status": "completed",
    }
    assert snapshot["active_turn"] is None


def test_progression_map_uses_latest_durable_active_session_across_module(store):
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))

    older = svc._new_state(
        "test_user",
        "older-active-map-session",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    newer = svc._new_state(
        "test_user",
        "newer-active-map-session",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    for state in (older, newer):
        state["status"] = "active"
        asyncio.run(store.upsert_session_runtime(
            session_id=state["session_id"],
            user_id="test_user",
            current_node=state["competency_node"],
            module_id="interview",
            task_type="interview_prep",
            test_mode=False,
            status="active",
            state_snapshot=state,
            pending_transition=None,
            session_version=1,
        ))
        svc.SessionStore.pop(state["session_id"], None)

    store.session_runtime["older-active-map-session"]["updated_at"] = 100.0
    store.session_runtime["newer-active-map-session"]["updated_at"] = 200.0

    nodes = asyncio.run(svc.get_progression_map("test_user", "interview"))
    active_ids = [node["node_id"] for node in nodes if node["display_status"] == "active"]

    assert active_ids == ["int_04_star_behavioral"]


def test_progression_map_prefers_newer_durable_session_over_stale_process_cache(store):
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    stale_local = svc._new_state(
        "test_user",
        "stale-local-map-session",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    stale_local["status"] = "active"
    stale_local["last_seen_at"] = 100.0
    svc.SessionStore[stale_local["session_id"]] = stale_local

    durable_newer = svc._new_state(
        "test_user",
        "newer-durable-map-session",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    durable_newer["status"] = "active"
    durable_newer["last_seen_at"] = 200.0
    asyncio.run(store.upsert_session_runtime(
        session_id=durable_newer["session_id"],
        user_id="test_user",
        current_node=durable_newer["competency_node"],
        module_id="interview",
        task_type="interview_prep",
        test_mode=False,
        status="active",
        state_snapshot=durable_newer,
        pending_transition=None,
        session_version=1,
    ))
    store.session_runtime[durable_newer["session_id"]]["updated_at"] = 200.0

    nodes = asyncio.run(svc.get_progression_map("test_user", "interview"))
    active_ids = [node["node_id"] for node in nodes if node["display_status"] == "active"]

    assert active_ids == ["int_04_star_behavioral"]


def test_progression_map_ignores_stale_active_rows_and_returns_one_current_node(store):
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    for node_id in (
        "int_01_elevator_pitch",
        "int_02_strength_with_evidence",
        "int_03_weakness_framing",
    ):
        asyncio.run(store.upsert_mastery(
            user_id="test_user",
            node_id=node_id,
            ema=0.82,
            attempts=3,
            clean_pass=True,
            node_completed=True,
            display_status="ready_to_advance",
        ))
    for node_id in ("int_04_star_behavioral", "int_05_why_this_role"):
        asyncio.run(store.upsert_mastery(
            user_id="test_user",
            node_id=node_id,
            ema=0.2,
            attempts=1,
            clean_pass=False,
            node_completed=False,
            display_status="active",
        ))

    nodes = asyncio.run(svc.get_progression_map("test_user", "interview"))
    active_ids = [node["node_id"] for node in nodes if node["display_status"] == "active"]
    by_id = {node["node_id"]: node for node in nodes}

    assert active_ids == ["int_04_star_behavioral"]
    assert by_id["int_05_why_this_role"]["display_status"] == "locked"


def test_keep_practicing_starts_same_skill_reattempt_and_closes_source_transition(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    captured = {}

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        captured.update({"user_id": user_id, "node_id": node_id, "reattempt": reattempt})
        return "same-skill-reattempt", {
            "session_id": "same-skill-reattempt",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.8,
            "display_status": "ready_to_advance",
            "node_mastered": False,
            "readiness_score": 0.8,
            "best_independent_score": 0.9,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    asyncio.run(store.upsert_mastery(
        user_id="test_user",
        node_id="int_01_elevator_pitch",
        ema=0.8,
        attempts=3,
        clean_pass=True,
        node_completed=True,
        display_status="ready_to_advance",
    ))

    source_state = svc._new_state(
        "test_user",
        "completed-source-for-practice",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "keep-practicing-transition",
        "from_node": "int_01_elevator_pitch",
        "from_title": "Tell Me About Yourself",
        "to_node": "int_02_strength_with_evidence",
        "to_title": "Back a Strength With Evidence",
        "status": "awaiting_next_opening",
    }
    source_state["input_allowed"] = False
    source_state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[source_state["session_id"]] = source_state

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": "keep-practicing-start",
            "source_session_id": source_state["session_id"],
            "source_transition_id": "keep-practicing-transition",
            "source_action": "reattempt",
            "reattempt_confirmed": True,
            "confirm": True,
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "same-skill-reattempt"
    assert captured == {
        "user_id": "test_user",
        "node_id": "int_01_elevator_pitch",
        "reattempt": True,
    }
    assert source_state["pending_node_transition"] is None
    assert source_state["status"] == "ended"
    assert source_state["handoff_session_id"] == "same-skill-reattempt"


def test_source_transition_rejects_conflicting_advance_and_reattempt_intents(store):
    from app.api import routes
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    asyncio.run(store.upsert_mastery(
        user_id="test_user",
        node_id="int_01_elevator_pitch",
        ema=0.8,
        attempts=3,
        clean_pass=True,
        node_completed=True,
        display_status="ready_to_advance",
    ))
    source_state = svc._new_state(
        "test_user",
        "source-with-conflicting-actions",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "one-action-only",
        "from_node": "int_01_elevator_pitch",
        "to_node": "int_02_strength_with_evidence",
        "status": "awaiting_next_opening",
    }
    source_state["input_allowed"] = False
    source_state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[source_state["session_id"]] = source_state

    advance = SessionStartRequest(
        competency_node="int_02_strength_with_evidence",
        client_start_id="advance-won",
        source_session_id=source_state["session_id"],
        source_transition_id="one-action-only",
        source_action="advance",
        confirm=True,
    )
    asyncio.run(store.begin_start_request(
        "test_user",
        advance.client_start_id,
        routes._start_request_hash(advance),
        source_session_id=advance.source_session_id,
        source_transition_id=advance.source_transition_id,
    ))

    response = TestClient(app).post(
        "/session/start",
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": "reattempt-lost",
            "source_session_id": source_state["session_id"],
            "source_transition_id": "one-action-only",
            "source_action": "reattempt",
            "reattempt_confirmed": True,
            "confirm": True,
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "source_transition_already_consumed"


@pytest.mark.parametrize(
    ("extra", "expected_code"),
    [
        ({"test_mode": True}, "source_transition_prep_only"),
        ({"simulation_config": {"topic": "unexpected"}}, "source_transition_prep_only"),
    ],
)
def test_same_skill_source_reattempt_rejects_test_or_simulation_mode(store, extra, expected_code):
    from app.services import session_service as svc
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    asyncio.run(store.upsert_mastery(
        user_id="test_user",
        node_id="int_01_elevator_pitch",
        ema=0.8,
        attempts=3,
        clean_pass=True,
        node_completed=True,
        display_status="ready_to_advance",
    ))
    source_state = svc._new_state(
        "test_user",
        f"invalid-reattempt-{len(extra)}",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "invalid-reattempt-transition",
        "from_node": "int_01_elevator_pitch",
        "to_node": "int_02_strength_with_evidence",
        "status": "awaiting_next_opening",
    }
    svc.SessionStore[source_state["session_id"]] = source_state

    response = TestClient(app).post(
        "/session/start",
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": f"invalid-reattempt-{next(iter(extra))}",
            "source_session_id": source_state["session_id"],
            "source_transition_id": "invalid-reattempt-transition",
            "source_action": "reattempt",
            "reattempt_confirmed": True,
            "confirm": True,
            **extra,
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == expected_code


def test_next_skill_start_hands_off_pending_source_transition(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    opening_calls = {"count": 0}

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        return "next-skill-session", {
            "session_id": "next-skill-session",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    async def fake_stream_opening(*_args, **_kwargs):
        opening_calls["count"] += 1
        yield "This old source session should not reopen."

    monkeypatch.setattr(svc, "start_session", fake_start)
    monkeypatch.setattr(svc, "stream_opening", fake_stream_opening)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    source_session_id = "completed-source-session"
    source_state = svc._new_state(
        "test_user",
        source_session_id,
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "transition-to-next",
        "from_node": "int_02_strength_with_evidence",
        "from_title": "Support Strengths With Evidence",
        "to_node": "int_03_weakness_framing",
        "to_title": "Frame a Weakness",
        "status": "awaiting_next_opening",
    }
    source_state["input_allowed"] = False
    source_state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[source_session_id] = source_state

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_03_weakness_framing",
            "client_start_id": "handoff-start-1",
            "source_session_id": source_session_id,
            "source_transition_id": "transition-to-next",
            "confirm": True,
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == "next-skill-session"
    assert source_state["pending_node_transition"] is None
    assert source_state["status"] == "ended"
    assert source_state["session_over"] is True
    assert source_state["block_reason"] == "transition_handed_off"
    assert source_state["handoff_session_id"] == "next-skill-session"

    old_turn = client.post(
        "/session/turn",
            json={
                "session_id": source_session_id,
                "user_input": "Can I keep answering here?",
                "client_turn_id": "old-session-turn-1",
                "expected_session_version": source_state["session_version"],
            },
            headers=AUTH,
        )
    assert old_turn.status_code == 409
    assert old_turn.json()["detail"]["code"] == "session_not_active"

    old_opening = client.get(
        f"/session/{source_session_id}/opening",
        headers=AUTH,
    )
    assert old_opening.status_code == 409
    assert old_opening.json()["detail"]["code"] == "session_not_active"
    assert opening_calls["count"] == 0

    restored_source = client.get(f"/session/{source_session_id}/state", headers=AUTH)
    assert restored_source.status_code == 200
    assert restored_source.json()["handoff_session_id"] == "next-skill-session"
    assert restored_source.json()["handoff_source_node"] == "int_02_strength_with_evidence"


def test_next_skill_can_advance_into_completed_target_as_reattempt(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    captured = {}

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        captured.update({"node_id": node_id, "reattempt": reattempt})
        return "next-skill-reattempt-session", {
            "session_id": "next-skill-reattempt-session",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    asyncio.run(store.upsert_mastery(
        "test_user",
        "int_03_weakness_framing",
        0.85,
        4,
        clean_pass=True,
        node_completed=True,
    ))

    source_state = svc._new_state(
        "test_user",
        "completed-target-source-session",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "advance-reattempt-transition",
        "from_node": "int_02_strength_with_evidence",
        "to_node": "int_03_weakness_framing",
        "status": "awaiting_next_opening",
    }
    source_state["input_allowed"] = False
    source_state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[source_state["session_id"]] = source_state

    response = TestClient(app).post(
        "/session/start",
        json={
            "competency_node": "int_03_weakness_framing",
            "client_start_id": "advance-completed-target",
            "source_session_id": source_state["session_id"],
            "source_transition_id": "advance-reattempt-transition",
            "source_action": "advance_reattempt",
            "reattempt_confirmed": True,
            "confirm": True,
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert captured == {"node_id": "int_03_weakness_framing", "reattempt": True}
    assert source_state["status"] == "ended"
    assert source_state["handoff_session_id"] == "next-skill-reattempt-session"


def test_next_skill_start_replays_completed_source_transition_after_client_timeout(monkeypatch, store):
    from app.api import routes
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    import asyncio

    calls = {"start": 0}

    async def fake_start(*_args, **_kwargs):
        calls["start"] += 1
        return "should-not-start-again", {}

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    source_session_id = "timeout-source-session"
    source_transition_id = "timeout-transition"
    next_session_id = "already-created-next-session"
    response_json = {
        "session_id": next_session_id,
        "node_title": "Tell a STAR Story",
        "first_message": "",
        "current_mastery": 0.0,
    }
    payload = {
        "competency_node": "int_04_star_story",
        "client_start_id": "original-confirmed-start",
        "source_session_id": source_session_id,
        "source_transition_id": source_transition_id,
        "source_action": "advance",
        "confirm": True,
    }
    store.start_requests[("test_user", "original-confirmed-start")] = {
        "user_id": "test_user",
        "client_start_id": "original-confirmed-start",
        "request_hash": routes._start_request_hash(SessionStartRequest(**payload)),
        "status": "completed",
        "session_id": next_session_id,
        "response_json": response_json,
        "error_code": None,
        "source_session_id": source_session_id,
        "source_transition_id": source_transition_id,
        "updated_at": 1_783_400_000,
    }
    source_state = svc._new_state(
        "test_user",
        source_session_id,
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = None
    source_state["status"] = "ended"
    source_state["session_over"] = True
    source_state["block_reason"] = "transition_handed_off"
    source_state["handoff_session_id"] = next_session_id
    svc.SessionStore[source_session_id] = source_state

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json=payload,
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == next_session_id
    assert response.json()["resumed"] is True
    assert calls["start"] == 0


def test_completed_start_retry_reconciles_handoff_without_restarting(monkeypatch, store):
    from app.api import routes
    from app.models import SessionStartRequest
    from app.services import session_service as svc
    from types import SimpleNamespace
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))
    source_session_id = "handoff-crash-source"
    source_transition_id = "handoff-crash-transition"
    source_state = svc._new_state(
        "test_user",
        source_session_id,
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": source_transition_id,
        "from_node": "int_02_strength_with_evidence",
        "to_node": "int_03_weakness_framing",
        "status": "awaiting_next_opening",
    }
    svc.SessionStore[source_session_id] = source_state

    calls = {"start": 0, "handoff": 0}
    original_handoff = svc.handoff_transition_to_session

    async def fake_start(user_id, node_id, session_id=None, **_kwargs):
        calls["start"] += 1
        assert session_id
        return session_id, {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    async def crash_once_then_handoff(*args, **kwargs):
        calls["handoff"] += 1
        if calls["handoff"] == 1:
            raise RuntimeError("simulated handoff persistence failure")
        await original_handoff(*args, **kwargs)

    monkeypatch.setattr(svc, "start_session", fake_start)
    monkeypatch.setattr(svc, "handoff_transition_to_session", crash_once_then_handoff)
    req = SessionStartRequest(
        competency_node="int_03_weakness_framing",
        client_start_id="handoff-crash-client-start",
        source_session_id=source_session_id,
        source_transition_id=source_transition_id,
        source_action="advance",
        confirm=True,
    )
    request = SimpleNamespace(state=SimpleNamespace(user_id="test_user"))

    with pytest.raises(RuntimeError, match="handoff persistence failure"):
        asyncio.run(routes.start(req, request))

    start_row = store.start_requests[("test_user", req.client_start_id)]
    assert start_row["status"] == "completed"
    target_session_id = start_row["session_id"]

    response = asyncio.run(routes.start(req, request))

    assert response.session_id == target_session_id
    assert response.resumed is True
    assert calls == {"start": 1, "handoff": 2}
    assert source_state["handoff_session_id"] == target_session_id
    assert source_state["status"] == "ended"


def test_handoff_retry_reconciles_session_closure_after_partial_persistence(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    source_state = svc._new_state(
        "test_user",
        "partial-handoff-source",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "partial-handoff-transition",
        "from_node": "int_02_strength_with_evidence",
        "to_node": "int_03_weakness_framing",
        "status": "awaiting_next_opening",
    }
    svc.SessionStore[source_state["session_id"]] = source_state

    original_end = store.end_session
    calls = {"end": 0}

    async def fail_end_once(*args, **kwargs):
        calls["end"] += 1
        if calls["end"] == 1:
            raise RuntimeError("session row closure failed")
        await original_end(*args, **kwargs)

    monkeypatch.setattr(store, "end_session", fail_end_once)
    args = (
        source_state["session_id"],
        "partial-handoff-transition",
        "partial-handoff-target",
        "int_03_weakness_framing",
        "test_user",
    )

    with pytest.raises(RuntimeError, match="session row closure failed"):
        asyncio.run(svc.handoff_transition_to_session(*args))
    asyncio.run(svc.handoff_transition_to_session(*args))

    assert calls["end"] == 2
    assert source_state["last_handed_off_transition"]["handoff_session_id"] == "partial-handoff-target"
    assert source_state["status"] == "ended"


def test_next_skill_source_transition_records_attempt_only_after_new_opening(monkeypatch, store):
    from app.content import registry
    from app.services import session_service as svc
    import asyncio

    async def fake_stream_generation(_spec):
        yield "Fresh next skill opening."

    monkeypatch.setattr(svc, "stream_generation", fake_stream_generation)
    asyncio.run(store.ensure_profile("test_user"))

    source_session_id = "source-session-attempt-ledger"
    source_state = svc._new_state(
        "test_user",
        source_session_id,
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "transition-for-ledger",
        "from_node": "int_02_strength_with_evidence",
        "from_title": "Support Strengths With Evidence",
        "to_node": "int_03_weakness_framing",
        "to_title": "Frame a Weakness",
        "status": "awaiting_next_opening",
    }
    source_state["input_allowed"] = False
    source_state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[source_session_id] = source_state

    client = TestClient(app)
    start = client.post(
        "/session/start",
        json={
            "competency_node": "int_03_weakness_framing",
            "client_start_id": "next-ledger-start",
            "source_session_id": source_session_id,
            "source_transition_id": "transition-for-ledger",
        },
        headers=AUTH,
    )

    assert start.status_code == 200
    next_session_id = start.json()["session_id"]
    assert asyncio.run(store.count_attempts("test_user", registry.INT_ID)) == 0

    opening = client.get(f"/session/{next_session_id}/opening", headers=AUTH)

    assert opening.status_code == 200
    assert "Fresh next skill opening." in opening.text
    assert asyncio.run(store.count_attempts("test_user", registry.INT_ID)) == 1


def test_pending_transition_opening_requires_session_start(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    opening_calls = {"count": 0}

    async def fake_stream_opening(*_args, **_kwargs):
        opening_calls["count"] += 1
        yield "This would bypass the next-skill start gate."

    monkeypatch.setattr(svc, "stream_opening", fake_stream_opening)
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "pending-transition-source-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    state["pending_node_transition"] = {
        "transition_id": "transition-needs-start",
        "from_node": "int_02_strength_with_evidence",
        "from_title": "Support Strengths With Evidence",
        "to_node": "int_03_weakness_framing",
        "to_title": "Frame a Weakness",
        "status": "awaiting_next_opening",
    }
    state["input_allowed"] = False
    state["block_reason"] = "awaiting_next_skill"
    svc.SessionStore[session_id] = state

    client = TestClient(app)
    response = client.get(
        f"/session/{session_id}/opening?transition_id=transition-needs-start",
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "next_skill_requires_session_start"
    assert response.json()["detail"]["next_node"] == "int_03_weakness_framing"
    assert opening_calls["count"] == 0


def test_start_rejects_invalid_source_transition_before_starting(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    calls = {"count": 0}

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        calls["count"] += 1
        return "should-not-start", {
            "session_id": "should-not-start",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    source_session_id = "invalid-source-session"
    source_state = svc._new_state(
        "test_user",
        source_session_id,
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
    )
    source_state["pending_node_transition"] = {
        "transition_id": "transition-to-other-node",
        "from_node": "int_02_strength_with_evidence",
        "to_node": "int_03_weakness_framing",
        "status": "awaiting_next_opening",
    }
    svc.SessionStore[source_session_id] = source_state

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={
            "competency_node": "int_04_star_behavioral",
            "client_start_id": "invalid-handoff-start",
            "source_session_id": source_session_id,
            "source_transition_id": "transition-to-other-node",
            "confirm": True,
        },
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_source_transition"
    assert calls["count"] == 0


def test_opening_rejects_duplicate_in_progress_request(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    opening_calls = {"count": 0}

    async def in_progress_opening(_session_id: str, _transition_id: str) -> dict:
        return {
            "accepted": False,
            "status": "in_progress",
            "message_id": None,
            "attempts": 1,
            "last_error": None,
        }

    async def fake_stream_opening(*_args, **_kwargs):
        opening_calls["count"] += 1
        yield "Only the owner of the opening request may stream this."

    monkeypatch.setattr(store, "begin_opening_request", in_progress_opening, raising=False)
    monkeypatch.setattr(svc, "stream_opening", fake_stream_opening)
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "opening-latched-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = False
    state["messages"] = []
    svc.SessionStore[session_id] = state

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/opening", headers=AUTH)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "opening_in_progress"
    assert opening_calls["count"] == 0


def test_opening_failed_request_retries_and_completes(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    opening_calls = {"count": 0}

    async def fake_stream_opening(*_args, **_kwargs):
        opening_calls["count"] += 1
        yield "Recovered opening."

    monkeypatch.setattr(svc, "stream_opening", fake_stream_opening)
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "opening-retry-session"
    node_id = "int_01_elevator_pitch"
    state = svc._new_state(
        "test_user",
        session_id,
        node_id,
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = False
    state["messages"] = []
    svc.SessionStore[session_id] = state
    opening_key = f"initial:{node_id}"
    store.opening_requests[(session_id, opening_key)] = {
        "session_id": session_id,
        "transition_id": opening_key,
        "status": "failed",
        "message_id": None,
        "attempts": 1,
        "last_error": "stream_failed",
    }

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/opening", headers=AUTH)

    assert response.status_code == 200
    assert "Recovered opening." in response.text
    assert opening_calls["count"] == 1
    request_row = store.opening_requests[(session_id, opening_key)]
    assert request_row["status"] == "completed"
    assert request_row["attempts"] == 2
    assert request_row["last_error"] is None


def test_completed_opening_request_replays_persisted_message_after_cold_hydrate(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    opening_calls = {"count": 0}

    async def fake_stream_opening(*_args, **_kwargs):
        opening_calls["count"] += 1
        yield "This should not be regenerated."

    monkeypatch.setattr(svc, "stream_opening", fake_stream_opening)
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "opening-completed-replay-session"
    node_id = "int_01_elevator_pitch"
    opening_key = f"initial:{node_id}"
    message_id = f"{session_id}:opening:{opening_key}"
    snapshot = {
        "session_id": session_id,
        "user_id": "test_user",
        "competency_node": node_id,
        "task_type": "interview_prep",
        "status": "active",
        "opening_streamed": True,
        "messages": [],
    }
    asyncio.run(store.upsert_session_runtime(
        session_id,
        "test_user",
        node_id,
        "interview",
        "interview_prep",
        False,
        "active",
        snapshot,
        None,
        1,
    ))
    asyncio.run(store.replace_session_messages(session_id, [
        {
            "message_id": message_id,
            "role": "assistant",
            "content": "Persisted opening from storage.",
            "node_id": node_id,
            "transition_id": None,
            "message_kind": "opening",
        }
    ]))
    store.opening_requests[(session_id, opening_key)] = {
        "session_id": session_id,
        "transition_id": opening_key,
        "status": "completed",
        "message_id": message_id,
        "attempts": 1,
        "last_error": None,
    }
    svc.SessionStore.pop(session_id, None)

    client = TestClient(app)
    response = client.get(f"/session/{session_id}/opening", headers=AUTH)

    assert response.status_code == 200
    assert "Persisted opening from storage." in response.text
    assert "This should not be regenerated." not in response.text
    assert opening_calls["count"] == 0


@pytest.mark.asyncio
async def test_committed_opening_replay_unlocks_and_persists_session(store):
    from app.services import session_service as svc

    session_id = "committed-opening-unlocks-session"
    node_id = "int_01_elevator_pitch"
    opening_key = f"initial:{node_id}"
    state = svc._new_state(
        "test_user",
        session_id,
        node_id,
        [],
        task_type="interview_prep",
    )
    state["committed_openings"] = {opening_key: "Committed opening."}
    state["opening_streamed"] = False
    state["input_allowed"] = False
    state["block_reason"] = "opening_streaming"
    state["messages"] = [
        {
            "message_id": f"{session_id}:opening:{opening_key}",
            "role": "assistant",
            "content": "Committed opening.",
            "node_id": node_id,
            "message_kind": "opening",
        }
    ]
    svc.SessionStore[session_id] = state

    chunks = [chunk async for chunk in svc.stream_opening(session_id)]

    assert chunks == ["Committed opening."]
    assert state["opening_streamed"] is True
    assert state["input_allowed"] is True
    assert state["block_reason"] is None
    persisted = await store.get_session_runtime(session_id)
    assert persisted is not None
    snapshot = persisted["state_snapshot"]
    assert snapshot["opening_streamed"] is True
    assert snapshot["input_allowed"] is True
    assert snapshot["block_reason"] is None


def test_completed_opening_replay_does_not_double_meter_attempt(monkeypatch, store):
    from app.content import registry
    from app.services import session_service as svc
    import asyncio

    generation_calls = {"count": 0}

    async def fake_stream_generation(_spec):
        generation_calls["count"] += 1
        yield "Opening from model."

    monkeypatch.setattr(svc, "stream_generation", fake_stream_generation)
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "opening-replay-attempt-meter"
    node_id = "int_01_elevator_pitch"
    state = svc._new_state(
        "test_user",
        session_id,
        node_id,
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = False
    svc.SessionStore[session_id] = state

    client = TestClient(app)
    first = client.get(f"/session/{session_id}/opening", headers=AUTH)
    second = client.get(f"/session/{session_id}/opening", headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert "Opening from model." in first.text
    assert "Opening from model." in second.text
    assert generation_calls["count"] == 1
    assert asyncio.run(store.count_attempts("test_user", registry.INT_ID)) == 1


def test_opening_done_frame_survives_latch_completion_failure(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_stream_opening(*_args, **_kwargs):
        yield "Opening text before latch failure."

    async def failing_complete_opening_request(*_args, **_kwargs):
        raise RuntimeError("opening latch write failed")

    monkeypatch.setattr(svc, "stream_opening", fake_stream_opening)
    monkeypatch.setattr(
        store,
        "complete_opening_request",
        failing_complete_opening_request,
        raising=False,
    )
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "opening-done-survives-latch-failure"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = False
    svc.SessionStore[session_id] = state

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(f"/session/{session_id}/opening", headers=AUTH)

    assert response.status_code == 200
    assert "Opening text before latch failure." in response.text
    assert "event: done" in response.text


def test_turn_done_frame_survives_latch_completion_failure(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_run_turn(*_args, **_kwargs):
        yield "Tutor reply before latch failure."

    async def failing_complete_turn_request(*_args, **_kwargs):
        raise RuntimeError("turn latch write failed")

    monkeypatch.setattr(svc, "run_turn", fake_run_turn)
    monkeypatch.setattr(
        store,
        "complete_turn_request",
        failing_complete_turn_request,
        raising=False,
    )
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "turn-done-survives-latch-failure"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "My answer",
            "client_turn_id": "turn-latch-failure-1",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )

    assert response.status_code == 200
    assert "Tutor reply before latch failure." in response.text
    assert "event: done" in response.text


def test_turn_done_frame_is_not_blocked_by_slow_latch_completion(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio
    import time

    async def fake_run_turn(*_args, **_kwargs):
        yield "Tutor reply before slow latch."

    async def slow_complete_turn_request(*_args, **_kwargs):
        await asyncio.sleep(0.3)

    monkeypatch.setattr(svc, "run_turn", fake_run_turn)
    monkeypatch.setattr(
        store,
        "complete_turn_request",
        slow_complete_turn_request,
        raising=False,
    )
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "turn-done-before-slow-latch"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["opening_streamed"] = True
    svc.SessionStore[session_id] = state

    client = TestClient(app, raise_server_exceptions=False)
    started = time.perf_counter()
    response = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "My answer",
            "client_turn_id": "turn-latch-slow-1",
            "expected_session_version": 1,
        },
        headers=AUTH,
    )
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert "Tutor reply before slow latch." in response.text
    assert "event: done" in response.text
    assert elapsed < 0.25


def test_test_mode_end_starts_async_scoring_and_report_endpoint_replays_result(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    calls = {"count": 0}

    async def fake_close_session(session_id: str):
        calls["count"] += 1
        state = await svc.get_session_state(session_id)
        assert state is not None
        state["status"] = "ended"
        state["session_over"] = True
        state["simulation_report"] = {
            "summary": "Role-aware report.",
            "score": 0.82,
            "strengths": ["Specific backend examples"],
            "improvements": ["Tighter structure"],
        }
        state["simulation_score"] = 0.82
        state["session_summary"] = "Role-aware report."
        await svc._persist_runtime_state(state)
        return {
            "summary": "Role-aware report.",
            "report": state["simulation_report"],
            "score": 0.82,
        }

    monkeypatch.setattr(svc, "close_session", fake_close_session)
    asyncio.run(store.ensure_profile("test_user"))

    session_id = "async-scoring-session"
    state = svc._new_state(
        "test_user",
        session_id,
        "int_01_elevator_pitch",
        [],
        task_type="interview_test",
    )
    state["opening_streamed"] = True
    state["messages"].append({
        "role": "user",
        "content": "I built reliable APIs and debugged payment failures.",
        "message_kind": "learner_answer",
    })
    svc.SessionStore[session_id] = state

    client = TestClient(app)
    end_response = client.post(f"/session/{session_id}/end", headers=AUTH)

    assert end_response.status_code == 202
    assert end_response.json()["status"] == "processing"
    assert state["session_over"] is True
    assert state["input_allowed"] is False
    assert state["block_reason"] == "scoring"

    report_response = client.get(f"/session/{session_id}/report", headers=AUTH)

    assert report_response.status_code == 200
    assert report_response.json()["status"] == "completed"
    assert report_response.json()["report"]["summary"] == "Role-aware report."
    assert calls["count"] == 1


def test_stale_opening_request_retries_as_owner(store):
    import asyncio
    import time

    store.opening_requests[("stale-opening-session", "initial:int_01_elevator_pitch")] = {
        "session_id": "stale-opening-session",
        "transition_id": "initial:int_01_elevator_pitch",
        "status": "in_progress",
        "message_id": None,
        "attempts": 1,
        "last_error": None,
        "updated_at": time.time() - 10_000,
    }

    retry = asyncio.run(
        store.begin_opening_request(
            "stale-opening-session",
            "initial:int_01_elevator_pitch",
        )
    )

    assert retry["accepted"] is True
    assert retry["status"] == "in_progress"
    assert retry["attempts"] == 2
    assert retry["last_error"] is None


def test_session_start_rejects_reused_client_start_id_with_different_payload(monkeypatch, store):
    from app.services import session_service as svc
    import asyncio

    async def fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False, **_kwargs):
        return "first-start-session", {
            "session_id": "first-start-session",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", fake_start)
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.set_demo_unlimited("test_user", True))

    client = TestClient(app)
    first = client.post(
        "/session/start",
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": "reused-start-id",
        },
        headers=AUTH,
    )
    second = client.post(
        "/session/start",
        json={
            "competency_node": "int_02_strength_with_evidence",
            "client_start_id": "reused-start-id",
        },
        headers=AUTH,
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "client_start_id_reused_with_different_payload"


def test_failed_session_start_can_retry_same_client_start_id_after_topup(monkeypatch, store):
    import asyncio
    from app.billing import pricing

    async def used_free_attempts(_user_id: str, _module_id: str) -> int:
        return pricing.FREE_ATTEMPTS

    monkeypatch.setattr(store, "count_attempts", used_free_attempts)
    asyncio.run(store.ensure_profile("test_user"))
    client = TestClient(app)
    payload = {
        "competency_node": "int_01_elevator_pitch",
        "client_start_id": "retry-after-topup",
        "confirm": True,
    }

    first = client.post("/session/start", json=payload, headers=AUTH)
    assert first.status_code == 402
    assert first.json()["detail"]["error"] == "insufficient_credits"

    asyncio.run(store.grant_credits("test_user", pricing.INT_ATTEMPT_COST, "topup"))
    second = client.post("/session/start", json=payload, headers=AUTH)

    assert second.status_code == 200
    assert second.json()["session_id"]


@pytest.mark.asyncio
async def test_attempt_meter_counts_only_recorded_opening_attempts(store):
    from app.content import registry

    await store.create_session(
        "abandoned-interview-session",
        "test_user",
        "interview_test",
        registry.INT_ID,
        "int_01_elevator_pitch",
        test_mode=True,
    )
    await store.upsert_session_runtime(
        session_id="abandoned-interview-session",
        user_id="test_user",
        current_node="int_01_elevator_pitch",
        module_id=registry.INT_ID,
        task_type="interview_test",
        test_mode=True,
        status="active",
        state_snapshot={"opening_streamed": False},
        pending_transition=None,
        session_version=1,
    )
    await store.create_session(
        "usable-interview-session",
        "test_user",
        "interview_test",
        registry.INT_ID,
        "int_02_strength_with_evidence",
        test_mode=True,
    )
    await store.upsert_session_runtime(
        session_id="usable-interview-session",
        user_id="test_user",
        current_node="int_02_strength_with_evidence",
        module_id=registry.INT_ID,
        task_type="interview_test",
        test_mode=True,
        status="active",
        state_snapshot={"opening_streamed": True},
        pending_transition=None,
        session_version=1,
    )
    await store.record_node_attempt(
        "usable-interview-session",
        "test_user",
        "int_02_strength_with_evidence",
        starting_mastery=0.0,
    )

    assert await store.count_attempts("test_user", registry.INT_ID) == 1


@pytest.mark.asyncio
async def test_failed_test_session_start_does_not_create_attempt_row(monkeypatch, store):
    from app.services import session_service as svc

    async def fail_probe_generation(*_args, **_kwargs):
        raise RuntimeError("probe generation unavailable")

    await store.ensure_profile("test_user")
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fail_probe_generation)

    with pytest.raises(RuntimeError, match="probe generation unavailable"):
        await svc.start_session("test_user", "int_01_elevator_pitch", test_mode=True)

    assert store.sessions == {}


def test_school_progress_includes_lesson_statuses(store):
    import asyncio
    from fastapi.testclient import TestClient

    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(
        store.upsert_mastery(
            "test_user",
            "c2_ch01_l1_new_words",
            ema=0.0,
            attempts=3,
            clean_pass=False,
            node_completed=True,
        )
    )

    client = TestClient(app)
    response = client.get("/school/progress?class_no=2", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["lesson_progress"]["c2_ch01_l1_new_words"] == "completed"
    assert body["passed_tests"] == []


def test_session_message_schema_uses_numeric_sequence_for_reload_order():
    from pathlib import Path

    schema = Path("app/db/schema.sql").read_text().lower()
    migration = Path("app/db/migrations/2026-07-06-session-runtime.sql").read_text().lower()
    repo = Path("app/db/repo.py").read_text().lower()

    assert "sequence_index" in schema
    assert "sequence_index" in migration
    assert "order by sequence_index" in repo
    assert "order by created_at, message_id" not in repo


@pytest.mark.asyncio
async def test_prep_close_at_next_skill_checkpoint_attributes_completed_node(monkeypatch, store):
    from app.services import session_service as svc

    captured = {}

    async def fake_summarize(node, _messages):
        captured["summary_node"] = node.id
        return "Grounded weakness progress."

    async def fake_write_memory(user_id, session_id, node_id, raw, task_type, score=0.0):
        captured["memory"] = {
            "user_id": user_id,
            "session_id": session_id,
            "node_id": node_id,
            "raw": raw,
            "task_type": task_type,
            "score": score,
        }

    async def no_probe_precache(_state):
        return None

    monkeypatch.setattr(svc, "summarize_session", fake_summarize)
    monkeypatch.setattr(svc, "_precache_test_items", no_probe_precache)
    monkeypatch.setattr(store, "write_memory", fake_write_memory)

    session_id = "prep-close-completed-node"
    state = svc._new_state(
        "user-1",
        session_id,
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["messages"] = [{"role": "user", "content": "My final weakness answer."}]
    state["pending_node_transition"] = {
        "from_node": "int_03_weakness_framing",
        "to_node": "int_04_star_behavioral",
        "status": "awaiting_next_opening",
    }
    svc.SessionStore[session_id] = state

    result = await svc.close_session(session_id)

    assert result["summary"] == "Grounded weakness progress."
    assert captured["summary_node"] == "int_03_weakness_framing"
    assert captured["memory"]["node_id"] == "int_03_weakness_framing"


@pytest.mark.asyncio
async def test_completed_simulation_rehydrates_report_and_terminal_state(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.services import session_service as svc

    async def fake_score_session(_state):
        return SimulationReport(
            score=0.82,
            summary="Strong interview close.",
            strengths=["clear project ownership"],
            improvements=["vary the examples"],
            clarity_score=0.84,
            confidence_score=0.8,
            scenario_label="Backend interview",
            role_focus="Backend Software Engineer",
            topic="Mixed interview",
        )

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
    )
    state["messages"] = [
        {"role": "assistant", "content": "Round 1"},
        {"role": "user", "content": "Answer 1"},
    ]
    state["blackboard"] = {"turn": 10, "tension": 0.7, "qualities": [0.8]}
    state["session_over"] = True

    result = await svc.close_session(session_id)
    svc.SessionStore.clear()
    restored = await svc.get_session_state(session_id)

    assert result["score"] == 0.82
    assert restored is not None
    assert restored["status"] == "ended"
    assert restored["session_over"] is True
    assert restored["simulation_report"]["score"] == 0.82
    assert restored["simulation_round"] == 10


@pytest.mark.asyncio
async def test_completed_simulation_close_is_idempotent_and_does_not_rescore(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.services import session_service as svc

    calls = {"score": 0}

    async def fake_score_session(_state):
        calls["score"] += 1
        return SimulationReport(
            score=0.82,
            summary="First scored report.",
            strengths=["clear ownership"],
            improvements=["vary examples"],
            clarity_score=0.84,
            confidence_score=0.8,
            scenario_label="Backend interview",
            role_focus="Backend Software Engineer",
            topic="Mixed interview",
        )

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
    )
    state["messages"] = [
        {"role": "assistant", "content": "Round 1"},
        {"role": "user", "content": "Answer 1"},
    ]
    state["blackboard"] = {"turn": 10, "tension": 0.7, "qualities": [0.8]}
    state["session_over"] = True

    first = await svc.close_session(session_id)
    svc.SessionStore.clear()
    second = await svc.close_session(session_id)

    assert calls["score"] == 1
    assert second == first


def test_completed_simulation_transcript_route_rehydrates_terminal_state(monkeypatch, store):
    import asyncio
    from app.ai.schemas import SimulationReport
    from app.services import session_service as svc

    async def fake_score_session(_state):
        return SimulationReport(
            score=0.8,
            summary="Good backend interview with clear ownership.",
            strengths=["clear project ownership"],
            improvements=["cover more conflict examples"],
            clarity_score=0.82,
            confidence_score=0.78,
            scenario_label="Backend interview",
            role_focus="Backend Software Engineer",
            topic="Mixed interview",
        )

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "score_session", fake_score_session)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    async def scenario():
        await store.ensure_profile("test_user")
        session_id, state = await svc.start_session(
            "test_user",
            "int_01_elevator_pitch",
            test_mode=True,
            simulation_config={
                "target_role": "Backend Software Engineer",
                "interview_type": "mixed",
            },
        )
        state["opening_streamed"] = True
        state["messages"] = [
            {"role": "assistant", "content": "[Interviewer]: First question."},
            {"role": "user", "content": "First answer."},
            {"role": "assistant", "content": "[Interviewer]: Final question."},
            {"role": "user", "content": "Final answer."},
        ]
        state["blackboard"] = {"turn": 10, "tension": 0.7, "qualities": [0.8]}
        state["session_over"] = True
        await svc.close_session(session_id)
        svc.SessionStore.clear()
        return session_id

    session_id = asyncio.run(scenario())

    response = TestClient(app).get(
        f"/session/{session_id}/transcript",
        headers=AUTH,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["opening_streamed"] is True
    assert [m["content"] for m in body["messages"]] == [
        "[Interviewer]: First question.",
        "First answer.",
        "[Interviewer]: Final question.",
        "Final answer.",
    ]
    assert body["state"]["status"] == "ended"
    assert body["state"]["session_over"] is True
    assert body["state"]["simulation_round"] == 10
    assert body["state"]["simulation_tension"] == 0.7
    assert body["state"]["simulation_report"]["score"] == 0.8


def test_simulation_scoring_failure_is_retryable_and_does_not_close_session(monkeypatch, store):
    import asyncio
    from fastapi.testclient import TestClient
    from app.services import session_service as svc

    async def failing_score_session(_state):
        raise RuntimeError("scorer unavailable")

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "score_session", failing_score_session)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    async def scenario():
        await store.ensure_profile("test_user")
        session_id, state = await svc.start_session(
            "test_user",
            "int_01_elevator_pitch",
            test_mode=True,
        )
        state["opening_streamed"] = True
        state["messages"] = [
            {"role": "assistant", "speaker_name": "Interviewer", "content": "Round 1"},
            {"role": "user", "content": "Answer 1"},
        ]
        state["blackboard"] = {"turn": 10, "tension": 0.7, "qualities": [0.8]}
        state["session_over"] = True
        return session_id, state

    session_id, state = asyncio.run(scenario())
    client = TestClient(app)
    response = client.post(f"/session/{session_id}/end", headers=AUTH)

    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    report_response = client.get(f"/session/{session_id}/report", headers=AUTH)
    assert report_response.status_code == 503
    assert report_response.json()["detail"]["code"] == "simulation_scoring_unavailable"
    assert state["status"] == "active"
    assert state["simulation_report"] is None
    assert state["last_error"] == {"code": "simulation_scoring_unavailable"}


@pytest.mark.asyncio
async def test_expired_runtime_rehydrates_as_expired_not_active(monkeypatch):
    from app.services import session_service as svc

    session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
    )
    state["expires_at"] = 1
    await svc._persist_runtime_state(state)
    svc.SessionStore.clear()

    restored = await svc.get_session_state(session_id)

    assert restored is not None
    assert restored["status"] == "expired"
    assert restored["input_allowed"] is False
    assert restored["block_reason"] == "session_expired"


def test_expired_session_routes_return_consistent_410(store):
    import asyncio
    from app.services import session_service as svc

    async def scenario():
        await store.ensure_profile("test_user")
        session_id, state = await svc.start_session(
            "test_user",
            "int_01_elevator_pitch",
        )
        state["expires_at"] = 1
        await svc._persist_runtime_state(state)
        svc.SessionStore.clear()
        return session_id

    session_id = asyncio.run(scenario())
    client = TestClient(app)

    transcript = client.get(f"/session/{session_id}/transcript", headers=AUTH)
    opening = client.get(f"/session/{session_id}/opening", headers=AUTH)
    turn = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "user_input": "hello",
            "client_turn_id": "expired-turn-1",
        },
        headers=AUTH,
    )
    end = client.post(f"/session/{session_id}/end", headers=AUTH)

    for response in (transcript, opening, turn, end):
        assert response.status_code == 410
        assert response.json()["detail"]["code"] == "session_expired"


@pytest.mark.asyncio
async def test_simulation_director_sees_current_user_turn(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc

    captured: dict[str, str] = {}

    async def capture_director(_bb, _personas, _task_type, transcript, _probe_items, **_kwargs):
        captured["transcript"] = transcript
        return DirectorDecision(
            action="probe_deeper",
            next_speaker="interviewer",
            intent="Ask one follow-up about the learner's latest answer.",
            tension=0.5,
            answer_quality=0.7,
            should_close=False,
        )

    async def fake_stream_generation(_spec):
        yield "Follow-up question."

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", capture_director)
    monkeypatch.setattr("app.services.simulation.persona.stream_generation", fake_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
    )
    state["opening_streamed"] = True
    state["input_allowed"] = True
    state["block_reason"] = None
    state["assessment_plan"] = None

    chunks = []
    async for item in svc.run_turn(
        session_id,
        "I built a checkout reliability dashboard that tracked payment retries.",
    ):
        if isinstance(item, str):
            chunks.append(item)

    assert "Follow-up question." in "".join(chunks)
    assert "checkout reliability dashboard" in captured["transcript"]


@pytest.mark.asyncio
async def test_test_mode_end_phrase_keeps_session_scoreable(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.services import session_service as svc

    async def fake_probe_items(*_args, **_kwargs):
        return []

    async def fake_score_session(_state):
        return SimulationReport(
            score=0.82,
            summary="The interview was closed and scored.",
            strengths=["clear backend ownership"],
            improvements=["add one more conflict example"],
            clarity_score=0.8,
            confidence_score=0.84,
        )

    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)
    monkeypatch.setattr(svc, "score_session", fake_score_session)

    session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
    )
    state["opening_streamed"] = True
    state["input_allowed"] = True
    state["block_reason"] = None
    state["messages"] = [
        {"role": "assistant", "speaker_name": "Interviewer", "content": "Tell me about a backend project."},
        {"role": "user", "content": "I built a payment retry dashboard."},
    ]
    state["blackboard"] = {"turn": 3, "tension": 0.5, "qualities": [0.8, 0.82]}

    chunks = []
    async for item in svc.run_turn(session_id, "done"):
        if isinstance(item, str):
            chunks.append(item)

    assert "finish" in "".join(chunks).lower()
    assert state["status"] == "active"
    assert state["session_over"] is True
    assert state["block_reason"] == "session_over"
    assert state["messages"][-2]["role"] == "user"
    assert state["messages"][-2]["content"] == "done"
    assert state["messages"][-2]["message_kind"] == "simulation_control"

    result = await svc.close_session(session_id)

    assert result["score"] == 0.82
    assert result["report"]["summary"] == "The interview was closed and scored."


@pytest.mark.asyncio
async def test_simulation_scoring_excludes_control_messages(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.content.task_types import TaskType
    from app.services import simulation_service as sim

    captured = {}

    async def fake_evaluate_simulation(_task_type, _topic, messages, **_kwargs):
        captured["messages"] = messages
        return SimulationReport(
            score=0.75,
            summary="Scored only learner answers.",
            strengths=["specific answer"],
            improvements=["add more evidence"],
            clarity_score=0.7,
            confidence_score=0.8,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", fake_evaluate_simulation)

    await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Backend Software Engineer",
        "messages": [
            {"role": "assistant", "content": "Tell me about a project."},
            {"role": "user", "content": "I built a queue monitor.", "message_kind": "learner_answer"},
            {"role": "user", "content": "done", "message_kind": "simulation_control"},
            {"role": "assistant", "content": "Tell me about a disagreement."},
            {"role": "user", "content": "I handled a disagreement with a PM.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about debugging."},
            {"role": "user", "content": "I debugged queue retries.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about impact."},
            {"role": "user", "content": "I reduced checkout failures.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about communication."},
            {"role": "user", "content": "I explained tradeoffs to support.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about a failure."},
            {"role": "user", "content": "I owned a migration lock and wrote a checklist.", "message_kind": "learner_answer"},
        ],
        "blackboard": {"qualities": []},
        "scenario_config": {"target_role": "Backend Software Engineer"},
        "career_context": {},
    })

    assert [m["content"] for m in captured["messages"] if m["role"] == "user"] == [
        "I built a queue monitor.",
        "I handled a disagreement with a PM.",
        "I debugged queue retries.",
        "I reduced checkout failures.",
        "I explained tradeoffs to support.",
        "I owned a migration lock and wrote a checklist.",
    ]


@pytest.mark.asyncio
async def test_simulation_scoring_excludes_unanswered_final_prompt(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.content.task_types import TaskType
    from app.services import simulation_service as sim

    captured = {}

    async def fake_evaluate_simulation(_task_type, _topic, messages, **_kwargs):
        captured["messages"] = messages
        return SimulationReport(
            score=0.8,
            summary="Scored only answered turns.",
            strengths=["clear project answer"],
            improvements=["answer the next debugging prompt"],
            clarity_score=0.8,
            confidence_score=0.78,
        )

    monkeypatch.setattr(sim, "evaluate_simulation", fake_evaluate_simulation)

    report = await sim.score_session({
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Backend Software Engineer",
        "messages": [
            {"role": "assistant", "content": "Introduce yourself."},
            {"role": "user", "content": "I build reliable APIs.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about a project."},
            {"role": "user", "content": "I built payment APIs.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about debugging."},
            {"role": "user", "content": "I isolated queue retry failures.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about disagreement."},
            {"role": "user", "content": "I pushed for a modular monolith.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about impact."},
            {"role": "user", "content": "I improved checkout visibility.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about failure."},
            {"role": "user", "content": "I owned a migration mistake.", "message_kind": "learner_answer"},
            {"role": "assistant", "content": "Tell me about a debugging process you handled."},
        ],
        "blackboard": {"qualities": []},
        "scenario_config": {"target_role": "Backend Software Engineer"},
        "career_context": {},
    })

    assert [m["content"] for m in captured["messages"]] == [
        "Introduce yourself.",
        "I build reliable APIs.",
        "Tell me about a project.",
        "I built payment APIs.",
        "Tell me about debugging.",
        "I isolated queue retry failures.",
        "Tell me about disagreement.",
        "I pushed for a modular monolith.",
        "Tell me about impact.",
        "I improved checkout visibility.",
        "Tell me about failure.",
        "I owned a migration mistake.",
    ]
    assert any("before the latest" in caveat.lower() for caveat in report.assessment_caveats)


@pytest.mark.asyncio
async def test_interview_test_probe_cursor_advances_without_repeating(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services.simulation_service import stream_simulation_round

    async def repeated_director(_bb, _personas, _task_type, _transcript, _probe_items, **_kwargs):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker="interviewer",
            intent="Ask again about Redis vs memcached composite index columns.",
            tension=0.5,
            answer_quality=0.6,
            should_close=False,
        )

    async def fake_stream_generation(spec):
        marker = "Your goal for THIS turn:"
        start = spec.prompt.find(marker)
        if start == -1:
            yield spec.prompt
            return
        yield spec.prompt[start + len(marker):].split("\n", 1)[0].strip()

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", repeated_director)
    monkeypatch.setattr("app.services.simulation.persona.stream_generation", fake_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    _session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
    )
    state["assessment_plan"] = None
    state["probe_items"] = [
        {"prompt": "Ask about project tradeoffs.", "aim": "names a tradeoff"},
        {"prompt": "Ask about teammate disagreement.", "aim": "shows collaboration"},
        {"prompt": "Ask about debugging under pressure.", "aim": "uses evidence"},
    ]

    outputs = []
    for answer in ("a1", "a2", "a3"):
        state["messages"].append({"role": "user", "content": answer})
        chunks = []
        async for item in stream_simulation_round(state):
            if isinstance(item, str):
                chunks.append(item)
        outputs.append("".join(chunks))

    assert "project tradeoffs" in outputs[0].lower()
    assert "teammate disagreement" in outputs[1].lower()
    assert "debugging under pressure" in outputs[2].lower()
    assert len(set(outputs)) == 3


@pytest.mark.asyncio
async def test_interview_persona_snapshot_does_not_expose_prompt_instructions(monkeypatch):
    from app.api.routes import _state_snapshot
    from app.services import session_service as svc

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    _session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
            "pressure_level": "high",
        },
    )

    snapshot = _state_snapshot(state)
    persona_text = str(snapshot["personas"])

    assert "prompt_role" not in persona_text
    assert "probe examples" not in persona_text.lower()
    assert "trade-offs" not in persona_text.lower()
    assert snapshot["personas"][0]["role"] == "Mixed interview interviewer for Backend Software Engineer"


@pytest.mark.asyncio
async def test_interview_test_honors_move_on_request_when_director_repeats(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services.simulation_service import stream_simulation_round

    async def repeated_director(_bb, _personas, _task_type, _transcript, _probe_items, **_kwargs):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker="interviewer",
            intent="Ask again for specific examples of Singleton and Factory design patterns.",
            tension=0.5,
            answer_quality=0.6,
            should_close=False,
        )

    async def fake_stream_generation(spec):
        marker = "Your goal for THIS turn:"
        start = spec.prompt.find(marker)
        if start == -1:
            yield spec.prompt
            return
        yield spec.prompt[start + len(marker):].split("\n", 1)[0].strip()

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", repeated_director)
    monkeypatch.setattr("app.services.simulation.persona.stream_generation", fake_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    _session_id, state = await svc.start_session(
        "user-1",
        "int_01_elevator_pitch",
        test_mode=True,
        simulation_config={
            "target_role": "Backend Software Engineer",
            "interview_type": "mixed",
        },
    )
    state["assessment_plan"] = None
    state["probe_items"] = []
    state["messages"] = [
        {"role": "assistant", "content": "[Interviewer]: Explain Singleton and Factory design patterns."},
        {"role": "user", "content": "I used Factory for payment adapters and Singleton for one config registry."},
        {"role": "assistant", "content": "[Interviewer]: Give more examples of Singleton and Factory design patterns."},
        {"role": "user", "content": "I covered that. Let's move to a disagreement-with-teammate story."},
    ]
    state["blackboard"] = {
        "topic": "Mixed interview for Backend Software Engineer",
        "phase": "pressure",
        "tension": 0.7,
        "turn": 4,
        "covered": ["design patterns"],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.7,
        "qualities": [0.7, 0.72, 0.74],
        "last_speaker": "interviewer",
    }

    chunks = []
    turns = []
    async for item in stream_simulation_round(state):
        if hasattr(item, "turn"):
            turns.append(item.turn)
        if isinstance(item, str):
            chunks.append(item)

    output = "".join(chunks).lower()
    assert turns == [4]
    assert state["blackboard"]["turn"] == 4
    assert "teammate" in output or "disagreement" in output
    assert "singleton" not in output
    assert "factory" not in output


@pytest.mark.asyncio
async def test_test_item_generation_times_out_to_fallback(monkeypatch, store):
    import asyncio
    import time

    from app.ai import test_gen
    from app.content.task_types import TaskType

    slow_completed = False

    async def slow_structured(*_args, **_kwargs):
        nonlocal slow_completed
        await asyncio.sleep(0.2)
        slow_completed = True
        raise AssertionError("slow local model should have been timed out")

    monkeypatch.setattr(test_gen, "PROBE_GENERATION_TIMEOUT_SECONDS", 0.01, raising=False)
    monkeypatch.setattr(test_gen, "ollama_structured", slow_structured)

    await store.ensure_profile("test_user")
    started = time.perf_counter()
    items = await test_gen.generate_test_items(
        "test_user",
        TaskType.INTERVIEW_TEST.value,
        career_context={
            "role_family": "software_technical",
            "primary_role": "Backend Software Engineer",
        },
        scenario_config={"target_role": "Backend Software Engineer"},
    )
    elapsed = time.perf_counter() - started

    assert elapsed < 0.25
    assert slow_completed is False
    assert items
    assert "Backend Software Engineer" in items[0].prompt


def test_test_item_generation_timeout_is_bounded_for_start_ux():
    from app.ai import test_gen

    assert test_gen.PROBE_GENERATION_TIMEOUT_SECONDS <= 15.0


@pytest.mark.asyncio
async def test_gd_test_confusion_gets_moderator_guidance(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services.simulation_service import stream_simulation_round

    async def bad_director(_bb, _personas, _task_type, _transcript, _probe_items, **_kwargs):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker="data_driven_analyst",
            intent="Demand a case study with Indian pilot evidence again.",
            tension=0.7,
            answer_quality=0.4,
            should_close=False,
        )

    async def fake_stream_generation(spec):
        marker = "Your goal for THIS turn:"
        start = spec.prompt.find(marker)
        if start == -1:
            yield spec.prompt
            return
        yield spec.prompt[start + len(marker):].split("\n", 1)[0].strip()

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", bad_director)
    monkeypatch.setattr("app.services.simulation.persona.stream_generation", fake_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    _session_id, state = await svc.start_session(
        "user-1",
        "gd_01_stake_position",
        test_mode=True,
        simulation_config={"topic": "AI in hiring"},
    )
    state["assessment_plan"] = None
    state["messages"] = [
        {"role": "assistant", "content": "[Data-Driven Analyst]: Give Indian pilot evidence."},
        {"role": "user", "content": "I don't understand what is going on here."},
    ]
    state["blackboard"] = {
        "topic": "AI in hiring",
        "phase": "pressure",
        "tension": 0.8,
        "turn": 5,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.4,
        "qualities": [0.4],
        "last_speaker": "data_driven_analyst",
    }

    speakers = []
    turns = []
    chunks = []
    async for item in stream_simulation_round(state):
        if hasattr(item, "turn"):
            turns.append(item.turn)
        if hasattr(item, "name"):
            speakers.append(item.name)
        if isinstance(item, str):
            chunks.append(item)

    output = "".join(chunks).lower()
    assert turns == [5]
    assert state["blackboard"]["turn"] == 5
    assert len(speakers) == 1
    assert speakers[0].lower().startswith("moderator")
    assert "explain" in output or "what is happening" in output
    assert "case study" not in output


@pytest.mark.asyncio
async def test_gd_test_honors_move_on_request(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services.simulation_service import stream_simulation_round

    async def bad_director(_bb, _personas, _task_type, _transcript, _probe_items, **_kwargs):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker="data_driven_analyst",
            intent="Demand the same case study with Indian pilot evidence again.",
            tension=0.7,
            answer_quality=0.5,
            should_close=False,
        )

    async def fake_stream_generation(spec):
        marker = "Your goal for THIS turn:"
        start = spec.prompt.find(marker)
        if start == -1:
            yield spec.prompt
            return
        yield spec.prompt[start + len(marker):].split("\n", 1)[0].strip()

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", bad_director)
    monkeypatch.setattr("app.services.simulation.persona.stream_generation", fake_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    _session_id, state = await svc.start_session(
        "user-1",
        "gd_01_stake_position",
        test_mode=True,
        simulation_config={"topic": "Remote work for engineering teams"},
    )
    state["assessment_plan"] = None
    state["messages"] = [
        {"role": "assistant", "content": "[Data-Driven Analyst]: Give Indian pilot evidence."},
        {"role": "user", "content": "I already covered that evidence. Can we move on to a different angle?"},
    ]
    state["blackboard"] = {
        "topic": "Remote work for engineering teams",
        "phase": "pressure",
        "tension": 0.75,
        "turn": 4,
        "covered": [],
        "open_threads": [],
        "positions": {},
        "last_quality": 0.5,
        "qualities": [0.5],
        "last_speaker": "data_driven_analyst",
    }

    speakers = []
    turns = []
    chunks = []
    async for item in stream_simulation_round(state):
        if hasattr(item, "turn"):
            turns.append(item.turn)
        if hasattr(item, "name"):
            speakers.append(item.name)
        if isinstance(item, str):
            chunks.append(item)

    output = "".join(chunks).lower()
    assert turns == [4]
    assert state["blackboard"]["turn"] == 4
    assert len(speakers) == 1
    assert speakers[0].lower().startswith("moderator")
    assert "new angle" in output or "different angle" in output
    assert "case study" not in output


@pytest.mark.asyncio
async def test_gd_test_honors_requested_quiet_expert(monkeypatch):
    from app.ai.schemas import DirectorDecision
    from app.services import session_service as svc
    from app.services.simulation_service import stream_simulation_round

    async def bad_director(_bb, _personas, _task_type, _transcript, _probe_items, **_kwargs):
        return DirectorDecision(
            action="probe_deeper",
            next_speaker="aggressive_challenger",
            intent="Push the learner again.",
            tension=0.7,
            answer_quality=0.5,
            should_close=False,
        )

    async def fake_stream_generation(spec):
        marker = "Your goal for THIS turn:"
        start = spec.prompt.find(marker)
        if start == -1:
            yield spec.prompt
            return
        yield spec.prompt[start + len(marker):].split("\n", 1)[0].strip()

    async def fake_probe_items(*_args, **_kwargs):
        return []

    monkeypatch.setattr("app.services.simulation.director.direct_simulation", bad_director)
    monkeypatch.setattr("app.services.simulation.persona.stream_generation", fake_stream_generation)
    monkeypatch.setattr(svc, "_load_or_generate_probe_items", fake_probe_items)

    _session_id, state = await svc.start_session(
        "user-1",
        "gd_01_stake_position",
        test_mode=True,
        simulation_config={
            "topic": "AI in hiring",
            "personas": ["quiet_expert", "aggressive_challenger", "data_driven_analyst"],
        },
    )
    state["assessment_plan"] = None
    state["messages"] = [
        {"role": "assistant", "content": "[Aggressive Challenger]: Make your point stronger."},
        {"role": "user", "content": "Can we hear from the Expert now?"},
    ]

    speakers = []
    chunks = []
    async for item in stream_simulation_round(state):
        if hasattr(item, "name"):
            speakers.append(item.name)
        if isinstance(item, str):
            chunks.append(item)

    output = "".join(chunks).lower()
    assert speakers[0] == "Quiet Expert"
    assert "quiet expert," not in output
    assert "implementation quality" in output
    assert "push the learner again" not in output


def test_career_bridge_personalization_rewrites_unrelated_role_examples():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="bridge-1",
        type="fill_blank",
        sentence="As a data analyst, I handled ___ clearly.",
        hint="one work responsibility",
        context="Use the data analyst role to keep the answer concrete.",
        answer_key="pressure",
        band="standard",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "backend software engineer", "gd_topics": ["AI in hiring"]},
        "interview",
    )

    assert "data analyst" not in personalized.sentence.lower()
    assert "data analyst" not in personalized.context.lower()
    assert "backend software engineer" in personalized.sentence
    assert personalized.answer_key == "pressure"


def test_career_bridge_personalization_rewrites_multiple_choice_options_and_key():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="bridge-mcq-1",
        type="multiple_choice",
        sentence="Which opening line makes the strongest first sentence of a pitch?",
        hint="lead with role plus one concrete strength",
        context="Pick the answer that is strongest for the learner's role.",
        answer_key="I'm a data analyst who turns messy spreadsheets into dashboards leadership actually uses.",
        options=[
            "Well, I was born in a small town and always liked computers growing up.",
            "I'm a data analyst who turns messy spreadsheets into dashboards leadership actually uses.",
            "There's a lot to say about me, so let me start from the beginning.",
        ],
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "backend software engineer", "role_family": "software_technical"},
        "interview",
    )

    combined = " ".join([personalized.answer_key, *(personalized.options or [])]).lower()
    assert "data analyst" not in combined
    assert "spreadsheet" not in combined
    assert "dashboard" not in combined
    assert "backend software engineer" in combined
    assert "reliable api" in combined or "production system" in combined
    assert personalized.answer_key in (personalized.options or [])


def test_career_bridge_personalization_rewrites_generic_weakness_for_software_role():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="int_03_weakness_framing_bx1",
        type="fill_blank",
        sentence="I used to struggle with delegating, so now I ___ at the start of every project.",
        hint="a concrete corrective habit",
        context="Drills the weakness->mitigation stem by pairing a real weakness with a specific fix.",
        answer_key="assign clear owners to each task",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "Backend Software Engineer", "role_family": "software_technical"},
        "interview",
    )

    combined = " ".join([personalized.sentence, personalized.hint, personalized.context, personalized.answer_key]).lower()
    assert "delegating" not in combined
    assert "technical trade-off" in combined or "stakeholder" in combined
    assert "recommendation" in personalized.answer_key.lower()
    assert "risk" in personalized.answer_key.lower()


def test_career_bridge_personalization_rewrites_quantify_impact_for_software_role():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="int_08_quantify_impact_bx1",
        type="fill_blank",
        sentence="I cut report time by ___% by automating the weekly export.",
        hint="any number (e.g. 40)",
        context="Forces a measurable result into a vague achievement.",
        answer_key="<number>",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "Backend Software Engineer", "role_family": "software_technical"},
        "interview",
    )

    combined = " ".join([personalized.sentence, personalized.hint, personalized.context]).lower()
    assert "weekly export" not in combined
    assert "backend reliability" in combined or "checkout reliability" in combined
    assert "triage" in personalized.sentence.lower()
    assert personalized.answer_key == "<number>"


def test_career_bridge_personalization_rewrites_star_action_fill_blank_for_software_role():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="int_04_star_behavioral_bx1",
        type="fill_blank",
        sentence="In the end, we shipped the release two days early because I ___.",
        hint="the specific Action of STAR — what you personally did",
        context="Anchors the Result beat first, then forces the learner to name the Action that caused it.",
        answer_key="reorganized the testing schedule and unblocked the team",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "Backend Software Engineer", "role_family": "software_technical"},
        "interview",
    )

    combined = " ".join(
        [
            personalized.sentence,
            personalized.hint,
            personalized.context,
            personalized.answer_key,
        ]
    ).lower()
    assert "shipped the release two days early" not in combined
    assert "testing schedule" not in combined
    assert "backend" in combined or "checkout" in combined or "observability" in combined
    assert "dashboard" in personalized.answer_key.lower()
    assert "trade-off" in personalized.answer_key.lower()


def test_career_bridge_personalization_rewrites_star_mcq_options_and_key_for_software_role():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="int_04_star_behavioral_bx2",
        type="multiple_choice",
        sentence="Which sentence belongs to the ACTION beat of a STAR answer?",
        hint="Action = the specific steps you personally took",
        context="Trains the learner to sort sentences into the correct STAR beat, the most common structuring error.",
        answer_key="I split the project into milestones and ran a daily ten-minute standup to catch blockers early.",
        options=[
            "Our team was three weeks behind on a major client deliverable.",
            "I split the project into milestones and ran a daily ten-minute standup to catch blockers early.",
            "We delivered on time and the client renewed their contract.",
        ],
        band="standard",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "Backend Software Engineer", "role_family": "software_technical"},
        "interview",
    )

    combined = " ".join([personalized.answer_key, *(personalized.options or [])]).lower()
    assert "major client deliverable" not in combined
    assert "daily ten-minute standup" not in combined
    assert "client renewed" not in combined
    assert "checkout" in combined or "payment" in combined
    assert "dashboard" in personalized.answer_key.lower()
    assert "retry" in personalized.answer_key.lower() or "error signal" in personalized.answer_key.lower()
    assert personalized.answer_key in (personalized.options or [])


def test_career_bridge_personalization_rewrites_ambiguous_client_drill_for_software_role():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="int_07_clarify_before_answering_bx1",
        type="fill_blank",
        sentence="When you ask how I'd handle a difficult client — do you mean a client who's unhappy with the work, or ___?",
        hint="offer a second clear interpretation to narrow the scope",
        context="Practices the 'do you mean A or B' clarifier stem to narrow a vague prompt before answering.",
        answer_key="one who keeps changing the requirements",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "Backend Software Engineer", "role_family": "software_technical"},
        "interview",
    )

    combined = " ".join(
        [
            personalized.sentence,
            personalized.hint,
            personalized.context,
            personalized.answer_key,
        ]
    ).lower()
    assert "difficult client" not in combined
    assert "unhappy with the work" not in combined
    assert "changing the requirements" not in combined
    assert "api" in combined or "checkout" in combined or "payment" in combined
    assert "incident" in combined or "reliability" in combined or "latency" in combined


def test_scaffolded_recovery_does_not_surface_impressed_avatar_state():
    from app.api.routes import _avatar_emotion

    assert _avatar_emotion("confident", 1.0, scaffolded=True) == "patient"
    assert _avatar_emotion("confident", 0.9, scaffolded=False) == "impressed"


def test_career_bridge_personalization_rewrites_software_examples_for_hr_profile():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="bridge-hr-1",
        type="multiple_choice",
        sentence="Which opening line makes the strongest first sentence of a pitch?",
        hint="lead with role plus one concrete strength",
        context="Practice a concrete opener without pretending the learner works in software.",
        answer_key="I'm a backend developer who builds payment systems for high-traffic apps.",
        options=[
            "Well, I was born in a small town and always liked computers growing up.",
            "I'm a backend developer who builds payment systems for high-traffic apps.",
            "There's a lot to say about me, so let me start from the beginning.",
        ],
        band="standard",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"primary_role": "HR Business Partner", "role_family": "hr_people"},
        "interview",
    )

    combined = " ".join([personalized.answer_key, *(personalized.options or [])]).lower()
    assert "backend developer" not in combined
    assert "payment systems" not in combined
    assert "high-traffic apps" not in combined
    assert "hr business partner" in combined
    assert "people" in combined or "hiring" in combined
    assert personalized.answer_key in (personalized.options or [])


def test_career_teach_game_prompt_blocks_grammar_drills_for_profiled_career_modules():
    from app.ai.prompts import build_teach_game_prompt
    from app.content.registry import get_node

    node = get_node("int_03_weakness_framing")
    prompt = build_teach_game_prompt(
        node,
        {
            "next_focus": "show the corrective habit and a real result",
            "errors": ["answer is vague and lacks impact"],
        },
        career_context={
            "primary_role": "Backend Software Engineer",
            "role_family": "software_technical",
        },
    ).lower()

    assert "career communication practice" in prompt
    assert "not a grammar" in prompt
    assert "verb tense" in prompt
    assert "interview move" in prompt


def test_gd_bridge_personalization_preserves_custom_topic_casing():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="bridge-gd-topic-1",
        type="spoken",
        sentence="Remote work needs one clear reason and one example.",
        hint="Use remote work as the discussion topic.",
        context="Practice staying specific when the GD topic is remote work.",
        answer_key="",
        band="standard",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"gd_topics": ["AI in hiring"]},
        "group_discussion",
    )

    combined = " ".join([
        personalized.sentence,
        personalized.hint,
        personalized.context,
    ])
    assert "AI in hiring" in combined
    assert "Ai In Hiring" not in combined
    assert "remote work" not in combined.lower()


def test_gd_bridge_personalization_handles_question_style_custom_topics():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="bridge-gd-topic-question",
        type="fill_blank",
        sentence=(
            "On this topic, I ___ that remote work helps companies more than "
            "it hurts them."
        ),
        hint="a verb that commits you to a side",
        context="Practice staying specific when the GD topic is remote work.",
        answer_key="believe",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"gd_topics": ["Should AI replace campus placement interviews in India?"]},
        "group_discussion",
    )

    assert "that Should" not in personalized.sentence
    assert "Should AI replace" not in personalized.sentence
    assert "AI replacing campus placement interviews in India" in personalized.sentence
    assert personalized.answer_key == "believe"


def test_gd_bridge_personalization_anchors_take_floor_to_selected_topic():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="gd_03_take_the_floor_bx1",
        type="fill_blank",
        sentence="If I could ___ to that, I think the cost angle matters just as much as the time saved.",
        hint="a verb meaning to contribute something extra",
        context="Drills the polite entry stem used to claim the floor.",
        answer_key="add",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"gd_topics": ["Digital payments"]},
        "group_discussion",
    )

    assert "cost angle matters just as much as the time saved" not in personalized.sentence
    assert "Digital payments" in personalized.sentence
    assert personalized.answer_key == "add"


def test_gd_bridge_personalization_rewrites_take_floor_mcq_options_to_selected_topic():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="gd_03_take_the_floor_bx2",
        type="multiple_choice",
        sentence="The group is mid-flow. Which entry is polite, well-timed, and links to the last speaker?",
        hint="assertive but not rude, and it should connect to what was just said",
        context="Contrasts a graceful interjection with abrupt or self-centred ones.",
        answer_key="Building on what Riya just said, could I add a quick point about cost?",
        options=[
            "Building on what Riya just said, could I add a quick point about cost?",
            "Stop — let me talk now, I've been waiting.",
            "Anyway, forget all that, here's a completely different topic.",
        ],
        band="standard",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"gd_topics": ["Should AI replace campus placement interviews in India?"]},
        "group_discussion",
    )

    combined = " ".join([personalized.answer_key, *(personalized.options or [])])
    assert "quick point about cost" not in combined
    assert "AI replacing campus placement interviews in India" in combined
    assert personalized.answer_key in (personalized.options or [])


def test_gd_bridge_personalization_rewrites_derailed_discussion_to_selected_topic():
    from app.content.schema import BridgeExercise
    from app.graph.nodes.bridge import personalize_bridge_exercise

    exercise = BridgeExercise(
        id="gd_09_steer_derailed_bx1",
        type="fill_blank",
        sentence="I think we've ___ a bit — the real question is whether the budget should grow at all.",
        hint="a verb meaning to wander off the topic",
        context="Drills a redirect phrase for a derailed discussion.",
        answer_key="drifted",
        band="foundational",
    )

    personalized = personalize_bridge_exercise(
        exercise,
        {"gd_topics": ["Should AI replace campus placement interviews in India?"]},
        "group_discussion",
    )

    assert "budget should grow" not in personalized.sentence
    assert "AI replacing campus placement interviews in India" in personalized.sentence
    assert personalized.answer_key == "drifted"


def test_gd_prep_followup_prompts_lock_to_selected_topic():
    from app.ai.prompts import build_challenge_prompt, build_strengthen_prompt
    from app.content.registry import get_node

    node = get_node("gd_01_stake_position")
    career_context = {
        "gd_topics": ["Should AI replace campus placement interviews in India?"],
    }
    diagnosis = {
        "understanding": "The learner gave a clear initial stance.",
        "strengths": ["specific position"],
        "errors": ["needs stronger support"],
        "next_focus": "add one concrete reason tied to campus hiring",
        "affect": "focused",
    }
    messages = [
        {
            "role": "user",
            "content": (
                "AI can screen resumes, but final campus placement interviews "
                "still need human judgment."
            ),
        }
    ]

    strengthen = build_strengthen_prompt(
        node,
        messages,
        diagnosis,
        memory_context=[],
        career_context=career_context,
    )
    challenge = build_challenge_prompt(
        node,
        messages,
        diagnosis,
        memory_context=[],
        career_context=career_context,
    )

    for prompt in (strengthen, challenge):
        assert "Should AI replace campus placement interviews in India?" in prompt
        assert "Do not switch to an unrelated GD topic" in prompt
        assert "remote work" not in prompt.lower()


def test_challenge_prompt_avoids_mastery_and_celebration_language():
    from app.ai.prompts import build_challenge_prompt
    from app.content.registry import get_node

    prompt = build_challenge_prompt(
        get_node("int_01_elevator_pitch"),
        messages=[
            {
                "role": "user",
                "content": "I am a backend engineer who improved checkout reliability.",
            }
        ],
        diagnosis={
            "understanding": "The learner gave a usable concise answer.",
            "strengths": ["clear role"],
            "errors": [],
            "next_focus": "pressure-test with a sharper transfer variant",
            "affect": "focused",
        },
        memory_context=[],
    )
    challenge_tail = prompt.split("Recent conversation:", 1)[-1].lower()

    assert "near-mastered" not in challenge_tail
    assert "near mastery" not in challenge_tail
    assert "mastered" not in challenge_tail
    assert "celebrate" not in challenge_tail
    assert "harder transfer check" in challenge_tail
    assert "acknowledge briefly" in challenge_tail


def test_interview_prep_followup_prompts_lock_to_role_and_recent_thread():
    from app.ai.prompts import build_challenge_prompt, build_strengthen_prompt
    from app.content.registry import get_node

    node = get_node("int_07_clarify_before_answering")
    career_context = {
        "primary_role": "Backend Software Engineer",
        "role_family": "software_technical",
        "target_roles": ["Platform Engineer"],
        "resume_facts": ["Built FastAPI payment and checkout reliability dashboards"],
    }
    diagnosis = {
        "understanding": "The learner asked a clarifying question with backend and user-trust angles.",
        "strengths": ["offered concrete backend/payment scopes"],
        "errors": ["can be more concise"],
        "next_focus": "ask a sharper clarifier tied to backend payment systems",
        "affect": "confident",
    }
    messages = [
        {
            "role": "user",
            "content": (
                "Before I answer, do you want me to focus on backend risks of "
                "digital payments like latency and fraud, or user trust?"
            ),
        }
    ]

    strengthen = build_strengthen_prompt(
        node,
        messages,
        diagnosis,
        memory_context=[],
        career_context=career_context,
    )
    challenge = build_challenge_prompt(
        node,
        messages,
        diagnosis,
        memory_context=[],
        career_context=career_context,
    )

    for prompt in (strengthen, challenge):
        assert "Interview prep context lock" in prompt
        assert "Backend Software Engineer" in prompt
        assert "digital payments" in prompt
        assert "Do not introduce unrelated domains" in prompt
        assert "remote work culture" in prompt
        assert "backend/API/reliability" in prompt


def test_gd_prep_opening_prompt_keeps_warmup_on_selected_topic():
    from app.ai.prompts import build_opening_prompt
    from app.content.registry import get_node

    prompt = build_opening_prompt(
        get_node("gd_04_build_on_others"),
        memory_context=[],
        career_context={
            "primary_role": "Backend Software Engineer",
            "role_family": "software_technical",
            "gd_topics": ["Should AI replace campus placement interviews in India?"],
        },
    )

    assert "Should AI replace campus placement interviews in India?" in prompt
    assert "GD prep opening contract" in prompt
    assert "Do not use role-specific interview, coding, or technical-meeting" in prompt
    assert "technical-meeting scenarios" in prompt
    assert "do not switch the selected gd topic" in prompt.lower()
    assert "a different name, place, or topic" not in prompt


def test_interview_prep_opening_does_not_replace_node_with_weakness_warmup():
    from app.ai.behaviors import behavior_for_value
    from app.ai.prompts import build_opening_prompt
    from app.content.registry import get_node

    prompt = build_opening_prompt(
        get_node("int_05_why_this_role"),
        memory_context=[],
        behavior=behavior_for_value("interview_prep"),
        weaknesses=[
            {
                "skill_id": "technical_tradeoff",
                "hit_count": 3,
                "last_raw": "Explain Redis queues versus other queue systems.",
            }
        ],
        career_context={
            "primary_role": "Backend Software Engineer",
            "role_family": "software_technical",
        },
    )

    assert "Today's skill: Why This Company" in prompt
    assert "Do not open with a separate weak-spot warm-up" in prompt
    assert "Use remembered weak spots only to tailor examples" in prompt
    assert "open with a 10-second warm-up" not in prompt
    assert "re-tests THAT first" not in prompt


@pytest.mark.asyncio
async def test_interview_report_flags_repeated_prompts_as_assessment_caveat(monkeypatch):
    from app.ai.schemas import SimulationReport
    from app.content.task_types import TaskType
    from app.services.simulation_service import score_session

    async def fake_evaluate_simulation(*_args, **_kwargs):
        return SimulationReport(
            score=0.8,
            summary="The candidate stayed composed.",
            strengths=["Clear project context"],
            improvements=["Elaborate further on the repeated Redis vs memcached prompt."],
            clarity_score=0.8,
            confidence_score=0.78,
        )

    monkeypatch.setattr("app.services.simulation_service.evaluate_simulation", fake_evaluate_simulation)

    repeated = "Can you explain the Redis vs memcached tradeoff in your backend project?"
    state = {
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Mixed interview for backend engineer",
        "scenario_config": {"target_role": "Backend Software Engineer"},
        "career_context": {"primary_role": "Backend Software Engineer"},
        "blackboard": {"qualities": [0.8, 0.78, 0.76, 0.75]},
        "messages": [
            {"role": "assistant", "speaker_name": "Interviewer", "content": repeated},
            {"role": "assistant", "speaker_name": "Interviewer", "content": repeated},
            {"role": "assistant", "speaker_name": "Interviewer", "content": repeated},
            {"role": "user", "content": "I used Redis for richer data structures and persistence tradeoffs."},
            {"role": "assistant", "speaker_name": "Interviewer", "content": "Tell me about a teammate disagreement."},
            {"role": "user", "content": "I disagreed with microservices for a small CRUD tool and explained why a modular monolith fit better."},
            {"role": "assistant", "speaker_name": "Interviewer", "content": "Tell me about a production failure."},
            {"role": "user", "content": "I caused a migration lock, helped rollback, and added traffic-window checks."},
            {"role": "assistant", "speaker_name": "Interviewer", "content": "Tell me about leadership."},
            {"role": "user", "content": "I mentored two juniors until they needed only minor review notes."},
            {"role": "assistant", "speaker_name": "Interviewer", "content": "Tell me about prioritization."},
            {"role": "user", "content": "I delayed a dashboard polish task so the team could fix checkout errors before launch."},
            {"role": "assistant", "speaker_name": "Interviewer", "content": "Tell me about handling ambiguity."},
            {"role": "user", "content": "I split an unclear compliance request into reversible milestones and got legal review on the risky pieces first."},
        ],
    }

    report = await score_session(state)

    assert report.assessment_caveats
    assert any("repeated" in caveat.lower() for caveat in report.assessment_caveats)
    assert report.simulator_integrity_notes
    assert "unanswered prompt" in report.simulator_integrity_notes[0].lower()
    assert all("elaborate further" not in item.lower() for item in report.improvements)


@pytest.mark.asyncio
async def test_progression_map_returns_display_safe_completed_career_ready_state(store):
    from app.services import session_service as svc

    await store.upsert_mastery(
        "user-1",
        "int_01_elevator_pitch",
        ema=0.0,
        attempts=3,
        clean_pass=False,
        node_completed=True,
        node_mastered=False,
        display_status="active",
    )

    rows = await svc.get_progression_map("user-1", "interview")
    first = next(row for row in rows if row["node_id"] == "int_01_elevator_pitch")

    assert first["status"] == "ready_to_advance"
    assert first["completed"] is True
    assert first["mastered"] is False
    assert first["raw_mastery"] == 0.0
    assert first["display_mastery"] == 0.0
    assert first["attempts"] == 3
