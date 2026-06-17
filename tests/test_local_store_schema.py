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
async def test_get_profile_has_credit_fields(store):
    await store.ensure_profile("u1", name="U One")
    profile = await store.get_profile("u1")
    assert profile is not None
    assert profile["credits"] == 0
    assert profile["demo_unlimited"] is False
    assert profile["name"] == "U One"


@pytest.mark.asyncio
async def test_billing_tables_exist(store):
    # content_unlocks / credit_transactions / purchases must be queryable.
    rows = store._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name IN ('content_unlocks','credit_transactions','purchases')"
    ).fetchall()
    names = {r["name"] for r in rows}
    assert names == {"content_unlocks", "credit_transactions", "purchases"}
