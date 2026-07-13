import asyncio

from fastapi.testclient import TestClient

from app.main import app

AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def test_profile_apis_reject_stale_token_without_recreating_profile(store):
    client = TestClient(app)
    assert _run(store.get_profile("test_user")) is None

    responses = [
        client.get("/me/gate", headers=AUTH),
        client.get("/me", headers=AUTH),
        client.get("/me/activity", headers=AUTH),
        client.patch("/me/preferences", headers=AUTH, json={"active_module": "interview"}),
        client.get("/onboarding/state", headers=AUTH),
        client.patch("/onboarding/state", headers=AUTH, json={"draft": {"primary_motive": "career"}}),
        client.post(
            "/onboarding/complete",
            headers=AUTH,
            json={
                "display_name": "Ravi",
                "primary_motive": "career",
                "career_profile": {"target_roles": ["Data Analyst"]},
            },
        ),
    ]

    assert [response.status_code for response in responses] == [401, 401, 401, 401, 401, 401, 401]
    assert _run(store.get_profile("test_user")) is None


def test_me_gate_returns_only_route_state(store):
    _run(store.ensure_profile("test_user", name="Asha", email="asha@example.com"))
    _run(
        store.complete_onboarding(
            user_id="test_user",
            display_name="Asha",
            primary_motive="school",
            school_profile={"school_name": "City Public School"},
            career_profile={"resume_text": "private resume text"},
        )
    )

    client = TestClient(app)
    response = client.get("/me/gate", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "user_id": "test_user",
        "onboarding": {
            "completed": True,
            "primary_motive": "school",
        },
        "home": "/school",
    }
    assert "email" not in body
    assert "career_profile" not in body
    assert "resume_text" not in str(body)


def test_me_gate_routes_career_users_to_career_home(store):
    _run(store.ensure_profile("test_user", name="Ravi", email="ravi@example.com"))
    _run(
        store.complete_onboarding(
            user_id="test_user",
            display_name="Ravi",
            primary_motive="career",
            school_profile={},
            career_profile={"target_roles": ["Data Analyst"]},
        )
    )

    client = TestClient(app)
    response = client.get("/me/gate", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["home"] == "/career"


def test_global_school_onboarding_routes_to_school_and_defers_class_to_school_profile(store):
    _run(store.ensure_profile("test_user", name="Asha", email="asha@example.com"))

    client = TestClient(app)
    response = client.post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Asha",
            "primary_motive": "school",
            "school_profile": {
                "school_name": "City Public School",
                "learning_goal": "Read chapters with confidence",
                "class_no": 5,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["destination"] == "/school"

    profile = _run(store.get_profile("test_user"))
    assert profile["primary_motive"] == "school"
    assert profile["onboarding_completed_at"]
    assert profile["school_profile"] == {
        "school_name": "City Public School",
        "learning_goal": "Read chapters with confidence",
    }
    assert "class_no" not in profile["school_profile"]

    me = client.get("/me", headers=AUTH)
    assert me.status_code == 200
    body = me.json()
    assert body["onboarding"]["completed"] is True
    assert body["onboarding"]["primary_motive"] == "school"
    assert body["school_profile"]["school_name"] == "City Public School"
    assert "class_no" not in body["school_profile"]


def test_career_onboarding_requires_personalization_when_resume_missing(store):
    _run(store.ensure_profile("test_user"))
    client = TestClient(app)

    empty = client.post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Ravi",
            "primary_motive": "career",
            "career_profile": {},
        },
    )
    assert empty.status_code == 422

    useful = client.post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Ravi",
            "primary_motive": "career",
            "career_profile": {
                "target_roles": ["Data Analyst"],
                "interview_goals": ["Explain projects clearly"],
                "gd_topic_ids": ["ai-in-education"],
                "custom_gd_topics": ["Indian startup funding"],
            },
        },
    )

    assert useful.status_code == 200
    assert useful.json()["destination"] == "/career"

    me = client.get("/me", headers=AUTH).json()
    assert me["onboarding"]["primary_motive"] == "career"
    assert me["career_profile"]["target_roles"] == ["Data Analyst"]
    assert me["career_profile"]["resume_present"] is False


