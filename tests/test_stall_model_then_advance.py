"""Wave 1.2b — after 2 stuck turns the coach MODELS the answer, not re-asks.

Live, a grade-2 learner got the identical "word that starts with B" re-ask for 9
turns. The clarify/redirect prompts now switch, on the 2nd consecutive stuck turn,
from "ask again" to "model a correct example, then give a fresh step". This is a
prompt-level change keyed on the existing attempt counters — routing/caps are
untouched.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.ai.prompts import build_clarify_prompt, build_redirect_prompt  # noqa: E402
from app.content.registry import get_node  # noqa: E402
from app.graph.nodes.clarify import clarify_node  # noqa: E402
from app.graph.nodes.redirect import redirect_node  # noqa: E402

_NODE = "c2_alphabet_sounds"


def test_clarify_prompt_models_answer_when_stuck():
    node = get_node(_NODE)
    stuck = build_clarify_prompt(node, [], {}, "", model_answer=True).lower()
    assert "model it for them" in stuck
    first = build_clarify_prompt(node, [], {}, "", model_answer=False).lower()
    assert "say it again in english" in first
    assert "model it for them" not in first


def test_redirect_prompt_models_answer_when_stuck():
    node = get_node(_NODE)
    stuck = build_redirect_prompt(node, [], {}, "", model_answer=True).lower()
    assert "model one short, correct answer" in stuck
    first = build_redirect_prompt(node, [], {}, "", model_answer=False).lower()
    assert "steer them back" in first
    assert "model one short, correct answer" not in first


@pytest.mark.asyncio
async def test_clarify_node_flips_to_model_on_second_stuck_turn():
    base = {"competency_node": _NODE, "messages": [], "last_diagnosis": {}}
    first = await clarify_node({**base, "clarify_attempts": 0})
    second = await clarify_node({**base, "clarify_attempts": 1})
    assert "model it for them" not in first["pending"].prompt.lower()
    assert "model it for them" in second["pending"].prompt.lower()


@pytest.mark.asyncio
async def test_redirect_node_flips_to_model_on_second_stuck_turn():
    base = {"competency_node": _NODE, "messages": [], "last_diagnosis": {}}
    first = await redirect_node({**base, "redirect_attempts": 0})
    second = await redirect_node({**base, "redirect_attempts": 1})
    assert "model one short, correct answer" not in first["pending"].prompt.lower()
    assert "model one short, correct answer" in second["pending"].prompt.lower()
