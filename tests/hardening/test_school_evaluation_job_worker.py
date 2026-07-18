from __future__ import annotations

import pytest

from app.services.school import evaluation_jobs


JOB = {
    "session_id": "00000000-0000-4000-8000-000000000001",
    "activity_id": "chapter-check-1",
    "user_id": "learner-1",
    "answer_hash": "answer-hash",
    "answer_claim_token": "claim-token",
    "lease_token": "lease-token",
    "attempts": 1,
    "status": "running",
}


class _Store:
    def __init__(self, job: dict | None):
        self.job = job
        self.retries: list[dict] = []
        self.failures: list[dict] = []
        self.answer_failures: list[tuple] = []

    async def claim_school_evaluation_job(self):
        claimed, self.job = self.job, None
        return claimed

    async def retry_school_evaluation_job(self, **kwargs):
        self.retries.append(kwargs)

    async def fail_school_evaluation_job(self, **kwargs):
        self.failures.append(kwargs)

    async def fail_school_answer_request(self, *args):
        self.answer_failures.append(args)


@pytest.mark.asyncio
async def test_worker_claims_a_durable_job_and_delegates_finalization():
    store = _Store(dict(JOB))
    handled: list[dict] = []

    async def processor(job: dict) -> None:
        handled.append(job)

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=processor,
        max_attempts=2,
    )

    assert processed is True
    assert handled == [JOB]
    assert store.retries == []
    assert store.failures == []
    assert store.answer_failures == []


@pytest.mark.asyncio
async def test_worker_requeues_a_retryable_failure_before_terminal_failure():
    store = _Store(dict(JOB))

    async def processor(_job: dict) -> None:
        raise evaluation_jobs.RetryableSchoolEvaluationJobError(
            "school_open_provider_failure"
        )

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=processor,
        max_attempts=2,
    )

    assert processed is True
    assert store.retries == [
        {
            "user_id": JOB["user_id"],
            "session_id": JOB["session_id"],
            "activity_id": JOB["activity_id"],
            "answer_hash": JOB["answer_hash"],
            "answer_claim_token": JOB["answer_claim_token"],
            "lease_token": JOB["lease_token"],
            "last_error_code": "school_open_provider_failure",
        }
    ]
    assert store.failures == []
    assert store.answer_failures == []


@pytest.mark.asyncio
async def test_worker_marks_terminal_failure_and_releases_the_answer_for_retry():
    terminal_job = {**JOB, "attempts": 2}
    store = _Store(terminal_job)

    async def processor(_job: dict) -> None:
        raise evaluation_jobs.RetryableSchoolEvaluationJobError(
            "school_open_provider_failure"
        )

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=processor,
        max_attempts=2,
    )

    assert processed is True
    assert store.retries == []
    assert store.failures == [
        {
            "user_id": JOB["user_id"],
            "session_id": JOB["session_id"],
            "activity_id": JOB["activity_id"],
            "answer_hash": JOB["answer_hash"],
            "answer_claim_token": JOB["answer_claim_token"],
            "lease_token": JOB["lease_token"],
            "last_error_code": "school_open_provider_failure",
            "response_json": None,
            "result_data": None,
        }
    ]
    assert store.answer_failures == [
        (
            JOB["user_id"],
            JOB["session_id"],
            JOB["activity_id"],
            JOB["answer_hash"],
            JOB["answer_claim_token"],
        )
    ]
