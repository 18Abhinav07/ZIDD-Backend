import asyncio
import inspect
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.db import repo
from app.main import app
from app.services import school_rebuild_curriculum as curriculum_service
from app.services import school_rebuild_recap as recap_service
from app.services import school_rebuild_report as report_service
from app.services import school_rebuild_profile as profile_service
from app.services.school_rebuild_profile import SCHOOL_PROFILE_FIELDS
from app.services.school_rebuild_state import (
    school_state_for_profile,
    unauthenticated_school_state,
)
from tests.hardening.test_school_rebuild_linked_masterclass_contract import (
    _paused_parent,
)
from tests.hardening.test_school_rebuild_phase_3_report_recap_contract import (
    _seed_completed_placement_report,
)


AUTH = {"Authorization": "Bearer test_token"}
EXPECTED_COACH_IDS = (
    "stuttering_sam",
    "fluent_finn",
    "brave_bella",
    "quiet_quint",
    "tech_black",
    "casual_purple",
    "casual_male",
    "casual_female",
    "casual_blue",
)


def _run(coro):
    return asyncio.run(coro)


def _profile_payload(**overrides):
    return {
        "display_name": "Mira Sharma",
        "school_name": "Saraswati Public School",
        "board_id": "cbse",
        "target_class_no": 3,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "low",
        "learner_goal": "Read every chapter without guessing.",
        "parent_goal": "Explain answers using evidence from the text.",
        "prior_difficulty_signals": ["writing", "reading", "chapter_answers"],
        **overrides,
    }


def _activate(client: TestClient, payload=None, *, activation_request_id=None):
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            **(payload or _profile_payload()),
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    assert saved.status_code == 200, saved.text
    draft = saved.json()["draft"]
    request_body = {
        "profile_version_id": draft["profile_version_id"],
        "expected_revision": draft["draft_revision"],
        "request_id": activation_request_id or str(uuid4()),
    }
    completed = client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json=request_body,
    )
    return completed, draft, request_body


def _seed_user(store):
    _run(
        store.ensure_profile(
            "test_user",
            name="Mira Sharma",
            email="mira@example.com",
        )
    )


def test_canonical_coach_registry_matches_frontend_ids_and_uses_crypto_choice():
    assert profile_service.CANONICAL_SCHOOL_COACH_IDS == EXPECTED_COACH_IDS
    source = inspect.getsource(profile_service.choose_school_coach_identity)
    assert "secrets.choice" in source
    assert "random.choice" not in source


def test_catalog_is_board_subject_class_authority_and_marks_ncert_unavailable(store):
    _seed_user(store)

    response = TestClient(app).get("/school/catalog", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["boards"] == [
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
    ]
    assert body["active_board_id"] is None
    assert body["active_subject_id"] is None
    assert body["active_class_no"] is None


def test_activation_round_trips_every_field_and_selects_profile_coach_once(
    store,
    monkeypatch,
):
    _seed_user(store)
    choices = []

    def choose(values):
        choices.append(tuple(values))
        return "brave_bella"

    monkeypatch.setattr(profile_service.secrets, "choice", choose)
    client = TestClient(app)
    payload = _profile_payload()
    completed, _draft, request_body = _activate(
        client,
        payload,
        activation_request_id=str(uuid4()),
    )

    assert completed.status_code == 200, completed.text
    profile = completed.json()["profile"]
    assert {field: profile[field] for field in SCHOOL_PROFILE_FIELDS} == payload
    assert profile["coach_avatar_id"] == "brave_bella"
    assert profile["coach_palette_id"] == "brave_bella"

    replay = client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json=request_body,
    )
    reloaded = client.get("/school/onboarding", headers=AUTH)
    state = client.get("/school/state", headers=AUTH)

    assert replay.status_code == 200
    assert replay.json()["profile"] == profile
    assert reloaded.json()["active_profile"] == profile
    assert state.json()["coach_avatar_id"] == "brave_bella"
    assert state.json()["coach_palette_id"] == "brave_bella"
    assert len(choices) == 1
    persisted = _run(store.get_active_school_profile_version("test_user"))
    assert persisted["coach_avatar_id"] == "brave_bella"
    assert persisted["coach_palette_id"] == "brave_bella"


