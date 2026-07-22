import asyncio

from fastapi.testclient import TestClient

from app.billing import pricing
from app.billing.gate import resolve_gate, resolve_school_chapter_gate
from app.config import get_settings
from app.content.registry import COMM_ID, GD_ID, INT_ID, get_module
from app.main import app
from tests.hardening.test_school_rebuild_phase_8_curriculum_teaching_contract import (
    AUTH,
    _seed_direct_curriculum_report_lineage,
    _seed_school_profile,
)


class JourneyStore:
    def __init__(self) -> None:
        self.unlocks: set[tuple[str, str, str]] = set()

    async def is_demo(self, _user_id: str) -> bool:
        return False

    async def has_unlock(self, user_id: str, scope: str, ref_id: str) -> bool:
        return (user_id, scope, ref_id) in self.unlocks


def _use_journey_policy(monkeypatch) -> None:
    monkeypatch.setenv("BILLING_MODE", "enabled")
    monkeypatch.setenv("BILLING_POLICY", "journey")
    get_settings.cache_clear()


def _unlock_school_curriculum(store, *, class_no: int = 3) -> None:
    profile = _seed_school_profile(store, target_class_no=class_no)
    _seed_direct_curriculum_report_lineage(store, profile)
    report = asyncio.run(
        store.get_school_placement_report_by_id("test_user", "placement-report")
    )
    asyncio.run(
        store.upsert_school_placement_report(
            **{
                **report,
                "placement_status": "target_ready",
                "unlock_state": "target_unlocked",
            }
        )
    )
    store.school_sessions[("test_user", str(report["placement_session_id"]))][
        "status"
    ] = "complete"


def test_journey_catalog_uses_the_beta_to_paid_credit_tariff() -> None:
    assert [(pack.credits, pack.price_paise) for pack in pricing.pack_list()] == [
        (100, 19_900),
        (300, 49_900),
        (750, 99_900),
    ]
    assert pricing.SCHOOL_CHAPTER_COST == 2
    assert pricing.CAREER_SKILL_COST == 4
    assert pricing.CAREER_TEST_ATTEMPT_COST == 12


def test_journey_policy_prices_prep_as_a_durable_skill_and_tests_as_attempts(monkeypatch) -> None:
    _use_journey_policy(monkeypatch)
    store = JourneyStore()
    node_id = get_module(INT_ID).order[0]

    prep = asyncio.run(resolve_gate(store, "learner", node_id, test_mode=False))
    test = asyncio.run(resolve_gate(store, "learner", node_id, test_mode=True))

    assert (prep.free, prep.cost, prep.scope, prep.ref_id, prep.record_unlock) == (
        False,
        4,
        "career_prep_skill",
        node_id,
        True,
    )
    assert (test.free, test.cost, test.scope, test.ref_id, test.record_unlock) == (
        False,
        12,
        "career_test_attempt",
        node_id,
        False,
    )


def test_journey_policy_prices_communication_as_one_durable_unlock(monkeypatch) -> None:
    _use_journey_policy(monkeypatch)
    store = JourneyStore()
    node_id = get_module(COMM_ID).order[0]

    decision = asyncio.run(resolve_gate(store, "learner", node_id))

    assert (decision.free, decision.cost, decision.scope, decision.ref_id) == (
        False,
        4,
        "career_communication_module",
        COMM_ID,
    )
    store.unlocks.add(("learner", decision.scope, decision.ref_id))
    owned = asyncio.run(resolve_gate(store, "learner", node_id))
    assert owned.free is True
    assert owned.owned is True


def test_journey_policy_keeps_gd_test_attempts_separate_from_prep_skills(monkeypatch) -> None:
    _use_journey_policy(monkeypatch)
    store = JourneyStore()
    node_id = get_module(GD_ID).order[0]

    prep = asyncio.run(resolve_gate(store, "learner", node_id, test_mode=False))
    test = asyncio.run(resolve_gate(store, "learner", node_id, test_mode=True))

    assert prep.scope == "career_prep_skill"
    assert test.scope == "career_test_attempt"
    assert prep.ref_id == test.ref_id == node_id


