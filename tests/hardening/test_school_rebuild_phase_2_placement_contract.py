import asyncio
import inspect
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_rebuild_placement_bank import PlacementBand, placement_tracks_for
from app.db import repo as db_repo
from app.main import app
from app.services import school_rebuild_placement as placement
from app.services import school_rebuild_state as school_state_service
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION

AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def _profile_payload(
    *,
    target_class_no: int = 3,
    prior_difficulty_signals: list[str] | None = None,
) -> dict:
    return {
        "display_name": "Open Assets Learner",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": target_class_no,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": "I want to understand Class 3 English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": prior_difficulty_signals or ["reading", "vocabulary"],
    }


def _seed_school_profile(store, *, target_class_no: int = 3, signals: list[str] | None = None) -> None:
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            **_profile_payload(
                target_class_no=target_class_no,
                prior_difficulty_signals=signals,
            ),
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    assert saved.status_code == 200
    draft = saved.json()["draft"]
    response = client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
            "request_id": str(uuid4()),
        },
    )
    assert response.status_code == 200


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {"answer_key", "accepted_answers", "model_answer", "rubric", "threshold"}
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def _stub_failing_open_placement_evaluator(monkeypatch) -> None:
    async def evaluate(**kwargs):
        activity = kwargs["activity"]
        answer = kwargs["answer"]
        return {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
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
                    "evidence_quote": answer.strip() or "(empty answer)",
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": ["placement_gap"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "This answer does not yet meet the check.",
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )


def _stub_passing_open_placement_evaluator(monkeypatch) -> None:
    async def evaluate(**kwargs):
        activity = kwargs["activity"]
        answer = kwargs["answer"]
        inference, separator, clue = answer.partition(" because ")

        def evidence_quote(criterion_id: str) -> str:
            if separator and criterion_id == "plausible_inference":
                return inference.strip()
            if separator and criterion_id == "relevant_text_clue":
                return clue.strip()
            return answer.strip()

        return {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": list(activity["skill_ids"]),
            "score": 1.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": evidence_quote(criterion["id"]),
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "This answer meets the placement check.",
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )


def _strong_open_placement_answer(item) -> str:
    answers = {
        "spv_c05_t03_v01": (
            "It probably rained while Ira was outside because her wet shoes "
            "and dripping umbrella are clear clues."
        ),
        "spv_c05_t03_v02": (
            "The puppy probably ate the food because only crumbs remained and "
            "it was licking its lips."
        ),
        "spv_c05_t03_v03": (
            "The residents are probably away because newspapers collected and "
            "no lights appeared for several evenings."
        ),
        "spv_c05_t03_v04": (
            "The team became quiet because it needed one run and the bowler was "
            "about to begin."
        ),
        "spv_c05_t03_v05": (
            "The plants most likely lacked water because the soil was dry and "
            "the watering can had been empty for days."
        ),
        "spv_c05_t08_v01": (
            "After the storm blocked the lane with broken branches, residents "
            "cut them up and reopened a path."
        ),
        "spv_c05_t08_v02": (
            "The school installed solar panels after comparing bills, then used "
            "the savings to buy library books."
        ),
        "spv_c05_t08_v03": (
            "The children called rescuers for an injured bird and kept the area "
            "quiet until help arrived."
        ),
        "spv_c05_t08_v04": (
            "Students investigated unsafe bus stops and submitted three practical "
            "improvements to the transport office."
        ),
        "spv_c05_t08_v05": (
            "Testing found harmful bacteria in one clear-looking water sample, "
            "so that sample needed treatment."
        ),
    }
    return answers[item.item_id]


def _pure_profile(*, target_class_no: int = 3) -> dict[str, Any]:
    return {
        "profile_version_id": "profile-v1",
        "target_class_no": target_class_no,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "prior_difficulty_signals": [],
    }


def _apply_score(
    envelope: placement.PlacementEnvelope,
    score: float,
    *,
    confidence: float = 1.0,
    elapsed_seconds: int = 0,
) -> placement.PlacementEnvelope:
    item = placement.next_item(envelope)
    assert item is not None
    return placement.apply_evaluated_attempt(
        envelope,
        item,
        evaluator_score=score,
        evaluator_confidence=confidence,
        elapsed_seconds_delta=elapsed_seconds,
    )


def _synthetic_bands(track, source_class_nos: tuple[int, ...]):
    targeted_template = next(
        item
        for band in track.bands
        for item in band.variants
        if item.stage == "targeted_diagnostic"
    )
    confirmatory_template = next(
        item
        for band in track.bands
        for item in band.variants
        if item.stage == "confirmatory"
    )
    return tuple(
        PlacementBand(
            source_class_no=source_class_no,
            variants=(
                replace(
                    targeted_template,
                    item_id=f"{track.track_id}.targeted.{source_class_no}",
                    source_class_no=source_class_no,
                ),
                replace(
                    confirmatory_template,
                    item_id=f"{track.track_id}.confirm.{source_class_no}",
                    source_class_no=source_class_no,
                ),
            ),
        )
        for source_class_no in source_class_nos
    )


def test_school_placement_start_requires_active_school_profile(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)

    response = client.post("/school/placement/start", headers=AUTH)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "school_profile_required"