def test_activation_and_placement_reject_unsupported_legacy_ncert_selection(store):
    _seed_user(store)
    client = TestClient(app)

    rejected, draft, _request = _activate(
        client,
        _profile_payload(board_id="ncert"),
    )
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "school_catalog_selection_unavailable"
    assert _run(store.get_active_school_profile_version("test_user")) is None
    with pytest.raises(ValueError, match="school_catalog_selection_unavailable"):
        _run(
            store.activate_school_profile_draft(
                user_id="test_user",
                profile_version_id=draft["profile_version_id"],
                expected_revision=draft["draft_revision"],
                request_id=str(uuid4()),
                payload_hash="unsupported-direct-activation",
            )
        )

    legacy = store.school_profile_versions[("test_user", draft["profile_version_id"])]
    legacy.update(
        {
            "status": "active",
            "activated_at": 1.0,
            "coach_avatar_id": "quiet_quint",
            "coach_palette_id": "quiet_quint",
        }
    )
    state = client.get("/school/state", headers=AUTH)
    placement = client.post("/school/placement/start", headers=AUTH)

    assert state.status_code == 200
    assert state.json()["next_action"] == "edit_profile"
    assert state.json()["allowed_next_actions"] == ["edit_profile"]
    assert state.json()["blocked_reason"] == "unsupported_school_catalog_selection"
    assert placement.status_code == 409
    assert placement.json()["detail"]["code"] == "school_catalog_selection_unavailable"


def test_every_state_shape_has_nullable_or_persisted_coach_identity():
    unauthenticated = unauthenticated_school_state()
    missing = school_state_for_profile(learner_profile={}, school_profile=None)
    assert unauthenticated["coach_avatar_id"] is None
    assert unauthenticated["coach_palette_id"] is None
    assert missing["coach_avatar_id"] is None
    assert missing["coach_palette_id"] is None

    profile = {
        **_profile_payload(),
        "profile_version_id": "profile-v1",
        "coach_avatar_id": "fluent_finn",
        "coach_palette_id": "fluent_finn",
    }
    placement = {"session_id": "placement-v1", "status": "active", "state_json": {}}
    report = {
        "report_id": "report-v1",
        "placement_session_id": "placement-v1",
        "profile_version_id": "profile-v1",
        "placement_status": "target_ready",
        "unlock_state": "target_unlocked",
        "evaluated_class_no": 3,
    }
    active_flow_cases = [
        {},
        {"placement_session": placement},
        {
            "placement_session": {**placement, "status": "complete"},
            "placement_report": report,
        },
        {
            "placement_session": {**placement, "status": "complete"},
            "placement_report": {**report, "placement_status": "below_target", "unlock_state": "recap_required"},
            "active_recap_session": {
                "session_id": "recap-v1",
                "status": "active",
                "state_json": {"status": "active", "active_learning_class_no": 2},
            },
        },
        {
            "placement_session": {**placement, "status": "complete"},
            "placement_report": report,
            "active_curriculum_session": {
                "session_id": "curriculum-v1",
                "status": "active",
                "state_json": {
                    "status": "active",
                    "phase": "learning",
                    "chapter": {"chapter_id": "eng_c3_ch01", "title": "Colours"},
                    "levels": [],
                },
            },
        },
        {
            "placement_session": {**placement, "status": "complete"},
            "placement_report": report,
            "active_masterclass_session": {
                "session_id": "masterclass-v1",
                "flow_type": "masterclass",
                "status": "active",
                "state_json": {"status": "active"},
            },
        },
        {
            "placement_session": {**placement, "status": "complete"},
            "placement_report": report,
            "active_support_session": {
                "session_id": "support-v1",
                "flow_type": "support",
                "status": "active",
                "state_json": {
                    "status": "active",
                    "coach_avatar_id": "casual_female",
                    "coach_palette_id": "casual_female",
                },
            },
        },
    ]
    for case in active_flow_cases:
        state = school_state_for_profile(
            learner_profile={"name": "Mira"},
            school_profile=profile,
            **case,
        )
        expected_coach = (
            "casual_female" if state["active_flow"] == "support" else "fluent_finn"
        )
        assert state["coach_avatar_id"] == expected_coach
        assert state["coach_palette_id"] == expected_coach
        if state["allowed_next_actions"]:
            assert state["next_action"] in state["allowed_next_actions"]
        else:
            assert state["next_action"] is None


