from pathlib import Path

import pytest

from app.db import repo


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "app/db/schema.sql"
MIGRATION = (
    ROOT
    / "app/db/migrations/2026-07-14-school-placement-report-nullable-classes.sql"
)


class _CaptureSession:
    def __init__(self) -> None:
        self.params: list[dict] = []
        self.commits = 0

    async def execute(self, _statement, params):
        self.params.append(dict(params))

    async def commit(self) -> None:
        self.commits += 1


def _report_kwargs(*, evaluated_class_no, active_learning_class_no) -> dict:
    return {
        "report_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "user_id": "test_user",
        "profile_version_id": "11111111-1111-4111-8111-111111111111",
        "placement_session_id": "22222222-2222-4222-8222-222222222222",
        "placement_status": "insufficient_evidence",
        "subject_id": "english",
        "target_class_no": 5,
        "evaluated_class_no": evaluated_class_no,
        "active_learning_class_no": active_learning_class_no,
        "unlock_state": "locked",
        "blocking_skills": [],
        "watchlist_skills": [],
        "evidence_summary": {},
        "recommended_recap_modules": [],
        "learner_summary": "More evidence is needed.",
        "parent_summary": "No class estimate is available.",
        "allowed_next_actions": ["start_placement"],
    }


def test_schema_and_additive_migration_allow_unknown_report_classes():
    schema = SCHEMA.read_text().lower()
    evaluated_line = next(
        line for line in schema.splitlines() if "evaluated_class_no" in line
    )
    active_line = next(
        line for line in schema.splitlines() if "active_learning_class_no" in line
    )
    migration = MIGRATION.read_text().lower()

    assert "not null" not in evaluated_line
    assert "not null" not in active_line
    assert "alter column evaluated_class_no drop not null" in migration
    assert "alter column active_learning_class_no drop not null" in migration
    assert "drop column" not in migration


@pytest.mark.asyncio
async def test_repository_preserves_null_and_integer_report_classes(monkeypatch):
    session = _CaptureSession()

    async def get_saved_report(*_args, **_kwargs):
        return {"report_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}

    monkeypatch.setattr(repo, "get_school_placement_report", get_saved_report)

    await repo.upsert_school_placement_report(
        session,
        **_report_kwargs(
            evaluated_class_no=None,
            active_learning_class_no=None,
        ),
    )
    await repo.upsert_school_placement_report(
        session,
        **_report_kwargs(
            evaluated_class_no=5,
            active_learning_class_no=4,
        ),
    )

    assert session.params[0]["evaluated_class_no"] is None
    assert session.params[0]["active_learning_class_no"] is None
    assert session.params[1]["evaluated_class_no"] == 5
    assert session.params[1]["active_learning_class_no"] == 4
    assert session.commits == 2
