from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.content.school.release_loader import load_release_manifest
from app.db import schema_guard
import scripts.apply_migrations as apply_migrations
import scripts.preflight_school_migrations as preflight_migrations
from scripts.apply_migrations import (
    DEFAULT_MIGRATIONS,
    MigrationHashMismatch,
    _apply_canonical_migration,
    _ordered_school_prefix_length,
    _statements,
)
from scripts.preflight_school_migrations import (
    APPROVED_CERTIFICATION_EPOCH,
    APPROVED_TAXONOMY_VERSION,
    PREDECESSOR_COLUMNS,
    PREDECESSOR_CONSTRAINTS,
    approved_release_mapping,
    collect_preflight,
    redact_database_url,
)


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "app/db/migrations/2026-07-13-001-school-release-authority.sql"
DISPOSABLE_DATABASE_PREFIX = "zidd_school_migration_test"
LOOPBACK_MIGRATION_URL = (
    "postgresql://postgres:test@127.0.0.1/zidd_school_migration_test_safety"
)

AVATAR_IDS = (
    "stuttering_sam",
    "fluent_finn",
    "brave_bella",
    "quiet_quint",
    "tech_black",
    "casual_purple",
    "casual_male",
    "casual_female",
    "casual_blue",
)

PROFILE_1 = "10000000-0000-4000-8000-000000000001"
PROFILE_2 = "10000000-0000-4000-8000-000000000002"
PROFILE_DRAFT = "10000000-0000-4000-8000-000000000003"
PROFILE_NCERT = "10000000-0000-4000-8000-000000000004"
SESSION_SUPPORTED = "20000000-0000-4000-8000-000000000001"
SESSION_LINKED = "20000000-0000-4000-8000-000000000002"
SESSION_LEGACY = "20000000-0000-4000-8000-000000000003"
SESSION_UNSUPPORTED = "20000000-0000-4000-8000-000000000004"
SESSION_OTHER_SUBJECT = "20000000-0000-4000-8000-000000000005"
SESSION_TERMINAL_SUPPORTED = "20000000-0000-4000-8000-000000000006"
SESSION_NCERT = "20000000-0000-4000-8000-000000000007"
SESSION_USER_MISMATCH = "20000000-0000-4000-8000-000000000008"
REPORT_SUPPORTED = "30000000-0000-4000-8000-000000000001"
REPORT_LEGACY = "30000000-0000-4000-8000-000000000002"
REPORT_IDENTITY_MISMATCH = "30000000-0000-4000-8000-000000000003"
REPORT_USER_MISMATCH = "30000000-0000-4000-8000-000000000004"


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


def test_statement_splitter_preserves_semicolons_inside_dollar_quotes():
    sql = """
    DO $$
    BEGIN
        PERFORM 1;
        PERFORM 'two;three';
    END
    $$;
    CREATE FUNCTION public.example() RETURNS void AS $body$
    BEGIN
        PERFORM 4;
    END;
    $body$ LANGUAGE plpgsql;
    SELECT 5;
    """

    statements = _statements(sql)

    assert len(statements) == 3
    assert "PERFORM 1;" in statements[0]
    assert "$body$ LANGUAGE plpgsql" in statements[1]
    assert statements[2] == "SELECT 5"


def test_school_migration_predecessor_accepts_any_ordered_prefix():
    assert _ordered_school_prefix_length((False, False, False)) == 0
    assert _ordered_school_prefix_length((True, True, False)) == 2
    assert _ordered_school_prefix_length((True, True, True)) == 3


def test_school_migration_predecessor_rejects_dependency_holes():
    with pytest.raises(RuntimeError, match="dependency_order"):
        _ordered_school_prefix_length((True, False, True))


def test_release_mapping_is_derived_from_the_approved_manifest():
    manifest = load_release_manifest()
    mapping = approved_release_mapping()

    assert [row["class_no"] for row in mapping] == [2, 3, 4, 5]
    assert [row["curriculum_release_id"] for row in mapping] == [
        release.curriculum_release_id for release in manifest.releases
    ]
    assert {row["taxonomy_version"] for row in mapping} == {
        APPROVED_TAXONOMY_VERSION
    }
    assert {row["certification_epoch"] for row in mapping} == {
        APPROVED_CERTIFICATION_EPOCH
    }
    for release, row in zip(manifest.releases, mapping, strict=True):
        payload = release.model_dump(mode="json")
        digest = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        assert row["release_digest"] == digest


def test_database_url_redaction_never_emits_credentials():
    redacted = redact_database_url(
        "postgresql://sensitive-user:sensitive-password@db.example.com:5432/zidd"
    )

    assert redacted == {
        "database": "zidd",
        "host": "db.example.com",
        "port": 5432,
        "scheme": "postgresql",
    }
    assert "sensitive" not in json.dumps(redacted)


class _FakeMarkerResult:
    def __init__(self, file_sha256: str):
        self.file_sha256 = file_sha256

    def mappings(self):
        return self

    def first(self):
        return {"file_sha256": self.file_sha256}


class _FakeMarkerConnection:
    def __init__(self, file_sha256: str):
        self.file_sha256 = file_sha256
        self.executed: list[str] = []

    async def scalar(self, statement):
        self.executed.append(str(statement))
        return True

    async def execute(self, statement, parameters=None):
        self.executed.append(str(statement))
        return _FakeMarkerResult(self.file_sha256)


class _FakeAbsentMarkerResult:
    def mappings(self):
        return self

    def first(self):
        return None


class _FakeRawMigrationConnection:
    def __init__(self):
        self.metadata_statements: list[str] = []
        self.raw_statements: list[str] = []

    async def scalar(self, statement):
        self.metadata_statements.append(str(statement))
        return True

    async def execute(self, statement, parameters=None):
        self.metadata_statements.append(str(statement))
        if "$body$" in str(statement) and getattr(statement, "_bindparams", {}):
            raise AssertionError("raw migration SQL was parsed as bind parameters")
        return _FakeAbsentMarkerResult()

    async def exec_driver_sql(self, statement):
        self.raw_statements.append(statement)


@pytest.mark.asyncio
async def test_canonical_migration_executes_json_dollar_quote_through_raw_driver(
    tmp_path,
):
    migration = tmp_path / "canonical-json.sql"
    migration.write_text(
        """
        DO $body$
        DECLARE
            payload jsonb := '{"class_no":2,"subject_id":"english"}'::jsonb;
        BEGIN
            PERFORM payload;
        END;
        $body$;
        """,
        encoding="utf-8",
    )
    connection = _FakeRawMigrationConnection()

    applied = await _apply_canonical_migration(connection, migration)

    assert applied is True
    assert len(connection.raw_statements) == 1
    assert '"class_no":2' in connection.raw_statements[0]
    assert "$body$" in connection.raw_statements[0]