def test_journey_policy_prices_a_school_chapter_as_a_durable_unlock(monkeypatch) -> None:
    _use_journey_policy(monkeypatch)
    store = JourneyStore()

    decision = asyncio.run(
        resolve_school_chapter_gate(
            store,
            "learner",
            subject_id="english",
            class_no=5,
            chapter_id="eng_c5_ch01",
        )
    )

    assert (decision.free, decision.cost, decision.scope, decision.ref_id, decision.record_unlock) == (
        False,
        2,
        "school_chapter",
        "english:class_5:eng_c5_ch01",
        True,
    )


def test_journey_test_start_debits_once_without_a_confirmation_roundtrip(monkeypatch, store) -> None:
    from app.services import session_service as svc

    _use_journey_policy(monkeypatch)
    node_id = get_module(INT_ID).order[0]
    asyncio.run(store.ensure_profile("test_user"))
    asyncio.run(store.grant_credits("test_user", 12, "test_credit"))

    async def prepared_start(user_id, competency_node, *, session_id, **_kwargs):
        return session_id, {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": competency_node,
            "module_id": INT_ID,
            "task_type": "interview_test",
            "test_mode": True,
            "current_mastery": 0.0,
            "session_version": 1,
            "status": "active",
            "messages": [],
        }

    monkeypatch.setattr(svc, "start_session", prepared_start)

    response = TestClient(app).post(
        "/session/start",
        json={
            "competency_node": node_id,
            "test_mode": True,
            "client_start_id": "journey-test-start-no-confirm",
        },
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["session_id"]
    assert asyncio.run(store.get_credits("test_user")) == 0


def test_journey_career_insufficient_response_keeps_scope_for_the_shared_wallet_ui(
    monkeypatch,
    store,
) -> None:
    _use_journey_policy(monkeypatch)
    node_id = get_module(INT_ID).order[0]
    asyncio.run(store.ensure_profile("test_user"))

    response = TestClient(app).post(
        "/session/start",
        json={
            "competency_node": node_id,
            "test_mode": True,
            "client_start_id": "journey-career-insufficient-scope",
        },
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 402
    assert response.json()["detail"] == {
        "error": "insufficient_credits",
        "cost": 12,
        "balance": 0,
        "scope": "career_test_attempt",
        "ref_id": node_id,
        "packs": [pack.model_dump() for pack in pricing.pack_list()],
    }


def test_journey_school_chapter_unlock_is_paid_once_after_access_is_valid(
    monkeypatch,
    store,
) -> None:
    _use_journey_policy(monkeypatch)
    _unlock_school_curriculum(store)
    client = TestClient(app)

    insufficient = client.post(
        "/school/curriculum/start",
        headers=AUTH,
        json={
            "chapter_id": "eng_c3_ch01",
            "client_start_id": "school-journey-insufficient",
        },
    )

    assert insufficient.status_code == 402
    assert insufficient.json()["detail"] == {
        "error": "insufficient_credits",
        "cost": 2,
        "balance": 0,
        "scope": "school_chapter",
        "ref_id": "english:class_3:eng_c3_ch01",
        "packs": [pack.model_dump() for pack in pricing.pack_list()],
    }
    assert asyncio.run(store.get_credits("test_user")) == 0

    asyncio.run(store.grant_credits("test_user", 2, "school-journey-credit"))
    first = client.post(
        "/school/curriculum/start",
        headers=AUTH,
        json={
            "chapter_id": "eng_c3_ch01",
            "client_start_id": "school-journey-paid",
        },
    )
    duplicate = client.post(
        "/school/curriculum/start",
        headers=AUTH,
        json={
            "chapter_id": "eng_c3_ch01",
            "client_start_id": "school-journey-paid",
        },
    )

    assert first.status_code == duplicate.status_code == 200
    assert duplicate.json() == first.json()
    assert first.json()["billing"] == {
        "cost": 2,
        "charged": True,
        "scope": "school_chapter",
        "ref_id": "english:class_3:eng_c3_ch01",
        "credits_remaining": 0,
    }
    assert asyncio.run(store.get_credits("test_user")) == 0
    assert asyncio.run(
        store.has_unlock(
            "test_user",
            "school_chapter",
            "english:class_3:eng_c3_ch01",
        )
    )
