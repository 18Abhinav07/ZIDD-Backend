"""FIX 3 — atomic credit deduction on the Postgres repo path.

The cloud (Postgres) backend uses ``repo.deduct_credit``. The original
implementation read the balance in Python, checked ``credits < amount``, then
issued an unguarded ``UPDATE ... SET credits = credits - :amt``. Two concurrent
spends could both pass the Python check and both subtract — double-spend.

The local integration suite exercises LocalStore (SQLite), not this Postgres
path, so we drive ``repo.deduct_credit`` directly against a faithful fake
``AsyncSession`` that records executed SQL and simulates ``rowcount``. This lets
us assert the two properties of the fix without a live Postgres:

  1. the spend UPDATE carries the ``credits >= :amt`` guard, and
  2. when that guarded UPDATE affects 0 rows (``rowcount == 0``) the call
     reports insufficient funds (returns False) instead of succeeding.

The demo-unlimited bypass must remain: those profiles are never charged and
always allowed.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.db import repo


class _FakeResult:
    """Mimics the slice of the SQLAlchemy Result API repo.deduct_credit uses."""

    def __init__(self, rows=None, rowcount=0):
        self._rows = rows or []
        self.rowcount = rowcount

    def mappings(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeSession:
    """Records every (sql, params) executed and returns scripted results.

    ``update_rowcount`` is the rowcount the guarded spend UPDATE will report;
    set it to 0 to simulate the WHERE guard rejecting an over-spend.
    """

    def __init__(self, profile_row, update_rowcount):
        self._profile_row = profile_row
        self._update_rowcount = update_rowcount
        self.executed = []  # list of (sql_text, params)
        self.committed = False

    async def execute(self, stmt, params=None):
        sql = str(getattr(stmt, "text", stmt))
        self.executed.append((sql, params or {}))
        low = sql.lower()
        if low.startswith("select") and "learner_profiles" in low:
            rows = [self._profile_row] if self._profile_row is not None else []
            return _FakeResult(rows=rows)
        if "update learner_profiles" in low:
            return _FakeResult(rowcount=self._update_rowcount)
        # credit_transactions insert / anything else
        return _FakeResult()

    async def commit(self):
        self.committed = True

    def _spend_update(self):
        for sql, params in self.executed:
            if "update learner_profiles" in sql.lower() and "credits = credits -" in sql.lower():
                return sql, params
        return None, None


@pytest.mark.asyncio
async def test_deduct_uses_atomic_guard_in_update():
    # Enough balance, the guarded UPDATE affects 1 row -> charge succeeds AND the
    # UPDATE itself must carry the `credits >= :amt` guard (atomic, no TOCTOU).
    session = _FakeSession(
        profile_row={"demo_unlimited": False, "credits": 100}, update_rowcount=1
    )
    ok = await repo.deduct_credit(session, "u1", 40, "spend")
    assert ok is True

    sql, params = session._spend_update()
    assert sql is not None, "spend UPDATE on learner_profiles not found"
    low = sql.lower()
    assert "credits >= :amt" in low, (
        "spend UPDATE must guard on `credits >= :amt` so the check and the "
        "decrement are one atomic statement"
    )
    assert "where user_id = :uid" in low
    assert params.get("amt") == 40


@pytest.mark.asyncio
async def test_deduct_returns_false_when_guarded_update_matches_zero_rows():
    # The guarded UPDATE matches 0 rows (insufficient funds at write time) ->
    # the call must report failure, NOT silently succeed.
    session = _FakeSession(
        profile_row={"demo_unlimited": False, "credits": 100}, update_rowcount=0
    )
    ok = await repo.deduct_credit(session, "u1", 40, "spend")
    assert ok is False, "rowcount==0 from the guarded UPDATE means insufficient funds"


@pytest.mark.asyncio
async def test_demo_unlimited_bypass_is_preserved():
    # Demo/judge profiles are never charged and always allowed: no spend UPDATE.
    session = _FakeSession(
        profile_row={"demo_unlimited": True, "credits": 0}, update_rowcount=0
    )
    ok = await repo.deduct_credit(session, "judge", 40, "spend")
    assert ok is True
    sql, _ = session._spend_update()
    assert sql is None, "demo_unlimited profiles must not trigger a spend UPDATE"


@pytest.mark.asyncio
async def test_missing_profile_returns_false():
    session = _FakeSession(profile_row=None, update_rowcount=0)
    ok = await repo.deduct_credit(session, "ghost", 40, "spend")
    assert ok is False
