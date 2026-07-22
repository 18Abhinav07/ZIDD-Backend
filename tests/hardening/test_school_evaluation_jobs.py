from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from app.db import repo
from app.db import schema_guard
from app.storage import pg_store
from scripts import apply_migrations
from tests.conftest import InMemoryStore


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "app/db/migrations/2026-07-18-school-evaluation-jobs.sql"
FK_REPAIR_MIGRATION = (
    ROOT / "app/db/migrations/2026-07-18-school-evaluation-jobs-fk-repair.sql"
)
RETRY_SCHEDULE_MIGRATION = (
    ROOT / "app/db/migrations/2026-07-19-school-evaluation-job-retry-schedule.sql"
)
REQUEST_METADATA_MIGRATION = (
    ROOT / "app/db/migrations/2026-07-19-school-evaluation-job-request-metadata.sql"
)
SESSION_ID = "10000000-0000-4000-8000-000000000001"
ACTIVITY_ID = "chapter-check-1"
USER_ID = "learner-1"
ANSWER_HASH = "answer-sha"
ANSWER_CLAIM_TOKEN = "answer-claim-token"


def _run(coro):
    return asyncio.run(coro)


def _normalized(text: str) -> str:
    return " ".join(text.split())


class _Result:
    def __init__(self, row: dict | None = None, scalar=None):
        self._row = copy.deepcopy(row) if row is not None else None
        self._scalar = scalar

    def mappings(self):
        return self

    def first(self):
        return copy.deepcopy(self._row) if self._row is not None else None

    def scalar_one_or_none(self):
        return self._scalar


class _EvaluationJobSession:
    """Small stateful SQL fake for repository transaction contracts."""

    def __init__(self):
        self.answer_requests = {
            (SESSION_ID, ACTIVITY_ID): {
                "session_id": SESSION_ID,
                "activity_id": ACTIVITY_ID,
                "user_id": USER_ID,
                "answer_hash": ANSWER_HASH,
                "claim_token": ANSWER_CLAIM_TOKEN,
                "status": "processing",
                "response_json": None,
                "updated_at": "created",
            }
        }
        self.jobs: dict[tuple[str, str], dict] = {}
        self.calls: list[tuple[str, dict]] = []
        self.commits = 0
        self.rollbacks = 0
        self.fail_next_job_insert = False
        self._transaction_snapshot: tuple[dict, dict] | None = None

    def _begin_transaction(self) -> None:
        if self._transaction_snapshot is None:
            self._transaction_snapshot = (
                copy.deepcopy(self.answer_requests),
                copy.deepcopy(self.jobs),
            )

    async def execute(self, statement, params=None):
        sql = _normalized(str(statement))
        params = dict(params or {})
        self.calls.append((sql, params))
        key = (str(params.get("session_id") or ""), str(params.get("activity_id") or ""))

        if "pg_advisory_xact_lock" in sql:
            self._begin_transaction()
            return _Result()

        if sql.startswith("SELECT user_id, answer_hash, claim_token, status, response_json"):
            return _Result(self.answer_requests.get(key))

        if sql.startswith("SELECT") and "FROM school_answer_requests" in sql:
            request = self.answer_requests.get(key)
            matches = bool(
                request
                and request["user_id"] == params.get("uid")
                and request["answer_hash"] == params.get("answer_hash")
                and request["claim_token"] == params.get("answer_claim_token")
                and request["status"] == "processing"
            )
            return _Result(request if matches else None)

        if sql.startswith("INSERT INTO school_answer_requests"):
            self.answer_requests[key] = {
                "session_id": params["session_id"],
                "activity_id": params["activity_id"],
                "user_id": params["uid"],
                "answer_hash": params["answer_hash"],
                "claim_token": params["claim_token"],
                "status": "processing",
                "response_json": None,
                "updated_at": "created",
            }
            return _Result()

        if sql.startswith("UPDATE school_answer_requests"):
            request = self.answer_requests.get(key)
            if request is not None and request.get("user_id") == params.get("uid"):
                request.update(
                    answer_hash=params["answer_hash"],
                    claim_token=params["claim_token"],
                    status="processing",
                    response_json=None,
                    updated_at="claimed",
                )
            return _Result()

        if sql.startswith("WITH terminal_request_candidates"):
            for job_key, job in self.jobs.items():
                deadline_expired = job.get("created_at") == "deadline-expired"
                recovery_expired = bool(
                    job.get("status") == "running"
                    and job.get("lease_expires_at") == "expired"
                    and job.get("attempts", 0) > job.get("max_attempts", 0)
                )
                if not (deadline_expired or recovery_expired):
                    continue
                error_code = (
                    "evaluation_deadline_exceeded"
                    if deadline_expired
                    else "evaluation_recovery_lease_expired"
                )
                job.update(
                    status="failed",
                    last_error_code=error_code,
                    error_json={"reason": error_code},
                    response_json=None,
                    result_data=None,
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    failed_at="failed",
                    updated_at="failed",
                )
                request = self.answer_requests.get(job_key)
                if (
                    request
                    and request.get("user_id") == job.get("user_id")
                    and request.get("answer_hash") == job.get("answer_hash")
                    and request.get("claim_token") == job.get("answer_claim_token")
                    and request.get("status") == "processing"
                ):
                    request.update(
                        status="failed",
                        response_json=None,
                        updated_at="failed",
                    )
            return _Result(scalar=0)

        if sql.startswith("WITH candidate") and "UPDATE school_evaluation_jobs AS job" in sql:
            for job_key, job in self.jobs.items():
                request = self.answer_requests.get(job_key)
                current_claim = bool(
                    request
                    and request.get("status") == "processing"
                    and request.get("user_id") == job.get("user_id")
                    and request.get("answer_hash") == job.get("answer_hash")
                    and request.get("claim_token") == job.get("answer_claim_token")
                )
                claimable = (
                    job["status"] == "queued"
                    and job["attempts"] < job["max_attempts"]
                    and job.get("next_attempt_at", "ready") == "ready"
                ) or (
                    job["status"] == "running"
                    and job.get("lease_expires_at") == "expired"
                    and job["attempts"] <= job["max_attempts"]
                )
                if not current_claim or not claimable:
                    continue
                job["status"] = "running"
                job["attempts"] += 1
                job["lease_owner"] = params["lease_owner"]
                job["lease_token"] = params["lease_token"]
                job["lease_version"] += 1
                job["lease_expires_at"] = "active"
                job["started_at"] = job.get("started_at") or "started"
                job["updated_at"] = "updated"
                return _Result(job)
            return _Result()

        if sql.startswith("SELECT") and "FROM school_evaluation_jobs" in sql:
            job = self.jobs.get(key)
            if job is not None and "user_id = :uid" in sql:
                if job["user_id"] != params.get("uid"):
                    job = None
            if job is not None and "raw_answer" not in sql:
                job = {
                    key: value
                    for key, value in job.items()
                    if key
                    not in {
                        "raw_answer",
                        "expected_state_json",
                        "request_metadata_json",
                        "expected_state_digest",
                        "answer_hash",
                        "answer_claim_token",
                        "lease_owner",
                        "lease_token",
                        "lease_version",
                        "error_json",
                        "response_json",
                        "result_data",
                    }
                }
            return _Result(job)

        if sql.startswith("INSERT INTO school_evaluation_jobs"):
            if self.fail_next_job_insert:
                self.fail_next_job_insert = False
                raise RuntimeError("injected_school_evaluation_job_insert")
            job = {
                "session_id": params["session_id"],
                "activity_id": params["activity_id"],
                "user_id": params["uid"],
                "raw_answer": params["raw_answer"],
                "expected_state_json": json.loads(params["expected_state_json"]),
                "request_metadata_json": json.loads(
                    params["request_metadata_json"]
                ),
                "expected_state_digest": params["expected_state_digest"],
                "answer_hash": params["answer_hash"],
                "answer_claim_token": params["answer_claim_token"],
                "flow_type": params["flow_type"],
                "evaluation_mode": params["evaluation_mode"],
                "status": "queued",
                "attempts": 0,
                "max_attempts": params["max_attempts"],
                "lease_owner": None,
                "lease_token": None,
                "lease_version": 0,
                "lease_expires_at": None,
                "next_attempt_at": "ready",
                "last_error_code": None,
                "error_json": None,
                "response_json": None,
                "result_data": None,
                "created_at": "created",
                "updated_at": "created",
                "started_at": None,
                "completed_at": None,
                "failed_at": None,
                "cancelled_at": None,
            }
            self.jobs[(job["session_id"], job["activity_id"])] = job
            return _Result(job)

        job = self.jobs.get(key)
        if "UPDATE school_evaluation_jobs" not in sql:
            return _Result()

        matches_job_identity = bool(
            job
            and job["user_id"] == params.get("uid")
            and job["answer_hash"] == params.get("answer_hash")
            and job["answer_claim_token"] == params.get("answer_claim_token")
        )
        matches_identity = bool(
            matches_job_identity
            and job.get("lease_owner") == params.get("lease_owner")
            and job.get("lease_token") == params.get("lease_token")
            and job.get("lease_version") == params.get("lease_version")
            and job.get("lease_expires_at") == "active"
        )
        request = self.answer_requests.get(key)
        matches_current_request = bool(
            request
            and request.get("user_id") == params.get("uid")
            and request.get("answer_hash") == params.get("answer_hash")
            and request.get("claim_token") == params.get("answer_claim_token")
            and request.get("status") == "processing"
        )
        if "SET user_id = :uid" in sql:
            if job is None or job.get("status") not in {"failed", "cancelled"}:
                return _Result()
            job.update(
                user_id=params["uid"],
                raw_answer=params["raw_answer"],
                expected_state_json=json.loads(params["expected_state_json"]),
                request_metadata_json=json.loads(params["request_metadata_json"]),
                expected_state_digest=params["expected_state_digest"],
                answer_hash=params["answer_hash"],
                answer_claim_token=params["answer_claim_token"],
                flow_type=params["flow_type"],
                evaluation_mode=params["evaluation_mode"],
                status="queued",
                attempts=0,
                max_attempts=params["max_attempts"],
                lease_owner=None,
                lease_token=None,
                lease_expires_at=None,
                next_attempt_at="ready",
                last_error_code=None,
                error_json=None,
                response_json=None,
                result_data=None,
                created_at="reset",
                updated_at="reset",
                started_at=None,
                completed_at=None,
                failed_at=None,
                cancelled_at=None,
            )
            return _Result(job)
        if "SET status = 'queued'" in sql:
            if (
                not matches_identity
                or job["status"] != "running"
                or job["attempts"] >= job["max_attempts"]
            ):
                return _Result()
            job.update(
                status="queued",
                lease_owner=None,
                lease_token=None,
                lease_expires_at=None,
                next_attempt_at=(
                    "scheduled" if params.get("retry_after_seconds", 0) else "ready"
                ),
                last_error_code=params["last_error_code"],
                error_json=json.loads(params["error_json"])
                if params.get("error_json")
                else None,
                response_json=None,
                result_data=None,
                failed_at=None,
                updated_at="retried",
            )
            return _Result(job)
        if "released_request AS" in sql:
            if (
                not matches_identity
                or job["status"] != "running"
                or not matches_current_request
            ):
                return _Result()
            job.update(
                status="failed",
                last_error_code=params["last_error_code"],
                error_json=json.loads(params["error_json"])
                if params.get("error_json")
                else None,
                response_json=None,
                result_data=None,
                lease_owner=None,
                lease_token=None,
                lease_expires_at=None,
                failed_at="failed",
                updated_at="failed",
            )
            request.update(
                status="failed",
                response_json=None,
                updated_at="failed",
            )
            return _Result(job)
        if "SET status = 'cancelled'" in sql:
            queued = bool(
                matches_job_identity
                and job["status"] == "queued"
                and matches_current_request
            )
            fenced_running = bool(
                matches_identity
                and job["status"] == "running"
                and matches_current_request
            )
            if not (queued or fenced_running):
                return _Result()
            job.update(
                status="cancelled",
                last_error_code=params["last_error_code"],
                error_json=json.loads(params["error_json"])
                if params.get("error_json")
                else None,
                lease_owner=None,
                lease_token=None,
                lease_expires_at=None,
                cancelled_at="cancelled",
                updated_at="cancelled",
            )
            return _Result(job)
        if "SET status = 'completed'" in sql:
            if not matches_identity or job["status"] != "running":
                return _Result()
            job.update(
                status="completed",
                response_json=json.loads(params["response_json"]),
                result_data=json.loads(params["result_data"]),
                error_json=None,
                lease_owner=None,
                lease_token=None,
                lease_expires_at=None,
                completed_at="completed",
                updated_at="completed",
            )
            return _Result(job)

        if "SET status = 'failed'" in sql:
            if not matches_identity or job["status"] != "running":
                return _Result()
            job.update(
                status="failed",
                last_error_code=params["last_error_code"],
                error_json=json.loads(params["error_json"])
                if params.get("error_json")
                else None,
                response_json=json.loads(params["response_json"])
                if params.get("response_json")
                else None,
                result_data=json.loads(params["result_data"])
                if params.get("result_data")
                else None,
                lease_token=None,
                lease_expires_at=None,
                failed_at="failed",
                updated_at="failed",
            )
            return _Result(job)

        if "renewed_request AS" in sql:
            if (
                not matches_identity
                or job["status"] != "running"
                or not matches_current_request
            ):
                return _Result(scalar=None)
            job["lease_expires_at"] = "active"
            job["updated_at"] = "heartbeated"
            request["updated_at"] = "heartbeated"
            return _Result(scalar=job["activity_id"])

        return _Result()

    async def commit(self):
        self.commits += 1
        self._transaction_snapshot = None

    async def rollback(self):
        self.rollbacks += 1
        if self._transaction_snapshot is not None:
            self.answer_requests, self.jobs = self._transaction_snapshot
        self._transaction_snapshot = None


