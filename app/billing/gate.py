"""Credit/unlock gate — the ONLY place that decides whether starting a session
is free or must be paid. The brain (graph/services) stays credit-blind; the
/session/start route guard consults this BEFORE svc.start_session.

Decision order (judges hit zero paywalls):
  1. demo_unlimited  -> free            (XPRIZE judge bypass, checked FIRST)
  2. school_english  -> free            (teaching is the funnel)
  3. communication   -> owned? free : first-node free-taste : 40cr ACCESS unlock
  4. interview / gd  -> first 2 attempts free, then 50cr ATTEMPT meter
"""
from dataclasses import dataclass

from app.billing import pricing
from app.content.registry import (
    COMM_ID,
    GD_ID,
    INT_ID,
    SCHOOL_ID,
    get_module,
    module_of,
)


@dataclass(frozen=True)
class GateDecision:
    free: bool
    cost: int
    scope: str           # "" | "feature" | "attempt"
    ref_id: str          # module id (feature) or node id (attempt)
    record_unlock: bool  # True -> persist a content_unlocks row after charging
    owned: bool          # already unlocked (ACCESS) -> free this time
    reason: str          # machine tag surfaced to the quote/UI


async def resolve_gate(store, user_id: str, node_id: str) -> GateDecision:
    """Decide the price to START a session on `node_id`.

    Raises KeyError if the node id is unknown (the route maps that to 404).
    """
    # 1. Judge/demo bypass — checked FIRST, before any module logic.
    if await store.is_demo(user_id):
        return GateDecision(True, 0, "", "", False, False, "demo_unlimited")

    module = module_of(node_id)  # KeyError -> unknown node -> 404 at the route

    # 2. School English: teaching is a free funnel.
    if module == SCHOOL_ID:
        return GateDecision(True, 0, "", "", False, False, "free_teaching")

    # 3. Communication: ACCESS archetype — unlock lasting value once.
    if module == COMM_ID:
        if await store.has_unlock(user_id, "feature", COMM_ID):
            return GateDecision(True, 0, "feature", COMM_ID, False, True, "owned")
        if node_id == get_module(COMM_ID).order[0]:
            return GateDecision(True, 0, "feature", COMM_ID, False, False, "free_taste")
        return GateDecision(
            False, pricing.COMM_MODULE_COST, "feature", COMM_ID, True, False, "access_unlock"
        )

    # 4. Interview / Group Discussion: ATTEMPT archetype — meter fresh compute.
    if module in (INT_ID, GD_ID):
        used = await store.count_attempts(user_id, module)
        if used < pricing.FREE_ATTEMPTS:
            return GateDecision(True, 0, "attempt", node_id, False, False, "free_attempt")
        cost = pricing.INT_ATTEMPT_COST if module == INT_ID else pricing.GD_ATTEMPT_COST
        return GateDecision(False, cost, "attempt", node_id, False, False, "attempt_meter")

    # Unknown module: fail OPEN to free so a future registry addition never
    # hard-walls a learner before its pricing is defined.
    return GateDecision(True, 0, "", "", False, False, "free_unmetered")


async def charge(store, user_id: str, decision: GateDecision) -> bool:
    """Deduct credits for a non-free decision and persist an ACCESS unlock.

    Returns True on success. Both store methods honor demo_unlimited (return True
    without charging) and return False when the balance is insufficient.

    ACCESS unlocks (record_unlock=True) route through the atomic
    charge_and_unlock: the credit debit and the content_unlocks insert land in
    ONE transaction, so a crash between them can never leave the learner having
    paid without the unlock recorded. ATTEMPT meters (record_unlock=False) are a
    pure debit — already atomic — so they stay on deduct_credits.
    """
    if decision.record_unlock:
        return await store.charge_and_unlock(
            user_id, decision.cost, decision.reason, decision.scope, decision.ref_id
        )
    return await store.deduct_credits(user_id, decision.cost, decision.reason)
