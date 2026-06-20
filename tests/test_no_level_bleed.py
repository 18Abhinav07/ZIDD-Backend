"""Phase 0.1 — kill level-bleed.

When an answer advances the learner to a new node, run_turn streams the OLD
node's feedback and then emits a discrete `NodeAdvance` marker (carried as an
`event: node_advance` SSE frame) so the two messages render as separate bubbles.
Under the two-step opening contract the advance turn STOPS there — it does not
stream the new node's opening. The frontend shows a "Next Skill" break and
fetches the opening via a separate `GET /session/{id}/opening` (stream_opening)
call, so the new-node opening can never bleed into the old node's feedback.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio


class _Scores:
    def __init__(self, scores):
        self._it = iter(scores)

    async def __call__(self, node, messages, user_input, behavior=None):
        score = next(self._it)
        return DiagnosisEval(
            score=score,
            understanding="x",
            errors=[] if score >= 0.6 else ["e"],
            strengths=["s"] if score >= 0.6 else [],
            next_focus="n",
            on_task=True,
            english=True,
            affect="neutral",
        )


async def _fake_stream(spec):
    # Distinct token per kind so we can tell old-node pedagogy from new opening.
    tag = "OPEN" if spec.kind == "opening" else "FEEDBACK"
    for tok in (tag, "-tok"):
        yield tok


@pytest.fixture(autouse=True)
def _patch_ai(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer", None, raising=False
    )
    monkeypatch.setattr("app.services.session_service.stream_generation", _fake_stream)
    yield
    svc.SessionStore.clear()


def _set_eval(monkeypatch, scores):
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer", _Scores(scores)
    )


async def test_advance_turn_emits_node_advance_marker(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])
    sid, state = await svc.start_session("lb1", "comm_01_self_intro")
    state["turn_count"] = 1

    # first pass: no advance yet — no NodeAdvance marker.
    # (ProgressUpdate and other typed frames are fine on non-advance turns.)
    first = [t async for t in svc.run_turn(sid, "pass one")]
    assert not any(isinstance(t, svc.NodeAdvance) for t in first)

    # second pass: advances comm_01 -> comm_02 mid-turn.
    yielded = [t async for t in svc.run_turn(sid, "pass two")]

    markers = [t for t in yielded if isinstance(t, svc.NodeAdvance)]
    assert len(markers) == 1, "advance turn must emit exactly one NodeAdvance marker"
    marker = markers[0]
    assert marker.from_node == "comm_01_self_intro"
    assert marker.to_node == "comm_02_describe_routine"

    idx = yielded.index(marker)
    before = [t for t in yielded[:idx] if isinstance(t, str)]
    after = [t for t in yielded[idx + 1:] if isinstance(t, str)]
    # old-node feedback precedes the marker...
    assert any("FEEDBACK" in t for t in before)
    # ...and under the two-step opening contract the new-node opening does NOT
    # bleed into the advance turn at all (not before, not after the marker).
    assert not any("OPEN" in t for t in before)
    assert not any("OPEN" in t for t in after)

    # the opening arrives only from a separate /opening (stream_opening) call.
    opening = [t async for t in svc.stream_opening(sid) if isinstance(t, str)]
    assert any("OPEN" in t for t in opening)


async def test_non_advance_turn_emits_no_marker(monkeypatch):
    _set_eval(monkeypatch, [0.5])
    sid, state = await svc.start_session("lb2", "comm_01_self_intro")
    state["turn_count"] = 1

    yielded = [t async for t in svc.run_turn(sid, "half answer")]
    assert not any(isinstance(t, svc.NodeAdvance) for t in yielded)
