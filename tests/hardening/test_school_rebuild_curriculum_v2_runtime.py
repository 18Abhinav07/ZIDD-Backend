from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_schema import (
    LiveChapterActivity,
    LiveChapterChecks,
    LiveChapterLevel,
)
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION
from app.services import school_rebuild_curriculum as curriculum


PHASES = (
    "connect",
    "explain",
    "model",
    "co_construct",
    "guided_practice",
    "feedback",
    "independent_application",
    "transfer",
    "review",
)
COMPACT_PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
SKILL_ID = "reading.detail"
ANCHOR_ID = "eng_c5_ch01:detail:1"


def _continue_activity(phase: str, *, level_id: str) -> dict:
    return {
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": phase,
        "interaction_type": "continue",
        "evidence_role": "experience",
        "source_anchor_ids": [ANCHOR_ID],
        "knowledge_components": [SKILL_ID],
        "teaching_block": f"Notice the chapter detail during {phase} in {level_id}.",
        "passage": f"Original teaching passage for {phase} in {level_id}.",
        "prompt": (
            f"Continue the {phase} teaching step for {level_id} when you are ready."
        ),
        "options": [],
        "accepted_answers": [],
    }


def _choice_activity(phase: str, ordinal: int, *, role: str) -> dict:
    variant_id = f"{phase}-v{ordinal}"
    answer = f"answer-{variant_id}"
    return {
        "schema_version": "school-activity-v2",
        "episode_kind": "comprehension_studio",
        "teaching_phase": phase,
        "interaction_type": "single_choice",
        "evidence_role": role,
        "certifying_language": "en" if role == "certifying" else None,
        "source_anchor_ids": [ANCHOR_ID],
        "knowledge_components": [SKILL_ID],
        "target_misconception_tags": ["missed_detail"],
        "relevance_terms": ["supported detail", "clue"],
        "pool_id": f"{phase}-pool",
        "variant_id": variant_id,
        "teaching_block": f"Use the detail skill in variant {ordinal}.",
        "passage": f"Original variant passage {ordinal} for {phase}.",
        "prompt": f"Which {phase} detail is supported in variant {ordinal}?",
        "options": [answer, f"wrong-{variant_id}"],
        "accepted_answers": [answer],
        "grading_mode": "selected_option",
        "response_mode": "short",
    }


def _step(phase: str, *, level_id: str) -> dict:
    if phase in {"connect", "explain", "model", "co_construct", "feedback"}:
        return {
            "step_id": f"step-{phase}",
            "phase": phase,
            "required": True,
            "activity": _continue_activity(phase, level_id=level_id),
        }
    role = "formative" if phase == "guided_practice" else "certifying"
    return {
        "step_id": f"step-{phase}",
        "phase": phase,
        "required": True,
        "pool_id": f"{phase}-pool",
        "variant_pool": [
            _choice_activity(phase, ordinal, role=role) for ordinal in range(1, 5)
        ],
    }


def _state(*, with_second_level: bool = False) -> dict:
    support_check = {
        "teaching_block": "Use one smaller clue before a fresh independent example.",
        "passage": "A separate support passage about a blue satchel.",
        "prompt": "Choose the supported detail.",
        "options": ["support-answer", "support-distractor"],
        "accepted_answers": ["support-answer"],
        "grading_mode": "selected_option",
        "knowledge_components": [SKILL_ID],
        "target_misconception_tags": ["missed_detail"],
    }

    def support_variant(ordinal: int) -> dict:
        return {
            **deepcopy(support_check),
            "teaching_block": f"Use authored support clue {ordinal}.",
            "passage": f"A fresh support passage {ordinal} about a school bag.",
            "prompt": f"Choose supported detail {ordinal}.",
        }

    def level(level_id: str) -> dict:
        return {
            "level_id": level_id,
            "title": "Find precise details",
            "focus": "Use a detail as evidence",
            "skill_ids": [SKILL_ID],
            "status": "not_started",
            "current_step": "connect",
            "attempts": [],
            "v2_step_index": 0,
            "v2_support_mode": None,
            "used_variant_ids": [],
            "episode_kind": "comprehension_studio",
            "source_anchor_ids": [ANCHOR_ID],
            "teaching_steps": [
                _step(phase, level_id=level_id) for phase in PHASES
            ],
            "checks": {
                "guided_check": deepcopy(support_check),
                "bridge": deepcopy(support_check),
                "revision_level_1": support_variant(1),
                "revision_level_2": support_variant(2),
                "revision_level_3": support_variant(3),
                "masterclass": deepcopy(support_check),
                "independent_check": deepcopy(support_check),
            },
        }

    levels = [level("detail-level-1")]
    if with_second_level:
        levels.append(level("detail-level-2"))
    levels[0]["status"] = "in_progress"
    return curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "status": "active",
            "phase": "learning",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "preferred_teaching_language": "en",
            "current_level_index": 0,
            "chapter": {"chapter_id": "eng_c5_ch01", "title": "Chapter one"},
            "chapter_assessment": None,
            "levels": levels,
            "hot_session_memory": {},
            "active_interrupt": None,
            "interrupt_history": [],
            "interrupt_counts": {},
        }
    )


def _current(state: dict) -> dict:
    activity = curriculum._current_activity(state)
    assert activity is not None
    return activity


def _answer(state: dict, answer: str) -> tuple[dict, dict]:
    activity = _current(state)
    return curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
    )


def _answer_correctly(state: dict) -> tuple[dict, dict]:
    activity = _current(state)
    answer = (
        "continue"
        if activity["interaction_type"] == "continue"
        else activity["accepted_answers"][0]
    )
    return _answer(state, answer)


def _advance_to_phase(state: dict, target_phase: str) -> dict:
    while _current(state)["phase"] != target_phase:
        state, _ = _answer_correctly(state)
    return state


def _wrong_current_answer(state: dict) -> tuple[dict, dict]:
    activity = _current(state)
    wrong = (
        activity["options"][1]
        if len(activity.get("options") or []) > 1
        else "unsupported answer"
    )
    return _answer(state, wrong)


def _target_ready_profile() -> dict:
    return {
        "profile_version_id": "profile-ready",
        "display_name": "Mira",
        "target_class_no": 5,
        "subject_ids": ["english"],
        "preferred_teaching_language": "en",
    }


def _target_ready_report() -> dict:
    return {
        "report_id": "placement-ready",
        "placement_status": "target_ready",
        "unlock_state": "target_unlocked",
    }


def _pause_for_masterclass(state: dict) -> dict:
    state, _ = _wrong_current_answer(state)
    assert _current(state)["support_mode"] == "bridge"
    state, _ = _wrong_current_answer(state)
    assert state["status"] == "paused_for_masterclass"
    return state


def _capped_state_with_exhausted_return_step(state: dict) -> tuple[dict, dict]:
    for trigger in (1, 2):
        state = _pause_for_masterclass(state)
        child_id = f"masterclass-{trigger}"
        state = curriculum.attach_masterclass_session(
            state,
            masterclass_session_id=child_id,
        )
        state = curriculum.resume_after_masterclass(
            state,
            masterclass_session_id=child_id,
            resolution="abandoned",
        )

    state, _ = _wrong_current_answer(state)
    state, _ = _wrong_current_answer(state)
    assert state["phase"] == "capped_support"

    state = curriculum.continue_after_support_cap(state)
    state, _ = _wrong_current_answer(state)
    state, _ = _wrong_current_answer(state)
    assert state["phase"] == "capped_support"

    level = state["levels"][0]
    return_step = level["teaching_steps"][level["v2_step_index"]]
    assert all(
        variant["variant_id"] in level["used_variant_ids"]
        for variant in return_step["variant_pool"]
    )
    return state, return_step


def test_v2_runs_all_nine_phases_and_starts_the_next_level():
    state = _state(with_second_level=True)

    visited = []
    for expected in PHASES:
        activity = _current(state)
        visited.append(activity["phase"])
        assert activity["phase"] == expected
        state, evaluation = _answer_correctly(state)
        assert evaluation["scored"] is (activity["interaction_type"] != "continue")

    assert tuple(visited) == PHASES
    assert state["levels"][0]["status"] == "complete"
    assert state["levels"][1]["status"] == "in_progress"
    assert state["current_level_index"] == 1
    assert _current(state)["phase"] == "connect"