def test_school_placement_start_uses_saved_profile_and_authored_snapshot_item(store):
    _seed_school_profile(store, signals=["reading", "vocabulary"])
    client = TestClient(app)

    response = client.post("/school/placement/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["profile_version_id"]
    assert body["subject_id"] == "english"
    assert body["target_class_no"] == 3
    assert body["preferred_teaching_language"] == "hi_en"
    assert body["stage"] == "snapshot"
    assert body["status"] == "in_progress"
    assert body["next_item"]["stage"] == "snapshot"
    assert body["next_item"]["source_class_no"] in (2, 3)
    assert body["next_item"]["learner_skill_label"]
    assert body["next_item"]["prompt"]
    assert body["next_item"].get("passage")
    _assert_no_hidden_keys(body)


def test_school_placement_start_replays_existing_accepted_session(store):
    _seed_school_profile(store)
    client = TestClient(app)

    first = client.post("/school/placement/start", headers=AUTH)
    replay = client.post("/school/placement/start", headers=AUTH)

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    placement_rows = [
        row
        for row in store.school_sessions.values()
        if row.get("user_id") == "test_user"
        and row.get("api_version") == "rebuild"
        and row.get("flow_type") == "placement"
    ]
    assert len(placement_rows) == 1


def test_school_placement_start_delegates_winner_selection_to_atomic_storage():
    source = inspect.getsource(school_rebuild_routes.start_school_placement)

    assert "get_or_create_active_school_placement_session" in source
    assert "get_active_school_session" not in source


def test_school_placement_start_retries_on_concurrent_material_activation(
    store,
    monkeypatch,
):
    _seed_school_profile(store)
    client = TestClient(app)
    old_profile = _run(store.get_active_school_profile_version("test_user"))
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            "preferred_teaching_language": "en",
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    assert saved.status_code == 200
    draft = saved.json()["draft"]
    original_start = store.get_or_create_active_school_placement_session
    raced = False

    async def activate_before_first_locked_start(**kwargs):
        nonlocal raced
        if not raced:
            raced = True
            await store.activate_school_profile_draft(
                user_id="test_user",
                profile_version_id=draft["profile_version_id"],
                expected_revision=draft["draft_revision"],
                request_id=str(uuid4()),
                payload_hash="concurrent-material-activation",
            )
        return await original_start(**kwargs)

    monkeypatch.setattr(
        store,
        "get_or_create_active_school_placement_session",
        activate_before_first_locked_start,
    )

    response = client.post("/school/placement/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    active_profile = _run(store.get_active_school_profile_version("test_user"))
    saved_session = _run(store.get_school_session("test_user", body["session_id"]))
    assert active_profile["profile_version_id"] == draft["profile_version_id"]
    assert active_profile["profile_version_id"] != old_profile["profile_version_id"]
    assert body["profile_version_id"] == active_profile["profile_version_id"]
    assert saved_session["profile_version_id"] == active_profile["profile_version_id"]
    assert saved_session["status"] == "active"


@pytest.mark.parametrize(
    ("next_action", "allowed_next_actions"),
    [
        ("view_placement_report", ["view_placement_report", "start_placement"]),
        ("start_recap", ["start_recap"]),
        ("start_curriculum", ["start_curriculum"]),
        ("resume_curriculum", ["resume_curriculum"]),
    ],
)
def test_school_placement_start_requires_canonical_start_action(
    store,
    monkeypatch,
    next_action,
    allowed_next_actions,
):
    _seed_school_profile(store)

    async def canonical_state(_request):
        return {
            "next_action": next_action,
            "allowed_next_actions": allowed_next_actions,
        }

    monkeypatch.setattr(school_rebuild_routes, "school_state", canonical_state)

    response = TestClient(app).post("/school/placement/start", headers=AUTH)

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "school_placement_start_not_allowed",
        "next_action": next_action,
        "allowed_next_actions": allowed_next_actions,
    }
    assert not [
        row
        for row in store.school_sessions.values()
        if row.get("user_id") == "test_user"
        and row.get("api_version") == "rebuild"
        and row.get("flow_type") == "placement"
    ]


def test_school_placement_start_supports_class_four_profile_with_authored_snapshot_item(store):
    _seed_school_profile(store, target_class_no=4, signals=["reading", "grammar"])
    client = TestClient(app)

    response = client.post("/school/placement/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["subject_id"] == "english"
    assert body["target_class_no"] == 4
    assert body["stage"] == "snapshot"
    assert body["status"] == "in_progress"
    assert body["next_item"]["target_class_no"] == 4
    assert body["next_item"]["source_class_no"] in (3, 4)
    assert body["next_item"]["learner_skill_label"]
    assert body["next_item"]["prompt"]
    assert body["next_item"].get("passage")
    _assert_no_hidden_keys(body)


def test_school_state_resumes_active_placement_after_start(store):
    _seed_school_profile(store)
    client = TestClient(app)

    started = client.post("/school/placement/start", headers=AUTH).json()
    state = client.get("/school/state", headers=AUTH).json()

    assert state["placement_status"] == "in_progress"
    assert state["active_flow"] == "placement"
    assert state["active_session_id"] == started["session_id"]
    assert state["next_action"] == "resume_placement"
    assert state["next_action_url"] == f"/school/readiness/{started['session_id']}"
    assert state["unlock_state"] == "locked"


def test_school_state_resumes_time_capped_evidence_despite_stale_report_action():
    profile_version_id = str(uuid4())
    school_profile = {
        **_profile_payload(target_class_no=5, prior_difficulty_signals=[]),
        "profile_version_id": profile_version_id,
    }
    envelope = placement.new_placement_envelope(school_profile)
    first_item = placement.next_item(envelope)
    assert first_item is not None
    envelope = placement.apply_evaluated_attempt(
        envelope,
        first_item,
        evaluator_score=0.7,
        evaluator_confidence=0.9,
        elapsed_seconds_delta=placement.PLACEMENT_LEARNER_TIME_BUDGET_SECONDS,
    )
    assert placement.placement_status(envelope) == "insufficient_evidence"

    placement_session_id = str(uuid4())
    state = school_state_service.school_state_for_profile(
        learner_profile={"name": "Open Assets"},
        school_profile=school_profile,
        placement_session={
            "session_id": placement_session_id,
            "status": "insufficient_evidence",
            "state_json": placement.envelope_to_json(envelope),
        },
        placement_report={
            "placement_session_id": placement_session_id,
            "placement_status": "insufficient_evidence",
            "unlock_state": "locked",
            "evaluated_class_no": 4,
            "allowed_next_actions": ["start_placement"],
        },
    )

    assert state["next_action"] == "resume_placement"
    assert state["allowed_next_actions"] == ["resume_placement"]
    assert state["next_action_url"] == (
        f"/school/readiness/{placement_session_id}"
    )


def test_school_placement_answer_persists_progress_and_rejects_wrong_item(store):
    _seed_school_profile(store)
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    item_id = started["next_item"]["item_id"]

    wrong = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": "not_the_next_item", "answer": "anything"},
    )
    assert wrong.status_code == 409
    assert wrong.json()["detail"]["code"] == "unexpected_placement_item"
    assert wrong.json()["detail"]["expected_item_id"] == item_id

    answered = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    )

    assert answered.status_code == 200
    body = answered.json()
    assert body["answered_count"] == 1
    assert body["next_item"]["item_id"] != item_id
    assert len(store.learning_events) == 1
    event = store.learning_events[0]
    assert event["domain"] == "school"
    assert event["task_type"] == "school_rebuild_placement"
    assert event["session_id"] == session_id
    assert event["node_id"] == item_id
    assert event["source"] == "school_rebuild"
    assert event["attempt_type"] == "snapshot"
    assert event["score"] == 1.0
    assert event["evidence_json"]["target_class_no"] == 3
    assert event["evidence_json"]["diagnostic_stage"] == "snapshot"
    assert event["evidence_json"]["learner_response_excerpt"] == "mat"
    assert event["evidence_json"]["learner_response_truncated"] is False
    assert event["evidence_json"]["evaluation_evidence"]["score"] == 1.0
    assert event["evidence_json"]["evaluation_evidence"]["confidence"] == 1.0
    assert event["evidence_json"]["evaluation_evidence"]["criteria"]
    assert "answer_key" not in repr(event["evidence_json"])
    _assert_no_hidden_keys(body)


