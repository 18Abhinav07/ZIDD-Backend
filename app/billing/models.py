"""Pydantic request/response models for the billing API surface."""
from pydantic import BaseModel


class PackInfo(BaseModel):
    id: str
    title: str
    price_paise: int
    credits: int


class PackListResponse(BaseModel):
    packs: list[PackInfo]


class BalanceResponse(BaseModel):
    user_id: str
    credits: int
    demo_unlimited: bool
    # The learner's display name (from their profile), so a surface that already
    # fetches the balance can greet them by the SAME name the coach uses, instead
    # of falling back to the raw user_id. Empty when the profile has no name.
    name: str = ""
    active_module: str | None = None


class QuoteResponse(BaseModel):
    node_id: str
    free: bool
    cost: int
    scope: str
    ref_id: str
    owned: bool
    reason: str


class UnlockInfo(BaseModel):
    scope: str
    ref_id: str
    credits_spent: int


class UnlockListResponse(BaseModel):
    unlocks: list[UnlockInfo]


class OrderRequest(BaseModel):
    pack_id: str


class OrderResponse(BaseModel):
    order_id: str
    pack_id: str
    amount_paise: int
    credits: int
    razorpay_key_id: str
