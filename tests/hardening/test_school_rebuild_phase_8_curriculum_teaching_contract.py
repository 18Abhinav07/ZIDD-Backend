import asyncio
import copy
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_v3_schema import (
    SchoolV3RubricCriterion,
    SchoolV3RubricEvaluation,
)
from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_placement as placement
from app.services import school_rebuild_recap as recap
from app.services.school import evaluation_jobs
from app.services.school_core.readiness import (
    SkillReadinessState,
    to_profile_upsert,
)

AUTH = {"Authorization": "Bearer test_token"}
_REAL_SCHOOL_OPEN_ANSWER_WITH_HEARTBEAT = (
    school_rebuild_routes._evaluate_school_open_answer_with_claim_heartbeat
)

RAINBOW_JOURNEY_PARAGRAPH = (
    "Last Sunday I travelled to Jaipur by train with my parents. We left home early and reached "
    "the station before sunrise. During the journey I watched green fields, small villages, and bright "
    "birds through the window. We visited the fort, tasted warm kachori, and walked through a busy "
    "market. I liked the colourful shops and the view from the fort, but I disliked the afternoon heat. "
    "In the evening we returned home tired, happy, and excited to share our photographs."
)

WISE_PARROT_STORY_CONTINUATION = (
    "After escaping from the golden cage, the parrot flew towards the forest and found its wise friend. "
    "It thanked the friend for showing a clever way to become free. The two birds visited the merchant "
    "garden the next morning. The parrot explained that love should not keep anyone trapped. The merchant "
    "felt sorry, opened the empty cage, and filled a feeder with fruit. From then on, many birds visited "
    "him freely, and he enjoyed their songs."
)

PLACEMENT_STRONG_SUMMARY_ANSWERS = {
    "spv_c05_t08_v01": (
        "A storm blocked the lane, so residents cut the fallen branches "
        "and reopened a path."
    ),
    "spv_c05_t08_v02": (
        "The school checked its power costs, installed solar panels, and "
        "used the money saved to buy library books."
    ),
    "spv_c05_t08_v03": (
        "The children contacted rescuers and kept the area calm while the "
        "injured bird waited for help."
    ),
    "spv_c05_t08_v04": (
        "Students studied dangerous bus stops and proposed three safer "
        "changes to the transport office."
    ),
    "spv_c05_t08_v05": (
        "Testing found harmful bacteria in one clear-looking water sample, "
        "so that sample needed treatment."
    ),
}


@pytest.fixture(autouse=True)
def _stub_school_open_answer_evaluator(monkeypatch):
    async def evaluate(
        activity: dict[str, Any] | None = None,
        answer: str | None = None,
        **_kwargs,
    ) -> SchoolV3RubricEvaluation:
        activity = activity or _kwargs["activity"]
        answer = str(answer if answer is not None else _kwargs["answer"])
        concept_slots = {
            slot["id"]: tuple(slot["any_of"])
            for slot in activity.get("concept_slots") or []
        }

        def evidence_quote(criterion_id: str) -> str:
            slot_id = {
                "plausible_inference": "inference_claim",
                "relevant_text_clue": "passage_clue",
            }.get(criterion_id)
            if slot_id is not None:
                for alias in concept_slots.get(slot_id, ()):
                    start = answer.casefold().find(alias.casefold())
                    if start >= 0:
                        return answer[start : start + len(alias)]
            return answer.strip() or "(empty answer)"

        return SchoolV3RubricEvaluation(
            schema_version=(
                "school.open.v1"
                if activity.get("grading_mode") == "strict_open_rubric"
                else "school-v3-rubric-1"
            ),
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=evidence_quote(criterion["id"]),
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        evaluate,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluate,
    )


def _run(coro):
    return asyncio.run(coro)


def _profile_payload(*, target_class_no: int = 3) -> dict:
    return {
        "display_name": "Open Assets Learner",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": target_class_no,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": f"I want to understand Class {target_class_no} English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": ["reading", "vocabulary"],
    }


def _activate_school_profile(client: TestClient, payload: dict):
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


def _seed_school_profile(store, *, target_class_no: int = 3) -> dict[str, Any]:
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    response = _activate_school_profile(
        TestClient(app),
        _profile_payload(target_class_no=target_class_no),
    )
    assert response.status_code == 200
    return response.json()["profile"]


def _seed_direct_curriculum_report_lineage(store, profile: dict[str, Any]) -> None:
    envelope = placement.new_placement_envelope(profile)
    for _ in range(30):
        item = placement.next_item(envelope)
        if item is None:
            break
        envelope = placement.apply_answer(envelope, item, "wrong")
    placement_status = placement.placement_status(envelope)
    assert placement_status != "in_progress"
    placement_session_id = "direct-curriculum-placement"
    session = {
        "session_id": placement_session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "placement",
        "subject_id": "english",
        "class_no": int(profile["target_class_no"]),
        "current_stage": envelope.state.stage,
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": None,
        "state_json": placement.envelope_to_json(envelope),
    }
    _run(
        store.upsert_school_session(
            **session,
            status="active",
        )
    )
    _run(
        store.upsert_school_session(
            **session,
            status=placement_status,
        )
    )
    _run(
        store.upsert_school_placement_report(
            report_id="placement-report",
            user_id="test_user",
            profile_version_id=profile["profile_version_id"],
            placement_session_id=placement_session_id,
            subject_id="english",
            target_class_no=int(profile["target_class_no"]),
            evaluated_class_no=int(profile["target_class_no"]),
            placement_status="target_ready",
            unlock_state="target_unlocked",
        )
    )


def _complete_weak_placement(client: TestClient) -> None:
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
        assert response.status_code == 200, response.text
        current = response.json()
    assert current["status"] == "below_target"


def _private_recap_activity_for_current_body(body: dict[str, Any]) -> dict[str, Any]:
    public_activity = body.get("current_activity") or {}
    session_id = str(body.get("session_id") or "")
    activity_id = str(public_activity.get("activity_id") or "")
    assert session_id and activity_id, body
    session = _run(
        school_rebuild_routes.get_storage().get_school_session(
            "test_user",
            session_id,
        )
    )
    assert session is not None
    return recap.recap_activity_for_answer(
        dict(session["state_json"]),
        activity_id=activity_id,
    )


def _settle_queued_recap_answer(
    response,
    *,
    body: dict[str, Any],
    client: TestClient,
):
    if response.status_code != 202:
        return response
    session_id = str(body["session_id"])
    activity_id = str(body["current_activity"]["activity_id"])
    store = school_rebuild_routes.get_storage()
    assert _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    ) is True
    job = _run(store.get_school_evaluation_job("test_user", session_id, activity_id))
    assert job is not None
    assert job["status"] == "completed", (
        activity_id,
        job.get("last_error_code"),
        job.get("error_json"),
    )
    settled = client.get(f"/school/recap/{session_id}", headers=AUTH)
    assert settled.status_code == 200, settled.text
    return settled


def _complete_recap_success_path(client: TestClient) -> dict:
    _complete_weak_placement(client)
    assert client.get("/school/placement/report", headers=AUTH).status_code == 200
    body = client.post("/school/recap/start", headers=AUTH).json()
    session_id = body["session_id"]
    guard = 0
    while body["current_activity"] is not None:
        guard += 1
        assert guard <= 40
        activity = body["current_activity"]
        response = client.post(
            f"/school/recap/{session_id}/answer",
            headers=AUTH,
            json={
                "activity_id": activity["activity_id"],
                "answer": _correct_private_curriculum_answer(
                    _private_recap_activity_for_current_body(body)
                ),
            },
        )
        response = _settle_queued_recap_answer(
            response,
            body=body,
            client=client,
        )
        assert response.status_code == 200, response.text
        body = response.json()
    assert body["status"] == "complete"
    return body


def _complete_target_ready_placement(client: TestClient) -> dict:
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    guard = 0
    while current["next_item"] is not None:
        guard += 1
        assert guard <= 20
        item = current["next_item"]
        saved = _run(
            school_rebuild_routes.get_storage().get_school_session(
                "test_user",
                session_id,
            )
        )
        private_item = placement.find_item(
            placement.envelope_from_json(saved["state_json"]),
            item["item_id"],
        )
        answer = (
            private_item.answer_key
            or next(iter(private_item.accepted_answers), None)
            or PLACEMENT_STRONG_SUMMARY_ANSWERS.get(private_item.item_id)
            or " because ".join(
                slot.aliases[0] for slot in private_item.semantic_claim_slots
            )
        )
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": answer},
        )
        assert response.status_code == 200, response.text
        current = response.json()
    assert current["status"] == "target_ready", current
    report = client.get("/school/placement/report", headers=AUTH)
    assert report.status_code == 200
    body = report.json()
    assert body["placement_status"] == "target_ready"
    assert body["unlock_state"] == "target_unlocked"
    return body


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {
        "answer_key",
        "answer_rule",
        "accepted_answers",
        "model_answer",
        "rubric",
        "rubric_criteria",
        "pass_score",
        "evaluation_mode",
        "preflight_rule",
        "threshold",
        "skill_scores",
        "weak_skill_ids",
        "remediation_skill_ids",
        "failed_rubric_item_ids",
        "failed_hard_blocker_item_ids",
    }
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def _authored_chapter_for_public_session(body: dict[str, Any]) -> dict[str, Any]:
    chapter_id = str((body.get("chapter") or {}).get("chapter_id") or "")
    subject_id = str(body.get("subject_id") or "english")
    class_no = int(body.get("target_class_no") or 0)
    chapter = next(
        (
            candidate
            for candidate in curriculum._available_chapters(subject_id, class_no)
            if candidate["chapter_id"] == chapter_id
        ),
        None,
    )
    assert chapter is not None, body
    return chapter


def _assert_current_activity_matches_catalog(body: dict[str, Any]) -> None:
    chapter = _authored_chapter_for_public_session(body)
    activity = body.get("current_activity") or {}
    assert chapter["levels"], chapter["chapter_id"]
    progress = dict(body.get("progress") or {})
    current_level_index = int(progress.get("current_level_index") or 0)
    assert 0 <= current_level_index < len(chapter["levels"]), progress
    expected_level = chapter["levels"][current_level_index]
    assert activity.get("level_id") == expected_level["level_id"]

    teaching_steps = list(expected_level.get("teaching_steps") or [])
    authored_phases = {
        str(step.get("phase") or "")
        for step in teaching_steps
        if isinstance(step, dict) and str(step.get("phase") or "")
    }
    assert activity["phase"] in authored_phases
    assert activity["activity_id"].startswith(f"{expected_level['level_id']}:")
    assert activity["kind"].startswith("v2_")
    assert str(activity.get("teaching_block") or "").strip()
    assert str(activity.get("prompt") or "").strip()

    declared_activity_anchor_ids = list(activity.get("source_anchor_ids") or [])
    public_anchor_ids = [
        str(anchor["anchor_id"])
        for anchor in activity.get("source_reference", {}).get("anchors") or []
    ]
    assert public_anchor_ids == declared_activity_anchor_ids, activity

    certification_anchor_ids = set(expected_level.get("source_anchor_ids") or [])
    companion_anchor_ids = set(
        expected_level.get("companion_source_anchor_ids") or []
    )
    assert set(declared_activity_anchor_ids).issubset(
        certification_anchor_ids | companion_anchor_ids
    ), activity
    if activity.get("evidence_role") == "certifying":
        assert not set(declared_activity_anchor_ids).intersection(
            companion_anchor_ids
        ), activity


def _assert_empty_chapter_progress(body: dict[str, Any]) -> None:
    chapter = _authored_chapter_for_public_session(body)
    assert body["progress"] == {
        "completed_levels": 0,
        "total_levels": len(chapter["levels"]),
        "current_level_index": 0,
    }


def _seed_certification_repair_session(
    store,
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    session_id = str(uuid4())
    old_state = {
        "engine_version": "school-rebuild-curriculum-2",
        "status": "active",
        "phase": "needs_support",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 5,
        "chapter": {
            "chapter_id": "eng_c5_ch01",
            "chapter_no": 1,
            "title": "Papa's Spectacles",
            "content_version": "chapter-v1",
            "certification_version": "certification-v1",
        },
        "levels": [],
        "completed_chapter_ids": [],
        "chapter_assessment": {"attempt_history": []},
        "support_required": {"reason": "chapter_check_attempts_exhausted"},
    }
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="chapter_check",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=old_state,
        )
    )
    repaired_state = {
        **old_state,
        "engine_version": curriculum.ENGINE_VERSION,
        "status": "complete",
        "phase": "complete",
        "completed_chapter_ids": ["eng_c5_ch01"],
        "support_required": None,
        "chapter_assessment": {
            "attempt_history": [
                {
                    "attempt_no": 2,
                    "score": 0.99,
                    "passed": True,
                    "skill_scores": {
                        "reading.paragraph_main_idea": 1.0,
                        "writing.summary_own_words": 0.98,
                    },
                }
            ]
        },
        "last_feedback": {
            "activity_id": "eng_c5_ch01:chapter_check:final",
            "level_id": "chapter_assessment",
            "kind": "chapter_check",
            "correct": True,
            "result_visible": True,
            "message": "Chapter check passed. The next chapter is ready.",
        },
    }
    repair = {
        "kind": "chapter_certification_reconciled",
        "chapter_id": "eng_c5_ch01",
        "attempt_no": 2,
        "skill_scores": {
            "reading.paragraph_main_idea": 1.0,
            "writing.summary_own_words": 0.98,
        },
    }
    repaired_state["state_reconciliations"] = [{
        "from_engine_version": "school-rebuild-curriculum-2",
        "to_engine_version": curriculum.ENGINE_VERSION,
        **repair,
    }]
    return session_id, old_state, repaired_state, repair


def test_curriculum_read_reconciles_saved_certification_once(store, monkeypatch):
    session_id, old_state, repaired_state, repair = _seed_certification_repair_session(
        store
    )

    def reconcile(state):
        if state.get("engine_version") == curriculum.ENGINE_VERSION:
            return state, None
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)
    client = TestClient(app)
    cas_calls = 0
    original_compare_and_set = store.compare_and_set_school_session

    async def count_compare_and_set(**kwargs):
        nonlocal cas_calls
        cas_calls += 1
        return await original_compare_and_set(**kwargs)

    monkeypatch.setattr(store, "compare_and_set_school_session", count_compare_and_set)

    first = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    second = client.get(f"/school/curriculum/{session_id}", headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert cas_calls == 1
    assert first.json()["status"] == "complete"
    assert first.json()["phase"] == "complete"
    saved = _run(store.get_school_session("test_user", session_id))
    assert saved["status"] == "complete"
    assert saved["state_json"]["engine_version"] == curriculum.ENGINE_VERSION
    profiles = {
        row["skill_id"]: row
        for row in _run(store.get_school_learning_graph("test_user"))["profiles"]
    }
    for skill_id, score in (
        ("reading.paragraph_main_idea", 1.0),
        ("writing.summary_own_words", 0.98),
    ):
        profile_row = profiles[skill_id]
        assert profile_row["mastery"] == 0.0
        assert profile_row["readiness"] == 0.0
        assert profile_row["attempts"] == 0
        assert profile_row["evidence_json"]["latest_certification"] == {
            "session_id": session_id,
            "chapter_id": "eng_c5_ch01",
            "score": score,
        }


def test_curriculum_read_backfills_legacy_matching_certification_ledger_once(
    store,
    monkeypatch,
):
    session_id, old_state, repaired_state, _repair = _seed_certification_repair_session(
        store
    )
    career_profile = {
        "target_roles": ["Data Analyst"],
        "interview_goals": ["Explain projects clearly"],
    }
    _run(store.complete_onboarding(
        user_id="test_user",
        display_name="Open Assets",
        primary_motive="school",
        school_profile={},
        career_profile=career_profile,
    ))
    career_before = copy.deepcopy(_run(store.get_profile("test_user"))["career_profile"])
    _run(school_rebuild_routes.SchoolLearningProfileService(
        store
    ).record_curriculum_attempt(
        user_id="test_user",
        session_id=session_id,
        chapter_id="eng_c5_ch01",
        level_id="chapter_assessment",
        focus="legacy chapter certification",
        skill_ids=[
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
        ],
        attempt_type="chapter_check",
        score=1.0,
        confidence=1.0,
        criteria=[],
        blockers=[],
        answer_excerpt="A legacy certified answer.",
        attempt_passed=True,
        chapter_certified=True,
    ))
    for profile in _run(store.get_school_learning_graph("test_user"))["profiles"]:
        if profile["skill_id"] == "writing.summary_own_words":
            profile["evidence_json"]["latest_certification"]["score"] = 0.98
    row = _run(store.get_school_session("test_user", session_id))
    assert _run(store.compare_and_set_school_session(
        school_session={
            **row,
            "status": "complete",
            "current_stage": "complete",
            "state_json": repaired_state,
        },
        expected_state_json=old_state,
    ))
    projection_attempts = 0
    original_projection = (
        school_rebuild_routes.SchoolLearningProfileService.record_chapter_certification
    )

    async def count_projection(self, **kwargs):
        nonlocal projection_attempts
        projection_attempts += 1
        return await original_projection(self, **kwargs)

    monkeypatch.setattr(
        school_rebuild_routes.SchoolLearningProfileService,
        "record_chapter_certification",
        count_projection,
    )

    client = TestClient(app)
    first = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    second = client.get(f"/school/curriculum/{session_id}", headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert projection_attempts == 1
    profiles = _run(store.get_school_learning_graph("test_user"))["profiles"]
    for skill_id, score in (
        ("reading.paragraph_main_idea", 1.0),
        ("writing.summary_own_words", 0.98),
    ):
        evidence = next(
            row["evidence_json"] for row in profiles if row["skill_id"] == skill_id
        )
        assert evidence["latest_certification"] == {
            "session_id": session_id,
            "chapter_id": "eng_c5_ch01",
            "score": score,
        }
        assert evidence["reconciliation_certification_ledger"][
            f"{session_id}:eng_c5_ch01"
        ] == evidence["latest_certification"]
    assert _run(store.get_profile("test_user"))["career_profile"] == career_before


def test_curriculum_post_retries_failed_certification_projection_without_another_cas(
    store,
    monkeypatch,
):
    session_id, _old_state, repaired_state, repair = _seed_certification_repair_session(
        store
    )

    def reconcile(state):
        if state.get("engine_version") == curriculum.ENGINE_VERSION:
            return state, None
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)
    cas_calls = 0
    projection_attempts = 0
    original_compare_and_set = store.compare_and_set_school_session
    original_projection = (
        school_rebuild_routes.SchoolLearningProfileService.record_chapter_certification
    )

    async def count_compare_and_set(**kwargs):
        nonlocal cas_calls
        cas_calls += 1
        return await original_compare_and_set(**kwargs)

    async def fail_first_projection(self, **kwargs):
        nonlocal projection_attempts
        projection_attempts += 1
        if projection_attempts == 1:
            raise RuntimeError("injected_certification_projection_failure")
        return await original_projection(self, **kwargs)

    monkeypatch.setattr(store, "compare_and_set_school_session", count_compare_and_set)
    monkeypatch.setattr(
        school_rebuild_routes.SchoolLearningProfileService,
        "record_chapter_certification",
        fail_first_projection,
    )
    activity_id = "eng_c5_ch01:chapter_check:final"
    answer = "The learner's final answer."
    store.school_answer_requests[(session_id, activity_id)] = {
        "user_id": "test_user",
        "answer_hash": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "claim_token": "historical-final-answer",
        "status": "completed",
        "response_json": {
            "session_id": session_id,
            "status": "active",
            "phase": "needs_support",
        },
        "updated_at": time.time(),
    }
    persist_calls = 0
    evaluator_calls = 0
    original_persist = store.persist_school_curriculum_attempt
    original_evaluator = (
        school_rebuild_routes._evaluate_school_open_answer_with_claim_heartbeat
    )

    async def count_persist(**kwargs):
        nonlocal persist_calls
        persist_calls += 1
        return await original_persist(**kwargs)

    async def count_evaluator(**kwargs):
        nonlocal evaluator_calls
        evaluator_calls += 1
        return await original_evaluator(**kwargs)

    monkeypatch.setattr(store, "persist_school_curriculum_attempt", count_persist)
    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        count_evaluator,
    )

    client = TestClient(app)
    first = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": answer},
    )
    second = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": answer},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "complete"
    assert second.json()["status"] == "complete"
    assert cas_calls == 1
    assert projection_attempts == 2
    assert persist_calls == 0
    assert evaluator_calls == 0
    profiles = _run(store.get_school_learning_graph("test_user"))["profiles"]
    certified_profiles = [
        row
        for row in profiles
        if row.get("evidence_json", {})
        .get("reconciliation_certification_ledger", {})
        .get(f"{session_id}:eng_c5_ch01", {})
        .get("session_id")
        == session_id
    ]
    assert len(certified_profiles) == 2
    assert {row["skill_id"] for row in certified_profiles} == {
        "reading.paragraph_main_idea",
        "writing.summary_own_words",
    }


