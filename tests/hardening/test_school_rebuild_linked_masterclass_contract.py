import json
import asyncio
from copy import deepcopy
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_masterclass as masterclass
from app.services.school import evaluation_jobs
from tests.hardening.test_school_rebuild_curriculum_transfer_contract import (
    _answer,
    _new_state,
)
from tests.hardening.test_school_rebuild_phase_8_curriculum_teaching_contract import (
    AUTH,
    _seed_direct_curriculum_report_lineage,
    _seed_school_profile,
)
from tests.hardening.test_school_rebuild_deep_teaching_loop_contract import (
    _passing_answer,
    _passing_open_evaluation,
)
from tests.hardening.test_school_rebuild_curriculum_v2_runtime import (
    _advance_to_phase as _advance_v2_to_phase,
    _pause_for_masterclass as _pause_v2_for_masterclass,
    _state as _new_v2_state,
)


def _run(coro):
    return asyncio.run(coro)


def _paused_parent(monkeypatch) -> dict:
    state = _new_state(monkeypatch)
    for _ in range(8):
        if state["status"] == "paused_for_masterclass":
            break
        state, _ = _answer(state, "hide")
    assert state["status"] == "paused_for_masterclass"
    level = next(
        item
        for item in state["levels"]
        if item["level_id"] == state["active_interrupt"]["level_id"]
    )
    for check in (level.get("checks") or {}).values():
        if isinstance(check, dict):
            check.setdefault("knowledge_components", list(level["skill_ids"]))
    return state


def _authored_masterclass_check(parent: dict) -> dict:
    level_id = parent["active_interrupt"]["level_id"]
    level = next(
        level
        for level in parent["levels"]
        if level["level_id"] == level_id
    )
    return level["checks"]["masterclass"]


def _authored_masterclass_answer(parent: dict) -> str:
    check = _authored_masterclass_check(parent)
    accepted = list(check.get("accepted_answers") or [])
    return accepted[0] if accepted else str(check.get("model_answer") or "share")


def _qualifying_completed_child_state(
    *,
    parent_id: str,
    interrupt: dict,
    skill_ids: list[str],
) -> dict:
    return {
        "status": "complete",
        "curriculum_session_id": parent_id,
        "interrupt_id": str(interrupt.get("interrupt_id") or ""),
        "level_id": str(interrupt.get("level_id") or ""),
        "skill_ids": skill_ids,
        "attempts": [
            {
                "remediation_phase": phase,
                "correct": True,
                "score": 1.0,
                "blockers": [],
                "skill_ids": skill_ids,
                "source_activity_id": f"{phase}-source",
            }
            for phase in ("independent_check", "transfer_check")
        ],
    }


def _direct_resume_fixture(monkeypatch):
    parent_id = str(uuid4())
    child_id = str(uuid4())
    parent_state = curriculum.attach_masterclass_session(
        _paused_parent(monkeypatch),
        masterclass_session_id=child_id,
    )
    parent = {
        "session_id": parent_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 3,
        "status": "paused_for_masterclass",
        "current_stage": "0",
        "linked_session_id": None,
        "profile_version_id": "profile-1",
        "source_placement_report_id": "report-1",
        "state_json": parent_state,
    }
    child = {
        "session_id": child_id,
        "flow_type": "masterclass",
        "status": "complete",
        "linked_session_id": parent_id,
        "state_json": _qualifying_completed_child_state(
            parent_id=parent_id,
            interrupt=parent_state["active_interrupt"],
            skill_ids=school_rebuild_routes._interrupt_skill_ids(
                parent_state,
                parent_state["active_interrupt"],
            ),
        ),
    }

    class Store:
        def __init__(self):
            self.cas_calls = []

        async def get_school_session(self, user_id, session_id):
            assert user_id == "test_user"
            assert session_id == child_id
            return deepcopy(child)

        async def compare_and_set_school_session(
            self,
            *,
            school_session,
            expected_state_json,
        ):
            self.cas_calls.append((school_session, expected_state_json))
            return True

    store = Store()

    async def parent_lookup(*, user_id, session_id):
        assert user_id == "test_user"
        assert session_id == parent_id
        return store, deepcopy(parent), {}, {}

    monkeypatch.setattr(
        school_rebuild_routes,
        "_curriculum_parent_for_masterclass",
        parent_lookup,
    )
    request = Request({
        "type": "http",
        "method": "POST",
        "path": f"/school/curriculum/{parent_id}/resume-masterclass",
        "headers": [],
    })
    request.state.user_id = "test_user"
    return parent_id, child_id, parent_state, child, store, request


def test_snapshot_only_resumes_the_completed_child_attached_to_the_interrupt(
    monkeypatch,
):
    parent_id, child_id, parent_state, child, _store, _request = (
        _direct_resume_fixture(monkeypatch)
    )
    older_child = {
        **child,
        "session_id": str(uuid4()),
        "api_version": "rebuild",
        "profile_version_id": "profile-1",
        "source_placement_report_id": "report-1",
    }
    parent = {
        "session_id": parent_id,
        "status": "paused_for_masterclass",
        "state_json": parent_state,
    }

    resumable = school_rebuild_routes._resumable_masterclass_from_snapshot(
        rows=[older_child],
        parent_session=parent,
        public_profile={"profile_version_id": "profile-1"},
        source_placement_report_id="report-1",
    )

    assert str(parent_state["active_interrupt"]["masterclass_session_id"]) == child_id
    assert resumable is None


def test_state_repairs_one_matching_orphaned_masterclass_child(store, monkeypatch):
    profile = _seed_school_profile(store, target_class_no=3)
    _seed_direct_curriculum_report_lineage(store, profile)
    parent_id = str(uuid4())
    parent_state = _paused_parent(monkeypatch)
    parent_state["profile_version_id"] = profile["profile_version_id"]
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="paused_for_masterclass",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=parent_state,
        )
    )
    child_id = str(uuid4())
    child_state = masterclass.new_masterclass_state(
        curriculum_session_id=parent_id,
        curriculum_state=parent_state,
    )
    _run(
        store.upsert_school_session(
            session_id=child_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="masterclass",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_practice",
            linked_session_id=parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=child_state,
        )
    )

    state = TestClient(app).get("/school/state", headers=AUTH)

    assert state.status_code == 200, state.text
    assert state.json()["active_flow"] == "masterclass"
    assert state.json()["active_session_id"] == child_id
    repaired_parent = _run(store.get_school_session("test_user", parent_id))
    assert (
        repaired_parent["state_json"]["active_interrupt"]["masterclass_session_id"]
        == child_id
    )


