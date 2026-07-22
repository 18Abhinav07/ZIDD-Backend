import asyncio
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_v3_schema import SchoolV3RubricCriterion, SchoolV3RubricEvaluation
from app.main import app
from app.services import school_rebuild_placement as placement
from app.services.school import evaluation_jobs
from app.services.school.evaluator_contract import SchoolOpenAnswerRetryableError
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION


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


def _advance_to_strict_writing_diagnostic(store, client, started):
    current = started
    session_id = started["session_id"]
    while current["stage"] == "snapshot":
        row = _run(store.get_school_session("test_user", session_id))
        envelope = placement.envelope_from_json(row["state_json"])
        item = placement.find_item(envelope, current["next_item"]["item_id"])
        answer = (
            "not a complete sentence"
            if item.primary_skill_id == "writing.complete_sentence"
            else item.accepted_answers[0]
        )
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item.item_id, "answer": answer},
        )
        assert response.status_code == 200
        current = response.json()

    assert current["stage"] == "targeted_diagnostic"
    row = _run(store.get_school_session("test_user", session_id))
    envelope = placement.envelope_from_json(row["state_json"])
    item = placement.find_item(envelope, current["next_item"]["item_id"])
    assert item.primary_skill_id == "writing.complete_sentence"
    assert item.evaluation_mode == "strict_rubric"
    return current, item


def test_placement_writing_uses_strict_evaluator_and_commits_criterion_evidence(
    store,
    monkeypatch,
):
    client = _seed_profile(store, signals=["writing"])
    started = client.post("/school/placement/start", headers=AUTH).json()
    current, strict_item = _advance_to_strict_writing_diagnostic(
        store,
        client,
        started,
    )
    item = current["next_item"]
    assert item["options"] is None

    async def evaluate(activity, answer, **_kwargs):
        assert set(criterion["id"] for criterion in activity["rubric_criteria"])
        return _passing_open_evaluation(activity, answer)

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluate,
    )
    answer = "The bird watches the garden from a branch."
    response = client.post(
        f"/school/placement/{current['session_id']}/answer",
        headers=AUTH,
        json={"item_id": strict_item.item_id, "answer": answer},
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "awaiting_evaluation",
        "session_id": current["session_id"],
        "activity_id": strict_item.item_id,
        "state_url": "/school/state",
    }
    queued_job = _run(
        store.get_school_evaluation_job(
            "test_user",
            current["session_id"],
            strict_item.item_id,
        )
    )
    assert queued_job["status"] == "queued"
    assert _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    ) is True
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
    # A rate-limit is a cloud-provider condition. Configure the enqueue policy
    # as Gemini so the persisted job has the production retry allowance.
    monkeypatch.setattr(
        school_rebuild_routes,
        "get_settings",
        lambda: SimpleNamespace(ai_backend="gemini"),
    )
    client = _seed_profile(store, signals=["writing"])
    started = client.post("/school/placement/start", headers=AUTH).json()
    current, strict_item = _advance_to_strict_writing_diagnostic(
        store,
        client,
        started,
    )
    before = _run(store.get_school_session("test_user", current["session_id"]))

    async def unavailable(*_args, **_kwargs):
        raise SchoolOpenAnswerRetryableError("provider_rate_limited")

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        unavailable,
    )
    response = client.post(
        f"/school/placement/{current['session_id']}/answer",
        headers=AUTH,
        json={
            "item_id": strict_item.item_id,
            "answer": "A complete English sentence.",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "awaiting_evaluation",
        "session_id": current["session_id"],
        "activity_id": strict_item.item_id,
        "state_url": "/school/state",
    }
    assert _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    ) is True
    after = _run(store.get_school_session("test_user", current["session_id"]))
    before_state = dict(before["state_json"])
    after_state = dict(after["state_json"])
    before_timing = before_state.pop("_placement_item_timing")
    after_timing = after_state.pop("_placement_item_timing")
    assert after_state == before_state
    assert after_timing == before_timing
    assert len(store.learning_events) == 8
    assert {event["attempt_type"] for event in store.learning_events} == {"snapshot"}
    failed_claim = _run(
        store.get_school_answer_request(
            "test_user",
            current["session_id"],
            strict_item.item_id,
        )
    )
    assert failed_claim["status"] == "failed"
    failed_job = _run(
        store.get_school_evaluation_job(
            "test_user",
            current["session_id"],
            strict_item.item_id,
        )
    )
    assert failed_job["status"] == "failed"
    assert failed_job["last_error_code"] == "provider_rate_limited"

    # Cloud policy deliberately gives a child-facing answer one bounded worker
    # pass. The durable failed claim makes the same learner retry a fresh,
    # independently queued job instead of leaving an orphaned processing latch.
    retried = client.post(
        f"/school/placement/{current['session_id']}/answer",
        headers=AUTH,
        json={
            "item_id": strict_item.item_id,
            "answer": "A complete English sentence.",
        },
    )
    assert retried.status_code == 202
    queued_retry = _run(
        store.get_school_evaluation_job(
            "test_user",
            current["session_id"],
            strict_item.item_id,
        )
    )
    retry_claim = _run(
        store.get_school_answer_request(
            "test_user",
            current["session_id"],
            strict_item.item_id,
        )
    )
    assert queued_retry["status"] == "queued"
    assert queued_retry["last_error_code"] is None
    assert retry_claim["status"] == "processing"


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