def _enqueue(session: _EvaluationJobSession, **overrides):
    payload = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "activity_id": ACTIVITY_ID,
        "raw_answer": "Because the character used evidence from the chapter.",
        "expected_state_json": {
            "chapter_id": "eng_c3_ch01",
            "current_activity_id": ACTIVITY_ID,
        },
        "answer_hash": ANSWER_HASH,
        "answer_claim_token": ANSWER_CLAIM_TOKEN,
        "flow_type": "curriculum",
        "evaluation_mode": "open_answer",
        "max_attempts": 3,
    }
    payload.update(overrides)
    return _run(repo.enqueue_school_evaluation_job(session, **payload))


def _claim(session: _EvaluationJobSession, lease_owner: str = "worker-a"):
    return _run(repo.claim_school_evaluation_job(
        session,
        lease_owner=lease_owner,
        lease_seconds=45,
    ))


def _complete(
    session: _EvaluationJobSession,
    *,
    user_id: str = USER_ID,
    lease_owner: str,
    lease_token: str,
    lease_version: int,
):
    return _run(repo.complete_school_evaluation_job(
        session,
        user_id=user_id,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=lease_owner,
        lease_token=lease_token,
        lease_version=lease_version,
        response_json={"visible_feedback": "Good evidence."},
        result_data={"score": 0.8, "passed": True},
    ))


def _claim_and_enqueue_payload(**overrides) -> dict:
    payload = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "activity_id": ACTIVITY_ID,
        "raw_answer": "Because the character used evidence from the chapter.",
        "expected_state_json": {
            "chapter_id": "eng_c3_ch01",
            "current_activity_id": ACTIVITY_ID,
        },
        "answer_hash": ANSWER_HASH,
        "flow_type": "curriculum",
        "evaluation_mode": "open_answer",
        "max_attempts": 2,
    }
    payload.update(overrides)
    return payload


