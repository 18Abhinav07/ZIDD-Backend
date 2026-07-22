import asyncio
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_rebuild_placement_bank import placement_tracks_for
from app.main import app
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    RUBRIC_SCHEMA_VERSION,
)
from app.services.school.language_confidence import LanguageConfidenceState
from app.services.school import evaluation_jobs
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_recap as recap

AUTH = {"Authorization": "Bearer test_token"}


def _schema_version_for(activity: dict[str, Any]) -> str:
    return (
        OPEN_RUBRIC_SCHEMA_VERSION
        if activity.get("grading_mode") == "strict_open_rubric"
        else RUBRIC_SCHEMA_VERSION
    )


@pytest.fixture(autouse=True)
def _trusted_open_answer_evaluator(monkeypatch):
    async def evaluate(activity, answer, **_kwargs):
        passed = answer != "wrong"
        return {
            "schema_version": _schema_version_for(activity),
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0 if passed else 0.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": passed,
                    "quality": 1.0 if passed else 0.0,
                    "evidence_quote": answer if passed else "(empty answer)",
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [] if passed else ["placement_gap"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Evidence recorded.",
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluate,
    )


def _run(coro):
    return asyncio.run(coro)


def _profile_payload() -> dict:
    return {
        "display_name": "Open Assets Learner",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": 3,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": "I want to understand Class 3 English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": ["reading", "vocabulary"],
    }


def _activate_school_profile(client: TestClient, payload: dict):
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            **payload,
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    assert saved.status_code == 200
    draft = saved.json()["draft"]
    return client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
            "request_id": str(uuid4()),
        },
    )


def _seed_school_profile(store) -> None:
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    response = _activate_school_profile(client, _profile_payload())
    assert response.status_code == 200


def _complete_weak_placement(client: TestClient) -> None:
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    for _ in range(20):
        item = current["next_item"]
        if item is None:
            break
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": "wrong"},
        )
        assert response.status_code == 200
        current = response.json()
    assert current["status"] == "below_target"


def _start_recap(client: TestClient) -> dict:
    _complete_weak_placement(client)
    report = client.get("/school/placement/report", headers=AUTH)
    assert report.status_code == 200
    response = client.post("/school/recap/start", headers=AUTH)
    assert response.status_code == 200
    return response.json()


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {"answer_key", "accepted_answers", "model_answer", "rubric", "threshold"}
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def _passing_recap_answer(store, session_id: str, activity_id: str) -> str:
    row = _run(store.get_school_session("test_user", session_id))
    activity = recap.recap_activity_for_answer(
        row["state_json"],
        activity_id=activity_id,
    )
    accepted_answers = list(activity.get("accepted_answers") or [])
    if accepted_answers:
        return str(accepted_answers[0])
    return "The visible clue supports this answer because it directly explains the event."


def _summary_recap_report() -> dict[str, Any]:
    track = next(
        track
        for track in placement_tracks_for("english", 5)
        if track.primary_skill_id == "writing.summary_own_words"
    )
    return {
        "profile_version_id": "profile-version",
        "report_id": "report-id",
        "placement_session_id": "placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [{
            "module_id": "summary-foundation",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 4,
            "target_class_no": 5,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    }


def test_recap_detail_check_accepts_a_complete_sentence_around_the_answer():
    activity = recap.RECAP_TRACK_CHECK_BANK[
        "english.c5.sentence_detail"
    ]["guided_check"]

    assert recap._answer_matches(
        activity,
        "The art club meets in Room 6 on Wednesday afternoon.",
    )
    assert not recap._answer_matches(
        activity,
        "The art club does not meet in Room 6 on Wednesday afternoon.",
    )


def test_recap_carries_hinglish_support_through_guided_and_certifying_steps():
    state = recap.new_recap_state(
        _summary_recap_report(),
        preferred_teaching_language="hi_en",
        en_production_confidence=0.2,
    )
    guided = recap.public_recap_response({
        "session_id": "recap-session",
        "status": "active",
        "subject_id": "english",
        "class_no": 5,
        "state_json": state,
    })["current_activity"]

    assert state["preferred_teaching_language"] == "hi_en"
    assert "Sabse important event ya idea" in guided["teaching_block"]

    state["en_production_confidence"] = 0.95
    state["modules"][0]["current_step"] = "independent_check"
    independent = recap.public_recap_response({
        "session_id": "recap-session",
        "status": "active",
        "subject_id": "english",
        "class_no": 5,
        "state_json": state,
    })["current_activity"]

    assert "answer English mein likho" in independent["teaching_block"]


