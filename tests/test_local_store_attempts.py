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
    assert await store.count_attempts("u1", "interview") == 0
    await store.create_session("s1", "u1", "interview", "interview", "int_01_elevator_pitch")
    await store.create_session("s2", "u1", "interview", "interview", "int_01_elevator_pitch")
    await store.create_session("s3", "u1", "group_discussion", "group_discussion", "gd_01_intro")
    assert await store.count_attempts("u1", "interview") == 2
    assert await store.count_attempts("u1", "group_discussion") == 1
    assert await store.count_attempts("u2", "interview") == 0
