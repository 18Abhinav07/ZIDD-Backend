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


def _humour_guided_activity(state: dict) -> tuple[dict, dict, dict]:
    level = state["levels"][0]
    step = next(
        item
        for item in level["teaching_steps"]
        if item["phase"] == "guided_practice"
    )
    activity = next(
        item
        for item in step["variant_pool"]
        if "funny" in str(item["prompt"]).casefold()
    )
    return level, step, activity


def _attach_feedback_for_activity(
    state: dict,
    *,
    level: dict,
    step: dict,
    activity: dict,
    feedback: dict,
) -> None:
    variant_id = str(activity["variant_id"])
    state["last_feedback"] = {
        "activity_id": (
            f"{level['level_id']}:{step['step_id']}:{variant_id}:1"
        ),
        "level_id": level["level_id"],
        "kind": "v2_guided_practice",
        "correct": True,
        "message": feedback["what_worked"],
    }
    curriculum._set_feedback_v2(state, feedback)


def test_private_feedback_detection_matches_secret_terms_not_word_substrings():
    assert not curriculum._contains_private_feedback_detail(
        "A related phrase is not automatically the requested response.",
        private_tokens={"late"},
    )
    assert curriculum._contains_private_feedback_detail(
        "The word late is an authored answer and must not be shown here.",
        private_tokens={"late"},
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


def test_public_feedback_keeps_fresh_formative_variant_guidance():
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": "Which detail in the passage helps you decide?",
            "grading_mode": "selected_option",
        },
        answer="PRIVATE_WRONG_CHOICE",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": [],
            "misconception_tags": [],
        },
        next_action="fresh_variant_without_skill_evidence",
        updated_state={"status": "active", "phase": "learning"},
    )
    state = _state()
    curriculum._set_feedback_v2(state, feedback)

    response = _public_response(state)

    assert response["feedback_v2"]["correct"] is False
    assert (
        response["feedback_v2"]["retry_policy"]
        == "fresh_variant_without_skill_evidence"
    )
    assert response["feedback_v2"]["what_worked"] == (
        "That choice does not fit the visible clue yet."
    )


def test_public_feedback_scopes_redaction_to_the_activity_that_created_it():
    state = curriculum.new_curriculum_state(
        school_profile={
            "subject_ids": ["english"],
            "target_class_no": 5,
            "preferred_teaching_language": "en",
        },
        placement_report=None,
        recap_session=None,
    )
    level, step, activity = _humour_guided_activity(state)
    feedback = curriculum._v2_feedback_action(
        activity=activity,
        answer="compare belief with reality",
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
    _attach_feedback_for_activity(
        state,
        level=level,
        step=step,
        activity=activity,
        feedback=feedback,
    )

    response = _public_response(state)

    assert response["feedback_v2"]["what_worked"] == (
        "You explained the mismatch between what the character believes and "
        "what the reader can see."
    )
    assert "compare belief with reality" not in repr(response)


def test_public_feedback_still_redacts_answer_key_from_its_own_activity():
    state = curriculum.new_curriculum_state(
        school_profile={
            "subject_ids": ["english"],
            "target_class_no": 5,
            "preferred_teaching_language": "en",
        },
        placement_report=None,
        recap_session=None,
    )
    level, step, activity = _humour_guided_activity(state)
    feedback = {
        "outcome": "correct",
        "feedback_type": "affirmation",
        "correct": True,
        "scored": True,
        "response_excerpt": "",
        "what_worked": "You chose compare belief with reality.",
        "criterion_gap": None,
        "misconception_tag": None,
        "next_support": "Continue to the next authored learning step.",
        "retry_policy": "advance",
        "allowed_next_actions": ["answer_next_activity"],
    }
    _attach_feedback_for_activity(
        state,
        level=level,
        step=step,
        activity=activity,
        feedback=feedback,
    )

    response = _public_response(state)

    assert response["feedback_v2"]["what_worked"] == "You completed this learning step."
    assert "compare belief with reality" not in repr(response)


def test_success_feedback_prefers_the_authored_learning_move_without_revealing_key():
    accepted_answer = "keep the same event"
    authored_feedback = "You protected the original event while planning the story."
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": "Which planning rule protects the original event?",
            "grading_mode": "selected_option",
            "accepted_answers": [accepted_answer],
            "success_feedback": authored_feedback,
        },
        answer=accepted_answer,
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

    assert feedback["what_worked"] == authored_feedback
    assert accepted_answer not in repr(feedback)


