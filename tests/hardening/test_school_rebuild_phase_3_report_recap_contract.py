import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_rebuild_placement_bank import placement_bank_for
from app.db import repo
from app.main import app
from app.services import school_rebuild_placement as placement
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION
from app.services.school_core.readiness import SkillReadinessState
from app.services.school_rebuild_recap import REVISION_STEPS, _checks_for_track
from app.services.school_rebuild_report import (
    _evidence_summary,
    build_placement_report,
    public_placement_report,
)

AUTH = {"Authorization": "Bearer test_token"}


@pytest.mark.asyncio
async def test_unknown_placement_class_persists_as_database_null(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.params = None
            self.committed = False

        async def execute(self, _statement, params):
            self.params = params

        async def commit(self):
            self.committed = True

    async def fake_get_report(_session, _user_id, _placement_session_id):
        return {"report_id": "report-id"}

    monkeypatch.setattr(repo, "get_school_placement_report", fake_get_report)
    session = FakeSession()

    await repo.upsert_school_placement_report(
        session,
        report_id="00000000-0000-0000-0000-000000000001",
        user_id="test_user",
        profile_version_id="00000000-0000-0000-0000-000000000002",
        placement_session_id="00000000-0000-0000-0000-000000000003",
        placement_status="insufficient_evidence",
        subject_id="english",
        target_class_no=5,
        evaluated_class_no=None,
        active_learning_class_no=None,
        unlock_state="locked",
        blocking_skills=[],
        watchlist_skills=[],
        evidence_summary={},
        recommended_recap_modules=[],
        learner_summary="We need a few more answers.",
        parent_summary="Placement is not complete.",
        allowed_next_actions=["resume_placement"],
    )

    assert session.params["evaluated_class_no"] is None
    assert session.params["active_learning_class_no"] is None
    assert session.committed is True


def test_unknown_placement_class_has_additive_nullable_schema_migration():
    root = Path(__file__).resolve().parents[2]
    schema = (root / "app/db/schema.sql").read_text(encoding="utf-8").casefold()
    migration = (
        root
        / "app/db/migrations/2026-07-14-school-placement-report-nullable-classes.sql"
    ).read_text(encoding="utf-8").casefold()

    assert "evaluated_class_no             integer," in schema
    assert "active_learning_class_no       integer," in schema
    assert "alter column evaluated_class_no drop not null" in migration
    assert "alter column active_learning_class_no drop not null" in migration


@pytest.mark.parametrize("terminal_status", ("abandoned", "insufficient_evidence"))
def test_evidence_free_incomplete_report_keeps_overall_class_unknown(terminal_status):
    envelope = placement.new_placement_envelope({
        "profile_version_id": "profile-version",
        "subject_ids": ["english"],
        "target_class_no": 5,
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    })
    if terminal_status == "abandoned":
        terminal = placement.abandon_placement(envelope)
    else:
        terminal = replace(
            envelope,
            state=replace(
                envelope.state,
                terminal_status="insufficient_evidence",
                terminal_reason="required_tracks_unresolved",
            ),
        )

    report = build_placement_report(
        user_id="test_user",
        placement_session_id="placement-session",
        placement_row={"state_json": placement.envelope_to_json(terminal)},
        learning_events=[],
    )
    public = public_placement_report(report)

    assert report["evaluated_class_no"] is None
    assert report["active_learning_class_no"] is None
    assert public["evaluated_class_no"] is None
    assert public["active_learning_class_no"] is None


def test_incomplete_report_emits_class_when_three_target_anchors_agree():
    envelope = placement.new_placement_envelope({
        "profile_version_id": "profile-version",
        "subject_ids": ["english"],
        "target_class_no": 5,
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    })
    track_states = dict(envelope.state.track_states)
    target_anchor_ids = [
        track_id
        for track_id, track in track_states.items()
        if track.snapshot_source_band == envelope.state.class_no
    ]
    assert len(target_anchor_ids) == 4
    for track_id in target_anchor_ids[:3]:
        track = track_states[track_id]
        track_states[track_id] = replace(
            track,
            status="resolved_ready",
            evidence=(
                placement.PlacementAttemptEvidence(
                    item_id=track.snapshot_item_id,
                    track_id=track.track_id,
                    primary_skill_id=track.primary_skill_id,
                    source_class_no=5,
                    stage="snapshot",
                    classification="pass",
                    evaluator_score=0.9,
                    evaluator_confidence=0.9,
                ),
            ),
            highest_passed_band=5,
        )
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            track_states=track_states,
            terminal_status="insufficient_evidence",
            terminal_reason="required_tracks_unresolved",
        ),
    )

    report = build_placement_report(
        user_id="test_user",
        placement_session_id="placement-session",
        placement_row={"state_json": placement.envelope_to_json(terminal)},
        learning_events=[],
    )

    assert report["evaluated_class_no"] == 5
    assert report["active_learning_class_no"] is None


