import asyncio
import copy
import inspect
import re
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes as rebuild_routes
from app.db import repo
from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_placement as placement
from app.services.school_rebuild_profile import SchoolRebuildProfileIn
from app.services.school_rebuild_state import school_state_for_profile

AUTH = {"Authorization": "Bearer test_token"}

SCHOOL_STATE_KEYS = {
    "profile_status",
    "target_class_no",
    "subject_id",
    "profile_version_id",
    "preferred_teaching_language",
    "coach_avatar_id",
    "coach_palette_id",
    "active_flow",
    "active_session_id",
    "placement_status",
    "unlock_state",
    "evaluated_class_no",
    "active_learning_class_no",
    "status",
    "next_action",
    "next_action_url",
    "allowed_next_actions",
    "learner_message",
    "parent_message",
    "blocked_reason",
}

CANONICAL_SCHOOL_NEXT_ACTIONS = {
    "sign_in",
    "complete_profile",
    "edit_profile",
    "start_placement",
    "resume_placement",
    "view_placement_report",
    "start_recap",
    "resume_recap",
    "revise_recap_path",
    "start_curriculum",
    "resume_curriculum",
    "start_masterclass",
    "resume_masterclass",
    "view_support_plan",
    "resume_support",
    "view_report",
    "retry",
}

CANONICAL_SCHOOL_ROUTES = {
    "/school/state",
    "/school/catalog",
    "/school/catalog/{subject_id}/classes/{class_no}",
    "/school/catalog/{subject_id}/classes/{class_no}/chapters/{chapter_id}",
    "/school/onboarding",
    "/school/onboarding/complete",
    "/school/placement/start",
    "/school/placement/report",
    "/school/placement/{session_id}",
    "/school/placement/{session_id}/abandon",
    "/school/placement/{session_id}/answer",
    "/school/recap/start",
    "/school/recap",
    "/school/recap/{session_id}",
    "/school/recap/{session_id}/answer",
    "/school/curriculum",
    "/school/curriculum/start",
    "/school/curriculum/{session_id}",
    "/school/curriculum/{session_id}/abandon-masterclass",
    "/school/curriculum/{session_id}/answer",
    "/school/curriculum/{session_id}/continue-after-support-cap",
    "/school/curriculum/{session_id}/masterclass/start",
    "/school/curriculum/{session_id}/resume-masterclass",
    "/school/masterclass/{session_id}",
    "/school/masterclass/{session_id}/answer",
    "/school/support/{session_id}",
}


def test_school_runtime_registers_only_canonical_rebuild_routes():
    client = TestClient(app)

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi_paths = {
        path
        for path in openapi_response.json()["paths"]
        if path.startswith("/school")
    }
    runtime_paths = {
        route.path
        for route in app.routes
        if getattr(route, "path", "").startswith("/school")
    }

    assert openapi_paths == CANONICAL_SCHOOL_ROUTES
    assert runtime_paths == CANONICAL_SCHOOL_ROUTES


def test_school_state_without_bearer_returns_backend_owned_sign_in_state(monkeypatch):
    monkeypatch.delenv("ZIDD_ALLOW_TEST_AUTH", raising=False)

    response = TestClient(app).get("/school/state")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == SCHOOL_STATE_KEYS
    assert body["profile_status"] == "unauthenticated"
    assert body["status"] == "needs_action"
    assert body["next_action"] == "sign_in"
    assert body["next_action_url"] == "/auth/login"
    assert body["allowed_next_actions"] == ["sign_in"]
    assert TestClient(app).get("/school/onboarding").status_code == 401


def _run(coro):
    return asyncio.run(coro)


def _assert_next_action_contract(body):
    if body["allowed_next_actions"]:
        assert body["next_action"] in CANONICAL_SCHOOL_NEXT_ACTIONS
        assert body["next_action"] in body["allowed_next_actions"]
    else:
        assert body["next_action"] is None


def _valid_school_profile():
    return {
        "display_name": "Open Assets",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": 3,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": "I want to understand Class 3 English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": ["vocabulary", "chapter_answers"],
    }


def test_school_profile_schema_requires_exactly_one_english_subject():
    subject_schema = SchoolRebuildProfileIn.model_json_schema()["properties"][
        "subject_ids"
    ]

    assert subject_schema["minItems"] == 1
    assert subject_schema["maxItems"] == 1
    assert subject_schema["items"]["const"] == "english"


def _save_school_profile_draft(
    client,
    profile=None,
    *,
    current_step=4,
    request_id=None,
    profile_version_id=None,
    expected_revision=None,
):
    payload = {
        **(profile or {}),
        "current_step": current_step,
        "request_id": request_id or str(uuid4()),
    }
    if profile_version_id is not None:
        payload["profile_version_id"] = profile_version_id
    if expected_revision is not None:
        payload["expected_revision"] = expected_revision
    return client.post("/school/onboarding", headers=AUTH, json=payload)


def _complete_school_profile_draft(client, draft, *, request_id=None):
    return client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
            "request_id": request_id or str(uuid4()),
        },
    )


def _save_and_complete_school_profile(client, profile=None):
    saved = _save_school_profile_draft(client, profile or _valid_school_profile())
    assert saved.status_code == 200, saved.text
    completed = _complete_school_profile_draft(client, saved.json()["draft"])
    assert completed.status_code == 200, completed.text
    return completed.json()["profile"]


def _state_school_profile():
    return {
        **_valid_school_profile(),
        "profile_version_id": "profile-v1",
    }


def _placement_session(status="active"):
    return {
        "session_id": "placement-v1",
        "status": status,
        "state_json": {},
    }


def _terminal_placement_session(*, exhausted: bool):
    envelope = placement.new_placement_envelope(_state_school_profile())
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            total_items=(
                placement.MAX_PLACEMENT_ITEMS
                if exhausted
                else envelope.state.total_items
            ),
            terminal_status="insufficient_evidence",
            terminal_reason=(
                "item_budget_exhausted_without_honest_boundary"
                if exhausted
                else "placement_window_ended"
            ),
        ),
    )
    return {
        **_placement_session("insufficient_evidence"),
        "state_json": placement.envelope_to_json(terminal),
    }


def _placement_report(status="below_target"):
    target_ready = status == "target_ready"
    insufficient = status == "insufficient_evidence"
    return {
        "report_id": "report-v1",
        "placement_session_id": "placement-v1",
        "profile_version_id": "profile-v1",
        "placement_status": status,
        "subject_id": "english",
        "target_class_no": 3,
        "evaluated_class_no": 3 if target_ready else 2,
        "active_learning_class_no": 3 if target_ready else 2,
        "unlock_state": (
            "target_unlocked"
            if target_ready
            else "locked" if insufficient else "recap_required"
        ),
        "learner_summary": "Your readiness result is saved.",
        "parent_summary": "The readiness evidence is saved.",
        "allowed_next_actions": (
            ["start_curriculum"]
            if target_ready
            else ["resume_placement"] if insufficient else ["start_recap"]
        ),
    }


def _recap_session(status="active", *, session_id="recap-v1", blocked_reason=None):
    state = {
        "status": status,
        "active_learning_class_no": 2,
        "current_activity": {"kind": "guided_check"},
    }
    if status in {"needs_support", "capped_support"}:
        state["support_required"] = {}
    if blocked_reason:
        state["support_required"] = {"reason": blocked_reason}
    return {
        "session_id": session_id,
        "status": "complete" if status == "complete" else "active",
        "state_json": state,
    }


def _curriculum_session(*, session_id="curriculum-v1", current_kind="guided_check"):
    return {
        "session_id": session_id,
        "status": "active",
        "state_json": {
            "status": "active",
            "phase": "learning",
            "active_learning_class_no": 3,
            "chapter": {"chapter_id": "eng_c3_ch01", "title": "Colours"},
            "current_activity": {
                "activity_id": "colour_clue:guided_check:1",
                "kind": current_kind,
            },
        },
    }


def _linked_session(flow_type, *, status="active"):
    session_id = f"{flow_type}-v1"
    return {
        "session_id": session_id,
        "flow_type": flow_type,
        "status": status,
        "state_json": {"status": status},
    }


