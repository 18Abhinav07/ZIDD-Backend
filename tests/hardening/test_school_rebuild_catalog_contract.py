import asyncio
import copy
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.api import school_rebuild_routes
from tests.hardening.test_school_rebuild_phase_8_curriculum_teaching_contract import (
    AUTH,
    _seed_direct_curriculum_report_lineage,
    _seed_school_profile,
)


FORBIDDEN_LEARNER_KEYS = {
    "accepted_answers",
    "answer_key",
    "answer_keys",
    "answer_rule",
    "concept_slots",
    "evaluation_mode",
    "forbidden_phrases",
    "hidden_score",
    "model_answer",
    "model_answers",
    "pass_score",
    "preflight_rule",
    "rubric",
    "rubric_criteria",
    "rubrics",
    "scoring",
}


def _run(coro):
    return asyncio.run(coro)


def _unlock_target_curriculum(store, *, class_no: int = 3) -> dict[str, Any]:
    profile = _seed_school_profile(store, target_class_no=class_no)
    _seed_direct_curriculum_report_lineage(store, profile)
    report = _run(
        store.get_school_placement_report_by_id("test_user", "placement-report")
    )
    _run(
        store.upsert_school_placement_report(
            **{
                **report,
                "placement_status": "target_ready",
                "unlock_state": "target_unlocked",
            }
        )
    )
    placement_key = ("test_user", str(report["placement_session_id"]))
    store.school_sessions[placement_key]["status"] = "complete"
    return profile


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        assert FORBIDDEN_LEARNER_KEYS.isdisjoint(value)
        for child in value.values():
            _assert_no_forbidden_keys(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_forbidden_keys(child)


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key
            for child in value.values()
            for key in _walk_keys(child)
        }
    if isinstance(value, list):
        return {key for child in value for key in _walk_keys(child)}
    return set()


def _start(client: TestClient, chapter_id: str, client_start_id: str):
    return client.post(
        "/school/curriculum/start",
        headers=AUTH,
        json={
            "chapter_id": chapter_id,
            "client_start_id": client_start_id,
        },
    )