def test_school_recap_open_response_uses_strict_rubric_evidence():
    track = next(
        track
        for track in placement_tracks_for("english", 5)
        if track.primary_skill_id == "writing.summary_own_words"
    )
    state = recap.new_recap_state({
        "profile_version_id": "profile-version",
        "report_id": "report-id",
        "placement_session_id": "placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [{
            "module_id": "summary-foundation",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 4,
            "target_class_no": 5,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    })
    activity = recap.recap_activity_for_answer(
        state,
        activity_id=recap.public_recap_response({
            "session_id": "recap-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        })["current_activity"]["activity_id"],
    )
    evaluator_activity = recap.evaluator_activity_for_answer(activity)
    answer = (
        "After checking its power costs, the school added solar panels and "
        "spent the savings on library books."
    )
    raw_evaluation = {
        "schema_version": _schema_version_for(evaluator_activity),
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 1.0,
        "confidence": 1.0,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": True,
                "quality": 1.0,
                "evidence_quote": answer,
            }
            for criterion in evaluator_activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Evidence recorded.",
    }

    updated, evaluation = recap.apply_recap_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=raw_evaluation,
    )

    assert evaluation["correct"] is True
    assert evaluation["score"] == 1.0
    assert evaluation["evaluation_mode"] == "llm_rubric"
    assert evaluation["criteria"]
    assert recap.public_recap_response({
        "session_id": "recap-session",
        "status": "active",
        "subject_id": "english",
        "class_no": 5,
        "state_json": updated,
    })["current_activity"]["kind"] == "independent_check"


def test_school_recap_open_items_activate_the_strict_open_contract():
    track = next(
        track
        for track in placement_tracks_for("english", 5)
        if track.track_id == "english.c5.inference"
    )
    state = recap.new_recap_state({
        "profile_version_id": "profile-version",
        "report_id": "report-id",
        "placement_session_id": "placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [{
            "module_id": "inference-foundation",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 4,
            "target_class_no": 5,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    })
    activity = recap.recap_activity_for_answer(
        state,
        activity_id=recap.public_recap_response({
            "session_id": "recap-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        })["current_activity"]["activity_id"],
    )

    evaluator_activity = recap.evaluator_activity_for_answer(activity)

    assert evaluator_activity is not None
    assert evaluator_activity["grading_mode"] == "strict_open_rubric"
    assert OPEN_RUBRIC_SCHEMA_VERSION == "school.open.v1"


def test_recap_open_feedback_names_missing_authored_move_without_answer_key():
    track = next(
        track
        for track in placement_tracks_for("english", 5)
        if track.track_id == "english.c5.inference"
    )
    state = recap.new_recap_state({
        "profile_version_id": "profile-version",
        "report_id": "report-id",
        "placement_session_id": "placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [{
            "module_id": "inference-foundation",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 4,
            "target_class_no": 5,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    })
    activity = recap.recap_activity_for_answer(
        state,
        activity_id=recap.public_recap_response({
            "session_id": "recap-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        })["current_activity"]["activity_id"],
    )
    evaluator_activity = recap.evaluator_activity_for_answer(activity)
    assert evaluator_activity is not None

    answer = "It rained."
    missing = {"relevant_text_clue", "clue_supports_inference"}
    raw_evaluation = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.55,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": criterion["id"] not in missing,
                "quality": 0.0 if criterion["id"] in missing else 1.0,
                "evidence_quote": answer,
            }
            for criterion in evaluator_activity["rubric_criteria"]
        ],
        "misconception_tags": ["missing_text_clue"],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Use a clue from the text.",
    }

    updated, evaluation = recap.apply_recap_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=raw_evaluation,
    )

    message = updated["last_feedback"]["message"]
    assert evaluation["correct"] is False
    assert "Name a text clue connected to the inference." in message
    assert "raincoat" not in message
    assert recap._current_activity(updated)["kind"] == "bridge"


