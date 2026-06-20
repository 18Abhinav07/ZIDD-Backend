#!/usr/bin/env python3
"""Local Razorpay webhook simulator (dev only).

Razorpay cannot POST to 127.0.0.1, so for a localhost run there is no real
webhook delivery. This script stands in for Razorpay: it builds the exact
`payment.captured` payload the backend route expects, signs the *exact bytes*
it will send with the shared ``RAZORPAY_WEBHOOK_SECRET`` (reproducing
``app/billing/razorpay_client.verify_webhook_signature``'s formula —
``hmac.new(secret, body, sha256).hexdigest()``), and POSTs those identical
bytes to ``/billing/razorpay/webhook`` with the ``X-Razorpay-Signature`` header.

The secret comes from ``get_settings().razorpay_webhook_secret`` — the *same*
source the backend verifies against — so a match is guaranteed when both read
the same ``.env``. The amount is auto-resolved from the local store via the
real ``get_purchase`` accessor (no schema coupling), so the happy path needs
only an ``order_id``.

Run it from the Zidd-Backend directory (so ``app`` imports and the relative
``.zidd_local.db`` resolves to the same file uvicorn writes):

    ./.venv/bin/python scripts/dev_webhook.py <order_id>

Negative tests:
    ./.venv/bin/python scripts/dev_webhook.py <order_id> --bad-sig        # -> 400
    ./.venv/bin/python scripts/dev_webhook.py <order_id> --wrong-amount   # -> 200 amount_mismatch
    ./.venv/bin/python scripts/dev_webhook.py whatever   --unknown-order  # -> 200 unknown_order

Exit code is 0 only when the observed (HTTP status, body "status") matches what
the flags predict — so the M1 gate can assert on it.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import os
import sys

# Make `app` importable regardless of the caller's CWD (script lives in
# Zidd-Backend/scripts/). The relative SQLite path still resolves against CWD,
# so run from Zidd-Backend/ for the store lookup to find uvicorn's DB.
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

import httpx  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.storage import get_storage  # noqa: E402

DEFAULT_URL = "http://127.0.0.1:8000/billing/razorpay/webhook"
DEFAULT_AMOUNT = 100  # paise; only used when the order isn't in the store
UNKNOWN_ORDER_ID = "order_UNKNOWN_SIM_doesnotexist"


def _sign(body: bytes, secret: str) -> str:
    """Reproduce the backend's verify formula exactly (razorpay_client.py)."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def _lookup_purchase(order_id: str) -> dict | None:
    """Best-effort read of the recorded purchase via the real store accessor.

    Returns None (not raising) if the store/table/row is absent, so the script
    still runs against an un-bootstrapped DB or a wrong CWD — it just falls back
    to the default amount and prints a hint.
    """
    try:
        store = get_storage()
        return await store.get_purchase(order_id)
    except Exception as exc:  # noqa: BLE001 — dev tool, degrade loudly not fatally
        print(f"  ! store lookup failed ({exc!r}); falling back to default amount")
        return None


async def _balance(user_id: str) -> int | None:
    try:
        return await get_storage().get_credits(user_id)
    except Exception:  # noqa: BLE001
        return None