@pytest.mark.parametrize(
    "track_id",
    ("english.c5.sentence_order", "english.c5.inference"),
)
@pytest.mark.parametrize("source_class_no", (4, 5))
def test_class_five_recap_uses_distinct_authored_checks_not_placement_items(
    track_id,
    source_class_no,
):
    checks = _checks_for_track(
        subject_id="english",
        target_class_no=5,
        track_id=track_id,
        source_class_no=source_class_no,
    )
    required_steps = {
        "guided_check",
        "bridge",
        "masterclass",
        "independent_check",
        "transfer_check",
        *REVISION_STEPS,
    }
    placement_ids = {
        item.item_id for item in placement_bank_for("english", 5)
    }
    placement_passages = {
        " ".join(item.passage.casefold().split())
        for item in placement_bank_for("english", 5)
    }
    placement_prompts = {
        " ".join(item.prompt.casefold().split())
        for item in placement_bank_for("english", 5)
    }

    assert required_steps <= set(checks)
    source_ids = [checks[step]["source_item_id"] for step in required_steps]
    assert len(source_ids) == len(set(source_ids))
    assert placement_ids.isdisjoint(source_ids)
    assert len({checks[step]["passage"] for step in required_steps}) == len(
        required_steps
    )
    assert placement_passages.isdisjoint(
        " ".join(checks[step]["passage"].casefold().split())
        for step in required_steps
    )
    assert placement_prompts.isdisjoint(
        " ".join(checks[step]["prompt"].casefold().split())
        for step in required_steps
    )


def test_sentence_order_revision_accepts_both_valid_contrast_orders():
    checks = _checks_for_track(
        subject_id="english",
        target_class_no=5,
        track_id="english.c5.sentence_order",
        source_class_no=5,
    )

    assert (
        "The driver found another road although the first route was blocked."
        in checks["revision_level_3"]["accepted_answers"]
    )


def test_placement_report_counts_blocked_attempt_as_needing_another_look():
    summary = _evidence_summary(
        [
            {
                "node_id": "strong",
                "score": 0.9,
                "confidence": 1.0,
                "blockers": [],
                "attempt_type": "snapshot",
            },
            {
                "node_id": "blocked",
                "score": 0.9,
                "confidence": 1.0,
                "blockers": ["required_criteria_missing"],
                "attempt_type": "targeted_diagnostic",
            },
        ],
        2,
    )

    assert summary["correct_attempts"] == 1
    assert summary["incorrect_attempts"] == 1


def test_placement_report_does_not_count_low_confidence_high_score_as_correct():
    summary = _evidence_summary(
        [
            {
                "node_id": "low-confidence-answer",
                "score": 0.9,
                "confidence": 0.2,
                "blockers": [],
                "attempt_type": "snapshot",
            }
        ],
        fallback_total=0,
    )

    assert summary["correct_attempts"] == 0
    assert summary["incorrect_attempts"] == 1


