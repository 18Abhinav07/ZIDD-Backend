"""Root pytest config — runs before any app import.

The app now fails at boot unless ZIDD_JWT_SECRET is set, and the test-auth
bypass requires an explicit ZIDD_ALLOW_TEST_AUTH=1 opt-in. Set both here so
the suite can boot the app and hit endpoints without auth headers. setdefault
means a real env value (if exported) always wins.
"""
import os

os.environ.setdefault("ZIDD_JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("ZIDD_ALLOW_TEST_AUTH", "1")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)