def _expected(
    args: argparse.Namespace, captured: bool, order_present: bool
) -> tuple[int, str | None]:
    """(expected_http_status, expected_body_status) given the flags + store state.

    Mirrors the webhook route's check precedence exactly (billing_routes.py):
    bad signature (400) > non-captured event (ignored) > order not in store
    (unknown_order) > amount mismatch (amount_mismatch) > grant (ok). The order
    matters: the route resolves the purchase BEFORE comparing the amount, so an
    order that isn't in the local store returns unknown_order even under
    --wrong-amount (and the happy path with an absent order is unknown_order,
    not ok).
    """
    if args.bad_sig:
        return 400, None
    if args.unknown_order:
        return 200, "unknown_order"
    if not captured:
        return 200, "ignored"
    if not order_present:
        return 200, "unknown_order"
    if args.wrong_amount:
        return 200, "amount_mismatch"
    return 200, "ok"


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sign + POST a fake Razorpay payment.captured webhook to the local backend.",
    )
    parser.add_argument("order_id", help="Razorpay order id from POST /billing/purchase/order")
    parser.add_argument("--amount", type=int, default=None,
                        help="Override amount in paise (default: resolved from the local store)")
    parser.add_argument("--status", default="captured",
                        help="Payment entity status (default: captured)")
    parser.add_argument("--event", default="payment.captured",
                        help="Webhook event name (default: payment.captured)")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Webhook URL (default: {DEFAULT_URL})")
    parser.add_argument("--bad-sig", action="store_true",
                        help="Corrupt the signature -> expect HTTP 400")
    parser.add_argument("--wrong-amount", action="store_true",
                        help="Send amount != recorded -> expect 200 amount_mismatch")
    parser.add_argument("--unknown-order", action="store_true",
                        help="Use an order id that was never recorded -> expect 200 unknown_order")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print body + signature, do not POST")
    args = parser.parse_args()

    settings = get_settings()
    secret = settings.razorpay_webhook_secret
    if not secret:
        print("FATAL: RAZORPAY_WEBHOOK_SECRET is empty in .env — cannot sign.", file=sys.stderr)
        return 2

    # ---- resolve order_id + amount -----------------------------------------
    order_id = UNKNOWN_ORDER_ID if args.unknown_order else args.order_id

    purchase = None
    if not args.unknown_order:
        purchase = await _lookup_purchase(order_id)

    if args.amount is not None:
        base_amount = args.amount
    elif purchase is not None:
        base_amount = int(purchase["amount_paise"])
    else:
        base_amount = DEFAULT_AMOUNT
        if not args.unknown_order:
            print(f"  ! order {order_id!r} not found in local store — webhook will likely "
                  f"return unknown_order. Run from Zidd-Backend/, or pass --amount.")

    send_amount = base_amount + 100 if args.wrong_amount else base_amount
    captured = (args.event == "payment.captured" and args.status == "captured")

    # ---- build payload, serialize ONCE, sign those exact bytes -------------
    payload = {
        "event": args.event,
        "payload": {"payment": {"entity": {
            "order_id": order_id,
            "amount": send_amount,
            "status": args.status,
        }}},
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = _sign(body, secret)
    if args.bad_sig:
        # Flip the last hex char — guaranteed-invalid, same length/format.
        sig = sig[:-1] + ("0" if sig[-1] != "0" else "1")

    print(f"  order_id : {order_id}")
    print(f"  amount   : {send_amount} paise"
          + (f"  (recorded {purchase['amount_paise']})" if purchase else ""))
    print(f"  event    : {args.event}  status={args.status}")
    print(f"  body     : {body.decode('utf-8')}")
    print(f"  signature: {sig}{'  [CORRUPTED]' if args.bad_sig else ''}")

    if args.dry_run:
        print("  (dry-run — not POSTing)")
        return 0

    # ---- balance before (when the user is known) ---------------------------
    bal_before = await _balance(purchase["user_id"]) if purchase else None

    # ---- POST the EXACT signed bytes ---------------------------------------
    try:
        resp = httpx.post(
            args.url,
            content=body,  # raw bytes — must be byte-identical to what we signed
            headers={
                "X-Razorpay-Signature": sig,
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
    except httpx.ConnectError:
        print(f"FATAL: could not connect to {args.url} — is the backend running "
              f"(uvicorn app.main:app)?", file=sys.stderr)
        return 2

    try:
        body_json = resp.json()
        body_status = body_json.get("status")
    except Exception:  # noqa: BLE001
        body_json = resp.text
        body_status = None

    print(f"  -> HTTP {resp.status_code}  body={body_json}")

    # ---- balance after + grant delta ---------------------------------------
    if purchase and bal_before is not None:
        bal_after = await _balance(purchase["user_id"])
        delta = (bal_after - bal_before) if bal_after is not None else None
        print(f"  balance: {bal_before} -> {bal_after}  (delta {delta:+d})"
              if delta is not None else f"  balance: {bal_before} -> {bal_after}")

    # ---- self-check against expected outcome -------------------------------
    exp_http, exp_status = _expected(args, captured, purchase is not None)
    ok = resp.status_code == exp_http and (exp_status is None or body_status == exp_status)
    verdict = "PASS" if ok else "FAIL"
    want = f"HTTP {exp_http}" + (f" + status={exp_status}" if exp_status else "")
    print(f"  [{verdict}] expected {want}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
