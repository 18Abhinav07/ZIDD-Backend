from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_content import load_live_chapter_file
from app.services import school_rebuild_curriculum as curriculum
from app.services.school.open_answer_ai import _downgrade_untraceable_evidence


SKILL_ID = "reading.detail"
ANCHOR_ID = "eng_c5_ch01:detail:1"


def _continue_activity(phase: str) -> dict:
    return {
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": phase,
        "interaction_type": "continue",
        "evidence_role": "experience",
        "source_anchor_ids": [ANCHOR_ID],
        "knowledge_components": [SKILL_ID],
        "teaching_block": f"Teaching for {phase}.",
        "passage": f"A safe original passage for {phase}.",
        "prompt": "Continue when you are ready.",
        "options": [],
        "accepted_answers": [],
    }


def _choice_activity(
    phase: str,
    *,
    variant_id: str,
    accepted_answer: str,
    evidence_role: str,
) -> dict:
    return {
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": phase,
        "interaction_type": "single_choice",
        "evidence_role": evidence_role,
        "certifying_language": "en" if evidence_role == "certifying" else None,
        "source_anchor_ids": [ANCHOR_ID],
        "knowledge_components": [SKILL_ID],
        "pool_id": f"{phase}-pool",
        "variant_id": variant_id,
        "teaching_block": f"Use the detail skill in {variant_id}.",
        "passage": f"Original passage {variant_id}.",
        "prompt": f"Choose the supported detail for {variant_id}.",
        "options": [accepted_answer, f"distractor-{variant_id}"],
        "accepted_answers": [accepted_answer],
        "grading_mode": "selected_option",
        "response_mode": "short",
    }


def _step(phase: str) -> dict:
    if phase in {
        "connect",
        "explain",
        "model",
        "co_construct",
        "feedback",
    }:
        return {
            "step_id": f"step-{phase}",
            "phase": phase,
            "required": True,
            "activity": _continue_activity(phase),
        }
    evidence_role = "formative" if phase == "guided_practice" else "certifying"
    return {
        "step_id": f"step-{phase}",
        "phase": phase,
        "required": True,
        "pool_id": f"{phase}-pool",
        "variant_pool": [
            _choice_activity(
                phase,
                variant_id=f"{phase}-a",
                accepted_answer=f"answer-{phase}-a",
                evidence_role=evidence_role,
            ),
            _choice_activity(
                phase,
                variant_id=f"{phase}-b",
                accepted_answer=f"answer-{phase}-b",
                evidence_role=evidence_role,
            ),
        ],
    }


def _state() -> dict:
    support_check = {
        "knowledge_components": [SKILL_ID],
        "teaching_block": "Use one smaller clue, then return to a fresh example.",
        "passage": "A separate support passage.",
        "prompt": "Choose the support answer.",
        "options": ["support-answer", "support-distractor"],
        "accepted_answers": ["support-answer"],
        "grading_mode": "selected_option",
    }
    phases = (
        "connect",
        "explain",
        "model",
        "co_construct",
        "guided_practice",
        "feedback",
        "independent_application",
        "transfer",
        "review",
    )
    return curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "status": "active",
            "phase": "learning",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "preferred_teaching_language": "en",
            "current_level_index": 0,
            "chapter": {"chapter_id": "eng_c5_ch01", "title": "Chapter one"},
            "levels": [
                {
                    "level_id": "chapter-one-detail",
                    "title": "Find precise details",
                    "focus": "Use a detail as evidence",
                    "skill_ids": [SKILL_ID],
                    "status": "in_progress",
                    "current_step": "connect",
                    "attempts": [],
                    "v2_step_index": 0,
                    "v2_support_mode": None,
                    "used_variant_ids": [],
                    "episode_kind": "comprehension_studio",
                    "source_anchor_ids": [ANCHOR_ID],
                    "teaching_steps": [_step(phase) for phase in phases],
                    "checks": {
                        "guided_check": deepcopy(support_check),
                        "bridge": deepcopy(support_check),
                        "masterclass": deepcopy(support_check),
                        "independent_check": deepcopy(support_check),
                    },
                }
            ],
            "hot_session_memory": {},
            "active_interrupt": None,
            "interrupt_history": [],
            "interrupt_counts": {},
        }
    )


def _answer_current(state: dict, answer: str) -> tuple[dict, dict]:
    activity = curriculum._current_activity(state)
    assert activity is not None
    return curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        evidence_id=f"event:{activity['activity_id']}",
    )


def _advance_to_guided(state: dict) -> dict:
    for expected_phase in ("connect", "explain", "model", "co_construct"):
        activity = curriculum._current_activity(state)
        assert activity is not None
        assert activity["phase"] == expected_phase
        state, evaluation = _answer_current(state, "continue")
        assert evaluation["scored"] is False
    return state