@pytest.mark.asyncio
async def test_marker_hash_mismatch_refuses_before_migration_sql():
    connection = _FakeMarkerConnection("0" * 64)

    with pytest.raises(MigrationHashMismatch, match="hash_mismatch"):
        await _apply_canonical_migration(connection, MIGRATION)

    assert len(connection.executed) == 4
    assert all("CREATE TABLE" not in statement for statement in connection.executed)
    assert all("ALTER TABLE" not in statement for statement in connection.executed)


@pytest.mark.asyncio
async def test_exact_marker_hash_skips_without_migration_sql():
    connection = _FakeMarkerConnection(hashlib.sha256(MIGRATION.read_bytes()).hexdigest())

    applied = await _apply_canonical_migration(connection, MIGRATION)

    assert applied is False
    assert len(connection.executed) == 4


@pytest.mark.asyncio
async def test_public_apply_requires_preflight_output_for_canonical_migration():
    with pytest.raises(RuntimeError, match="preflight.*output"):
        await apply_migrations.apply([MIGRATION])


@pytest.mark.asyncio
async def test_failed_preflight_persists_evidence_before_engine_or_sql(
    monkeypatch,
    tmp_path,
):
    output = tmp_path / "school-preflight.json"
    result = {
        "active": {
            "profiles": {"count": 1, "ids": [PROFILE_1]},
            "reports": {"count": 0, "ids": []},
            "sessions": {"count": 1, "ids": [SESSION_UNSUPPORTED]},
        },
        "ambiguous_lineage": {
            "reports": [],
            "sessions": [{"session_id": SESSION_UNSUPPORTED}],
        },
        "approved_release_mapping": [],
        "database": {
            "database": "zidd_school_migration_test_canonical",
            "host": "127.0.0.1",
            "port": 55433,
            "scheme": "postgresql",
        },
        "ok": False,
        "predecessor": {},
    }
    calls: list[str] = []

    async def fake_preflight(connection, database_url):
        await connection.assert_concurrent_write_blocked()
        calls.append("preflight_in_transaction")
        return result

    class FakeConnection:
        writes_blocked = False

        async def execute(self, statement, parameters=None):
            rendered = str(statement)
            if "pg_advisory_xact_lock" in rendered:
                calls.append("advisory_lock")
            elif "LOCK TABLE" in rendered:
                self.writes_blocked = True
                calls.append("table_locks")
            else:
                raise AssertionError(f"migration SQL executed: {rendered}")

        async def assert_concurrent_write_blocked(self):
            if not self.writes_blocked:
                raise AssertionError("writer slipped between preflight and table lock")

    connection = FakeConnection()

    monkeypatch.setattr(
        apply_migrations,
        "get_settings",
        lambda: type("Settings", (), {"supabase_pooler_url": "postgresql://redacted"})(),
    )
    monkeypatch.setattr(
        apply_migrations,
        "collect_preflight_on_connection",
        fake_preflight,
        raising=False,
    )
    monkeypatch.setattr(
        apply_migrations,
        "get_engine",
        lambda: _BoundEngine(connection),
    )

    with pytest.raises(RuntimeError, match="preflight_failed"):
        await apply_migrations.apply([MIGRATION], preflight_output=output)

    assert calls == ["advisory_lock", "table_locks", "preflight_in_transaction"]
    assert json.loads(output.read_text()) == result
    assert "redacted" not in output.read_text()
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


@pytest.mark.asyncio
async def test_preflight_evidence_write_failure_executes_zero_migration_sql(
    monkeypatch,
    tmp_path,
):
    events: list[str] = []

    class FakeConnection:
        async def execute(self, statement, parameters=None):
            rendered = str(statement)
            if "pg_advisory_xact_lock" in rendered:
                events.append("advisory_lock")
                return None
            if "LOCK TABLE" in rendered:
                events.append("table_locks")
                return None
            raise AssertionError(f"migration SQL executed: {rendered}")

    async def good_preflight(connection, database_url):
        events.append("preflight")
        return {"ok": True, "database": {}}

    def fail_write(result, output):
        events.append("evidence_write")
        raise OSError("disk full")

    monkeypatch.setattr(
        apply_migrations,
        "get_settings",
        lambda: type("Settings", (), {"supabase_pooler_url": "postgresql://redacted"})(),
    )
    monkeypatch.setattr(apply_migrations, "get_engine", lambda: _BoundEngine(FakeConnection()))
    monkeypatch.setattr(
        apply_migrations,
        "collect_preflight_on_connection",
        good_preflight,
        raising=False,
    )
    monkeypatch.setattr(apply_migrations, "write_preflight_output", fail_write)

    with pytest.raises(OSError, match="disk full"):
        await apply_migrations.apply(
            [MIGRATION],
            preflight_output=tmp_path / "preflight.json",
        )

    assert events == ["advisory_lock", "table_locks", "preflight", "evidence_write"]


@pytest.mark.asyncio
async def test_migration_snapshot_is_executed_after_checked_in_file_changes(tmp_path):
    migration = tmp_path / "canonical.sql"
    migration.write_text("SELECT 'snapshotted'", encoding="utf-8")
    snapshot = apply_migrations.snapshot_migrations([migration])[0]
    migration.write_text("SELECT 'mutated'", encoding="utf-8")
    connection = _FakeRawMigrationConnection()

    await _apply_canonical_migration(connection, snapshot)

    assert connection.raw_statements == ["SELECT 'snapshotted'"]
    assert snapshot.sha256 == hashlib.sha256(b"SELECT 'snapshotted'").hexdigest()


def test_legacy_school_migration_hash_locks_match_exact_current_bytes(monkeypatch):
    expected = {
        "2026-07-09-school-v2-placement.sql": "e536ccd5adef032a3dc0f76d4056d57c96f278d6132e519e10bcbb921d5f721e",
        "2026-07-09-school-v2-practice.sql": "d6f431b3de13721fe0b520230a81236af04da6d529aec274143d68e460ce38cd",
        "2026-07-09-school-v2-curriculum.sql": "12715900c832802ee1d729cc1eb733c8ce4e846da63ad91555ae221f5d03ca30",
        "2026-07-09-school-v3-core.sql": "97ac9cd25453517ffad8fa0baefe4b03701fea5a947b22a8aa340fbcb4094714",
        "2026-07-10-school-rebuild-profile.sql": "4541df5f0a0e11ebc4f3e48dc13620fa4ba8319033a44cd3168832fa1b0cc7fe",
        "2026-07-10-school-placement-reports.sql": "68cbad3ee1fcc29700a69c2be423fc184c3647335bed6f60f2636854d1732254",
        "2026-07-11-school-answer-idempotency.sql": "d195958bbb3400c77a5255a837d95f9943382549863c04cac26dd7f77a02973b",
        "2026-07-12-school-session-lineage.sql": "6998e23b00c8c1d5d4866063a15e98be1a2be8308debf01cc0e07277c719ec15",
        "2026-07-12-school-onboarding-drafts.sql": "2d57b79d672ceeef699ee41386223bac8751308d7e901576ae5592d285c719ca",
    }
    locked = {
        path.name: digest
        for path, digest in apply_migrations.LOCKED_LEGACY_SCHOOL_MIGRATION_SHA256.items()
    }

    assert locked == expected
    for path, digest in apply_migrations.LOCKED_LEGACY_SCHOOL_MIGRATION_SHA256.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest

    changed = next(iter(apply_migrations.LOCKED_LEGACY_SCHOOL_MIGRATION_SHA256))
    snapshot = apply_migrations.MigrationSnapshot(
        path=changed,
        content=b"mutated",
        text="mutated",
        sha256=hashlib.sha256(b"mutated").hexdigest(),
    )
    with pytest.raises(MigrationHashMismatch, match="legacy_school_migration_hash_mismatch"):
        apply_migrations._validate_locked_migration_hashes([snapshot])


