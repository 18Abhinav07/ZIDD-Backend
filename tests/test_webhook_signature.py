"""C1 — exercise the REAL webhook HMAC path end to end.

Every other billing test stubs `verify_webhook_signature -> True`, so the actual
signing formula and the `400 Invalid signature` branch
(`billing_routes.py:121-122`) were never executed by the suite — a future
regression to the HMAC could ship green. These tests deliberately do NOT stub the
verifier:

  * a unit test pins a known secret and asserts the real
    `hmac.new(secret, body, sha256).hexdigest()` is accepted and ANY other
    signature (tampered, empty, junk, or right-sig-wrong-body) is rejected;
  * a route test posts a garbage `X-Razorpay-Signature` and asserts 400 + no
    grant (proving the dead branch is live);
  * a route test signs the EXACT body bytes the route reads and asserts the
    happy path still grants — closing the loop with no stub anywhere.

Note: this module stubs ONLY `create_order` (to avoid the live Razorpay SDK);
`verify_webhook_signature` stays real.
"""
import hashlib
import hmac
import json
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

from app.billing import razorpay_client  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.storage import reset_storage  # noqa: E402

AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"
WEBHOOK_SECRET = "whsec_test_deadbeefcafe1234567890"  # known test-only secret


def _sign(body: bytes) -> str:
    """Reproduce razorpay_client.verify_webhook_signature's exact formula."""
    return hmac.new(WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _captured_body(order_id: str = "order_test_abc", amount: int = 9900) -> bytes:
    return json.dumps(
        {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": order_id,
                        "status": "captured",
                        "amount": amount,
                    }
                }
            },
        }
    ).encode("utf-8")


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    # Pin BOTH the store and the webhook secret for this module, then clear the
    # settings cache so the real verifier reads OUR known secret (an OS env var
    # wins over the .env file in pydantic-settings).
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", WEBHOOK_SECRET)
    get_settings.cache_clear()
    reset_storage()
    yield
    reset_storage()
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_state(_isolate):
    from app.storage import get_storage
    get_storage()  # ensure schema exists before wiping
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
def _stub_order_only(monkeypatch):
    # Avoid the live Razorpay SDK for order creation, but leave the webhook
    # signature verifier REAL — that is the whole point of this module.
    monkeypatch.setattr(
        razorpay_client, "create_order",
        lambda amount_paise, receipt: {"id": "order_test_abc"},
    )


def test_verify_signature_accepts_real_hmac_and_rejects_everything_else():
    body = _captured_body()
    good = _sign(body)

    assert razorpay_client.verify_webhook_signature(body, good) is True

    # tampered (flip the last hex char), empty, and junk signatures all fail
    flipped = good[:-1] + ("0" if good[-1] != "0" else "1")
    assert razorpay_client.verify_webhook_signature(body, flipped) is False
    assert razorpay_client.verify_webhook_signature(body, "") is False
    assert razorpay_client.verify_webhook_signature(body, "deadbeef") is False
    # right signature, DIFFERENT body -> fails (it signs THIS body, not any body)
    assert razorpay_client.verify_webhook_signature(body + b" ", good) is False


def test_webhook_bad_signature_returns_400_and_grants_nothing():
    client = TestClient(app)
    client.post("/auth/register", json={"user_id": "test_user", "password": "pw"})
    client.post("/billing/purchase/order", json={"pack_id": "starter"}, headers=AUTH)
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]

    w = client.post(
        "/billing/razorpay/webhook",
        content=_captured_body(),
        headers={"X-Razorpay-Signature": "not-a-valid-signature"},
    )
    assert w.status_code == 400
    assert w.json()["detail"] == "Invalid signature"
    after = client.get("/billing/balance", headers=AUTH).json()["credits"]
    assert after == before  # the 400 branch is now proven live: zero grant


def test_webhook_real_signature_grants_credits_once():
    client = TestClient(app)
    client.post("/auth/register", json={"user_id": "test_user", "password": "pw"})
    client.post("/billing/purchase/order", json={"pack_id": "starter"}, headers=AUTH)
    before = client.get("/billing/balance", headers=AUTH).json()["credits"]

    # Sign the EXACT bytes the route reads via `await request.body()`.
    body = _captured_body()
    w = client.post(
        "/billing/razorpay/webhook",
        content=body,
        headers={"X-Razorpay-Signature": _sign(body)},
    )
    assert w.status_code == 200
    assert w.json()["status"] == "ok"
    after = client.get("/billing/balance", headers=AUTH).json()["credits"]
    assert after == before + 100  # starter pack = 100 credits, real HMAC verified
