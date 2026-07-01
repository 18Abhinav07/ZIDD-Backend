"""NCERT school rebuild — Phase 2: the live assessment API.

End-to-end through the real app: browse the class -> chapters, fetch a test
(answer keys stripped), submit answers, and get a scored report. This is the test
path the school feature never had.
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

from fastapi.testclient import TestClient  # noqa: E402

from app.content import curriculum as cur  # noqa: E402
from app.main import app  # noqa: E402

AUTH = {"Authorization": "Bearer test_token"}  # -> user_id "test_user"
client = TestClient(app)


def test_browse_classes_and_chapters():
    r = client.get("/school/classes", headers=AUTH)
    assert r.status_code == 200
    assert any(c["class_no"] == 2 for c in r.json())

    d = client.get("/school/class/2", headers=AUTH)
    assert d.status_code == 200
    body = d.json()
    assert body["chapters"][0]["ncert_unit"] == "First Day at School"
    assert len(body["chapters"][0]["levels"]) == 4
    assert body["chapters"][0]["chapter_test_id"] == "c2_ch01_test"
    assert [m["at_percent"] for m in body["milestones"]] == [30, 60, 100]
    assert len(body["chapters"]) >= 6


def test_served_test_never_leaks_the_answer_key():
    r = client.get("/school/test/c2_ch01_test", headers=AUTH)
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert "answer_key" not in item and "accept" not in item
        assert "prompt" in item and "type" in item


def test_submit_correct_passes_with_report():
    test = cur.get_chapter("c2_ch01_first_day").chapter_test
    correct = {i.id: i.answer_key for i in test.items}
    r = client.post("/school/test/c2_ch01_test/submit",
                    json={"answers": correct}, headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is True and body["score"] == 1.0
    assert body["weak_skills"] == []
    assert {s["skill"] for s in body["by_skill"]} == {"new_words", "comprehension", "nouns", "use"}


def test_submit_wrong_fails_and_names_weak_skills():
    r = client.post("/school/test/c2_ch01_test/submit",
                    json={"answers": {}}, headers=AUTH)
    body = r.json()
    assert body["passed"] is False and body["correct"] == 0
    assert set(body["weak_skills"]) == {"new_words", "comprehension", "nouns", "use"}


def test_milestone_unlocks_at_class_progress():
    n = client.get("/school/class/2", headers=AUTH).json()
    total = len(n["chapters"])
    # ~33% done -> the 30% check unlocks
    two = client.get(f"/school/class/2/milestone?chapters_done=2", headers=AUTH).json()
    assert two["due"]["at_percent"] == 30
    # whole class done, 30+60 already taken -> the 100% term review unlocks
    done = client.get(
        f"/school/class/2/milestone?chapters_done={total}&fired=30,60", headers=AUTH
    ).json()
    assert done["due"]["at_percent"] == 100


def test_unknown_test_is_404():
    assert client.get("/school/test/nope", headers=AUTH).status_code == 404