def test_queued_masterclass_answer_keeps_recovered_child_pending(store, monkeypatch):
    """The browser must not regain an actionable detour during semantic grading."""

    profile = _seed_school_profile(store, target_class_no=3)
    _seed_direct_curriculum_report_lineage(store, profile)
    parent_id = str(uuid4())
    parent_state = _paused_parent(monkeypatch)
    parent_state["profile_version_id"] = profile["profile_version_id"]
    active_level = next(
        level
        for level in parent_state["levels"]
        if level["level_id"] == parent_state["active_interrupt"]["level_id"]
    )
    active_level.pop("teaching_steps", None)
    active_level["checks"]["independent_check"] = {
        "teaching_block": "Explain the mismatch in a complete sentence.",
        "passage": "Ravi looks for the brush while it is still behind his ear.",
        "prompt": "Explain why the situation is humorous.",
        "options": [],
        "accepted_answers": [],
        "grading_mode": "strict_open_rubric",
        "response_mode": "paragraph",
        "evaluation_mode": "llm_rubric",
        "preflight_rule": "relevant_english_response",
        "pass_score": 0.75,
        "rubric_criteria": [
            {
                "id": "humorous_contrast",
                "description": "Explains the search and the visible brush clue.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
        "min_response_words": 6,
        "relevance_terms": ["Ravi", "brush", "behind his ear"],
        "certifying_language": "en",
        "knowledge_components": list(active_level["skill_ids"]),
    }
    child_id = str(uuid4())
    child_state = masterclass.new_masterclass_state(
        curriculum_session_id=parent_id,
        curriculum_state=parent_state,
    )
    child_state["phase_index"] = 1
    activity = masterclass.current_activity(child_state)
    assert activity["evaluation_mode"] == "llm_rubric"

    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="paused_for_masterclass",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=parent_state,
        )
    )
    _run(
        store.upsert_school_session(
            session_id=child_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="masterclass",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_practice",
            linked_session_id=parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=child_state,
        )
    )

    client = TestClient(app)
    queued = client.post(
        f"/school/masterclass/{child_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity["activity_id"],
            "answer": (
                "Ravi looks for the brush even though it is behind his ear, "
                "so the search makes the situation humorous."
            ),
        },
    )

    assert queued.status_code == 202, queued.text
    state = client.get("/school/state", headers=AUTH)
    assert state.status_code == 200, state.text
    body = state.json()
    assert body["active_flow"] == "masterclass"
    assert body["active_session_id"] == child_id
    assert body["status"] == "awaiting_evaluation"
    assert body["next_action"] is None
    assert body["allowed_next_actions"] == []
    assert body["blocked_reason"] == "answer_evaluation_in_progress"


def test_fully_authored_supported_masterclass_answer_bypasses_queue_and_provider(
    store,
    monkeypatch,
):
    """A factual support check should resolve from its authored evidence alone."""

    profile = _seed_school_profile(store, target_class_no=3)
    _seed_direct_curriculum_report_lineage(store, profile)
    parent_id = str(uuid4())
    parent_state = _paused_parent(monkeypatch)
    parent_state["profile_version_id"] = profile["profile_version_id"]
    active_level = next(
        level
        for level in parent_state["levels"]
        if level["level_id"] == parent_state["active_interrupt"]["level_id"]
    )
    active_level.pop("teaching_steps", None)
    active_level["checks"]["masterclass"] = {
        "teaching_block": "Keep each supplied event in order.",
        "passage": "First the wind rose; next the kite string snapped; then the kite dropped into a field.",
        "prompt": "Turn the supplied kite events into a short past-tense story in order.",
        "options": [],
        "accepted_answers": [],
        "grading_mode": "strict_open_rubric",
        "response_mode": "paragraph",
        "evaluation_mode": "llm_rubric",
        "preflight_rule": "relevant_english_response",
        "pass_score": 0.75,
        "rubric_criteria": [
            {"id": "wind", "description": "Keeps the wind rising first.", "required": True, "min_quality": 0.7},
            {"id": "string", "description": "Keeps the string snapping next.", "required": True, "min_quality": 0.7},
            {"id": "field", "description": "Keeps the kite dropping into the field last.", "required": True, "min_quality": 0.7},
        ],
        "concept_slots": [
            {"id": "wind", "description": "Keeps the wind rising first.", "any_of": ["wind rose"]},
            {"id": "string", "description": "Keeps the string snapping next.", "any_of": ["kite string snapped", "string snapped"]},
            {"id": "field", "description": "Keeps the kite dropping into the field last.", "any_of": ["kite dropped into a field"]},
        ],
        "ordered_concept_slot_ids": ["wind", "string", "field"],
        "semantic_evidence_policy": "literal_aliases",
        "min_response_words": 10,
        "relevance_terms": ["wind", "kite", "field"],
        "knowledge_components": list(active_level["skill_ids"]),
    }
    child_id = str(uuid4())
    child_state = masterclass.new_masterclass_state(
        curriculum_session_id=parent_id,
        curriculum_state=parent_state,
    )
    activity = masterclass.current_activity(child_state)
    assert activity["evidence_role"] == "supported"

    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="paused_for_masterclass",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=parent_state,
        )
    )
    _run(
        store.upsert_school_session(
            session_id=child_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="masterclass",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_practice",
            linked_session_id=parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=child_state,
        )
    )

    async def queue_must_not_run(**_kwargs):
        raise AssertionError("fully authored supported practice must not queue")

    monkeypatch.setattr(
        store,
        "claim_and_enqueue_school_evaluation_job",
        queue_must_not_run,
        raising=False,
    )
    combined_context_calls: list[tuple[str, str, str]] = []

    async def combined_context(*, user_id, session_id, activity_id):
        combined_context_calls.append((user_id, session_id, activity_id))
        return {
            "active_profile": await store.get_active_school_profile_version(user_id),
            "school_session": await store.get_school_session(user_id, session_id),
            "answer_request": await store.get_school_answer_request(
                user_id,
                session_id,
                activity_id,
            ),
        }

    monkeypatch.setattr(
        store,
        "get_school_masterclass_answer_context",
        combined_context,
        raising=False,
    )
    response = TestClient(app).post(
        f"/school/masterclass/{child_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity["activity_id"],
            "answer": "First the wind rose. Next the kite string snapped, and then the kite dropped into a field.",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["last_feedback"]["correct"] is True
    assert combined_context_calls == [
        ("test_user", child_id, activity["activity_id"])
    ]


def test_state_does_not_expose_a_mismatched_orphaned_masterclass_child(store, monkeypatch):
    profile = _seed_school_profile(store, target_class_no=3)
    _seed_direct_curriculum_report_lineage(store, profile)
    parent_id = str(uuid4())
    parent_state = _paused_parent(monkeypatch)
    parent_state["profile_version_id"] = profile["profile_version_id"]
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="paused_for_masterclass",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=parent_state,
        )
    )
    child_state = masterclass.new_masterclass_state(
        curriculum_session_id=parent_id,
        curriculum_state=parent_state,
    )
    child_state["interrupt_id"] = "different-interrupt"
    child_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=child_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="masterclass",
            subject_id="english",
            class_no=3,
            status="active",
            current_stage="focused_practice",
            linked_session_id=parent_id,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=child_state,
        )
    )

    state = TestClient(app).get("/school/state", headers=AUTH)

    assert state.status_code == 200, state.text
    assert state.json()["active_session_id"] == parent_id
    assert state.json()["next_action"] == "start_masterclass"
    repaired_parent = _run(store.get_school_session("test_user", parent_id))
    assert not repaired_parent["state_json"]["active_interrupt"].get(
        "masterclass_session_id"
    )


