import asyncio
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.main import app
from app.services import school_rebuild_recap as recap
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
    assert client.get("/school/placement/report", headers=AUTH).status_code == 200
    response = client.post("/school/recap/start", headers=AUTH)
    assert response.status_code == 200
    return response.json()


def _passing_answer(store, session_id: str, activity_id: str) -> str:
    row = _run(store.get_school_session("test_user", session_id))
    activity = recap.recap_activity_for_answer(
        row["state_json"],
        activity_id=activity_id,
    )
    accepted_answers = list(activity.get("accepted_answers") or [])
    if accepted_answers:
        return str(accepted_answers[0])
    return "The passage gives a clear clue, so this answer is supported."


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {"answer_key", "accepted_answers", "model_answer", "rubric", "threshold"}
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def test_school_recap_wrong_guided_answer_opens_bridge_support(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    guided = body["current_activity"]

    response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": guided["activity_id"], "answer": "wrong"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["last_feedback"]["correct"] is False
    assert body["last_feedback"]["next_move"] == {
        "stage": "bridge",
        "focus": guided["focus"],
        "strategy": "Find the exact who, what, where, or when clue before forming the answer.",
    }
    assert body["current_activity"]["kind"] == "bridge"
    assert body["current_activity"]["module_id"] == guided["module_id"]
    teaching_block = body["current_activity"]["teaching_block"]
    assert teaching_block.startswith("Sentence mein pehle kaun ya kya hai")
    assert teaching_block.endswith(
        "Use this clue before trying again: "
        "Find the exact who, what, where, or when clue before forming the answer."
    )
    assert body["modules"][0]["status"] == "in_progress"
    _assert_no_hidden_keys(body)


def test_school_recap_repeated_miss_opens_masterclass_and_correct_answer_returns_to_independent_check(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]

    guided = body["current_activity"]
    bridge_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": guided["activity_id"], "answer": "wrong"},
    )
    assert bridge_response.status_code == 200
    bridge = bridge_response.json()["current_activity"]

    masterclass_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": bridge["activity_id"], "answer": "wrong"},
    )

    assert masterclass_response.status_code == 200
    masterclass_body = masterclass_response.json()
    assert masterclass_body["last_feedback"]["correct"] is False
    assert masterclass_body["current_activity"]["kind"] == "masterclass"
    assert masterclass_body["current_activity"]["module_id"] == guided["module_id"]
    assert "Masterclass" in masterclass_body["current_activity"]["title"]
    _assert_no_hidden_keys(masterclass_body)

    masterclass = masterclass_body["current_activity"]
    recovered_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": masterclass["activity_id"],
            "answer": _passing_answer(
                store,
                session_id,
                masterclass["activity_id"],
            ),
        },
    )

    assert recovered_response.status_code == 200
    recovered = recovered_response.json()
    assert recovered["last_feedback"]["correct"] is True
    assert recovered["current_activity"]["kind"] == "independent_check"
    assert recovered["modules"][0]["status"] == "in_progress"

    events = [
        row
        for row in store.learning_events
        if row.get("task_type") == "school_rebuild_recap"
        and row.get("session_id") == session_id
    ]
    assert [event["attempt_type"] for event in events] == [
        "guided_check",
        "bridge",
        "masterclass",
    ]
    assert [float(event["score"]) for event in events] == [0.0, 0.0, 1.0]


def test_school_recap_masterclass_miss_opens_bounded_revision_and_records_each_attempt(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]

    guided = body["current_activity"]
    bridge = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": guided["activity_id"], "answer": "wrong"},
    ).json()["current_activity"]
    masterclass = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": bridge["activity_id"], "answer": "wrong"},
    ).json()["current_activity"]

    still_learning_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": masterclass["activity_id"], "answer": "wrong"},
    )

    assert still_learning_response.status_code == 200
    still_learning = still_learning_response.json()
    assert still_learning["last_feedback"]["correct"] is False
    assert still_learning["current_activity"]["kind"] == "revision_level_1"
    assert still_learning["current_activity"]["activity_id"] != masterclass["activity_id"]
    assert still_learning["current_activity"]["attempt_no"] == 1
    _assert_no_hidden_keys(still_learning)

    recovered_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": still_learning["current_activity"]["activity_id"],
            "answer": _passing_answer(
                store,
                session_id,
                still_learning["current_activity"]["activity_id"],
            ),
        },
    )

    assert recovered_response.status_code == 200
    recovered = recovered_response.json()
    assert recovered["current_activity"]["kind"] == "revision_level_2"

    events = [
        row
        for row in store.learning_events
        if row.get("task_type") == "school_rebuild_recap"
        and row.get("session_id") == session_id
    ]
    assert [event["attempt_type"] for event in events] == [
        "guided_check",
        "bridge",
        "masterclass",
        "revision_level_1",
    ]
    assert [float(event["score"]) for event in events] == [0.0, 0.0, 0.0, 1.0]


