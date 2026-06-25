"""P1 — clarify_attempts / bridge_attempts are refunded on recovery.

P0-6 refunds redirect_attempts when a fluent-off-task learner comes back on-task.
This pins the two sibling caps that were left permanently un-refunded:

  * clarify_attempts (consecutive "say it in English" nudges) must reset the
    moment the learner produces competent English again — on-task OR off-task,
    since producing English is what breaks the non-English streak. It must NOT
    reset while the learner is still non-English.
  * bridge_attempts (consecutive sub-0.4 scaffolds) must reset on a clean PASS,
    when the learner has climbed out of bridge territory. It must NOT reset on a
    still-struggling on-task turn — and crucially the refund must not be able to
    defeat the infinite-bridge-loop cap (the council fix), because route_node
    increments bridge_attempts EARLIER in the same turn than this fold runs.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.services.session_service import _update_progress  # noqa: E402


# ---------- direct unit tests on the reset matrix ----------

def _state(*, english, on_task, score, **over) -> dict:
    base = {
        "last_diagnosis": {"english": english, "on_task": on_task},
        "last_eval_score": score,
        "clean_streak": 0,
        "level_fails": 0,
        "strengthen_attempts": 0,
        "scaffold": 0,
        "redirect_attempts": 2,
        "clarify_attempts": 2,
        "bridge_attempts": 2,
    }
    base.update(over)
    return base


def test_non_english_turn_does_not_refund_any_cap():
    # Still non-English: the clarify streak is alive, refund nothing.
    st = _state(english=False, on_task=True, score=0.0)
    _update_progress(st)
    assert st["clarify_attempts"] == 2
    assert st["redirect_attempts"] == 2
    assert st["bridge_attempts"] == 2


def test_english_offtask_refunds_clarify_only():
    # Competent English but off-task: the non-English streak is broken (refund
    # clarify), but the learner is still off-task (keep redirect) and produced no
    # passing answer (keep bridge).
    st = _state(english=True, on_task=False, score=0.0)
    _update_progress(st)
    assert st["clarify_attempts"] == 0
    assert st["redirect_attempts"] == 2
    assert st["bridge_attempts"] == 2


def test_ontask_struggling_refunds_clarify_and_redirect_not_bridge():
    # On-task English but a sub-pass (still-struggling) answer: clarify + redirect
    # refund, but bridge_attempts is preserved so the cap stays reachable.
    st = _state(english=True, on_task=True, score=0.3)
    _update_progress(st)
    assert st["clarify_attempts"] == 0
    assert st["redirect_attempts"] == 0
    assert st["bridge_attempts"] == 2


def test_clean_pass_refunds_all_three_caps():
    # Full recovery (clean pass): every recovery counter clears.
    st = _state(english=True, on_task=True, score=0.9)
    _update_progress(st)
    assert st["clarify_attempts"] == 0
    assert st["redirect_attempts"] == 0
    assert st["bridge_attempts"] == 0
    assert st["clean_streak"] == 1


# ---------- integration: the refund must not defeat the bridge cap ----------

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.services import session_service as svc  # noqa: E402


class _Scores:
    def __init__(self, scores):
        self._it = iter(scores)

    async def __call__(self, node, messages, user_input, behavior=None):
        score = next(self._it)
        return DiagnosisEval(
            score=score, understanding="x",
            errors=[] if score >= 0.6 else ["e"],
            strengths=["s"] if score >= 0.6 else [],
            next_focus="n", on_task=True, english=True,
        )


async def _fake_stream(spec):
    for tok in ("ok", " ", "done"):
        yield tok


@pytest.fixture
def _patch_ai(monkeypatch):
    async def _fake_summary(node, messages):
        return "summary"

    monkeypatch.setattr("app.services.session_service.stream_generation", _fake_stream)
    monkeypatch.setattr("app.services.session_service.summarize_session", _fake_summary)
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.fails_language_gate", lambda *a, **k: False
    )
    yield
    svc.SessionStore.clear()


async def _drain(agen):
    async for _ in agen:
        pass


@pytest.mark.asyncio
async def test_bridge_cap_still_reached_despite_refund(monkeypatch, _patch_ai):
    # Four consecutive sub-0.4 on-task answers: bridge three times, then the cap
    # escapes to teach. The PASS-gated refund never fires (no answer reaches 0.7),
    # so it cannot wipe route_node's same-turn bridge_attempts increment and the
    # infinite-bridge-loop guard still holds.
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        _Scores([0.2, 0.2, 0.2, 0.2]),
    )
    sid, state = await svc.start_session("cb1", "comm_01_self_intro")
    state["turn_count"] = 1

    routes = []
    for _ in range(4):
        await _drain(svc.run_turn(sid, "a weak but on-task attempt"))
        routes.append(state["last_route"])

    assert routes == ["bridge", "bridge", "bridge", "teach"]
    assert state["bridge_attempts"] == 3


@pytest.mark.asyncio
async def test_clean_pass_refunds_bridge_mid_session(monkeypatch, _patch_ai):
    # bridge, bridge (attempts climb to 2); a mid-band on-task turn does NOT refund
    # (still struggling); only the clean PASS drives bridge_attempts back to 0.
    # Uses a node with NO pre-authored bridge exercises so bridge takes the LLM
    # path (no answer-key grading) and every turn's score flows through _Scores.
    # The 0.2 -> 0.6 -> 0.9 ramp keeps each step's jump <= the swing-damper
    # threshold, so the recovery genuinely reaches the PASS branch end-to-end
    # (a single 0.2 -> 0.9 jump would be smoothed to 0.62 and never pass — that
    # upward-damping is the separate swing-sign backlog item, not this fix).
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        _Scores([0.2, 0.2, 0.6, 0.9]),
    )
    # Every shipped node now carries authored bridge exercises (Wave 3.2), but this
    # test exercises the LLM bridge path (scores flow through _Scores every turn).
    # Strip the served node's exercises so bridge_node takes the generation branch.
    import app.graph.nodes.bridge as bridge_mod
    _real_get_node = bridge_mod.get_node

    def _no_authored_bridge(nid):
        n = _real_get_node(nid)
        n.bridge_exercises = []
        return n

    monkeypatch.setattr(bridge_mod, "get_node", _no_authored_bridge)
    sid, state = await svc.start_session("cb2", "c2_naming_words")
    state["turn_count"] = 1

    await _drain(svc.run_turn(sid, "weak 1"))
    await _drain(svc.run_turn(sid, "weak 2"))
    assert state["bridge_attempts"] == 2
    await _drain(svc.run_turn(sid, "an improving on-task attempt"))
    assert state["bridge_attempts"] == 2   # mid-band, not a pass -> NOT refunded
    assert state["last_route"] != "bridge"  # 0.6 climbed out of bridge territory
    await _drain(svc.run_turn(sid, "a strong on-task answer"))
    assert state["bridge_attempts"] == 0   # refunded on the clean pass
