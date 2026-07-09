"""Billing API — wallet balance, pack catalog, session quotes, unlock history,
and the Razorpay order + webhook surface. Enforcement decisions come from
app.billing.gate; these routes read state and create/confirm purchases.
"""
import json
import logging

from fastapi import APIRouter, Body, HTTPException, Request

from app.billing import pricing, razorpay_client
from app.billing.gate import resolve_gate
from app.billing.models import (
    BalanceResponse,
    OrderRequest,
    OrderResponse,
    PackListResponse,
    QuoteResponse,
    UnlockInfo,
    UnlockListResponse,
)
from app.config import get_settings
from app.content import registry
from app.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

_LOCAL_DEV_HOSTS = {"localhost", "127.0.0.1", "::1", "testserver"}


def _uid(request: Request) -> str:
    return getattr(request.state, "user_id", None) or ""


def _is_local_dev_grant_enabled(request: Request) -> bool:
    settings = get_settings()
    if settings.app_env.lower() not in {"dev", "test", "local"}:
        return False
    if not settings.enable_dev_credit_grant:
        return False
    host = (request.url.hostname or "").lower()
    origin = (request.headers.get("origin") or "").strip()
    if host not in _LOCAL_DEV_HOSTS:
        return False
    if origin:
        try:
            origin_host = origin.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()
        except IndexError:
            return False
        if origin_host not in _LOCAL_DEV_HOSTS:
            return False
    return True


@router.get("/balance", response_model=BalanceResponse)
async def balance(request: Request) -> BalanceResponse:
    user_id = _uid(request)
    store = get_storage()
    # Best-effort name read so the dashboard can greet by the profile name (the
    # same one the coach uses); a missing/failed profile just leaves it blank.
    prof = None
    try:
        prof = await store.get_profile(user_id)
        name = (prof or {}).get("name", "") or ""
    except Exception:
        name = ""

    prefs = (prof or {}).get("preferences") or {}
    active_module = prefs.get("active_module") if isinstance(prefs, dict) else None
    try:
        if not active_module and hasattr(store, "get_last_active_node"):
            last_node = await store.get_last_active_node(user_id)
            if last_node:
                active_module = registry.module_of(last_node)
    except Exception as e:
        logger.warning("Failed to resolve active module for %s: %s", user_id, e)

    return BalanceResponse(
        user_id=user_id,
        credits=await store.get_credits(user_id),
        demo_unlimited=await store.is_demo(user_id),
        name=name,
        active_module=active_module,
    )