def test_blocking_skill_stats_do_not_count_low_confidence_high_score_as_correct():
    envelope = placement.new_placement_envelope({
        "profile_version_id": "profile-version",
        "subject_ids": ["english"],
        "target_class_no": 5,
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    })
    track_states = dict(envelope.state.track_states)
    first_track_id = next(iter(track_states))
    first_track = track_states[first_track_id]
    track_states[first_track_id] = replace(
        first_track,
        status="confirmed_weak",
        boundary_band=min(first_track.authored_bands),
    )
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            track_states=track_states,
            terminal_status="below_target",
        ),
    )

    report = build_placement_report(
        user_id="test_user",
        placement_session_id="placement-session",
        placement_row={"state_json": placement.envelope_to_json(terminal)},
        learning_events=[
            {
                "session_id": "placement-session",
                "task_type": "school_rebuild_placement",
                "node_id": "low-confidence-answer",
                "skill_id": first_track.primary_skill_id,
                "score": 0.9,
                "confidence": 0.2,
                "blockers": [],
                "attempt_type": "snapshot",
            }
        ],
    )

    assert report["blocking_skills"][0]["attempts"] == 1
    assert report["blocking_skills"][0]["correct_attempts"] == 0


def test_only_confirmed_weak_tracks_become_recap_modules_and_unresolved_tracks_stay_watchlisted():
    envelope = placement.new_placement_envelope({
        "profile_version_id": "profile-version",
        "subject_ids": ["english"],
        "target_class_no": 3,
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    })
    track_states = dict(envelope.state.track_states)
    skill_states = dict(envelope.state.skill_states)
    first_track_id, second_track_id = tuple(track_states)[:2]
    first_track = track_states[first_track_id]
    second_track = track_states[second_track_id]
    track_states[first_track_id] = replace(
        first_track,
        status="confirmed_weak",
        boundary_band=min(first_track.authored_bands),
    )
    track_states[second_track_id] = replace(
        second_track,
        status="unresolved",
        boundary_band=min(second_track.authored_bands),
        unresolved_reason="continued_contradiction",
    )
    for track in (first_track, second_track):
        skill_states[track.primary_skill_id] = SkillReadinessState(
            skill_id=track.primary_skill_id,
            practice_readiness=0.0,
            total_attempts=2,
            last_confidence=1.0,
        )
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            track_states=track_states,
            skill_states=skill_states,
            terminal_status="below_target",
        ),
    )

    report = build_placement_report(
        user_id="test_user",
        placement_session_id="placement-session",
        placement_row={"state_json": placement.envelope_to_json(terminal)},
        learning_events=[],
    )

    assert len(report["blocking_skills"]) == 1
    assert {
        module["primary_skill_id"]
        for module in report["recommended_recap_modules"]
    } == {first_track.primary_skill_id}
    assert report["watchlist_skills"] == [
        {
            "label": second_track.learner_skill_label,
            "source_class_no": min(second_track.authored_bands),
            "status": "needs_confirmation",
        }
    ]


