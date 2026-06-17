"""Phase 0.1 — kill level-bleed.

When an answer advances the learner to a new node, run_turn used to stream the
OLD-node feedback and the NEW-node opening as one undifferentiated run of
string tokens, so the UI rendered both in a single bubble. Fix: emit a discrete
`NodeAdvance` marker between them (carried as an `event: node_advance` SSE frame
on the same connection) so the two messages render as separate bubbles.
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

    async def __call__(self, node, messages, user_input):
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
    # old-node feedback precedes the marker; new-node opening follows it.
    assert any("FEEDBACK" in t for t in before)
    assert any("OPEN" in t for t in after)
    # and the opening must NOT bleed in before the marker.
    assert not any("OPEN" in t for t in before)


async def test_non_advance_turn_emits_no_marker(monkeypatch):
    _set_eval(monkeypatch, [0.5])
    sid, state = await svc.start_session("lb2", "comm_01_self_intro")
    state["turn_count"] = 1

    yielded = [t async for t in svc.run_turn(sid, "half answer")]
    assert not any(isinstance(t, svc.NodeAdvance) for t in yielded)