def _request_metadata(*, arrival_id: str = "arrival-1") -> dict:
    return {
        "answer_arrival": {
            "arrival_id": arrival_id,
            "received_at": "2026-07-19T09:00:00Z",
        }
    }


def _placement_retry_timing(*, item_id: str = ACTIVITY_ID) -> dict:
    return {
        "item_id": item_id,
        "retry_pending": True,
        "accrued_learner_seconds": 12.5,
        "presented_at": "2026-07-19T09:00:00+00:00",
    }


def _claimed_placement_job_store() -> tuple[InMemoryStore, dict, dict]:
    store = InMemoryStore()
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "api_version": "rebuild",
        "flow_type": "placement",
        "status": "active",
        "state_json": {
            "_placement_item_timing": {
                "item_id": ACTIVITY_ID,
                "presented_at": "2026-07-19T08:59:00+00:00",
            }
        },
    }
    answer_claim = _run(store.claim_school_answer_request(
        USER_ID,
        SESSION_ID,
        ACTIVITY_ID,
        ANSWER_HASH,
    ))
    assert answer_claim["outcome"] == "claimed"
    queued = _run(store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        raw_answer="The learner's private answer.",
        expected_state_json={"current_activity_id": ACTIVITY_ID},
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        flow_type="placement",
        evaluation_mode="open_answer",
    ))
    assert queued["outcome"] == "queued"
    claimed = _run(store.claim_school_evaluation_job("in-memory-worker", lease_seconds=45))
    assert claimed is not None
    return store, answer_claim, claimed


def _terminalize_placement_job(
    store: InMemoryStore,
    answer_claim: dict,
    claimed: dict,
    *,
    placement_retry_timing: dict,
):
    return _run(store.terminalize_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        last_error_code="placement_english_response_required",
        placement_retry_timing=placement_retry_timing,
    ))


def test_in_memory_terminalization_applies_valid_placement_retry_timing_atomically():
    store, answer_claim, claimed = _claimed_placement_job_store()
    timing = _placement_retry_timing()

    terminalized = _terminalize_placement_job(
        store,
        answer_claim,
        claimed,
        placement_retry_timing=timing,
    )

    assert terminalized is not None
    assert terminalized["status"] == "failed"
    assert store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"
    assert store.school_sessions[(USER_ID, SESSION_ID)]["state_json"][
        "_placement_item_timing"
    ] == timing


@pytest.mark.parametrize(
    "placement_retry_timing",
    [
        {**_placement_retry_timing(), "untrusted": "field"},
        {**_placement_retry_timing(), "item_id": "other-item"},
        {**_placement_retry_timing(), "retry_pending": False},
        {**_placement_retry_timing(), "accrued_learner_seconds": float("nan")},
        {**_placement_retry_timing(), "presented_at": "not-an-iso-date"},
    ],
)
def test_in_memory_terminalization_rejects_malformed_placement_retry_timing(
    placement_retry_timing: dict,
):
    store, answer_claim, claimed = _claimed_placement_job_store()

    with pytest.raises(
        ValueError,
        match="invalid_school_evaluation_job_placement_retry_timing",
    ):
        _terminalize_placement_job(
            store,
            answer_claim,
            claimed,
            placement_retry_timing=placement_retry_timing,
        )

    assert store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "running"
    assert store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "processing"


def test_in_memory_terminalization_rejects_stale_placement_timing_identity():
    store, answer_claim, claimed = _claimed_placement_job_store()
    store.school_sessions[(USER_ID, SESSION_ID)]["state_json"][
        "_placement_item_timing"
    ]["item_id"] = "other-item"

    terminalized = _terminalize_placement_job(
        store,
        answer_claim,
        claimed,
        placement_retry_timing=_placement_retry_timing(),
    )

    assert terminalized is None
    assert store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "running"
    assert store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "processing"
    assert store.school_sessions[(USER_ID, SESSION_ID)]["state_json"][
        "_placement_item_timing"
    ]["item_id"] == "other-item"


def test_in_memory_terminalization_never_applies_timing_to_a_nonplacement_job():
    store, answer_claim, claimed = _claimed_placement_job_store()
    store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)]["flow_type"] = "curriculum"

    terminalized = _terminalize_placement_job(
        store,
        answer_claim,
        claimed,
        placement_retry_timing=_placement_retry_timing(),
    )

    assert terminalized is None
    assert store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "running"
    assert store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "processing"
    assert store.school_sessions[(USER_ID, SESSION_ID)]["state_json"][
        "_placement_item_timing"
    ] == {
        "item_id": ACTIVITY_ID,
        "presented_at": "2026-07-19T08:59:00+00:00",
    }


def test_terminalization_rejects_malformed_placement_timing_before_sql():
    session = _EvaluationJobSession()

    with pytest.raises(
        ValueError,
        match="invalid_school_evaluation_job_placement_retry_timing",
    ):
        _run(repo.terminalize_school_evaluation_job(
            session,
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            answer_hash=ANSWER_HASH,
            answer_claim_token=ANSWER_CLAIM_TOKEN,
            lease_owner="worker-a",
            lease_token="lease-token",
            lease_version=1,
            last_error_code="placement_english_response_required",
            placement_retry_timing={**_placement_retry_timing(), "untrusted": True},
        ))

    assert session.calls == []
    assert session.commits == 0


def test_claim_and_enqueue_recovers_a_no_job_claim_and_preserves_outcomes():
    claim_and_enqueue = getattr(repo, "claim_and_enqueue_school_evaluation_job", None)
    assert callable(claim_and_enqueue)

    crashed_claim = _EvaluationJobSession()
    queued = _run(claim_and_enqueue(
        crashed_claim,
        **_claim_and_enqueue_payload(),
    ))
    assert queued["outcome"] == "queued"
    assert queued["claim_token"] == ANSWER_CLAIM_TOKEN
    assert queued["job"]["status"] == "queued"
    assert "raw_answer" not in queued["job"]
    assert crashed_claim.jobs[(SESSION_ID, ACTIVITY_ID)]["answer_claim_token"] == (
        ANSWER_CLAIM_TOKEN
    )
    lock_keys = [
        params["lock_key"]
        for sql, params in crashed_claim.calls
        if "pg_advisory_xact_lock" in sql
    ]
    assert f"school-answer:{SESSION_ID}:{ACTIVITY_ID}" in lock_keys
    assert f"school-evaluation-job:{SESSION_ID}:{ACTIVITY_ID}" in lock_keys
    assert crashed_claim.commits == 1

    existing = _run(claim_and_enqueue(
        crashed_claim,
        **_claim_and_enqueue_payload(),
    ))
    assert existing["outcome"] == "in_progress"
    assert existing["claim_token"] == ANSWER_CLAIM_TOKEN
    assert existing["job"]["status"] == "queued"
    assert "raw_answer" not in existing["job"]

    completed = _EvaluationJobSession()
    completed.answer_requests[(SESSION_ID, ACTIVITY_ID)].update(
        status="completed",
        response_json={"feedback": "Already recorded."},
    )
    replay = _run(claim_and_enqueue(
        completed,
        **_claim_and_enqueue_payload(),
    ))
    assert replay == {
        "outcome": "completed",
        "response_json": {"feedback": "Already recorded."},
    }

    conflict = _run(claim_and_enqueue(
        _EvaluationJobSession(),
        **_claim_and_enqueue_payload(answer_hash="different-answer-sha"),
    ))
    assert conflict == {"outcome": "conflict"}


def test_claim_and_enqueue_rolls_back_a_reclaimed_request_when_job_write_fails():
    claim_and_enqueue = getattr(repo, "claim_and_enqueue_school_evaluation_job", None)
    assert callable(claim_and_enqueue)

    session = _EvaluationJobSession()
    session.answer_requests[(SESSION_ID, ACTIVITY_ID)].update(status="failed")
    session.fail_next_job_insert = True

    with pytest.raises(RuntimeError, match="injected_school_evaluation_job_insert"):
        _run(claim_and_enqueue(session, **_claim_and_enqueue_payload()))

    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"
    assert session.jobs == {}
    assert session.rollbacks == 1