def test_resolved_ready_track_is_not_reclassified_as_a_recap_gap_by_low_ema():
    envelope = placement.new_placement_envelope({
        "profile_version_id": "profile-version",
        "subject_ids": ["english"],
        "target_class_no": 5,
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    })
    track_states = dict(envelope.state.track_states)
    skill_states = dict(envelope.state.skill_states)
    first_track_id, second_track_id = tuple(track_states)[:2]
    first_track = track_states[first_track_id]
    second_track = track_states[second_track_id]
    track_states[first_track_id] = replace(
        first_track,
        status="confirmed_weak",
        boundary_band=min(first_track.authored_bands),
    )
    track_states[second_track_id] = replace(
        second_track,
        status="resolved_ready",
        boundary_band=max(second_track.authored_bands),
    )
    skill_states[first_track.primary_skill_id] = SkillReadinessState(
        skill_id=first_track.primary_skill_id,
        practice_readiness=0.0,
        total_attempts=2,
        last_confidence=1.0,
    )
    # Placement track resolution is the placement authority. A low generic EMA
    # must not turn a resolved track into a claimed prerequisite gap.
    skill_states[second_track.primary_skill_id] = SkillReadinessState(
        skill_id=second_track.primary_skill_id,
        practice_readiness=0.0,
        total_attempts=3,
        last_confidence=0.95,
    )
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            track_states=track_states,
            skill_states=skill_states,
            terminal_status="below_target",
        ),
    )

    report = build_placement_report(
        user_id="test_user",
        placement_session_id="placement-session",
        placement_row={"state_json": placement.envelope_to_json(terminal)},
        learning_events=[],
    )

    assert [row["label"] for row in report["blocking_skills"]] == [
        first_track.learner_skill_label
    ]
    assert [row["primary_skill_id"] for row in report["recommended_recap_modules"]] == [
        first_track.primary_skill_id
    ]


def test_recap_modules_follow_confirmed_weak_track_identity_when_skill_is_shared():
    envelope = placement.new_placement_envelope({
        "profile_version_id": "profile-version",
        "subject_ids": ["english"],
        "target_class_no": 5,
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    })
    track_states = dict(envelope.state.track_states)
    weak_track_id, ready_sibling_id = tuple(track_states)[:2]
    weak_track = track_states[weak_track_id]
    ready_sibling = track_states[ready_sibling_id]
    track_states[weak_track_id] = replace(
        weak_track,
        status="confirmed_weak",
        boundary_band=min(weak_track.authored_bands),
    )
    track_states[ready_sibling_id] = replace(
        ready_sibling,
        primary_skill_id=weak_track.primary_skill_id,
        status="resolved_ready",
        highest_passed_band=max(ready_sibling.authored_bands),
        boundary_band=max(ready_sibling.authored_bands),
    )
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            track_states=track_states,
            terminal_status="below_target",
        ),
    )

    report = build_placement_report(
        user_id="test_user",
        placement_session_id="placement-session",
        placement_row={"state_json": placement.envelope_to_json(terminal)},
        learning_events=[],
    )

    assert [
        module["placement_track_id"]
        for module in report["recommended_recap_modules"]
    ] == [weak_track_id]


def _run(coro):
    return asyncio.run(coro)


def _profile_payload() -> dict:
    return {
        "display_name": "Open Assets Learner",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": 3,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": "I want to understand Class 3 English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": ["reading", "vocabulary"],
    }


def _activate_school_profile(client: TestClient, payload: dict) -> object:
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            **payload,
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    assert saved.status_code == 200
    draft = saved.json()["draft"]
    return client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
            "request_id": str(uuid4()),
        },
    )


def _seed_school_profile(store) -> None:
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    response = _activate_school_profile(client, _profile_payload())
    assert response.status_code == 200


@pytest.fixture(autouse=True)
def _trusted_open_placement_evaluator(monkeypatch):
    async def evaluate(**kwargs):
        activity = kwargs["activity"]
        answer = kwargs["answer"]
        passed = answer != "wrong"
        return {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": list(activity["skill_ids"]),
            "score": 1.0 if passed else 0.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": passed,
                    "quality": 1.0 if passed else 0.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [] if passed else ["placement_gap"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Evidence recorded.",
        }

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )


