import asyncio

from fastapi.testclient import TestClient

from app.api import auth as auth_module
from app.config import get_settings
from app.main import app
from app.middleware.rate_limit import turn_counts
from app.services import session_service as svc

AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def test_auth_limiter_counts_only_google_auth(monkeypatch):
    def _invalid_google_token(*args, **kwargs):
        raise ValueError("bad token")

    monkeypatch.setattr(
        auth_module.google_id_token,
        "verify_oauth2_token",
        _invalid_google_token,
    )

    client = TestClient(app)
    for _ in range(get_settings().auth_google_limit_per_minute):
        assert client.post("/auth/google", json={"id_token": "bad"}).status_code == 401

    limited = client.post("/auth/google", json={"id_token": "bad"})
    assert limited.status_code == 429
    assert limited.json()["detail"]["code"] == "auth_rate_limited"

    assert client.get("/health").status_code != 429


def test_turn_limiter_counts_only_session_turn(monkeypatch, store):
    async def _fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False):
        return "session-for-rate-test", {
            "session_id": "session-for-rate-test",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", _fake_start)
    _run(store.ensure_profile("test_user"))
    _run(store.set_demo_unlimited("test_user", True))

    client = TestClient(app)
    for index in range(get_settings().session_turn_limit_per_day + 5):
        response = client.post(
            "/session/start",
            json={
                "competency_node": "comm_00_greetings",
                "client_start_id": f"rate-start-{index}",
            },
            headers=AUTH,
        )
        assert response.status_code == 200

    assert "test_user" not in turn_counts

    for _ in range(get_settings().session_turn_limit_per_day):
        response = client.post(
            "/session/turn",
            json={"session_id": "missing", "user_input": "hello"},
            headers=AUTH,
        )
        assert response.status_code == 404

    limited = client.post(
        "/session/turn",
        json={"session_id": "missing", "user_input": "hello"},
        headers=AUTH,
    )
    assert limited.status_code == 429
    assert limited.json()["detail"]["code"] == "turn_limit_exceeded"
