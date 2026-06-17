"""Billing API — wallet balance, pack catalog, session quotes, unlock history,
and the Razorpay order + webhook surface. Enforcement decisions come from
app.billing.gate; these routes read state and create/confirm purchases.
"""
import json

from fastapi import APIRouter, HTTPException, Request

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
from app.storage import get_storage

router = APIRouter(prefix="/billing", tags=["billing"])


def _uid(request: Request) -> str:
    return getattr(request.state, "user_id", None) or ""


@router.get("/balance", response_model=BalanceResponse)
async def balance(request: Request) -> BalanceResponse:
    user_id = _uid(request)
    store = get_storage()
    return BalanceResponse(
        user_id=user_id,
        credits=await store.get_credits(user_id),
        demo_unlimited=await store.is_demo(user_id),
    )


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
    order = razorpay_client.create_order(pack.price_paise, receipt=f"{user_id}:{pack.id}")
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
    payload = json.loads(body)
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = entity.get("order_id", "")
    if not order_id:
        return {"status": "ignored"}
    store = get_storage()
    purchase = await store.get_purchase(order_id)
    if purchase is None:
        return {"status": "unknown_order"}
    # mark_purchase_paid is the idempotency latch: True only on the transition,
    # so credits grant exactly once even if Razorpay retries the webhook.
    if await store.mark_purchase_paid(order_id):
        await store.grant_credits(
            purchase["user_id"], purchase["credits"], f"purchase:{purchase['pack_id']}"
        )
    return {"status": "ok"}