def test_school_recap_does_not_remediate_a_backend_proven_complete_inference():
    track = next(
        track
        for track in placement_tracks_for("english", 5)
        if track.track_id == "english.c5.inference"
    )
    state = recap.new_recap_state({
        "profile_version_id": "profile-version",
        "report_id": "report-id",
        "placement_session_id": "placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [{
            "module_id": "inference-foundation",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 4,
            "target_class_no": 5,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    })
    activity = recap.recap_activity_for_answer(
        state,
        activity_id=recap.public_recap_response({
            "session_id": "recap-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        })["current_activity"]["activity_id"],
    )
    answer = "It probably rained because his hair and raincoat were wet."
    evidence_by_id = {
        "plausible_inference": "It probably rained",
        "relevant_text_clue": "his hair and raincoat were wet",
        "clue_supports_inference": answer,
        "complete_response": answer,
        "english_response": answer,
    }
    raw_evaluation = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.8,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion_id,
                "met": criterion_id != "complete_response",
                "quality": 0.0 if criterion_id == "complete_response" else 1.0,
                "evidence_quote": evidence_by_id[criterion_id],
            }
            for criterion_id in (
                "plausible_inference",
                "relevant_text_clue",
                "clue_supports_inference",
                "complete_response",
                "english_response",
            )
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The inference and clue are connected.",
    }

    updated, evaluation = recap.apply_recap_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=raw_evaluation,
    )

    assert evaluation["correct"] is True
    assert evaluation["score"] == 1.0
    assert evaluation["missing_criteria"] == []
    assert recap.public_recap_response({
        "session_id": "recap-session",
        "status": "active",
        "subject_id": "english",
        "class_no": 5,
        "state_json": updated,
    })["current_activity"]["kind"] == "independent_check"


def _summary_evaluation(*, activity: dict, answer: str, own_words_met: bool) -> dict:
    return {
        "schema_version": _schema_version_for(activity),
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.84 if not own_words_met else 1.0,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": own_words_met if criterion["id"] == "own_words" else True,
                "quality": (
                    (1.0 if own_words_met else 0.2)
                    if criterion["id"] == "own_words"
                    else 1.0
                ),
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Evidence recorded.",
    }


def _summary_activity() -> dict:
    return {
        "activity_id": "recap-summary:transfer_check:1",
        "skill_ids": ["writing.summary_own_words"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "passage": (
            "Two water samples looked equally clear, but a test showed that "
            "one contained harmful bacteria and needed treatment."
        ),
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": criterion_id,
                "required": True,
                "min_quality": 0.7,
            }
            for criterion_id in (
                "main_idea_or_event",
                "essential_details",
                "own_words",
                "concise_complete_response",
                "english_response",
            )
        ],
    }


def test_backend_corrects_false_model_copying_claim_for_a_clear_paraphrase():
    activity = _summary_activity()
    answer = (
        "Testing revealed that one apparently clear water sample contained "
        "dangerous bacteria and had to be treated."
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _summary_evaluation(
            activity=activity,
            answer=answer,
            own_words_met=False,
        ),
        answer=answer,
    )

    own_words = next(
        criterion
        for criterion in decision["criteria"]
        if criterion["id"] == "own_words"
    )
    assert decision["correct"] is True
    assert own_words["met"] is True
    assert own_words["quality"] >= 0.9


def test_backend_rejects_copied_summary_even_when_model_calls_it_own_words():
    activity = _summary_activity()
    answer = activity["passage"]

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _summary_evaluation(
            activity=activity,
            answer=answer,
            own_words_met=True,
        ),
        answer=answer,
    )

    own_words = next(
        criterion
        for criterion in decision["criteria"]
        if criterion["id"] == "own_words"
    )
    assert decision["correct"] is False
    assert own_words["met"] is False
    assert "own_words" in decision["missing_criteria"]


def _inference_activity() -> dict:
    return {
        "activity_id": "recap-inference:independent_check:1",
        "skill_ids": ["reading.inference_reason"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "passage": (
            "The scoreboard showed one run needed. Every player leaned forward "
            "and stopped talking as the bowler began."
        ),
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": criterion_id,
                "required": True,
                "min_quality": 0.7,
            }
            for criterion_id in (
                "plausible_inference",
                "relevant_text_clue",
                "clue_supports_inference",
                "complete_response",
                "english_response",
            )
        ],
    }


def _inference_evaluation(*, activity: dict, answer: str) -> dict:
    return {
        "schema_version": _schema_version_for(activity),
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.9,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": criterion["id"] != "clue_supports_inference",
                "quality": 0.5 if criterion["id"] == "clue_supports_inference" else 1.0,
                "evidence_quote": answer,
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Evidence recorded.",
    }