def test_v2_cycle_advances_through_teaching_certification_and_review():
    state = _advance_to_guided(_state())

    state, _ = _answer_current(state, "answer-guided_practice-a")
    assert curriculum._current_activity(state)["phase"] == "feedback"
    state, _ = _answer_current(state, "continue")
    assert curriculum._current_activity(state)["phase"] == "independent_application"
    state, _ = _answer_current(state, "answer-independent_application-a")
    assert curriculum._current_activity(state)["phase"] == "transfer"
    state, _ = _answer_current(state, "answer-transfer-a")
    assert curriculum._current_activity(state)["phase"] == "review"
    with pytest.raises(ValueError, match="chapter_assessment_required_for_v2"):
        _answer_current(state, "answer-review-a")


def test_wrong_v2_answer_routes_to_support_then_fresh_authored_variant():
    state = _advance_to_guided(_state())
    first = curriculum._current_activity(state)
    assert first["variant"]["variant_id"] == "guided_practice-a"

    state, evaluation = _answer_current(state, "distractor-guided_practice-a")

    support = curriculum._current_activity(state)
    assert evaluation["correct"] is False
    assert support["support_mode"] == "bridge"
    assert state["feedback_v2"]["retry_policy"] == "bridge_then_fresh_variant"
    assert state["feedback_v2"]["criterion_gap"]
    assert "distractor-guided_practice-a" in state["feedback_v2"]["response_excerpt"]

    state, _ = _answer_current(state, "support-answer")
    retry = curriculum._current_activity(state)

    assert retry["phase"] == "guided_practice"
    assert retry["variant"]["variant_id"] == "guided_practice-b"
    assert retry["passage"] != first["passage"]
    assert state["hot_session_memory"]["active_support_count"] == 1


def test_v2_feedback_uses_the_visible_prompt_instead_of_internal_rubric_ids():
    state = _advance_to_guided(_state())
    activity = curriculum._current_activity(state)

    state, _ = _answer_current(state, "distractor-guided_practice-a")
    feedback = state["feedback_v2"]

    assert "authored answer match" not in feedback["criterion_gap"].casefold()
    assert "required idea" not in feedback["criterion_gap"].casefold()
    assert activity["prompt"] in feedback["criterion_gap"]


def test_v2_feedback_names_a_safe_own_words_gap_without_leaking_an_answer():
    prompt = "Write the three events in your own words."
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "summarize an event",
            "prompt": prompt,
            "rubric_criteria": [
                {
                    "id": "summary:guided:1:own_words",
                    "description": "Uses original sentences rather than copying labels.",
                    "required": True,
                    "min_quality": 0.7,
                }
            ],
        },
        answer="Problem: the ball travelled away. Response: pupils asked for help.",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [
                {
                    "id": "summary:guided:1:own_words",
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": "Response: pupils asked for help.",
                }
            ],
            "missing_criteria": ["summary:guided:1:own_words"],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    gap = feedback["criterion_gap"].casefold()
    assert "own words" in gap
    assert "copy" in gap
    assert prompt.casefold() in gap
    assert "summary:guided:1:own_words" not in gap


def test_v2_success_feedback_is_anchored_to_the_learners_saved_answer():
    state = _advance_to_guided(_state())

    state, _ = _answer_current(state, "answer-guided_practice-a")
    feedback = state["feedback_v2"]

    assert "answer-guided_practice-a" in feedback["what_worked"]
    assert "required idea" not in feedback["what_worked"].casefold()


def test_v2_success_feedback_uses_validated_evidence_beyond_the_answer_prefix():
    evidence = "the atlas clue proves where Ria searched"
    internal_focus = "support an inference with a visible clue"
    answer = ("A long opening sentence without the useful detail. " * 5) + evidence

    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": internal_focus,
            "prompt": "Which clue supports your inference?",
        },
        answer=answer,
        evaluation={
            "correct": True,
            "scored": True,
            "criteria": [
                {
                    "id": "private_criterion_id",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": evidence,
                }
            ],
            "missing_criteria": [],
            "misconception_tags": [],
        },
        next_action="advance",
        updated_state={"status": "active", "phase": "learning"},
    )

    assert evidence in feedback["what_worked"]
    assert internal_focus not in feedback["what_worked"]
    assert "private_criterion_id" not in repr(feedback)


