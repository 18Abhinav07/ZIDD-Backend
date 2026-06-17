import os
from contextlib import asynccontextmanager
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("SUPABASE_POOLER_URL","postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres")
import pytest
import app.storage.pg_store as pg_store
from app.storage.pg_store import PgStore
@pytest.fixture
def offline(monkeypatch):
    @asynccontextmanager
    async def _none():
        yield None
    monkeypatch.setattr(pg_store, "_session", _none)
@pytest.mark.asyncio
async def test_billing_methods_degrade_gracefully(offline):
    store = PgStore()
    assert await store.get_credits("u1") == 0
    assert await store.is_demo("u1") is False
    assert await store.grant_credits("u1", 50, "welcome") == 0
    assert await store.deduct_credits("u1", 40, "x") is False
    assert await store.has_unlock("u1", "feature", "communication") is False
    assert await store.list_unlocks("u1") == []
    assert await store.count_attempts("u1", "interview") == 0
    assert await store.get_purchase("order_x") is None
    assert await store.mark_purchase_paid("order_x") is False
    await store.set_demo_unlimited("u1", True)
    await store.add_unlock("u1", "feature", "communication", 40)
    await store.record_purchase("order_x", "u1", "starter", 100, 9900)
