"""Spec B selector — integration through run_turn / _maybe_advance.

Three paths:
  1. single-candidate fast path: a normal two-clean-pass advance moves
     comm_01 -> comm_02 EXACTLY as before, records last_selection=ADVANCE, and
     does NOT invoke the LLM call (select_next_content untouched).
  2. multi-candidate path: with >1 candidate the LLM call decides; its pick is
     honored (and validated onto the candidate set).
  3. LLM-failure path: when select_next_content raises, the deterministic
     fallback still advances the learner — the turn never breaks.

Mirrors tests/test_no_level_bleed.py: monkeypatch the eval + stream boundary,
clear SessionStore between tests.
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


# ---------- 1. single-candidate fast path ----------

async def test_single_candidate_advances_without_llm_call(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    # Tripwire: the LLM selector must NOT be called on the single-candidate path.
    called = {"n": 0}

    async def _boom(snapshot, candidates):  # pragma: no cover - must not run
        called["n"] += 1
        raise AssertionError("select_next_content called on single-candidate path")

    monkeypatch.setattr(
        "app.services.session_service.select_next_content", _boom
    )

    sid, state = await svc.start_session("sel1", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(sid, "pass one")          # first clean pass, no advance yet
    assert state["competency_node"] == "comm_01_self_intro"

    await _drain(sid, "pass two")          # second clean pass -> advance
    # advance target is the linear next node, exactly as the old next_node path
    assert state["competency_node"] == "comm_02_describe_routine"
    assert called["n"] == 0

    sel = state["last_selection"]
    assert sel is not None
    assert sel["action"] == "ADVANCE"
    assert sel["band"] == "standard"
    assert sel["rationale"] == "single valid candidate"


async def test_non_advancing_turn_records_no_selection(monkeypatch):
    _set_eval(monkeypatch, [0.5])
    sid, state = await svc.start_session("sel2", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(sid, "half answer")
    assert state["competency_node"] == "comm_01_self_intro"
    assert state["last_selection"] is None


# ---------- 2. multi-candidate LLM path ----------

async def test_multi_candidate_uses_llm_pick(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    # Force two candidates so Stage 2 (the LLM call) is exercised.
    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "ADVANCE", "next_ref": "comm_03_past_event", "band": "standard"},
    ]
    monkeypatch.setattr(
        "app.services.session_service.compute_valid_candidates",
        lambda state: cands,
    )

    seen = {"snapshot": None, "candidates": None}

    async def _pick(snapshot, candidates):
        seen["snapshot"] = snapshot
        seen["candidates"] = candidates
        return SelectionDecision(
            action="ADVANCE",
            next_ref="comm_03_past_event",
            band="stretch",
            rationale="learner is strong, push ahead",
        )

    monkeypatch.setattr("app.services.session_service.select_next_content", _pick)

    sid, state = await svc.start_session("sel3", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(sid, "pass one")
    await _drain(sid, "pass two")

    # the LLM's pick (the second candidate) is honored
    assert state["competency_node"] == "comm_03_past_event"
    assert seen["candidates"] == cands
    assert seen["snapshot"]["current_node"] == "comm_01_self_intro"

    sel = state["last_selection"]
    assert sel["action"] == "ADVANCE"
    assert sel["band"] == "stretch"
    assert sel["rationale"] == "learner is strong, push ahead"


async def test_multi_candidate_llm_out_of_set_pick_is_snapped(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "ADVANCE", "next_ref": "comm_03_past_event", "band": "standard"},
    ]
    monkeypatch.setattr(
        "app.services.session_service.compute_valid_candidates",
        lambda state: cands,
    )

    async def _pick(snapshot, candidates):
        # hallucinated ref outside the candidate set -> must snap to candidates[0]
        return SelectionDecision(
            action="ADVANCE",
            next_ref="invented_node_x",
            band="standard",
            rationale="bad ref",
        )

    monkeypatch.setattr("app.services.session_service.select_next_content", _pick)

    sid, state = await svc.start_session("sel4", "comm_01_self_intro")
    state["turn_count"] = 1
    await _drain(sid, "pass one")
    await _drain(sid, "pass two")

    assert state["competency_node"] == "comm_02_describe_routine"


# ---------- 3. LLM-failure fallback path ----------

async def test_multi_candidate_llm_failure_falls_back(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])

    cands = [
        {"action": "ADVANCE", "next_ref": "comm_02_describe_routine", "band": "standard"},
        {"action": "ADVANCE", "next_ref": "comm_03_past_event", "band": "standard"},
    ]
    monkeypatch.setattr(
        "app.services.session_service.compute_valid_candidates",
        lambda state: cands,
    )

    async def _explode(snapshot, candidates):
        raise RuntimeError("model transport down")

    monkeypatch.setattr("app.services.session_service.select_next_content", _explode)

    sid, state = await svc.start_session("sel5", "comm_01_self_intro")
    state["turn_count"] = 1
    await _drain(sid, "pass one")
    yielded = await _drain(sid, "pass two")

    # turn did not break, and the fallback advanced to the first forward candidate
    assert state["competency_node"] == "comm_02_describe_routine"
    assert state["last_selection"]["action"] == "ADVANCE"
    # the advance still emitted its normal NodeAdvance marker
    assert any(isinstance(t, svc.NodeAdvance) for t in yielded)
