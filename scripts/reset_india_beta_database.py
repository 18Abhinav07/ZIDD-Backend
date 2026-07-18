"""Safely clear only India-beta learner runtime data.

This is an operator command, not an application endpoint.  It deliberately
preserves migrations, release metadata, source content, and Supabase's ``auth``
schema.  A Google user can sign in again after the reset and receive a fresh
public learner profile without affecting the legacy/default-region database.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable
from urllib.parse import urlsplit

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.db.engine import get_migration_engine
from app.db.schema_guard import validate_runtime_schema


class IndiaBetaResetRefused(RuntimeError):
    """The target cannot be proven to be the disposable India beta database."""


@dataclass(frozen=True)
class IndiaBetaResetTarget:
    direct_host: str
    runtime_host: str


@dataclass(frozen=True)
class IndiaBetaResetPlan:
    truncate_tables: tuple[str, ...]
    preserve_tables: tuple[str, ...]


# These are application-owned, learner-derived tables only.  The list is
# intentionally explicit: a new table must be consciously added here rather
# than being swept up by a broad public-schema operation.
_TRUNCATE_TABLES = (
    "school_profile_draft_requests",
    "school_answer_requests",
    "school_placement_reports",
    "school_sessions",
    "school_language_confidence",
    "school_v2_placement_sessions",
    "school_v2_practice_sessions",
    "school_v2_curriculum_sessions",
    "school_skill_mastery",
    "school_results",
    "session_messages",
    "session_turn_requests",
    "session_start_requests",
    "session_opening_requests",
    "session_end_requests",
    "session_runtime",
    "turn_evaluations",
    "turns",
    "node_attempts",
    "weaknesses",
    "memory_entries",
    "competency_nodes",
    "learning_events",
    "session_reports",
    "learner_skill_profiles",
    "test_items",
    "credit_transactions",
    "content_unlocks",
    "purchases",
    "sessions",
    "learner_profiles",
)
_PRESERVE_TABLES = (
    "school_migration_markers",
    "school_curriculum_releases",
)


def india_beta_reset_plan() -> IndiaBetaResetPlan:
    return IndiaBetaResetPlan(
        truncate_tables=_TRUNCATE_TABLES,
        preserve_tables=_PRESERVE_TABLES,
    )


def _url_host(url: str, *, missing_code: str) -> str:
    parsed = urlsplit(url.strip())
    if not parsed.hostname:
        raise IndiaBetaResetRefused(missing_code)
    return parsed.hostname.casefold()


def validate_india_beta_reset_target(
    settings,
    *,
    expected_direct_host: str,
) -> IndiaBetaResetTarget:
    """Fail closed unless the operator names the exact India direct host."""

    if str(getattr(settings, "app_env", "")).strip().casefold() == "prod":
        raise IndiaBetaResetRefused("india_beta_reset_forbidden_in_production")
    if str(getattr(settings, "data_region", "")).strip().casefold() != "india":
        raise IndiaBetaResetRefused("india_beta_reset_requires_data_region_india")
    if not bool(getattr(settings, "migration_database_configured", False)):
        raise IndiaBetaResetRefused("india_beta_reset_direct_database_missing")

    direct_host = _url_host(
        str(getattr(settings, "supabase_direct_url_ind", "")),
        missing_code="india_beta_reset_direct_database_missing",
    )
    runtime_host = _url_host(
        str(getattr(settings, "supabase_transaction_pooler_url_ind", "")),
        missing_code="india_beta_reset_runtime_database_missing",
    )
    expected = expected_direct_host.strip().casefold()
    if not expected or direct_host != expected:
        raise IndiaBetaResetRefused("india_beta_reset_direct_host_mismatch")
    return IndiaBetaResetTarget(
        direct_host=direct_host,
        runtime_host=runtime_host,
    )


def truncate_statement(plan: IndiaBetaResetPlan) -> str:
    names = ", ".join(f"public.{table}" for table in plan.truncate_tables)
    return f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"


async def _existing_tables(conn, names: Iterable[str]) -> set[str]:
    rows = (
        await conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY(:table_names)
                """
            ),
            {"table_names": list(names)},
        )
    ).scalars().all()
    return {str(row) for row in rows}


async def _counts(conn, table_names: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in table_names:
        counts[table] = int(
            await conn.scalar(text(f"SELECT count(*) FROM public.{table}")) or 0
        )
    return counts


async def execute_india_beta_reset(
    *,
    expected_direct_host: str,
    confirm: bool,
) -> dict[str, object]:
    """Return a dry-run plan or atomically clear the India beta learner data."""

    settings = get_settings()
    target = validate_india_beta_reset_target(
        settings,
        expected_direct_host=expected_direct_host,
    )
    plan = india_beta_reset_plan()
    engine = get_migration_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtext('zidd_india_beta_reset_v1'))")
            )
            existing = await _existing_tables(
                conn,
                (*plan.truncate_tables, *plan.preserve_tables),
            )
            missing = sorted(set(plan.truncate_tables) - existing)
            if missing:
                raise IndiaBetaResetRefused(
                    "india_beta_reset_schema_incomplete:" + ",".join(missing)
                )
            missing_preserved = sorted(set(plan.preserve_tables) - existing)
            if missing_preserved:
                raise IndiaBetaResetRefused(
                    "india_beta_reset_preserved_schema_missing:"
                    + ",".join(missing_preserved)
                )
            before = await _counts(conn, plan.truncate_tables)
            if not confirm:
                return {
                    "executed": False,
                    "target": target,
                    "before": before,
                    "preserved_tables": plan.preserve_tables,
                    "auth_schema_touched": False,
                }
            await conn.execute(text(truncate_statement(plan)))
            await validate_runtime_schema(conn)
            after = await _counts(conn, plan.truncate_tables)
            if any(after.values()):
                raise RuntimeError("india_beta_reset_postcondition_failed")
            return {
                "executed": True,
                "target": target,
                "before": before,
                "after": after,
                "preserved_tables": plan.preserve_tables,
                "auth_schema_touched": False,
            }
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected-direct-host",
        required=True,
        help="Exact host from SUPABASE_DIRECT_URL_IND. Required as a second target check.",
    )
    parser.add_argument(
        "--confirm-india-beta-reset",
        action="store_true",
        help="Execute the destructive reset. Without this flag, only a dry run is printed.",
    )
    args = parser.parse_args()
    result = asyncio.run(
        execute_india_beta_reset(
            expected_direct_host=args.expected_direct_host,
            confirm=args.confirm_india_beta_reset,
        )
    )
    print(
        {
            **result,
            "target": result["target"].__dict__,
        }
    )


if __name__ == "__main__":
    main()
