#!/usr/bin/env python3
"""M4 — full money-loop E2E driver against a LIVE localhost backend.

Self-asserting. Exit 0 only when every checklist item passes. Uses REAL JWTs
minted via POST /auth/register (the middleware test_token bypass CANNOT fire in
a real uvicorn boot — no PYTEST_CURRENT_TEST in env), so this exercises the
genuine HS256 verify path the deployed app uses.

Run from Zidd-Backend/ with the venv python so the relative .zidd_local.db and
scripts/dev_webhook.py resolve to the same store uvicorn writes:

    ./.venv/bin/python scripts/dev_e2e.py

Covers (plan M4 Verification):
  Block A  Communication ACCESS unlock (whole-track): free taste -> 402
           confirm_required -> 40cr charge -> sibling node now free (owned).
  Block B  Interview ATTEMPT meter: 2 free attempts -> 402 confirm_required ->
           50cr charge -> out-of-credits 402 insufficient_credits w/ packs.
  Block C  Real Razorpay sandbox order -> dev_webhook.py grant -> idempotent
           re-post -> bad-sig/unknown-order/wrong-amount negatives.
"""
from __future__ import annotations

import subprocess
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"
SUFFIX = str(int(time.time()))  # unique per run -> fresh balances, no collisions

# --- assertion bookkeeping -------------------------------------------------
_failures: list[str] = []
_passes = 0


def check(label: str, cond: bool, detail: str = "") -> bool:
    global _passes
    if cond:
        _passes += 1
        print(f"  PASS  {label}")
    else:
        _failures.append(label)
        print(f"  FAIL  {label}   {detail}")
    return cond


def section(name: str) -> None:
    print(f"\n=== {name} ===")


def register(c: httpx.Client, uid: str) -> dict:
    """Register a fresh user, return {'h': auth-header, 'uid': uid}."""
    r = c.post("/auth/register", json={"user_id": uid, "password": "pw12345"})
    if r.status_code != 200:
        raise SystemExit(f"FATAL: register {uid} -> {r.status_code} {r.text[:200]}")
    tok = r.json()["access_token"]
    return {"h": {"Authorization": f"Bearer {tok}"}, "uid": uid}


def balance(c: httpx.Client, h: dict) -> int:
    r = c.get("/billing/balance", headers=h)
    r.raise_for_status()
    return r.json()["credits"]


def start(c: httpx.Client, h: dict, uid: str, node: str, confirm: bool) -> httpx.Response:
    return c.post(
        "/session/start",
        headers=h,
        json={"user_id": uid, "competency_node": node, "confirm": confirm},
        timeout=180.0,
    )


def end(c: httpx.Client, h: dict, session_id: str) -> httpx.Response:
    # END runs a best-effort Ollama summarize; give it room.
    return c.post(f"/session/{session_id}/end", headers=h, timeout=240.0)


# --------------------------------------------------------------------------
def block_a(c: httpx.Client) -> None:
    section("Block A — Communication ACCESS unlock (whole-track)")
    u = register(c, f"e2e_comm_{SUFFIX}")
    h, uid = u["h"], u["uid"]

    check("A1 welcome balance == 50", balance(c, h) == 50, f"got {balance(c, h)}")

    # comm_01 is order[0] -> free taste, no charge.
    r = start(c, h, uid, "comm_01_self_intro", confirm=False)
    check("A2 comm_01 free taste -> 200", r.status_code == 200, f"got {r.status_code} {r.text[:160]}")
    check("A3 free taste did not charge (bal 50)", balance(c, h) == 50, f"got {balance(c, h)}")

    # comm_02 is gated -> 402 confirm_required at cost 40.
    r = start(c, h, uid, "comm_02_describe_routine", confirm=False)
    d = r.json().get("detail", {}) if r.status_code == 402 else {}
    check("A4 comm_02 -> 402 confirm_required", r.status_code == 402 and d.get("error") == "confirm_required",
          f"got {r.status_code} {r.text[:200]}")
    check("A5 confirm_required cost == 40", d.get("cost") == 40, f"got {d.get('cost')}")
    check("A6 confirm_required balance == 50", d.get("balance") == 50, f"got {d.get('balance')}")

    # confirm -> charge 40 -> balance 10.
    r = start(c, h, uid, "comm_02_describe_routine", confirm=True)
    check("A7 comm_02 confirm:true -> 200", r.status_code == 200, f"got {r.status_code} {r.text[:200]}")
    check("A8 balance after 40cr charge == 10", balance(c, h) == 10, f"got {balance(c, h)}")

    # comm_03 -> now FREE (whole-track unlock owns every comm node).
    r = start(c, h, uid, "comm_03_past_event", confirm=False)
    check("A9 comm_03 owned/free -> 200 (no confirm)", r.status_code == 200,
          f"got {r.status_code} {r.text[:200]}")
    check("A10 sibling node did not charge (bal still 10)", balance(c, h) == 10, f"got {balance(c, h)}")


