"""Phase 4 Layer B — probe-item precache wiring in session_service.

A TEST-mode session must open instantly: generating the probe bank on the
critical path would block the learner behind an LLM call. So the engine
precomputes it at the END of the PREP sibling's session (when the learner is
done coaching that module) and caches it on the TEST task type. A TEST start
then reads the cache; on a miss or a stale entry it falls back to synchronous
generation so the session still opens with a real bank.

Wiring under test:
  (a) PREP end_session precaches the TEST sibling's bank (gd_prep -> gd_test),
  (b) single-mode PREP end does NOT precache (no distinct test sibling),
  (c) TEST start reads a FRESH cache without regenerating,
  (d) TEST start regenerates when the cache is STALE (older than TEST_ITEM_TTL),
  (e) TEST start with no cache falls back to synchronous generation.

Storage is pointed at a tmp SQLite db (the dispatcher's LOCAL backend); the
generator is monkeypatched so no network/Ollama is touched.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.ai.schemas import ProbeItem  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services import session_service as svc  # noqa: E402
from app.storage import get_storage, reset_storage  # noqa: E402

pytestmark = pytest.mark.asyncio

GD_PREP_NODE = "gd_01_stake_position"      # group_discussion -> gd_prep / gd_test
COMM_NODE = "comm_02_describe_routine"      # single-mode -> communication


def _items(*skill_ids: str) -> list[ProbeItem]:
    return [
        ProbeItem(skill_id=s, prompt=f"prompt for {s}", aim=f"aim for {s}")
        for s in skill_ids
    ]


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Point the dispatcher at a fresh tmp SQLite db for this test."""
    db = tmp_path / "precache.db"
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(db))
    get_settings.cache_clear()
    reset_storage()
    yield get_storage()
    reset_storage()
    get_settings.cache_clear()
    svc.SessionStore.clear()


@pytest.fixture(autouse=True)
def _patch_summary(monkeypatch):
    """summarize_session is the only AI call on the PREP end_session path."""
    async def _fake_summary(node, messages):
        return "summary"

    monkeypatch.setattr(
        "app.services.session_service.summarize_session", _fake_summary
    )
    yield


async def test_prep_end_precaches_test_items(monkeypatch, store):
    """Ending a PREP session precaches the bank on its TEST sibling."""
    generated = _items("GD_STANCE_CLARITY", "GD_REBUTTAL")

    async def _fake_gen(user_id, task_type, n_items=4):
        assert task_type == "gd_test"  # the test sibling, not the prep value
        return generated

    monkeypatch.setattr(
        "app.services.session_service.generate_test_items", _fake_gen
    )

    sid, _state = await svc.start_session("u_prep", GD_PREP_NODE)
    await svc.end_session(sid)

    cached = await store.get_cached_test_items("u_prep", "gd_test")
    assert cached == [it.model_dump() for it in generated]


async def test_single_mode_prep_end_does_not_precache(monkeypatch, store):
    """A single-mode module has no distinct TEST sibling -> no precache, no gen."""
    called = False

    async def _fake_gen(user_id, task_type, n_items=4):
        nonlocal called
        called = True
        return _items("X")

    monkeypatch.setattr(
        "app.services.session_service.generate_test_items", _fake_gen
    )

    sid, _state = await svc.start_session("u_comm", COMM_NODE)
    await svc.end_session(sid)

    assert called is False
    assert (await store.get_cached_test_items("u_comm", "communication")) is None


async def test_test_start_uses_fresh_cache(monkeypatch, store):
    """A FRESH cached bank is loaded onto state without regenerating."""
    cached = _items("GD_STANCE_CLARITY", "GD_REBUTTAL")
    await store.cache_test_items(
        "u_fresh", "gd_test", [it.model_dump() for it in cached]
    )

    async def _boom(user_id, task_type, n_items=4):
        raise AssertionError("must not regenerate when cache is fresh")

    monkeypatch.setattr(
        "app.services.session_service.generate_test_items", _boom
    )

    _sid, state = await svc.start_session("u_fresh", GD_PREP_NODE, test_mode=True)
    assert state["probe_items"] == [it.model_dump() for it in cached]


async def test_stale_cache_regenerates(monkeypatch, store):
    """A cache older than TEST_ITEM_TTL is treated as a miss -> regenerate."""
    stale = _items("OLD_SKILL")
    await store.cache_test_items(
        "u_stale", "gd_test", [it.model_dump() for it in stale], ts=1.0
    )
    fresh = _items("GD_STANCE_CLARITY", "GD_REBUTTAL")

    async def _fake_gen(user_id, task_type, n_items=4):
        return fresh

    monkeypatch.setattr(
        "app.services.session_service.generate_test_items", _fake_gen
    )

    _sid, state = await svc.start_session("u_stale", GD_PREP_NODE, test_mode=True)
    assert state["probe_items"] == [it.model_dump() for it in fresh]


async def test_no_cache_sync_fallback(monkeypatch, store):
    """No precache (no prior PREP) -> TEST start generates synchronously."""
    fresh = _items("GD_STANCE_CLARITY")

    async def _fake_gen(user_id, task_type, n_items=4):
        assert task_type == "gd_test"
        return fresh

    monkeypatch.setattr(
        "app.services.session_service.generate_test_items", _fake_gen
    )

    _sid, state = await svc.start_session("u_none", GD_PREP_NODE, test_mode=True)
    assert state["probe_items"] == [it.model_dump() for it in fresh]
