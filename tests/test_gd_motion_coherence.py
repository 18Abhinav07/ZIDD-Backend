"""P0-4 — GD sim topic coherence: one concrete motion, shared verbatim.

The learner was briefed on one topic while the panel debated another, because
the opening and the persona/director prompts each invented a different motion
from the vague teach_focus seed. Now `sim_topic` is a CONCRETE motion stored once
and read verbatim by the opening, the director, and every persona.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.motions import GD_MOTIONS, motion_for_node  # noqa: E402
from app.content.registry import get_module, get_node  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402


# ---------- motion bank ----------

def test_motion_for_node_is_stable_and_in_bank():
    a = motion_for_node("gd_01_stake_position")
    b = motion_for_node("gd_01_stake_position")
    assert a == b                       # deterministic across calls (sha1, not hash())
    assert a in GD_MOTIONS


def test_every_gd_node_maps_to_a_concrete_motion():
    for node in get_module("group_discussion").nodes:
        motion = motion_for_node(node.id)
        assert motion in GD_MOTIONS
        # the motion is a debatable proposition, never the teaching instruction
        assert motion != node.teach_focus


# ---------- opening prompt briefs the exact motion ----------

def test_opening_prompt_briefs_motion_when_sim_topic_present():
    from app.ai.prompts import build_opening_prompt
    node = get_node("gd_01_stake_position")
    motion = motion_for_node(node.id)
    prompt = build_opening_prompt(node, "", sim_topic=motion)
    assert motion in prompt
    assert "motion under discussion" in prompt.lower()


def test_opening_prompt_generic_when_no_sim_topic():
    from app.ai.prompts import build_opening_prompt
    node = get_node("gd_01_stake_position")
    prompt = build_opening_prompt(node, "")
    assert "motion under discussion" not in prompt.lower()


# ---------- end-to-end: the briefed motion == the panel's motion ----------

pytestmark_async = pytest.mark.asyncio


class _Capture:
    def __init__(self):
        self.prompts: list[str] = []

    async def __call__(self, spec):
        self.prompts.append(spec.prompt)
        for tok in ("ok", " ", "done"):
            yield tok


@pytest.fixture
def cap(monkeypatch):
    c = _Capture()
    monkeypatch.setattr("app.services.session_service.stream_generation", c)
    yield c
    svc.SessionStore.clear()


async def _drain(agen):
    async for _ in agen:
        pass


@pytest.mark.asyncio
async def test_gd_opening_briefs_the_seeded_motion(cap):
    sid, state = await svc.start_session("gm1", "gd_01_stake_position", test_mode=True)
    motion = state["sim_topic"]
    assert motion in GD_MOTIONS

    await _drain(svc.stream_opening(sid))

    # the opening the learner hears briefs the SAME motion the panel will debate
    assert any(motion in p for p in cap.prompts)


@pytest.mark.asyncio
async def test_interview_opening_not_treated_as_gd_motion(cap):
    sid, state = await svc.start_session("gm2", "int_01_elevator_pitch", test_mode=True)
    await _drain(svc.stream_opening(sid))
    # interview opening keeps the generic framing, not the GD motion brief
    assert not any("motion under discussion" in p.lower() for p in cap.prompts)
