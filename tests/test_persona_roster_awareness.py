"""P1 (Fix 1a) — GD personas are roster-aware so the panel cross-talks.

Before this, `build_persona_prompt` told a persona only the topic, the phase,
the transcript, and its own intent — it never named the OTHER participants or
their stances, so every voice spoke into a vacuum (parallel monologues aimed at
the learner). Now the full roster is threaded in and the persona is told to
engage the others by name. A one-voice interview roster adds nothing (the block
is empty), so interview turns are unchanged.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.ai.prompts import build_persona_prompt  # noqa: E402
from app.services.simulation import persona as persona_mod  # noqa: E402
from app.services.simulation.blackboard import new_blackboard  # noqa: E402


def _bb() -> dict:
    return new_blackboard("Is remote work good for teams?")


_ROSTER = [
    {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"},
    {"speaker_id": "gd_b", "name": "Meera", "stance": "strongly against"},
    {"speaker_id": "gd_c", "name": "Kabir", "stance": "pragmatic middle ground"},
]


# ---------- prompt-level: the OTHER voices are named, self is excluded ----------

def test_persona_prompt_names_the_other_panelists():
    speaker = _ROSTER[0]  # Aarav
    prompt = build_persona_prompt(
        speaker, "Press the learner.", "[Learner]: it depends.", _bb(), _ROSTER
    )
    # the two OTHER panelists are named with their stances ...
    assert "Meera" in prompt
    assert "Kabir" in prompt
    assert "strongly against" in prompt
    assert "pragmatic middle ground" in prompt
    # ... and the persona is told to engage them, not monologue
    lower = prompt.lower()
    assert "by name" in lower
    assert "real group" in lower


def test_persona_prompt_excludes_self_from_other_voices():
    speaker = _ROSTER[1]  # Meera
    prompt = build_persona_prompt(
        speaker, "Rebut the point.", "[Learner]: hello", _bb(), _ROSTER
    )
    others_block = prompt.split("Your goal for THIS turn")[0]
    # Meera must NOT be listed among the "other participants" block
    assert "- Meera (" not in others_block
    # the other two ARE listed there
    assert "- Aarav (" in others_block
    assert "- Kabir (" in others_block


def test_persona_prompt_no_roster_is_unchanged():
    speaker = _ROSTER[0]
    with_none = build_persona_prompt(speaker, "x", "[Learner]: hi", _bb())
    with_explicit_none = build_persona_prompt(
        speaker, "x", "[Learner]: hi", _bb(), None
    )
    assert with_none == with_explicit_none
    # no cross-talk block leaks in when there is no roster
    assert "other participants" not in with_none.lower()


def test_persona_prompt_single_voice_roster_adds_no_block():
    # a one-voice interview roster has no "others" -> block is empty, prompt
    # identical to passing no roster at all.
    interviewer = {"speaker_id": "interviewer", "name": "Interviewer", "role": "panel interviewer"}
    solo = [interviewer]
    with_solo = build_persona_prompt(interviewer, "Probe.", "[Learner]: hi", _bb(), solo)
    without = build_persona_prompt(interviewer, "Probe.", "[Learner]: hi", _bb())
    assert with_solo == without


# ---------- threading: stream_persona_turn forwards the roster to the prompt ----------

@pytest.mark.asyncio
async def test_stream_persona_turn_threads_roster_into_prompt(monkeypatch):
    captured: list = []

    async def fake_stream_generation(spec):
        captured.append(spec)
        yield "ok"

    monkeypatch.setattr(persona_mod, "stream_generation", fake_stream_generation)

    stream = persona_mod.stream_persona_turn(
        _ROSTER[0], "Press for a metric.", "[Learner]: fine", _bb(), _ROSTER
    )
    _ = [tok async for tok in stream]

    assert len(captured) == 1
    # the other panelists reached the rendered prompt -> cross-talk is possible
    assert "Meera" in captured[0].prompt
    assert "Kabir" in captured[0].prompt