def test_backend_accepts_explicit_link_between_valid_inference_and_clue():
    activity = _inference_activity()
    answer = (
        "The team became quiet because only one run was needed and everyone "
        "focused as the bowler began."
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _inference_evaluation(activity=activity, answer=answer),
        answer=answer,
    )

    linkage = next(
        criterion
        for criterion in decision["criteria"]
        if criterion["id"] == "clue_supports_inference"
    )
    assert decision["correct"] is True
    assert linkage["met"] is True
    assert linkage["quality"] >= 0.9


def test_backend_does_not_invent_inference_link_without_explicit_connection():
    activity = _inference_activity()
    answer = "The team became quiet. One run was needed."

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _inference_evaluation(activity=activity, answer=answer),
        answer=answer,
    )

    assert decision["correct"] is False
    assert "clue_supports_inference" in decision["missing_criteria"]


def test_school_recap_route_evaluates_open_response_with_qwen_contract(
    store,
    monkeypatch,
):
    _seed_school_profile(store)
    client = TestClient(app)
    started = _start_recap(client)
    session_id = started["session_id"]
    row = _run(store.get_school_session("test_user", session_id))
    track = next(
        track
        for track in placement_tracks_for("english", 3)
        if track.primary_skill_id == "reading.inference_reason"
    )
    state = recap.new_recap_state({
        "profile_version_id": row["profile_version_id"],
        "report_id": row["source_placement_report_id"],
        "placement_session_id": row["linked_session_id"],
        "subject_id": "english",
        "target_class_no": 3,
        "active_learning_class_no": 2,
        "recommended_recap_modules": [{
            "module_id": "summary-foundation",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 2,
            "target_class_no": 3,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    })
    state["modules"][0]["current_step"] = "independent_check"
    _run(store.upsert_school_session(**{
        **row,
        "state_json": {
            **state,
            "coach_avatar_id": row["state_json"].get("coach_avatar_id"),
            "coach_palette_id": row["state_json"].get("coach_palette_id"),
        },
    }))
    current = client.get(f"/school/recap/{session_id}", headers=AUTH).json()
    activity_id = current["current_activity"]["activity_id"]
    answer = "The people fixed the problem together and made the place safe again."
    evaluator_calls = []

    async def evaluate(activity, _answer, **_kwargs):
        evaluator_calls.append(activity["activity_id"])
        return {
            "schema_version": _schema_version_for(activity),
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Evidence recorded.",
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluate,
    )

    response = TestClient(app, raise_server_exceptions=False).post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": answer},
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "awaiting_evaluation",
        "session_id": session_id,
        "activity_id": activity_id,
        "state_url": "/school/state",
    }
    assert _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    ) is True
    completed = client.get(f"/school/recap/{session_id}", headers=AUTH)

    assert evaluator_calls == [activity_id]
    assert completed.status_code == 200
    assert completed.json()["last_feedback"]["correct"] is True
    assert completed.json()["current_activity"]["kind"] == "transfer_check"


def test_school_recap_serves_current_activity_without_leaking_answers(store):
    _seed_school_profile(store)
    client = TestClient(app)

    body = _start_recap(client)

    assert body["progress"]["completed_modules"] == 0
    assert body["progress"]["total_modules"] == len(body["modules"])
    activity = body["current_activity"]
    assert activity["kind"] == "guided_check"
    assert activity["module_id"] == body["modules"][0]["module_id"]
    assert activity["activity_id"]
    assert activity["teaching_block"]
    assert activity["prompt"]
    assert activity["can_answer"] is True
    assert body["last_feedback"] is None
    _assert_no_hidden_keys(body)


def test_school_recap_start_carries_saved_teaching_language_and_confidence(
    store,
    monkeypatch,
):
    _seed_school_profile(store)

    async def load_confidence(_store, user_id):
        return LanguageConfidenceState(
            user_id=user_id,
            en_production_confidence=0.42,
            total_signals=7,
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "load_language_confidence",
        load_confidence,
    )

    client = TestClient(app)
    body = _start_recap(client)
    row = _run(store.get_school_session("test_user", body["session_id"]))

    assert row["state_json"]["preferred_teaching_language"] == "hi_en"
    assert row["state_json"]["en_production_confidence"] == pytest.approx(0.42)
    assert body["current_activity"]["teaching_block"] != (
        recap.recap_activity_for_answer(
            {
                **row["state_json"],
                "preferred_teaching_language": "en",
            },
            activity_id=body["current_activity"]["activity_id"],
        )["teaching_block"]
    )


