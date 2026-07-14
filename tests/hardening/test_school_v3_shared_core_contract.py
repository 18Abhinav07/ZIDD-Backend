import ast
from pathlib import Path

import pytest

from app.services.school_core import readiness as core_readiness
from app.services import school_v2_readiness


def _seed_active_profile(store, user_id: str) -> str:
    profile_version_id = "90000000-0000-4000-8000-000000000001"
    store.school_profile_versions[(user_id, profile_version_id)] = {
        "profile_version_id": profile_version_id,
        "user_id": user_id,
        "status": "active",
    }
    return profile_version_id


def test_school_v2_readiness_is_compatibility_reexport():
    assert school_v2_readiness.SkillReadinessState is core_readiness.SkillReadinessState
    assert school_v2_readiness.AttemptEvidence is core_readiness.AttemptEvidence
    assert school_v2_readiness.apply_attempt_evidence is core_readiness.apply_attempt_evidence
    assert school_v2_readiness.apply_placement_ready_seed is core_readiness.apply_placement_ready_seed
    assert school_v2_readiness.classify_skill_status is core_readiness.classify_skill_status


def test_school_readiness_core_has_no_subject_or_class_literals():
    source = Path(core_readiness.__file__).read_text()
    tree = ast.parse(source)
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    assert "class 5" not in {value.lower() for value in literals}
    assert "subject_id" not in literals
    assert "class_no" not in literals
    assert "eng.c5" not in source


def test_no_second_school_readiness_ema_formula_exists():
    services_root = Path(core_readiness.__file__).parents[1]
    offenders = []
    for path in services_root.rglob("*.py"):
        if path == Path(core_readiness.__file__):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in {
                "_ema",
                "apply_attempt_evidence",
                "classify_skill_status",
                "apply_placement_ready_seed",
            }:
                offenders.append(f"{path.relative_to(services_root)}:{node.name}")

    assert offenders == []


def test_school_readiness_accepts_json_restored_hint_history():
    state = core_readiness.SkillReadinessState(
        skill_id="reading.word_meaning_context",
        recent_hint_flags=[False, True],  # JSON storage restores tuples as lists.
    )

    updated = core_readiness.apply_attempt_evidence(
        state,
        core_readiness.AttemptEvidence(
            attempt_type="bridge",
            evaluator_score=0.75,
            evaluator_confidence=1.0,
            skill_ids=("reading.word_meaning_context",),
            support_level="bridge",
        ),
    )

    assert updated.recent_hint_flags == (False, True, True)
    assert core_readiness.hint_dependency(updated) == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_generic_school_sessions_enforce_one_active_flow(store):
    await store.ensure_profile("learner")
    profile_version_id = _seed_active_profile(store, "learner")
    await store.upsert_school_session(
        session_id="00000000-0000-0000-0000-000000000001",
        user_id="learner",
        api_version="rebuild",
        flow_type="placement",
        subject_id="english",
        class_no=5,
        status="active",
        current_stage="snapshot",
        profile_version_id=profile_version_id,
        state_json={"stage": "snapshot"},
    )

    with pytest.raises(ValueError, match="duplicate_active_school_session"):
        await store.upsert_school_session(
            session_id="00000000-0000-0000-0000-000000000002",
            user_id="learner",
            api_version="rebuild",
            flow_type="placement",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="snapshot",
            profile_version_id=profile_version_id,
            state_json={},
        )

    active = await store.get_active_school_session(
        "learner",
        "rebuild",
        "placement",
        "english",
        5,
    )
    assert active["session_id"] == "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_generic_school_sessions_have_real_link_contract(store):
    await store.ensure_profile("learner")
    profile_version_id = _seed_active_profile(store, "learner")
    curriculum_id = "00000000-0000-0000-0000-000000000010"
    masterclass_id = "00000000-0000-0000-0000-000000000011"

    with pytest.raises(ValueError, match="linked_school_session_not_found"):
        await store.upsert_school_session(
            session_id=masterclass_id,
            user_id="learner",
            api_version="rebuild",
            flow_type="masterclass",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="guided",
            profile_version_id=profile_version_id,
            linked_session_id=curriculum_id,
            state_json={},
        )

    await store.upsert_school_session(
        session_id=curriculum_id,
        user_id="learner",
        api_version="rebuild",
        flow_type="curriculum",
        subject_id="english",
        class_no=5,
        status="paused_for_masterclass",
        current_stage="chapter_level",
        profile_version_id=profile_version_id,
        state_json={"answered_item_ids": ["item_1"]},
    )
    await store.upsert_school_session(
        session_id=masterclass_id,
        user_id="learner",
        api_version="rebuild",
        flow_type="masterclass",
        subject_id="english",
        class_no=5,
        status="active",
        current_stage="guided",
        profile_version_id=profile_version_id,
        linked_session_id=curriculum_id,
        state_json={"trigger_skill_id": "writing.reason_answer"},
    )

    linked = await store.get_school_sessions_linked_to("learner", curriculum_id)
    assert [row["session_id"] for row in linked] == [masterclass_id]
