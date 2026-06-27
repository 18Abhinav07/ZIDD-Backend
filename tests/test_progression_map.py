"""Regression tests for the two progression-map bugs.

Bug 1 (clean_pass): _persist_mastery previously required current_mastery >= 0.8
(MASTERY_COMPLETE) to write clean_pass=True. EMA alpha 0.3 cannot reach 0.8 in
<=2 turns, making the gate unreachable and always writing clean_pass=False.

Bug 2 (map locked): get_progression_map used clean_pass as the sole "completed"
signal. Since clean_pass was always False, all nodes after the first appeared
locked on return visits. The fix adds node_completed (written by _maybe_advance
on every actual advance) and uses it as the primary completion signal.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.services import session_service as svc  # noqa: E402

# First two non-voice nodes in the communication module (indices 0 and 1).
_NODE_1 = "comm_00_greetings"
_NODE_2 = "comm_01_self_intro"
_MODULE = "communication"


# ---------------------------------------------------------------------------
# Bug 1 — clean_pass written correctly (no EMA gate)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_persist_mastery_clean_pass_within_cap(tmp_path, monkeypatch):
    """clean_pass=True when attempts <= CLEAN_PASS_MAX_ATTEMPTS, regardless of EMA."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    state = svc._new_state("u1", "s1", _NODE_1, "", task_type="comm_prep")
    # Simulate 2 clean-pass turns: EMA stays far below 0.8 (as it would in reality)
    state["attempts"] = 2
    state["current_mastery"] = 0.51  # max EMA after 2 perfect turns with alpha=0.3

    await svc._persist_mastery(state)

    store = get_storage()
    prog = await store.get_progression("u1")
    row = next(p for p in prog if p["node_id"] == _NODE_1)
    assert row["clean_pass"], "Expected clean_pass=True for attempts=2, got False"

    reset_storage()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_persist_mastery_no_clean_pass_over_cap(tmp_path, monkeypatch):
    """clean_pass=False when attempts exceed CLEAN_PASS_MAX_ATTEMPTS."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    state = svc._new_state("u2", "s2", _NODE_1, "", task_type="comm_prep")
    state["attempts"] = svc.CLEAN_PASS_MAX_ATTEMPTS + 1
    state["current_mastery"] = 0.9  # even with high EMA, over cap → not clean

    await svc._persist_mastery(state)

    store = get_storage()
    prog = await store.get_progression("u2")
    row = next(p for p in prog if p["node_id"] == _NODE_1)
    assert not row["clean_pass"], "Expected clean_pass=False when over attempt cap"

    reset_storage()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Bug 2 — node_completed written on advance, unlocks subsequent map nodes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_maybe_advance_writes_node_completed(tmp_path, monkeypatch):
    """_maybe_advance writes node_completed=True for the node that was just completed."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    state = svc._new_state("u3", "s3", _NODE_1, "", task_type="comm_prep")
    state["clean_streak"] = svc.ADVANCE_STREAK
    state["advance_streak"] = svc.ADVANCE_STREAK
    state["attempts"] = 2
    state["current_mastery"] = 0.51
    state["node_history"] = {}
    state["remediation"] = False
    state["module_done"] = False
    state["tester_level"] = False
    state["review_level"] = False

    await svc._maybe_advance(state)

    store = get_storage()
    prog = await store.get_progression("u3")
    row = next((p for p in prog if p["node_id"] == _NODE_1), None)
    assert row is not None, "_maybe_advance must persist a mastery row for the completed node"
    assert row["node_completed"], "Expected node_completed=True after advancing past node"
    # The user should now be on the next node
    assert state["competency_node"] != _NODE_1

    reset_storage()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_maybe_advance_node_completed_non_clean(tmp_path, monkeypatch):
    """node_completed=True even when the advance was non-clean (> cap attempts)."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    state = svc._new_state("u4", "s4", _NODE_1, "", task_type="comm_prep")
    state["clean_streak"] = svc.ADVANCE_STREAK
    state["advance_streak"] = svc.ADVANCE_STREAK
    state["attempts"] = svc.CLEAN_PASS_MAX_ATTEMPTS + 5  # grind advance
    state["current_mastery"] = 0.4
    state["node_history"] = {}
    state["remediation"] = False
    state["module_done"] = False
    state["tester_level"] = False
    state["review_level"] = False

    await svc._maybe_advance(state)

    store = get_storage()
    prog = await store.get_progression("u4")
    row = next((p for p in prog if p["node_id"] == _NODE_1), None)
    assert row is not None
    assert row["node_completed"], "node_completed must be True even for a non-clean advance"
    assert not row["clean_pass"], "clean_pass must be False for an over-cap advance"

    reset_storage()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# End-to-end map status test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_progression_map_unlocks_after_advance(tmp_path, monkeypatch):
    """After a node is advanced past, the next node appears as 'active' on the map."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    # Directly write a completed mastery record for node 1 (simulates a past advance)
    store = get_storage()
    await store.upsert_mastery("u5", _NODE_1, 0.51, 2, clean_pass=True, node_completed=True)

    # No active session → map should show node 1 as mastered, node 2 as active
    nodes = await svc.get_progression_map("u5", _MODULE)
    by_id = {n["node_id"]: n for n in nodes}

    assert _NODE_1 in by_id, "Node 1 must appear in map"
    assert by_id[_NODE_1]["status"] == "mastered", (
        f"Node 1 must be mastered after advance, got {by_id[_NODE_1]['status']}"
    )
    assert _NODE_2 in by_id, "Node 2 must appear in map"
    assert by_id[_NODE_2]["status"] == "active", (
        f"Node 2 must be active (unlocked) after node 1 is completed, got {by_id[_NODE_2]['status']}"
    )
    # All subsequent nodes after the first unlocked should be locked
    nodes_list = [n for n in nodes if n["node_id"] not in (_NODE_1, _NODE_2)]
    for n in nodes_list:
        assert n["status"] == "locked", f"Expected locked for {n['node_id']}, got {n['status']}"

    reset_storage()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_progression_map_non_clean_advance_still_unlocks(tmp_path, monkeypatch):
    """A non-clean advance (node_completed=True, clean_pass=False) still shows mastered."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    store = get_storage()
    # Non-clean advance: clean_pass=False but node_completed=True
    await store.upsert_mastery("u6", _NODE_1, 0.4, 7, clean_pass=False, node_completed=True)

    nodes = await svc.get_progression_map("u6", _MODULE)
    by_id = {n["node_id"]: n for n in nodes}

    assert by_id[_NODE_1]["status"] == "mastered", (
        "Node 1 must be mastered even with clean_pass=False when node_completed=True"
    )
    assert by_id[_NODE_2]["status"] == "active", (
        "Node 2 must unlock after a non-clean advance of node 1"
    )

    reset_storage()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_progression_map_fresh_user_first_node_active(tmp_path, monkeypatch):
    """A brand-new user with no records sees exactly the first node as active."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import reset_storage

    get_settings.cache_clear()
    reset_storage()

    nodes = await svc.get_progression_map("u_fresh", _MODULE)
    assert len(nodes) > 0
    active_nodes = [n for n in nodes if n["status"] == "active"]
    locked_nodes = [n for n in nodes if n["status"] == "locked"]
    mastered_nodes = [n for n in nodes if n["status"] == "mastered"]

    assert len(active_nodes) == 1, f"Expected exactly 1 active node, got {len(active_nodes)}"
    assert active_nodes[0]["node_id"] == nodes[0]["node_id"], "First node must be active"
    assert len(mastered_nodes) == 0, "No mastered nodes for a fresh user"
    assert len(locked_nodes) == len(nodes) - 1

    reset_storage()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_progression_map_active_session_overrides_mastered(tmp_path, monkeypatch):
    """A live session on a previously mastered node shows it as active, not mastered."""
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(tmp_path / "test.db"))
    from app.config import get_settings
    from app.storage import get_storage, reset_storage

    get_settings.cache_clear()
    reset_storage()

    store = get_storage()
    # Both nodes have been completed before
    await store.upsert_mastery("u7", _NODE_1, 0.7, 2, clean_pass=True, node_completed=True)
    await store.upsert_mastery("u7", _NODE_2, 0.6, 4, clean_pass=False, node_completed=True)

    # Simulate active session on node 1 (user is replaying it)
    fake_session = svc._new_state("u7", "s7", _NODE_1, "", task_type="comm_prep")
    fake_session["clean_streak"] = 1
    svc.SessionStore["s7"] = fake_session

    try:
        nodes = await svc.get_progression_map("u7", _MODULE)
        by_id = {n["node_id"]: n for n in nodes}

        assert by_id[_NODE_1]["status"] == "active", (
            "Active session node must show as active even when node_completed=True"
        )
        assert by_id[_NODE_2]["status"] == "mastered", (
            "Previously completed nodes after active node must remain mastered"
        )
    finally:
        svc.SessionStore.pop("s7", None)
        reset_storage()
        get_settings.cache_clear()