def _complete_below_target_placement(client: TestClient) -> str:
    private_items = {
        item.item_id: item for item in placement_bank_for("english", 3)
    }
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    for _ in range(20):
        item = current["next_item"]
        if item is None:
            break
        private = private_items[item["item_id"]]
        fail_target_word_role = (
            private.stage == "snapshot"
            and private.source_class_no == 3
            and private.track_id.endswith(".word_roles")
        )
        answer = (
            "wrong"
            if fail_target_word_role
            else (
                private.accepted_answers[0]
                if private.evaluation_mode == "deterministic"
                else "This complete English answer uses the passage clue clearly."
            )
        )
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": answer},
        )
        assert response.status_code == 200
        current = response.json()
    assert current["status"] == "below_target"
    return session_id


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {"answer_key", "accepted_answers", "model_answer", "rubric", "threshold"}
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def _replace_placement_report_same_profile(
    store,
    *,
    old_placement_session_id: str,
    old_report: dict,
) -> dict:
    old_placement = _run(
        store.get_school_session("test_user", old_placement_session_id)
    )
    new_placement_session_id = "same-profile-new-placement"
    _run(
        store.upsert_school_session(
            **{
                **old_placement,
                "session_id": new_placement_session_id,
                "status": "active",
            }
        )
    )
    _run(
        store.upsert_school_session(
            **{
                **old_placement,
                "session_id": new_placement_session_id,
                "status": "complete",
            }
        )
    )
    new_report = {
        **old_report,
        "report_id": "same-profile-new-report",
        "placement_session_id": new_placement_session_id,
    }
    return _run(store.upsert_school_placement_report(**new_report))


def _seed_completed_placement_report(store, client, placement_status: str) -> tuple[dict, dict]:
    started = client.post("/school/placement/start", headers=AUTH).json()
    placement_row = _run(store.get_school_session("test_user", started["session_id"]))
    completed_row = {
        **placement_row,
        "status": "complete",
        "state_json": {
            **placement_row["state_json"],
            "status": "complete",
        },
    }
    _run(store.upsert_school_session(**completed_row))
    target_ready = placement_status == "target_ready"
    report = _run(
        store.upsert_school_placement_report(
            report_id=str(uuid4()),
            user_id="test_user",
            profile_version_id=placement_row["profile_version_id"],
            placement_session_id=placement_row["session_id"],
            placement_status=placement_status,
            subject_id="english",
            target_class_no=3,
            evaluated_class_no=3 if target_ready else 2,
            active_learning_class_no=3 if target_ready else 2,
            unlock_state="target_unlocked" if target_ready else "recap_required",
            blocking_skills=[] if target_ready else [{"skill_id": "reading"}],
            watchlist_skills=[],
            evidence_summary={"total_attempts": 8},
            recommended_recap_modules=[] if target_ready else [{"module_id": "reading"}],
            learner_summary="Placement summary.",
            parent_summary="Parent placement summary.",
            allowed_next_actions=["start_curriculum"] if target_ready else ["start_recap"],
        )
    )
    return completed_row, report


@pytest.mark.parametrize("placement_status", ["target_ready", "below_target"])
def test_compatible_profile_edit_before_child_flow_inherits_immutable_report(
    store,
    placement_status,
):
    _seed_school_profile(store)
    client = TestClient(app)
    placement_row, report = _seed_completed_placement_report(
        store,
        client,
        placement_status,
    )

    edited_payload = {
        **_profile_payload(),
        "parent_goal": "Build a steady weekly reading habit.",
    }
    activation = _activate_school_profile(client, edited_payload)
    assert activation.status_code == 200
    intermediate_profile = activation.json()["profile"]
    second_activation = _activate_school_profile(
        client,
        {
            **edited_payload,
            "learner_goal": "Read new chapters independently each week.",
        },
    )
    assert second_activation.status_code == 200
    current_profile = second_activation.json()["profile"]
    assert current_profile["profile_version_id"] != intermediate_profile[
        "profile_version_id"
    ]

    state = client.get("/school/state", headers=AUTH)
    report_response = client.get("/school/placement/report", headers=AUTH)

    assert state.status_code == 200
    assert state.json()["profile_version_id"] == current_profile["profile_version_id"]
    assert state.json()["placement_status"] == placement_status
    assert report_response.status_code == 200
    assert report_response.json()["report_id"] == report["report_id"]
    persisted_report = _run(
        store.get_school_placement_report("test_user", placement_row["session_id"])
    )
    assert persisted_report["profile_version_id"] == placement_row["profile_version_id"]
    assert persisted_report["profile_version_id"] != current_profile["profile_version_id"]


