"""PgStore._session() context manager — single-yield, degrade-gracefully.

_session() must yield exactly once per path:
  * a live AsyncSession (closed in the finally), or
  * None when the engine/sessionmaker can't be built.

A body exception must propagate UNCHANGED. The OLD code wrapped the body in
`except Exception: yield None`, which yields a SECOND time and makes
asynccontextmanager raise RuntimeError("generator didn't stop after athrow()"),
masking the real error. test_body_exception_propagates_unchanged pins that:
it raises ValueError inside the `with` body and asserts the SAME ValueError
escapes (it would be a RuntimeError under the old double-yield) and the session
still closes.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

import app.db.engine as engine_mod  # noqa: E402
from app.storage.pg_store import _session  # noqa: E402


class _CloseTrackingSession:
    """Minimal stand-in for an AsyncSession: records that close() ran."""

    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def _install_maker(monkeypatch, sess):
    # get_sessionmaker() -> maker; maker() -> sess. _session imports the name
    # lazily, so patching the attribute on app.db.engine is enough.
    monkeypatch.setattr(engine_mod, "get_sessionmaker", lambda: (lambda: sess))


@pytest.mark.asyncio
async def test_happy_path_yields_session_and_closes(monkeypatch):
    sess = _CloseTrackingSession()
    _install_maker(monkeypatch, sess)
    async with _session() as s:
        assert s is sess
    assert sess.closed is True  # finally ran on the normal exit


@pytest.mark.asyncio
async def test_body_exception_propagates_unchanged(monkeypatch):
    # The core regression guard: a body exception must surface as ITSELF, not as
    # the double-yield RuntimeError, and the session must still close.
    sess = _CloseTrackingSession()
    _install_maker(monkeypatch, sess)
    with pytest.raises(ValueError, match="boom"):
        async with _session() as s:
            assert s is sess
            raise ValueError("boom")
    assert sess.closed is True  # finally still closed despite the raise


@pytest.mark.asyncio
async def test_yields_none_when_sessionmaker_unavailable(monkeypatch):
    def _boom():
        raise RuntimeError("engine not configured")

    monkeypatch.setattr(engine_mod, "get_sessionmaker", _boom)
    async with _session() as s:
        assert s is None  # degrade: caller no-ops


@pytest.mark.asyncio
async def test_yields_none_when_maker_raises(monkeypatch):
    # The robustness gain from folding `sess = maker()` into the setup try:
    # a session-construction failure now degrades to None instead of raising on
    # __aenter__ (which the caller's body-level guard could not catch).
    def _maker():
        raise RuntimeError("pool exhausted")

    monkeypatch.setattr(engine_mod, "get_sessionmaker", lambda: _maker)
    async with _session() as s:
        assert s is None


@pytest.mark.asyncio
async def test_none_path_does_not_call_close(monkeypatch):
    # When setup fails we never built a session, so there is nothing to close and
    # no AttributeError on a missing `sess`. A body exception on the None path
    # still propagates unchanged.
    def _boom():
        raise RuntimeError("engine not configured")

    monkeypatch.setattr(engine_mod, "get_sessionmaker", _boom)
    with pytest.raises(KeyError):
        async with _session() as s:
            assert s is None
            raise KeyError("caller-side error on the offline path")
