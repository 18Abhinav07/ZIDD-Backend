"""NCERT school rebuild — Phase 2: curriculum loader (chapters + class manifests).

Proves the new structure is loadable and queryable: classes, ordered chapters,
chapter navigation, level->chapter lookup, and a real milestone exam that scores
through the assessment engine.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content import curriculum as cur  # noqa: E402
from app.content.assessment import score_assessment  # noqa: E402


def test_class_and_chapters_load_in_order():
    assert 2 in cur.all_classes()
    c2 = cur.get_class(2)
    assert "Class 2" in c2.title
    assert cur.chapter_count(2) >= 6                  # full Marigold-aligned class
    chapters = cur.class_chapters(2)
    assert chapters[0].id == "c2_ch01_first_day"
    assert chapters[0].ncert_unit == "First Day at School"
    assert chapters[1].ncert_unit == "Haldi's Adventure"
    # every class 2-5 is authored with genuine NCERT chapters
    assert set(cur.all_classes()) >= {2, 3, 4, 5}


def test_chapter_navigation_and_level_lookup():
    assert cur.next_chapter(2, "c2_ch01_first_day").id == "c2_ch02_haldi"
    assert cur.next_chapter(2, cur.class_chapters(2)[-1].id) is None  # last chapter
    owner = cur.chapter_of_level("c2_ch01_l3_grammar_nouns")
    assert owner is not None and owner.id == "c2_ch01_first_day"


def test_chapter_levels_are_tutorable_by_the_engine():
    # A chapter's levels must be servable by the SAME engine that tutors every
    # other module — so they teach/eval/scaffold/advance with no parallel path.
    from app.content.registry import all_node_ids, get_node, module_of, next_node
    assert get_node("c2_ch01_l1_new_words").title == "New Words"
    assert module_of("c2_ch01_l1_new_words") == "c2_ch01_first_day"
    assert next_node("c2_ch01_l1_new_words") == "c2_ch01_l2_understand"
    assert next_node("c2_ch01_l4_use_it") is None  # last level -> chapter complete
    assert "c2_ch01_l3_grammar_nouns" in all_node_ids()
    # a chapter level must resolve to the school task type so a session can start
    from app.content.task_types import TaskType, task_type_of
    assert task_type_of("c2_ch01_l1_new_words") == TaskType.SCHOOL_ENGLISH


def test_every_class_has_30_60_100_milestones_that_score():
    for n in cur.all_classes():
        ms = cur.get_class(n).milestones
        assert [m.at_percent for m in ms] == [30, 60, 100], f"class {n} milestones"
        for m in ms:
            full = {i.id: i.answer_key for i in m.items}
            assert score_assessment(m, full).passed is True
            assert score_assessment(m, {}).passed is False