def test_paused_curriculum_exposes_exact_masterclass_start_action():
    profile = {
        **_profile_payload(),
        "profile_version_id": "profile-v1",
        "coach_avatar_id": "tech_black",
        "coach_palette_id": "tech_black",
    }
    state = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile=profile,
        placement_session={
            "session_id": "placement-v1",
            "status": "complete",
            "state_json": {},
        },
        placement_report={
            "report_id": "report-v1",
            "placement_status": "target_ready",
            "unlock_state": "target_unlocked",
            "evaluated_class_no": 3,
        },
        active_curriculum_session={
            "session_id": "curriculum-v1",
            "status": "paused_for_masterclass",
            "state_json": {
                "status": "paused_for_masterclass",
                "phase": "paused_for_masterclass",
                "chapter": {"chapter_id": "eng_c3_ch01", "title": "Colours"},
                "levels": [],
                "active_interrupt": {"interrupt_id": "level-1:masterclass:1"},
            },
        },
    )

    assert state["active_flow"] == "masterclass"
    assert state["next_action"] == "start_masterclass"
    assert state["allowed_next_actions"] == ["start_masterclass"]
    assert state["next_action_url"] == "/school/session/curriculum-v1"


def test_malformed_report_transition_recovers_without_unlocking():
    state = school_state_for_profile(
        learner_profile={"name": "Mira"},
        school_profile={
            **_profile_payload(),
            "profile_version_id": "profile-v1",
            "coach_avatar_id": "quiet_quint",
            "coach_palette_id": "quiet_quint",
        },
        placement_session={
            "session_id": "placement-v1",
            "status": "complete",
            "state_json": {},
        },
        placement_report={
            "report_id": "report-v1",
            "placement_status": "target_ready",
        },
    )

    assert state["status"] == "recoverable_error"
    assert state["next_action"] == "retry"
    assert state["allowed_next_actions"] == ["retry"]
    assert state["unlock_state"] == "locked"
    assert state["blocked_reason"] == "inconsistent_school_state"


