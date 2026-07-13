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


def test_school_v2_placement_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-09-school-v2-placement.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    assert "create table if not exists public.school_v2_placement_sessions" in sql
    assert "create unique index if not exists idx_school_v2_one_active_placement" in sql
    assert "alter table public.school_v2_placement_sessions enable row level security" in sql
    assert "revoke all on table public.school_v2_placement_sessions from anon" in sql
    assert "revoke all on table public.school_v2_placement_sessions from authenticated" in sql
    assert "revoke all on table public.school_v2_placement_sessions from public" in sql


def test_school_v2_practice_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-09-school-v2-practice.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    assert "create table if not exists public.school_v2_practice_sessions" in sql
    assert "create unique index if not exists idx_school_v2_one_active_practice" in sql
    assert "alter table public.school_v2_practice_sessions enable row level security" in sql
    assert "revoke all on table public.school_v2_practice_sessions from anon" in sql
    assert "revoke all on table public.school_v2_practice_sessions from authenticated" in sql
    assert "revoke all on table public.school_v2_practice_sessions from public" in sql


def test_school_v2_curriculum_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-09-school-v2-curriculum.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    assert "create table if not exists public.school_v2_curriculum_sessions" in sql
    assert "create unique index if not exists idx_school_v2_one_active_curriculum" in sql
    assert "alter table public.school_v2_curriculum_sessions enable row level security" in sql
    assert "revoke all on table public.school_v2_curriculum_sessions from anon" in sql
    assert "revoke all on table public.school_v2_curriculum_sessions from authenticated" in sql
    assert "revoke all on table public.school_v2_curriculum_sessions from public" in sql


def test_school_v3_core_migration_is_registered_and_locked_down():
    migration = MIGRATIONS / "2026-07-09-school-v3-core.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    for table in ("school_sessions", "school_language_confidence"):
        assert (
            f"create table if not exists public.{table}" in sql
            or f"create table if not exists {table}" in sql
        )
        assert (
            f"alter table public.{table} enable row level security" in sql
            or f"alter table {table} enable row level security" in sql
        )
        assert f"revoke all on table public.{table} from anon" in sql
        assert f"revoke all on table public.{table} from authenticated" in sql
        assert f"revoke all on table public.{table} from public" in sql


def test_school_rebuild_profile_migration_is_registered_and_guarded():
    migration = MIGRATIONS / "2026-07-10-school-rebuild-profile.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    assert "create table if not exists public.school_profile_versions" in sql
    assert "create unique index if not exists idx_school_profile_versions_one_active" in sql
    assert "alter table public.school_profile_versions enable row level security" in sql
    assert "revoke all on table public.school_profile_versions from anon" in sql
    assert "revoke all on table public.school_profile_versions from authenticated" in sql
    assert "revoke all on table public.school_profile_versions from public" in sql

    from app.db.schema_guard import REQUIRED_MIGRATION_FILES

    assert (
        "app/db/migrations/2026-07-10-school-rebuild-profile.sql"
        in REQUIRED_MIGRATION_FILES
    )


def test_school_answer_idempotency_migration_is_locked_down_and_guarded():
    migration = MIGRATIONS / "2026-07-11-school-answer-idempotency.sql"
    assert migration.exists()
    sql = _sql(migration)
    assert "create table if not exists public.school_answer_requests" in sql
    assert "primary key (session_id, activity_id)" in sql
    assert "references public.school_sessions(session_id) on delete cascade" in sql
    assert "claim_token text not null" in sql
    assert "check (status in ('processing', 'completed', 'failed'))" in sql
    assert "alter table public.school_answer_requests enable row level security" in sql
    assert "revoke all on table public.school_answer_requests from anon" in sql
    assert "revoke all on table public.school_answer_requests from authenticated" in sql
    assert "revoke all on table public.school_answer_requests from public" in sql

    from app.db.schema_guard import REQUIRED_MIGRATION_FILES, REQUIRED_RUNTIME_COLUMNS

    assert (
        "app/db/migrations/2026-07-11-school-answer-idempotency.sql"
        in REQUIRED_MIGRATION_FILES
    )
    assert {
        "session_id",
        "activity_id",
        "user_id",
        "answer_hash",
        "claim_token",
        "status",
        "response_json",
        "created_at",
        "updated_at",
    } <= REQUIRED_RUNTIME_COLUMNS["school_answer_requests"]


