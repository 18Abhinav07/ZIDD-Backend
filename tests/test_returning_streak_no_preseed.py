"""P1 — a returning learner's clean_streak is NOT pre-seeded from a prior pass.

start_session used to set clean_streak = 1 whenever storage reported the learner
had clean-passed this node before. With ADVANCE_STREAK = 2 that meant ONE clean
answer this session re-advanced them, and a single borderline 0.7 answer tripped
the clean_streak>=1 challenge gate — both without re-proving any retained skill.
The streak now starts at 0; retained mastery still loads via current_mastery, and
a genuinely strong return still reaches challenge through the CEILING_SCORE /
session_attempts escape (route_node), independent of the streak.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio

NODE = "comm_01_self_intro"   # a coaching node: is_test False, skips the probe load


class _FakeStore:
    """Minimal store: returns a prior clean-passed progression row for NODE."""

    def __init__(self, progression):
        self._progression = progression

    async def ensure_profile(self, *a, **k):
        pass

    async def create_session(self, *a, **k):
        pass

    async def load_context(self, *a, **k):
        return []

    async def get_weaknesses(self, *a, **k):
        return []

    async def get_progression(self, *a, **k):
        return self._progression


@pytest.fixture
def _fake_store(monkeypatch):
    def _install(progression):
        monkeypatch.setattr(svc, "get_storage", lambda: _FakeStore(progression))
    yield _install
    svc.SessionStore.clear()


async def test_prior_clean_pass_does_not_preseed_streak(_fake_store):
    _fake_store([
        {"node_id": NODE, "ema": 0.8, "attempts": 3, "clean_pass": True},
    ])

    _sid, state = await svc.start_session("ret-1", NODE)

    assert state["clean_streak"] == 0          # NOT pre-seeded to 1
    assert state["current_mastery"] == 0.8     # retained mastery still loads
    assert state["attempts"] == 3              # prior attempt count still loads


async def test_no_prior_progress_also_starts_streak_zero(_fake_store):
    _fake_store([])   # brand-new learner, no progression row

    _sid, state = await svc.start_session("ret-2", NODE)

    assert state["clean_streak"] == 0
    assert state["current_mastery"] == 0.0     # cold start
