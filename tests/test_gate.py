# tests/test_gate.py
import os
import sqlite3

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.billing.gate import resolve_gate, charge
from app.content.registry import COMM_ID, INT_ID, get_module
from app.storage.local_store import LocalStore

COMM_FIRST = get_module(COMM_ID).order[0]
COMM_SECOND = get_module(COMM_ID).order[1]
INT_NODE = "int_01_elevator_pitch"


@pytest.fixture
def store(tmp_path):
    s = LocalStore(str(tmp_path / "test.db"))
    return s


@pytest.mark.asyncio
async def test_demo_user_is_free_first(store):
    await store.ensure_profile("judge")
    await store.set_demo_unlimited("judge", True)
    d = await resolve_gate(store, "judge", COMM_SECOND)
    assert d.free is True
    assert d.reason == "demo_unlimited"


@pytest.mark.asyncio
async def test_comm_first_node_is_free_taste(store):
    await store.ensure_profile("u1")
    d = await resolve_gate(store, "u1", COMM_FIRST)
    assert d.free is True
    assert d.reason == "free_taste"


@pytest.mark.asyncio
async def test_comm_second_node_costs_40(store):
    await store.ensure_profile("u1")
    d = await resolve_gate(store, "u1", COMM_SECOND)
    assert d.free is False
    assert d.cost == 40
    assert d.scope == "feature"
    assert d.ref_id == COMM_ID
    assert d.record_unlock is True
    assert d.reason == "access_unlock"


@pytest.mark.asyncio
async def test_comm_owned_is_free(store):
    await store.ensure_profile("u1")
    await store.add_unlock("u1", "feature", COMM_ID, 40)
    d = await resolve_gate(store, "u1", COMM_SECOND)
    assert d.free is True
    assert d.owned is True
    assert d.reason == "owned"


@pytest.mark.asyncio
async def test_interview_first_two_free_then_metered(store):
    await store.ensure_profile("u1")
    # 0 prior attempts -> free.
    d0 = await resolve_gate(store, "u1", INT_NODE)
    assert d0.free is True and d0.reason == "free_attempt"
    # Simulate two prior COMPLETED sessions on the interview module. Only ended
    # sessions count as consumed attempts (FIX #3).
    await store.create_session("s1", "u1", "interview", INT_ID, INT_NODE)
    await store.create_session("s2", "u1", "interview", INT_ID, INT_NODE)
    await store.end_session("s1")
    await store.end_session("s2")
    d2 = await resolve_gate(store, "u1", INT_NODE)
    assert d2.free is False
    assert d2.cost == 50
    assert d2.scope == "attempt"
    assert d2.ref_id == INT_NODE
    assert d2.record_unlock is False
    assert d2.reason == "attempt_meter"


@pytest.mark.asyncio
async def test_unknown_node_raises_keyerror(store):
    await store.ensure_profile("u1")
    with pytest.raises(KeyError):
        await resolve_gate(store, "u1", "does_not_exist")


@pytest.mark.asyncio
async def test_charge_deducts_and_records_unlock(store):
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 50, "welcome")
    d = await resolve_gate(store, "u1", COMM_SECOND)  # cost 40, record_unlock
    ok = await charge(store, "u1", d)
    assert ok is True
    assert await store.get_credits("u1") == 10
    assert await store.has_unlock("u1", "feature", COMM_ID) is True


@pytest.mark.asyncio
async def test_charge_attempt_does_not_record_unlock(store):
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 50, "welcome")
    await store.create_session("s1", "u1", "interview", INT_ID, INT_NODE)
    await store.create_session("s2", "u1", "interview", INT_ID, INT_NODE)
    await store.end_session("s1")
    await store.end_session("s2")
    d = await resolve_gate(store, "u1", INT_NODE)  # cost 50, no record_unlock
    ok = await charge(store, "u1", d)
    assert ok is True
    assert await store.get_credits("u1") == 0
    assert await store.list_unlocks("u1") == []


@pytest.mark.asyncio
async def test_charge_and_unlock_rolls_back_credits_when_unlock_fails(store):
    """FIX #2 atomicity: if the content_unlocks insert raises mid-method, the
    whole transaction must roll back — the learner is NOT charged. Proves the
    old two-transaction bug (paid-but-no-unlock) is closed: deduct + unlock are
    one unit, so a failure on the unlock leaves credits untouched."""
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 50, "welcome")

    # Force the content_unlocks INSERT (the second statement after the debit) to
    # raise, simulating a crash between the deduct and the unlock. sqlite3's
    # Connection.execute is a read-only C attribute, so wrap the connection in a
    # thin proxy that delegates everything but intercepts the unlock insert.
    real_conn = store._conn

    class _BoomConn:
        def execute(self, sql, *args, **kwargs):
            if "content_unlocks" in sql:
                raise sqlite3.OperationalError("simulated unlock-insert failure")
            return real_conn.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(real_conn, name)

    store._conn = _BoomConn()
    try:
        with pytest.raises(sqlite3.OperationalError):
            await store.charge_and_unlock("u1", 40, "access_unlock", "feature", COMM_ID)
    finally:
        store._conn = real_conn

    # Credits unchanged (debit rolled back) and no unlock recorded.
    assert await store.get_credits("u1") == 50
    assert await store.has_unlock("u1", "feature", COMM_ID) is False
    assert await store.list_unlocks("u1") == []


@pytest.mark.asyncio
async def test_charge_and_unlock_insufficient_funds_no_charge(store):
    """FIX #2 balance guard: when credits < cost the atomic UPDATE matches no row
    (rowcount 0), so the method returns False and nothing is debited or unlocked."""
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 30, "welcome")  # below the 40 cost
    ok = await store.charge_and_unlock("u1", 40, "access_unlock", "feature", COMM_ID)
    assert ok is False
    assert await store.get_credits("u1") == 30
    assert await store.has_unlock("u1", "feature", COMM_ID) is False


@pytest.mark.asyncio
async def test_charge_and_unlock_second_call_does_not_duplicate_unlock(store):
    """FIX #2 store-level idempotency (TOCTOU money race): charge_and_unlock
    inserts the unlock FIRST and charges only on a fresh insert. A second
    identical call hits ON CONFLICT DO NOTHING (rowcount 0), so it returns True
    WITHOUT a second debit — the learner pays exactly once per unlock even if two
    concurrent /session/start requests both pass the gate's not-owned check
    before either commits. Pins the fix: no duplicate unlock AND no double charge."""
    await store.ensure_profile("u1")
    await store.grant_credits("u1", 100, "welcome")

    ok1 = await store.charge_and_unlock("u1", 40, "access_unlock", "feature", COMM_ID)
    assert ok1 is True
    assert await store.get_credits("u1") == 60
    assert len(await store.list_unlocks("u1")) == 1

    # Second identical call: already owned -> ON CONFLICT inserts 0 rows, the
    # debit is skipped, and the method returns True. Credits stay at 60 and the
    # unlock row is not duplicated.
    ok2 = await store.charge_and_unlock("u1", 40, "access_unlock", "feature", COMM_ID)
    assert ok2 is True
    assert len(await store.list_unlocks("u1")) == 1   # still exactly one unlock
    assert await store.get_credits("u1") == 60        # NOT charged a second time
