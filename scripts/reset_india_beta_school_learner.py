#!/usr/bin/env python3
"""Safely reset one India-beta learner's School state without touching Career.

This is an operator command for browser QA. It preserves the Google-linked
account, wallet, Career sessions and every other learner's data. Only the
selected learner's School profile lineage, School runtime records, and
School-domain learning projections are removed.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from dotenv import dotenv_values
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.db.engine import get_migration_engine
from scripts.reset_india_beta_database import (
    IndiaBetaResetRefused,
    validate_india_beta_reset_target,
)


@dataclass(frozen=True)
class SchoolLearnerResetPlan:
    school_tables: tuple[str, ...]
    school_domain_tables: tuple[str, ...]
    preserved_categories: tuple[str, ...]


_SCHOOL_TABLES = (
    "school_evaluation_jobs",
    "school_answer_requests",
    "school_placement_reports",
    "school_sessions",
    "school_profile_draft_requests",
    "school_profile_versions",
    "school_language_confidence",
    "school_v2_placement_sessions",
    "school_v2_practice_sessions",
    "school_v2_curriculum_sessions",
    "school_skill_mastery",
    "school_results",
)
_SCHOOL_DOMAIN_TABLES = (
    "learning_events",
    "learner_skill_profiles",
    "session_reports",
    "test_items",
    "weaknesses",
)
_PRESERVED_CATEGORIES = (
    "learner account and Google identity",
    "credit wallet and purchases",
    "Career sessions, reports, memory, and learning evidence",
    "all other learners",
    "migration markers and curriculum releases",
)


def school_learner_reset_plan() -> SchoolLearnerResetPlan:
    return SchoolLearnerResetPlan(
        school_tables=_SCHOOL_TABLES,
        school_domain_tables=_SCHOOL_DOMAIN_TABLES,
        preserved_categories=_PRESERVED_CATEGORIES,
    )


def _load_env_file(path: Path | None) -> None:
    if path is None:
        return
    if not path.is_file():
        raise IndiaBetaResetRefused("india_beta_school_reset_env_file_missing")
    for key, value in dotenv_values(path).items():
        if value is not None:
            os.environ[str(key)] = str(value)
    # This command never targets the legacy/default data region. The direct
    # host confirmation below remains a second, human-supplied target check.
    os.environ["DATA_REGION"] = "india"
    get_settings.cache_clear()


async def _existing_tables(conn, table_names: tuple[str, ...]) -> set[str]:
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
            {"table_names": list(table_names)},
        )
    ).scalars().all()
    return {str(row) for row in rows}


async def _learner_id_for_email(conn, email: str) -> str | None:
    row = (
        await conn.execute(
            text(
                """
                SELECT user_id
                FROM public.learner_profiles
                WHERE lower(email) = lower(:email)
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"email": email},
        )
    ).scalar_one_or_none()
    return str(row) if row is not None else None


