"""Findings #3 / #7 / #8 — session ownership (IDOR) + falsy-`sub` identity guard.

Every per-session route binds to the AUTHENTICATED identity (JWT `sub` stamped
by the middleware) and refuses to act on a session owned by someone else. A
validly-signed token whose `sub` is missing/empty/whitespace must not
authenticate at all (it would otherwise fall through to a spoofable identity).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import jwt
import pytest
from fastapi.testclient import TestClient

import app.api.routes as routes
from app.config import get_jwt_secret
from app.main import app
from app.services import session_service as svc

OWN = {"Authorization": "Bearer test_token"}  # -> middleware identity "test_user"
VICTIM_STATE = {
    "session_id": "victim_sid",
    "user_id": "victim",  # owned by someone OTHER than test_user
    "competency_node": "comm_02_describe_routine",
    "current_mastery": 0.5,
    "turn_count": 1,
}


def _sign(payload: dict) -> dict:
    tok = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture
def client():
    return TestClient(app)


# ---- IDOR: session owned by 'victim', caller authenticates as 'test_user' ---

def test_turn_on_anothers_session_is_403(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: dict(VICTIM_STATE))
    r = client.post(
        "/session/turn",
        json={"session_id": "victim_sid", "user_input": "hi"},
        headers=OWN,
    )
    assert r.status_code == 403


def test_end_on_anothers_session_is_403(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: dict(VICTIM_STATE))
    r = client.post("/session/victim_sid/end", headers=OWN)
    assert r.status_code == 403


def test_state_on_anothers_session_is_403(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: dict(VICTIM_STATE))
    r = client.get("/session/victim_sid/state", headers=OWN)
    assert r.status_code == 403


def test_opening_on_anothers_session_is_403(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: dict(VICTIM_STATE))
    r = client.get("/session/victim_sid/opening", headers=OWN)
    assert r.status_code == 403


def test_progress_of_another_user_is_403(client):
    r = client.get("/session/progress/victim", headers=OWN)
    assert r.status_code == 403


def test_unknown_session_is_404(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: None)
    r = client.get("/session/nope/state", headers=OWN)
    assert r.status_code == 404


# ---- positive: caller owns the session / queries their own progress ---------

def test_turn_on_own_session_ok(client, monkeypatch):
    own_state = dict(VICTIM_STATE, user_id="test_user")
    monkeypatch.setattr(svc, "get_state", lambda sid: own_state)
    monkeypatch.setattr(routes, "_state_snapshot", lambda st: {"session_id": st["session_id"]})

    async def _fake_run_turn(session_id, user_input):
        yield "ok-token"

    monkeypatch.setattr(svc, "run_turn", _fake_run_turn)
    r = client.post(
        "/session/turn",
        json={"session_id": "own_sid", "user_input": "hi"},
        headers=OWN,
    )
    assert r.status_code == 200
    assert "ok-token" in r.text


def test_progress_of_self_ok(client, monkeypatch):
    async def _fake_map(user_id, module_id):
        return [{"node_id": "comm_01_self_intro", "mastery": 0.0}]

    monkeypatch.setattr(svc, "get_progression_map", _fake_map)
    r = client.get("/session/progress/test_user", headers=OWN)
    assert r.status_code == 200
    assert r.json()[0]["node_id"] == "comm_01_self_intro"


# ---- #7: a validly-signed token with no usable `sub` must 401 ---------------

def test_token_missing_sub_is_401(client):
    r = client.get("/session/x/state", headers=_sign({"foo": "bar"}))
    assert r.status_code == 401


def test_token_empty_sub_is_401(client):
    r = client.get("/session/x/state", headers=_sign({"sub": ""}))
    assert r.status_code == 401


def test_token_whitespace_sub_is_401(client):
    r = client.get("/session/x/state", headers=_sign({"sub": "   "}))
    assert r.status_code == 401
