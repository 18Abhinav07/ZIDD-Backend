"""FIX #9 — PgStore.load_context must return the SAME shape as LocalStore.

Callers (session_service.start_session) iterate the result and call
`mem.get("node_id")` / `mem.get("raw")` — i.e. they require list[dict]. The pg
path used to return a §-delimited str, so the loop silently iterated characters.
Both backends must hand back list[dict] with the identical key set.

Offline / DB-mocked: no live Postgres, no embeddings. We stub pg_store._session
to yield a fake AsyncSession whose execute() returns canned rows, mirroring the
monkeypatch pattern in test_pg_store_billing_degrade.py.
"""
import os
from contextlib import asynccontextmanager

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

import app.storage.pg_store as pg_store
from app.storage.pg_store import PgStore
from app.storage.local_store import LocalStore

# The canonical dict shape every backend's load_context element must carry.
_KEYS = {"node_id", "score", "strengths", "watch", "next_focus", "date", "raw"}

_SUMMARY = "Strengths: clear stance\nWatch: filler words\nNext focus: structure"


@pytest.mark.asyncio
async def test_local_load_context_returns_list_of_dicts(tmp_path):
    store = LocalStore(str(tmp_path / "c.db"))
    await store.write_memory(
        "u1", "s1", "gd_01", _SUMMARY, task_type="gd_prep", score=0.6
    )
    out = await store.load_context("u1", "gd_prep")
    assert isinstance(out, list)
    assert out and isinstance(out[0], dict)
    assert set(out[0].keys()) == _KEYS


@pytest.mark.asyncio
async def test_pg_load_context_returns_list_of_dicts(monkeypatch):
    # Fake session whose execute().all() yields (competency_node, content) rows,
    # the shape memory_store.load_context now reads. We bypass embeddings by
    # stubbing embed.
    class _Result:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    class _FakeSession:
        async def execute(self, *a, **k):
            # The REAL competency node ("gd_01"), distinct from the task_type
            # ("gd_prep") the lookup is keyed by.
            return _Result([("gd_01", _SUMMARY)])

    @asynccontextmanager
    async def _fake_session():
        yield _FakeSession()

    monkeypatch.setattr(pg_store, "_session", _fake_session)

    import app.memory.store as memory_store

    async def _fake_embed(text):
        return [0.0] * 768

    monkeypatch.setattr(memory_store, "embed", _fake_embed)

    store = PgStore()
    out = await store.load_context("u1", "gd_prep")
    assert isinstance(out, list)
    assert out and isinstance(out[0], dict)
    assert set(out[0].keys()) == _KEYS
    # FIX #6 regression: the row carries the REAL competency node, not the coarse
    # task_type — so the node-level welcome-back match in start_session can fire.
    assert out[0]["node_id"] == "gd_01"
    assert out[0]["node_id"] != "gd_prep"


@pytest.mark.asyncio
async def test_pg_load_context_offline_returns_empty_list(monkeypatch):
    # Offline (no session) must be [] not "" — same empty shape as LocalStore.
    @asynccontextmanager
    async def _none():
        yield None

    monkeypatch.setattr(pg_store, "_session", _none)
    store = PgStore()
    out = await store.load_context("u1", "gd_prep")
    assert out == []
    assert isinstance(out, list)


@pytest.mark.asyncio
async def test_both_backends_same_shape(tmp_path, monkeypatch):
    """The crux: for the same logical summary, both stores' first element has
    the identical key set — the cross-backend contract callers rely on."""
    local = LocalStore(str(tmp_path / "c2.db"))
    await local.write_memory(
        "u1", "s1", "gd_01", _SUMMARY, task_type="gd_prep", score=0.6
    )
    local_out = await local.load_context("u1", "gd_prep")

    class _Result:
        def all(self):
            return [("gd_01", _SUMMARY)]

    class _FakeSession:
        async def execute(self, *a, **k):
            return _Result()

    @asynccontextmanager
    async def _fake_session():
        yield _FakeSession()

    monkeypatch.setattr(pg_store, "_session", _fake_session)
    import app.memory.store as memory_store

    async def _fake_embed(text):
        return [0.0] * 768

    monkeypatch.setattr(memory_store, "embed", _fake_embed)
    pg_out = await PgStore().load_context("u1", "gd_prep")

    assert type(local_out) is type(pg_out) is list
    assert set(local_out[0].keys()) == set(pg_out[0].keys()) == _KEYS
