import json
import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_masterclass as masterclass
from tests.hardening.test_school_rebuild_curriculum_transfer_contract import (
    _answer,
    _new_state,
)
from tests.hardening.test_school_rebuild_phase_8_curriculum_teaching_contract import (
    AUTH,
    _seed_direct_curriculum_report_lineage,
    _seed_school_profile,
)


def _paused_parent(monkeypatch) -> dict:
    state = _new_state(monkeypatch)
    state, _ = _answer(state, "hide")
    state, _ = _answer(state, "hide")
    assert state["status"] == "paused_for_masterclass"
    return state


def _authored_masterclass_check(parent: dict) -> dict:
    level_id = parent["active_interrupt"]["level_id"]
    level = next(
        level
        for level in parent["levels"]
        if level["level_id"] == level_id
    )
    return level["checks"]["masterclass"]


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


def test_masterclass_requires_success_before_backend_marks_it_complete(monkeypatch):
    parent = _paused_parent(monkeypatch)
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )
    accepted_answer = _authored_masterclass_check(parent)["accepted_answers"][0]
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
    assert child["status"] == "complete"
    assert masterclass.current_activity(child) is None


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
                }
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

    assert child["status"] == "complete"
    assert evaluation["correct"] is True
    assert {criterion["id"] for criterion in evaluation["criteria"]} >= {
        "last_use_clue",
        "table_clue",
        "response_min_words",
    }


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
    accepted_answer = _authored_masterclass_check(parent_state)[
        "accepted_answers"
    ][0]
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

    premature = client.post(
        f"/school/curriculum/{parent_session_id}/resume-masterclass",
        headers=AUTH,
    )
    assert premature.status_code == 409, premature.text
    assert premature.json()["detail"]["code"] == "masterclass_not_complete"

    activity = child["current_activity"]
    completed = client.post(
        f"/school/masterclass/{child_id}/answer",
        headers=AUTH,
        json={"activity_id": activity["activity_id"], "answer": accepted_answer},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "complete"

    resumed = client.post(
        f"/school/curriculum/{parent_session_id}/resume-masterclass",
        headers=AUTH,
    )
    assert resumed.status_code == 200, resumed.text
    body = resumed.json()
    assert body["status"] == "active"
    assert body["phase"] == "learning"
    assert body["current_activity"]["kind"] == "independent_check"
