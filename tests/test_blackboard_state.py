import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.services.session_service import _new_state


def test_new_state_has_blackboard_key():
    state = _new_state("u1", "s1", "comm_01_self_intro", [])
    assert "blackboard" in state
    assert state["blackboard"] is None
    # neighbor untouched — blackboard was inserted next to personas
    assert state["personas"] is None
