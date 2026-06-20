#!/usr/bin/env python3
"""Seed a profile + 'created' purchase straight into the local store (dev only).

This is the isolated-test companion to ``dev_webhook.py``. The real money loop
records a purchase via ``POST /billing/purchase/order`` (which calls the Razorpay
SDK to mint an ``order_id``); that path needs the SDK installed and a valid JWT.
For verifying the *webhook half* on its own — HMAC verify, amount reconcile,
single-grant latch — we don't need a real Razorpay order at all: we only need a
profile row (so ``grant_credits`` finds it instead of raising ``KeyError``) and a
``purchases`` row with a known ``order_id`` + ``amount_paise``.

Run from the Zidd-Backend directory so the relative ``.zidd_local.db`` resolves
to the same file uvicorn writes:

    ./.venv/bin/python scripts/dev_seed_purchase.py
    ./.venv/bin/python scripts/dev_seed_purchase.py --order-id order_SIM_x --pack-id value

Prints the order_id + the user's current balance so you can hand the order_id to
``dev_webhook.py`` and watch the grant delta.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from app.billing import pricing  # noqa: E402
from app.storage import get_storage  # noqa: E402

DEFAULT_ORDER_ID = "order_SIM_m1_001"
DEFAULT_USER_ID = "sim_user_m1"
DEFAULT_PACK_ID = "starter"


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed a profile + 'created' purchase into the local store for webhook testing.",
    )
    parser.add_argument("--order-id", default=DEFAULT_ORDER_ID)
    parser.add_argument("--user-id", default=DEFAULT_USER_ID)
    parser.add_argument("--pack-id", default=DEFAULT_PACK_ID,
                        help="Pricing pack id; its credits/price are used unless overridden.")
    parser.add_argument("--credits", type=int, default=None,
                        help="Override credits to grant (default: pack.credits)")
    parser.add_argument("--amount", type=int, default=None,
                        help="Override amount in paise (default: pack.price_paise)")
    parser.add_argument("--status", default="created",
                        help="Purchase status to seed (default: created)")
    args = parser.parse_args()

    pack = pricing.get_pack(args.pack_id)
    if pack is None:
        known = ", ".join(p.id for p in pricing.list_packs()) if hasattr(pricing, "list_packs") else "?"
        print(f"FATAL: unknown pack {args.pack_id!r} (known: {known})", file=sys.stderr)
        return 2

    credits = args.credits if args.credits is not None else pack.credits
    amount = args.amount if args.amount is not None else pack.price_paise

    store = get_storage()
    await store.ensure_profile(args.user_id, name="sim-m1")
    await store.record_purchase(
        args.order_id, args.user_id, pack.id, credits, amount, status=args.status,
    )
    # Read back through the real accessors so we print exactly what the webhook
    # handler will see (record_purchase is ON CONFLICT DO NOTHING — a re-seed of
    # an existing order_id is a no-op, which we surface rather than hide).
    purchase = await store.get_purchase(args.order_id)
    balance = await store.get_credits(args.user_id)

    print(f"  user_id  : {args.user_id}")
    print(f"  order_id : {args.order_id}")
    print(f"  pack     : {pack.id}  credits={purchase['credits']}  amount={purchase['amount_paise']} paise")
    print(f"  status   : {purchase['status']}")
    print(f"  balance  : {balance} credits")
    print()
    print(f"Next: ./.venv/bin/python scripts/dev_webhook.py {args.order_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