def test_placement_recap_and_curriculum_snapshot_profile_coach_identity(
    store,
    monkeypatch,
):
    async def evaluate(**kwargs):
        activity = kwargs["activity"]
        answer = kwargs["answer"]
        return {
            "schema_version": "school-v3-rubric-1",
            "item_id": activity["activity_id"],
            "skill_ids": list(activity["skill_ids"]),
            "score": 0.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": ["placement_gap"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Evidence recorded.",
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    identity = {
        "coach_avatar_id": profile["coach_avatar_id"],
        "coach_palette_id": profile["coach_palette_id"],
    }

    placement_response = client.post("/school/placement/start", headers=AUTH)
    assert placement_response.status_code == 200
    assert {key: placement_response.json()[key] for key in identity} == identity
    placement_row = _run(
        store.get_school_session("test_user", placement_response.json()["session_id"])
    )
    assert {key: placement_row["state_json"][key] for key in identity} == identity
    item = placement_response.json()["next_item"]
    answered = client.post(
        f"/school/placement/{placement_row['session_id']}/answer",
        headers=AUTH,
        json={"item_id": item["item_id"], "answer": "wrong"},
    )
    assert answered.status_code == 200, answered.text
    assert {key: answered.json()[key] for key in identity} == identity
    placement_row = _run(
        store.get_school_session("test_user", placement_row["session_id"])
    )
    assert {key: placement_row["state_json"][key] for key in identity} == identity

    _run(store.upsert_school_session(**{**placement_row, "status": "complete"}))
    report_row = _run(
        store.upsert_school_placement_report(
            report_id=str(uuid4()),
            user_id="test_user",
            profile_version_id=profile["profile_version_id"],
            placement_session_id=placement_row["session_id"],
            placement_status="below_target",
            subject_id="english",
            target_class_no=3,
            evaluated_class_no=2,
            active_learning_class_no=2,
            unlock_state="recap_required",
            blocking_skills=[{"skill_id": "reading.sentence_comprehension"}],
            watchlist_skills=[],
            evidence_summary={"total_attempts": 8},
            recommended_recap_modules=[
                {
                    "module_id": "reading.sentence_comprehension",
                    "skill_id": "reading.sentence_comprehension",
                    "placement_track_id": "english.c3.sentence_detail",
                    "primary_skill_id": "reading.sentence_comprehension",
                    "focus": "understand a simple sentence",
                    "source_class_no": 2,
                    "target_class_no": 3,
                }
            ],
            learner_summary="Placement summary.",
            parent_summary="Parent placement summary.",
            allowed_next_actions=["start_recap"],
        )
    )
    public_report = client.get("/school/placement/report", headers=AUTH)
    direct_report = report_service.public_placement_report(
        report_row,
        coach_source=placement_row["state_json"],
    )
    assert public_report.status_code == 200, public_report.text
    assert {key: public_report.json()[key] for key in identity} == identity
    assert {key: direct_report[key] for key in identity} == identity
    assert "allowed_next_actions" not in public_report.json()
    assert "allowed_next_actions" not in direct_report
    assert "coach_seed" not in public_report.text

    recap_response = client.post("/school/recap/start", headers=AUTH)
    assert recap_response.status_code == 200, recap_response.text
    recap_row = _run(
        store.get_school_session("test_user", recap_response.json()["session_id"])
    )
    assert {key: recap_response.json()[key] for key in identity} == identity
    assert {key: recap_row["state_json"][key] for key in identity} == identity
    direct_recap = recap_service.public_recap_response(recap_row)
    assert {key: direct_recap[key] for key in identity} == identity
    assert "coach_seed" not in recap_response.text


def test_curriculum_and_linked_masterclass_persist_identity_without_reselection(
    store,
    monkeypatch,
):
    _seed_user(store)
    picks = iter(["stuttering_sam", "casual_blue"])
    pick_count = 0

    def choose(_values):
        nonlocal pick_count
        pick_count += 1
        return next(picks)

    monkeypatch.setattr(profile_service.secrets, "choice", choose)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    _placement, report = _seed_completed_placement_report(
        store,
        client,
        "target_ready",
    )

    curriculum_response = client.post(
        "/school/curriculum/start",
        headers=AUTH,
        json={"chapter_id": "eng_c3_ch01", "client_start_id": str(uuid4())},
    )
    assert curriculum_response.status_code == 200, curriculum_response.text
    curriculum_row = _run(
        store.get_school_session("test_user", curriculum_response.json()["session_id"])
    )
    assert curriculum_row["source_placement_report_id"] == report["report_id"]
    assert curriculum_row["state_json"]["coach_avatar_id"] == profile["coach_avatar_id"]
    assert curriculum_response.json()["coach_avatar_id"] == profile["coach_avatar_id"]
    assert "coach_seed" not in curriculum_response.text

    paused = _paused_parent(monkeypatch)
    paused.update(
        {
            "profile_version_id": profile["profile_version_id"],
            "coach_avatar_id": profile["coach_avatar_id"],
            "coach_palette_id": profile["coach_palette_id"],
        }
    )
    _run(
        store.upsert_school_session(
            **{
                **curriculum_row,
                "status": "paused_for_masterclass",
                "state_json": paused,
            }
        )
    )
    first = client.post(
        f"/school/curriculum/{curriculum_row['session_id']}/masterclass/start",
        headers=AUTH,
    )
    second = client.post(
        f"/school/curriculum/{curriculum_row['session_id']}/masterclass/start",
        headers=AUTH,
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["session_id"] == second.json()["session_id"]
    assert first.json()["coach_avatar_id"] == "casual_blue"
    assert first.json()["coach_palette_id"] == "casual_blue"
    assert second.json()["coach_avatar_id"] == "casual_blue"
    reloaded = client.get(
        f"/school/masterclass/{first.json()['session_id']}",
        headers=AUTH,
    )
    assert reloaded.status_code == 200
    assert reloaded.json()["coach_avatar_id"] == "casual_blue"
    assert reloaded.json()["coach_palette_id"] == "casual_blue"
    child = _run(store.get_school_session("test_user", first.json()["session_id"]))
    assert child["state_json"]["coach_avatar_id"] == "casual_blue"
    assert child["state_json"]["coach_palette_id"] == "casual_blue"
    assert pick_count == 2


def test_linked_support_creation_selects_and_persists_one_coach(store, monkeypatch):
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    parent_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=None,
            state_json={
                "profile_version_id": profile["profile_version_id"],
                "coach_avatar_id": profile["coach_avatar_id"],
                "coach_palette_id": profile["coach_palette_id"],
            },
        )
    )
    choices = []

    def choose(_values):
        choices.append("casual_female")
        return "casual_female"

    monkeypatch.setattr(profile_service.secrets, "choice", choose)
    create = {
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "support",
        "subject_id": "english",
        "class_no": 3,
        "status": "active",
        "current_stage": "focused_support",
        "linked_session_id": parent_id,
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": None,
        "state_json": {"status": "active"},
    }
    first = _run(
        school_rebuild_routes._get_or_create_school_session(
            store,
            session_id=str(uuid4()),
            **create,
        )
    )
    replay = _run(
        school_rebuild_routes._get_or_create_school_session(
            store,
            session_id=str(uuid4()),
            **create,
        )
    )

    assert first["session_id"] == replay["session_id"]
    assert first["state_json"]["coach_avatar_id"] == "casual_female"
    assert first["state_json"]["coach_palette_id"] == "casual_female"
    assert replay["state_json"]["coach_avatar_id"] == "casual_female"
    assert choices == ["casual_female"]


