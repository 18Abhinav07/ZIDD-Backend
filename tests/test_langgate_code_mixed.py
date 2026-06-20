"""P1 — deterministic romanized-Hindi / Hinglish code-mix heuristic.

langdetect reads Latin-script Hinglish as English (it keys on charset + n-gram
profile, so a majority-English-by-token code-mix classifies as `en`), so the
single most common real failure — a learner answering a gated module in
romanized Hindi or heavy code-mix — slipped straight past the pre-gate to the
unreliable local-LLM `english` flag. A curated marker lexicon now catches it
BEFORE langdetect.

The hard constraint is no false positives: a valid simple-English answer (the
young learners the gate should encourage) must NEVER be gated. The heuristic
requires BOTH an absolute marker floor and a ratio floor, and every marker in
the lexicon is an unambiguous romanization with no valid-English collision.
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
from app.graph.nodes.evaluate import evaluate_node  # noqa: E402


@pytest.fixture
def _detect_says_english(monkeypatch):
    """Force langdetect to report English, isolating the marker heuristic: any
    True verdict under this fixture is the lexicon's doing, not langdetect's."""
    monkeypatch.setattr(langgate, "detect", lambda _s: "en")


# ---------- the heuristic catches what langdetect misses ----------

def test_code_mixed_answer_langdetect_reads_as_english_still_gates(_detect_says_english):
    # Majority-English by token, so langdetect says "en" — but it is substantially
    # Hindi. The lexicon (ko, aur, karna, chahiye, kyunki, bahut, hai) catches it.
    assert langgate.fails_language_gate(
        "I think company ko aur growth karna chahiye kyunki market bahut bada hai",
        "interview",
    ) is True


def test_fully_romanized_hindi_gates(_detect_says_english):
    # Both floors cleared with margin even with langdetect neutralised.
    assert langgate.fails_language_gate(
        "mujhe yeh nahi pata", "communication"
    ) is True


# ---------- the false-positive guards hold ----------

def test_valid_simple_english_never_gates(_detect_says_english):
    assert langgate.fails_language_gate(
        "I really want to improve my English and speak more clearly",
        "communication",
    ) is False


def test_lone_stray_marker_does_not_gate(_detect_says_english):
    # One casual Hindi word in an otherwise-English answer is below the absolute
    # floor (needs >= 2) — left for the LLM, not slammed to 0.0.
    assert langgate.fails_language_gate(
        "I think we should focus on the growth yaar", "group_discussion"
    ) is False


def test_two_markers_below_ratio_floor_does_not_gate(_detect_says_english):
    # Exactly two markers (ko, ka) but only ~15% of tokens — below the 30% ratio
    # floor, so a predominantly-English answer is not gated on a stray couple.
    assert langgate.fails_language_gate(
        "the meeting ko schedule and then we discuss the plan ka detail later",
        "interview",
    ) is False


def test_english_colliding_words_are_not_markers(_detect_says_english):
    # main / the / to / is / us / do / par are all valid English and excluded from
    # the lexicon — an answer built from them must not gate.
    assert langgate.fails_language_gate(
        "the main point is to do this for us at par with the rest",
        "communication",
    ) is False


# ---------- module + length preconditions still apply ----------

def test_school_module_bypasses_even_heavy_hinglish():
    assert langgate.fails_language_gate(
        "mujhe yeh bilkul samajh nahi aaya aur main soch raha hu", "school_english"
    ) is False


def test_short_code_mix_below_token_floor_bypasses():
    # 3 tokens: under MIN_LANGCHECK_TOKENS, never judged.
    assert langgate.fails_language_gate("ko aur hai", "interview") is False


# ---------- evaluate_node short-circuits a code-mix without the LLM ----------

@pytest.mark.asyncio
async def test_evaluate_shortcircuits_code_mix_without_calling_llm(monkeypatch):
    # langdetect would pass this as English; the heuristic short-circuits it, so
    # the eval LLM is never reached.
    monkeypatch.setattr(langgate, "detect", lambda _s: "en")

    def _boom(*a, **k):
        raise AssertionError("eval LLM must NOT be called on a gated code-mix answer")

    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", _boom)

    state = {
        "competency_node": "comm_01_self_intro",
        "user_input": "I think company ko aur growth karna chahiye kyunki market bahut bada hai",
        "messages": [],
        "current_mastery": 0.5,
        "attempts": 0,
    }
    out = await evaluate_node(state)

    assert out["last_eval_score"] == 0.0
    assert out["last_diagnosis"]["english"] is False
    assert out["last_diagnosis"]["on_task"] is False
