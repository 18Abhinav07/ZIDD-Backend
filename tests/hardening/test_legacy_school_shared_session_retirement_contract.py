import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import session_service as svc


AUTH = {"Authorization": "Bearer test_token"}
LEGACY_MODULE_ID = "school_english"
LEGACY_NODE_ID = "c5_tenses_mix"
RETIREMENT_CODE = "legacy_school_module_retired"
MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "app/db/migrations/2026-07-16-retire-legacy-school-shared-sessions.sql"
)
SCHEMA = Path(__file__).resolve().parents[2] / "app/db/schema.sql"


def _run(coro):
    return asyncio.run(coro)


def _legacy_runtime(session_id: str, user_id: str = "test_user") -> dict:
    return {
        "session_id": session_id,
        "user_id": user_id,
        "current_node": LEGACY_NODE_ID,
        "module_id": LEGACY_MODULE_ID,
        "task_type": "school_lesson",
        "test_mode": False,
        "status": "active",
        "state_snapshot": {
            "session_id": session_id,
            "user_id": user_id,
            "competency_node": LEGACY_NODE_ID,
            "module_id": LEGACY_MODULE_ID,
            "task_type": "school_lesson",
        },
        "pending_transition": None,
        "session_version": 1,
        "active_turn_id": None,
        "active_opening_id": None,
        "last_error": None,
        "lease_expires_at": None,
    }


def _mismatched_career_runtime(
    session_id: str,
    *,
    top_level: dict | None = None,
    snapshot: dict | None = None,
) -> dict:
    row = {
        "session_id": session_id,
        "user_id": "test_user",
        "current_node": "int_01_elevator_pitch",
        "module_id": "interview",
        "task_type": "interview_prep",
        "test_mode": False,
        "status": "active",
        "state_snapshot": {
            "session_id": session_id,
            "user_id": "test_user",
            "competency_node": "int_01_elevator_pitch",
            "module_id": "interview",
            "task_type": "interview_prep",
        },
        "pending_transition": None,
        "session_version": 1,
        "active_turn_id": None,
        "active_opening_id": None,
        "last_error": None,
        "lease_expires_at": None,
    }
    row.update(top_level or {})
    row["state_snapshot"].update(snapshot or {})
    return row


def _parent_only_retired_runtime(
    session_id: str,
    user_id: str = "test_user",
) -> dict:
    row = _mismatched_career_runtime(session_id)
    row["user_id"] = user_id
    row["status"] = "ended"
    row["state_snapshot"].update(
        {
            "user_id": user_id,
            "status": "ended",
            "session_over": True,
            "input_allowed": False,
            "block_reason": RETIREMENT_CODE,
        }
    )
    row["last_error"] = {
        "code": RETIREMENT_CODE,
        "replacement": "/school",
    }
    return row


@pytest.mark.parametrize(
    "path",
    (
        "/session/progress/me?module_id=school_english",
        "/session/progress/test_user?module_id=school_english",
    ),
)
def test_progress_routes_return_gone_for_legacy_school_module(store, path):
    _run(store.ensure_profile("test_user"))

    response = TestClient(app).get(path, headers=AUTH)

    assert response.status_code == 410
    assert response.json()["detail"] == {
        "code": "legacy_school_module_retired",
        "replacement": "/school",
    }


def test_shared_session_read_rejects_legacy_school_during_hydration(store):
    _run(store.ensure_profile("test_user"))
    session_id = "legacy-school-runtime"
    store.session_runtime[session_id] = _legacy_runtime(session_id)

    response = TestClient(app).get(
        f"/session/{session_id}/state",
        headers=AUTH,
    )

    assert response.status_code == 410
    assert response.json()["detail"] == {
        "code": "legacy_school_module_retired",
        "replacement": "/school",
    }
    assert session_id not in svc.SessionStore


def test_shared_session_read_rejects_and_evicts_cached_legacy_school(store):
    _run(store.ensure_profile("test_user"))
    session_id = "legacy-school-cached"
    svc.SessionStore[session_id] = svc._new_state(
        "test_user",
        session_id,
        LEGACY_NODE_ID,
        [],
        task_type="school_english",
        module_id=LEGACY_MODULE_ID,
    )

    response = TestClient(app).get(
        f"/session/{session_id}/transcript",
        headers=AUTH,
    )

    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "legacy_school_module_retired"
    assert session_id not in svc.SessionStore