def test_linked_support_route_is_owned_and_returns_persisted_plan_contract(store):
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    _placement, report = _seed_completed_placement_report(
        store,
        client,
        "target_ready",
    )
    parent_id = str(uuid4())
    support_id = str(uuid4())
    report_id = report["report_id"]
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="2",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=report_id,
            state_json={"status": "active"},
        )
    )
    history = [
        {
            "event": "masterclass_abandoned",
            "source_session_id": "masterclass-v2",
        }
    ]
    cap = {"used": 2, "limit": 2, "remaining": 0}
    _run(
        store.upsert_school_session(
            session_id=support_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="support",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_support",
            linked_session_id=parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=report_id,
            state_json={
                "status": "active",
                "reason": "masterclass_cap_exceeded",
                "focus": "Use details from the passage to explain an answer.",
                "cap": cap,
                "history": history,
                "coach_avatar_id": "casual_male",
                "coach_palette_id": "casual_male",
            },
        )
    )

    response = client.get(f"/school/support/{support_id}", headers=AUTH)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "session_id": support_id,
        "flow_type": "support",
        "status": "active",
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": report_id,
        "parent_session_id": parent_id,
        "parent_flow_type": "curriculum",
        "subject_id": "english",
        "target_class_no": 3,
        "coach_avatar_id": "casual_male",
        "coach_palette_id": "casual_male",
        "reason": "masterclass_cap_exceeded",
        "focus": "Use details from the passage to explain an answer.",
        "cap": cap,
        "history": history,
    }
    parent_response = client.get(f"/school/support/{parent_id}", headers=AUTH)
    assert parent_response.status_code == 404
    assert parent_response.json()["detail"]["code"] == "support_session_not_found"


