"""Phase 0.1 — the /session/turn endpoint maps a NodeAdvance marker to a
discrete `event: node_advance` SSE frame on the same connection, with string
tokens still emitted as plain `data:` (message) frames before/after it.
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

from app.api import routes  # noqa: E402
from app.main import app  # noqa: E402
from app.services import session_service as svc  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    fake_state = {
        "session_id": "s1",
        "user_id": "test_user",  # ownership gate: caller (Bearer test_token) owns it
        "competency_node": "comm_02_describe_routine",
        "current_mastery": 0.7,
        "turn_count": 4,
        "last_route": "challenge",
        "last_eval_score": 1.0,
        "last_diagnosis": {"on_task": True, "english": True, "affect": "neutral"},
    }
    monkeypatch.setattr(svc, "get_state", lambda sid: fake_state)

    async def _fake_run_turn(session_id, user_input):
        yield "feedback-tok"
        yield svc.NodeAdvance(
            from_node="comm_01_self_intro", to_node="comm_02_describe_routine"
        )
        yield "opening-tok"

    monkeypatch.setattr(svc, "run_turn", _fake_run_turn)
    return TestClient(app)


def test_turn_emits_node_advance_frame(client):
    resp = client.post(
        "/session/turn",
        json={"session_id": "s1", "user_input": "hi"},
        headers={"Authorization": "Bearer test_token"},
    )
    assert resp.status_code == 200
    body = resp.text

    assert "event: node_advance" in body
    assert '"from_node": "comm_01_self_intro"' in body
    assert '"to_node": "comm_02_describe_routine"' in body

    # ordering: feedback message precedes the node_advance frame; opening follows.
    adv = body.index("event: node_advance")
    assert body.index("feedback-tok") < adv
    assert body.index("opening-tok") > adv
