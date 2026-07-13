from __future__ import annotations

import asyncio
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import repo
from scripts.apply_migrations import _statements


MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "app/db/migrations/2026-07-12-school-session-lineage.sql"
)
DISPOSABLE_DATABASE_PREFIX = "zidd_school_migration_test"

PROFILE_1 = "11111111-1111-4111-8111-111111111111"
PROFILE_1_REPLACEMENT = "11111111-1111-4111-8111-111111111112"
PROFILE_2 = "22222222-2222-4222-8222-222222222222"
PLACEMENT_SESSION = "10000000-0000-4000-8000-000000000001"
RECAP_SESSION = "10000000-0000-4000-8000-000000000002"
CURRICULUM_SESSION = "10000000-0000-4000-8000-000000000003"
CROSS_USER_SESSION = "10000000-0000-4000-8000-000000000004"
MALFORMED_SESSION = "10000000-0000-4000-8000-000000000005"
UNRESOLVED_SESSION = "10000000-0000-4000-8000-000000000006"
TERMINAL_SESSION = "10000000-0000-4000-8000-000000000007"
NON_REBUILD_ACTIVE_SESSION = "10000000-0000-4000-8000-000000000008"
NON_REBUILD_PAUSED_SESSION = "10000000-0000-4000-8000-000000000009"
POST_CUTOVER_NON_REBUILD_SESSION = "10000000-0000-4000-8000-000000000010"
REPORT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ATOMIC_RACE_SESSION = "70000000-0000-4000-8000-000000000001"
ATOMIC_REPORT_FAILURE_SESSION = "70000000-0000-4000-8000-000000000002"
ATOMIC_LEDGER_FAILURE_SESSION = "70000000-0000-4000-8000-000000000003"

LOOPBACK_MIGRATION_URL = (
    "postgresql://postgres:test@127.0.0.1/zidd_school_migration_test_safety"
)


def _migration_test_url() -> str:
    url = os.environ.get("SCHOOL_MIGRATION_TEST_URL", "").strip()
    if not url:
        if os.environ.get("CI", "").strip().lower() == "true":
            pytest.fail("SCHOOL_MIGRATION_TEST_URL is required in CI")
        pytest.skip("SCHOOL_MIGRATION_TEST_URL is not configured")
    parsed_url = urlparse(url)
    database_name = unquote(parsed_url.path.lstrip("/")).split("/", 1)[0]
    if not database_name.startswith(DISPOSABLE_DATABASE_PREFIX):
        pytest.fail(
            "Refusing SCHOOL_MIGRATION_TEST_URL: database name must start with "
            f"{DISPOSABLE_DATABASE_PREFIX!r}"
        )
    if (parsed_url.hostname or "").lower() not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Refusing SCHOOL_MIGRATION_TEST_URL: must use a loopback host")
    if os.environ.get("SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER", "").strip() != "1":
        pytest.fail(
            "Refusing role creation without "
            "SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER=1"
        )
    return url