def test_in_memory_claim_and_enqueue_matches_atomic_claim_outcomes():
    store = InMemoryStore()
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
    }
    crashed_claim = _run(store.claim_school_answer_request(
        USER_ID,
        SESSION_ID,
        ACTIVITY_ID,
        ANSWER_HASH,
    ))
    claim_and_enqueue = getattr(store, "claim_and_enqueue_school_evaluation_job", None)
    assert callable(claim_and_enqueue)

    queued = _run(claim_and_enqueue(**_claim_and_enqueue_payload()))
    assert queued["outcome"] == "queued"
    assert queued["claim_token"] == crashed_claim["claim_token"]
    assert "raw_answer" not in queued["job"]
    assert store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)][
        "answer_claim_token"
    ] == crashed_claim["claim_token"]

    existing = _run(claim_and_enqueue(**_claim_and_enqueue_payload()))
    assert existing["outcome"] == "in_progress"
    assert existing["job"]["status"] == "queued"

    store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)].update(
        status="completed",
        response_json={"feedback": "Already recorded."},
    )
    replay = _run(claim_and_enqueue(**_claim_and_enqueue_payload()))
    assert replay == {
        "outcome": "completed",
        "response_json": {"feedback": "Already recorded."},
    }
    assert _run(claim_and_enqueue(
        **_claim_and_enqueue_payload(answer_hash="different-answer-sha")
    )) == {"outcome": "conflict"}


def test_schema_and_migration_define_one_to_one_server_only_evaluation_jobs():
    schema = _normalized((ROOT / "app/db/schema.sql").read_text())
    migration = _normalized(MIGRATION.read_text())

    for sql in (schema, migration):
        sql = sql.replace("public.", "")
        assert "CREATE TABLE IF NOT EXISTS school_evaluation_jobs" in sql
        assert "PRIMARY KEY (session_id, activity_id)" in sql
        assert (
            "FOREIGN KEY (session_id, activity_id) REFERENCES "
            "school_answer_requests(session_id, activity_id) ON DELETE CASCADE"
        ) in sql
        assert "raw_answer TEXT NOT NULL" in sql
        assert "expected_state_json JSONB NOT NULL" in sql
        assert "expected_state_digest TEXT NOT NULL" in sql
        assert "answer_claim_token TEXT NOT NULL" in sql
        assert "flow_type TEXT NOT NULL" in sql
        assert "evaluation_mode TEXT NOT NULL" in sql
        assert "CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled'))" in sql
        assert "attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0)" in sql
        assert "max_attempts INTEGER NOT NULL DEFAULT 3 CHECK (max_attempts > 0)" in sql
        assert "lease_owner TEXT" in sql
        assert "lease_token TEXT" in sql
        assert "lease_version INTEGER NOT NULL DEFAULT 0 CHECK (lease_version >= 0)" in sql
        assert "lease_expires_at TIMESTAMPTZ" in sql
        assert "last_error_code TEXT" in sql
        assert "error_json JSONB" in sql
        assert "response_json JSONB" in sql
        assert "result_data JSONB" in sql
        assert "cancelled_at TIMESTAMPTZ" in sql
        assert "ALTER TABLE school_evaluation_jobs ENABLE ROW LEVEL SECURITY" in sql
        assert "REVOKE ALL ON TABLE school_evaluation_jobs FROM anon" in sql
        assert "REVOKE ALL ON TABLE school_evaluation_jobs FROM authenticated" in sql

    migration_sql = _normalized(MIGRATION.read_text()).replace("public.", "")
    for token in (
        "ADD COLUMN IF NOT EXISTS max_attempts",
        "ADD COLUMN IF NOT EXISTS lease_owner",
        "ADD COLUMN IF NOT EXISTS lease_version",
        "ADD COLUMN IF NOT EXISTS error_json",
        "ADD COLUMN IF NOT EXISTS cancelled_at",
        "DROP CONSTRAINT IF EXISTS school_evaluation_jobs_status_check",
        "ADD CONSTRAINT school_evaluation_jobs_max_attempts_check",
        "ADD CONSTRAINT school_evaluation_jobs_lease_version_check",
    ):
        assert token in migration_sql

    assert MIGRATION.resolve() in {
        path.resolve() for path in apply_migrations.DEFAULT_MIGRATIONS
    }
    assert FK_REPAIR_MIGRATION.resolve() in {
        path.resolve() for path in apply_migrations.DEFAULT_MIGRATIONS
    }
    assert RETRY_SCHEDULE_MIGRATION.resolve() in {
        path.resolve() for path in apply_migrations.DEFAULT_MIGRATIONS
    }
    assert "app/db/migrations/2026-07-18-school-evaluation-jobs.sql" in (
        schema_guard.REQUIRED_MIGRATION_FILES
    )
    assert (
        "app/db/migrations/2026-07-18-school-evaluation-jobs-fk-repair.sql"
        in schema_guard.REQUIRED_MIGRATION_FILES
    )
    assert (
        "app/db/migrations/2026-07-19-school-evaluation-job-retry-schedule.sql"
        in schema_guard.REQUIRED_MIGRATION_FILES
    )
    assert REQUEST_METADATA_MIGRATION.resolve() in {
        path.resolve() for path in apply_migrations.DEFAULT_MIGRATIONS
    }
    assert (
        "app/db/migrations/2026-07-19-school-evaluation-job-request-metadata.sql"
        in schema_guard.REQUIRED_MIGRATION_FILES
    )
    assert "school_evaluation_jobs" in schema_guard.REQUIRED_RUNTIME_COLUMNS
    assert (
        "school_evaluation_jobs",
        ("session_id", "activity_id"),
        "school_answer_requests",
        ("session_id", "activity_id"),
    ) in schema_guard.REQUIRED_RUNTIME_COMPOSITE_FOREIGN_KEYS


def test_evaluation_job_fk_repair_is_idempotent_and_fails_closed_on_orphans():
    sql = _normalized(FK_REPAIR_MIGRATION.read_text()).replace("public.", "")

    assert "LEFT JOIN school_answer_requests AS request" in sql
    assert "school_evaluation_jobs_answer_request_fk_repair_blocked:orphan_job" in sql
    # The PL/pgSQL loop target is `constraint_row`. The SQL relation alias
    # must remain distinct or PostgreSQL treats it as an unassigned record.
    assert "FOR constraint_row IN SELECT foreign_key.conname" in sql
    assert "FROM pg_constraint AS foreign_key" in sql
    assert "foreign_key.conkey = ARRAY[job_session_attnum, job_activity_attnum]" in sql
    assert (
        "foreign_key.confkey = ARRAY[ request_session_attnum, request_activity_attnum ]"
        in sql
    )
    assert "ADD CONSTRAINT school_evaluation_jobs_answer_request_fkey" in sql
    assert "foreign_key.confdeltype <> 'c'" in sql
    assert "DROP CONSTRAINT %I" in sql
    assert "EXECUTE format" in sql
    assert (
        "FOREIGN KEY (session_id, activity_id) REFERENCES "
        "school_answer_requests(session_id, activity_id) ON DELETE CASCADE"
    ) in sql


def test_retry_schedule_is_durable_and_claimable_indexed():
    schema = _normalized((ROOT / "app/db/schema.sql").read_text())
    migration = _normalized(RETRY_SCHEDULE_MIGRATION.read_text())

    assert "next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now()" in schema
    assert "status, next_attempt_at, lease_expires_at, created_at" in schema
    assert "ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ" in migration
    assert "SET DEFAULT now()" in migration
    assert "SET NOT NULL" in migration
    assert "next_attempt_at" in schema_guard.REQUIRED_RUNTIME_COLUMNS[
        "school_evaluation_jobs"
    ]


