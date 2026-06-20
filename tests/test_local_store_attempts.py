# tests/test_local_store_attempts.py
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.storage.local_store import LocalStore


@pytest.fixture
def store(tmp_path):
    return LocalStore(str(tmp_path / "test.db"))


@pytest.mark.asyncio
async def test_count_attempts_by_module(store):
    # FIX #4: a STARTED session consumes an attempt (the production FE never calls
    # /session/end, so completion can't be the signal). Counting is per-module.
    assert await store.count_attempts("u1", "interview") == 0
    await store.create_session("s1", "u1", "interview", "interview", "int_01_elevator_pitch")
    await store.create_session("s2", "u1", "interview", "interview", "int_01_elevator_pitch")
    await store.create_session("s3", "u1", "group_discussion", "group_discussion", "gd_01_intro")
    assert await store.count_attempts("u1", "interview") == 2
    assert await store.count_attempts("u1", "group_discussion") == 1
    assert await store.count_attempts("u2", "interview") == 0


@pytest.mark.asyncio
async def test_count_attempts_counts_started_sessions(store):
    """FIX #4: a started interview/GD session MUST consume an attempt even if it
    is never ended. The production frontend never calls /session/end and TEST-mode
    sims persist no per-turn rows, so the OLD `ended IS NOT NULL` filter made the
    count permanently 0 and bypassed the ATTEMPT meter forever. The gate counts
    BEFORE the current session's row is inserted, so counting started rows still
    leaves exactly FREE_ATTEMPTS free (1st start sees 0, 2nd sees 1) then meters."""
    assert await store.count_attempts("u1", "interview") == 0
    await store.create_session("s1", "u1", "interview", "interview", "int_01_elevator_pitch")
    assert await store.count_attempts("u1", "interview") == 1  # counts at start, no /end
    await store.create_session("s2", "u1", "interview", "interview", "int_01_elevator_pitch")
    assert await store.count_attempts("u1", "interview") == 2  # the 3rd start would meter
