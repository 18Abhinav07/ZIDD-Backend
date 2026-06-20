"""Finding #14 — PgStore.write_memory must accept the `score` kwarg that
LocalStore has and that session_service.end_session passes, so the cloud backend
does not raise a TypeError that a caller's bare `except` would silently swallow
(dropping end-of-session memory).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import inspect

import pytest

from app.storage.pg_store import PgStore


def test_pg_write_memory_signature_has_score():
    params = inspect.signature(PgStore.write_memory).parameters
    assert "score" in params
    assert params["score"].default == 0.0


@pytest.mark.asyncio
async def test_pg_write_memory_accepts_score_kwarg_without_typeerror():
    store = PgStore()
    # Offline -> degrades to False, but the score kwarg must NOT raise TypeError.
    result = await store.write_memory(
        "u", "s", "n", "Strengths: x\nWatch: y\nNext focus: z", task_type="t", score=0.9
    )
    assert result is False
