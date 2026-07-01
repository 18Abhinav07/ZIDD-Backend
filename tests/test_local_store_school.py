# tests/test_local_store_school.py
"""School per-skill mastery + durable results store (Phase B1).

School assessment skill tags don't fit the communication/interview SkillID
taxonomy (they all coerce to OTHER), so school gets a dedicated, deterministic,
BIDIRECTIONAL per-skill mastery EMA folded from exact-graded assessment results.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.storage.local_store import LocalStore


@pytest.fixture
def store(tmp_path):
    return LocalStore(str(tmp_path / "test.db"))


def _by_skill(*pairs):
    # (skill, correct, total) tuples -> score_assessment-shaped dicts
    return [{"skill": s, "correct": c, "total": t} for s, c, t in pairs]


@pytest.mark.asyncio
async def test_record_persists_result_and_per_skill_mastery(store):
    await store.record_assessment_result(
        "u1", "c2_ch06_test", 2, "chapter", 0.6, True,
        _by_skill(("new_words", 2, 2), ("grammar", 0, 2)),
    )
    results = await store.get_school_results("u1")
    assert len(results) == 1
    r = results[0]
    assert r["test_id"] == "c2_ch06_test" and r["passed"] is True
    assert r["weak_skills"] == ["grammar"]  # 0/2 < pass-mark, new_words 2/2 is not

    mastery = {m["skill"]: m["ema"] for m in await store.get_school_skill_mastery("u1")}
    assert mastery["new_words"] == 1.0   # first sight of a 2/2 skill -> ema = ratio
    assert mastery["grammar"] == 0.0     # first sight of a 0/2 skill -> ema = 0


@pytest.mark.asyncio
async def test_mastery_is_bidirectional_weakness_recovers_on_later_passes(store):
    # miss the skill -> weak
    await store.record_assessment_result(
        "u1", "t1", 2, "chapter", 0.0, False, _by_skill(("grammar", 0, 2)))
    assert "grammar" in await store.get_school_weak_skills("u1")

    # pass it once -> EMA climbs (0 -> 0.5) but still below the 0.6 weak line
    await store.record_assessment_result(
        "u1", "t2", 2, "chapter", 1.0, True, _by_skill(("grammar", 2, 2)))
    assert "grammar" in await store.get_school_weak_skills("u1")

    # pass it again -> EMA 0.5 -> 0.75, the weakness is now resolved (unlike the
    # increment-only weakness counter, which only ever ages out by the clock).
    await store.record_assessment_result(
        "u1", "t3", 2, "chapter", 1.0, True, _by_skill(("grammar", 2, 2)))
    assert "grammar" not in await store.get_school_weak_skills("u1")
    mastery = {m["skill"]: m["ema"] for m in await store.get_school_skill_mastery("u1")}
    assert abs(mastery["grammar"] - 0.75) < 1e-9


@pytest.mark.asyncio
async def test_weak_skills_are_weakest_first_and_thresholded(store):
    await store.record_assessment_result(
        "u1", "t1", 3, "milestone", 0.5, False,
        _by_skill(("comprehension", 0, 2), ("nouns", 1, 2), ("verbs", 2, 2)),
    )
    weak = await store.get_school_weak_skills("u1")
    assert weak == ["comprehension", "nouns"]   # 0.0 then 0.5, both < 0.6; verbs (1.0) excluded


@pytest.mark.asyncio
async def test_retaking_a_test_upserts_not_duplicates(store):
    await store.record_assessment_result(
        "u1", "t1", 2, "chapter", 0.0, False, _by_skill(("grammar", 0, 2)))
    await store.record_assessment_result(
        "u1", "t1", 2, "chapter", 1.0, True, _by_skill(("grammar", 2, 2)))
    results = await store.get_school_results("u1")
    assert len(results) == 1                 # same test_id -> one row
    assert results[0]["passed"] is True      # latest result wins


@pytest.mark.asyncio
async def test_review_skills_are_mastered_but_stale_only(store):
    # master one skill (2/2 -> ema 1.0) and fail another (0/2 -> ema 0.0)
    await store.record_assessment_result(
        "u1", "t1", 5, "chapter", 0.5, False,
        _by_skill(("prepositions", 2, 2), ("tenses", 0, 2)))
    # just practised -> nothing is stale yet, so nothing is due for review
    assert await store.get_school_review_skills("u1") == []
    # widen the window so everything counts as stale: only the MASTERED skill is
    # due for a refresher; the weak one is handled by weak-skill targeting instead.
    due = await store.get_school_review_skills("u1", stale_seconds=-1)
    assert "prepositions" in due and "tenses" not in due


@pytest.mark.asyncio
async def test_results_filter_by_class_and_isolate_by_user(store):
    await store.record_assessment_result("u1", "c2_t", 2, "chapter", 1.0, True, _by_skill(("a", 1, 1)))
    await store.record_assessment_result("u1", "c3_t", 3, "chapter", 1.0, True, _by_skill(("a", 1, 1)))
    await store.record_assessment_result("u2", "c2_t", 2, "chapter", 1.0, True, _by_skill(("a", 1, 1)))
    assert [r["test_id"] for r in await store.get_school_results("u1", 2)] == ["c2_t"]
    assert len(await store.get_school_results("u1")) == 2
    assert len(await store.get_school_results("u2")) == 1
