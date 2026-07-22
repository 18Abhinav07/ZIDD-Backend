from datetime import datetime, timedelta, timezone

import pytest

from app.billing.wallet import (
    CreditLot,
    allocate_spend,
    recovery_credit_amount,
    wallet_summary,
)


NOW = datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc)


def test_wallet_spends_expiring_beta_credits_before_purchased_credits() -> None:
    lots = [
        CreditLot(1, "paid_purchase", 100, None),
        CreditLot(2, "beta_grant", 7, NOW + timedelta(days=1)),
    ]

    assert allocate_spend(lots, amount=9, now=NOW) == [(2, 7), (1, 2)]


def test_wallet_never_counts_expired_beta_credit_as_available() -> None:
    lots = [
        CreditLot(1, "beta_grant", 300, NOW - timedelta(seconds=1)),
        CreditLot(2, "paid_purchase", 12, None),
    ]

    assert allocate_spend(lots, amount=13, now=NOW) is None
    assert wallet_summary(lots, now=NOW) == {
        "credits": 12,
        "beta_credits": 0,
        "paid_credits": 12,
        "promo_credits": 0,
        "beta_expires_at": None,
    }


def test_wallet_reports_the_nearest_active_beta_expiry_without_mixing_paid_credit() -> None:
    lots = [
        CreditLot(1, "beta_grant", 80, NOW + timedelta(days=5)),
        CreditLot(2, "beta_grant", 20, NOW + timedelta(days=2)),
        CreditLot(3, "promo", 5, None),
    ]

    summary = wallet_summary(lots, now=NOW)

    assert summary["credits"] == 105
    assert summary["beta_credits"] == 100
    assert summary["promo_credits"] == 5
    assert summary["paid_credits"] == 0
    assert summary["beta_expires_at"] == NOW + timedelta(days=2)


def test_wallet_creates_recovery_credit_for_a_refund_after_an_expiring_lot_closes() -> None:
    assert recovery_credit_amount(
        amount=9,
        allocation_total=9,
        restored_amount=2,
    ) == 7


@pytest.mark.parametrize(
    "allocation_total, restored_amount",
    [(8, 2), (10, 11), (-1, 0)],
)
def test_wallet_rejects_malformed_refund_allocation_totals(
    allocation_total: int,
    restored_amount: int,
) -> None:
    with pytest.raises(ValueError):
        recovery_credit_amount(
            amount=10,
            allocation_total=allocation_total,
            restored_amount=restored_amount,
        )
