import os
import tempfile

os.environ["AI_BACKEND"] = "local"
_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["LOCAL_STORE_PATH"] = _DB.name
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.content.registry import COMM_ID, get_module
from app.main import app
from app.services import session_service as svc
from app.storage import get_storage, reset_storage

COMM_SECOND = get_module(COMM_ID).order[1]
AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"


@pytest.fixture(autouse=True)
def fake_start(monkeypatch):
    async def _fake_start(user_id, node_id, learner_name="", test_mode=False):
        return ("s1", {
            "session_id": "s1",
            "competency_node": node_id,
            "current_mastery": 0.0,
        })
    monkeypatch.setattr(svc, "start_session", _fake_start)


@pytest.fixture(autouse=True)
def _isolate_store(monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    yield
    reset_storage()
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_state(_isolate_store):
    get_storage()  # ensure the LocalStore schema exists before wiping
    import sqlite3
    conn = sqlite3.connect(_DB.name)
    conn.executescript(
        "DELETE FROM content_unlocks; "
        "DELETE FROM credit_transactions; "
        "DELETE FROM profiles;"
    )
    conn.commit()
    conn.close()
    yield


def _seed(coro):
    asyncio.get_event_loop().run_until_complete(coro)


def test_paid_node_without_confirm_returns_402_confirm_required():
    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    _seed(store.grant_credits("test_user", 50, "welcome"))
    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND},
        headers=AUTH,
    )
    assert r.status_code == 402
    body = r.json()["detail"]
    assert body["error"] == "confirm_required"
    assert body["cost"] == 40
    assert body["balance"] == 50


def test_paid_node_with_confirm_charges_and_starts():
    store = get_storage()
    _seed(store.ensure_profile("buyer"))
    _seed(store.grant_credits("buyer", 50, "welcome"))
    _seed(store.ensure_profile("test_user"))
    _seed(store.grant_credits("test_user", 50, "welcome"))
    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND, "confirm": True},
        headers=AUTH,
    )
    assert r.status_code == 200
    assert r.json()["session_id"] == "s1"
    assert _run(store.get_credits("test_user")) == 10
    assert _run(store.has_unlock("test_user", "feature", COMM_ID)) is True


def test_insufficient_balance_returns_pack_picker():
    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND, "confirm": True},
        headers=AUTH,
    )
    assert r.status_code == 402
    body = r.json()["detail"]
    assert body["error"] == "insufficient_credits"
    assert [p["id"] for p in body["packs"]] == ["starter", "value", "pro"]


def test_unknown_node_returns_404():
    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": "no_such_node"},
        headers=AUTH,
    )
    assert r.status_code == 404


def test_start_failure_refunds_charged_credits(monkeypatch):
    # A paying (non-demo) user confirms a paid ACCESS node. We charge 40, then
    # svc.start_session raises ValueError -> 400. The 40 credits charged for a
    # session that never started MUST be refunded, not silently lost.
    async def _boom(user_id, node_id, learner_name="", test_mode=False):
        raise ValueError("brain refused to start")
    monkeypatch.setattr(svc, "start_session", _boom)

    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    _seed(store.grant_credits("test_user", 50, "welcome"))

    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND, "confirm": True},
        headers=AUTH,
    )
    assert r.status_code == 400
    # Balance restored to the pre-charge amount: charged 40 then refunded 40.
    assert _run(store.get_credits("test_user")) == 50


def test_start_failure_removes_access_unlock(monkeypatch):
    # Revenue-leak guard. A first-time PAID Communication node is an ACCESS
    # unlock: charge() deducts 40 AND writes a content_unlocks row (owned
    # forever). If svc.start_session then raises ValueError -> 400, the refund
    # must undo BOTH sides: hand the 40 credits back AND delete the unlock row.
    # Otherwise the learner gets their credits back and keeps permanent free
    # (owned) access to the whole module — paying nothing.
    async def _boom(user_id, node_id, learner_name="", test_mode=False):
        raise ValueError("brain refused to start")
    monkeypatch.setattr(svc, "start_session", _boom)

    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    _seed(store.grant_credits("test_user", 50, "welcome"))

    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND, "confirm": True},
        headers=AUTH,
    )
    assert r.status_code == 400
    # (a) credits refunded back to the pre-charge balance.
    assert _run(store.get_credits("test_user")) == 50
    # (b) the ACCESS unlock charge() wrote must be gone — no permanent free access.
    assert _run(store.has_unlock("test_user", "feature", COMM_ID)) is False


def test_start_failure_does_not_refund_demo_user(monkeypatch):
    # Demo/judge users are never charged (decision.free), so a start failure must
    # NOT hand them a phantom refund that inflates a balance they never spent.
    async def _boom(user_id, node_id, learner_name="", test_mode=False):
        raise ValueError("brain refused to start")
    monkeypatch.setattr(svc, "start_session", _boom)

    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    _seed(store.grant_credits("test_user", 50, "welcome"))
    _seed(store.set_demo_unlimited("test_user", True))

    client = TestClient(app)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND, "confirm": True},
        headers=AUTH,
    )
    assert r.status_code == 400
    # Demo user was never charged and gets no refund: balance unchanged.
    assert _run(store.get_credits("test_user")) == 50


def test_start_failure_refunds_on_non_value_error(monkeypatch):
    # FIX #5 — the refund/compensation must fire on ANY start failure, not only
    # ValueError. A downstream KeyError after charge() must NOT burn the wallet,
    # and a non-ValueError fault surfaces as a 500 (not a misleading 400).
    async def _boom(user_id, node_id, learner_name="", test_mode=False):
        raise KeyError("downstream defect after charge")

    monkeypatch.setattr(svc, "start_session", _boom)

    store = get_storage()
    _seed(store.ensure_profile("test_user"))
    _seed(store.grant_credits("test_user", 50, "welcome"))

    client = TestClient(app, raise_server_exceptions=False)
    r = client.post(
        "/session/start",
        json={"user_id": "test_user", "competency_node": COMM_SECOND, "confirm": True},
        headers=AUTH,
    )
    assert r.status_code == 500
    # Charged 40 then refunded 40 despite the non-ValueError failure.
    assert _run(store.get_credits("test_user")) == 50
    # The ACCESS unlock charge() wrote must also be undone.
    assert _run(store.has_unlock("test_user", "feature", COMM_ID)) is False


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
