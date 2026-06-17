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

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.storage import get_storage, reset_storage


@pytest.fixture(autouse=True)
def _isolate_store(monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    yield
    reset_storage()
    get_settings.cache_clear()


def test_register_grants_welcome_credits():
    client = TestClient(app)
    r = client.post("/auth/register", json={"user_id": "newbie", "password": "pw"})
    assert r.status_code == 200
    store = get_storage()
    credits = asyncio.get_event_loop().run_until_complete(store.get_credits("newbie"))
    assert credits == 50
    txns = store._conn.execute(
        "SELECT delta, reason FROM credit_transactions WHERE user_id = ?",
        ("newbie",),
    ).fetchall()
    assert [(t["delta"], t["reason"]) for t in txns] == [(50, "welcome")]
