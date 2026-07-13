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
    profile_rows = [
        {
            "skill_id": "evidence_under_pressure",
            "module_id": "interview",
            "task_type": "interview_prep",
            "mastery": 0.0,
            "readiness": 0.44,
            "confidence": 0.7,
            "gaps_json": ["needs quantified impact"],
            "evidence_json": {"latest_quote": "I improved reliability but did not quantify impact."},
            "recommended_next_action": "Add one measurable result.",
            "source_summary": "Missing measurable impact.",
        },
        {
            "skill_id": "gd_02_support_with_evidence",
            "module_id": "group_discussion",
            "task_type": "gd_prep",
            "mastery": 0.0,
            "readiness": 0.82,
            "confidence": 0.8,
            "gaps_json": ["needs evidence"],
            "evidence_json": {"latest_event": "turn_evaluation:eval-1"},
            "recommended_next_action": "Add one concrete example.",
            "source_summary": "Good stance, missing evidence.",
        },
        {
            "skill_id": "concise_tradeoff",
            "module_id": "interview",
            "task_type": "interview_test",
            "mastery": 0.0,
            "readiness": 0.9,
            "confidence": 0.76,
            "gaps_json": ["maintain concise tradeoff framing"],
            "evidence_json": {"latest_quote": "I would prioritize safeguards before speed."},
            "recommended_next_action": "Use this tradeoff under pressure.",
            "source_summary": "Resolved concise tradeoff gap.",
        },
        {
            "skill_id": "clear_stance_mastered",
            "module_id": "group_discussion",
            "task_type": "gd_prep",
            "mastery": 0.96,
            "readiness": 0.93,
            "confidence": 0.9,
            "gaps_json": ["keep stance direct"],
            "evidence_json": {"latest_quote": "Remote should be default with explicit guardrails."},
            "recommended_next_action": "Pressure-test with a new topic.",
            "source_summary": "Sustained clear stance.",
        },
    ]
    for row in profile_rows:
        _run(
            store.upsert_learner_skill_profile(
                user_id="test_user",
                domain="career",
                attempts=5,
                strengths_json=["clear stance"],
                **row,
            )
        )

    response = TestClient(app).get("/me/learning-graph", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["career_profile"]["resume_present"] is True
    assert "resume_text" not in body["career_profile"]
    assert body["active_sessions"] == []
    assert {row["skill_id"] for row in body["profiles"]} >= {
        "evidence_under_pressure",
        "gd_02_support_with_evidence",
        "concise_tradeoff",
        "clear_stance_mastered",
    }
    memory = body["memory_context"]
    assert memory["active_gaps"][0]["skill_id"] == "evidence_under_pressure"
    assert memory["improving_gaps"][0]["skill_id"] == "gd_02_support_with_evidence"
    assert any(item["skill_id"] == "concise_tradeoff" for item in memory["improving_gaps"])
    assert memory["resolved_gaps"] == []
    assert memory["mastered_skills"][0]["skill_id"] == "clear_stance_mastered"
    assert "quantify impact" in memory["active_gaps"][0]["latest_evidence"]


def test_active_career_session_query_excludes_expired_leases():
    from app.db import repo

    class Result:
        def mappings(self):
            return self

        def all(self):
            return []

    class Session:
        statement = ""

        async def execute(self, statement, _params):
            self.statement = str(statement)
            return Result()

    session = Session()
    assert _run(repo.get_active_career_session_runtimes(session, "user-1")) == []
    assert "lease_expires_at IS NULL OR lease_expires_at > now()" in session.statement
    assert "DISTINCT ON (module_id, test_mode)" in session.statement
