import json
import inspect
from pathlib import Path

import pytest

from app.db import repo as db_repo
from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import (
    LiveChapterActivity,
    LiveChapterLevel,
    LiveSchoolChapter,
    LiveSourceAnchor,
    LiveTeachingStep,
)
from app.services.school.projection import (
    SchoolAttemptEvidence,
    derive_school_projection_delta,
)
from app.services.school_core.readiness import (
    AttemptEvidence,
    SkillReadinessState,
    apply_attempt_evidence,
    classify_skill_status,
)


def _activity(**overrides) -> LiveChapterActivity:
    values = {
        "teaching_block": "Notice how the reader uses a clue before deciding.",
        "passage": "Mina carried an umbrella although the sky was still bright.",
        "prompt": "Which detail suggests that Mina expects rain?",
        "options": ["She carried an umbrella", "The sky was bright"],
        "accepted_answers": ["She carried an umbrella"],
        "response_mode": "short",
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": "guided_practice",
        "interaction_type": "single_choice",
        "evidence_role": "formative",
        "source_anchor_ids": ["eng_c5_u01_m01:think:4"],
        "knowledge_components": ["reading.inference_reason"],
    }
    values.update(overrides)
    return LiveChapterActivity(**values)


def _teaching_steps() -> list[LiveTeachingStep]:
    phases = (
        "connect",
        "explain",
        "model",
        "co_construct",
        "guided_practice",
        "feedback",
        "independent_application",
    )
    return [
        LiveTeachingStep(
            step_id=f"infer-{phase}",
            phase=phase,
            activity=_activity(
                teaching_phase=phase,
                interaction_type="continue",
                evidence_role=(
                    "certifying"
                    if phase == "independent_application"
                    else "experience"
                ),
                options=[],
                accepted_answers=["continue"],
            ),
        )
        for phase in phases
    ]


def test_activity_v2_keeps_deep_teaching_metadata_in_runtime_projection():
    activity = _activity()

    expected = {
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": "guided_practice",
        "interaction_type": "single_choice",
        "evidence_role": "formative",
        "source_anchor_ids": ["eng_c5_u01_m01:think:4"],
        "knowledge_components": ["reading.inference_reason"],
    }
    runtime = activity.runtime_dict()
    assert {key: runtime[key] for key in expected} == expected


def test_teaching_step_can_model_before_it_checks():
    step = LiveTeachingStep(
        step_id="infer-model-1",
        phase="model",
        required=True,
        activity=_activity(
            teaching_phase="model",
            interaction_type="continue",
            evidence_role="experience",
            options=[],
            accepted_answers=["continue"],
        ),
    )

    assert step.phase == "model"
    assert step.activity.interaction_type == "continue"


def test_source_anchor_records_coverage_without_storing_textbook_body():
    anchor = LiveSourceAnchor(
        anchor_id="eng_c5_u01_m01:think:4",
        section_label="Let us Think",
        page_start=4,
        page_end=4,
        source_url="https://ncert.nic.in/textbook/pdf/eesa101.pdf#page=4",
        coverage_treatment="textbook_companion",
        required_for_chapter_certification=True,
    )

    payload = anchor.model_dump()
    assert payload["section_label"] == "Let us Think"
    assert "textbook_body" not in payload
    assert anchor.required_for_chapter_certification is True


def test_source_anchor_rejects_non_official_material():
    with pytest.raises(
        ValueError,
        match="live_source_anchor_requires_official_ncert_url",
    ):
        LiveSourceAnchor(
            anchor_id="eng_c5_u01_m01:fake:1",
            section_label="Fake material",
            page_start=1,
            page_end=1,
            source_url="https://example.com/fake.pdf",
            coverage_treatment="textbook_companion",
        )