def test_target_ready_learner_starts_each_level_with_an_authored_challenge():
    state = curriculum.new_curriculum_state(
        school_profile=_target_ready_profile(),
        placement_report=_target_ready_report(),
        recap_session=None,
    )

    for level in state["levels"]:
        independent_index = next(
            index
            for index, step in enumerate(level["teaching_steps"])
            if step["phase"] == "independent_application"
        )
        assert level["entry_mode"] == "challenge"
        assert level["v2_step_index"] == independent_index

    activity = _current(state)
    assert activity["phase"] == "independent_application"
    assert activity["entry_mode"] == "challenge"


def test_active_gap_suppresses_target_ready_challenge_for_affected_level():
    state = curriculum.new_curriculum_state(
        school_profile=_target_ready_profile(),
        placement_report=_target_ready_report(),
        recap_session=None,
        learning_memory={
            "active_gaps": [
                {
                    "skill_id": "reading.inference_reason",
                    "skill_status": "weak",
                }
            ]
        },
    )

    first = state["levels"][0]
    second = state["levels"][1]
    assert first["entry_mode"] == "full_cycle"
    assert first["v2_step_index"] == 0
    assert second["entry_mode"] == "challenge"


def test_failed_entry_challenge_returns_to_full_teaching_before_support():
    state = _state()
    level = state["levels"][0]
    level["entry_mode"] = "challenge"
    level["v2_step_index"] = PHASES.index("independent_application")
    level["current_step"] = "independent_application"
    state = curriculum.normalize_curriculum_state(state)

    state, _ = _wrong_current_answer(state)

    assert state["levels"][0]["entry_mode"] == "full_cycle"
    assert state["levels"][0]["v2_support_mode"] is None
    assert _current(state)["phase"] == "connect"
    assert state["feedback_v2"]["retry_policy"] == "challenge_fallback"


def test_level_contract_accepts_compact_teaching_cycle_without_losing_proof_phases():
    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    level_payload = deepcopy(json.loads(chapter_path.read_text())["levels"][0])
    level_payload["teaching_steps"] = [
        step
        for step in level_payload["teaching_steps"]
        if step["phase"] in COMPACT_PHASES
    ]

    level = LiveChapterLevel.model_validate(level_payload)

    assert tuple(step.phase for step in level.teaching_steps or ()) == COMPACT_PHASES


def test_end_of_review_refuses_to_complete_without_a_chapter_assessment():
    state = _state()
    for _ in PHASES[:-1]:
        state, _ = _answer_correctly(state)

    with pytest.raises(ValueError, match="chapter_assessment_required_for_v2"):
        _answer_correctly(state)


def test_wrong_certifying_answer_bridges_then_retries_same_phase_fresh():
    state = _advance_to_phase(_state(), "independent_application")
    first = _current(state)
    state, evaluation = _wrong_current_answer(state)

    bridge = _current(state)
    assert evaluation["correct"] is False
    assert bridge["support_mode"] == "bridge"
    assert state["levels"][0]["v2_step_index"] == PHASES.index(
        "independent_application"
    )
    assert state["levels"][0]["v2_return_activity_id"] == first["activity_id"]

    state, _ = _answer(state, "support-answer")
    retry = _current(state)
    assert retry["phase"] == "independent_application"
    assert retry["variant"]["variant_id"] != first["variant"]["variant_id"]
    assert retry["variant"]["fresh"] is True
    assert first["variant"]["variant_id"] in state["levels"][0][
        "used_variant_ids"
    ]
    assert first["variant"]["variant_id"] in state["hot_session_memory"][
        "used_variant_ids"
    ]


def test_exhausted_required_variant_pool_fails_loudly():
    state = _advance_to_phase(_state(), "independent_application")
    variants = {
        item["variant_id"]
        for item in state["levels"][0]["teaching_steps"][6]["variant_pool"]
    }
    state["levels"][0]["used_variant_ids"] = sorted(variants)

    with pytest.raises(ValueError, match="authored_variant_pool_exhausted"):
        curriculum._current_activity(state)


def test_variant_selection_rejects_repeated_passage_and_prompt_fingerprints():
    state = _advance_to_phase(_state(), "independent_application")
    first_variant = state["levels"][0]["teaching_steps"][6]["variant_pool"][0]
    state["hot_session_memory"]["passage_fingerprints"] = [
        curriculum._content_fingerprint(first_variant["passage"])
    ]
    state["hot_session_memory"]["prompt_fingerprints"] = [
        curriculum._content_fingerprint(first_variant["prompt"])
    ]

    selected = _current(state)

    assert selected["variant"]["variant_id"] != first_variant["variant_id"]
    assert selected["passage"] != first_variant["passage"]
    assert selected["prompt"] != first_variant["prompt"]


def test_fingerprint_history_remains_complete_when_state_is_normalized():
    passage_fingerprints = [
        curriculum._content_fingerprint(f"passage {index}")
        for index in range(41)
    ]
    prompt_fingerprints = [
        curriculum._content_fingerprint(f"prompt {index}")
        for index in range(41)
    ]

    normalized = curriculum.normalize_curriculum_state(
        {
            "levels": [],
            "hot_session_memory": {
                "passage_fingerprints": passage_fingerprints,
                "prompt_fingerprints": prompt_fingerprints,
            },
        }
    )

    assert normalized["hot_session_memory"]["passage_fingerprints"] == (
        passage_fingerprints
    )
    assert normalized["hot_session_memory"]["prompt_fingerprints"] == (
        prompt_fingerprints
    )


def test_lifecycle_rejects_case_and_whitespace_duplicate_after_answer():
    state = _state()
    served = _current(state)
    duplicate = state["levels"][0]["teaching_steps"][1]["activity"]
    duplicate["passage"] = f"  {served['passage'].upper()}\n"
    duplicate["prompt"] = f"\t{served['prompt'].upper()}  "

    state, _ = _answer(state, "continue")

    assert curriculum._content_fingerprint(served["passage"]) in state[
        "hot_session_memory"
    ]["passage_fingerprints"]
    assert curriculum._content_fingerprint(served["prompt"]) in state[
        "hot_session_memory"
    ]["prompt_fingerprints"]
    with pytest.raises(ValueError, match="authored_activity_variant_unavailable"):
        _current(state)


def test_support_check_rejects_normalized_duplicate_after_trigger_answer():
    state = _advance_to_phase(_state(), "independent_application")
    served = _current(state)
    state, _ = _wrong_current_answer(state)
    for support in state["levels"][0]["checks"].values():
        support["passage"] = f"  {served['passage'].upper()}\n"
        support["prompt"] = f"\t{served['prompt'].upper()}  "

    with pytest.raises(ValueError, match="authored_support_pool_exhausted"):
        _current(state)


def test_legacy_check_rejects_duplicate_after_answer_transition():
    state = _state()
    level = state["levels"][0]
    authored = deepcopy(level["teaching_steps"][0]["activity"])
    level.pop("teaching_steps")
    level["checks"]["guided_check"] = authored
    level["checks"]["bridge"] = {
        **deepcopy(authored),
        "passage": f"  {authored['passage'].upper()}\n",
        "prompt": f"\t{authored['prompt'].upper()}  ",
    }
    level["return_step"] = "bridge"
    level["current_step"] = "guided_check"
    state = curriculum.normalize_curriculum_state(state)

    state, _ = _answer(state, "continue")
    state["levels"][0]["current_step"] = "guided_check"

    with pytest.raises(ValueError, match="authored_activity_variant_unavailable"):
        _current(state)


def test_normalization_recovers_fingerprints_from_pre_patch_attempts():
    state = _state()
    level = state["levels"][0]
    served = deepcopy(level["teaching_steps"][0]["activity"])
    duplicate = level["teaching_steps"][1]["activity"]
    duplicate["passage"] = f"  {served['passage'].upper()}\n"
    duplicate["prompt"] = f"\t{served['prompt'].upper()}  "
    level["attempts"] = [
        {
            "step_id": "step-connect",
            "variant_id": "step-connect:single",
        }
    ]
    level["v2_step_index"] = 1
    level["current_step"] = "explain"
    state["hot_session_memory"] = {}

    migrated = curriculum.normalize_curriculum_state(state)

    assert curriculum._content_fingerprint(served["passage"]) in migrated[
        "hot_session_memory"
    ]["passage_fingerprints"]
    with pytest.raises(ValueError, match="authored_activity_variant_unavailable"):
        _current(migrated)


