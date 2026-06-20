"""The /session/turn endpoint maps a SimulationState marker (emitted once per
round by the TEST-mode multi-persona simulation) to a discrete
`event: simulation_state` SSE frame on the same connection.

Mirrors tests/test_turn_sse_speaker.py: run_turn yields a single interleaved
sequence of markers + string tokens; the API maps each SimulationState to
`event: simulation_state` carrying `{turn, speaker_id, tension}` so the UI can
show round count and tension. The frame lands right after the speaker frame and
before that speaker's token stream.
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
from app.services.simulation_service import SimulationState, Speaker  # noqa: E402


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
        yield SimulationState(turn=3, speaker_id="gd_a", tension=0.45)
        yield "Remote work boosts output."

    monkeypatch.setattr(svc, "run_turn", _fake_run_turn)
    return TestClient(app)


def test_turn_emits_simulation_state_frame(client):
    resp = client.post(
        "/session/turn",
        json={"session_id": "s1", "user_input": "I think it depends."},
        headers={"Authorization": "Bearer test_token"},
    )
    assert resp.status_code == 200
    body = resp.text

    assert "event: simulation_state" in body
    assert '"turn": 3' in body
    assert '"speaker_id": "gd_a"' in body
    assert '"tension": 0.45' in body

    # the simulation_state frame lands after the speaker frame and before the
    # speaker's text tokens.
    speaker = body.index("event: speaker")
    sim_state = body.index("event: simulation_state")
    text = body.index("Remote work boosts output.")
    assert speaker < sim_state < text

    # the marker never leaks as a plain token / repr.
    assert "SimulationState(" not in body
