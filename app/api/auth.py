from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import jwt
import datetime
import bcrypt
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "zidd_beta_secret_key" # Normally loaded from settings
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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=TokenResponse)
async def register(req: AuthRequest):
    store = get_storage()
    profile = await store.get_profile(req.user_id)
    if profile:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password using bcrypt
    hashed_password = hash_password(req.password)
    await store.ensure_profile(req.user_id, name="", password_hash=hashed_password)
    
    token = create_access_token({"sub": req.user_id})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
async def login(req: AuthRequest):
    store = get_storage()
    profile = await store.get_profile(req.user_id)
    
    if not profile or not profile.get("password_hash"):
        # Legacy fallback if no password exists in DB yet, assign it now.
        if profile and not profile.get("password_hash"):
            hashed_password = hash_password(req.password)
            await store.ensure_profile(req.user_id, name=profile.get("name", ""), password_hash=hashed_password)
            profile = await store.get_profile(req.user_id)
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
    hashed_password = profile.get("password_hash")
    if not hashed_password or not verify_password(req.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": req.user_id})
    return {"access_token": token, "token_type": "bearer"}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
