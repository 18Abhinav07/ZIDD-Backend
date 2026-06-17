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
from app.main import app

AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"


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
        {"payload": {"payment": {"entity": {"order_id": "order_test_abc"}}}}
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
