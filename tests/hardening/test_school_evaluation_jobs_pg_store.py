from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from app.db import repo
from app.storage import pg_store
from app.api import school_rebuild_routes
from app.services import school_rebuild_curriculum as curriculum


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
        "claim_and_enqueue_school_evaluation_job_atomic",
        "claim_school_evaluation_job",
        "heartbeat_school_evaluation_job",
        "terminalize_school_evaluation_job",
        "complete_school_evaluation_job",
        "fail_school_evaluation_job",
        "retry_school_evaluation_job",
        "cancel_school_evaluation_job",
        "persist_school_curriculum_attempt",
        "persist_school_evaluated_curriculum_attempt",
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
            request_metadata={"answer_arrival": {"arrival_id": "arrival-1"}},
        )
        await store.claim_and_enqueue_school_evaluation_job_atomic(
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            raw_answer="Private learner answer.",
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            answer_hash=ANSWER_HASH,
            flow_type="curriculum",
            evaluation_mode="open_answer",
            max_attempts=2,
            request_metadata={"answer_arrival": {"arrival_id": "arrival-1"}},
        )
        await store.claim_school_evaluation_job(LEASE_OWNER, lease_seconds=45)
        await store.heartbeat_school_evaluation_job(**identity, lease_seconds=45)
        await store.terminalize_school_evaluation_job(
            **identity,
            last_error_code="placement_english_response_required",
            error_json={"error_code": "placement_english_response_required"},
            placement_retry_timing={
                "item_id": ACTIVITY_ID,
                "retry_pending": True,
                "accrued_learner_seconds": 12.5,
                "presented_at": "2026-07-19T09:00:00+00:00",
            },
        )
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
        await store.persist_school_evaluated_curriculum_attempt(**attempt)
        await store.persist_school_answer_attempt(**attempt)

    asyncio.run(exercise())

    assert [name for name, *_ in calls] == list(method_names)
    assert all(db_session is session for _, db_session, _, _ in calls)
    forwarded = {name: kwargs for name, _, _, kwargs in calls}
    assert forwarded["claim_school_evaluation_job"] == {
        "lease_owner": LEASE_OWNER,
        "lease_seconds": 45,
    }
    assert forwarded["enqueue_school_evaluation_job"]["request_metadata"] == {
        "answer_arrival": {"arrival_id": "arrival-1"}
    }
    assert forwarded["claim_and_enqueue_school_evaluation_job_atomic"]["request_metadata"] == {
        "answer_arrival": {"arrival_id": "arrival-1"}
    }
    assert forwarded["terminalize_school_evaluation_job"] == {
        **identity,
        "last_error_code": "placement_english_response_required",
        "error_json": {"error_code": "placement_english_response_required"},
        "placement_retry_timing": {
            "item_id": ACTIVITY_ID,
            "retry_pending": True,
            "accrued_learner_seconds": 12.5,
            "presented_at": "2026-07-19T09:00:00+00:00",
        },
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
    assert forwarded["persist_school_evaluated_curriculum_attempt"][
        "evaluation_job_completion"
    ] == forwarded["persist_school_answer_attempt"]["evaluation_job_completion"]


def test_atomic_evaluation_enqueue_uses_one_locked_mutation_and_returns_queue_metadata():
    """A queued answer must not spend serial India-Supabase round trips before 202."""

    class _Result:
        def __init__(self, row):
            self.row = row

        def mappings(self):
            return self

        def first(self):
            return self.row

    class _Session:
        def __init__(self):
            self.calls: list[tuple[object, dict]] = []
            self.commits = 0
            self.rollbacks = 0

        async def execute(self, statement, params):
            self.calls.append((statement, params))
            return _Result({
                "outcome": "queued",
                "claim_token": ANSWER_CLAIM_TOKEN,
                "response_json": None,
                "queue_session_id": SESSION_ID,
                "queue_activity_id": ACTIVITY_ID,
                "queue_status": "queued",
                "queue_attempts": 0,
                "queue_max_attempts": 2,
                "queue_lease_version": 0,
                "queue_lease_expires_at": None,
                "queue_next_attempt_at": None,
                "queue_last_error_code": None,
                "queue_error_json": None,
                "queue_created_at": None,
                "queue_updated_at": None,
                "queue_started_at": None,
                "queue_completed_at": None,
                "queue_failed_at": None,
                "queue_cancelled_at": None,
            })

        async def commit(self):
            self.commits += 1

        async def rollback(self):
            self.rollbacks += 1

    async def exercise():
        session = _Session()
        result = await repo.claim_and_enqueue_school_evaluation_job_atomic(
            session,
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
            raw_answer="Because the character used evidence from the chapter.",
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            answer_hash=ANSWER_HASH,
            flow_type="curriculum",
            evaluation_mode="llm_rubric",
            max_attempts=2,
            request_metadata={"answer_arrival": {"arrival_id": "arrival-1"}},
        )
        return session, result

    session, result = asyncio.run(exercise())

    assert result == {
        "outcome": "queued",
        "claim_token": ANSWER_CLAIM_TOKEN,
        "job": {
            "session_id": SESSION_ID,
            "activity_id": ACTIVITY_ID,
            "status": "queued",
            "attempts": 0,
            "max_attempts": 2,
            "lease_version": 0,
            "lease_expires_at": None,
            "next_attempt_at": None,
            "last_error_code": None,
            "error_json": None,
            "created_at": None,
            "updated_at": None,
            "started_at": None,
            "completed_at": None,
            "failed_at": None,
            "cancelled_at": None,
        },
    }
    assert len(session.calls) == 1
    sql = str(session.calls[0][0]).lower()
    assert "pg_advisory_xact_lock" in sql
    assert "school_answer_requests" in sql
    assert "school_evaluation_jobs" in sql
    assert "on conflict (session_id, activity_id)" in sql
    assert session.commits == 1
    assert session.rollbacks == 0


def test_school_routes_prefer_the_postgres_atomic_enqueue_when_available():
    calls: list[str] = []

    class _Store:
        async def claim_and_enqueue_school_evaluation_job_atomic(self, **_kwargs):
            calls.append("atomic")
            return {"outcome": "queued", "job": {"status": "queued"}}

        async def claim_and_enqueue_school_evaluation_job(self, **_kwargs):
            raise AssertionError("the generic queue path must not run for Postgres")

    result = asyncio.run(
        school_rebuild_routes._claim_and_enqueue_school_evaluation_job(
            _Store(),
            user_id=USER_ID,
            session_id=SESSION_ID,
            activity_id=ACTIVITY_ID,
        )
    )

    assert result == {"outcome": "queued", "job": {"status": "queued"}}
    assert calls == ["atomic"]


def test_evaluated_curriculum_persistence_uses_one_locked_context_and_one_bulk_mutation():
    """Queued LLM answers must not pay one cross-region SQL round trip per projection."""

    class _Result:
        def __init__(self, row):
            self.row = row

        def mappings(self):
            return self

        def first(self):
            return self.row

    class _Session:
        def __init__(self):
            self.calls: list[tuple[object, dict]] = []
            self.commits = 0
            self.rollbacks = 0

        async def execute(self, statement, params):
            self.calls.append((statement, params))
            if len(self.calls) == 1:
                return _Result(
                    {
                        "active_profile_version_id": "profile-v1",
                        "request_status": "processing",
                        "request_answer_hash": ANSWER_HASH,
                        "request_claim_token": ANSWER_CLAIM_TOKEN,
                        "request_response_json": None,
                        "session_state_json": {"current_activity_id": ACTIVITY_ID},
                        "session_status": "active",
                        "session_profile_version_id": "profile-v1",
                        "profile_rows_json": [],
                        "language_confidence": None,
                        "language_total_signals": None,
                        "job_status": "running",
                        "job_answer_hash": ANSWER_HASH,
                        "job_answer_claim_token": ANSWER_CLAIM_TOKEN,
                        "job_user_id": USER_ID,
                        "job_lease_owner": LEASE_OWNER,
                        "job_lease_token": LEASE_TOKEN,
                        "job_lease_version": LEASE_VERSION,
                    }
                )
            return _Result(
                {
                    "inserted": True,
                    "session_transitioned": True,
                    "job_completed": True,
                    "request_completed": True,
                }
            )

        async def commit(self):
            self.commits += 1

        async def rollback(self):
            self.rollbacks += 1

    async def exercise():
        session = _Session()
        result = await repo.persist_school_evaluated_curriculum_attempt(
            session,
            learning_event={
                "source_event_key": "queued-worker-event",
                "user_id": USER_ID,
                "domain": "school",
                "task_type": "school_rebuild_curriculum",
                "module_id": "eng_c5_ch01",
                "session_id": SESSION_ID,
                "node_id": ACTIVITY_ID,
                "skill_id": "reading.inference_reason",
                "source": "school_rebuild",
                "attempt_type": "independent_check",
                "score": 0.92,
                "confidence": 0.95,
                "criteria_json": [],
                "evidence_json": {},
                "blockers": [],
                "gap": "",
            },
            school_session={
                "session_id": SESSION_ID,
                "user_id": USER_ID,
                "api_version": "rebuild",
                "flow_type": "curriculum",
                "subject_id": "english",
                "class_no": 5,
                "status": "active",
                "current_stage": "2",
                "profile_version_id": "profile-v1",
                "state_json": {"current_activity_id": "next-activity"},
            },
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            request_activity_id=ACTIVITY_ID,
            request_answer_hash=ANSWER_HASH,
            request_claim_token=ANSWER_CLAIM_TOKEN,
            response_json={"feedback": "Recorded."},
            projection_evidence={
                "session_id": SESSION_ID,
                "chapter_id": "eng_c5_ch01",
                "level_id": "level-1",
                "module_id": "eng_c5_ch01",
                "task_type": "school_rebuild_curriculum",
                "focus": "Use a clue from the text.",
                "skill_ids": ["reading.inference_reason"],
                "attempt_type": "independent_check",
                "score": 0.92,
                "confidence": 0.95,
                "criteria": [],
                "blockers": [],
                "answer_excerpt": "A short learner response.",
                "attempt_passed": True,
            },
            language_evaluation=None,
            evaluation_job_completion={
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "activity_id": ACTIVITY_ID,
                "answer_hash": ANSWER_HASH,
                "answer_claim_token": ANSWER_CLAIM_TOKEN,
                "lease_owner": LEASE_OWNER,
                "lease_token": LEASE_TOKEN,
                "lease_version": LEASE_VERSION,
                "response_json": {"feedback": "Recorded."},
                "result_data": {"score": 0.92},
            },
        )
        return session, result

    session, result = asyncio.run(exercise())

    assert result == {"outcome": "persisted"}
    assert len(session.calls) == 2
    context_sql = str(session.calls[0][0]).lower()
    mutation_sql = str(session.calls[1][0]).lower()
    assert "pg_advisory_xact_lock" in context_sql
    assert "for update" in context_sql
    assert "school_evaluation_jobs" in context_sql
    assert "insert into learning_events" in mutation_sql
    assert "jsonb_to_recordset" in mutation_sql
    assert "update school_sessions" in mutation_sql
    assert "update school_evaluation_jobs" in mutation_sql
    assert "update school_answer_requests" in mutation_sql
    assert session.commits == 1
    assert session.rollbacks == 0


def test_pg_store_uses_compact_transaction_for_direct_curriculum_answers(
    monkeypatch,
):
    session = object()
    forwarded: list[dict] = []

    @asynccontextmanager
    async def fake_session():
        yield session

    async def capture(db_session, **kwargs):
        assert db_session is session
        forwarded.append(kwargs)
        return {"outcome": "persisted"}

    monkeypatch.setattr(pg_store, "_session", fake_session)
    monkeypatch.setattr(repo, "persist_school_deterministic_curriculum_attempt", capture)

    async def exercise() -> dict:
        return await pg_store.PgStore().persist_school_deterministic_curriculum_attempt(
            learning_event={"source_event_key": "direct-curriculum"},
            school_session={"user_id": USER_ID, "session_id": SESSION_ID},
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            request_activity_id=ACTIVITY_ID,
            request_answer_hash=ANSWER_HASH,
            response_json={"feedback": "Recorded."},
        )

    assert asyncio.run(exercise()) == {"outcome": "persisted"}
    assert forwarded == [{
        "learning_event": {"source_event_key": "direct-curriculum"},
        "school_session": {"user_id": USER_ID, "session_id": SESSION_ID},
        "expected_state_json": {"current_activity_id": ACTIVITY_ID},
        "request_activity_id": ACTIVITY_ID,
        "request_answer_hash": ANSWER_HASH,
        "response_json": {"feedback": "Recorded."},
    }]


def test_compact_direct_curriculum_persist_uses_claim_context_and_bulk_mutation():
    """A deterministic answer must not fall back to serial generic persistence."""

    class _Result:
        def __init__(self, row):
            self.row = row

        def mappings(self):
            return self

        def first(self):
            return self.row

    class _Session:
        def __init__(self):
            self.calls: list[tuple[object, dict]] = []
            self.commits = 0
            self.rollbacks = 0

        async def execute(self, statement, params):
            self.calls.append((statement, params))
            if len(self.calls) == 1:
                return _Result(
                    {
                        "active_profile_version_id": "profile-v1",
                        "request_origin": "claimed",
                        "request_status": "processing",
                        "request_answer_hash": ANSWER_HASH,
                        "request_claim_token": "direct-claim-token",
                        "request_response_json": None,
                        "session_state_json": {
                            "current_activity_id": ACTIVITY_ID,
                        },
                        "session_status": "active",
                        "session_profile_version_id": "profile-v1",
                        "profile_rows_json": [],
                        "language_confidence": None,
                        "language_total_signals": None,
                    }
                )
            return _Result(
                {
                    "inserted": True,
                    "session_transitioned": True,
                    "request_completed": True,
                }
            )

        async def commit(self):
            self.commits += 1

        async def rollback(self):
            self.rollbacks += 1

    async def exercise():
        session = _Session()
        result = await repo.persist_school_deterministic_curriculum_attempt(
            session,
            learning_event={
                "source_event_key": "direct-worker-event",
                "user_id": USER_ID,
                "domain": "school",
                "task_type": "school_rebuild_curriculum",
                "module_id": "eng_c5_ch01",
                "session_id": SESSION_ID,
                "node_id": ACTIVITY_ID,
                "skill_id": "reading.inference_reason",
                "source": "school_rebuild",
                "attempt_type": "independent_check",
                "score": 0.92,
                "confidence": 0.95,
                "criteria_json": [],
                "evidence_json": {},
                "blockers": [],
                "gap": "",
            },
            school_session={
                "session_id": SESSION_ID,
                "user_id": USER_ID,
                "api_version": "rebuild",
                "flow_type": "curriculum",
                "subject_id": "english",
                "class_no": 5,
                "status": "active",
                "current_stage": "2",
                "profile_version_id": "profile-v1",
                "state_json": {"current_activity_id": "next-activity"},
            },
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            request_activity_id=ACTIVITY_ID,
            request_answer_hash=ANSWER_HASH,
            response_json={"feedback": "Recorded."},
            projection_evidence=None,
            language_evaluation=None,
        )
        return session, result

    session, result = asyncio.run(exercise())

    assert result == {"outcome": "persisted"}
    assert len(session.calls) == 2
    context_sql = str(session.calls[0][0]).lower()
    mutation_sql = str(session.calls[1][0]).lower()
    assert "pg_advisory_xact_lock" in context_sql
    assert "insert into school_answer_requests" in context_sql
    assert "school_evaluation_jobs" not in context_sql
    assert "insert into learning_events" in mutation_sql
    assert "jsonb_to_recordset" in mutation_sql
    assert "update school_sessions" in mutation_sql
    assert "update school_answer_requests" in mutation_sql
    assert "school_evaluation_jobs" not in mutation_sql
    assert session.commits == 1
    assert session.rollbacks == 0


def test_pg_store_forwards_unscored_curriculum_steps_to_the_dedicated_transaction(
    monkeypatch,
):
    session = object()
    forwarded: list[dict] = []

    @asynccontextmanager
    async def fake_session():
        yield session

    async def capture(db_session, **kwargs):
        assert db_session is session
        forwarded.append(kwargs)
        return {"outcome": "persisted"}

    monkeypatch.setattr(pg_store, "_session", fake_session)
    monkeypatch.setattr(repo, "persist_school_curriculum_experience_step", capture)

    async def exercise() -> dict:
        return await pg_store.PgStore().persist_school_curriculum_experience_step(
            school_session={
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "api_version": "rebuild",
                "flow_type": "curriculum",
            },
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            request_activity_id=ACTIVITY_ID,
            request_answer_hash=ANSWER_HASH,
            response_json={"feedback": "Continue."},
        )

    assert asyncio.run(exercise()) == {"outcome": "persisted"}
    assert forwarded == [{
        "school_session": {
            "user_id": USER_ID,
            "session_id": SESSION_ID,
            "api_version": "rebuild",
            "flow_type": "curriculum",
        },
        "expected_state_json": {"current_activity_id": ACTIVITY_ID},
        "request_activity_id": ACTIVITY_ID,
        "request_answer_hash": ANSWER_HASH,
        "response_json": {"feedback": "Continue."},
    }]


def test_locked_answer_session_upsert_does_not_relock_existing_lineage():
    """A canonical answer transaction must reuse its own session/profile locks."""

    class Result:
        def first(self):
            return object()

    class RecordingSession:
        def __init__(self):
            self.sql: list[str] = []

        async def execute(self, statement, _params):
            self.sql.append(str(statement))
            return Result()

    session = RecordingSession()

    async def exercise() -> None:
        await repo.upsert_school_session(
            session,
            session_id=SESSION_ID,
            user_id=USER_ID,
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="6",
            profile_version_id="10000000-0000-4000-8000-000000000002",
            state_json={
                "profile_version_id": "10000000-0000-4000-8000-000000000002",
            },
            _commit=False,
            _profile_lineage_locked=True,
            _locked_existing_session={
                "status": "active",
                "profile_version_id": "10000000-0000-4000-8000-000000000002",
                "source_placement_report_id": None,
            },
        )

    asyncio.run(exercise())

    assert not any("FROM learner_profiles" in sql for sql in session.sql)
    assert not any("SELECT status," in sql for sql in session.sql)
    assert any("FROM school_profile_versions" in sql for sql in session.sql)
    assert any("INSERT INTO school_sessions" in sql for sql in session.sql)


def test_pg_store_compacts_current_curriculum_state_before_persisting_it(monkeypatch):
    session = object()
    forwarded: list[dict] = []

    @asynccontextmanager
    async def fake_session():
        yield session

    async def capture(db_session, **kwargs):
        assert db_session is session
        forwarded.append(kwargs)
        return {"outcome": "persisted"}

    state = curriculum.new_curriculum_state(
        school_profile={
            "target_class_no": 5,
            "subject_ids": ["english"],
            "profile_version_id": "profile-v1",
        },
        placement_report={"report_id": "placement-report"},
        recap_session=None,
    )
    monkeypatch.setattr(pg_store, "_session", fake_session)
    monkeypatch.setattr(repo, "persist_school_curriculum_experience_step", capture)

    async def exercise() -> dict:
        return await pg_store.PgStore().persist_school_curriculum_experience_step(
            school_session={
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "api_version": "rebuild",
                "flow_type": "curriculum",
                "subject_id": "english",
                "class_no": 5,
                "status": "active",
                "profile_version_id": "profile-v1",
                "state_json": state,
            },
            expected_state_json=state,
            request_activity_id="connect-1",
            request_answer_hash=ANSWER_HASH,
            response_json={"feedback": "Continue."},
        )

    assert asyncio.run(exercise()) == {"outcome": "persisted"}
    persisted = forwarded[0]["school_session"]["state_json"]
    assert "levels" not in persisted
    assert "chapter_assessment" not in persisted
    assert persisted["authored_content_reference"]["chapter_id"] == "eng_c5_ch01"
    assert forwarded[0]["expected_state_json"] is state


def test_experience_step_uses_one_atomic_statement_without_evidence_writes():
    class _Result:
        def mappings(self):
            return self

        def first(self):
            return {
                "origin": "claimed",
                "status": "completed",
                "answer_hash": ANSWER_HASH,
                "response_json": {"feedback": "Continue."},
                "session_transitioned": True,
            }

    class _Session:
        def __init__(self):
            self.calls: list[tuple[object, dict]] = []
            self.commits = 0
            self.rollbacks = 0

        async def execute(self, statement, params):
            self.calls.append((statement, params))
            return _Result()

        async def commit(self):
            self.commits += 1

        async def rollback(self):
            self.rollbacks += 1

    async def exercise():
        session = _Session()
        result = await repo.persist_school_curriculum_experience_step(
            session,
            school_session={
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "api_version": "rebuild",
                "flow_type": "curriculum",
                "status": "active",
                "current_stage": "1",
                "profile_version_id": "10000000-0000-4000-8000-000000000099",
                "state_json": {
                    "profile_version_id": "10000000-0000-4000-8000-000000000099",
                    "current_activity_id": "next-activity",
                },
            },
            expected_state_json={"current_activity_id": ACTIVITY_ID},
            request_activity_id=ACTIVITY_ID,
            request_answer_hash=ANSWER_HASH,
            response_json={"feedback": "Continue."},
        )
        return session, result

    session, result = asyncio.run(exercise())

    assert result == {"outcome": "persisted"}
    assert len(session.calls) == 1
    sql = str(session.calls[0][0]).lower()
    assert "pg_advisory_xact_lock" in sql
    assert "school_answer_requests" in sql
    assert "update school_sessions" in sql
    assert "learning_events" not in sql
    assert "learner_skill_profiles" not in sql
    assert "school_language_confidence" not in sql
    assert session.commits == 1
    assert session.rollbacks == 0
