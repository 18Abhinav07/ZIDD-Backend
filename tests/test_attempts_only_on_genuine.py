"""P1 — `attempts` increments only on a genuine attempt at the skill.

`attempts` (the scored-attempt counter) feeds two things: the clean-pass
determination (`attempts <= CLEAN_PASS_MAX_ATTEMPTS`) and, via its session
sibling, the ceiling-escape (`session_attempts <= 1`). A clarify (non-English)
or redirect (fluent-but-off-task) turn is NOT an attempt at the competency, yet
evaluate_node used to increment the counter on every turn. That inflated the
count — a learner who fumbled in Hindi or wandered off-topic before nailing the
answer was wrongly marked "not clean" and lost the first-strong-answer ceiling
escape. The counter now advances only when the diagnosis is english AND on_task.
Give-up and graded bridge items are on-task English, so they still count.
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
from app.graph.nodes.evaluate import evaluate_node  # noqa: E402


def _state(user_input: str, **over) -> dict:
    base = {
        "competency_node": "comm_01_self_intro",
        "user_input": user_input,
        "messages": [],
        "current_mastery": 0.5,
        "attempts": 2,            # a non-zero baseline so we see carry-forward, not reset
        "session_attempts": 2,
    }
    base.update(over)
    return base


def _patch_eval(monkeypatch, *, english: bool, on_task: bool, score: float = 0.8):
    async def _fake(*a, **k):
        return DiagnosisEval(
            score=score, understanding="u", errors=[], strengths=[],
            next_focus="n", english=english, on_task=on_task,
        )
    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _fake)


# ---------- the detour turns do NOT count ----------

@pytest.mark.asyncio
async def test_non_english_turn_does_not_increment(monkeypatch):
    # Hits the deterministic language gate -> english=False -> no LLM call.
    def _boom(*a, **k):
        raise AssertionError("LLM must not be called on a gated non-English answer")
    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _boom)

    out = await evaluate_node(_state("mujhe yeh nahi pata samajh aaya"))

    assert out["attempts"] == 2            # carried, not incremented
    assert out["session_attempts"] == 2


@pytest.mark.asyncio
async def test_fluent_off_task_turn_does_not_increment(monkeypatch):
    # Fluent English aimed at the wrong question -> on_task=False -> redirect.
    _patch_eval(monkeypatch, english=True, on_task=False, score=0.0)

    out = await evaluate_node(_state("I had pizza for lunch and it was delicious today"))

    assert out["attempts"] == 2
    assert out["session_attempts"] == 2


# ---------- a genuine attempt DOES count ----------

@pytest.mark.asyncio
async def test_on_task_english_turn_increments(monkeypatch):
    _patch_eval(monkeypatch, english=True, on_task=True, score=0.8)

    out = await evaluate_node(_state("I am a software engineer who enjoys solving hard problems"))

    assert out["attempts"] == 3
    assert out["session_attempts"] == 3


# ---------- scope preserved: give-up and bridge items still count ----------

@pytest.mark.asyncio
async def test_giveup_still_counts_as_attempt(monkeypatch):
    # "idk" -> stuck_diagnosis (on_task=True, english=True): a real, if stuck,
    # attempt at the node. No LLM call.
    def _boom(*a, **k):
        raise AssertionError("LLM must not be called on a give-up")
    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _boom)

    out = await evaluate_node(_state("idk"))

    assert out["attempts"] == 3
    assert out["session_attempts"] == 3


@pytest.mark.asyncio
async def test_graded_bridge_item_still_counts_as_attempt(monkeypatch):
    # A served fill_blank answer is graded deterministically (on_task English).
    def _boom(*a, **k):
        raise AssertionError("LLM must not be called on a graded bridge item")
    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _boom)

    state = _state(
        "went",
        pending_answer_key={"type": "fill_blank", "answer_key": "went"},
    )
    out = await evaluate_node(state)

    assert out["attempts"] == 3
    assert out["session_attempts"] == 3
