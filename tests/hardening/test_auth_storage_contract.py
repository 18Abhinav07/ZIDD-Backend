import asyncio

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import auth as auth_module
from app.config import get_jwt_secret, get_settings
from app.storage.pg_store import PgStore
from app.main import app
from app.models import SessionStartRequest
from app.storage import get_storage, reset_storage


def _run(coro):
    return asyncio.run(coro)


def test_legacy_local_auth_routes_are_removed():
    client = TestClient(app)

    assert client.post("/auth/register", json={"user_id": "u", "password": "pw"}).status_code == 404
    assert client.post("/auth/login", json={"user_id": "u", "password": "pw"}).status_code == 404
    assert client.post("/auth/refresh").status_code == 404


def test_google_auth_creates_profile_and_mints_backend_jwt(monkeypatch, store):
    monkeypatch.setattr(
        auth_module.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: {
            "iss": "https://accounts.google.com",
            "sub": "google-sub-1",
            "email": "learner@example.com",
            "email_verified": True,
            "name": "  Asha  ",
        },
    )

    client = TestClient(app)
    response = client.post("/auth/google", json={"id_token": "fake"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["is_new_user"] is True

    profile = _run(store.get_profile_by_google_sub("google-sub-1"))
    assert profile["user_id"] == "google:google-sub-1"
    assert profile["name"] == "Asha"
    assert profile["credits"] == get_settings().welcome_credits
    assert store.google_login_resolutions == 1


def test_google_cert_fetch_timeout_is_bounded():
    calls = {}

    def delegate(url, method="GET", body=None, headers=None, timeout=None, **kwargs):
        calls["timeout"] = timeout
        return object()

    bounded = auth_module.BoundedGoogleRequest(delegate, timeout=5.0)
    bounded("https://www.googleapis.com/oauth2/v1/certs", timeout=120)

    assert calls["timeout"] == 5.0


def test_session_start_body_rejects_user_id():
    with pytest.raises(ValidationError):
        SessionStartRequest(user_id="spoof", competency_node="comm_00_greetings")


def test_storage_runtime_is_cloud_only_even_if_env_requests_local(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    get_settings.cache_clear()
    reset_storage()

    assert isinstance(get_storage(), PgStore)


def test_db_engine_reuses_bounded_pool_for_auth_latency(monkeypatch):
    from app.db import engine as engine_module

    engine_module._engine = None
    get_settings.cache_clear()

    engine = engine_module.get_engine()

    assert engine.sync_engine.pool.__class__.__name__ != "NullPool"


def test_dev_credit_grant_requires_explicit_enable(monkeypatch, store):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ENABLE_DEV_CREDIT_GRANT", "false")
    get_settings.cache_clear()
    _run(store.ensure_profile("test_user"))

    client = TestClient(app)
    response = client.post(
        "/billing/dev/grant?amount=25",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 404
    assert _run(store.get_credits("test_user")) == 0
    get_settings.cache_clear()


def test_dev_credit_grant_works_only_when_explicitly_enabled(monkeypatch, store):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ENABLE_DEV_CREDIT_GRANT", "true")
    get_settings.cache_clear()
    _run(store.ensure_profile("test_user"))

    client = TestClient(app)
    response = client.post(
        "/billing/dev/grant?amount=25",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["granted"] == 25
    assert response.json()["credits"] == 25
    get_settings.cache_clear()


def test_dev_credit_grant_stays_closed_in_prod_even_with_flag(monkeypatch, store):
    from app.api.auth import create_access_token

    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("ENABLE_DEV_CREDIT_GRANT", "true")
    get_settings.cache_clear()
    get_jwt_secret.cache_clear()
    _run(store.ensure_profile("test_user"))
    token = create_access_token({"sub": "test_user"})

    client = TestClient(app)
    response = client.post(
        "/billing/dev/grant?amount=25",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert _run(store.get_credits("test_user")) == 0
    get_settings.cache_clear()
    get_jwt_secret.cache_clear()