def test_curriculum_get_retries_failed_certification_projection_without_another_cas(
    store,
    monkeypatch,
):
    session_id, _old_state, repaired_state, repair = _seed_certification_repair_session(
        store
    )

    def reconcile(state):
        if state.get("engine_version") == curriculum.ENGINE_VERSION:
            return state, None
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)
    cas_calls = 0
    projection_attempts = 0
    original_compare_and_set = store.compare_and_set_school_session
    original_projection = (
        school_rebuild_routes.SchoolLearningProfileService.record_chapter_certification
    )

    async def count_compare_and_set(**kwargs):
        nonlocal cas_calls
        cas_calls += 1
        return await original_compare_and_set(**kwargs)

    async def fail_first_projection(self, **kwargs):
        nonlocal projection_attempts
        projection_attempts += 1
        if projection_attempts == 1:
            raise RuntimeError("injected_certification_projection_failure")
        return await original_projection(self, **kwargs)

    monkeypatch.setattr(store, "compare_and_set_school_session", count_compare_and_set)
    monkeypatch.setattr(
        school_rebuild_routes.SchoolLearningProfileService,
        "record_chapter_certification",
        fail_first_projection,
    )

    client = TestClient(app)
    first = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    second = client.get(f"/school/curriculum/{session_id}", headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert cas_calls == 1
    assert projection_attempts == 2
    certified_profiles = [
        row
        for row in _run(store.get_school_learning_graph("test_user"))["profiles"]
        if row.get("evidence_json", {})
        .get("reconciliation_certification_ledger", {})
        .get(f"{session_id}:eng_c5_ch01", {})
        .get("session_id")
        == session_id
    ]
    assert len(certified_profiles) == 2
    assert {row["skill_id"] for row in certified_profiles} == {
        "reading.paragraph_main_idea",
        "writing.summary_own_words",
    }


def test_curriculum_recovery_ignores_completed_state_without_repair_provenance(
    store,
    monkeypatch,
):
    session_id, old_state, repaired_state, _repair = _seed_certification_repair_session(
        store
    )
    ordinary_complete_state = {
        **repaired_state,
        "state_reconciliations": [],
    }
    row = _run(store.get_school_session("test_user", session_id))
    assert _run(
        store.compare_and_set_school_session(
            school_session={
                **row,
                "status": "complete",
                "current_stage": "complete",
                "state_json": ordinary_complete_state,
            },
            expected_state_json=old_state,
        )
    )
    projection_attempts = 0
    original_projection = (
        school_rebuild_routes.SchoolLearningProfileService.record_chapter_certification
    )

    async def count_projection(self, **kwargs):
        nonlocal projection_attempts
        projection_attempts += 1
        return await original_projection(self, **kwargs)

    monkeypatch.setattr(
        school_rebuild_routes.SchoolLearningProfileService,
        "record_chapter_certification",
        count_projection,
    )

    response = TestClient(app).get(
        f"/school/curriculum/{session_id}",
        headers=AUTH,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert projection_attempts == 0
    assert _run(store.get_school_learning_graph("test_user"))["profiles"] == []


def test_curriculum_recovery_preserves_newer_latest_certification(store, monkeypatch):
    session_id, old_state, repaired_state, _repair = _seed_certification_repair_session(
        store
    )
    newer_session_id = "newer-certified-session"
    newer_chapter_id = "eng_c5_ch02"
    newer_score = 0.97
    _run(
        school_rebuild_routes.SchoolLearningProfileService(
            store
        ).record_curriculum_attempt(
            user_id="test_user",
            session_id=newer_session_id,
            chapter_id=newer_chapter_id,
            level_id="chapter_assessment",
            focus="newer chapter check",
            skill_ids=["reading.paragraph_main_idea"],
            attempt_type="chapter_check",
            score=newer_score,
            confidence=1.0,
            criteria=[],
            blockers=[],
            answer_excerpt="A newer certified answer.",
            attempt_passed=True,
            chapter_certified=True,
        )
    )
    row = _run(store.get_school_session("test_user", session_id))
    assert _run(
        store.compare_and_set_school_session(
            school_session={
                **row,
                "status": "complete",
                "current_stage": "complete",
                "state_json": repaired_state,
            },
            expected_state_json=old_state,
        )
    )
    projection_attempts = 0
    original_projection = (
        school_rebuild_routes.SchoolLearningProfileService.record_chapter_certification
    )

    async def count_projection(self, **kwargs):
        nonlocal projection_attempts
        projection_attempts += 1
        return await original_projection(self, **kwargs)

    monkeypatch.setattr(
        school_rebuild_routes.SchoolLearningProfileService,
        "record_chapter_certification",
        count_projection,
    )
    client = TestClient(app)

    first = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    second = client.get(f"/school/curriculum/{session_id}", headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert projection_attempts == 1
    profile = _run(store.get_school_learning_graph("test_user"))["profiles"]
    reading = next(
        row for row in profile if row["skill_id"] == "reading.paragraph_main_idea"
    )
    evidence = reading["evidence_json"]
    assert evidence["latest_certification"] == {
        "session_id": newer_session_id,
        "chapter_id": newer_chapter_id,
        "score": newer_score,
    }
    assert evidence["reconciliation_certification_ledger"][
        f"{session_id}:eng_c5_ch01"
    ] == {
        "session_id": session_id,
        "chapter_id": "eng_c5_ch01",
        "score": 1.0,
    }


def test_curriculum_answer_reconciles_stale_certification_to_completed_response(
    store,
    monkeypatch,
):
    session_id, _old_state, repaired_state, repair = _seed_certification_repair_session(
        store
    )

    def reconcile(_state):
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "eng_c5_ch01:chapter_check:final",
            "answer": "The learner's final answer.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert response.json()["phase"] == "complete"
    _assert_no_hidden_keys(response.json())
    assert not store.school_answer_requests
    assert not store.learning_events


def test_curriculum_duplicate_final_answer_returns_reconciled_completed_response(
    store,
    monkeypatch,
):
    session_id, _old_state, repaired_state, repair = _seed_certification_repair_session(
        store
    )
    activity_id = "eng_c5_ch01:chapter_check:final"
    answer = "The learner's final answer."
    answer_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    stale_response = {
        "session_id": session_id,
        "status": "active",
        "phase": "needs_support",
        "current_activity": None,
    }
    store.school_answer_requests[(session_id, activity_id)] = {
        "user_id": "test_user",
        "answer_hash": answer_hash,
        "claim_token": "historical-final-answer",
        "status": "completed",
        "response_json": stale_response,
        "updated_at": time.time(),
    }

    def reconcile(state):
        if state.get("engine_version") == curriculum.ENGINE_VERSION:
            return state, None
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)
    cas_calls = 0
    persist_calls = 0
    evaluator_calls = 0
    original_compare_and_set = store.compare_and_set_school_session
    original_persist = store.persist_school_curriculum_attempt
    original_evaluator = (
        school_rebuild_routes._evaluate_school_open_answer_with_claim_heartbeat
    )

    async def count_compare_and_set(**kwargs):
        nonlocal cas_calls
        cas_calls += 1
        return await original_compare_and_set(**kwargs)

    async def count_persist(**kwargs):
        nonlocal persist_calls
        persist_calls += 1
        return await original_persist(**kwargs)

    async def count_evaluator(**kwargs):
        nonlocal evaluator_calls
        evaluator_calls += 1
        return await original_evaluator(**kwargs)

    monkeypatch.setattr(store, "compare_and_set_school_session", count_compare_and_set)
    monkeypatch.setattr(store, "persist_school_curriculum_attempt", count_persist)
    monkeypatch.setattr(
        school_rebuild_routes,
        "_evaluate_school_open_answer_with_claim_heartbeat",
        count_evaluator,
    )

    client = TestClient(app)
    repaired = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    replay = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": answer},
    )

    assert repaired.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["status"] == "complete"
    assert replay.json()["phase"] == "complete"
    assert replay.json() != stale_response
    assert cas_calls == 1
    assert persist_calls == 0
    assert evaluator_calls == 0
    _assert_no_hidden_keys(replay.json())


def test_curriculum_only_canonicalizes_the_reconciled_final_answer_replay(
    store,
    monkeypatch,
):
    session_id, _old_state, repaired_state, repair = _seed_certification_repair_session(
        store
    )
    final_activity_id = "eng_c5_ch01:chapter_check:final"
    final_answer = "The learner's final answer."
    earlier_activity_id = "eng_c5_ch01:chapter_check:earlier"
    earlier_answer = "The learner's earlier answer."
    final_cached_response = {
        "session_id": session_id,
        "status": "active",
        "phase": "needs_support",
    }
    earlier_cached_response = {
        "session_id": session_id,
        "status": "active",
        "phase": "learning",
        "replay_marker": "earlier-completed-answer",
    }
    store.school_answer_requests[(session_id, final_activity_id)] = {
        "user_id": "test_user",
        "answer_hash": hashlib.sha256(final_answer.encode("utf-8")).hexdigest(),
        "claim_token": "historical-final-answer",
        "status": "completed",
        "response_json": final_cached_response,
        "updated_at": time.time(),
    }
    store.school_answer_requests[(session_id, earlier_activity_id)] = {
        "user_id": "test_user",
        "answer_hash": hashlib.sha256(earlier_answer.encode("utf-8")).hexdigest(),
        "claim_token": "historical-earlier-answer",
        "status": "completed",
        "response_json": earlier_cached_response,
        "updated_at": time.time(),
    }

    def reconcile(state):
        if state.get("engine_version") == curriculum.ENGINE_VERSION:
            return state, None
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)
    client = TestClient(app)

    final = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": final_activity_id, "answer": final_answer},
    )
    conflict = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": final_activity_id, "answer": "A conflicting answer."},
    )
    earlier = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": earlier_activity_id, "answer": earlier_answer},
    )

    assert final.status_code == 200
    assert final.json()["status"] == "complete"
    assert final.json()["phase"] == "complete"
    assert final.json() != final_cached_response
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "curriculum_answer_conflict"
    assert earlier.status_code == 200
    assert earlier.json() == earlier_cached_response
    _assert_no_hidden_keys(final.json())


def _seed_stale_ordinary_curriculum_session(store, *, session_id: str) -> dict[str, Any]:
    chapter = next(
        item
        for item in curriculum._available_chapters("english", 5)
        if item["chapter_id"] == "eng_c5_ch01"
    )
    current_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
        level_id="papas_spectacles_poem_comprehension",
    )
    stale_state = copy.deepcopy(current_state)
    stale_state["engine_version"] = "school-rebuild-curriculum-4"
    row = _run(store.get_school_session("test_user", session_id))
    changed = _run(
        store.compare_and_set_school_session(
            school_session={**row, "state_json": stale_state},
            expected_state_json=current_state,
        )
    )
    assert changed is True
    return stale_state


def test_curriculum_read_reconciles_ordinary_state_without_cas(store, monkeypatch):
    session_id = str(uuid4())
    stale_state = _seed_stale_ordinary_curriculum_session(
        store,
        session_id=session_id,
    )
    persisted_before = _run(store.get_school_session("test_user", session_id))
    canonical_state, repair = curriculum.reconcile_curriculum_state(stale_state)
    assert repair is None
    expected = curriculum.public_curriculum_response(
        {**persisted_before, "state_json": canonical_state}
    )
    cas_calls = 0
    original_compare_and_set = store.compare_and_set_school_session

    async def count_compare_and_set(**kwargs):
        nonlocal cas_calls
        cas_calls += 1
        return await original_compare_and_set(**kwargs)

    monkeypatch.setattr(store, "compare_and_set_school_session", count_compare_and_set)

    response = TestClient(app).get(
        f"/school/curriculum/{session_id}",
        headers=AUTH,
    )

    assert response.status_code == 200
    body = response.json()
    for key in ("status", "phase", "progress", "levels", "current_activity"):
        assert body[key] == expected[key]
    assert cas_calls == 0
    persisted_after = _run(store.get_school_session("test_user", session_id))
    assert persisted_after["state_json"] == stale_state
    assert persisted_after["state_json"]["engine_version"] == "school-rebuild-curriculum-4"


def test_curriculum_answer_from_stale_ordinary_state_persists_current_engine(
    store,
    monkeypatch,
):
    session_id = str(uuid4())
    stale_state = _seed_stale_ordinary_curriculum_session(
        store,
        session_id=session_id,
    )
    client = TestClient(app)
    read = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    assert read.status_code == 200
    activity = read.json()["current_activity"]
    captured_persist: dict[str, Any] = {}
    persist_calls = 0
    original_persist = store.persist_school_curriculum_attempt
    evaluator_calls = 0

    async def capture_persist(**kwargs):
        nonlocal persist_calls
        persist_calls += 1
        captured_persist.update(copy.deepcopy(kwargs))
        return await original_persist(**kwargs)

    async def count_evaluator(activity, answer, **_kwargs):
        nonlocal evaluator_calls
        evaluator_calls += 1
        return SchoolV3RubricEvaluation(
            schema_version=(
                "school.open.v1"
                if activity.get("grading_mode") == "strict_open_rubric"
                else "school-v3-rubric-1"
            ),
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer,
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(store, "persist_school_curriculum_attempt", capture_persist)
    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        count_evaluator,
    )
    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)

    payload = {
        "activity_id": activity["activity_id"],
        "answer": "I used the chapter details to explain my answer.",
    }
    queued = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json=payload,
    )
    in_progress = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json=payload,
    )

    assert queued.status_code == 202
    assert in_progress.status_code == 409
    assert in_progress.json()["detail"]["code"] == "curriculum_answer_in_progress"
    assert persist_calls == 0
    assert evaluator_calls == 0
    queued_job = _run(
        store.get_school_evaluation_job(
            "test_user", session_id, activity["activity_id"]
        )
    )
    persisted_before_worker = _run(store.get_school_session("test_user", session_id))
    assert queued_job["expected_state_json"] == persisted_before_worker["state_json"]

    processed = _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    )
    assert processed is True
    job = _run(
        store.get_school_evaluation_job(
            "test_user", session_id, activity["activity_id"]
        )
    )
    assert job["status"] == "completed", (
        job.get("last_error_code"),
        job.get("error_json"),
    )

    replay = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json=payload,
    )

    assert replay.status_code == 200
    assert persist_calls == 1
    assert evaluator_calls == 1
    assert captured_persist["expected_state_json"] == stale_state
    assert captured_persist["evaluation_job_completion"] is not None
    assert (
        captured_persist["school_session"]["state_json"]["engine_version"]
        == curriculum.ENGINE_VERSION
    )
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"]["engine_version"] == curriculum.ENGINE_VERSION