def test_school_session_lineage_migration_is_registered_locked_down_and_cuts_over():
    migration = MIGRATIONS / "2026-07-12-school-session-lineage.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    for column in ("profile_version_id", "source_placement_report_id"):
        assert f"add column if not exists {column}" in sql
    assert "references public.school_profile_versions(profile_version_id)" in sql
    assert "references public.school_placement_reports(report_id)" in sql
    assert "api_version <> 'rebuild'" in sql
    assert "state_json ->> 'profile_version_id'" in sql
    assert "state_json ->> 'source_placement_report_id'" in sql
    assert "when decision.should_expire then 'expired'" in sql
    assert "school_rebuild_active_profile_lineage" in sql
    assert "alter table public.school_sessions enable row level security" in sql
    assert "revoke all on table public.school_sessions from anon" in sql
    assert "revoke all on table public.school_sessions from authenticated" in sql
    assert "revoke all on table public.school_sessions from public" in sql
    assert "create table if not exists public.school_migration_markers" in sql
    assert "2026-07-12-school-session-lineage-cutover-v1" in sql
    assert "on conflict (migration_key) do nothing" in sql
    assert "returning migration_key" in sql
    assert "with claimed_cutover as" in sql
    assert sql.count("update public.school_sessions") == 2
    assert "where exists (select 1 from claimed_cutover)" in sql
    assert "alter table public.school_migration_markers enable row level security" in sql
    assert "revoke all on table public.school_migration_markers from anon" in sql
    assert "revoke all on table public.school_migration_markers from authenticated" in sql
    assert "revoke all on table public.school_migration_markers from public" in sql

    from app.db.schema_guard import (
        REQUIRED_MIGRATION_FILES,
        REQUIRED_RUNTIME_COLUMNS,
        required_schema_points,
    )

    assert "app/db/migrations/2026-07-12-school-session-lineage.sql" in REQUIRED_MIGRATION_FILES
    assert {"profile_version_id", "source_placement_report_id"} <= REQUIRED_RUNTIME_COLUMNS[
        "school_sessions"
    ]
    assert {"migration_key", "claimed_at"} <= REQUIRED_RUNTIME_COLUMNS[
        "school_migration_markers"
    ]
    assert "public.index.idx_school_sessions_profile_flow_updated" in required_schema_points()
    assert "public.index.idx_school_sessions_source_report" in required_schema_points()


