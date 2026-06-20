"""Spec B task #14 — the 9th SSE frame: adaptation_cue.

The marker `svc.AdaptationCue` surfaces `state["last_selection"]` (the selector's
{"action", "band", "rationale"} for this turn) so the UI can show an "adapting
your path" cue. The selector logic is untouched — these tests only assert the
new frame plumbing in `_run_turn_locked`.

Cases:
  - emitted on ADVANCE, positioned AFTER ProgressUpdate and BEFORE NodeAdvance
  - payload fields carry action/band/rationale straight from last_selection
  - suppressed on REPEAT (last_selection.action == "REPEAT")
  - suppressed on module-done (last_selection is None there), but SessionRecap fires

Mirrors tests/test_selector_integration.py: monkeypatch the eval + stream
boundary, clear SessionStore between tests.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DiagnosisEval, SelectionDecision  # noqa: E402
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
    for tok in ("FEEDBACK", "-tok"):
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
    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _Scores(scores))


async def _drain(sid, text):
    return [t async for t in svc.run_turn(sid, text)]


# ---------- emitted on ADVANCE, ordered between ProgressUpdate and NodeAdvance ----------

async def test_adaptation_cue_emitted_on_advance_in_order(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    sid, state = await svc.start_session("cue1", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(sid, "pass one")          # first clean pass, no advance yet
    yielded = await _drain(sid, "pass two")  # second clean pass -> advance

    assert state["competency_node"] == "comm_02_describe_routine"

    cues = [t for t in yielded if isinstance(t, svc.AdaptationCue)]
    assert len(cues) == 1
    assert cues[0].action == "ADVANCE"

    # ordering: progress_update -> adaptation_cue -> node_advance
    i_prog = next(i for i, t in enumerate(yielded) if isinstance(t, svc.ProgressUpdate))
    i_cue = next(i for i, t in enumerate(yielded) if isinstance(t, svc.AdaptationCue))
    i_adv = next(i for i, t in enumerate(yielded) if isinstance(t, svc.NodeAdvance))
    assert i_prog < i_cue < i_adv


# ---------- payload fields come straight from last_selection ----------

async def test_adaptation_cue_payload_fields(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    # Two candidates -> Stage 2 LLM call decides; we pin a known band + rationale.
    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "ADVANCE", "next_ref": "comm_03_past_event", "band": "standard"},
    ]
    monkeypatch.setattr(
        "app.services.session_service.compute_valid_candidates",
        lambda state: cands,
    )

    async def _pick(snapshot, candidates):
        return SelectionDecision(
            action="ADVANCE",
            next_ref="comm_03_past_event",
            band="stretch",
            rationale="learner is strong, push ahead",
        )

    monkeypatch.setattr("app.services.session_service.select_next_content", _pick)

    sid, state = await svc.start_session("cue2", "comm_01_self_intro")
    state["turn_count"] = 1
    await _drain(sid, "pass one")
    yielded = await _drain(sid, "pass two")

    cues = [t for t in yielded if isinstance(t, svc.AdaptationCue)]
    assert len(cues) == 1
    cue = cues[0]
    sel = state["last_selection"]
    # the cue mirrors state["last_selection"] verbatim
    assert cue.action == sel["action"] == "ADVANCE"
    assert cue.band == sel["band"] == "stretch"
    assert cue.rationale == sel["rationale"] == "learner is strong, push ahead"


# ---------- suppressed on REPEAT ----------

async def test_adaptation_cue_suppressed_on_repeat(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    # Two candidates so the LLM stage runs; the LLM picks REPEAT (hold position).
    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "REPEAT", "next_ref": "comm_01_self_intro", "band": "standard"},
    ]
    monkeypatch.setattr(
        "app.services.session_service.compute_valid_candidates",
        lambda state: cands,
    )

    async def _pick(snapshot, candidates):
        return SelectionDecision(
            action="REPEAT",
            next_ref="comm_01_self_intro",
            band="standard",
            rationale="not solid yet, hold here",
        )

    monkeypatch.setattr("app.services.session_service.select_next_content", _pick)

    sid, state = await svc.start_session("cue3", "comm_01_self_intro")
    state["turn_count"] = 1
    await _drain(sid, "pass one")
    yielded = await _drain(sid, "pass two")

    # held on the current node, and the selector recorded a REPEAT
    assert state["competency_node"] == "comm_01_self_intro"
    assert state["last_selection"]["action"] == "REPEAT"
    # no cue on REPEAT, and no node advance either
    assert not any(isinstance(t, svc.AdaptationCue) for t in yielded)
    assert not any(isinstance(t, svc.NodeAdvance) for t in yielded)
    # progress still fires
    assert any(isinstance(t, svc.ProgressUpdate) for t in yielded)


# ---------- suppressed on module-done (last_selection is None there) ----------

async def test_adaptation_cue_suppressed_on_module_done(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    # No valid candidates -> terminal node behavior: module_done=True, the
    # selector records NO selection (last_selection stays None).
    monkeypatch.setattr(
        "app.services.session_service.compute_valid_candidates",
        lambda state: [],
    )

    sid, state = await svc.start_session("cue4", "comm_01_self_intro")
    state["turn_count"] = 1
    await _drain(sid, "pass one")
    yielded = await _drain(sid, "pass two")

    assert state["module_done"] is True
    assert state["last_selection"] is None
    # no cue on the module-done turn
    assert not any(isinstance(t, svc.AdaptationCue) for t in yielded)
    # but the recap IS emitted
    assert any(isinstance(t, svc.SessionRecap) for t in yielded)