def test_placement_learning_event_bounds_the_exact_learner_response(store):
    _seed_school_profile(store, signals=[])
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    learner_answer = "x" * 500

    response = client.post(
        f"/school/placement/{started['session_id']}/answer",
        headers=AUTH,
        json={
            "item_id": started["next_item"]["item_id"],
            "answer": learner_answer,
        },
    )

    assert response.status_code == 200
    evidence = store.learning_events[-1]["evidence_json"]
    assert evidence["learner_response_excerpt"] == learner_answer[:320]
    assert len(evidence["learner_response_excerpt"]) == 320
    assert evidence["learner_response_truncated"] is True


def test_school_placement_answer_replay_is_payload_bound(store):
    _seed_school_profile(store)
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    item_id = started["next_item"]["item_id"]

    first = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    )
    replay = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    )
    changed = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "changed"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "placement_answer_conflict"
    assert len(
        [
            event
            for event in store.learning_events
            if event.get("session_id") == session_id
            and event.get("node_id") == item_id
        ]
    ) == 1


def test_school_placement_post_claim_failure_marks_request_failed(
    store,
    monkeypatch,
):
    _seed_school_profile(store)
    started = TestClient(app).post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    item_id = started["next_item"]["item_id"]

    original_apply_evaluated_attempt = placement.apply_evaluated_attempt

    def fail_after_claim(*_args, **_kwargs):
        raise RuntimeError("placement construction failed")

    monkeypatch.setattr(placement, "apply_evaluated_attempt", fail_after_claim)
    response = TestClient(app, raise_server_exceptions=False).post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, item_id)
    )
    assert response.status_code == 500
    assert request_row["status"] == "failed"
    assert request_row["response_json"] is None

    monkeypatch.setattr(
        placement,
        "apply_evaluated_attempt",
        original_apply_evaluated_attempt,
    )
    corrected = TestClient(app).post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "corrected answer"},
    )
    corrected_request = _run(
        store.get_school_answer_request("test_user", session_id, item_id)
    )

    assert corrected.status_code == 200
    assert corrected_request["status"] == "completed"
    assert corrected_request["answer_hash"] != request_row["answer_hash"]


def test_school_placement_stale_cas_uses_flow_neutral_public_code(store, monkeypatch):
    _seed_school_profile(store)
    started = TestClient(app).post("/school/placement/start", headers=AUTH).json()

    async def stale_cas(**_kwargs):
        raise ValueError("stale_school_answer_session")

    monkeypatch.setattr(store, "persist_school_answer_attempt", stale_cas)
    response = TestClient(app).post(
        f"/school/placement/{started['session_id']}/answer",
        headers=AUTH,
        json={"item_id": started["next_item"]["item_id"], "answer": "mat"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_school_answer_session"


def test_school_placement_duplicate_answer_is_idempotent(store):
    _seed_school_profile(store)
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    item_id = started["next_item"]["item_id"]

    first = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    ).json()
    replay = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    ).json()

    assert first["answered_count"] == 1
    assert replay["answered_count"] == 1
    assert replay["next_item"]["item_id"] == first["next_item"]["item_id"]


def test_school_placement_weak_snapshot_routes_to_targeted_diagnostic(store, monkeypatch):
    _stub_failing_open_placement_evaluator(monkeypatch)
    _seed_school_profile(store, signals=["reading"])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]

    for _ in range(8):
        item = current["next_item"]
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": "wrong"},
        )
        assert response.status_code == 200
        current = response.json()
        if current["stage"] == "targeted_diagnostic":
            break

    assert current["stage"] == "targeted_diagnostic"
    assert current["status"] == "in_progress"
    assert current["readiness_summary"]["weak_skill_ids"]
    assert current["next_item"]["stage"] == "targeted_diagnostic"


def test_school_placement_exhausted_weak_bank_starts_earliest_supported_recap(
    store,
    monkeypatch,
):
    _stub_failing_open_placement_evaluator(monkeypatch)
    _seed_school_profile(store, signals=["reading"])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]

    for _ in range(20):
        item = current["next_item"]
        if item is None:
            break
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": "wrong"},
        )
        assert response.status_code == 200
        current = response.json()

    assert current["next_item"] is None
    assert current["status"] == "below_target"
    row = _run(store.get_school_session("test_user", session_id))
    assert row["status"] == "below_target"
    assert len(store.learning_events) == 18
    assert {event["attempt_type"] for event in store.learning_events} == {
        "snapshot",
        "targeted_diagnostic",
        "confirmatory",
    }


def test_terminal_floor_failure_creates_idempotent_recap_report_backed_state(
    store,
    monkeypatch,
):
    _stub_failing_open_placement_evaluator(monkeypatch)
    _seed_school_profile(store, signals=["reading"])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]

    terminal_payload = None
    for _ in range(20):
        item = current["next_item"]
        if item is None:
            break
        terminal_payload = {"item_id": item["item_id"], "answer": "wrong"}
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json=terminal_payload,
        )
        assert response.status_code == 200
        current = response.json()

    assert current["status"] == "below_target"
    assert terminal_payload is not None
    assert len(store.school_placement_reports) == 1
    saved_report = next(iter(store.school_placement_reports.values()))
    saved_session = _run(store.get_school_session("test_user", session_id))
    assert saved_report["placement_session_id"] == session_id
    assert saved_report["profile_version_id"] == saved_session["profile_version_id"]
    assert saved_report["placement_status"] == "below_target"
    assert saved_report["unlock_state"] == "recap_required"
    assert saved_report["allowed_next_actions"] == ["start_recap"]
    assert saved_report["recommended_recap_modules"]
    _assert_no_hidden_keys(saved_report)

    state = client.get("/school/state", headers=AUTH).json()

    assert state["placement_status"] == "below_target"
    assert state["active_flow"] == "placement_report"
    assert state["active_session_id"] == session_id
    assert state["unlock_state"] == "recap_required"
    assert state["next_action"] == "start_recap"
    assert state["next_action_url"] == "/school/recap"
    assert state["allowed_next_actions"] == [
        "view_placement_report",
        "start_recap",
    ]
    assert state["blocked_reason"] is None
    _assert_no_hidden_keys(state)

    replay = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json=terminal_payload,
    )
    first_report = client.get("/school/placement/report", headers=AUTH)
    second_report = client.get("/school/placement/report", headers=AUTH)

    assert replay.status_code == 200
    assert first_report.status_code == 200
    assert second_report.status_code == 200
    assert len(store.school_placement_reports) == 1
    assert first_report.json()["report_id"] == saved_report["report_id"]
    assert second_report.json()["report_id"] == saved_report["report_id"]
    assert first_report.json()["profile_version_id"] == saved_session["profile_version_id"]
    _assert_no_hidden_keys(replay.json())
    _assert_no_hidden_keys(first_report.json())