def test_state_reconciles_a_lineage_fallback_before_deriving_navigation(store, monkeypatch):
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    state = _advance_v2_to_phase(_new_v2_state(), "independent_application")
    trigger = curriculum._current_activity(state)
    level = state["levels"][0]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = ["context_ignored"]
    state.update({
        "status": "active",
        "phase": "needs_support",
        "active_interrupt": None,
        "profile_version_id": profile["profile_version_id"],
        "support_required": {
            "reason": "authored_targeted_support_unavailable",
            "attempt_count": 2,
            "weak_skill_ids": list(trigger["assessed_skill_ids"]),
            "remediation_skill_ids": list(trigger["assessed_skill_ids"]),
            "focus": "Use a detail as evidence",
        },
    })
    parent_id = str(uuid4())
    _run(
        store.upsert_school_session(
            session_id=parent_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=state,
        )
    )
    original_snapshot = store.get_school_state_snapshot
    parent_row = _run(store.get_school_session("test_user", parent_id))

    async def stale_snapshot(user_id: str):
        snapshot = await original_snapshot(user_id)
        raw_curriculum = dict(snapshot["curriculum_session"])
        snapshot["curriculum_session"] = {
            **raw_curriculum,
            "source_placement_report_id": "obsolete-report",
        }
        return snapshot

    async def fallback_curriculum(*_args, **_kwargs):
        return deepcopy(parent_row)

    monkeypatch.setattr(store, "get_school_state_snapshot", stale_snapshot)
    monkeypatch.setattr(
        school_rebuild_routes,
        "_latest_curriculum_for_profile",
        fallback_curriculum,
    )
    monkeypatch.setattr(
        curriculum,
        "session_content_version_is_current",
        lambda _session: True,
    )

    response = TestClient(app).get("/school/state", headers=AUTH)

    assert response.status_code == 200, response.text
    assert response.json()["active_session_id"] == parent_id, response.json()
    assert response.json()["next_action"] == "start_masterclass", response.json()
    repaired_parent = _run(store.get_school_session("test_user", parent_id))
    assert repaired_parent["status"] == "paused_for_masterclass"
    assert repaired_parent["state_json"]["phase"] == "paused_for_masterclass"


def _deep_masterclass_parent() -> dict:
    chapter = deepcopy(curriculum._available_chapters("english", 5)[1])
    level = next(
        item
        for item in chapter["levels"]
        if item["level_id"] == "scooter_dialogue_and_speaker"
    )
    return {
        "status": "paused_for_masterclass",
        "phase": "paused_for_masterclass",
        "chapter": {"chapter_id": chapter["chapter_id"]},
        "active_interrupt": {
            "interrupt_id": "scooter_dialogue_and_speaker:masterclass:1",
            "level_id": level["level_id"],
            "focus": level["focus"],
            "trigger_count": 1,
            "runtime_contract": "v2",
        },
        "hot_session_memory": {
            "used_variant_ids": [
                "scooter_dialogue_and_speaker:guided:1",
                "scooter_dialogue_and_speaker:independent:1",
                "scooter_dialogue_and_speaker:transfer:1",
            ],
        },
        "levels": [level],
    }


def _single_skill_v2_parent() -> tuple[dict, str, str, set[str]]:
    parent = _deep_masterclass_parent()
    level = parent["levels"][0]
    target_skill, unrelated_level_skill = level["skill_ids"]
    parent["active_interrupt"]["skill_ids"] = [
        target_skill,
        "skill.outside.level",
    ]
    incompatible_source_ids = set()
    for phase in ("guided_practice", "independent_application", "transfer"):
        step = next(item for item in level["teaching_steps"] if item["phase"] == phase)
        candidate = deepcopy(step["variant_pool"][0])
        candidate["variant_id"] = f"{level['level_id']}:{phase}:unrelated"
        candidate["passage"] = "This item only checks the unrelated level skill."
        candidate["prompt"] = "Use the unrelated skill only."
        candidate["knowledge_components"] = [unrelated_level_skill]
        step["variant_pool"].insert(0, candidate)
        incompatible_source_ids.add(candidate["variant_id"])
    level["checks"]["revision_level_1"]["knowledge_components"] = [
        unrelated_level_skill
    ]
    incompatible_source_ids.add(
        f"{level['level_id']}:check:revision_level_1"
    )
    return parent, target_skill, unrelated_level_skill, incompatible_source_ids


