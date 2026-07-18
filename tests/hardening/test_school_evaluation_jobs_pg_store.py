from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from app.db import repo
from app.storage import pg_store


USER_ID = "learner-1"
SESSION_ID = "10000000-0000-4000-8000-000000000001"
ACTIVITY_ID = "chapter-check-1"
ANSWER_HASH = "answer-sha"
ANSWER_CLAIM_TOKEN = "answer-claim-token"
LEASE_OWNER = "worker-a"
LEASE_TOKEN = "lease-token"
LEASE_VERSION = 1


def test_pg_store_forwards_the_complete_fenced_evaluation_job_contract(monkeypatch):
    session = object()
    calls: list[tuple[str, object, tuple, dict]] = []

    @asynccontextmanager
    async def fake_session():
        yield session

    def capture(name: str):
        async def method(db_session, *args, **kwargs):
            calls.append((name, db_session, args, kwargs))
            return {"method": name}

        return method

    monkeypatch.setattr(pg_store, "_session", fake_session)
    method_names = (
        "get_school_evaluation_job",
        "get_school_evaluation_job_status",
        "enqueue_school_evaluation_job",
        "claim_school_evaluation_job",
        "heartbeat_school_evaluation_job",
        "complete_school_evaluation_job",
        "fail_school_evaluation_job",
        "retry_school_evaluation_job",
        "cancel_school_evaluation_job",
        "persist_school_curriculum_attempt",
        "persist_school_answer_attempt",
    )
    for name in method_names:
        monkeypatch.setattr(repo, name, capture(name))

    async def exercise() -> None:
        store = pg_store.PgStore()
        await store.get_school_evaluation_job(USER_ID, SESSION_ID, ACTIVITY_ID)
        await store.get_school_evaluation_job_status(USER_ID, SESSION_ID, ACTIVITY_ID)
        await store.enqueue_school_evaluation_job(
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            raw_answer="Private learner answer.",
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            answer_hash=ANSWER_HASH,
            answer_claim_token=ANSWER_CLAIM_TOKEN,
            flow_type="curriculum",
            evaluation_mode="open_answer",
            max_attempts=2,
        )
        await store.claim_school_evaluation_job(LEASE_OWNER, lease_seconds=45)
        identity = {
            "user_id": USER_ID,
            "session_id": SESSION_ID,
            "activity_id": ACTIVITY_ID,
            "answer_hash": ANSWER_HASH,
            "answer_claim_token": ANSWER_CLAIM_TOKEN,
            "lease_owner": LEASE_OWNER,
            "lease_token": LEASE_TOKEN,
            "lease_version": LEASE_VERSION,
        }
        await store.heartbeat_school_evaluation_job(**identity, lease_seconds=45)
        await store.complete_school_evaluation_job(
            **identity,
            response_json={"feedback": "Recorded."},
            result_data={"score": 0.9},
        )
        await store.fail_school_evaluation_job(
            **identity,
            last_error_code="provider_timeout",
            error_json={"retryable": True},
        )
        await store.retry_school_evaluation_job(
            **identity,
            last_error_code="provider_timeout",
            error_json={"retryable": True},
        )
        await store.cancel_school_evaluation_job(
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            answer_hash=ANSWER_HASH,
            answer_claim_token=ANSWER_CLAIM_TOKEN,
            error_json={"reason": "session_cancelled"},
        )
        attempt = {
            "learning_event": {"source_event_key": "evaluation-job-atomic"},
            "school_session": {
                "user_id": USER_ID,
                "session_id": SESSION_ID,
            },
            "expected_state_json": {"current_activity_id": ACTIVITY_ID},
            "request_activity_id": ACTIVITY_ID,
            "request_answer_hash": ANSWER_HASH,
            "request_claim_token": ANSWER_CLAIM_TOKEN,
            "response_json": {"feedback": "Recorded."},
            "evaluation_job_completion": {
                **identity,
                "response_json": {"feedback": "Recorded."},
                "result_data": {"score": 0.9},
            },
        }
        await store.persist_school_curriculum_attempt(**attempt)
        await store.persist_school_answer_attempt(**attempt)

    asyncio.run(exercise())

    assert [name for name, *_ in calls] == list(method_names)
    assert all(db_session is session for _, db_session, _, _ in calls)
    forwarded = {name: kwargs for name, _, _, kwargs in calls}
    assert forwarded["claim_school_evaluation_job"] == {
        "lease_owner": LEASE_OWNER,
        "lease_seconds": 45,
    }
    assert forwarded["retry_school_evaluation_job"] == {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "activity_id": ACTIVITY_ID,
        "answer_hash": ANSWER_HASH,
        "answer_claim_token": ANSWER_CLAIM_TOKEN,
        "lease_owner": LEASE_OWNER,
        "lease_token": LEASE_TOKEN,
        "lease_version": LEASE_VERSION,
        "last_error_code": "provider_timeout",
        "error_json": {"retryable": True},
    }
    assert forwarded["persist_school_curriculum_attempt"][
        "evaluation_job_completion"
    ] == forwarded["persist_school_answer_attempt"]["evaluation_job_completion"]