def test_terminal_insufficient_evidence_creates_locked_report(store, monkeypatch):
    _stub_failing_open_placement_evaluator(monkeypatch)
    _seed_school_profile(store, signals=["reading"])
    monkeypatch.setattr(placement, "MIN_SCORABLE_FOR_TERMINAL_PLACEMENT", 999)
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]

    for _ in range(20):
        item = current["next_item"]
        if item is None:
            break
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": "wrong"},
        )
        assert response.status_code == 200
        current = response.json()

    assert current["status"] == "insufficient_evidence"
    assert len(store.school_placement_reports) == 1
    report = next(iter(store.school_placement_reports.values()))
    assert report["placement_status"] == "insufficient_evidence"
    assert report["unlock_state"] == "locked"
    assert report["allowed_next_actions"] == ["start_placement"]
    assert report["evidence_summary"]["track_verdicts"]

    state = client.get("/school/state", headers=AUTH).json()
    assert state["placement_status"] == "insufficient_evidence"
    assert state["unlock_state"] == "locked"
    assert state["active_flow"] == "placement_report"
    assert state["next_action"] == "start_placement"
    assert state["next_action_url"] == "/school/readiness"
    assert state["allowed_next_actions"] == [
        "view_placement_report",
        "start_placement",
    ]

    restarted = client.post("/school/placement/start", headers=AUTH)
    assert restarted.status_code == 200
    assert restarted.json()["session_id"] != session_id
    _assert_no_hidden_keys(report)
    _assert_no_hidden_keys(state)


def test_store_resumes_only_the_same_insufficient_placement_session(store):
    _seed_school_profile(store, target_class_no=5, signals=[])
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    row = _run(store.get_school_session("test_user", session_id))
    envelope = placement.envelope_from_json(row["state_json"])
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            terminal_status="insufficient_evidence",
            terminal_reason="placement_window_ended",
        ),
    )
    terminal_json = {
        **row["state_json"],
        **placement.envelope_to_json(terminal),
    }
    _run(store.upsert_school_session(
        session_id=session_id,
        user_id="test_user",
        api_version="rebuild",
        flow_type="placement",
        subject_id="english",
        class_no=5,
        status="insufficient_evidence",
        current_stage=terminal.state.stage,
        profile_version_id=row["profile_version_id"],
        source_placement_report_id=None,
        state_json=terminal_json,
    ))
    resumable = placement.resume_placement(terminal)
    resumed_json = {
        **terminal_json,
        **placement.envelope_to_json(resumable),
    }

    resumed = _run(store.resume_school_placement_session(
        user_id="test_user",
        session_id=session_id,
        profile_version_id=row["profile_version_id"],
        current_stage=resumable.state.stage,
        state_json=resumed_json,
    ))

    assert resumed["session_id"] == session_id
    assert resumed["status"] == "active"
    assert resumed["completed_at"] is None
    assert resumed["state_json"] == resumed_json

    replay = _run(store.resume_school_placement_session(
        user_id="test_user",
        session_id=session_id,
        profile_version_id=row["profile_version_id"],
        current_stage=resumable.state.stage,
        state_json=resumed_json,
    ))
    assert replay == resumed


def test_store_rejects_resume_state_that_deletes_or_rewrites_evidence(store):
    _seed_school_profile(store, target_class_no=5, signals=[])
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    row = _run(store.get_school_session("test_user", session_id))
    envelope = placement.envelope_from_json(row["state_json"])
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            terminal_status="insufficient_evidence",
            terminal_reason="placement_window_ended",
        ),
    )
    terminal_json = {
        **row["state_json"],
        **placement.envelope_to_json(terminal),
    }
    _run(store.upsert_school_session(
        session_id=session_id,
        user_id="test_user",
        api_version="rebuild",
        flow_type="placement",
        subject_id="english",
        class_no=5,
        status="insufficient_evidence",
        current_stage=terminal.state.stage,
        profile_version_id=row["profile_version_id"],
        source_placement_report_id=None,
        state_json=terminal_json,
    ))
    resumed = placement.resume_placement(terminal)
    invalid = {
        **terminal_json,
        **placement.envelope_to_json(resumed),
    }
    invalid["placement_state"] = {
        **invalid["placement_state"],
        "total_items": 1,
        "answered_item_ids": ["fabricated-placement-item"],
    }

    with pytest.raises(ValueError, match="placement_session_resume_conflict"):
        _run(store.resume_school_placement_session(
            user_id="test_user",
            session_id=session_id,
            profile_version_id=row["profile_version_id"],
            current_stage=resumed.state.stage,
            state_json=invalid,
        ))


def test_resume_validation_is_shared_by_postgres_and_in_memory_stores(store):
    postgres_source = inspect.getsource(db_repo.resume_school_placement_session)
    memory_source = inspect.getsource(store.resume_school_placement_session)

    assert "validate_placement_resume_state_json" in postgres_source
    assert "validate_placement_resume_state_json" in memory_source
    assert "FOR UPDATE" in postgres_source