@router.post("/dev/grant")
async def dev_grant(request: Request, amount: int = 500) -> dict:
    """DEV-ONLY top-up so credits can be tested locally without Razorpay.

    Razorpay needs live/test keys plus a publicly reachable webhook to grant
    credits, which is impossible on localhost, so the wallet could never be
    funded in dev. This grants the authenticated user credits directly. Hard
    404 outside non-prod so it can never exist on a real deployment.
    """
    if not _is_local_dev_grant_enabled(request):
        raise HTTPException(status_code=404, detail="Not found")
    user_id = _uid(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    amount = max(1, min(amount, 100_000))  # sane bounds
    store = get_storage()
    new_balance = await store.grant_credits(user_id, amount, "dev_grant")
    return {"user_id": user_id, "granted": amount, "credits": new_balance}


@router.get("/packs", response_model=PackListResponse)
async def packs() -> PackListResponse:
    return PackListResponse(packs=pricing.pack_list())


@router.get("/quote", response_model=QuoteResponse)
async def quote(node_id: str, request: Request) -> QuoteResponse:
    user_id = _uid(request)
    store = get_storage()
    try:
        d = await resolve_gate(store, user_id, node_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown competency node") from e
    return QuoteResponse(
        node_id=node_id,
        free=d.free,
        cost=d.cost,
        scope=d.scope,
        ref_id=d.ref_id,
        owned=d.owned,
        reason=d.reason,
    )


@router.get("/unlocks", response_model=UnlockListResponse)
async def unlocks(request: Request) -> UnlockListResponse:
    user_id = _uid(request)
    store = get_storage()
    rows = await store.list_unlocks(user_id)
    return UnlockListResponse(
        unlocks=[
            UnlockInfo(
                scope=r["scope"],
                ref_id=r["ref_id"],
                credits_spent=r["credits_spent"],
            )
            for r in rows
        ]
    )


@router.post("/purchase/order", response_model=OrderResponse)
async def create_purchase_order(req: OrderRequest, request: Request) -> OrderResponse:
    user_id = _uid(request)
    pack = pricing.get_pack(req.pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Unknown pack")
    try:
        order = razorpay_client.create_order(pack.price_paise, receipt=f"{user_id}:{pack.id}")
    except Exception as e:
        # Razorpay 5xx / timeout / network error: surface a clean 502 instead of
        # a raw unhandled 500, and record NO purchase row (there is no order to
        # reconcile against — the next attempt creates a fresh one).
        logger.error(
            "razorpay create_order failed for user=%s pack=%s: %r", user_id, pack.id, e
        )
        raise HTTPException(
            status_code=502, detail="Payment gateway unavailable. Please try again."
        ) from e
    order_id = order["id"]
    store = get_storage()
    await store.record_purchase(
        order_id, user_id, pack.id, pack.credits, pack.price_paise, status="created"
    )
    return OrderResponse(
        order_id=order_id,
        pack_id=pack.id,
        amount_paise=pack.price_paise,
        credits=pack.credits,
        razorpay_key_id=get_settings().razorpay_key_id,
    )


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request) -> dict:
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not razorpay_client.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        # Signature verified but the body is not valid JSON — a real anomaly
        # (never sent by Razorpay normally). Return a clean 400 instead of an
        # unhandled 500 stack trace, and surface it for reconciliation.
        logger.warning("razorpay webhook: signature valid but body is not valid JSON")
        raise HTTPException(status_code=400, detail="Malformed webhook payload")
    if not isinstance(payload, dict):
        logger.warning("razorpay webhook: signature valid but JSON body is not an object")
        raise HTTPException(status_code=400, detail="Malformed webhook payload")
    # Safely navigate payload.payment.entity. A signature-valid body whose nested
    # objects are the wrong type (Razorpay schema drift, a malformed-but-signed
    # event, or a signed replay) must NOT raise an unhandled 500 — Razorpay retries
    # 5xx forever. Treat a structural anomaly like the missing-order_id case below:
    # 200-ack so the retries stop, but never grant.
    inner = payload.get("payload")
    payment = inner.get("payment") if isinstance(inner, dict) else None
    entity = payment.get("entity") if isinstance(payment, dict) else None
    if not isinstance(entity, dict):
        logger.warning("razorpay webhook: signature valid but payload.payment.entity is not an object")
        return {"status": "ignored"}
    order_id = entity.get("order_id", "")
    if not order_id:
        return {"status": "ignored"}
    # Razorpay posts payment.failed / payment.authorized to the SAME endpoint;
    # only a successful capture should grant credits. Acknowledge (200) anything
    # else so Razorpay stops retrying, but never grant.
    event = payload.get("event", "")
    if event != "payment.captured" or entity.get("status", "") != "captured":
        return {"status": "ignored"}
    store = get_storage()
    purchase = await store.get_purchase(order_id)
    if purchase is None:
        # A signature-valid captured payment for an order we never recorded is a
        # real anomaly (lost order write, cross-environment event, or replay).
        # Keep the 200-ack so Razorpay stops retrying, but never let it vanish
        # silently — surface it for reconciliation.
        logger.warning("razorpay webhook: captured payment for unknown order_id=%s", order_id)
        return {"status": "unknown_order"}
    # Reconcile the captured amount against what we quoted; a mismatch means a
    # tampered/wrong event, so refuse to grant.
    try:
        captured_amount = int(entity.get("amount", -1))
    except (ValueError, TypeError):
        # A non-numeric / null amount on a signed event is an anomaly, not a
        # grantable capture. Treat it as a mismatch (never grant) rather than
        # letting int() raise an unhandled 500 that Razorpay retries forever.
        captured_amount = -1
    if captured_amount != int(purchase["amount_paise"]):
        logger.warning(
            "razorpay webhook: amount mismatch for order_id=%s (captured=%s expected=%s)",
            order_id,
            entity.get("amount"),
            purchase["amount_paise"],
        )
        return {"status": "amount_mismatch"}
    # Atomic latch + grant: ONE transaction folds the 'paid' transition and the
    # credit grant, so a crash between them can never leave the order paid with
    # credits never granted. Returns True only on the first captured webhook
    # (granted once); False on a retry (already paid → no double grant).
    try:
        await store.mark_paid_and_grant(
            order_id,
            purchase["user_id"],
            purchase["credits"],
            f"purchase:{purchase['pack_id']}",
        )
    except KeyError:
        # The order is recorded but its buyer profile is gone (should be
        # impossible — the order was created under that user). The latch was
        # rolled back, so the order stays unpaid for reconciliation. Ack 200 so
        # Razorpay stops retrying a case retries can't fix, but log loudly.
        logger.error(
            "razorpay webhook: paid order_id=%s but buyer profile %s missing; "
            "grant deferred for reconciliation",
            order_id,
            purchase["user_id"],
        )
        return {"status": "grant_failed"}
    return {"status": "ok"}


@router.post("/razorpay/verify")
async def razorpay_verify(request: Request, body: dict = Body(...)) -> dict:
    """Grant credits on a verified Checkout success, without the webhook.

    Razorpay's webhook can't reach localhost, so a TEST payment would otherwise
    never fund the wallet. The Checkout success handler posts here with the
    payment id/order id/signature; we verify the signature (HMAC over
    'order_id|payment_id' with the API secret), confirm the order belongs to the
    authenticated buyer, reconcile the amount, then grant via the SAME idempotent
    latch the webhook uses — so a later webhook for the same order never
    double-grants. Also a useful safety net in prod when a webhook is delayed."""
    user_id = _uid(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    order_id = body.get("razorpay_order_id") or body.get("order_id") or ""
    payment_id = body.get("razorpay_payment_id") or ""
    signature = body.get("razorpay_signature") or ""
    if not razorpay_client.verify_payment_signature(order_id, payment_id, signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    store = get_storage()
    purchase = await store.get_purchase(order_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="Unknown order")
    if purchase["user_id"] != user_id:
        # Never let one learner's verify grant against another's order.
        raise HTTPException(status_code=403, detail="Not your order")
    try:
        granted = await store.mark_paid_and_grant(
            order_id,
            purchase["user_id"],
            purchase["credits"],
            f"purchase:{purchase['pack_id']}",
        )
    except KeyError as e:
        raise HTTPException(status_code=409, detail="Buyer profile missing") from e
    return {"granted": bool(granted), "credits": await store.get_credits(user_id)}
