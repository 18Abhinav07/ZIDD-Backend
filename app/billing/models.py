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
