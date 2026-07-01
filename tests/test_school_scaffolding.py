"""Wave 3.2 — every School English node now ships deterministic scaffolding.

The 16 grade-2..5 nodes had ZERO bridge_exercises/exemplars, so a stuck child got
no structured scaffold (only free-form LLM generation). Each node now carries a
foundational fill_blank + a standard multiple_choice (key-graded, no LLM) and
exemplars, exactly the ladder the interview/comm modules already had.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.registry import get_module, get_node  # noqa: E402
from app.graph.answer_check import (  # noqa: E402
    BRIDGE_CORRECT_SCORE,
    BRIDGE_WRONG_SCORE,
    grade_pending_answer,
)


def _pending(bx):
    return {"type": bx.type, "answer_key": bx.answer_key,
            "accept": bx.accept, "options": bx.options}


def test_all_16_school_nodes_have_scaffolding_and_exemplars():
    nodes = get_module("school_english").nodes
    assert len(nodes) == 16
    for n in nodes:
        assert n.bridge_exercises, f"{n.id} has no bridge_exercises"
        assert n.exemplars, f"{n.id} has no exemplars"
        # foundational + standard ladder present
        bands = {bx.band for bx in n.bridge_exercises}
        assert {"foundational", "standard"} <= bands, f"{n.id} missing a band: {bands}"


def test_school_fill_blank_grades_deterministically():
    bx = get_node("c2_simple_sentence").bridge_exercises[0]  # "The cat ___."
    assert grade_pending_answer(_pending(bx), "runs").score == BRIDGE_CORRECT_SCORE
    assert grade_pending_answer(_pending(bx), "sleeps").score == BRIDGE_CORRECT_SCORE  # accept synonym
    assert grade_pending_answer(_pending(bx), "purple").score == BRIDGE_WRONG_SCORE


def test_school_multiple_choice_grades_deterministically():
    mc = get_node("c2_alphabet_sounds").bridge_exercises[1]  # "starts with 'm'?"
    assert grade_pending_answer(_pending(mc), "moon").score == BRIDGE_CORRECT_SCORE
    assert grade_pending_answer(_pending(mc), "apple").score == BRIDGE_WRONG_SCORE