STATE_CASES = [
    pytest.param(
        {"school_profile": None},
        {
            "profile_status": "missing",
            "active_flow": "onboarding",
            "status": "needs_action",
            "next_action": "complete_profile",
            "next_action_url": "/school/onboarding",
            "allowed_next_actions": ["complete_profile"],
            "blocked_reason": None,
        },
        id="missing-profile",
    ),
    pytest.param(
        {},
        {
            "active_flow": "none",
            "status": "needs_action",
            "next_action": "start_placement",
            "next_action_url": "/school/readiness",
            "allowed_next_actions": ["start_placement"],
            "blocked_reason": None,
        },
        id="ready-to-start-placement",
    ),
    pytest.param(
        {"placement_session": _placement_session()},
        {
            "active_flow": "placement",
            "status": "in_progress",
            "next_action": "resume_placement",
            "next_action_url": "/school/readiness/placement-v1",
            "allowed_next_actions": ["resume_placement"],
            "blocked_reason": None,
        },
        id="placement-in-progress",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report("target_ready"),
            "active_curriculum_session": _curriculum_session(),
            "processing_answer_request": {"status": "processing", "stale": False},
        },
        {
            "active_flow": "curriculum",
            "status": "awaiting_evaluation",
            "next_action": None,
            "next_action_url": "/school/classes/3/chapters/eng_c3_ch01",
            "allowed_next_actions": [],
            "blocked_reason": "answer_evaluation_in_progress",
        },
        id="answer-awaiting-evaluation",
    ),
    pytest.param(
        {"placement_session": _terminal_placement_session(exhausted=True)},
        {
            "active_flow": "placement_report",
            "placement_status": "insufficient_evidence",
            "unlock_state": "locked",
            "status": "insufficient_evidence",
            "next_action": "start_placement",
            "next_action_url": "/school/readiness",
            "allowed_next_actions": ["view_placement_report", "start_placement"],
            "blocked_reason": "insufficient_evidence",
        },
        id="insufficient-evidence",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report("below_target"),
        },
        {
            "active_flow": "placement_report",
            "placement_status": "below_target",
            "status": "ready",
            "next_action": "start_recap",
            "next_action_url": "/school/recap",
            "allowed_next_actions": ["view_placement_report", "start_recap"],
            "blocked_reason": None,
        },
        id="below-target-report",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report("target_ready"),
        },
        {
            "active_flow": "curriculum",
            "placement_status": "target_ready",
            "status": "ready",
            "next_action": "start_curriculum",
            "next_action_url": "/school/classes/3",
            "allowed_next_actions": ["start_curriculum"],
            "blocked_reason": None,
        },
        id="target-ready-report",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report(),
            "active_recap_session": _recap_session(),
        },
        {
            "active_flow": "recap",
            "status": "in_progress",
            "next_action": "resume_recap",
            "next_action_url": "/school/recap/recap-v1",
            "allowed_next_actions": ["resume_recap"],
            "blocked_reason": None,
        },
        id="recap-in-progress",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report(),
            "active_recap_session": _recap_session("complete"),
        },
        {
            "active_flow": "curriculum",
            "status": "complete",
            "next_action": "start_curriculum",
            "next_action_url": "/school/classes/3",
            "allowed_next_actions": ["start_curriculum"],
            "blocked_reason": None,
        },
        id="recap-complete",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report(),
            "active_recap_session": _recap_session("needs_support"),
        },
        {
            "active_flow": "support",
            "status": "needs_support",
            "next_action": "view_support_plan",
            "next_action_url": "/school/support/recap-v1",
            "allowed_next_actions": ["view_support_plan"],
            "blocked_reason": "recap_support_required",
        },
        id="recap-needs-support",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report(),
            "active_recap_session": _recap_session("needs_path_revision"),
        },
        {
            "active_flow": "recap",
            "status": "needs_path_revision",
            "next_action": "revise_recap_path",
            "next_action_url": "/school/recap/recap-v1",
            "allowed_next_actions": ["revise_recap_path"],
            "blocked_reason": "recap_path_revision_required",
        },
        id="recap-needs-path-revision",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report("target_ready"),
            "active_curriculum_session": _curriculum_session(),
        },
        {
            "active_flow": "curriculum",
            "status": "in_progress",
            "next_action": "resume_curriculum",
            "next_action_url": "/school/session/curriculum-v1",
            "allowed_next_actions": ["resume_curriculum"],
            "blocked_reason": None,
        },
        id="curriculum-in-progress",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report("target_ready"),
            "active_curriculum_session": _curriculum_session(),
            "linked_session": _linked_session("masterclass"),
        },
        {
            "active_flow": "masterclass",
            "active_session_id": "masterclass-v1",
            "status": "in_progress",
            "next_action": "resume_masterclass",
            "next_action_url": "/school/masterclass/masterclass-v1",
            "allowed_next_actions": ["resume_masterclass"],
            "blocked_reason": None,
        },
        id="linked-masterclass-in-progress",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report("target_ready"),
            "active_curriculum_session": _curriculum_session(),
            "linked_session": _linked_session("support"),
        },
        {
            "active_flow": "support",
            "active_session_id": "support-v1",
            "status": "in_progress",
            "next_action": "resume_support",
            "next_action_url": "/school/support/support-v1",
            "allowed_next_actions": ["resume_support"],
            "blocked_reason": None,
        },
        id="linked-support-in-progress",
    ),
    pytest.param(
        {
            "placement_session": _placement_session("complete"),
            "placement_report": _placement_report(),
            "active_recap_session": _recap_session(
                "capped_support", blocked_reason="masterclass_cap_exceeded"
            ),
        },
        {
            "active_flow": "support",
            "status": "needs_support",
            "next_action": "view_support_plan",
            "next_action_url": "/school/support/recap-v1",
            "allowed_next_actions": ["view_support_plan"],
            "blocked_reason": "masterclass_cap_exceeded",
        },
        id="capped-support",
    ),
    pytest.param(
        {"placement_session": _placement_session("mystery")},
        {
            "active_flow": "none",
            "status": "recoverable_error",
            "next_action": "retry",
            "next_action_url": "/school",
            "allowed_next_actions": ["retry"],
            "blocked_reason": "inconsistent_school_state",
        },
        id="unknown-state-is-recoverable",
    ),
]


@pytest.mark.parametrize(("overrides", "expected"), STATE_CASES)
def test_school_state_for_profile_is_exhaustive(overrides, expected):
    kwargs = {
        "learner_profile": {"name": "Mira"},
        "school_profile": _state_school_profile(),
        **overrides,
    }

    body = school_state_for_profile(**kwargs)

    assert set(body) == SCHOOL_STATE_KEYS
    assert body.items() >= expected.items()
    _assert_next_action_contract(body)
    assert body["learner_message"]
    assert body["parent_message"]
    if expected["status"] == "recoverable_error":
        assert body["unlock_state"] == "locked"
        assert body["placement_status"] != "target_ready"


@pytest.mark.parametrize(
    ("report_status", "expected"),
    [
        pytest.param(
            "insufficient_evidence",
            {
                "active_flow": "placement_report",
                "placement_status": "insufficient_evidence",
                "unlock_state": "locked",
                "status": "insufficient_evidence",
                "next_action": "start_placement",
                "next_action_url": "/school/readiness",
                "allowed_next_actions": [
                    "view_placement_report",
                    "start_placement",
                ],
                "blocked_reason": "insufficient_evidence",
            },
            id="insufficient-evidence-locked-report",
        ),
        pytest.param(
            "abandoned",
            {
                "active_flow": "placement_report",
                "placement_status": "abandoned",
                "unlock_state": "locked",
                "status": "recoverable_error",
                "next_action": "start_placement",
                "next_action_url": "/school/readiness",
                "allowed_next_actions": ["view_placement_report", "start_placement"],
                "blocked_reason": "placement_abandoned",
            },
            id="abandoned-locked-report",
        ),
    ],
)
def test_school_state_never_unlocks_recap_for_valid_locked_report(
    report_status, expected
):
    report = _placement_report("below_target")
    report["placement_status"] = report_status
    report["unlock_state"] = "locked"

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=(
            _terminal_placement_session(exhausted=True)
            if report_status == "insufficient_evidence"
            else _placement_session("complete")
        ),
        placement_report=report,
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body.items() >= expected.items()
    assert "start_recap" not in body["allowed_next_actions"]


@pytest.mark.parametrize(
    "invalid_field",
    [
        pytest.param("target_class_no", id="missing-target-class"),
        pytest.param("profile_version_id", id="missing-profile-version"),
        pytest.param("subject_ids", id="empty-subjects"),
        pytest.param("preferred_teaching_language", id="missing-teaching-language"),
    ],
)
def test_school_state_routes_incomplete_profile_to_onboarding(invalid_field):
    school_profile = _state_school_profile()
    if invalid_field == "subject_ids":
        school_profile[invalid_field] = []
    else:
        school_profile.pop(invalid_field)

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=school_profile,
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["profile_status"] == "incomplete"
    assert body["active_flow"] == "onboarding"
    assert body["status"] == "needs_action"
    assert body["next_action"] == "complete_profile"
    assert body["next_action_url"] == "/school/onboarding"
    assert body["allowed_next_actions"] == ["complete_profile"]


@pytest.mark.parametrize(
    ("linked_argument", "linked_session"),
    [
        pytest.param(
            "active_masterclass_session",
            _linked_session("masterclass"),
            id="masterclass",
        ),
        pytest.param(
            "active_support_session",
            _linked_session("support"),
            id="support",
        ),
    ],
)
def test_processing_answer_precedes_active_linked_session(
    linked_argument, linked_session
):
    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("target_ready"),
        active_curriculum_session=_curriculum_session(),
        processing_answer_request={"status": "processing", "stale": False},
        **{linked_argument: linked_session},
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "curriculum"
    assert body["status"] == "awaiting_evaluation"
    assert body["next_action"] is None
    assert body["next_action_url"] == "/school/classes/3/chapters/eng_c3_ch01"
    assert body["allowed_next_actions"] == []
    assert body["blocked_reason"] == "answer_evaluation_in_progress"


@pytest.mark.parametrize(
    ("flow", "session_kwargs", "expected_url", "expected_next_action"),
    [
        pytest.param(
            "placement",
            {"placement_session": _placement_session()},
            "/school/readiness/placement-v1",
            "resume_placement",
            id="placement",
        ),
        pytest.param(
            "recap",
            {
                "placement_session": _placement_session("complete"),
                "placement_report": _placement_report(),
                "active_recap_session": _recap_session(),
            },
            "/school/recap/recap-v1",
            "resume_recap",
            id="recap",
        ),
        pytest.param(
            "curriculum",
            {
                "placement_session": _placement_session("complete"),
                "placement_report": _placement_report("target_ready"),
                "active_curriculum_session": _curriculum_session(),
            },
            "/school/session/curriculum-v1",
            "resume_curriculum",
            id="curriculum",
        ),
        pytest.param(
            "masterclass",
            {
                "placement_session": _placement_session("complete"),
                "placement_report": _placement_report("target_ready"),
                "active_curriculum_session": _curriculum_session(),
                "active_masterclass_session": _linked_session("masterclass"),
            },
            "/school/masterclass/masterclass-v1",
            "resume_masterclass",
            id="masterclass",
        ),
    ],
)
def test_processing_answer_lock_uses_active_flow_and_releases_at_stale_boundary(
    flow, session_kwargs, expected_url, expected_next_action
):
    flow_key = {
        "placement": "placement_session",
        "recap": "active_recap_session",
        "curriculum": "active_curriculum_session",
        "masterclass": "active_masterclass_session",
    }[flow]
    live_kwargs = copy.deepcopy(session_kwargs)
    live_kwargs[flow_key]["processing_answer_request"] = {
        "status": "processing",
        "age_seconds": 119.999,
        "stale": False,
    }

    live = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        **live_kwargs,
    )

    assert live["active_flow"] == flow
    assert live["status"] == "awaiting_evaluation"
    assert live["next_action"] is None
    assert live["next_action_url"] == expected_url
    assert live["allowed_next_actions"] == []
    assert live["blocked_reason"] == "answer_evaluation_in_progress"

    stale_kwargs = copy.deepcopy(session_kwargs)
    stale_kwargs[flow_key]["processing_answer_request"] = {
        "status": "processing",
        "age_seconds": 120.0,
        "stale": True,
    }
    stale = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        **stale_kwargs,
    )

    assert stale["active_flow"] == flow
    assert stale["status"] == "in_progress"
    assert stale["next_action"] == expected_next_action
    assert stale["next_action_url"] == expected_url


