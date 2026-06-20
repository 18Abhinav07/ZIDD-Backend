"""Test-auth bypass must be hard-blocked under APP_ENV=prod (security).

The middleware's ``test_token`` / no-header fallback exists only so the legacy
test suite can hit protected endpoints without minting real JWTs. It is gated on
an explicit ``ZIDD_ALLOW_TEST_AUTH=1`` opt-in AND pytest's ``PYTEST_CURRENT_TEST``
marker — but defense-in-depth requires it to be *impossible* in production even
if both of those leak into a prod process's env. These tests prove the
``APP_ENV=prod`` guard closes that door.

Baseline in the test process (set by conftest.py / pytest):
  - ZIDD_ALLOW_TEST_AUTH = "1"
  - PYTEST_CURRENT_TEST   = present (pytest sets it per-test)
  - APP_ENV               = unset -> defaults to "dev"
So the bypass is LIVE by default here; each test only flips APP_ENV to observe
the guard.
"""
import os

import pytest

from app.config import get_jwt_secret
from app.middleware.auth import JWTAuthMiddleware

# A ≥32-char secret so the prod tests pass get_jwt_secret's prod-floor check
# (the suite's default secret is only 21 chars). In real prod the secret is
# guaranteed ≥32 by the boot-time floor, so this faithfully models prod: the
# 401 then comes solely from jwt.decode rejecting the non-JWT 'test_token',
# isolating the bypass-block from the unrelated weak-secret guard.
_PROD_STRENGTH_SECRET = "prod-strength-jwt-secret-0123456789abcdef"


class _FakeURL:
    def __init__(self, path: str):
        self.path = path


class _FakeRequest:
    """Minimal stand-in for starlette Request the middleware actually reads."""

    def __init__(self, path: str = "/billing/balance", token: str | None = "test_token"):
        self.url = _FakeURL(path)
        self.headers = {"Authorization": f"Bearer {token}"} if token is not None else {}

        class _State:
            pass

        self.state = _State()


def _bypass_prerequisites_present() -> bool:
    """Confirm the opt-in vars are live so a 'blocked' result is attributable
    to the APP_ENV guard and not a missing prerequisite."""
    return (
        os.environ.get("ZIDD_ALLOW_TEST_AUTH") == "1"
        and "PYTEST_CURRENT_TEST" in os.environ
    )


@pytest.mark.asyncio
async def test_bypass_fires_outside_prod(monkeypatch):
    """Positive control: with APP_ENV=dev the test_token bypass DOES fire,
    so the prod block below is a real state change, not a no-op."""
    assert _bypass_prerequisites_present()
    monkeypatch.setenv("APP_ENV", "dev")

    captured = {}

    async def _call_next(request):
        captured["user_id"] = getattr(request.state, "user_id", None)
        return "ok"

    middleware = JWTAuthMiddleware(app=None)
    result = await middleware.dispatch(_FakeRequest(token="test_token"), _call_next)

    assert result == "ok"
    assert captured["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_token_bypass_blocked_in_prod(monkeypatch):
    """APP_ENV=prod refuses the test_token bypass even with the opt-in vars set:
    'test_token' is not a valid JWT, so the verifier rejects it -> 401."""
    assert _bypass_prerequisites_present()
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("ZIDD_JWT_SECRET", _PROD_STRENGTH_SECRET)
    get_jwt_secret.cache_clear()

    called = {"next": False}

    async def _call_next(request):
        called["next"] = True
        return "ok"

    try:
        middleware = JWTAuthMiddleware(app=None)
        result = await middleware.dispatch(_FakeRequest(token="test_token"), _call_next)
    finally:
        get_jwt_secret.cache_clear()

    # Bypass did NOT short-circuit to call_next; the real verifier ran and
    # rejected the non-JWT 'test_token' string with a 401.
    assert not called["next"]
    assert getattr(result, "status_code", None) == 401


@pytest.mark.asyncio
async def test_no_header_fallback_blocked_in_prod(monkeypatch):
    """APP_ENV=prod also refuses the no-Authorization-header fallback ->
    401 Missing header, instead of the 'test_user_from_middleware_fallback' id."""
    assert _bypass_prerequisites_present()
    monkeypatch.setenv("APP_ENV", "prod")

    called = {"next": False}

    async def _call_next(request):
        called["next"] = True
        return "ok"

    middleware = JWTAuthMiddleware(app=None)
    result = await middleware.dispatch(_FakeRequest(token=None), _call_next)

    assert not called["next"]
    assert getattr(result, "status_code", None) == 401


@pytest.mark.asyncio
async def test_prod_guard_is_case_insensitive(monkeypatch):
    """The guard lower()s APP_ENV, so 'PROD'/'Prod' block the bypass too."""
    assert _bypass_prerequisites_present()
    monkeypatch.setenv("APP_ENV", "PROD")
    monkeypatch.setenv("ZIDD_JWT_SECRET", _PROD_STRENGTH_SECRET)
    get_jwt_secret.cache_clear()

    called = {"next": False}

    async def _call_next(request):
        called["next"] = True
        return "ok"

    try:
        middleware = JWTAuthMiddleware(app=None)
        result = await middleware.dispatch(_FakeRequest(token="test_token"), _call_next)
    finally:
        get_jwt_secret.cache_clear()

    assert not called["next"]
    assert getattr(result, "status_code", None) == 401