def test_chapter_check_rejects_duplicate_after_answer_transition():
    state = _state()
    first_item = {
        **_choice_activity("chapter_check", 1, role="certifying"),
        "item_id": "chapter-item-1",
        "skill_ids": [SKILL_ID],
    }
    second_item = {
        **_choice_activity("chapter_check", 2, role="certifying"),
        "item_id": "chapter-item-2",
        "skill_ids": [SKILL_ID],
        "passage": f"  {first_item['passage'].upper()}\n",
        "prompt": f"\t{first_item['prompt'].upper()}  ",
    }
    state["phase"] = "chapter_check"
    state["chapter_assessment"] = {
        "attempt_no": 1,
        "selected_item_ids": ["chapter-item-1", "chapter-item-2"],
        "current_index": 0,
        "items": [first_item, second_item],
        "responses": [],
    }

    state, _ = _answer_correctly(state)

    with pytest.raises(ValueError, match="chapter_assessment_fresh_form_unavailable"):
        _current(state)


def test_singleton_selection_rejects_repeated_passage_and_prompt_fingerprints():
    state = _state()
    level = state["levels"][0]
    step = level["teaching_steps"][0]
    activity = step["activity"]
    state["hot_session_memory"]["passage_fingerprints"] = [
        curriculum._content_fingerprint(activity["passage"])
    ]
    state["hot_session_memory"]["prompt_fingerprints"] = [
        curriculum._content_fingerprint(activity["prompt"])
    ]

    selected, variant_id, fresh = curriculum._v2_step_activity(state, level, step)

    assert selected is None
    assert variant_id == "step-connect:single"
    assert fresh is False
    with pytest.raises(ValueError, match="authored_activity_variant_unavailable"):
        curriculum._current_activity(state)


def test_exhausted_authored_support_pool_fails_instead_of_reusing_revision_three():
    state = _advance_to_phase(_state(), "independent_application")
    state["levels"][0]["v2_support_mode"] = "bridge"
    state["levels"][0]["attempts"] = [
        {"kind": "v2_support", "activity_id": f"support-{index}"}
        for index in range(4)
    ]

    with pytest.raises(ValueError, match="authored_support_pool_exhausted"):
        curriculum._current_activity(state)


def test_chapter_remediation_uses_authored_masterclass_without_bridge_pool():
    state = _state()
    masterclass = deepcopy(state["levels"][0]["checks"]["masterclass"])
    state["levels"][0]["checks"] = {"masterclass": masterclass}

    state = curriculum._start_assessment_remediation(state, [SKILL_ID])
    activity = curriculum._current_activity(state)

    assert activity is not None
    assert activity["kind"] == "v2_support"
    assert activity["variant"]["variant_id"] == "masterclass"
    assert activity["assessed_skill_ids"] == [SKILL_ID]
    assert activity["prompt"] == masterclass["prompt"]


def test_chapter_remediation_without_authored_support_returns_safe_plan():
    state = _state()
    state["levels"][0]["checks"] = {}

    state = curriculum._start_assessment_remediation(state, [SKILL_ID])

    assert state["status"] == "active"
    assert state["phase"] == "needs_support"
    assert curriculum._current_activity(state) is None
    assert state["support_required"]["reason"] == (
        "authored_remediation_unavailable"
    )
    assert state["support_required"]["remediation_skill_ids"] == [SKILL_ID]
    public = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )
    assert public["next_action"] == {
        "action": "view_support_plan",
        "next_action_url": "/school/support/session-1",
        "reason": "authored_remediation_unavailable",
        "requires_explicit_confirmation": False,
    }


def test_expanded_chapter_remediation_without_revision_content_returns_safe_plan():
    state = _state()
    masterclass = deepcopy(state["levels"][0]["checks"]["masterclass"])
    state["levels"][0]["checks"] = {"masterclass": masterclass}

    state = curriculum._start_assessment_remediation(
        state,
        [SKILL_ID],
        mode="expanded_revision",
        skill_scores={SKILL_ID: 0.2},
    )

    assert state["status"] == "active"
    assert state["phase"] == "needs_support"
    assert curriculum._current_activity(state) is None
    assert state["support_required"]["reason"] == (
        "authored_remediation_unavailable"
    )
    assert state["support_required"]["remediation_skill_ids"] == [SKILL_ID]


def test_public_option_order_is_stable_varied_and_evaluated_by_value():
    options = ["authored-correct", "distractor-a", "distractor-b"]
    presentations = [
        curriculum._stable_public_options(f"activity-{index}", options)
        for index in range(8)
    ]

    assert presentations == [
        curriculum._stable_public_options(f"activity-{index}", options)
        for index in range(8)
    ]
    correct_positions = {
        presentation.index("authored-correct")
        for presentation in presentations
    }
    assert len(correct_positions) > 1
    assert any(presentation[0] != "authored-correct" for presentation in presentations)

    activity = {
        "activity_id": "activity-0",
        "grading_mode": "selected_option",
        "accepted_answers": ["authored-correct"],
        "options": options,
    }
    assert curriculum.evaluate_deterministic_answer(
        activity,
        "authored-correct",
    )["correct"] is True
    assert curriculum.evaluate_deterministic_answer(
        activity,
        presentations[0][0],
    )["correct"] is False


def test_resume_requires_the_exact_attached_masterclass_and_restores_position():
    state = _advance_to_phase(_state(), "transfer")
    return_step_index = state["levels"][0]["v2_step_index"]
    return_activity_id = _current(state)["activity_id"]
    state = _pause_for_masterclass(state)

    with pytest.raises(ValueError, match="masterclass_session_not_attached"):
        curriculum.resume_after_masterclass(
            state,
            masterclass_session_id="masterclass-1",
            resolution="complete",
        )

    state = curriculum.attach_masterclass_session(
        state,
        masterclass_session_id="masterclass-1",
    )
    with pytest.raises(ValueError, match="masterclass_session_mismatch"):
        curriculum.resume_after_masterclass(
            state,
            masterclass_session_id="wrong-child",
            resolution="complete",
        )

    state = curriculum.resume_after_masterclass(
        state,
        masterclass_session_id="masterclass-1",
        resolution="complete",
    )
    retry = _current(state)
    assert state["current_level_index"] == 0
    assert state["levels"][0]["v2_step_index"] == return_step_index
    assert state["levels"][0]["v2_support_mode"] is None
    assert retry["phase"] == "transfer"
    assert retry["lineage"]["return_activity_id"] == return_activity_id
    assert retry["lineage"]["masterclass_session_id"] == "masterclass-1"


def test_resume_excludes_variants_already_consumed_inside_masterclass():
    state = _advance_to_phase(_state(), "transfer")
    state = _pause_for_masterclass(state)
    state = curriculum.attach_masterclass_session(
        state,
        masterclass_session_id="masterclass-1",
    )

    state = curriculum.resume_after_masterclass(
        state,
        masterclass_session_id="masterclass-1",
        resolution="complete",
        consumed_variant_ids=["transfer-v2"],
    )

    retry = _current(state)
    assert retry["phase"] == "transfer"
    assert retry["variant"]["variant_id"] != "transfer-v2"
    assert "transfer-v2" in state["levels"][0]["used_variant_ids"]


def test_completed_masterclass_advances_when_saved_step_has_no_fresh_variant():
    state = _advance_to_phase(_state(), "transfer")
    state = _pause_for_masterclass(state)
    state = curriculum.attach_masterclass_session(
        state,
        masterclass_session_id="masterclass-1",
    )
    level = state["levels"][0]
    return_step_index = int(state["active_interrupt"]["return_step_index"])
    return_step = level["teaching_steps"][return_step_index]
    level["used_variant_ids"] = [
        candidate["variant_id"]
        for candidate in return_step["variant_pool"]
    ]

    resumed = curriculum.resume_after_masterclass(
        state,
        masterclass_session_id="masterclass-1",
        resolution="complete",
    )

    assert resumed["status"] == "active"
    assert resumed["phase"] == "learning"
    assert resumed["levels"][0]["v2_step_index"] == return_step_index + 1
    assert resumed["feedback_v2"]["outcome"] == (
        "masterclass_complete_advanced"
    )
    assert resumed["feedback_v2"]["retry_policy"] == (
        "advance_after_exhausted_return"
    )
    assert "next authored lesson step" in resumed["feedback_v2"]["next_support"]
    assert _current(resumed)["phase"] == "review"


