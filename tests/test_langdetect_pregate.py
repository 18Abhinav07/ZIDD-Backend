"""Phase 0.2 — deterministic non-LLM language pre-gate.

Local qwen's structured eval is over-lenient and unreliably sets the `english`
flag, so broken / non-English answers slip through and get praised, and the
clarify path stays unreachable. Fix: before the eval LLM, run a cheap non-LLM
language check (`langdetect`). On a language-gated module, a long-enough answer
detected as non-English short-circuits to a synthesized `english=False,
score=0.0` diagnosis (skips the LLM entirely) which route_node sends to clarify.

Conservative by design: short inputs, names, "ok/yes", and the lenient
school_english module bypass the gate so we never block a real English answer.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai import langgate  # noqa: E402
from app.graph import route  # noqa: E402
from app.graph.nodes.evaluate import evaluate_node  # noqa: E402


# ---------- pure pre-gate ----------

def test_long_nonenglish_on_gated_module_fails_gate():
    # A full Hindi (romanised) sentence on a language-gated module.
    assert langgate.fails_language_gate(
        "yeh ek bahut lamba hindi vaakya hai bilkul saaf", "group_discussion"
    ) is True


def test_short_english_input_bypasses_pregate():
    # "ok" must never trip the gate — too short to judge, would false-positive.
    assert langgate.fails_language_gate("ok", "communication") is False
    assert langgate.fails_language_gate("yes please", "interview") is False


def test_long_english_passes_gate():
    assert langgate.fails_language_gate(
        "I work as a software engineer and I really enjoy solving hard problems",
        "interview",
    ) is False


def test_school_module_skips_langgate():
    # school_english is lenient: children code-mix constantly. Never gate it.
    assert langgate.fails_language_gate(
        "yeh ek bahut lamba hindi vaakya hai bilkul saaf", "school_english"
    ) is False


# ---------- evaluate_node short-circuit ----------

def _base_state(node_id: str, user_input: str) -> dict:
    return {
        "competency_node": node_id,
        "user_input": user_input,
        "messages": [],
        "current_mastery": 0.5,
        "attempts": 0,
    }


@pytest.mark.asyncio
async def test_pregate_shortcircuits_nonenglish_without_calling_llm(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("eval LLM must NOT be called on a gated non-English answer")

    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _boom)

    state = _base_state(
        "comm_01_self_intro",
        "main aaj subah jaldi utha aur maine apna kaam shuru kiya",
    )
    out = await evaluate_node(state)

    assert out["last_eval_score"] == 0.0
    assert out["last_diagnosis"]["english"] is False
    assert out["last_diagnosis"]["on_task"] is False


@pytest.mark.asyncio
async def test_pregate_diagnosis_routes_to_clarify(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not call")),
    )
    state = _base_state(
        "comm_01_self_intro",
        "main aaj subah jaldi utha aur maine apna kaam shuru kiya",
    )
    out = await evaluate_node(state)

    # Feed the synthesized diagnosis into route_node the way the graph does.
    route_state = {
        **state,
        **out,
        "bridge_attempts": 0,
        "strengthen_attempts": 0,
        "fails": 0,
        "clean_streak": 0,
    }
    # B11/B12 (Test-fix-01): a non-English answer must NOT scaffold the skill
    # (bridge) — it routes to clarify ("say that in English") instead.
    assert route.route_node(route_state) == "clarify"