def _open_revision_levels(client: TestClient, session_id: str, guided: dict) -> dict:
    bridge = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": guided["activity_id"], "answer": "wrong"},
    ).json()["current_activity"]
    masterclass = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": bridge["activity_id"], "answer": "wrong"},
    ).json()["current_activity"]
    response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": masterclass["activity_id"], "answer": "wrong"},
    )
    assert response.status_code == 200
    return response.json()


def test_school_recap_revision_miss_stays_on_current_revision_level(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    guided = body["current_activity"]
    focus = guided["focus"]

    body = _open_revision_levels(client, session_id, guided)

    revision = body["current_activity"]
    assert revision["kind"] == "revision_level_1"

    response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": revision["activity_id"], "answer": "wrong"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["last_feedback"]["correct"] is False
    assert body["last_feedback"]["message"] == "Not yet. Stay on this revision level and rebuild the clue."
    assert body["current_activity"]["kind"] == "revision_level_1"
    assert body["current_activity"]["module_id"] == guided["module_id"]
    assert body["current_activity"]["title"] == f"Revision 1: {focus}"
    assert "Revision level 1" in body["current_activity"]["teaching_block"]
    assert body["modules"][0]["status"] == "in_progress"
    _assert_no_hidden_keys(body)

    events = [
        row
        for row in store.learning_events
        if row.get("task_type") == "school_rebuild_recap"
        and row.get("session_id") == session_id
    ]
    assert [event["attempt_type"] for event in events] == [
        "guided_check",
        "bridge",
        "masterclass",
        "revision_level_1",
    ]
    assert [float(event["score"]) for event in events] == [0.0, 0.0, 0.0, 0.0]


def test_school_recap_revision_levels_return_to_independent_check(store):
    _seed_school_profile(store)
    client = TestClient(app)
    body = _start_recap(client)
    session_id = body["session_id"]
    focus = body["current_activity"]["focus"]

    body = _open_revision_levels(client, session_id, body["current_activity"])
    revision_1 = body["current_activity"]

    revision_2_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": revision_1["activity_id"],
            "answer": _passing_answer(
                store,
                session_id,
                revision_1["activity_id"],
            ),
        },
    )
    assert revision_2_response.status_code == 200
    revision_2_body = revision_2_response.json()
    assert revision_2_body["last_feedback"]["correct"] is True
    assert revision_2_body["current_activity"]["kind"] == "revision_level_2"
    assert revision_2_body["current_activity"]["title"] == f"Revision 2: {focus}"

    revision_3_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": revision_2_body["current_activity"]["activity_id"],
            "answer": _passing_answer(
                store,
                session_id,
                revision_2_body["current_activity"]["activity_id"],
            ),
        },
    )
    assert revision_3_response.status_code == 200
    revision_3_body = revision_3_response.json()
    assert revision_3_body["current_activity"]["kind"] == "revision_level_3"
    assert revision_3_body["current_activity"]["title"] == f"Revision 3: {focus}"

    independent_response = client.post(
        f"/school/recap/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": revision_3_body["current_activity"]["activity_id"],
            "answer": _passing_answer(
                store,
                session_id,
                revision_3_body["current_activity"]["activity_id"],
            ),
        },
    )
    assert independent_response.status_code == 200
    independent = independent_response.json()
    assert independent["last_feedback"]["correct"] is True
    assert independent["current_activity"]["kind"] == "independent_check"
    assert independent["modules"][0]["status"] == "in_progress"
    _assert_no_hidden_keys(independent)

    events = [
        row
        for row in store.learning_events
        if row.get("task_type") == "school_rebuild_recap"
        and row.get("session_id") == session_id
    ]
    assert [event["attempt_type"] for event in events] == [
        "guided_check",
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    ]
    assert [float(event["score"]) for event in events] == [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
