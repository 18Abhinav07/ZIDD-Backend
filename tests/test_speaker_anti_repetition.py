"""P1 (Fix 2) — speaker anti-repetition: rotate the floor, don't spam one voice.

The Director picks who speaks each round, but a degraded round (LLM failure or a
hallucinated speaker_id) used to default to `personas[0]` — the Moderator in the
GD roster — so every fallback round handed the floor straight back to the same
voice and the panel read as the Moderator talking to itself.

Now the Blackboard tracks `last_speaker`, the Director prompt is told who spoke
last and to rotate, and BOTH degraded paths (`_fallback_decision`, an invalid
`_snap_speaker`) round-robin off the last speaker instead of pinning personas[0].
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.ai.prompts import build_director_prompt  # noqa: E402
from app.ai.schemas import DirectorDecision  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services.simulation import director as director_mod  # noqa: E402
from app.services.simulation.blackboard import (  # noqa: E402
    apply_decision,
    new_blackboard,
    note_turn,
)
from app.services.simulation.director import (  # noqa: E402
    _fallback_decision,
    _next_in_rotation,
    _snap_speaker,
    decide_round,
)

# The real GD roster shape: Moderator FIRST — the exact source of the spam bug.
_GD = [
    {"speaker_id": "moderator", "name": "Moderator", "stance": "neutral facilitator"},
    {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"},
    {"speaker_id": "gd_b", "name": "Meera", "stance": "strongly against"},
    {"speaker_id": "gd_c", "name": "Kabir", "stance": "pragmatic middle ground"},
]


# ---------- blackboard tracks last_speaker ----------

def test_new_blackboard_last_speaker_empty():
    assert new_blackboard("T")["last_speaker"] == ""


def test_note_turn_sets_last_speaker():
    bb = new_blackboard("T")
    assert note_turn(bb, "gd_b", "my point")["last_speaker"] == "gd_b"


def test_apply_decision_carries_last_speaker():
    bb = note_turn(new_blackboard("T"), "gd_a", "x")  # last_speaker -> gd_a
    decision = DirectorDecision(
        action="probe_deeper", next_speaker="gd_b", intent="i",
        tension=0.4, answer_quality=0.5, should_close=False,
    )
    # apply_decision does NOT itself rotate; note_turn is what advances the
    # speaker, so apply_decision must carry the prior last_speaker through.
    assert apply_decision(bb, decision)["last_speaker"] == "gd_a"


# ---------- _next_in_rotation primitive ----------

def test_rotation_advances_one_step():
    assert _next_in_rotation(_GD, "moderator") == "gd_a"
    assert _next_in_rotation(_GD, "gd_a") == "gd_b"
    assert _next_in_rotation(_GD, "gd_b") == "gd_c"


def test_rotation_wraps_around():
    assert _next_in_rotation(_GD, "gd_c") == "moderator"


def test_rotation_empty_last_opens_with_first():
    assert _next_in_rotation(_GD, "") == "moderator"


def test_rotation_unknown_last_opens_with_first():
    assert _next_in_rotation(_GD, "ghost") == "moderator"


def test_rotation_empty_roster_raises():
    with pytest.raises(ValueError):
        _next_in_rotation([], "gd_a")


# ---------- _fallback_decision rotates instead of spamming personas[0] ----------

def test_fallback_after_moderator_is_not_moderator_again():
    bb = note_turn(new_blackboard("T"), "moderator", "framing")  # last = moderator
    dd = _fallback_decision(bb, _GD)
    assert dd.next_speaker == "gd_a"          # rotated, NOT moderator again


def test_fallback_first_round_opens_with_first_persona():
    # fresh blackboard (no last_speaker) keeps the old open-with-first behavior
    dd = _fallback_decision(new_blackboard("T"), _GD)
    assert dd.next_speaker == "moderator"


def test_fallback_walks_the_panel_across_degraded_rounds():
    # simulate 3 consecutive degraded rounds; the floor must move each time
    bb = new_blackboard("T")
    seen = []
    for _ in range(3):
        spk = _fallback_decision(bb, _GD).next_speaker
        seen.append(spk)
        bb = note_turn(bb, spk, "...")        # record who just spoke
    assert seen == ["moderator", "gd_a", "gd_b"]
    assert len(set(seen)) == 3                # never the same voice twice


# ---------- _snap_speaker: honor valid, rotate invalid ----------

def test_snap_valid_pick_honored_even_if_repeat():
    # a deliberate Director repeat is allowed (it may have a reason)
    assert _snap_speaker("moderator", _GD, last_speaker="moderator") == "moderator"


def test_snap_invalid_pick_rotates_off_last_speaker():
    assert _snap_speaker("hallucinated", _GD, last_speaker="gd_a") == "gd_b"


def test_snap_invalid_pick_no_last_speaker_snaps_first():
    # back-compat: no last_speaker arg -> old personas[0] behavior
    assert _snap_speaker("hallucinated", _GD) == "moderator"


# ---------- director prompt surfaces the last speaker ----------

def _bb_with_last(last: str) -> dict:
    bb = new_blackboard("Remote work")
    bb["last_speaker"] = last
    return bb


def test_director_prompt_names_last_speaker_and_says_rotate():
    prompt = build_director_prompt(
        _bb_with_last("gd_a"), _GD, TaskType.GD_TEST, "[Learner]: hi"
    )
    assert "Last voice to speak: Aarav" in prompt
    assert "speaker_id=gd_a" in prompt
    lower = prompt.lower()
    assert "rotate" in lower
    assert "two turns running" in lower or "same speaker" in lower


def test_director_prompt_first_round_says_no_one_yet():
    prompt = build_director_prompt(
        new_blackboard("Remote work"), _GD, TaskType.GD_TEST, "[Learner]: hi"
    )
    assert "No one has spoken yet" in prompt


# ---------- integration: decide_round rotates on a Director failure ----------

@pytest.mark.asyncio
async def test_decide_round_fallback_rotates_off_last_speaker(monkeypatch):
    async def _boom(*a, **k):
        raise RuntimeError("director down")

    monkeypatch.setattr(director_mod, "direct_simulation", _boom)

    bb = note_turn(new_blackboard("T"), "moderator", "framing")  # last = moderator
    new_bb, persona, decision = await decide_round(
        bb, _GD, TaskType.GD_TEST, "[Learner]: hi"
    )
    # the failed round must NOT hand the floor back to the Moderator
    assert persona["speaker_id"] == "gd_a"
    assert decision.next_speaker == "gd_a"
    # decide_round only decides/snaps — note_turn (later, in the round runner)
    # is what advances last_speaker, so apply_decision carries the prior value
    # through unchanged here.
    assert new_bb["last_speaker"] == "moderator"
