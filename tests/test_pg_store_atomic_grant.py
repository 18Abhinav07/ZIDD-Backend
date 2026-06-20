"""PgStore.mark_paid_and_grant atomicity (cloud webhook money path).

The cloud backend's OLD two-step latch (repo.mark_purchase_paid committed, THEN
repo.grant_credits committed in a second transaction) could leave an order
permanently 'paid' with credits never granted if the grant failed between the
two commits — and Razorpay's retry then hit `status != 'paid'` -> 0 rows ->
grant skipped forever (customer paid, no credits). The fix folds both into
repo.mark_paid_and_grant under a SINGLE commit() with rollback-on-failure.

These tests exercise that contract at the LOGIC layer with a fake AsyncSession:
the project has no Postgres in CI (and aiosqlite is not installed), so they
assert the execute/commit/rollback SEQUENCE rather than real asyncpg
transaction isolation. The single-commit + rollback-on-failure structure
mirrors the already-shipped, reviewed repo.charge_and_unlock atomic pattern.
"""
from contextlib import asynccontextmanager

import pytest

import app.storage.pg_store as pg_store_mod
from app.db import repo
from app.storage.pg_store import PgStore


class _FakeResult:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class _FakeSession:
    """Records execute/commit/rollback order; can fail on a chosen SQL fragment."""

    def __init__(self, *, paid_rowcount=1, profile_rowcount=1, fail_on=None):
        self.ops: list[tuple[str, str]] = []   # ("execute"|"commit"|"rollback", sql)
        self.commits = 0
        self.rollbacks = 0
        self._paid_rowcount = paid_rowcount
        self._profile_rowcount = profile_rowcount
        self._fail_on = fail_on               # substring -> raise RuntimeError

    async def execute(self, stmt, params=None):
        sql = " ".join(str(stmt).split())     # collapse the text() whitespace
        self.ops.append(("execute", sql))
        if self._fail_on and self._fail_on in sql:
            raise RuntimeError("simulated DB failure")
        if "UPDATE purchases" in sql:
            return _FakeResult(self._paid_rowcount)
        if "UPDATE learner_profiles" in sql:
            return _FakeResult(self._profile_rowcount)
        return _FakeResult(1)

    async def commit(self):
        self.commits += 1
        self.ops.append(("commit", ""))

    async def rollback(self):
        self.rollbacks += 1
        self.ops.append(("rollback", ""))

    def sql_ops(self) -> list[str]:
        return [sql for kind, sql in self.ops if kind == "execute"]


# ---------- repo.mark_paid_and_grant: the atomic unit ----------

@pytest.mark.asyncio
async def test_fresh_webhook_latches_and_grants_in_one_commit():
    s = _FakeSession(paid_rowcount=1, profile_rowcount=1)
    ok = await repo.mark_paid_and_grant(s, "order_1", "u1", 100, "purchase:starter")
    assert ok is True
    # Exactly ONE commit, no rollback — latch + grant + ledger are one unit.
    assert s.commits == 1
    assert s.rollbacks == 0
    sqls = s.sql_ops()
    assert any("UPDATE purchases" in q for q in sqls)
    assert any("UPDATE learner_profiles SET credits = credits + :amt" in q for q in sqls)
    assert any("INSERT INTO credit_transactions" in q for q in sqls)


@pytest.mark.asyncio
async def test_retry_already_paid_does_not_grant_or_commit():
    # The latch UPDATE matches 0 rows (already paid) -> no grant, no commit.
    s = _FakeSession(paid_rowcount=0)
    ok = await repo.mark_paid_and_grant(s, "order_1", "u1", 100, "purchase:starter")
    assert ok is False
    assert s.commits == 0                       # nothing granted
    assert s.rollbacks == 1                      # clean rollback of the no-op latch
    sqls = s.sql_ops()
    assert not any("learner_profiles" in q for q in sqls)     # grant never attempted
    assert not any("credit_transactions" in q for q in sqls)


@pytest.mark.asyncio
async def test_grant_failure_rolls_back_latch_no_commit():
    # The ledger INSERT fails AFTER the paid-latch UPDATE. The whole unit must
    # roll back: NO commit, so the 'paid' latch never persists -> a later retry
    # can still grant. This is the core money-safety guarantee.
    s = _FakeSession(paid_rowcount=1, fail_on="INSERT INTO credit_transactions")
    with pytest.raises(RuntimeError):
        await repo.mark_paid_and_grant(s, "order_1", "u1", 100, "purchase:starter")
    assert s.commits == 0
    assert s.rollbacks >= 1


@pytest.mark.asyncio
async def test_missing_profile_raises_keyerror_and_rolls_back():
    # Latch succeeds but the buyer profile is gone (UPDATE matches 0 rows).
    # Must roll back the latch and raise KeyError so the route defers the grant.
    s = _FakeSession(paid_rowcount=1, profile_rowcount=0)
    with pytest.raises(KeyError):
        await repo.mark_paid_and_grant(s, "order_1", "ghost", 100, "purchase:starter")
    assert s.commits == 0
    assert s.rollbacks >= 1


@pytest.mark.asyncio
async def test_negative_credits_rejected_before_any_write():
    s = _FakeSession()
    with pytest.raises(ValueError):
        await repo.mark_paid_and_grant(s, "order_1", "u1", -5, "purchase:starter")
    assert s.commits == 0
    assert s.sql_ops() == []                     # rejected before touching the DB


# ---------- PgStore wrapper: delegation + degrade + error parity ----------

@pytest.mark.asyncio
async def test_pgstore_delegates_to_repo_atomic_grant(monkeypatch):
    captured = {}

    @asynccontextmanager
    async def _fake_session():
        yield _FakeSession(paid_rowcount=1, profile_rowcount=1)

    async def _spy(session, order_id, user_id, credits, reason):
        captured["args"] = (order_id, user_id, credits, reason)
        return True

    monkeypatch.setattr(pg_store_mod, "_session", _fake_session)
    monkeypatch.setattr(repo, "mark_paid_and_grant", _spy)
    ok = await PgStore().mark_paid_and_grant("o1", "u1", 100, "purchase:starter")
    assert ok is True
    assert captured["args"] == ("o1", "u1", 100, "purchase:starter")


@pytest.mark.asyncio
async def test_pgstore_offline_returns_false(monkeypatch):
    @asynccontextmanager
    async def _none():
        yield None

    monkeypatch.setattr(pg_store_mod, "_session", _none)
    assert await PgStore().mark_paid_and_grant("o1", "u1", 100, "r") is False


@pytest.mark.asyncio
async def test_pgstore_propagates_keyerror_for_missing_profile(monkeypatch):
    # Parity with LocalStore: a missing profile raises KeyError (NOT swallowed to
    # False) so the webhook route's `except KeyError` defers reconciliation and
    # leaves the order unpaid. Runs the REAL repo helper against a fake session.
    @asynccontextmanager
    async def _fake_session():
        yield _FakeSession(paid_rowcount=1, profile_rowcount=0)

    monkeypatch.setattr(pg_store_mod, "_session", _fake_session)
    with pytest.raises(KeyError):
        await PgStore().mark_paid_and_grant("o1", "ghost", 100, "r")