def test_request_metadata_schema_is_additive_and_runtime_guarded():
    schema = _normalized((ROOT / "app/db/schema.sql").read_text())
    migration = _normalized(REQUEST_METADATA_MIGRATION.read_text())

    assert "request_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb" in schema
    assert "school_evaluation_jobs_request_metadata_object" in schema
    assert "jsonb_typeof(request_metadata_json) = 'object'" in schema
    assert "ADD COLUMN IF NOT EXISTS request_metadata_json JSONB" in migration
    assert "school_evaluation_jobs_request_metadata_object" in migration
    assert "SET DEFAULT '{}'::jsonb" in migration
    assert "SET NOT NULL" in migration
    assert "request_metadata_json" in schema_guard.REQUIRED_RUNTIME_COLUMNS[
        "school_evaluation_jobs"
    ]
    assert (
        "school_evaluation_jobs",
        "school_evaluation_jobs_request_metadata_object",
    ) in schema_guard.REQUIRED_RUNTIME_CHECKS


def test_enqueue_creates_one_job_only_after_the_matching_answer_claim():
    session = _EvaluationJobSession()

    created = _enqueue(session)
    replay = _enqueue(session)

    assert created["outcome"] == "queued"
    assert replay["outcome"] == "existing"
    assert len(session.jobs) == 1
    job = created["job"]
    assert job["raw_answer"] == "Because the character used evidence from the chapter."
    assert job["expected_state_json"] == {
        "chapter_id": "eng_c3_ch01",
        "current_activity_id": ACTIVITY_ID,
    }
    assert job["expected_state_digest"] == hashlib.sha256(
        json.dumps(job["expected_state_json"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert job["answer_claim_token"] == ANSWER_CLAIM_TOKEN
    assert job["status"] == "queued"
    assert "lease_is_active" not in replay["job"]
    assert session.commits == 2

    answer_claim_sql = next(
        sql for sql, _ in session.calls if "FROM school_answer_requests" in sql
    )
    assert "status = 'processing'" in answer_claim_sql
    assert "answer_hash = :answer_hash" in answer_claim_sql
    assert "claim_token = :answer_claim_token" in answer_claim_sql
    assert "user_id = :uid" in answer_claim_sql
    assert "FOR UPDATE" in answer_claim_sql
    assert any("pg_advisory_xact_lock" in sql for sql, _ in session.calls)


def test_enqueue_never_rewrites_an_existing_claim_payload():
    session = _EvaluationJobSession()
    created = _enqueue(session)

    conflicting_replay = _enqueue(
        session,
        raw_answer="A replacement answer must never overwrite the job.",
    )

    assert created["outcome"] == "queued"
    assert conflicting_replay == {"outcome": "conflict"}
    stored = session.jobs[(SESSION_ID, ACTIVITY_ID)]
    assert stored["raw_answer"] == "Because the character used evidence from the chapter."
    assert stored["answer_claim_token"] == ANSWER_CLAIM_TOKEN


def test_request_metadata_round_trips_to_the_claimed_job_but_not_public_status():
    session = _EvaluationJobSession()
    metadata = _request_metadata()

    queued = _enqueue(session, request_metadata=metadata)
    claimed = _claim(session)
    status = _run(repo.get_school_evaluation_job_status(
        session, USER_ID, SESSION_ID, ACTIVITY_ID
    ))

    assert queued["job"]["request_metadata_json"] == metadata
    assert claimed is not None
    assert claimed["request_metadata_json"] == metadata
    assert status is not None
    assert "request_metadata_json" not in status


def test_request_metadata_mismatch_conflicts_for_both_enqueue_paths():
    direct_session = _EvaluationJobSession()
    assert _enqueue(
        direct_session,
        request_metadata=_request_metadata(arrival_id="arrival-a"),
    )["outcome"] == "queued"
    assert _enqueue(
        direct_session,
        request_metadata=_request_metadata(arrival_id="arrival-b"),
    ) == {"outcome": "conflict"}

    atomic_session = _EvaluationJobSession()
    assert _run(repo.claim_and_enqueue_school_evaluation_job(
        atomic_session,
        **_claim_and_enqueue_payload(
            request_metadata=_request_metadata(arrival_id="arrival-a"),
        ),
    ))["outcome"] == "queued"
    assert _run(repo.claim_and_enqueue_school_evaluation_job(
        atomic_session,
        **_claim_and_enqueue_payload(
            request_metadata=_request_metadata(arrival_id="arrival-b"),
        ),
    )) == {"outcome": "conflict"}


@pytest.mark.parametrize("terminal_status", ["failed", "cancelled"])
def test_reenqueue_terminal_job_replaces_request_metadata(terminal_status: str):
    session = _EvaluationJobSession()
    original_metadata = _request_metadata(arrival_id="arrival-old")
    replacement_metadata = _request_metadata(arrival_id="arrival-new")
    _enqueue(session, request_metadata=original_metadata)
    session.jobs[(SESSION_ID, ACTIVITY_ID)].update(status=terminal_status)

    requeued = _enqueue(session, request_metadata=replacement_metadata)

    assert requeued["outcome"] == "queued"
    assert requeued["job"]["status"] == "queued"
    assert requeued["job"]["request_metadata_json"] == replacement_metadata
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["request_metadata_json"] == (
        replacement_metadata
    )


@pytest.mark.parametrize("request_metadata", [[], "not-an-object", 1])
def test_enqueue_rejects_non_object_request_metadata(request_metadata):
    with pytest.raises(ValueError, match="invalid_school_evaluation_job_request_metadata"):
        _enqueue(_EvaluationJobSession(), request_metadata=request_metadata)


def test_new_claim_replaces_only_a_terminal_job_and_preserves_lease_generation():
    session = _EvaluationJobSession()
    _enqueue(session)
    claimed = _claim(session)
    assert claimed is not None

    failed = _run(repo.fail_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        last_error_code="provider_timeout",
        error_json={"retryable": False},
    ))
    assert failed is not None
    assert failed["status"] == "failed"

    next_answer_hash = "next-answer-sha"
    next_claim_token = "next-answer-claim-token"
    session.answer_requests[(SESSION_ID, ACTIVITY_ID)].update(
        answer_hash=next_answer_hash,
        claim_token=next_claim_token,
        status="processing",
    )
    replacement = _enqueue(
        session,
        raw_answer="A later claimed answer.",
        expected_state_json={"current_activity_id": ACTIVITY_ID, "revision": 2},
        answer_hash=next_answer_hash,
        answer_claim_token=next_claim_token,
    )

    assert replacement["outcome"] == "queued"
    assert replacement["job"]["answer_hash"] == next_answer_hash
    assert replacement["job"]["answer_claim_token"] == next_claim_token
    assert replacement["job"]["status"] == "queued"
    assert replacement["job"]["attempts"] == 0
    assert replacement["job"]["lease_version"] == claimed["lease_version"]
    assert replacement["job"]["error_json"] is None
    assert replacement["job"]["response_json"] is None
    assert replacement["job"]["result_data"] is None


def test_atomic_enqueue_replaces_a_failed_request_with_a_new_answer_claim():
    session = _EvaluationJobSession()
    original = _run(repo.claim_and_enqueue_school_evaluation_job(
        session,
        **_claim_and_enqueue_payload(),
    ))
    assert original["outcome"] == "queued"

    session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] = "failed"
    session.jobs[(SESSION_ID, ACTIVITY_ID)]["status"] = "failed"

    replacement = _run(repo.claim_and_enqueue_school_evaluation_job(
        session,
        **_claim_and_enqueue_payload(
            raw_answer="A new answer after the evaluator failed.",
            answer_hash="replacement-answer-sha",
        ),
    ))

    assert replacement["outcome"] == "queued"
    assert replacement["claim_token"] != original["claim_token"]
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["answer_hash"] == (
        "replacement-answer-sha"
    )
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "processing"
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["answer_hash"] == (
        "replacement-answer-sha"
    )


def test_claim_uses_a_concrete_default_worker_identity():
    session = _EvaluationJobSession()
    _enqueue(session)

    claimed = _run(repo.claim_school_evaluation_job(session))

    assert claimed is not None
    assert claimed["lease_owner"] == "school-evaluation-worker"
    assert claimed["lease_token"]
    assert claimed["lease_version"] == 1


def test_get_job_is_duplicate_safe_and_never_returns_another_users_payload():
    session = _EvaluationJobSession()
    _enqueue(session)

    first = _run(repo.get_school_evaluation_job(
        session, USER_ID, SESSION_ID, ACTIVITY_ID
    ))
    second = _run(repo.get_school_evaluation_job(
        session, USER_ID, SESSION_ID, ACTIVITY_ID
    ))
    foreign = _run(repo.get_school_evaluation_job(
        session, "learner-2", SESSION_ID, ACTIVITY_ID
    ))

    assert first == second
    assert first["raw_answer"] == "Because the character used evidence from the chapter."
    assert foreign is None
    assert len(session.jobs) == 1
    read_sql = [sql for sql, _ in session.calls if "FROM school_evaluation_jobs" in sql][-1]
    assert "user_id = :uid" in read_sql


def test_public_job_status_never_selects_or_returns_answer_payload():
    session = _EvaluationJobSession()
    _enqueue(session)

    status = _run(repo.get_school_evaluation_job_status(
        session, USER_ID, SESSION_ID, ACTIVITY_ID
    ))

    assert status is not None
    assert status["status"] == "queued"
    assert "raw_answer" not in status
    assert "expected_state_json" not in status
    assert "answer_hash" not in status
    assert "answer_claim_token" not in status
    assert "lease_token" not in status
    status_sql = [
        sql for sql, _ in session.calls if "FROM school_evaluation_jobs" in sql
    ][-1]
    assert "raw_answer" not in status_sql
    assert "expected_state_json" not in status_sql


def test_retry_requeues_only_the_current_running_lease_with_attempts_remaining():
    session = _EvaluationJobSession()
    _enqueue(session, max_attempts=2)
    first = _claim(session)
    assert first is not None

    assert _run(repo.retry_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner="other-worker",
        lease_token=first["lease_token"],
        lease_version=first["lease_version"],
        last_error_code="provider_timeout",
    )) is None

    retried = _run(repo.retry_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=first["lease_owner"],
        lease_token=first["lease_token"],
        lease_version=first["lease_version"],
        last_error_code="provider_timeout",
        error_json={"retryable": True},
    ))
    assert retried is not None
    assert retried["status"] == "queued"
    assert retried["attempts"] == 1
    assert retried["lease_token"] is None
    assert retried["last_error_code"] == "provider_timeout"
    assert retried["error_json"] == {"retryable": True}

    final_attempt = _claim(session, lease_owner="worker-b")
    assert final_attempt is not None
    assert final_attempt["attempts"] == 2
    assert _run(repo.retry_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=final_attempt["lease_owner"],
        lease_token=final_attempt["lease_token"],
        lease_version=final_attempt["lease_version"],
        last_error_code="provider_timeout",
        error_json={"retryable": True},
    )) is None

    retry_sql = [sql for sql, _ in session.calls if "SET status = 'queued'" in sql][-1]
    for predicate in (
        "lease_owner = :lease_owner",
        "lease_token = :lease_token",
        "lease_version = :lease_version",
        "status = 'running'",
        "lease_expires_at > now()",
    ):
        assert predicate in retry_sql


