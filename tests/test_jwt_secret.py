"""JWT signing-secret hardening (security ship-blocker #1).

Proves:
1. get_jwt_secret() fails closed when ZIDD_JWT_SECRET is unset.
2. A token minted by app/api/auth.py's signer verifies through
   app/middleware/auth.py's verifier — i.e. both read the SAME secret.
"""
from types import SimpleNamespace

import jwt
import pytest

from app.api.auth import ALGORITHM, create_access_token
from app.config import get_jwt_secret
from app.middleware.auth import JWTAuthMiddleware


def test_get_jwt_secret_raises_when_unset(monkeypatch):
    """No committed default — a missing secret must fail at call time.

    "Unset" means *nowhere*: not in the OS env AND not in the .env-backed
    settings. A real localhost run populates .env with ZIDD_JWT_SECRET, which
    get_jwt_secret() falls back to — so deleting only the OS var no longer
    models an unconfigured app. Stub get_settings() to an empty secret too, so
    this asserts the genuine fail-closed contract regardless of the CWD's .env.
    """
    monkeypatch.delenv("ZIDD_JWT_SECRET", raising=False)
    monkeypatch.setattr(
        "app.config.get_settings", lambda: SimpleNamespace(zidd_jwt_secret="")
    )
    get_jwt_secret.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="ZIDD_JWT_SECRET is not set"):
            get_jwt_secret()
    finally:
        # Drop the failed-call state. monkeypatch restores the env var at
        # teardown, so the next caller re-reads the conftest secret cleanly.
        get_jwt_secret.cache_clear()


def test_get_jwt_secret_rejects_short_secret_in_prod(monkeypatch):
    """Production refuses a weak (<32-char) HMAC key — it is brute-forceable."""
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("ZIDD_JWT_SECRET", "short-key")  # 9 chars
    get_jwt_secret.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="at least 32 characters"):
            get_jwt_secret()
    finally:
        get_jwt_secret.cache_clear()


def test_get_jwt_secret_accepts_strong_secret_in_prod(monkeypatch):
    """A 32+ char secret is accepted under APP_ENV=prod."""
    strong = "x" * 32
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("ZIDD_JWT_SECRET", strong)
    get_jwt_secret.cache_clear()
    try:
        assert get_jwt_secret() == strong
    finally:
        get_jwt_secret.cache_clear()


def test_get_jwt_secret_allows_short_secret_outside_prod(monkeypatch):
    """Dev/test stay permissive so the suite runs with a short fixture secret."""
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ZIDD_JWT_SECRET", "short-dev-secret")  # <32, fine in dev
    get_jwt_secret.cache_clear()
    try:
        assert get_jwt_secret() == "short-dev-secret"
    finally:
        get_jwt_secret.cache_clear()


def test_sign_verify_round_trip_share_one_secret():
    """The signer's token decodes with the secret the verifier uses."""
    token = create_access_token({"sub": "round_trip_user"})
    # The verifier in the middleware decodes with exactly this secret + alg.
    payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
    assert payload["sub"] == "round_trip_user"


@pytest.mark.asyncio
async def test_middleware_verifier_accepts_signer_token():
    """Drive the real middleware: a signer token sets request.state.user_id."""

    class _FakeURL:
        path = "/billing/balance"

    class _FakeRequest:
        def __init__(self, token: str):
            self.url = _FakeURL()
            self.headers = {"Authorization": f"Bearer {token}"}

            class _State:
                pass

            self.state = _State()

    captured = {}

    async def _call_next(request):
        captured["user_id"] = getattr(request.state, "user_id", None)
        return "ok"

    token = create_access_token({"sub": "mw_user"})
    middleware = JWTAuthMiddleware(app=None)
    result = await middleware.dispatch(_FakeRequest(token), _call_next)

    assert result == "ok"
    assert captured["user_id"] == "mw_user"