def test_recover_completed_masterclass_replay_advances_legacy_partial_transition():
    state = _advance_to_phase(_state(), "transfer")
    state = _pause_for_masterclass(state)
    state = curriculum.attach_masterclass_session(
        state,
        masterclass_session_id="masterclass-1",
    )
    interrupt = deepcopy(state["active_interrupt"])
    level = state["levels"][0]
    return_step_index = int(interrupt["return_step_index"])
    return_step = level["teaching_steps"][return_step_index]
    level["used_variant_ids"] = [
        candidate["variant_id"]
        for candidate in return_step["variant_pool"]
    ]
    level["status"] = "in_progress"
    level["v2_step_index"] = return_step_index
    level["current_step"] = return_step["phase"]
    level["v2_support_mode"] = None
    level["v2_last_masterclass_session_id"] = "masterclass-1"
    legacy_partial = curriculum.normalize_curriculum_state({
        **state,
        "status": "active",
        "phase": "learning",
        "active_interrupt": None,
        "interrupt_history": [
            *state["interrupt_history"],
            {
                **interrupt,
                "masterclass_session_id": "masterclass-1",
                "resolution": "complete",
            },
        ],
    })

    recovered = curriculum.recover_completed_masterclass_replay(
        legacy_partial,
        masterclass_session_id="masterclass-1",
    )

    assert recovered is not None
    assert recovered["levels"][0]["v2_step_index"] == return_step_index + 1
    assert recovered["feedback_v2"]["outcome"] == (
        "masterclass_complete_advanced"
    )
    assert _current(recovered)["phase"] == "review"


def test_abandon_consumes_interrupt_cap_and_third_trigger_caps_without_child():
    state = _advance_to_phase(_state(), "review")

    for trigger in (1, 2):
        state = _pause_for_masterclass(state)
        child_id = f"masterclass-{trigger}"
        state = curriculum.attach_masterclass_session(
            state,
            masterclass_session_id=child_id,
        )
        state = curriculum.resume_after_masterclass(
            state,
            masterclass_session_id=child_id,
            resolution="abandoned",
        )
        assert state["interrupt_counts"]["detail-level-1"] == trigger
        assert state["interrupt_history"][-1]["resolution"] == "abandoned"
        assert _current(state)["phase"] == "review"

    state, _ = _wrong_current_answer(state)
    assert _current(state)["support_mode"] == "bridge"
    state, _ = _wrong_current_answer(state)
    assert state["status"] == "active"
    assert state["phase"] == "capped_support"
    assert state["active_interrupt"] is None
    assert state["interrupt_counts"]["detail-level-1"] == 3
    assert state["interrupt_history"][-1]["resolution"] == "capped_out"
    assert "masterclass_cap_exceeded" in state["levels"][0]["active_blockers"]
    assert state["support_required"] == {
        "reason": "masterclass_cap_exceeded",
        "level_id": "detail-level-1",
        "skill_ids": ["reading.detail"],
        "focus": "Use a detail as evidence",
        "auto_masterclass_disabled": True,
        "continuation_action": "continue_after_support_cap",
        "cap": {
            "used": 2,
            "limit": 2,
            "scope": "level",
        },
        "history": [
            {
                "interrupt_id": "detail-level-1:masterclass:1",
                "level_id": "detail-level-1",
                "focus": "Use a detail as evidence",
                "skill_ids": ["reading.detail"],
                "trigger_count": 1,
                "masterclass_session_id": "masterclass-1",
                "resolution": "abandoned",
            },
            {
                "interrupt_id": "detail-level-1:masterclass:2",
                "level_id": "detail-level-1",
                "focus": "Use a detail as evidence",
                "skill_ids": ["reading.detail"],
                "trigger_count": 2,
                "masterclass_session_id": "masterclass-2",
                "resolution": "abandoned",
            },
        ],
    }


def test_capped_support_requires_explicit_continue_then_resumes_fresh_without_credit():
    state = _advance_to_phase(_state(), "review")

    for trigger in (1, 2):
        state = _pause_for_masterclass(state)
        child_id = f"masterclass-{trigger}"
        state = curriculum.attach_masterclass_session(
            state,
            masterclass_session_id=child_id,
        )
        state = curriculum.resume_after_masterclass(
            state,
            masterclass_session_id=child_id,
            resolution="abandoned",
        )

    failed_activity = _current(state)
    failed_variant_id = failed_activity["variant"]["variant_id"]
    state, _ = _wrong_current_answer(state)
    state, _ = _wrong_current_answer(state)

    public = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": state["status"], "state_json": state}
    )
    assert public["current_activity"] is None
    assert public["next_action"] == {
        "action": "continue_after_support_cap",
        "level_id": "detail-level-1",
        "reason": "masterclass_cap_exceeded",
        "requires_explicit_confirmation": True,
    }

    history_before = deepcopy(state["interrupt_history"])
    state = curriculum.continue_after_support_cap(state)

    assert state["status"] == "active"
    assert state["phase"] == "learning"
    assert state["levels"][0]["status"] == "in_progress"
    assert state["levels"][0]["v2_auto_masterclass_disabled"] is True
    assert "masterclass_cap_exceeded" in state["levels"][0]["active_blockers"]
    assert state["support_required"]["reason"] == "masterclass_cap_exceeded"
    assert state["interrupt_history"] == history_before

    retry = _current(state)
    assert retry["phase"] == "review"
    assert retry["variant"]["variant_id"] != failed_variant_id
    assert retry["grading_mode"] == "selected_option"
    assert retry["certifying_language"] == "en"
    assert retry["relevance_terms"] == ["supported detail", "clue"]

    state, _ = _wrong_current_answer(state)
    state, _ = _wrong_current_answer(state)
    assert state["status"] == "active"
    assert state["phase"] == "capped_support"
    assert state["active_interrupt"] is None
    assert state["interrupt_counts"]["detail-level-1"] == 3


def test_capped_support_advances_past_an_exhausted_return_step_without_credit():
    state, return_step = _capped_state_with_exhausted_return_step(
        _advance_to_phase(_state(), "transfer")
    )
    level_before = state["levels"][0]
    used_variant_ids_before = list(level_before["used_variant_ids"])
    interrupt_history_before = deepcopy(state["interrupt_history"])

    resumed = curriculum.continue_after_support_cap(state)

    level_after = resumed["levels"][0]
    assert resumed["status"] == "active"
    assert resumed["phase"] == "learning"
    assert level_after["status"] == "in_progress"
    assert level_after["v2_step_index"] == level_before["v2_step_index"] + 1
    assert level_after["current_step"] == "review"
    assert level_after["used_variant_ids"] == used_variant_ids_before
    assert "masterclass_cap_exceeded" in level_after["active_blockers"]
    assert resumed["interrupt_history"] == interrupt_history_before
    assert resumed["chapter_assessment"] is None
    assert resumed["feedback_v2"]["outcome"] == "continued_after_support_cap_advanced"
    assert resumed["feedback_v2"]["correct"] is None
    assert resumed["feedback_v2"]["scored"] is False
    public = curriculum.public_curriculum_response(
        {
            "session_id": "session-1",
            "status": resumed["status"],
            "state_json": resumed,
        }
    )
    assert public["feedback_v2"]["outcome"] == "continued_after_support_cap_advanced"

    next_activity = _current(resumed)
    assert next_activity["phase"] == "review"
    assert next_activity["variant"]["variant_id"] not in used_variant_ids_before
    assert next_activity["prompt"] not in {
        variant["prompt"] for variant in return_step["variant_pool"]
    }


def test_capped_support_raises_typed_error_without_next_authored_activity():
    state, _ = _capped_state_with_exhausted_return_step(
        _advance_to_phase(_state(), "review")
    )

    with pytest.raises(
        ValueError,
        match="capped_support_return_activity_unavailable",
    ):
        curriculum.continue_after_support_cap(state)


def test_capped_support_rejects_replayed_singleton_successor_after_exhausted_pool():
    state = _advance_to_phase(_state(), "review")
    level = state["levels"][0]
    repeated_activity = deepcopy(level["teaching_steps"][0]["activity"])
    repeated_activity["teaching_phase"] = "final_continue"
    level["teaching_steps"].append(
        {
            "step_id": "step-final-continue",
            "phase": "final_continue",
            "required": True,
            "activity": repeated_activity,
        }
    )
    state, return_step = _capped_state_with_exhausted_return_step(state)

    assert return_step["phase"] == "review"
    assert curriculum._content_fingerprint(repeated_activity["passage"]) in state[
        "hot_session_memory"
    ]["passage_fingerprints"]
    assert curriculum._content_fingerprint(repeated_activity["prompt"]) in state[
        "hot_session_memory"
    ]["prompt_fingerprints"]
    with pytest.raises(ValueError) as exc_info:
        curriculum.continue_after_support_cap(state)

    assert str(exc_info.value) == "capped_support_return_activity_unavailable"
    assert "authored_variant_pool_exhausted" not in str(exc_info.value)


