from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db import repo
from scripts.apply_migrations import _statements


MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "app/db/migrations/2026-07-12-school-onboarding-drafts.sql"
)
DISPOSABLE_DATABASE_PREFIX = "zidd_school_migration_test"
PROFILE_OLD_DRAFT = "10000000-0000-4000-8000-000000000001"
PROFILE_LATEST_DRAFT = "10000000-0000-4000-8000-000000000002"
PROFILE_INVALID_ACTIVE = "20000000-0000-4000-8000-000000000001"
PROFILE_ARCHIVED_HISTORY = "30000000-0000-4000-8000-000000000001"
PROFILE_VALID_ACTIVE = "40000000-0000-4000-8000-000000000001"
INVALID_ACTIVE_SESSION = "50000000-0000-4000-8000-000000000001"
VALID_ACTIVE_SESSION = "50000000-0000-4000-8000-000000000002"
VALID_PAUSED_SESSION = "50000000-0000-4000-8000-000000000003"
VALID_COMPLETED_SESSION = "50000000-0000-4000-8000-000000000004"
VALID_PLACEMENT_REPORT = "60000000-0000-4000-8000-000000000001"


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
            "Refusing migration test without "
            "SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER=1"
        )
    return url


async def _assert_empty_public_schema(connection) -> None:
    rows = await connection.execute(
        text(
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
    )
    table_names = [str(row.table_name) for row in rows]
    if table_names:
        pytest.fail(
            "Refusing nonempty disposable database; public already contains: "
            + ", ".join(table_names)
        )


async def _ensure_api_roles(connection) -> None:
    await connection.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    CREATE ROLE anon NOLOGIN;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'
                ) THEN
                    CREATE ROLE authenticated NOLOGIN;
                END IF;
            END
            $$
            """
        )
    )


BASELINE_SQL = f"""
CREATE TABLE public.learner_profiles (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL DEFAULT '',
    primary_motive TEXT,
    onboarding_completed_at TIMESTAMPTZ,
    school_profile JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    onboarding_state JSONB NOT NULL DEFAULT '{{}}'::jsonb
);

