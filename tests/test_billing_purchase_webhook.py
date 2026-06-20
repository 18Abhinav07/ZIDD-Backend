# tests/test_billing_purchase_webhook.py
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

import json

import pytest
from fastapi.testclient import TestClient

from app.billing import razorpay_client
from app.config import get_settings
from app.main import app
from app.storage import reset_storage

AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"


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
    # The DB file persists across tests; wipe billing tables so each test starts
    # clean (fresh unpaid orders), keeping the new webhook tests faithful.
    from app.storage import get_storage
    get_storage()  # ensure the LocalStore schema exists before wiping
    import sqlite3
    conn = sqlite3.connect(_DB.name)
    conn.executescript(
        "DELETE FROM purchases; "
        "DELETE FROM content_unlocks; "
        "DELETE FROM credit_transactions; "
        "DELETE FROM profiles;"
    )
    conn.commit()
    conn.close()
    yield


@pytest.fixture(autouse=True)
def stub_razorpay(monkeypatch):
    monkeypatch.setattr(
        razorpay_client, "create_order",
        lambda amount_paise, receipt: {"id": "order_test_abc"},
    )
    monkeypatch.setattr(
        razorpay_client, "verify_webhook_signature",
        lambda body, signature: True,
    )


def test_order_then_webhook_grants_credits_once():
    client = TestClient(app)
    # Register so the profile exists and gets 50 welcome credits.
    reg = client.post("/auth/register", json={"user_id": "test_user", "password": "pw"})
    assert reg.status_code == 200

    # Create a Razorpay order for the Starter pack (100 credits).
    order = client.post("/billing/purchase/order", json={"pack_id": "starter"}, headers=AUTH)
    assert order.status_code == 200
    assert order.json()["order_id"] == "order_test_abc"

    webhook_body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_test_abc",
                        "status": "captured",
                        "amount": 9900,
                    }
                }
            },
        }
    )

    # First webhook: grants 100 -> 150 total.
    w1 = client.post(
        "/billing/razorpay/webhook",
        content=webhook_body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w1.status_code == 200
    assert w1.json()["status"] == "ok"
    bal1 = client.get("/billing/balance", headers=AUTH).json()
    assert bal1["credits"] == 150

    # Second (retry) webhook: idempotent, no double grant.
    w2 = client.post(
        "/billing/razorpay/webhook",
        content=webhook_body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w2.status_code == 200
    bal2 = client.get("/billing/balance", headers=AUTH).json()
    assert bal2["credits"] == 150


def _register_and_order(client):
    # The DB file persists across tests in this module, so test_user may already
    # exist from a prior test — registration is idempotent for our purposes.
    client.post("/auth/register", json={"user_id": "test_user", "password": "pw"})
    order = client.post("/billing/purchase/order", json={"pack_id": "starter"}, headers=AUTH)
    assert order.status_code == 200


def test_webhook_ignores_non_captured_event():
    # A correctly-SIGNED webhook for a known created order but with a
    # non-captured event (payment.failed) must NOT grant credits and must NOT
    # flip the purchase to paid. Acknowledge with 200 so Razorpay stops retrying.
    client = TestClient(app)
    _register_and_order(client)
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]

    webhook_body = json.dumps(
        {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_test_abc",
                        "status": "failed",
                        "amount": 9900,
                    }
                }
            },
        }
    )
    w = client.post(
        "/billing/razorpay/webhook",
        content=webhook_body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w.status_code == 200
    # Balance unchanged: no grant on a non-captured event.
    after = client.get("/billing/balance", headers=AUTH).json()["credits"]
    assert after == before


def test_webhook_unknown_order_acks_and_warns(caplog):
    # A signature-valid captured payment for an order we never recorded must:
    #  - return 200 (so Razorpay stops retrying),
    #  - report status "unknown_order",
    #  - grant NO credits,
    #  - and emit a warning log so the anomaly is observable (not silently dropped).
    client = TestClient(app)
    client.post("/auth/register", json={"user_id": "test_user", "password": "pw"})
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]

    webhook_body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_never_seen",  # no matching purchase row
                        "status": "captured",
                        "amount": 9900,
                    }
                }
            },
        }
    )
    with caplog.at_level("WARNING", logger="app.api.billing_routes"):
        w = client.post(
            "/billing/razorpay/webhook",
            content=webhook_body,
            headers={"X-Razorpay-Signature": "sig"},
        )
    assert w.status_code == 200
    assert w.json()["status"] == "unknown_order"
    after = client.get("/billing/balance", headers=AUTH).json()["credits"]
    assert after == before  # no grant
    assert any(
        "unknown order_id=order_never_seen" in r.getMessage() for r in caplog.records
    )


def test_webhook_rejects_amount_mismatch():
    # A SIGNED payment.captured event whose amount != the stored amount_paise
    # must NOT grant credits and must NOT mark the purchase paid.
    client = TestClient(app)
    _register_and_order(client)
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]

    webhook_body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_test_abc",
                        "status": "captured",
                        "amount": 1,  # mismatch: stored amount_paise is 9900
                    }
                }
            },
        }
    )
    w = client.post(
        "/billing/razorpay/webhook",
        content=webhook_body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w.status_code == 200
    after = client.get("/billing/balance", headers=AUTH).json()["credits"]
    assert after == before


# ---------- signature-valid but structurally malformed: 200-ack, never 500 ----------
# A 500 here is retried by Razorpay forever and never reaches a reconcilable
# terminal status. These must degrade like the sibling anomaly branches: ack, log,
# never grant.

def test_webhook_string_amount_is_200_not_500():
    # amount is a non-numeric string -> int() would ValueError into a 500.
    client = TestClient(app, raise_server_exceptions=False)
    _register_and_order(client)
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]
    body = json.dumps({
        "event": "payment.captured",
        "payload": {"payment": {"entity": {
            "order_id": "order_test_abc", "status": "captured", "amount": "not-a-number",
        }}},
    })
    w = client.post(
        "/billing/razorpay/webhook", content=body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w.status_code == 200
    assert w.json()["status"] == "amount_mismatch"   # not granted
    assert client.get("/billing/balance", headers=AUTH).json()["credits"] == before


def test_webhook_null_amount_is_200_not_500():
    # amount is null -> int(None) would TypeError into a 500.
    client = TestClient(app, raise_server_exceptions=False)
    _register_and_order(client)
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]
    body = json.dumps({
        "event": "payment.captured",
        "payload": {"payment": {"entity": {
            "order_id": "order_test_abc", "status": "captured", "amount": None,
        }}},
    })
    w = client.post(
        "/billing/razorpay/webhook", content=body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w.status_code == 200
    assert w.json()["status"] == "amount_mismatch"
    assert client.get("/billing/balance", headers=AUTH).json()["credits"] == before


def test_webhook_non_dict_nested_payload_is_200_not_500():
    # payload.payment is not an object -> the nested .get() chain would
    # AttributeError into a 500.
    client = TestClient(app, raise_server_exceptions=False)
    client.post("/auth/register", json={"user_id": "test_user", "password": "pw"})
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]
    body = json.dumps({
        "event": "payment.captured",
        "payload": {"payment": "totally-not-a-dict"},
    })
    w = client.post(
        "/billing/razorpay/webhook", content=body,
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert w.status_code == 200
    assert w.json()["status"] == "ignored"
    assert client.get("/billing/balance", headers=AUTH).json()["credits"] == before
