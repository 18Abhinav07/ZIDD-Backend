from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
import datetime
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.config import get_jwt_secret, get_settings
from app.storage import get_storage

router = APIRouter(prefix="/auth", tags=["auth"])

ALGORITHM = "HS256"
GOOGLE_CERT_TIMEOUT_SECONDS = 5.0


class BoundedGoogleRequest:
    """google-auth Request wrapper with a short cert-fetch timeout."""

    def __init__(self, delegate: google_requests.Request, timeout: float) -> None:
        self._delegate = delegate
        self._timeout = timeout

    def __call__(
        self,
        url,
        method="GET",
        body=None,
        headers=None,
        timeout=None,
        **kwargs,
    ):
        effective_timeout = self._timeout
        if timeout is not None:
            effective_timeout = min(float(timeout), self._timeout)
        return self._delegate(
            url,
            method=method,
            body=body,
            headers=headers,
            timeout=effective_timeout,
            **kwargs,
        )


_google_request = BoundedGoogleRequest(
    google_requests.Request(), GOOGLE_CERT_TIMEOUT_SECONDS
)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    is_new_user: bool = False

class GoogleAuthRequest(BaseModel):
    id_token: str

@router.post("/google", response_model=TokenResponse)
async def google_auth(req: GoogleAuthRequest):
    """Verify a Google-issued id_token (from Next.js/NextAuth) and mint our own
    JWT. Resolves the account by google_sub first, then by email for legacy
    account continuity, else creates a new profile. Welcome credits are granted
    exactly once, only on that creation path.
    """
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="Google sign-in is not configured")

    try:
        claims = google_id_token.verify_oauth2_token(
            req.id_token, _google_request, settings.google_client_id
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # Google's own doc-recommended issuer check: verify_oauth2_token already
    # validates signature/audience/expiry, but not which of Google's two valid
    # issuer strings was used — enforce it explicitly rather than trusting the
    # library's default.
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    google_sub = claims.get("sub")
    email = claims.get("email")
    email_verified = claims.get("email_verified", False)
    name = claims.get("name", "") or ""

    if not google_sub or not email or not email_verified:
        raise HTTPException(status_code=401, detail="Google account missing a verified email")

    resolved = await get_storage().resolve_google_login(
        google_sub=google_sub,
        email=email,
        name=name,
        welcome_credits=get_settings().welcome_credits,
    )
    user_id = resolved["user_id"]
    is_new = bool(resolved["is_new_user"])

    token = create_access_token({"sub": user_id})
    return {"access_token": token, "token_type": "bearer", "is_new_user": is_new}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=ALGORITHM)
    return encoded_jwt