@pytest.mark.parametrize("correct", (True, False))
def test_v2_feedback_does_not_duplicate_terminal_evidence_punctuation(correct):
    evidence = "The helpful nurse carried the heavy box this morning."
    feedback = curriculum._v2_feedback_action(
        activity={"prompt": "Write one natural sentence."},
        answer=evidence,
        evaluation={
            "correct": correct,
            "scored": True,
            "criteria": [
                {
                    "id": "sentence",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": evidence,
                }
            ],
            "missing_criteria": [] if correct else ["sentence"],
            "misconception_tags": [],
        },
        next_action="advance" if correct else "bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    assert '.".' not in feedback["what_worked"]
    assert feedback["what_worked"].endswith('."')


def test_v2_miss_feedback_never_copies_hidden_rubric_descriptions():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "answer with a reason",
            "prompt": "Why did Ria return to the atlas?",
            "rubric_criteria": [
                {
                    "id": "private_reason_rule",
                    "description": "PRIVATE_RUBRIC_SENTINEL and MODEL_ANSWER_SENTINEL",
                }
            ],
            "model_answer": "MODEL_ANSWER_SENTINEL",
            "accepted_answers": ["ACCEPTED_ANSWER_SENTINEL"],
        },
        answer="I am not sure yet.",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [
                {
                    "id": "private_reason_rule",
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": "",
                }
            ],
            "missing_criteria": ["private_reason_rule"],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )
    serialized = repr(feedback)

    assert "PRIVATE_RUBRIC_SENTINEL" not in serialized
    assert "MODEL_ANSWER_SENTINEL" not in serialized
    assert "ACCEPTED_ANSWER_SENTINEL" not in serialized
    assert "Why did Ria return to the atlas?" in feedback["criterion_gap"]


def test_v2_supported_choice_feedback_corrects_without_revealing_the_answer():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "use a complete phrase",
            "prompt": "Which phrase names the matching unit naturally?",
            "grading_mode": "selected_option",
            "evidence_role": "supported",
            "options": ["spoke softly", "a pair of gloves"],
            "accepted_answers": ["a pair of gloves"],
        },
        answer="spoke softly",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": ["selected_option_match"],
            "misconception_tags": [],
        },
        next_action="advance_without_skill_evidence",
        updated_state={"status": "active", "phase": "learning"},
    )

    assert feedback["what_worked"] == "That choice does not fit the visible clue yet."
    assert "Eliminate each choice with a visible clue" in feedback["criterion_gap"]
    assert "Which phrase names the matching unit naturally?" in feedback["criterion_gap"]
    assert "a pair of gloves" not in repr(feedback)


def test_v2_sequence_choice_feedback_explains_immediately_before_without_answer_leak():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "track an object through ordered events",
            "prompt": "Where was the whistle immediately before it went indoors?",
            "grading_mode": "selected_option",
            "evidence_role": "supported",
            "options": ["on the bench", "inside the kit bag"],
            "accepted_answers": ["inside the kit bag"],
        },
        answer="on the bench",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": ["selected_option_match"],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    assert "Trace only the final two events" in feedback["criterion_gap"]
    assert "last place or action just before" in feedback["criterion_gap"]
    assert "inside the kit bag" not in repr(feedback)


def test_v2_dialogue_choice_feedback_points_to_reporting_verb_without_answer_leak():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "follow every speaker",
            "prompt": "Who promises to bring the first-aid box?",
            "grading_mode": "selected_option",
            "evidence_role": "supported",
            "options": ["Mira", "the coach"],
            "accepted_answers": ["Mira"],
        },
        answer="the coach",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": ["selected_option_match"],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    assert "follow the name or reporting verb" in feedback["criterion_gap"]
    assert "speaker of a different turn" in feedback["criterion_gap"]
    assert "Mira" not in repr(feedback)


def test_v2_open_feedback_names_each_missing_event_part_without_leaking_answers():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "track the travelling object",
            "prompt": "Retell the token's journey in three ordered steps.",
            "grading_mode": "strict_open_rubric",
            "evidence_role": "certifying",
        },
        answer="The conductor found it.",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": [
                "scooter_event_sequence:independent:1:start",
                "scooter_event_sequence:independent:1:middle",
            ],
            "misconception_tags": [],
        },
        next_action="challenge_fallback",
        updated_state={"status": "active", "phase": "learning"},
    )

    gap = feedback["criterion_gap"].casefold()
    assert "where or how the event begins" in gap
    assert "what happens between the beginning and ending" in gap
    assert "fell from renu's book" not in gap
    assert "slid down the aisle" not in gap
    assert feedback["retry_policy"] == "challenge_fallback"


