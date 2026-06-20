import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)
import pytest

pytestmark = pytest.mark.asyncio

from app.ai.calls import GEMINI_FLASH
from app.services.simulation import persona as persona_mod
from app.services.simulation.blackboard import new_blackboard


async def test_stream_persona_turn_wires_spec_and_streams(monkeypatch):
    captured: list = []

    async def fake_stream_generation(spec):
        captured.append(spec)
        yield "Hello"
        yield " there"

    monkeypatch.setattr(persona_mod, "stream_generation", fake_stream_generation)

    stream = persona_mod.stream_persona_turn(
        {"speaker_id": "gd_a", "name": "Aarav", "stance": "for"},
        "Press for a metric.",
        "[Learner]: remote work is fine",
        new_blackboard("Remote work"),
    )

    tokens = [tok async for tok in stream]

    assert tokens == ["Hello", " there"]
    assert len(captured) == 1
    spec = captured[0]
    assert spec.kind == "simulation"
    assert spec.model == GEMINI_FLASH
    assert "Aarav" in spec.prompt
    assert "Press for a metric." in spec.prompt
    assert "Remote work" in spec.prompt