def test_curriculum_answer_uses_matching_canonical_snapshot_without_legacy_reads(
    store,
    monkeypatch,
):
    session_id = str(uuid4())
    chapter = next(
        item
        for item in curriculum._available_chapters("english", 5)
        if item["chapter_id"] == "eng_c5_ch01"
    )
    seeded_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
        level_id="papas_spectacles_poem_comprehension",
    )
    persisted = _run(store.get_school_session("test_user", session_id))
    persisted_state = {
        **seeded_state,
        "learner_memory": {"strong_skills": ["reading.paragraph_main_idea"]},
    }
    assert _run(
        store.compare_and_set_school_session(
            school_session={**persisted, "state_json": persisted_state},
            expected_state_json=seeded_state,
        )
    ) is True
    client = TestClient(app)
    activity = client.get(
        f"/school/curriculum/{session_id}",
        headers=AUTH,
    ).json()["current_activity"]

    async def unexpected_legacy_read(*_args, **_kwargs):
        raise AssertionError("matching curriculum answer must use canonical snapshot")

    monkeypatch.setattr(
        school_rebuild_routes,
        "_latest_placement_report_for_profile",
        unexpected_legacy_read,
    )
    monkeypatch.setattr(store, "get_active_school_profile_version", unexpected_legacy_read)
    monkeypatch.setattr(store, "get_school_session", unexpected_legacy_read)

    read = client.get(
        f"/school/curriculum/{session_id}",
        headers=AUTH,
    )
    response = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity["activity_id"],
            "answer": "I used the chapter details to explain my answer.",
        },
    )

    assert read.status_code == 200, read.text
    assert response.status_code == 202, response.text
    assert store.school_state_snapshot_calls >= 1
    queued_job = _run(
        store.get_school_evaluation_job(
            "test_user",
            session_id,
            activity["activity_id"],
        )
    )
    assert queued_job["expected_state_json"]["learner_memory"] == {
        "strong_skills": ["reading.paragraph_main_idea"]
    }


def test_curriculum_answer_uses_bundled_context_when_storage_supports_it(
    store,
    monkeypatch,
):
    """Live curriculum answers must not hydrate the full School dashboard."""

    session_id = str(uuid4())
    chapter = next(
        item
        for item in curriculum._available_chapters("english", 5)
        if item["chapter_id"] == "eng_c5_ch01"
    )
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
        level_id="papas_spectacles_poem_comprehension",
    )
    client = TestClient(app)
    activity = client.get(
        f"/school/curriculum/{session_id}",
        headers=AUTH,
    ).json()["current_activity"]
    snapshot_calls_before = store.school_state_snapshot_calls
    calls: list[tuple[str, str, str]] = []

    async def bundled_context(*, user_id: str, session_id: str, activity_id: str):
        calls.append((user_id, session_id, activity_id))
        return {
            "active_profile": await store.get_active_school_profile_version(user_id),
            "placement_report": await store.get_school_placement_report_by_id(
                user_id,
                "placement-report",
            ),
            "school_session": await store.get_school_session(user_id, session_id),
            "answer_request": await store.get_school_answer_request(
                user_id,
                session_id,
                activity_id,
            ),
        }

    async def full_dashboard_snapshot_must_not_run(*_args, **_kwargs):
        raise AssertionError("curriculum answer must use its bundled preflight")

    monkeypatch.setattr(
        store,
        "get_school_curriculum_answer_context",
        bundled_context,
        raising=False,
    )
    monkeypatch.setattr(
        store,
        "get_school_state_snapshot",
        full_dashboard_snapshot_must_not_run,
    )

    response = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity["activity_id"],
            "answer": "I used the chapter details to explain my answer.",
        },
    )

    assert response.status_code == 202, response.text
    assert calls == [("test_user", session_id, activity["activity_id"])]
    assert store.school_state_snapshot_calls == snapshot_calls_before


def test_curriculum_direct_answer_uses_atomic_persist_when_storage_supports_it(
    store,
    monkeypatch,
):
    """A direct teaching step must not pay a second claim round trip."""

    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    chapter = next(
        item
        for item in curriculum._available_chapters("english", 5)
        if item["chapter_id"] == "eng_c5_ch01"
    )
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
        level_id="papas_spectacles_poem_comprehension",
    )
    level = state["levels"][state["current_level_index"]]
    co_construct_index = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if str(step.get("phase") or "") == "co_construct"
    )
    level["v2_step_index"] = co_construct_index
    level["current_step"] = "co_construct"
    state = curriculum.normalize_curriculum_state(state)
    saved = _run(store.get_school_session("test_user", session_id))
    assert _run(store.compare_and_set_school_session(
        school_session={**saved, "state_json": state},
        expected_state_json=saved["state_json"],
    )) is True
    started = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    assert started.status_code == 200, started.text
    body = started.json()
    activity = _private_activity_for_current_body(body)
    answer = _correct_private_curriculum_answer(activity)
    assert curriculum.evaluator_activity_for_answer(activity, answer) is None

    atomic_calls: list[dict[str, Any]] = []
    original_claim = store.claim_school_answer_request
    original_persist = store.persist_school_curriculum_attempt

    async def atomic_persist(**kwargs):
        atomic_calls.append(copy.deepcopy(kwargs))
        claim = await original_claim(
            "test_user",
            body["session_id"],
            activity["activity_id"],
            hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        )
        assert claim["outcome"] == "claimed"
        return await original_persist(
            **kwargs,
            request_claim_token=claim["claim_token"],
        )

    async def unexpected_external_claim(*_args, **_kwargs):
        raise AssertionError("direct curriculum answer must use atomic persistence")

    monkeypatch.setattr(
        store,
        "persist_school_deterministic_curriculum_attempt",
        atomic_persist,
        raising=False,
    )
    monkeypatch.setattr(store, "claim_school_answer_request", unexpected_external_claim)

    response = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={"activity_id": activity["activity_id"], "answer": answer},
    )

    assert response.status_code == 200, response.text
    assert len(atomic_calls) == 1
    assert atomic_calls[0]["request_activity_id"] == activity["activity_id"]
    assert atomic_calls[0]["language_evaluation"] is None
    saved_request = store.school_answer_requests[(body["session_id"], activity["activity_id"])]
    assert saved_request["status"] == "completed"


def test_curriculum_continue_uses_experience_persist_without_evidence_writes(
    store,
    monkeypatch,
):
    """An acknowledgement step advances durably without becoming learner evidence."""

    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    chapter = next(
        item
        for item in curriculum._available_chapters("english", 5)
        if item["chapter_id"] == "eng_c5_ch01"
    )
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
        level_id="papas_spectacles_poem_comprehension",
    )
    level = state["levels"][state["current_level_index"]]
    connect_index = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if str(step.get("phase") or "") == "connect"
    )
    level["v2_step_index"] = connect_index
    level["current_step"] = "connect"
    state = curriculum.normalize_curriculum_state(state)
    saved = _run(store.get_school_session("test_user", session_id))
    assert _run(store.compare_and_set_school_session(
        school_session={**saved, "state_json": state},
        expected_state_json=saved["state_json"],
    )) is True
    body = client.get(f"/school/curriculum/{session_id}", headers=AUTH).json()
    activity = _private_activity_for_current_body(body)
    assert activity["interaction_type"] == "continue"

    calls: list[dict[str, Any]] = []

    async def persist_experience(**kwargs):
        calls.append(copy.deepcopy(kwargs))
        return {"outcome": "persisted"}

    async def unexpected(*_args, **_kwargs):
        raise AssertionError("continue must not use the evidence persistence path")

    monkeypatch.setattr(
        store,
        "persist_school_curriculum_experience_step",
        persist_experience,
        raising=False,
    )
    monkeypatch.setattr(
        store,
        "persist_school_deterministic_curriculum_attempt",
        unexpected,
        raising=False,
    )
    monkeypatch.setattr(store, "claim_school_answer_request", unexpected)

    response = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={"activity_id": activity["activity_id"], "answer": "continue"},
    )

    assert response.status_code == 200, response.text
    assert "school-preflight" in response.headers["server-timing"]
    assert "school-persist" in response.headers["server-timing"]
    assert len(calls) == 1
    assert calls[0]["request_activity_id"] == activity["activity_id"]
    assert calls[0]["request_answer_hash"]
    assert "learning_event" not in calls[0]
    assert "projection_evidence" not in calls[0]
    assert "language_evaluation" not in calls[0]


def test_compact_curriculum_state_rehydrates_authored_content_without_public_key_leak():
    """Persist learner runtime only while rebuilding the same authored lesson."""

    state = curriculum.new_curriculum_state(
        school_profile={
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "hi_en",
            "profile_version_id": "profile-v1",
        },
        placement_report={"report_id": "placement-report"},
        recap_session=None,
    )
    activity_id = curriculum.current_curriculum_activity_id(state)
    assert activity_id
    original_size = len(json.dumps(state, sort_keys=True, separators=(",", ":")))

    compact = curriculum.compact_curriculum_state(state)

    assert compact["authored_content_reference"]["schema_version"] == (
        "school-curriculum-runtime-v1"
    )
    assert "levels" not in compact
    assert "chapter_assessment" not in compact
    assert len(json.dumps(compact, sort_keys=True, separators=(",", ":"))) < original_size // 8

    hydrated = curriculum.normalize_curriculum_state(compact)
    assert curriculum.current_curriculum_activity_id(hydrated) == activity_id
    assert len(hydrated["levels"]) == len(state["levels"])
    assert len(hydrated["chapter_assessment"]["items"]) == len(
        state["chapter_assessment"]["items"]
    )

    updated, evaluation = curriculum.apply_curriculum_answer(
        compact,
        activity_id=activity_id,
        answer="continue",
    )
    assert evaluation["scored"] is False
    resumed = curriculum.normalize_curriculum_state(
        curriculum.compact_curriculum_state(updated)
    )
    assert curriculum.current_curriculum_activity_id(resumed) != activity_id

    public = curriculum.public_curriculum_response(
        {
            "session_id": "runtime-only-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": compact,
        }
    )
    _assert_no_hidden_keys(public)


def _private_activity_for_current_body(body: dict[str, Any]) -> dict[str, Any]:
    """Return the server-side authored activity for a public test response.

    Public curriculum responses must never contain keys, model exemplars, or
    rubrics. Contract tests use the persisted, canonical activity solely to
    drive a complete learner journey; this prevents the test fixture from
    becoming a second, stale curriculum catalogue.
    """

    public_activity = body.get("current_activity") or {}
    session_id = str(body.get("session_id") or "")
    assert session_id and public_activity, body
    session = _run(
        school_rebuild_routes.get_storage().get_school_session(
            "test_user",
            session_id,
        )
    )
    assert session is not None
    state = dict(session["state_json"])
    activity_id = curriculum.current_curriculum_activity_id(state)
    assert activity_id, state
    return curriculum.curriculum_activity_for_answer(state, activity_id=activity_id)


def _private_concept_slot_answer(activity: dict[str, Any]) -> str | None:
    slots = [
        slot
        for slot in activity.get("concept_slots") or []
        if isinstance(slot, dict) and slot.get("any_of")
    ]
    if slots:
        slot_by_id = {str(slot.get("id") or ""): slot for slot in slots}
        ordered_ids = [
            str(slot_id)
            for slot_id in activity.get("ordered_concept_slot_ids") or []
            if str(slot_id) in slot_by_id
        ]
        ordered_slots = [slot_by_id[slot_id] for slot_id in ordered_ids]
        ordered_slots.extend(
            slot
            for slot in slots
            if slot not in ordered_slots
        )
        answer = " ".join(
            str(slot["any_of"][0]).strip()
            for slot in ordered_slots
            if str(slot["any_of"][0]).strip()
        )
        minimum_words = int(activity.get("min_response_words") or 0)
        if len(answer.split()) < minimum_words:
            answer = f"{answer} This explains the chapter idea clearly."
        return answer
    return None


def _private_open_answer_satisfies_current_contract(
    activity: dict[str, Any],
    answer: str,
) -> bool:
    """Check a private authored candidate against the same backend gate.

    The test evaluator deliberately supplies a valid high-quality structured
    result. This helper only chooses between private authored candidates; it
    never manufactures or reads a public answer key.
    """

    evaluator_activity = recap.evaluator_activity_for_answer(activity) or activity
    if not curriculum._open_answer_preflight(evaluator_activity, answer):
        return False
    try:
        result = SchoolV3RubricEvaluation(
            schema_version=(
                "school.open.v1"
                if evaluator_activity.get("grading_mode") == "strict_open_rubric"
                else "school-v3-rubric-1"
            ),
            item_id=str(evaluator_activity["activity_id"]),
            skill_ids=list(evaluator_activity.get("skill_ids") or []),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=str(criterion["id"]),
                    met=True,
                    quality=0.9,
                    evidence_quote=answer,
                )
                for criterion in evaluator_activity.get("rubric_criteria") or []
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )
        return bool(
            curriculum.decide_open_answer_evaluation(
                evaluator_activity,
                result,
                answer=answer,
            )["correct"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def _correct_private_curriculum_answer(activity: dict[str, Any]) -> str:
    """Select an authored passing answer without exposing it through the API."""

    if activity.get("interaction_type") == "continue":
        return "continue"

    slot_answer = _private_concept_slot_answer(activity)
    model_answer = str(activity.get("model_answer") or "").strip()
    if activity.get("evaluation_mode") in {"strict_rubric", "llm_rubric"}:
        generic_strict_response = (
            "I used the passage clue to explain the answer in clear English."
        )
        for candidate in (slot_answer, model_answer, generic_strict_response):
            if candidate and _private_open_answer_satisfies_current_contract(
                activity,
                candidate,
            ):
                return candidate
        raise AssertionError(
            "private authored open-answer candidates do not satisfy the current "
            f"backend contract for {activity.get('activity_id')!r}"
        )

    if model_answer:
        return model_answer
    if activity.get("answer_key"):
        return str(activity["answer_key"])
    accepted_answers = [
        str(answer).strip()
        for answer in activity.get("accepted_answers") or []
        if str(answer).strip()
    ]
    if accepted_answers:
        return accepted_answers[0]
    if slot_answer:
        return slot_answer

    if activity.get("evaluation_mode") in {"strict_rubric", "llm_rubric"}:
        # Strict recap items deliberately have no hidden exemplar. The test
        # evaluator is stubbed to validate the rubric contract, so supply a
        # real learner-style response rather than inventing an answer key.
        return "I used the passage clue and explained the answer in my own words."

    raise AssertionError(
        "test oracle has no authored answer source for "
        f"{activity.get('activity_id')!r}"
    )


def _settle_queued_curriculum_answer(
    response,
    *,
    body: dict[str, Any],
    client: TestClient,
    activity_id: str,
):
    """Run the durable worker before asserting the post-answer learner state."""

    if response.status_code != 202:
        return response
    session_id = str(body["session_id"])
    store = school_rebuild_routes.get_storage()
    assert _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    ) is True
    job = _run(store.get_school_evaluation_job("test_user", session_id, activity_id))
    assert job is not None
    assert job["status"] == "completed", (
        activity_id,
        job.get("last_error_code"),
        job.get("error_json"),
    )
    settled = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    assert settled.status_code == 200, settled.text
    return settled


def _answer(body: dict, answer: str | None, client: TestClient) -> dict:
    # Always submit against the server's current durable state. A preceding
    # answer can update learner evidence and therefore the next adaptive entry
    # point even when the immediate synchronous response still reflects the
    # pre-projection snapshot.
    canonical = client.get(
        f"/school/curriculum/{body['session_id']}",
        headers=AUTH,
    )
    assert canonical.status_code == 200, canonical.text
    body = canonical.json()
    activity = _private_activity_for_current_body(body)
    if answer is None:
        answer = _correct_private_curriculum_answer(
            _private_activity_for_current_body(body)
        )
    response = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={"activity_id": activity["activity_id"], "answer": answer},
    )
    response = _settle_queued_curriculum_answer(
        response,
        body=body,
        client=client,
        activity_id=str(activity["activity_id"]),
    )
    assert response.status_code == 200
    # A deterministic answer response is generated before the same transaction
    # projects its new learner evidence. Reload the canonical session so the
    # next test action follows the durable adaptive entry point, exactly as a
    # learner resuming the page would. Queued answers already take this path.
    refreshed = client.get(
        f"/school/curriculum/{body['session_id']}",
        headers=AUTH,
    )
    assert refreshed.status_code == 200, refreshed.text
    result = refreshed.json()
    _assert_no_hidden_keys(result)
    return result



def _complete_current_curriculum_session(
    body: dict[str, Any],
    client: TestClient,
) -> dict:
    initial_state = _run(
        school_rebuild_routes.get_storage().get_school_session(
            "test_user",
            body["session_id"],
        )
    )["state_json"]
    chapter_assessment = dict(initial_state.get("chapter_assessment") or {})
    completion_budget = max(
        50,
        len(initial_state.get("levels") or []) * 16
        + len(chapter_assessment.get("items") or []) * 3,
    )
    guard = 0
    while body["current_activity"] is not None:
        guard += 1
        assert guard <= completion_budget
        activity = body["current_activity"]
        body = _answer(body, None, client)
        if (
            activity.get("interaction_type") != "continue"
            and activity.get("kind") != "chapter_check"
            and body.get("last_feedback") is not None
        ):
            assert body["last_feedback"]["correct"] is True, (
                activity,
                body["last_feedback"],
            )
    assert body["status"] == "complete"
    return body


