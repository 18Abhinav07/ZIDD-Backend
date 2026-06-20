"""Root pytest config — runs before any app import.

The app now fails at boot unless ZIDD_JWT_SECRET is set, and the test-auth
bypass requires an explicit ZIDD_ALLOW_TEST_AUTH=1 opt-in. Set both here so
the suite can boot the app and hit endpoints without auth headers. setdefault
means a real env value (if exported) always wins.
"""
import os
import tempfile

os.environ.setdefault("ZIDD_JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("ZIDD_ALLOW_TEST_AUTH", "1")

# Test-isolation: pin the default LocalStore onto a throwaway, per-process path so
# the suite never reads or writes the dev `.zidd_local.db`. That file is also the
# live store of a running uvicorn, and persists across runs — without this, any
# storage-touching test that does not set its own path leaks persisted progression
# between runs (a learner's loaded `attempts` carries over and flips clean-pass
# assertions: the documented `.zidd_local.db` pollution). The pid keeps each run's
# store fresh; tests that need a dedicated store still override LOCAL_STORE_PATH
# (setdefault lets those and any real CI value win).
os.environ.setdefault(
    "LOCAL_STORE_PATH",
    os.path.join(tempfile.gettempdir(), f"zidd_test_store_{os.getpid()}.db"),
)
