"""Phase 3.2 — TEST-mode multi-persona simulation.

The TEST behavior (interview_test / gd_test) runs a simulation: a SINGLE Ollama
call emits ALL persona turns in one streaming pass, persona-tagged
(`[Name]: ...`). The service parses those tags live and re-emits a discrete
`Speaker` marker as each tagged block begins, then streams that block's text —
so the UI renders distinct speaker bubbles without waiting for N serialized 14B
calls. These tests pin the incremental parser (the hard part: a tag may be split
across stream chunks) entirely offline.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import SimulationReport  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation_service import (  # noqa: E402
    Speaker,
    build_personas,
    score_session,
    split_persona_stream,
    stream_simulation_round,
)

pytestmark = pytest.mark.asyncio


_PERSONAS = [
    {"speaker_id": "p1", "name": "Aarav"},
    {"speaker_id": "p2", "name": "Meera"},
]


async def _feed(text: str, size: int = 3):
    """Yield `text` in small fixed-size chunks, so tags straddle chunk edges."""
    for i in range(0, len(text), size):
        yield text[i : i + size]


async def _collect(stream):
    out = []
    async for item in stream:
        out.append(item)
    return out


async def test_gd_test_emits_multiple_personas():
    raw = (
        "[Aarav]: I think remote work boosts productivity.\n"
        "[Meera]: I disagree, it isolates teams."
    )
    out = await _collect(split_persona_stream(_feed(raw), _PERSONAS))

    speakers = [i for i in out if isinstance(i, Speaker)]
    assert [s.speaker_id for s in speakers] == ["p1", "p2"]
    assert [s.name for s in speakers] == ["Aarav", "Meera"]


async def test_persona_tag_stripped_from_streamed_text():
    raw = "[Aarav]: Remote work helps.\n[Meera]: It can isolate teams."
    out = await _collect(split_persona_stream(_feed(raw), _PERSONAS))

    text = "".join(i for i in out if isinstance(i, str))
    # the bracketed speaker tags are consumed into Speaker markers, never leaked
    assert "[Aarav]" not in text
    assert "[Meera]" not in text
    assert "Remote work helps." in text
    assert "It can isolate teams." in text


async def test_text_attributed_to_correct_speaker_in_order():
    raw = "[Aarav]: First point.\n[Meera]: Second point."
    out = await _collect(split_persona_stream(_feed(raw), _PERSONAS))

    # Walk the stream; every text token belongs to the most recent Speaker.
    current = None
    said: dict[str, str] = {}
    for item in out:
        if isinstance(item, Speaker):
            current = item.speaker_id
        else:
            said[current] = said.get(current, "") + item
    assert "First point." in said["p1"]
    assert "Second point." in said["p2"]
    assert "Second point." not in said["p1"]


# ---- roster + round runner (single-pass, AI boundary patched) ----------------


def _chunked(text: str, size: int = 4):
    async def gen(spec):
        for i in range(0, len(text), size):
            yield text[i : i + size]

    return gen


async def test_gd_test_roster_has_distinct_named_personas():
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    names = [p["name"] for p in personas]
    assert len(personas) >= 2
    assert len(set(names)) == len(names)              # distinct names
    assert all(p["speaker_id"] for p in personas)     # every persona addressable
    assert all(p.get("stance") for p in personas)     # GD voices carry a stance


async def test_interview_test_roster_is_interviewer():
    personas = build_personas(TaskType.INTERVIEW_TEST, "Backend role")
    assert len(personas) >= 1
    assert all(p["speaker_id"] for p in personas)


async def test_gd_test_round_streams_tagged_personas(monkeypatch):
    personas = build_personas(TaskType.GD_TEST, "Remote work")
    a, b = personas[0]["name"], personas[1]["name"]
    script = f"[{a}]: Remote work boosts output.\n[{b}]: It isolates teams."
    monkeypatch.setattr(sim, "stream_generation", _chunked(script))

    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Remote work",
        "messages": [],
        "user_input": "I think it depends on the team.",
    }
    out = await _collect(stream_simulation_round(state))

    speakers = [i for i in out if isinstance(i, Speaker)]
    assert [s.name for s in speakers] == [a, b]
    text = "".join(i for i in out if isinstance(i, str))
    assert f"[{a}]" not in text and f"[{b}]" not in text
    assert "Remote work boosts output." in text


async def test_round_persists_roster_in_state(monkeypatch):
    monkeypatch.setattr(sim, "stream_generation", _chunked("[X]: hi."))
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Topic",
        "messages": [],
        "user_input": "ok",
    }
    await _collect(stream_simulation_round(state))
    # roster fixed once per session so speaker_ids stay stable across rounds
    assert state.get("personas")
    again = build_personas(TaskType.GD_TEST, "Topic")
    assert [p["speaker_id"] for p in state["personas"]] == [
        p["speaker_id"] for p in again
    ]


async def test_round_prompt_carries_topic_and_personas(monkeypatch):
    captured = {}

    def fake(spec):
        captured["spec"] = spec

        async def gen():
            yield "[Z]: hi."

        return gen()

    monkeypatch.setattr(sim, "stream_generation", fake)
    personas = build_personas(TaskType.GD_TEST, "Climate policy")
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Climate policy",
        "messages": [],
        "user_input": "We should act now.",
    }
    await _collect(stream_simulation_round(state))

    prompt = captured["spec"].prompt
    assert "Climate policy" in prompt
    for p in personas:
        assert p["name"] in prompt
    # learner's latest contribution is in the prompt so personas react to it
    assert "We should act now." in prompt


# ---- scoring at end (test sessions scored, not coached mid-stream) -----------


async def test_round_does_not_score_midstream(monkeypatch):
    monkeypatch.setattr(
        sim, "stream_generation", _chunked("[Aarav]: point.\n[Meera]: counter.")
    )
    state = {
        "task_type": TaskType.GD_TEST.value,
        "sim_topic": "Topic",
        "messages": [],
        "user_input": "ok",
    }
    out = await _collect(stream_simulation_round(state))
    # only speaker markers + text mid-stream; never a score/report
    assert all(isinstance(i, (Speaker, str)) for i in out)
    assert not any(isinstance(i, SimulationReport) for i in out)


async def test_interview_test_scores_at_end(monkeypatch):
    captured = {}

    async def fake_eval(task_type, topic, messages):
        captured["args"] = (task_type, topic, messages)
        return SimulationReport(
            score=0.72,
            summary="Structured, concrete answers.",
            strengths=["clear ownership"],
            improvements=["quantify impact"],
        )

    monkeypatch.setattr(sim, "evaluate_simulation", fake_eval)
    state = {
        "task_type": TaskType.INTERVIEW_TEST.value,
        "sim_topic": "Backend role",
        "messages": [{"role": "user", "content": "I led a DB migration."}],
    }
    report = await score_session(state)

    assert isinstance(report, SimulationReport)
    assert report.score == 0.72
    assert report.improvements
    tt, topic, msgs = captured["args"]
    assert tt == TaskType.INTERVIEW_TEST
    assert topic == "Backend role"
    assert msgs == state["messages"]
