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
from fastapi.testclient import TestClient

from app.main import app
from app.storage import get_storage


def test_register_grants_welcome_credits():
    client = TestClient(app)
    r = client.post("/auth/register", json={"user_id": "newbie", "password": "pw"})
    assert r.status_code == 200
    store = get_storage()
    credits = asyncio.get_event_loop().run_until_complete(store.get_credits("newbie"))
    assert credits == 50
    txns = store._conn.execute(
        "SELECT delta, reason FROM credit_transactions WHERE user_id = ?",
        ("newbie",),
    ).fetchall()
    assert [(t["delta"], t["reason"]) for t in txns] == [(50, "welcome")]