def test_deep_teaching_sequence_is_reachable_from_the_live_chapter_contract():
    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    payload = json.loads(chapter_path.read_text(encoding="utf-8"))
    anchor = LiveSourceAnchor(
        anchor_id="eng_c5_u01_m01:think:4",
        section_label="Let us Think",
        page_start=4,
        page_end=4,
        source_url="https://ncert.nic.in/textbook/pdf/eesa101.pdf#page=4",
        coverage_treatment="textbook_companion",
        required_for_chapter_certification=True,
    )
    payload["source_anchors"] = [anchor.model_dump()]
    payload["levels"][0].update({
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [anchor.anchor_id],
        "teaching_steps": [step.runtime_dict() for step in _teaching_steps()],
    })

    chapter = LiveSchoolChapter.model_validate(payload)

    assert chapter.levels[0].teaching_steps
    assert chapter.runtime_dict()["source_anchors"][0]["anchor_id"] == anchor.anchor_id


def test_deep_teaching_sequence_rejects_a_check_before_modeling():
    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    payload = json.loads(chapter_path.read_text(encoding="utf-8"))
    steps = _teaching_steps()
    steps[2], steps[4] = steps[4], steps[2]

    with pytest.raises(ValueError, match="invalid_live_teaching_phase_sequence"):
        LiveChapterLevel.model_validate({
            **payload["levels"][0],
            "episode_kind": "comprehension_studio",
            "source_anchor_ids": ["eng_c5_u01_m01:think:4"],
            "teaching_steps": [step.runtime_dict() for step in steps],
        })


def test_optional_teaching_steps_cannot_bypass_modeling_order():
    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    payload = json.loads(chapter_path.read_text(encoding="utf-8"))
    optional_early_check = LiveTeachingStep(
        step_id="infer-early-check",
        phase="guided_practice",
        required=False,
        activity=_activity(teaching_phase="guided_practice"),
    )

    with pytest.raises(ValueError, match="invalid_live_teaching_phase_sequence"):
        LiveChapterLevel.model_validate({
            **payload["levels"][0],
            "episode_kind": "comprehension_studio",
            "source_anchor_ids": ["eng_c5_u01_m01:think:4"],
            "teaching_steps": [
                optional_early_check.runtime_dict(),
                *[step.runtime_dict() for step in _teaching_steps()],
            ],
        })


def test_loader_rejects_skills_outside_the_class_band(tmp_path: Path):
    source_path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    class_root = tmp_path / "class_2"
    class_root.mkdir()
    target_path = class_root / source_path.name
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    payload["source_anchors"] = [{
        "anchor_id": "eng_c5_u01_m01:think:4",
        "section_label": "Let us Think",
        "page_start": 4,
        "page_end": 4,
        "source_url": "https://ncert.nic.in/textbook/pdf/eesa101.pdf#page=4",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": True,
    }]
    payload["levels"][0].update({
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": ["eng_c5_u01_m01:think:4"],
        "teaching_steps": [step.runtime_dict() for step in _teaching_steps()],
    })
    target_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="out_of_band_live_chapter_skill"):
        load_live_chapter_file(target_path)


def test_one_independent_chapter_check_cannot_make_skill_ready_or_mastered():
    state = apply_attempt_evidence(
        SkillReadinessState(skill_id="reading.inference_reason"),
        AttemptEvidence(
            attempt_type="chapter_check",
            evaluator_score=0.9,
            evaluator_confidence=1.0,
            skill_ids=("reading.inference_reason",),
            support_level="independent",
            language_required="en",
            language_detected="en",
        ),
    )

    assert classify_skill_status(state) == "practice_ready"
    assert state.chapter_passes == 1
    assert state.transfer_passes == 0


def test_chapter_check_cannot_replace_a_later_retention_review():
    state = SkillReadinessState(
        skill_id="reading.inference_reason",
        practice_readiness=0.8,
        certified_readiness=0.8,
        total_attempts=4,
        certified_attempts=4,
        independent_passes=3,
        transfer_passes=1,
        recent_hint_flags=(False, False, False, False),
    )
    state = apply_attempt_evidence(
        state,
        AttemptEvidence(
            attempt_type="chapter_check",
            evaluator_score=1.0,
            evaluator_confidence=1.0,
            skill_ids=("reading.inference_reason",),
            support_level="independent",
        ),
    )

    assert state.certified_readiness >= 0.9
    assert state.review_passes == 0
    assert classify_skill_status(state) == "ready"