def test_success_feedback_for_route_summary_names_the_route_not_generic_main_idea():
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": "Summarize the napkin's movement from cause to outcome.",
            "grading_mode": "strict_open_rubric",
            "knowledge_components": [
                "reading.event_sequence",
                "reading.paragraph_main_idea",
            ],
        },
        answer="PRIVATE_LEARNER_ROUTE_SUMMARY",
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

    assert feedback["what_worked"] == (
        "You tracked the object's movement from what started it to where it ended."
    )
    assert "PRIVATE_LEARNER_ROUTE_SUMMARY" not in repr(feedback)


def test_success_feedback_for_a_choice_does_not_mislabel_it_as_sentence_writing():
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": "Which sentence is fully supported by the fact packet?",
            "grading_mode": "selected_option",
        },
        answer="PRIVATE_SELECTED_OPTION",
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

    assert feedback["what_worked"] == "You matched your choice to a visible clue."
    assert "completed the sentence" not in feedback["what_worked"].casefold()


def test_multi_clue_task_feedback_names_the_required_reasoning_structure():
    hint = curriculum._learner_visible_task_recheck_hint(
        {
            "prompt": (
                "Decide what Iqra should do and justify the decision with both clues."
            ),
        }
    )

    assert hint == "State your decision, then explain how both visible clues support it."
    assert "Iqra" not in hint
    assert "wallet" not in hint.casefold()


def test_success_feedback_describes_multi_skill_story_and_pattern_work():
    story_feedback = curriculum._learner_visible_success_move(
        {
            "prompt": "Turn this original verse into a short past-tense story.",
            "knowledge_components": [
                "grammar.tense_usage",
                "writing.summary_own_words",
            ],
        }
    )
    pattern_feedback = curriculum._learner_visible_success_move(
        {
            "prompt": (
                "Explain the written pattern and how both contexts show different "
                "meanings. Then use light in a new complete sentence."
            ),
            "knowledge_components": [
                "vocab.spelling",
                "reading.word_meaning_context",
                "vocab.chapter_word_usage",
            ],
        }
    )
    sequence_feedback = curriculum._learner_visible_success_move(
        {
            "prompt": "Which event happened second?",
            "knowledge_components": [
                "reading.paragraph_main_idea",
                "reading.inference_reason",
            ],
        }
    )
    first_aid_feedback = curriculum._learner_visible_success_move(
        {
            "prompt": "Who promises to bring the first-aid box?",
            "grading_mode": "selected_option",
            "knowledge_components": ["reading.dialogue_attribution"],
        }
    )
    dialogue_feedback = curriculum._learner_visible_success_move(
        {
            "prompt": "Name each speaker and explain how the reply responds.",
            "knowledge_components": [
                "reading.dialogue_attribution",
                "writing.dialogue",
            ],
        }
    )

    assert story_feedback == (
        "You turned the verse into a clear past-tense story while keeping the "
        "events in order."
    )
    assert pattern_feedback == (
        "You compared the spelling pattern, explained both meanings from context, "
        "and used the word in a new sentence."
    )
    assert sequence_feedback == (
        "You followed the events in the order the task asked for."
    )
    assert first_aid_feedback == "You identified the speaker who makes the promise."
    assert dialogue_feedback == (
        "You identified the speakers and explained how the reply carries the conversation forward."
    )


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
    assert prompt.casefold() not in public_feedback["criterion_gap"].casefold()
    assert "visible task" in public_feedback["criterion_gap"].casefold()
    assert "bridge" in public_feedback["next_support"].casefold()
    assert learner_answer not in repr(state)
    assert learner_answer not in repr(response)


def test_open_word_usage_feedback_names_the_missing_response_move_without_answer_key():
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": "Infer the chapter word and use it in another setting.",
            "grading_mode": "strict_open_rubric",
            "knowledge_components": ["reading.word_meaning_context"],
        },
        answer="PRIVATE_PARTIAL_WORD_RESPONSE",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": [
                "chapter_words_target",
                "chapter_words_target:detail_2",
            ],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    guidance = str(feedback["criterion_gap"]).casefold()

    assert "explain the word's meaning" in guidance
    assert "new sentence" in guidance
    assert "re-read the visible task" not in guidance
    assert "looked closely" not in guidance
    assert "PRIVATE_PARTIAL_WORD_RESPONSE" not in repr(feedback)


