"""NCERT school rebuild — Phase 1: chapter-as-module + gradable tests.

Proves the new structure end to end on a real Class-2 chapter (Marigold Unit 1):
a chapter carries NCERT metadata + ordered levels + a chapter test, and every
test item grades deterministically through the SAME answer_check engine the tutor
uses, so a school assessment never depends on the LLM rubric to mark it.
"""
import json
import os
from pathlib import Path

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.content.schema import Module, SchoolClass, Assessment, AssessmentItem  # noqa: E402
from app.graph.answer_check import (  # noqa: E402
    BRIDGE_CORRECT_SCORE,
    BRIDGE_WRONG_SCORE,
    grade_pending_answer,
)

_DATA = Path(__file__).parent.parent / "app" / "content" / "data" / "school"


def _chapter() -> Module:
    return Module.model_validate(json.load(open(_DATA / "class2_ch01_first_day.json")))


def test_chapter_loads_with_ncert_metadata_and_levels():
    ch = _chapter()
    assert ch.class_no == 2 and ch.chapter_no == 1
    assert ch.ncert_unit == "First Day at School"
    assert ch.genre == "poem"
    # the levels inside the chapter, in teaching order
    assert [n.title for n in ch.nodes] == [
        "New Words", "Read and Understand", "Naming Words (Nouns)", "Use It: Write a Sentence",
    ]


def test_chapter_carries_a_gradable_test():
    t = _chapter().chapter_test
    assert t is not None and t.kind == "chapter" and len(t.items) == 5
    # every item is tagged with the skill it assesses (for the report)
    assert {i.skill for i in t.items} == {"new_words", "comprehension", "nouns", "use"}


def test_chapter_test_items_grade_deterministically():
    for item in _chapter().chapter_test.items:
        pending = {"type": item.type, "answer_key": item.answer_key,
                   "options": item.options, "accept": item.accept}
        assert grade_pending_answer(pending, item.answer_key).score == BRIDGE_CORRECT_SCORE
        assert grade_pending_answer(pending, "totally_wrong_zzz").score == BRIDGE_WRONG_SCORE


def test_school_class_manifest_validates():
    sc = SchoolClass(
        class_no=2, title="Class 2 — English (Marigold)",
        chapters=["c2_ch01_first_day"],
        milestones=[Assessment(
            id="c2_m100", title="Class 2 Final", kind="milestone", at_percent=100,
            items=[AssessmentItem(id="m1", type="multiple_choice", prompt="Which is a naming word?",
                            answer_key="book", options=["book", "run"], skill="nouns")],
        )],
    )
    assert sc.chapters == ["c2_ch01_first_day"]
    assert sc.milestones[0].at_percent == 100


def test_milestone_at_invalid_percent_is_rejected():
    with pytest.raises(ValidationError):
        Assessment(id="bad", title="x", kind="milestone", at_percent=50,
             items=[AssessmentItem(id="m", type="multiple_choice", prompt="q",
                             answer_key="a", options=["a", "b"])])
