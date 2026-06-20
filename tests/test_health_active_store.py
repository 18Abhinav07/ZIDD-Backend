"""/health `sqlite_writable` must reflect the ACTIVE store, not the dormant
cloud engine.

Before this, the probe ran SELECT 1 against the Supabase pooler engine
(get_engine()) regardless of backend, so a local build — whose real store is the
SQLite LocalStore — reported sqlite_writable:false even though every
credit/purchase/grant persists fine. The field now asks the active store about
itself: a real write probe on LocalStore (under AI_BACKEND=local), or pooler
connectivity on PgStore (cloud).
"""
import os
import tempfile

os.environ["AI_BACKEND"] = "local"
_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["LOCAL_STORE_PATH"] = _DB.name
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.storage import reset_storage  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    yield
    reset_storage()
    get_settings.cache_clear()


def test_health_reports_active_local_store_writable():
    # The active LocalStore IS writable, so the field must be True on a local
    # build — even though the Supabase pooler (the old probe target) is
    # unreachable in tests.
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["sqlite_writable"] is True


@pytest.mark.asyncio
async def test_local_store_ping_writable_true():
    from app.storage.local_store import LocalStore

    store = LocalStore(_DB.name)
    assert await store.ping_writable() is True


@pytest.mark.asyncio
async def test_pg_store_ping_writable_false_when_pooler_unreachable():
    # The OLD false-on-local was really "cloud engine unreachable"; that signal
    # now lives ONLY on the cloud backend, where it is honest.
    from app.storage.pg_store import PgStore

    assert await PgStore().ping_writable() is False