def _seed_curriculum_activity_session(
    store,
    *,
    session_id: str,
    chapter: dict[str, Any],
    level_id: str | None = None,
) -> dict[str, Any]:
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    levels = copy.deepcopy(chapter["levels"])
    if level_id is None:
        level_id = next(
            str(level["level_id"])
            for level in levels
            if any(
                str(step.get("phase") or "") == "independent_application"
                and (
                    isinstance(step.get("activity"), dict)
                    or any(
                        isinstance(variant, dict)
                        and str(variant.get("evaluation_mode") or "")
                        == "llm_rubric"
                        for variant in step.get("variant_pool") or []
                    )
                )
                for step in level.get("teaching_steps") or []
            )
        )
    level_index = next(
        index for index, level in enumerate(levels) if level["level_id"] == level_id
    )
    for index, level in enumerate(levels):
        level["status"] = "complete" if index < level_index else "not_started"
        level["current_step"] = "complete" if index < level_index else "guided_check"
        level["attempts"] = []
    levels[level_index]["status"] = "in_progress"
    levels[level_index]["current_step"] = "independent_check"
    if levels[level_index].get("teaching_steps"):
        independent_index = next(
            index
            for index, step in enumerate(levels[level_index]["teaching_steps"])
            if step["phase"] == "independent_application"
        )
        levels[level_index]["v2_step_index"] = independent_index
        levels[level_index]["current_step"] = "independent_application"
    state = curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "profile_version_id": profile["profile_version_id"],
            "status": "active",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "source_recap_session_id": None,
            "source_placement_report_id": "placement-report",
            "chapter": {key: value for key, value in chapter.items() if key != "levels"},
            "completed_chapter_ids": [],
            "completed_chapter_versions": {},
            "carry_forward_focuses": [],
            "current_level_index": level_index,
            "levels": levels,
            "last_feedback": None,
        }
    )
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage=str(level_index),
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=state,
        )
    )
    return state


def test_curriculum_answer_status_uses_narrow_context_and_rehydrates_only_public_session(
    store,
    monkeypatch,
):
    """Pending rubric polling must not rehydrate the learner dashboard or answer data."""

    chapter = next(
        item
        for item in curriculum._available_chapters("english", 5)
        if item["chapter_id"] == "eng_c5_ch01"
    )
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
    )
    client = TestClient(app)
    initial = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    assert initial.status_code == 200, initial.text
    activity_id = str(initial.json()["current_activity"]["activity_id"])

    store.school_answer_requests[(session_id, activity_id)] = {
        "user_id": "test_user",
        "status": "processing",
        "answer_hash": "private-answer-hash",
        "claim_token": "private-claim-token",
        "raw_answer": "private learner answer must never leave storage",
        "updated_at": time.time(),
    }
    calls: list[tuple[str, str, str]] = []

    async def narrow_context(*, user_id: str, session_id: str, activity_id: str):
        calls.append((user_id, session_id, activity_id))
        return {
            "active_profile": await store.get_active_school_profile_version(user_id),
            "placement_report": await store.get_school_placement_report_by_id(
                user_id,
                "placement-report",
            ),
            "school_session": await store.get_school_session(user_id, session_id),
            "answer_request": await store.get_school_answer_request(
                user_id,
                session_id,
                activity_id,
            ),
        }

    async def full_dashboard_snapshot_must_not_run(*_args, **_kwargs):
        raise AssertionError("pending answer status must not load the School dashboard")

    monkeypatch.setattr(
        store,
        "get_school_curriculum_answer_context",
        narrow_context,
        raising=False,
    )
    monkeypatch.setattr(
        store,
        "get_school_state_snapshot",
        full_dashboard_snapshot_must_not_run,
    )

    pending = client.get(
        f"/school/curriculum/{session_id}/answers/{activity_id}/status",
        headers=AUTH,
    )

    assert pending.status_code == 200, pending.text
    assert pending.json() == {
        "status": "awaiting_evaluation",
        "session_id": session_id,
        "activity_id": activity_id,
    }
    assert calls == [("test_user", session_id, activity_id)]
    assert "private learner answer" not in pending.text
    assert "private-answer-hash" not in pending.text
    assert "private-claim-token" not in pending.text

    store.school_answer_requests[(session_id, activity_id)].update(
        status="completed",
        response_json={
            "answer_key": "must-not-be-returned-from-stored-response",
            "raw_answer": "must-not-be-returned-from-stored-response",
        },
        updated_at=time.time(),
    )
    completed = client.get(
        f"/school/curriculum/{session_id}/answers/{activity_id}/status",
        headers=AUTH,
    )

    assert completed.status_code == 200, completed.text
    body = completed.json()
    assert body["status"] == "completed"
    assert body["session"]["session_id"] == session_id
    _assert_no_hidden_keys(body)
    assert "must-not-be-returned-from-stored-response" not in completed.text


def _seed_frog_chapter_check_session(store, *, session_id: str) -> dict[str, Any]:
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    chapter = copy.deepcopy(
        next(
            candidate
            for candidate in curriculum._available_chapters("english", 5)
            if candidate["chapter_id"] == "eng_c5_ch05"
        )
    )
    levels = copy.deepcopy(chapter["levels"])
    for level in levels:
        level["status"] = "complete"
        level["current_step"] = "complete"
        level["attempts"] = []
    state = curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "profile_version_id": profile["profile_version_id"],
            "status": "active",
            "phase": "chapter_check",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "source_recap_session_id": None,
            "source_placement_report_id": "placement-report",
            "chapter": {
                key: value
                for key, value in chapter.items()
                if key not in {"levels", "chapter_assessment"}
            },
            "chapter_assessment": curriculum._new_chapter_assessment_state(
                chapter["chapter_assessment"]
            ),
            "completed_chapter_ids": [
                "eng_c5_ch01",
                "eng_c5_ch02",
                "eng_c5_ch03",
                "eng_c5_ch04",
            ],
            "completed_chapter_versions": {},
            "carry_forward_focuses": [],
            "current_level_index": len(levels) - 1,
            "levels": levels,
            "last_feedback": None,
        }
    )
    state = curriculum._begin_chapter_assessment(state)
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="chapter_check",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=state,
        )
    )
    return state


def _replace_curriculum_source_report_same_profile(
    store,
    *,
    source_report_id: str,
) -> None:
    old_report = next(
        dict(row)
        for row in store.school_placement_reports.values()
        if str(row.get("report_id")) == str(source_report_id)
    )
    old_placement = _run(
        store.get_school_session("test_user", old_report["placement_session_id"])
    )
    new_placement_session_id = "same-profile-curriculum-new-placement"
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
    _run(
        store.upsert_school_placement_report(
            **{
                **old_report,
                "report_id": "same-profile-curriculum-new-report",
                "placement_session_id": new_placement_session_id,
            }
        )
    )


def _drive_frog_chapter_check(
    body: dict[str, Any],
    client: TestClient,
    *,
    fail_first: bool,
) -> dict[str, Any]:
    state = _run(
        school_rebuild_routes.get_storage().get_school_session(
            "test_user",
            body["session_id"],
        )
    )["state_json"]
    expected_answers = len(
        (state.get("chapter_assessment") or {}).get("selected_item_ids") or []
    )
    assert expected_answers > 0
    answered = 0
    while body["phase"] == "chapter_check":
        activity = body["current_activity"]
        assert activity is not None
        answer = (
            "wrong"
            if fail_first and answered == 0
            else None
        )
        body = _answer(body, answer, client)
        answered += 1
        assert answered <= expected_answers
    assert answered == expected_answers
    return body


def _drive_frog_remediation(
    body: dict[str, Any],
    client: TestClient,
) -> dict[str, Any]:
    answered = 0
    while body["phase"] == "remediation":
        activity = body["current_activity"]
        assert activity is not None
        assert activity["kind"] in {"masterclass", "independent_check"}
        body = _answer(body, None, client)
        assert body["last_feedback"]["correct"] is True, activity
        answered += 1
        assert answered <= 14
    assert answered >= 2
    return body