def test_school_onboarding_draft_migration_is_additive_registered_and_guarded():
    migration = MIGRATIONS / "2026-07-12-school-onboarding-drafts.sql"
    assert migration.exists()
    assert migration.resolve() in {path.resolve() for path in DEFAULT_MIGRATIONS}

    sql = _sql(migration)
    for column in (
        "current_step",
        "draft_revision",
        "last_save_request_id",
        "last_save_payload_hash",
        "source_profile_version_id",
        "activation_request_id",
        "activation_payload_hash",
        "activation_result_profile_version_id",
    ):
        assert f"add column if not exists {column}" in sql
    for column in (
        "display_name",
        "school_name",
        "board_id",
        "target_class_no",
        "subject_ids",
        "preferred_teaching_language",
        "english_comfort",
        "learner_goal",
        "parent_goal",
        "prior_difficulty_signals",
    ):
        assert f"alter column {column} drop not null" in sql
    assert "school_profile_versions_complete_non_drafts" in sql
    assert "status <> 'active'" in sql
    assert "nullif(btrim(learner_goal), '') is not null" in sql
    assert "nullif(btrim(parent_goal), '') is not null" in sql
    assert "board_id in ('cbse', 'ncert')" in sql
    assert "subject_ids <@ '[\"english\"]'::jsonb" in sql
    assert "preferred_teaching_language in ('en', 'hi', 'hi_en')" in sql
    assert "english_comfort in ('low', 'medium', 'high')" in sql
    assert "with invalid_active_profiles as" in sql
    assert "archived_invalid_profiles as" in sql
    assert "update public.school_sessions" in sql
    assert "status in ('active', 'paused_for_masterclass')" in sql
    assert "when status = 'active'" not in sql
    assert sql.index("with invalid_active_profiles as") < sql.index(
        "add constraint school_profile_versions_complete_non_drafts"
    )
    assert "create unique index if not exists idx_school_profile_versions_one_draft" in sql
    assert "create unique index if not exists idx_school_profile_versions_activation_request" in sql

    from app.db.schema_guard import (
        REQUIRED_MIGRATION_FILES,
        REQUIRED_RUNTIME_COLUMNS,
        required_schema_points,
    )

    assert "app/db/migrations/2026-07-12-school-onboarding-drafts.sql" in REQUIRED_MIGRATION_FILES
    assert {
        "current_step",
        "draft_revision",
        "last_save_request_id",
        "last_save_payload_hash",
        "source_profile_version_id",
        "activation_request_id",
        "activation_payload_hash",
        "activation_result_profile_version_id",
    } <= REQUIRED_RUNTIME_COLUMNS["school_profile_versions"]
    assert "public.index.idx_school_profile_versions_one_draft" in required_schema_points()
    assert "public.index.idx_school_profile_versions_activation_request" in required_schema_points()
    assert (
        "public.check.school_profile_versions.school_profile_versions_complete_non_drafts"
        in required_schema_points()
    )


def test_school_draft_request_ledger_is_durable_locked_down_and_guarded():
    migration_sql = _sql(MIGRATIONS / "2026-07-12-school-onboarding-drafts.sql")
    schema_sql = _sql(SCHEMA)
    for sql in (migration_sql, schema_sql):
        assert "create table if not exists" in sql
        assert "school_profile_draft_requests" in sql
        assert "primary key (user_id, request_id)" in sql
        assert "profile_version_id uuid not null" in sql
        assert "payload_hash text not null" in sql
        assert "response_json jsonb not null" in sql
        assert "references" in sql
        assert "school_profile_versions(profile_version_id)" in sql
        assert "alter table" in sql
        assert "school_profile_draft_requests enable row level security" in sql
        assert "revoke all on table public.school_profile_draft_requests from anon" in sql
        assert (
            "revoke all on table public.school_profile_draft_requests from authenticated"
            in sql
        )
        assert "revoke all on table public.school_profile_draft_requests from public" in sql

    from app.db.schema_guard import REQUIRED_RUNTIME_COLUMNS, required_schema_points

    assert {
        "user_id",
        "request_id",
        "profile_version_id",
        "payload_hash",
        "response_json",
        "created_at",
        "updated_at",
    } <= REQUIRED_RUNTIME_COLUMNS["school_profile_draft_requests"]
    assert "public.school_profile_draft_requests.response_json" in required_schema_points()


def test_fresh_schema_supports_partial_drafts_but_checks_complete_non_drafts():
    sql = _sql(SCHEMA)
    table = sql.split("create table if not exists school_profile_versions", 1)[1].split(
        ");", 1
    )[0]
    for column in (
        "display_name",
        "school_name",
        "board_id",
        "target_class_no",
        "subject_ids",
        "preferred_teaching_language",
        "english_comfort",
        "learner_goal",
        "parent_goal",
        "prior_difficulty_signals",
    ):
        definition = next(line for line in table.splitlines() if line.strip().startswith(column))
        assert "not null" not in definition
    assert "school_profile_versions_complete_non_drafts" in table
    assert "status <> 'active'" in table
    assert "board_id in ('cbse', 'ncert')" in table
    assert "subject_ids <@ '[\"english\"]'::jsonb" in table
    assert "preferred_teaching_language in ('en', 'hi', 'hi_en')" in table
    assert "english_comfort in ('low', 'medium', 'high')" in table
    assert "idx_school_profile_versions_one_draft" in sql
    assert "idx_school_profile_versions_activation_request" in sql


