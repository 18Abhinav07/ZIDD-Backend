"""GET /session/{id}/transcript — reload-safe conversation rehydration.

A browser reload used to wipe the chat: the FE started with an empty transcript
and only replayed the streamed opening, so every turn in between was lost. The
backend already persists the full conversation in state["messages"]; this route
serves it (ownership-gated like every per-session route) so the client can
restore the transcript + session chrome on mount instead of starting blank.

Mirrors the offline, monkeypatched style of test_session_ownership.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest
from fastapi.testclient import TestClient

import app.api.routes as routes
from app.main import app
from app.services import session_service as svc

OWN = {"Authorization": "Bearer test_token"}  # -> middleware identity "test_user"


@pytest.fixture
def client():
    return TestClient(app)


def _own_state(**over) -> dict:
    base = {
        "session_id": "sid1",
        "user_id": "test_user",
        "competency_node": "comm_02_describe_routine",
        "current_mastery": 0.42,
        "turn_count": 3,
        "messages": [
            {"role": "assistant", "content": "Hi! Ready to practice?"},
            {"role": "user", "content": "yes"},
            {"role": "assistant", "content": "Great, tell me about your day."},
        ],
        "opening_streamed": True,
    }
    base.update(over)
    return base


def test_transcript_unknown_session_is_404(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: None)
    r = client.get("/session/nope/transcript", headers=OWN)
    assert r.status_code == 404


def test_transcript_on_anothers_session_is_403(client, monkeypatch):
    # Owned by 'victim'; caller authenticates as 'test_user' -> IDOR read blocked.
    monkeypatch.setattr(svc, "get_state", lambda sid: _own_state(user_id="victim"))
    r = client.get("/session/sid1/transcript", headers=OWN)
    assert r.status_code == 403


def test_transcript_returns_messages_state_and_opening_flag(client, monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: _own_state())
    monkeypatch.setattr(
        routes,
        "_state_snapshot",
        lambda st: {"session_id": st["session_id"], "current_mastery": st["current_mastery"]},
    )
    r = client.get("/session/sid1/transcript", headers=OWN)
    assert r.status_code == 200
    body = r.json()

    # opening already streamed -> the client rehydrates instead of replaying it.
    assert body["opening_streamed"] is True
    # the same snapshot the done frame carries, so the UI restores its chrome too.
    assert body["state"]["current_mastery"] == 0.42

    msgs = body["messages"]
    assert len(msgs) == 3
    # Stable, deterministic ids so React keys survive a reload (no remount churn).
    assert [m["id"] for m in msgs] == ["sid1-0", "sid1-1", "sid1-2"]
    assert msgs[0]["role"] == "assistant"
    assert msgs[0]["content"] == "Hi! Ready to practice?"
    assert msgs[1] == {"id": "sid1-1", "role": "user", "content": "yes", "speaker_name": None}


def test_transcript_empty_for_fresh_session(client, monkeypatch):
    # A brand-new session (opening not yet streamed) -> empty transcript + flag
    # False, so the client knows to stream the opening rather than restore blank.
    monkeypatch.setattr(
        svc, "get_state", lambda sid: _own_state(messages=[], opening_streamed=False)
    )
    monkeypatch.setattr(routes, "_state_snapshot", lambda st: {"session_id": st["session_id"]})
    r = client.get("/session/sid1/transcript", headers=OWN)
    assert r.status_code == 200
    body = r.json()
    assert body["messages"] == []
    assert body["opening_streamed"] is False
