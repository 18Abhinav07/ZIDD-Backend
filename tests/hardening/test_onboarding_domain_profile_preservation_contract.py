import asyncio

import pytest
from fastapi.testclient import TestClient

from app.db import repo
from app.main import app


AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def test_school_onboarding_preserves_existing_career_profile(store):
    career_profile = {
        "target_roles": ["Data Analyst"],
        "interview_goals": ["Explain projects clearly"],
    }
    _run(store.ensure_profile("test_user"))
    _run(
        store.complete_onboarding(
            user_id="test_user",
            display_name="Ravi",
            primary_motive="career",
            school_profile={},
            career_profile=career_profile,
        )
    )

    response = TestClient(app).post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Ravi",
            "primary_motive": "school",
            "school_profile": {"school_name": "City Public School"},
        },
    )

    assert response.status_code == 200
    assert _run(store.get_profile("test_user"))["career_profile"] == career_profile


def test_career_onboarding_preserves_existing_school_profile(store):
    school_profile = {
        "school_name": "City Public School",
        "learning_goal": "Read independently",
    }
    _run(store.ensure_profile("test_user"))
    _run(
        store.complete_onboarding(
            user_id="test_user",
            display_name="Asha",
            primary_motive="school",
            school_profile=school_profile,
            career_profile={},
        )
    )

    response = TestClient(app).post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Asha",
            "primary_motive": "career",
            "career_profile": {"target_roles": ["Backend Engineer"]},
        },
    )

    assert response.status_code == 200
    assert _run(store.get_profile("test_user"))["school_profile"] == school_profile


class _MappingResult:
    def __init__(self, row: dict) -> None:
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return dict(self._row)


class _CaptureSession:
    def __init__(self) -> None:
        self.statements: list[str] = []
        self.params: list[dict] = []
        self.commits = 0

    async def execute(self, statement, params):
        self.statements.append(str(statement))
        self.params.append(dict(params))
        return _MappingResult(
            {
                "user_id": "test_user",
                "name": "Asha",
                "primary_motive": params["primary_motive"],
                "school_profile": {},
                "career_profile": {},
            }
        )

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_repository_updates_only_the_selected_onboarding_domain():
    session = _CaptureSession()

    await repo.complete_onboarding(
        session,
        user_id="test_user",
        display_name="Asha",
        primary_motive="school",
        school_profile={"school_name": "City Public School"},
        career_profile={},
    )

    sql = " ".join(session.statements[0].lower().split())
    assert "school_profile = case when :primary_motive = 'school'" in sql
    assert "career_profile = case when :primary_motive = 'career'" in sql
    assert "else learner_profiles.school_profile" in sql
    assert "else learner_profiles.career_profile" in sql
    assert session.commits == 1