def test_every_live_level_has_deep_fresh_masterclass_evidence_pools():
    for class_no in (2, 3, 4, 5):
        for chapter in curriculum._available_chapters("english", class_no):
            for level in chapter["levels"]:
                parent = {
                    "status": "paused_for_masterclass",
                    "phase": "paused_for_masterclass",
                    "chapter": {"chapter_id": chapter["chapter_id"]},
                    "levels": chapter["levels"],
                    "hot_session_memory": {},
                    "active_interrupt": {
                        "interrupt_id": f"{level['level_id']}:masterclass:1",
                        "level_id": level["level_id"],
                        "trigger_count": 1,
                    },
                }

                child = masterclass.new_masterclass_state(
                    curriculum_session_id="curriculum-probe",
                    curriculum_state=parent,
                )
                pools = child["phase_activity_pools"]

                # Some production-only levels have exactly the two dedicated
                # authored support checks once recognition choices are excluded.
                assert len(pools["supported_practice"]) >= 2
                assert len(pools["misconception_rebuild"]) >= 3
                assert len(pools["independent_check"]) >= 3
                assert len(pools["transfer_check"]) >= 2


def test_linked_masterclass_is_built_from_the_paused_level_authored_check(monkeypatch):
    parent = _paused_parent(monkeypatch)
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )

    activity = masterclass.current_activity(child)
    authored_check = _authored_masterclass_check(parent)
    assert activity["kind"] == "masterclass"
    assert activity["passage"] == authored_check["passage"]
    assert activity["prompt"] == authored_check["prompt"]
    assert activity["teaching_block"] == authored_check["teaching_block"]


def test_masterclass_public_response_never_leaks_hidden_answers(monkeypatch):
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=_paused_parent(monkeypatch),
    )
    payload = masterclass.public_masterclass_response(
        {
            "session_id": "masterclass-1",
            "linked_session_id": "curriculum-1",
            "status": "active",
            "state_json": child,
        }
    )

    serialized = json.dumps(payload)
    assert "accepted_answers" not in serialized
    assert "answer_key" not in serialized
    assert payload["current_activity"]["can_answer"] is True


def test_authored_v2_masterclass_uses_deep_fresh_remediation_sequence():
    parent = _deep_masterclass_parent()
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )

    assert child["engine_version"] == "school-rebuild-masterclass-3"
    assert child["skill_ids"] == parent["levels"][0]["skill_ids"]
    assert [item["phase"] for item in child["remediation_sequence"]] == [
        "supported_practice",
        "misconception_rebuild",
        "independent_check",
        "transfer_check",
    ]
    assert all(child["phase_activity_pools"][phase] for phase in (
        "supported_practice",
        "misconception_rebuild",
        "independent_check",
        "transfer_check",
    ))

    level = parent["levels"][0]
    for phase, check_kind in (
        ("independent_check", "independent_check"),
        ("transfer_check", "transfer_check"),
    ):
        canonical = level["checks"][check_kind]
        assert all(
            (candidate["passage"], candidate["prompt"])
            != (canonical["passage"], canonical["prompt"])
            for candidate in child["phase_activity_pools"][phase]
        )


def test_deep_masterclass_reuses_distinct_authored_checks_only_after_variants_are_exhausted():
    parent = _deep_masterclass_parent()
    level = parent["levels"][0]
    for phase in ("independent_application", "transfer"):
        step = next(
            item for item in level["teaching_steps"] if item["phase"] == phase
        )
        level.setdefault("used_variant_ids", []).extend(
            candidate["variant_id"] for candidate in step["variant_pool"]
        )

    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )

    assert [
        item["source_activity_id"]
        for item in child["phase_activity_pools"]["independent_check"]
    ] == [f"{level['level_id']}:check:independent_check"]
    assert [
        item["source_activity_id"]
        for item in child["phase_activity_pools"]["transfer_check"]
    ] == [f"{level['level_id']}:check:transfer_check"]


def test_every_live_level_has_a_certifying_retention_fallback_after_variant_exhaustion():
    for class_no in (2, 3, 4, 5):
        for chapter in curriculum._available_chapters("english", class_no):
            for raw_level in chapter["levels"]:
                level = deepcopy(raw_level)
                for phase in ("independent_application", "transfer"):
                    step = next(
                        item
                        for item in level["teaching_steps"]
                        if item["phase"] == phase
                    )
                    level.setdefault("used_variant_ids", []).extend(
                        candidate["variant_id"]
                        for candidate in step["variant_pool"]
                    )
                child = masterclass.new_masterclass_state(
                    curriculum_session_id="curriculum-probe",
                    curriculum_state={
                        "status": "paused_for_masterclass",
                        "phase": "paused_for_masterclass",
                        "chapter": {"chapter_id": chapter["chapter_id"]},
                        "levels": [level],
                        "active_interrupt": {
                            "interrupt_id": f"{level['level_id']}:masterclass:2",
                            "level_id": level["level_id"],
                            "trigger_count": 2,
                        },
                    },
                )
                for remediation_phase, check_kind in (
                    ("independent_check", "independent_check"),
                    ("transfer_check", "transfer_check"),
                ):
                    assert [
                        item["source_activity_id"]
                        for item in child["phase_activity_pools"][remediation_phase]
                    ] == [f"{level['level_id']}:check:{check_kind}"]


def test_v2_masterclass_starts_with_the_broadest_trigger_skill_support():
    chapter = deepcopy(curriculum._available_chapters("english", 5)[0])
    level = next(
        item
        for item in chapter["levels"]
        if item["level_id"] == "papas_spectacles_personal_response"
    )
    parent = {
        "status": "paused_for_masterclass",
        "phase": "paused_for_masterclass",
        "chapter": {"chapter_id": chapter["chapter_id"]},
        "levels": [level],
        "hot_session_memory": {},
        "active_interrupt": {
            "runtime_contract": "v2",
            "interrupt_id": f"{level['level_id']}:masterclass:1",
            "level_id": level["level_id"],
            "focus": level["focus"],
            "skill_ids": list(level["skill_ids"]),
            "trigger_count": 1,
        },
    }

    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    supported_pool = child["phase_activity_pools"]["supported_practice"]
    activity = masterclass.current_activity(child)

    assert len(activity["assessed_skill_ids"]) == max(
        len(candidate["assessed_skill_ids"])
        for candidate in supported_pool
    )
    assert set(activity["assessed_skill_ids"]) == set(level["skill_ids"])
    assert "because" in activity["prompt"].casefold()
    assert "but" in activity["prompt"].casefold()


def test_masterclass_preserves_hinglish_support_for_the_triggered_skill():
    parent = _deep_masterclass_parent()
    parent["preferred_teaching_language"] = "hi_en"
    parent["en_production_confidence"] = 0.2

    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    activity = masterclass.current_activity(child)

    assert child["preferred_teaching_language"] == "hi_en"
    assert child["en_production_confidence"] == 0.2
    assert "kisne kaha" in activity["teaching_block"]


