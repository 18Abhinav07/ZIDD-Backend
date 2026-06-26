"""Wave 3.1 / D2 / D5 — the voice tier is gated "coming soon".

comm_08/09/10 are level_type:'voice' but no voice pipeline exists, so they were
silently coached/graded as typed text (D5), and the non-monotonic comm ladder
(comm_08 regresses to A2 after comm_07=B2) made placement_node's at/above-ceiling
fallback land a strong learner on the last positional node — a voice node (D2).
These guard that the advance ladder and placement both skip the voice tier, so a
learner's text path completes cleanly at comm_07 and never enters a voice node.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.registry import (  # noqa: E402
    COMM_ID,
    get_module,
    get_node,
    next_node,
    placement_node,
)

_VOICE = {"comm_08_voice_intro", "comm_09_voice_convo", "comm_10_voice_pressure"}
_LAST_TEXT = "comm_07_handle_question"


def test_voice_nodes_really_are_voice():
    # Guards the premise: if the data is re-tagged, this test must be revisited.
    for nid in _VOICE:
        assert get_node(nid).level_type == "voice"
    assert get_node(_LAST_TEXT).level_type == "text"


def test_next_node_completes_module_at_last_text_node():
    # Finishing the last TEXT node completes the module — no advance into voice.
    assert next_node(_LAST_TEXT) is None


def test_no_text_node_ever_advances_into_a_voice_node():
    order = get_module(COMM_ID).order
    text_nodes = [nid for nid in order if get_node(nid).level_type == "text"]
    for nid in text_nodes:
        nxt = next_node(nid)
        assert nxt not in _VOICE, f"{nid} advanced into voice node {nxt}"


def test_text_ladder_still_advances_between_text_nodes():
    assert next_node("comm_00_greetings") == "comm_01_self_intro"
    assert next_node("comm_06_persuade") == _LAST_TEXT


def test_placement_above_ceiling_falls_back_to_last_text_node():
    # A C2 learner is above communication's B2 ceiling — fallback must be the
    # last TEXT node (comm_07), never the positional last node comm_10 (voice).
    placed = placement_node(COMM_ID, "C2")
    assert placed.level_type == "text"
    assert placed.id == _LAST_TEXT


def test_placement_never_returns_a_voice_node():
    for cefr in ("A1", "A2", "B1", "B2", "C1", "C2"):
        assert placement_node(COMM_ID, cefr).id not in _VOICE


@pytest.mark.asyncio
async def test_direct_start_on_voice_node_is_refused():
    # A direct id start (bypassing placement/advance) must be refused, not coached
    # as text. The guard raises before any storage call.
    from app.services import session_service as svc
    with pytest.raises(ValueError, match="coming soon"):
        await svc.start_session("u_voice", "comm_08_voice_intro")


def test_module_node_count_excludes_voice():
    # Onboarding's "N NODES" badge must reflect only reachable nodes, not the
    # gated voice tier (the FE showed "11 NODES" for an 8-node reachable comm).
    from app.content.registry import list_modules
    mods = {m["id"]: m for m in list_modules()}
    assert mods["communication"]["level_count"] == 8   # 11 - 3 voice
    assert mods["school_english"]["level_count"] == 16  # no voice tier, unchanged


@pytest.mark.asyncio
async def test_progression_map_excludes_voice_nodes():
    # The learner's path must not render voice nodes — they never unlock, and a
    # "complete" module with locked nodes trailing below is confusing.
    from app.services.session_service import get_progression_map
    rows = await get_progression_map("u_nonexistent_voicecheck", "communication")
    ids = {r["node_id"] for r in rows}
    assert ids, "expected a non-empty path"
    assert ids.isdisjoint(_VOICE)
    assert len(ids) == 8
