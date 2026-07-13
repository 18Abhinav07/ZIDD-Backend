"""Read-only compatibility preflight for canonical School migrations."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import asyncpg
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.content.school.release_loader import load_release_manifest


APPROVED_TAXONOMY_VERSION = "english-2026-27-v1"
APPROVED_CERTIFICATION_EPOCH = "2026-27"
ACTIVE_SESSION_STATUSES = ("active", "paused_for_masterclass")

PREDECESSOR_COLUMNS: dict[str, tuple[str, ...]] = {
    "school_migration_markers": ("migration_key", "claimed_at"),
    "school_profile_versions": (
        "profile_version_id",
        "user_id",
        "status",
        "board_id",
        "target_class_no",
        "subject_ids",
    ),
    "school_sessions": (
        "session_id",
        "user_id",
        "profile_version_id",
        "api_version",
        "flow_type",
        "subject_id",
        "class_no",
        "status",
        "linked_session_id",
    ),
    "school_placement_reports": (
        "report_id",
        "user_id",
        "profile_version_id",
        "placement_session_id",
        "subject_id",
        "target_class_no",
    ),
}

PREDECESSOR_CONSTRAINTS: dict[str, str] = {
    "school_migration_markers_pkey": "migration_key_primary_key",
    "school_profile_versions_pkey": "profile_version_id_primary_key",
    "school_sessions_pkey": "session_id_primary_key",
    "school_placement_reports_pkey": "report_id_primary_key",
    "school_rebuild_active_profile_lineage": "active_rebuild_profile_lineage",
    "school_sessions_linked_same_user": "linked_session_same_user",
}

ACTIVE_FLOW_INDEX = "idx_school_sessions_one_active_flow"


def _canonical_release_digest(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def approved_release_mapping() -> list[dict[str, object]]:
    manifest = load_release_manifest()
    return [
        {
            "academic_year": release.academic_year,
            "board_id": release.board_id,
            "certification_epoch": APPROVED_CERTIFICATION_EPOCH,
            "class_no": release.class_no,
            "curriculum_release_id": release.curriculum_release_id,
            "manifest_sha256": manifest.manifest_sha256,
            "release_digest": _canonical_release_digest(
                release.model_dump(mode="json")
            ),
            "subject_id": release.subject_id,
            "taxonomy_version": APPROVED_TAXONOMY_VERSION,
        }
        for release in manifest.releases
    ]


def redact_database_url(database_url: str) -> dict[str, object]:
    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://", 1))
    return {
        "database": unquote(parsed.path.lstrip("/")).split("/", 1)[0],
        "host": parsed.hostname or "",
        "port": parsed.port or 5432,
        "scheme": parsed.scheme,
    }


def _normalize_sql(value: str) -> str:
    return " ".join(
        value.lower().replace('"', "").replace("::text[]", "").replace("::text", "").split()
    )


def _strip_outer_parentheses(value: str) -> str:
    current = value.strip()
    while current.startswith("(") and current.endswith(")"):
        depth = 0
        closes_at_end = False
        for index, character in enumerate(current):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    closes_at_end = index == len(current) - 1
                    break
        if not closes_at_end:
            break
        current = current[1:-1].strip()
    return current


def _constraint_is_exact(
    name: str,
    definition: str,
    *,
    validated: bool = True,
    update_action: str | None = None,
    delete_action: str | None = None,
) -> bool:
    if not validated:
        return False
    normalized = _normalize_sql(definition).replace("public.", "")
    requirement = PREDECESSOR_CONSTRAINTS[name]
    primary_keys = {
        "migration_key_primary_key": "primary key (migration_key)",
        "profile_version_id_primary_key": "primary key (profile_version_id)",
        "session_id_primary_key": "primary key (session_id)",
        "report_id_primary_key": "primary key (report_id)",
    }
    if requirement in primary_keys:
        return normalized == primary_keys[requirement]
    if requirement == "linked_session_same_user":
        return (
            update_action == "a"
            and delete_action == "a"
            and normalized
            == (
            "foreign key (user_id, linked_session_id) "
            "references school_sessions(user_id, session_id)"
            )
        )
    if requirement != "active_rebuild_profile_lineage":
        return False
    if not normalized.startswith("check "):
        return False
    expression = _strip_outer_parentheses(normalized.removeprefix("check "))
    flattened = " ".join(
        expression.replace("(", " ").replace(")", " ").split()
    )
    return flattened in {
        (
            "api_version <> 'rebuild' or status not in "
            "'active', 'paused_for_masterclass' or profile_version_id is not null"
        ),
        (
            "api_version <> 'rebuild' or status <> all "
            "array['active', 'paused_for_masterclass'] or "
            "profile_version_id is not null"
        ),
    }


def _active_index_is_exact(definition: str) -> bool:
    normalized = _normalize_sql(definition)
    match = re.fullmatch(
        r"create unique index \S+ on public\.school_sessions(?: using \w+)? "
        r"\(user_id, flow_type, subject_id, class_no\) where (.+)",
        normalized,
    )
    if not match:
        return False
    predicate = _strip_outer_parentheses(match.group(1))
    return predicate in {
        "status in ('active', 'paused_for_masterclass')",
        "status = any (array['active', 'paused_for_masterclass'])",
    }


class _SQLAlchemyPreflightAdapter:
    def __init__(self, connection) -> None:
        self._connection = connection

    @staticmethod
    def _statement(query: str) -> str:
        prepared = re.sub(
            r"\$(\d+)::text\[\]",
            lambda match: f"CAST(:arg{match.group(1)} AS text[])",
            query,
        )
        return re.sub(
            r"\$(\d+)",
            lambda match: f":arg{match.group(1)}",
            prepared,
        )

    async def fetch(self, query: str, *args):
        parameters = {f"arg{index}": value for index, value in enumerate(args, 1)}
        result = await self._connection.execute(
            text(self._statement(query)),
            parameters,
        )
        return result.mappings().all()

    async def fetchrow(self, query: str, *args):
        rows = await self.fetch(query, *args)
        return rows[0] if rows else None


async def collect_preflight_on_connection(
    connection,
    database_url: str,
) -> dict[str, object]:
    return await collect_preflight(
        _SQLAlchemyPreflightAdapter(connection),
        database_url,
    )


async def collect_preflight(connection, database_url: str) -> dict[str, object]:
    column_rows = await connection.fetch(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = ANY($1::text[])
        ORDER BY table_name, ordinal_position
        """,
        list(PREDECESSOR_COLUMNS),
    )
    found_columns: dict[str, set[str]] = {
        table: set() for table in PREDECESSOR_COLUMNS
    }
    for row in column_rows:
        found_columns[str(row["table_name"])].add(str(row["column_name"]))

    table_checks = []
    for table, required_columns in sorted(PREDECESSOR_COLUMNS.items()):
        missing_columns = sorted(set(required_columns) - found_columns[table])
        table_checks.append(
            {
                "exists": bool(found_columns[table]),
                "missing_columns": missing_columns,
                "table": table,
            }
        )

    constraint_rows = await connection.fetch(
        """
        SELECT constraint_row.conname AS constraint_name,
               pg_get_constraintdef(constraint_row.oid, true) AS definition,
               constraint_row.convalidated AS validated,
               constraint_row.confupdtype::text AS update_action,
               constraint_row.confdeltype::text AS delete_action
        FROM pg_constraint AS constraint_row
        JOIN pg_class AS table_row ON table_row.oid = constraint_row.conrelid
        JOIN pg_namespace AS namespace_row ON namespace_row.oid = table_row.relnamespace
        WHERE namespace_row.nspname = 'public'
          AND table_row.relname = ANY($1::text[])
        ORDER BY constraint_row.conname
        """,
        list(PREDECESSOR_COLUMNS),
    )
    found_constraints = {str(row["constraint_name"]): row for row in constraint_rows}
    constraint_checks = [
        {
            "constraint": name,
            "definition": (
                _normalize_sql(str(found_constraints[name]["definition"]))
                if name in found_constraints
                else None
            ),
            "exists": name in found_constraints,
            "exact": _constraint_is_exact(
                name,
                str(found_constraints.get(name, {}).get("definition", "")),
                validated=bool(
                    found_constraints.get(name, {}).get("validated", False)
                ),
                update_action=(
                    str(found_constraints[name].get("update_action") or "")
                    if name in found_constraints
                    else None
                ),
                delete_action=(
                    str(found_constraints[name].get("delete_action") or "")
                    if name in found_constraints
                    else None
                ),
            ),
            "validated": bool(
                found_constraints.get(name, {}).get("validated", False)
            ),
        }
        for name in PREDECESSOR_CONSTRAINTS
    ]

    index_row = await connection.fetchrow(
        """
        SELECT pg_get_indexdef(index_row.indexrelid) AS indexdef,
               index_row.indisvalid,
               index_row.indisready
        FROM pg_index AS index_row
        JOIN pg_class AS index_class ON index_class.oid = index_row.indexrelid
        JOIN pg_namespace AS namespace_row
          ON namespace_row.oid = index_class.relnamespace
        WHERE namespace_row.nspname = 'public' AND index_class.relname = $1
        """,
        ACTIVE_FLOW_INDEX,
    )
    index_definition = str(index_row["indexdef"]) if index_row else ""
    index_check = {
        "columns": ["user_id", "flow_type", "subject_id", "class_no"],
        "exact": (
            _active_index_is_exact(index_definition)
            and bool(index_row and index_row["indisvalid"])
            and bool(index_row and index_row["indisready"])
        ),
        "index": ACTIVE_FLOW_INDEX,
        "ready": bool(index_row and index_row["indisready"]),
        "predicate": "status IN ('active', 'paused_for_masterclass')",
        "valid": bool(index_row and index_row["indisvalid"]),
    }

    predecessor_ok = (
        all(item["exists"] and not item["missing_columns"] for item in table_checks)
        and all(item["exists"] and item["exact"] for item in constraint_checks)
        and index_check["exact"]
    )
    active = {
        "profiles": {"count": 0, "ids": []},
        "reports": {"count": 0, "ids": []},
        "sessions": {"count": 0, "ids": []},
    }
    ambiguous_sessions: list[dict[str, object]] = []
    ambiguous_reports: list[dict[str, object]] = []
    lineage_candidates = {
        "reports": {"count": 0, "ids": []},
        "sessions": {"count": 0, "ids": []},
    }

    mapping = approved_release_mapping()
    mapping_counts = Counter(
        (
            str(row["board_id"]),
            str(row["subject_id"]),
            int(row["class_no"]),
        )
        for row in mapping
    )
    duplicate_approved_mappings = [
        {
            "board_id": board_id,
            "class_no": class_no,
            "count": count,
            "subject_id": subject_id,
        }
        for (board_id, subject_id, class_no), count in sorted(mapping_counts.items())
        if count > 1
    ]

    if all(item["exists"] and not item["missing_columns"] for item in table_checks):
        profile_rows = await connection.fetch(
            """
            SELECT profile_version_id::text AS id
            FROM public.school_profile_versions
            WHERE status = 'active'
            ORDER BY profile_version_id
            """
        )
        session_rows = await connection.fetch(
            """
            SELECT session.session_id::text AS id,
                   session.api_version,
                   session.user_id AS session_user_id,
                   session.profile_version_id::text AS profile_version_id,
                   session.subject_id,
                   session.class_no,
                   profile.profile_version_id IS NOT NULL AS profile_exists,
                   profile.user_id AS profile_user_id,
                   profile.board_id AS profile_board_id
            FROM public.school_sessions AS session
            LEFT JOIN public.school_profile_versions AS profile
              ON profile.profile_version_id = session.profile_version_id
            WHERE session.status = ANY($1::text[])
            ORDER BY session.session_id
            """,
            list(ACTIVE_SESSION_STATUSES),
        )
        report_rows = await connection.fetch(
            """
            SELECT report.report_id::text AS id,
                   report.subject_id,
                   report.target_class_no AS class_no,
                   placement.api_version
            FROM public.school_placement_reports AS report
            JOIN public.school_profile_versions AS profile
              ON profile.profile_version_id = report.profile_version_id
             AND profile.status = 'active'
            JOIN public.school_sessions AS placement
              ON placement.session_id = report.placement_session_id
            ORDER BY report.report_id
            """
        )
        candidate_session_rows = await connection.fetch(
            """
            SELECT session.session_id::text AS id,
                   session.api_version,
                   session.user_id AS session_user_id,
                   session.profile_version_id::text AS profile_version_id,
                   session.subject_id,
                   session.class_no,
                   profile.profile_version_id IS NOT NULL AS profile_exists,
                   profile.user_id AS profile_user_id,
                   profile.board_id AS profile_board_id
            FROM public.school_sessions AS session
            LEFT JOIN public.school_profile_versions AS profile
              ON profile.profile_version_id = session.profile_version_id
            WHERE session.api_version = 'rebuild'
            ORDER BY session.session_id
            """
        )
        candidate_report_rows = await connection.fetch(
            """
            SELECT report.report_id::text AS id,
                   report.user_id AS report_user_id,
                   report.profile_version_id::text AS report_profile_version_id,
                   report.subject_id,
                   report.target_class_no AS class_no,
                   placement.api_version,
                   placement.user_id AS placement_user_id,
                   placement.profile_version_id::text AS placement_profile_version_id,
                   placement.subject_id AS placement_subject_id,
                   placement.class_no AS placement_class_no,
                   profile.profile_version_id IS NOT NULL AS profile_exists,
                   profile.user_id AS profile_user_id,
                   profile.board_id AS profile_board_id
            FROM public.school_placement_reports AS report
            LEFT JOIN public.school_profile_versions AS profile
              ON profile.profile_version_id = report.profile_version_id
            JOIN public.school_sessions AS placement
              ON placement.session_id = report.placement_session_id
            WHERE placement.api_version = 'rebuild'
            ORDER BY report.report_id
            """
        )
        active = {
            "profiles": {
                "count": len(profile_rows),
                "ids": [str(row["id"]) for row in profile_rows],
            },
            "reports": {
                "count": len(report_rows),
                "ids": [str(row["id"]) for row in report_rows],
            },
            "sessions": {
                "count": len(session_rows),
                "ids": [str(row["id"]) for row in session_rows],
            },
        }
        backfill_session_rows = list(candidate_session_rows)
        backfill_report_rows = list(candidate_report_rows)
        lineage_candidates = {
            "reports": {
                "count": len(backfill_report_rows),
                "ids": [str(row["id"]) for row in backfill_report_rows],
            },
            "sessions": {
                "count": len(backfill_session_rows),
                "ids": [str(row["id"]) for row in backfill_session_rows],
            },
        }
        for row in backfill_session_rows:
            board_id = str(row.get("profile_board_id") or "")
            key = (board_id, str(row["subject_id"]), int(row["class_no"]))
            reasons = []
            if not bool(row.get("profile_exists", False)):
                reasons.append("profile_lineage_missing")
            if str(row.get("session_user_id") or "") != str(
                row.get("profile_user_id") or ""
            ):
                reasons.append("session_profile_user_mismatch")
            if mapping_counts[key] != 1:
                reasons.append(
                    "duplicate_approved_release_mapping"
                    if mapping_counts[key] > 1
                    else "no_unique_approved_release"
                )
            for reason in reasons:
                ambiguous_sessions.append(
                    {
                        "board_id": board_id or None,
                        "class_no": key[2],
                        "reason": reason,
                        "session_id": str(row["id"]),
                        "subject_id": key[1],
                    }
                )
        for row in backfill_report_rows:
            board_id = str(row.get("profile_board_id") or "")
            key = (board_id, str(row["subject_id"]), int(row["class_no"]))
            reasons = []
            if not bool(row.get("profile_exists", False)):
                reasons.append("profile_lineage_missing")
            users = {
                str(row.get("report_user_id") or ""),
                str(row.get("profile_user_id") or ""),
                str(row.get("placement_user_id") or ""),
            }
            if len(users) != 1:
                reasons.append("report_profile_placement_user_mismatch")
            if str(row.get("report_profile_version_id") or "") != str(
                row.get("placement_profile_version_id") or ""
            ):
                reasons.append("report_placement_profile_mismatch")
            if (
                str(row["subject_id"]) != str(row.get("placement_subject_id") or "")
                or int(row["class_no"]) != int(row.get("placement_class_no") or -1)
            ):
                reasons.append("report_placement_identity_mismatch")
            if str(row.get("api_version") or "") != "rebuild":
                reasons.append("placement_session_not_rebuild")
            if mapping_counts[key] != 1:
                reasons.append(
                    "duplicate_approved_release_mapping"
                    if mapping_counts[key] > 1
                    else "no_unique_approved_release"
                )
            for reason in reasons:
                ambiguous_reports.append(
                    {
                        "board_id": board_id or None,
                        "class_no": key[2],
                        "reason": reason,
                        "report_id": str(row["id"]),
                        "subject_id": key[1],
                    }
                )

    return {
        "active": active,
        "ambiguous_lineage": {
            "reports": ambiguous_reports,
            "sessions": ambiguous_sessions,
        },
        "approved_release_mapping": mapping,
        "database": redact_database_url(database_url),
        "duplicate_approved_mappings": duplicate_approved_mappings,
        "lineage_candidates": lineage_candidates,
        "ok": (
            predecessor_ok
            and not duplicate_approved_mappings
            and not ambiguous_sessions
            and not ambiguous_reports
        ),
        "predecessor": {
            "constraints": constraint_checks,
            "index": index_check,
            "tables": table_checks,
        },
    }


def _database_url(explicit_url: str | None) -> str:
    if explicit_url:
        return explicit_url
    env_url = os.environ.get("SCHOOL_MIGRATION_DATABASE_URL", "").strip()
    if env_url:
        return env_url
    configured = get_settings().supabase_pooler_url
    if not configured:
        raise RuntimeError(
            "SCHOOL_MIGRATION_DATABASE_URL or SUPABASE_POOLER_URL is required"
        )
    return str(configured)


async def run_preflight(database_url: str) -> dict[str, object]:
    asyncpg_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    connection = await asyncpg.connect(asyncpg_url, statement_cache_size=0)
    try:
        transaction = connection.transaction(
            isolation="serializable",
            readonly=True,
            deferrable=True,
        )
        await transaction.start()
        try:
            return await collect_preflight(connection, database_url)
        finally:
            await transaction.rollback()
    finally:
        await connection.close()


def write_preflight_output(result: dict[str, object], output: Path) -> None:
    rendered = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, output)
        os.chmod(output, 0o600)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(run_preflight(_database_url(args.database_url)))
    write_preflight_output(result, args.output)
    status = "PASS" if result["ok"] else "FAIL"
    sys.stdout.write(f"School migration preflight {status}: {args.output}\n")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
