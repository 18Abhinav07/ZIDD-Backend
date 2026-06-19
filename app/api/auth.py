from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import jwt
import datetime
import bcrypt
from app.config import get_jwt_secret, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

from app.storage import get_storage

class AuthRequest(BaseModel):
    user_id: str
    password: str
    # Optional display name captured at registration so the coach can address the
    # learner by name. Ignored by login. Stored on the profile and sourced into
    # every session's learner_name by start_session.
    name: str = ""

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=TokenResponse)
async def register(req: AuthRequest):
    # Reject empty / whitespace-only credentials up front. A blank user_id would
    # later become a blank JWT `sub` (which the middleware now rejects) and a
    # blank password is never a real credential.
    user_id = req.user_id.strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id must not be empty")
    if not req.password:
        raise HTTPException(status_code=400, detail="password must not be empty")

    store = get_storage()
    profile = await store.get_profile(user_id)
    if profile:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password using bcrypt
    hashed_password = hash_password(req.password)
    await store.ensure_profile(user_id, name=req.name.strip(), password_hash=hashed_password)
    await store.grant_credits(user_id, get_settings().welcome_credits, "welcome")

    token = create_access_token({"sub": user_id})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login(req: AuthRequest):
    store = get_storage()
    profile = await store.get_profile(req.user_id)

    # A missing profile, OR a profile with no/blank password hash (session-seeded,
    # legacy, or demo ids), is NOT a usable credential. The old code hashed the
    # caller's submitted password INTO such a profile and then verified against
    # that just-written hash, minting a valid token for any account it knew the
    # id of (account takeover). Any null/blank-hash profile must 401 instead.
    hashed_password = profile.get("password_hash") if profile else None
    if not hashed_password or not verify_password(req.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": req.user_id})
    return {"access_token": token, "token_type": "bearer"}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=ALGORITHM)
    return encoded_jwt
