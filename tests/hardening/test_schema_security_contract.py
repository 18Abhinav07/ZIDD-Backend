from pathlib import Path

from scripts.apply_migrations import DEFAULT_MIGRATIONS


MIGRATIONS = Path("app/db/migrations")
SCHEMA = Path("app/db/schema.sql")


def _sql(path: Path) -> str:
    return path.read_text().lower()


def test_node_attempts_has_rls_and_no_direct_api_grants():
    migration = MIGRATIONS / "2026-07-04-node-attempts-rls.sql"
    assert migration.exists()

    sql = _sql(migration)
    assert "alter table public.node_attempts enable row level security" in sql
    assert "revoke all on table public.node_attempts from anon" in sql
    assert "revoke all on table public.node_attempts from authenticated" in sql
    assert "revoke all on table public.node_attempts from public" in sql


def test_session_hardening_migration_adds_all_runtime_progress_columns():
    migration = MIGRATIONS / "2026-07-04-session-hardening.sql"
    assert migration.exists()

    sql = _sql(migration)
    for column in (
        "best_mastery",
        "node_completed",
        "completed_at",
        "completion_count",
        "last_completed_session_id",
    ):
        assert f"add column if not exists {column}" in sql


def test_session_runtime_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-06-session-runtime.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    for table in (
        "session_runtime",
        "session_messages",
        "session_turn_requests",
        "session_opening_requests",
        "session_end_requests",
    ):
        assert f"create table if not exists public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on table public.{table} from anon" in sql
        assert f"revoke all on table public.{table} from authenticated" in sql
        assert f"revoke all on table public.{table} from public" in sql


def test_session_turn_requests_have_unique_active_version_slot():
    migration = _sql(MIGRATIONS / "2026-07-06-session-runtime.sql")
    schema = _sql(SCHEMA)
    for token in ("ranked_turn_requests", "duplicate_active_version"):
        assert token in migration
    required = (
        "ranked_turn_requests",
        "duplicate_active_version",
        "create unique index if not exists idx_session_turn_requests_session_version",
        "on public.session_turn_requests(session_id, expected_version)",
        "where expected_version is not null and status in ('in_progress', 'completed')",
    )
    for token in required[2:]:
        assert token in migration
        assert token.replace("public.", "") in schema or token in schema


def test_schema_guard_requires_turn_version_slot_index():
    from app.db.schema_guard import required_schema_points

    assert "public.index.idx_session_turn_requests_session_version" in required_schema_points()


def test_schema_guard_operator_message_lists_start_idempotency_migration():
    from app.db.schema_guard import REQUIRED_MIGRATION_FILES

    assert (
        "app/db/migrations/2026-07-06-session-start-idempotency.sql"
        in REQUIRED_MIGRATION_FILES
    )


def test_session_start_requests_have_unique_source_transition_slot():
    migration = _sql(MIGRATIONS / "2026-07-06-session-start-idempotency.sql")
    schema = _sql(SCHEMA)
    for token in ("ranked_start_requests", "duplicate_source_transition"):
        assert token in migration
    required = (
        "ranked_start_requests",
        "duplicate_source_transition",
        "create unique index if not exists idx_session_start_requests_source_transition",
        "on public.session_start_requests(source_session_id, source_transition_id)",
        "where source_session_id is not null",
        "source_transition_id is not null",
        "status in ('in_progress', 'completed')",
    )
    for token in required[2:]:
        assert token in migration
        assert token.replace("public.", "") in schema or token in schema


def test_session_start_idempotency_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-06-session-start-idempotency.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    assert "create table if not exists public.session_start_requests" in sql
    assert "primary key (user_id, client_start_id)" in sql
    assert "alter table public.session_start_requests enable row level security" in sql
    assert "revoke all on table public.session_start_requests from anon" in sql
    assert "revoke all on table public.session_start_requests from authenticated" in sql
    assert "revoke all on table public.session_start_requests from public" in sql


def test_attempt_charge_idempotency_migration_is_registered_and_unique():
    migration = MIGRATIONS / "2026-07-11-attempt-charge-idempotency.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    assert "add column if not exists idempotency_key text" in sql
    assert "create unique index if not exists idx_credit_transactions_idempotency_key" in sql
    assert "on public.credit_transactions(user_id, idempotency_key)" in sql
    assert "where idempotency_key is not null" in sql


def test_career_learning_profile_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-09-career-learning-profile.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    for table in ("learning_events", "session_reports", "learner_skill_profiles"):
        assert f"create table if not exists public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on table public.{table} from anon" in sql
        assert f"revoke all on table public.{table} from authenticated" in sql
        assert f"revoke all on table public.{table} from public" in sql


def test_full_schema_includes_node_attempts_rls_contract():
    sql = _sql(SCHEMA)
    assert "create table if not exists node_attempts" in sql
    assert "alter table public.node_attempts enable row level security" in sql
    assert "revoke all on table public.node_attempts from anon" in sql
    assert "revoke all on table public.node_attempts from authenticated" in sql
    assert "revoke all on table public.node_attempts from public" in sql


def test_full_schema_includes_session_runtime_rls_contract():
    sql = _sql(SCHEMA)
    for table in (
        "session_runtime",
        "session_messages",
        "session_turn_requests",
        "session_start_requests",
        "session_opening_requests",
        "session_end_requests",
    ):
        assert f"create table if not exists {table}" in sql
        assert f"alter table {table} " in sql
        assert "enable row level security" in sql
        assert f"revoke all on table public.{table} from anon" in sql
        assert f"revoke all on table public.{table} from authenticated" in sql
        assert f"revoke all on table public.{table} from public" in sql


def test_full_schema_includes_session_lifecycle_columns():
    sql = _sql(SCHEMA)
    for column in (
        "status",
        "module_id",
        "task_type",
        "last_seen_at",
        "expires_at",
        "test_mode",
        "reattempt_of_session_id",
    ):
        assert column in sql


def test_session_messages_persist_full_transcript_metadata():
    schema = _sql(SCHEMA)
    migration = _sql(MIGRATIONS / "2026-07-06-session-runtime.sql")
    repo = Path("app/db/repo.py").read_text().lower()
    from app.db.schema_guard import REQUIRED_RUNTIME_COLUMNS

    for column in (
        "sequence_index",
        "turn_id",
        "transition_id",
        "node_id",
        "role",
        "content",
        "speaker_name",
        "speaker_id",
        "message_kind",
        "status",
    ):
        assert column in schema
        assert f"add column if not exists {column}" in migration
        assert column in migration
        assert column in REQUIRED_RUNTIME_COLUMNS["session_messages"]
        assert column in repo
