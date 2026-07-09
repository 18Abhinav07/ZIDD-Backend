from fastapi.testclient import TestClient

from app.main import app

AUTH = {"Authorization": "Bearer test_token"}


def test_school_submit_marks_result_saved_when_progress_persists(store):
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    client = TestClient(app)

    response = client.post(
        "/school/test/c2_ch01_test/submit",
        json={"answers": {}},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert response.json()["degraded"] is False


def test_school_submit_reports_unsaved_progress_when_persistence_fails(monkeypatch, store):
    import asyncio

    async def broken_record_assessment_result(**_kwargs):
        raise RuntimeError("database unavailable")

    asyncio.run(store.ensure_profile("test_user"))
    monkeypatch.setattr(store, "record_assessment_result", broken_record_assessment_result)
    client = TestClient(app)

    response = client.post(
        "/school/test/c2_ch01_test/submit",
        json={"answers": {}},
        headers=AUTH,
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "progress_not_saved"


def test_school_progress_reports_structured_storage_failure(monkeypatch, store):
    import asyncio

    async def broken_get_school_results(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    asyncio.run(store.ensure_profile("test_user"))
    monkeypatch.setattr(store, "get_school_results", broken_get_school_results)
    client = TestClient(app)

    response = client.get("/school/progress?class_no=2", headers=AUTH)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "progress_unavailable"
    assert response.json()["detail"]["class_no"] == 2


def test_duplicate_school_submit_does_not_increment_mastery_attempts_twice(store):
    import asyncio

    asyncio.run(store.ensure_profile("test_user"))
    client = TestClient(app)
    payload = {
        "answers": {
            "c2_ch01_test_i1": "school",
            "c2_ch01_test_i2": "pencil",
            "c2_ch01_test_i3": "dog",
            "c2_ch01_test_i4": "book",
            "c2_ch01_test_i5": "I like my school.",
        }
    }

    first = client.post("/school/test/c2_ch01_test/submit", json=payload, headers=AUTH)
    second = client.post("/school/test/c2_ch01_test/submit", json=payload, headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    mastery = asyncio.run(store.get_school_skill_mastery("test_user"))
    assert mastery
    assert {row["attempts"] for row in mastery} == {1}
