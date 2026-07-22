from __future__ import annotations

import asyncio
import inspect

import pytest

from app.services.school import evaluation_jobs


_DEFAULT_RESULT = object()


JOB = {
    "session_id": "00000000-0000-4000-8000-000000000001",
    "activity_id": "chapter-check-1",
    "user_id": "learner-1",
    "answer_hash": "answer-hash",
    "answer_claim_token": "claim-token",
    "lease_owner": "school-evaluation-worker-a",
    "lease_token": "lease-token",
    "lease_version": 1,
    "attempts": 1,
    "max_attempts": 2,
    "status": "running",
}


class _Store:
    def __init__(
        self,
        job: dict | None,
        *,
        retry_result: dict | None | object = _DEFAULT_RESULT,
        failure_result: dict | None | object = _DEFAULT_RESULT,
    ):
        self.job = job
        self.retry_result = (
            {"status": "queued"} if retry_result is _DEFAULT_RESULT else retry_result
        )
        self.failure_result = (
            {"status": "failed"}
            if failure_result is _DEFAULT_RESULT
            else failure_result
        )
        self.retries: list[dict] = []
        self.terminalizations: list[dict] = []

    async def claim_school_evaluation_job(self):
        claimed, self.job = self.job, None
        return claimed

    async def retry_school_evaluation_job(self, **kwargs):
        self.retries.append(kwargs)
        return self.retry_result

    async def terminalize_school_evaluation_job(self, **kwargs):
        self.terminalizations.append(kwargs)
        return self.failure_result


def test_worker_default_does_not_apply_an_arbitrary_claim_deadline():
    parameter = inspect.signature(
        evaluation_jobs.run_one_school_evaluation_job
    ).parameters["claim_timeout_seconds"]

    assert parameter.default is None


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
    assert store.terminalizations == []


@pytest.mark.asyncio
async def test_worker_cancels_a_stalled_database_claim_without_calling_processor():
    claim_started = asyncio.Event()
    claim_cancelled = asyncio.Event()
    processor_called = False

    class _BlockingClaimStore:
        async def claim_school_evaluation_job(self):
            claim_started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                claim_cancelled.set()
                raise

    async def processor(_job: dict) -> None:
        nonlocal processor_called
        processor_called = True

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=_BlockingClaimStore(),
        processor=processor,
        max_attempts=2,
        claim_timeout_seconds=0.001,
    )

    assert claim_started.is_set()
    assert claim_cancelled.is_set()
    assert processed is False
    assert processor_called is False


@pytest.mark.asyncio
async def test_worker_cancels_a_stalled_processor_at_the_hard_deadline():
    store = _Store(dict(JOB))
    blocker = asyncio.Event()
    cancelled = asyncio.Event()

    async def processor(_job: dict) -> None:
        try:
            await blocker.wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=processor,
        max_attempts=2,
        processor_timeout_seconds=0.001,
    )

    assert processed is True
    assert cancelled.is_set()
    assert store.retries == []
    assert store.terminalizations == [
        {
            "user_id": JOB["user_id"],
            "session_id": JOB["session_id"],
            "activity_id": JOB["activity_id"],
            "answer_hash": JOB["answer_hash"],
            "answer_claim_token": JOB["answer_claim_token"],
            "lease_owner": JOB["lease_owner"],
            "lease_token": JOB["lease_token"],
            "lease_version": JOB["lease_version"],
            "last_error_code": "school_evaluation_worker_stalled",
            "error_json": {"error_code": "school_evaluation_worker_stalled"},
        }
    ]


@pytest.mark.asyncio
async def test_worker_loop_survives_a_transient_claim_error():
    stop_event = __import__("asyncio").Event()

    class _FlakyClaimStore:
        def __init__(self) -> None:
            self.claim_calls = 0

        async def claim_school_evaluation_job(self):
            self.claim_calls += 1
            if self.claim_calls == 1:
                raise RuntimeError("temporary database failure")
            stop_event.set()
            return None

    store = _FlakyClaimStore()

    async def processor(_job: dict) -> None:
        raise AssertionError("the processor must not run")

    await evaluation_jobs.run_school_evaluation_worker(
        store=store,
        processor=processor,
        max_attempts=2,
        stop_event=stop_event,
        poll_seconds=0.001,
    )

    assert store.claim_calls == 2