def block_b(c: httpx.Client) -> dict:
    section("Block B — Interview ATTEMPT meter (2 free, then 50cr)")
    u = register(c, f"e2e_int_{SUFFIX}")
    h, uid = u["h"], u["uid"]
    NODE = "int_01_elevator_pitch"

    check("B1 welcome balance == 50", balance(c, h) == 50, f"got {balance(c, h)}")

    # Two free attempts: START+END ticks count_attempts.
    for i in (1, 2):
        r = start(c, h, uid, NODE, confirm=False)
        ok = check(f"B2.{i} free attempt #{i} START -> 200", r.status_code == 200,
                   f"got {r.status_code} {r.text[:160]}")
        if ok:
            sid = r.json()["session_id"]
            er = end(c, h, sid)
            check(f"B3.{i} free attempt #{i} END -> 200", er.status_code == 200,
                  f"got {er.status_code} {er.text[:160]}")
    check("B4 free attempts did not charge (bal 50)", balance(c, h) == 50, f"got {balance(c, h)}")

    # 3rd attempt -> meter trips -> 402 confirm_required cost 50.
    r = start(c, h, uid, NODE, confirm=False)
    d = r.json().get("detail", {}) if r.status_code == 402 else {}
    check("B5 3rd attempt -> 402 confirm_required", r.status_code == 402 and d.get("error") == "confirm_required",
          f"got {r.status_code} {r.text[:200]}")
    check("B6 attempt-meter cost == 50", d.get("cost") == 50, f"got {d.get('cost')}")

    # confirm -> charge 50 -> balance 0. END it to keep the store tidy.
    r = start(c, h, uid, NODE, confirm=True)
    check("B7 3rd attempt confirm:true -> 200", r.status_code == 200, f"got {r.status_code} {r.text[:200]}")
    check("B8 balance after 50cr charge == 0", balance(c, h) == 0, f"got {balance(c, h)}")
    if r.status_code == 200:
        end(c, h, r.json()["session_id"])

    # 4th attempt with confirm -> can't pay -> 402 insufficient_credits + packs.
    r = start(c, h, uid, NODE, confirm=True)
    d = r.json().get("detail", {}) if r.status_code == 402 else {}
    check("B9 4th attempt -> 402 insufficient_credits", r.status_code == 402 and d.get("error") == "insufficient_credits",
          f"got {r.status_code} {r.text[:200]}")
    check("B10 insufficient_credits carries packs[]", isinstance(d.get("packs"), list) and len(d.get("packs", [])) > 0,
          f"got {d.get('packs')}")

    return u  # reuse this balance-0 user for Block C purchase


def webhook(order_id: str, *flags: str) -> int:
    """Run the signed-webhook simulator as a subprocess; return its exit code.

    Self-asserts internally (exit 0 only when the outcome matches the flag's
    prediction). sys.executable is the venv python since we're run with it.
    """
    cmd = [sys.executable, "scripts/dev_webhook.py", order_id, *flags]
    p = subprocess.run(cmd, capture_output=True, text=True)
    tag = " ".join(flags) or "valid"
    print(f"    [dev_webhook {tag}] exit={p.returncode}  {p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ''}")
    if p.returncode != 0:
        print(p.stdout[-400:])
        print(p.stderr[-400:])
    return p.returncode


def block_c(c: httpx.Client, payer: dict) -> None:
    section("Block C — Real Razorpay sandbox order + webhook grant")
    h, uid = payer["h"], payer["uid"]
    check("C1 payer starts at balance 0", balance(c, h) == 0, f"got {balance(c, h)}")

    # Real sandbox order via the SDK.
    r = c.post("/billing/purchase/order", headers=h, json={"pack_id": "starter"})
    check("C2 purchase/order -> 200", r.status_code == 200, f"got {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        return
    body = r.json()
    order_id = body.get("order_id", "")
    check("C3 real sandbox order_id (order_*)", order_id.startswith("order_"), f"got {order_id!r}")
    check("C4 order credits == 100", body.get("credits") == 100, f"got {body.get('credits')}")
    check("C5 razorpay_key_id is test key", str(body.get("razorpay_key_id", "")).startswith("rzp_test_"),
          f"got {body.get('razorpay_key_id')}")

    # Valid capture -> grant exactly once: 0 -> 100.
    bal_before = balance(c, h)
    rc = webhook(order_id)
    check("C6 valid webhook exit 0", rc == 0)
    check("C7 grant applied (+100)", balance(c, h) - bal_before == 100, f"got delta {balance(c, h) - bal_before}")

    # Idempotency: re-post same order -> 200 ok, NO double grant.
    bal_before = balance(c, h)
    rc = webhook(order_id)
    check("C8 re-post webhook exit 0", rc == 0)
    check("C9 idempotent (no double grant, delta 0)", balance(c, h) - bal_before == 0,
          f"got delta {balance(c, h) - bal_before}")

    # Negatives — each flag self-asserts its predicted outcome; balance unchanged.
    bal_before = balance(c, h)
    check("C10 --bad-sig exit 0 (predicts 400)", webhook(order_id, "--bad-sig") == 0)
    check("C11 --unknown-order exit 0 (predicts unknown_order)", webhook(order_id, "--unknown-order") == 0)
    check("C12 --wrong-amount exit 0 (predicts amount_mismatch)", webhook(order_id, "--wrong-amount") == 0)
    check("C13 negatives granted nothing (bal unchanged)", balance(c, h) == bal_before,
          f"got {balance(c, h)} want {bal_before}")


def main() -> int:
    # Liveness gate.
    try:
        with httpx.Client(base_url=BASE, timeout=10.0) as c:
            if c.get("/health").status_code != 200:
                raise SystemExit("FATAL: backend /health != 200 — boot uvicorn from Zidd-Backend/ first")
    except httpx.ConnectError:
        raise SystemExit("FATAL: backend not reachable at 127.0.0.1:8000 — boot uvicorn first")

    with httpx.Client(base_url=BASE, timeout=60.0) as c:
        block_a(c)
        payer = block_b(c)
        block_c(c, payer)

    section("RESULT")
    total = _passes + len(_failures)
    print(f"  {_passes}/{total} checks passed")
    if _failures:
        print("  FAILURES:")
        for f in _failures:
            print(f"    - {f}")
        return 1
    print("  ALL GREEN — M4 money loop verified end-to-end on localhost.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
