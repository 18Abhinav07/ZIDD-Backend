"""Destructively reset the Supabase dev product state.

This is intentionally not part of app startup. It is for local/dev reset only:
all users, sessions, credits, progress, messages, purchases, and profile data
are removed so every Google login starts as a new learner.
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


RESET_SQL = """
TRUNCATE TABLE
    session_opening_requests,
    session_start_requests,
    session_end_requests,
    session_turn_requests,
    session_messages,
    session_runtime,
    node_attempts,
    turn_evaluations,
    turns,
    memory_entries,
    school_results,
    school_skill_mastery,
    weaknesses,
    competency_nodes,
    test_items,
    content_unlocks,
    credit_transactions,
    purchases,
    sessions,
    learner_profiles
RESTART IDENTITY CASCADE
"""


async def reset() -> None:
    settings = get_settings()
    if not settings.supabase_pooler_url:
        raise RuntimeError("SUPABASE_POOLER_URL is required to reset dev state.")
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(text(RESET_SQL))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm-dev-reset",
        action="store_true",
        help="Required. Deletes all product learner state from the configured database.",
    )
    args = parser.parse_args()
    if not args.confirm_dev_reset:
        raise SystemExit("Refusing to reset without --confirm-dev-reset")
    asyncio.run(reset())
    print("Supabase dev product state reset.")


if __name__ == "__main__":
    main()
