# tests/test_school_routes.py
"""School API: submit persists a durable, per-skill learning record (Phase B1).

A graded submit folds per-skill ratios into the learner's school mastery and the
/school/progress endpoint reads it back — so progress survives a cache clear and
the live tutor can target real weak spots.
"""
import os
import tempfile

os.environ["AI_BACKEND"] = "local"
_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["LOCAL_STORE_PATH"] = _DB.name
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ["ZIDD_ALLOW_TEST_AUTH"] = "1"
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.content import curriculum as cur
from app.main import app
from app.storage import get_storage, reset_storage

AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"
TEST_ID = "c2_ch06_test"


@pytest.fixture(autouse=True)
def _isolate_store(monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_PATH", _DB.name)
    get_settings.cache_clear()
    reset_storage()
    # Clear the school tables so each test starts from a clean learning record
    # (the temp DB file is shared module-wide).
    store = get_storage()
    store._conn.execute("DELETE FROM school_results")
    store._conn.execute("DELETE FROM school_skill_mastery")
    store._conn.commit()
    yield
    reset_storage()
    get_settings.cache_clear()


def _keys() -> dict:
    a = cur.find_assessment(TEST_ID)
    return {i.id: i.answer_key for i in a.items}


def test_submit_persists_result_and_progress_reflects_pass():
    client = TestClient(app)
    r = client.post(f"/school/test/{TEST_ID}/submit", json={"answers": _keys()}, headers=AUTH)
    assert r.status_code == 200 and r.json()["passed"] is True

    prog = client.get("/school/progress", headers=AUTH).json()
    assert TEST_ID in prog["passed_tests"]
    assert prog["weak_skills"] == []                      # all-correct -> no weak skills
    assert prog["overall"] == 1.0
    assert all(m["mastery"] == 1.0 for m in prog["skill_mastery"])
    assert {m["skill"] for m in prog["skill_mastery"]} == {"new_words", "comprehension", "grammar"}


def test_submit_all_wrong_surfaces_weak_skills():
    client = TestClient(app)
    wrong = {k: "zzz_wrong" for k in _keys()}
    r = client.post(f"/school/test/{TEST_ID}/submit", json={"answers": wrong}, headers=AUTH)
    assert r.status_code == 200 and r.json()["passed"] is False

    prog = client.get("/school/progress", headers=AUTH).json()
    assert TEST_ID not in prog["passed_tests"]
    assert set(prog["weak_skills"]) == {"new_words", "comprehension", "grammar"}


def test_retaking_a_failed_test_recovers_mastery_end_to_end():
    client = TestClient(app)
    wrong = {k: "zzz_wrong" for k in _keys()}
    client.post(f"/school/test/{TEST_ID}/submit", json={"answers": wrong}, headers=AUTH)
    # two clean retakes pull each skill's EMA back above the weak line
    client.post(f"/school/test/{TEST_ID}/submit", json={"answers": _keys()}, headers=AUTH)
    client.post(f"/school/test/{TEST_ID}/submit", json={"answers": _keys()}, headers=AUTH)

    prog = client.get("/school/progress", headers=AUTH).json()
    assert prog["weak_skills"] == []                     # recovered on demonstrated success
    assert TEST_ID in prog["passed_tests"]               # latest submit upserts to passed


def test_progress_scopes_by_class():
    client = TestClient(app)
    client.post(f"/school/test/{TEST_ID}/submit", json={"answers": _keys()}, headers=AUTH)
    in_class = client.get("/school/progress", params={"class_no": 2}, headers=AUTH).json()
    other_class = client.get("/school/progress", params={"class_no": 5}, headers=AUTH).json()
    assert TEST_ID in in_class["passed_tests"]
    assert other_class["results"] == []                  # nothing recorded for class 5
