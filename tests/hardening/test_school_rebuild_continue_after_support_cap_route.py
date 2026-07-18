from __future__ import annotations

import asyncio
from copy import deepcopy
from uuid import UUID

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services.school.authority import CANONICAL_SCHOOL_AUTHORITY
from tests.hardening.test_school_rebuild_curriculum_v2_runtime import (
    _advance_to_phase,
    _pause_for_masterclass,
    _state,
    _wrong_current_answer,
)


SESSION_ID = UUID("8c2f5eef-5276-47f3-b04f-d252f4f31c9c")
USER_ID = "support-cap-learner"


def _run(coro):
    return asyncio.run(coro)


def _request(*, authenticated: bool = True) -> Request:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": f"/school/curriculum/{SESSION_ID}/continue-after-support-cap",
            "headers": [],
        }
    )
    if authenticated:
        request.state.user_id = USER_ID
    return request


def _capped_state() -> dict:
    state = _advance_to_phase(_state(), "review")
    for trigger in (1, 2):
        state = _pause_for_masterclass(state)
        child_id = f"masterclass-{trigger}"
        state = curriculum.attach_masterclass_session(
            state,
            masterclass_session_id=child_id,
        )
        state = curriculum.resume_after_masterclass(
            state,
            masterclass_session_id=child_id,
            resolution="abandoned",
        )
    state, _evaluation = _wrong_current_answer(state)
    state, _evaluation = _wrong_current_answer(state)
    assert state["phase"] == "capped_support"
    return state


def _row(state: dict) -> dict:
    return {
        "session_id": str(SESSION_ID),
        "user_id": USER_ID,
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": str(state["status"]),
        "current_stage": "0",
        "linked_session_id": None,
        "profile_version_id": "profile-1",
        "source_placement_report_id": "report-1",
        "state_json": deepcopy(state),
    }


class _RouteStore:
    """Only exposes the read/CAS surface allowed for this transition."""

    def __init__(self, row: dict, *, cas_result: bool = True, row_after_cas=None):
        self.row = deepcopy(row)
        self.cas_result = cas_result
        self.row_after_cas = deepcopy(row_after_cas)
        self.cas_calls: list[dict] = []
        self.get_calls: list[tuple[str, str]] = []

    async def compare_and_set_school_session(
        self,
        *,
        school_session: dict,
        expected_state_json: dict,
    ) -> bool:
        self.cas_calls.append(
            {
                "school_session": deepcopy(school_session),
                "expected_state_json": deepcopy(expected_state_json),
            }
        )
        if self.cas_result:
            self.row = {**self.row, **deepcopy(school_session)}
            return True
        if self.row_after_cas is not None:
            self.row = deepcopy(self.row_after_cas)
        return False

    async def get_school_session(self, user_id: str, session_id: str) -> dict:
        self.get_calls.append((user_id, session_id))
        return deepcopy(self.row)


def _install_parent_lookup(monkeypatch, store: _RouteStore):
    calls: list[tuple[str, str]] = []

    async def lookup(*, user_id: str, session_id: str):
        calls.append((user_id, session_id))
        return store, deepcopy(store.row), {"profile_version_id": "profile-1"}, {
            "report_id": "report-1"
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_curriculum_parent_for_masterclass",
        lookup,
    )
    return calls


def test_continue_after_support_cap_route_is_canonical():
    expected = (
        "POST",
        "/school/curriculum/{session_id}/continue-after-support-cap",
        "continue_school_curriculum_after_support_cap",
        "app.services.school_rebuild_curriculum",
    )
    assert any(
        (entry.method, entry.path, entry.endpoint_name, entry.owning_service)
        == expected
        for entry in CANONICAL_SCHOOL_AUTHORITY
    )


