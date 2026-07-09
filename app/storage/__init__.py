"""Storage surface.

Runtime product data is Supabase/Postgres only. Qwen/Ollama may run locally,
but learner profiles, sessions, credits, progress, and memory must never fall
back to a local product database.
"""

from app.storage.pg_store import PgStore

# The method surface every backend implements (documentation + Phase-2 contract):
#   ensure_profile(user_id, name="", email=None, google_sub=None)
#   get_profile(user_id) -> dict | None
#   get_profile_by_email(email) -> dict | None
#   get_profile_by_google_sub(google_sub) -> dict | None
#   update_onboarding_state(user_id, draft) -> dict
#   complete_onboarding(user_id, display_name, primary_motive, school_profile, career_profile) -> dict
#   create_session(session_id, user_id, task_type, module_id, node_id, test_mode=False,
#                  career_context=None, scenario_config=None, persona_roster=None,
#                  context_hash="default")
#   end_session(session_id, final_summary="", avg_score=0.0)
#   record_turn(session_id, user_id, node_id, score, on_task, english, affect)
#   get_turns(session_id) -> list[dict]
#   upsert_mastery(user_id, node_id, ema, attempts, clean_pass=False, node_completed=False)
#   get_progression(user_id) -> list[dict]
#   get_module_passrate(user_id, node_ids) -> (clean, total)
#   bump_weakness(user_id, task_type, skill_id, score, raw="")
#   get_weaknesses(user_id, task_type=None) -> list[dict]
#   write_memory(user_id, session_id, node_id, content, task_type="") -> bool
#   load_context(user_id, task_type, k=3) -> list[dict]

_cached: PgStore | None = None


def get_storage() -> PgStore:
    """Return the cloud storage backend, memoized per process."""
    global _cached
    if _cached is None:
        _cached = PgStore()
    return _cached


def reset_storage() -> None:
    global _cached
    _cached = None
