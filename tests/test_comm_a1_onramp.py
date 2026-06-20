"""comm A1 on-ramp: the new ground-floor node + its placement.

Adds comm_00_greetings (CEFR A1) at the front of the communication module and
routes a self-reported "beginner" to it. A2+ placement is unchanged — the A1
node is an earlier ramp, not a new gate, so anyone at/above A2 still starts at
self-intro.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.registry import (  # noqa: E402
    SELF_REPORT_CEFR,
    get_node,
    module_of,
    next_node,
    placement_node,
)


def test_a1_node_exists_and_is_a1():
    node = get_node("comm_00_greetings")
    assert node.cefr == "A1"
    assert module_of("comm_00_greetings") == "communication"
    # A real bridge ladder foundational -> stretch, every answer key present.
    bands = [bx.band for bx in node.bridge_exercises]
    assert "foundational" in bands and "stretch" in bands
    assert all(bx.answer_key for bx in node.bridge_exercises)


def test_a1_node_is_first_and_advances_into_self_intro():
    # The on-ramp sits at the very front of the module and flows into the old
    # first node, so the ladder is greetings -> self-intro -> ...
    assert next_node("comm_00_greetings") == "comm_01_self_intro"


def test_a1_placement_lands_on_onramp():
    assert placement_node("communication", "A1").id == "comm_00_greetings"


def test_a2_placement_unchanged_skips_onramp():
    # An A2 learner is at/above the on-ramp's band, so they still start at
    # self-intro — the A1 node never blocks an A2+ learner.
    assert placement_node("communication", "A2").id == "comm_01_self_intro"


def test_beginner_self_report_routes_to_onramp():
    # The self-report remap: a self-described beginner now starts at the A1 ground
    # floor rather than mid-A2.
    assert SELF_REPORT_CEFR["beginner"] == "A1"
    placed = placement_node("communication", SELF_REPORT_CEFR["beginner"])
    assert placed.id == "comm_00_greetings"