def test_v2_open_feedback_turns_dialogue_gap_ids_into_child_facing_coaching():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "follow every speaker",
            "prompt": (
                "Identify both speakers, the listener in the first line, and "
                "Ravi's contribution."
            ),
            "grading_mode": "strict_open_rubric",
            "evidence_role": "certifying",
        },
        answer="The key was beside the whistle.",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": [
                "scooter_dialogue_and_speaker:independent:1:first_speaker",
                "scooter_dialogue_and_speaker:independent:1:listener",
                "scooter_dialogue_and_speaker:independent:1:contribution",
            ],
            "misconception_tags": [],
        },
        next_action="challenge_fallback",
        updated_state={"status": "active", "phase": "learning"},
    )

    gap = feedback["criterion_gap"].casefold()
    assert "who speaks first" in gap
    assert "who hears the line" in gap
    assert "what new information or action the reply adds" in gap
    assert "captain" not in gap
    assert "beside the whistle" not in gap


def test_v2_certifying_choice_feedback_does_not_reveal_the_answer():
    feedback = curriculum._v2_feedback_action(
        activity={
            "focus": "use a complete phrase",
            "prompt": "Which phrase names the matching unit naturally?",
            "grading_mode": "selected_option",
            "evidence_role": "certifying",
            "options": ["spoke softly", "a pair of gloves"],
            "accepted_answers": ["a pair of gloves"],
        },
        answer="spoke softly",
        evaluation={
            "correct": False,
            "scored": True,
            "criteria": [],
            "missing_criteria": ["selected_option_match"],
            "misconception_tags": [],
        },
        next_action="bridge_then_fresh_variant",
        updated_state={"status": "active", "phase": "learning"},
    )

    assert "a pair of gloves" not in feedback["criterion_gap"]


def test_hot_session_memory_records_traceable_instructional_state():
    state = _advance_to_guided(_state())
    activity = curriculum._current_activity(state)
    state, _ = _answer_current(state, "distractor-guided_practice-a")
    memory = state["hot_session_memory"]

    assert memory["last_activity_id"] == activity["activity_id"]
    assert memory["recent_evidence_ids"][-1] == f"event:{activity['activity_id']}"
    assert memory["recent_criterion_gaps"][-1]["criterion_id"] == "authored_answer_match"
    assert memory["unresolved_outcome_id"] == "chapter-one-detail"
    assert memory["next_instructional_action"] == "bridge_then_fresh_variant"
    assert activity["activity_id"] in memory["served_activity_ids"]
    assert memory["passage_fingerprints"]
    assert "guided_practice-a" in memory["used_variant_ids"]


def test_public_v2_activity_and_feedback_never_expose_grading_secrets():
    state = _advance_to_guided(_state())
    state, _ = _answer_current(state, "distractor-guided_practice-a")
    response = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )
    serialized = repr(response).casefold()

    assert "accepted_answers" not in serialized
    assert "answer_key" not in serialized
    assert "rubric_criteria" not in serialized
    assert response["feedback_v2"]["allowed_next_actions"] == [
        "answer_next_activity"
    ]


def test_public_curriculum_activity_explains_which_official_section_it_practises():
    state = _advance_to_guided(_state())
    state["chapter"]["book_title"] = "Santoor"
    state["chapter"]["source_anchors"] = [
        {
            "anchor_id": ANCHOR_ID,
            "section_label": "Let us Think",
            "page_start": 4,
            "page_end": 4,
            "source_url": "https://ncert.nic.in/textbook/pdf/example.pdf#page=4",
            "coverage_treatment": "zidd_equivalent",
            "required_for_chapter_certification": True,
        }
    ]
    response = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )

    reference = response["current_activity"]["source_reference"]
    assert reference["book_title"] == response["chapter"]["book_title"]
    assert reference["anchors"] == [
        {
            "anchor_id": ANCHOR_ID,
            "section_label": "Let us Think",
            "page_start": 4,
            "page_end": 4,
            "source_url": "https://ncert.nic.in/textbook/pdf/example.pdf#page=4",
            "coverage_treatment": "zidd_equivalent",
        }
    ]
    serialized = repr(response).casefold()
    assert "accepted_answers" not in serialized
    assert "rubric_criteria" not in serialized


def test_public_v2_payload_redacts_internal_criterion_ids_everywhere():
    state = _advance_to_guided(_state())
    state, _ = _answer_current(state, "distractor-guided_practice-a")
    response = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )
    serialized = repr(response).casefold()

    assert "authored_answer_match" not in serialized
    assert "criterion:" not in serialized
    assert "answer-guided_practice-a" not in serialized


