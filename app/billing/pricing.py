"""Monetization catalog — credit packs and gate costs.

Single source of pricing truth. The gate (gate.py) and the Razorpay order route
both read constants from here, so a price change is one edit. Prices are in
paise (₹1 = 100 paise) to match Razorpay's integer amount unit and avoid float
drift. Welcome-credit amount lives in config.Settings.welcome_credits, not here.
"""
from app.billing.models import PackInfo

# ---------- credit packs (purchasable with real money) ----------
PACKS: dict[str, PackInfo] = {
    "starter": PackInfo(id="starter", title="Starter", price_paise=9900, credits=100),
    "value": PackInfo(id="value", title="Value", price_paise=24900, credits=280),
    "pro": PackInfo(id="pro", title="Pro", price_paise=49900, credits=625),
}


def pack_list() -> list[PackInfo]:
    """Packs in display order (cheapest first; Pro is the price anchor)."""
    return [PACKS["starter"], PACKS["value"], PACKS["pro"]]


def get_pack(pack_id: str) -> PackInfo | None:
    return PACKS.get(pack_id)


# ---------- gate costs (credit prices) ----------
COMM_MODULE_COST = 40   # a la carte: unlock one Communication module (ACCESS)
INT_ATTEMPT_COST = 50   # per Interview attempt, text (ATTEMPT)
GD_ATTEMPT_COST = 50    # per Group-Discussion session, text (ATTEMPT)
FREE_ATTEMPTS = 2       # free Interview/GD attempts before metering starts