def test_capped_support_rejects_replayed_variant_pool_successor_after_exhausted_pool():
    state = _advance_to_phase(_state(), "review")
    level = state["levels"][0]
    replay_source = _current(state)
    level["teaching_steps"].append(
        {
            "step_id": "step-final-replay-pool",
            "phase": "final_replay",
            "required": True,
            "pool_id": "final-replay-pool",
            "variant_pool": [
                {
                    **_choice_activity("final_replay", ordinal, role="certifying"),
                    "passage": f"  {replay_source['passage'].upper()}\n",
                    "prompt": f"\t{replay_source['prompt'].upper()}  ",
                }
                for ordinal in range(1, 3)
            ],
        }
    )
    state, return_step = _capped_state_with_exhausted_return_step(state)

    assert return_step["phase"] == "review"
    assert curriculum._content_fingerprint(replay_source["passage"]) in state[
        "hot_session_memory"
    ]["passage_fingerprints"]
    assert curriculum._content_fingerprint(replay_source["prompt"]) in state[
        "hot_session_memory"
    ]["prompt_fingerprints"]
    with pytest.raises(ValueError) as exc_info:
        curriculum.continue_after_support_cap(state)

    assert str(exc_info.value) == "capped_support_return_activity_unavailable"


def test_continue_after_support_cap_rejects_non_capped_state():
    with pytest.raises(ValueError, match="curriculum_not_capped_for_support"):
        curriculum.continue_after_support_cap(_state())


def test_feedback_and_bounded_hot_memory_do_not_store_raw_answer():
    state = _advance_to_phase(_state(), "independent_application")
    raw_answer = "private-child-response-" * 20
    state["hot_session_memory"]["recent_outcomes"] = [
        {
            "activity_id": f"old-{index}",
            "outcome": "correct",
            "correct": True,
            "scored": True,
            "skill_ids": [SKILL_ID],
        }
        for index in range(12)
    ]
    state, _ = _answer(state, raw_answer)

    feedback = state["feedback_v2"]
    assert set(feedback) == {
        "outcome",
        "feedback_type",
        "correct",
        "scored",
        "what_worked",
        "criterion_gap",
        "misconception_tag",
        "next_support",
        "retry_policy",
        "allowed_next_actions",
        "response_excerpt",
    }
    assert len(state["hot_session_memory"]["recent_outcomes"]) <= 8
    assert state["hot_session_memory"]["last_activity_id"]
    assert state["hot_session_memory"]["active_support_count"] > 0
    assert raw_answer not in repr(state["hot_session_memory"])
    assert raw_answer not in repr(state)
    assert "answer" not in state["levels"][0]["attempts"][-1]
    assert state["levels"][0]["attempts"][-1]["response_excerpt"] == ""
    assert feedback["response_excerpt"] == ""

    public = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": state["status"], "state_json": state}
    )
    assert raw_answer not in repr(public["session_memory"])
    assert raw_answer not in repr(public)
    assert public["feedback_v2"]["response_excerpt"] == ""


def test_targeted_variant_misconception_tags_are_validated_and_serialized():
    activity = LiveChapterActivity.model_validate(
        _choice_activity("guided_practice", 1, role="formative")
    )

    assert activity.target_misconception_tags == ["missed_detail"]
    assert activity.relevance_terms == ["supported detail", "clue"]
    assert activity.runtime_dict()["target_misconception_tags"] == ["missed_detail"]
    assert activity.runtime_dict()["relevance_terms"] == [
        "supported detail",
        "clue",
    ]


def test_runtime_credits_only_the_skills_assessed_by_the_authored_activity():
    state = _advance_to_phase(_state(), "independent_application")
    level = state["levels"][0]
    level["skill_ids"] = [SKILL_ID, "vocab.antonyms"]
    first_variant = level["teaching_steps"][6]["variant_pool"][0]
    first_variant["knowledge_components"] = [SKILL_ID]
    state["hot_session_memory"]["skill_streaks"] = {}

    activity = _current(state)

    assert activity["assessed_skill_ids"] == [SKILL_ID]
    assert activity["skill_ids"] == [SKILL_ID]
    assert activity["knowledge_components"] == [SKILL_ID]

    state, evaluation = _answer_correctly(state)

    assert evaluation["skill_ids"] == [SKILL_ID]
    assert state["levels"][0]["attempts"][-1]["skill_ids"] == [SKILL_ID]
    assert state["hot_session_memory"]["skill_streaks"] == {SKILL_ID: 1}
    assert "vocab.antonyms" not in state["hot_session_memory"]["skill_streaks"]


def test_real_chapter_spelling_activity_never_credits_antonym_mastery():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_spelling_and_opposites"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "independent_application"
    )
    level["current_step"] = "independent_application"
    state["current_level_index"] = level_index
    state["hot_session_memory"]["skill_streaks"] = {}

    activity = _current(state)

    assert activity["variant"]["variant_id"].endswith(
        "spelling_and_opposites:independent_application:v1"
    )
    assert activity["skill_ids"] == ["vocab.spelling"]
    assert activity["assessed_skill_ids"] == ["vocab.spelling"]

    state, evaluation = _answer_correctly(state)

    assert evaluation["skill_ids"] == ["vocab.spelling"]
    assert state["hot_session_memory"]["skill_streaks"] == {
        "vocab.spelling": 1
    }
    assert "vocab.antonyms" not in state["hot_session_memory"]["skill_streaks"]


def test_real_peered_misconception_routes_to_tagged_semantic_support():
    """Mirror the browser path from a wrong transfer response into support."""

    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_chapter_words"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "transfer"
    )
    level["current_step"] = "transfer"
    state["current_level_index"] = level_index

    activity = _current(state)
    answer = "Peered means running quickly before using a torch."
    assert activity["variant"]["variant_id"].endswith(":transfer:v1")
    assert "peered" in activity["prompt"].casefold()

    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": "running quickly",
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": ["context_ignored"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Use the sentence context to infer the word.",
        }
    )

    state, result = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=evaluation,
    )
    support = _current(state)

    assert result["correct"] is False
    assert state["levels"][level_index]["v2_active_misconception_tags"] == [
        "context_ignored"
    ]
    assert support["support_mode"] == "bridge"
    assert "context_ignored" in support["target_misconception_tags"]
    assert "peered" in " ".join(
        [support["teaching_block"], support["passage"], support["prompt"]]
    ).casefold()
    assert "pair of socks" not in support["passage"].casefold()
    assert "incomplete_phrase" not in support["target_misconception_tags"]


def test_normalized_legacy_forced_bridge_retargets_peered_support():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_chapter_words"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "transfer"
    )
    level["current_step"] = "transfer"
    state["current_level_index"] = level_index
    trigger = _current(state)
    level["attempts"] = [
        {
            "activity_id": trigger["activity_id"],
            "kind": trigger["kind"],
            "phase": trigger["phase"],
            "attempt_no": 1,
            "correct": False,
            "scored": True,
            "score": 0.0,
            "confidence": 1.0,
            "variant_id": trigger["variant"]["variant_id"],
        }
    ]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = ["context_ignored"]
    level["v2_forced_support_kind"] = "bridge"

    normalized = curriculum.normalize_curriculum_state(state)
    repaired_level = normalized["levels"][level_index]
    support = _current(normalized)

    assert repaired_level.get("v2_forced_support_kind") is None
    assert repaired_level["v2_trigger_relevance_terms"] == [
        "peered",
        "looked closely",
        "torch",
    ]
    assert repaired_level["v2_step_index"] == level["v2_step_index"]
    assert len(repaired_level["attempts"]) == 1
    assert support["variant"]["variant_id"] == "revision_level_3"
    assert "context_ignored" in support["target_misconception_tags"]
    assert "peered" in support["passage"].casefold()
    assert "pair of socks" not in support["passage"].casefold()


def test_continue_activity_carries_no_assessed_skill_or_streak_evidence():
    state = _state()
    activity = _current(state)

    assert activity["interaction_type"] == "continue"
    assert activity["knowledge_components"] == [SKILL_ID]
    assert activity["assessed_skill_ids"] == []
    assert activity["skill_ids"] == []

    state, evaluation = _answer_correctly(state)

    assert evaluation["scored"] is False
    assert evaluation["skill_ids"] == []
    assert state["hot_session_memory"]["skill_streaks"] == {}


