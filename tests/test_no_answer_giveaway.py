"""Tutoring quality — the tutor must not write the answer the learner should give.

The product's worst pedagogical failure live was the coach handing over the exact
sentence ("say 'Hello, I am Ryuk'"), collapsing the task to copying. The opening,
teach, and strengthen prompts now forbid it explicitly.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import (  # noqa: E402
    build_opening_prompt,
    build_strengthen_prompt,
    build_teach_prompt,
)
from app.content.registry import get_node  # noqa: E402

_RULE = "never write out the exact answer"


def test_opening_forbids_answer_giveaway():
    node = get_node("comm_00_greetings")
    p = build_opening_prompt(node, []).lower()
    assert _RULE in p
    assert "use different details" in p


def test_teach_models_on_a_different_example():
    node = get_node("comm_00_greetings")
    p = build_teach_prompt(node, [], {}, "").lower()
    assert _RULE in p
    assert "different example" in p


def test_strengthen_forbids_giveaway():
    node = get_node("comm_00_greetings")
    p = build_strengthen_prompt(node, [], {}, "").lower()
    assert _RULE in p
