"""FIX #15 — selector must degrade gracefully on hostile input.

Two crash vectors the original code had:
  - validate_decision indexed candidates[0] when snapping an out-of-set forward
    action/ref; an EMPTY candidate list raised IndexError instead of degrading.
  - compute_valid_candidates called next_node(node_id) directly; an UNKNOWN
    node_id (not in the registry) raised KeyError instead of degrading.

Both now follow the existing graceful-degradation philosophy: empty candidates
-> REPEAT current node (mirrors fallback_decision); unknown node -> [] (treated
like a terminal node, so the caller marks the module done).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import SelectionDecision  # noqa: E402
from app.services.selector import (  # noqa: E402
    compute_valid_candidates,
    validate_decision,
)

MID_NODE = "comm_01_self_intro"


# ---------- validate_decision: empty candidate set ----------

def test_validate_decision_empty_candidates_degrades_to_repeat():
    # A forward decision with NO candidates must not IndexError on candidates[0];
    # it degrades to REPEAT pinned to the current node (no forward target exists).
    state = {"competency_node": MID_NODE}
    d = SelectionDecision(
        action="ADVANCE",
        next_ref="comm_02_describe_routine",
        band="stretch",
        rationale="model wants to advance but nothing is valid",
    )
    out = validate_decision(d, [], state)
    assert out.action == "REPEAT"
    assert out.next_ref == MID_NODE
    assert out.band == "stretch"  # band preserved, not lost in the degrade


# ---------- compute_valid_candidates: unknown node_id ----------

def test_compute_valid_candidates_unknown_node_returns_empty():
    # An id that is not in the registry must not raise KeyError; it degrades to
    # [] (same as a terminal node) so the caller marks the module done.
    out = compute_valid_candidates({"competency_node": "not_a_real_node_xyz"})
    assert out == []