def test_experience_choice_is_checked_but_never_creates_skill_evidence():
    state = _advance_to_phase(_state(), "guided_practice")
    guided_step = state["levels"][0]["teaching_steps"][4]
    for variant in guided_step["variant_pool"]:
        variant["evidence_role"] = "experience"

    activity = _current(state)
    assert activity["interaction_type"] == "single_choice"
    assert activity["evidence_role"] == "experience"
    assert activity["assessed_skill_ids"] == []

    state, evaluation = _answer(state, activity["options"][1])

    assert evaluation["correct"] is False
    assert evaluation["scored"] is True
    assert evaluation["skill_ids"] == []
    assert state["hot_session_memory"]["skill_streaks"] == {}
    assert state["last_feedback"]["correct"] is False
    retry = _current(state)
    assert retry["phase"] == "guided_practice"
    assert retry["variant"]["variant_id"] != activity["variant"]["variant_id"]


def test_support_selection_targets_the_failed_misconception_before_pool_order():
    state = _advance_to_phase(_state(), "independent_application")
    level = state["levels"][0]
    level["skill_ids"] = [SKILL_ID, "grammar.tense_usage"]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_skill_ids"] = [SKILL_ID, "grammar.tense_usage"]
    level["v2_active_misconception_tags"] = ["tense_shift"]
    level["checks"]["bridge"]["target_misconception_tags"] = ["missed_detail"]
    level["checks"]["revision_level_1"]["target_misconception_tags"] = [
        "tense_shift"
    ]
    level["checks"]["revision_level_1"]["knowledge_components"] = [
        "grammar.tense_usage"
    ]
    level["checks"]["revision_level_2"]["target_misconception_tags"] = [
        "tense_shift"
    ]
    level["checks"]["revision_level_3"]["target_misconception_tags"] = [
        "sequence_lost"
    ]

    targeted = _current(state)

    assert targeted["variant"]["variant_id"] == "revision_level_1"
    assert targeted["skill_ids"] == ["grammar.tense_usage"]
    assert targeted["assessed_skill_ids"] == ["grammar.tense_usage"]

    sequence_state = deepcopy(state)
    sequence_state["levels"][0]["v2_active_misconception_tags"] = [
        "sequence_lost",
        "criterion:poem_to_story_target",
    ]
    sequence_repair = _current(sequence_state)
    assert sequence_repair["variant"]["variant_id"] == "revision_level_3"

    level["attempts"].append(
        {
            "kind": "v2_support",
            "variant_id": "revision_level_1",
            "activity_id": targeted["activity_id"],
        }
    )
    next_targeted = _current(state)

    assert next_targeted["variant"]["variant_id"] == "revision_level_2"
    assert next_targeted["activity_id"] != targeted["activity_id"]


def test_active_misconception_without_fresh_tagged_support_fails_closed():
    state = _advance_to_phase(_state(), "independent_application")
    level = state["levels"][0]
    step = level["teaching_steps"][level["v2_step_index"]]
    for variant in step["variant_pool"]:
        variant["target_misconception_tags"] = ["missed_detail", "context_ignored"]
        variant["wrong_answer_misconception_tags"] = {
            variant["options"][1]: ["context_ignored"]
        }

    state, evaluation = _wrong_current_answer(state)

    assert evaluation["misconception_tags"] == ["context_ignored"]
    assert state["status"] == "active"
    assert state["phase"] == "needs_support"
    assert state["support_required"]["reason"] == (
        "authored_targeted_support_unavailable"
    )
    assert curriculum._current_activity(state) is None


def test_wrong_options_route_to_distinct_authored_remediation_targets():
    def support_for(wrong_answer: str) -> dict:
        state = _advance_to_phase(_state(), "guided_practice")
        level = state["levels"][0]
        guided_step = next(
            step
            for step in level["teaching_steps"]
            if step["phase"] == "guided_practice"
        )
        for variant in guided_step["variant_pool"]:
            variant["options"] = [
                variant["accepted_answers"][0],
                "ignored the stated clue",
                "replaced the main idea with a detail",
            ]
            variant["target_misconception_tags"] = [
                "missed_detail",
                "main_idea_replaced_by_detail",
            ]
            variant["wrong_answer_misconception_tags"] = {
                "ignored the stated clue": ["missed_detail"],
                "replaced the main idea with a detail": [
                    "main_idea_replaced_by_detail"
                ],
            }
        level["checks"]["bridge"]["target_misconception_tags"] = [
            "missed_detail"
        ]
        level["checks"]["revision_level_3"][
            "target_misconception_tags"
        ] = ["main_idea_replaced_by_detail"]

        for _ in range(1):
            state, evaluation = _answer(state, wrong_answer)
            assert evaluation["misconception_tags"] == [
                (
                    "missed_detail"
                    if wrong_answer == "ignored the stated clue"
                    else "main_idea_replaced_by_detail"
                )
            ]

        support = _current(state)
        assert support["kind"] == "v2_support"
        return support

    clue_support = support_for("ignored the stated clue")
    main_idea_support = support_for("replaced the main idea with a detail")

    assert clue_support["variant"]["variant_id"] == "bridge"
    assert main_idea_support["variant"]["variant_id"] == "revision_level_3"
    assert clue_support["activity_id"] != main_idea_support["activity_id"]


def test_wrong_answer_misconception_mapping_is_closed_to_authored_options_and_tags():
    activity = _choice_activity("guided_practice", 1, role="formative")
    wrong_answer = activity["options"][1]
    activity["wrong_answer_misconception_tags"] = {
        wrong_answer: ["missed_detail"]
    }

    validated = LiveChapterActivity.model_validate(activity)
    assert validated.wrong_answer_misconception_tags == {
        wrong_answer: ["missed_detail"]
    }

    unknown_option = deepcopy(activity)
    unknown_option["wrong_answer_misconception_tags"] = {
        "answer that is not an option": ["missed_detail"]
    }
    with pytest.raises(ValueError, match="wrong_answer_mapping_key_not_authored"):
        LiveChapterActivity.model_validate(unknown_option)

    unknown_tag = deepcopy(activity)
    unknown_tag["wrong_answer_misconception_tags"] = {
        wrong_answer: ["model_invented_tag"]
    }
    with pytest.raises(ValueError, match="wrong_answer_mapping_tag_not_authored"):
        LiveChapterActivity.model_validate(unknown_tag)


def test_failed_open_criterion_maps_to_authored_remediation_and_drops_unknown_tags():
    chapter = json.loads(
        (
            Path(__file__).parents[2]
            / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
        ).read_text()
    )
    level = chapter["levels"][0]
    independent_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "independent_application"
    )
    activity = deepcopy(independent_step["variant_pool"][0])
    criterion_id = activity["rubric_criteria"][0]["id"]
    activity["criterion_misconception_tags"] = {
        criterion_id: ["unsupported_inference"]
    }

    validated = LiveChapterActivity.model_validate(activity)
    assert validated.criterion_misconception_tags == {
        criterion_id: ["unsupported_inference"]
    }
    assert curriculum._bounded_remediation_tags(
        activity,
        {
            "misconception_tags": ["model_invented_tag"],
            "missing_criteria": [criterion_id],
        },
        correct=False,
    ) == ["unsupported_inference"]

    activity["criterion_misconception_tags"] = {
        "criterion_not_in_the_rubric": ["unsupported_inference"]
    }
    with pytest.raises(ValueError, match="criterion_mapping_key_not_authored"):
        LiveChapterActivity.model_validate(activity)


def test_deterministic_failure_carries_authored_misconception_to_support():
    state = _advance_to_phase(_state(), "independent_application")
    activity = _current(state)
    assert activity["target_misconception_tags"] == ["missed_detail"]

    state, evaluation = _wrong_current_answer(state)

    assert evaluation["correct"] is False
    assert state["levels"][0]["v2_active_misconception_tags"] == [
        "missed_detail",
    ]
    assert "missed_detail" in evaluation["misconception_tags"]
    assert "missed_detail" in state["hot_session_memory"][
        "unresolved_misconception_tags"
    ]


def test_support_never_inherits_trigger_skill_when_authored_check_tests_another_skill():
    state = _advance_to_phase(_state(), "independent_application")
    level = state["levels"][0]
    level["skill_ids"] = [SKILL_ID, "grammar.prepositions"]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_skill_ids"] = [SKILL_ID]
    for check in level["checks"].values():
        check["knowledge_components"] = ["grammar.prepositions"]

    with pytest.raises(ValueError, match="authored_support_not_available_for_trigger"):
        curriculum._current_activity(state)


