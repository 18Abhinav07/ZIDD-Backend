import asyncio
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.main import app
from app.services import school_rebuild_recap
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    RUBRIC_SCHEMA_VERSION,
)

AUTH = {"Authorization": "Bearer test_token"}


@pytest.fixture(autouse=True)
def _trusted_open_answer_evaluator(monkeypatch):
    async def evaluate(**kwargs):
        activity = kwargs["activity"]
        answer = kwargs["answer"]
        passed = answer != "wrong"
        return {
            "schema_version": (
                OPEN_RUBRIC_SCHEMA_VERSION
                if activity.get("grading_mode") == "strict_open_rubric"
                else RUBRIC_SCHEMA_VERSION
            ),
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
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )
    monkeypatch.setattr(
        school_rebuild_recap,
        "_answer_matches",
        lambda _activity, answer: answer != "wrong",
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
    response = _activate_school_profile(TestClient(app), _profile_payload())
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


def _correct_answer(activity: dict[str, Any]) -> str:
    focus = activity["focus"].lower()
    kind = activity["kind"]
    answers = {
        ("recognize naming words", "guided_check"): "teacher",
        ("recognize naming words", "independent_check"): "flower",
        ("understand a simple sentence", "guided_check"): "mat",
        ("understand a simple sentence", "independent_check"): "mangoes",
        ("use context to understand a word", "guided_check"): "small",
        ("use context to understand a word", "independent_check"): "smart",
        ("write a complete sentence", "guided_check"): "sitting",
        ("write a complete sentence", "independent_check"): "ran",
        ("answer with a reason", "guided_check"): "dark",
        ("answer with a reason", "independent_check"): "thirsty",
        ("find the main idea", "guided_check"): "Aman caring for plants",
        ("find the main idea", "independent_check"): "children reading in a library",
        ("use because to give a reason", "guided_check"): "because",
        ("use because to give a reason", "independent_check"): "because",
        ("use past tense", "guided_check"): "went",
        ("use past tense", "independent_check"): "played",
    }
    try:
        return answers[(focus, kind)]
    except KeyError:
        return "valid test answer"


def _complete_recap_success_path(
    client: TestClient,
    *,
    complete_placement: bool = True,
) -> dict:
    if complete_placement:
        _complete_weak_placement(client)
    assert client.get("/school/placement/report", headers=AUTH).status_code == 200
    body = client.post("/school/recap/start", headers=AUTH).json()
    session_id = body["session_id"]

    guard = 0
    while body["current_activity"] is not None:
        guard += 1
        assert guard <= 40
        activity = body["current_activity"]
        response = client.post(
            f"/school/recap/{session_id}/answer",
            headers=AUTH,
            json={
                "activity_id": activity["activity_id"],
                "answer": _correct_answer(activity),
            },
        )
        assert response.status_code == 200
        body = response.json()
    return body


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {"answer_key", "accepted_answers", "model_answer", "rubric", "threshold"}
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def test_school_recap_completion_marks_path_complete_without_leaking_answers(store):
    _seed_school_profile(store)
    client = TestClient(app)

    body = _complete_recap_success_path(client)

    assert body["status"] == "complete"
    assert body["current_activity"] is None
    assert body["progress"]["completed_modules"] == body["progress"]["total_modules"]
    assert all(module["status"] == "complete" for module in body["modules"])
    _assert_no_hidden_keys(body)


def test_school_state_after_completed_recap_unlocks_target_curriculum(store):
    _seed_school_profile(store)
    client = TestClient(app)
    recap = _complete_recap_success_path(client)

    state = client.get("/school/state", headers=AUTH).json()

    assert state["profile_status"] == "complete"
    assert state["placement_status"] == "below_target"
    assert state["unlock_state"] == "target_unlocked"
    assert state["evaluated_class_no"] == 2
    assert state["active_learning_class_no"] == 3
    assert state["active_flow"] == "curriculum"
    assert state["active_session_id"] is None
    assert state["next_action"] == "start_curriculum"
    assert state["next_action_url"] == "/school/classes/3"
    assert "target class" in state["learner_message"].lower()
    assert recap["status"] == "complete"


def test_get_school_recap_returns_completed_path_after_unlock(store):
    _seed_school_profile(store)
    client = TestClient(app)
    completed = _complete_recap_success_path(client)

    response = client.get("/school/recap", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == completed["session_id"]
    assert body["status"] == "complete"
    assert body["current_activity"] is None
    assert body["progress"]["completed_modules"] == body["progress"]["total_modules"]
    _assert_no_hidden_keys(body)


def test_start_school_recap_after_completion_is_idempotent(store):
    _seed_school_profile(store)
    client = TestClient(app)
    completed = _complete_recap_success_path(client)

    response = client.post("/school/recap/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == completed["session_id"]
    assert body["status"] == "complete"
    assert body["current_activity"] is None
    _assert_no_hidden_keys(body)


def test_school_curriculum_landing_requires_completed_recap_and_hides_keys(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_weak_placement(client)
    assert client.get("/school/placement/report", headers=AUTH).status_code == 200

    locked = client.get("/school/curriculum", headers=AUTH)
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "curriculum_locked"

    _complete_recap_success_path(client, complete_placement=False)

    response = client.get("/school/curriculum", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["flow_type"] == "curriculum"
    assert body["status"] == "unlocked"
    assert body["subject_id"] == "english"
    assert body["target_class_no"] == 3
    assert body["active_learning_class_no"] == 3
    assert body["source_recap_session_id"]
    assert body["chapters_preview"]
    assert body["chapters_preview"][0]["status"] == "ready"
    _assert_no_hidden_keys(body)