def test_placement_start_resumes_the_same_insufficient_session_via_canonical_state(
    store,
):
    _seed_school_profile(store, target_class_no=5, signals=[])
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    row = _run(store.get_school_session("test_user", session_id))
    envelope = placement.envelope_from_json(row["state_json"])
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            terminal_status="insufficient_evidence",
            terminal_reason="placement_window_ended",
        ),
    )
    terminal_json = {
        **row["state_json"],
        **placement.envelope_to_json(terminal),
    }
    _run(store.upsert_school_session(
        session_id=session_id,
        user_id="test_user",
        api_version="rebuild",
        flow_type="placement",
        subject_id="english",
        class_no=5,
        status="insufficient_evidence",
        current_stage=terminal.state.stage,
        profile_version_id=row["profile_version_id"],
        source_placement_report_id=None,
        state_json=terminal_json,
    ))
    report = client.get("/school/placement/report", headers=AUTH)
    canonical = client.get("/school/state", headers=AUTH)

    assert report.status_code == 200
    assert canonical.status_code == 200
    assert canonical.json()["next_action"] == "resume_placement"
    assert canonical.json()["active_session_id"] == session_id

    resumed = client.post("/school/placement/start", headers=AUTH)

    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["session_id"] == session_id
    assert resumed.json()["status"] == "in_progress"
    assert resumed.json()["answered_count"] == started["answered_count"]
    assert resumed.json()["next_item"]["item_id"] == started["next_item"]["item_id"]
    saved = _run(store.get_school_session("test_user", session_id))
    assert saved["status"] == "active"
    assert saved["completed_at"] is None
    assert len(store.school_sessions) == 1

    # The completed insufficient-evidence report remains historical evidence,
    # but it must no longer mask the resumed active placement.
    assert len(store.school_placement_reports) == 1
    resumed_state = client.get("/school/state", headers=AUTH)
    assert resumed_state.status_code == 200
    assert resumed_state.json()["status"] == "in_progress"
    assert resumed_state.json()["placement_status"] == "in_progress"
    assert resumed_state.json()["active_session_id"] == session_id
    assert resumed_state.json()["next_action"] == "resume_placement"

    stale_report = client.get("/school/placement/report", headers=AUTH)
    assert stale_report.status_code == 409
    assert stale_report.json()["detail"]["code"] == "placement_in_progress"


def test_postgres_start_retires_conflicting_legacy_placement_before_insert():
    source = inspect.getsource(db_repo.get_or_create_active_school_placement_session)
    helper_source = inspect.getsource(
        db_repo._retire_conflicting_legacy_school_placement_sessions
    )

    assert "_retire_conflicting_legacy_school_placement_sessions" in source
    assert source.index("_retire_conflicting_legacy_school_placement_sessions") < source.index(
        "await upsert_school_session"
    )
    assert "api_version <> 'rebuild'" in helper_source
    assert "status = 'abandoned'" in helper_source
    assert "legacy_runtime_retired_for_canonical_placement" in helper_source
    assert "completed_at" in helper_source


def test_postgres_placement_presentation_types_jsonb_variadic_binds():
    source = inspect.getsource(db_repo.present_school_placement_item)

    assert "CAST(:timing_key AS text)" in source
    assert "'item_id', CAST(:item_id AS text)" in source


def test_canonical_placement_engine_has_no_v3_runtime_dependency():
    source = inspect.getsource(placement)

    assert "school_v3_placement" not in source
    assert "school_v3_runtime" not in source
    assert placement.PlacementSessionState.__module__ == placement.__name__
    assert placement.PlacementTrackState.__module__ == placement.__name__
    assert placement.PlacementAttemptEvidence.__module__ == placement.__name__


def test_canonical_track_and_skill_maps_are_immutable():
    state = placement.new_placement_envelope(_pure_profile()).state

    with pytest.raises(TypeError):
        state.track_states["new-track"] = next(iter(state.track_states.values()))
    with pytest.raises(TypeError):
        state.skill_states["new-skill"] = next(iter(state.skill_states.values()))


def test_eight_high_confidence_snapshot_passes_finish_target_ready_and_seed_only_readiness():
    envelope = placement.new_placement_envelope(_pure_profile())

    for _ in range(8):
        envelope = _apply_score(envelope, 1.0)

    assert placement.placement_status(envelope) == "target_ready"
    assert envelope.state.terminal_reason == "all_required_tracks_ready"
    assert envelope.state.readiness_seeds_applied is True
    assert len(envelope.state.answered_item_ids) == 8
    assert {track.status for track in envelope.state.track_states.values()} == {"resolved_ready"}
    for skill_state in envelope.state.skill_states.values():
        assert skill_state.ready_source == "placement"
        assert skill_state.certified_readiness == pytest.approx(0.8)
        assert skill_state.independent_passes == 0
        assert skill_state.transfer_passes == 0


def test_target_ready_route_persists_every_seed_and_replays_without_inflation(
    store,
    monkeypatch,
):
    _stub_passing_open_placement_evaluator(monkeypatch)
    _seed_school_profile(store, target_class_no=5, signals=[])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    last_request = None

    while current["status"] == "in_progress":
        row = _run(store.get_school_session("test_user", session_id))
        envelope = placement.envelope_from_json(row["state_json"])
        private_item = placement.find_item(
            envelope,
            current["next_item"]["item_id"],
        )
        answer = (
            private_item.accepted_answers[0]
            if private_item.accepted_answers
            else _strong_open_placement_answer(private_item)
        )
        last_request = {
            "item_id": current["next_item"]["item_id"],
            "answer": answer,
        }
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json=last_request,
        )
        assert response.status_code == 200
        current = response.json()

    final_row = _run(store.get_school_session("test_user", session_id))
    final_envelope = placement.envelope_from_json(final_row["state_json"])
    diagnostic = {
        "terminal_reason": final_envelope.state.terminal_reason,
        "tracks": {
            track_id: {
                "status": track.status,
                "evidence": [
                    {
                        "item_id": evidence.item_id,
                        "classification": evidence.classification,
                        "score": evidence.evaluator_score,
                        "confidence": evidence.evaluator_confidence,
                        "blockers": evidence.certifying_blockers,
                    }
                    for evidence in track.evidence
                ],
            }
            for track_id, track in final_envelope.state.track_states.items()
            if track.status not in {"provisional_ready", "resolved_ready"}
        },
    }
    assert current["status"] == "target_ready", diagnostic
    assert current["answered_count"] == 8
    graph = _run(store.get_school_learning_graph("test_user"))
    profiles = [
        row for row in graph["profiles"] if row.get("domain") == "school"
    ]
    assert len(profiles) == 8
    for profile in profiles:
        state = profile["evidence_json"]["school_readiness_state"]
        assert profile["evidence_json"]["skill_status"] == "ready"
        assert state["ready_source"] == "placement"
        assert state["independent_passes"] == 0
        assert profile["mastery"] == 0.0

    assert last_request is not None
    replay = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json=last_request,
    )
    assert replay.status_code == 200
    assert replay.json() == current
    replay_graph = _run(store.get_school_learning_graph("test_user"))
    assert replay_graph["profiles"] == graph["profiles"]