def test_terminal_placement_seed_is_persisted_as_ready_without_mastery():
    evidence = SchoolAttemptEvidence.from_dict({
        "session_id": "placement-1",
        "chapter_id": "",
        "level_id": "confirmatory",
        "module_id": "english",
        "task_type": "school_rebuild_placement",
        "focus": "Infer a reason from evidence",
        "skill_ids": ["reading.inference_reason"],
        "attempt_type": "confirmatory",
        "score": 0.9,
        "confidence": 0.95,
        "criteria": [],
        "blockers": [],
        "answer_excerpt": "The clue explains the character's choice.",
        "attempt_passed": True,
        "placement_ready_skill_confidence": {
            "reading.inference_reason": 0.95,
        },
    })

    [row] = derive_school_projection_delta(evidence, [])

    state = row["evidence_json"]["school_readiness_state"]
    assert row["evidence_json"]["skill_status"] == "ready"
    assert state["ready_source"] == "placement"
    assert state["independent_passes"] == 0
    assert row["mastery"] == 0.0


def test_failed_high_score_cannot_count_as_a_certifying_pass():
    prior = []
    for attempt_no in (1, 2):
        evidence = SchoolAttemptEvidence.from_dict({
            "session_id": "curriculum-1",
            "chapter_id": "eng_c5_ch01",
            "level_id": "infer",
            "module_id": "eng_c5_u01_m01",
            "task_type": "school_rebuild_curriculum",
            "focus": "Infer a reason from evidence",
            "skill_ids": ["reading.inference_reason"],
            "attempt_type": "independent_check",
            "score": 0.95,
            "confidence": 1.0,
            "criteria": [],
            "blockers": [],
            "answer_excerpt": f"Attempt {attempt_no}",
            "attempt_passed": False,
        })
        [row] = derive_school_projection_delta(evidence, prior)
        prior = [row]

    state = row["evidence_json"]["school_readiness_state"]
    assert state["independent_passes"] == 0
    assert "attempt_not_passed" in state["active_blockers"]
    assert row["evidence_json"]["skill_status"] == "weak"


def test_projection_uses_shared_readiness_state_and_never_turns_one_chapter_score_into_mastery():
    evidence = SchoolAttemptEvidence.from_dict(
        {
            "session_id": "session-1",
            "chapter_id": "eng_c5_ch01",
            "level_id": "chapter-check",
            "module_id": "eng_c5_u01_m01",
            "task_type": "school_rebuild_curriculum",
            "focus": "Infer a reason from evidence",
            "skill_ids": ["reading.inference_reason"],
            "attempt_type": "chapter_check",
            "score": 0.9,
            "confidence": 1.0,
            "criteria": [],
            "blockers": [],
            "answer_excerpt": "The clue shows that she expected rain.",
            "attempt_passed": True,
            "certified_skill_scores": {"reading.inference_reason": 0.9},
        }
    )

    [row] = derive_school_projection_delta(evidence, [])

    assert row["readiness"] >= 0.8
    assert row["mastery"] < 1.0
    readiness_state = row["evidence_json"]["school_readiness_state"]
    assert row["evidence_json"]["skill_status"] == "practice_ready"
    assert readiness_state["chapter_passes"] == 1
    assert readiness_state["transfer_passes"] == 0


def test_no_second_school_readiness_formula_exists_outside_shared_core():
    services_root = Path(__file__).resolve().parents[2] / "app" / "services"
    offenders = []
    for relative_path in ("school/projection.py", "school_rebuild_learning.py"):
        path = services_root / relative_path
        if "_ATTEMPT_ALPHA" in path.read_text(encoding="utf-8"):
            offenders.append(relative_path)

    assert offenders == []


def test_school_profile_persistence_uses_projection_mastery_not_monotonic_sql():
    source = inspect.getsource(db_repo.upsert_learner_skill_profile)

    assert "WHEN EXCLUDED.domain = 'school' THEN EXCLUDED.mastery" in source
    assert "ELSE GREATEST(learner_skill_profiles.mastery, EXCLUDED.mastery)" in source
