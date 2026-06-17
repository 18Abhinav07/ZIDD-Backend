import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.storage.local_store import LocalStore  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return LocalStore(str(tmp_path / "test.db"))


@pytest.mark.asyncio
async def test_grant_then_get_credits(store):
    await store.ensure_profile("u1")
    assert await store.grant_credits("u1", 50, "welcome") == 50
    assert await store.get_credits("u1") == 50


@pytest.mark.asyncio
async def test_deduct_credits_success_and_failure(store):
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 50, "welcome")
    assert await store.deduct_credits("u1", 40, "access_unlock") is True
    assert await store.get_credits("u1") == 10
    assert await store.deduct_credits("u1", 40, "access_unlock") is False
    assert await store.get_credits("u1") == 10


@pytest.mark.asyncio
async def test_demo_user_never_charged(store):
    await store.ensure_profile("judge")
    await store.set_demo_unlimited("judge", True)
    assert await store.is_demo("judge") is True
    assert await store.deduct_credits("judge", 1000, "attempt_meter") is True
    assert await store.get_credits("judge") == 0


@pytest.mark.asyncio
async def test_credit_transactions_are_logged(store):
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 50, "welcome")
    await store.deduct_credits("u1", 40, "access_unlock")
    rows = store._conn.execute(
        "SELECT delta, reason FROM credit_transactions WHERE user_id = ? ORDER BY id",
        ("u1",),
    ).fetchall()
    assert [tuple(r) for r in rows] == [(50, "welcome"), (-40, "access_unlock")]