def test_masterclass_certifying_phases_keep_the_english_response_requirement():
    parent = _deep_masterclass_parent()
    parent["preferred_teaching_language"] = "hi_en"
    parent["en_production_confidence"] = 0.95
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    child["phase_index"] = 2

    activity = masterclass.current_activity(child)

    assert activity["remediation_phase"] == "independent_check"
    assert "answer English mein likho" in activity["teaching_block"]


def test_failed_deep_masterclass_phase_rotates_to_a_fresh_authored_activity():
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=_deep_masterclass_parent(),
    )
    child["phase_index"] = 2
    first = masterclass.current_activity(child)

    child, result = masterclass.apply_masterclass_answer(
        child,
        activity_id=first["activity_id"],
        answer="no",
        open_answer_preflight_failed=True,
    )
    second = masterclass.current_activity(child)

    assert result["correct"] is False
    assert first["source_activity_id"] != second["source_activity_id"]
    assert (first["passage"], first["prompt"]) != (
        second["passage"],
        second["prompt"],
    )


def test_masterclass_feedback_names_the_missing_reasoning_not_the_hidden_answer():
    feedback = masterclass._masterclass_failure_feedback({
        "criteria": [
            {
                "id": "sound_lab_independent_application_v2_pattern",
                "met": True,
            },
            {
                "id": "sound_lab_independent_application_v2_first_meaning",
                "met": True,
            },
            {
                "id": "sound_lab_independent_application_v2_second_meaning",
                "met": False,
            },
            {
                "id": "sound_lab_independent_application_v2_original_usage",
                "met": True,
            },
        ],
        "model_answer": (
            "Rain means water falling from clouds, while train means a rail "
            "vehicle."
        ),
    })

    assert "what each word means in that context" in feedback
    assert "rail vehicle" not in feedback
    assert "water falling from clouds" not in feedback


def test_masterclass_reports_answered_and_current_source_variants_as_consumed():
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=_deep_masterclass_parent(),
    )
    first = masterclass.current_activity(child)
    child["attempts"] = [{"source_activity_id": first["source_activity_id"]}]
    child["phase_index"] = 1
    current = masterclass.current_activity(child)

    assert masterclass.consumed_source_activity_ids(child) == (
        first["source_activity_id"],
        current["source_activity_id"],
    )


def test_masterclass_requires_success_at_each_phase_before_completion(monkeypatch):
    parent = _paused_parent(monkeypatch)
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    accepted_answer = _authored_masterclass_answer(parent)
    activity = masterclass.current_activity(child)
    child, failed = masterclass.apply_masterclass_answer(
        child,
        activity_id=activity["activity_id"],
        answer="hide",
    )
    assert failed["correct"] is False
    assert child["status"] == "active"

    activity = masterclass.current_activity(child)
    child, passed = masterclass.apply_masterclass_answer(
        child,
        activity_id=activity["activity_id"],
        answer=accepted_answer,
    )
    assert passed["correct"] is True
    assert child["status"] == "active"

    for expected_phase in ("independent_check", "transfer_check"):
        activity = masterclass.current_activity(child)
        assert activity["remediation_phase"] == expected_phase
        child, passed = masterclass.apply_masterclass_answer(
            child,
            activity_id=activity["activity_id"],
            answer="share",
        )
        assert passed["correct"] is True

    assert child["status"] == "complete"
    assert masterclass.current_activity(child) is None


def test_masterclass_requires_supported_independent_and_transfer_evidence(monkeypatch):
    parent = _paused_parent(monkeypatch)
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )

    supported = masterclass.current_activity(child)
    assert supported["remediation_phase"] == "supported_practice"
    child, supported_result = masterclass.apply_masterclass_answer(
        child,
        activity_id=supported["activity_id"],
        answer=_authored_masterclass_answer(parent),
    )
    assert supported_result["correct"] is True
    assert child["status"] == "active"

    independent = masterclass.current_activity(child)
    assert independent["remediation_phase"] == "independent_check"
    child, independent_result = masterclass.apply_masterclass_answer(
        child,
        activity_id=independent["activity_id"],
        answer="share",
    )
    assert independent_result["correct"] is True
    assert child["status"] == "active"

    transfer = masterclass.current_activity(child)
    assert transfer["remediation_phase"] == "transfer_check"
    child, transfer_result = masterclass.apply_masterclass_answer(
        child,
        activity_id=transfer["activity_id"],
        answer="share",
    )
    assert transfer_result["correct"] is True
    assert child["status"] == "complete"
    assert masterclass.current_activity(child) is None


def test_masterclass_persistence_attempt_type_preserves_child_evidence_truth():
    cases = (
        ("supported_practice", "supported", "masterclass"),
        ("misconception_rebuild", "supported", "masterclass"),
        ("independent_check", "certifying", "independent_check"),
        ("transfer_check", "certifying", "transfer_check"),
        ("independent_check", "supported", "masterclass"),
    )

    assert [
        masterclass.persistence_attempt_type({
            "remediation_phase": remediation_phase,
            "evidence_role": evidence_role,
        })
        for remediation_phase, evidence_role, _expected in cases
    ] == [expected for _phase, _role, expected in cases]


def test_v2_masterclass_scopes_child_and_phase_pools_to_trigger_skills():
    parent, target_skill, unrelated_skill, incompatible_ids = (
        _single_skill_v2_parent()
    )

    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )

    assert child["skill_ids"] == [target_skill]
    pooled = [
        activity
        for activities in child["phase_activity_pools"].values()
        for activity in activities
    ]
    assert pooled
    assert incompatible_ids.isdisjoint(
        str(activity.get("source_activity_id") or "") for activity in pooled
    )
    assert all(
        target_skill in activity["knowledge_components"]
        and unrelated_skill not in activity["knowledge_components"]
        for activity in pooled
    )


def test_masterclass_evaluation_credits_only_assessed_trigger_components():
    parent, target_skill, unrelated_skill, _incompatible_ids = (
        _single_skill_v2_parent()
    )
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    child["phase_index"] = 2
    activity = masterclass.current_activity(child)

    assert activity["skill_ids"] == [target_skill]
    assert activity["assessed_skill_ids"] == [target_skill]
    assert activity["knowledge_components"] == [target_skill]
    assert unrelated_skill not in activity["skill_ids"]

    answer, open_evaluation = _passing_answer(activity)
    child, evaluation = masterclass.apply_masterclass_answer(
        child,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=open_evaluation,
    )

    assert evaluation["skill_ids"] == [target_skill]
    assert child["attempts"][-1]["skill_ids"] == [target_skill]