def test_public_v2_feedback_redacts_untrusted_persisted_rubric_details():
    state = _advance_to_guided(_state())
    state["feedback_v2"] = {
        "outcome": "needs_support",
        "feedback_type": "corrective",
        "correct": False,
        "scored": True,
        "response_excerpt": "I need another clue.",
        "what_worked": "MODEL_ANSWER_SENTINEL",
        "criterion_gap": (
            "criterion:private_reason_rule PRIVATE_RUBRIC_SENTINEL"
        ),
        "misconception_tag": "criterion:private_reason_rule",
        "next_support": "BLOCKER_ID_SENTINEL",
        "retry_policy": "bridge_then_fresh_variant",
        "allowed_next_actions": ["answer_next_activity"],
    }
    state["last_feedback"] = {
        "activity_id": "activity-1",
        "level_id": "level-1",
        "kind": "guided_check",
        "correct": False,
        "message": "PRIVATE_RUBRIC_SENTINEL",
        "accepted_answers": ["ACCEPTED_ANSWER_SENTINEL"],
    }
    state["hot_session_memory"]["next_instructional_action"] = (
        "criterion:private_reason_rule"
    )

    response = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )
    serialized = repr(
        {
            "feedback_v2": response["feedback_v2"],
            "last_feedback": response["last_feedback"],
            "session_memory": response["session_memory"],
        }
    ).casefold()

    assert "private_reason_rule" not in serialized
    assert "criterion:" not in serialized
    assert "model_answer_sentinel" not in serialized
    assert "accepted_answer_sentinel" not in serialized
    assert "private_rubric_sentinel" not in serialized
    assert "blocker_id_sentinel" not in serialized


def test_public_last_feedback_whitelists_legacy_shape_without_feedback_v2():
    state = _advance_to_guided(_state())
    state["feedback_v2"] = None
    state["last_feedback"] = {
        "activity_id": "activity-1",
        "level_id": "level-1",
        "kind": "guided_check",
        "correct": False,
        "message": "PRIVATE_RUBRIC_SENTINEL",
        "blockers": ["BLOCKER_ID_SENTINEL"],
        "model_answer": "MODEL_ANSWER_SENTINEL",
    }

    response = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )

    assert set(response["last_feedback"]) == {
        "activity_id",
        "level_id",
        "kind",
        "correct",
        "message",
    }
    assert "sentinel" not in repr(response["last_feedback"]).casefold()


def test_v2_memory_note_uses_current_activity_skills_not_all_level_skills():
    state = _state()
    level = state["levels"][0]
    level["skill_ids"] = [SKILL_ID, "vocab.antonyms"]
    level["v2_step_index"] = 4
    level["current_step"] = "guided_practice"
    state["learner_memory"] = {
        "active_gaps": [
            {"skill_id": "vocab.antonyms", "gap": "private unrelated gap"}
        ],
        "improving_gaps": [
            {"skill_id": SKILL_ID, "gap": "private matching gap"}
        ],
    }

    activity = curriculum._current_activity(state)

    assert activity["assessed_skill_ids"] == [SKILL_ID]
    assert "building confidence" in activity["teaching_block"]
    assert "another careful try" not in activity["teaching_block"]
    assert "private unrelated gap" not in activity["teaching_block"]


def test_v2_experience_activity_without_assessed_skills_has_no_memory_note():
    state = _state()
    state["learner_memory"] = {
        "active_gaps": [{"skill_id": SKILL_ID, "gap": "private old gap"}],
        "improving_gaps": [],
    }

    activity = curriculum._current_activity(state)

    assert activity["assessed_skill_ids"] == []
    assert "Zidd remembers" not in activity["teaching_block"]
    assert "private old gap" not in activity["teaching_block"]


def test_live_class5_chapter1_has_nine_compact_disjoint_teaching_cycles():
    path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    chapter = load_live_chapter_file(path)
    canonical_phases = [
        "connect",
        "co_construct",
        "guided_practice",
        "independent_application",
        "transfer",
        "review",
    ]

    assert len(chapter.levels) == 9
    assert len(chapter.source_anchors or ()) == 13
    for level in chapter.levels:
        steps = list(level.teaching_steps or ())
        assert [step.phase for step in steps] == canonical_phases
        connect = steps[0].activity
        assert connect is not None
        assert "Worked example" in connect.passage
        strategy = connect.passage.split("Worked example", 1)[0]
        assert len(strategy.split()) >= 10
        assert sum(
            activity.interaction_type == "continue"
            for step in steps
            for activity in (
                [step.activity]
                if step.activity is not None
                else list(step.variant_pool or ())
            )
        ) == 1
        independent = next(
            step for step in steps if step.phase == "independent_application"
        )
        assert all(
            (
                "Before you try it alone:" in activity.teaching_block
                or activity.teaching_block.startswith("Work independently.")
            )
            for activity in independent.variant_pool or ()
        )
        activities = [
            activity
            for step in steps
            for activity in (
                [step.activity]
                if step.activity is not None
                else list(step.variant_pool or ())
            )
        ]
        passages = [activity.passage for activity in activities]
        assert len(passages) == len(set(passages))
        for phase in ("independent_application", "transfer", "review"):
            step = next(item for item in steps if item.phase == phase)
            assert len(step.variant_pool or ()) >= 3
        certifying = [
            activity
            for activity in activities
            if activity.evidence_role == "certifying"
        ]
        assert certifying
        assert all(activity.certifying_language == "en" for activity in certifying)


