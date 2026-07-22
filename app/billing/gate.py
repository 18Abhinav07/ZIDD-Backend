"""Credit/unlock gate — the ONLY place that decides whether starting a session
is free or must be paid. The brain (graph/services) stays credit-blind; the
/session/start route guard consults this BEFORE svc.start_session.

Decision order (judges hit zero paywalls):
  0. billing disabled -> free            (free beta, no credit storage access)
  1. demo_unlimited   -> free            (XPRIZE judge bypass, checked FIRST)
  2. school_english   -> free            (teaching is the funnel)
  3. communication    -> owned? free : first-node free-taste : 40cr ACCESS unlock
  4. interview / gd   -> first 2 attempts free, then 50cr ATTEMPT meter
"""
from dataclasses import dataclass

from app.billing import pricing
from app.config import get_settings
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


@dataclass(frozen=True)
class ChargeOutcome:
    allowed: bool
    compensatable: bool


async def resolve_gate(
    store,
    user_id: str,
    node_id: str,
    *,
    test_mode: bool = False,
) -> GateDecision:
    """Decide the price to START a session on `node_id`.

    Raises KeyError if the node id is unknown (the route maps that to 404).
    """
    if get_settings().billing_mode == "disabled":
        module_of(node_id)  # Preserve the unknown-node contract without storage.
        return GateDecision(True, 0, "", "", False, False, "billing_disabled")

    # 1. Judge/demo bypass — checked FIRST, before any module logic.
    if await store.is_demo(user_id):
        return GateDecision(True, 0, "", "", False, False, "demo_unlimited")

    module = module_of(node_id)  # KeyError -> unknown node -> 404 at the route

    if get_settings().billing_policy == "journey":
        # Canonical School has a dedicated route gate below. Keep the retired
        # legacy School module free so no old endpoint is accidentally turned
        # into a charge path during migration.
        if module == SCHOOL_ID:
            return GateDecision(True, 0, "", "", False, False, "legacy_school_retired")
        if module == COMM_ID:
            scope = "career_communication_module"
            if await store.has_unlock(user_id, scope, COMM_ID):
                return GateDecision(True, 0, scope, COMM_ID, False, True, "owned")
            return GateDecision(
                False,
                pricing.CAREER_SKILL_COST,
                scope,
                COMM_ID,
                True,
                False,
                "career_communication_unlock",
            )
        if module in (INT_ID, GD_ID):
            if test_mode:
                return GateDecision(
                    False,
                    pricing.CAREER_TEST_ATTEMPT_COST,
                    "career_test_attempt",
                    node_id,
                    False,
                    False,
                    "career_test_attempt",
                )
            scope = "career_prep_skill"
            if await store.has_unlock(user_id, scope, node_id):
                return GateDecision(True, 0, scope, node_id, False, True, "owned")
            return GateDecision(
                False,
                pricing.CAREER_SKILL_COST,
                scope,
                node_id,
                True,
                False,
                "career_prep_skill_unlock",
            )
        return GateDecision(True, 0, "", "", False, False, "free_unmetered")

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


async def resolve_school_chapter_gate(
    store,
    user_id: str,
    *,
    subject_id: str,
    class_no: int,
    chapter_id: str,
) -> GateDecision:
    """Price a canonical School chapter after the route validates access.

    The stable entitlement reference is content identity, never a generated
    session or a client id. A retry, reload, masterclass, or future session for
    that chapter therefore cannot debit the learner a second time.
    """
    if get_settings().billing_mode == "disabled":
        return GateDecision(True, 0, "", "", False, False, "billing_disabled")
    if await store.is_demo(user_id):
        return GateDecision(True, 0, "", "", False, False, "demo_unlimited")
    if get_settings().billing_policy != "journey":
        return GateDecision(True, 0, "", "", False, False, "free_teaching")
    ref_id = f"{subject_id}:class_{int(class_no)}:{chapter_id}"
    scope = "school_chapter"
    if await store.has_unlock(user_id, scope, ref_id):
        return GateDecision(True, 0, scope, ref_id, False, True, "owned")
    return GateDecision(
        False,
        pricing.SCHOOL_CHAPTER_COST,
        scope,
        ref_id,
        True,
        False,
        "school_chapter_unlock",
    )


async def charge(
    store,
    user_id: str,
    decision: GateDecision,
    idempotency_key: str | None = None,
) -> ChargeOutcome:
    """Deduct credits for a non-free decision and persist an ACCESS unlock.

    `allowed` permits the start. `compensatable` means this request owns (or is
    reclaiming) a debit that may be reversed if a metered attempt cannot start.

    ACCESS unlocks (record_unlock=True) route through the atomic
    charge_and_unlock: the credit debit and the content_unlocks insert land in
    ONE transaction, so a crash between them can never leave the learner having
    paid without the unlock recorded. ATTEMPT meters (record_unlock=False) are a
    pure debit — already atomic — so they stay on deduct_credits.
    """
    if get_settings().billing_mode == "disabled":
        return ChargeOutcome(True, False)

    if decision.record_unlock:
        allowed, charged = await store.charge_and_unlock(
            user_id, decision.cost, decision.reason, decision.scope, decision.ref_id
        )
        return ChargeOutcome(bool(allowed), bool(charged))
    if idempotency_key:
        if not hasattr(store, "deduct_credits_once"):
            raise RuntimeError("storage_missing_idempotent_credit_debit")
        allowed = await store.deduct_credits_once(
            user_id,
            decision.cost,
            decision.reason,
            idempotency_key,
        )
        return ChargeOutcome(bool(allowed), bool(allowed))
    allowed = await store.deduct_credits(user_id, decision.cost, decision.reason)
    return ChargeOutcome(bool(allowed), bool(allowed))
