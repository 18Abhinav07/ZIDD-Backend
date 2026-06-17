# tests/test_local_store_unlocks.py
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
async def test_add_and_has_unlock(store):
    assert await store.has_unlock("u1", "feature", "communication") is False
    await store.add_unlock("u1", "feature", "communication", 40)
    assert await store.has_unlock("u1", "feature", "communication") is True


@pytest.mark.asyncio
async def test_add_unlock_is_idempotent(store):
    await store.add_unlock("u1", "feature", "communication", 40)
    await store.add_unlock("u1", "feature", "communication", 40)
    rows = await store.list_unlocks("u1")
    assert len(rows) == 1
    assert rows[0]["scope"] == "feature"
    assert rows[0]["ref_id"] == "communication"
    assert rows[0]["credits_spent"] == 40
