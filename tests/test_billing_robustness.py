"""Findings #10 (malformed webhook body) and #15 (create_order gateway error).

Both must degrade to a clean HTTP error instead of an unhandled 500.
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

import pytest
from fastapi.testclient import TestClient

from app.billing import razorpay_client
from app.config import get_settings
from app.main import app
from app.storage import get_storage, reset_storage

AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"


@pytest.fixture(autouse=True)
def _isolate_store(monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    yield
    reset_storage()
    get_settings.cache_clear()


def test_webhook_malformed_body_is_400_not_500(monkeypatch):
    # FIX #10 — signature-valid but non-JSON body: clean 400, not a 500 that
    # Razorpay would retry forever.
    monkeypatch.setattr(
        razorpay_client, "verify_webhook_signature", lambda body, sig: True
    )
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post(
        "/billing/razorpay/webhook",
        content=b"not-json{{{",
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert r.status_code == 400


def test_webhook_non_object_json_is_400(monkeypatch):
    # A valid-JSON-but-not-an-object body (e.g. a bare list) must also 400, never
    # crash on `.get(...)`.
    monkeypatch.setattr(
        razorpay_client, "verify_webhook_signature", lambda body, sig: True
    )
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post(
        "/billing/razorpay/webhook",
        content=b"[1, 2, 3]",
        headers={"X-Razorpay-Signature": "sig"},
    )
    assert r.status_code == 400


def test_create_order_gateway_failure_is_502_no_purchase(monkeypatch):
    # FIX #15 — Razorpay outage: clean 502, and no orphan purchase row recorded.
    def _boom(amount_paise, receipt):
        raise RuntimeError("razorpay 503 service unavailable")

    monkeypatch.setattr(razorpay_client, "create_order", _boom)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.post("/billing/purchase/order", json={"pack_id": "starter"}, headers=AUTH)
    assert r.status_code == 502

    # No purchase row should exist for a never-created order.
    store = get_storage()
    rows = store._conn.execute("SELECT COUNT(*) AS n FROM purchases").fetchone()
    assert rows["n"] == 0
