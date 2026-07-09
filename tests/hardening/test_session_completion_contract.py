import asyncio
import time

from fastapi.testclient import TestClient

from app.main import app
from app.services import session_service as svc

AUTH = {"Authorization": "Bearer test_token"}
NODE = "comm_00_greetings"


def _run(coro):
    return asyncio.run(coro)


def test_session_routes_reject_stale_token_without_recreating_profile(store):
    client = TestClient(app)
    assert _run(store.get_profile("test_user")) is None

    progress = client.get("/session/progress/me?module_id=interview", headers=AUTH)
    start = client.post("/session/start", json={"competency_node": NODE}, headers=AUTH)
    placement = client.post(
        "/onboarding/placement",
        json={"module_id": "interview", "writing_sample": "", "self_report": "beginner"},
        headers=AUTH,
    )

    assert [progress.status_code, start.status_code, placement.status_code] == [401, 401, 401]
    assert _run(store.get_profile("test_user")) is None


def test_completed_node_requires_explicit_reattempt(monkeypatch, store):
    captured = {}

    async def _fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False):
        captured["reattempt"] = reattempt
        return "reattempt-session", {
            "session_id": "reattempt-session",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", _fake_start)
    _run(store.ensure_profile("test_user"))
    _run(store.set_demo_unlimited("test_user", True))
    _run(store.upsert_mastery("test_user", NODE, 0.8, 2, clean_pass=True, node_completed=True))

    client = TestClient(app)
    blocked = client.post(
        "/session/start",
        json={"competency_node": NODE, "client_start_id": "completed-blocked"},
        headers=AUTH,
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "completed_node"

    confirmed = client.post(
        "/session/start",
        json={
            "competency_node": NODE,
            "reattempt_confirmed": True,
            "client_start_id": "completed-confirmed",
        },
        headers=AUTH,
    )
    assert confirmed.status_code == 200
    assert captured["reattempt"] is True


def test_clean_pass_without_completion_does_not_block_session_start(monkeypatch, store):
    captured = {}

    async def _fake_start(user_id, node_id, learner_name="", test_mode=False, reattempt=False):
        captured["node_id"] = node_id
        captured["reattempt"] = reattempt
        return "active-session", {
            "session_id": "active-session",
            "user_id": user_id,
            "competency_node": node_id,
            "current_mastery": 0.0,
        }

    monkeypatch.setattr(svc, "start_session", _fake_start)
    _run(store.ensure_profile("test_user"))
    _run(store.set_demo_unlimited("test_user", True))
    _run(store.upsert_mastery("test_user", NODE, 0.42, 1, clean_pass=True, node_completed=False))

    client = TestClient(app)
    response = client.post(
        "/session/start",
        json={"competency_node": NODE, "client_start_id": "clean-pass-start"},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert captured["node_id"] == NODE
    assert captured["reattempt"] is False


def test_clean_pass_without_completion_does_not_render_mastered(store):
    _run(store.ensure_profile("test_user"))
    _run(store.upsert_mastery("test_user", NODE, 0.42, 1, clean_pass=True, node_completed=False))

    nodes = _run(svc.get_progression_map("test_user", "communication"))
    by_id = {node["node_id"]: node for node in nodes}

    assert by_id[NODE]["completed"] is False
    assert by_id[NODE]["status"] == "active"
    assert by_id[NODE]["display_mastery"] == 0.42


def test_school_lesson_progress_requires_node_completion(store):
    _run(store.ensure_profile("test_user"))
    _run(store.upsert_mastery("test_user", "c2_ch01_l1_new_words", 0.35, 1, clean_pass=True, node_completed=False))

    client = TestClient(app)
    response = client.get("/school/progress?class_no=2", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["lesson_progress"]["c2_ch01_l1_new_words"] == "in_progress"


def test_progression_keeps_completed_node_mastered_during_reattempt(store):
    _run(store.ensure_profile("test_user"))
    _run(store.upsert_mastery("test_user", NODE, 0.82, 2, clean_pass=True, node_completed=True))

    state = svc._new_state("test_user", "active-reattempt", NODE, "", task_type="comm_prep")
    state["reattempt"] = True
    svc.SessionStore["active-reattempt"] = state

    nodes = _run(svc.get_progression_map("test_user", "communication"))
    by_id = {node["node_id"]: node for node in nodes}

    assert by_id[NODE]["status"] == "mastered"
    assert by_id[NODE]["reattempt_session_id"] == "active-reattempt"


def test_career_progression_returns_registry_nodes_for_empty_history(store):
    _run(store.ensure_profile("test_user"))
    client = TestClient(app)

    gd = client.get("/session/progress/me?module_id=group_discussion", headers=AUTH)
    interview = client.get("/session/progress/me?module_id=interview", headers=AUTH)

    assert gd.status_code == 200
    assert interview.status_code == 200
    assert len(gd.json()) > 0
    assert len(interview.json()) > 0
    assert gd.json()[0]["status"] == "active"
    assert interview.json()[0]["status"] == "active"


def test_progression_unknown_module_returns_404(store):
    _run(store.ensure_profile("test_user"))
    client = TestClient(app)

    response = client.get("/session/progress/me?module_id=missing_module", headers=AUTH)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_module"


def test_progression_storage_failure_returns_503(monkeypatch, store):
    _run(store.ensure_profile("test_user"))

    async def _broken_progression(user_id: str):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(store, "get_progression", _broken_progression)
    client = TestClient(app)

    response = client.get("/session/progress/me?module_id=group_discussion", headers=AUTH)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "progression_unavailable"


def test_start_progression_storage_failure_returns_structured_503(monkeypatch, store):
    _run(store.ensure_profile("test_user"))

    async def _broken_progression(user_id: str):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(store, "get_progression", _broken_progression)
    client = TestClient(app)

    response = client.post(
        "/session/start",
        json={"competency_node": NODE, "client_start_id": "progression-failure-start"},
        headers=AUTH,
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "progression_unavailable"
    assert response.json()["detail"]["node_id"] == NODE


def test_cleanup_expires_stale_sessions_and_locks():
    state = svc._new_state("test_user", "stale-session", NODE, "", task_type="comm_prep")
    state["last_seen_at"] = time.time() - 10_000
    state["expires_at"] = time.time() - 1
    svc.SessionStore["stale-session"] = state
    svc._SESSION_LOCKS["stale-session"] = asyncio.Lock()

    expired = _run(svc.cleanup_sessions())

    assert expired == ["stale-session"]
    assert "stale-session" not in svc.SessionStore
    assert "stale-session" not in svc._SESSION_LOCKS
