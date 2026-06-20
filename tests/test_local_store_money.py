"""Findings #2 (atomic latch+grant) and #6 (shared-connection write safety)."""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import asyncio

import pytest

from app.storage.local_store import LocalStore


@pytest.fixture
def store(tmp_path):
    return LocalStore(str(tmp_path / "m.db"))


@pytest.mark.asyncio
async def test_mark_paid_and_grant_grants_exactly_once(store):
    # FIX #2 — the latch and the grant land in ONE transaction.
    await store.ensure_profile("u")
    await store.record_purchase("ord1", "u", "starter", 100, 9900, status="created")

    assert await store.mark_paid_and_grant("ord1", "u", 100, "purchase:starter") is True
    assert await store.get_credits("u") == 100
    assert (await store.get_purchase("ord1"))["status"] == "paid"

    # Retry (Razorpay re-delivery): already paid -> no second grant.
    assert await store.mark_paid_and_grant("ord1", "u", 100, "purchase:starter") is False
    assert await store.get_credits("u") == 100


@pytest.mark.asyncio
async def test_mark_paid_and_grant_missing_profile_rolls_back_latch(store):
    # If the grant cannot land (no profile), the 'paid' latch must roll back too,
    # so the order is never stranded paid-without-credits — a retry can still grant.
    await store.record_purchase("ord2", "ghost", "starter", 100, 9900, status="created")
    with pytest.raises(KeyError):
        await store.mark_paid_and_grant("ord2", "ghost", 100, "purchase:starter")
    assert (await store.get_purchase("ord2"))["status"] == "created"


@pytest.mark.asyncio
async def test_concurrent_credit_ops_lose_no_writes(store):
    # FIX #6 — many concurrent grant/deduct ops over the single shared sqlite
    # connection must not lose a write to a sibling's rollback(); every committed
    # op must leave its ledger row.
    await store.ensure_profile("c")
    await store.grant_credits("c", 1000, "seed")  # 1 ledger row

    grants = [store.grant_credits("c", 2, f"g{i}") for i in range(40)]
    deducts = [store.deduct_credits("c", 1, f"d{i}") for i in range(40)]
    await asyncio.gather(*grants, *deducts)

    # final = 1000 + 40*2 - 40*1 = 1040; ample balance so every deduct succeeds.
    assert await store.get_credits("c") == 1040
    row = store._conn.execute(
        "SELECT COUNT(*) AS n FROM credit_transactions WHERE user_id = 'c'"
    ).fetchone()
    assert row["n"] == 81  # 1 seed + 40 grants + 40 deducts, none stomped