def test_real_antonym_failure_selects_antonym_repair_and_credits_only_antonym():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_spelling_and_opposites"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "independent_application"
    )
    level["current_step"] = "independent_application"
    level["used_variant_ids"] = [
        "papas_spectacles_spelling_and_opposites:independent_application:v1",
        "papas_spectacles_spelling_and_opposites:independent_application:v2",
    ]
    state["current_level_index"] = level_index
    state["hot_session_memory"]["skill_streaks"] = {}

    failed_activity = _current(state)
    assert failed_activity["assessed_skill_ids"] == ["vocab.antonyms"]
    state, _ = _answer(state, "narrow")

    assert "related_not_opposite" in state["levels"][level_index][
        "v2_active_misconception_tags"
    ]
    support = _current(state)
    assert support["variant"]["variant_id"] == "revision_level_1"
    assert support["assessed_skill_ids"] == ["vocab.antonyms"]
    assert "opposite" in (
        support["teaching_block"] + " " + support["prompt"]
    ).casefold()

    state, evaluation = _answer_correctly(state)

    assert evaluation["skill_ids"] == ["vocab.antonyms"]
    assert state["hot_session_memory"]["skill_streaks"] == {
        "vocab.antonyms": 1
    }


def test_sound_logistics_choice_credits_its_authored_spelling_and_context_skills():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_sound_lab"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "guided_practice"
    )
    level["current_step"] = "guided_practice"
    level["used_variant_ids"] = [
        "papas_spectacles_sound_lab:guided:v1",
        "papas_spectacles_sound_lab:guided:v2",
        "papas_spectacles_sound_lab:guided:v3",
    ]
    state["current_level_index"] = level_index
    state["hot_session_memory"]["skill_streaks"] = {}

    activity = _current(state)
    assert activity["variant"]["variant_id"].endswith("guided:v4")
    assert activity["assessed_skill_ids"] == [
        "vocab.spelling",
        "reading.word_meaning_context",
    ]
    assert activity["skill_ids"] == activity["assessed_skill_ids"]

    state, evaluation = _answer_correctly(state)

    assert evaluation["correct"] is True
    assert evaluation["scored"] is True
    assert evaluation["skill_ids"] == activity["assessed_skill_ids"]
    assert state["hot_session_memory"]["skill_streaks"] == {
        "vocab.spelling": 1,
        "reading.word_meaning_context": 1,
    }


def test_wrong_sound_logistics_choice_opens_authored_skill_remediation():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_sound_lab"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "guided_practice"
    )
    level["current_step"] = "guided_practice"
    level["used_variant_ids"] = [
        "papas_spectacles_sound_lab:guided:v1",
        "papas_spectacles_sound_lab:guided:v2",
        "papas_spectacles_sound_lab:guided:v3",
    ]
    state["current_level_index"] = level_index

    state, evaluation = _answer(state, "coat and goat differ at the start")

    assert evaluation["correct"] is False
    assert evaluation["scored"] is True
    assert evaluation["skill_ids"] == [
        "vocab.spelling",
        "reading.word_meaning_context",
    ]
    assert state["levels"][level_index]["v2_support_mode"] == "bridge"
    assert _current(state)["support_mode"] == "bridge"


def test_failed_chapter_check_starts_real_v2_remediation_and_returns_to_assessment():
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    for level in state["levels"]:
        level["status"] = "complete"
        level["v2_step_index"] = len(level["teaching_steps"])
        level["current_step"] = "complete"

    state = curriculum._start_assessment_remediation(
        state,
        ["vocab.spelling"],
        mode="focused_revision",
    )
    activity = _current(state)

    assert state["phase"] == "remediation"
    assert activity["support_mode"] == "bridge"
    assert activity["assessed_skill_ids"] == ["vocab.spelling"]

    state, evaluation = _answer_correctly(state)

    assert evaluation["skill_ids"] == ["vocab.spelling"]
    assert state["phase"] == "chapter_check"
    assert _current(state)["kind"] == "chapter_check"


def test_loaded_authored_chapters_start_and_advance_under_anti_replay_guard():
    for class_no in (2, 3, 4, 5):
        chapters = curriculum._available_chapters("english", class_no)
        for chapter_index, chapter in enumerate(chapters):
            state = curriculum.new_curriculum_state(
                school_profile={
                    "profile_version_id": f"profile-class-{class_no}",
                    "target_class_no": class_no,
                    "subject_ids": ["english"],
                    "preferred_teaching_language": "en",
                },
                placement_report={
                    "report_id": f"placement-class-{class_no}",
                    "unlock_state": "target_unlocked",
                },
                recap_session=None,
                latest_curriculum_session={
                    "state_json": {
                        "subject_id": "english",
                        "target_class_no": class_no,
                        "completed_chapter_ids": [
                            item["chapter_id"] for item in chapters[:chapter_index]
                        ]
                    }
                },
                requested_chapter_id=chapter["chapter_id"],
            )

            first = _current(state)
            state, _ = _answer_correctly(state)
            second = _current(state)

            assert state["chapter"]["chapter_id"] == chapter["chapter_id"]
            assert first["phase"] == "connect"
            assert first["passage"] and first["prompt"]
            assert second["activity_id"] != first["activity_id"]


def _chapter_words_review_state() -> tuple[dict, int]:
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "profile-1",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "report-1",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
    )
    level_index = next(
        index
        for index, level in enumerate(state["levels"])
        if level["level_id"] == "papas_spectacles_chapter_words"
    )
    for level in state["levels"]:
        level["status"] = "not_started"
    level = state["levels"][level_index]
    level["status"] = "in_progress"
    level["v2_step_index"] = next(
        index
        for index, step in enumerate(level["teaching_steps"])
        if step["phase"] == "review"
    )
    level["current_step"] = "review"
    state["current_level_index"] = level_index
    return state, level_index


def test_new_curriculum_state_isolates_authored_level_content():
    state, level_index = _chapter_words_review_state()
    session_level = state["levels"][level_index]
    authored_level = next(
        level
        for level in curriculum.CLASS_5_CURRICULUM_CHAPTERS[0]["levels"]
        if level["level_id"] == "papas_spectacles_chapter_words"
    )

    session_level["checks"].pop("revision_level_4")
    review_step = next(
        step for step in session_level["teaching_steps"] if step["phase"] == "review"
    )
    review_step["variant_pool"][0].pop("criterion_misconception_tags")

    assert "revision_level_4" in authored_level["checks"]
    assert all(
        variant["criterion_misconception_tags"]
        for variant in next(
            step
            for step in authored_level["teaching_steps"]
            if step["phase"] == "review"
        )["variant_pool"]
    )


def _failed_review_evaluation(activity: dict) -> SchoolRubricEvaluation:
    return SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": "stared at it for a long time",
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Use the sentence context to contrast the two looks.",
        }
    )


def test_revision_level_4_is_optional_and_is_included_in_runtime_checks():
    chapter = json.loads(
        (
            Path(__file__).parents[2]
            / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
        ).read_text()
    )
    legacy_checks = deepcopy(chapter["levels"][0]["checks"])
    assert "revision_level_4" not in LiveChapterChecks.model_validate(
        legacy_checks
    ).runtime_dict()

    checks = deepcopy(legacy_checks)
    checks["revision_level_4"] = {
        **deepcopy(checks["revision_level_3"]),
        "teaching_block": "Use a fourth fresh support clue.",
        "passage": "A fourth original support passage avoids every earlier clue.",
        "prompt": "Choose the fourth supported detail.",
    }

    runtime_checks = LiveChapterChecks.model_validate(checks).runtime_dict()

    assert runtime_checks["revision_level_4"]["prompt"] == (
        "Choose the fourth supported detail."
    )


def test_review_v1_missing_glanced_context_uses_source_semantic_support_without_model_tags():
    state, level_index = _chapter_words_review_state()
    activity = _current(state)

    assert activity["variant"]["variant_id"].endswith(":review:v1")
    assert "glanced" in activity["prompt"].casefold()

    state, result = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer="The nurse glanced at the chart and stared at it for a long time.",
        open_answer_evaluation=_failed_review_evaluation(activity),
    )
    support = _current(state)
    public_activity = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": state["status"], "state_json": state}
    )["current_activity"]

    assert result["correct"] is False
    assert state["levels"][level_index]["v2_active_misconception_tags"] == [
        "context_ignored"
    ]
    assert support["variant"]["variant_id"] == "revision_level_4"
    assert "glanced" in " ".join(
        [support["teaching_block"], support["passage"], support["prompt"]]
    ).casefold()
    assert "pair of socks" not in support["passage"].casefold()
    assert public_activity is not None
    assert not {
        "answer_key",
        "accepted_answers",
        "model_answer",
        "criterion_misconception_tags",
        "rubric_criteria",
    }.intersection(public_activity)