def test_school_state_snapshot_exposes_processing_age_for_every_active_flow():
    class SnapshotResult:
        def __init__(self, row):
            self.row = row

        def mappings(self):
            return self

        def first(self):
            return self.row

    class SnapshotSession:
        statement = ""
        params = {}

        async def execute(self, statement, params):
            self.statement = str(statement)
            self.params = dict(params)
            return SnapshotResult(
                {
                    "learner_profile": {"user_id": "user-1"},
                    "school_profile": {"profile_version_id": "profile-v1"},
                    "placement_session": {"session_id": "placement-v1"},
                    "placement_report": None,
                    "recap_session": {"session_id": "recap-v1"},
                    "curriculum_session": {"session_id": "curriculum-v1"},
                    "linked_sessions": [
                        {"session_id": "masterclass-v1", "flow_type": "masterclass"}
                    ],
                    "processing_answer_requests": [
                        {
                            "session_id": f"{flow}-v1",
                            "activity_id": f"{flow}-activity",
                            "status": "processing",
                            "age_seconds": 20.0,
                            "stale": False,
                        }
                        for flow in ("placement", "recap", "curriculum", "masterclass")
                    ],
                    "school_skill_profiles": [],
                }
            )

    session = SnapshotSession()
    snapshot = _run(repo.get_school_state_snapshot(session, "user-1"))

    assert session.params["stale_seconds"] == 120
    assert "age_seconds" in session.statement
    assert "stale" in session.statement
    for key in ("placement_session", "recap_session", "curriculum_session"):
        assert snapshot[key]["processing_answer_request"]["age_seconds"] == 20.0
        assert snapshot[key]["processing_answer_request"]["stale"] is False
    assert snapshot["linked_sessions"][0]["processing_answer_request"][
        "activity_id"
    ] == "masterclass-activity"


@pytest.mark.parametrize(
    ("child_argument", "child_session"),
    [
        pytest.param(
            "active_recap_session",
            _recap_session(),
            id="recap-without-report",
        ),
        pytest.param(
            "active_curriculum_session",
            _curriculum_session(),
            id="curriculum-without-report",
        ),
    ],
)
def test_active_child_without_placement_report_is_recoverable(
    child_argument, child_session
):
    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        **{child_argument: child_session},
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["status"] == "recoverable_error"
    assert body["next_action"] == "retry"
    assert body["next_action_url"] == "/school"
    assert body["allowed_next_actions"] == ["retry"]
    assert body["unlock_state"] == "locked"
    assert body["blocked_reason"] == "inconsistent_school_state"


@pytest.mark.parametrize(
    ("placement_status", "unlock_state"),
    [
        pytest.param("below_target", "recap_required", id="below-target"),
        pytest.param("insufficient_evidence", "locked", id="insufficient-evidence"),
        pytest.param("abandoned", "locked", id="abandoned"),
    ],
)
def test_active_curriculum_cannot_override_non_target_report(
    placement_status, unlock_state
):
    report = _placement_report("below_target")
    report["placement_status"] = placement_status
    report["unlock_state"] = unlock_state

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=report,
        active_curriculum_session=_curriculum_session(),
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["status"] == "recoverable_error"
    assert body["unlock_state"] == "locked"
    assert body["next_action"] == "retry"
    assert body["allowed_next_actions"] == ["retry"]
    assert body["blocked_reason"] == "inconsistent_school_state"


def test_completed_recap_does_not_override_non_target_report_in_pure_state():
    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("below_target"),
        active_recap_session=_recap_session("complete"),
        active_curriculum_session=_curriculum_session(),
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["status"] == "recoverable_error"
    assert body["unlock_state"] == "locked"
    assert body["next_action"] == "retry"
    assert body["allowed_next_actions"] == ["retry"]


@pytest.mark.parametrize(
    ("placement_status", "unlock_state", "should_normalize"),
    [
        pytest.param("below_target", "recap_required", True, id="below-target"),
        pytest.param(
            "insufficient_evidence", "locked", False, id="insufficient-evidence"
        ),
        pytest.param("abandoned", "locked", False, id="abandoned"),
        pytest.param("below_target", "locked", False, id="invalid-transition"),
        pytest.param(
            "target_ready", "target_unlocked", False, id="already-target-ready"
        ),
    ],
)
def test_recap_unlock_normalizes_only_below_target_report(
    placement_status, unlock_state, should_normalize
):
    report = _placement_report("below_target")
    report["placement_status"] = placement_status
    report["unlock_state"] = unlock_state

    result = rebuild_routes._state_report_with_recap_unlock(
        placement_report=report,
        recap_session=_recap_session("complete"),
        curriculum_session=_curriculum_session(),
    )

    if should_normalize:
        assert result is not report
        assert result["placement_status"] == "target_ready"
        assert result["unlock_state"] == "target_unlocked"
    else:
        assert result is report


def test_inactive_masterclass_does_not_relabel_active_support():
    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("target_ready"),
        active_curriculum_session=_curriculum_session(),
        active_masterclass_session=_linked_session("masterclass", status="complete"),
        active_support_session=_linked_session("support"),
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "support"
    assert body["active_session_id"] == "support-v1"
    assert body["next_action"] == "resume_support"
    assert body["next_action_url"] == "/school/support/support-v1"
    assert body["allowed_next_actions"] == ["resume_support"]


def test_malformed_curriculum_state_json_is_recoverable():
    for malformed_state_json in ([{"status": "active"}], "active", 7):
        curriculum_session = _curriculum_session()
        curriculum_session["state_json"] = malformed_state_json

        body = school_state_for_profile(
            learner_profile={"name": "Mira"},
            school_profile=_state_school_profile(),
            placement_session=_placement_session("complete"),
            placement_report=_placement_report("target_ready"),
            active_curriculum_session=curriculum_session,
        )

        assert set(body) == SCHOOL_STATE_KEYS
        assert body["active_flow"] == "none"
        assert body["status"] == "recoverable_error"
        assert body["next_action"] == "retry"
        assert body["allowed_next_actions"] == ["retry"]
        assert body["blocked_reason"] == "inconsistent_school_state"


@pytest.mark.parametrize("case", ["malformed", "versioned"])
def test_curriculum_session_content_version_check_is_shape_safe(case):
    if case == "malformed":
        for malformed_state_json in ([{"status": "active"}], "active", 7):
            assert curriculum.session_content_version_is_current(
                {"state_json": malformed_state_json}
            )
        for malformed_chapter in ("corrupt", ["corrupt"], 7):
            assert curriculum.session_content_version_is_current(
                {"state_json": {"chapter": malformed_chapter}}
            )
        return

    live_chapter = next(
        chapter
        for chapter in curriculum.CLASS_3_CURRICULUM_CHAPTERS
        if chapter["chapter_id"] == "eng_c3_ch01"
    )
    session = {
        "subject_id": "english",
        "class_no": 3,
        "state_json": {
            "chapter": {
                "chapter_id": live_chapter["chapter_id"],
                "content_version": live_chapter["content_version"],
            }
        },
    }

    assert curriculum.session_content_version_is_current(session)
    stale_session = copy.deepcopy(session)
    stale_session["state_json"]["chapter"]["content_version"] = "stale-version"
    assert not curriculum.session_content_version_is_current(stale_session)


def test_malformed_curriculum_chapter_is_recoverable():
    curriculum_session = _curriculum_session()
    curriculum_session["state_json"]["chapter"] = "corrupt"

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("target_ready"),
        active_curriculum_session=curriculum_session,
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["status"] == "recoverable_error"
    assert body["next_action"] == "retry"
    assert body["blocked_reason"] == "inconsistent_school_state"


def test_malformed_curriculum_support_required_is_recoverable():
    curriculum_session = _curriculum_session()
    curriculum_session["state_json"]["phase"] = "needs_support"
    curriculum_session["state_json"]["support_required"] = "corrupt"

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("target_ready"),
        active_curriculum_session=curriculum_session,
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["status"] == "recoverable_error"
    assert body["next_action"] == "retry"
    assert body["blocked_reason"] == "inconsistent_school_state"


def test_malformed_recap_support_required_is_recoverable():
    recap_session = _recap_session("capped_support")
    recap_session["state_json"]["support_required"] = "corrupt"

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("below_target"),
        active_recap_session=recap_session,
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["status"] == "recoverable_error"
    assert body["next_action"] == "retry"
    assert body["blocked_reason"] == "inconsistent_school_state"


