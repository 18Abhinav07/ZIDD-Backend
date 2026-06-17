# tests/test_gate.py
import os

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
    # Simulate two prior sessions on the interview module.
    await store.create_session("s1", "u1", "interview", INT_ID, INT_NODE)
    await store.create_session("s2", "u1", "interview", INT_ID, INT_NODE)
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
    d = await resolve_gate(store, "u1", INT_NODE)  # cost 50, no record_unlock
    ok = await charge(store, "u1", d)
    assert ok is True
    assert await store.get_credits("u1") == 0
    assert await store.list_unlocks("u1") == []
