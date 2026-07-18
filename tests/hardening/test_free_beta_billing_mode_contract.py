import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import billing_routes
from app.billing.gate import GateDecision, charge, resolve_gate
from app.billing.models import OrderRequest
from app.config import Settings, get_settings
from app.content.registry import COMM_ID, GD_ID, INT_ID, SCHOOL_ID, get_module
from app.main import app


AUTH = {"Authorization": "Bearer test_token"}


def _set_billing_mode(monkeypatch, mode: str) -> None:
    monkeypatch.setenv("BILLING_MODE", mode)
    get_settings.cache_clear()


class NoBillingStore:
    def __getattr__(self, name):
        raise AssertionError(f"disabled billing touched store.{name}")


class IdempotentDebitStore:
    def __init__(self) -> None:
        self.balance = 100
        self.debits = 0
        self.keys: dict[tuple[str, str], tuple[int, str]] = {}

    async def deduct_credits_once(
        self,
        user_id: str,
        amount: int,
        reason: str,
        idempotency_key: str,
    ) -> bool:
        key = (user_id, idempotency_key)
        payload = (amount, reason)
        if key in self.keys:
            if self.keys[key] != payload:
                raise ValueError("credit_idempotency_key_reused_with_different_payload")
            return True
        if self.balance < amount:
            return False
        self.balance -= amount
        self.debits += 1
        self.keys[key] = payload
        return True


def test_settings_default_to_enabled_and_normalize_billing_mode(monkeypatch):
    monkeypatch.delenv("BILLING_MODE", raising=False)

    assert Settings(_env_file=None).billing_mode == "enabled"
    assert Settings(_env_file=None, billing_mode=" DISABLED ").billing_mode == "disabled"
    with pytest.raises(ValidationError):
        Settings(_env_file=None, billing_mode="paused")


@pytest.mark.parametrize("module_id", [COMM_ID, INT_ID, GD_ID, SCHOOL_ID])
def test_disabled_mode_makes_every_learning_module_free_without_store_reads(
    monkeypatch,
    module_id,
):
    _set_billing_mode(monkeypatch, "disabled")
    node_id = get_module(module_id).order[-1]

    decision = asyncio.run(resolve_gate(NoBillingStore(), "learner", node_id))

    assert decision == GateDecision(
        free=True,
        cost=0,
        scope="",
        ref_id="",
        record_unlock=False,
        owned=False,
        reason="billing_disabled",
    )


def test_disabled_mode_still_rejects_an_unknown_learning_node(monkeypatch):
    _set_billing_mode(monkeypatch, "disabled")

    with pytest.raises(KeyError):
        asyncio.run(resolve_gate(NoBillingStore(), "learner", "does_not_exist"))


def test_disabled_mode_charge_is_allowed_without_a_debit(monkeypatch):
    _set_billing_mode(monkeypatch, "disabled")
    stale_paid_decision = GateDecision(
        free=False,
        cost=50,
        scope="attempt",
        ref_id="int_01_elevator_pitch",
        record_unlock=False,
        owned=False,
        reason="attempt_meter",
    )

    outcome = asyncio.run(
        charge(
            NoBillingStore(),
            "learner",
            stale_paid_decision,
            idempotency_key="session_start:free-beta",
        )
    )

    assert outcome.allowed is True
    assert outcome.compensatable is False


