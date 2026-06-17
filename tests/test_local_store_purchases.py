# tests/test_local_store_purchases.py
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
async def test_record_and_get_purchase(store):
    await store.record_purchase("order_1", "u1", "starter", 100, 9900)
    p = await store.get_purchase("order_1")
    assert p is not None
    assert p["user_id"] == "u1"
    assert p["pack_id"] == "starter"
    assert p["credits"] == 100
    assert p["amount_paise"] == 9900
    assert p["status"] == "created"


@pytest.mark.asyncio
async def test_mark_purchase_paid_is_idempotent(store):
    await store.record_purchase("order_1", "u1", "starter", 100, 9900)
    # First mark transitions -> True.
    assert await store.mark_purchase_paid("order_1") is True
    assert (await store.get_purchase("order_1"))["status"] == "paid"
    # Second mark is a no-op -> False (so credits grant exactly once).
    assert await store.mark_purchase_paid("order_1") is False


@pytest.mark.asyncio
async def test_get_missing_purchase_returns_none(store):
    assert await store.get_purchase("nope") is None