def test_school_recap_correct_answers_advance_module_and_record_evidence(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    guided = body["current_activity"]

    guided_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": guided["activity_id"],
            "answer": _passing_recap_answer(
                store,
                session_id,
                guided["activity_id"],
            ),
        },
    )

    assert guided_response.status_code == 200
    after_guided = guided_response.json()
    assert after_guided["last_feedback"]["correct"] is True
    assert after_guided["current_activity"]["kind"] == "independent_check"
    assert after_guided["modules"][0]["status"] == "in_progress"
    _assert_no_hidden_keys(after_guided)

    independent = after_guided["current_activity"]
    independent_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": independent["activity_id"],
            "answer": _passing_recap_answer(
                store,
                session_id,
                independent["activity_id"],
            ),
        },
    )

    assert independent_response.status_code == 200
    after_independent = independent_response.json()
    assert after_independent["last_feedback"]["correct"] is True
    assert after_independent["current_activity"]["kind"] == "transfer_check"
    current_row = _run(store.get_school_session("test_user", session_id))
    transfer = recap.recap_activity_for_answer(
        current_row["state_json"],
        activity_id=after_independent["current_activity"]["activity_id"],
    )
    transfer_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": transfer["activity_id"],
            "answer": (
                transfer["accepted_answers"][0]
                if transfer.get("accepted_answers")
                else "The teacher is the person named in the sentence."
            ),
        },
    )

    assert transfer_response.status_code == 200
    completed = transfer_response.json()
    assert completed["last_feedback"]["correct"] is True
    assert completed["modules"][0]["status"] == "complete"
    assert completed["current_module_index"] == 1
    assert completed["progress"]["completed_modules"] == 1
    assert completed["current_activity"]["module_id"] == completed["modules"][1]["module_id"]
    assert completed["current_activity"]["kind"] == "guided_check"

    events = [
        row
        for row in store.learning_events
        if row.get("task_type") == "school_rebuild_recap"
        and row.get("session_id") == session_id
    ]
    assert len(events) == 3
    assert {event["attempt_type"] for event in events} == {
        "guided_check",
        "independent_check",
        "transfer_check",
    }
    assert all(float(event["score"]) == 1.0 for event in events)


def test_school_recap_answer_replay_is_payload_bound(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    activity_id = body["current_activity"]["activity_id"]

    first = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": "teacher"},
    )
    replay = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": "teacher"},
    )
    changed = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": "changed"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "recap_answer_conflict"
    assert len(
        [
            event
            for event in store.learning_events
            if event.get("session_id") == session_id
            and event.get("node_id") == activity_id
        ]
    ) == 1


def test_school_recap_post_claim_failure_marks_request_failed(store, monkeypatch):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    activity_id = body["current_activity"]["activity_id"]

    def fail_after_claim(*_args, **_kwargs):
        raise RuntimeError("recap response construction failed")

    monkeypatch.setattr(recap, "public_recap_response", fail_after_claim)
    response = TestClient(app, raise_server_exceptions=False).post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": "teacher"},
    )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    assert response.status_code == 500
    assert request_row["status"] == "failed"
    assert request_row["response_json"] is None


def test_school_recap_stale_cas_uses_flow_neutral_public_code(store, monkeypatch):
    _seed_school_profile(store)
    body = _start_recap(TestClient(app))

    async def stale_cas(**_kwargs):
        raise ValueError("stale_school_answer_session")

    monkeypatch.setattr(store, "persist_school_answer_attempt", stale_cas)
    response = TestClient(app).post(
        f"/school/recap/{body['session_id']}/answer",
        headers=AUTH,
        json={
            "activity_id": body["current_activity"]["activity_id"],
            "answer": "teacher",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_school_answer_session"


def test_school_recap_replays_completed_activity_answer(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    stale_activity_id = body["current_activity"]["activity_id"]

    ok = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": stale_activity_id, "answer": "teacher"},
    )
    assert ok.status_code == 200

    stale = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": stale_activity_id, "answer": "teacher"},
    )

    assert stale.status_code == 200
    assert stale.json() == ok.json()