def test_insufficient_session_and_report_preserve_evaluated_class():
    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_terminal_placement_session(exhausted=True),
        placement_report=_placement_report("insufficient_evidence"),
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "placement_report"
    assert body["placement_status"] == "insufficient_evidence"
    assert body["unlock_state"] == "locked"
    assert body["evaluated_class_no"] == 2
    assert body["next_action"] == "start_placement"
    assert body["next_action_url"] == "/school/readiness"
    assert body["allowed_next_actions"] == [
        "view_placement_report",
        "start_placement",
    ]


def test_terminal_placement_with_null_next_item_can_still_be_resumable():
    placement_session = _terminal_placement_session(exhausted=False)
    envelope = placement.envelope_from_json(placement_session["state_json"])

    assert placement.next_item(envelope) is None
    assert placement.can_resume_placement(envelope) is True

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=placement_session,
    )

    assert body["active_flow"] == "placement"
    assert body["next_action"] == "resume_placement"
    assert body["next_action_url"] == "/school/readiness/placement-v1"
    assert body["allowed_next_actions"] == ["resume_placement"]


@pytest.mark.parametrize(
    "malformed_state_json",
    [
        pytest.param([], id="list"),
        pytest.param("not-a-placement-envelope", id="string"),
    ],
)
def test_malformed_terminal_placement_envelope_is_recoverable(
    malformed_state_json,
):
    placement_session = _terminal_placement_session(exhausted=True)
    placement_session["state_json"] = malformed_state_json

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=placement_session,
        placement_report=_placement_report("insufficient_evidence"),
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["placement_status"] == "not_started"
    assert body["status"] == "recoverable_error"
    assert body["next_action"] == "retry"
    assert body["allowed_next_actions"] == ["retry"]
    assert body["blocked_reason"] == "inconsistent_school_state"


def test_terminal_placement_with_inconsistent_queue_reference_is_recoverable():
    placement_session = _terminal_placement_session(exhausted=True)
    placement_session["state_json"]["placement_state"]["pending_track_ids"] = [
        "missing-track"
    ]

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=placement_session,
        placement_report=_placement_report("insufficient_evidence"),
    )

    assert set(body) == SCHOOL_STATE_KEYS
    assert body["active_flow"] == "none"
    assert body["placement_status"] == "not_started"
    assert body["status"] == "recoverable_error"
    assert body["next_action"] == "retry"
    assert body["allowed_next_actions"] == ["retry"]
    assert body["blocked_reason"] == "inconsistent_school_state"


def test_exhausted_terminal_envelope_overrides_stale_resumable_report():
    placement_session = _terminal_placement_session(exhausted=True)
    envelope = placement.envelope_from_json(placement_session["state_json"])
    stale_report = _placement_report("insufficient_evidence")

    assert placement.next_item(envelope) is None
    assert placement.can_resume_placement(envelope) is False
    assert stale_report["allowed_next_actions"] == ["resume_placement"]

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=placement_session,
        placement_report=stale_report,
    )

    assert body["active_flow"] == "placement_report"
    assert body["active_session_id"] == "placement-v1"
    assert body["next_action"] == "start_placement"
    assert body["next_action_url"] == "/school/readiness"
    assert body["allowed_next_actions"] == [
        "view_placement_report",
        "start_placement",
    ]


def test_school_state_routes_curriculum_support_phase_without_false_progress():
    curriculum_session = _curriculum_session()
    curriculum_session["state_json"]["phase"] = "needs_support"
    curriculum_session["state_json"]["support_required"] = {
        "reason": "chapter_support_required"
    }

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("target_ready"),
        active_curriculum_session=curriculum_session,
    )

    assert body["status"] == "needs_support"
    assert body["next_action"] == "view_support_plan"
    assert body["next_action_url"] == "/school/support/curriculum-v1"
    assert body["allowed_next_actions"] == ["view_support_plan"]
    assert body["blocked_reason"] == "chapter_support_required"


def test_school_state_rejects_unknown_placement_report_as_recoverable():
    report = _placement_report("below_target")
    report["placement_status"] = "mystery"
    report["unlock_state"] = "mystery"

    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=report,
    )

    assert body["status"] == "recoverable_error"
    assert body["unlock_state"] == "locked"
    assert body["allowed_next_actions"] == ["retry"]


def test_completed_linked_detour_does_not_override_active_curriculum():
    body = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=_state_school_profile(),
        placement_session=_placement_session("complete"),
        placement_report=_placement_report("target_ready"),
        active_curriculum_session=_curriculum_session(),
        linked_session=_linked_session("masterclass", status="complete"),
    )

    assert body["active_flow"] == "curriculum"
    assert body["status"] == "in_progress"
    assert body["next_action"] == "resume_curriculum"


ENDPOINT_STATE_CASES = [
    pytest.param(case.id, case.values[1], id=case.id)
    for case in STATE_CASES
]


def _stored_session(
    *,
    session_id,
    flow_type,
    status,
    state_json,
    linked_session_id=None,
    source_report_id=None,
    profile_version_id="profile-v1",
    updated_at=1.0,
):
    return {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": flow_type,
        "subject_id": "english",
        "class_no": 3,
        "status": status,
        "current_stage": None,
        "linked_session_id": linked_session_id,
        "profile_version_id": profile_version_id,
        "source_placement_report_id": source_report_id,
        "state_json": state_json,
        "updated_at": updated_at,
    }


def _seed_endpoint_state(store, scenario):
    _run(store.ensure_profile("test_user", name="Mira", email="mira@example.com"))
    if scenario == "missing-profile":
        return
    profile = _state_school_profile()
    now = 1.0
    store.school_profile_versions[("test_user", profile["profile_version_id"])] = {
        **profile,
        "user_id": "test_user",
        "status": "active",
        "current_step": 4,
        "draft_revision": 1,
        "source_profile_version_id": None,
        "created_at": now,
        "updated_at": now,
        "activated_at": now,
        "archived_at": None,
    }
    if scenario == "ready-to-start-placement":
        return

    placement_status = (
        "active"
        if scenario == "placement-in-progress"
        else "insufficient_evidence"
        if scenario == "insufficient-evidence"
        else "mystery" if scenario == "unknown-state-is-recoverable" else "complete"
    )
    placement_state = (
        _terminal_placement_session(exhausted=True)["state_json"]
        if scenario == "insufficient-evidence"
        else placement.envelope_to_json(placement.new_placement_envelope(profile))
    )
    placement_row = _stored_session(
        session_id="placement-v1",
        flow_type="placement",
        status=placement_status,
        state_json=placement_state,
    )
    store.school_sessions[("test_user", "placement-v1")] = placement_row
    if scenario in {
        "placement-in-progress",
        "insufficient-evidence",
        "unknown-state-is-recoverable",
    }:
        return

    report_status = (
        "below_target"
        if scenario
        in {
            "below-target-report",
            "recap-in-progress",
            "recap-complete",
            "recap-needs-support",
            "recap-needs-path-revision",
            "capped-support",
        }
        else "target_ready"
    )
    report = _placement_report(report_status)
    store.school_placement_reports[("test_user", "placement-v1")] = {
        **report,
        "user_id": "test_user",
        "blocking_skills": [],
        "watchlist_skills": [],
        "evidence_summary": {},
        "recommended_recap_modules": [],
    }
    if scenario in {"below-target-report", "target-ready-report"}:
        return

    if scenario.startswith("recap-") or scenario == "capped-support":
        recap_status = {
            "recap-in-progress": "active",
            "recap-complete": "complete",
            "recap-needs-support": "needs_support",
            "recap-needs-path-revision": "needs_path_revision",
            "capped-support": "capped_support",
        }[scenario]
        recap_row = _stored_session(
            session_id="recap-v1",
            flow_type="recap",
            status="complete" if recap_status == "complete" else "active",
            state_json=_recap_session(
                recap_status,
                blocked_reason=(
                    "masterclass_cap_exceeded" if scenario == "capped-support" else None
                ),
            )["state_json"],
            linked_session_id="placement-v1",
            source_report_id="report-v1",
        )
        store.school_sessions[("test_user", "recap-v1")] = recap_row
        return

    curriculum_state = curriculum.new_curriculum_state(
        school_profile=profile,
        placement_report=report,
        recap_session=None,
    )
    curriculum_row = _stored_session(
        session_id="curriculum-v1",
        flow_type="curriculum",
        status="active",
        state_json=curriculum_state,
        linked_session_id="placement-v1",
        source_report_id="report-v1",
    )
    store.school_sessions[("test_user", "curriculum-v1")] = curriculum_row
    if scenario == "answer-awaiting-evaluation":
        activity_id = curriculum.public_curriculum_response(curriculum_row)[
            "current_activity"
        ]["activity_id"]
        _run(
            store.claim_school_answer_request(
                "test_user",
                "curriculum-v1",
                activity_id,
                "answer-hash",
            )
        )
        return
    if scenario not in {
        "linked-masterclass-in-progress",
        "linked-support-in-progress",
    }:
        return

    flow_type = "masterclass" if "masterclass" in scenario else "support"
    child_id = f"{flow_type}-v1"
    stale_child = _stored_session(
        session_id=f"old-{child_id}",
        flow_type=flow_type,
        status="active",
        state_json={"status": "active"},
        linked_session_id="curriculum-v1",
        source_report_id="old-report",
        profile_version_id="old-profile",
        updated_at=3.0,
    )
    current_child = _stored_session(
        session_id=child_id,
        flow_type=flow_type,
        status="active",
        state_json={"status": "active"},
        linked_session_id="curriculum-v1",
        source_report_id="report-v1",
        updated_at=2.0,
    )
    store.school_sessions[("test_user", stale_child["session_id"])] = stale_child
    store.school_sessions[("test_user", child_id)] = current_child