async def _count_user_rows(conn, table_name: str, user_id: str) -> int:
    return int(
        await conn.scalar(
            text(f"SELECT count(*) FROM public.{table_name} WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        or 0
    )


async def _count_school_domain_rows(conn, table_name: str, user_id: str) -> int:
    if table_name in {"learning_events", "learner_skill_profiles"}:
        predicate = "domain = 'school'"
    else:
        predicate = "task_type LIKE 'school\\_%' ESCAPE '\\'"
    return int(
        await conn.scalar(
            text(
                f"SELECT count(*) FROM public.{table_name} "
                f"WHERE user_id = :user_id AND {predicate}"
            ),
            {"user_id": user_id},
        )
        or 0
    )


async def _delete_school_rows(conn, user_id: str) -> None:
    # A curriculum session can point back to its placement report. Clear that
    # reverse link before removing reports, then remove the session graph.
    await conn.execute(
        text(
            """
            UPDATE public.school_sessions
            SET source_placement_report_id = NULL
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    )
    for table_name in (
        "school_evaluation_jobs",
        "school_answer_requests",
        "school_placement_reports",
        "school_sessions",
        "school_profile_draft_requests",
        "school_language_confidence",
        "school_v2_placement_sessions",
        "school_v2_practice_sessions",
        "school_v2_curriculum_sessions",
        "school_skill_mastery",
        "school_results",
    ):
        await conn.execute(
            text(f"DELETE FROM public.{table_name} WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
    await conn.execute(
        text(
            """
            UPDATE public.school_profile_versions
            SET source_profile_version_id = NULL,
                activation_result_profile_version_id = NULL
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    )
    await conn.execute(
        text("DELETE FROM public.school_profile_versions WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    for table_name in ("learning_events", "learner_skill_profiles"):
        await conn.execute(
            text(
                f"DELETE FROM public.{table_name} "
                "WHERE user_id = :user_id AND domain = 'school'"
            ),
            {"user_id": user_id},
        )
    for table_name in ("session_reports", "test_items", "weaknesses"):
        await conn.execute(
            text(
                f"DELETE FROM public.{table_name} "
                "WHERE user_id = :user_id "
                "AND task_type LIKE 'school\\_%' ESCAPE '\\'"
            ),
            {"user_id": user_id},
        )
    # Leave account, credits, purchases, and Career identity untouched. A
    # School-only onboarding reset should not turn into a cross-product reset.
    await conn.execute(
        text(
            """
            UPDATE public.learner_profiles
            SET school_profile = '{}'::jsonb,
                onboarding_state = CASE
                    WHEN primary_motive = 'school' THEN '{}'::jsonb
                    ELSE onboarding_state
                END,
                primary_motive = CASE
                    WHEN primary_motive = 'school' THEN NULL
                    ELSE primary_motive
                END,
                onboarding_completed_at = CASE
                    WHEN primary_motive = 'school' THEN NULL
                    ELSE onboarding_completed_at
                END
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    )


async def execute_india_beta_school_learner_reset(
    *,
    email: str,
    expected_direct_host: str,
    confirm: bool,
) -> dict[str, object]:
    settings = get_settings()
    target = validate_india_beta_reset_target(
        settings,
        expected_direct_host=expected_direct_host,
    )
    plan = school_learner_reset_plan()
    engine = get_migration_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "SELECT pg_advisory_xact_lock("
                    "hashtext('zidd_india_beta_school_reset:' || :email))"
                ),
                {"email": email.casefold()},
            )
            existing = await _existing_tables(
                conn,
                (*plan.school_tables, *plan.school_domain_tables),
            )
            missing = sorted(set(plan.school_tables) - existing)
            if missing:
                raise IndiaBetaResetRefused(
                    "india_beta_school_reset_schema_incomplete:" + ",".join(missing)
                )
            missing_domain = sorted(set(plan.school_domain_tables) - existing)
            if missing_domain:
                raise IndiaBetaResetRefused(
                    "india_beta_school_reset_domain_schema_incomplete:"
                    + ",".join(missing_domain)
                )
            user_id = await _learner_id_for_email(conn, email)
            if user_id is None:
                raise IndiaBetaResetRefused("india_beta_school_reset_learner_not_found")
            before = {
                table_name: await _count_user_rows(conn, table_name, user_id)
                for table_name in plan.school_tables
            }
            before.update(
                {
                    table_name: await _count_school_domain_rows(conn, table_name, user_id)
                    for table_name in plan.school_domain_tables
                }
            )
            if not confirm:
                return {
                    "executed": False,
                    "email": email,
                    "target": target,
                    "before": before,
                    "preserved_categories": plan.preserved_categories,
                    "auth_schema_touched": False,
                }
            await _delete_school_rows(conn, user_id)
            after = {
                table_name: await _count_user_rows(conn, table_name, user_id)
                for table_name in plan.school_tables
            }
            after.update(
                {
                    table_name: await _count_school_domain_rows(conn, table_name, user_id)
                    for table_name in plan.school_domain_tables
                }
            )
            if any(after.values()):
                raise RuntimeError("india_beta_school_reset_postcondition_failed")
            return {
                "executed": True,
                "email": email,
                "target": target,
                "before": before,
                "after": after,
                "preserved_categories": plan.preserved_categories,
                "auth_schema_touched": False,
            }
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--expected-direct-host",
        required=True,
        help="Exact host from SUPABASE_DIRECT_URL_IND. Required as a second target check.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional dotenv file. Its IND values are loaded before validation.",
    )
    parser.add_argument(
        "--confirm-india-beta-school-reset",
        action="store_true",
        help="Execute the destructive School-only reset for the named learner.",
    )
    args = parser.parse_args()
    _load_env_file(args.env_file)
    result = asyncio.run(
        execute_india_beta_school_learner_reset(
            email=str(args.email).strip(),
            expected_direct_host=str(args.expected_direct_host),
            confirm=bool(args.confirm_india_beta_school_reset),
        )
    )
    print({**result, "target": result["target"].__dict__})


if __name__ == "__main__":
    main()