def test_enqueue_resets_a_terminal_job_for_a_new_answer_claim():
    session = _EvaluationJobSession()
    _enqueue(session)
    first = _claim(session)
    assert first is not None
    assert _run(repo.fail_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=first["lease_owner"],
        lease_token=first["lease_token"],
        lease_version=first["lease_version"],
        last_error_code="provider_timeout",
    )) is not None

    next_answer_hash = "answer-sha-retry"
    next_claim_token = "answer-claim-token-retry"
    session.answer_requests[(SESSION_ID, ACTIVITY_ID)].update(
        answer_hash=next_answer_hash,
        claim_token=next_claim_token,
        status="processing",
    )
    reset = _enqueue(
        session,
        raw_answer="A replacement answer after a terminal evaluator failure.",
        answer_hash=next_answer_hash,
        answer_claim_token=next_claim_token,
        max_attempts=2,
    )

    assert reset["outcome"] == "queued"
    assert reset["job"]["status"] == "queued"
    assert reset["job"]["answer_hash"] == next_answer_hash
    assert reset["job"]["answer_claim_token"] == next_claim_token
    assert reset["job"]["attempts"] == 0
    assert reset["job"]["lease_token"] is None
    assert reset["job"]["response_json"] is None
    assert reset["job"]["result_data"] is None


def test_cancelled_job_clears_its_lease_and_cannot_be_claimed_or_finalized_again():
    session = _EvaluationJobSession()
    _enqueue(session)

    cancelled = _run(repo.cancel_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        error_json={"reason": "session_cancelled"},
    ))
    assert cancelled is not None
    assert cancelled["status"] == "cancelled"
    assert cancelled["cancelled_at"] == "cancelled"
    assert cancelled["raw_answer"] == "Because the character used evidence from the chapter."
    assert _claim(session) is None
    assert _run(repo.cancel_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
    )) is None


def test_in_memory_store_matches_job_claim_fencing_and_safe_status_contract():
    store = InMemoryStore()
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
    }
    answer_claim = _run(store.claim_school_answer_request(
        USER_ID,
        SESSION_ID,
        ACTIVITY_ID,
        ANSWER_HASH,
    ))
    assert answer_claim["outcome"] == "claimed"

    queued = _run(store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        raw_answer="The learner's private answer.",
        expected_state_json={"current_activity_id": ACTIVITY_ID},
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        flow_type="curriculum",
        evaluation_mode="open_answer",
        max_attempts=2,
        request_metadata=_request_metadata(),
    ))
    assert queued["outcome"] == "queued"

    claimed = _run(store.claim_school_evaluation_job("in-memory-worker", lease_seconds=45))
    assert claimed is not None
    assert claimed["request_metadata_json"] == _request_metadata()
    assert _run(store.heartbeat_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        lease_seconds=45,
    )) is True

    public_status = _run(store.get_school_evaluation_job_status(
        USER_ID, SESSION_ID, ACTIVITY_ID
    ))
    assert public_status is not None
    assert public_status["status"] == "running"
    assert "raw_answer" not in public_status
    assert "request_metadata_json" not in public_status
    assert "answer_claim_token" not in public_status
    assert _run(store.complete_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        response_json={"feedback": "Recorded."},
        result_data={"score": 0.9},
    )) is not None
    assert _run(store.complete_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        response_json={"feedback": "Duplicate."},
        result_data={"score": 1.0},
    )) is None


def test_in_memory_retry_does_not_claim_before_next_attempt_at():
    store = InMemoryStore()
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
    }
    answer_claim = _run(store.claim_school_answer_request(
        USER_ID,
        SESSION_ID,
        ACTIVITY_ID,
        ANSWER_HASH,
    ))
    _run(store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        raw_answer="The learner's private answer.",
        expected_state_json={"current_activity_id": ACTIVITY_ID},
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        flow_type="curriculum",
        evaluation_mode="open_answer",
        max_attempts=2,
    ))
    claimed = _run(store.claim_school_evaluation_job("in-memory-worker"))
    assert claimed is not None

    retried = _run(store.retry_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        last_error_code="provider_timeout",
        retry_after_seconds=60,
    ))
    assert retried is not None
    assert retried["next_attempt_at"] > time.time()
    assert _run(store.claim_school_evaluation_job("in-memory-worker")) is None

    store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)]["next_attempt_at"] = (
        time.time() - 1
    )
    assert _run(store.claim_school_evaluation_job("in-memory-worker")) is not None