def test_school_onboarding_migration_archives_legacy_blank_goal_active_profiles_only():
    sql = _sql(MIGRATIONS / "2026-07-12-school-onboarding-drafts.sql")
    cleanup = sql.split("with invalid_active_profiles as", 1)[1].split(
        "alter table public.school_profile_versions\n    drop constraint", 1
    )[0]

    assert "where status = 'active'" in cleanup
    assert "and not (" in cleanup
    assert "nullif(btrim(learner_goal), '') is not null" in cleanup
    assert "nullif(btrim(parent_goal), '') is not null" in cleanup
    assert "set status = 'archived'" in cleanup
    assert "archived_at = now()" in cleanup
    assert "set status = 'expired'" in cleanup
    assert "status in ('active', 'paused_for_masterclass')" in cleanup
    assert "where status = 'archived'" not in cleanup


def test_school_onboarding_migration_archives_duplicate_legacy_drafts_before_index():
    sql = _sql(MIGRATIONS / "2026-07-12-school-onboarding-drafts.sql")

    assert "with ranked_legacy_drafts as" in sql
    assert "partition by user_id" in sql
    assert "order by updated_at desc, profile_version_id desc" in sql
    assert "draft_rank > 1" in sql
    assert "set status = 'archived'" in sql
    assert "archived_at = now()" in sql
    archive_position = sql.index("with ranked_legacy_drafts as")
    lifecycle_position = sql.index(
        "add constraint school_profile_versions_lifecycle"
    )
    draft_index_position = sql.index(
        "create unique index if not exists idx_school_profile_versions_one_draft"
    )
    assert archive_position < lifecycle_position
    assert archive_position < draft_index_position


def test_school_onboarding_migration_normalizes_all_legacy_lifecycle_timestamps():
    sql = _sql(MIGRATIONS / "2026-07-12-school-onboarding-drafts.sql")
    lifecycle_cleanup = sql.split("with invalid_active_profiles as", 1)[0]

    assert "where status = 'draft'" in lifecycle_cleanup
    assert "activated_at = null" in lifecycle_cleanup
    assert "archived_at = null" in lifecycle_cleanup
    assert "where status = 'active'" in lifecycle_cleanup
    assert "activated_at = coalesce(activated_at, updated_at, created_at, now())" in lifecycle_cleanup
    assert "where status = 'archived'" in lifecycle_cleanup
    assert "archived_at = coalesce(archived_at, updated_at, created_at, now())" in lifecycle_cleanup


def test_school_session_links_are_same_user_owned_in_schema_and_migration():
    schema_sql = _sql(SCHEMA)
    migration_sql = _sql(MIGRATIONS / "2026-07-12-school-session-lineage.sql")

    assert "unique (user_id, session_id)" in schema_sql
    assert "foreign key (user_id, linked_session_id)" in schema_sql
    assert "references school_sessions(user_id, session_id)" in schema_sql
    assert "legacy_cross_user_links" in migration_sql
    assert "set linked_session_id = null" in migration_sql
    assert "foreign key (user_id, linked_session_id)" in migration_sql
    assert "references public.school_sessions(user_id, session_id)" in migration_sql


def test_school_lineage_integration_harness_never_cleans_public_schema():
    source = Path(
        "tests/integration/test_school_session_lineage_migration.py"
    ).read_text().lower()

    assert "drop table" not in source
    assert "cascade" not in source
    assert "_assert_empty_public_schema" in source
    assert "post_cutover_non_rebuild_session" in source


