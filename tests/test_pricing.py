# tests/test_pricing.py
from app.billing import pricing
from app.billing.models import PackInfo


def test_pack_list_order_and_values():
    packs = pricing.pack_list()
    assert [p.id for p in packs] == ["starter", "value", "pro"]
    starter, value, pro = packs
    assert (starter.price_paise, starter.credits) == (9900, 100)
    assert (value.price_paise, value.credits) == (24900, 280)
    assert (pro.price_paise, pro.credits) == (49900, 625)
    assert all(isinstance(p, PackInfo) for p in packs)


def test_get_pack_known_and_unknown():
    assert pricing.get_pack("starter").credits == 100
    assert pricing.get_pack("nope") is None


def test_gate_cost_constants():
    assert pricing.COMM_MODULE_COST == 40
    assert pricing.INT_ATTEMPT_COST == 50
    assert pricing.GD_ATTEMPT_COST == 50
    assert pricing.FREE_ATTEMPTS == 2