def test_legacy_empty_tag_glanced_support_uses_stored_trigger_terms():
    state, level_index = _chapter_words_review_state()
    trigger = _current(state)
    level = state["levels"][level_index]
    level["attempts"] = [
        {
            "activity_id": trigger["activity_id"],
            "kind": trigger["kind"],
            "phase": trigger["phase"],
            "attempt_no": 1,
            "correct": False,
            "scored": True,
            "score": 0.0,
            "confidence": 1.0,
            "variant_id": trigger["variant"]["variant_id"],
        }
    ]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = []
    level["v2_trigger_relevance_terms"] = ["glanced", "quick look", "stared"]

    support = _current(curriculum.normalize_curriculum_state(state))

    assert support["variant"]["variant_id"] == "revision_level_4"
    assert "glanced" in support["passage"].casefold()
    assert "pair of socks" not in support["passage"].casefold()


def test_legacy_empty_tag_glanced_support_without_fresh_semantic_source_pauses_safely():
    state, level_index = _chapter_words_review_state()
    trigger = _current(state)
    level = state["levels"][level_index]
    level["attempts"] = [
        {
            "activity_id": trigger["activity_id"],
            "kind": trigger["kind"],
            "phase": trigger["phase"],
            "attempt_no": 1,
            "correct": False,
            "scored": True,
            "score": 0.0,
            "confidence": 1.0,
            "variant_id": trigger["variant"]["variant_id"],
        },
        {
            "activity_id": "prior-semantic-support",
            "kind": "v2_support",
            "variant_id": "revision_level_4",
        },
    ]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = []
    level["v2_trigger_relevance_terms"] = ["glanced", "quick look", "stared"]

    normalized = curriculum.normalize_curriculum_state(state)
    public = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": state}
    )

    assert normalized["status"] == "active"
    assert normalized["phase"] == "needs_support"
    assert normalized["support_required"]["reason"] == (
        "authored_source_semantic_support_unavailable"
    )
    assert curriculum._current_activity(normalized) is None
    assert public["current_activity"] is None
    assert public["next_action"]["action"] == "view_support_plan"
    assert "socks" not in json.dumps(public).casefold()


def test_legacy_empty_tag_support_pool_exhaustion_pauses_safely():
    state, level_index = _chapter_words_review_state()
    trigger = _current(state)
    level = state["levels"][level_index]
    level["attempts"] = [
        {
            "activity_id": trigger["activity_id"],
            "kind": trigger["kind"],
            "phase": trigger["phase"],
            "attempt_no": 1,
            "correct": False,
            "scored": True,
            "score": 0.0,
            "confidence": 1.0,
            "variant_id": trigger["variant"]["variant_id"],
        },
        *[
            {
                "activity_id": f"prior-support:{variant_id}",
                "kind": "v2_support",
                "variant_id": variant_id,
            }
            for variant_id in (
                "bridge",
                "revision_level_1",
                "revision_level_2",
                "revision_level_3",
                "revision_level_4",
            )
        ],
    ]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = []
    level["v2_trigger_relevance_terms"] = ["glanced", "quick look", "stared"]

    normalized = curriculum.normalize_curriculum_state(state)

    assert normalized["status"] == "active"
    assert normalized["phase"] == "needs_support"
    assert normalized["support_required"]["reason"] == "authored_support_pool_exhausted"
    assert curriculum._current_activity(normalized) is None


def test_tagged_support_pool_exhaustion_pauses_public_read_safely():
    state, level_index = _chapter_words_review_state()
    trigger = _current(state)
    level = state["levels"][level_index]
    level["attempts"] = [
        {
            "activity_id": trigger["activity_id"],
            "kind": trigger["kind"],
            "phase": trigger["phase"],
            "attempt_no": 1,
            "correct": False,
            "scored": True,
            "score": 0.0,
            "confidence": 1.0,
            "variant_id": trigger["variant"]["variant_id"],
        },
        *[
            {
                "activity_id": f"spent-{variant_id}",
                "kind": "v2_support",
                "variant_id": variant_id,
            }
            for variant_id in (
                "bridge",
                "revision_level_1",
                "revision_level_2",
                "revision_level_3",
                "revision_level_4",
            )
        ],
    ]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = ["context_ignored"]

    normalized = curriculum.normalize_curriculum_state(state)
    public = curriculum.public_curriculum_response(
        {"session_id": "session-1", "status": "active", "state_json": normalized}
    )

    assert normalized["status"] == "active"
    assert normalized["phase"] == "needs_support"
    assert normalized["support_required"]["reason"] == "authored_support_pool_exhausted"
    assert public["current_activity"] is None
    assert public["next_action"]["action"] == "view_support_plan"


def test_v5_reconciliation_backfills_source_support_for_existing_snapshot():
    state, level_index = _chapter_words_review_state()
    level = state["levels"][level_index]
    review_step = next(
        step for step in level["teaching_steps"] if step["phase"] == "review"
    )
    for variant in review_step["variant_pool"]:
        variant.pop("criterion_misconception_tags", None)
    level["checks"].pop("revision_level_4")
    trigger = _current(state)
    level["attempts"] = [
        {
            "activity_id": trigger["activity_id"],
            "kind": trigger["kind"],
            "phase": trigger["phase"],
            "attempt_no": 1,
            "correct": False,
            "scored": True,
            "score": 0.0,
            "confidence": 1.0,
            "variant_id": trigger["variant"]["variant_id"],
        },
        {
            "activity_id": "prior-peered-support",
            "kind": "v2_support",
            "variant_id": "revision_level_3",
        },
    ]
    level["v2_support_mode"] = "bridge"
    level["v2_trigger_activity_id"] = trigger["activity_id"]
    level["v2_return_activity_id"] = trigger["activity_id"]
    level["v2_trigger_skill_ids"] = trigger["assessed_skill_ids"]
    level["v2_active_misconception_tags"] = []
    level["v2_trigger_relevance_terms"] = ["glanced", "quick look", "stared"]
    state["engine_version"] = "school-rebuild-curriculum-5"

    reconciled, repair = curriculum.reconcile_curriculum_state(state)
    support = _current(reconciled)

    assert repair is None
    assert reconciled["engine_version"] == curriculum.ENGINE_VERSION
    assert "revision_level_4" in reconciled["levels"][level_index]["checks"]
    assert all(
        variant["criterion_misconception_tags"]
        for variant in next(
            step
            for step in reconciled["levels"][level_index]["teaching_steps"]
            if step["phase"] == "review"
        )["variant_pool"]
    )
    assert support["variant"]["variant_id"] == "revision_level_4"
    assert curriculum.current_curriculum_activity_id(state) == support["activity_id"]


def test_v5_reconciliation_does_not_overwrite_existing_empty_tag_mapping():
    state, level_index = _chapter_words_review_state()
    review_step = next(
        step
        for step in state["levels"][level_index]["teaching_steps"]
        if step["phase"] == "review"
    )
    review_step["variant_pool"][0]["criterion_misconception_tags"] = {}
    state["engine_version"] = "school-rebuild-curriculum-5"

    reconciled, _repair = curriculum.reconcile_curriculum_state(state)
    reconciled_review = next(
        step
        for step in reconciled["levels"][level_index]["teaching_steps"]
        if step["phase"] == "review"
    )

    assert reconciled_review["variant_pool"][0]["criterion_misconception_tags"] == {}


def test_generic_clear_relevant_english_cannot_map_to_semantic_misconception():
    state, level_index = _chapter_words_review_state()
    review_step = next(
        step
        for step in state["levels"][level_index]["teaching_steps"]
        if step["phase"] == "review"
    )
    activity = deepcopy(review_step["variant_pool"][0])

    assert "clear_relevant_english" not in activity[
        "criterion_misconception_tags"
    ]
    activity["criterion_misconception_tags"] = {
        "clear_relevant_english": ["context_ignored"]
    }

    with pytest.raises(
        ValueError,
        match="generic_criterion_cannot_map_to_semantic_misconception",
    ):
        LiveChapterActivity.model_validate(activity)
