"""H3 — a streaming turn whose generator dies mid-stream MUST still emit a
terminal `done` frame (preceded by an `error` frame), so the client's streaming
lock is always released.

Before this, `run_turn` / `stream_opening` raising mid-iteration closed the SSE
body at a clean EOF with NO `done` frame. The frontend clears `isStreaming` only
on a `done` frame / onError / disconnect, so a half-finished stream left the
simulator UI stuck "streaming" forever, input locked, no report. On a local
Ollama backend a mid-stream drop is a when-not-if, so the route generators now
catch the failure, announce it with an `event: error` frame, and ALWAYS fall
through to the terminal `done` frame.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import session_service as svc  # noqa: E402


_FAKE_STATE = {
    "session_id": "s1",
    "user_id": "test_user",  # ownership gate: caller (Bearer test_token) owns it
    "competency_node": "comm_02_describe_routine",
    "current_mastery": 0.7,
    "turn_count": 4,
    "last_route": "challenge",
    "last_eval_score": 1.0,
    "last_diagnosis": {"on_task": True, "english": True, "affect": "neutral"},
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(svc, "get_state", lambda sid: _FAKE_STATE)
    return TestClient(app)


def test_turn_stream_crash_still_emits_terminal_done(client, monkeypatch):
    async def _boom_run_turn(session_id, user_input):
        yield "half-a-thought"
        raise RuntimeError("local LLM dropped the connection mid-stream")

    monkeypatch.setattr(svc, "run_turn", _boom_run_turn)

    resp = client.post(
        "/session/turn",
        json={"session_id": "s1", "user_input": "hi"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert resp.status_code == 200
    body = resp.text
    # the partial token still reached the client ...
    assert "half-a-thought" in body
    # ... an explicit error frame announced the mid-stream failure ...
    assert "event: error" in body
    # ... and a terminal done frame ALWAYS closes the stream (releases the lock).
    assert "event: done" in body
    # the lock-releasing done frame is emitted AFTER the error frame, never before.
    assert body.rindex("event: done") > body.index("event: error")


def test_opening_stream_crash_still_emits_terminal_done(client, monkeypatch):
    async def _boom_opening(session_id):
        yield "opening-half"
        raise RuntimeError("local LLM dropped the connection mid-stream")

    monkeypatch.setattr(svc, "stream_opening", _boom_opening)

    resp = client.get(
        "/session/s1/opening",
        headers={"Authorization": "Bearer test_token"},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "opening-half" in body
    assert "event: error" in body
    assert "event: done" in body
    assert body.rindex("event: done") > body.index("event: error")