def test_curriculum_short_answer_requires_exact_match_not_substring():
    public_profile = {"target_class_no": 3, "subject_ids": ["english"]}
    state = curriculum.new_curriculum_state(
        school_profile=public_profile,
        placement_report={"report_id": "test-report", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    assert public_profile["target_class_no"] == 3
    first_level = state["levels"][0]
    typed_step_index = next(
        index
        for index, step in enumerate(first_level["teaching_steps"])
        if str(step.get("phase") or "") == "co_construct"
    )
    first_level["v2_step_index"] = typed_step_index
    first_level["current_step"] = "co_construct"
    activity_id = curriculum.current_curriculum_activity_id(state)
    assert activity_id
    activity = curriculum.curriculum_activity_for_answer(state, activity_id=activity_id)
    assert activity["grading_mode"] == "selected_option"
    accepted_answer = _correct_private_curriculum_answer(activity)
    rejected_answer = f"{accepted_answer} extra"

    rejected, rejected_evaluation = curriculum.apply_curriculum_answer(
        copy.deepcopy(state),
        activity_id=activity_id,
        answer=rejected_answer,
    )
    accepted, accepted_evaluation = curriculum.apply_curriculum_answer(
        copy.deepcopy(state),
        activity_id=activity_id,
        answer=accepted_answer,
    )

    assert rejected_evaluation["correct"] is False
    assert accepted_evaluation["correct"] is True
    assert curriculum.current_curriculum_activity_id(accepted) != activity_id
    assert rejected["current_level_index"] == accepted["current_level_index"]


def test_curriculum_phrase_match_rejects_a_negated_expected_answer():
    assert curriculum._accepted_phrase_matches("not a rainbow", "rainbow") is False
    assert curriculum._accepted_phrase_matches("this is not past tense", "past tense") is False
    assert curriculum._accepted_phrase_matches(
        "i do not believe this is a rainbow",
        "rainbow",
    ) is False
    assert curriculum._accepted_phrase_matches("this is a rainbow not a boat", "rainbow") is True


def test_independent_failure_feedback_names_the_bridge_transition():
    assert curriculum._feedback_message(
        "independent_check",
        False,
        "bridge",
    ) == "Not yet. Zidd will slow this chapter level down with a bridge check."


def test_curriculum_starts_real_class_3_colours_chapter_after_recap(store):
    _seed_school_profile(store)
    client = TestClient(app)
    recap = _complete_recap_success_path(client)

    response = client.post("/school/curriculum/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["flow_type"] == "curriculum"
    assert body["status"] == "active"
    assert body["source_recap_session_id"] == recap["session_id"]
    assert body["chapter"]["chapter_id"] == "eng_c3_ch01"
    assert body["chapter"]["title"] == "Colours"
    assert body["chapter"]["book_title"] == "Santoor"
    assert body["chapter"]["unit_title"] == "Fun with Friends"
    _assert_empty_chapter_progress(body)
    assert body["carry_forward_focuses"]
    assert all(
        isinstance(focus, str) and focus.strip()
        for focus in body["carry_forward_focuses"]
    )
    _assert_current_activity_matches_catalog(body)
    assert body["current_activity"]["phase"] == "connect"
    assert body["current_activity"]["interaction_type"] == "continue"
    assert "Santoor Chapter" not in body["current_activity"]["teaching_block"]
    _assert_no_hidden_keys(body)

    active_profile = _run(store.get_active_school_profile_version("test_user"))
    saved = _run(store.get_school_session("test_user", body["session_id"]))
    assert saved["profile_version_id"] == active_profile["profile_version_id"]
    assert saved["source_placement_report_id"] == body["source_placement_report_id"]
    assert saved["linked_session_id"] == recap["session_id"]
    assert saved["state_json"]["profile_version_id"] == active_profile["profile_version_id"]

    _replace_curriculum_source_report_same_profile(
        store,
        source_report_id=body["source_placement_report_id"],
    )
    obsolete_get = client.get(
        f"/school/curriculum/{body['session_id']}", headers=AUTH
    )
    obsolete_answer = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={
            "activity_id": body["current_activity"]["activity_id"],
            "answer": "obsolete report answer",
        },
    )
    assert obsolete_get.status_code == 404
    assert obsolete_answer.status_code == 404

    replacement_payload = _profile_payload(target_class_no=3)
    replacement_payload["preferred_teaching_language"] = "en"
    replacement = _activate_school_profile(client, replacement_payload)
    assert replacement.status_code == 200
    old_get = client.get(f"/school/curriculum/{body['session_id']}", headers=AUTH)
    assert old_get.status_code == 404
    old_answer = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={
            "activity_id": body["current_activity"]["activity_id"],
            "answer": "old profile answer",
        },
    )
    assert old_answer.status_code == 404


def test_curriculum_get_refreshes_learning_memory_created_after_session_start(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)
    started = client.post("/school/curriculum/start", headers=AUTH).json()
    initial_strong_skills = list(started["memory_summary"]["strong_skills"])

    skill_id = "writing.summary_own_words"
    readiness_state = SkillReadinessState(
        skill_id=skill_id,
        practice_readiness=0.94,
        certified_readiness=0.94,
        total_attempts=5,
        certified_attempts=5,
        independent_passes=3,
        transfer_passes=1,
        review_passes=1,
        recent_hint_flags=(False,),
        last_confidence=1.0,
    )
    profile_fields = to_profile_upsert(readiness_state)
    _run(store.upsert_learner_skill_profile(
        user_id="test_user",
        domain="school",
        skill_id=skill_id,
        module_id="eng_c5_ch01",
        task_type="school_rebuild_curriculum",
        mastery=profile_fields["mastery"],
        readiness=profile_fields["readiness"],
        confidence=1.0,
        attempts=5,
        strengths_json=["explain a reason from passage evidence"],
        gaps_json=[],
        evidence_json={
            "latest_quote": "I used the passage clue to explain why he searched.",
            "attempt_type": "transfer_check",
            "chapter_id": "eng_c5_ch01",
            "level_id": "papas_spectacles_humour_and_reasons",
            "school_readiness_state": profile_fields["school_readiness_state"],
        },
        recommended_next_action="Continue with a new independent example.",
        source_summary="Strong transfer evidence in eng_c5_ch01.",
    ))

    refreshed = client.get(
        f"/school/curriculum/{started['session_id']}",
        headers=AUTH,
    )

    assert refreshed.status_code == 200
    refreshed_skills = refreshed.json()["memory_summary"]["strong_skills"]
    profile = next(
        item
        for item in refreshed_skills
        if item["skill_id"] == skill_id
    )
    assert profile["skill_id"] == skill_id
    assert profile["latest_evidence"] == "I used the passage clue to explain why he searched."
    assert profile["last_attempt_type"] == "transfer_check"
    assert profile["last_chapter_id"] == "eng_c5_ch01"
    assert profile["attempts"] == 5
    assert profile["skill_status"] == "mastered"
    assert len(refreshed_skills) >= len(initial_strong_skills)


def test_compatible_profile_edit_keeps_active_curriculum_and_historical_report_lineage(store):
    original_profile = _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    curriculum_body = client.post("/school/curriculum/start", headers=AUTH).json()

    report_before = _run(
        store.get_school_placement_report_by_id(
            "test_user",
            curriculum_body["source_placement_report_id"],
        )
    )
    assert report_before["profile_version_id"] == original_profile["profile_version_id"]

    compatible_payload = _profile_payload()
    compatible_payload["parent_goal"] = "Build a steady weekly reading habit."
    replacement = _activate_school_profile(client, compatible_payload)
    assert replacement.status_code == 200
    replacement_profile = replacement.json()["profile"]

    saved_curriculum = _run(
        store.get_school_session("test_user", curriculum_body["session_id"])
    )
    assert saved_curriculum["status"] == "active"
    assert saved_curriculum["profile_version_id"] == replacement_profile["profile_version_id"]
    assert (
        saved_curriculum["state_json"]["profile_version_id"]
        == replacement_profile["profile_version_id"]
    )

    report_after = _run(
        store.get_school_placement_report_by_id(
            "test_user",
            curriculum_body["source_placement_report_id"],
        )
    )
    assert report_after["profile_version_id"] == original_profile["profile_version_id"]

    state = client.get("/school/state", headers=AUTH)
    assert state.status_code == 200
    assert state.json()["active_session_id"] == curriculum_body["session_id"]
    assert state.json()["next_action"] == "resume_curriculum"

    resumed = client.get(
        f"/school/curriculum/{curriculum_body['session_id']}",
        headers=AUTH,
    )
    assert resumed.status_code == 200
    assert resumed.json()["session_id"] == curriculum_body["session_id"]


def test_curriculum_bridge_masterclass_and_independent_advance_are_tracked(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    body = client.post("/school/curriculum/start", headers=AUTH).json()
    session_id = body["session_id"]

    # V2 deliberately begins with a low-stakes connection and co-construction
    # before a scored guided attempt. A miss at that point must produce a
    # fresh, targeted bridge rather than prematurely certifying progress.
    body = _answer(body, None, client)
    assert body["current_activity"]["phase"] == "co_construct"
    body = _answer(body, None, client)
    assert body["current_activity"]["phase"] == "guided_practice"
    guided_activity_id = body["current_activity"]["activity_id"]

    body = _answer(body, "wrong", client)
    assert body["last_feedback"]["correct"] is False
    assert body["current_activity"]["kind"] == "v2_support"
    assert body["current_activity"]["support_mode"] == "bridge"
    assert body["current_activity"]["lineage"]["trigger_activity_id"] == guided_activity_id
    _assert_no_hidden_keys(body)

    body = _answer(body, None, client)
    assert body["current_activity"]["phase"] == "guided_practice"
    assert body["current_activity"]["support_mode"] is None
    assert body["current_activity"]["activity_id"] != guided_activity_id

    body = _answer(body, None, client)
    assert body["current_activity"]["phase"] == "independent_application"
    assert (
        _private_activity_for_current_body(body)["evaluation_mode"] == "llm_rubric"
    )
    _assert_no_hidden_keys(body)
    assert body["session_id"] == session_id

    curriculum_events = [
        event
        for event in store.learning_events
        if event.get("task_type") == "school_rebuild_curriculum"
    ]
    assert len(curriculum_events) == 5
    assert curriculum_events[-1]["score"] >= 0.8
    assert any(
        event["attempt_type"] == "v2_support"
        for event in curriculum_events
    )


def test_school_state_resumes_active_curriculum_session(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    started = client.post("/school/curriculum/start", headers=AUTH).json()

    state = client.get("/school/state", headers=AUTH).json()

    assert state["active_flow"] == "curriculum"
    assert state["active_session_id"] == started["session_id"]
    assert state["next_action"] == "resume_curriculum"
    assert state["next_action_url"] == f"/school/session/{started['session_id']}"


def test_completed_curriculum_session_opens_next_chapter(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    completed_first = _complete_current_curriculum_session(first, client)

    landing = client.get("/school/curriculum", headers=AUTH).json()

    assert completed_first["chapter"]["chapter_id"] == "eng_c3_ch01"
    first_preview, second_preview = landing["chapters_preview"][:2]
    assert first_preview["title"] == "Colours"
    assert first_preview["status"] == "complete"
    assert second_preview["title"] == "Badal and Moti"
    assert second_preview["status"] == "ready"
    assert "Start Chapter 2" in landing["source_note"]

    second = client.post("/school/curriculum/start", headers=AUTH)

    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "active"
    assert body["chapter"]["chapter_id"] == "eng_c3_ch02"
    assert body["chapter"]["title"] == "Badal and Moti"
    assert body["chapter"]["book_title"] == "Santoor"
    _assert_empty_chapter_progress(body)
    _assert_current_activity_matches_catalog(body)
    assert body["current_activity"]["phase"] == "connect"
    assert body["current_activity"]["interaction_type"] == "continue"
    _assert_no_hidden_keys(body)


def test_completed_second_authored_chapter_opens_best_friends(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()

    assert second["chapter"]["chapter_id"] == "eng_c3_ch02"
    completed_second = _complete_current_curriculum_session(second, client)

    assert completed_second["status"] == "complete"
    assert completed_second["next_available_chapter"]["chapter_id"] == "eng_c3_ch03"
    assert completed_second["next_available_chapter"]["title"] == "Best Friends"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    third_preview = landing["chapters_preview"][2]
    assert third_preview["title"] == "Best Friends"
    assert third_preview["status"] == "ready"

    third_response = client.post("/school/curriculum/start", headers=AUTH)
    assert third_response.status_code == 200
    third = third_response.json()
    assert third["chapter"]["chapter_id"] == "eng_c3_ch03"
    assert third["chapter"]["title"] == "Best Friends"
    _assert_current_activity_matches_catalog(third)
    _assert_no_hidden_keys(third)


def test_completed_third_authored_chapter_opens_out_in_the_garden(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()

    assert third["chapter"]["chapter_id"] == "eng_c3_ch03"
    completed_third = _complete_current_curriculum_session(third, client)

    assert completed_third["status"] == "complete"
    assert completed_third["next_available_chapter"]["chapter_id"] == "eng_c3_ch04"
    assert completed_third["next_available_chapter"]["title"] == "Out in the Garden"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fourth_preview = landing["chapters_preview"][3]
    assert fourth_preview["title"] == "Out in the Garden"
    assert fourth_preview["status"] == "ready"

    fourth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fourth_response.status_code == 200
    fourth = fourth_response.json()
    assert fourth["chapter"]["chapter_id"] == "eng_c3_ch04"
    assert fourth["chapter"]["title"] == "Out in the Garden"
    assert fourth["chapter"]["unit_title"] == "Toys and Games"
    _assert_current_activity_matches_catalog(fourth)
    _assert_no_hidden_keys(fourth)


def test_completed_fourth_authored_chapter_opens_talking_toys(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert fourth["chapter"]["chapter_id"] == "eng_c3_ch04"
    completed_fourth = _complete_current_curriculum_session(fourth, client)

    assert completed_fourth["status"] == "complete"
    assert completed_fourth["next_available_chapter"]["chapter_id"] == "eng_c3_ch05"
    assert completed_fourth["next_available_chapter"]["title"] == "Talking Toys"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fifth_preview = landing["chapters_preview"][4]
    assert fifth_preview["title"] == "Talking Toys"
    assert fifth_preview["status"] == "ready"

    fifth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fifth_response.status_code == 200
    fifth = fifth_response.json()
    assert fifth["chapter"]["chapter_id"] == "eng_c3_ch05"
    assert fifth["chapter"]["title"] == "Talking Toys"
    assert fifth["chapter"]["unit_title"] == "Toys and Games"
    _assert_current_activity_matches_catalog(fifth)
    _assert_no_hidden_keys(fifth)


def test_completed_fifth_authored_chapter_opens_paper_boats(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert fifth["chapter"]["chapter_id"] == "eng_c3_ch05"
    completed_fifth = _complete_current_curriculum_session(fifth, client)

    assert completed_fifth["status"] == "complete"
    assert completed_fifth["next_available_chapter"]["chapter_id"] == "eng_c3_ch06"
    assert completed_fifth["next_available_chapter"]["title"] == "Paper Boats"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    sixth_preview = landing["chapters_preview"][5]
    assert sixth_preview["title"] == "Paper Boats"
    assert sixth_preview["status"] == "ready"

    sixth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert sixth_response.status_code == 200
    sixth = sixth_response.json()
    assert sixth["chapter"]["chapter_id"] == "eng_c3_ch06"
    assert sixth["chapter"]["title"] == "Paper Boats"
    assert sixth["chapter"]["unit_title"] == "Toys and Games"
    _assert_current_activity_matches_catalog(sixth)
    _assert_no_hidden_keys(sixth)


def test_completed_sixth_authored_chapter_opens_the_big_laddoo(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert sixth["chapter"]["chapter_id"] == "eng_c3_ch06"
    completed_sixth = _complete_current_curriculum_session(sixth, client)

    assert completed_sixth["status"] == "complete"
    assert completed_sixth["next_available_chapter"]["chapter_id"] == "eng_c3_ch07"
    assert completed_sixth["next_available_chapter"]["title"] == "The Big Laddoo"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    seventh_preview = landing["chapters_preview"][6]
    assert seventh_preview["title"] == "The Big Laddoo"
    assert seventh_preview["status"] == "ready"

    seventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert seventh_response.status_code == 200
    seventh = seventh_response.json()
    assert seventh["chapter"]["chapter_id"] == "eng_c3_ch07"
    assert seventh["chapter"]["title"] == "The Big Laddoo"
    assert seventh["chapter"]["unit_title"] == "Good Food"
    _assert_current_activity_matches_catalog(seventh)
    _assert_no_hidden_keys(seventh)


def test_completed_seventh_authored_chapter_opens_thank_god(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()

    assert seventh["chapter"]["chapter_id"] == "eng_c3_ch07"
    completed_seventh = _complete_current_curriculum_session(seventh, client)

    assert completed_seventh["status"] == "complete"
    assert completed_seventh["next_available_chapter"]["chapter_id"] == "eng_c3_ch08"
    assert completed_seventh["next_available_chapter"]["title"] == "Thank God!"
    state = client.get("/school/state", headers=AUTH).json()
    assert state["next_action"] == "start_curriculum"
    assert state["allowed_next_actions"] == ["start_curriculum"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    eighth_preview = landing["chapters_preview"][7]
    assert eighth_preview["title"] == "Thank God!"
    assert eighth_preview["status"] == "ready"

    eighth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eighth_response.status_code == 200
    eighth = eighth_response.json()
    assert eighth["chapter"]["chapter_id"] == "eng_c3_ch08"
    assert eighth["chapter"]["title"] == "Thank God!"
    assert eighth["chapter"]["unit_title"] == "Good Food"
    _assert_current_activity_matches_catalog(eighth)
    _assert_no_hidden_keys(eighth)


def test_completed_last_authored_chapter_hides_next_chapter(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eleventh, client)
    twelfth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert twelfth["chapter"]["chapter_id"] == "eng_c3_ch12"
    completed_twelfth = _complete_current_curriculum_session(twelfth, client)

    assert completed_twelfth["status"] == "complete"
    assert completed_twelfth["next_available_chapter"] is None
    _assert_no_hidden_keys(completed_twelfth)

    state = client.get("/school/state", headers=AUTH).json()
    assert state["status"] == "complete"
    assert state["active_flow"] == "curriculum"
    assert state["active_session_id"] == completed_twelfth["session_id"]
    assert state["next_action"] == "view_report"
    assert state["next_action_url"] == "/school/reports"
    assert state["allowed_next_actions"] == ["view_report"]

    next_response = client.post("/school/curriculum/start", headers=AUTH)

    assert next_response.status_code == 409
    assert next_response.json()["detail"]["code"] == "curriculum_locked"


def test_completed_eighth_authored_chapter_opens_madhu_wish(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert eighth["chapter"]["chapter_id"] == "eng_c3_ch08"
    completed_eighth = _complete_current_curriculum_session(eighth, client)

    assert completed_eighth["status"] == "complete"
    assert completed_eighth["next_available_chapter"]["chapter_id"] == "eng_c3_ch09"
    assert completed_eighth["next_available_chapter"]["title"] == "Madhu's Wish"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    ninth_preview = landing["chapters_preview"][8]
    assert ninth_preview["title"] == "Madhu's Wish"
    assert ninth_preview["status"] == "ready"

    ninth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert ninth_response.status_code == 200
    ninth = ninth_response.json()
    assert ninth["chapter"]["chapter_id"] == "eng_c3_ch09"
    assert ninth["chapter"]["title"] == "Madhu's Wish"
    assert ninth["chapter"]["unit_title"] == "Good Food"
    _assert_current_activity_matches_catalog(ninth)
    _assert_no_hidden_keys(ninth)


def test_completed_ninth_authored_chapter_opens_night(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert ninth["chapter"]["chapter_id"] == "eng_c3_ch09"
    completed_ninth = _complete_current_curriculum_session(ninth, client)

    assert completed_ninth["status"] == "complete"
    assert completed_ninth["next_available_chapter"]["chapter_id"] == "eng_c3_ch10"
    assert completed_ninth["next_available_chapter"]["title"] == "Night"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    tenth_preview = landing["chapters_preview"][9]
    assert tenth_preview["title"] == "Night"
    assert tenth_preview["status"] == "ready"

    tenth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert tenth_response.status_code == 200
    tenth = tenth_response.json()
    assert tenth["chapter"]["chapter_id"] == "eng_c3_ch10"
    assert tenth["chapter"]["title"] == "Night"
    assert tenth["chapter"]["unit_title"] == "The Sky"
    _assert_current_activity_matches_catalog(tenth)
    _assert_no_hidden_keys(tenth)


def test_completed_tenth_authored_chapter_opens_chanda_mama(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert tenth["chapter"]["chapter_id"] == "eng_c3_ch10"
    completed_tenth = _complete_current_curriculum_session(tenth, client)

    assert completed_tenth["status"] == "complete"
    assert completed_tenth["next_available_chapter"]["chapter_id"] == "eng_c3_ch11"
    assert completed_tenth["next_available_chapter"]["title"] == "Chanda Mama Counts the Stars"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    eleventh_preview = landing["chapters_preview"][10]
    assert eleventh_preview["title"] == "Chanda Mama Counts the Stars"
    assert eleventh_preview["status"] == "ready"

    eleventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eleventh_response.status_code == 200
    eleventh = eleventh_response.json()
    assert eleventh["chapter"]["chapter_id"] == "eng_c3_ch11"
    assert eleventh["chapter"]["title"] == "Chanda Mama Counts the Stars"
    assert eleventh["chapter"]["unit_title"] == "The Sky"
    _assert_current_activity_matches_catalog(eleventh)
    _assert_no_hidden_keys(eleventh)


def test_completed_eleventh_authored_chapter_opens_chandrayaan(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()

    assert eleventh["chapter"]["chapter_id"] == "eng_c3_ch11"
    completed_eleventh = _complete_current_curriculum_session(eleventh, client)

    assert completed_eleventh["status"] == "complete"
    assert completed_eleventh["next_available_chapter"]["chapter_id"] == "eng_c3_ch12"
    assert completed_eleventh["next_available_chapter"]["title"] == "Chandrayaan"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    twelfth_preview = landing["chapters_preview"][11]
    assert twelfth_preview["title"] == "Chandrayaan"
    assert twelfth_preview["status"] == "ready"

    twelfth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert twelfth_response.status_code == 200
    twelfth = twelfth_response.json()
    assert twelfth["chapter"]["chapter_id"] == "eng_c3_ch12"
    assert twelfth["chapter"]["title"] == "Chandrayaan"
    assert twelfth["chapter"]["unit_title"] == "The Sky"
    _assert_current_activity_matches_catalog(twelfth)
    _assert_no_hidden_keys(twelfth)


def test_class_four_target_ready_placement_opens_together_we_can_curriculum(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    report = _complete_target_ready_placement(client)

    landing_response = client.get("/school/curriculum", headers=AUTH)

    assert landing_response.status_code == 200
    landing = landing_response.json()
    assert landing["target_class_no"] == 4
    assert landing["source_placement_report_id"] == report["report_id"]
    assert landing["chapters_preview"][0]["chapter_id"] == "eng_c4_ch01"
    assert landing["chapters_preview"][0]["title"] == "Together We Can"
    assert landing["chapters_preview"][0]["status"] == "ready"

    started_response = client.post("/school/curriculum/start", headers=AUTH)
    assert started_response.status_code == 200
    started = started_response.json()
    assert started["chapter"]["chapter_id"] == "eng_c4_ch01"
    assert started["chapter"]["title"] == "Together We Can"
    assert started["chapter"]["unit_title"] == "My Land"
    _assert_current_activity_matches_catalog(started)
    _assert_no_hidden_keys(started)


def test_completed_class_four_first_chapter_opens_tinkling_bells(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    assert first["chapter"]["chapter_id"] == "eng_c4_ch01"
    completed_first = _complete_current_curriculum_session(first, client)

    assert completed_first["status"] == "complete"
    assert completed_first["next_available_chapter"]["chapter_id"] == "eng_c4_ch02"
    assert completed_first["next_available_chapter"]["title"] == "The Tinkling Bells"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    second_preview = landing["chapters_preview"][1]
    assert second_preview["chapter_id"] == "eng_c4_ch02"
    assert second_preview["title"] == "The Tinkling Bells"
    assert second_preview["status"] == "ready"

    second_response = client.post("/school/curriculum/start", headers=AUTH)
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["chapter"]["chapter_id"] == "eng_c4_ch02"
    assert second["chapter"]["title"] == "The Tinkling Bells"
    assert second["chapter"]["unit_title"] == "My Land"
    _assert_current_activity_matches_catalog(second)
    _assert_no_hidden_keys(second)


def test_completed_class_four_second_chapter_opens_be_smart_be_safe(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    assert second["chapter"]["chapter_id"] == "eng_c4_ch02"
    completed_second = _complete_current_curriculum_session(second, client)

    assert completed_second["status"] == "complete"
    assert completed_second["next_available_chapter"]["chapter_id"] == "eng_c4_ch03"
    assert completed_second["next_available_chapter"]["title"] == "Be Smart, Be Safe"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    third_preview = landing["chapters_preview"][2]
    assert third_preview["chapter_id"] == "eng_c4_ch03"
    assert third_preview["title"] == "Be Smart, Be Safe"
    assert third_preview["status"] == "ready"

    third_response = client.post("/school/curriculum/start", headers=AUTH)
    assert third_response.status_code == 200
    third = third_response.json()
    assert third["chapter"]["chapter_id"] == "eng_c4_ch03"
    assert third["chapter"]["title"] == "Be Smart, Be Safe"
    assert third["chapter"]["unit_title"] == "My Land"
    _assert_current_activity_matches_catalog(third)
    _assert_no_hidden_keys(third)


def test_completed_class_four_third_chapter_opens_one_thing_at_a_time(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    assert third["chapter"]["chapter_id"] == "eng_c4_ch03"
    completed_third = _complete_current_curriculum_session(third, client)

    assert completed_third["status"] == "complete"
    assert completed_third["next_available_chapter"]["chapter_id"] == "eng_c4_ch04"
    assert completed_third["next_available_chapter"]["title"] == "One Thing at a Time"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fourth_preview = landing["chapters_preview"][3]
    assert fourth_preview["chapter_id"] == "eng_c4_ch04"
    assert fourth_preview["title"] == "One Thing at a Time"
    assert fourth_preview["status"] == "ready"

    fourth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fourth_response.status_code == 200
    fourth = fourth_response.json()
    assert fourth["chapter"]["chapter_id"] == "eng_c4_ch04"
    assert fourth["chapter"]["title"] == "One Thing at a Time"
    assert fourth["chapter"]["unit_title"] == "My Beautiful World"
    _assert_current_activity_matches_catalog(fourth)
    _assert_no_hidden_keys(fourth)


def test_completed_class_four_fourth_chapter_opens_the_old_stag(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert fourth["chapter"]["chapter_id"] == "eng_c4_ch04"
    completed_fourth = _complete_current_curriculum_session(fourth, client)

    assert completed_fourth["status"] == "complete"
    assert completed_fourth["next_available_chapter"]["chapter_id"] == "eng_c4_ch05"
    assert completed_fourth["next_available_chapter"]["title"] == "The Old Stag"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fifth_preview = landing["chapters_preview"][4]
    assert fifth_preview["chapter_id"] == "eng_c4_ch05"
    assert fifth_preview["title"] == "The Old Stag"
    assert fifth_preview["status"] == "ready"

    fifth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fifth_response.status_code == 200
    fifth = fifth_response.json()
    assert fifth["chapter"]["chapter_id"] == "eng_c4_ch05"
    assert fifth["chapter"]["title"] == "The Old Stag"
    assert fifth["chapter"]["unit_title"] == "My Beautiful World"
    _assert_current_activity_matches_catalog(fifth)
    _assert_no_hidden_keys(fifth)


def test_completed_class_four_fifth_chapter_opens_braille(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert fifth["chapter"]["chapter_id"] == "eng_c4_ch05"
    completed_fifth = _complete_current_curriculum_session(fifth, client)

    assert completed_fifth["status"] == "complete"
    assert completed_fifth["next_available_chapter"]["chapter_id"] == "eng_c4_ch06"
    assert completed_fifth["next_available_chapter"]["title"] == "Braille"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["chapter_id"] == "eng_c4_ch06"
    assert landing["chapters_preview"][5]["title"] == "Braille"
    assert landing["chapters_preview"][5]["status"] == "ready"

    sixth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert sixth_response.status_code == 200
    sixth = sixth_response.json()
    assert sixth["chapter"]["chapter_id"] == "eng_c4_ch06"
    assert sixth["chapter"]["title"] == "Braille"
    assert sixth["chapter"]["unit_title"] == "My Beautiful World"
    _assert_current_activity_matches_catalog(sixth)
    _assert_no_hidden_keys(sixth)


def test_completed_class_four_sixth_chapter_opens_fit_body(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert sixth["chapter"]["chapter_id"] == "eng_c4_ch06"
    completed_sixth = _complete_current_curriculum_session(sixth, client)

    assert completed_sixth["status"] == "complete"
    assert completed_sixth["next_available_chapter"]["chapter_id"] == "eng_c4_ch07"
    assert completed_sixth["next_available_chapter"]["title"] == "Fit Body, Fit Mind, Fit Nation"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["chapter_id"] == "eng_c4_ch07"
    assert landing["chapters_preview"][6]["title"] == "Fit Body, Fit Mind, Fit Nation"
    assert landing["chapters_preview"][6]["status"] == "ready"

    seventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert seventh_response.status_code == 200
    seventh = seventh_response.json()
    assert seventh["chapter"]["chapter_id"] == "eng_c4_ch07"
    assert seventh["chapter"]["title"] == "Fit Body, Fit Mind, Fit Nation"
    assert seventh["chapter"]["unit_title"] == "Fun with Games"
    _assert_current_activity_matches_catalog(seventh)
    _assert_no_hidden_keys(seventh)


def test_completed_class_four_seventh_chapter_opens_lagori_champions(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    assert seventh["chapter"]["chapter_id"] == "eng_c4_ch07"
    completed_seventh = _complete_current_curriculum_session(seventh, client)

    assert completed_seventh["status"] == "complete"
    assert completed_seventh["next_available_chapter"]["chapter_id"] == "eng_c4_ch08"
    assert completed_seventh["next_available_chapter"]["title"] == "The Lagori Champions"
    assert completed_seventh["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["chapter_id"] == "eng_c4_ch08"
    assert landing["chapters_preview"][7]["title"] == "The Lagori Champions"
    assert landing["chapters_preview"][7]["status"] == "ready"

    eighth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eighth_response.status_code == 200
    eighth = eighth_response.json()
    assert eighth["chapter"]["chapter_id"] == "eng_c4_ch08"
    assert eighth["chapter"]["title"] == "The Lagori Champions"
    assert eighth["chapter"]["unit_title"] == "Fun with Games"
    _assert_current_activity_matches_catalog(eighth)
    _assert_no_hidden_keys(eighth)


def test_completed_class_four_eighth_chapter_opens_hekko(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert eighth["chapter"]["chapter_id"] == "eng_c4_ch08"
    completed_eighth = _complete_current_curriculum_session(eighth, client)

    assert completed_eighth["status"] == "complete"
    assert completed_eighth["next_available_chapter"]["chapter_id"] == "eng_c4_ch09"
    assert completed_eighth["next_available_chapter"]["title"] == "Hekko"
    assert completed_eighth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["chapter_id"] == "eng_c4_ch09"
    assert landing["chapters_preview"][8]["title"] == "Hekko"
    assert landing["chapters_preview"][8]["status"] == "ready"

    ninth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert ninth_response.status_code == 200
    ninth = ninth_response.json()
    assert ninth["chapter"]["chapter_id"] == "eng_c4_ch09"
    assert ninth["chapter"]["title"] == "Hekko"
    assert ninth["chapter"]["unit_title"] == "Fun with Games"
    _assert_current_activity_matches_catalog(ninth)
    _assert_no_hidden_keys(ninth)


def test_completed_class_four_ninth_chapter_opens_the_swing(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert ninth["chapter"]["chapter_id"] == "eng_c4_ch09"
    completed_ninth = _complete_current_curriculum_session(ninth, client)

    assert completed_ninth["status"] == "complete"
    assert completed_ninth["next_available_chapter"]["chapter_id"] == "eng_c4_ch10"
    assert completed_ninth["next_available_chapter"]["title"] == "The Swing"
    assert completed_ninth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["status"] == "complete"
    assert landing["chapters_preview"][9]["chapter_id"] == "eng_c4_ch10"
    assert landing["chapters_preview"][9]["title"] == "The Swing"
    assert landing["chapters_preview"][9]["status"] == "ready"

    tenth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert tenth_response.status_code == 200
    tenth = tenth_response.json()
    assert tenth["chapter"]["chapter_id"] == "eng_c4_ch10"
    assert tenth["chapter"]["title"] == "The Swing"
    assert tenth["chapter"]["unit_title"] == "Up High"
    _assert_current_activity_matches_catalog(tenth)
    _assert_no_hidden_keys(tenth)


def test_completed_class_four_tenth_chapter_opens_magical_mountains(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert tenth["chapter"]["chapter_id"] == "eng_c4_ch10"
    completed_tenth = _complete_current_curriculum_session(tenth, client)

    assert completed_tenth["status"] == "complete"
    assert completed_tenth["next_available_chapter"]["chapter_id"] == "eng_c4_ch11"
    assert completed_tenth["next_available_chapter"]["title"] == "A Journey to the Magical Mountains"
    assert completed_tenth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
        "eng_c4_ch10",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["status"] == "complete"
    assert landing["chapters_preview"][9]["status"] == "complete"
    assert landing["chapters_preview"][10]["chapter_id"] == "eng_c4_ch11"
    assert landing["chapters_preview"][10]["title"] == "A Journey to the Magical Mountains"
    assert landing["chapters_preview"][10]["status"] == "ready"

    eleventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eleventh_response.status_code == 200
    eleventh = eleventh_response.json()
    assert eleventh["chapter"]["chapter_id"] == "eng_c4_ch11"
    assert eleventh["chapter"]["title"] == "A Journey to the Magical Mountains"
    assert eleventh["chapter"]["unit_title"] == "Up High"
    _assert_current_activity_matches_catalog(eleventh)
    _assert_no_hidden_keys(eleventh)


def test_completed_class_four_eleventh_chapter_opens_maheshwar(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()
    assert eleventh["chapter"]["chapter_id"] == "eng_c4_ch11"
    completed_eleventh = _complete_current_curriculum_session(eleventh, client)

    assert completed_eleventh["status"] == "complete"
    assert completed_eleventh["next_available_chapter"]["chapter_id"] == "eng_c4_ch12"
    assert completed_eleventh["next_available_chapter"]["title"] == "Maheshwar"
    assert completed_eleventh["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
        "eng_c4_ch10",
        "eng_c4_ch11",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 12 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["status"] == "complete"
    assert landing["chapters_preview"][9]["status"] == "complete"
    assert landing["chapters_preview"][10]["status"] == "complete"
    assert landing["chapters_preview"][11]["chapter_id"] == "eng_c4_ch12"
    assert landing["chapters_preview"][11]["title"] == "Maheshwar"
    assert landing["chapters_preview"][11]["status"] == "ready"

    twelfth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert twelfth_response.status_code == 200
    twelfth = twelfth_response.json()
    assert twelfth["chapter"]["chapter_id"] == "eng_c4_ch12"
    assert twelfth["chapter"]["title"] == "Maheshwar"
    assert twelfth["chapter"]["unit_title"] == "Up High"
    _assert_current_activity_matches_catalog(twelfth)
    _assert_no_hidden_keys(twelfth)


def test_class_four_twelfth_chapter_completion_finishes_authored_class(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eleventh, client)
    twelfth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert twelfth["chapter"]["chapter_id"] == "eng_c4_ch12"
    completed_twelfth = _complete_current_curriculum_session(twelfth, client)

    assert completed_twelfth["status"] == "complete"
    assert completed_twelfth["next_available_chapter"] is None
    assert completed_twelfth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
        "eng_c4_ch10",
        "eng_c4_ch11",
        "eng_c4_ch12",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "All available target-class chapters are complete."
    for chapter in landing["chapters_preview"]:
        assert chapter["status"] == "complete"


def test_class_five_target_ready_placement_opens_papas_spectacles(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["target_class_no"] == 5
    assert landing["book_title"] == "Santoor"
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 1 when you are ready."
    assert landing["chapters_preview"][0]["chapter_id"] == "eng_c5_ch01"
    assert landing["chapters_preview"][0]["title"] == "Papa's Spectacles"
    assert landing["chapters_preview"][0]["status"] == "ready"
    assert landing["chapters_preview"][1]["chapter_id"] == "eng_c5_ch02"
    assert landing["chapters_preview"][1]["status"] == "locked_next"

    response = client.post("/school/curriculum/start", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["chapter"]["chapter_id"] == "eng_c5_ch01"
    assert body["chapter"]["title"] == "Papa's Spectacles"
    assert body["chapter"]["unit_title"] == "Let's Have Fun"
    assert (
        body["current_activity"]["level_id"]
        == "papas_spectacles_poem_comprehension"
    )
    teaching_block = body["current_activity"]["teaching_block"].lower()
    assert "because" in teaching_block
    assert "passage evidence" in teaching_block
    _assert_no_hidden_keys(body)


def test_class_five_completed_first_chapter_opens_gone_with_the_scooter(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    assert first["chapter"]["chapter_id"] == "eng_c5_ch01"
    completed = _complete_current_curriculum_session(first, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch02"
    assert completed["next_available_chapter"]["title"] == "Gone with the Scooter"
    assert completed["completed_chapter_ids"] == ["eng_c5_ch01"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 2 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["chapter_id"] == "eng_c5_ch02"
    assert landing["chapters_preview"][1]["title"] == "Gone with the Scooter"
    assert landing["chapters_preview"][1]["status"] == "ready"

    second_response = client.post("/school/curriculum/start", headers=AUTH)
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["chapter"]["chapter_id"] == "eng_c5_ch02"
    assert second["chapter"]["title"] == "Gone with the Scooter"
    assert second["chapter"]["unit_title"] == "Let's Have Fun"
    _assert_current_activity_matches_catalog(second)
    _assert_no_hidden_keys(second)


def test_class_five_second_chapter_completion_opens_the_rainbow(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    assert second["chapter"]["chapter_id"] == "eng_c5_ch02"
    completed = _complete_current_curriculum_session(second, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch03"
    assert completed["next_available_chapter"]["title"] == "The Rainbow"
    assert completed["completed_chapter_ids"] == ["eng_c5_ch01", "eng_c5_ch02"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 3 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["chapter_id"] == "eng_c5_ch03"
    assert landing["chapters_preview"][2]["title"] == "The Rainbow"
    assert landing["chapters_preview"][2]["status"] == "ready"

    third_response = client.post("/school/curriculum/start", headers=AUTH)
    assert third_response.status_code == 200
    third = third_response.json()
    assert third["chapter"]["chapter_id"] == "eng_c5_ch03"
    assert third["chapter"]["title"] == "The Rainbow"
    assert third["chapter"]["unit_title"] == "My Colourful World"
    _assert_current_activity_matches_catalog(third)
    _assert_no_hidden_keys(third)


def test_class_five_third_chapter_completion_opens_the_wise_parrot(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    assert third["chapter"]["chapter_id"] == "eng_c5_ch03"
    completed = _complete_current_curriculum_session(third, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch04"
    assert completed["next_available_chapter"]["title"] == "The Wise Parrot"
    assert completed["completed_chapter_ids"] == ["eng_c5_ch01", "eng_c5_ch02", "eng_c5_ch03"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 4 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["chapter_id"] == "eng_c5_ch04"
    assert landing["chapters_preview"][3]["title"] == "The Wise Parrot"
    assert landing["chapters_preview"][3]["status"] == "ready"

    fourth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fourth_response.status_code == 200
    fourth = fourth_response.json()
    assert fourth["chapter"]["chapter_id"] == "eng_c5_ch04"
    assert fourth["chapter"]["title"] == "The Wise Parrot"
    assert fourth["chapter"]["unit_title"] == "My Colourful World"
    _assert_current_activity_matches_catalog(fourth)
    _assert_no_hidden_keys(fourth)


def test_class_five_fourth_chapter_completion_opens_and_completes_the_frog(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    for expected_chapter_id in ("eng_c5_ch01", "eng_c5_ch02", "eng_c5_ch03"):
        body = client.post("/school/curriculum/start", headers=AUTH).json()
        assert body["chapter"]["chapter_id"] == expected_chapter_id
        _complete_current_curriculum_session(body, client)

    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert fourth["chapter"]["chapter_id"] == "eng_c5_ch04"
    completed = _complete_current_curriculum_session(fourth, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch05"
    assert completed["next_available_chapter"]["title"] == "The Frog"
    assert completed["completed_chapter_ids"] == [
        "eng_c5_ch01",
        "eng_c5_ch02",
        "eng_c5_ch03",
        "eng_c5_ch04",
    ]
    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["chapter_id"] == "eng_c5_ch05"
    assert landing["chapters_preview"][4]["title"] == "The Frog"
    assert landing["chapters_preview"][4]["status"] == "ready"

    fifth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fifth_response.status_code == 200
    fifth = fifth_response.json()
    assert fifth["chapter"]["chapter_id"] == "eng_c5_ch05"
    assert fifth["chapter"]["title"] == "The Frog"
    assert fifth["chapter"]["unit_title"] == "Water"
    _assert_current_activity_matches_catalog(fifth)
    _assert_no_hidden_keys(fifth)

    completed_fifth = _complete_current_curriculum_session(fifth, client)

    assert completed_fifth["status"] == "complete"
    assert completed_fifth["phase"] == "complete"
    assert completed_fifth["chapter_assessment"]["status"] == "passed"
    assert completed_fifth["chapter_assessment"]["last_result"]["passed"] is True
    assert completed_fifth["next_available_chapter"] == {
        "chapter_id": "eng_c5_ch06",
        "chapter_no": 6,
        "title": "What a Tank!",
        "book_title": "Santoor",
        "unit_title": "Water",
        "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf",
        "source_note": (
            "NCERT structural alignment only. All learner-facing passages, examples, "
            "questions, feedback authorities, and assessments are Zidd-authored originals."
        ),
    }
    assert completed_fifth["completed_chapter_ids"] == [
        "eng_c5_ch01",
        "eng_c5_ch02",
        "eng_c5_ch03",
        "eng_c5_ch04",
        "eng_c5_ch05",
    ]
    _assert_no_hidden_keys(completed_fifth)


def test_frog_chapter_check_failure_runs_remediation_then_alternate_form(store):
    session_id = str(uuid4())
    initial = _seed_frog_chapter_check_session(store, session_id=session_id)
    first_form_ids = set(initial["chapter_assessment"]["selected_item_ids"])
    client = TestClient(app)
    response = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    _assert_no_hidden_keys(body)

    body = _drive_frog_chapter_check(body, client, fail_first=True)

    assert body["phase"] == "remediation"
    assert body["chapter_assessment"]["status"] == "remediation"
    assert body["chapter_assessment"]["last_result"]["passed"] is False
    row = _run(store.get_school_session("test_user", session_id))
    assert row["state_json"]["chapter_assessment"]["attempt_history"][-1][
        "remediation_skill_ids"
    ]
    assert body["current_activity"]["kind"] == "masterclass"
    _assert_no_hidden_keys(body)

    body = _drive_frog_remediation(body, client)

    assert body["phase"] == "chapter_check"
    assert body["chapter_assessment"]["attempt_no"] == 2
    row = _run(store.get_school_session("test_user", session_id))
    second_form_ids = set(row["state_json"]["chapter_assessment"]["selected_item_ids"])
    assert first_form_ids.isdisjoint(second_form_ids)

    completed = _drive_frog_chapter_check(body, client, fail_first=False)

    assert completed["status"] == "complete", completed["chapter_assessment"]["last_result"]
    assert completed["phase"] == "complete"
    assert completed["chapter_assessment"]["status"] == "passed"
    assert completed["chapter_assessment"]["last_result"]["passed"] is True
    assert "eng_c5_ch05" in completed["completed_chapter_ids"]
    _assert_no_hidden_keys(completed)


def test_frog_second_failed_chapter_check_enters_needs_support_without_unlock(store):
    session_id = str(uuid4())
    _seed_frog_chapter_check_session(store, session_id=session_id)
    client = TestClient(app)
    body = client.get(f"/school/curriculum/{session_id}", headers=AUTH).json()

    body = _drive_frog_chapter_check(body, client, fail_first=True)
    body = _drive_frog_remediation(body, client)
    body = _drive_frog_chapter_check(body, client, fail_first=True)

    assert body["status"] == "active"
    assert body["phase"] == "needs_support"
    assert body["current_activity"] is None
    assert body["chapter_assessment"]["status"] == "needs_support"
    assert body["chapter_assessment"]["last_result"]["passed"] is False
    row = _run(store.get_school_session("test_user", session_id))
    assert row["state_json"]["chapter_assessment"]["attempt_history"][-1][
        "remediation_skill_ids"
    ]
    assert "eng_c5_ch05" not in body["completed_chapter_ids"]
    assert body["next_available_chapter"] is None
    _assert_no_hidden_keys(body)


def test_wise_parrot_chapter_covers_the_full_core_learning_surface():
    levels = {
        level["level_id"]: level
        for level in curriculum.CLASS_5_WISE_PARROT_CHAPTER["levels"]
    }
    required_level_ids = {
        "wise_parrot_story_sequence",
        "wise_parrot_freedom_reason",
        "wise_parrot_words_phrases",
        "wise_parrot_collective_nouns",
        "wise_parrot_present_perfect",
        "wise_parrot_bird_sanctuary",
        "wise_parrot_ai_oi_sounds",
        "wise_parrot_opinion_reason",
        "wise_parrot_story_continuation",
        "wise_parrot_bird_feeder_steps",
    }
    assert required_level_ids <= set(levels)

    continuation_check = levels["wise_parrot_story_continuation"]["checks"]["independent_check"]
    assert continuation_check["response_mode"] == "paragraph"
    assert continuation_check["evaluation_mode"] == "llm_rubric"
    assert continuation_check["pass_score"] == 0.75
    assert 60 <= len(WISE_PARROT_STORY_CONTINUATION.split()) <= 90
    assert curriculum._open_answer_preflight(
        continuation_check,
        WISE_PARROT_STORY_CONTINUATION,
    ) is True
    assert curriculum._open_answer_preflight(continuation_check, "The parrot flew away.") is False

    opinion_check = levels["wise_parrot_opinion_reason"]["checks"]["independent_check"]
    assert curriculum._answer_matches(
        opinion_check,
        "He should have unlocked the cage because animals deserve to choose where they live.",
    ) is True

    feeder_check = levels["wise_parrot_bird_feeder_steps"]["checks"]["independent_check"]
    assert "steps" in feeder_check["prompt"].lower()
    assert feeder_check["answer_rule"] == "bird_feeder_procedure"
    assert curriculum._answer_matches(
        feeder_check,
        "First clean the container, next add fresh grains and water, then place it safely, and finally clean it regularly.",
    ) is True


def test_backend_owns_the_open_answer_rubric_gate():
    activity = {
        "activity_id": "wise_parrot_story_continuation:independent_check:1",
        "skill_ids": ["writing.summary_own_words", "writing.reason_answer"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "rubric_criteria": [
            {"id": "continues_story", "required": True},
            {"id": "narrative_coherence", "required": True},
            {"id": "language_control", "required": False},
        ],
    }
    inflated_model_result = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": list(activity["skill_ids"]),
        "score": 0.99,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {"id": "continues_story", "met": True, "quality": 0.9, "evidence_quote": "the parrot"},
            {"id": "narrative_coherence", "met": False, "quality": 0.2, "evidence_quote": "clock sandwich"},
            {"id": "language_control", "met": True, "quality": 0.9, "evidence_quote": "flew"},
        ],
        "misconception_tags": ["incoherent_sequence"],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Model claimed this was nearly complete.",
    }

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        inflated_model_result,
        answer="the parrot flew through a clock sandwich",
    )

    assert decision["correct"] is False
    assert decision["score"] < 0.75
    assert decision["model_score"] == 0.99
    assert "narrative_coherence" in decision["missing_criteria"]


def test_ambiguous_concept_answer_uses_semantic_evaluator_before_progression(
    store,
    monkeypatch,
):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=next(
            chapter
            for chapter in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if chapter["chapter_id"] == "eng_c5_ch05"
        ),
        level_id=None,
    )
    answer = (
        "It hopped across moss and used the water-filled ditch, but the ditch "
        "did not cover its eyes."
    )
    captured = []

    async def semantic_evaluator(activity, learner_answer):
        captured.append(activity)
        quotes = {
            "land_evidence": "hopped across moss",
            "water_evidence": "used the water-filled ditch",
        }
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=1.0,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=1.0,
                    evidence_quote=quotes[criterion["id"]],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="Both habitat uses are supported.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        semantic_evaluator,
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "frog_between_two_homes:independent_check:1",
            "answer": answer,
        },
    )

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0]["evaluation_mode"] == "llm_rubric"
    assert [criterion["id"] for criterion in captured[0]["rubric_criteria"]] == [
        "land_evidence",
        "water_evidence",
    ]
    assert response.json()["last_feedback"]["correct"] is True
    event = store.learning_events[-1]
    assert event["evidence_json"]["evaluation_mode"] == "semantic_llm_rubric"


def test_open_answer_provider_failure_does_not_mutate_session_or_evidence(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )

    async def unavailable(_activity, _answer):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", unavailable)
    before_event_count = len(store.learning_events)
    client = TestClient(app)
    response = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "open_answer_evaluation_unavailable"
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state
    assert len(store.learning_events) == before_event_count


def test_open_answer_is_durably_queued_before_any_curriculum_progress(store, monkeypatch):
    """A semantic answer acknowledges quickly and cannot advance before its worker."""

    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=next(
            chapter
            for chapter in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if chapter["chapter_id"] == "eng_c5_ch05"
        ),
        level_id=None,
    )
    queued: list[dict[str, Any]] = []
    original_claim_and_enqueue = store.claim_and_enqueue_school_evaluation_job

    async def claim_and_enqueue(**kwargs):
        queued.append(copy.deepcopy(kwargs))
        return await original_claim_and_enqueue(**kwargs)

    monkeypatch.setattr(
        store,
        "claim_and_enqueue_school_evaluation_job",
        claim_and_enqueue,
        raising=False,
    )

    activity_id = (
        "frog_poem_meaning:frog_poem_meaning:independent_application:"
        "frog_poem_meaning:independent:1:1"
    )
    answer = (
        "The jump feels very high and exciting, but the frog does not reach clouds; "
        "this is not a scientific height claim."
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity_id,
            "answer": answer,
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "status": "awaiting_evaluation",
        "session_id": session_id,
        "activity_id": activity_id,
        "state_url": "/school/state",
    }
    assert len(queued) == 1
    assert queued[0]["user_id"] == "test_user"
    assert queued[0]["session_id"] == session_id
    assert queued[0]["activity_id"] == activity_id
    assert queued[0]["raw_answer"] == answer
    assert queued[0]["expected_state_json"] == original_state
    assert queued[0]["flow_type"] == "curriculum"
    assert queued[0]["evaluation_mode"] == "llm_rubric"
    assert _run(store.get_school_session("test_user", session_id))["state_json"] == original_state
    assert not [event for event in store.learning_events if event["session_id"] == session_id]
    request = _run(
        store.get_school_answer_request(
            "test_user",
            session_id,
            activity_id,
        )
    )
    assert request is not None
    assert request["status"] == "processing"

    # The browser refreshes this endpoint immediately after the fast answer
    # acknowledgement. It must expose a stable passive state, not another
    # actionable copy of the same activity while the durable worker owns it.
    state_response = TestClient(app).get("/school/state", headers=AUTH)
    assert state_response.status_code == 200
    pending_state = state_response.json()
    assert pending_state["status"] == "awaiting_evaluation"
    assert pending_state["active_flow"] == "curriculum"
    assert pending_state["active_session_id"] == session_id
    assert pending_state["next_action"] is None
    assert pending_state["allowed_next_actions"] == []


def test_queued_open_answer_uses_the_post_reconciliation_state_snapshot(
    store,
    monkeypatch,
):
    """The worker must receive the state the answer route actually serves."""

    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=next(
            chapter
            for chapter in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if chapter["chapter_id"] == "eng_c5_ch05"
        ),
        level_id=None,
    )
    reconciled_state = copy.deepcopy(original_state)
    reconciled_state["hot_session_memory"] = {
        **dict(reconciled_state.get("hot_session_memory") or {}),
        "reconciled_before_queue": True,
    }
    queued: list[dict[str, Any]] = []

    async def reconciled_row(*, row, **_kwargs):
        return {**row, "state_json": copy.deepcopy(reconciled_state)}

    async def claim_and_enqueue(**kwargs):
        queued.append(copy.deepcopy(kwargs))
        return {"outcome": "queued", "job": {"status": "queued"}}

    monkeypatch.setattr(
        school_rebuild_routes,
        "_reconcile_saved_curriculum_session",
        reconciled_row,
    )
    monkeypatch.setattr(
        store,
        "claim_and_enqueue_school_evaluation_job",
        claim_and_enqueue,
        raising=False,
    )

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": (
                "frog_poem_meaning:frog_poem_meaning:independent_application:"
                "frog_poem_meaning:independent:1:1"
            ),
            "answer": (
                "The jump feels very high and exciting, but the frog does not reach clouds; "
                "this is not a scientific height claim."
            ),
        },
    )

    assert response.status_code == 200
    assert len(queued) == 1
    assert queued[0]["expected_state_json"] == reconciled_state


def test_semantic_answer_uses_one_atomic_claim_and_enqueue_operation(
    store,
    monkeypatch,
):
    """A semantic submit cannot leave a live answer claim without its job."""

    session_id = str(uuid4())
    expected_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=next(
            chapter
            for chapter in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if chapter["chapter_id"] == "eng_c5_ch05"
        ),
        level_id=None,
    )
    atomic_calls: list[dict[str, Any]] = []

    async def atomic_claim_and_enqueue(**kwargs):
        atomic_calls.append(copy.deepcopy(kwargs))
        return {"outcome": "queued", "job": {"status": "queued"}}

    async def split_claim_must_not_run(*_args, **_kwargs):
        raise AssertionError("semantic answers must claim and enqueue atomically")

    monkeypatch.setattr(
        store,
        "claim_and_enqueue_school_evaluation_job",
        atomic_claim_and_enqueue,
        raising=False,
    )
    monkeypatch.setattr(store, "claim_school_answer_request", split_claim_must_not_run)

    answer = (
        "The jump feels very high and exciting, but the frog does not reach clouds; "
        "this is not a scientific height claim."
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": (
                "frog_poem_meaning:frog_poem_meaning:independent_application:"
                "frog_poem_meaning:independent:1:1"
            ),
            "answer": answer,
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "awaiting_evaluation"
    assert len(atomic_calls) == 1
    assert atomic_calls[0]["user_id"] == "test_user"
    assert atomic_calls[0]["session_id"] == session_id
    assert atomic_calls[0]["raw_answer"] == answer
    assert atomic_calls[0]["expected_state_json"] == expected_state
    assert atomic_calls[0]["flow_type"] == "curriculum"
    assert atomic_calls[0]["evaluation_mode"] == "llm_rubric"


def test_fully_authored_supported_curriculum_answer_bypasses_queue_and_provider(
    store,
    monkeypatch,
):
    """Literal, non-certifying support must not wait for a model worker."""

    session_id = str(uuid4())
    chapter = copy.deepcopy(
        next(
            candidate
            for candidate in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if candidate["chapter_id"] == "eng_c5_ch01"
        )
    )
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=chapter,
        level_id="papas_spectacles_poem_to_story",
    )
    level = state["levels"][state["current_level_index"]]
    level.update(
        {
            "v2_support_mode": "bridge",
            "v2_trigger_skill_ids": [
                "grammar.tense_usage",
                "writing.complete_sentence",
            ],
            "v2_active_misconception_tags": ["tense_shift"],
            "v2_forced_support_kind": "revision_level_1",
        }
    )
    state = curriculum.normalize_curriculum_state(state)
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage=str(state["current_level_index"]),
            linked_session_id=None,
            profile_version_id=state["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=state,
        )
    )
    activity = curriculum._current_activity(state)
    assert activity is not None
    assert activity["kind"] == "v2_support"
    assert activity["evidence_role"] == "supported"
    assert activity["certifying_language"] is None
    assert activity["semantic_evidence_policy"] == "literal_aliases"

    async def queue_must_not_run(**_kwargs):
        raise AssertionError("fully authored supported practice must not queue")

    monkeypatch.setattr(
        store,
        "claim_and_enqueue_school_evaluation_job",
        queue_must_not_run,
        raising=False,
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity["activity_id"],
            "answer": "Mira opened the gate and walked into the garden.",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["last_feedback"]["correct"] is True


def test_open_answer_provider_schema_failure_returns_structured_503(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )

    async def invalid_schema(_activity, _answer):
        return SchoolV3RubricEvaluation.model_validate(
            {
                "schema_version": "school-v3-rubric-1",
                "item_id": "rainbow_journey_writing:independent_check:1",
                "skill_ids": ["writing.summary_own_words"],
                "score": 4,
                "confidence": 0.9,
                "language_detected": "en",
                "criteria": [
                    {
                        "id": "journey_structure",
                        "met": True,
                        "quality": 0.9,
                        "evidence_quote": "Last Sunday",
                    }
                ],
                "misconception_tags": [],
                "blockers": [],
                "needs_human_review": False,
                "feedback_to_learner": "Invalid provider score scale.",
            }
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        invalid_schema,
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "open_answer_evaluation_unavailable"
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state


def test_open_answer_server_deadline_prevents_late_progress_mutation(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )

    async def too_slow(_activity, _answer):
        await asyncio.sleep(0.05)
        raise AssertionError("deadline should cancel the evaluator")

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", too_slow)
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS",
        0.01,
        raising=False,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: 0.01,
        raising=False,
    )
    before_event_count = len(store.learning_events)
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "open_answer_evaluation_timeout"
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state
    assert len(store.learning_events) == before_event_count


def test_local_open_answer_evaluator_has_no_server_deadline(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )

    async def slow_local_success(activity, answer):
        await asyncio.sleep(0.03)
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        slow_local_success,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS",
        0.01,
        raising=False,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: None,
        raising=False,
    )

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 200
    assert response.json()["progress"]["completed_levels"] == (
        int(original_state["current_level_index"]) + 1
    )
    assert response.json()["last_feedback"]["correct"] is True


def test_structurally_incomplete_open_answer_skips_model_and_opens_bridge(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    call_count = 0

    async def should_not_run(_activity, _answer):
        nonlocal call_count
        call_count += 1
        raise AssertionError("preflight failure must not call the model")

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", should_not_run)
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "wise_parrot_story_continuation:independent_check:1",
            "answer": "The parrot flew away.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    _assert_no_hidden_keys(body)
    assert call_count == 0
    assert body["current_activity"]["kind"] == "bridge"
    assert body["progress"]["completed_levels"] == 8
    event = store.learning_events[-1]
    assert event["score"] == 0.0
    assert "open_answer_preflight_failed" in event["blockers"]


def test_inflated_open_answer_model_score_cannot_advance_required_gap(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )

    async def inflated(activity, answer):
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.99,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=criterion["id"] != "narrative_coherence",
                    quality=0.2 if criterion["id"] == "narrative_coherence" else 0.9,
                    evidence_quote="the parrot flew towards the forest",
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=["incoherent_sequence"],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The model gave this a high headline score.",
        )

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", inflated)
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "wise_parrot_story_continuation:independent_check:1",
            "answer": WISE_PARROT_STORY_CONTINUATION,
        },
    )

    assert response.status_code == 200
    body = response.json()
    _assert_no_hidden_keys(body)
    assert body["current_activity"]["kind"] == "bridge"
    assert body["progress"]["completed_levels"] == 8
    event = store.learning_events[-1]
    assert event["score"] < 0.75
    assert event["evidence_json"]["model_score"] == 0.99
    assert any(
        criterion["id"] == "narrative_coherence" and criterion["met"] is False
        for criterion in event["criteria_json"]
    )


def test_curriculum_attempt_store_boundary_rolls_back_event_and_state_together(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    session_write = {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "current_stage": "8",
        "linked_session_id": None,
        "state_json": {**original_state, "last_feedback": {"message": "should roll back"}},
    }
    learning_event = {
        "source_event_key": "school_rebuild:curriculum:atomic:test",
        "user_id": "test_user",
        "domain": "school",
        "task_type": "school_rebuild_curriculum",
        "module_id": "wise_parrot_opinion_reason",
        "session_id": session_id,
        "node_id": "activity",
        "skill_id": "curriculum.wise_parrot_opinion_reason",
        "source": "school_rebuild",
    }
    original_upsert = store.upsert_school_session

    async def fail_after_session_write(**kwargs):
        await original_upsert(**kwargs)
        raise RuntimeError("simulated session write failure")

    monkeypatch.setattr(store, "upsert_school_session", fail_after_session_write)

    with pytest.raises(RuntimeError, match="simulated session write failure"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event=learning_event,
                school_session=session_write,
                expected_state_json=original_state,
            )
        )

    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state
    assert not any(
        event.get("source_event_key") == learning_event["source_event_key"]
        for event in store.learning_events
    )


def test_curriculum_attempt_rejects_state_changed_by_another_submit(store):
    session_id = str(uuid4())
    expected_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    newer_state = copy.deepcopy(expected_state)
    newer_state["last_feedback"] = {"message": "another request committed first"}
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="7",
            linked_session_id=None,
            state_json=newer_state,
        )
    )
    event_key = "school_rebuild:curriculum:stale:test"

    with pytest.raises(ValueError, match="stale_school_answer_session"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={
                    "source_event_key": event_key,
                    "user_id": "test_user",
                    "domain": "school",
                    "task_type": "school_rebuild_curriculum",
                    "module_id": "wise_parrot_opinion_reason",
                    "session_id": session_id,
                    "node_id": "activity",
                    "skill_id": "curriculum.wise_parrot_opinion_reason",
                    "source": "school_rebuild",
                },
                school_session={
                    "session_id": session_id,
                    "user_id": "test_user",
                    "api_version": "rebuild",
                    "flow_type": "curriculum",
                    "subject_id": "english",
                    "class_no": 5,
                    "status": "active",
                    "current_stage": "8",
                    "linked_session_id": None,
                    "state_json": expected_state,
                },
                expected_state_json=expected_state,
            )
        )

    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == newer_state
    assert not any(event.get("source_event_key") == event_key for event in store.learning_events)


def test_in_memory_curriculum_attempt_boundary_serializes_concurrent_writers(store, monkeypatch):
    session_id = str(uuid4())
    expected_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    active_writers = 0
    max_active_writers = 0
    original_record = store.record_learning_event

    async def overlapping_record(**kwargs):
        nonlocal active_writers, max_active_writers
        active_writers += 1
        max_active_writers = max(max_active_writers, active_writers)
        await asyncio.sleep(0.02)
        await original_record(**kwargs)
        active_writers -= 1

    monkeypatch.setattr(store, "record_learning_event", overlapping_record)

    def event(label: str) -> dict[str, Any]:
        return {
            "source_event_key": f"school_rebuild:curriculum:concurrent:{label}",
            "user_id": "test_user",
            "domain": "school",
            "task_type": "school_rebuild_curriculum",
            "module_id": "wise_parrot_opinion_reason",
            "session_id": session_id,
            "node_id": f"activity-{label}",
            "skill_id": "curriculum.wise_parrot_opinion_reason",
            "source": "school_rebuild",
        }

    def session_write(label: str) -> dict[str, Any]:
        state = copy.deepcopy(expected_state)
        state["last_feedback"] = {"message": label}
        return {
            "session_id": session_id,
            "user_id": "test_user",
            "api_version": "rebuild",
            "flow_type": "curriculum",
            "subject_id": "english",
            "class_no": 5,
            "status": "active",
            "current_stage": "8",
            "linked_session_id": None,
            "state_json": state,
        }

    async def compete():
        return await asyncio.gather(
            store.persist_school_curriculum_attempt(
                learning_event=event("first"),
                school_session=session_write("first"),
                expected_state_json=expected_state,
            ),
            store.persist_school_curriculum_attempt(
                learning_event=event("second"),
                school_session=session_write("second"),
                expected_state_json=expected_state,
            ),
            return_exceptions=True,
        )

    results = _run(compete())

    assert max_active_writers == 1
    assert sum(result is None for result in results) == 1
    assert sum(
        isinstance(result, ValueError) and str(result) == "stale_school_answer_session"
        for result in results
    ) == 1
    assert len(
        [event for event in store.learning_events if "curriculum:concurrent" in event["source_event_key"]]
    ) == 1


def test_curriculum_answer_avoids_redundant_profile_and_post_commit_reads(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    session_reads = 0
    profile_reads = 0
    original_get_session = store.get_school_session
    original_get_profile = store.get_profile

    async def count_session_read(user_id, requested_session_id):
        nonlocal session_reads
        session_reads += 1
        return await original_get_session(user_id, requested_session_id)

    async def count_profile_read(user_id):
        nonlocal profile_reads
        profile_reads += 1
        return await original_get_profile(user_id)

    monkeypatch.setattr(store, "get_school_session", count_session_read)
    monkeypatch.setattr(store, "get_profile", count_profile_read)

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "wise_parrot_opinion_reason:independent_check:1",
            "answer": "He should unlock the cage because the parrot deserves freedom.",
        },
    )

    assert response.status_code == 200
    assert session_reads == 1
    assert profile_reads == 0


def test_rainbow_travel_check_accepts_an_original_past_tense_journey_sentence():
    travel_level = next(
        level
        for level in curriculum.CLASS_5_RAINBOW_CHAPTER["levels"]
        if level["level_id"] == "rainbow_travel_paragraph"
    )
    check = travel_level["checks"]["independent_check"]

    assert curriculum._answer_matches(check, "Yesterday I went to Jaipur by train.") is True
    assert curriculum._answer_matches(check, "I went home.") is True
    assert curriculum._answer_matches(check, "went") is False
    assert curriculum._answer_matches(check, "I will go to Jaipur tomorrow.") is False


def test_rainbow_chapter_covers_the_full_core_learning_surface():
    levels = {
        level["level_id"]: level
        for level in curriculum.CLASS_5_RAINBOW_CHAPTER["levels"]
    }
    required_level_ids = {
        "rainbow_image_bridge",
        "rainbow_word_meanings",
        "rainbow_reference_words",
        "rainbow_rhyme_sound",
        "rainbow_compound_words",
        "rainbow_noun_verb_use",
        "rainbow_opposites",
        "rainbow_travel_paragraph",
        "rainbow_journey_writing",
        "rainbow_colour_order",
        "rainbow_natural_human_made",
    }
    assert required_level_ids <= set(levels)

    comparison_check = levels["rainbow_image_bridge"]["checks"]["independent_check"]
    assert "why" in comparison_check["prompt"].lower()
    assert curriculum._answer_matches(
        comparison_check,
        "It seems to build a colourful bridge from earth to sky.",
    ) is True

    compound_checks = levels["rainbow_compound_words"]["checks"]
    assert compound_checks["masterclass"]["passage"] != compound_checks["independent_check"]["passage"]

    paragraph_check = levels["rainbow_journey_writing"]["checks"]["independent_check"]
    assert paragraph_check["response_mode"] == "paragraph"
    assert paragraph_check["evaluation_mode"] == "llm_rubric"
    assert paragraph_check["pass_score"] == 0.75
    assert len(RAINBOW_JOURNEY_PARAGRAPH.split()) == 80
    assert curriculum._open_answer_preflight(paragraph_check, RAINBOW_JOURNEY_PARAGRAPH) is True
    assert curriculum._open_answer_preflight(paragraph_check, "I went home.") is False
    repetitive_word_salad = " ".join(["I", "went", "bus"] * 27)
    assert len(repetitive_word_salad.split()) == 81
    assert curriculum._open_answer_preflight(paragraph_check, repetitive_word_salad) is False


def test_curriculum_answer_replay_returns_exact_response_and_one_event(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    payload = {
        "activity_id": "wise_parrot_opinion_reason:independent_check:1",
        "answer": "He should unlock the cage because the parrot deserves freedom.",
    }
    client = TestClient(app)

    first = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )
    replay = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert len([event for event in store.learning_events if event["session_id"] == session_id]) == 1


def test_curriculum_answer_same_activity_different_answer_conflicts(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    client = TestClient(app)
    first = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity_id,
            "answer": "He should unlock the cage because the parrot deserves freedom.",
        },
    )
    conflict = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": "Keep the cage locked."},
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "curriculum_answer_conflict"
    assert len([event for event in store.learning_events if event["session_id"] == session_id]) == 1


def test_concurrent_identical_open_answers_invoke_evaluator_once(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )
    started = threading.Event()
    release = threading.Event()
    call_count = 0

    async def blocked_evaluator(activity, answer):
        nonlocal call_count
        call_count += 1
        started.set()
        await asyncio.to_thread(release.wait, 2)
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes, "evaluate_school_open_answer", blocked_evaluator
    )
    payload = {
        "activity_id": "rainbow_journey_writing:independent_check:1",
        "answer": RAINBOW_JOURNEY_PARAGRAPH,
    }

    def submit():
        return TestClient(app).post(
            f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(submit)
        assert started.wait(2)
        concurrent = submit()
        release.set()
        first = first_future.result(timeout=3)

    assert first.status_code == 200
    assert concurrent.status_code in {200, 409}
    if concurrent.status_code == 409:
        assert concurrent.json()["detail"]["code"] == "curriculum_answer_in_progress"
    else:
        assert concurrent.json() == first.json()
    replay = submit()
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert call_count == 1
    assert len([event for event in store.learning_events if event["session_id"] == session_id]) == 1


def test_long_local_evaluation_renews_answer_claim_before_it_can_go_stale(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )
    started = threading.Event()
    call_count = 0

    async def slow_local_evaluator(activity, answer):
        nonlocal call_count
        call_count += 1
        started.set()
        await asyncio.sleep(0.08)
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        slow_local_evaluator,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: None,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_ANSWER_HEARTBEAT_SECONDS",
        0.005,
        raising=False,
    )
    store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS = 0.02
    payload = {
        "activity_id": "rainbow_journey_writing:independent_check:1",
        "answer": RAINBOW_JOURNEY_PARAGRAPH,
    }

    def submit():
        return TestClient(app).post(
            f"/school/curriculum/{session_id}/answer",
            headers=AUTH,
            json=payload,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(submit)
        assert started.wait(1)
        time.sleep(0.05)
        concurrent = submit()
        first = first_future.result(timeout=2)

    assert first.status_code == 200
    assert concurrent.status_code == 409
    assert concurrent.json()["detail"]["code"] == "curriculum_answer_in_progress"
    assert call_count == 1


def test_worker_cancels_evaluation_and_releases_the_answer_when_its_lease_is_lost(
    store,
    monkeypatch,
):
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )
    activity_id = curriculum.current_curriculum_activity_id(state)
    assert activity_id
    answer = (
        "The curve looks like a bridge because it arches over the river "
        "and seems to connect the reeds to the old fort."
    )
    activity = curriculum.curriculum_activity_for_answer(
        state,
        activity_id=activity_id,
    )
    assert activity["evaluation_mode"] == "llm_rubric"
    assert curriculum._open_answer_preflight(activity, answer)
    cancelled = threading.Event()

    async def evaluator_that_must_be_cancelled(_activity, _answer):
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            cancelled.set()
            raise
        raise AssertionError("lost claim must cancel evaluator")

    async def lose_lease(*_args, **_kwargs):
        return False

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluator_that_must_be_cancelled,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_ANSWER_HEARTBEAT_SECONDS",
        0.005,
    )
    monkeypatch.setattr(store, "heartbeat_school_evaluation_job", lose_lease)
    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity_id,
            "answer": answer,
        },
    )

    assert response.status_code == 200, (
        activity_id,
        response.json().get("last_feedback"),
        response.json().get("current_activity"),
        cancelled.is_set(),
    )
    processed = _run(
        evaluation_jobs.run_one_school_evaluation_job(
            store=store,
            processor=school_rebuild_routes.process_school_evaluation_job,
            max_attempts=2,
        )
    )

    assert processed is True
    assert cancelled.wait(0.2)
    job = _run(store.get_school_evaluation_job("test_user", session_id, activity_id))
    request = _run(store.get_school_answer_request("test_user", session_id, activity_id))
    assert job["status"] == "failed"
    assert job["last_error_code"] == "stale_school_evaluation_job"
    assert request["status"] == "failed"
    assert _run(store.get_school_session("test_user", session_id))["state_json"] == state


def test_open_answer_provider_failure_can_be_retried_with_same_request(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id=None,
    )
    attempts = 0

    async def fail_then_succeed(activity, answer):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("provider unavailable")
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"], met=True, quality=0.9, evidence_quote=answer[:120]
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes, "evaluate_school_open_answer", fail_then_succeed
    )
    payload = {
        "activity_id": "rainbow_journey_writing:independent_check:1",
        "answer": RAINBOW_JOURNEY_PARAGRAPH,
    }
    client = TestClient(app)
    failed = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )
    request_row = _run(
        store.get_school_answer_request("test_user", session_id, payload["activity_id"])
    )
    retried = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )

    assert failed.status_code == 503
    assert request_row["status"] == "failed"
    assert retried.status_code == 200
    assert attempts == 2


def test_completed_curriculum_answer_replays_after_session_completion(store):
    session_id = str(uuid4())
    _seed_frog_chapter_check_session(store, session_id=session_id)
    client = TestClient(app)
    body = client.get(f"/school/curriculum/{session_id}", headers=AUTH).json()
    for _ in range(12):
        activity = body["current_activity"]
        body = _answer(body, None, client)
    final_activity = body["current_activity"]
    payload = {
        "activity_id": final_activity["activity_id"],
        "answer": _correct_private_curriculum_answer(
            _private_activity_for_current_body(body)
        ),
    }
    before = len(store.learning_events)
    first = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )
    replay = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )

    assert first.status_code == 200
    assert first.json()["status"] == "complete"
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert len(store.learning_events) == before + 1


def test_failed_curriculum_persist_does_not_complete_answer_request(store, monkeypatch):
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"answer").hexdigest()
    claimed = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    assert claimed["outcome"] == "claimed"
    original_upsert = store.upsert_school_session

    async def fail_after_session_write(**kwargs):
        await original_upsert(**kwargs)
        raise RuntimeError("simulated session write failure")

    monkeypatch.setattr(store, "upsert_school_session", fail_after_session_write)
    with pytest.raises(RuntimeError, match="simulated session write failure"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={
                    "source_event_key": "school_rebuild:curriculum:request-rollback",
                    "user_id": "test_user",
                    "domain": "school",
                    "task_type": "school_rebuild_curriculum",
                    "module_id": "wise_parrot_opinion_reason",
                    "session_id": session_id,
                    "node_id": activity_id,
                    "skill_id": "curriculum.wise_parrot_opinion_reason",
                    "source": "school_rebuild",
                },
                school_session={
                    "session_id": session_id,
                    "user_id": "test_user",
                    "api_version": "rebuild",
                    "flow_type": "curriculum",
                    "subject_id": "english",
                    "class_no": 5,
                    "status": "active",
                    "current_stage": "8",
                    "linked_session_id": None,
                    "state_json": {**state, "last_feedback": {"message": "rollback"}},
                },
                expected_state_json=state,
                request_activity_id=activity_id,
                request_answer_hash=answer_hash,
                request_claim_token=claimed["claim_token"],
                response_json={"exact": "public response"},
            )
        )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    assert request_row["status"] != "completed"


def test_stale_processing_school_answer_request_can_be_reclaimed(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"same answer").hexdigest()
    first = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    assert first["outcome"] == "claimed"
    store.school_answer_requests[(session_id, activity_id)]["updated_at"] = (
        time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    )

    reclaimed = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )

    assert store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS >= 60
    assert reclaimed["outcome"] == "claimed"


def test_expired_school_answer_claim_cannot_complete_newer_lease(store):
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"same answer").hexdigest()
    first = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    store.school_answer_requests[(session_id, activity_id)]["updated_at"] = (
        time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    )
    newer = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    assert first["claim_token"] != newer["claim_token"]
    event_key = "school_rebuild:curriculum:old-completion-fenced"

    with pytest.raises(ValueError, match="stale_school_answer_request"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={
                    "source_event_key": event_key,
                    "user_id": "test_user",
                    "domain": "school",
                    "task_type": "school_rebuild_curriculum",
                    "module_id": "wise_parrot_opinion_reason",
                    "session_id": session_id,
                    "node_id": activity_id,
                    "skill_id": "curriculum.wise_parrot_opinion_reason",
                    "source": "school_rebuild",
                },
                school_session={
                    "session_id": session_id,
                    "user_id": "test_user",
                    "api_version": "rebuild",
                    "flow_type": "curriculum",
                    "subject_id": "english",
                    "class_no": 5,
                    "status": "active",
                    "current_stage": "8",
                    "linked_session_id": None,
                    "state_json": {**state, "last_feedback": {"message": "old worker"}},
                },
                expected_state_json=state,
                request_activity_id=activity_id,
                request_answer_hash=answer_hash,
                request_claim_token=first["claim_token"],
                response_json={"worker": "old"},
            )
        )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    persisted = _run(store.get_school_session("test_user", session_id))
    assert request_row["status"] == "processing"
    assert request_row["claim_token"] == newer["claim_token"]
    assert persisted["state_json"] == state
    assert not any(event.get("source_event_key") == event_key for event in store.learning_events)


def test_expired_school_answer_claim_cannot_fail_newer_lease(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id=None,
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"same answer").hexdigest()
    first = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    store.school_answer_requests[(session_id, activity_id)]["updated_at"] = (
        time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    )
    newer = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )

    _run(
        store.fail_school_answer_request(
            "test_user",
            session_id,
            activity_id,
            answer_hash,
            first["claim_token"],
        )
    )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    assert first["claim_token"] != newer["claim_token"]
    assert request_row["status"] == "processing"
    assert request_row["claim_token"] == newer["claim_token"]


def test_revised_rainbow_content_reopens_only_the_stale_chapter_completion():
    landing = curriculum.curriculum_landing(
        school_profile={"target_class_no": 5, "subject_ids": ["english"]},
        placement_report={"unlock_state": "target_unlocked", "report_id": "report-1"},
        recap_session=None,
        latest_curriculum_session={
            "status": "complete",
            "state_json": {
                "status": "complete",
                "subject_id": "english",
                "target_class_no": 5,
                "completed_chapter_ids": ["eng_c5_ch01", "eng_c5_ch02", "eng_c5_ch03"],
                "completed_chapter_certification_versions": {
                    "eng_c5_ch01": curriculum.CLASS_5_PAPAS_SPECTACLES_CHAPTER[
                        "certification_version"
                    ],
                    "eng_c5_ch02": curriculum.CLASS_5_GONE_WITH_SCOOTER_CHAPTER[
                        "certification_version"
                    ],
                    "eng_c5_ch03": "2026-07-15.4",
                },
                "chapter": {"chapter_id": "eng_c5_ch03"},
            },
        },
    )

    assert landing["source_note"] == (
        "Target class is unlocked. Start Chapter 3 when you are ready."
    )
    assert [chapter["status"] for chapter in landing["chapters_preview"][:4]] == [
        "complete",
        "complete",
        "ready",
        "locked_next",
    ]


def test_non_certifying_content_revision_preserves_completed_chapter():
    chapters = curriculum.CLASS_5_CURRICULUM_CHAPTERS
    completed_ids = [str(chapter["chapter_id"]) for chapter in chapters]
    final_chapter = chapters[-1]
    landing = curriculum.curriculum_landing(
        school_profile={"target_class_no": 5, "subject_ids": ["english"]},
        placement_report={"unlock_state": "target_unlocked", "report_id": "report-1"},
        recap_session=None,
        latest_curriculum_session={
            "status": "complete",
            "state_json": {
                "status": "complete",
                "subject_id": "english",
                "target_class_no": 5,
                "completed_chapter_ids": completed_ids,
                "completed_chapter_versions": {
                    **{
                        str(chapter["chapter_id"]): str(chapter["content_version"])
                        for chapter in chapters
                    },
                    "eng_c5_ch01": "pre-non-certifying-content-revision",
                },
                "completed_chapter_certification_versions": {
                    str(chapter["chapter_id"]): str(
                        chapter.get("certification_version")
                        or chapter["content_version"]
                    )
                    for chapter in curriculum.CLASS_5_CURRICULUM_CHAPTERS
                },
                "chapter": {
                    "chapter_id": str(final_chapter["chapter_id"]),
                    "content_version": str(final_chapter["content_version"]),
                },
            },
        },
    )

    assert landing["chapters_preview"][-1]["status"] == "complete"
    assert landing["source_note"] == "All available target-class chapters are complete."