@pytest.mark.parametrize(
    "malformed_state_json",
    [
        pytest.param([{"status": "active"}], id="list"),
        pytest.param("active", id="string"),
    ],
)
def test_get_school_state_recovers_malformed_placement_state(
    store, malformed_state_json
):
    _seed_endpoint_state(store, "ready-to-start-placement")
    store.school_sessions[("test_user", "placement-v1")] = _stored_session(
        session_id="placement-v1",
        flow_type="placement",
        status="active",
        state_json=malformed_state_json,
    )

    response = TestClient(app).get("/school/state", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == SCHOOL_STATE_KEYS
    assert body["status"] == "recoverable_error"
    assert body["unlock_state"] == "locked"
    assert body["allowed_next_actions"] == ["retry"]


def test_get_school_state_recovers_malformed_curriculum_chapter(store):
    _seed_endpoint_state(store, "curriculum-in-progress")
    curriculum_row = store.school_sessions[("test_user", "curriculum-v1")]
    curriculum_row["state_json"]["chapter"] = "corrupt"

    response = TestClient(app).get("/school/state", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == SCHOOL_STATE_KEYS
    assert body["status"] == "recoverable_error"
    assert body["unlock_state"] == "locked"
    assert body["allowed_next_actions"] == ["retry"]


def test_get_school_state_recovers_malformed_curriculum_levels(store):
    _seed_endpoint_state(store, "curriculum-in-progress")
    curriculum_row = store.school_sessions[("test_user", "curriculum-v1")]
    curriculum_row["state_json"]["levels"] = ["corrupt"]

    response = TestClient(app).get("/school/state", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == SCHOOL_STATE_KEYS
    assert body["status"] == "recoverable_error"
    assert body["unlock_state"] == "locked"
    assert body["allowed_next_actions"] == ["retry"]


def test_get_school_state_uses_completed_curriculum_for_next_chapter(store):
    _seed_endpoint_state(store, "curriculum-in-progress")
    curriculum_row = store.school_sessions[("test_user", "curriculum-v1")]
    curriculum_row["status"] = "complete"
    curriculum_row["state_json"].update(
        {
            "status": "complete",
            "phase": "complete",
            "next_available_chapter": {
                "chapter_id": "eng_c3_ch02",
                "chapter_no": 2,
                "title": "Badal and Moti",
            },
        }
    )

    response = TestClient(app).get("/school/state", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["active_flow"] == "curriculum"
    assert body["active_session_id"] == "curriculum-v1"
    assert body["next_action"] == "start_curriculum"
    assert body["next_action_url"] == "/school/classes/3"
    assert body["learner_message"].endswith(
        "this chapter is complete. Start the next chapter."
    )
    assert body["parent_message"] == (
        "The learner completed this chapter and can continue to the next one."
    )


def test_class_map_selects_next_chapter_after_completed_curriculum(store):
    _seed_endpoint_state(store, "curriculum-in-progress")
    curriculum_row = store.school_sessions[("test_user", "curriculum-v1")]
    completed_chapter = curriculum_row["state_json"]["chapter"]
    completion_version = (
        completed_chapter.get("certification_version")
        or completed_chapter.get("content_version")
    )
    curriculum_row["status"] = "complete"
    curriculum_row["state_json"].update(
        {
            "status": "complete",
            "phase": "complete",
            "completed_chapter_ids": [completed_chapter["chapter_id"]],
            "completed_chapter_certification_versions": {
                completed_chapter["chapter_id"]: completion_version,
            },
            "next_available_chapter": {
                "chapter_id": "eng_c3_ch02",
                "chapter_no": 2,
                "title": "Badal and Moti",
            },
        }
    )

    response = TestClient(app).get(
        "/school/catalog/english/classes/3",
        headers=AUTH,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["active_chapter_id"] == "eng_c3_ch02"
    assert body["chapters"][0]["status"] == "complete"
    assert body["chapters"][1]["status"] == "ready"


@pytest.mark.parametrize(("scenario", "expected"), ENDPOINT_STATE_CASES)
def test_get_school_state_is_exhaustive_for_persisted_states(store, scenario, expected):
    _seed_endpoint_state(store, scenario)

    response = TestClient(app).get("/school/state", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == SCHOOL_STATE_KEYS
    assert body.items() >= expected.items()
    _assert_next_action_contract(body)
    assert body["learner_message"]
    assert body["parent_message"]
    if scenario == "unknown-state-is-recoverable":
        assert body["status"] == "recoverable_error"
        assert body["unlock_state"] == "locked"
        assert body["placement_status"] != "target_ready"


def test_school_state_overlaps_only_independent_reads_without_changing_output(
    store,
    monkeypatch,
):
    _seed_endpoint_state(store, "curriculum-in-progress")
    client = TestClient(app)
    expected = client.get("/school/state", headers=AUTH).json()

    active_reads = set()
    observed_overlaps = set()

    async def delayed(name, operation, *args, **kwargs):
        active_reads.add(name)
        try:
            await asyncio.sleep(0.02)
            observed_overlaps.add(frozenset(active_reads))
            return await operation(*args, **kwargs)
        finally:
            active_reads.remove(name)

    original_learner = rebuild_routes._learner_profile
    original_profile = store.get_active_school_profile_version
    original_placement = rebuild_routes._latest_placement_for_profile
    original_report = rebuild_routes._latest_placement_report_for_profile
    original_recap = rebuild_routes._latest_recap_for_profile
    original_curriculum = rebuild_routes._latest_curriculum_for_profile
    original_linked = rebuild_routes._current_linked_school_sessions
    original_processing = rebuild_routes._processing_curriculum_answer_request

    monkeypatch.setattr(
        rebuild_routes,
        "_learner_profile",
        lambda *args, **kwargs: delayed(
            "learner", original_learner, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        store,
        "get_active_school_profile_version",
        lambda *args, **kwargs: delayed(
            "profile", original_profile, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        rebuild_routes,
        "_latest_placement_for_profile",
        lambda *args, **kwargs: delayed(
            "placement", original_placement, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        rebuild_routes,
        "_latest_placement_report_for_profile",
        lambda *args, **kwargs: delayed(
            "placement_report", original_report, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        rebuild_routes,
        "_latest_recap_for_profile",
        lambda *args, **kwargs: delayed(
            "recap", original_recap, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        rebuild_routes,
        "_latest_curriculum_for_profile",
        lambda *args, **kwargs: delayed(
            "curriculum", original_curriculum, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        rebuild_routes,
        "_current_linked_school_sessions",
        lambda *args, **kwargs: delayed(
            "linked_sessions", original_linked, *args, **kwargs
        ),
    )
    monkeypatch.setattr(
        rebuild_routes,
        "_processing_curriculum_answer_request",
        lambda *args, **kwargs: delayed(
            "processing_answer", original_processing, *args, **kwargs
        ),
    )

    response = client.get("/school/state", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == expected
    for expected_pair in (
        {"learner", "profile"},
        {"placement", "placement_report"},
        {"recap", "curriculum"},
        {"linked_sessions", "processing_answer"},
    ):
        assert any(expected_pair <= overlap for overlap in observed_overlaps)


def test_school_state_routes_profile_missing_to_school_onboarding(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    _run(
        store.complete_onboarding(
            user_id="test_user",
            display_name="Open Assets",
            primary_motive="school",
            school_profile={"school_name": "Old School"},
            career_profile={},
        )
    )

    client = TestClient(app)
    response = client.get("/school/state", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["profile_status"] == "missing"
    assert body["next_action"] == "complete_profile"
    assert body["next_action_url"] == "/school/onboarding"
    assert body["unlock_state"] == "locked"


def test_school_onboarding_partial_save_reloads_without_invented_defaults(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)

    initial = client.get("/school/onboarding", headers=AUTH)
    assert initial.status_code == 200
    assert initial.json() == {
        "profile_status": "missing",
        "active_profile": None,
        "draft": None,
        "profile": None,
    }

    saved = _save_school_profile_draft(
        client,
        {"display_name": "Mira", "school_name": ""},
        current_step=1,
    )

    assert saved.status_code == 200
    draft = saved.json()["draft"]
    assert draft["status"] == "draft"
    assert draft["current_step"] == 1
    assert draft["draft_revision"] == 1
    assert draft["display_name"] == "Mira"
    assert draft["school_name"] == ""
    assert draft["board_id"] is None
    assert draft["target_class_no"] is None
    assert draft["subject_ids"] is None
    assert draft["preferred_teaching_language"] is None
    assert draft["prior_difficulty_signals"] is None

    reloaded = client.get("/school/onboarding", headers=AUTH)
    assert reloaded.status_code == 200
    assert reloaded.json()["profile_status"] == "incomplete"
    assert reloaded.json()["active_profile"] is None
    assert reloaded.json()["profile"] is None
    assert reloaded.json()["draft"] == draft

    state = client.get("/school/state", headers=AUTH).json()
    assert state["profile_status"] == "missing"
    assert state["preferred_teaching_language"] is None
    assert state["next_action"] == "complete_profile"


def test_school_onboarding_save_is_idempotent_and_conflict_safe(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    request_id = str(uuid4())
    payload = {"display_name": "Mira"}

    first = _save_school_profile_draft(
        client,
        payload,
        current_step=1,
        request_id=request_id,
    )
    duplicate = _save_school_profile_draft(
        client,
        payload,
        current_step=1,
        request_id=request_id,
    )
    changed = _save_school_profile_draft(
        client,
        {"display_name": "Mira changed"},
        current_step=1,
        request_id=request_id,
    )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.json()["draft"] == first.json()["draft"]
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "school_draft_request_conflict"
    assert len(store.school_profile_versions) == 1


def test_school_draft_save_replay_returns_original_snapshot_after_later_save(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    first_request_id = str(uuid4())
    first = _save_school_profile_draft(
        client,
        {"display_name": "Mira"},
        current_step=1,
        request_id=first_request_id,
    )
    first_draft = first.json()["draft"]
    second = _save_school_profile_draft(
        client,
        {"school_name": "Mira School"},
        current_step=2,
        profile_version_id=first_draft["profile_version_id"],
        expected_revision=first_draft["draft_revision"],
    )

    replay = _save_school_profile_draft(
        client,
        {"display_name": "Mira"},
        current_step=1,
        request_id=first_request_id,
    )

    assert second.status_code == 200
    assert second.json()["draft"]["draft_revision"] == 2
    assert replay.status_code == 200
    assert replay.json()["draft"] == first_draft
    current = _run(store.get_school_profile_draft("test_user"))
    assert current["draft_revision"] == 2
    assert current["school_name"] == "Mira School"


def test_school_draft_save_replay_survives_activation_and_conflicts_on_changed_payload(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    save_request_id = str(uuid4())
    saved = _save_school_profile_draft(
        client,
        _valid_school_profile(),
        request_id=save_request_id,
    )
    saved_draft = saved.json()["draft"]
    completed = _complete_school_profile_draft(client, saved_draft)

    replay = _save_school_profile_draft(
        client,
        _valid_school_profile(),
        request_id=save_request_id,
    )
    changed = _save_school_profile_draft(
        client,
        {**_valid_school_profile(), "display_name": "Changed learner"},
        request_id=save_request_id,
    )

    assert completed.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["draft"] == saved_draft
    assert replay.json()["active_profile"] == completed.json()["profile"]
    assert _run(store.get_school_profile_draft("test_user")) is None
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "school_draft_request_conflict"


def test_school_onboarding_rejects_stale_revision_and_keeps_one_draft(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    first = _save_school_profile_draft(client, {"display_name": "Mira"}).json()["draft"]

    updated = _save_school_profile_draft(
        client,
        {"school_name": "Mira School"},
        current_step=2,
        profile_version_id=first["profile_version_id"],
        expected_revision=first["draft_revision"],
    )
    stale = _save_school_profile_draft(
        client,
        {"board_id": "cbse"},
        current_step=2,
        profile_version_id=first["profile_version_id"],
        expected_revision=first["draft_revision"],
    )

    assert updated.status_code == 200
    assert updated.json()["draft"]["draft_revision"] == 2
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "school_draft_revision_conflict"
    drafts = [row for row in store.school_profile_versions.values() if row["status"] == "draft"]
    assert len(drafts) == 1


def test_competing_first_school_draft_saves_require_lineage_after_winner(store):
    async def compete():
        await store.ensure_profile(
            "test_user",
            name="Open Assets",
            email="open@example.com",
        )
        return await asyncio.gather(
            store.save_school_profile_draft(
                user_id="test_user",
                profile_version_id=None,
                expected_revision=None,
                current_step=1,
                request_id=str(uuid4()),
                payload_hash="first-save-a",
                patch={"display_name": "Mira"},
            ),
            store.save_school_profile_draft(
                user_id="test_user",
                profile_version_id=None,
                expected_revision=None,
                current_step=1,
                request_id=str(uuid4()),
                payload_hash="first-save-b",
                patch={"display_name": "Mira B"},
            ),
            return_exceptions=True,
        )

    results = _run(compete())

    saved = [result for result in results if isinstance(result, dict)]
    conflicts = [result for result in results if isinstance(result, ValueError)]
    assert len(saved) == 1
    assert len(conflicts) == 1
    assert str(conflicts[0]) == "school_draft_lineage_required"
    drafts = [row for row in store.school_profile_versions.values() if row["status"] == "draft"]
    assert len(drafts) == 1


def test_school_onboarding_complete_activates_exact_persisted_draft(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    draft = _save_school_profile_draft(client, _valid_school_profile()).json()["draft"]

    response = _complete_school_profile_draft(client, draft)

    assert response.status_code == 200
    body = response.json()
    assert body["profile_status"] == "complete"
    assert body["profile"]["profile_version_id"] == draft["profile_version_id"]
    assert body["profile"]["target_class_no"] == 3
    assert body["profile"]["subject_ids"] == ["english"]
    assert body["profile"]["preferred_teaching_language"] == "hi_en"

    state = client.get("/school/state", headers=AUTH).json()
    assert state["profile_status"] == "complete"
    assert state["target_class_no"] == 3
    assert state["subject_id"] == "english"
    assert state["preferred_teaching_language"] == "hi_en"
    assert state["next_action"] == "start_placement"
    assert state["next_action_url"] == "/school/readiness"


@pytest.mark.parametrize("invalid_goal", [None, "blank"])
def test_school_onboarding_complete_rejects_incomplete_or_goal_less_draft(
    store,
    invalid_goal,
):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    profile = _valid_school_profile()
    if invalid_goal is None:
        profile.pop("target_class_no")
    else:
        profile["learner_goal"] = "  "
        profile["parent_goal"] = ""
    draft = _save_school_profile_draft(client, profile).json()["draft"]

    response = _complete_school_profile_draft(client, draft)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "school_profile_incomplete"
    assert _run(store.get_active_school_profile_version("test_user")) is None
    assert store.school_profile_versions[("test_user", draft["profile_version_id"])]["status"] == "draft"


def test_school_onboarding_edit_seeds_active_and_does_not_change_state_until_activation(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)

    saved = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=3,
    )

    assert saved.status_code == 200
    body = saved.json()
    assert body["active_profile"]["profile_version_id"] == active["profile_version_id"]
    assert body["profile"] == body["active_profile"]
    assert body["draft"]["profile_version_id"] != active["profile_version_id"]
    assert body["draft"]["display_name"] == active["display_name"]
    assert body["draft"]["school_name"] == active["school_name"]
    assert body["draft"]["preferred_teaching_language"] == "en"

    state = client.get("/school/state", headers=AUTH).json()
    assert state["profile_version_id"] == active["profile_version_id"]
    assert state["preferred_teaching_language"] == "hi_en"


def test_school_onboarding_noop_activation_keeps_active_profile_and_sessions(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)
    placement = client.post("/school/placement/start", headers=AUTH).json()
    draft = _save_school_profile_draft(client, {}, current_step=4).json()["draft"]

    completed = _complete_school_profile_draft(client, draft)

    assert completed.status_code == 200
    assert completed.json()["profile"]["profile_version_id"] == active["profile_version_id"]
    assert _run(store.get_school_session("test_user", placement["session_id"]))["status"] == "active"
    assert store.school_profile_versions[("test_user", draft["profile_version_id"])]["status"] == "archived"


def test_school_onboarding_reordered_set_fields_are_noop(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)
    placement = client.post("/school/placement/start", headers=AUTH).json()
    draft = _save_school_profile_draft(
        client,
        {
            "subject_ids": list(reversed(active["subject_ids"])),
            "prior_difficulty_signals": list(
                reversed(active["prior_difficulty_signals"])
            ),
        },
        current_step=4,
    ).json()["draft"]

    completed = _complete_school_profile_draft(client, draft)

    assert completed.status_code == 200
    assert completed.json()["profile"]["profile_version_id"] == active["profile_version_id"]
    assert _run(store.get_school_session("test_user", placement["session_id"]))["status"] == "active"


def test_school_onboarding_nonmaterial_edit_versions_profile_without_restarting_session(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)
    placement = client.post("/school/placement/start", headers=AUTH).json()
    placement_row = _run(
        store.get_school_session("test_user", placement["session_id"])
    )
    _run(
        store.upsert_school_session(
            **{
                **placement_row,
                "status": "complete",
                "state_json": {
                    **placement_row["state_json"],
                    "status": "complete",
                },
            }
        )
    )
    report_id = str(uuid4())
    _run(
        store.upsert_school_placement_report(
            report_id=report_id,
            user_id="test_user",
            profile_version_id=active["profile_version_id"],
            placement_session_id=placement["session_id"],
            placement_status="target_ready",
            subject_id="english",
            target_class_no=3,
            evaluated_class_no=3,
            active_learning_class_no=3,
            unlock_state="target_unlocked",
            blocking_skills=[],
            watchlist_skills=[],
            evidence_summary={},
            recommended_recap_modules=[],
            learner_summary="Ready for Class 3.",
            parent_summary="The learner is ready for Class 3.",
            allowed_next_actions=["start_curriculum"],
        )
    )
    curriculum_session_id = str(uuid4())
    live_chapter = next(
        chapter
        for chapter in curriculum.CLASS_3_CURRICULUM_CHAPTERS
        if chapter["chapter_id"] == "eng_c3_ch01"
    )
    _run(
        store.upsert_school_session(
            session_id=curriculum_session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            profile_version_id=active["profile_version_id"],
            source_placement_report_id=report_id,
            state_json={
                "status": "active",
                "phase": "learning",
                "chapter": {
                    key: live_chapter[key]
                    for key in ("chapter_id", "title", "content_version")
                },
                "profile_version_id": active["profile_version_id"],
            },
        )
    )
    draft = _save_school_profile_draft(
        client,
        {"parent_goal": "Build a steady weekly reading habit."},
        current_step=4,
    ).json()["draft"]

    completed = _complete_school_profile_draft(client, draft)

    assert completed.status_code == 200
    replacement = completed.json()["profile"]
    assert replacement["profile_version_id"] == draft["profile_version_id"]
    assert replacement["profile_version_id"] != active["profile_version_id"]
    persisted_placement = _run(
        store.get_school_session("test_user", placement["session_id"])
    )
    persisted_curriculum = _run(
        store.get_school_session("test_user", curriculum_session_id)
    )
    assert persisted_placement["status"] == "complete"
    assert persisted_curriculum["status"] == "active"
    assert persisted_placement["profile_version_id"] == active["profile_version_id"]
    assert persisted_placement["state_json"]["profile_version_id"] == active[
        "profile_version_id"
    ]
    assert persisted_curriculum["profile_version_id"] == replacement[
        "profile_version_id"
    ]
    assert persisted_curriculum["state_json"]["profile_version_id"] == replacement[
        "profile_version_id"
    ]
    report = _run(
        store.get_school_placement_report(
            "test_user",
            placement["session_id"],
            profile_version_id=active["profile_version_id"],
        )
    )
    assert report is not None
    assert report["profile_version_id"] == active["profile_version_id"]
    assert (
        _run(
            store.get_school_placement_report(
                "test_user",
                placement["session_id"],
                profile_version_id=replacement["profile_version_id"],
            )
        )
        is None
    )
    state = client.get("/school/state", headers=AUTH).json()
    assert state["profile_version_id"] == replacement["profile_version_id"]
    assert state["active_session_id"] == curriculum_session_id
    assert state["next_action"] == "resume_curriculum"


def test_school_onboarding_material_activation_expires_prior_profile_sessions(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    first_profile = _save_and_complete_school_profile(client)
    first_placement = client.post("/school/placement/start", headers=AUTH).json()
    draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]

    replacement = _complete_school_profile_draft(client, draft)

    assert replacement.status_code == 200
    replacement_profile = replacement.json()["profile"]
    assert replacement_profile["profile_version_id"] == draft["profile_version_id"]
    assert replacement_profile["profile_version_id"] != first_profile["profile_version_id"]
    old_row = _run(store.get_school_session("test_user", first_placement["session_id"]))
    assert old_row["profile_version_id"] == first_profile["profile_version_id"]
    assert old_row["status"] == "expired"

    learner = _run(store.get_profile("test_user"))
    assert learner["name"] == replacement_profile["display_name"]
    assert learner["primary_motive"] == "school"
    assert learner["school_profile"]["school_name"] == replacement_profile["school_name"]
    assert learner["onboarding_completed_at"] is not None
    assert learner["onboarding_state"] == {}


def test_school_onboarding_activation_request_is_required_idempotent_and_bound(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    draft = _save_school_profile_draft(client, _valid_school_profile()).json()["draft"]
    activation_request_id = str(uuid4())

    missing_request = client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
        },
    )
    first = _complete_school_profile_draft(
        client,
        draft,
        request_id=activation_request_id,
    )
    duplicate = _complete_school_profile_draft(
        client,
        draft,
        request_id=activation_request_id,
    )
    active_replay = _complete_school_profile_draft(
        client,
        draft,
        request_id=activation_request_id,
    )

    assert missing_request.status_code == 422
    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.json()["profile"] == first.json()["profile"]
    assert active_replay.status_code == 200
    assert active_replay.json()["profile"] == first.json()["profile"]

    next_draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]
    reused = _complete_school_profile_draft(
        client,
        next_draft,
        request_id=activation_request_id,
    )
    assert reused.status_code == 409
    assert reused.json()["detail"]["code"] == "school_activation_request_conflict"


def test_school_onboarding_cannot_complete_arbitrary_active_profile(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    profile_version_id = str(uuid4())
    now = 1.0
    store.school_profile_versions[("test_user", profile_version_id)] = {
        **_valid_school_profile(),
        "profile_version_id": profile_version_id,
        "user_id": "test_user",
        "status": "active",
        "current_step": 4,
        "draft_revision": 1,
        "source_profile_version_id": None,
        "activation_request_id": None,
        "activation_payload_hash": None,
        "activation_result_profile_version_id": None,
        "created_at": now,
        "updated_at": now,
        "activated_at": now,
        "archived_at": None,
    }

    response = TestClient(app).post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": profile_version_id,
            "expected_revision": 1,
            "request_id": str(uuid4()),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "school_profile_already_active"
    active = _run(store.get_active_school_profile_version("test_user"))
    assert active["activation_request_id"] is None


def test_school_profile_activation_rolls_back_profile_learner_and_sessions(store, monkeypatch):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    first_profile = _save_and_complete_school_profile(client)
    placement = client.post("/school/placement/start", headers=AUTH).json()
    draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]
    profile_rows_before = copy.deepcopy(store.school_profile_versions)
    learner_before = copy.deepcopy(store.profiles)
    sessions_before = copy.deepcopy(store.school_sessions)

    async def fail_expiration(_user_id: str, _profile_version_id: str) -> int:
        raise RuntimeError("injected session expiration failure")

    monkeypatch.setattr(store, "expire_active_school_sessions_from_other_profiles", fail_expiration)
    failed_client = TestClient(app, raise_server_exceptions=False)

    response = _complete_school_profile_draft(failed_client, draft)

    assert response.status_code == 500
    assert _run(store.get_active_school_profile_version("test_user"))["profile_version_id"] == first_profile["profile_version_id"]
    assert store.school_profile_versions == profile_rows_before
    assert store.profiles == learner_before
    assert store.school_sessions == sessions_before
    assert _run(store.get_school_session("test_user", placement["session_id"]))["status"] == "active"


def test_school_session_upsert_preserves_lineage_and_requires_it_for_new_active_rebuild(
    store,
):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    profile = _save_and_complete_school_profile(TestClient(app))
    session_id = "lineage-preservation-session"
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="recap",
            subject_id="english",
            class_no=3,
            status="active",
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="lineage-report",
            state_json={"status": "active"},
        )
    )

    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="recap",
            subject_id="english",
            class_no=3,
            status="active",
            profile_version_id=None,
            source_placement_report_id=None,
            state_json={"status": "active", "updated": True},
        )
    )

    saved = _run(store.get_school_session("test_user", session_id))
    assert saved["profile_version_id"] == profile["profile_version_id"]
    assert saved["source_placement_report_id"] == "lineage-report"

    with pytest.raises(ValueError, match="school_session_lineage_conflict"):
        _run(
            store.upsert_school_session(
                session_id=session_id,
                user_id="test_user",
                api_version="rebuild",
                flow_type="recap",
                subject_id="english",
                class_no=3,
                status="active",
                profile_version_id=None,
                source_placement_report_id=None,
                state_json={
                    "status": "active",
                    "profile_version_id": "00000000-0000-4000-8000-000000000099",
                },
            )
        )

    with pytest.raises(ValueError, match="active_school_session_profile_lineage_required"):
        _run(
            store.upsert_school_session(
                session_id="missing-profile-lineage",
                user_id="test_user",
                api_version="rebuild",
                flow_type="placement",
                subject_id="english",
                class_no=4,
                status="active",
                state_json={},
            )
        )


def test_school_session_upsert_rejects_archived_api_versions_from_becoming_active(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))

    with pytest.raises(ValueError, match="archived_school_api_version"):
        _run(
            store.upsert_school_session(
                session_id="archived-v3-session",
                user_id="test_user",
                api_version="v3",
                flow_type="placement",
                subject_id="english",
                class_no=3,
                status="active",
                state_json={},
            )
        )


def test_school_session_upsert_rejects_terminal_resurrection_after_activation(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    old_profile = _save_and_complete_school_profile(client)
    kwargs = {
        "session_id": "stale-lineage-session",
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "placement",
        "subject_id": "english",
        "class_no": 3,
        "profile_version_id": old_profile["profile_version_id"],
        "state_json": {"status": "active"},
    }
    _run(store.upsert_school_session(**kwargs, status="active"))
    draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]
    _complete_school_profile_draft(client, draft)

    with pytest.raises(ValueError, match="stale_school_session_transition"):
        _run(store.upsert_school_session(**kwargs, status="active"))
    with pytest.raises(ValueError, match="stale_school_session_transition"):
        _run(
            store.upsert_school_session(
                **{
                    **kwargs,
                    "status": "complete",
                    "state_json": {"status": "complete"},
                }
            )
        )
    saved = _run(store.get_school_session("test_user", "stale-lineage-session"))
    assert saved["status"] == "expired"
    assert saved["profile_version_id"] == old_profile["profile_version_id"]

    _run(
        store.upsert_school_session(
            **{
                **kwargs,
                "status": "expired",
                "state_json": saved["state_json"],
            }
        )
    )
    assert _run(store.get_school_session("test_user", "stale-lineage-session"))[
        "status"
    ] == "expired"


@pytest.mark.parametrize("winner", ["activation", "terminal"])
def test_school_profile_activation_and_terminal_transition_are_serialized(store, winner):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)
    session_kwargs = {
        "session_id": f"race-{winner}",
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "placement",
        "subject_id": "english",
        "class_no": 3,
        "status": "active",
        "profile_version_id": active["profile_version_id"],
        "state_json": {"status": "active"},
    }
    _run(store.upsert_school_session(**session_kwargs))
    draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]

    async def race():
        lock = store._school_lineage_lock("test_user")
        await lock.acquire()
        activation = lambda: store.activate_school_profile_draft(
            user_id="test_user",
            profile_version_id=draft["profile_version_id"],
            expected_revision=draft["draft_revision"],
            request_id=str(uuid4()),
            payload_hash=f"race-{winner}",
        )
        terminal = lambda: store.upsert_school_session(
            **{
                **session_kwargs,
                "status": "complete",
                "state_json": {"status": "complete"},
            }
        )
        first_factory, second_factory = (
            (activation, terminal) if winner == "activation" else (terminal, activation)
        )
        first = asyncio.create_task(first_factory())
        await asyncio.sleep(0)
        second = asyncio.create_task(second_factory())
        await asyncio.sleep(0)
        lock.release()
        return await asyncio.gather(first, second, return_exceptions=True)

    results = _run(race())
    row = _run(store.get_school_session("test_user", session_kwargs["session_id"]))
    if winner == "activation":
        assert isinstance(results[0], dict)
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "stale_school_session_transition"
        assert row["status"] == "expired"
    else:
        assert results[0] is None
        assert isinstance(results[1], dict)
        assert row["status"] == "complete"
        _run(
            store.upsert_school_session(
                **{
                    **session_kwargs,
                    "status": "complete",
                    "state_json": {"status": "complete"},
                }
            )
        )


def test_curriculum_persist_rejects_terminal_transition_after_profile_expiry(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)
    session = {
        "session_id": "stale-curriculum-terminal",
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 3,
        "status": "active",
        "profile_version_id": active["profile_version_id"],
        "state_json": {"status": "active", "step": 1},
    }
    _run(store.upsert_school_session(**session))
    draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]
    _complete_school_profile_draft(client, draft)

    with pytest.raises(ValueError, match="stale_school_session_transition"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={"source_event_key": "stale-terminal-event"},
                school_session={
                    **session,
                    "status": "complete",
                    "state_json": {"status": "complete", "step": 1},
                },
                expected_state_json=session["state_json"],
            )
        )

    row = _run(store.get_school_session("test_user", session["session_id"]))
    assert row["status"] == "expired"
    assert not any(
        event.get("source_event_key") == "stale-terminal-event"
        for event in store.learning_events
    )


def test_activation_and_active_session_upsert_share_learner_lineage_lock():
    activation_source = inspect.getsource(repo.activate_school_profile_draft)
    upsert_source = inspect.getsource(repo.upsert_school_session)

    assert "await _lock_school_profile_lineage(session, user_id)" in activation_source
    assert "await _lock_school_profile_lineage(session, user_id)" in upsert_source
    assert "status = 'active'" in upsert_source
    assert "FOR SHARE" in upsert_source


def test_postgres_school_session_upsert_coalesces_omitted_lineage():
    source = Path("app/db/repo.py").read_text().lower()

    assert (
        "profile_version_id = coalesce(excluded.profile_version_id, "
        "school_sessions.profile_version_id)"
    ) in source
    assert (
        "source_placement_report_id = coalesce(excluded.source_placement_report_id, "
        "school_sessions.source_placement_report_id)"
    ) in source


def test_school_repo_casts_optional_uuid_null_checks():
    source = "\n".join(
        inspect.getsource(function)
        for function in (
            repo.get_active_school_session,
            repo.get_latest_school_session,
            repo.get_school_placement_report,
        )
    )

    uncast_parameters = re.findall(
        r"(?<!cast\():([a-z_][a-z0-9_]*)\s+is\s+null",
        source,
        flags=re.IGNORECASE,
    )

    assert uncast_parameters == []


def test_global_school_onboarding_routes_to_school_not_subjects(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)

    response = client.post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Open Assets",
            "primary_motive": "school",
            "school_profile": {"school_name": "Open Assets Test School"},
        },
    )

    assert response.status_code == 200
    assert response.json()["destination"] == "/school"


def test_school_answer_attempt_persists_event_state_report_and_response_atomically(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    profile = _save_and_complete_school_profile(TestClient(app))
    session_id = str(uuid4())
    initial_state = {"status": "active", "step": 1}
    session = {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "placement",
        "subject_id": "english",
        "class_no": 3,
        "status": "active",
        "profile_version_id": profile["profile_version_id"],
        "state_json": initial_state,
    }
    _run(store.upsert_school_session(**session))
    answer_hash = "answer-hash"
    claim = _run(
        store.claim_school_answer_request(
            "test_user", session_id, "placement-item", answer_hash
        )
    )
    report = {
        "report_id": str(uuid4()),
        "user_id": "test_user",
        "profile_version_id": profile["profile_version_id"],
        "placement_session_id": session_id,
        "placement_status": "target_ready",
    }
    response = {"session_id": session_id, "status": "complete"}

    _run(
        store.persist_school_answer_attempt(
            learning_event={
                "source_event_key": "school-answer-atomic",
                "user_id": "test_user",
                "session_id": session_id,
            },
            school_session={
                **session,
                "status": "complete",
                "state_json": {"status": "complete", "step": 2},
            },
            expected_state_json=initial_state,
            request_activity_id="placement-item",
            request_answer_hash=answer_hash,
            request_claim_token=claim["claim_token"],
            response_json=response,
            placement_report=report,
        )
    )

    saved_session = _run(store.get_school_session("test_user", session_id))
    saved_request = _run(
        store.get_school_answer_request("test_user", session_id, "placement-item")
    )
    saved_report = _run(store.get_school_placement_report("test_user", session_id))
    assert saved_session["status"] == "complete"
    assert saved_session["state_json"]["step"] == 2
    assert saved_request["status"] == "completed"
    assert saved_request["response_json"] == response
    assert saved_report["report_id"] == report["report_id"]
    assert any(
        event.get("source_event_key") == "school-answer-atomic"
        for event in store.learning_events
    )


@pytest.mark.parametrize("winner", ["activation", "answer"])
def test_school_answer_attempt_and_activation_are_serialized(store, winner):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    active = _save_and_complete_school_profile(client)
    session_id = str(uuid4())
    initial_state = {"status": "active", "step": 1}
    session = {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "placement",
        "subject_id": "english",
        "class_no": 3,
        "status": "active",
        "profile_version_id": active["profile_version_id"],
        "state_json": initial_state,
    }
    _run(store.upsert_school_session(**session))
    answer_hash = "race-answer-hash"
    claim = _run(
        store.claim_school_answer_request(
            "test_user", session_id, "race-item", answer_hash
        )
    )
    draft = _save_school_profile_draft(
        client,
        {"preferred_teaching_language": "en"},
        current_step=4,
    ).json()["draft"]

    async def race():
        lock = store._school_lineage_lock("test_user")
        await lock.acquire()
        activation = lambda: store.activate_school_profile_draft(
            user_id="test_user",
            profile_version_id=draft["profile_version_id"],
            expected_revision=draft["draft_revision"],
            request_id=str(uuid4()),
            payload_hash=f"answer-race-{winner}",
        )
        answer = lambda: store.persist_school_answer_attempt(
            learning_event={
                "source_event_key": f"answer-race-event-{winner}",
                "user_id": "test_user",
                "session_id": session_id,
            },
            school_session={
                **session,
                "status": "complete",
                "state_json": {"status": "complete", "step": 2},
            },
            expected_state_json=initial_state,
            request_activity_id="race-item",
            request_answer_hash=answer_hash,
            request_claim_token=claim["claim_token"],
            response_json={"status": "complete"},
        )
        first_factory, second_factory = (
            (activation, answer) if winner == "activation" else (answer, activation)
        )
        first = asyncio.create_task(first_factory())
        await asyncio.sleep(0)
        second = asyncio.create_task(second_factory())
        await asyncio.sleep(0)
        lock.release()
        return await asyncio.gather(first, second, return_exceptions=True)

    results = _run(race())
    saved = _run(store.get_school_session("test_user", session_id))
    if winner == "activation":
        assert isinstance(results[0], dict)
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "stale_school_session_transition"
        assert saved["status"] == "expired"
        assert not any(
            event.get("source_event_key") == "answer-race-event-activation"
            for event in store.learning_events
        )
    else:
        assert results[0] is None
        assert isinstance(results[1], dict)
        assert saved["status"] == "complete"
        request_row = _run(
            store.get_school_answer_request("test_user", session_id, "race-item")
        )
        assert request_row["status"] == "completed"


def test_school_session_get_or_create_serializes_concurrent_starts(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    profile = _save_and_complete_school_profile(TestClient(app))

    async def create(session_id: str):
        return await store.get_or_create_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="placement",
            subject_id="english",
            class_no=3,
            status="active",
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=None,
            state_json={"profile_version_id": profile["profile_version_id"]},
        )

    async def race():
        return await asyncio.gather(create(str(uuid4())), create(str(uuid4())))

    first, second = _run(race())

    assert first["session_id"] == second["session_id"]
    assert len(
        [
            row
            for row in store.school_sessions.values()
            if row.get("user_id") == "test_user"
            and row.get("flow_type") == "placement"
            and row.get("status") == "active"
        ]
    ) == 1


def test_school_session_compare_and_set_allows_only_one_lifecycle_winner(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    profile = _save_and_complete_school_profile(TestClient(app))
    session_id = str(uuid4())
    original_state = {
        "profile_version_id": profile["profile_version_id"],
        "phase": "paused_for_masterclass",
        "active_interrupt": {"interrupt_id": "interrupt-1"},
    }
    _run(store.upsert_school_session(
        session_id=session_id,
        user_id="test_user",
        api_version="rebuild",
        flow_type="curriculum",
        subject_id="english",
        class_no=3,
        status="paused_for_masterclass",
        profile_version_id=profile["profile_version_id"],
        source_placement_report_id=None,
        state_json=original_state,
    ))
    write = {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 3,
        "status": "active",
        "current_stage": "learning",
        "linked_session_id": None,
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": None,
        "state_json": {
            "profile_version_id": profile["profile_version_id"],
            "phase": "learning",
            "active_interrupt": None,
        },
    }

    first = _run(store.compare_and_set_school_session(
        school_session=write,
        expected_state_json=original_state,
    ))
    second = _run(store.compare_and_set_school_session(
        school_session=write,
        expected_state_json=original_state,
    ))

    assert first is True
    assert second is False


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("get", "/school/placement/not-a-uuid", None),
        (
            "post",
            "/school/placement/not-a-uuid/answer",
            {"item_id": "item", "answer": "answer"},
        ),
        ("get", "/school/recap/not-a-uuid", None),
        (
            "post",
            "/school/recap/not-a-uuid/answer",
            {"activity_id": "activity", "answer": "answer"},
        ),
        ("get", "/school/curriculum/not-a-uuid", None),
        (
            "post",
            "/school/curriculum/not-a-uuid/answer",
            {"activity_id": "activity", "answer": "answer"},
        ),
    ],
)
def test_canonical_school_session_paths_reject_malformed_uuid(
    store,
    method,
    path,
    json_body,
):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    response = TestClient(app).request(
        method,
        path,
        headers=AUTH,
        json=json_body,
    )

    assert response.status_code == 422
