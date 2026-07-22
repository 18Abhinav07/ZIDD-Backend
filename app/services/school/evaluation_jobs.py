"""Durable runner for School semantic-evaluation jobs.

The runner owns leases and retry policy only. A flow-specific finalizer owns
the learning-state transition, so a provider result cannot advance a learner
unless it is committed through the existing answer/evidence transaction.
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Awaitable, Callable
from typing import Any

from app.middleware.rate_limit import school_evaluation_job_context


logger = logging.getLogger(__name__)

SchoolEvaluationJob = dict[str, Any]
SchoolEvaluationJobProcessor = Callable[[SchoolEvaluationJob], Awaitable[None]]
_wake_event = asyncio.Event()
SCHOOL_EVALUATION_RETRY_DELAY_SECONDS = 1.0
# Claiming a durable job is database work, not provider work.  In particular,
# a cross-region Supabase round trip must not be cancelled by an arbitrary
# worker-local deadline and leave a queued learner answer waiting for another
# poll cycle.  Shutdown still cancels the worker task, and focused callers can
# supply a bounded timeout where that behavior is explicitly required.
SCHOOL_EVALUATION_CLAIM_TIMEOUT_SECONDS: float | None = None


class RetryableSchoolEvaluationJobError(RuntimeError):
    """A provider failure which may be safely retried with the same answer."""

    def __init__(
        self,
        code: str,
        *,
        retry_after_seconds: float | None = None,
    ) -> None:
        self.code = str(code or "school_evaluation_retryable_failure")
        try:
            normalized_retry_after = (
                float(retry_after_seconds)
                if retry_after_seconds is not None
                else None
            )
        except (TypeError, ValueError):
            normalized_retry_after = None
        self.retry_after_seconds = (
            normalized_retry_after
            if normalized_retry_after is not None
            and math.isfinite(normalized_retry_after)
            and normalized_retry_after >= 0
            else None
        )
        super().__init__(self.code)


class TerminalSchoolEvaluationJobError(RuntimeError):
    """A stale or malformed job that must not consume a provider retry."""

    def __init__(
        self,
        code: str,
        *,
        placement_retry_timing: dict[str, Any] | None = None,
    ) -> None:
        self.code = str(code or "school_evaluation_terminal_failure")
        self.placement_retry_timing = placement_retry_timing
        super().__init__(self.code)


def notify_school_evaluation_job_enqueued() -> None:
    """Wake an in-process worker after a durable enqueue commits."""

    _wake_event.set()


def _identity(job: SchoolEvaluationJob) -> dict[str, str | int]:
    fields = (
        "user_id",
        "session_id",
        "activity_id",
        "answer_hash",
        "answer_claim_token",
        "lease_owner",
        "lease_token",
    )
    identity = {field: str(job.get(field) or "") for field in fields}
    try:
        lease_version = int(job.get("lease_version"))
    except (TypeError, ValueError):
        lease_version = 0
    if not all(identity.values()) or lease_version <= 0:
        raise ValueError("invalid_school_evaluation_job_identity")
    return {**identity, "lease_version": lease_version}


async def _retry_or_fail(
    *,
    store: Any,
    job: SchoolEvaluationJob,
    error_code: str,
    max_attempts: int,
    retry_after_seconds: float | None = None,
    force_terminal: bool = False,
    placement_retry_timing: dict[str, Any] | None = None,
) -> None:
    identity = _identity(job)
    attempts = max(0, int(job.get("attempts") or 0))
    configured_attempts = max(1, int(max_attempts))
    persisted_attempts = max(1, int(job.get("max_attempts") or configured_attempts))
    effective_max_attempts = min(configured_attempts, persisted_attempts)
    if not force_terminal and attempts < effective_max_attempts:
        durable_retry_delay = (
            SCHOOL_EVALUATION_RETRY_DELAY_SECONDS
            if retry_after_seconds is None
            else retry_after_seconds
        )
        retried = await store.retry_school_evaluation_job(
            **identity,
            last_error_code=error_code,
            retry_after_seconds=durable_retry_delay,
        )
        if retried is None:
            logger.warning(
                "School evaluation retry lost lease for session=%s activity=%s",
                job.get("session_id"),
                job.get("activity_id"),
            )
        return

    terminalize_kwargs: dict[str, Any] = {
        **identity,
        "last_error_code": error_code,
        "error_json": {"error_code": error_code},
    }
    if placement_retry_timing is not None:
        terminalize_kwargs["placement_retry_timing"] = placement_retry_timing
    failed = await store.terminalize_school_evaluation_job(
        **terminalize_kwargs,
    )
    if failed is None:
        logger.warning(
            "School evaluation terminal failure lost lease for session=%s activity=%s",
            job.get("session_id"),
            job.get("activity_id"),
        )
        return
    # The terminalizer atomically releases the paired answer request. The
    # finalizer never ran, so no evidence or session transition exists and the
    # learner can deliberately retry the same item.


async def run_one_school_evaluation_job(
    *,
    store: Any,
    processor: SchoolEvaluationJobProcessor,
    max_attempts: int,
    claim_timeout_seconds: float | None = SCHOOL_EVALUATION_CLAIM_TIMEOUT_SECONDS,
    processor_timeout_seconds: float | None = None,
) -> bool:
    """Lease and process one job without granting it state-transition power."""

    try:
        if claim_timeout_seconds is None:
            job = await store.claim_school_evaluation_job()
        else:
            job = await asyncio.wait_for(
                store.claim_school_evaluation_job(),
                timeout=max(0.001, float(claim_timeout_seconds)),
            )
    except TimeoutError:
        logger.warning("School evaluation job claim timed out")
        return False
    if job is None:
        return False
    try:
        with school_evaluation_job_context():
            if processor_timeout_seconds is None:
                await processor(job)
            else:
                await asyncio.wait_for(
                    processor(job),
                    timeout=max(0.001, float(processor_timeout_seconds)),
                )
    except TimeoutError:
        await _retry_or_fail(
            store=store,
            job=job,
            error_code="school_evaluation_worker_stalled",
            max_attempts=max_attempts,
            force_terminal=True,
        )
    except RetryableSchoolEvaluationJobError as exc:
        await _retry_or_fail(
            store=store,
            job=job,
            error_code=exc.code,
            max_attempts=max_attempts,
            retry_after_seconds=exc.retry_after_seconds,
        )
    except TerminalSchoolEvaluationJobError as exc:
        await _retry_or_fail(
            store=store,
            job=job,
            error_code=exc.code,
            max_attempts=max_attempts,
            force_terminal=True,
            placement_retry_timing=exc.placement_retry_timing,
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
    claim_timeout_seconds: float | None = SCHOOL_EVALUATION_CLAIM_TIMEOUT_SECONDS,
    processor_timeout_seconds: float | None = None,
    poll_seconds: float = 1.0,
) -> None:
    """Run until shutdown; database leases make concurrent instances safe."""

    while not stop_event.is_set():
        # Clear before claiming, not after an empty claim. If an enqueue commits
        # while the claim is in flight, clearing here leaves its wake signal
        # intact so the next claim is immediate rather than delayed by a poll.
        _wake_event.clear()
        try:
            processed = await run_one_school_evaluation_job(
                store=store,
                processor=processor,
                max_attempts=max_attempts,
                claim_timeout_seconds=claim_timeout_seconds,
                processor_timeout_seconds=processor_timeout_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("School evaluation worker loop failed before job completion")
            processed = False
        if processed:
            continue
        if stop_event.is_set():
            break
        if _wake_event.is_set():
            continue
        try:
            await asyncio.wait_for(_wake_event.wait(), timeout=poll_seconds)
        except TimeoutError:
            pass


__all__ = [
    "RetryableSchoolEvaluationJobError",
    "TerminalSchoolEvaluationJobError",
    "SchoolEvaluationJob",
    "SchoolEvaluationJobProcessor",
    "notify_school_evaluation_job_enqueued",
    "run_one_school_evaluation_job",
    "run_school_evaluation_worker",
]
