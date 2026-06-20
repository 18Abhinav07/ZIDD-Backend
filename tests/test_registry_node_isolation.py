"""FIX #14 — get_node must not hand out the registry's shared Concept.

The same Concept instance lives in module-global _NODE_INDEX. Returning the bare
reference meant a caller that mutated a returned node corrupted the canonical
copy for every subsequent caller. get_node now returns model_copy(deep=True), so
mutations are isolated — including nested mutable fields (prerequisites list).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content import registry

# Any real node id; pick the first available so this survives content edits.
_NODE_ID = next(iter(registry.all_node_ids()))


def test_get_node_returns_distinct_objects():
    a = registry.get_node(_NODE_ID)
    b = registry.get_node(_NODE_ID)
    # Different instances — never the shared registry object handed twice.
    assert a is not b


def test_mutating_returned_node_does_not_corrupt_registry():
    first = registry.get_node(_NODE_ID)
    original_title = first.title
    first.title = "MUTATED BY CALLER"
    # A fresh get must see the untouched canonical title.
    fresh = registry.get_node(_NODE_ID)
    assert fresh.title == original_title
    assert fresh.title != "MUTATED BY CALLER"


def test_mutating_nested_list_field_is_isolated():
    # Deep copy: appending to a returned node's prerequisites list must not leak
    # into the registry's canonical list (a shallow copy would share the list).
    first = registry.get_node(_NODE_ID)
    original_len = len(first.prerequisites)
    first.prerequisites.append("phantom_prereq")
    fresh = registry.get_node(_NODE_ID)
    assert len(fresh.prerequisites) == original_len
    assert "phantom_prereq" not in fresh.prerequisites
