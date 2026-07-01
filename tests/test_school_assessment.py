"""NCERT school rebuild — Phase 2: the assessment engine.

Per-chapter scoring, 30/60/100% milestone triggers, and parent-readable report
cards — none of which existed. Pure functions, deterministic grading.
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

from app.content.schema import Assessment, AssessmentItem, Module  # noqa: E402
from app.content.assessment import (  # noqa: E402
    milestone_due,
    report_card,
    score_assessment,
)
from app.graph.answer_check import (  # noqa: E402
    BRIDGE_CORRECT_SCORE,
    grade_pending_answer,
)

_DATA = Path(__file__).parent.parent / "app" / "content" / "data" / "school"


def _chapter_test() -> Assessment:
    ch = Module.model_validate(json.load(open(_DATA / "class2_ch01_first_day.json")))
    return ch.chapter_test


def test_all_correct_passes_with_no_weak_skills():
    test = _chapter_test()
    answers = {i.id: i.answer_key for i in test.items}
    r = score_assessment(test, answers)
    assert r.correct == 5 and r.total == 5 and r.score == 1.0
    assert r.passed is True
    assert r.weak_skills == [] and r.missed_item_ids == []


def test_all_wrong_fails_and_flags_every_skill():
    test = _chapter_test()
    answers = {i.id: "zzz_wrong" for i in test.items}
    r = score_assessment(test, answers)
    assert r.correct == 0 and r.passed is False
    assert set(r.weak_skills) == {"new_words", "comprehension", "nouns", "use"}
    assert len(r.missed_item_ids) == 5


def test_mixed_score_and_per_skill_breakdown():
    test = _chapter_test()
    # answer the 3 multiple_choice items right, the 2 fill_blanks wrong
    answers = {}
    for i in test.items:
        answers[i.id] = i.answer_key if i.type == "multiple_choice" else "nope"
    r = score_assessment(test, answers)
    assert r.correct == 3 and r.total == 5 and r.score == 0.6
    assert r.passed is True  # pass_mark 0.6
    # a missing answer counts as wrong
    assert score_assessment(test, {}).correct == 0


def _ms(pct):
    return Assessment(id=f"m{pct}", title=f"Milestone {pct}", kind="milestone",
                      at_percent=pct,
                      items=[AssessmentItem(id=f"m{pct}i", type="multiple_choice",
                                            prompt="q", answer_key="a", options=["a", "b"])])


MILES = [_ms(30), _ms(60), _ms(100)]


def test_milestone_fires_at_thresholds():
    assert milestone_due(0, 5, MILES, set()) is None            # 0% -> nothing
    assert milestone_due(2, 5, MILES, set()).at_percent == 30   # 40% -> 30 fires
    assert milestone_due(2, 5, MILES, {30}) is None             # 40% but 30 fired -> none
    assert milestone_due(3, 5, MILES, {30}).at_percent == 60    # 60% -> 60 fires
    assert milestone_due(5, 5, MILES, {30, 60}).at_percent == 100  # 100% -> final


def test_milestone_never_skipped_on_a_big_jump():
    # learner jumps to 80% with nothing fired -> the LOWEST unfired (30) fires first
    assert milestone_due(4, 5, MILES, set()).at_percent == 30
    assert milestone_due(4, 5, MILES, {30}).at_percent == 60


def test_mcq_distractor_differing_only_by_punctuation_is_not_marked_correct():
    """Regression (P0): _norm() strips terminal '?'/'.', so two MCQ options that
    differ ONLY by punctuation collapsed to the same normalized string, and the
    grader returned the WRONG option's index as the key — marking a distractor
    correct even on a click. The grader must resolve options by exact text."""
    item = AssessmentItem(
        id="q", type="multiple_choice",
        prompt="Which one is a correct question?",
        answer_key="Where is the lion?",
        options=["Where is the lion.", "Where is the lion?", "The lion where is?"],
    )
    test = Assessment(id="t", title="t", kind="chapter", items=[item])
    assert score_assessment(test, {"q": "Where is the lion?"}).correct == 1  # key -> right
    assert score_assessment(test, {"q": "Where is the lion."}).correct == 0  # period -> wrong
    assert score_assessment(test, {"q": "The lion where is?"}).correct == 0  # jumbled -> wrong


def test_every_live_mcq_option_grades_unambiguously():
    """Content guard over ALL Class 2-5 chapter tests + milestones: for every
    multiple_choice item, the exact key scores correct and EVERY other option
    scores wrong — i.e. no two options collide under the grader."""
    chapter_files = sorted(_DATA.glob("class*_ch*.json"))
    manifest_files = sorted(_DATA.glob("class[2-5].json"))
    assessments: list[Assessment] = []
    for f in chapter_files:
        assessments.append(Module.model_validate(json.load(open(f))).chapter_test)
    for f in manifest_files:
        for m in json.load(open(f)).get("milestones", []):
            assessments.append(Assessment.model_validate(m))

    seen_mcq = 0
    for test in assessments:
        for item in test.items:
            if item.type != "multiple_choice":
                continue
            seen_mcq += 1
            pending = {"type": "multiple_choice", "answer_key": item.answer_key,
                       "options": item.options, "accept": item.accept or []}
            assert grade_pending_answer(pending, item.answer_key).score == BRIDGE_CORRECT_SCORE
            for opt in item.options or []:
                if opt == item.answer_key or opt in (item.accept or []):
                    continue
                got = grade_pending_answer(pending, opt).score
                assert got != BRIDGE_CORRECT_SCORE, (test.id, item.id, opt)
    assert seen_mcq > 30  # sanity: the real bank was actually exercised


def test_every_live_item_and_bridge_key_grades_correct():
    """Every authored item — chapter-test items, milestone items, AND teaching
    bridge exercises across all Class 2-5 content — must grade its OWN answer key
    as correct. Guards the re-authored content (new comprehension fills, 6-item
    tests, mixed milestones) against an ungradable key or a malformed item."""
    def _ok(d: dict, ident) -> int:
        pending = {"type": d["type"], "answer_key": d["answer_key"],
                   "options": d.get("options"), "accept": d.get("accept")}
        assert grade_pending_answer(pending, d["answer_key"]).score == BRIDGE_CORRECT_SCORE, ident
        return 1

    checked = 0
    for f in sorted(_DATA.glob("class*_ch*.json")):
        data = json.load(open(f))
        for node in data.get("nodes", []):
            for bx in node.get("bridge_exercises", []):
                checked += _ok(bx, (f.name, bx["id"]))
        for it in (data.get("chapter_test") or {}).get("items", []):
            checked += _ok(it, (f.name, it["id"]))
    for f in sorted(_DATA.glob("class[2-5].json")):
        for m in json.load(open(f)).get("milestones", []):
            for it in m["items"]:
                checked += _ok(it, (f.name, it["id"]))
    assert checked > 150   # the whole bank was actually exercised


def test_regenerated_chapter_tests_cover_two_comprehension_items():
    """The re-authored chapter tests probe comprehension TWICE (an MC + a fill),
    not once with a recycled vocab fill."""
    data = json.load(open(_DATA / "class2_ch06_zoo.json"))
    skills = [i["skill"] for i in data["chapter_test"]["items"]]
    assert skills.count("comprehension") == 2
    assert skills.count("new_words") == 2 and skills.count("grammar") == 2


def test_report_card_rolls_up_class_results():
    test = _chapter_test()
    good = score_assessment(test, {i.id: i.answer_key for i in test.items})
    bad = score_assessment(test, {})
    card = report_card("Class 2 — English", [good, bad])
    assert card["assessments"] == 2 and card["passed"] == 1
    assert 0.0 < card["overall"] < 1.0
    assert "nouns" in card["mastered_skills"] or "nouns" in card["weak_skills"]