def test_story_feedback_does_not_turn_a_generic_detail_gap_into_vocab_advice():
    feedback = curriculum._v2_feedback_action(
        activity={
            "prompt": (
                "Retell the ribbon event briefly in your own words and include the "
                "supplied result without inventing a new ending."
            ),
            "grading_mode": "strict_open_rubric",
            "knowledge_components": [
                "grammar.tense_usage",
                "writing.complete_sentence",
                "writing.summary_own_words",
            ],
        },
        answer="PRIVATE_TOO_SHORT_STORY",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": [
                "poem_to_story_transfer:detail_2",
                "poem_to_story_transfer:detail_3",
            ],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    guidance = str(feedback["criterion_gap"]).casefold()

    assert "supplied events" in guidance
    assert "original order" in guidance
    assert "time clue" not in guidance
    assert "word in a clear setting" not in guidance
    assert "PRIVATE_TOO_SHORT_STORY" not in repr(feedback)


def test_public_response_keeps_safe_selected_option_feedback_for_live_chapter_content():
    state = curriculum.new_curriculum_state(
        school_profile={
            "subject_ids": ["english"],
            "target_class_no": 5,
            "preferred_teaching_language": "en",
        },
        placement_report=None,
        recap_session=None,
    )
    spelling_level = state["levels"][4]
    activity = next(
        step["activity"]
        for step in spelling_level["teaching_steps"]
        if step["phase"] == "co_construct"
    )
    feedback = curriculum._v2_feedback_action(
        activity=activity,
        answer="wide",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": ["vocab:spelling:letter_order"],
            "misconception_tags": ["letter_order_error"],
        },
        next_action="advance_with_diagnostic_support",
        updated_state={"status": "active", "phase": "learning"},
    )
    curriculum._set_feedback_v2(state, feedback)

    response = _public_response(state)

    assert response["feedback_v2"]["what_worked"] == (
        "That spelling needs another careful look."
    )
    assert "compare each letter" in response["feedback_v2"]["criterion_gap"].casefold()
    assert "spectacles" not in repr(response["feedback_v2"]).casefold()


def test_public_feedback_keeps_corrective_guidance_when_prompt_shares_hidden_term():
    learner_answer = "PRIVATE_LEARNER_PARTIAL_ANSWER"
    prompt = (
        "Infer reliable, identify the collective noun class, and write a different "
        "sentence that shows the meaning."
    )
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
            "missing_criteria": ["chapter:independent:requirement-2"],
            "misconception_tags": [],
        },
        next_action="challenge_fallback",
        updated_state={"status": "active", "phase": "learning"},
    )
    state = _state()
    state["chapter"] = {"accepted_answers": ["reliable"]}
    curriculum._set_feedback_v2(state, feedback)

    response = _public_response(state)
    public_feedback = response["feedback_v2"]

    assert public_feedback["correct"] is False
    assert public_feedback["scored"] is True
    assert "three parts" in public_feedback["criterion_gap"].casefold()
    assert prompt.casefold() not in public_feedback["criterion_gap"].casefold()
    assert learner_answer not in repr(response)


def test_public_feedback_recovers_signed_legacy_prompt_echo_without_leaking_it():
    prompt = (
        "Infer reliable, identify the collective noun class, and write a different "
        "sentence that shows the meaning."
    )
    state = _state()
    state["chapter"] = {"accepted_answers": ["reliable"]}
    curriculum._set_feedback_v2(
        state,
        {
            "outcome": "needs_support",
            "feedback_type": "corrective",
            "correct": False,
            "scored": True,
            "response_excerpt": "",
            "what_worked": "Start with one visible clue before you try again.",
            "criterion_gap": f'Re-read the task: "{prompt}"',
            "misconception_tag": None,
            "next_support": "Build this skill from the first teaching step.",
            "retry_policy": "challenge_fallback",
            "allowed_next_actions": ["answer_next_activity"],
        },
    )

    response = _public_response(state)
    public_feedback = response["feedback_v2"]

    assert public_feedback["correct"] is False
    assert public_feedback["scored"] is True
    assert public_feedback["retry_policy"] == "challenge_fallback"
    assert "complete each part" in public_feedback["criterion_gap"].casefold()
    assert prompt.casefold() not in repr(response).casefold()


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
