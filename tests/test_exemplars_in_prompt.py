"""Wave 1.1 — authored exemplars must reach the prompt.

The curriculum hand-authors 1-2 model answers per node (Concept.exemplars), but
NO prompt consumed them: build_eval_prompt anchored "what a mastered answer looks
like" on success_criteria alone, so 66 situated exemplars were dead weight at
runtime. These tests guard that the exemplars are now injected into the grading /
teaching anchors (eval, teach, strengthen), that the scaffold-DOWN bridge prompt
deliberately does NOT pull them in (a full mastered answer is the wrong anchor for
a smaller sub-step), and that a node WITHOUT exemplars (school_english) degrades
silently with no empty header. Offline prompt-content assertions — no LLM call.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import (  # noqa: E402
    build_bridge_prompt,
    build_eval_prompt,
    build_strengthen_prompt,
    build_teach_prompt,
)
from app.content.registry import get_node  # noqa: E402

_HEADER = "model answers at the target quality bar"


def test_eval_prompt_injects_authored_exemplars():
    node = get_node("comm_00_greetings")
    assert node.exemplars, "fixture node must ship authored exemplars"
    prompt = build_eval_prompt(node, [], "Hello, I am Abhinav from Jaipur.")
    assert _HEADER in prompt.lower()
    # Every authored exemplar reaches the grading anchor verbatim.
    for ex in node.exemplars:
        assert ex in prompt
    # And it must instruct the model NOT to parrot them back.
    assert "do not copy them" in prompt.lower()


def test_teach_and_strengthen_inject_exemplars():
    node = get_node("comm_00_greetings")
    teach = build_teach_prompt(node, [], {}, [])
    strengthen = build_strengthen_prompt(node, [], {}, [])
    for prompt in (teach, strengthen):
        assert _HEADER in prompt.lower()
        assert node.exemplars[0] in prompt


def test_bridge_prompt_excludes_exemplars():
    """Bridge scaffolds DOWN to bridge_focus; a full mastered exemplar would
    anchor too high, so it is intentionally left out."""
    node = get_node("comm_00_greetings")
    bridge = build_bridge_prompt(node, [], {}, [])
    assert _HEADER not in bridge.lower()
    assert node.exemplars[0] not in bridge


def test_node_without_exemplars_degrades_silently():
    # Every shipped node now carries exemplars, so build a synthetic node with
    # none — the block must vanish entirely (no empty header, no crash).
    from app.content.schema import Concept
    node = Concept(id="x", title="X", level=1, level_type="text", skill="s",
                   teach_focus="t", success_criteria="c", bridge_focus="b",
                   exemplars=[])
    prompt = build_eval_prompt(node, [], "The cat sat on the mat.")
    assert _HEADER not in prompt.lower()
