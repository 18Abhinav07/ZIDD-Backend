"""Apply the checked-in idempotent Supabase migrations.

This is intentionally small: migrations in app/db/migrations are already written
as safe CREATE/ALTER IF NOT EXISTS statements. The script gives local/dev
operators a repeatable command instead of pasting SQL into the dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.db.engine import get_engine
from app.db.schema_guard import validate_runtime_schema


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
]


def _statements(sql: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";").strip()
            if statement:
                chunks.append(statement)
            current = []
    trailing = "\n".join(current).strip()
    if trailing:
        chunks.append(trailing.rstrip(";").strip())
    return chunks


async def apply(files: list[Path]) -> None:
    settings = get_settings()
    if not settings.supabase_pooler_url:
        raise RuntimeError("SUPABASE_POOLER_URL is required to apply migrations.")

    engine = get_engine()
    try:
        async with engine.begin() as conn:
            for path in files:
                for statement in _statements(path.read_text()):
                    await conn.execute(text(statement))
        await validate_runtime_schema()
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()
    files = args.files or DEFAULT_MIGRATIONS
    asyncio.run(apply(files))
    print(f"Applied {len(files)} migration file(s) and validated runtime schema.")


if __name__ == "__main__":
    main()