def test_mixed_snapshot_queues_only_weak_and_ambiguous_tracks_for_stage_two():
    envelope = placement.new_placement_envelope(_pure_profile())
    snapshot_track_ids = tuple(envelope.state.track_states)

    for score in (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.70):
        envelope = _apply_score(envelope, score)

    assert placement.placement_status(envelope) == "in_progress"
    assert envelope.state.stage == "targeted_diagnostic"
    assert envelope.state.pending_track_ids == snapshot_track_ids[-2:]
    assert envelope.state.targeted_skill_ids == tuple(
        envelope.state.track_states[track_id].primary_skill_id
        for track_id in snapshot_track_ids[-2:]
    )
    assert placement.next_item(envelope).track_id in set(snapshot_track_ids[-2:])


def test_stage_two_binary_search_descends_then_narrows_up_with_arbitrary_authored_bands(monkeypatch):
    tracks = placement_tracks_for("english", 5)
    first = tracks[0]
    expanded = replace(
        first,
        snapshot_item=replace(first.snapshot_item, source_class_no=5),
        bands=_synthetic_bands(first, (1, 2, 3, 4, 5)),
    )
    monkeypatch.setattr(
        placement,
        "placement_tracks_for",
        lambda subject_id, class_no: (expanded,) + tracks[1:],
    )
    envelope = placement.new_placement_envelope(_pure_profile(target_class_no=5))

    envelope = _apply_score(envelope, 0.0)
    for _ in range(7):
        envelope = _apply_score(envelope, 1.0)

    first_targeted = placement.next_item(envelope)
    assert first_targeted.track_id == expanded.track_id
    assert first_targeted.source_class_no == 3
    envelope = placement.apply_evaluated_attempt(
        envelope,
        first_targeted,
        evaluator_score=1.0,
        evaluator_confidence=1.0,
    )
    narrowed = placement.next_item(envelope)
    assert narrowed.track_id == expanded.track_id
    assert narrowed.source_class_no == 4

    envelope = placement.apply_evaluated_attempt(
        envelope,
        narrowed,
        evaluator_score=0.0,
        evaluator_confidence=1.0,
    )
    assert placement.placement_status(envelope) == "below_target"
    assert envelope.state.confirmatory_track_ids == ()
    assert envelope.state.track_states[expanded.track_id].highest_passed_band == 3
    assert envelope.state.track_states[expanded.track_id].first_failed_band == 4


def test_missing_same_track_item_never_falls_back_to_an_unrelated_track(monkeypatch):
    tracks = placement_tracks_for("english", 3)
    missing = replace(tracks[0], bands=())
    monkeypatch.setattr(
        placement,
        "placement_tracks_for",
        lambda subject_id, class_no: (missing,) + tracks[1:],
    )
    envelope = placement.new_placement_envelope(_pure_profile())

    envelope = _apply_score(envelope, 0.0)
    for _ in range(7):
        envelope = _apply_score(envelope, 1.0)

    assert placement.next_item(envelope) is None
    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert envelope.state.track_states[missing.track_id].status == "unresolved"
    assert envelope.state.track_states[missing.track_id].unresolved_reason == "missing_authored_same_track_item"


def test_stage_three_is_entered_only_for_insufficient_boundary_evidence():
    envelope = placement.new_placement_envelope(_pure_profile())
    ambiguous_track_id = next(iter(envelope.state.track_states))

    envelope = _apply_score(envelope, 0.70)
    for _ in range(7):
        envelope = _apply_score(envelope, 1.0)

    targeted = placement.next_item(envelope)
    assert targeted.track_id == ambiguous_track_id
    envelope = placement.apply_evaluated_attempt(
        envelope,
        targeted,
        evaluator_score=0.70,
        evaluator_confidence=1.0,
    )

    assert envelope.state.stage == "confirmatory"
    assert envelope.state.confirmatory_track_ids == (ambiguous_track_id,)
    track = envelope.state.track_states[ambiguous_track_id]
    assert track.unresolved_reason == "insufficient_boundary_evidence"
    confirmatory = placement.next_item(envelope)
    assert confirmatory.track_id == ambiguous_track_id
    assert confirmatory.source_class_no == track.boundary_band


def test_same_band_contradiction_is_the_other_valid_stage_three_trigger():
    envelope = placement.new_placement_envelope(_pure_profile(target_class_no=2))
    contradicted_track_id = next(iter(envelope.state.track_states))

    envelope = _apply_score(envelope, 0.0)
    for _ in range(7):
        envelope = _apply_score(envelope, 1.0)
    targeted = placement.next_item(envelope)
    assert targeted.track_id == contradicted_track_id
    assert targeted.source_class_no == 1

    envelope = placement.apply_evaluated_attempt(
        envelope,
        targeted,
        evaluator_score=1.0,
        evaluator_confidence=1.0,
    )

    assert envelope.state.stage == "confirmatory"
    assert envelope.state.confirmatory_track_ids == (contradicted_track_id,)
    assert (
        envelope.state.track_states[contradicted_track_id].unresolved_reason
        == "contradictory_evidence"
    )


@pytest.mark.parametrize(
    ("score", "confidence", "blockers", "scorable", "expected"),
    [
        (0.80, 0.75, (), True, "pass"),
        (1.00, 1.00, ("language_mismatch",), True, "ambiguous"),
        (0.59, 0.75, (), True, "fail"),
        (0.79, 1.00, (), True, "ambiguous"),
        (1.00, 0.74, (), True, "ambiguous"),
        (1.00, 1.00, (), False, "unscorable"),
    ],
)
def test_evidence_classification_uses_backend_thresholds(
    score,
    confidence,
    blockers,
    scorable,
    expected,
):
    assert placement.classify_placement_evidence(
        evaluator_score=score,
        evaluator_confidence=confidence,
        certifying_blockers=blockers,
        scorable=scorable,
    ) == expected


def test_all_weak_at_authored_floor_starts_earliest_supported_recap_path():
    envelope = placement.new_placement_envelope(_pure_profile())

    for _ in range(18):
        item = placement.next_item(envelope)
        if item is None:
            break
        envelope = placement.apply_evaluated_attempt(
            envelope,
            item,
            evaluator_score=0.0,
            evaluator_confidence=1.0,
        )

    assert placement.placement_status(envelope) == "below_target"
    assert envelope.state.terminal_reason == "authored_floor_rebuild_required"
    assert envelope.state.readiness_seeds_applied is False
    assert all(
        track.status == "confirmed_weak"
        for track in envelope.state.track_states.values()
    )
    assert all(
        track.unresolved_reason == "below_authored_floor"
        for track in envelope.state.track_states.values()
    )
    assert all(state.ready_source is None for state in envelope.state.skill_states.values())


