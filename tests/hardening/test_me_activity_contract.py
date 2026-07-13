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


def test_learning_graph_uses_store_aggregate_without_extra_checkouts():
    from app.services.learning_profile import CareerLearningProfileService

    class AggregateStore:
        async def get_learning_graph(self, _user_id):
            return {
                "profiles": [],
                "reports": [],
                "events": [],
                "progression": [{"module_id": "group_discussion"}],
                "active_sessions": [{"session_id": "session-gd"}],
            }

        async def get_progression(self, _user_id):
            raise AssertionError("progression must use the aggregate session")

        async def get_active_career_session_runtimes(self, _user_id):
            raise AssertionError("active sessions must use the aggregate session")

    graph = _run(CareerLearningProfileService(AggregateStore()).get_learning_graph("user-1"))

    assert graph["progression"] == [{"module_id": "group_discussion"}]
    assert graph["active_sessions"] == [{"session_id": "session-gd"}]


def test_learning_graph_projects_only_career_memory_evidence():
    from app.db import repo

    class EmptyResult:
        def mappings(self):
            return self

        def all(self):
            return []

    class RecordingSession:
        statements = []

        async def execute(self, statement, _params):
            self.statements.append(str(statement))
            return EmptyResult()

    session = RecordingSession()
    graph = _run(repo.get_learning_graph(session, "user-1"))
    event_query = next(sql for sql in session.statements if "FROM learning_events" in sql)

    assert "domain = 'career'" in event_query
    assert "jsonb_strip_nulls(jsonb_build_object" in event_query
    assert "criterion.value->>'evidence_quote'" in event_query
    assert "evidence_json->>'answer_excerpt'" in event_query
    assert "REGEXP_REPLACE" in event_query
    assert "'tutor_plan'" not in event_query
    assert f"LIMIT {repo.CAREER_LEARNING_EVENT_LIMIT}" in event_query
    assert graph["progression"] == []
    assert graph["active_sessions"] == []


def test_compact_event_projection_keeps_derived_grounded_quote():
    from app.services.learning_profile import build_career_memory_context

    context = build_career_memory_context({
        "profiles": [],
        "reports": [],
        "progression": [],
        "events": [{
            "source_event_key": "turn_evaluation:legacy-1",
            "domain": "career",
            "task_type": "gd_prep",
            "module_id": "group_discussion",
            "session_id": "session-legacy",
            "skill_id": "gd_09_manage_dominator",
            "source": "prep_turn",
            "attempt_type": "independent",
            "score": 0.8,
            "confidence": 0.8,
            "evidence_json": {
                "answer_excerpt": "Rohan made a useful point. Maya, please take the floor on mentoring risk.",
                "latest_quote": "Maya, please take the floor on mentoring risk",
                "pass_eligible": True,
                "proof": {"grounded": True},
            },
            "gap": "Keep the handoff tied to the motion.",
        }],
    })

    assert context["improving_gaps"][0]["latest_evidence"] == (
        "Maya, please take the floor on mentoring risk"
    )
