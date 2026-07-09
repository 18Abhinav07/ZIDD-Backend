import asyncio

from fastapi.testclient import TestClient

from app.main import app


AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def test_career_activity_does_not_recommend_completed_personalization(store):
    _run(store.ensure_profile("test_user", name="Raptor", email="raptor@example.com"))
    _run(
        store.complete_onboarding(
            "test_user",
            display_name="Raptor",
            primary_motive="career",
            school_profile={},
            career_profile={
                "resume_text": "Backend engineer with API, database, and distributed systems projects.",
                "target_roles": ["Backend Software Engineer"],
                "interview_goals": ["project deep dives", "system design communication"],
                "gd_topic_ids": ["remote-work"],
                "custom_gd_topics": ["AI in engineering hiring"],
            },
        )
    )

    response = TestClient(app).get("/me/activity", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["career"]["profile_complete"] is True
    titles = {item["title"] for item in body["recommendations"]}
    assert "Complete career personalization" not in titles


def test_incomplete_career_activity_recommends_personalization(store):
    _run(store.ensure_profile("test_user", name="Raptor", email="raptor@example.com"))
    profile = store._profile("test_user")
    profile["primary_motive"] = "career"
    profile["onboarding_completed_at"] = 1.0
    profile["career_profile"] = {}

    response = TestClient(app).get("/me/activity", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["career"]["profile_complete"] is False
    titles = {item["title"] for item in body["recommendations"]}
    assert "Complete career personalization" in titles


def test_career_activity_counts_durable_node_attempts_not_mastery_updates(store):
    _run(store.ensure_profile("test_user", name="Raptor", email="raptor@example.com"))
    _run(
        store.complete_onboarding(
            "test_user",
            display_name="Raptor",
            primary_motive="career",
            school_profile={},
            career_profile={
                "target_roles": ["Backend Software Engineer"],
                "interview_goals": ["mock interview practice"],
            },
        )
    )
    _run(
        store.upsert_mastery(
            "test_user",
            "int_01_elevator_pitch",
            ema=1.0,
            attempts=4,
            clean_pass=False,
            node_completed=True,
        )
    )
    _run(
        store.record_node_attempt(
            session_id="attempt-1",
            user_id="test_user",
            node_id="int_01_elevator_pitch",
            starting_mastery=0.0,
        )
    )

    response = TestClient(app).get("/me/activity", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["career"]["completed_nodes"] == 1
    assert body["career"]["attempts"] == 1


def test_learning_graph_returns_public_career_profile_without_resume_text(store):
    _run(store.ensure_profile("test_user", name="Raptor", email="raptor@example.com"))
    profile = store._profile("test_user")
    profile["career_profile"] = {
        "resume_text": "PRIVATE resume text should not leave /me.",
        "target_roles": ["Backend Software Engineer"],
    }
    _run(
        store.upsert_learner_skill_profile(
            user_id="test_user",
            domain="career",
            skill_id="gd_02_support_with_evidence",
            module_id="group_discussion",
            task_type="gd_prep",
            mastery=0.0,
            readiness=0.82,
            confidence=0.8,
            attempts=5,
            strengths_json=["clear stance"],
            gaps_json=["needs evidence"],
            evidence_json={"latest_event": "turn_evaluation:eval-1"},
            recommended_next_action="Add one concrete example.",
            source_summary="Good stance, missing evidence.",
        )
    )

    response = TestClient(app).get("/me/learning-graph", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["career_profile"]["resume_present"] is True
    assert "resume_text" not in body["career_profile"]
    assert body["profiles"][0]["skill_id"] == "gd_02_support_with_evidence"
    assert body["profiles"][0]["readiness"] == 0.82