def test_material_profile_edit_does_not_inherit_completed_placement_report(store):
    _seed_school_profile(store)
    client = TestClient(app)
    placement_row, report = _seed_completed_placement_report(
        store,
        client,
        "target_ready",
    )

    edited_payload = {
        **_profile_payload(),
        "preferred_teaching_language": "en",
    }
    activation = _activate_school_profile(client, edited_payload)
    assert activation.status_code == 200
    current_profile = activation.json()["profile"]

    state = client.get("/school/state", headers=AUTH)
    report_response = client.get("/school/placement/report", headers=AUTH)

    assert state.status_code == 200
    assert state.json()["profile_version_id"] == current_profile["profile_version_id"]
    assert state.json()["placement_status"] == "not_started"
    assert state.json()["next_action"] == "start_placement"
    assert report_response.status_code == 404
    persisted_report = _run(
        store.get_school_placement_report("test_user", placement_row["session_id"])
    )
    assert persisted_report["report_id"] == report["report_id"]
    assert persisted_report["profile_version_id"] == placement_row["profile_version_id"]
    assert persisted_report["profile_version_id"] != current_profile["profile_version_id"]


def test_school_placement_report_is_evidence_backed_and_does_not_leak_keys(store):
    _seed_school_profile(store)
    client = TestClient(app)
    placement_session_id = _complete_below_target_placement(client)

    response = client.get("/school/placement/report", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["placement_session_id"] == placement_session_id
    assert body["placement_status"] == "below_target"
    assert body["target_class_no"] == 3
    assert body["evaluated_class_no"] == 2
    assert body["unlock_state"] == "recap_required"
    assert body["allowed_next_actions"] == ["start_recap"]
    assert body["track_verdicts"]
    assert body["evidence_summary"]["total_attempts"] == 9
    assert body["evidence_summary"]["correct_attempts"] == 8
    assert body["blocking_skills"]
    assert all("skill_id" not in skill for skill in body["blocking_skills"])
    assert body["recommended_recap_modules"]
    assert all("placement_track_id" not in module for module in body["recommended_recap_modules"])
    assert all("primary_skill_id" not in module for module in body["recommended_recap_modules"])
    assert body["learner_summary"]
    assert body["parent_summary"]
    _assert_no_hidden_keys(body)

    saved = _run(store.get_school_placement_report("test_user", placement_session_id))
    assert saved is not None
    assert saved["placement_status"] == "below_target"
    assert saved["recommended_recap_modules"][0]["placement_track_id"].endswith(".word_roles")
    assert saved["recommended_recap_modules"][0]["primary_skill_id"] == "grammar.noun_verb_adjective"


def test_school_state_after_report_routes_to_readiness_report_before_recap(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_below_target_placement(client)
    report = client.get("/school/placement/report", headers=AUTH).json()

    state = client.get("/school/state", headers=AUTH).json()

    assert state["placement_status"] == "below_target"
    assert state["active_flow"] == "placement_report"
    assert state["active_session_id"] == report["placement_session_id"]
    assert state["unlock_state"] == "recap_required"
    assert state["next_action"] == "start_recap"
    assert state["next_action_url"] == "/school/recap"
    assert state["blocked_reason"] is None


def test_school_recap_start_uses_stored_report_and_creates_personalized_path(store):
    _seed_school_profile(store)
    client = TestClient(app)
    placement_session_id = _complete_below_target_placement(client)
    report = client.get("/school/placement/report", headers=AUTH).json()

    response = client.post("/school/recap/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["flow_type"] == "recap"
    assert body["status"] == "active"
    assert body["source_placement_report_id"] == report["report_id"]
    assert body["source_placement_session_id"] == placement_session_id
    assert body["target_class_no"] == 3
    assert body["active_learning_class_no"] == 2
    assert body["modules"]
    assert all(module["teaching_block"] for module in body["modules"])
    assert all(module["independent_check_label"] for module in body["modules"])
    assert all("skill_id" not in module for module in body["modules"])
    _assert_no_hidden_keys(body)

    state = client.get("/school/state", headers=AUTH).json()
    assert state["active_flow"] == "recap"
    assert state["active_session_id"] == body["session_id"]
    assert state["next_action"] == "resume_recap"
    assert state["next_action_url"] == f"/school/recap/{body['session_id']}"

    saved_recap = _run(store.get_school_session("test_user", body["session_id"]))
    assert saved_recap["profile_version_id"] == report["profile_version_id"]
    assert saved_recap["source_placement_report_id"] == report["report_id"]
    assert saved_recap["linked_session_id"] == placement_session_id


def test_old_report_and_completed_recap_do_not_unlock_replacement_profile(store):
    _seed_school_profile(store)
    client = TestClient(app)
    placement_session_id = _complete_below_target_placement(client)
    report = client.get("/school/placement/report", headers=AUTH).json()
    recap_body = client.post("/school/recap/start", headers=AUTH).json()
    recap_row = _run(store.get_school_session("test_user", recap_body["session_id"]))
    _run(
        store.upsert_school_session(
            **{
                **recap_row,
                "status": "complete",
                "state_json": {**recap_row["state_json"], "status": "complete"},
            }
        )
    )

    replacement_payload = _profile_payload()
    replacement_payload["preferred_teaching_language"] = "en"
    replacement = _activate_school_profile(client, replacement_payload)

    assert replacement.status_code == 200
    new_profile_id = replacement.json()["profile"]["profile_version_id"]
    assert new_profile_id != report["profile_version_id"]
    old_report = _run(
        store.get_school_placement_report(
            "test_user",
            placement_session_id,
            profile_version_id=report["profile_version_id"],
        )
    )
    assert old_report is not None

    state = client.get("/school/state", headers=AUTH).json()
    assert state["profile_version_id"] == new_profile_id
    assert state["unlock_state"] == "locked"
    assert state["next_action"] == "start_placement"
    old_recap_get = client.get(
        f"/school/recap/{recap_body['session_id']}", headers=AUTH
    )
    assert old_recap_get.status_code == 404
    old_recap_answer = client.post(
        f"/school/recap/{recap_body['session_id']}/answer",
        headers=AUTH,
        json={"activity_id": "old-profile-activity", "answer": "old profile answer"},
    )
    assert old_recap_answer.status_code == 404
    locked = client.post("/school/curriculum/start", headers=AUTH)
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "curriculum_locked"


def test_same_profile_obsolete_report_recap_direct_routes_return_not_found(store):
    _seed_school_profile(store)
    client = TestClient(app)
    placement_session_id = _complete_below_target_placement(client)
    report = client.get("/school/placement/report", headers=AUTH).json()
    recap_body = client.post("/school/recap/start", headers=AUTH).json()
    _replace_placement_report_same_profile(
        store,
        old_placement_session_id=placement_session_id,
        old_report=_run(
            store.get_school_placement_report("test_user", placement_session_id)
        ),
    )

    old_get = client.get(f"/school/recap/{recap_body['session_id']}", headers=AUTH)
    old_answer = client.post(
        f"/school/recap/{recap_body['session_id']}/answer",
        headers=AUTH,
        json={
            "activity_id": recap_body["current_activity"]["activity_id"],
            "answer": "teacher",
        },
    )

    assert report["report_id"] != "same-profile-new-report"
    assert old_get.status_code == 404
    assert old_answer.status_code == 404
