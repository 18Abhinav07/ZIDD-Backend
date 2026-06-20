"""P0-1 — close_session returns the full scored simulation report.

The streamed TEST-mode rounds defer all feedback to the end; score_session then
produces a SimulationReport with five rubric sub-scores plus strengths and
improvements. The /end route previously returned only the one-line `summary`, so
that whole report was computed and then discarded — no numeric score ever
reached the learner. close_session must now surface the full report dict, while
the end_session back-compat wrapper still returns just the summary string.

Fully offline: the AI boundary is patched; storage is best-effort no-op.
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


def _seed(task_type: str, sid: str = "close-sim-1") -> str:
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
    async def _eval(task_type, topic, messages):
        return SimulationReport(
            score=0.82,
            summary="Strong, well-structured contribution under pressure.",
            strengths=["clear stance", "stayed composed"],
            improvements=["cite an example"],
            participation_score=0.8,
            relevance_score=0.75,
            language_score=0.7,
        )

    async def _sum(node, messages):
        return "generic coaching summary"

    monkeypatch.setattr(sim, "evaluate_simulation", _eval)
    monkeypatch.setattr(svc, "summarize_session", _sum)
    yield
    svc.SessionStore.clear()


async def test_close_session_returns_full_report_for_test():
    sid = _seed(TaskType.GD_TEST.value)
    result = await svc.close_session(sid)

    assert result["summary"] == "Strong, well-structured contribution under pressure."
    assert result["score"] == pytest.approx(0.82)

    report = result["report"]
    assert report is not None, "TEST session must surface the scored report"
    # The five rubric sub-scores + strengths + improvements all survive to the caller.
    assert report["score"] == pytest.approx(0.82)
    assert report["participation_score"] == pytest.approx(0.8)
    assert report["relevance_score"] == pytest.approx(0.75)
    assert report["language_score"] == pytest.approx(0.7)
    assert report["strengths"] == ["clear stance", "stayed composed"]
    assert report["improvements"] == ["cite an example"]
    # session closed out
    assert svc.get_state(sid) is None


async def test_close_session_no_report_for_prep():
    sid = _seed(TaskType.GD_PREP.value)
    result = await svc.close_session(sid)

    assert result["summary"] == "generic coaching summary"
    assert result["report"] is None  # coaching sessions are summarised, not scored


async def test_end_session_wrapper_still_returns_summary_string():
    """The bare-string contract the scripts/older tests depend on is preserved."""
    sid = _seed(TaskType.GD_TEST.value)
    summary = await svc.end_session(sid)
    assert summary == "Strong, well-structured contribution under pressure."
    assert isinstance(summary, str)


async def test_close_session_missing_session_is_inert():
    result = await svc.close_session("does-not-exist")
    assert result == {"summary": "", "report": None, "score": 0.0}