def test_duplicate_item_application_is_an_exact_no_op():
    envelope = placement.new_placement_envelope(_pure_profile())
    item = placement.next_item(envelope)
    first = placement.apply_evaluated_attempt(
        envelope,
        item,
        evaluator_score=1.0,
        evaluator_confidence=1.0,
        elapsed_seconds_delta=7,
    )

    duplicate = placement.apply_evaluated_attempt(
        first,
        item,
        evaluator_score=0.0,
        evaluator_confidence=1.0,
        elapsed_seconds_delta=99,
    )

    assert duplicate is first


def test_explicit_abandon_is_terminal_locked_and_never_seeds_readiness():
    envelope = placement.new_placement_envelope(_pure_profile())
    first = _apply_score(envelope, 1.0)

    abandoned = placement.abandon_placement(first)

    assert placement.placement_status(abandoned) == "abandoned"
    assert abandoned.state.terminal_reason == "learner_abandoned"
    assert abandoned.state.readiness_seeds_applied is False
    assert placement.next_item(abandoned) is None
    assert all(
        state.ready_source is None for state in abandoned.state.skill_states.values()
    )


def test_school_placement_abandon_persists_locked_report_and_allows_clean_restart(store):
    _seed_school_profile(store)
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()

    response = client.post(
        f"/school/placement/{started['session_id']}/abandon",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "abandoned"
    saved = _run(store.get_school_session("test_user", started["session_id"]))
    assert saved["status"] == "abandoned"
    report = _run(store.get_school_placement_report("test_user", started["session_id"]))
    assert report["placement_status"] == "abandoned"
    assert report["unlock_state"] == "locked"
    assert report["allowed_next_actions"] == ["start_placement"]
    state = client.get("/school/state", headers=AUTH).json()
    assert state["placement_status"] == "abandoned"
    assert state["unlock_state"] == "locked"
    assert state["allowed_next_actions"] == ["view_placement_report", "start_placement"]
    _assert_no_hidden_keys(response.json())
    _assert_no_hidden_keys(report)


def test_school_placement_abandon_cas_preserves_a_concurrent_answer_commit(
    store,
    monkeypatch,
):
    _seed_school_profile(store, target_class_no=3, signals=[])
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    session_id = started["session_id"]
    original_get = store.get_school_session
    raced = False
    committed_item_id: str | None = None

    async def get_with_concurrent_answer(user_id: str, requested_session_id: str):
        nonlocal raced, committed_item_id
        row = await original_get(user_id, requested_session_id)
        if raced or requested_session_id != session_id or row is None:
            return row
        raced = True
        stale_row = dict(row)
        envelope = placement.envelope_from_json(row["state_json"])
        item = placement.next_item(envelope)
        assert item is not None
        committed_item_id = item.item_id
        advanced = placement.apply_evaluated_attempt(
            envelope,
            item,
            evaluator_score=1.0,
            evaluator_confidence=1.0,
        )
        concurrent_state = {
            **row["state_json"],
            **placement.envelope_to_json(advanced),
        }
        await store.upsert_school_session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            api_version=row["api_version"],
            flow_type=row["flow_type"],
            subject_id=row["subject_id"],
            class_no=int(row["class_no"]),
            status="active",
            current_stage=advanced.state.stage,
            linked_session_id=row.get("linked_session_id"),
            profile_version_id=row.get("profile_version_id"),
            source_placement_report_id=row.get("source_placement_report_id"),
            state_json=concurrent_state,
        )
        return stale_row

    monkeypatch.setattr(store, "get_school_session", get_with_concurrent_answer)

    response = client.post(
        f"/school/placement/{session_id}/abandon",
        headers=AUTH,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "placement_abandon_conflict"
    saved = _run(original_get("test_user", session_id))
    restored = placement.envelope_from_json(saved["state_json"])
    assert saved["status"] == "active"
    assert restored.state.answered_item_ids == (committed_item_id,)
    assert _run(store.get_school_placement_report("test_user", session_id)) is None


def test_shuffled_public_mcq_answer_is_graded_by_backend_text_authority(store):
    _seed_school_profile(store, target_class_no=3, signals=["vocabulary"])
    client = TestClient(app)
    started = client.post("/school/placement/start", headers=AUTH).json()
    row = _run(store.get_school_session("test_user", started["session_id"]))
    envelope = placement.envelope_from_json(row["state_json"])
    item = placement.find_item(envelope, started["next_item"]["item_id"])

    response = client.post(
        f"/school/placement/{started['session_id']}/answer",
        headers=AUTH,
        json={"item_id": item.item_id, "answer": item.answer_key},
    )

    assert response.status_code == 200
    assert store.learning_events[-1]["score"] == 1.0
    assert store.learning_events[-1]["node_id"] == item.item_id


def test_placement_persists_private_server_presentation_time_without_leaking_it(
    store,
    monkeypatch,
):
    presented_at = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        store,
        "_school_placement_presented_at",
        lambda: presented_at,
    )
    _seed_school_profile(store, signals=[])
    client = TestClient(app)

    response = client.post("/school/placement/start", headers=AUTH)

    assert response.status_code == 200
    public = response.json()
    row = _run(store.get_school_session("test_user", public["session_id"]))
    timing = row["state_json"]["_placement_item_timing"]
    assert timing == {
        "item_id": public["next_item"]["item_id"],
        "presented_at": presented_at.isoformat(),
    }
    assert "_placement_item_timing" not in public
    _assert_no_hidden_keys(public)


def test_placement_start_stamps_presentation_after_session_write_latency(
    store,
    monkeypatch,
):
    original_create = store.get_or_create_active_school_placement_session
    write_completed_at: datetime | None = None

    async def delayed_create(**kwargs):
        nonlocal write_completed_at
        await asyncio.sleep(0.03)
        row = await original_create(**kwargs)
        write_completed_at = datetime.now(timezone.utc)
        return row

    monkeypatch.setattr(
        store,
        "get_or_create_active_school_placement_session",
        delayed_create,
    )
    _seed_school_profile(store, signals=[])
    client = TestClient(app)

    response = client.post("/school/placement/start", headers=AUTH)
    response_completed_at = datetime.now(timezone.utc)

    assert response.status_code == 200
    assert write_completed_at is not None
    row = _run(
        store.get_school_session("test_user", response.json()["session_id"])
    )
    presented_at = datetime.fromisoformat(
        row["state_json"]["_placement_item_timing"]["presented_at"]
    )
    assert write_completed_at <= presented_at <= response_completed_at


