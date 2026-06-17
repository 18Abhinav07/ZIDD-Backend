"""Phase 2.1/2.2 — local-first SQLite storage backend.

Memory was a no-op offline (pg/pgvector unreachable on qwen-dev), so nothing
felt personalized. The LocalStore mirrors the cloud surface on SQLite so every
turn + weakness is logged and retrievable with Postgres OFFLINE. The dispatcher
picks local whenever ai_backend == "local".

Weaknesses aggregate by the fixed SkillID taxonomy: bump_weakness UPSERTs on the
exact (user_id, task_type, skill_id) tuple, so two phrasings of the same skill
sum into one row instead of fragmenting.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.storage import get_storage  # noqa: E402
from app.storage.local_store import LocalStore  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return LocalStore(str(tmp_path / "test.db"))


@pytest.mark.asyncio
async def test_local_store_roundtrip(store):
    await store.ensure_profile("u1", name="Asha")
    prof = await store.get_profile("u1")
    assert prof is not None
    assert prof["name"] == "Asha"

    await store.create_session("s1", "u1", "interview_prep", "interview", "n1")
    await store.end_session("s1", final_summary="went well", avg_score=0.7)
    # ending a session shouldn't error and profile still present
    assert (await store.get_profile("u1")) is not None


@pytest.mark.asyncio
async def test_turn_logged_offline(store):
    await store.ensure_profile("u1")
    await store.create_session("s1", "u1", "communication", "communication", "n1")
    await store.record_turn(
        "s1", "u1", "n1", score=0.3, on_task=True, english=True, affect="neutral"
    )
    await store.record_turn(
        "s1", "u1", "n1", score=0.9, on_task=True, english=True, affect="happy"
    )
    turns = await store.get_turns("s1")
    assert len(turns) == 2
    assert turns[0]["score"] == 0.3


@pytest.mark.asyncio
async def test_weakness_aggregates(store):
    await store.ensure_profile("u1")
    await store.bump_weakness("u1", "interview_prep", "STRUCTURE_STAR_METHOD", 0.3, raw="no STAR")
    await store.bump_weakness("u1", "interview_prep", "STRUCTURE_STAR_METHOD", 0.2, raw="still no STAR")
    weaknesses = await store.get_weaknesses("u1")
    assert len(weaknesses) == 1
    w = weaknesses[0]
    assert w["skill_id"] == "STRUCTURE_STAR_METHOD"
    assert w["hit_count"] == 2
    assert w["last_score"] == 0.2
    assert w["last_raw"] == "still no STAR"


@pytest.mark.asyncio
async def test_skill_id_upsert_increments_not_duplicates(store):
    await store.ensure_profile("u1")
    # two different raw phrasings coercing to the SAME skill_id -> one row
    await store.bump_weakness("u1", "communication", "grammar_past_tense", 0.3, raw="struggles with past tense")
    await store.bump_weakness("u1", "communication", "GRAMMAR_PAST_TENSE", 0.25, raw="failed past tense")
    weaknesses = await store.get_weaknesses("u1")
    rows = [w for w in weaknesses if w["skill_id"] == "GRAMMAR_PAST_TENSE"]
    assert len(rows) == 1
    assert rows[0]["hit_count"] == 2


@pytest.mark.asyncio
async def test_unmatched_skill_falls_to_other(store):
    await store.ensure_profile("u1")
    await store.bump_weakness("u1", "communication", "completely made up tag", 0.3)
    weaknesses = await store.get_weaknesses("u1")
    assert any(w["skill_id"] == "OTHER" for w in weaknesses)


@pytest.mark.asyncio
async def test_test_item_cache_roundtrip(store):
    # Phase 4 Layer B: probe items precomputed at PREP end are cached on the test
    # sibling so a TEST start opens instantly instead of blocking on generation.
    items = [
        {"skill_id": "GD_STANCE_CLARITY", "prompt": "State your stance.", "aim": "clear side"},
        {"skill_id": "GD_REBUTTAL", "prompt": "Rebut the prior point.", "aim": "direct rebuttal"},
    ]
    await store.cache_test_items("u1", "gd_test", items)
    got = await store.get_cached_test_items("u1", "gd_test")
    assert got == items


@pytest.mark.asyncio
async def test_test_item_cache_miss_returns_none(store):
    # no precache for this user/task -> a clean miss, so the caller regenerates.
    assert (await store.get_cached_test_items("nobody", "gd_test")) is None


@pytest.mark.asyncio
async def test_test_item_cache_stale_returns_none(store):
    items = [{"skill_id": "GD_REBUTTAL", "prompt": "x", "aim": "y"}]
    # cached long ago; with a freshness window the read treats it as a miss.
    await store.cache_test_items("u1", "gd_test", items, ts=1.0)
    assert (await store.get_cached_test_items("u1", "gd_test", max_age=10.0)) is None
    # without a window the stale row is still returned (caller opted out of TTL)
    assert (await store.get_cached_test_items("u1", "gd_test")) == items


@pytest.mark.asyncio
async def test_test_item_cache_overwrites(store):
    await store.cache_test_items("u1", "gd_test", [{"skill_id": "A", "prompt": "1", "aim": "a"}])
    await store.cache_test_items("u1", "gd_test", [{"skill_id": "B", "prompt": "2", "aim": "b"}])
    got = await store.get_cached_test_items("u1", "gd_test")
    assert got == [{"skill_id": "B", "prompt": "2", "aim": "b"}]


def test_dispatcher_picks_local_when_backend_local(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("AI_BACKEND", "local")
    get_settings.cache_clear()
    storage = get_storage()
    assert isinstance(storage, LocalStore)
    get_settings.cache_clear()
