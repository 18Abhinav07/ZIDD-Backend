from __future__ import annotations

import asyncio
import copy

import pytest

from tests.conftest import InMemoryStore


USER_ID = "learner-atomic"
SESSION_ID = "10000000-0000-4000-8000-000000000101"
ACTIVITY_ID = "chapter-check-atomic"
PROFILE_VERSION_ID = "profile-atomic"
ANSWER_HASH = "answer-sha-atomic"


def _run(coro):
    return asyncio.run(coro)


def _seed_running_job() -> tuple[InMemoryStore, dict, dict, dict]:
    store = InMemoryStore()
    initial_state = {"current_activity_id": ACTIVITY_ID, "step": 1}
    store.school_profile_versions[(USER_ID, PROFILE_VERSION_ID)] = {"status": "active"}
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "session_id": SESSION_ID,
        "user_id": USER_ID,
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "current_stage": "activity",
        "profile_version_id": PROFILE_VERSION_ID,
        "state_json": copy.deepcopy(initial_state),
    }
    claim = _run(
        store.claim_school_answer_request(USER_ID, SESSION_ID, ACTIVITY_ID, ANSWER_HASH)
    )
    queued = _run(
        store.enqueue_school_evaluation_job(
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            raw_answer="The learner's private answer.",
            expected_state_json=initial_state,
            answer_hash=ANSWER_HASH,
            answer_claim_token=claim["claim_token"],
            flow_type="curriculum",
            evaluation_mode="open_answer",
            max_attempts=2,
        )
    )
    assert queued["outcome"] == "queued"
    job = _run(store.claim_school_evaluation_job("atomic-worker", lease_seconds=45))
    assert job is not None
    return store, initial_state, claim, job


def _completion(job: dict, response: dict) -> dict:
    return {
        "user_id": job["user_id"],
        "session_id": job["session_id"],
        "activity_id": job["activity_id"],
        "answer_hash": job["answer_hash"],
        "answer_claim_token": job["answer_claim_token"],
        "lease_owner": job["lease_owner"],
        "lease_token": job["lease_token"],
        "lease_version": job["lease_version"],
        "response_json": response,
        "result_data": {"score": 0.9, "passed": True},
    }


def _school_session(initial_state: dict) -> dict:
    return {
        "session_id": SESSION_ID,
        "user_id": USER_ID,
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "current_stage": "activity",
        "profile_version_id": PROFILE_VERSION_ID,
        "state_json": {**initial_state, "step": 2},
    }


def _learning_event() -> dict:
    return {
        "source_event_key": "school-evaluation-job:atomic-completion",
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "domain": "school",
        "task_type": "school_rebuild_curriculum",
        "module_id": "atomic-completion",
    }


def test_curriculum_attempt_completes_the_fenced_job_in_the_same_commit():
    store, initial_state, claim, job = _seed_running_job()
    response = {"feedback": "Recorded."}

    _run(
        store.persist_school_curriculum_attempt(
            learning_event=_learning_event(),
            school_session=_school_session(initial_state),
            expected_state_json=initial_state,
            request_activity_id=ACTIVITY_ID,
            request_answer_hash=ANSWER_HASH,
            request_claim_token=claim["claim_token"],
            response_json=response,
            evaluation_job_completion=_completion(job, response),
        )
    )

    persisted_job = _run(store.get_school_evaluation_job(USER_ID, SESSION_ID, ACTIVITY_ID))
    persisted_request = _run(
        store.get_school_answer_request(USER_ID, SESSION_ID, ACTIVITY_ID)
    )
    persisted_session = _run(store.get_school_session(USER_ID, SESSION_ID))

    assert persisted_job["status"] == "completed"
    assert persisted_job["lease_owner"] is None
    assert persisted_job["lease_token"] is None
    assert persisted_job["response_json"] == response
    assert persisted_job["result_data"] == {"score": 0.9, "passed": True}
    assert persisted_request["status"] == "completed"
    assert persisted_request["response_json"] == response
    assert persisted_session["state_json"]["step"] == 2
    assert [event["source_event_key"] for event in store.learning_events] == [
        "school-evaluation-job:atomic-completion"
    ]


def test_stale_completion_lease_rolls_back_the_entire_answer_attempt():
    store, initial_state, claim, job = _seed_running_job()
    response = {"feedback": "Should not persist."}
    completion = _completion(job, response)
    completion["lease_token"] = "stale-lease-token"

    with pytest.raises(ValueError, match="stale_school_evaluation_job"):
        _run(
            store.persist_school_answer_attempt(
                learning_event=_learning_event(),
                school_session=_school_session(initial_state),
                expected_state_json=initial_state,
                request_activity_id=ACTIVITY_ID,
                request_answer_hash=ANSWER_HASH,
                request_claim_token=claim["claim_token"],
                response_json=response,
                evaluation_job_completion=completion,
            )
        )

    persisted_job = _run(store.get_school_evaluation_job(USER_ID, SESSION_ID, ACTIVITY_ID))
    persisted_request = _run(
        store.get_school_answer_request(USER_ID, SESSION_ID, ACTIVITY_ID)
    )
    persisted_session = _run(store.get_school_session(USER_ID, SESSION_ID))

    assert persisted_job["status"] == "running"
    assert persisted_job["lease_token"] == job["lease_token"]
    assert persisted_request["status"] == "processing"
    assert persisted_session["state_json"] == initial_state
    assert store.learning_events == []


@pytest.mark.parametrize("terminal_status", ["failed", "cancelled"])
def test_new_claim_resets_only_a_terminal_job(terminal_status: str):
    store, initial_state, claim, job = _seed_running_job()
    if terminal_status == "failed":
        terminal = _run(
            store.fail_school_evaluation_job(
                **_completion(job, {"feedback": "Retry."}),
                last_error_code="provider_timeout",
            )
        )
    else:
        terminal = _run(
            store.cancel_school_evaluation_job(
                user_id=job["user_id"],
                session_id=job["session_id"],
                activity_id=job["activity_id"],
                answer_hash=job["answer_hash"],
                answer_claim_token=job["answer_claim_token"],
                lease_owner=job["lease_owner"],
                lease_token=job["lease_token"],
                lease_version=job["lease_version"],
            )
        )
    assert terminal is not None
    _run(
        store.fail_school_answer_request(
            USER_ID,
            SESSION_ID,
            ACTIVITY_ID,
            ANSWER_HASH,
            claim["claim_token"],
        )
    )

    next_hash = f"{ANSWER_HASH}-{terminal_status}"
    next_claim = _run(
        store.claim_school_answer_request(USER_ID, SESSION_ID, ACTIVITY_ID, next_hash)
    )
    assert next_claim["outcome"] == "claimed"
    reset = _run(
        store.enqueue_school_evaluation_job(
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            raw_answer="A new answer after the terminal job.",
            expected_state_json=initial_state,
            answer_hash=next_hash,
            answer_claim_token=next_claim["claim_token"],
            flow_type="curriculum",
            evaluation_mode="open_answer",
            max_attempts=3,
        )
    )

    assert reset["outcome"] == "queued"
    assert reset["job"]["status"] == "queued"
    assert reset["job"]["answer_hash"] == next_hash
    assert reset["job"]["answer_claim_token"] == next_claim["claim_token"]
    assert reset["job"]["attempts"] == 0
    assert reset["job"]["response_json"] is None
    assert reset["job"]["result_data"] is None