class _FakePreflightConnection:
    async def fetch(self, query: str, *args):
        if "information_schema.columns" in query:
            return [
                {"table_name": table, "column_name": column}
                for table, columns in PREDECESSOR_COLUMNS.items()
                for column in columns
            ]
        if "FROM pg_constraint" in query:
            return [
                {
                    "constraint_name": name,
                    "definition": "CHECK (true)",
                    "validated": True,
                    "update_action": "a",
                    "delete_action": "a",
                }
                for name in PREDECESSOR_CONSTRAINTS
            ]
        if "FROM public.school_profile_versions" in query:
            return [{"id": PROFILE_1}]
        if "FROM public.school_sessions" in query:
            return [
                {
                    "id": SESSION_LINKED,
                    "api_version": "rebuild",
                    "session_user_id": "user-1",
                    "profile_exists": True,
                    "profile_user_id": "user-1",
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 3,
                },
                {
                    "id": SESSION_UNSUPPORTED,
                    "api_version": "rebuild",
                    "session_user_id": "user-2",
                    "profile_exists": True,
                    "profile_user_id": "user-2",
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 6,
                },
            ]
        if "FROM public.school_placement_reports" in query:
            return [
                {
                    "id": REPORT_SUPPORTED,
                    "api_version": "rebuild",
                    "report_user_id": "user-1",
                    "profile_exists": True,
                    "profile_user_id": "user-1",
                    "placement_user_id": "user-1",
                    "report_profile_version_id": PROFILE_1,
                    "placement_profile_version_id": PROFILE_1,
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 3,
                    "placement_subject_id": "english",
                    "placement_class_no": 3,
                }
            ]
        raise AssertionError(query)

    async def fetchrow(self, query: str, *args):
        assert "FROM pg_index" in query
        return {
            "indexdef": (
                "CREATE UNIQUE INDEX idx_school_sessions_one_active_flow "
                "ON public.school_sessions "
                "(user_id, flow_type, subject_id, class_no) "
                "WHERE status IN ('active', 'paused_for_masterclass')"
            ),
            "indisvalid": True,
            "indisready": True,
        }


@pytest.mark.asyncio
async def test_preflight_reports_active_ids_and_ambiguous_lineage_deterministically():
    database_url = "postgresql://user:password@127.0.0.1/zidd"

    first = await collect_preflight(_FakePreflightConnection(), database_url)
    second = await collect_preflight(_FakePreflightConnection(), database_url)

    assert first == second
    assert first["ok"] is False
    assert first["active"] == {
        "profiles": {"count": 1, "ids": [PROFILE_1]},
        "reports": {"count": 1, "ids": [REPORT_SUPPORTED]},
        "sessions": {
            "count": 2,
            "ids": [SESSION_LINKED, SESSION_UNSUPPORTED],
        },
    }
    assert first["ambiguous_lineage"]["sessions"] == [
        {
            "board_id": "cbse",
            "class_no": 6,
            "reason": "no_unique_approved_release",
            "session_id": SESSION_UNSUPPORTED,
            "subject_id": "english",
        }
    ]
    assert first["database"] == {
        "database": "zidd",
        "host": "127.0.0.1",
        "port": 5432,
        "scheme": "postgresql",
    }


def test_release_authority_migration_is_appended_and_guarded():
    assert DEFAULT_MIGRATIONS[-2].resolve() == MIGRATION.resolve()
    assert DEFAULT_MIGRATIONS[-1].name == "2026-07-14-integrated-domain-contract.sql"
    assert DEFAULT_MIGRATIONS.count(MIGRATION) == 1
    assert (
        "app/db/migrations/2026-07-13-001-school-release-authority.sql"
        in schema_guard.REQUIRED_MIGRATION_FILES
    )

    required = schema_guard.REQUIRED_RUNTIME_COLUMNS
    assert {
        "curriculum_release_id",
        "board_id",
        "subject_id",
        "class_no",
        "academic_year",
        "manifest",
        "release_digest",
        "status",
        "effective_from",
        "effective_through",
        "retired_on",
        "created_at",
        "updated_at",
    } <= required["school_curriculum_releases"]
    assert {"file_sha256", "applied_at"} <= required["school_migration_markers"]
    assert {
        "curriculum_release_id",
        "taxonomy_version",
        "certification_epoch",
    } <= required["school_sessions"]
    assert {
        "curriculum_release_id",
        "taxonomy_version",
        "certification_epoch",
    } <= required["school_placement_reports"]
    assert {"coach_avatar_id", "coach_palette_id"} <= required[
        "school_profile_versions"
    ]


def test_release_authority_schema_and_sql_are_locked_down():
    migration_sql = MIGRATION.read_text().lower()
    schema_sql = (ROOT / "app/db/schema.sql").read_text().lower()
    for sql in (migration_sql, schema_sql):
        assert "school_curriculum_releases" in sql
        assert "unique (board_id, subject_id, class_no, academic_year, release_digest)" in sql
        assert "curriculum_release_id text" in sql
        assert "manifest jsonb not null" in sql
        assert "release_digest text not null" in sql
        assert "enable row level security" in sql
        assert "school_curriculum_releases from anon" in sql
        assert "school_curriculum_releases from authenticated" in sql
        assert "school_curriculum_releases from public" in sql
        assert "idx_school_sessions_one_active_flow" in sql
        assert "(user_id, flow_type, subject_id, class_no)" in sql
        assert "where status in ('active', 'paused_for_masterclass')" in sql
    assert "reject_school_curriculum_release_identity_change" in migration_sql
    assert "return old" in migration_sql
    assert "return new" not in migration_sql
    seeded_payloads = [
        json.loads(payload)
        for _tag, payload in re.findall(
            r"\$(release_\d+)\$(\{.*?\})\$\1\$::jsonb",
            MIGRATION.read_text(),
            flags=re.DOTALL,
        )
    ]
    manifest = load_release_manifest()
    assert seeded_payloads == [
        release.model_dump(mode="json") for release in manifest.releases
    ]
    for avatar_id in AVATAR_IDS:
        assert avatar_id in migration_sql