def test_legacy_school_retirement_does_not_bypass_session_ownership(store):
    _run(store.ensure_profile("test_user"))
    session_id = "other-users-legacy-school-runtime"
    store.session_runtime[session_id] = _legacy_runtime(
        session_id,
        user_id="another_user",
    )

    response = TestClient(app).get(
        f"/session/{session_id}/state",
        headers=AUTH,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "not your session"


@pytest.mark.parametrize(
    ("runtime_owner", "expected_status"),
    (("test_user", 410), ("another_user", 403)),
)
def test_parent_only_retired_runtime_route_preserves_ownership(
    store,
    runtime_owner,
    expected_status,
):
    _run(store.ensure_profile("test_user"))
    session_id = f"parent-only-retired-{runtime_owner}"
    store.session_runtime[session_id] = _parent_only_retired_runtime(
        session_id,
        user_id=runtime_owner,
    )

    response = TestClient(app, raise_server_exceptions=False).get(
        f"/session/{session_id}/state",
        headers=AUTH,
    )

    assert response.status_code == expected_status
    if expected_status == 410:
        assert response.json()["detail"] == {
            "code": RETIREMENT_CODE,
            "replacement": "/school",
        }
    else:
        assert response.json()["detail"] == "not your session"


@pytest.mark.parametrize(
    ("source_owner", "expected_status"),
    (("test_user", 410), ("another_user", 403)),
)
def test_career_start_translates_retired_school_source_by_ownership(
    store,
    source_owner,
    expected_status,
):
    _run(store.ensure_profile("test_user"))
    source_session_id = f"retired-school-source-{source_owner}"
    store.session_runtime[source_session_id] = _legacy_runtime(
        source_session_id,
        user_id=source_owner,
    )

    response = TestClient(app, raise_server_exceptions=False).post(
        "/session/start",
        headers=AUTH,
        json={
            "competency_node": "int_01_elevator_pitch",
            "client_start_id": f"career-from-retired-school-{source_owner}",
            "source_session_id": source_session_id,
            "source_transition_id": "retired-school-transition",
            "source_action": "advance",
        },
    )

    assert response.status_code == expected_status
    if expected_status == 410:
        assert response.json()["detail"] == {
            "code": "legacy_school_module_retired",
            "replacement": "/school",
        }
    else:
        assert response.json()["detail"] == "not your session"


@pytest.mark.parametrize(
    ("marker", "top_level", "snapshot"),
    (
        ("top_module", {"module_id": LEGACY_MODULE_ID}, {}),
        ("top_task", {"task_type": LEGACY_MODULE_ID}, {}),
        ("snapshot_module", {}, {"module_id": LEGACY_MODULE_ID}),
        ("snapshot_task", {}, {"task_type": LEGACY_MODULE_ID}),
    ),
)
def test_hydration_rejects_legacy_school_in_every_runtime_marker(
    store,
    marker,
    top_level,
    snapshot,
):
    session_id = f"mismatched-runtime-{marker}"
    store.session_runtime[session_id] = _mismatched_career_runtime(
        session_id,
        top_level=top_level,
        snapshot=snapshot,
    )

    with pytest.raises(svc.LegacySchoolModuleRetiredError):
        _run(svc.get_session_state(session_id))

    assert session_id not in svc.SessionStore


@pytest.mark.parametrize(
    ("marker", "top_level", "snapshot"),
    (
        ("last_error", {"last_error": {"code": RETIREMENT_CODE}}, {}),
        ("snapshot_block_reason", {}, {"block_reason": RETIREMENT_CODE}),
    ),
)
def test_hydration_rejects_parent_only_legacy_retirement_sentinel(
    store,
    marker,
    top_level,
    snapshot,
):
    session_id = f"parent-only-sentinel-{marker}"
    row = _mismatched_career_runtime(
        session_id,
        top_level=top_level,
        snapshot=snapshot,
    )
    row["status"] = "ended"
    store.session_runtime[session_id] = row

    with pytest.raises(svc.LegacySchoolModuleRetiredError):
        _run(svc.get_session_state(session_id))

    assert session_id not in svc.SessionStore


def test_registered_additive_migration_terminalizes_legacy_shared_sessions():
    sql = MIGRATION.read_text().lower()

    assert "update public.session_runtime" in sql
    assert "update public.sessions" in sql
    assert "module_id = 'school_english'" in sql
    assert "task_type = 'school_english'" in sql
    assert "status = 'ended'" in sql
    assert "legacy_school_module_retired" in sql
    assert "pending_transition = null" in sql
    assert "active_turn_id = null" in sql
    assert "active_opening_id = null" in sql


def test_retirement_migration_uses_one_fail_fast_quiescence_gate_before_cutover():
    sql = " ".join(MIGRATION.read_text().lower().split())
    lock_statement = (
        "lock table public.sessions, public.session_runtime "
        "in access exclusive mode nowait;"
    )

    lock_position = sql.index(lock_statement)
    first_guard = sql.index(
        "create or replace function public.reject_active_legacy_school_session_row"
    )
    first_terminalization = min(
        sql.index("update public.session_runtime"),
        sql.index("update public.sessions"),
    )

    assert sql.count("lock table ") == 1
    assert "share row exclusive" not in sql
    assert lock_position < first_guard < first_terminalization


def test_retirement_migration_installs_durable_legacy_write_guards():
    sql = " ".join(MIGRATION.read_text().lower().split())

    session_function_start = sql.index(
        "create or replace function public.reject_active_legacy_school_session_row"
    )
    session_function_end = sql.index(
        "drop trigger if exists sessions_reject_active_legacy_school"
    )
    runtime_function_start = sql.index(
        "create or replace function public.reject_active_legacy_school_runtime_row"
    )
    runtime_function_end = sql.index(
        "drop trigger if exists session_runtime_reject_active_legacy_school"
    )
    session_function = sql[session_function_start:session_function_end]
    runtime_function = sql[runtime_function_start:runtime_function_end]

    assert "new.status is distinct from 'ended'" in session_function
    assert "new.module_id = 'school_english'" in session_function
    assert "new.task_type = 'school_english'" in session_function
    assert "from public.session_runtime runtime" in session_function
    assert "runtime.session_id = new.session_id" in session_function
    assert (
        "runtime.state_snapshot ->> 'module_id' = 'school_english'"
        in session_function
    )
    assert (
        "runtime.state_snapshot ->> 'task_type' = 'school_english'"
        in session_function
    )
    assert (
        "runtime.last_error ->> 'code' = 'legacy_school_module_retired'"
        in session_function
    )
    assert "before insert or update on public.sessions" in sql

    assert "new.status is distinct from 'ended'" in runtime_function
    assert "new.module_id = 'school_english'" in runtime_function
    assert "new.task_type = 'school_english'" in runtime_function
    assert (
        "new.state_snapshot ->> 'module_id' = 'school_english'"
        in runtime_function
    )
    assert (
        "new.state_snapshot ->> 'task_type' = 'school_english'"
        in runtime_function
    )
    assert (
        "new.state_snapshot ->> 'block_reason' = 'legacy_school_module_retired'"
        in runtime_function
    )
    assert (
        "new.last_error ->> 'code' = 'legacy_school_module_retired'"
        in runtime_function
    )
    assert "from public.sessions parent" in runtime_function
    assert "parent.session_id = new.session_id" in runtime_function
    assert "parent.module_id = 'school_english'" in runtime_function
    assert "parent.task_type = 'school_english'" in runtime_function
    assert "before insert or update on public.session_runtime" in sql

    first_terminalization = min(
        sql.index("update public.session_runtime"),
        sql.index("update public.sessions"),
    )
    assert (
        sql.index("create trigger sessions_reject_active_legacy_school")
        < first_terminalization
    )
    assert (
        sql.index("create trigger session_runtime_reject_active_legacy_school")
        < first_terminalization
    )


def test_final_schema_installs_idempotent_legacy_retirement_guards():
    sql = " ".join(SCHEMA.read_text().lower().split())

    for function_name in (
        "reject_active_legacy_school_session_row",
        "reject_active_legacy_school_runtime_row",
    ):
        assert f"create or replace function {function_name}()" in sql
    assert "drop trigger if exists sessions_reject_active_legacy_school" in sql
    assert (
        "create trigger sessions_reject_active_legacy_school before insert or update "
        "on sessions for each row execute function "
        "reject_active_legacy_school_session_row()"
    ) in sql
    assert "drop trigger if exists session_runtime_reject_active_legacy_school" in sql
    assert (
        "create trigger session_runtime_reject_active_legacy_school before insert or update "
        "on session_runtime for each row execute function "
        "reject_active_legacy_school_runtime_row()"
    ) in sql
    assert "new.status is distinct from 'ended'" in sql
    assert "legacy_school_module_retired" in sql
