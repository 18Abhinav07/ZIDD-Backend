"""Phase 2.3 — session_service writes through the storage dispatcher OFFLINE.

The felt-personalization fix: with Postgres unreachable (qwen-dev), the old
`_db()` path yielded None and every track call was a silent no-op, so memory and
weaknesses never accumulated. Phase 2.3 routes through `get_storage()`, which
returns the LOCAL SQLite backend when `ai_backend == "local"`. These tests point
that backend at a tmp db and assert the engine actually persists:

  (a) every scored turn lands a row in the local `turns` table,
  (b) a low-scoring turn bumps an aggregated weakness row,
  (c) start_session hydrates `state["weakness_context"]` from prior weaknesses.

Reuses the test_engine_loop AI-boundary monkeypatch pattern so the decision loop
runs with no network and no Ollama.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services import session_service as svc  # noqa: E402
from app.storage import get_storage, reset_storage  # noqa: E402

pytestmark = pytest.mark.asyncio

NODE = "comm_01_self_intro"


# ---------- AI-boundary fakes (mirror test_engine_loop) ----------

class _Scores:
    def __init__(self, scores, on_task=None, english=None, affect=None):
        self._it = iter(scores)
        self._on_task = iter(on_task) if on_task is not None else None
        self._english = iter(english) if english is not None else None
        self._affect = iter(affect) if affect is not None else None

    async def __call__(self, node, messages, user_input, behavior=None):
        score = next(self._it)
        return DiagnosisEval(
            score=score,
            understanding="x",
            errors=[] if score >= 0.6 else ["e"],
            strengths=["s"] if score >= 0.6 else [],
            next_focus="n",
            on_task=next(self._on_task) if self._on_task is not None else True,
            english=next(self._english) if self._english is not None else True,
            affect=next(self._affect) if self._affect is not None else "neutral",
        )


async def _fake_stream(spec):
    for tok in ("ok", " ", "done"):
        yield tok


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Point the dispatcher at a fresh tmp SQLite db for this test."""
    db = tmp_path / "track.db"
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORE_PATH", str(db))
    get_settings.cache_clear()
    reset_storage()
    yield get_storage()
    reset_storage()
    get_settings.cache_clear()
    svc.SessionStore.clear()


@pytest.fixture(autouse=True)
def _patch_ai(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer", None, raising=False
    )
    monkeypatch.setattr("app.services.session_service.stream_generation", _fake_stream)

    async def _fake_summary(node, messages):
        return "summary"

    monkeypatch.setattr("app.services.session_service.summarize_session", _fake_summary)
    yield


def _set_eval(monkeypatch, scores, on_task=None, english=None, affect=None):
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        _Scores(scores, on_task=on_task, english=english, affect=affect),
    )


async def _drain(agen):
    async for _ in agen:
        pass


# ---------- tests ----------

async def test_scored_turn_logged_to_local_store(monkeypatch, store):
    """A scored turn persists a turn row via the dispatcher (offline)."""
    _set_eval(monkeypatch, [0.8])
    sid, state = await svc.start_session("u_track", NODE)
    state["turn_count"] = 1  # skip opening; this is a real scored answer
    await _drain(svc.run_turn(sid, "I am a software engineer from Pune."))

    turns = await store.get_turns(sid)
    assert len(turns) == 1
    assert turns[0]["user_id"] == "u_track"
    assert turns[0]["score"] == pytest.approx(0.8)


async def test_low_score_bumps_weakness(monkeypatch, store):
    """A low-scoring turn aggregates a weakness row via the dispatcher."""
    _set_eval(monkeypatch, [0.2])
    sid, state = await svc.start_session("u_weak", NODE)
    state["turn_count"] = 1
    await _drain(svc.run_turn(sid, "uh i dunno"))

    weaknesses = await store.get_weaknesses("u_weak")
    assert weaknesses, "low-scoring turn should bump a weakness row"
    assert weaknesses[0]["hit_count"] >= 1


async def test_start_session_hydrates_weakness_context(store):
    """start_session loads prior weaknesses into state['weakness_context']."""
    from app.content.registry import module_of

    task_type = module_of(NODE)
    await store.bump_weakness(
        "u_returning", task_type, "STRUCTURE_STAR_METHOD", 0.3, raw="no STAR structure"
    )

    _sid, state = await svc.start_session("u_returning", NODE)
    wc = state.get("weakness_context")
    assert wc, "weakness_context must be populated from prior weaknesses"
    assert any(w["skill_id"] == "STRUCTURE_STAR_METHOD" for w in wc)