def test_disabled_quote_is_free_without_credit_or_unlock_reads(monkeypatch):
    _set_billing_mode(monkeypatch, "disabled")
    monkeypatch.setattr(billing_routes, "get_storage", lambda: NoBillingStore())
    node_id = get_module(COMM_ID).order[-1]

    response = TestClient(app).get(
        "/billing/quote",
        params={"node_id": node_id},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json() == {
        "node_id": node_id,
        "free": True,
        "cost": 0,
        "scope": "",
        "ref_id": "",
        "owned": False,
        "reason": "billing_disabled",
    }


def test_disabled_payment_surfaces_are_404_before_auth_or_side_effects(monkeypatch):
    _set_billing_mode(monkeypatch, "disabled")
    monkeypatch.setenv("ZIDD_ALLOW_TEST_AUTH", "0")

    def unexpected(*_args, **_kwargs):
        raise AssertionError("disabled payment surface reached a side effect")

    monkeypatch.setattr(billing_routes, "get_storage", unexpected)
    monkeypatch.setattr(billing_routes.razorpay_client, "create_order", unexpected)
    monkeypatch.setattr(
        billing_routes.razorpay_client,
        "verify_payment_signature",
        unexpected,
    )
    monkeypatch.setattr(
        billing_routes.razorpay_client,
        "verify_webhook_signature",
        unexpected,
    )

    client = TestClient(app, raise_server_exceptions=False)
    responses = [
        client.get("/billing/packs"),
        client.post("/billing/dev/grant?amount=25"),
        client.post("/billing/purchase/order", json={"pack_id": "starter"}),
        client.post(
            "/billing/razorpay/verify",
            json={
                "razorpay_order_id": "order_disabled",
                "razorpay_payment_id": "pay_disabled",
                "razorpay_signature": "signature",
            },
        ),
        client.post(
            "/billing/razorpay/webhook",
            content=b"{}",
            headers={"X-Razorpay-Signature": "signature"},
        ),
    ]

    assert [response.status_code for response in responses] == [404] * len(responses)


def test_disabled_order_handler_rejects_before_gateway_call(monkeypatch):
    _set_billing_mode(monkeypatch, "disabled")

    def unexpected(*_args, **_kwargs):
        raise AssertionError("disabled order handler called Razorpay")

    monkeypatch.setattr(billing_routes.razorpay_client, "create_order", unexpected)
    request = SimpleNamespace(state=SimpleNamespace(user_id="learner"))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            billing_routes.create_purchase_order(
                OrderRequest(pack_id="starter"),
                request,
            )
        )

    assert exc_info.value.status_code == 404


def test_enabled_order_route_keeps_existing_gateway_and_storage_flow(monkeypatch):
    _set_billing_mode(monkeypatch, "enabled")
    recorded = []

    class PurchaseStore:
        async def record_purchase(self, *args, **kwargs):
            recorded.append((args, kwargs))

    monkeypatch.setattr(billing_routes, "get_storage", lambda: PurchaseStore())
    monkeypatch.setattr(
        billing_routes.razorpay_client,
        "create_order",
        lambda amount, receipt: {"id": "order_enabled"},
    )

    response = TestClient(app).post(
        "/billing/purchase/order",
        json={"pack_id": "starter"},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["order_id"] == "order_enabled"
    assert recorded == [
        (
            ("order_enabled", "test_user", "starter", 100, 9900),
            {"status": "created"},
        )
    ]


def test_enabled_order_route_still_requires_authentication(monkeypatch):
    _set_billing_mode(monkeypatch, "enabled")
    monkeypatch.setenv("ZIDD_ALLOW_TEST_AUTH", "0")

    def unexpected(*_args, **_kwargs):
        raise AssertionError("unauthenticated order reached Razorpay")

    monkeypatch.setattr(billing_routes.razorpay_client, "create_order", unexpected)

    response = TestClient(app, raise_server_exceptions=False).post(
        "/billing/purchase/order",
        json={"pack_id": "starter"},
    )

    assert response.status_code == 401


def test_enabled_webhook_remains_public_for_signature_validation(monkeypatch):
    _set_billing_mode(monkeypatch, "enabled")
    monkeypatch.setenv("ZIDD_ALLOW_TEST_AUTH", "0")
    monkeypatch.setattr(
        billing_routes.razorpay_client,
        "verify_webhook_signature",
        lambda *_args, **_kwargs: False,
    )

    response = TestClient(app).post(
        "/billing/razorpay/webhook",
        content=b"{}",
        headers={"X-Razorpay-Signature": "invalid"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid signature"}


def test_enabled_charge_keeps_idempotent_single_debit(monkeypatch):
    _set_billing_mode(monkeypatch, "enabled")
    store = IdempotentDebitStore()
    decision = GateDecision(
        free=False,
        cost=50,
        scope="attempt",
        ref_id="int_01_elevator_pitch",
        record_unlock=False,
        owned=False,
        reason="attempt_meter",
    )

    first = asyncio.run(
        charge(store, "learner", decision, idempotency_key="session_start:one")
    )
    replay = asyncio.run(
        charge(store, "learner", decision, idempotency_key="session_start:one")
    )

    assert first.allowed is True
    assert replay.allowed is True
    assert store.balance == 50
    assert store.debits == 1
