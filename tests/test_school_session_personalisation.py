# tests/test_school_session_personalisation.py
"""A school 'Learn' session is personalised by the learner's assessment history.

The dedicated school per-skill mastery (folded from exact-graded chapter tests)
feeds the live coaching session: start_session surfaces the learner's weakest
school skills into weakness_context, so the opening warms up on a REAL gap.
"""
import os
import tempfile

os.environ["AI_BACKEND"] = "local"
_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["LOCAL_STORE_PATH"] = _DB.name
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest

from app.config import get_settings
from app.services import session_service as svc
from app.storage import get_storage, reset_storage

# A real school chapter level node (coaching, not a test) — verified in the zoo
# chapter; task_type_of resolves it to SCHOOL_ENGLISH via its class_no.
SCHOOL_NODE = "c2_ch06_l3_grammar"


@pytest.fixture(autouse=True)
def _isolate_store(monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    store = get_storage()
    store._conn.execute("DELETE FROM school_results")
    store._conn.execute("DELETE FROM school_skill_mastery")
    store._conn.commit()
    yield
    reset_storage()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_school_session_surfaces_weak_assessment_skills():
    store = get_storage()
    await store.ensure_profile("u_school")
    # The learner failed a chapter test on 'asking_questions' and 'comprehension'.
    await store.record_assessment_result(
        "u_school", "c2_ch06_test", 2, "chapter", 0.0, False,
        [{"skill": "asking_questions", "correct": 0, "total": 2},
         {"skill": "comprehension", "correct": 0, "total": 2}],
    )
    _sid, state = await svc.start_session("u_school", SCHOOL_NODE)
    surfaced = {w["skill_id"] for w in state["weakness_context"]}
    # humanized + present so the opening prompt can target them
    assert "asking questions" in surfaced
    assert "comprehension" in surfaced


@pytest.mark.asyncio
async def test_school_session_surfaces_stale_mastered_skills_for_review(monkeypatch):
    # The store decides which mastered skills are stale (time-based); here we stub
    # it to verify the SESSION wires review skills into the opening context.
    from app.storage.local_store import LocalStore

    async def _fake_review(self, user_id, **kw):
        return ["prepositions", "asking_questions"]

    monkeypatch.setattr(LocalStore, "get_school_review_skills", _fake_review)
    store = get_storage()
    await store.ensure_profile("u_rev")
    _sid, state = await svc.start_session("u_rev", SCHOOL_NODE)
    assert state["review_context"] == ["prepositions", "asking questions"]  # humanized


@pytest.mark.asyncio
async def test_school_session_clean_history_surfaces_no_weak_skills():
    store = get_storage()
    await store.ensure_profile("u_clean")
    await store.record_assessment_result(
        "u_clean", "c2_ch06_test", 2, "chapter", 1.0, True,
        [{"skill": "asking_questions", "correct": 2, "total": 2}],
    )
    _sid, state = await svc.start_session("u_clean", SCHOOL_NODE)
    assert state["weakness_context"] == []