def test_live_chapter2_own_words_rubric_is_visible_in_the_learner_prompt():
    path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch02.json"
    )
    chapter = load_live_chapter_file(path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "scooter_summary_and_profile"
    )
    guided = next(
        step for step in level.teaching_steps or () if step.phase == "guided_practice"
    )
    activity = next(
        item
        for item in guided.variant_pool or ()
        if item.variant_id == "scooter_summary_and_profile:guided:1"
    )

    assert "own words" in activity.prompt.casefold()
    assert any(
        criterion.id.endswith(":own_words")
        for criterion in activity.rubric_criteria or ()
    )


def test_live_pair_phrase_checks_do_not_reject_concise_complete_sentences():
    path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    chapter = load_live_chapter_file(path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "papas_spectacles_order_and_pairs"
    )
    pair_sentence_checks = [
        activity.model_dump(mode="json")
        for step in level.teaching_steps or ()
        for activity in step.variant_pool or ()
        if activity.evaluation_mode == "llm_rubric"
        and "pair" in activity.prompt.casefold()
    ]

    assert pair_sentence_checks
    assert all(
        curriculum._open_answer_preflight(
            activity,
            "A pair of shoes lay outside.",
        )
        for activity in pair_sentence_checks
    )


def test_live_pair_phrase_transfer_accepts_a_new_pair_and_location_detail():
    path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    chapter = load_live_chapter_file(path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "papas_spectacles_order_and_pairs"
    )
    transfer_step = next(
        step for step in level.teaching_steps or () if step.phase == "transfer"
    )
    activity = next(
        item.model_dump(mode="json")
        for item in transfer_step.variant_pool or ()
        if item.variant_id == "papas_spectacles_order_and_pairs:transfer:v3"
    )
    activity.update(
        activity_id=activity["variant_id"],
        skill_ids=activity["knowledge_components"],
        assessed_skill_ids=activity["knowledge_components"],
    )
    answer = "A pair of shoes stood beside the front door."
    model_evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": "school.open.v1",
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": "order_and_pairs_target",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "A pair of bright red flags",
                },
                {
                    "id": "order_and_pairs_target:detail_2",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "beside the main entrance gate",
                },
                {
                    "id": "clear_relevant_english",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "The sentence is clear English.",
                },
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The sentence includes a pair and its location.",
        }
    )

    recovered = _downgrade_untraceable_evidence(
        model_evaluation,
        answer,
        activity,
    )
    result = curriculum.decide_semantic_concept_evaluation(
        activity,
        recovered,
        answer=answer,
    )

    assert all(criterion.met for criterion in recovered.criteria)
    assert all(
        criterion.evidence_quote.casefold() in answer.casefold()
        for criterion in recovered.criteria
    )
    assert result["correct"] is True


def test_live_pair_phrase_support_can_remediate_the_skills_it_triggers():
    path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    chapter = load_live_chapter_file(path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "papas_spectacles_order_and_pairs"
    )
    raw_level = level.model_dump(mode="json")
    pair_support = raw_level["checks"]["revision_level_1"]

    assert pair_support["interaction_type"] == "paragraph_text"
    assert pair_support["evidence_role"] == "supported"
    assert set(pair_support["knowledge_components"]) == {
        "vocab.chapter_word_usage",
        "writing.complete_sentence",
    }
    assert pair_support["evaluation_mode"] == "llm_rubric"


@pytest.mark.parametrize(
    ("variant_id", "answer"),
    (
        (
                "papas_spectacles_sound_lab:transfer:v3",
                (
                    "Coach and roach share -oach but begin with c and r. A coach "
                    "trains a team, while a roach is an insect. "
                    "Our coach taught the team a new defence."
                ),
        ),
        (
                "papas_spectacles_sound_lab:transfer:v4",
                (
                    "Flight and slight share -light but begin with f and s. A flight "
                    "is a journey through the air, while slight means small or minor. "
                    "A slight scratch marked the table."
                ),
        ),
    ),
)
def test_live_word_use_transfer_does_not_require_model_answer_wording(
    variant_id,
    answer,
):
    path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    chapter = load_live_chapter_file(path)
    level = next(
        item for item in chapter.levels if item.level_id == "papas_spectacles_sound_lab"
    )
    transfer_step = next(
        step for step in level.teaching_steps or () if step.phase == "transfer"
    )
    activity = next(
        item.model_dump(mode="json")
        for item in transfer_step.variant_pool or ()
        if item.variant_id == variant_id
    )
    activity.update(
        activity_id=activity["variant_id"],
        skill_ids=activity["knowledge_components"],
        assessed_skill_ids=activity["knowledge_components"],
    )
    assert not any(
        str(slot["id"]).endswith("_original_usage")
        for slot in activity["concept_slots"]
    )
    model_evaluation = _passing_open_evaluation(activity, answer)

    recovered = _downgrade_untraceable_evidence(
        model_evaluation,
        answer,
        activity,
    )
    result = curriculum.decide_semantic_concept_evaluation(
        activity,
        recovered,
        answer=answer,
    )

    assert not any(
        str(criterion["id"]).startswith("sound_lab_word_use_target:detail_")
        for criterion in activity["rubric_criteria"]
    )
    assert all(criterion.met for criterion in recovered.criteria)
    assert result["correct"] is True, result