CREATE TABLE public.school_profile_versions (
    profile_version_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    display_name TEXT NOT NULL DEFAULT '',
    school_name TEXT NOT NULL,
    board_id TEXT NOT NULL,
    target_class_no INTEGER NOT NULL CHECK (target_class_no BETWEEN 2 AND 5),
    subject_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_teaching_language TEXT NOT NULL
        CHECK (preferred_teaching_language IN ('en', 'hi', 'hi_en')),
    english_comfort TEXT NOT NULL CHECK (english_comfort IN ('low', 'medium', 'high')),
    learner_goal TEXT NOT NULL DEFAULT '',
    parent_goal TEXT NOT NULL DEFAULT '',
    prior_difficulty_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX idx_school_profile_versions_one_active
    ON public.school_profile_versions(user_id)
    WHERE status = 'active';

CREATE TABLE public.school_sessions (
    session_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    profile_version_id UUID REFERENCES public.school_profile_versions(profile_version_id),
    api_version TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    class_no INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    current_stage TEXT NOT NULL DEFAULT '',
    linked_session_id UUID REFERENCES public.school_sessions(session_id),
    source_placement_report_id UUID,
    state_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE public.school_placement_reports (
    report_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    profile_version_id UUID NOT NULL
        REFERENCES public.school_profile_versions(profile_version_id),
    placement_session_id UUID NOT NULL
        REFERENCES public.school_sessions(session_id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.learner_profiles(user_id, display_name)
VALUES
    ('draft-user', 'Draft User'),
    ('invalid-active-user', 'Invalid Active User'),
    ('history-user', 'History User'),
    ('valid-active-user', 'Valid Active User');

INSERT INTO public.school_profile_versions
    (profile_version_id, user_id, status, display_name, school_name, board_id,
     target_class_no, subject_ids, preferred_teaching_language, english_comfort,
     learner_goal, parent_goal, prior_difficulty_signals, created_at, updated_at,
     activated_at, archived_at)
VALUES
    ('{PROFILE_OLD_DRAFT}', 'draft-user', 'draft', 'Draft User', 'Draft School',
     'cbse', 3, '["english"]'::jsonb, 'hi_en', 'medium', '', '',
     '["reading"]'::jsonb, now() - interval '2 days', now() - interval '2 days',
     now() - interval '2 days', now() - interval '2 days'),
    ('{PROFILE_LATEST_DRAFT}', 'draft-user', 'draft', 'Draft User', 'Draft School',
     'cbse', 3, '["english"]'::jsonb, 'hi_en', 'medium', '', '',
     '["reading"]'::jsonb, now() - interval '1 day', now() - interval '1 day',
     now() - interval '1 day', now() - interval '1 day'),
    ('{PROFILE_INVALID_ACTIVE}', 'invalid-active-user', 'active', 'Invalid User',
     'Invalid School', 'cbse', 3, '["english"]'::jsonb, 'hi_en', 'medium', '', '',
     '["reading"]'::jsonb, now(), now(), NULL, now()),
    ('{PROFILE_ARCHIVED_HISTORY}', 'history-user', 'archived', 'History User',
     'History School', 'unknown-board', 3, '["unknown"]'::jsonb, 'hi_en', 'medium',
     '', '', '["unknown"]'::jsonb, now(), now(), now(), NULL),
    ('{PROFILE_VALID_ACTIVE}', 'valid-active-user', 'active', 'Valid User',
     'Valid School', 'cbse', 3, '["english"]'::jsonb, 'hi_en', 'medium',
     'Learn English', '', '["reading", "vocabulary"]'::jsonb,
     now(), now(), NULL, now());

INSERT INTO public.school_sessions
    (session_id, user_id, profile_version_id, api_version, flow_type, subject_id,
     class_no, status, state_json)
VALUES
    ('{INVALID_ACTIVE_SESSION}', 'invalid-active-user', '{PROFILE_INVALID_ACTIVE}',
     'rebuild', 'placement', 'english', 3, 'paused_for_masterclass', '{{}}'::jsonb),
    ('{VALID_ACTIVE_SESSION}', 'valid-active-user', '{PROFILE_VALID_ACTIVE}',
     'rebuild', 'placement', 'english', 3, 'active', '{{}}'::jsonb),
    ('{VALID_COMPLETED_SESSION}', 'valid-active-user', '{PROFILE_VALID_ACTIVE}',
     'rebuild', 'placement_history', 'english', 3, 'complete',
     '{{"profile_version_id": "{PROFILE_VALID_ACTIVE}"}}'::jsonb);

INSERT INTO public.school_placement_reports
    (report_id, user_id, profile_version_id, placement_session_id)
VALUES
    ('{VALID_PLACEMENT_REPORT}', 'valid-active-user', '{PROFILE_VALID_ACTIVE}',
     '{VALID_COMPLETED_SESSION}');
"""


async def _execute_statements(connection, sql: str) -> None:
    for statement in _statements(sql):
        await connection.execute(text(statement))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_school_onboarding_draft_migration_and_repository_atomicity():
    url = _migration_test_url()
    sqlalchemy_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(sqlalchemy_url)
    try:
        async with engine.connect() as connection:
            outer_transaction = await connection.begin()
            try:
                database_name = await connection.scalar(text("SELECT current_database()"))
                if not str(database_name).startswith(DISPOSABLE_DATABASE_PREFIX):
                    pytest.fail("Connected database is not marked disposable")
                await _assert_empty_public_schema(connection)
                await _ensure_api_roles(connection)
                await _execute_statements(connection, BASELINE_SQL)
                await _execute_statements(connection, MIGRATION.read_text())
                await _execute_statements(connection, MIGRATION.read_text())

                migrated_rows = {
                    str(row.profile_version_id): row
                    for row in (
                        await connection.execute(
                            text(
                                """
                                SELECT profile_version_id, status, activated_at, archived_at
                                FROM public.school_profile_versions
                                """
                            )
                        )
                    )
                }
                assert migrated_rows[PROFILE_OLD_DRAFT].status == "archived"
                assert migrated_rows[PROFILE_OLD_DRAFT].archived_at is not None
                assert migrated_rows[PROFILE_LATEST_DRAFT].status == "draft"
                assert migrated_rows[PROFILE_LATEST_DRAFT].activated_at is None
                assert migrated_rows[PROFILE_LATEST_DRAFT].archived_at is None
                assert migrated_rows[PROFILE_INVALID_ACTIVE].status == "archived"
                assert migrated_rows[PROFILE_INVALID_ACTIVE].archived_at is not None
                assert migrated_rows[PROFILE_ARCHIVED_HISTORY].status == "archived"
                assert migrated_rows[PROFILE_ARCHIVED_HISTORY].archived_at is not None
                assert migrated_rows[PROFILE_VALID_ACTIVE].status == "active"
                assert migrated_rows[PROFILE_VALID_ACTIVE].activated_at is not None
                assert migrated_rows[PROFILE_VALID_ACTIVE].archived_at is None

                invalid_session = (
                    await connection.execute(
                        text(
                            """
                            SELECT status, completed_at
                            FROM public.school_sessions
                            WHERE session_id = CAST(:session_id AS uuid)
                            """
                        ),
                        {"session_id": INVALID_ACTIVE_SESSION},
                    )
                ).one()
                assert invalid_session.status == "expired"
                assert invalid_session.completed_at is not None

                indexes = {
                    str(row.indexname)
                    for row in await connection.execute(
                        text(
                            """
                            SELECT indexname
                            FROM pg_indexes
                            WHERE schemaname = 'public'
                              AND tablename = 'school_profile_versions'
                            """
                        )
                    )
                }
                assert "idx_school_profile_versions_one_draft" in indexes
                assert "idx_school_profile_versions_activation_request" in indexes
                check_names = {
                    str(row.conname)
                    for row in await connection.execute(
                        text(
                            """
                            SELECT constraint_row.conname
                            FROM pg_constraint AS constraint_row
                            JOIN pg_class AS table_row
                              ON table_row.oid = constraint_row.conrelid
                            JOIN pg_namespace AS namespace_row
                              ON namespace_row.oid = table_row.relnamespace
                            WHERE namespace_row.nspname = 'public'
                              AND table_row.relname = 'school_profile_versions'
                            """
                        )
                    )
                }
                assert "school_profile_versions_complete_non_drafts" in check_names
                assert "school_profile_versions_lifecycle" in check_names
                ledger_rls = await connection.scalar(
                    text(
                        """
                        SELECT table_row.relrowsecurity
                        FROM pg_class AS table_row
                        JOIN pg_namespace AS namespace_row
                          ON namespace_row.oid = table_row.relnamespace
                        WHERE namespace_row.nspname = 'public'
                          AND table_row.relname = 'school_profile_draft_requests'
                        """
                    )
                )
                assert ledger_rls is True

                with pytest.raises(IntegrityError):
                    async with connection.begin_nested():
                        await connection.execute(
                            text(
                                """
                                INSERT INTO public.school_profile_versions
                                    (profile_version_id, user_id, status)
                                VALUES (CAST(:profile_version_id AS uuid), 'draft-user', 'draft')
                                """
                            ),
                            {"profile_version_id": str(uuid4())},
                        )
                with pytest.raises(IntegrityError):
                    async with connection.begin_nested():
                        await connection.execute(
                            text(
                                """
                                UPDATE public.school_profile_versions
                                SET board_id = 'invalid-board'
                                WHERE profile_version_id = CAST(:profile_version_id AS uuid)
                                """
                            ),
                            {"profile_version_id": PROFILE_VALID_ACTIVE},
                        )

                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )
                try:
                    with pytest.raises(ValueError, match="archived_school_api_version"):
                        await repo.upsert_school_session(
                            session,
                            session_id=str(uuid4()),
                            user_id="valid-active-user",
                            api_version="v3",
                            flow_type="placement",
                            subject_id="english",
                            class_no=3,
                            status="active",
                            state_json={},
                        )
                    await repo.upsert_school_session(
                        session,
                        session_id=VALID_PAUSED_SESSION,
                        user_id="valid-active-user",
                        api_version="rebuild",
                        flow_type="curriculum",
                        subject_id="english",
                        class_no=3,
                        status="paused_for_masterclass",
                        profile_version_id=PROFILE_VALID_ACTIVE,
                        state_json={"status": "paused_for_masterclass"},
                    )
                    first_request_id = str(uuid4())
                    draft = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=None,
                        expected_revision=None,
                        current_step=4,
                        request_id=first_request_id,
                        payload_hash="invalid-material-edit",
                        patch={"display_name": "X"},
                    )
                    updated_draft = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=str(draft["profile_version_id"]),
                        expected_revision=int(draft["draft_revision"]),
                        current_step=4,
                        request_id=str(uuid4()),
                        payload_hash="invalid-material-edit-2",
                        patch={"school_name": "Updated Valid School"},
                    )
                    replay = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=None,
                        expected_revision=None,
                        current_step=4,
                        request_id=first_request_id,
                        payload_hash="invalid-material-edit",
                        patch={"display_name": "X"},
                    )
                    assert replay == draft
                    assert updated_draft["draft_revision"] == 2
                    with pytest.raises(IntegrityError):
                        await repo.activate_school_profile_draft(
                            session,
                            user_id="valid-active-user",
                            profile_version_id=str(draft["profile_version_id"]),
                            expected_revision=int(updated_draft["draft_revision"]),
                            request_id=str(uuid4()),
                            payload_hash="invalid-activation",
                        )
                finally:
                    await session.close()

                active_profile = (
                    await connection.execute(
                        text(
                            """
                            SELECT profile_version_id::text AS profile_version_id
                            FROM public.school_profile_versions
                            WHERE user_id = 'valid-active-user' AND status = 'active'
                            """
                        )
                    )
                ).one()
                assert active_profile.profile_version_id == PROFILE_VALID_ACTIVE
                saved_draft = (
                    await connection.execute(
                        text(
                            """
                            SELECT status
                            FROM public.school_profile_versions
                            WHERE profile_version_id = CAST(:profile_version_id AS uuid)
                            """
                        ),
                        {"profile_version_id": str(draft["profile_version_id"])},
                    )
                ).one()
                assert saved_draft.status == "draft"
                ledger_rows = await connection.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM public.school_profile_draft_requests
                        WHERE user_id = 'valid-active-user'
                        """
                    )
                )
                assert ledger_rows == 2
                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )
                try:
                    compatible_draft = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=str(draft["profile_version_id"]),
                        expected_revision=int(updated_draft["draft_revision"]),
                        current_step=4,
                        request_id=str(uuid4()),
                        payload_hash="compatible-profile-edit",
                        patch={
                            "display_name": "Valid User",
                            "school_name": "Valid School",
                            "parent_goal": "Build a steady reading habit",
                        },
                    )
                    activation_request_id = str(uuid4())
                    replacement = await repo.activate_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=str(compatible_draft["profile_version_id"]),
                        expected_revision=int(compatible_draft["draft_revision"]),
                        request_id=activation_request_id,
                        payload_hash="compatible-profile-activation",
                    )
                    activation_replay = await repo.activate_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=str(compatible_draft["profile_version_id"]),
                        expected_revision=int(compatible_draft["draft_revision"]),
                        request_id=activation_request_id,
                        payload_hash="compatible-profile-activation",
                    )
                finally:
                    await session.close()

                assert str(replacement["profile_version_id"]) == str(
                    compatible_draft["profile_version_id"]
                )
                assert str(activation_replay["profile_version_id"]) == str(
                    replacement["profile_version_id"]
                )
                rebound_sessions = {
                    str(row.session_id): row
                    for row in await connection.execute(
                        text(
                            """
                            SELECT session_id::text AS session_id,
                                   status,
                                   profile_version_id::text AS profile_version_id,
                                   state_json ->> 'profile_version_id' AS state_profile_version_id
                            FROM public.school_sessions
                            WHERE session_id IN (
                                CAST(:active_session_id AS uuid),
                                CAST(:paused_session_id AS uuid),
                                CAST(:completed_session_id AS uuid)
                            )
                            """
                        ),
                        {
                            "active_session_id": VALID_ACTIVE_SESSION,
                            "paused_session_id": VALID_PAUSED_SESSION,
                            "completed_session_id": VALID_COMPLETED_SESSION,
                        },
                    )
                }
                assert rebound_sessions[VALID_ACTIVE_SESSION].status == "active"
                assert rebound_sessions[VALID_PAUSED_SESSION].status == (
                    "paused_for_masterclass"
                )
                assert rebound_sessions[VALID_COMPLETED_SESSION].status == "complete"
                for active_session_id in (VALID_ACTIVE_SESSION, VALID_PAUSED_SESSION):
                    active_session = rebound_sessions[active_session_id]
                    assert active_session.profile_version_id == str(
                        compatible_draft["profile_version_id"]
                    )
                    assert active_session.state_profile_version_id == str(
                        compatible_draft["profile_version_id"]
                    )
                completed_session = rebound_sessions[VALID_COMPLETED_SESSION]
                assert completed_session.profile_version_id == PROFILE_VALID_ACTIVE
                assert completed_session.state_profile_version_id == PROFILE_VALID_ACTIVE
                report_profile_version_id = await connection.scalar(
                    text(
                        """
                        SELECT profile_version_id::text
                        FROM public.school_placement_reports
                        WHERE report_id = CAST(:report_id AS uuid)
                        """
                    ),
                    {"report_id": VALID_PLACEMENT_REPORT},
                )
                assert report_profile_version_id == PROFILE_VALID_ACTIVE

                await connection.execute(
                    text(
                        """
                        CREATE OR REPLACE FUNCTION public.fail_school_profile_update()
                        RETURNS trigger
                        LANGUAGE plpgsql
                        AS $$
                        BEGIN
                            IF NEW.user_id = 'valid-active-user'
                               AND NEW.school_profile ->> 'parent_goal' = 'Force rollback'
                            THEN
                                RAISE EXCEPTION 'injected school profile update failure';
                            END IF;
                            RETURN NEW;
                        END;
                        $$
                        """
                    )
                )
                await connection.execute(
                    text(
                        """
                        CREATE TRIGGER fail_school_profile_update_trigger
                        BEFORE UPDATE ON public.learner_profiles
                        FOR EACH ROW EXECUTE FUNCTION public.fail_school_profile_update()
                        """
                    )
                )
                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )
                try:
                    rollback_draft = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=None,
                        expected_revision=None,
                        current_step=4,
                        request_id=str(uuid4()),
                        payload_hash="rollback-compatible-edit",
                        patch={"parent_goal": "Force rollback"},
                    )
                    with pytest.raises(DBAPIError):
                        await repo.activate_school_profile_draft(
                            session,
                            user_id="valid-active-user",
                            profile_version_id=str(
                                rollback_draft["profile_version_id"]
                            ),
                            expected_revision=int(rollback_draft["draft_revision"]),
                            request_id=str(uuid4()),
                            payload_hash="rollback-compatible-activation",
                        )
                finally:
                    await session.close()

                active_after_rollback = await connection.scalar(
                    text(
                        """
                        SELECT profile_version_id::text
                        FROM public.school_profile_versions
                        WHERE user_id = 'valid-active-user' AND status = 'active'
                        """
                    )
                )
                assert active_after_rollback == str(replacement["profile_version_id"])
                statuses_after_rollback = {
                    str(row.session_id): row.status
                    for row in await connection.execute(
                        text(
                            """
                            SELECT session_id::text AS session_id, status
                            FROM public.school_sessions
                            WHERE session_id IN (
                                CAST(:active_session_id AS uuid),
                                CAST(:paused_session_id AS uuid)
                            )
                            """
                        ),
                        {
                            "active_session_id": VALID_ACTIVE_SESSION,
                            "paused_session_id": VALID_PAUSED_SESSION,
                        },
                    )
                }
                assert statuses_after_rollback == {
                    VALID_ACTIVE_SESSION: "active",
                    VALID_PAUSED_SESSION: "paused_for_masterclass",
                }
                await connection.execute(
                    text(
                        "DROP TRIGGER fail_school_profile_update_trigger "
                        "ON public.learner_profiles"
                    )
                )
                await connection.execute(
                    text("DROP FUNCTION public.fail_school_profile_update()")
                )
                await connection.execute(
                    text(
                        """
                        UPDATE public.school_profile_versions
                        SET status = 'archived', archived_at = now(), updated_at = now()
                        WHERE profile_version_id = CAST(:profile_version_id AS uuid)
                          AND status = 'draft'
                        """
                    ),
                    {"profile_version_id": str(rollback_draft["profile_version_id"])},
                )

                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )
                try:
                    noop_draft = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=None,
                        expected_revision=None,
                        current_step=4,
                        request_id=str(uuid4()),
                        payload_hash="noop-edit",
                        patch={},
                    )
                    noop_result = await repo.activate_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=str(noop_draft["profile_version_id"]),
                        expected_revision=int(noop_draft["draft_revision"]),
                        request_id=str(uuid4()),
                        payload_hash="noop-activation",
                    )
                finally:
                    await session.close()

                assert str(noop_result["profile_version_id"]) == str(
                    replacement["profile_version_id"]
                )
                noop_draft_status = await connection.scalar(
                    text(
                        """
                        SELECT status
                        FROM public.school_profile_versions
                        WHERE profile_version_id = CAST(:profile_version_id AS uuid)
                        """
                    ),
                    {"profile_version_id": str(noop_draft["profile_version_id"])},
                )
                assert noop_draft_status == "archived"
                noop_session_rows = list(
                    await connection.execute(
                        text(
                            """
                            SELECT status, profile_version_id::text AS profile_version_id
                            FROM public.school_sessions
                            WHERE session_id IN (
                                CAST(:active_session_id AS uuid),
                                CAST(:paused_session_id AS uuid),
                                CAST(:completed_session_id AS uuid)
                            )
                            """
                        ),
                        {
                            "active_session_id": VALID_ACTIVE_SESSION,
                            "paused_session_id": VALID_PAUSED_SESSION,
                            "completed_session_id": VALID_COMPLETED_SESSION,
                        },
                    )
                )
                assert {row.status for row in noop_session_rows} == {
                    "active",
                    "paused_for_masterclass",
                    "complete",
                }
                noop_profiles_by_status = {
                    row.status: row.profile_version_id for row in noop_session_rows
                }
                assert noop_profiles_by_status["active"] == str(
                    replacement["profile_version_id"]
                )
                assert noop_profiles_by_status["paused_for_masterclass"] == str(
                    replacement["profile_version_id"]
                )
                assert noop_profiles_by_status["complete"] == PROFILE_VALID_ACTIVE

                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                )
                try:
                    material_draft = await repo.save_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=None,
                        expected_revision=None,
                        current_step=4,
                        request_id=str(uuid4()),
                        payload_hash="material-edit",
                        patch={"preferred_teaching_language": "en"},
                    )
                    material_result = await repo.activate_school_profile_draft(
                        session,
                        user_id="valid-active-user",
                        profile_version_id=str(material_draft["profile_version_id"]),
                        expected_revision=int(material_draft["draft_revision"]),
                        request_id=str(uuid4()),
                        payload_hash="material-activation",
                    )
                finally:
                    await session.close()

                assert str(material_result["profile_version_id"]) == str(
                    material_draft["profile_version_id"]
                )
                expired_sessions = {
                    str(row.session_id): row
                    for row in await connection.execute(
                        text(
                            """
                            SELECT session_id::text AS session_id, status, completed_at
                            FROM public.school_sessions
                            WHERE session_id IN (
                                CAST(:active_session_id AS uuid),
                                CAST(:paused_session_id AS uuid)
                            )
                            """
                        ),
                        {
                            "active_session_id": VALID_ACTIVE_SESSION,
                            "paused_session_id": VALID_PAUSED_SESSION,
                        },
                    )
                }
                for expired_session in expired_sessions.values():
                    assert expired_session.status == "expired"
                    assert expired_session.completed_at is not None

                migration_source = MIGRATION.read_text().lower()
                assert "ranked_legacy_drafts" in migration_source
                assert "school_profile_versions_complete_non_drafts" in migration_source
                assert "school_profile_draft_requests" in migration_source
            finally:
                await outer_transaction.rollback()
    finally:
        await engine.dispose()