def test_release_sql_uses_exact_mapping_and_one_current_uniqueness():
    migration_sql = MIGRATION.read_text().lower()
    schema_sql = (ROOT / "app/db/schema.sql").read_text().lower()
    for sql in (migration_sql, schema_sql):
        assert "idx_school_curriculum_releases_one_current" in sql
        assert "(board_id, subject_id, class_no, academic_year)" in sql
        assert "where status = 'current'" in sql
        assert "school_curriculum_releases_identity_digest_unique" in sql

    session_backfill = migration_sql.split(
        "update public.school_sessions as school_session", 1
    )[1].split("update public.school_placement_reports", 1)[0]
    report_backfill = migration_sql.rsplit(
        "with approved_release_mapping", 1
    )[1].split("create unique index", 1)[0]
    for release in load_release_manifest().releases:
        assert release.curriculum_release_id in session_backfill
        assert release.curriculum_release_id in report_backfill
    assert "release.status" not in session_backfill
    assert "release.status" not in report_backfill
    assert "school_curriculum_releases as release" not in session_backfill
    assert "school_curriculum_releases as release" not in report_backfill
    assert "join public.school_profile_versions as profile" in session_backfill
    assert "profile.user_id = school_session.user_id" in session_backfill
    assert "profile.board_id = mapping.board_id" in session_backfill
    assert "placement.user_id = report.user_id" in report_backfill
    assert "profile.user_id = report.user_id" in report_backfill
    assert "placement.profile_version_id = report.profile_version_id" in report_backfill
    assert "placement.subject_id = report.subject_id" in report_backfill
    assert "placement.class_no = report.target_class_no" in report_backfill


def test_seed_conflicts_never_update_immutable_release_data():
    migration_sql = MIGRATION.read_text().lower()
    seed_sql = migration_sql.split(
        "insert into public.school_curriculum_releases", 1
    )[1].split("alter table public.school_migration_markers", 1)[0]

    assert "on conflict (curriculum_release_id) do nothing" in seed_sql
    assert "school_curriculum_release_seed_mismatch" in seed_sql
    assert "do update" not in seed_sql


def test_additive_reconciliation_never_overwrites_persisted_report_lineage():
    reconciliation_sql = (
        ROOT
        / "app/db/migrations/2026-07-14-school-additive-reconciliation.sql"
    ).read_text().lower()

    assert "school_session_lineage_conflict" in reconciliation_sql
    assert "school_session.source_placement_report_id is null" in reconciliation_sql
    assert "when source_placement_report_id is not null" in reconciliation_sql
    assert "then source_placement_report_id" in reconciliation_sql


def test_schema_bootstrap_seeds_exact_canonical_release_payloads():
    schema_sql = (ROOT / "app/db/schema.sql").read_text()
    seeded_payloads = [
        json.loads(payload)
        for _tag, payload in re.findall(
            r"\$(release_\d+)\$(\{.*?\})\$\1\$::jsonb",
            schema_sql,
            flags=re.DOTALL,
        )
    ]

    assert seeded_payloads == [
        release.model_dump(mode="json")
        for release in load_release_manifest().releases
    ]


def test_preflight_active_index_rejects_extra_predicate_clause():
    definition = (
        "CREATE UNIQUE INDEX idx_school_sessions_one_active_flow "
        "ON public.school_sessions "
        "(user_id, flow_type, subject_id, class_no) "
        "WHERE status IN ('active', 'paused_for_masterclass') "
        "AND api_version = 'rebuild'"
    )

    assert preflight_migrations._active_index_is_exact(definition) is False


@pytest.mark.asyncio
async def test_preflight_rejects_duplicate_approved_mapping(monkeypatch):
    mapping = approved_release_mapping()
    duplicate = [*mapping, dict(mapping[0])]
    monkeypatch.setattr(
        preflight_migrations,
        "approved_release_mapping",
        lambda: duplicate,
    )

    result = await preflight_migrations.collect_preflight(
        _FakePreflightConnection(),
        "postgresql://user:password@127.0.0.1/zidd",
    )

    assert result["ok"] is False
    assert result["duplicate_approved_mappings"] == [
        {
            "board_id": "cbse",
            "class_no": 2,
            "count": 2,
            "subject_id": "english",
        }
    ]


class _RecordingPreflightConnection(_FakePreflightConnection):
    def __init__(self):
        self.queries: list[str] = []

    async def fetch(self, query: str, *args):
        self.queries.append(query)
        if "api_version = 'rebuild'" in query and "school_placement_reports" not in query:
            return [
                {
                    "id": SESSION_SUPPORTED,
                    "api_version": "rebuild",
                    "session_user_id": "user-1",
                    "profile_exists": True,
                    "profile_user_id": "user-1",
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 3,
                },
                {
                    "id": SESSION_TERMINAL_SUPPORTED,
                    "api_version": "rebuild",
                    "session_user_id": "user-2",
                    "profile_exists": True,
                    "profile_user_id": "user-2",
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 4,
                },
            ]
        if "placement.api_version = 'rebuild'" in query:
            return [
                {
                    "id": REPORT_SUPPORTED,
                    "api_version": "rebuild",
                    "report_user_id": "user-1",
                    "profile_exists": True,
                    "profile_user_id": "user-1",
                    "placement_user_id": "user-1",
                    "report_profile_version_id": PROFILE_1,
                    "placement_profile_version_id": PROFILE_1,
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 3,
                    "placement_subject_id": "english",
                    "placement_class_no": 3,
                },
                {
                    "id": REPORT_LEGACY,
                    "api_version": "rebuild",
                    "report_user_id": "user-2",
                    "profile_exists": True,
                    "profile_user_id": "user-2",
                    "placement_user_id": "user-2",
                    "report_profile_version_id": PROFILE_2,
                    "placement_profile_version_id": PROFILE_2,
                    "profile_board_id": "cbse",
                    "subject_id": "english",
                    "class_no": 4,
                    "placement_subject_id": "english",
                    "placement_class_no": 4,
                },
            ]
        return await super().fetch(query, *args)


@pytest.mark.asyncio
async def test_preflight_inspects_every_rebuild_backfill_candidate():
    connection = _RecordingPreflightConnection()

    result = await collect_preflight(
        connection,
        "postgresql://user:password@127.0.0.1/zidd",
    )

    assert result["lineage_candidates"] == {
        "reports": {
            "count": 2,
            "ids": [REPORT_SUPPORTED, REPORT_LEGACY],
        },
        "sessions": {
            "count": 2,
            "ids": [SESSION_SUPPORTED, SESSION_TERMINAL_SUPPORTED],
        },
    }
    assert result["ambiguous_lineage"]["reports"] == []
    assert any("api_version = 'rebuild'" in query for query in connection.queries)
    assert any("placement.api_version = 'rebuild'" in query for query in connection.queries)


@pytest.mark.asyncio
async def test_preflight_rejects_inexact_required_constraint_definitions():
    result = await collect_preflight(
        _FakePreflightConnection(),
        "postgresql://user:password@127.0.0.1/zidd",
    )

    checks = result["predecessor"]["constraints"]
    assert all("exact" in check for check in checks)
    assert not all(check["exact"] for check in checks)
    assert result["ok"] is False


