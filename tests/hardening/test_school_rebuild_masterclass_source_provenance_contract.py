"""Public masterclass provenance must stay safe for learner clients."""

from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_masterclass as masterclass
from tests.hardening.test_school_rebuild_phase_8_curriculum_teaching_contract import (
    AUTH,
    _seed_direct_curriculum_report_lineage,
    _seed_school_profile,
)


def _paused_parent_with_source_anchors() -> dict:
    check = {
        "passage": "A new practice passage.",
        "prompt": "What should the learner do?",
        "teaching_block": "Use the clue in the passage.",
        "options": ["Share the idea", "Ignore the clue"],
        "accepted_answers": ["Share the idea"],
        "knowledge_components": ["skill.inference"],
        "source_anchor_ids": ["internal-anchor-17"],
    }
    return {
        "status": "paused_for_masterclass",
        "phase": "paused_for_masterclass",
        "chapter": {
            "chapter_id": "eng_c5_ch01",
            "book_title": "Marigold",
            "title": "Ice-cream Man",
            "source_anchors": [{
                "anchor_id": "internal-anchor-17",
                "section_label": "Let us talk",
                "page_start": 11,
                "page_end": 12,
                "source_url": "https://ncert.nic.in/textbook.php?eeng101=0-10",
                "coverage_treatment": "internal_only",
                "text_excerpt": "This textbook body must remain private.",
            }],
        },
        "active_interrupt": {
            "interrupt_id": "level-1:masterclass:1",
            "level_id": "level-1",
            "trigger_count": 1,
        },
        "levels": [{
            "level_id": "level-1",
            "focus": "Use a clue to explain an answer",
            "skill_ids": ["skill.inference"],
            "checks": {
                "masterclass": check,
                "independent_check": check,
                "transfer_check": check,
            },
        }],
    }


def test_masterclass_public_activity_projects_only_safe_parent_source_metadata():
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=_paused_parent_with_source_anchors(),
    )

    payload = masterclass.public_masterclass_response({
        "session_id": "masterclass-1",
        "linked_session_id": "curriculum-1",
        "status": "active",
        "state_json": child,
    })

    assert payload["current_activity"]["source_reference"] == {
        "book_title": "Marigold",
        "chapter_title": "Ice-cream Man",
        "anchors": [{
            "section_label": "Let us talk",
            "page_start": 11,
            "page_end": 12,
            "source_url": "https://ncert.nic.in/textbook.php?eeng101=0-10",
        }],
    }
    serialized = json.dumps(payload)
    for private_value in (
        "internal-anchor-17",
        "internal_only",
        "This textbook body must remain private.",
        "accepted_answers",
        "answer_key",
        "model_answer",
        "rubric",
    ):
        assert private_value not in serialized


@pytest.mark.parametrize(
    "source_url",
    (
        "https://learner:secret@ncert.nic.in/textbook.php?eeng101=0-10",
        "https://ncert.nic.in:444/textbook.php?eeng101=0-10",
    ),
)
def test_masterclass_public_activity_rejects_noncanonical_ncert_source_urls(
    source_url: str,
):
    parent = _paused_parent_with_source_anchors()
    parent["chapter"]["source_anchors"][0]["source_url"] = source_url
    child = masterclass.new_masterclass_state(
        curriculum_session_id="curriculum-1",
        curriculum_state=parent,
    )

    payload = masterclass.public_masterclass_response({
        "session_id": "masterclass-1",
        "linked_session_id": "curriculum-1",
        "status": "active",
        "state_json": child,
    })

    assert "source_reference" not in payload["current_activity"]


def _legacy_child_and_parent_rows() -> tuple[dict, dict]:
    parent_id = str(uuid4())
    child_id = str(uuid4())
    parent_state = _paused_parent_with_source_anchors()
    child_state = masterclass.new_masterclass_state(
        curriculum_session_id=parent_id,
        curriculum_state=parent_state,
    )
    child_state.pop("source_provenance")
    parent_state = curriculum.attach_masterclass_session(
        parent_state,
        masterclass_session_id=child_id,
    )
    return {
        "session_id": child_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "masterclass",
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "current_stage": "focused_practice",
        "linked_session_id": parent_id,
        "profile_version_id": "profile-1",
        "source_placement_report_id": "placement-report",
        "state_json": child_state,
    }, {
        "session_id": parent_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": "paused_for_masterclass",
        "current_stage": "learning",
        "linked_session_id": None,
        "profile_version_id": "profile-1",
        "source_placement_report_id": "placement-report",
        "state_json": parent_state,
    }


def test_legacy_masterclass_uses_only_its_linked_parent_for_safe_provenance():
    child, parent = _legacy_child_and_parent_rows()

    payload = masterclass.public_masterclass_response(
        child,
        parent_session=parent,
    )

    assert "source_provenance" not in child["state_json"]
    assert payload["current_activity"]["source_reference"] == {
        "book_title": "Marigold",
        "chapter_title": "Ice-cream Man",
        "anchors": [{
            "section_label": "Let us talk",
            "page_start": 11,
            "page_end": 12,
            "source_url": "https://ncert.nic.in/textbook.php?eeng101=0-10",
        }],
    }


def test_legacy_masterclass_omits_provenance_when_parent_lineage_does_not_match():
    child, parent = _legacy_child_and_parent_rows()
    parent["session_id"] = str(uuid4())

    payload = masterclass.public_masterclass_response(
        child,
        parent_session=parent,
    )

    assert "source_reference" not in payload["current_activity"]


@pytest.mark.parametrize(
    ("missing_row", "lineage_field"),
    (
        ("child", "profile_version_id"),
        ("child", "source_placement_report_id"),
        ("parent", "profile_version_id"),
        ("parent", "source_placement_report_id"),
    ),
)
def test_legacy_masterclass_omits_provenance_without_complete_lineage(
    missing_row: str,
    lineage_field: str,
):
    child, parent = _legacy_child_and_parent_rows()
    (child if missing_row == "child" else parent)[lineage_field] = None

    payload = masterclass.public_masterclass_response(
        child,
        parent_session=parent,
    )

    assert "source_reference" not in payload["current_activity"]


def test_masterclass_get_backfills_legacy_provenance_from_its_linked_parent(store):
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    child, parent = _legacy_child_and_parent_rows()
    for row in (parent, child):
        row["profile_version_id"] = profile["profile_version_id"]
        asyncio.run(store.upsert_school_session(**row))

    response = TestClient(app).get(
        f"/school/masterclass/{child['session_id']}",
        headers=AUTH,
    )

    assert response.status_code == 200, response.text
    assert response.json()["current_activity"]["source_reference"]["anchors"] == [{
        "section_label": "Let us talk",
        "page_start": 11,
        "page_end": 12,
        "source_url": "https://ncert.nic.in/textbook.php?eeng101=0-10",
    }]


def test_masterclass_get_omits_legacy_provenance_when_parent_lineage_is_missing(
    store,
):
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    child, parent = _legacy_child_and_parent_rows()
    child["profile_version_id"] = profile["profile_version_id"]
    parent["profile_version_id"] = profile["profile_version_id"]
    parent["source_placement_report_id"] = None
    asyncio.run(store.upsert_school_session(**parent))
    asyncio.run(store.upsert_school_session(**child))

    response = TestClient(app).get(
        f"/school/masterclass/{child['session_id']}",
        headers=AUTH,
    )

    assert response.status_code == 200, response.text
    assert "source_reference" not in response.json()["current_activity"]
