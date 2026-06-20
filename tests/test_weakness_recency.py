"""Weakness recency + cap: stale single-hit weaknesses age out, surface is capped.

bump_weakness only ever increments and get_weaknesses returned EVERYTHING, so one
early failure stayed the top interview/GD probe target forever even after the
learner mastered it. get_weaknesses now drops weaknesses not re-encountered within
the recency window and caps the surface; a persistent (repeatedly-bumped, recent)
weakness still shows.
"""
import os
import time

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.storage.local_store import (  # noqa: E402
    _WEAKNESS_RECENCY_SECONDS,
    _WEAKNESS_SURFACE_CAP,
    LocalStore,
)


@pytest.mark.asyncio
async def test_recent_weakness_surfaces(tmp_path):
    store = LocalStore(str(tmp_path / "w.db"))
    await store.bump_weakness("u1", "interview_prep", "STRUCTURE_STAR_METHOD", 0.2, raw="no STAR")
    out = await store.get_weaknesses("u1")
    assert len(out) == 1
    assert out[0]["skill_id"] == "STRUCTURE_STAR_METHOD"
    # also via the task-scoped query path
    assert len(await store.get_weaknesses("u1", "interview_prep")) == 1


@pytest.mark.asyncio
async def test_stale_weakness_ages_out(tmp_path):
    # A single failure long ago that was never re-encountered must drop off, so it
    # stops being the top probe target after the learner has moved on.
    store = LocalStore(str(tmp_path / "w.db"))
    await store.bump_weakness("u1", "interview_prep", "STRUCTURE_STAR_METHOD", 0.2)
    stale = time.time() - _WEAKNESS_RECENCY_SECONDS - 86_400
    store._conn.execute("UPDATE weaknesses SET last_seen = ? WHERE user_id = 'u1'", (stale,))
    store._conn.commit()
    assert await store.get_weaknesses("u1") == []
    assert await store.get_weaknesses("u1", "interview_prep") == []


@pytest.mark.asyncio
async def test_persistent_weakness_survives_despite_old_first_hit(tmp_path):
    # First seen long ago, but re-encountered recently: bump_weakness refreshes
    # last_seen, so a genuinely persistent weakness stays inside the window.
    store = LocalStore(str(tmp_path / "w.db"))
    await store.bump_weakness("u1", "interview_prep", "STRUCTURE_STAR_METHOD", 0.2)
    # backdate the first hit
    old = time.time() - _WEAKNESS_RECENCY_SECONDS - 10_000
    store._conn.execute("UPDATE weaknesses SET last_seen = ? WHERE user_id = 'u1'", (old,))
    store._conn.commit()
    # re-encounter it now -> last_seen refreshed to ~now
    await store.bump_weakness("u1", "interview_prep", "STRUCTURE_STAR_METHOD", 0.3)
    out = await store.get_weaknesses("u1")
    assert len(out) == 1
    assert out[0]["hit_count"] == 2


@pytest.mark.asyncio
async def test_surface_is_capped(tmp_path):
    store = LocalStore(str(tmp_path / "w.db"))
    skills = [
        "GRAMMAR_PAST_TENSE", "GRAMMAR_PRESENT_TENSE", "GRAMMAR_ARTICLES",
        "GRAMMAR_PLURALS", "GRAMMAR_PREPOSITIONS", "VOCABULARY_RANGE",
        "SENTENCE_STRUCTURE", "CLARITY_CONCISENESS",
    ]
    assert len(skills) > _WEAKNESS_SURFACE_CAP
    for sk in skills:
        await store.bump_weakness("u1", "communication", sk, 0.2)
    out = await store.get_weaknesses("u1")
    assert len(out) == _WEAKNESS_SURFACE_CAP   # capped, not all 8