def test_preflight_rejects_not_valid_or_cascading_foreign_key():
    definition = (
        "FOREIGN KEY (user_id, linked_session_id) "
        "REFERENCES school_sessions(user_id, session_id)"
    )

    assert not preflight_migrations._constraint_is_exact(
        "school_sessions_linked_same_user",
        definition,
        validated=False,
        update_action="a",
        delete_action="a",
    )
    assert not preflight_migrations._constraint_is_exact(
        "school_sessions_linked_same_user",
        definition,
        validated=True,
        update_action="c",
        delete_action="a",
    )


@pytest.mark.asyncio
async def test_standalone_preflight_disables_asyncpg_statement_cache(monkeypatch):
    captured = {}

    class Transaction:
        async def start(self):
            return None

        async def rollback(self):
            return None

    class Connection:
        def transaction(self, **kwargs):
            captured["transaction"] = kwargs
            return Transaction()

        async def close(self):
            return None

    async def connect(url, **kwargs):
        captured["url"] = url
        captured["connect"] = kwargs
        return Connection()

    async def collect(connection, database_url):
        return {"ok": True}

    monkeypatch.setattr(preflight_migrations.asyncpg, "connect", connect)
    monkeypatch.setattr(preflight_migrations, "collect_preflight", collect)

    result = await preflight_migrations.run_preflight(
        "postgresql+asyncpg://user:secret@127.0.0.1/zidd"
    )

    assert result == {"ok": True}
    assert captured["connect"] == {"statement_cache_size": 0}
    assert captured["transaction"]["readonly"] is True


def test_preflight_output_is_private_and_deterministic(tmp_path):
    output = tmp_path / "evidence.json"
    result = {"ok": True, "active": {"sessions": {"ids": [SESSION_SUPPORTED]}}}

    preflight_migrations.write_preflight_output(result, output)
    first = output.read_bytes()
    preflight_migrations.write_preflight_output(result, output)

    assert output.read_bytes() == first
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