def test_catalog_lists_only_approved_live_subject_classes_in_order(store):
    _seed_school_profile(store, target_class_no=3)

    response = TestClient(app).get("/school/catalog", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == {
        "boards": [
            {
                "board_id": "cbse",
                "title": "CBSE",
                "description": "CBSE curriculum aligned with approved learning material.",
                "support_status": "available",
                "subjects": [
                    {
                        "subject_id": "english",
                        "title": "English",
                        "support_status": "available",
                        "classes": [
                            {
                                "class_no": class_no,
                                "title": f"Class {class_no}",
                                "support_status": "available",
                            }
                            for class_no in (2, 3, 4, 5)
                        ],
                    }
                ],
            },
            {
                "board_id": "ncert",
                "title": "NCERT",
                "description": "NCERT is used as a content source for the CBSE release.",
                "support_status": "unavailable",
                "unavailable_reason": "NCERT is a content source, not a school board.",
                "subjects": [
                    {
                        "subject_id": "english",
                        "title": "English",
                        "support_status": "unavailable",
                        "unavailable_reason": (
                            "Choose CBSE to use the available English release."
                        ),
                        "classes": [
                            {
                                "class_no": class_no,
                                "title": f"Class {class_no}",
                                "support_status": "unavailable",
                                "unavailable_reason": (
                                    "NCERT is not a selectable school board."
                                ),
                            }
                            for class_no in (2, 3, 4, 5)
                        ],
                    }
                ],
            },
        ],
        "active_board_id": "cbse",
        "active_subject_id": "english",
        "active_class_no": 3,
    }


def test_class_map_rejects_active_profile_mismatch(store):
    _seed_school_profile(store, target_class_no=3)

    response = TestClient(app).get(
        "/school/catalog/english/classes/4",
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "school_catalog_profile_mismatch"


def test_class_map_orders_chapters_and_exposes_progression_safe_summaries(store):
    _unlock_target_curriculum(store)
    client = TestClient(app)

    response = client.get("/school/catalog/english/classes/3", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "subject_id",
        "class_no",
        "book_title",
        "coach_avatar_id",
        "coach_palette_id",
        "active_chapter_id",
        "chapters",
        "recent_growth",
    }
    assert body["recent_growth"] == {
        "improving_count": 0,
        "strong_count": 0,
        "active_focus_count": 0,
    }
    assert body["subject_id"] == "english"
    assert body["class_no"] == 3
    assert body["book_title"] == "Santoor"
    assert body["coach_avatar_id"]
    assert body["coach_palette_id"] == body["coach_avatar_id"]
    assert "coach_seed" not in response.text
    assert body["active_chapter_id"] == "eng_c3_ch01"
    assert [chapter["chapter_no"] for chapter in body["chapters"]] == list(
        range(1, 13)
    )
    assert body["chapters"][0] == {
        "chapter_id": "eng_c3_ch01",
        "chapter_no": 1,
        "title": "Colours",
        "status": "ready",
        "completed_levels": 0,
        "total_levels": 5,
        "active_session_id": None,
    }
    assert {chapter["status"] for chapter in body["chapters"][1:]} == {"locked"}
    _assert_no_forbidden_keys(body)


def test_class_map_summarizes_real_school_growth_without_skill_ids(store):
    _unlock_target_curriculum(store)
    for skill_id, readiness in (
        ("reading.inference_reason", 0.72),
        ("writing.short_answer", 0.91),
        ("grammar.tense_usage", 0.35),
    ):
        _run(store.upsert_learner_skill_profile(
            user_id="test_user",
            domain="school",
            skill_id=skill_id,
            module_id="english",
            task_type="curriculum",
            readiness=readiness,
            mastery=0.0,
            confidence=0.8,
            attempts=3,
            strengths_json=[],
            gaps_json=[],
            evidence_json={},
            recommended_next_action="Continue focused practice.",
            source_summary="School evidence.",
        ))

    response = TestClient(app).get(
        "/school/catalog/english/classes/3",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["recent_growth"] == {
        "improving_count": 1,
        "strong_count": 1,
        "active_focus_count": 1,
    }
    assert "reading.inference_reason" not in response.text


def test_chapter_map_returns_ordered_learner_stages_without_hidden_keys(store):
    _unlock_target_curriculum(store)
    client = TestClient(app)

    response = client.get(
        "/school/catalog/english/classes/3/chapters/eng_c3_ch01",
        headers=AUTH,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subject_id"] == "english"
    assert body["class_no"] == 3
    assert body["chapter_id"] == "eng_c3_ch01"
    assert body["chapter_no"] == 1
    assert body["title"] == "Colours"
    assert body["book_title"] == "Santoor"
    assert body["coach_avatar_id"]
    assert body["coach_palette_id"] == body["coach_avatar_id"]
    assert "coach_seed" not in response.text
    assert body["status"] == "ready"
    assert body["active_session_id"] is None
    assert [level["learner_stage"] for level in body["levels"]] == [
        "Discover",
        "Practise Together",
        "Practise Together",
        "Try It Yourself",
        "Use It Somewhere New",
    ]
    assert [level["status"] for level in body["levels"]] == [
        "ready",
        "locked",
        "locked",
        "locked",
        "locked",
    ]
    assert body["chapter_check"] == {
        "title": "Chapter challenge",
        "status": "locked",
    }
    _assert_no_forbidden_keys(body)


def test_catalog_maps_take_start_authority_only_from_canonical_state(store, monkeypatch):
    _unlock_target_curriculum(store)

    async def non_starting_state(_request):
        return {
            "next_action": "view_report",
            "allowed_next_actions": ["view_report"],
        }

    monkeypatch.setattr(school_rebuild_routes, "school_state", non_starting_state)
    client = TestClient(app)

    class_map = client.get("/school/catalog/english/classes/3", headers=AUTH)
    chapter_map = client.get(
        "/school/catalog/english/classes/3/chapters/eng_c3_ch01",
        headers=AUTH,
    )

    assert class_map.status_code == 200
    assert chapter_map.status_code == 200
    assert class_map.json()["active_chapter_id"] is None
    assert class_map.json()["chapters"][0]["status"] == "locked"
    assert chapter_map.json()["status"] == "locked"
    forbidden_authority_keys = {
        "allowed_next_actions",
        "next_action",
        "next_action_url",
        "can_start",
        "start_url",
    }
    assert forbidden_authority_keys.isdisjoint(_walk_keys(class_map.json()))
    assert forbidden_authority_keys.isdisjoint(_walk_keys(chapter_map.json()))


def test_curriculum_landing_requires_canonical_state_authority(store, monkeypatch):
    _unlock_target_curriculum(store)

    async def non_starting_state(_request):
        return {
            "next_action": "view_report",
            "allowed_next_actions": ["view_report"],
        }

    monkeypatch.setattr(school_rebuild_routes, "school_state", non_starting_state)

    response = TestClient(app).get("/school/curriculum", headers=AUTH)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "curriculum_locked"


def test_explicit_start_rejects_a_progression_locked_chapter(store):
    _unlock_target_curriculum(store)

    response = _start(
        TestClient(app),
        "eng_c3_ch02",
        "locked-chapter-start",
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "curriculum_chapter_locked"


def test_explicit_start_resumes_active_chapter_and_tracks_level_progress(store):
    _unlock_target_curriculum(store)
    client = TestClient(app)
    started = _start(client, "eng_c3_ch01", "first-start")
    assert started.status_code == 200
    session_id = started.json()["session_id"]

    resumed = _start(client, "eng_c3_ch01", "resume-active-start")
    saved = _run(store.get_school_session("test_user", session_id))
    state = copy.deepcopy(saved["state_json"])
    state["levels"][0]["status"] = "complete"
    state["levels"][0]["current_step"] = "complete"
    state["levels"][1]["status"] = "in_progress"
    state["levels"][1]["current_step"] = "guided_check"
    state["current_level_index"] = 1
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="1",
            linked_session_id=saved.get("linked_session_id"),
            profile_version_id=saved["profile_version_id"],
            source_placement_report_id=saved["source_placement_report_id"],
            state_json=state,
        )
    )
    class_map = client.get("/school/catalog/english/classes/3", headers=AUTH)
    chapter_map = client.get(
        "/school/catalog/english/classes/3/chapters/eng_c3_ch01",
        headers=AUTH,
    )

    assert resumed.status_code == 200
    assert resumed.json()["session_id"] == session_id
    active_summary = class_map.json()["chapters"][0]
    assert active_summary["status"] == "active"
    assert active_summary["active_session_id"] == session_id
    assert active_summary["completed_levels"] == 1
    assert class_map.json()["active_chapter_id"] == "eng_c3_ch01"
    assert chapter_map.json()["status"] == "active"
    assert chapter_map.json()["active_session_id"] == session_id
    assert chapter_map.json()["levels"][0]["status"] == "complete"
    assert chapter_map.json()["levels"][1]["status"] == "active"


def test_catalog_expires_active_session_when_authored_content_version_changed(store):
    _unlock_target_curriculum(store)
    client = TestClient(app)
    started = _start(client, "eng_c3_ch01", "stale-content-start")
    assert started.status_code == 200
    session_id = started.json()["session_id"]
    row = store.school_sessions[("test_user", session_id)]
    row["state_json"]["chapter"]["content_version"] = "obsolete-content-version"

    class_map = client.get("/school/catalog/english/classes/3", headers=AUTH)

    assert class_map.status_code == 200
    assert class_map.json()["chapters"][0]["status"] == "ready"
    assert class_map.json()["chapters"][0]["active_session_id"] is None
    expired = store.school_sessions[("test_user", session_id)]
    assert expired["status"] == "expired"
    assert expired["state_json"]["phase"] == "content_refresh_required"


def test_expired_curriculum_session_is_not_returned_as_current(monkeypatch):
    class ExpiredCurriculumStore:
        async def get_active_school_session(self, *args, **kwargs):
            return None

        async def get_latest_school_session(self, *args, **kwargs):
            return {
                "session_id": "expired-curriculum",
                "status": "expired",
                "state_json": {"phase": "content_refresh_required"},
            }

    monkeypatch.setattr(
        school_rebuild_routes,
        "get_storage",
        lambda: ExpiredCurriculumStore(),
    )

    result = _run(
        school_rebuild_routes._latest_curriculum_for_profile(
            "test_user",
            {
                "subject_ids": ["english"],
                "target_class_no": 3,
                "profile_version_id": "profile-version",
            },
            "placement-report",
        )
    )

    assert result is None


def test_duplicate_client_start_id_replays_the_same_session_response(store):
    _unlock_target_curriculum(store)
    client = TestClient(app)

    first = _start(client, "eng_c3_ch01", "stable-catalog-start-id")
    duplicate = _start(client, "eng_c3_ch01", "stable-catalog-start-id")

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.json() == first.json()
    curriculum_sessions = [
        row
        for row in store.school_sessions.values()
        if row.get("flow_type") == "curriculum"
    ]
    assert len(curriculum_sessions) == 1
    start_request = store.start_requests[("test_user", "stable-catalog-start-id")]
    assert start_request["status"] == "completed"
    assert start_request["session_id"] == first.json()["session_id"]


def test_client_start_id_cannot_replay_across_placement_report_lineage(store, monkeypatch):
    _unlock_target_curriculum(store)
    original_report = _run(
        store.get_school_placement_report_by_id("test_user", "placement-report")
    )
    current_report = {"value": original_report}

    async def latest_report(_user_id, _public_profile):
        return dict(current_report["value"])

    monkeypatch.setattr(
        school_rebuild_routes,
        "_latest_placement_report_for_profile",
        latest_report,
    )
    client = TestClient(app)
    first = _start(client, "eng_c3_ch01", "lineage-bound-start")
    assert first.status_code == 200

    current_report["value"] = {
        **original_report,
        "report_id": "replacement-placement-report",
        "placement_session_id": "replacement-placement-session",
    }
    replay = _start(client, "eng_c3_ch01", "lineage-bound-start")

    assert replay.status_code == 409
    assert replay.json()["detail"]["code"] == (
        "client_start_id_reused_with_different_payload"
    )


def test_bodyless_curriculum_start_remains_backward_compatible(store):
    _unlock_target_curriculum(store)

    response = TestClient(app).post("/school/curriculum/start", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["chapter"]["chapter_id"] == "eng_c3_ch01"
    assert store.start_requests == {}


def test_catalog_projects_needs_support_from_the_active_chapter_state(store):
    _unlock_target_curriculum(store)
    client = TestClient(app)
    started = _start(client, "eng_c3_ch01", "needs-support-start").json()
    saved = _run(store.get_school_session("test_user", started["session_id"]))
    state = copy.deepcopy(saved["state_json"])
    state["phase"] = "needs_support"
    state["status"] = "active"
    _run(
        store.upsert_school_session(
            session_id=started["session_id"],
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="needs_support",
            linked_session_id=saved.get("linked_session_id"),
            profile_version_id=saved["profile_version_id"],
            source_placement_report_id=saved["source_placement_report_id"],
            state_json=state,
        )
    )

    class_map = client.get("/school/catalog/english/classes/3", headers=AUTH).json()
    chapter_map = client.get(
        "/school/catalog/english/classes/3/chapters/eng_c3_ch01",
        headers=AUTH,
    ).json()

    assert class_map["chapters"][0]["status"] == "needs_support"
    assert chapter_map["status"] == "needs_support"
    assert chapter_map["levels"][0]["status"] == "needs_support"
    assert chapter_map["chapter_check"]["status"] == "needs_support"
