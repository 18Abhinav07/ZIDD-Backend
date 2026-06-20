"""LocalStore money-write lock is a threading.Lock (thread-safe, loop-free).

The connection is opened check_same_thread=False, so FastAPI's threadpool can
touch it from several OS threads. The previous guard was an asyncio.Lock, which
is NOT thread-safe and binds to one event loop — concurrent grants driven from
different threads' loops could race (lost updates) and the loop coupling was the
most plausible cause of a stale-worker /health 'sqlite_writable:false' false
negative. These tests pin the correct behavior: many threads granting credits
concurrently land EVERY increment (no lost updates, no errors), and ping_writable
works regardless of which loop calls it.
"""
import asyncio
import os
import threading

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.storage.local_store import LocalStore  # noqa: E402


def test_lock_is_thread_lock_not_asyncio():
    store = LocalStore(":memory:")
    # threading.Lock() returns a _thread.lock; the public marker is being a sync
    # context manager that is NOT an asyncio.Lock.
    assert not isinstance(store._lock, asyncio.Lock)
    assert hasattr(store._lock, "acquire") and hasattr(store._lock, "release")


@pytest.mark.asyncio
async def test_ping_writable_true(tmp_path):
    store = LocalStore(str(tmp_path / "w.db"))
    assert await store.ping_writable() is True


def test_concurrent_grants_from_many_threads_lose_nothing(tmp_path):
    # Drive grant_credits from THREADS = separate OS threads, each with its own
    # event loop, all hitting the one shared connection. With a correct
    # threading.Lock every increment lands; a non-thread-safe asyncio.Lock could
    # interleave writes and lose updates (or error across loops).
    store = LocalStore(str(tmp_path / "c.db"))
    uid = "racer"
    asyncio.run(store.ensure_profile(uid))
    asyncio.run(store.grant_credits(uid, 100, "seed"))

    THREADS = 8
    PER_THREAD = 50
    errors: list[Exception] = []

    def worker():
        async def do():
            for _ in range(PER_THREAD):
                await store.grant_credits(uid, 1, "concurrent")
        try:
            asyncio.run(do())
        except Exception as e:  # pragma: no cover - failure path
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"thread errors: {errors}"
    final = asyncio.run(store.get_credits(uid))
    assert final == 100 + THREADS * PER_THREAD   # every increment landed, none lost