def test_placement_answer_records_learner_elapsed_and_evaluator_wait_separately(
    store,
    monkeypatch,
):
    started_at = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)
    answer_arrived_at = started_at + timedelta(seconds=11)
    next_presented_at = answer_arrived_at + timedelta(seconds=4)
    presentation_times = iter((started_at, next_presented_at))
    monotonic_times = iter((100.0, 104.0))
    monkeypatch.setattr(
        store,
        "_school_placement_presented_at",
        lambda: next(presentation_times),
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_placement_server_now",
        lambda: answer_arrived_at,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_placement_monotonic",
        lambda: next(monotonic_times),
    )
    _stub_passing_open_placement_evaluator(monkeypatch)
    _seed_school_profile(store, target_class_no=5, signals=[])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    row = _run(store.get_school_session("test_user", session_id))
    envelope = placement.envelope_from_json(row["state_json"])
    item = placement.find_item(envelope, current["next_item"]["item_id"])
    answer = (
        item.accepted_answers[0]
        if item.accepted_answers
        else "The passage evidence supports this complete answer."
    )

    response = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item.item_id, "answer": answer},
    )

    assert response.status_code == 200
    saved = _run(store.get_school_session("test_user", session_id))
    restored = placement.envelope_from_json(saved["state_json"])
    assert restored.state.elapsed_seconds == 11
    assert restored.state.evaluator_wait_seconds == 4
    timing = saved["state_json"]["_placement_item_timing"]
    assert timing["item_id"] == response.json()["next_item"]["item_id"]
    assert timing["presented_at"] == next_presented_at.isoformat()
    assert "_placement_item_timing" not in response.json()
    _assert_no_hidden_keys(response.json())


def test_placement_answer_captures_arrival_before_any_awaited_profile_work(
    store,
    monkeypatch,
):
    _seed_school_profile(store, target_class_no=5, signals=[])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    item_id = current["next_item"]["item_id"]
    row = _run(store.get_school_session("test_user", session_id))
    item = placement.find_item(
        placement.envelope_from_json(row["state_json"]),
        item_id,
    )
    answer = item.accepted_answers[0]
    call_order: list[str] = []
    answer_arrived_at = datetime(2026, 7, 14, 9, 0, 5, tzinfo=timezone.utc)
    original_learner_profile = school_rebuild_routes._learner_profile

    def server_now():
        call_order.append("answer_arrived")
        return answer_arrived_at

    async def learner_profile(user_id: str):
        call_order.append("profile_read")
        return await original_learner_profile(user_id)

    monkeypatch.setattr(school_rebuild_routes, "_placement_server_now", server_now)
    monkeypatch.setattr(school_rebuild_routes, "_learner_profile", learner_profile)

    response = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": answer},
    )

    assert response.status_code == 200
    assert call_order[:2] == ["answer_arrived", "profile_read"]


def test_failed_evaluator_retry_excludes_provider_and_retry_wall_time(
    store,
    monkeypatch,
):
    started_at = datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc)
    route_times = iter(
        (
            started_at + timedelta(seconds=10),
            started_at + timedelta(seconds=14),
            started_at + timedelta(seconds=100),
        )
    )
    presentation_times = iter(
        (started_at, started_at + timedelta(seconds=104))
    )
    monotonic_times = iter((200.0, 300.0, 304.0))
    monkeypatch.setattr(
        store,
        "_school_placement_presented_at",
        lambda: next(presentation_times),
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_placement_server_now",
        lambda: next(route_times),
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_placement_monotonic",
        lambda: next(monotonic_times),
    )
    original = school_rebuild_routes.placement_evaluator.evaluate_school_placement_item
    calls = 0

    async def flaky_evaluator(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise school_rebuild_routes.placement_evaluator.SchoolPlacementEvaluatorUnavailableError(
                school_rebuild_routes.placement_evaluator.EVALUATOR_UNAVAILABLE_CODE
            )
        return await original(*args, **kwargs)

    monkeypatch.setattr(
        school_rebuild_routes.placement_evaluator,
        "evaluate_school_placement_item",
        flaky_evaluator,
    )
    _seed_school_profile(store, target_class_no=3, signals=[])
    client = TestClient(app)
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    item_id = current["next_item"]["item_id"]

    failed = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    )
    assert failed.status_code == 503
    after_failure = _run(store.get_school_session("test_user", session_id))
    timing = after_failure["state_json"]["_placement_item_timing"]
    assert timing["item_id"] == item_id
    assert timing["retry_pending"] is True
    assert timing["accrued_learner_seconds"] == 10

    retried = client.post(
        f"/school/placement/{session_id}/answer",
        headers=AUTH,
        json={"item_id": item_id, "answer": "mat"},
    )

    assert retried.status_code == 200
    saved = _run(store.get_school_session("test_user", session_id))
    restored = placement.envelope_from_json(saved["state_json"])
    assert restored.state.elapsed_seconds == 10
    assert restored.state.evaluator_wait_seconds == 4


def test_canonical_serialization_round_trip_preserves_track_boundaries_queues_and_timing():
    envelope = placement.new_placement_envelope(_pure_profile())
    for score in (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.70):
        envelope = _apply_score(envelope, score, elapsed_seconds=3)
    envelope = replace(
        envelope,
        state=replace(
            envelope.state,
            stage_elapsed_seconds=11,
            evaluator_wait_seconds=29,
            terminal_reason="pending_boundary_resolution",
        ),
    )

    payload = placement.envelope_to_json(envelope)
    restored = placement.envelope_from_json(payload)

    assert payload["engine_version"] == placement.ENGINE_VERSION
    assert restored == envelope
    assert restored.state.pending_track_ids == envelope.state.pending_track_ids
    assert restored.state.confirmatory_track_ids == envelope.state.confirmatory_track_ids
    assert restored.state.track_states == envelope.state.track_states


def test_serialization_rejects_unknown_engine_and_migrates_only_pristine_v1_state():
    with pytest.raises(ValueError, match="unsupported_placement_engine_version"):
        placement.envelope_from_json({"engine_version": "future-placement-99"})

    migrated = placement.envelope_from_json({
        "engine_version": "school-rebuild-placement-1",
        "profile_version_id": "profile-v1",
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
        "placement_state": {
            "subject_id": "english",
            "class_no": 3,
            "answered_item_ids": [],
            "total_items": 0,
            "scorable_answers": 0,
        },
    })
    assert migrated.state.stage == "snapshot"
    assert len(migrated.state.track_states) == 8

    with pytest.raises(ValueError, match="placement_state_migration_required"):
        placement.envelope_from_json({
            "engine_version": "school-rebuild-placement-1",
            "profile_version_id": "profile-v1",
            "placement_state": {
                "subject_id": "english",
                "class_no": 3,
                "answered_item_ids": ["legacy-item"],
                "total_items": 1,
                "scorable_answers": 1,
            },
        })
