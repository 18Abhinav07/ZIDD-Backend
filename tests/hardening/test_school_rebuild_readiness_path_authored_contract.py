from copy import deepcopy

import pytest

from app.services import school_rebuild_recap as recap


def _report(*, track_id: str = "english.c3.word_roles") -> dict:
    return {
        "profile_version_id": "profile-v1",
        "report_id": "report-v1",
        "placement_session_id": "placement-v1",
        "subject_id": "english",
        "target_class_no": 3,
        "active_learning_class_no": 2,
        "recommended_recap_modules": [
            {
                "module_id": "recap_word_roles",
                "title": "Word jobs",
                "source_class_no": 2,
                "target_class_no": 3,
                "focus": "Recognize a word's job in a sentence",
                "placement_track_id": track_id,
                "primary_skill_id": "grammar.noun_verb_adjective",
            }
        ],
    }


def test_readiness_path_uses_same_track_authored_items_without_label_prompt_fallback():
    state = recap.new_recap_state(_report())
    module = state["modules"][0]
    activity = recap._current_activity(state)

    assert module["placement_track_id"] == "english.c3.word_roles"
    assert module["primary_skill_id"] == "grammar.noun_verb_adjective"
    assert "person, place, animal, or thing" in module["teaching_block"]
    assert activity["prompt"] == "Which word names a person?"
    assert activity["passage"] == "The teacher wrote neatly."
    assert "Write the answer for" not in str(state)
    assert "What is the main clue for" not in str(state)


def test_readiness_path_fails_closed_when_placement_track_content_is_missing():
    with pytest.raises(ValueError, match="recap_content_not_authored"):
        recap.new_recap_state(_report(track_id="english.c3.missing_track"))


def test_readiness_path_requires_guided_independent_and_transfer_evidence():
    state = recap.new_recap_state(_report())

    guided = recap._current_activity(state)
    state, _ = recap.apply_recap_answer(
        state,
        activity_id=guided["activity_id"],
        answer="teacher",
    )
    assert recap._current_activity(state)["kind"] == "independent_check"

    independent = recap._current_activity(state)
    state, independent_evaluation = recap.apply_recap_answer(
        state,
        activity_id=independent["activity_id"],
        answer="rushed",
    )
    assert state["status"] == "active"
    transfer = recap._current_activity(state)
    assert transfer["kind"] == "transfer_check"
    assert transfer["source_class_no"] == 3
    assert "complete" not in state["last_feedback"]["message"].lower()
    assert independent_evaluation["correct"] is True
    assert independent_evaluation["source_class_no"] == 3

    state, _ = recap.apply_recap_answer(
        state,
        activity_id=transfer["activity_id"],
        answer="ancient",
    )
    assert state["status"] == "complete"
    assert recap._current_activity(state) is None


def test_readiness_support_copy_is_instructional_not_a_weakness_label_template():
    state = recap.new_recap_state(_report())
    guided = recap._current_activity(state)
    state, _ = recap.apply_recap_answer(
        state,
        activity_id=guided["activity_id"],
        answer="wrote",
    )

    bridge = recap._current_activity(state)
    assert bridge["kind"] == "bridge"
    assert "rebuild recognize" not in bridge["teaching_block"].lower()
    assert "naming word" in bridge["teaching_block"].lower()


def test_public_readiness_activity_never_exposes_authored_answers_or_source_item_ids():
    state = recap.new_recap_state(_report())
    payload = recap.public_recap_response(
        {
            "session_id": "recap-v1",
            "status": "active",
            "subject_id": "english",
            "class_no": 3,
            "state_json": deepcopy(state),
        }
    )

    activity = payload["current_activity"]
    assert "accepted_answers" not in activity
    assert "answer_key" not in activity
    assert "source_item_id" not in activity
    assert "placement_track_id" not in activity