def test_pg_store_exposes_and_delegates_the_safe_job_status_read():
    for method_name in (
        "enqueue_school_evaluation_job",
        "claim_and_enqueue_school_evaluation_job",
        "get_school_evaluation_job",
        "get_school_evaluation_job_status",
        "claim_school_evaluation_job",
        "heartbeat_school_evaluation_job",
        "terminalize_school_evaluation_job",
        "complete_school_evaluation_job",
        "fail_school_evaluation_job",
        "retry_school_evaluation_job",
        "cancel_school_evaluation_job",
    ):
        assert callable(getattr(pg_store.PgStore, method_name, None))

    marker = object()

    @asynccontextmanager
    async def fake_session():
        yield marker

    async def fake_get_status(session, user_id, session_id, activity_id):
        assert session is marker
        assert (user_id, session_id, activity_id) == (USER_ID, SESSION_ID, ACTIVITY_ID)
        return {"status": "queued", "attempts": 0, "max_attempts": 3}

    original_session = pg_store._session
    original_get_status = repo.get_school_evaluation_job_status
    pg_store._session = fake_session
    repo.get_school_evaluation_job_status = fake_get_status
    try:
        status = _run(pg_store.PgStore().get_school_evaluation_job_status(
            USER_ID, SESSION_ID, ACTIVITY_ID
        ))
    finally:
        pg_store._session = original_session
        repo.get_school_evaluation_job_status = original_get_status

    assert status == {"status": "queued", "attempts": 0, "max_attempts": 3}


def test_stale_lease_reclaim_fences_old_worker_completion():
    session = _EvaluationJobSession()
    _enqueue(session)

    first = _claim(session)
    assert first is not None
    first_lease_token = first["lease_token"]
    first_lease_version = first["lease_version"]
    assert first["attempts"] == 1
    assert first["lease_owner"] == "worker-a"

    session.jobs[(SESSION_ID, ACTIVITY_ID)]["lease_expires_at"] = "expired"
    reclaimed = _claim(session, lease_owner="worker-b")
    assert reclaimed is not None
    assert reclaimed["attempts"] == 2
    assert reclaimed["lease_token"] != first_lease_token
    assert reclaimed["lease_owner"] == "worker-b"
    assert reclaimed["lease_version"] == first_lease_version + 1

    assert _complete(
        session,
        lease_owner="worker-a",
        lease_token=first_lease_token,
        lease_version=first_lease_version,
    ) is None
    completed = _complete(
        session,
        lease_owner="worker-b",
        lease_token=reclaimed["lease_token"],
        lease_version=reclaimed["lease_version"],
    )
    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["result_data"] == {"score": 0.8, "passed": True}
    assert _complete(
        session,
        lease_owner="worker-b",
        lease_token=reclaimed["lease_token"],
        lease_version=reclaimed["lease_version"],
    ) is None

    claim_sql = next(
        sql
        for sql, _ in session.calls
        if sql.startswith("WITH candidate AS")
    )
    assert "FOR UPDATE SKIP LOCKED" in claim_sql
    assert "status = 'queued'" in claim_sql
    assert "lease_expires_at <= now()" in claim_sql
    completion_sql = next(
        sql for sql, _ in session.calls if "SET status = 'completed'" in sql
    )
    for predicate in (
        "user_id = :uid",
        "answer_hash = :answer_hash",
        "answer_claim_token = :answer_claim_token",
        "lease_owner = :lease_owner",
        "lease_token = :lease_token",
        "lease_version = :lease_version",
        "lease_expires_at > now()",
    ):
        assert predicate in completion_sql


def test_heartbeat_fail_and_completion_reject_mismatched_identity_or_lease():
    session = _EvaluationJobSession()
    _enqueue(session)
    claimed = _claim(session)
    assert claimed is not None

    assert _run(repo.heartbeat_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        lease_seconds=45,
    )) is True
    assert _complete(
        session,
        user_id="learner-2",
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
    ) is None
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "running"

    failed = _run(repo.fail_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        last_error_code="evaluation_timeout",
        error_json={"retryable": True},
        response_json={"visible_feedback": "Try again."},
        result_data={"retryable": True},
    ))
    assert failed is not None
    assert failed["status"] == "failed"
    assert failed["last_error_code"] == "evaluation_timeout"
    assert failed["error_json"] == {"retryable": True}

    heartbeat_sql = next(
        sql for sql, _ in session.calls if "SET lease_expires_at" in sql
    )
    failure_sql = next(
        sql
        for sql, _ in session.calls
        if sql.startswith("UPDATE school_evaluation_jobs")
        and "SET status = 'failed'" in sql
    )
    for sql in (heartbeat_sql, failure_sql):
        for predicate in (
            "user_id = :uid",
            "answer_hash = :answer_hash",
            "answer_claim_token = :answer_claim_token",
            "lease_owner = :lease_owner",
            "lease_token = :lease_token",
            "lease_version = :lease_version",
            "lease_expires_at > now()",
        ):
            assert predicate in sql


def test_fenced_heartbeat_renews_only_its_matching_processing_request():
    session = _EvaluationJobSession()
    _enqueue(session)
    claimed = _claim(session)
    assert claimed is not None

    request = session.answer_requests[(SESSION_ID, ACTIVITY_ID)]
    request["updated_at"] = "stale-before-heartbeat"
    assert _run(repo.heartbeat_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        lease_seconds=45,
    )) is True
    assert request["updated_at"] == "heartbeated"

    session.jobs[(SESSION_ID, ACTIVITY_ID)]["lease_expires_at"] = "expired"
    request["updated_at"] = "stale-after-lost-lease"
    assert _run(repo.heartbeat_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        lease_seconds=45,
    )) is False
    assert request["updated_at"] == "stale-after-lost-lease"

    heartbeat_sql = [
        sql for sql, _ in session.calls if "SET lease_expires_at" in sql
    ][-1]
    assert "FOR UPDATE" in heartbeat_sql
    assert "UPDATE school_answer_requests AS request" in heartbeat_sql
    assert "SET updated_at = now()" in heartbeat_sql
    assert "raw_answer" not in heartbeat_sql


def test_in_memory_heartbeat_keeps_processing_request_non_stale_and_rejects_lost_lease():
    store = InMemoryStore()
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
    }
    answer_claim = _run(store.claim_school_answer_request(
        USER_ID,
        SESSION_ID,
        ACTIVITY_ID,
        ANSWER_HASH,
    ))
    _run(store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        raw_answer="The learner's private answer.",
        expected_state_json={"current_activity_id": ACTIVITY_ID},
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        flow_type="curriculum",
        evaluation_mode="open_answer",
    ))
    claimed = _run(store.claim_school_evaluation_job("in-memory-worker", lease_seconds=45))
    assert claimed is not None

    request = store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)]
    request["updated_at"] = time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    assert _run(store.get_school_answer_request(
        USER_ID, SESSION_ID, ACTIVITY_ID
    ))["stale"] is True
    assert _run(store.heartbeat_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        lease_seconds=45,
    )) is True
    assert _run(store.get_school_answer_request(
        USER_ID, SESSION_ID, ACTIVITY_ID
    ))["stale"] is False

    request["updated_at"] = time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    store.school_evaluation_jobs[(SESSION_ID, ACTIVITY_ID)]["lease_expires_at"] = (
        time.time() - 1
    )
    assert _run(store.heartbeat_school_evaluation_job(
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=answer_claim["claim_token"],
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        lease_seconds=45,
    )) is False
    assert _run(store.get_school_answer_request(
        USER_ID, SESSION_ID, ACTIVITY_ID
    ))["stale"] is True


