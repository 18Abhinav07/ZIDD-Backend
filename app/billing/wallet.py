"""Pure credit-lot policy used by the durable wallet store.

The database owns balance mutations. This module only makes the deterministic
decisions that must be identical in every caller: expired lots cannot spend,
and credits that will expire are used before non-expiring purchased credit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreditLot:
    lot_id: int
    source: str
    remaining_credits: int
    expires_at: datetime | None


def _is_active(lot: CreditLot, *, now: datetime) -> bool:
    return lot.remaining_credits > 0 and (
        lot.expires_at is None or lot.expires_at > now
    )


def _spend_order(lot: CreditLot) -> tuple[int, datetime, int]:
    # Expiring grants are deliberately spent first. This protects a learner's
    # paid balance when their beta or promo grant is about to lapse.
    return (
        0 if lot.expires_at is not None else 1,
        lot.expires_at or datetime.max.replace(tzinfo=None),
        lot.lot_id,
    )


def allocate_spend(
    lots: list[CreditLot],
    *,
    amount: int,
    now: datetime,
) -> list[tuple[int, int]] | None:
    """Return a deterministic `(lot_id, debit)` allocation or `None`.

    A caller must apply the returned allocation inside the same transaction
    that records the debit. The function has no side effects, making it safe
    to exercise independently from Postgres locking behavior.
    """
    if amount < 0:
        raise ValueError("credit_amount_must_not_be_negative")
    if amount == 0:
        return []
    available = sorted(
        (lot for lot in lots if _is_active(lot, now=now)),
        key=_spend_order,
    )
    if sum(lot.remaining_credits for lot in available) < amount:
        return None
    remaining = amount
    allocations: list[tuple[int, int]] = []
    for lot in available:
        debit = min(remaining, lot.remaining_credits)
        if debit:
            allocations.append((lot.lot_id, debit))
            remaining -= debit
        if remaining == 0:
            break
    return allocations


def recovery_credit_amount(
    *,
    amount: int,
    allocation_total: int,
    restored_amount: int,
) -> int:
    """Return credit that must be recovered outside original expired lots.

    A failed attempt must be net-zero for the learner. If its original beta
    lot has expired by the time compensation runs, restoring that same lot
    would leave the learner with no spendable credit. The caller grants the
    returned remainder as a non-expiring recovery lot instead.
    """
    if amount < 0 or allocation_total not in (0, amount):
        raise ValueError("invalid_wallet_refund_allocation_total")
    if restored_amount < 0 or restored_amount > amount:
        raise ValueError("invalid_wallet_refund_restored_amount")
    return amount - restored_amount


def wallet_summary(lots: list[CreditLot], *, now: datetime) -> dict:
    """Build the public wallet summary from currently spendable lots."""
    active = [lot for lot in lots if _is_active(lot, now=now)]
    beta_lots = [lot for lot in active if lot.source == "beta_grant"]
    paid_sources = {"paid_purchase", "legacy_migrated"}
    return {
        "credits": sum(lot.remaining_credits for lot in active),
        "beta_credits": sum(lot.remaining_credits for lot in beta_lots),
        "paid_credits": sum(
            lot.remaining_credits for lot in active if lot.source in paid_sources
        ),
        "promo_credits": sum(
            lot.remaining_credits
            for lot in active
            if lot.source not in paid_sources | {"beta_grant"}
        ),
        "beta_expires_at": min(
            (lot.expires_at for lot in beta_lots if lot.expires_at is not None),
            default=None,
        ),
    }