def test_v2_masterclass_fails_closed_without_compatible_authored_components():
    parent, _target_skill, unrelated_skill, _incompatible_ids = (
        _single_skill_v2_parent()
    )
    level = parent["levels"][0]
    independent = next(
        item
        for item in level["teaching_steps"]
        if item["phase"] == "independent_application"
    )
    for activity in independent["variant_pool"]:
        activity["knowledge_components"] = [unrelated_skill]

    with pytest.raises(
        ValueError,
        match="masterclass_content_required:independent_check",
    ):
        masterclass.new_masterclass_state(
            curriculum_session_id="curriculum-1",
            curriculum_state=parent,
        )


def test_v2_masterclass_rejects_trigger_skills_outside_the_level():
    parent = _deep_masterclass_parent()
    parent["active_interrupt"]["skill_ids"] = ["skill.outside.level"]

    with pytest.raises(ValueError, match="masterclass_trigger_skills_missing"):
        masterclass.new_masterclass_state(
            curriculum_session_id="curriculum-1",
            curriculum_state=parent,
        )


def test_masterclass_accepts_authored_concept_slot_content_and_records_criteria():
    parent = {
        "status": "paused_for_masterclass",
        "phase": "paused_for_masterclass",
        "chapter": {"chapter_id": "eng_c5_ch01"},
        "active_interrupt": {
            "interrupt_id": "search-evidence:masterclass:1",
            "level_id": "search-evidence",
            "focus": "track an object through details and evidence",
            "trigger_count": 1,
        },
        "levels": [{
            "level_id": "search-evidence",
            "focus": "track an object through details and evidence",
            "skill_ids": ["reading.sentence_comprehension", "reading.inference_reason"],
            "checks": {
                "masterclass": {
                    "passage": (
                        "Papa wore his spectacles while reading a seed packet. "
                        "The folded packet and a clean dust patch are on the balcony table."
                    ),
                    "prompt": "Why is the balcony table a sensible place to check?",
                    "teaching_block": "Join the last-use clue with the location clue.",
                    "options": [],
                    "response_mode": "short",
                    "answer_rule": "concept_slots",
                    "concept_slots": [
                        {
                            "id": "last_use_clue",
                            "description": "Connects the glasses to the packet.",
                            "any_of": ["wore his spectacles while reading"],
                        },
                        {
                            "id": "table_clue",
                            "description": "Uses the table evidence.",
                            "any_of": ["clean patch is beside the packet"],
                        },
                    ],
                    "forbidden_phrases": ["there are no clues"],
                    "min_response_words": 10,
                    "accepted_answers": [],
                    "knowledge_components": [
                        "reading.sentence_comprehension",
                        "reading.inference_reason",
                    ],
                },
                "independent_check": {
                    "passage": "A fresh clue points to a reading table.",
                    "prompt": "Where should the learner check independently?",
                    "teaching_block": "Use the strongest stated clue.",
                    "options": [],
                    "accepted_answers": ["reading table"],
                    "knowledge_components": ["reading.sentence_comprehension"],
                },
                "transfer_check": {
                    "passage": "A ticket stub lies beside the atlas shelf.",
                    "prompt": "Where should the learner search in this new setting?",
                    "teaching_block": "Transfer the clue strategy.",
                    "options": [],
                    "accepted_answers": ["atlas shelf"],
                    "knowledge_components": ["reading.inference_reason"],
                },
            },
        }],
    }
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    activity = masterclass.current_activity(child)

    child, evaluation = masterclass.apply_masterclass_answer(
        child,
        activity_id=activity["activity_id"],
        answer=(
            "Papa wore his spectacles while reading, and the clean patch is "
            "beside the packet, so the balcony table is worth checking."
        ),
    )

    assert child["status"] == "active"
    assert evaluation["correct"] is True
    assert {criterion["id"] for criterion in evaluation["criteria"]} >= {
        "last_use_clue",
        "table_clue",
        "response_min_words",
    }

    for answer in ("reading table", "atlas shelf"):
        activity = masterclass.current_activity(child)
        child, evaluation = masterclass.apply_masterclass_answer(
            child,
            activity_id=activity["activity_id"],
            answer=answer,
        )
        assert evaluation["correct"] is True
    assert child["status"] == "complete"


