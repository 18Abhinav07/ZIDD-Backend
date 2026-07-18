import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import os

from app.config import get_jwt_secret, get_settings

ALGORITHM = "HS256"

_PAYMENT_PATHS = (
    "/billing/packs",
    "/billing/dev/grant",
    "/billing/purchase",
    "/billing/razorpay",
)


def _is_payment_path(path: str) -> bool:
    return any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in _PAYMENT_PATHS
    )


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            get_settings().billing_mode == "disabled"
            and _is_payment_path(request.url.path)
        ):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        # Exclude auth and health paths
        if (
            request.url.path.startswith("/auth")
            or request.url.path.startswith("/health")
            or request.url.path == "/"
            or request.url.path == "/billing/razorpay/webhook"
        ):
            return await call_next(request)
            
        # Test-auth bypass requires an EXPLICIT opt-in so it can never fire in
        # production even if PYTEST_CURRENT_TEST somehow leaks into the env.
        # Hard-blocked when APP_ENV=prod: the bypass is dev/test-only by design,
        # so prod refuses it regardless of the pytest opt-in vars. APP_ENV is read
        # from os.environ directly (mirroring config.get_jwt_secret) so it can't be
        # served stale from a memoized settings instance.
        test_auth_allowed = (
            os.environ.get("ZIDD_ALLOW_TEST_AUTH") == "1"
            and "PYTEST_CURRENT_TEST" in os.environ
            and os.environ.get("APP_ENV", "dev").lower() != "prod"
        )

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            if request.method == "GET" and request.url.path == "/school/state":
                request.state.user_id = None
                return await call_next(request)
            # Allow fallback ONLY in pytest environment if no header is provided (for legacy tests)
            if test_auth_allowed:
                request.state.user_id = "test_user_from_middleware_fallback"
                return await call_next(request)
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid authorization header"})
        else:
            token = auth_header.split(" ")[1]
            if test_auth_allowed and token == "test_token":
                request.state.user_id = "test_user"
                return await call_next(request)

            try:
                payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
                sub = payload.get("sub")
                # A validly-signed token with a missing/empty/non-string `sub`
                # must NOT authenticate as None. A null identity would later
                # fall through to a spoofable body field (identity-spoofing
                # chain); reject the token outright instead.
                if not isinstance(sub, str) or not sub.strip():
                    return JSONResponse(status_code=401, content={"detail": "Invalid token"})
                request.state.user_id = sub
            except jwt.ExpiredSignatureError:
                return JSONResponse(status_code=401, content={"detail": "Token expired"})
            except jwt.InvalidTokenError:
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        
        return await call_next(request)
