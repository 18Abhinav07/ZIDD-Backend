import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.ai import calls
from app.ai.calls import direct_simulation
from app.ai.schemas import DirectorDecision
from app.content.task_types import TaskType
from app.services.simulation.blackboard import new_blackboard

pytestmark = pytest.mark.asyncio


PERSONAS = [
    {"speaker_id": "gd_a", "name": "Aarav", "stance": "for"},
    {"speaker_id": "gd_b", "name": "Meera", "stance": "against"},
]


def _canned() -> DirectorDecision:
    return DirectorDecision(
        action="probe_deeper",
        next_speaker="gd_a",
        intent="x",
        tension=0.5,
        answer_quality=0.5,
        should_close=False,
    )


async def test_direct_simulation_local_path(monkeypatch):
    """Local backend routes through ollama_structured and wires the prompt."""
    bb = new_blackboard("Remote work")
    canned = _canned()
    captured = {}

    async def fake_ollama_structured(prompt, schema):
        captured["prompt"] = prompt
        captured["schema"] = schema
        return canned

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_ollama_structured)

    result = await direct_simulation(bb, PERSONAS, TaskType.GD_TEST, "transcript")

    assert result == canned
    assert captured["schema"] is DirectorDecision
    # Proves build_director_prompt was actually wired in.
    assert "Remote work" in captured["prompt"]
    assert "Aarav" in captured["prompt"]


async def test_direct_simulation_remote_path(monkeypatch):
    """Remote backend routes through get_gemini_client + call_with_structured_output."""
    bb = new_blackboard("Remote work")
    canned = _canned()
    captured = {}
    sentinel_client = object()

    async def fake_structured(client, prompt, schema):
        captured["client"] = client
        captured["prompt"] = prompt
        captured["schema"] = schema
        return canned

    monkeypatch.setattr(calls, "_local", lambda: False)
    monkeypatch.setattr(calls, "get_gemini_client", lambda: sentinel_client)
    monkeypatch.setattr(calls, "call_with_structured_output", fake_structured)

    result = await direct_simulation(bb, PERSONAS, TaskType.GD_TEST, "transcript")

    assert result == canned
    assert captured["client"] is sentinel_client
    assert captured["schema"] is DirectorDecision
    assert "Remote work" in captured["prompt"]
    assert "Meera" in captured["prompt"]
