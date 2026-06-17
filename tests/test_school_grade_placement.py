"""Phase 0.3 — school selects by grade, not CEFR.

school_english is a primary-grade ladder (grades 2-5), not a CEFR continuum.
Placing a Grade-2 child by a CEFR self-report band ("intermediate" -> B1) is
nonsense and would drop them mid-ladder. So school_english places by grade:
grade N -> the first node of that grade's band. comm/interview/gd keep the CEFR
placement selector unchanged.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.content import registry  # noqa: E402
from app.services import session_service as svc  # noqa: E402


def test_school_uses_grade_placement_not_cefr():
    assert registry.uses_grade_placement("school_english") is True
    assert registry.uses_grade_placement("communication") is False
    assert registry.uses_grade_placement("interview") is False
    assert registry.uses_grade_placement("group_discussion") is False


def test_school_placement_by_grade():
    # Each grade lands on the FIRST node of its band.
    assert registry.grade_placement_node(2).id == "c2_alphabet_sounds"
    assert registry.grade_placement_node(3).id == "c3_action_words"
    assert registry.grade_placement_node(4).id == "c4_past_tense"
    assert registry.grade_placement_node(5).id == "c5_tenses_mix"


def test_grade_placement_clamps_out_of_range():
    # Below grade 2 -> first node; above grade 5 -> grade-5 band start.
    assert registry.grade_placement_node(1).id == "c2_alphabet_sounds"
    assert registry.grade_placement_node(9).id == "c5_tenses_mix"


def test_non_school_still_uses_cefr():
    # comm/interview/gd placement is unchanged: first node at/above the band.
    assert registry.placement_node("communication", "B1").id == "comm_03_past_event"
    assert registry.placement_node("communication", "B2").id == "comm_06_persuade"


@pytest.mark.asyncio
async def test_place_user_school_routes_by_grade():
    # No LLM call: grade is a deterministic, non-CEFR placement.
    out = await svc.place_user("school_english", grade=4)
    assert out["starting_node"] == "c4_past_tense"
    assert out["grade"] == 4


@pytest.mark.asyncio
async def test_place_user_non_school_ignores_grade():
    # comm still places by CEFR self-report, grade is irrelevant.
    out = await svc.place_user("communication", self_report="advanced")
    assert out["starting_node"] == "comm_06_persuade"  # advanced -> B2

