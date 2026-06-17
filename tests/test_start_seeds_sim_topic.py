"""Phase 3.2 — a TEST-mode session is seeded with a sim_topic and a personas slot.

The simulation round runner reads state["sim_topic"] (rides in the prompt) and
caches state["personas"] across rounds. start_session must seed both for an
assessment session so the very first turn streams a coherent panel. A PREP
session carries no sim_topic (it runs the coaching graph, not a simulation).

Offline: storage is best-effort no-op; no AI is exercised by start_session.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.registry import get_node  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"


@pytest.fixture(autouse=True)
def _clear():
    svc.SessionStore.clear()
    yield
    svc.SessionStore.clear()


async def test_test_mode_seeds_sim_topic_and_personas_slot():
    _, state = await svc.start_session("u1", GD_NODE, test_mode=True)
    assert state["task_type"] == TaskType.GD_TEST.value
    # a non-empty topic derived from the node so the panel has something to debate
    assert isinstance(state["sim_topic"], str) and state["sim_topic"].strip()
    assert get_node(GD_NODE).teach_focus in state["sim_topic"] or \
        get_node(GD_NODE).title in state["sim_topic"]
    # personas slot exists, unfilled until the first round builds the roster
    assert state["personas"] is None


async def test_prep_mode_has_no_sim_topic():
    _, state = await svc.start_session("u1", GD_NODE, test_mode=False)
    assert state["task_type"] == TaskType.GD_PREP.value
    assert state["sim_topic"] == ""
    assert state["personas"] is None