def test_continue_after_support_cap_is_mounted_and_uses_authenticated_lineage(
    monkeypatch,
):
    capped = _capped_state()
    row = _row(capped)
    row["user_id"] = "test_user"
    store = _RouteStore(row)
    lookup_calls: list[tuple[str, str]] = []

    async def lookup(*, user_id: str, session_id: str):
        lookup_calls.append((user_id, session_id))
        return store, deepcopy(store.row), {"profile_version_id": "profile-1"}, {
            "report_id": "report-1"
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_curriculum_parent_for_masterclass",
        lookup,
    )

    response = TestClient(app).post(
        f"/school/curriculum/{SESSION_ID}/continue-after-support-cap",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200, response.text
    assert lookup_calls == [("test_user", str(SESSION_ID))]
    assert len(store.cas_calls) == 1
    assert response.json()["feedback_v2"]["outcome"] == (
        "continued_after_support_cap"
    )


def test_continue_after_support_cap_authenticates_before_lineage_lookup(monkeypatch):
    store = _RouteStore(_row(_capped_state()))
    lookup_calls = _install_parent_lookup(monkeypatch, store)

    with pytest.raises(HTTPException) as exc_info:
        _run(
            school_rebuild_routes.continue_school_curriculum_after_support_cap(
                SESSION_ID,
                _request(authenticated=False),
            )
        )

    assert exc_info.value.status_code == 401
    assert lookup_calls == []
    assert store.cas_calls == []


def test_continue_after_support_cap_persists_one_unscored_session_transition(
    monkeypatch,
):
    capped = _capped_state()
    store = _RouteStore(_row(capped))
    lookup_calls = _install_parent_lookup(monkeypatch, store)

    response = _run(
        school_rebuild_routes.continue_school_curriculum_after_support_cap(
            SESSION_ID,
            _request(),
        )
    )

    assert lookup_calls == [(USER_ID, str(SESSION_ID))]
    assert len(store.cas_calls) == 1
    assert store.cas_calls[0]["expected_state_json"] == capped
    persisted = store.cas_calls[0]["school_session"]
    assert persisted["status"] == "active"
    assert persisted["state_json"]["phase"] == "learning"
    assert persisted["state_json"]["feedback_v2"]["scored"] is False
    assert response["phase"] == "learning"
    assert response["current_activity"] is not None
    assert response["feedback_v2"]["outcome"] == "continued_after_support_cap"


def test_continue_after_support_cap_duplicate_returns_persisted_response_without_write(
    monkeypatch,
):
    transitioned = curriculum.continue_after_support_cap(_capped_state())
    store = _RouteStore(_row(transitioned))
    _install_parent_lookup(monkeypatch, store)

    response = _run(
        school_rebuild_routes.continue_school_curriculum_after_support_cap(
            SESSION_ID,
            _request(),
        )
    )

    assert response["phase"] == "learning"
    assert response["feedback_v2"]["outcome"] == "continued_after_support_cap"
    assert store.cas_calls == []


def test_continue_after_support_cap_concurrent_duplicate_reloads_completed_transition(
    monkeypatch,
):
    capped = _capped_state()
    transitioned = curriculum.continue_after_support_cap(capped)
    store = _RouteStore(
        _row(capped),
        cas_result=False,
        row_after_cas=_row(transitioned),
    )
    _install_parent_lookup(monkeypatch, store)

    response = _run(
        school_rebuild_routes.continue_school_curriculum_after_support_cap(
            SESSION_ID,
            _request(),
        )
    )

    assert len(store.cas_calls) == 1
    assert store.get_calls == [(USER_ID, str(SESSION_ID))]
    assert response["feedback_v2"]["outcome"] == "continued_after_support_cap"


def test_continue_after_support_cap_rejects_stale_state_instead_of_overwriting(
    monkeypatch,
):
    capped = _capped_state()
    stale_row = _row(capped)
    stale_row["state_json"] = {
        **capped,
        "phase": "learning",
        "feedback_v2": {"outcome": "another_transition", "scored": False},
    }
    store = _RouteStore(
        _row(capped),
        cas_result=False,
        row_after_cas=stale_row,
    )
    _install_parent_lookup(monkeypatch, store)

    with pytest.raises(HTTPException) as exc_info:
        _run(
            school_rebuild_routes.continue_school_curriculum_after_support_cap(
                SESSION_ID,
                _request(),
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "code": "curriculum_support_cap_transition_conflict"
    }
    assert len(store.cas_calls) == 1


def test_continue_after_support_cap_requires_capped_support_state(monkeypatch):
    store = _RouteStore(_row(_state()))
    _install_parent_lookup(monkeypatch, store)

    with pytest.raises(HTTPException) as exc_info:
        _run(
            school_rebuild_routes.continue_school_curriculum_after_support_cap(
                SESSION_ID,
                _request(),
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {"code": "curriculum_not_capped_for_support"}
    assert store.cas_calls == []
