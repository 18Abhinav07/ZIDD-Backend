# tests/test_rate_limit_prune.py
"""FIX: turn_counts must stay bounded.

The daily turn tracker is a module-level defaultdict keyed by user_id. Without a
prune/cap it grows once per distinct id ever seen (anonymous + spoofable ids
included) and never shrinks — an unbounded memory leak. These tests pin the two
guarantees of _prune: stale prior-day entries are dropped, and a single-day
flood is capped at _MAX_TRACKED.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.middleware import rate_limit
from app.middleware.rate_limit import _prune, turn_counts, _MAX_TRACKED


@pytest.fixture(autouse=True)
def _clear_tracker():
    """Each test starts and ends with an empty shared tracker."""
    turn_counts.clear()
    yield
    turn_counts.clear()


def test_prune_drops_previous_day_entries():
    # One entry from today, many from a stale prior day.
    turn_counts["active"] = {"date": "2026-06-18", "count": 5}
    for i in range(50):
        turn_counts[f"stale_{i}"] = {"date": "2026-06-17", "count": 1}

    _prune("2026-06-18")

    # Only today's entry survives; every prior-day entry is evicted.
    assert "active" in turn_counts
    assert turn_counts["active"]["count"] == 5
    assert all(not k.startswith("stale_") for k in turn_counts)
    assert len(turn_counts) == 1


def test_prune_caps_single_day_flood_at_max_tracked():
    # A same-day flood that exceeds the cap (no stale entries to drop first).
    over = _MAX_TRACKED + 250
    for i in range(over):
        turn_counts[f"u_{i}"] = {"date": "2026-06-18", "count": 1}

    _prune("2026-06-18")

    # Bounded at the cap regardless of unique-id volume; oldest-inserted evicted.
    assert len(turn_counts) == _MAX_TRACKED
    # The most-recently-inserted ids survive (insertion-order eviction from front).
    assert f"u_{over - 1}" in turn_counts
    assert "u_0" not in turn_counts


def test_prune_is_noop_when_all_current_day_and_under_cap():
    # All entries are today's and the set is under the cap: prune must not evict
    # anyone (the active in-day tracking set is never thinned by the sweep).
    for i in range(100):
        turn_counts[f"u_{i}"] = {"date": "2026-06-18", "count": i}

    _prune("2026-06-18")

    assert len(turn_counts) == 100
    # Counters are preserved intact — prune never touches surviving entries.
    assert turn_counts["u_42"]["count"] == 42
