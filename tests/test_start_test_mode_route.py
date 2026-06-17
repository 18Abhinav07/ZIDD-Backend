"""Phase 3.2 — POST /session/start accepts a `test_mode` flag and threads it
into start_session so the session opens on the assessment TaskType variant.

The UI flips this when a learner chooses to be tested (vs. coached) on an
interview/GD node. Storage/AI are not exercised here; the route's call into
start_session is captured to assert the flag propagates and defaults to False.
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

INT_NODE = "int_01_elevator_pitch"


@pytest.fixture
def captured(monkeypatch):
    calls: list[dict] = []

    async def _fake_start(user_id, node_id, learner_name="", test_mode=False):
        calls.append(
            {
                "user_id": user_id,
                "node_id": node_id,
                "test_mode": test_mode,
            }
        )
        state = {
            "session_id": "s1",
            "competency_node": node_id,
            "current_mastery": 0.0,
        }
        return "s1", state

    monkeypatch.setattr(svc, "start_session", _fake_start)
    return calls


def test_start_threads_test_mode_true(captured):
    client = TestClient(app)
    resp = client.post(
        "/session/start",
        json={"user_id": "u1", "competency_node": INT_NODE, "test_mode": True},
    )
    assert resp.status_code == 200
    assert captured[0]["test_mode"] is True


def test_start_defaults_test_mode_false(captured):
    client = TestClient(app)
    resp = client.post(
        "/session/start",
        json={"user_id": "u1", "competency_node": INT_NODE},
    )
    assert resp.status_code == 200
    assert captured[0]["test_mode"] is False