@pytest.mark.asyncio
async def test_worker_does_not_lose_an_enqueue_signal_that_arrives_during_an_empty_claim(monkeypatch):
    """A committed job must be reclaimed without waiting for the next poll.

    The enqueue signal can arrive after the worker starts an empty claim but
    before that claim returns. Clearing the event after the claim loses that
    signal and adds an avoidable full poll interval to learner feedback.
    """

    wake_event = asyncio.Event()
    monkeypatch.setattr(evaluation_jobs, "_wake_event", wake_event)
    stop_event = asyncio.Event()
    first_claim_started = asyncio.Event()
    release_first_claim = asyncio.Event()
    second_claim_started = asyncio.Event()
    handled: list[dict] = []

    class _WakeRaceStore:
        def __init__(self) -> None:
            self.claim_calls = 0

        async def claim_school_evaluation_job(self):
            self.claim_calls += 1
            if self.claim_calls == 1:
                first_claim_started.set()
                await release_first_claim.wait()
                return None
            second_claim_started.set()
            stop_event.set()
            return dict(JOB)

    async def processor(job: dict) -> None:
        handled.append(job)

    worker = asyncio.create_task(
        evaluation_jobs.run_school_evaluation_worker(
            store=_WakeRaceStore(),
            processor=processor,
            max_attempts=2,
            stop_event=stop_event,
            poll_seconds=5.0,
        )
    )
    try:
        await first_claim_started.wait()
        evaluation_jobs.notify_school_evaluation_job_enqueued()
        release_first_claim.set()
        await asyncio.wait_for(second_claim_started.wait(), timeout=0.1)
    finally:
        stop_event.set()
        evaluation_jobs.notify_school_evaluation_job_enqueued()
        await worker

    assert handled == [JOB]


@pytest.mark.asyncio
async def test_worker_persists_a_provider_retry_after_without_blocking_the_worker(monkeypatch):
    store = _Store(dict(JOB))
    delays: list[float] = []

    async def capture_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(evaluation_jobs.asyncio, "sleep", capture_sleep)

    async def processor(_job: dict) -> None:
        raise evaluation_jobs.RetryableSchoolEvaluationJobError(
            "school_open_provider_failure",
            retry_after_seconds=37.5,
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
            "lease_owner": JOB["lease_owner"],
            "lease_token": JOB["lease_token"],
            "lease_version": JOB["lease_version"],
            "last_error_code": "school_open_provider_failure",
            "retry_after_seconds": 37.5,
        }
    ]
    assert store.terminalizations == []
    assert delays == []


@pytest.mark.asyncio
async def test_worker_terminal_failure_does_not_consume_provider_retries():
    store = _Store(dict(JOB))

    async def processor(_job: dict) -> None:
        raise evaluation_jobs.TerminalSchoolEvaluationJobError(
            "stale_school_evaluation_job"
        )

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=processor,
        max_attempts=2,
    )

    assert processed is True
    assert store.retries == []
    assert store.terminalizations == [
        {
            "user_id": JOB["user_id"],
            "session_id": JOB["session_id"],
            "activity_id": JOB["activity_id"],
            "answer_hash": JOB["answer_hash"],
            "answer_claim_token": JOB["answer_claim_token"],
            "lease_owner": JOB["lease_owner"],
            "lease_token": JOB["lease_token"],
            "lease_version": JOB["lease_version"],
            "last_error_code": "stale_school_evaluation_job",
            "error_json": {"error_code": "stale_school_evaluation_job"},
        }
    ]


@pytest.mark.asyncio
async def test_worker_forwards_placement_retry_timing_with_terminal_failure():
    store = _Store(dict(JOB))
    placement_retry_timing = {
        "item_id": JOB["activity_id"],
        "retry_pending": True,
        "accrued_learner_seconds": 12.5,
        "presented_at": "2026-07-19T09:00:00+00:00",
    }

    async def processor(_job: dict) -> None:
        raise evaluation_jobs.TerminalSchoolEvaluationJobError(
            "placement_english_response_required",
            placement_retry_timing=placement_retry_timing,
        )

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=processor,
        max_attempts=2,
    )

    assert processed is True
    assert store.retries == []
    assert store.terminalizations == [
        {
            "user_id": JOB["user_id"],
            "session_id": JOB["session_id"],
            "activity_id": JOB["activity_id"],
            "answer_hash": JOB["answer_hash"],
            "answer_claim_token": JOB["answer_claim_token"],
            "lease_owner": JOB["lease_owner"],
            "lease_token": JOB["lease_token"],
            "lease_version": JOB["lease_version"],
            "last_error_code": "placement_english_response_required",
            "error_json": {
                "error_code": "placement_english_response_required"
            },
            "placement_retry_timing": placement_retry_timing,
        }
    ]


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
    assert store.terminalizations == [
        {
            "user_id": JOB["user_id"],
            "session_id": JOB["session_id"],
            "activity_id": JOB["activity_id"],
            "answer_hash": JOB["answer_hash"],
            "answer_claim_token": JOB["answer_claim_token"],
            "lease_owner": JOB["lease_owner"],
            "lease_token": JOB["lease_token"],
            "lease_version": JOB["lease_version"],
            "last_error_code": "school_open_provider_failure",
            "error_json": {"error_code": "school_open_provider_failure"},
        }
    ]


@pytest.mark.asyncio
async def test_worker_does_not_release_answer_when_a_fenced_failure_loses_its_lease():
    terminal_job = {**JOB, "attempts": 2}
    store = _Store(terminal_job, failure_result=None)

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
    assert len(store.terminalizations) == 1