def test_in_memory_school_state_snapshot_matches_processing_request_staleness():
    store = InMemoryStore()
    now = time.time()
    profile_version_id = "profile-v1"
    report_id = "report-v1"
    store.school_profile_versions[(USER_ID, profile_version_id)] = {
        "user_id": USER_ID,
        "profile_version_id": profile_version_id,
        "status": "active",
        "subject_ids": ["english"],
        "target_class_no": 5,
        "updated_at": now,
    }
    store.school_placement_reports[(USER_ID, report_id)] = {
        "user_id": USER_ID,
        "report_id": report_id,
        "profile_version_id": profile_version_id,
        "subject_id": "english",
        "target_class_no": 5,
        "updated_at": now,
    }
    store.school_sessions[(USER_ID, SESSION_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "api_version": "rebuild",
        "profile_version_id": profile_version_id,
        "subject_id": "english",
        "class_no": 5,
        "flow_type": "curriculum",
        "status": "active",
        "source_placement_report_id": report_id,
        "updated_at": now,
    }
    store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)] = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "activity_id": ACTIVITY_ID,
        "answer_hash": ANSWER_HASH,
        "claim_token": ANSWER_CLAIM_TOKEN,
        "status": "processing",
        "response_json": None,
        "updated_at": now - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1,
    }

    stale_snapshot = _run(store.get_school_state_snapshot(USER_ID))
    stale_request = stale_snapshot["processing_answer_requests"][0]
    assert stale_request["age_seconds"] >= store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS
    assert stale_request["stale"] is True

    store.school_answer_requests[(SESSION_ID, ACTIVITY_ID)]["updated_at"] = time.time()
    fresh_snapshot = _run(store.get_school_state_snapshot(USER_ID))
    fresh_request = fresh_snapshot["processing_answer_requests"][0]
    assert fresh_request["age_seconds"] < store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS
    assert fresh_request["stale"] is False


def test_expired_final_attempt_gets_one_fenced_recovery_then_releases_request():
    session = _EvaluationJobSession()
    _enqueue(session, max_attempts=1)
    final_attempt = _claim(session)
    assert final_attempt is not None
    session.jobs[(SESSION_ID, ACTIVITY_ID)]["lease_expires_at"] = "expired"

    recovery = _claim(session, lease_owner="worker-recovery")
    assert recovery is not None
    assert recovery["attempts"] == 2
    assert recovery["lease_version"] == final_attempt["lease_version"] + 1
    assert recovery["lease_token"] != final_attempt["lease_token"]
    assert _complete(
        session,
        lease_owner=final_attempt["lease_owner"],
        lease_token=final_attempt["lease_token"],
        lease_version=final_attempt["lease_version"],
    ) is None

    session.jobs[(SESSION_ID, ACTIVITY_ID)]["lease_expires_at"] = "expired"
    assert _claim(session, lease_owner="worker-after-recovery") is None
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["lease_owner"] is None
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["lease_token"] is None
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"

    claim_sql = next(
        sql
        for sql, _ in session.calls
        if sql.startswith("WITH candidate AS")
    )
    assert "job.attempts <= job.max_attempts" in claim_sql
    terminal_sql = next(
        sql for sql, _ in session.calls if "evaluation_recovery_lease_expired" in sql
    )
    assert "UPDATE school_answer_requests AS request" in terminal_sql
    assert "FOR UPDATE OF request SKIP LOCKED" in terminal_sql
    assert "FOR UPDATE OF job SKIP LOCKED" in terminal_sql
    assert terminal_sql.index("FOR UPDATE OF request SKIP LOCKED") < (
        terminal_sql.index("FOR UPDATE OF job SKIP LOCKED")
    )


def test_evaluation_job_deadline_terminalizes_and_releases_the_processing_request():
    session = _EvaluationJobSession()
    _enqueue(session)
    session.jobs[(SESSION_ID, ACTIVITY_ID)]["created_at"] = "deadline-expired"

    assert _claim(session) is None
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["last_error_code"] == (
        "evaluation_deadline_exceeded"
    )
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"

    deadline_sql = next(
        sql for sql, _ in session.calls if "evaluation_deadline_exceeded" in sql
    )
    assert "job.created_at <= now()" in deadline_sql
    assert "deadline_seconds" in deadline_sql


def test_terminalize_fenced_job_releases_the_exact_processing_request_atomically():
    terminalize = getattr(repo, "terminalize_school_evaluation_job", None)
    assert callable(terminalize)

    session = _EvaluationJobSession()
    _enqueue(session)
    claimed = _claim(session)
    assert claimed is not None

    assert _run(terminalize(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token="lost-lease-token",
        lease_version=claimed["lease_version"],
        last_error_code="evaluation_runner_stopped",
    )) is None
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "running"
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "processing"

    commits_before_terminalization = session.commits
    terminalized = _run(terminalize(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        last_error_code="evaluation_runner_stopped",
        error_json={"reason": "runner_stopped"},
    ))
    assert terminalized is not None
    assert terminalized["status"] == "failed"
    assert terminalized["lease_owner"] is None
    assert terminalized["lease_token"] is None
    assert session.commits == commits_before_terminalization + 1
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["status"] == "failed"
    assert session.answer_requests[(SESSION_ID, ACTIVITY_ID)]["response_json"] is None
    assert _complete(
        session,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
    ) is None

    terminal_sql = [
        sql
        for sql, _ in session.calls
        if "terminalized_job AS" in sql and "released_request AS" in sql
    ][-1]
    assert "FOR UPDATE" in terminal_sql
    assert "UPDATE school_evaluation_jobs AS job" in terminal_sql
    assert "locked_placement_session AS" in terminal_sql
    assert "patched_placement_session AS" in terminal_sql
    assert "school_session.api_version = 'rebuild'" in terminal_sql
    assert "school_session.flow_type = 'placement'" in terminal_sql
    assert "job.flow_type = 'placement'" in terminal_sql
    assert "state_json #>> '{_placement_item_timing,item_id}' = :activity_id" in terminal_sql
    assert "UPDATE school_answer_requests AS request" in terminal_sql
    assert "raw_answer" not in terminal_sql

    terminalized_job_cte = terminal_sql.split("terminalized_job AS (", 1)[1].split(
        "), released_request AS", 1
    )[0]
    returned_job_fields = terminalized_job_cte.split("RETURNING", 1)[1]
    assert "job.user_id" in returned_job_fields
    assert "job.answer_hash" in returned_job_fields
    assert "job.answer_claim_token" in returned_job_fields


def test_terminalization_types_nullable_placement_timing_for_curriculum_jobs():
    """A curriculum job has no placement timing, so its NULL parameter is JSONB."""
    session = _EvaluationJobSession()
    _enqueue(session)
    claimed = _claim(session)
    assert claimed is not None

    terminalized = _run(repo.terminalize_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
        last_error_code="school_open_provider_failure",
    ))

    assert terminalized is not None
    terminal_sql = [
        sql
        for sql, _ in session.calls
        if "terminalized_job AS" in sql and "released_request AS" in sql
    ][-1]
    assert ":placement_retry_timing IS NULL" not in terminal_sql
    assert ":placement_retry_timing IS NOT NULL" not in terminal_sql
    assert "CAST(:placement_retry_timing AS jsonb) IS NULL" in terminal_sql
    assert "CAST(:placement_retry_timing AS jsonb) IS NOT NULL" in terminal_sql


def test_running_cancellation_requires_the_current_lease_fence():
    session = _EvaluationJobSession()
    _enqueue(session)
    claimed = _claim(session)
    assert claimed is not None

    assert _run(repo.cancel_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
    )) is None
    assert session.jobs[(SESSION_ID, ACTIVITY_ID)]["status"] == "running"

    assert _run(repo.cancel_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token="lost-lease-token",
        lease_version=claimed["lease_version"],
    )) is None

    cancelled = _run(repo.cancel_school_evaluation_job(
        session,
        user_id=USER_ID,
        session_id=SESSION_ID,
        activity_id=ACTIVITY_ID,
        answer_hash=ANSWER_HASH,
        answer_claim_token=ANSWER_CLAIM_TOKEN,
        lease_owner=claimed["lease_owner"],
        lease_token=claimed["lease_token"],
        lease_version=claimed["lease_version"],
    ))
    assert cancelled is not None
    assert cancelled["status"] == "cancelled"

    cancellation_sql = [
        sql for sql, _ in session.calls if "SET status = 'cancelled'" in sql
    ][-1]
    for predicate in (
        "lease_owner = :lease_owner",
        "lease_token = :lease_token",
        "lease_version = :lease_version",
        "lease_expires_at > now()",
    ):
        assert predicate in cancellation_sql