def test_me_and_onboarding_do_not_expose_raw_resume_text(store):
    _run(store.ensure_profile("test_user", name="Ravi"))
    client = TestClient(app)

    response = client.post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Ravi",
            "primary_motive": "career",
            "career_profile": {
                "resume_text": "PRIVATE resume: payment incident, internal project, phone 9999999999",
                "target_roles": ["Backend Engineer"],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["career_profile"]["resume_present"] is True
    assert "resume_text" not in body["career_profile"]
    assert "PRIVATE resume" not in str(body)

    me = client.get("/me", headers=AUTH)
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["career_profile"]["resume_present"] is True
    assert "resume_text" not in me_body["career_profile"]
    assert "PRIVATE resume" not in str(me_body)


def test_onboarding_state_round_trips_drafts(store):
    _run(store.ensure_profile("test_user", name="Ravi"))
    client = TestClient(app)

    before = client.get("/onboarding/state", headers=AUTH)
    assert before.status_code == 200
    assert before.json()["draft"] == {}
    assert before.json()["display_name"] == "Ravi"
    assert before.json()["completed"] is False

    patched = client.patch(
        "/onboarding/state",
        headers=AUTH,
        json={
            "draft": {
                "step": "career-details",
                "primary_motive": "career",
                "target_roles": ["Product Manager"],
            }
        },
    )
    assert patched.status_code == 200

    after = client.get("/onboarding/state", headers=AUTH)
    assert after.json()["draft"] == {
        "step": "career-details",
        "primary_motive": "career",
        "target_roles": ["Product Manager"],
    }


def test_me_activity_summarizes_empty_and_school_progress(store):
    _run(store.ensure_profile("test_user"))
    client = TestClient(app)

    empty = client.get("/me/activity", headers=AUTH)
    assert empty.status_code == 200
    assert empty.json()["school"]["results_count"] == 0
    assert empty.json()["school"]["recent_classes"] == []
    assert empty.json()["recommendations"]
    assert store.activity_snapshot_calls == 1

    _run(
        store.record_assessment_result(
            user_id="test_user",
            test_id="c2_ch01_test",
            class_no=2,
            kind="chapter",
            score=0.5,
            passed=False,
            by_skill=[
                {"skill": "new_words", "correct": 0, "total": 1},
                {"skill": "comprehension", "correct": 1, "total": 1},
            ],
        )
    )

    activity = client.get("/me/activity", headers=AUTH)
    assert activity.status_code == 200
    body = activity.json()
    assert store.activity_snapshot_calls == 2
    assert body["school"]["results_count"] == 1
    assert body["school"]["recent_classes"] == [2]
    assert body["school"]["weak_skills"] == ["new_words"]
    assert body["school"]["average_score"] == 0.5


def test_me_activity_accepts_json_string_snapshot(monkeypatch, store):
    _run(store.ensure_profile("test_user"))

    async def _json_snapshot(user_id: str) -> dict:
        assert user_id == "test_user"
        return {
            "school_results": '[{"class_no":"3","score":"0.75"}]',
            "school_skill_mastery": '[{"skill":"grammar","ema":"0.45","attempts":"2"}]',
            "school_weak_skills": '["grammar"]',
            "progression": '[{"attempts":"4","clean_pass":true}]',
            "weaknesses": '[{"task_type":"interview","skill_id":"structure","hit_count":"1","last_raw":null}]',
        }

    monkeypatch.setattr(store, "get_activity_snapshot", _json_snapshot)
    client = TestClient(app)

    response = client.get("/me/activity", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["school"]["results_count"] == 1
    assert body["school"]["recent_classes"] == [3]
    assert body["school"]["average_score"] == 0.75
    assert body["school"]["weak_skills"] == ["grammar"]
    assert body["school"]["skill_mastery"] == [
        {"skill": "grammar", "mastery": 0.45, "attempts": 2}
    ]
    assert body["career"]["attempts"] == 4
    assert body["career"]["weaknesses"] == [
        {
            "task_type": "interview",
            "skill_id": "structure",
            "hit_count": 1,
            "last_raw": "",
        }
    ]


def test_me_activity_degrades_when_snapshot_unavailable(monkeypatch, store):
    _run(store.ensure_profile("test_user"))

    async def _broken_snapshot(user_id: str) -> dict:
        raise RuntimeError("activity tables unavailable")

    monkeypatch.setattr(store, "get_activity_snapshot", _broken_snapshot)
    client = TestClient(app)

    response = client.get("/me/activity", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["degraded"] is True
    assert body["school"]["results_count"] == 0
    assert body["school"]["recent_classes"] == []
    assert body["career"]["attempts"] == 0
    assert body["recommendations"]
