"""Storage surface + backend dispatcher.

One interface, two backends:
  - LocalStore (SQLite) — picked when ai_backend == "local" or Postgres is
    unreachable. Source of truth during qwen-dev so memory works OFFLINE.
  - PgStore — pgvector + repo, picked for cloud. Same signatures, so the
    cloud swap is config-only (flip AI_BACKEND).

`get_storage()` is the only entry point the app calls. It is memoized so the
SQLite connection is reused across the process; cache resets when settings
change (tests call get_settings.cache_clear()).
"""
from app.config import get_settings
from app.storage.local_store import LocalStore
from app.storage.pg_store import PgStore

# The method surface every backend implements (documentation + Phase-2 contract):
#   ensure_profile(user_id, name="")
#   get_profile(user_id) -> dict | None
#   create_session(session_id, user_id, task_type, module_id, node_id)
#   end_session(session_id, final_summary="", avg_score=0.0)
#   record_turn(session_id, user_id, node_id, score, on_task, english, affect)
#   get_turns(session_id) -> list[dict]
#   upsert_mastery(user_id, node_id, ema, attempts, clean_pass=False)
#   get_progression(user_id) -> list[dict]
#   get_module_passrate(user_id, node_ids) -> (clean, total)
#   bump_weakness(user_id, task_type, skill_id, score, raw="")
#   get_weaknesses(user_id, task_type=None) -> list[dict]
#   write_memory(user_id, session_id, node_id, content, task_type="") -> bool
#   load_context(user_id, task_type, k=3) -> str

_cached: LocalStore | PgStore | None = None


def get_storage() -> "LocalStore | PgStore":
    """Return the active storage backend, memoized per process.

    Local when ai_backend == "local"; otherwise Postgres (which itself degrades
    to no-op if unreachable). Reset by clearing this module's cache via
    reset_storage() — tests that flip AI_BACKEND call get_settings.cache_clear()
    then get_storage() fresh.
    """
    global _cached
    settings = get_settings()
    want_local = settings.ai_backend == "local"
    # Rebuild if backend kind changed since last build.
    if _cached is not None:
        is_local = isinstance(_cached, LocalStore)
        if is_local == want_local:
            return _cached
    if want_local:
        path = getattr(settings, "local_store_path", "") or ".zidd_local.db"
        _cached = LocalStore(path)
    else:
        _cached = PgStore()
    return _cached


def reset_storage() -> None:
    global _cached
    _cached = None
