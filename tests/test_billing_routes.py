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

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.content.registry import COMM_ID, get_module
from app.main import app
from app.storage import get_storage, reset_storage

COMM_FIRST = get_module(COMM_ID).order[0]
COMM_SECOND = get_module(COMM_ID).order[1]
AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"


@pytest.fixture(autouse=True)
def _isolate_store(monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    yield
    reset_storage()
    get_settings.cache_clear()


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


def test_balance_includes_profile_name():
    # The dashboard greets by the profile name (matching the coach), so balance
    # carries it. ensure_profile updates the name when non-empty.
    store = get_storage()
    _run(store.ensure_profile("test_user", "Asha"))
    client = TestClient(app)
    r = client.get("/billing/balance", headers=AUTH)
    assert r.status_code == 200
    assert r.json()["name"] == "Asha"


def test_dev_grant_tops_up_in_non_prod():
    store = get_storage()
    _run(store.ensure_profile("test_user"))
    client = TestClient(app)
    r = client.post("/billing/dev/grant", params={"amount": 300}, headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["granted"] == 300
    assert body["credits"] >= 300
    bal = client.get("/billing/balance", headers=AUTH)
    assert bal.json()["credits"] == body["credits"]


def test_dev_grant_unavailable_in_prod(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    get_settings.cache_clear()
    client = TestClient(app)
    r = client.post("/billing/dev/grant", headers=AUTH)
    assert r.status_code != 200  # hard-disabled outside non-prod (404, never funds)


import hashlib as _hashlib  # noqa: E402
import hmac as _hmac  # noqa: E402


def _sign(order_id, payment_id, secret):
    return _hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), _hashlib.sha256).hexdigest()


def test_razorpay_verify_grants_once_on_valid_signature(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "shh_test_secret")
    get_settings.cache_clear()
    store = get_storage()
    _run(store.ensure_profile("test_user"))
    base = _run(store.get_credits("test_user"))   # the shared DB may carry residual
    _run(store.record_purchase("order_V", "test_user", "starter", 100, 9900, status="created"))
    sig = _sign("order_V", "pay_V", "shh_test_secret")
    body = {"razorpay_order_id": "order_V", "razorpay_payment_id": "pay_V", "razorpay_signature": sig}
    client = TestClient(app)
    r = client.post("/billing/razorpay/verify", json=body, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["granted"] is True and r.json()["credits"] == base + 100
    # idempotent: a second verify (or a later webhook) never double-grants
    r2 = client.post("/billing/razorpay/verify", json=body, headers=AUTH)
    assert r2.json()["granted"] is False and r2.json()["credits"] == base + 100


def test_razorpay_verify_rejects_forged_signature(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "shh_test_secret")
    get_settings.cache_clear()
    store = get_storage()
    _run(store.ensure_profile("test_user"))
    base = _run(store.get_credits("test_user"))
    _run(store.record_purchase("order_F", "test_user", "starter", 100, 9900, status="created"))
    client = TestClient(app)
    r = client.post("/billing/razorpay/verify", json={
        "razorpay_order_id": "order_F", "razorpay_payment_id": "pay_F",
        "razorpay_signature": "deadbeef",
    }, headers=AUTH)
    assert r.status_code == 400
    assert _run(store.get_credits("test_user")) == base  # never granted


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
