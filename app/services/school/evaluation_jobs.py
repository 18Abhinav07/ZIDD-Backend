"""Durable runner for School semantic-evaluation jobs.

The runner owns leases and retry policy only. A flow-specific finalizer owns
the learning-state transition, so a provider result cannot advance a learner
unless it is committed through the existing answer/evidence transaction.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any


logger = logging.getLogger(__name__)

SchoolEvaluationJob = dict[str, Any]
SchoolEvaluationJobProcessor = Callable[[SchoolEvaluationJob], Awaitable[None]]
_wake_event = asyncio.Event()


class RetryableSchoolEvaluationJobError(RuntimeError):
    """A provider failure which may be safely retried with the same answer."""

    def __init__(self, code: str) -> None:
        self.code = str(code or "school_evaluation_retryable_failure")
        super().__init__(self.code)


def notify_school_evaluation_job_enqueued() -> None:
    """Wake an in-process worker after a durable enqueue commits."""

    _wake_event.set()


def _identity(job: SchoolEvaluationJob) -> dict[str, str]:
    fields = (
        "user_id",
        "session_id",
        "activity_id",
        "answer_hash",
        "answer_claim_token",
        "lease_token",
    )
    identity = {field: str(job.get(field) or "") for field in fields}
    if not all(identity.values()):
        raise ValueError("invalid_school_evaluation_job_identity")
    return identity


async def _retry_or_fail(
    *,
    store: Any,
    job: SchoolEvaluationJob,
    error_code: str,
    max_attempts: int,
) -> None:
    identity = _identity(job)
    attempts = max(0, int(job.get("attempts") or 0))
    if attempts < max_attempts:
        await store.retry_school_evaluation_job(
            **identity,
            last_error_code=error_code,
        )
        return

    await store.fail_school_evaluation_job(
        **identity,
        last_error_code=error_code,
        response_json=None,
        result_data=None,
    )
    # The finalizer never ran, so no evidence or session transition exists.
    # Releasing this claim lets the learner deliberately retry the same item.
    await store.fail_school_answer_request(
        identity["user_id"],
        identity["session_id"],
        identity["activity_id"],
        identity["answer_hash"],
        identity["answer_claim_token"],
    )


async def run_one_school_evaluation_job(
    *,
    store: Any,
    processor: SchoolEvaluationJobProcessor,
    max_attempts: int,
) -> bool:
    """Lease and process one job without granting it state-transition power."""

    job = await store.claim_school_evaluation_job()
    if job is None:
        return False
    try:
        await processor(job)
    except RetryableSchoolEvaluationJobError as exc:
        await _retry_or_fail(
            store=store,
            job=job,
            error_code=exc.code,
            max_attempts=max_attempts,
        )
    except Exception:
        logger.exception(
            "School evaluation worker failed for session=%s activity=%s",
            job.get("session_id"),
            job.get("activity_id"),
        )
        await _retry_or_fail(
            store=store,
            job=job,
            error_code="school_evaluation_worker_failure",
            max_attempts=max_attempts,
        )
    return True


async def run_school_evaluation_worker(
    *,
    store: Any,
    processor: SchoolEvaluationJobProcessor,
    max_attempts: int,
    stop_event: asyncio.Event,
    poll_seconds: float = 1.0,
) -> None:
    """Run until shutdown; database leases make concurrent instances safe."""

    while not stop_event.is_set():
        processed = await run_one_school_evaluation_job(
            store=store,
            processor=processor,
            max_attempts=max_attempts,
        )
        if processed:
            continue
        _wake_event.clear()
        try:
            await asyncio.wait_for(_wake_event.wait(), timeout=poll_seconds)
        except TimeoutError:
            pass


__all__ = [
    "RetryableSchoolEvaluationJobError",
    "SchoolEvaluationJob",
    "SchoolEvaluationJobProcessor",
    "notify_school_evaluation_job_enqueued",
    "run_one_school_evaluation_job",
    "run_school_evaluation_worker",
]
