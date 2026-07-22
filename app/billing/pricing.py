"""Monetization catalog — credit packs and gate costs.

Single source of pricing truth. The gate (gate.py) and the Razorpay order route
both read constants from here, so a price change is one edit. Prices are in
paise (₹1 = 100 paise) to match Razorpay's integer amount unit and avoid float
drift. Welcome-credit amount lives in config.Settings.welcome_credits, not here.
"""
from app.billing.models import PackInfo

# ---------- credit packs (purchasable with real money) ----------
PACKS: dict[str, PackInfo] = {
    "starter": PackInfo(id="starter", title="Starter", price_paise=19_900, credits=100),
    "value": PackInfo(id="value", title="Value", price_paise=49_900, credits=300),
    "pro": PackInfo(id="pro", title="Pro", price_paise=99_900, credits=750),
}


def pack_list() -> list[PackInfo]:
    """Packs in display order (cheapest first; Pro is the price anchor)."""
    return [PACKS["starter"], PACKS["value"], PACKS["pro"]]


def get_pack(pack_id: str) -> PackInfo | None:
    return PACKS.get(pack_id)


# ---------- gate costs (credit prices) ----------
# Journey tariff. A durable unlock owns the learning content permanently; only
# a fresh assessment simulation consumes a new attempt charge.
SCHOOL_CHAPTER_COST = 2
CAREER_SKILL_COST = 4
CAREER_TEST_ATTEMPT_COST = 12

# Legacy tariff remains here only to preserve existing deployments while they
# transition to BILLING_POLICY=journey.
COMM_MODULE_COST = 40
INT_ATTEMPT_COST = 50
GD_ATTEMPT_COST = 50
FREE_ATTEMPTS = 2
