from __future__ import annotations

from app.services import school_rebuild_curriculum as curriculum


def _state() -> dict:
    return {
        "engine_version": curriculum.ENGINE_VERSION,
        "status": "active",
        "phase": "learning",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 5,
        "current_level_index": 0,
        "chapter": {},
        "levels": [],
        "hot_session_memory": {},
    }


def _public_response(state: dict) -> dict:
    return curriculum.public_curriculum_response(
        {
            "session_id": "feedback-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        }
    )


def test_public_response_keeps_trusted_success_feedback_task_grounded_and_answer_free():
    learner_answer = "PRIVATE_LEARNER_SUCCESS_ANSWER"
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": "Which source clue supports the idea?",
            "grading_mode": "selected_option",
        },
        answer=learner_answer,
        evaluation={
            "correct": True,
            "scored": True,
            "criteria": [],
            "missing_criteria": [],
            "misconception_tags": [],
        },
        next_action="advance",
        updated_state={"status": "active", "phase": "learning"},
    )
    state = _state()
    curriculum._set_feedback_v2(state, feedback)

    response = _public_response(state)
    public_feedback = response["feedback_v2"]

    assert "source clue" in public_feedback["what_worked"].casefold()
    assert "your response met visible task criteria" not in public_feedback[
        "what_worked"
    ].casefold()
    assert learner_answer not in repr(state)
    assert learner_answer not in repr(response)


def test_public_response_keeps_trusted_incorrect_feedback_visible_and_directs_bridge():
    learner_answer = "PRIVATE_LEARNER_INCORRECT_ANSWER"
    prompt = "Why did the child return to the library? Use one source clue."
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": prompt,
            "grading_mode": "strict_open_rubric",
        },
        answer=learner_answer,
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": ["story:guided:reason"],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )
    state = _state()
    curriculum._set_feedback_v2(state, feedback)

    response = _public_response(state)
    public_feedback = response["feedback_v2"]

    assert "add a reason" in public_feedback["criterion_gap"].casefold()
    assert prompt.casefold() in public_feedback["criterion_gap"].casefold()
    assert "bridge" in public_feedback["next_support"].casefold()
    assert learner_answer not in repr(state)
    assert learner_answer not in repr(response)


def test_stale_or_malicious_feedback_is_redacted_from_state_and_public_response():
    raw_answer = "PRIVATE_LEARNER_STALE_ANSWER"
    state = _state()
    state["feedback_v2"] = {
        "outcome": "needs_support",
        "feedback_type": "corrective",
        "correct": False,
        "scored": True,
        "response_excerpt": raw_answer,
        "what_worked": "MODEL_ANSWER_SENTINEL",
        "criterion_gap": "criterion:private_reason_rule PRIVATE_RUBRIC_SENTINEL",
        "misconception_tag": "criterion:private_reason_rule",
        "next_support": "ACCEPTED_ANSWER_SENTINEL",
        "retry_policy": "bridge_then_fresh_variant",
        "allowed_next_actions": ["answer_next_activity"],
        "learner_answer": raw_answer,
    }
    state["feedback_v2_public_digest"] = "stale-digest"

    normalized = curriculum.normalize_curriculum_state(state)
    response = _public_response(state)
    serialized = repr({"state": normalized, "response": response}).casefold()

    assert raw_answer.casefold() not in serialized
    assert "model_answer_sentinel" not in serialized
    assert "private_reason_rule" not in serialized
    assert "private_rubric_sentinel" not in serialized
    assert "accepted_answer_sentinel" not in serialized
    assert response["feedback_v2"]["what_worked"] == (
        "This learning step needs another visible clue."
    )

    malformed_state = _state()
    malformed_state["feedback_v2"] = {
        "outcome": ["needs_support"],
        "feedback_type": "corrective",
        "correct": False,
        "scored": True,
        "response_excerpt": "",
        "what_worked": "safe-looking text",
        "criterion_gap": None,
        "misconception_tag": None,
        "next_support": "Continue with the next visible learning step.",
        "retry_policy": "bridge_then_fresh_variant",
        "allowed_next_actions": ["answer_next_activity"],
    }
    malformed_state["feedback_v2_public_digest"] = "stale-digest"

    malformed_response = _public_response(malformed_state)

    assert malformed_response["feedback_v2"]["what_worked"] == (
        "This learning step needs another visible clue."
    )

    signed_state = _state()
    curriculum._set_feedback_v2(
        signed_state,
        {
            "outcome": "needs_support",
            "feedback_type": "corrective",
            "correct": False,
            "scored": True,
            "response_excerpt": "",
            "what_worked": "MODEL_ANSWER_SENTINEL",
            "criterion_gap": "criterion:private_reason_rule",
            "misconception_tag": None,
            "next_support": "ACCEPTED_ANSWER_SENTINEL",
            "retry_policy": "bridge_then_fresh_variant",
            "allowed_next_actions": ["answer_next_activity"],
        },
    )

    signed_response = _public_response(signed_state)
    signed_serialized = repr(signed_response).casefold()

    assert "model_answer_sentinel" not in signed_serialized
    assert "private_reason_rule" not in signed_serialized
    assert "accepted_answer_sentinel" not in signed_serialized
    assert signed_response["feedback_v2"]["what_worked"] == (
        "This learning step needs another visible clue."
    )
