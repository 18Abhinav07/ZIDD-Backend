import asyncio
import json
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.api import school_rebuild_routes
from app.services import school_rebuild_placement as placement


def _run(coro):
    return asyncio.run(coro)


def _profile():
    return {
        "profile_version_id": "profile-v1",
        "target_class_no": 5,
        "subject_ids": ["english"],
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    }


def _row(*, session_id: str, flow_type: str, state_json: dict, report_id: str | None):
    return {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": flow_type,
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "profile_version_id": "profile-v1",
        "source_placement_report_id": report_id,
        "linked_session_id": None,
        "state_json": state_json,
    }


def _assert_no_private_evaluator_data(value):
    serialized = json.dumps(value)
    for private_value in (
        "private-answer-hash",
        "private-claim-token",
        "private raw answer",
        "private-answer-key",
    ):
        assert private_value not in serialized
    for forbidden_key in ("answer_key", "raw_answer", "response_json"):
        assert f'"{forbidden_key}"' not in serialized


def test_pending_answer_statuses_use_only_narrow_context(monkeypatch):
    """Placement, recap, and masterclass polling must not need School state."""

    profile = _profile()
    report = {"report_id": "placement-report"}

    for flow_type, handler in (
        ("placement", school_rebuild_routes.get_school_placement_answer_status),
        ("recap", school_rebuild_routes.get_school_recap_answer_status),
        ("masterclass", school_rebuild_routes.get_school_masterclass_answer_status),
    ):
        session_id = str(uuid4())
        state = (
            placement.envelope_to_json(placement.new_placement_envelope(profile))
            if flow_type == "placement"
            else {}
        )
        row = _row(
            session_id=session_id,
            flow_type=flow_type,
            state_json=state,
            report_id=None if flow_type == "placement" else report["report_id"],
        )
        activity_id = f"{flow_type}-activity"

        async def narrow_context(_request, _session_id, _activity_id, *, row=row):
            assert _session_id == session_id
            assert _activity_id == activity_id
            return {
                "user_id": "test_user",
                "store": SimpleNamespace(),
                "public_profile": profile,
                "placement_report": None if flow_type == "placement" else report,
                "row": row,
                "linked_parent": None,
                "answer_request": {
                    "status": "processing",
                    "answer_hash": "private-answer-hash",
                    "claim_token": "private-claim-token",
                    "raw_answer": "private raw answer",
                    "stale": False,
                },
            }

        monkeypatch.setattr(
            school_rebuild_routes,
            "_school_answer_status_context",
            narrow_context,
        )
        response = _run(handler(UUID(session_id), activity_id, SimpleNamespace()))
        assert response == {
            "status": "awaiting_evaluation",
            "session_id": session_id,
            "activity_id": activity_id,
        }
        _assert_no_private_evaluator_data(response)


def test_completed_placement_answer_status_regenerates_public_session(monkeypatch):
    """Completed polling never replays private idempotency response JSON."""

    profile = _profile()
    session_id = str(uuid4())
    row = _row(
        session_id=session_id,
        flow_type="placement",
        state_json=placement.envelope_to_json(placement.new_placement_envelope(profile)),
        report_id=None,
    )
    row["status"] = "complete"

    async def narrow_context(_request, _session_id, _activity_id):
        assert _session_id == session_id
        return {
            "user_id": "test_user",
            "store": SimpleNamespace(),
            "public_profile": profile,
            "placement_report": None,
            "row": row,
            "linked_parent": None,
            "answer_request": {
                "status": "completed",
                "answer_hash": "private-answer-hash",
                "claim_token": "private-claim-token",
                "raw_answer": "private raw answer",
                "response_json": {
                    "answer_key": "private-answer-key",
                    "raw_answer": "private raw answer",
                },
            },
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_answer_status_context",
        narrow_context,
    )
    response = _run(
        school_rebuild_routes.get_school_placement_answer_status(
            UUID(session_id),
            "placement-activity",
            SimpleNamespace(),
        )
    )
    assert response["status"] == "completed"
    assert response["session"]["session_id"] == session_id
    _assert_no_private_evaluator_data(response)
