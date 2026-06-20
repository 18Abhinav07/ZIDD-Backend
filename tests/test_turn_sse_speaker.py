"""Phase 3.2 — the /session/turn endpoint maps a Speaker marker (emitted by the
TEST-mode multi-persona simulation) to a discrete `event: speaker` SSE frame on
the same connection, with each persona's text still streamed as plain `data:`
(message) frames after its speaker frame.

Mirrors the NodeAdvance wiring: run_turn yields a single interleaved sequence of
markers + string tokens; the API maps each Speaker to `event: speaker` carrying
`{speaker_id, name}` so the UI opens a new speaker bubble before the text lands.
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
from app.services.simulation_service import Speaker  # noqa: E402


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
        yield Speaker(speaker_id="gd_a", name="Aarav")
        yield "Remote work boosts output."
        yield Speaker(speaker_id="gd_b", name="Meera")
        yield "It isolates teams."

    monkeypatch.setattr(svc, "run_turn", _fake_run_turn)
    return TestClient(app)


def test_turn_emits_speaker_frames(client):
    resp = client.post(
        "/session/turn",
        json={"session_id": "s1", "user_input": "I think it depends."},
        headers={"Authorization": "Bearer test_token"},
    )
    assert resp.status_code == 200
    body = resp.text

    assert "event: speaker" in body
    assert '"speaker_id": "gd_a"' in body
    assert '"name": "Aarav"' in body
    assert '"speaker_id": "gd_b"' in body
    assert '"name": "Meera"' in body

    # each speaker frame precedes its own text; tags never leak as plain tokens.
    a = body.index('"name": "Aarav"')
    b = body.index('"name": "Meera"')
    assert a < body.index("Remote work boosts output.") < b
    assert b < body.index("It isolates teams.")
    assert "[Aarav]" not in body
