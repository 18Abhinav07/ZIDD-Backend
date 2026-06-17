"""Phase 3.2 — end_session scores TEST-mode simulations via score_session.

Coaching ("prep") sessions summarise the transcript (summarize_session). Assessment
("test") sessions are NOT coached mid-stream; their whole transcript is scored once
at close via score_session -> evaluate_simulation, and that report's summary is the
session's closing summary. Fully offline: the AI boundary is patched; storage is
best-effort no-op.
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
from app.services import session_service as svc  # noqa: E402
from app.services import simulation_service as sim  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_NODE = "gd_01_stake_position"


def _seed(task_type: str) -> str:
    sid = "end-sim-1"
    svc.SessionStore[sid] = {
        "user_id": "u1",
        "session_id": sid,
        "competency_node": GD_NODE,
        "task_type": task_type,
        "sim_topic": "Is remote work good for teams?",
        "current_mastery": 0.0,
        "messages": [
            {"role": "user", "content": "I think it depends on the team."},
            {"role": "assistant", "content": "Remote work boosts output."},
        ],
    }
    return sid


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    calls = {"scored": 0, "summarized": 0}

    async def _eval(task_type, topic, messages):
        calls["scored"] += 1
        return SimulationReport(
            score=0.82,
            summary="Strong, well-structured contribution under pressure.",
            strengths=["clear stance"],
            improvements=["cite an example"],
        )

    async def _sum(node, messages):
        calls["summarized"] += 1
        return "generic coaching summary"

    monkeypatch.setattr(sim, "evaluate_simulation", _eval)
    monkeypatch.setattr(svc, "summarize_session", _sum)
    yield calls
    svc.SessionStore.clear()


async def test_test_session_close_scored_via_simulation(_patch):
    sid = _seed(TaskType.GD_TEST.value)
    summary = await svc.end_session(sid)
    assert _patch["scored"] == 1
    assert _patch["summarized"] == 0
    assert summary == "Strong, well-structured contribution under pressure."


async def test_prep_session_close_still_summarized(_patch):
    sid = _seed(TaskType.GD_PREP.value)
    summary = await svc.end_session(sid)
    assert _patch["scored"] == 0
    assert _patch["summarized"] == 1
    assert summary == "generic coaching summary"