def test_migration_test_url_skips_locally_when_unconfigured(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("SCHOOL_MIGRATION_TEST_URL", raising=False)

    with pytest.raises(pytest.skip.Exception):
        _migration_test_url()


def test_migration_test_url_fails_in_ci_when_unconfigured(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("SCHOOL_MIGRATION_TEST_URL", raising=False)

    with pytest.raises(
        pytest.fail.Exception,
        match="SCHOOL_MIGRATION_TEST_URL is required in CI",
    ):
        _migration_test_url()


def test_migration_test_url_rejects_non_loopback_host(monkeypatch):
    monkeypatch.setenv(
        "SCHOOL_MIGRATION_TEST_URL",
        "postgresql://postgres:test@db.example.com/zidd_school_migration_test_safety",
    )
    monkeypatch.setenv("SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER", "1")

    with pytest.raises(pytest.fail.Exception, match="loopback host"):
        _migration_test_url()


def test_migration_test_url_requires_disposable_cluster_flag(monkeypatch):
    monkeypatch.setenv("SCHOOL_MIGRATION_TEST_URL", LOOPBACK_MIGRATION_URL)
    monkeypatch.delenv("SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER", raising=False)

    with pytest.raises(
        pytest.fail.Exception,
        match="SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER=1",
    ):
        _migration_test_url()


async def _apply_lineage_migration(connection: asyncpg.Connection) -> None:
    for statement in _statements(MIGRATION.read_text()):
        await connection.execute(statement)


async def _create_baseline(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                CREATE ROLE anon NOLOGIN NOSUPERUSER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated NOLOGIN NOSUPERUSER;
            END IF;
        END
        $$;

        CREATE TABLE public.learner_profiles (
            user_id TEXT PRIMARY KEY
        );

        CREATE TABLE public.school_profile_versions (
            profile_version_id UUID PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
            status TEXT NOT NULL DEFAULT 'active',
            source_profile_version_id UUID,
            board_id TEXT,
            target_class_no INTEGER,
            subject_ids JSONB,
            preferred_teaching_language TEXT,
            english_comfort TEXT,
            prior_difficulty_signals JSONB,
            activated_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE public.school_sessions (
            session_id UUID PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
            api_version TEXT NOT NULL,
            flow_type TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            class_no INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            current_stage TEXT NOT NULL DEFAULT '',
            linked_session_id UUID REFERENCES public.school_sessions(session_id),
            state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ
        );

        CREATE UNIQUE INDEX idx_school_sessions_one_active_flow
            ON public.school_sessions(user_id, flow_type, subject_id, class_no)
            WHERE status IN ('active', 'paused_for_masterclass');

        CREATE TABLE public.school_answer_requests (
            session_id UUID NOT NULL REFERENCES public.school_sessions(session_id),
            activity_id TEXT NOT NULL,
            user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
            answer_hash TEXT NOT NULL,
            claim_token TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
            response_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (session_id, activity_id)
        );

        CREATE TABLE public.learning_events (
            source_event_key TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
            domain TEXT NOT NULL,
            task_type TEXT NOT NULL,
            module_id TEXT NOT NULL DEFAULT '',
            session_id TEXT,
            node_id TEXT NOT NULL DEFAULT '',
            skill_id TEXT NOT NULL,
            source TEXT NOT NULL,
            attempt_type TEXT NOT NULL DEFAULT '',
            score DOUBLE PRECISION NOT NULL DEFAULT 0,
            confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
            criteria_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
            gap TEXT NOT NULL DEFAULT '',
            scenario_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            caveats JSONB NOT NULL DEFAULT '[]'::jsonb,
            model_name TEXT,
            prompt_version TEXT,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE public.school_placement_reports (
            report_id UUID PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
            profile_version_id UUID NOT NULL
                REFERENCES public.school_profile_versions(profile_version_id),
            placement_session_id UUID NOT NULL
                REFERENCES public.school_sessions(session_id),
            placement_status TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            target_class_no INTEGER NOT NULL,
            evaluated_class_no INTEGER NOT NULL,
            active_learning_class_no INTEGER NOT NULL,
            unlock_state TEXT NOT NULL,
            blocking_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            watchlist_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            evidence_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            recommended_recap_modules_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            learner_summary TEXT NOT NULL DEFAULT '',
            parent_summary TEXT NOT NULL DEFAULT '',
            allowed_next_actions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(user_id, placement_session_id)
        );

        ALTER TABLE public.school_sessions ENABLE ROW LEVEL SECURITY;
        GRANT SELECT, INSERT, UPDATE, DELETE ON public.school_sessions TO anon;
        GRANT SELECT, INSERT, UPDATE, DELETE ON public.school_sessions TO authenticated;
        GRANT SELECT ON public.school_sessions TO PUBLIC;
        """
    )


async def _assert_empty_public_schema(connection: asyncpg.Connection) -> None:
    table_names = await connection.fetch(
        """
        SELECT table_row.relname AS table_name
        FROM pg_class AS table_row
        JOIN pg_namespace AS namespace_row
          ON namespace_row.oid = table_row.relnamespace
        WHERE namespace_row.nspname = 'public'
          AND table_row.relkind IN ('r', 'p')
        ORDER BY table_row.relname
        """
    )
    if table_names:
        pytest.fail(
            "Refusing nonempty disposable database; public already contains: "
            + ", ".join(str(row["table_name"]) for row in table_names)
        )


async def _seed_rows(connection: asyncpg.Connection) -> None:
    await connection.execute(
        f"""
        INSERT INTO public.learner_profiles(user_id)
        VALUES ('user-1'), ('user-2');

        INSERT INTO public.school_profile_versions
            (profile_version_id, user_id, status, source_profile_version_id,
             board_id, target_class_no, subject_ids,
             preferred_teaching_language, english_comfort,
             prior_difficulty_signals, activated_at)
        VALUES
            ('{PROFILE_1}', 'user-1', 'active', NULL, 'cbse', 3,
             '["english"]'::jsonb, 'hi_en', 'medium', '["reading"]'::jsonb, now()),
            ('{PROFILE_1_REPLACEMENT}', 'user-1', 'draft', '{PROFILE_1}', 'cbse', 5,
             '["english"]'::jsonb, 'hi_en', 'medium', '["reading"]'::jsonb, NULL),
            ('{PROFILE_2}', 'user-2', 'active', NULL, 'cbse', 4,
             '["english"]'::jsonb, 'en', 'high', '[]'::jsonb, now());

        INSERT INTO public.school_sessions
            (session_id, user_id, api_version, flow_type, subject_id, class_no,
             status, state_json)
        VALUES
            ('{PLACEMENT_SESSION}', 'user-1', 'rebuild', 'placement', 'english', 3,
             'active', '{{"profile_version_id": "{PROFILE_1}"}}'::jsonb);

        INSERT INTO public.school_placement_reports
            (report_id, user_id, profile_version_id, placement_session_id,
             placement_status, subject_id, target_class_no, evaluated_class_no,
             active_learning_class_no, unlock_state, blocking_skills_json,
             learner_summary)
        VALUES
            ('{REPORT_ID}', 'user-1', '{PROFILE_1}', '{PLACEMENT_SESSION}',
             'complete', 'english', 3, 3, 3, 'ready', '["reading_fluency"]'::jsonb,
             'Ready for class 3 English.');

        INSERT INTO public.school_sessions
            (session_id, user_id, api_version, flow_type, subject_id, class_no,
             status, state_json)
        VALUES
            ('{RECAP_SESSION}', 'user-1', 'rebuild', 'recap', 'english', 3,
             'paused_for_masterclass',
             '{{"source_placement_report_id": "{REPORT_ID}"}}'::jsonb),
            ('{CURRICULUM_SESSION}', 'user-1', 'rebuild', 'curriculum', 'english', 3,
             'active', '{{"source_placement_report_id": "{REPORT_ID}"}}'::jsonb),
            ('{CROSS_USER_SESSION}', 'user-2', 'rebuild', 'recap', 'english', 4,
             'active',
             '{{"profile_version_id": "{PROFILE_2}", "source_placement_report_id": "{REPORT_ID}"}}'::jsonb),
            ('{MALFORMED_SESSION}', 'user-1', 'rebuild', 'support', 'english', 3,
             'active', '{{"profile_version_id": "not-a-uuid"}}'::jsonb),
            ('{UNRESOLVED_SESSION}', 'user-1', 'rebuild', 'masterclass', 'english', 3,
             'paused_for_masterclass', '{{}}'::jsonb),
            ('{TERMINAL_SESSION}', 'user-1', 'rebuild', 'placement', 'english', 4,
             'complete', '{{}}'::jsonb),
            ('{NON_REBUILD_ACTIVE_SESSION}', 'user-1', 'v3', 'legacy-a', 'english', 3,
             'active', '{{}}'::jsonb),
            ('{NON_REBUILD_PAUSED_SESSION}', 'user-2', 'v2', 'legacy-b', 'english', 4,
            'paused_for_masterclass', '{{}}'::jsonb);

        UPDATE public.school_sessions
        SET linked_session_id = '{CROSS_USER_SESSION}'
        WHERE session_id = '{TERMINAL_SESSION}';
        """
    )


async def _rows_by_id(connection: asyncpg.Connection) -> dict[str, asyncpg.Record]:
    rows = await connection.fetch(
        """
        SELECT session_id::text AS session_id, status,
               profile_version_id::text AS profile_version_id,
               source_placement_report_id::text AS source_placement_report_id,
               linked_session_id::text AS linked_session_id,
               completed_at
        FROM public.school_sessions
        """
    )
    return {row["session_id"]: row for row in rows}


async def _assert_optional_uuid_repo_queries(url: str) -> None:
    sqlalchemy_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(sqlalchemy_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            active_filtered = await repo.get_active_school_session(
                session,
                "user-1",
                "rebuild",
                "curriculum",
                "english",
                3,
                profile_version_id=PROFILE_1,
                source_placement_report_id=REPORT_ID,
            )
            active_unfiltered = await repo.get_active_school_session(
                session,
                "user-1",
                "rebuild",
                "curriculum",
                "english",
                3,
                profile_version_id=None,
                source_placement_report_id=None,
            )
            latest_filtered = await repo.get_latest_school_session(
                session,
                "user-1",
                "rebuild",
                "recap",
                "english",
                3,
                profile_version_id=PROFILE_1,
                source_placement_report_id=REPORT_ID,
            )
            latest_unfiltered = await repo.get_latest_school_session(
                session,
                "user-1",
                "rebuild",
                "recap",
                "english",
                3,
                profile_version_id=None,
                source_placement_report_id=None,
            )
            report_filtered = await repo.get_school_placement_report(
                session,
                "user-1",
                PLACEMENT_SESSION,
                profile_version_id=PROFILE_1,
            )
            report_unfiltered = await repo.get_school_placement_report(
                session,
                "user-1",
                PLACEMENT_SESSION,
                profile_version_id=None,
            )
    finally:
        await engine.dispose()

    for row in (active_filtered, active_unfiltered):
        assert row is not None
        assert row["session_id"] == CURRICULUM_SESSION
        assert row["profile_version_id"] == PROFILE_1
        assert row["source_placement_report_id"] == REPORT_ID
    for row in (latest_filtered, latest_unfiltered):
        assert row is not None
        assert row["session_id"] == RECAP_SESSION
        assert row["profile_version_id"] == PROFILE_1
        assert row["source_placement_report_id"] == REPORT_ID
    for row in (report_filtered, report_unfiltered):
        assert row is not None
        assert row["report_id"] == REPORT_ID
        assert row["profile_version_id"] == PROFILE_1
        assert row["placement_session_id"] == PLACEMENT_SESSION
        assert row["blocking_skills"] == ["reading_fluency"]


async def _assert_concurrent_school_start_returns_winner(url: str) -> None:
    sqlalchemy_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(sqlalchemy_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def create(session_id: str):
        async with session_factory() as session:
            return await repo.get_or_create_school_session(
                session,
                session_id=session_id,
                user_id="user-1",
                api_version="rebuild",
                flow_type="support",
                subject_id="english",
                class_no=4,
                status="active",
                linked_session_id=PLACEMENT_SESSION,
                profile_version_id=PROFILE_1,
                source_placement_report_id=None,
                state_json={"status": "active"},
            )

    try:
        first, second = await asyncio.gather(
            create("60000000-0000-4000-8000-000000000001"),
            create("60000000-0000-4000-8000-000000000002"),
        )
    finally:
        await engine.dispose()

    assert first["session_id"] == second["session_id"]


async def _assert_atomic_placement_start_serializes_material_activation(url: str) -> None:
    sqlalchemy_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(sqlalchemy_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    activation_locked = asyncio.Event()
    release_activation = asyncio.Event()

    async def activate_material_profile() -> None:
        async with session_factory() as session:
            await repo._lock_school_profile_lineage(session, "user-1")
            await session.execute(
                text(
                    """
                    UPDATE school_profile_versions
                    SET status = CASE
                            WHEN profile_version_id = CAST(:old_profile_id AS uuid)
                            THEN 'archived'
                            ELSE 'active'
                        END,
                        activated_at = CASE
                            WHEN profile_version_id = CAST(:new_profile_id AS uuid)
                            THEN now()
                            ELSE activated_at
                        END,
                        updated_at = now()
                    WHERE user_id = :uid
                      AND profile_version_id IN (
                          CAST(:old_profile_id AS uuid),
                          CAST(:new_profile_id AS uuid)
                      )
                    """
                ),
                {
                    "uid": "user-1",
                    "old_profile_id": PROFILE_1,
                    "new_profile_id": PROFILE_1_REPLACEMENT,
                },
            )
            await session.execute(
                text(
                    """
                    UPDATE school_sessions
                    SET status = 'expired', completed_at = COALESCE(completed_at, now())
                    WHERE user_id = :uid
                      AND profile_version_id = CAST(:old_profile_id AS uuid)
                      AND status IN ('active', 'paused_for_masterclass')
                    """
                ),
                {"uid": "user-1", "old_profile_id": PROFILE_1},
            )
            activation_locked.set()
            await release_activation.wait()
            await session.commit()

    def placement_start(session_id: str, profile_version_id: str):
        async def run() -> dict:
            async with session_factory() as session:
                return await repo.get_or_create_active_school_placement_session(
                    session,
                    session_id=session_id,
                    user_id="user-1",
                    profile_version_id=profile_version_id,
                    subject_id="english",
                    class_no=5,
                    current_stage="snapshot",
                    state_json={
                        "status": "in_progress",
                        "stage": "snapshot",
                        "profile_version_id": profile_version_id,
                    },
                )

        return run

    activation_task = asyncio.create_task(activate_material_profile())
    await activation_locked.wait()
    stale_start_task = asyncio.create_task(
        placement_start(
            "72000000-0000-4000-8000-000000000001",
            PROFILE_1,
        )()
    )
    await asyncio.sleep(0.05)
    release_activation.set()
    await activation_task
    stale_result = await asyncio.gather(stale_start_task, return_exceptions=True)
    assert len(stale_result) == 1
    assert isinstance(stale_result[0], ValueError)
    assert str(stale_result[0]) == "stale_school_profile_lineage"

    first, second = await asyncio.gather(
        placement_start(
            "72000000-0000-4000-8000-000000000002",
            PROFILE_1_REPLACEMENT,
        )(),
        placement_start(
            "72000000-0000-4000-8000-000000000003",
            PROFILE_1_REPLACEMENT,
        )(),
    )
    assert first["session_id"] == second["session_id"]
    assert first["profile_version_id"] == PROFILE_1_REPLACEMENT
    assert first["status"] == "active"

    async with session_factory() as session:
        active_profile_id = await session.scalar(
            text(
                """
                SELECT profile_version_id::text
                FROM school_profile_versions
                WHERE user_id = :uid AND status = 'active'
                """
            ),
            {"uid": "user-1"},
        )
        active_placements = await session.execute(
            text(
                """
                SELECT session_id::text AS session_id,
                       profile_version_id::text AS profile_version_id
                FROM school_sessions
                WHERE user_id = :uid
                  AND flow_type = 'placement'
                  AND subject_id = 'english'
                  AND class_no = 5
                  AND status IN ('active', 'paused_for_masterclass')
                """
            ),
            {"uid": "user-1"},
        )
        rows = active_placements.mappings().all()

    assert active_profile_id == PROFILE_1_REPLACEMENT
    assert len(rows) == 1
    assert rows[0]["session_id"] == first["session_id"]
    assert rows[0]["profile_version_id"] == active_profile_id

    async with session_factory() as session:
        await repo._lock_school_profile_lineage(session, "user-1")
        await session.execute(
            text(
                """
                UPDATE school_profile_versions
                SET status = CASE
                        WHEN profile_version_id = CAST(:old_profile_id AS uuid)
                        THEN 'active'
                        ELSE 'draft'
                    END,
                    updated_at = now()
                WHERE user_id = :uid
                  AND profile_version_id IN (
                      CAST(:old_profile_id AS uuid),
                      CAST(:new_profile_id AS uuid)
                  )
                """
            ),
            {
                "uid": "user-1",
                "old_profile_id": PROFILE_1,
                "new_profile_id": PROFILE_1_REPLACEMENT,
            },
        )
        await session.execute(
            text(
                """
                UPDATE school_sessions
                SET status = CASE
                        WHEN session_id = CAST(:seeded_placement_id AS uuid)
                        THEN 'active'
                        ELSE 'expired'
                    END,
                    completed_at = CASE
                        WHEN session_id = CAST(:seeded_placement_id AS uuid)
                        THEN NULL
                        ELSE COALESCE(completed_at, now())
                    END
                WHERE user_id = :uid
                  AND flow_type = 'placement'
                  AND status IN ('active', 'expired')
                """
            ),
            {"uid": "user-1", "seeded_placement_id": PLACEMENT_SESSION},
        )
        await session.commit()
    await engine.dispose()


async def _assert_atomic_school_answer_persistence(url: str) -> None:
    sqlalchemy_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(sqlalchemy_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    def session_write(session_id: str, flow_type: str, state: dict) -> dict:
        return {
            "session_id": session_id,
            "user_id": "user-1",
            "api_version": "rebuild",
            "flow_type": flow_type,
            "subject_id": "english",
            "class_no": 3,
            "status": "active",
            "current_stage": "answer",
            "linked_session_id": None,
            "profile_version_id": PROFILE_1,
            "source_placement_report_id": None,
            "state_json": state,
        }

    def event(session_id: str, label: str) -> dict:
        return {
            "source_event_key": f"school-answer-atomic:{session_id}:{label}",
            "user_id": "user-1",
            "domain": "school",
            "task_type": "school_rebuild_placement",
            "module_id": "english",
            "session_id": session_id,
            "node_id": "atomic-item",
            "skill_id": "placement.atomic",
            "source": "school_rebuild",
        }

    def report(session_id: str, report_id: str, profile_version_id: str) -> dict:
        return {
            "report_id": report_id,
            "user_id": "user-1",
            "profile_version_id": profile_version_id,
            "placement_session_id": session_id,
            "placement_status": "target_ready",
            "subject_id": "english",
            "target_class_no": 3,
            "evaluated_class_no": 3,
            "active_learning_class_no": 3,
            "unlock_state": "target_unlocked",
            "blocking_skills": [],
            "watchlist_skills": [],
            "evidence_summary": {},
            "recommended_recap_modules": [],
            "learner_summary": "Ready.",
            "parent_summary": "Ready.",
            "allowed_next_actions": ["start_curriculum"],
        }

    async def create_session(session_id: str, flow_type: str, state: dict) -> None:
        async with session_factory() as session:
            await repo.get_or_create_school_session(
                session,
                **session_write(session_id, flow_type, state),
            )

    async def claim(session_id: str, activity_id: str) -> dict:
        async with session_factory() as session:
            return await repo.claim_school_answer_request(
                session,
                "user-1",
                session_id,
                activity_id,
                "answer-hash",
            )

    try:
        initial_state = {"step": 0}
        await create_session(ATOMIC_RACE_SESSION, "atomic-race", initial_state)
        race_claim = await claim(ATOMIC_RACE_SESSION, "atomic-item")

        async def race_transition(label: str):
            async with session_factory() as session:
                await repo.persist_school_answer_attempt(
                    session,
                    learning_event=event(ATOMIC_RACE_SESSION, label),
                    school_session=session_write(
                        ATOMIC_RACE_SESSION,
                        "atomic-race",
                        {"step": 1, "winner": label},
                    ),
                    expected_state_json=initial_state,
                    request_activity_id="atomic-item",
                    request_answer_hash="answer-hash",
                    request_claim_token=race_claim["claim_token"],
                    response_json={"winner": label},
                )

        race_results = await asyncio.gather(
            race_transition("first"),
            race_transition("second"),
            return_exceptions=True,
        )
        assert sum(result is None for result in race_results) == 1
        assert sum(
            isinstance(result, ValueError)
            and str(result) == "stale_school_answer_session"
            for result in race_results
        ) == 1

        async with session_factory() as session:
            race_session = await repo.get_school_session(
                session,
                "user-1",
                ATOMIC_RACE_SESSION,
            )
            race_request = await repo.get_school_answer_request(
                session,
                "user-1",
                ATOMIC_RACE_SESSION,
                "atomic-item",
            )
            event_count = await session.scalar(
                text(
                    """
                    SELECT count(*)
                    FROM learning_events
                    WHERE source_event_key LIKE 'school-answer-atomic:%'
                    """
                )
            )
        assert event_count == 1
        assert race_request["status"] == "completed"
        assert race_request["response_json"] == {
            "winner": race_session["state_json"]["winner"]
        }

        report_initial = {"step": 0}
        await create_session(
            ATOMIC_REPORT_FAILURE_SESSION,
            "atomic-report-failure",
            report_initial,
        )
        report_claim = await claim(
            ATOMIC_REPORT_FAILURE_SESSION,
            "report-item",
        )
        with pytest.raises(IntegrityError):
            async with session_factory() as session:
                await repo.persist_school_answer_attempt(
                    session,
                    learning_event=event(
                        ATOMIC_REPORT_FAILURE_SESSION,
                        "report-failure",
                    ),
                    school_session=session_write(
                        ATOMIC_REPORT_FAILURE_SESSION,
                        "atomic-report-failure",
                        {"step": 1},
                    ),
                    expected_state_json=report_initial,
                    request_activity_id="report-item",
                    request_answer_hash="answer-hash",
                    request_claim_token=report_claim["claim_token"],
                    response_json={"winner": "must-not-persist"},
                    placement_report=report(
                        ATOMIC_REPORT_FAILURE_SESSION,
                        "71000000-0000-4000-8000-000000000001",
                        "ffffffff-ffff-4fff-8fff-ffffffffffff",
                    ),
                )

        async with session_factory() as session:
            failed_report_session = await repo.get_school_session(
                session,
                "user-1",
                ATOMIC_REPORT_FAILURE_SESSION,
            )
            failed_report_request = await repo.get_school_answer_request(
                session,
                "user-1",
                ATOMIC_REPORT_FAILURE_SESSION,
                "report-item",
            )
            failed_report = await repo.get_school_placement_report(
                session,
                "user-1",
                ATOMIC_REPORT_FAILURE_SESSION,
            )
            failed_report_events = await session.scalar(
                text(
                    """
                    SELECT count(*) FROM learning_events
                    WHERE session_id = :session_id
                    """
                ),
                {"session_id": ATOMIC_REPORT_FAILURE_SESSION},
            )
        assert failed_report_session["state_json"] == report_initial
        assert failed_report_request["status"] == "processing"
        assert failed_report_request["response_json"] is None
        assert failed_report is None
        assert failed_report_events == 0

        ledger_initial = {"step": 0}
        await create_session(
            ATOMIC_LEDGER_FAILURE_SESSION,
            "atomic-ledger-failure",
            ledger_initial,
        )
        await claim(ATOMIC_LEDGER_FAILURE_SESSION, "ledger-item")
        with pytest.raises(ValueError, match="stale_school_answer_request"):
            async with session_factory() as session:
                await repo.persist_school_answer_attempt(
                    session,
                    learning_event=event(
                        ATOMIC_LEDGER_FAILURE_SESSION,
                        "ledger-failure",
                    ),
                    school_session=session_write(
                        ATOMIC_LEDGER_FAILURE_SESSION,
                        "atomic-ledger-failure",
                        {"step": 1},
                    ),
                    expected_state_json=ledger_initial,
                    request_activity_id="ledger-item",
                    request_answer_hash="answer-hash",
                    request_claim_token="wrong-claim-token",
                    response_json={"winner": "must-not-persist"},
                    placement_report=report(
                        ATOMIC_LEDGER_FAILURE_SESSION,
                        "71000000-0000-4000-8000-000000000002",
                        PROFILE_1,
                    ),
                )

        async with session_factory() as session:
            failed_ledger_session = await repo.get_school_session(
                session,
                "user-1",
                ATOMIC_LEDGER_FAILURE_SESSION,
            )
            failed_ledger_request = await repo.get_school_answer_request(
                session,
                "user-1",
                ATOMIC_LEDGER_FAILURE_SESSION,
                "ledger-item",
            )
            failed_ledger_report = await repo.get_school_placement_report(
                session,
                "user-1",
                ATOMIC_LEDGER_FAILURE_SESSION,
            )
            failed_ledger_events = await session.scalar(
                text(
                    """
                    SELECT count(*) FROM learning_events
                    WHERE session_id = :session_id
                    """
                ),
                {"session_id": ATOMIC_LEDGER_FAILURE_SESSION},
            )
        assert failed_ledger_session["state_json"] == ledger_initial
        assert failed_ledger_request["status"] == "processing"
        assert failed_ledger_request["response_json"] is None
        assert failed_ledger_report is None
        assert failed_ledger_events == 0
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_school_session_lineage_migration_on_disposable_postgres():
    url = _migration_test_url()
    connection = await asyncpg.connect(url)
    try:
        database_name = await connection.fetchval("SELECT current_database()")
        if not str(database_name).startswith(DISPOSABLE_DATABASE_PREFIX):
            pytest.fail(
                "Connected database failed disposable-name verification; refusing migration"
            )

        await _assert_empty_public_schema(connection)
        await _create_baseline(connection)
        await _seed_rows(connection)
        await _apply_lineage_migration(connection)
        await connection.execute(
            f"""
            INSERT INTO public.school_sessions
                (session_id, user_id, api_version, flow_type, subject_id,
                 class_no, status, state_json)
            VALUES
                ('{POST_CUTOVER_NON_REBUILD_SESSION}', 'user-1', 'v3',
                 'post-cutover-legacy', 'english', 3, 'active', '{{}}'::jsonb)
            """
        )
        await _apply_lineage_migration(connection)

        await _assert_optional_uuid_repo_queries(url)
        await _assert_concurrent_school_start_returns_winner(url)
        await _assert_atomic_placement_start_serializes_material_activation(url)
        await _assert_atomic_school_answer_persistence(url)

        rows = await _rows_by_id(connection)
        assert rows[PLACEMENT_SESSION]["profile_version_id"] == PROFILE_1
        assert rows[PLACEMENT_SESSION]["status"] == "active"
        for session_id in (RECAP_SESSION, CURRICULUM_SESSION):
            assert rows[session_id]["profile_version_id"] == PROFILE_1
            assert rows[session_id]["source_placement_report_id"] == REPORT_ID
        assert rows[CROSS_USER_SESSION]["profile_version_id"] == PROFILE_2
        assert rows[CROSS_USER_SESSION]["source_placement_report_id"] is None
        assert rows[CROSS_USER_SESSION]["status"] == "active"
        for session_id in (MALFORMED_SESSION, UNRESOLVED_SESSION):
            assert rows[session_id]["status"] == "expired"
            assert rows[session_id]["profile_version_id"] is None
            assert rows[session_id]["completed_at"] is not None
        assert rows[TERMINAL_SESSION]["status"] == "complete"
        assert rows[TERMINAL_SESSION]["profile_version_id"] is None
        assert rows[TERMINAL_SESSION]["linked_session_id"] is None
        for session_id in (NON_REBUILD_ACTIVE_SESSION, NON_REBUILD_PAUSED_SESSION):
            assert rows[session_id]["status"] == "expired"
            assert rows[session_id]["completed_at"] is not None
        assert rows[POST_CUTOVER_NON_REBUILD_SESSION]["status"] == "active"
        assert rows[POST_CUTOVER_NON_REBUILD_SESSION]["completed_at"] is None
        assert await connection.fetchval(
            """
            SELECT count(*)
            FROM public.school_migration_markers
            WHERE migration_key = '2026-07-12-school-session-lineage-cutover-v1'
            """
        ) == 1

        column_types = {
            row["column_name"]: row["udt_name"]
            for row in await connection.fetch(
                """
                SELECT column_name, udt_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'school_sessions'
                  AND column_name IN (
                      'profile_version_id', 'source_placement_report_id'
                  )
                """
            )
        }
        assert column_types == {
            "profile_version_id": "uuid",
            "source_placement_report_id": "uuid",
        }

        foreign_keys = {
            row["definition"]
            for row in await connection.fetch(
                """
                SELECT pg_get_constraintdef(constraint_row.oid, true) AS definition
                FROM pg_constraint AS constraint_row
                JOIN pg_class AS table_row ON table_row.oid = constraint_row.conrelid
                JOIN pg_namespace AS namespace_row
                  ON namespace_row.oid = table_row.relnamespace
                WHERE constraint_row.contype = 'f'
                  AND namespace_row.nspname = 'public'
                  AND table_row.relname = 'school_sessions'
                """
            )
        }
        assert any(
            "FOREIGN KEY (profile_version_id) REFERENCES school_profile_versions(profile_version_id)"
            in definition
            for definition in foreign_keys
        )
        assert any(
            "FOREIGN KEY (source_placement_report_id) REFERENCES school_placement_reports(report_id)"
            in definition
            for definition in foreign_keys
        )
        assert any(
            "FOREIGN KEY (user_id, linked_session_id) REFERENCES school_sessions(user_id, session_id)"
            in definition
            for definition in foreign_keys
        )

        check_definition = await connection.fetchval(
            """
            SELECT pg_get_constraintdef(constraint_row.oid, true)
            FROM pg_constraint AS constraint_row
            JOIN pg_class AS table_row ON table_row.oid = constraint_row.conrelid
            JOIN pg_namespace AS namespace_row
              ON namespace_row.oid = table_row.relnamespace
            WHERE namespace_row.nspname = 'public'
              AND table_row.relname = 'school_sessions'
              AND constraint_row.conname = 'school_rebuild_active_profile_lineage'
            """
        )
        assert check_definition
        assert "profile_version_id IS NOT NULL" in check_definition

        indexes = {
            row["indexname"]
            for row in await connection.fetch(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public' AND tablename = 'school_sessions'
                """
            )
        }
        assert {
            "idx_school_sessions_one_active_flow",
            "idx_school_sessions_profile_flow_updated",
            "idx_school_sessions_source_report",
        } <= indexes

        with pytest.raises(asyncpg.CheckViolationError):
            await connection.execute(
                """
                INSERT INTO public.school_sessions
                    (session_id, user_id, api_version, flow_type, subject_id,
                     class_no, status)
                VALUES
                    ('30000000-0000-4000-8000-000000000001', 'user-1',
                     'rebuild', 'check-test', 'english', 3, 'active')
                """
            )
        await connection.execute(
            """
            INSERT INTO public.school_sessions
                (session_id, user_id, api_version, flow_type, subject_id,
                 class_no, status)
            VALUES
                ('30000000-0000-4000-8000-000000000002', 'user-1',
                 'rebuild', 'historical-test', 'english', 3, 'complete')
            """
        )
        with pytest.raises(asyncpg.ForeignKeyViolationError):
            await connection.execute(
                f"""
                INSERT INTO public.school_sessions
                    (session_id, user_id, profile_version_id, api_version,
                     flow_type, subject_id, class_no, status)
                VALUES
                    ('30000000-0000-4000-8000-000000000003', 'user-1',
                     'ffffffff-ffff-4fff-8fff-ffffffffffff', 'rebuild',
                     'profile-fk-test', 'english', 3, 'complete')
                """
            )
        with pytest.raises(asyncpg.ForeignKeyViolationError):
            await connection.execute(
                f"""
                INSERT INTO public.school_sessions
                    (session_id, user_id, profile_version_id,
                     source_placement_report_id, api_version, flow_type,
                     subject_id, class_no, status)
                VALUES
                    ('30000000-0000-4000-8000-000000000004', 'user-1',
                     '{PROFILE_1}', 'ffffffff-ffff-4fff-8fff-ffffffffffff',
                     'rebuild', 'report-fk-test', 'english', 3, 'complete')
                """
            )
        with pytest.raises(asyncpg.UniqueViolationError):
            await connection.execute(
                f"""
                INSERT INTO public.school_sessions
                    (session_id, user_id, profile_version_id, api_version,
                     flow_type, subject_id, class_no, status)
                VALUES
                    ('30000000-0000-4000-8000-000000000005', 'user-1',
                     '{PROFILE_1}', 'rebuild', 'placement', 'english', 3, 'active')
                """
            )

        with pytest.raises(asyncpg.ForeignKeyViolationError):
            await connection.execute(
                f"""
                INSERT INTO public.school_sessions
                    (session_id, user_id, profile_version_id, api_version,
                     flow_type, subject_id, class_no, status, linked_session_id)
                VALUES
                    ('30000000-0000-4000-8000-000000000007', 'user-2',
                     '{PROFILE_2}', 'rebuild', 'cross-user-link-test', 'english',
                     3, 'complete', '{PLACEMENT_SESSION}')
                """
            )
        with pytest.raises(asyncpg.UniqueViolationError):
            await connection.execute(
                f"""
                INSERT INTO public.school_sessions
                    (session_id, user_id, profile_version_id, api_version,
                     flow_type, subject_id, class_no, status)
                VALUES
                    ('30000000-0000-4000-8000-000000000006', 'user-1',
                     '{PROFILE_1_REPLACEMENT}', 'rebuild', 'placement',
                     'english', 3, 'active')
                """
            )

        assert await connection.fetchval(
            """
            SELECT relrowsecurity
            FROM pg_class AS table_row
            JOIN pg_namespace AS namespace_row
              ON namespace_row.oid = table_row.relnamespace
            WHERE namespace_row.nspname = 'public'
              AND table_row.relname = 'school_sessions'
            """
        ) is True
        assert await connection.fetchval(
            """
            SELECT relrowsecurity
            FROM pg_class AS table_row
            JOIN pg_namespace AS namespace_row
              ON namespace_row.oid = table_row.relnamespace
            WHERE namespace_row.nspname = 'public'
              AND table_row.relname = 'school_migration_markers'
            """
        ) is True
        assert await connection.fetchval(
            """
            SELECT count(*)
            FROM information_schema.table_privileges
            WHERE table_schema = 'public'
              AND table_name = 'school_sessions'
              AND grantee IN ('anon', 'authenticated', 'PUBLIC')
            """
        ) == 0
        assert await connection.fetchval(
            """
            SELECT count(*)
            FROM information_schema.table_privileges
            WHERE table_schema = 'public'
              AND table_name = 'school_migration_markers'
              AND grantee IN ('anon', 'authenticated', 'PUBLIC')
            """
        ) == 0
    finally:
        await connection.close()
