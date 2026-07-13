"""Apply the checked-in idempotent Supabase migrations.

This is intentionally small: migrations in app/db/migrations are already written
as safe CREATE/ALTER IF NOT EXISTS statements. The script gives local/dev
operators a repeatable command instead of pasting SQL into the dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import hashlib
import re
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.db.engine import get_engine
from app.db.schema_guard import validate_runtime_schema
from scripts.preflight_school_migrations import (
    collect_preflight_on_connection,
    write_preflight_output,
)


DEFAULT_MIGRATIONS = [
    ROOT / "app/db/migrations/2026-07-04-google-auth.sql",
    ROOT / "app/db/migrations/2026-07-04-onboarding-profile.sql",
    ROOT / "app/db/migrations/2026-07-04-cloud-state-tables.sql",
    ROOT / "app/db/migrations/2026-07-04-session-hardening.sql",
    ROOT / "app/db/migrations/2026-07-04-node-attempts-rls.sql",
    ROOT / "app/db/migrations/2026-07-05-career-simulation-personalization.sql",
    ROOT / "app/db/migrations/2026-07-06-session-runtime.sql",
    ROOT / "app/db/migrations/2026-07-06-session-start-idempotency.sql",
    ROOT / "app/db/migrations/2026-07-08-prep-turn-evaluations.sql",
    ROOT / "app/db/migrations/2026-07-09-career-learning-profile.sql",
    ROOT / "app/db/migrations/2026-07-09-school-v2-placement.sql",
    ROOT / "app/db/migrations/2026-07-09-school-v2-practice.sql",
    ROOT / "app/db/migrations/2026-07-09-school-v2-curriculum.sql",
    ROOT / "app/db/migrations/2026-07-09-school-v3-core.sql",
    ROOT / "app/db/migrations/2026-07-10-school-rebuild-profile.sql",
    ROOT / "app/db/migrations/2026-07-10-school-placement-reports.sql",
    ROOT / "app/db/migrations/2026-07-11-school-answer-idempotency.sql",
    ROOT / "app/db/migrations/2026-07-12-school-session-lineage.sql",
    ROOT / "app/db/migrations/2026-07-12-school-onboarding-drafts.sql",
    ROOT / "app/db/migrations/2026-07-13-001-school-release-authority.sql",
]

CANONICAL_MIGRATIONS = frozenset(
    {ROOT / "app/db/migrations/2026-07-13-001-school-release-authority.sql"}
)

LOCKED_LEGACY_SCHOOL_MIGRATION_SHA256 = {
    ROOT / "app/db/migrations/2026-07-09-school-v2-placement.sql": (
        "e536ccd5adef032a3dc0f76d4056d57c96f278d6132e519e10bcbb921d5f721e"
    ),
    ROOT / "app/db/migrations/2026-07-09-school-v2-practice.sql": (
        "d6f431b3de13721fe0b520230a81236af04da6d529aec274143d68e460ce38cd"
    ),
    ROOT / "app/db/migrations/2026-07-09-school-v2-curriculum.sql": (
        "12715900c832802ee1d729cc1eb733c8ce4e846da63ad91555ae221f5d03ca30"
    ),
    ROOT / "app/db/migrations/2026-07-09-school-v3-core.sql": (
        "d29fb8e40df681b830a0e8f36db9230ac9a97c946fdd2281e90b755da5dfd381"
    ),
    ROOT / "app/db/migrations/2026-07-10-school-rebuild-profile.sql": (
        "4541df5f0a0e11ebc4f3e48dc13620fa4ba8319033a44cd3168832fa1b0cc7fe"
    ),
    ROOT / "app/db/migrations/2026-07-10-school-placement-reports.sql": (
        "68cbad3ee1fcc29700a69c2be423fc184c3647335bed6f60f2636854d1732254"
    ),
    ROOT / "app/db/migrations/2026-07-11-school-answer-idempotency.sql": (
        "d195958bbb3400c77a5255a837d95f9943382549863c04cac26dd7f77a02973b"
    ),
    ROOT / "app/db/migrations/2026-07-12-school-session-lineage.sql": (
        "6998e23b00c8c1d5d4866063a15e98be1a2be8308debf01cc0e07277c719ec15"
    ),
    ROOT / "app/db/migrations/2026-07-12-school-onboarding-drafts.sql": (
        "2d57b79d672ceeef699ee41386223bac8751308d7e901576ae5592d285c719ca"
    ),
}


class MigrationHashMismatch(RuntimeError):
    """Raised before SQL when a canonical migration changed after application."""


@dataclass(frozen=True)
class MigrationSnapshot:
    path: Path
    content: bytes
    text: str
    sha256: str


def snapshot_migrations(files: list[Path]) -> list[MigrationSnapshot]:
    snapshots = []
    for path in files:
        content = path.read_bytes()
        snapshots.append(
            MigrationSnapshot(
                path=path,
                content=content,
                text=content.decode("utf-8"),
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return snapshots


def _statements(sql: str) -> list[str]:
    """Split SQL on top-level semicolons, preserving quoted procedural bodies."""

    chunks: list[str] = []
    current: list[str] = []
    index = 0
    state = "normal"
    dollar_tag = ""
    block_depth = 0
    while index < len(sql):
        character = sql[index]
        following = sql[index + 1] if index + 1 < len(sql) else ""

        if state == "line_comment":
            if character == "\n":
                current.append(character)
                state = "normal"
            index += 1
            continue

        if state == "block_comment":
            if character == "/" and following == "*":
                block_depth += 1
                index += 2
                continue
            if character == "*" and following == "/":
                block_depth -= 1
                index += 2
                if block_depth == 0:
                    current.append(" ")
                    state = "normal"
                continue
            index += 1
            continue

        if state == "dollar_quote":
            if sql.startswith(dollar_tag, index):
                current.append(dollar_tag)
                index += len(dollar_tag)
                state = "normal"
            else:
                current.append(character)
                index += 1
            continue

        if state in {"single_quote", "double_quote"}:
            current.append(character)
            quote = "'" if state == "single_quote" else '"'
            if character == quote:
                if following == quote:
                    current.append(following)
                    index += 2
                    continue
                state = "normal"
            index += 1
            continue

        if character == "-" and following == "-":
            state = "line_comment"
            index += 2
            continue
        if character == "/" and following == "*":
            state = "block_comment"
            block_depth = 1
            index += 2
            continue
        if character == "'":
            current.append(character)
            state = "single_quote"
            index += 1
            continue
        if character == '"':
            current.append(character)
            state = "double_quote"
            index += 1
            continue
        if character == "$":
            match = re.match(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$", sql[index:])
            if match:
                dollar_tag = match.group(0)
                current.append(dollar_tag)
                index += len(dollar_tag)
                state = "dollar_quote"
                continue
        if character == ";":
            statement = "".join(current).strip()
            if statement:
                chunks.append(statement)
            current = []
            index += 1
            continue
        current.append(character)
        index += 1

    trailing = "".join(current).strip()
    if trailing:
        chunks.append(trailing)
    return chunks


def _validate_locked_migration_hashes(
    migrations: list[MigrationSnapshot] | list[Path],
) -> None:
    snapshots = (
        migrations
        if not migrations or isinstance(migrations[0], MigrationSnapshot)
        else snapshot_migrations(migrations)
    )
    by_path = {snapshot.path.resolve(): snapshot for snapshot in snapshots}
    requested = set(by_path)
    canonical_requested = any(
        path.resolve() in requested for path in CANONICAL_MIGRATIONS
    )
    for path, expected_hash in LOCKED_LEGACY_SCHOOL_MIGRATION_SHA256.items():
        if not canonical_requested and path.resolve() not in requested:
            continue
        snapshot = by_path.get(path.resolve())
        if snapshot is None:
            snapshot = snapshot_migrations([path])[0]
        actual_hash = snapshot.sha256
        if actual_hash != expected_hash:
            raise MigrationHashMismatch(
                "legacy_school_migration_hash_mismatch:"
                f"{path.name}:expected={expected_hash}:actual={actual_hash}"
            )


async def _apply_canonical_migration(
    conn,
    migration: MigrationSnapshot | Path,
) -> bool:
    """Apply and mark one canonical migration in the caller's transaction."""

    snapshot = (
        migration
        if isinstance(migration, MigrationSnapshot)
        else snapshot_migrations([migration])[0]
    )
    migration_key = snapshot.path.name
    checked_hash = snapshot.sha256
    await conn.execute(
        text(
            "SELECT pg_advisory_xact_lock("
            "hashtext('zidd_school_canonical_migrations'))"
        )
    )
    marker_exists = await conn.scalar(
        text("SELECT to_regclass('public.school_migration_markers') IS NOT NULL")
    )
    if not marker_exists:
        raise RuntimeError(
            "canonical_school_migration_predecessor_missing:school_migration_markers"
        )
    hash_column_exists = await conn.scalar(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'school_migration_markers'
                  AND column_name = 'file_sha256'
            )
            """
        )
    )
    hash_expression = "file_sha256" if hash_column_exists else "NULL::text"
    existing = (
        await conn.execute(
            text(
                f"""
                SELECT {hash_expression} AS file_sha256
                FROM public.school_migration_markers
                WHERE migration_key = :migration_key
                FOR UPDATE
                """
            ),
            {"migration_key": migration_key},
        )
    ).mappings().first()
    if existing is not None:
        stored_hash = existing["file_sha256"]
        if stored_hash != checked_hash:
            raise MigrationHashMismatch(
                "canonical_school_migration_hash_mismatch:"
                f"{migration_key}:stored={stored_hash or 'missing'}:"
                f"checked_in={checked_hash}"
            )
        return False

    for statement in _statements(snapshot.text):
        await conn.exec_driver_sql(statement)
    await conn.execute(
        text(
            """
            INSERT INTO public.school_migration_markers
                (migration_key, file_sha256, applied_at)
            VALUES (:migration_key, :file_sha256, now())
            """
        ),
        {"migration_key": migration_key, "file_sha256": checked_hash},
    )
    return True


async def apply(
    files: list[Path],
    *,
    preflight_output: Path | None = None,
) -> None:
    snapshots = snapshot_migrations(files)
    _validate_locked_migration_hashes(snapshots)
    canonical_requested = any(
        path.resolve() in {item.resolve() for item in CANONICAL_MIGRATIONS}
        for path in files
    )
    if canonical_requested and preflight_output is None:
        raise RuntimeError("canonical_school_migration_preflight_output_required")

    settings = get_settings()
    if not settings.supabase_pooler_url:
        raise RuntimeError("SUPABASE_POOLER_URL is required to apply migrations.")

    engine = get_engine()
    try:
        async with engine.begin() as conn:
            if canonical_requested:
                await conn.execute(
                    text(
                        "SELECT pg_advisory_xact_lock("
                        "hashtext('zidd_school_canonical_migrations'))"
                    )
                )
                await conn.execute(
                    text(
                        "LOCK TABLE public.school_profile_versions, "
                        "public.school_sessions, "
                        "public.school_placement_reports "
                        "IN SHARE ROW EXCLUSIVE MODE"
                    )
                )
                preflight = await collect_preflight_on_connection(
                    conn,
                    settings.supabase_pooler_url,
                )
                write_preflight_output(preflight, preflight_output)
                if not preflight.get("ok", False):
                    raise RuntimeError("canonical_school_migration_preflight_failed")

            canonical_paths = {item.resolve() for item in CANONICAL_MIGRATIONS}
            for snapshot in snapshots:
                if snapshot.path.resolve() in canonical_paths:
                    await _apply_canonical_migration(conn, snapshot)
                    continue
                for statement in _statements(snapshot.text):
                    await conn.exec_driver_sql(statement)
            await validate_runtime_schema(conn)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--preflight-output", type=Path)
    args = parser.parse_args()
    files = args.files or DEFAULT_MIGRATIONS
    canonical_requested = any(
        path.resolve() in {item.resolve() for item in CANONICAL_MIGRATIONS}
        for path in files
    )
    if canonical_requested and args.preflight_output is None:
        parser.error("--preflight-output is required for canonical School migrations")
    asyncio.run(apply(files, preflight_output=args.preflight_output))
    print(f"Applied {len(files)} migration file(s) and validated runtime schema.")


if __name__ == "__main__":
    main()