def test_curriculum_support_state_url_resolves_parent_backed_plan(store):
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    _placement, report = _seed_completed_placement_report(
        store,
        client,
        "target_ready",
    )
    parent_id = str(uuid4())
    cap = {"used": 2, "limit": 2, "remaining": 0}
    history = [
        {
            "event": "chapter_check_failed",
            "source_session_id": parent_id,
        }
    ]
    support_required = {
        "reason": "chapter_check_attempts_exhausted",
        "focus": "Explain an answer with evidence from the passage.",
        "cap": cap,
        "history": history,
    }
    parent_state = curriculum_service.new_curriculum_state(
        school_profile=profile,
        placement_report=report,
        recap_session=None,
    )
    parent_state.update(
        {
            "status": "active",
            "phase": "needs_support",
            "support_required": support_required,
            "coach_avatar_id": profile["coach_avatar_id"],
            "coach_palette_id": profile["coach_palette_id"],
        }
    )
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="chapter_check",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=report["report_id"],
            state_json=parent_state,
        )
    )

    state_response = client.get("/school/state", headers=AUTH)
    assert state_response.status_code == 200, state_response.text
    state = state_response.json()
    assert state["next_action_url"] == f"/school/support/{parent_id}"

    plan_response = client.get(state["next_action_url"], headers=AUTH)
    assert plan_response.status_code == 200, plan_response.text
    assert plan_response.json() == {
        "session_id": parent_id,
        "flow_type": "support",
        "status": "needs_support",
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": report["report_id"],
        "parent_session_id": parent_id,
        "parent_flow_type": "curriculum",
        "subject_id": "english",
        "target_class_no": 3,
        "coach_avatar_id": profile["coach_avatar_id"],
        "coach_palette_id": profile["coach_palette_id"],
        "reason": support_required["reason"],
        "focus": support_required["focus"],
        "cap": cap,
        "history": history,
    }


def test_recap_support_state_url_resolves_parent_backed_plan(store):
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    _placement, report = _seed_completed_placement_report(
        store,
        client,
        "below_target",
    )
    parent_id = str(uuid4())
    cap = {"used": 3, "limit": 3, "remaining": 0}
    history = [
        {
            "event": "recap_revision_exhausted",
            "source_session_id": parent_id,
        }
    ]
    support_required = {
        "reason": "recap_support_cap_exceeded",
        "focus": "Find the main idea supported by the details.",
        "cap": cap,
        "history": history,
    }
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="recap",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="support_plan",
            linked_session_id=report["placement_session_id"],
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=report["report_id"],
            state_json={
                "status": "capped_support",
                "active_learning_class_no": 2,
                "support_required": support_required,
                "coach_avatar_id": profile["coach_avatar_id"],
                "coach_palette_id": profile["coach_palette_id"],
            },
        )
    )

    state_response = client.get("/school/state", headers=AUTH)
    assert state_response.status_code == 200, state_response.text
    state = state_response.json()
    assert state["next_action_url"] == f"/school/support/{parent_id}"

    plan_response = client.get(state["next_action_url"], headers=AUTH)
    assert plan_response.status_code == 200, plan_response.text
    assert plan_response.json() == {
        "session_id": parent_id,
        "flow_type": "support",
        "status": "capped_support",
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": report["report_id"],
        "parent_session_id": parent_id,
        "parent_flow_type": "recap",
        "subject_id": "english",
        "target_class_no": 3,
        "coach_avatar_id": profile["coach_avatar_id"],
        "coach_palette_id": profile["coach_palette_id"],
        "reason": support_required["reason"],
        "focus": support_required["focus"],
        "cap": cap,
        "history": history,
    }