def _passing_open_evaluation(activity: dict, answer: str) -> SchoolRubricEvaluation:
    evaluator_activity = curriculum.evaluator_activity_for_answer(activity, answer)
    assert evaluator_activity is not None
    criteria = []
    for criterion in evaluator_activity["rubric_criteria"]:
        criterion_id = str(criterion["id"])
        slot = next(
            (
                item
                for item in evaluator_activity.get("concept_slots") or []
                if str(item.get("id") or "") == criterion_id
            ),
            None,
        )
        evidence_quote = (
            str((slot.get("any_of") or [answer])[0]) if slot else answer
        )
        assert evidence_quote.casefold() in answer.casefold()
        criteria.append(
            {
                "id": criterion_id,
                "met": True,
                "quality": 1.0,
                "evidence_quote": evidence_quote,
            }
        )
    return SchoolRubricEvaluation.model_validate(
        {
            "schema_version": (
                "school.open.v1"
                if evaluator_activity.get("grading_mode")
                == "strict_open_rubric"
                else "school-v3-rubric-1"
            ),
            "item_id": evaluator_activity["activity_id"],
            "skill_ids": evaluator_activity["skill_ids"],
            "score": 1.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": criteria,
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The response uses the required evidence.",
        }
    )


def _passing_answer(activity: dict) -> tuple[str, SchoolRubricEvaluation | None]:
    if activity.get("interaction_type") == "continue":
        return "continue", None
    if activity.get("options"):
        answer = str((activity.get("accepted_answers") or [])[0])
        return answer, None
    if (
        activity.get("evaluation_mode") != "llm_rubric"
        and activity.get("accepted_answers")
    ):
        return str(activity["accepted_answers"][0]), None
    slots_by_id = {
        str(slot.get("id") or ""): slot
        for slot in activity.get("concept_slots") or []
    }
    ordered_ids = list(activity.get("ordered_concept_slot_ids") or [])
    selected_slot_ids = ordered_ids or list(slots_by_id)
    slot_phrases = [
        str((slots_by_id[slot_id].get("any_of") or [slot_id])[0])
        for slot_id in selected_slot_ids
        if slot_id in slots_by_id
    ]
    relevance_terms = [
        str(term) for term in activity.get("relevance_terms") or []
    ][:4]
    evidence_words = list(dict.fromkeys([*slot_phrases, *relevance_terms]))
    answer = (
        "In my own explanation, "
        + ", ".join(evidence_words)
        + " connect the important clue to the question. This gives a clear "
        "reason and explains the idea without copying the example."
    )
    return answer, _passing_open_evaluation(activity, answer)


def test_every_live_chapter_strong_path_completes_and_unlocks_in_order():
    for class_no in (2, 3, 4, 5):
        chapters = curriculum._available_chapters("english", class_no)
        latest_session = None

        for chapter_index, expected_chapter in enumerate(chapters):
            state = curriculum.new_curriculum_state(
                school_profile={
                    "profile_version_id": f"profile-{class_no}",
                    "target_class_no": class_no,
                    "subject_ids": ["english"],
                    "preferred_teaching_language": "en",
                },
                placement_report={
                    "report_id": f"report-{class_no}",
                    "unlock_state": "target_unlocked",
                },
                recap_session=None,
                latest_curriculum_session=latest_session,
            )
            assert state["chapter"]["chapter_id"] == expected_chapter["chapter_id"]

            answer_count = 0
            while state["status"] != "complete":
                activity = curriculum._current_activity(state)
                assert activity is not None
                answer, open_evaluation = _passing_answer(activity)
                state, evaluation = curriculum.apply_curriculum_answer(
                    state,
                    activity_id=activity["activity_id"],
                    answer=answer,
                    evidence_id=(
                        f"event:{class_no}:{chapter_index}:{answer_count}"
                    ),
                    open_answer_evaluation=open_evaluation,
                )
                assert evaluation["correct"] is True, {
                    "class_no": class_no,
                    "chapter_id": expected_chapter["chapter_id"],
                    "activity_id": activity["activity_id"],
                    "concept_slots": activity.get("concept_slots"),
                    "answer": answer,
                    "evaluation": evaluation,
                }
                answer_count += 1
                assert answer_count <= 220

            assert state["chapter_assessment"]["attempt_history"][-1]["passed"] is True
            latest_session = {
                "status": "complete",
                "flow_type": "curriculum",
                "subject_id": "english",
                "class_no": class_no,
                "state_json": state,
            }


