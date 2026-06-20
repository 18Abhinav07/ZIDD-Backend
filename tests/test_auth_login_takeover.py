"""Finding #1 — login account-takeover + register input validation.

A profile seeded WITHOUT a password (session/legacy/demo id) must not be
loginable. The old code hashed the caller's submitted password into such a
profile and then verified against that just-written hash, minting a valid token
for any account whose id was known. Registration must also reject blank ids.
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


@pytest.fixture(autouse=True)
def reset_state(_isolate_store):
    get_storage()  # ensure the schema exists before wiping
    import sqlite3
    conn = sqlite3.connect(_DB.name)
    conn.executescript("DELETE FROM credit_transactions; DELETE FROM profiles;")
    conn.commit()
    conn.close()
    yield


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_login_against_null_hash_profile_is_401():
    store = get_storage()
    _run(store.ensure_profile("victim"))  # NULL password_hash
    client = TestClient(app)
    r = client.post("/auth/login", json={"user_id": "victim", "password": "anything"})
    assert r.status_code == 401
    # The failed attempt must NOT have provisioned a password hash either.
    prof = _run(store.get_profile("victim"))
    assert not prof.get("password_hash")


def test_register_then_login_roundtrip():
    client = TestClient(app)
    reg = client.post("/auth/register", json={"user_id": "alice", "password": "pw123"})
    assert reg.status_code == 200
    ok = client.post("/auth/login", json={"user_id": "alice", "password": "pw123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    bad = client.post("/auth/login", json={"user_id": "alice", "password": "wrong"})
    assert bad.status_code == 401


def test_register_rejects_blank_user_id():
    client = TestClient(app)
    for uid in ("", "   "):
        r = client.post("/auth/register", json={"user_id": uid, "password": "pw"})
        assert r.status_code == 400


def test_register_rejects_blank_password():
    client = TestClient(app)
    r = client.post("/auth/register", json={"user_id": "bob", "password": ""})
    assert r.status_code == 400
