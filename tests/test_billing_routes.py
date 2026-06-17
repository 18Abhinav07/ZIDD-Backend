# tests/test_billing_routes.py
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

from fastapi.testclient import TestClient

from app.content.registry import COMM_ID, get_module
from app.main import app
from app.storage import get_storage

COMM_FIRST = get_module(COMM_ID).order[0]
COMM_SECOND = get_module(COMM_ID).order[1]
AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_packs_endpoint():
    client = TestClient(app)
    r = client.get("/billing/packs", headers=AUTH)
    assert r.status_code == 200
    assert [p["id"] for p in r.json()["packs"]] == ["starter", "value", "pro"]


def test_balance_endpoint():
    store = get_storage()
    _run(store.ensure_profile("test_user"))
    _run(store.grant_credits("test_user", 50, "welcome"))
    client = TestClient(app)
    r = client.get("/billing/balance", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "test_user"
    assert body["credits"] == 50
    assert body["demo_unlimited"] is False


def test_quote_free_taste_and_paid():
    store = get_storage()
    _run(store.ensure_profile("test_user"))
    client = TestClient(app)
    free = client.get("/billing/quote", params={"node_id": COMM_FIRST}, headers=AUTH)
    assert free.status_code == 200
    assert free.json()["free"] is True
    assert free.json()["reason"] == "free_taste"
    paid = client.get("/billing/quote", params={"node_id": COMM_SECOND}, headers=AUTH)
    assert paid.status_code == 200
    assert paid.json()["free"] is False
    assert paid.json()["cost"] == 40


def test_quote_unknown_node_404():
    client = TestClient(app)
    r = client.get("/billing/quote", params={"node_id": "nope"}, headers=AUTH)
    assert r.status_code == 404


def test_unlocks_endpoint():
    store = get_storage()
    _run(store.ensure_profile("test_user"))
    _run(store.add_unlock("test_user", "feature", COMM_ID, 40))
    client = TestClient(app)
    r = client.get("/billing/unlocks", headers=AUTH)
    assert r.status_code == 200
    unlocks = r.json()["unlocks"]
    assert any(u["scope"] == "feature" and u["ref_id"] == COMM_ID for u in unlocks)