def test_live_class5_chapter1_strong_path_reaches_chapter_check():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    answered = 0
    while state["phase"] == "learning":
        activity = curriculum._current_activity(state)
        assert activity is not None
        answer, open_evaluation = _passing_answer(activity)
        state, evaluation = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=answer,
            evidence_id=f"event:{answered}",
            open_answer_evaluation=open_evaluation,
        )
        assert evaluation["correct"] is True
        answered += 1
        assert answered <= 90

    assert answered == 54
    assert state["phase"] == "chapter_check"
    assert all(level["status"] == "complete" for level in state["levels"])
    assert state["chapter_assessment"]["attempt_no"] == 1
    assert len(state["chapter_assessment"]["selected_item_ids"]) == 16


def test_live_class5_chapter1_failed_check_completes_authored_remediation_and_retests():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-remediation",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-remediation",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )

    answered = 0
    while state["phase"] == "learning":
        activity = curriculum._current_activity(state)
        assert activity is not None
        answer, open_evaluation = _passing_answer(activity)
        state, evaluation = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=answer,
            evidence_id=f"remediation:learning:{answered}",
            open_answer_evaluation=open_evaluation,
        )
        assert evaluation["correct"] is True
        answered += 1
        assert answered <= 90

    assert state["phase"] == "chapter_check"
    first_form_ids = set(state["chapter_assessment"]["selected_item_ids"])
    while state["phase"] == "chapter_check":
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, evaluation = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect",
            evidence_id=f"remediation:check:{answered}",
            open_answer_preflight_failed=(
                activity.get("evaluation_mode") == "llm_rubric"
            ),
        )
        assert evaluation["correct"] is False
        answered += 1

    assert state["phase"] == "remediation", state.get("support_required")
    assert state.get("support_required") is None
    assert state["remediation_queue"]

    remediation_count = 0
    while state["phase"] == "remediation":
        activity = curriculum._current_activity(state)
        assert activity is not None
        answer, open_evaluation = _passing_answer(activity)
        state, evaluation = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=answer,
            evidence_id=f"remediation:support:{remediation_count}",
            open_answer_evaluation=open_evaluation,
        )
        assert evaluation["correct"] is True
        remediation_count += 1
        assert remediation_count <= 40

    assert state["phase"] == "chapter_check"
    assert state["chapter_assessment"]["attempt_no"] == 2
    assert first_form_ids.isdisjoint(
        set(state["chapter_assessment"]["selected_item_ids"])
    )

    while state["phase"] == "chapter_check":
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, evaluation = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect",
            evidence_id=f"remediation:second-check:{answered}",
            open_answer_preflight_failed=(
                activity.get("evaluation_mode") == "llm_rubric"
            ),
        )
        assert evaluation["correct"] is False
        answered += 1

    assert state["phase"] == "needs_support"
    assert state["status"] == "active"
    assert state["support_required"]["reason"] == "chapter_check_attempts_exhausted"
    assert state["support_required"]["cap"] == {
        "used": 2,
        "limit": 2,
        "scope": "chapter_check",
    }


@pytest.mark.parametrize("chapter_no", range(1, 11))
def test_live_class5_two_assessment_forms_are_fully_disjoint(chapter_no):
    path = (
        Path.cwd()
        / "app/content/school_rebuild_chapters/english/class_5"
        / f"eng_c5_ch{chapter_no:02d}.json"
    )
    chapter = load_live_chapter_file(path).runtime_dict()
    state = {
        "chapter_assessment": curriculum._new_chapter_assessment_state(
            chapter["chapter_assessment"]
        )
    }

    first = curriculum._begin_chapter_assessment(state)
    first_ids = set(first["chapter_assessment"]["selected_item_ids"])
    second = curriculum._begin_chapter_assessment(first)
    second_ids = set(second["chapter_assessment"]["selected_item_ids"])

    assert len(first_ids) == 16
    assert len(second_ids) == 16
    assert first_ids.isdisjoint(second_ids)