def test_school_onboarding_integration_harness_is_disposable_and_non_destructive():
    source = Path(
        "tests/integration/test_school_onboarding_draft_migration.py"
    ).read_text().lower()

    assert "drop table" not in source
    assert "cascade" not in source
    assert "_assert_empty_public_schema" in source
    assert "school_migration_test_url is required in ci" in source
    assert "school_migration_test_disposable_cluster" in source
    assert "outer_transaction.rollback" in source
    assert "ranked_legacy_drafts" in source
    assert "school_profile_versions_complete_non_drafts" in source
    assert "school_profile_draft_requests" in source


def test_school_lineage_required_migrations_preserve_dependency_order():
    from app.db.schema_guard import REQUIRED_MIGRATION_FILES

    required = list(REQUIRED_MIGRATION_FILES)
    rebuild_profile = "app/db/migrations/2026-07-10-school-rebuild-profile.sql"
    placement_reports = "app/db/migrations/2026-07-10-school-placement-reports.sql"
    answer_idempotency = "app/db/migrations/2026-07-11-school-answer-idempotency.sql"
    session_lineage = "app/db/migrations/2026-07-12-school-session-lineage.sql"

    assert placement_reports in required
    assert required.index(rebuild_profile) < required.index(placement_reports)
    assert required.index(placement_reports) < required.index(answer_idempotency)
    assert required.index(answer_idempotency) < required.index(session_lineage)


def test_full_schema_includes_school_session_lineage_contract():
    sql = _sql(SCHEMA)
    school_sessions = sql.split("create table if not exists school_sessions", 1)[1].split(
        ");", 1
    )[0]
    assert "profile_version_id" in school_sessions
    assert "references school_profile_versions(profile_version_id)" in school_sessions
    assert "source_placement_report_id" in school_sessions
    assert "foreign key (source_placement_report_id)" in sql
    assert "references school_placement_reports(report_id)" in sql
    assert "school_rebuild_active_profile_lineage" in sql
    assert "idx_school_sessions_profile_flow_updated" in sql
    assert "idx_school_sessions_source_report" in sql
    assert "create table if not exists school_migration_markers" in sql
    assert "alter table school_migration_markers enable row level security" in sql
    assert "revoke all on table public.school_migration_markers from anon" in sql
    assert "revoke all on table public.school_migration_markers from authenticated" in sql
    assert "revoke all on table public.school_migration_markers from public" in sql


def test_every_required_migration_is_in_the_default_sequence():
    from app.db.schema_guard import REQUIRED_MIGRATION_FILES

    defaults = {
        str(path.resolve().relative_to(Path.cwd().resolve()))
        for path in DEFAULT_MIGRATIONS
    }
    assert set(REQUIRED_MIGRATION_FILES) <= defaults


def test_full_schema_includes_school_answer_request_rls_contract():
    sql = _sql(SCHEMA)
    assert "create table if not exists school_answer_requests" in sql
    assert "primary key (session_id, activity_id)" in sql
    assert "claim_token text not null" in sql
    assert "alter table school_answer_requests enable row level security" in sql
    assert "revoke all on table public.school_answer_requests from anon" in sql
    assert "revoke all on table public.school_answer_requests from authenticated" in sql
    assert "revoke all on table public.school_answer_requests from public" in sql


def test_schema_guard_requires_school_v2_placement_sessions():
    from app.db.schema_guard import REQUIRED_RUNTIME_COLUMNS, required_schema_points

    required = {
        "placement_session_id",
        "user_id",
        "subject_id",
        "target_class_no",
        "preferred_language",
        "status",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    }
    assert required <= REQUIRED_RUNTIME_COLUMNS["school_v2_placement_sessions"]
    assert "public.school_v2_placement_sessions.state_json" in required_schema_points()