def test_standalone_preflight_cli_requires_output_and_never_prints_ids(
    monkeypatch,
    tmp_path,
    capsys,
):
    output = tmp_path / "preflight.json"
    result = {
        "ok": False,
        "active": {"sessions": {"count": 1, "ids": [SESSION_SUPPORTED]}},
    }

    async def run(database_url):
        return result

    monkeypatch.setattr(preflight_migrations, "run_preflight", run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "preflight_school_migrations.py",
            "--database-url",
            "postgresql://user:secret@127.0.0.1/zidd",
            "--output",
            str(output),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        preflight_migrations.main()

    stdout = capsys.readouterr().out
    assert exc_info.value.code == 1
    assert str(output) in stdout
    assert SESSION_SUPPORTED not in stdout
    assert "secret" not in stdout
    assert SESSION_SUPPORTED in output.read_text()
    assert stat.S_IMODE(output.stat().st_mode) == 0o600

    monkeypatch.setattr(
        sys,
        "argv",
        ["preflight_school_migrations.py", "--database-url", "postgresql://local"],
    )
    with pytest.raises(SystemExit) as missing_output:
        preflight_migrations.main()
    assert missing_output.value.code == 2


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
CREATE TABLE public.learner_profiles (user_id TEXT PRIMARY KEY);

CREATE TABLE public.school_profile_versions (
    profile_version_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    status TEXT NOT NULL,
    board_id TEXT,
    target_class_no INTEGER,
    subject_ids JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.school_sessions (
    session_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    profile_version_id UUID REFERENCES public.school_profile_versions(profile_version_id),
    api_version TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    class_no INTEGER NOT NULL,
    status TEXT NOT NULL,
    linked_session_id UUID,
    state_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT school_rebuild_active_profile_lineage CHECK (
        api_version <> 'rebuild'
        OR status NOT IN ('active', 'paused_for_masterclass')
        OR profile_version_id IS NOT NULL
    ),
    CONSTRAINT school_sessions_user_session_unique UNIQUE (user_id, session_id),
    CONSTRAINT school_sessions_linked_same_user
        FOREIGN KEY (user_id, linked_session_id)
        REFERENCES public.school_sessions(user_id, session_id)
);

CREATE UNIQUE INDEX idx_school_sessions_one_active_flow
ON public.school_sessions(user_id, flow_type, subject_id, class_no)
WHERE status IN ('active', 'paused_for_masterclass');

CREATE TABLE public.school_placement_reports (
    report_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    profile_version_id UUID NOT NULL REFERENCES public.school_profile_versions(profile_version_id),
    placement_session_id UUID NOT NULL REFERENCES public.school_sessions(session_id),
    subject_id TEXT NOT NULL,
    target_class_no INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.school_migration_markers (
    migration_key TEXT PRIMARY KEY,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.school_profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_placement_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_migration_markers ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.school_profile_versions TO anon, authenticated, PUBLIC;
GRANT ALL ON TABLE public.school_sessions TO anon, authenticated, PUBLIC;
GRANT ALL ON TABLE public.school_placement_reports TO anon, authenticated, PUBLIC;
GRANT ALL ON TABLE public.school_migration_markers TO anon, authenticated, PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO PUBLIC;
"""


SEEDED_SQL = f"""
INSERT INTO public.learner_profiles(user_id) VALUES ('user-1'), ('user-2');

INSERT INTO public.school_profile_versions
    (profile_version_id, user_id, status, board_id, target_class_no, subject_ids)
VALUES
    ('{PROFILE_1}', 'user-1', 'active', 'cbse', 3, '["english"]'::jsonb),
    ('{PROFILE_2}', 'user-2', 'active', 'cbse', 4, '["english"]'::jsonb),
    ('{PROFILE_DRAFT}', 'user-1', 'draft', NULL, NULL, NULL),
    ('{PROFILE_NCERT}', 'user-2', 'archived', 'ncert', 4, '["english"]'::jsonb);

INSERT INTO public.school_sessions
    (session_id, user_id, profile_version_id, api_version, flow_type, subject_id,
     class_no, status)
VALUES
    ('{SESSION_SUPPORTED}', 'user-1', '{PROFILE_1}', 'rebuild', 'placement',
     'english', 3, 'complete'),
    ('{SESSION_LINKED}', 'user-1', '{PROFILE_1}', 'rebuild', 'recap',
     'english', 3, 'active'),
    ('{SESSION_LEGACY}', 'user-2', '{PROFILE_2}', 'v3', 'placement',
     'english', 4, 'complete'),
    ('{SESSION_UNSUPPORTED}', 'user-2', '{PROFILE_2}', 'rebuild', 'placement',
     'english', 6, 'complete'),
    ('{SESSION_OTHER_SUBJECT}', 'user-2', '{PROFILE_2}', 'rebuild', 'placement',
     'math', 4, 'complete'),
    ('{SESSION_NCERT}', 'user-2', '{PROFILE_NCERT}', 'rebuild', 'placement',
     'english', 4, 'complete'),
    ('{SESSION_USER_MISMATCH}', 'user-1', '{PROFILE_2}', 'rebuild', 'placement',
     'english', 4, 'complete');

UPDATE public.school_sessions
SET linked_session_id = '{SESSION_SUPPORTED}'
WHERE session_id = '{SESSION_LINKED}';

INSERT INTO public.school_placement_reports
    (report_id, user_id, profile_version_id, placement_session_id, subject_id,
     target_class_no)
VALUES
    ('{REPORT_SUPPORTED}', 'user-1', '{PROFILE_1}', '{SESSION_SUPPORTED}',
     'english', 3),
    ('{REPORT_LEGACY}', 'user-2', '{PROFILE_2}', '{SESSION_LEGACY}',
     'english', 4),
    ('{REPORT_IDENTITY_MISMATCH}', 'user-1', '{PROFILE_1}', '{SESSION_SUPPORTED}',
     'english', 4),
    ('{REPORT_USER_MISMATCH}', 'user-2', '{PROFILE_1}', '{SESSION_SUPPORTED}',
     'english', 3);
"""


async def _execute_sql(connection, sql: str) -> None:
    for statement in _statements(sql):
        await connection.exec_driver_sql(statement)


async def _execute_schema_bootstrap(connection) -> None:
    for statement in _statements((ROOT / "app/db/schema.sql").read_text()):
        normalized = " ".join(statement.lower().split())
        if normalized == "create extension if not exists vector":
            continue
        if normalized.startswith("create table if not exists memory_entries"):
            await connection.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
                    session_id TEXT,
                    competency_node TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            continue
        await connection.exec_driver_sql(statement)


async def _assert_release_authority_absent(connection) -> None:
    assert await connection.scalar(
        text("SELECT to_regclass('public.school_curriculum_releases')")
    ) is None
    rows = await connection.execute(
        text(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (
                  (table_name = 'school_sessions'
                   AND column_name IN (
                       'curriculum_release_id',
                       'taxonomy_version',
                       'certification_epoch'
                   ))
                  OR
                  (table_name = 'school_placement_reports'
                   AND column_name IN (
                       'curriculum_release_id',
                       'taxonomy_version',
                       'certification_epoch'
                   ))
              )
            """
        )
    )
    assert rows.all() == []


class _BoundConnectionContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, traceback):
        return None


class _BoundEngine:
    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return _BoundConnectionContext(self.connection)

    async def dispose(self):
        return None


def test_cli_requires_preflight_output_for_canonical_apply(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["apply_migrations.py", str(MIGRATION)])

    with pytest.raises(SystemExit) as exc_info:
        apply_migrations.main()

    assert exc_info.value.code == 2
    assert "--preflight-output is required" in capsys.readouterr().err


def test_default_migrations_keep_explicit_school_dependency_order():
    school_files = [
        path.name
        for path in DEFAULT_MIGRATIONS
        if "school" in path.name
        or path.name == "2026-07-14-integrated-domain-contract.sql"
    ]
    assert school_files == [
        "2026-07-09-school-v2-placement.sql",
        "2026-07-09-school-v2-practice.sql",
        "2026-07-09-school-v2-curriculum.sql",
        "2026-07-09-school-v3-core.sql",
        "2026-07-10-school-rebuild-profile.sql",
        "2026-07-10-school-placement-reports.sql",
        "2026-07-11-school-answer-idempotency.sql",
        "2026-07-12-school-session-lineage.sql",
        "2026-07-12-school-onboarding-drafts.sql",
        "2026-07-14-school-additive-reconciliation.sql",
        "2026-07-13-001-school-release-authority.sql",
        "2026-07-14-integrated-domain-contract.sql",
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_schema_bootstrap_public_apply_preflight_guard_and_idempotency(
    monkeypatch,
    tmp_path,
):
    url = _migration_test_url()
    engine = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://", 1))
    try:
        async with engine.connect() as connection:
            outer_transaction = await connection.begin()
            try:
                await _assert_empty_public_schema(connection)
                await _ensure_api_roles(connection)
                await _execute_schema_bootstrap(connection)
                await schema_guard.validate_runtime_schema(connection)

                monkeypatch.setattr(
                    apply_migrations,
                    "get_settings",
                    lambda: type("Settings", (), {"supabase_pooler_url": url})(),
                )
                monkeypatch.setattr(
                    apply_migrations,
                    "get_engine",
                    lambda: _BoundEngine(connection),
                )
                output = tmp_path / "bootstrap-preflight.json"

                await apply_migrations.apply(
                    DEFAULT_MIGRATIONS,
                    preflight_output=output,
                    reconcile_predecessor=True,
                )
                first_marker_time = await connection.scalar(
                    text(
                        """
                        SELECT applied_at
                        FROM public.school_migration_markers
                        WHERE migration_key = :migration_key
                        """
                    ),
                    {"migration_key": MIGRATION.name},
                )
                await apply_migrations.apply(
                    DEFAULT_MIGRATIONS,
                    preflight_output=output,
                    reconcile_predecessor=True,
                )
                second_marker_time = await connection.scalar(
                    text(
                        """
                        SELECT applied_at
                        FROM public.school_migration_markers
                        WHERE migration_key = :migration_key
                        """
                    ),
                    {"migration_key": MIGRATION.name},
                )

                evidence = json.loads(output.read_text())
                assert evidence["ok"] is True
                assert evidence["database"]["database"].startswith(
                    DISPOSABLE_DATABASE_PREFIX
                )
                assert "postgres:test" not in output.read_text()
                assert first_marker_time == second_marker_time
                await schema_guard.validate_runtime_schema(connection)
            finally:
                await outer_transaction.rollback()
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reconciliation_resumes_a_valid_school_prefix_eight(
    monkeypatch,
    tmp_path,
):
    url = _migration_test_url()
    engine = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://", 1))
    try:
        async with engine.connect() as connection:
            outer_transaction = await connection.begin()
            try:
                await _assert_empty_public_schema(connection)
                await _ensure_api_roles(connection)
                await _execute_schema_bootstrap(connection)
                await _execute_sql(
                    connection,
                    """
                    DROP TABLE public.school_profile_draft_requests;
                    ALTER TABLE public.school_sessions
                        DROP CONSTRAINT IF EXISTS school_sessions_source_placement_report_id_fkey,
                        DROP CONSTRAINT IF EXISTS school_rebuild_active_profile_lineage,
                        DROP CONSTRAINT IF EXISTS school_sessions_linked_same_user,
                        DROP CONSTRAINT IF EXISTS school_sessions_user_session_unique,
                        DROP CONSTRAINT IF EXISTS school_sessions_curriculum_release_id_fkey;
                    ALTER TABLE public.school_sessions
                        DROP COLUMN profile_version_id CASCADE,
                        DROP COLUMN source_placement_report_id CASCADE,
                        DROP COLUMN curriculum_release_id CASCADE,
                        DROP COLUMN taxonomy_version,
                        DROP COLUMN certification_epoch;
                    ALTER TABLE public.school_sessions
                        ADD CONSTRAINT school_sessions_linked_session_id_fkey
                        FOREIGN KEY (linked_session_id)
                        REFERENCES public.school_sessions(session_id);
                    ALTER TABLE public.school_profile_versions
                        DROP CONSTRAINT IF EXISTS school_profile_versions_complete_non_drafts,
                        DROP CONSTRAINT IF EXISTS school_profile_versions_lifecycle,
                        DROP CONSTRAINT IF EXISTS school_profile_versions_coach_identity,
                        DROP COLUMN current_step,
                        DROP COLUMN draft_revision,
                        DROP COLUMN last_save_request_id,
                        DROP COLUMN last_save_payload_hash,
                        DROP COLUMN source_profile_version_id CASCADE,
                        DROP COLUMN activation_request_id,
                        DROP COLUMN activation_payload_hash,
                        DROP COLUMN activation_result_profile_version_id CASCADE,
                        DROP COLUMN coach_avatar_id,
                        DROP COLUMN coach_palette_id;
                    ALTER TABLE public.school_placement_reports
                        DROP CONSTRAINT IF EXISTS school_placement_reports_curriculum_release_id_fkey,
                        DROP COLUMN curriculum_release_id,
                        DROP COLUMN taxonomy_version,
                        DROP COLUMN certification_epoch;
                    ALTER TABLE public.school_migration_markers
                        DROP CONSTRAINT IF EXISTS school_migration_markers_file_sha256,
                        DROP COLUMN file_sha256,
                        DROP COLUMN applied_at;
                    """,
                )

                monkeypatch.setattr(
                    apply_migrations,
                    "get_settings",
                    lambda: type("Settings", (), {"supabase_pooler_url": url})(),
                )
                monkeypatch.setattr(
                    apply_migrations,
                    "get_engine",
                    lambda: _BoundEngine(connection),
                )

                async def apply_disposable_final_schema(_connection):
                    await _execute_schema_bootstrap(_connection)

                monkeypatch.setattr(
                    apply_migrations,
                    "_apply_final_schema",
                    apply_disposable_final_schema,
                )
                await apply_migrations.apply(
                    DEFAULT_MIGRATIONS,
                    preflight_output=tmp_path / "prefix-eight-preflight.json",
                    reconcile_predecessor=True,
                )

                assert await connection.scalar(
                    text(
                        """
                        SELECT count(*) = 5
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'school_sessions'
                          AND column_name IN (
                              'profile_version_id',
                              'source_placement_report_id',
                              'curriculum_release_id',
                              'taxonomy_version',
                              'certification_epoch'
                          )
                        """
                    )
                )
                await schema_guard.validate_runtime_schema(connection)
            finally:
                await outer_transaction.rollback()
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_release_migration_applies_to_empty_predecessor_schema():
    url = _migration_test_url()
    engine = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://", 1))
    try:
        async with engine.connect() as connection:
            outer_transaction = await connection.begin()
            try:
                await _assert_empty_public_schema(connection)
                await _ensure_api_roles(connection)
                await _execute_sql(connection, BASELINE_SQL)
                await _assert_release_authority_absent(connection)

                applied = await _apply_canonical_migration(connection, MIGRATION)

                assert applied is True
                assert await connection.scalar(
                    text("SELECT count(*) FROM public.school_curriculum_releases")
                ) == 4
            finally:
                await outer_transaction.rollback()
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_release_migration_upgrades_copy_and_enforces_authority():
    url = _migration_test_url()
    engine = create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://", 1))
    try:
        async with engine.connect() as connection:
            outer_transaction = await connection.begin()
            try:
                await _assert_empty_public_schema(connection)
                await _ensure_api_roles(connection)
                await _execute_sql(connection, BASELINE_SQL)
                await _execute_sql(connection, SEEDED_SQL)
                await _assert_release_authority_absent(connection)
                pre_migration_grants = await connection.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM information_schema.table_privileges
                        WHERE table_schema = 'public'
                          AND table_name IN (
                              'school_migration_markers',
                              'school_profile_versions',
                              'school_sessions',
                              'school_placement_reports'
                          )
                          AND grantee IN ('anon', 'authenticated', 'PUBLIC')
                        """
                    )
                )
                assert pre_migration_grants > 0

                preflight = await preflight_migrations.collect_preflight_on_connection(
                    connection,
                    url,
                )
                assert preflight["ok"] is False
                session_reasons = {
                    (row["session_id"], row["reason"])
                    for row in preflight["ambiguous_lineage"]["sessions"]
                }
                report_reasons = {
                    (row["report_id"], row["reason"])
                    for row in preflight["ambiguous_lineage"]["reports"]
                }
                assert (SESSION_NCERT, "no_unique_approved_release") in session_reasons
                assert (
                    SESSION_USER_MISMATCH,
                    "session_profile_user_mismatch",
                ) in session_reasons
                assert (
                    REPORT_IDENTITY_MISMATCH,
                    "report_placement_identity_mismatch",
                ) in report_reasons
                assert (
                    REPORT_USER_MISMATCH,
                    "report_profile_placement_user_mismatch",
                ) in report_reasons

                assert await _apply_canonical_migration(connection, MIGRATION) is True
                assert await _apply_canonical_migration(connection, MIGRATION) is False

                release_rows = (
                    await connection.execute(
                        text(
                            """
                            SELECT curriculum_release_id, class_no, manifest,
                                   release_digest
                            FROM public.school_curriculum_releases
                            ORDER BY class_no
                            """
                        )
                    )
                ).mappings().all()
                expected = approved_release_mapping()
                assert [row["curriculum_release_id"] for row in release_rows] == [
                    row["curriculum_release_id"] for row in expected
                ]
                assert [row["release_digest"] for row in release_rows] == [
                    row["release_digest"] for row in expected
                ]
                manifest = load_release_manifest()
                assert [row["manifest"] for row in release_rows] == [
                    release.model_dump(mode="json") for release in manifest.releases
                ]

                sessions = {
                    str(row.session_id): row
                    for row in await connection.execute(
                        text(
                            """
                            SELECT session_id, curriculum_release_id,
                                   taxonomy_version, certification_epoch
                            FROM public.school_sessions
                            """
                        )
                    )
                }
                for session_id in (SESSION_SUPPORTED, SESSION_LINKED):
                    assert sessions[session_id].curriculum_release_id.endswith("c3_cesa1")
                    assert sessions[session_id].taxonomy_version == APPROVED_TAXONOMY_VERSION
                    assert sessions[session_id].certification_epoch == APPROVED_CERTIFICATION_EPOCH
                for session_id in (
                    SESSION_LEGACY,
                    SESSION_UNSUPPORTED,
                    SESSION_OTHER_SUBJECT,
                    SESSION_NCERT,
                    SESSION_USER_MISMATCH,
                ):
                    assert sessions[session_id].curriculum_release_id is None
                    assert sessions[session_id].taxonomy_version is None
                    assert sessions[session_id].certification_epoch is None

                reports = {
                    str(row.report_id): row
                    for row in await connection.execute(
                        text(
                            """
                            SELECT report_id, curriculum_release_id,
                                   taxonomy_version, certification_epoch
                            FROM public.school_placement_reports
                            """
                        )
                    )
                }
                assert reports[REPORT_SUPPORTED].curriculum_release_id.endswith("c3_cesa1")
                assert reports[REPORT_LEGACY].curriculum_release_id is None
                assert reports[REPORT_IDENTITY_MISMATCH].curriculum_release_id is None
                assert reports[REPORT_USER_MISMATCH].curriculum_release_id is None

                profiles = await connection.execute(
                    text(
                        """
                        SELECT coach_avatar_id, coach_palette_id
                        FROM public.school_profile_versions
                        ORDER BY profile_version_id
                        """
                    )
                )
                for row in profiles:
                    assert row.coach_avatar_id in AVATAR_IDS
                    assert row.coach_palette_id == row.coach_avatar_id

                immutable_savepoint = await connection.begin_nested()
                try:
                    with pytest.raises(DBAPIError, match="immutable"):
                        await connection.execute(
                            text(
                                """
                                UPDATE public.school_curriculum_releases
                                SET manifest = jsonb_set(
                                    manifest,
                                    '{book_title}',
                                    '"changed"'
                                )
                                WHERE class_no = 2
                                """
                            )
                        )
                finally:
                    await immutable_savepoint.rollback()

                delete_savepoint = await connection.begin_nested()
                try:
                    with pytest.raises(DBAPIError, match="immutable"):
                        await connection.execute(
                            text(
                                "DELETE FROM public.school_curriculum_releases "
                                "WHERE class_no = 2"
                            )
                        )
                finally:
                    await delete_savepoint.rollback()

                fk_savepoint = await connection.begin_nested()
                try:
                    with pytest.raises(IntegrityError):
                        await connection.execute(
                            text(
                                """
                                UPDATE public.school_sessions
                                SET curriculum_release_id = 'missing-release'
                                WHERE session_id = CAST(:session_id AS uuid)
                                """
                            ),
                            {"session_id": SESSION_SUPPORTED},
                        )
                finally:
                    await fk_savepoint.rollback()

                index_row = (
                    await connection.execute(
                        text(
                            """
                            SELECT indexdef
                            FROM pg_indexes
                            WHERE schemaname = 'public'
                              AND indexname = 'idx_school_sessions_one_active_flow'
                            """
                        )
                    )
                ).one()
                assert schema_guard._exact_runtime_index_matches(
                    "idx_school_sessions_one_active_flow",
                    index_row.indexdef,
                )

                current_release_savepoint = await connection.begin_nested()
                try:
                    with pytest.raises(IntegrityError):
                        await connection.execute(
                            text(
                                """
                                INSERT INTO public.school_curriculum_releases
                                    (curriculum_release_id, board_id, subject_id,
                                     class_no, academic_year, manifest,
                                     release_digest, status, effective_from,
                                     effective_through)
                                VALUES
                                    ('duplicate-current', 'cbse', 'english', 3,
                                     '2026-27', '{}'::jsonb, :digest, 'current',
                                     DATE '2026-04-01', DATE '2027-03-31')
                                """
                            ),
                            {"digest": "f" * 64},
                        )
                finally:
                    await current_release_savepoint.rollback()

                security_rows = (
                    await connection.execute(
                        text(
                            """
                            SELECT table_row.relname AS table_name,
                                   table_row.relrowsecurity AS rls_enabled
                            FROM pg_class AS table_row
                            JOIN pg_namespace AS namespace_row
                              ON namespace_row.oid = table_row.relnamespace
                            WHERE namespace_row.nspname = 'public'
                              AND table_row.relname IN (
                                  'school_curriculum_releases',
                                  'school_migration_markers',
                                  'school_profile_versions',
                                  'school_sessions',
                                  'school_placement_reports'
                              )
                            ORDER BY table_row.relname
                            """
                        )
                    )
                ).mappings().all()
                client_grants = await connection.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM information_schema.table_privileges
                        WHERE table_schema = 'public'
                          AND table_name IN (
                              'school_curriculum_releases',
                              'school_migration_markers',
                              'school_profile_versions',
                              'school_sessions',
                              'school_placement_reports'
                          )
                          AND grantee IN ('anon', 'authenticated', 'PUBLIC')
                        """
                    )
                )
                assert [row["table_name"] for row in security_rows] == sorted(
                    [
                        "school_curriculum_releases",
                        "school_migration_markers",
                        "school_profile_versions",
                        "school_sessions",
                        "school_placement_reports",
                    ]
                )
                assert all(row["rls_enabled"] for row in security_rows)
                assert client_grants == 0

                marker = (
                    await connection.execute(
                        text(
                            """
                            SELECT file_sha256, applied_at
                            FROM public.school_migration_markers
                            WHERE migration_key = :migration_key
                            """
                        ),
                        {"migration_key": MIGRATION.name},
                    )
                ).one()
                assert marker.file_sha256 == hashlib.sha256(MIGRATION.read_bytes()).hexdigest()
                assert marker.applied_at is not None

                mismatch_savepoint = await connection.begin_nested()
                try:
                    await connection.execute(
                        text(
                            """
                            UPDATE public.school_migration_markers
                            SET file_sha256 = :different_hash
                            WHERE migration_key = :migration_key
                            """
                        ),
                        {
                            "different_hash": "0" * 64,
                            "migration_key": MIGRATION.name,
                        },
                    )
                    with pytest.raises(MigrationHashMismatch, match="hash_mismatch"):
                        await _apply_canonical_migration(connection, MIGRATION)
                finally:
                    await mismatch_savepoint.rollback()
            finally:
                if outer_transaction.is_active:
                    await outer_transaction.rollback()
    finally:
        await engine.dispose()


def test_migration_test_url_rejects_non_loopback_and_requires_disposable_flag(monkeypatch):
    monkeypatch.setenv(
        "SCHOOL_MIGRATION_TEST_URL",
        "postgresql://postgres:test@db.example.com/zidd_school_migration_test_safety",
    )
    monkeypatch.setenv("SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER", "1")
    with pytest.raises(pytest.fail.Exception, match="loopback host"):
        _migration_test_url()

    monkeypatch.setenv("SCHOOL_MIGRATION_TEST_URL", LOOPBACK_MIGRATION_URL)
    monkeypatch.delenv("SCHOOL_MIGRATION_TEST_DISPOSABLE_CLUSTER", raising=False)
    with pytest.raises(pytest.fail.Exception, match="DISPOSABLE_CLUSTER=1"):
        _migration_test_url()
