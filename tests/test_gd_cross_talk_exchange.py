"""P1 (Fix 1b) — GD rounds schedule a 2-3 persona exchange (real cross-talk).

Before this, a TEST round streamed exactly ONE persona, so a group discussion was
just a chain of 1-on-1s with the learner — the panel never argued with itself. Now
a GD round opens single-voice (don't dogpile the learner's first contribution),
then as the discussion heats up the Director's chosen speaker is followed by a
bounded, deterministic set of REACTORS — each a different voice, each told to
engage the previous speaker by name. Reactors use note_turn only, so they never
inflate the round counter that drives the hard MAX_SIM_ROUNDS cap. Interview
(one interviewer) never cross-talks.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.ai.schemas import DirectorDecision  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import simulation_service as sim  # noqa: E402
from app.services.simulation import director as director_mod  # noqa: E402
from app.services.simulation.blackboard import new_blackboard  # noqa: E402
from app.services.simulation_service import (  # noqa: E402
    SimulationState,
    Speaker,
    _GD_PANEL,
    _extra_speakers,
    _reactor_intent,
    _reactor_pool,
)
from app.services.simulation.director import _next_in_rotation  # noqa: E402


# ---------------- pure scheduling helpers ----------------

@pytest.mark.parametrize(
    "phase,expected",
    [("opening", 0), ("probing", 1), ("pressure", 2), ("winddown", 0), ("weird", 1)],
)
def test_extra_speakers_by_phase_for_gd(phase, expected):
    assert _extra_speakers(phase, False, TaskType.GD_TEST) == expected


def test_extra_speakers_zero_when_closing():
    assert _extra_speakers("pressure", True, TaskType.GD_TEST) == 0


def test_extra_speakers_zero_for_interview():
    assert _extra_speakers("pressure", False, TaskType.INTERVIEW_TEST) == 0


def test_reactor_intent_names_previous_speaker_and_is_cross_talk():
    intent = _reactor_intent("Aarav")
    assert "Aarav" in intent
    assert "cross-talk" in intent.lower()
    assert "learner" in intent.lower()  # explicitly NOT a reply to the learner


# ---------------- reactor pool excludes the Moderator ----------------

def test_reactor_pool_drops_the_moderator():
    ids = [p["speaker_id"] for p in _reactor_pool(_GD_PANEL)]
    assert ids == ["gd_a", "gd_b", "gd_c"]
    assert "moderator" not in ids


def test_reactor_after_last_debater_rotates_to_a_debater_not_the_moderator():
    # The bug this guards: with the full roster, a reactor following the LAST
    # debater (gd_c) wrapped round-robin to personas[0] == the Moderator, so the
    # neutral facilitator "jumped in" to argue. The debater-only pool wraps to
    # the first debater instead, and no last_speaker can ever yield the Moderator.
    pool = _reactor_pool(_GD_PANEL)
    assert _next_in_rotation(pool, "gd_c") == "gd_a"
    for last in ("moderator", "gd_a", "gd_b", "gd_c", ""):
        assert _next_in_rotation(pool, last) != "moderator"


def test_reactor_pool_falls_back_when_only_a_moderator_remains():
    # _next_in_rotation rejects an empty roster; a degenerate moderator-only
    # roster must fall back to itself rather than raise.
    only_mod = [{"speaker_id": "moderator", "name": "Moderator", "stance": "x"}]
    assert _reactor_pool(only_mod) == only_mod


# ---------------- integration over stream_simulation_round ----------------

def _seed_state(task_type: str, *, phase: str | None) -> dict:
    bb = None
    if phase is not None:
        bb = new_blackboard("Is remote work good for teams?")
        bb["phase"] = phase
        bb["turn"] = 3  # mid-session; proves reactors don't bump the cap counter
    return {
        "task_type": task_type,
        "messages": [{"role": "user", "content": "I think it depends."}],
        "sim_topic": "Is remote work good for teams?",
        "personas": None,
        "blackboard": bb,
        "probe_items": [],
        "session_over": False,
    }


@pytest.fixture
def patched(monkeypatch):
    captured: list[tuple[str, str]] = []  # (speaker_name, intent)

    async def _direct(bb, personas, task_type, transcript, probe_items=None):
        # primary = personas[1] (gd_a/Aarav for GD; only interviewer for interview)
        primary = personas[1]["speaker_id"] if len(personas) > 1 else personas[0]["speaker_id"]
        return DirectorDecision(
            action="escalate_pressure",
            next_speaker=primary,
            intent="Press the learner's claim.",
            tension=0.7,
            answer_quality=0.5,
            should_close=False,
        )

    monkeypatch.setattr(director_mod, "direct_simulation", _direct)

    async def _persona(persona, intent, transcript, bb, roster=None):
        captured.append((persona["name"], intent))
        yield f"[{persona['name']} speaks]"

    monkeypatch.setattr(sim, "stream_persona_turn", _persona)
    return captured


async def _collect(state):
    return [item async for item in sim.stream_simulation_round(state)]


@pytest.mark.asyncio
async def test_gd_pressure_round_schedules_three_distinct_speakers(patched):
    state = _seed_state(TaskType.GD_TEST.value, phase="pressure")
    out = await _collect(state)

    speakers = [t for t in out if isinstance(t, Speaker)]
    ids = [s.speaker_id for s in speakers]
    # 1 primary + 2 reactors = 3 voices, ALL different (no spam, real cross-talk)
    assert len(speakers) == 3
    assert len(set(ids)) == 3
    assert ids[0] == "gd_a"            # Director's primary pick
    # exactly ONE round snapshot regardless of how many voices spoke
    assert len([t for t in out if isinstance(t, SimulationState)]) == 1


@pytest.mark.asyncio
async def test_gd_reactors_engage_the_previous_speaker_by_name(patched):
    state = _seed_state(TaskType.GD_TEST.value, phase="pressure")
    await _collect(state)

    names_intents = patched
    # primary spoke first with the Director's intent
    assert names_intents[0][1] == "Press the learner's claim."
    # reactor 1 was told to engage the PRIMARY (Aarav) by name ...
    assert "Aarav" in names_intents[1][1]
    # ... reactor 2 to engage reactor 1 (Meera) by name -> a genuine chain
    assert "Meera" in names_intents[2][1]


@pytest.mark.asyncio
async def test_gd_opening_round_is_single_voice(patched):
    # fresh blackboard -> phase "opening" -> ease the learner in with one voice
    state = _seed_state(TaskType.GD_TEST.value, phase=None)
    out = await _collect(state)
    assert len([t for t in out if isinstance(t, Speaker)]) == 1


@pytest.mark.asyncio
async def test_interview_never_cross_talks_even_under_pressure(patched):
    state = _seed_state(TaskType.INTERVIEW_TEST.value, phase="pressure")
    out = await _collect(state)
    assert len([t for t in out if isinstance(t, Speaker)]) == 1


@pytest.mark.asyncio
async def test_reactors_do_not_inflate_the_round_counter(patched):
    # seeded turn=3; one apply_decision -> 4. Reactors use note_turn (no ++turn),
    # so the cap counter advances by exactly ONE despite 3 voices speaking.
    state = _seed_state(TaskType.GD_TEST.value, phase="pressure")
    await _collect(state)
    assert state["blackboard"]["turn"] == 4
    # last_speaker advanced through the whole chain to the final reactor
    assert state["blackboard"]["last_speaker"] == "gd_c"


@pytest.mark.asyncio
async def test_reactor_is_never_the_moderator_when_primary_is_last_debater(monkeypatch):
    # End-to-end guard: the Director picks the LAST debater (gd_c) as the primary
    # speaker. The follow-up reactors must rotate within the debaters and never
    # land on the Moderator (the pre-fix round-robin wrapped gd_c -> moderator).
    async def _direct(bb, personas, task_type, transcript, probe_items=None):
        return DirectorDecision(
            action="escalate_pressure",
            next_speaker="gd_c",
            intent="Press the learner's claim.",
            tension=0.7,
            answer_quality=0.5,
            should_close=False,
        )

    monkeypatch.setattr(director_mod, "direct_simulation", _direct)

    async def _persona(persona, intent, transcript, bb, roster=None):
        yield f"[{persona['name']} speaks]"

    monkeypatch.setattr(sim, "stream_persona_turn", _persona)

    state = _seed_state(TaskType.GD_TEST.value, phase="pressure")
    out = await _collect(state)
    ids = [s.speaker_id for s in out if isinstance(s, Speaker)]
    assert ids[0] == "gd_c"                 # Director's primary pick honored
    assert "moderator" not in ids           # no facilitator jumping into cross-talk
    assert len(set(ids)) == len(ids)        # still all-distinct voices