def test_schema_guard_requires_school_v2_practice_sessions():
    from app.db.schema_guard import REQUIRED_RUNTIME_COLUMNS, required_schema_points

    required = {
        "practice_session_id",
        "user_id",
        "subject_id",
        "target_class_no",
        "skill_id",
        "status",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    }
    assert required <= REQUIRED_RUNTIME_COLUMNS["school_v2_practice_sessions"]
    assert "public.school_v2_practice_sessions.state_json" in required_schema_points()
    assert "public.index.idx_school_v2_one_active_practice" in required_schema_points()


def test_schema_guard_requires_school_v2_curriculum_sessions():
    from app.db.schema_guard import REQUIRED_RUNTIME_COLUMNS, required_schema_points

    required = {
        "curriculum_session_id",
        "user_id",
        "subject_id",
        "target_class_no",
        "chapter_id",
        "status",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    }
    assert required <= REQUIRED_RUNTIME_COLUMNS["school_v2_curriculum_sessions"]
    assert "public.school_v2_curriculum_sessions.state_json" in required_schema_points()
    assert "public.index.idx_school_v2_one_active_curriculum" in required_schema_points()


def test_schema_guard_requires_school_rebuild_profile_versions():
    from app.db.schema_guard import REQUIRED_RUNTIME_COLUMNS, required_schema_points

    required = {
        "profile_version_id",
        "user_id",
        "status",
        "display_name",
        "school_name",
        "board_id",
        "target_class_no",
        "subject_ids",
        "preferred_teaching_language",
        "english_comfort",
        "learner_goal",
        "parent_goal",
        "prior_difficulty_signals",
        "activated_at",
    }
    assert required <= REQUIRED_RUNTIME_COLUMNS["school_profile_versions"]
    assert "public.school_profile_versions.target_class_no" in required_schema_points()
    assert "public.index.idx_school_profile_versions_one_active" in required_schema_points()


def test_full_schema_includes_node_attempts_rls_contract():
    sql = _sql(SCHEMA)
    assert "create table if not exists node_attempts" in sql
    assert "alter table public.node_attempts enable row level security" in sql
    assert "revoke all on table public.node_attempts from anon" in sql
    assert "revoke all on table public.node_attempts from authenticated" in sql
    assert "revoke all on table public.node_attempts from public" in sql


def test_full_schema_includes_school_v2_placement_rls_contract():
    sql = _sql(SCHEMA)
    assert "create table if not exists school_v2_placement_sessions" in sql
    assert "create unique index if not exists idx_school_v2_one_active_placement" in sql
    assert "alter table school_v2_placement_sessions enable row level security" in sql
    assert "revoke all on table public.school_v2_placement_sessions from anon" in sql
    assert "revoke all on table public.school_v2_placement_sessions from authenticated" in sql
    assert "revoke all on table public.school_v2_placement_sessions from public" in sql


def test_full_schema_includes_school_v2_practice_rls_contract():
    sql = _sql(SCHEMA)
    assert "create table if not exists school_v2_practice_sessions" in sql
    assert "create unique index if not exists idx_school_v2_one_active_practice" in sql
    assert "alter table school_v2_practice_sessions enable row level security" in sql
    assert "revoke all on table public.school_v2_practice_sessions from anon" in sql
    assert "revoke all on table public.school_v2_practice_sessions from authenticated" in sql
    assert "revoke all on table public.school_v2_practice_sessions from public" in sql


def test_full_schema_includes_school_v2_curriculum_rls_contract():
    sql = _sql(SCHEMA)
    assert "create table if not exists school_v2_curriculum_sessions" in sql
    assert "create unique index if not exists idx_school_v2_one_active_curriculum" in sql
    assert "alter table school_v2_curriculum_sessions enable row level security" in sql
    assert "revoke all on table public.school_v2_curriculum_sessions from anon" in sql
    assert "revoke all on table public.school_v2_curriculum_sessions from authenticated" in sql
    assert "revoke all on table public.school_v2_curriculum_sessions from public" in sql


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