def test_state_and_class_map_use_one_school_snapshot_authority(store, monkeypatch):
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    _placement, report = _seed_completed_placement_report(
        store,
        client,
        "target_ready",
    )

    assert hasattr(store, "get_school_state_snapshot")
    store.school_state_snapshot_calls = 0

    async def legacy_read_forbidden(*_args, **_kwargs):
        raise AssertionError("canonical School reads must use the state snapshot")

    for method_name in (
        "get_profile",
        "get_active_school_profile_version",
        "get_active_school_session",
        "get_latest_school_session",
        "get_school_placement_report",
        "get_latest_compatible_school_placement_report",
        "get_school_sessions_linked_to",
        "get_learning_graph",
    ):
        monkeypatch.setattr(store, method_name, legacy_read_forbidden)

    state_response = client.get("/school/state", headers=AUTH)
    assert state_response.status_code == 200, state_response.text
    assert state_response.json()["next_action"] == "start_curriculum"
    assert store.school_state_snapshot_calls == 1

    class_response = client.get(
        "/school/catalog/english/classes/3",
        headers=AUTH,
    )
    assert class_response.status_code == 200, class_response.text
    assert class_response.json()["class_no"] == 3
    assert class_response.json()["coach_avatar_id"] == profile["coach_avatar_id"]
    assert class_response.json()["active_chapter_id"] == "eng_c3_ch01"
    assert report["unlock_state"] == "target_unlocked"
    assert store.school_state_snapshot_calls == 2


def test_support_route_rejects_unauthorized_owner_and_broken_parent_lineage(store):
    _seed_user(store)
    client = TestClient(app)
    completed, _draft, _request = _activate(client)
    assert completed.status_code == 200
    profile = completed.json()["profile"]
    _placement, report = _seed_completed_placement_report(
        store,
        client,
        "target_ready",
    )
    foreign_profile = dict(
        store.school_profile_versions[
            ("test_user", profile["profile_version_id"])
        ]
    )
    foreign_profile["user_id"] = "another_user"
    store.school_profile_versions[
        ("another_user", profile["profile_version_id"])
    ] = foreign_profile
    foreign_parent_id = str(uuid4())
    foreign_report_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=foreign_parent_id,
            user_id="another_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="2",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=foreign_report_id,
            state_json={"status": "active"},
        )
    )
    foreign_support_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=foreign_support_id,
            user_id="another_user",
            api_version="rebuild",
            flow_type="support",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_support",
            linked_session_id=foreign_parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=foreign_report_id,
            state_json={"status": "active"},
        )
    )
    broken_parent_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=broken_parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="2",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="parent-report",
            state_json={"status": "active"},
        )
    )
    broken_support_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=broken_support_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="support",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_support",
            linked_session_id=broken_parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id=report["report_id"],
            state_json={"status": "active"},
        )
    )

    unauthenticated = client.get(
        f"/school/support/{broken_support_id}",
        headers={"Authorization": "Bearer invalid"},
    )
    foreign = client.get(f"/school/support/{foreign_support_id}", headers=AUTH)
    broken = client.get(f"/school/support/{broken_support_id}", headers=AUTH)

    assert unauthenticated.status_code == 401
    assert foreign.status_code == 404
    assert foreign.json()["detail"]["code"] == "support_session_not_found"
    assert broken.status_code == 409
    assert broken.json()["detail"]["code"] == "school_support_lineage_invalid"


def test_repository_activation_assigns_coach_in_the_active_profile_update_transaction():
    source = inspect.getsource(repo.activate_school_profile_draft)
    update = source.index("SET status = 'active'")
    commit = source.index("await session.commit()", update)
    assert "coach_avatar_id" in source[update:commit]
    assert "coach_palette_id" in source[update:commit]
