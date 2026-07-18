import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_v3_schema import SchoolV3RubricCriterion, SchoolV3RubricEvaluation
from app.main import app
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION
from app.services.school_rebuild_placement_evaluator import (
    EVALUATOR_UNAVAILABLE_CODE,
    SchoolPlacementEvaluatorUnavailableError,
)


AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def _seed_profile(store, *, signals):
    _run(store.ensure_profile("test_user", name="QA Learner", email="qa@example.com"))
    client = TestClient(app)
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            "display_name": "QA Learner",
            "school_name": "QA School",
            "board_id": "cbse",
            "target_class_no": 3,
            "subject_ids": ["english"],
            "preferred_teaching_language": "hi_en",
            "english_comfort": "medium",
            "learner_goal": "Understand Class 3 English.",
            "parent_goal": "Build independent understanding.",
            "prior_difficulty_signals": signals,
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    draft = saved.json()["draft"]
    activated = client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
            "request_id": str(uuid4()),
        },
    )
    assert activated.status_code == 200
    return client


def _passing_open_evaluation(activity, answer):
    return SchoolV3RubricEvaluation(
        schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
        item_id=activity["activity_id"],
        skill_ids=list(activity["skill_ids"]),
        score=1.0,
        confidence=0.95,
        language_detected="en",
        criteria=[
            SchoolV3RubricCriterion(
                id=criterion["id"],
                met=True,
                quality=1.0,
                evidence_quote=answer,
            )
            for criterion in activity["rubric_criteria"]
        ],
        misconception_tags=[],
        blockers=[],
        needs_human_review=False,
        feedback_to_learner="Your sentence is clear and complete.",
    )


def test_placement_writing_uses_strict_evaluator_and_commits_criterion_evidence(
    store,
    monkeypatch,
):
    client = _seed_profile(store, signals=["writing"])
    started = client.post("/school/placement/start", headers=AUTH).json()
    item = started["next_item"]
    assert item["options"] is None

    async def evaluate(**kwargs):
        activity = kwargs["activity"]
        answer = kwargs["answer"]
        assert set(criterion["id"] for criterion in activity["rubric_criteria"])
        return _passing_open_evaluation(activity, answer)

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )
    answer = "The bird watches the garden from a branch."
    response = client.post(
        f"/school/placement/{started['session_id']}/answer",
        headers=AUTH,
        json={"item_id": item["item_id"], "answer": answer},
    )

    assert response.status_code == 200
    event = store.learning_events[-1]
    assert event["score"] == 1.0
    assert event["confidence"] == 0.95
    assert event["criteria_json"]
    assert all(row["evidence_quote"] == answer for row in event["criteria_json"])
    assert event["evidence_json"]["evaluation_mode"] == "strict_rubric"


def test_placement_evaluator_failure_is_retriable_and_does_not_advance_state(
    store,
    monkeypatch,
):
    client = _seed_profile(store, signals=["writing"])
    started = client.post("/school/placement/start", headers=AUTH).json()
    item = started["next_item"]
    before = _run(store.get_school_session("test_user", started["session_id"]))

    async def unavailable(*_args, **_kwargs):
        raise SchoolPlacementEvaluatorUnavailableError(EVALUATOR_UNAVAILABLE_CODE)

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        unavailable,
    )
    response = client.post(
        f"/school/placement/{started['session_id']}/answer",
        headers=AUTH,
        json={"item_id": item["item_id"], "answer": "A complete English sentence."},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == EVALUATOR_UNAVAILABLE_CODE
    after = _run(store.get_school_session("test_user", started["session_id"]))
    before_state = dict(before["state_json"])
    after_state = dict(after["state_json"])
    before_timing = before_state.pop("_placement_item_timing")
    after_timing = after_state.pop("_placement_item_timing")
    assert after_state == before_state
    assert after_timing["item_id"] == before_timing["item_id"]
    assert after_timing["retry_pending"] is True
    assert after_timing["accrued_learner_seconds"] >= 0
    assert store.learning_events == []
    failed_claim = _run(
        store.get_school_answer_request(
            "test_user",
            started["session_id"],
            item["item_id"],
        )
    )
    assert failed_claim["status"] == "failed"


def test_stale_answer_claim_cannot_rebase_placement_timing(store):
    client = _seed_profile(store, signals=[])
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    item_id = started["next_item"]["item_id"]
    before = _run(store.get_school_session("test_user", session_id))
    claim = _run(
        store.claim_school_answer_request(
            "test_user",
            session_id,
            item_id,
            "answer-hash",
        )
    )

    _run(
        store.fail_school_answer_request(
            "test_user",
            session_id,
            item_id,
            "answer-hash",
            f"stale-{claim['claim_token']}",
            placement_retry_timing={
                "item_id": item_id,
                "presented_at": "2099-01-01T00:00:00+00:00",
                "retry_pending": True,
                "accrued_learner_seconds": 999,
            },
        )
    )

    after = _run(store.get_school_session("test_user", session_id))
    assert after["state_json"] == before["state_json"]
    current_claim = _run(
        store.get_school_answer_request("test_user", session_id, item_id)
    )
    assert current_claim["status"] == "processing"