def test_linked_masterclass_routes_verify_child_completion_before_parent_resume(
    store,
    monkeypatch,
):
    profile = _seed_school_profile(store, target_class_no=3)
    _seed_direct_curriculum_report_lineage(store, profile)
    placement_report = asyncio.run(
        store.get_school_placement_report_by_id("test_user", "placement-report")
    )
    assert placement_report is not None
    asyncio.run(
        store.upsert_school_placement_report(
            **{
                **placement_report,
                "placement_status": "target_ready",
                "unlock_state": "target_unlocked",
                "evaluated_class_no": 3,
                "active_learning_class_no": 3,
                "allowed_next_actions": ["start_curriculum"],
            }
        )
    )
    parent_state = _paused_parent(monkeypatch)
    parent_state["profile_version_id"] = profile["profile_version_id"]
    active_level = next(
        level
        for level in parent_state["levels"]
        if level["level_id"] == parent_state["active_interrupt"]["level_id"]
    )
    active_level["checks"]["independent_check"] = {
        "teaching_block": "Explain the mismatch without answer choices.",
        "passage": (
            "Ravi searches the art cupboard for a brush that is still tucked "
            "behind his ear."
        ),
        "prompt": "Explain why the situation is humorous.",
        "options": [],
        "accepted_answers": [],
        "grading_mode": "strict_open_rubric",
        "response_mode": "paragraph",
        "evaluation_mode": "llm_rubric",
        "preflight_rule": "relevant_english_response",
        "pass_score": 0.75,
        "rubric_criteria": [
            {
                "id": "humorous_contrast",
                "description": "Explains the search and the visible brush clue.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
        "min_response_words": 6,
        "relevance_terms": ["Ravi", "brush", "behind his ear"],
        "certifying_language": "en",
        "knowledge_components": list(active_level["skill_ids"]),
    }

    async def passing_evaluator(activity, answer, **_kwargs):
        return _passing_open_evaluation(activity, answer)

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        passing_evaluator,
    )
    accepted_answer = _authored_masterclass_answer(parent_state)
    parent_session_id = str(uuid4())
    asyncio.run(store.upsert_school_session(
        session_id=parent_session_id,
        user_id="test_user",
        api_version="rebuild",
        flow_type="curriculum",
        subject_id="english",
        class_no=3,
        status="paused_for_masterclass",
        current_stage="0",
        linked_session_id=None,
        profile_version_id=profile["profile_version_id"],
        source_placement_report_id="placement-report",
        state_json=parent_state,
    ))
    client = TestClient(app)

    started = client.post(
        f"/school/curriculum/{parent_session_id}/masterclass/start",
        headers=AUTH,
    )
    assert started.status_code == 200, started.text
    child = started.json()
    child_id = child["session_id"]
    attached_parent = _run(store.get_school_session("test_user", parent_session_id))
    assert (
        attached_parent["state_json"]["active_interrupt"]["masterclass_session_id"]
        == child_id
    )

    premature = client.post(
        f"/school/curriculum/{parent_session_id}/resume-masterclass",
        headers=AUTH,
    )
    assert premature.status_code == 409, premature.text
    assert premature.json()["detail"]["code"] == "masterclass_not_complete"

    activity = child["current_activity"]
    supported = client.post(
        f"/school/masterclass/{child_id}/answer",
        headers=AUTH,
        json={"activity_id": activity["activity_id"], "answer": accepted_answer},
    )
    assert supported.status_code == 200, supported.text
    assert supported.json()["status"] == "active"
    child_events = [
        event
        for event in store.learning_events
        if event.get("session_id") == child_id
    ]
    assert [event["attempt_type"] for event in child_events] == ["masterclass"]

    current = supported.json()
    phase_answers = {
        "independent_check": (
            "Ravi searches for the brush although it is behind his ear, so "
            "the mismatch makes the situation humorous."
        ),
        "transfer_check": "share",
    }
    for expected_phase in ("independent_check", "transfer_check"):
        activity = current["current_activity"]
        assert activity["remediation_phase"] == expected_phase
        response = client.post(
            f"/school/masterclass/{child_id}/answer",
            headers=AUTH,
            json={
                "activity_id": activity["activity_id"],
                "answer": phase_answers[expected_phase],
            },
        )
        if response.status_code == 202:
            assert _run(
                evaluation_jobs.run_one_school_evaluation_job(
                    store=store,
                    processor=school_rebuild_routes.process_school_evaluation_job,
                    max_attempts=2,
                )
            ) is True
            response = client.get(
                f"/school/masterclass/{child_id}",
                headers=AUTH,
            )
            assert response.json()["linked_curriculum"]["session_id"] == (
                parent_session_id
            )
        assert response.status_code == 200, response.text
        current = response.json()
        child_events = [
            event
            for event in store.learning_events
            if event.get("session_id") == child_id
        ]
        assert child_events[-1]["attempt_type"] == expected_phase

    assert current["status"] == "complete"
    assert [event["attempt_type"] for event in child_events] == [
        "masterclass",
        "independent_check",
        "transfer_check",
    ]
    for skill_id in active_level["skill_ids"]:
        profile = store.learner_skill_profiles[("test_user", "school", skill_id)]
        readiness = profile["evidence_json"]["school_readiness_state"]
        assert readiness["independent_passes"] == 1
        assert readiness["transfer_passes"] == 1

    refreshed_state = client.get("/school/state", headers=AUTH)
    assert refreshed_state.status_code == 200, refreshed_state.text
    assert refreshed_state.json()["active_flow"] == "curriculum"
    assert refreshed_state.json()["active_session_id"] == parent_session_id
    assert refreshed_state.json()["next_action"] == "resume_masterclass"
    assert refreshed_state.json()["next_action_url"] == (
        f"/school/session/{parent_session_id}"
    )
    assert refreshed_state.json()["allowed_next_actions"] == ["resume_masterclass"]

    resumed = client.post(
        f"/school/curriculum/{parent_session_id}/masterclass/start",
        headers=AUTH,
    )
    assert resumed.status_code == 200, resumed.text
    body = resumed.json()
    assert body["session_id"] == parent_session_id
    assert body["status"] == "active"
    assert body["phase"] == "learning"
    assert body["current_activity"]["kind"] == "independent_check"

    replayed = client.post(
        f"/school/curriculum/{parent_session_id}/resume-masterclass",
        headers=AUTH,
    )
    assert replayed.status_code == 200, replayed.text
    assert replayed.json()["status"] == "active"
    assert replayed.json()["phase"] == "learning"
    assert (
        replayed.json()["current_activity"]["activity_id"]
        == body["current_activity"]["activity_id"]
    )


def test_resume_masterclass_reports_when_parent_content_changed(store, monkeypatch):
    profile = _seed_school_profile(store, target_class_no=3)
    _seed_direct_curriculum_report_lineage(store, profile)
    parent_state = _paused_parent(monkeypatch)
    parent_state["profile_version_id"] = profile["profile_version_id"]
    parent_session_id = str(uuid4())
    asyncio.run(
        store.upsert_school_session(
            session_id=parent_session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="paused_for_masterclass",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=parent_state,
        )
    )
    expired_state = {
        **parent_state,
        "status": "expired",
        "phase": "content_refresh_required",
        "active_interrupt": None,
        "expiration_reason": "authored_content_version_changed",
    }
    asyncio.run(
        store.upsert_school_session(
            session_id=parent_session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=3,
            status="expired",
            current_stage="0",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=expired_state,
        )
    )

    response = TestClient(app).post(
        f"/school/curriculum/{parent_session_id}/resume-masterclass",
        headers=AUTH,
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "curriculum_content_refresh_required"


def test_resume_renders_transition_before_compare_and_set(monkeypatch):
    parent_id = str(uuid4())
    child_id = str(uuid4())
    parent_state = curriculum.attach_masterclass_session(
        _paused_parent(monkeypatch),
        masterclass_session_id=child_id,
    )
    parent = {
        "session_id": parent_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 3,
        "status": "paused_for_masterclass",
        "current_stage": "0",
        "linked_session_id": None,
        "profile_version_id": "profile-1",
        "source_placement_report_id": "report-1",
        "state_json": parent_state,
    }
    child = {
        "session_id": child_id,
        "flow_type": "masterclass",
        "status": "complete",
        "linked_session_id": parent_id,
        "state_json": _qualifying_completed_child_state(
            parent_id=parent_id,
            interrupt=parent_state["active_interrupt"],
            skill_ids=school_rebuild_routes._interrupt_skill_ids(
                parent_state,
                parent_state["active_interrupt"],
            ),
        ),
    }

    class Store:
        def __init__(self):
            self.cas_calls = []

        async def get_school_session(self, user_id, session_id):
            assert user_id == "test_user"
            assert session_id == child_id
            return deepcopy(child)

        async def compare_and_set_school_session(
            self,
            *,
            school_session,
            expected_state_json,
        ):
            self.cas_calls.append((school_session, expected_state_json))
            return True

    store = Store()

    async def parent_lookup(*, user_id, session_id):
        assert user_id == "test_user"
        assert session_id == parent_id
        return store, deepcopy(parent), {}, {}

    def fail_render(_session):
        raise ValueError("render_failed")

    monkeypatch.setattr(
        school_rebuild_routes,
        "_curriculum_parent_for_masterclass",
        parent_lookup,
    )
    monkeypatch.setattr(curriculum, "public_curriculum_response", fail_render)
    request = Request({
        "type": "http",
        "method": "POST",
        "path": f"/school/curriculum/{parent_id}/resume-masterclass",
        "headers": [],
    })
    request.state.user_id = "test_user"

    with pytest.raises(ValueError, match="render_failed"):
        asyncio.run(
            school_rebuild_routes.resume_school_curriculum_masterclass(
                UUID(parent_id),
                request,
            )
        )

    assert store.cas_calls == []


def test_resume_validates_json_serialization_before_compare_and_set(monkeypatch):
    parent_id, _child_id, _parent_state, _child, store, request = (
        _direct_resume_fixture(monkeypatch)
    )

    monkeypatch.setattr(
        curriculum,
        "public_curriculum_response",
        lambda _session: {"status": "active", "invalid_number": float("nan")},
    )

    with pytest.raises(ValueError, match="Out of range float values"):
        asyncio.run(
            school_rebuild_routes.resume_school_curriculum_masterclass(
                UUID(parent_id),
                request,
            )
        )

    assert store.cas_calls == []


@pytest.mark.parametrize("invalid_child", ["link", "evidence"])
def test_resume_rejects_unqualified_completed_child(monkeypatch, invalid_child):
    parent_id, _child_id, _parent_state, child, store, request = (
        _direct_resume_fixture(monkeypatch)
    )
    if invalid_child == "link":
        child["linked_session_id"] = "another-curriculum-session"
    else:
        child["state_json"]["attempts"] = []

    with pytest.raises(HTTPException) as caught:
        asyncio.run(
            school_rebuild_routes.resume_school_curriculum_masterclass(
                UUID(parent_id),
                request,
            )
        )

    assert caught.value.status_code == 409
    assert caught.value.detail["code"] == "masterclass_completion_invalid"
    assert store.cas_calls == []


def test_resume_recovers_legacy_partial_transition_with_exhausted_return_pool(
    monkeypatch,
):
    parent_id = str(uuid4())
    child_id = str(uuid4())
    state = _advance_v2_to_phase(_new_v2_state(), "transfer")
    state = _pause_v2_for_masterclass(state)
    state = curriculum.attach_masterclass_session(
        state,
        masterclass_session_id=child_id,
    )
    interrupt = deepcopy(state["active_interrupt"])
    level = state["levels"][0]
    return_step_index = int(interrupt["return_step_index"])
    return_step = level["teaching_steps"][return_step_index]
    level["used_variant_ids"] = [
        candidate["variant_id"] for candidate in return_step["variant_pool"]
    ]
    level["status"] = "in_progress"
    level["v2_step_index"] = return_step_index
    level["current_step"] = return_step["phase"]
    level["v2_support_mode"] = None
    level["v2_last_masterclass_session_id"] = child_id
    parent_state = curriculum.normalize_curriculum_state({
        **state,
        "status": "active",
        "phase": "learning",
        "active_interrupt": None,
        "interrupt_history": [{
            **interrupt,
            "masterclass_session_id": child_id,
            "resolution": "complete",
        }],
    })
    parent = {
        "session_id": parent_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "current_stage": "0",
        "linked_session_id": None,
        "profile_version_id": "profile-1",
        "source_placement_report_id": "report-1",
        "state_json": parent_state,
    }
    child = {
        "session_id": child_id,
        "flow_type": "masterclass",
        "status": "complete",
        "linked_session_id": parent_id,
        "state_json": _qualifying_completed_child_state(
            parent_id=parent_id,
            interrupt=interrupt,
            skill_ids=school_rebuild_routes._interrupt_skill_ids(
                parent_state,
                interrupt,
            ),
        ),
    }

    class Store:
        def __init__(self):
            self.row = deepcopy(parent)
            self.cas_calls = []

        async def get_school_session(self, user_id, session_id):
            assert user_id == "test_user"
            if session_id == child_id:
                return deepcopy(child)
            assert session_id == parent_id
            return deepcopy(self.row)

        async def compare_and_set_school_session(
            self,
            *,
            school_session,
            expected_state_json,
        ):
            self.cas_calls.append((school_session, expected_state_json))
            self.row = {**self.row, **deepcopy(school_session)}
            return True

    store = Store()

    async def parent_lookup(*, user_id, session_id):
        assert (user_id, session_id) == ("test_user", parent_id)
        return store, deepcopy(store.row), {}, {}

    monkeypatch.setattr(
        school_rebuild_routes,
        "_curriculum_parent_for_masterclass",
        parent_lookup,
    )
    request = Request({
        "type": "http",
        "method": "POST",
        "path": f"/school/curriculum/{parent_id}/resume-masterclass",
        "headers": [],
    })
    request.state.user_id = "test_user"

    response = asyncio.run(
        school_rebuild_routes.resume_school_curriculum_masterclass(
            UUID(parent_id),
            request,
        )
    )

    assert response["status"] == "active"
    assert response["phase"] == "learning"
    assert response["current_activity"]["phase"] == "review"
    assert response["feedback_v2"]["outcome"] == (
        "masterclass_complete_advanced"
    )
    assert len(store.cas_calls) == 1
