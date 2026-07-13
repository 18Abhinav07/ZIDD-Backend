import copy
import json

import pytest

from app.services import school_rebuild_curriculum as curriculum


def _assessment_item(index: int, skill_id: str) -> dict:
    return {
        "item_id": f"frog_chapter_check_{index:02d}",
        "passage": f"Original frog check passage {index}.",
        "prompt": f"Choose the correct response for check {index}.",
        "skill_ids": [skill_id],
        "options": ["correct", "incorrect"],
        "accepted_answers": ["correct"],
    }


def _correct_answer(activity: dict) -> str:
    accepted = list(activity.get("accepted_answers") or [])
    if accepted:
        return accepted[0]
    if activity.get("answer_rule") == "concept_slots":
        phrases = [
            str((slot.get("any_of") or [slot.get("description") or "detail"])[0])
            for slot in activity.get("concept_slots") or []
        ]
        answer = ". ".join(phrases)
        minimum = int(activity.get("min_response_words") or 0)
        while len(answer.split()) < minimum:
            answer += " This explains the required passage detail clearly."
        return answer
    answers_by_rule = {
        "wise_parrot_reason": (
            "The forest parrot was wise because it showed a clever escape plan."
        ),
        "past_tense_travel_sentence": "I travelled by bus with my family.",
        "release_opinion_reason": (
            "The trader should release the bird because freedom matters."
        ),
        "bird_feeder_procedure": (
            "First clean the container, add grains and water, place it safely, "
            "and clean it regularly."
        ),
    }
    return answers_by_rule[str(activity.get("answer_rule") or "")]


def _chapter_with_assessment() -> dict:
    chapter = copy.deepcopy(curriculum.CLASS_5_WISE_PARROT_CHAPTER)
    chapter["chapter_id"] = "eng_c5_test_assessment"
    chapter["chapter_no"] = 99
    chapter["content_version"] = "test-assessment-1"
    chapter["levels"] = chapter["levels"][:1]
    chapter["levels"][0]["checks"].pop("transfer_check", None)
    skills = list(chapter["levels"][0]["skill_ids"])
    chapter["chapter_assessment"] = {
        "items_per_attempt": 12,
        "pass_score": 0.8,
        "max_attempts": 2,
        "items": [
            _assessment_item(index, skills[index % len(skills)])
            for index in range(1, 21)
        ],
    }
    return chapter


def _chapter_with_extended_revision() -> dict:
    chapter = _chapter_with_assessment()
    chapter["chapter_assessment"]["max_attempts"] = 3
    skills = list(chapter["levels"][0]["skill_ids"])
    chapter["chapter_assessment"]["items"] = [
        _assessment_item(index, skills[index % len(skills)])
        for index in range(1, 37)
    ]
    checks = chapter["levels"][0]["checks"]
    for revision_no in range(1, 4):
        check = copy.deepcopy(checks["masterclass"])
        check.update(
            {
                "passage": f"Authored revision passage {revision_no}.",
                "prompt": f"Answer authored revision check {revision_no}.",
                "options": ["correct", "incorrect"],
                "accepted_answers": ["correct"],
            }
        )
        checks[f"revision_level_{revision_no}"] = check
    return chapter


def _multi_level_chapter_with_extended_revision() -> dict:
    chapter = copy.deepcopy(curriculum.CLASS_5_WISE_PARROT_CHAPTER)
    chapter["chapter_id"] = "eng_c5_bounded_revision"
    chapter["chapter_no"] = 98
    chapter["content_version"] = "bounded-revision-1"
    chapter["levels"] = chapter["levels"][:3]
    for level_index, level in enumerate(chapter["levels"], start=1):
        level["checks"].pop("transfer_check", None)
        for revision_no in range(1, 4):
            revision = copy.deepcopy(level["checks"]["masterclass"])
            revision.update(
                {
                    "passage": (
                        f"Level {level_index} authored revision passage {revision_no}."
                    ),
                    "prompt": (
                        f"Answer level {level_index} revision {revision_no}."
                    ),
                    "options": ["correct", "incorrect"],
                    "accepted_answers": ["correct"],
                }
            )
            level["checks"][f"revision_level_{revision_no}"] = revision
    skill_ids = list(
        dict.fromkeys(
            skill_id
            for level in chapter["levels"]
            for skill_id in level["skill_ids"]
        )
    )
    chapter["chapter_assessment"] = {
        "items_per_attempt": 12,
        "pass_score": 0.8,
        "max_attempts": 3,
        "items": [
            _assessment_item(index, skill_ids[(index - 1) % len(skill_ids)])
            for index in range(1, 37)
        ],
    }
    return chapter


def _answer_until_phase(state: dict, phase: str, *, limit: int = 20) -> dict:
    for _ in range(limit):
        if state.get("phase") == phase:
            return state
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=_correct_answer(activity),
        )
    raise AssertionError(f"test fixture did not reach {phase}")


def _fail_assessment_form(state: dict) -> dict:
    while state.get("phase") == "chapter_check":
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect",
        )
    return state


def _state_at_final_independent(monkeypatch) -> dict:
    chapter = _chapter_with_assessment()
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"
    return state


def _enter_chapter_check(monkeypatch) -> dict:
    state = _state_at_final_independent(monkeypatch)
    for _ in range(3):
        if state.get("phase") == "chapter_check":
            return state
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=_correct_answer(activity),
        )
    raise AssertionError("test fixture did not reach chapter_check")


def _enter_chapter_check_for(monkeypatch, chapter: dict) -> dict:
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"
    activity = curriculum._current_activity(state)
    assert activity is not None
    updated, _ = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=_correct_answer(activity),
    )
    return updated


def _fail_first_assessment(monkeypatch) -> tuple[dict, str]:
    state = _enter_chapter_check(monkeypatch)
    weak_skill_id = _chapter_with_assessment()["levels"][0]["skill_ids"][0]
    for _ in range(12):
        activity = curriculum._current_activity(state)
        assert activity is not None
        answer = "incorrect" if weak_skill_id in activity["skill_ids"] else "correct"
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=answer,
        )
    return state, weak_skill_id


def test_final_independent_pass_enters_chapter_check_without_unlocking(monkeypatch):
    state = _state_at_final_independent(monkeypatch)
    activity = curriculum._current_activity(state)
    assert activity is not None
    answer = _correct_answer(activity)

    updated, _ = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
    )

    assert updated["status"] == "active"
    assert updated["phase"] == "chapter_check"
    assert updated["completed_chapter_ids"] == []
    chapter_check = curriculum._current_activity(updated)
    assert chapter_check is not None
    assert chapter_check["kind"] == "chapter_check"


def test_public_chapter_check_exposes_progress_but_no_hidden_grading_fields(monkeypatch):
    updated = _enter_chapter_check(monkeypatch)
    updated["preferred_teaching_language"] = "hi_en"
    updated["chapter"]["chapter_assessment"] = {
        "items": [{"accepted_answers": ["must never leak"]}]
    }

    public = curriculum.public_curriculum_response(
        {
            "session_id": "curriculum-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": updated,
        }
    )

    assert public["phase"] == "chapter_check"
    assert public["chapter_assessment"] == {
        "status": "in_progress",
        "attempt_no": 1,
        "item_number": 1,
        "total_items": 12,
        "last_result": None,
    }
    assert public["current_activity"]["teaching_block"] == (
        "Work independently. Answer in English. "
        "Zidd will share the result after the chapter check."
    )
    assert "chapter_assessment" not in public["chapter"]
    serialized = json.dumps(public)
    for forbidden in (
        "accepted_answers",
        "answer_rule",
        "rubric_criteria",
        "pass_score",
        "preflight_rule",
    ):
        assert forbidden not in serialized


def test_public_completed_check_exposes_only_the_safe_result_summary(monkeypatch):
    state = _enter_chapter_check(monkeypatch)
    state["phase"] = "remediation"
    state["chapter_assessment"]["attempt_history"] = [
        {
            "attempt_no": 1,
            "score": 0.72,
            "passed": False,
            "skill_scores": {"reading.inference_reason": 0.5},
            "weak_skill_ids": ["reading.inference_reason"],
            "remediation_skill_ids": ["reading.inference_reason"],
            "failed_rubric_item_ids": ["hidden-item-id"],
            "failed_hard_blocker_item_ids": ["hidden-blocked-item-id"],
        }
    ]

    public = curriculum.public_curriculum_response(
        {
            "session_id": "curriculum-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        }
    )

    assert public["chapter_assessment"]["last_result"] == {
        "attempt_no": 1,
        "score": 0.72,
        "passed": False,
    }
    serialized = json.dumps(public)
    for forbidden in (
        "skill_scores",
        "weak_skill_ids",
        "remediation_skill_ids",
        "failed_rubric_item_ids",
        "failed_hard_blocker_item_ids",
        "hidden-item-id",
        "hidden-blocked-item-id",
    ):
        assert forbidden not in serialized


def test_level_activity_keeps_hidden_concept_grading_only_on_backend(monkeypatch):
    chapter = _chapter_with_assessment()
    independent = chapter["levels"][0]["checks"]["independent_check"]
    independent.update(
        {
            "options": [],
            "accepted_answers": [],
            "answer_rule": "concept_slots",
            "concept_slots": [
                {
                    "id": "land_evidence",
                    "description": "Names movement across land.",
                    "any_of": ["hopped on moss"],
                },
                {
                    "id": "water_evidence",
                    "description": "Names movement into water.",
                    "any_of": ["hid in the ditch"],
                },
            ],
            "forbidden_phrases": ["does not use water"],
            "min_response_words": 10,
            "ordered_concept_slot_ids": [
                "land_evidence",
                "water_evidence",
            ],
        }
    )
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"

    activity = curriculum._current_activity(state)
    assert activity is not None
    assert activity["concept_slots"] == independent["concept_slots"]
    assert activity["forbidden_phrases"] == ["does not use water"]
    assert activity["min_response_words"] == 10
    assert activity["ordered_concept_slot_ids"] == [
        "land_evidence",
        "water_evidence",
    ]

    public = curriculum._public_activity(activity)
    serialized = json.dumps(public)
    for forbidden in (
        "concept_slots",
        "forbidden_phrases",
        "min_response_words",
        "ordered_concept_slot_ids",
    ):
        assert forbidden not in serialized

    _, evaluation = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer="It hopped on moss and later hid in the ditch filled with water.",
    )
    assert evaluation["correct"] is True


def test_passing_chapter_check_is_the_only_event_that_completes_chapter(monkeypatch):
    state = _enter_chapter_check(monkeypatch)

    for item_number in range(1, 13):
        activity = curriculum._current_activity(state)
        assert activity is not None
        assert activity["kind"] == "chapter_check"
        state, evaluation = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="correct",
        )
        assert evaluation["kind"] == "chapter_check"
        if item_number < 12:
            assert state["status"] == "active"
            assert state["completed_chapter_ids"] == []
            assert state["last_feedback"] == {
                "activity_id": activity["activity_id"],
                "level_id": "chapter_assessment",
                "kind": "chapter_check",
                "correct": None,
                "result_visible": False,
                "message": "Answer saved. Keep going; results appear after the chapter check.",
            }

    assert state["status"] == "complete"
    assert state["phase"] == "complete"
    assert state["completed_chapter_ids"] == ["eng_c5_test_assessment"]
    result = state["chapter_assessment"]["attempt_history"][-1]
    assert result["passed"] is True
    assert result["score"] == 1.0
    assert set(result["skill_scores"]) == set(
        _chapter_with_assessment()["levels"][0]["skill_ids"]
    )


def test_one_ordinary_deterministic_miss_can_still_pass_thresholds(monkeypatch):
    state = _enter_chapter_check(monkeypatch)

    for item_number in range(12):
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect" if item_number == 0 else "correct",
        )

    result = state["chapter_assessment"]["attempt_history"][-1]
    assert result["score"] > 0.9
    assert min(result["skill_scores"].values()) >= 0.6
    assert result["failed_hard_blocker_item_ids"] == []
    assert result["passed"] is True
    assert state["phase"] == "complete"


def test_contradictory_concept_answer_cannot_pass_chapter_when_aggregate_is_high(monkeypatch):
    chapter = _chapter_with_assessment()
    concept_item = chapter["chapter_assessment"]["items"][0]
    concept_item.update(
        {
            "options": [],
            "accepted_answers": [],
            "answer_rule": "concept_slots",
            "concept_slots": [
                {
                    "id": "land_evidence",
                    "description": "Names land evidence.",
                    "any_of": ["land"],
                },
                {
                    "id": "water_evidence",
                    "description": "Names water evidence.",
                    "any_of": ["water"],
                },
            ],
            "forbidden_phrases": ["does not use water"],
        }
    )
    state = _enter_chapter_check_for(monkeypatch, chapter)

    for item_number in range(12):
        activity = curriculum._current_activity(state)
        assert activity is not None
        answer = (
            "The frog uses land and water but does not use water."
            if item_number == 0
            else "correct"
        )
        open_answer_evaluation = None
        if item_number == 0:
            open_answer_evaluation = {
                "schema_version": "school-v3-rubric-1",
                "item_id": activity["activity_id"],
                "skill_ids": activity["skill_ids"],
                "score": 1.0,
                "confidence": 0.95,
                "language_detected": "en",
                "criteria": [
                    {
                        "id": "land_evidence",
                        "met": True,
                        "quality": 1.0,
                        "evidence_quote": "land",
                    },
                    {
                        "id": "water_evidence",
                        "met": True,
                        "quality": 1.0,
                        "evidence_quote": "water",
                    },
                ],
                "misconception_tags": [],
                "blockers": [],
                "needs_human_review": False,
                "feedback_to_learner": "Both words are present.",
            }
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=answer,
            open_answer_evaluation=open_answer_evaluation,
        )

    result = state["chapter_assessment"]["attempt_history"][-1]
    first_response = state["chapter_assessment"]["responses"][0]
    assert first_response["score"] == 1.0
    assert first_response["blockers"] == ["contradictory_response"]
    assert result["score"] == 1.0
    assert result["failed_hard_blocker_item_ids"] == [concept_item["item_id"]]
    assert result["passed"] is False
    assert state["completed_chapter_ids"] == []
    assert state["phase"] == "remediation"


def test_failed_chapter_check_reopens_only_a_weak_skill_level(monkeypatch):
    state, weak_skill_id = _fail_first_assessment(monkeypatch)

    assert state["status"] == "active"
    assert state["phase"] == "remediation"
    assert state["completed_chapter_ids"] == []
    assert state["remediation_queue"] == [state["levels"][0]["level_id"]]
    assert state["levels"][0]["status"] == "in_progress"
    assert state["levels"][0]["current_step"] == "masterclass"
    result = state["chapter_assessment"]["attempt_history"][-1]
    assert result["passed"] is False
    assert result["weak_skill_ids"] == [weak_skill_id]
    remediation = curriculum._current_activity(state)
    assert remediation is not None
    assert remediation["kind"] == "masterclass"


def test_remediation_success_starts_an_alternate_second_check(monkeypatch):
    state, _ = _fail_first_assessment(monkeypatch)
    first_item_ids = set(state["chapter_assessment"]["selected_item_ids"])

    masterclass = curriculum._current_activity(state)
    assert masterclass is not None
    state, _ = curriculum.apply_curriculum_answer(
        state,
        activity_id=masterclass["activity_id"],
        answer=_correct_answer(masterclass),
    )
    independent = curriculum._current_activity(state)
    assert independent is not None
    assert independent["kind"] == "independent_check"
    state, _ = curriculum.apply_curriculum_answer(
        state,
        activity_id=independent["activity_id"],
        answer=_correct_answer(independent),
    )

    assert state["phase"] == "chapter_check"
    assert state["chapter_assessment"]["attempt_no"] == 2
    second_item_ids = set(state["chapter_assessment"]["selected_item_ids"])
    assert len(second_item_ids - first_item_ids) >= 8
    assert state["chapter_assessment"]["responses"] == []
    assert curriculum._current_activity(state)["kind"] == "chapter_check"


def test_second_failed_check_pauses_for_support_without_unlock_or_loop(monkeypatch):
    state, _ = _fail_first_assessment(monkeypatch)
    for expected_kind in ("masterclass", "independent_check"):
        activity = curriculum._current_activity(state)
        assert activity is not None
        assert activity["kind"] == expected_kind
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=_correct_answer(activity),
        )

    for _ in range(12):
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect",
        )

    assert state["status"] == "active"
    assert state["phase"] == "needs_support"
    assert state["completed_chapter_ids"] == []
    assert curriculum._current_activity(state) is None
    assert state["support_required"]["reason"] == "chapter_check_attempts_exhausted"
    assert state["support_required"]["attempt_count"] == 2
    assert state["chapter_assessment"]["attempt_history"][-1]["passed"] is False


def test_second_failed_check_opens_three_authored_revision_levels_before_final_form(
    monkeypatch,
):
    chapter = _chapter_with_extended_revision()
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"
    state = _answer_until_phase(state, "chapter_check")
    state = _fail_assessment_form(state)
    state = _answer_until_phase(state, "chapter_check")

    first_two_forms = set(state["chapter_assessment"]["used_item_ids"]) | set(
        state["chapter_assessment"]["selected_item_ids"]
    )
    state = _fail_assessment_form(state)

    assert state["phase"] == "remediation"
    assert state["remediation_mode"] == "expanded_revision"
    assert state["chapter_assessment"]["attempt_no"] == 2
    activity = curriculum._current_activity(state)
    assert activity is not None
    assert activity["kind"] == "revision_level_1"
    assert activity["passage"] == "Authored revision passage 1."

    observed_revision_kinds = []
    while state.get("phase") == "remediation":
        activity = curriculum._current_activity(state)
        assert activity is not None
        if activity["kind"].startswith("revision_level_"):
            observed_revision_kinds.append(activity["kind"])
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=_correct_answer(activity),
        )

    assert observed_revision_kinds == [
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    ]
    assert state["phase"] == "chapter_check"
    assert state["chapter_assessment"]["attempt_no"] == 3
    assert set(state["chapter_assessment"]["selected_item_ids"]).isdisjoint(
        first_two_forms
    )


def test_third_failed_check_creates_truthful_parent_backed_support(monkeypatch):
    chapter = _chapter_with_extended_revision()
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"
    for _ in range(2):
        state = _answer_until_phase(state, "chapter_check")
        state = _fail_assessment_form(state)
    state = _answer_until_phase(state, "chapter_check")
    state = _fail_assessment_form(state)

    assert state["phase"] == "needs_support"
    assert state["completed_chapter_ids"] == []
    assert curriculum._current_activity(state) is None
    support = state["support_required"]
    assert support["attempt_count"] == 3
    assert support["focus"] == chapter["levels"][0]["focus"]
    assert support["cap"] == {
        "used": 3,
        "limit": 3,
        "scope": "chapter_check",
    }
    assert [event["path_type"] for event in support["history"]] == [
        "focused_revision",
        "expanded_revision",
        "parent_supported_pause",
    ]


def test_expanded_revision_is_bounded_to_three_activities_across_many_levels(
    monkeypatch,
):
    chapter = _multi_level_chapter_with_extended_revision()
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    for level in state["levels"][:-1]:
        level["status"] = "complete"
        level["current_step"] = "complete"
    state["levels"][-1]["status"] = "in_progress"
    state["levels"][-1]["current_step"] = "independent_check"
    state["current_level_index"] = len(state["levels"]) - 1

    for _ in range(2):
        state = _answer_until_phase(state, "chapter_check")
        state = _fail_assessment_form(state)

    assert state["remediation_mode"] == "expanded_revision"
    assert len(state["assessment_revision_plan"]) == 3
    observed = []
    while state.get("phase") == "remediation":
        activity = curriculum._current_activity(state)
        assert activity is not None
        observed.append((activity["level_id"], activity["kind"]))
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect",
        )

    assert len(observed) == 3
    assert all(kind.startswith("revision_level_") for _, kind in observed)
    assert state["phase"] == "chapter_check"
    assert state["chapter_assessment"]["attempt_no"] == 3
    assert state["assessment_revision_targeted_skill_ids"]
    assert state["assessment_revision_deferred_skill_ids"] == []


def test_live_class5_chapter1_has_bounded_revisions_and_three_fresh_forms():
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    skill_ids = list(
        dict.fromkeys(
            skill_id
            for level in state["levels"]
            for skill_id in level["skill_ids"]
        )
    )
    remediating = curriculum._start_assessment_remediation(
        state,
        skill_ids,
        mode="expanded_revision",
        skill_scores={skill_id: 0.0 for skill_id in skill_ids},
    )
    assert len(remediating["assessment_revision_plan"]) == 3
    assert set(remediating["assessment_revision_targeted_skill_ids"]) | set(
        remediating["assessment_revision_deferred_skill_ids"]
    ) == set(skill_ids)
    for entry in remediating["assessment_revision_plan"]:
        level = next(
            level
            for level in remediating["levels"]
            if level["level_id"] == entry["level_id"]
        )
        assert entry["kind"] in level["checks"]

    selecting = state
    forms = []
    taught_skills = set(skill_ids)
    for _ in range(3):
        selecting = curriculum._begin_chapter_assessment(selecting)
        selected_ids = set(selecting["chapter_assessment"]["selected_item_ids"])
        selected_items = [
            item
            for item in selecting["chapter_assessment"]["items"]
            if item["item_id"] in selected_ids
        ]
        forms.append(selected_ids)
        assert {
            skill_id
            for item in selected_items
            for skill_id in item["skill_ids"]
        } == taught_skills

    assert all(
        forms[left].isdisjoint(forms[right])
        for left in range(len(forms))
        for right in range(left + 1, len(forms))
    )


def test_each_selected_check_covers_every_taught_skill_even_when_bank_is_clustered(
    monkeypatch,
):
    chapter = _chapter_with_assessment()
    taught_skills = list(chapter["levels"][0]["skill_ids"]) + ["writing.short_answer"]
    chapter["levels"][0]["skill_ids"] = taught_skills
    chapter["chapter_assessment"]["items"] = [
        _assessment_item(index, taught_skills[0])
        for index in range(1, 8)
    ] + [
        _assessment_item(index, taught_skills[1])
        for index in range(8, 15)
    ] + [
        _assessment_item(index, taught_skills[2])
        for index in range(15, 21)
    ]
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"
    activity = curriculum._current_activity(state)
    assert activity is not None
    state, _ = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=_correct_answer(activity),
    )

    item_by_id = {
        item["item_id"]: item for item in state["chapter_assessment"]["items"]
    }
    selected_skills = {
        skill_id
        for item_id in state["chapter_assessment"]["selected_item_ids"]
        for skill_id in item_by_id[item_id]["skill_ids"]
    }
    assert selected_skills == set(taught_skills)


def test_multi_skill_remediation_follows_weak_level_queue_before_retest(monkeypatch):
    chapter = copy.deepcopy(curriculum.CLASS_5_WISE_PARROT_CHAPTER)
    chapter["chapter_id"] = "eng_c5_multi_remediation"
    chapter["chapter_no"] = 99
    chapter["content_version"] = "multi-remediation-1"
    chapter["levels"] = chapter["levels"][:2]
    for level in chapter["levels"]:
        level["checks"].pop("transfer_check", None)
    first_skill = chapter["levels"][0]["skill_ids"][0]
    second_skill = next(
        skill_id
        for skill_id in chapter["levels"][1]["skill_ids"]
        if skill_id != first_skill
    )
    chapter["chapter_assessment"] = {
        "items_per_attempt": 12,
        "pass_score": 0.8,
        "max_attempts": 2,
        "items": [
            _assessment_item(index, first_skill if index % 2 else second_skill)
            for index in range(1, 21)
        ],
    }
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    state["levels"][0]["status"] = "complete"
    state["levels"][0]["current_step"] = "complete"
    state["levels"][1]["status"] = "in_progress"
    state["levels"][1]["current_step"] = "independent_check"
    state["current_level_index"] = 1
    final_lesson = curriculum._current_activity(state)
    assert final_lesson is not None
    state, _ = curriculum.apply_curriculum_answer(
        state,
        activity_id=final_lesson["activity_id"],
        answer=_correct_answer(final_lesson),
    )
    for _ in range(12):
        activity = curriculum._current_activity(state)
        assert activity is not None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer="incorrect",
        )

    expected_queue = [level["level_id"] for level in chapter["levels"]]
    assert state["remediation_queue"] == expected_queue
    for expected_level_id in expected_queue:
        masterclass = curriculum._current_activity(state)
        assert masterclass is not None
        assert masterclass["level_id"] == expected_level_id
        assert masterclass["kind"] == "masterclass"
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=masterclass["activity_id"],
            answer=_correct_answer(masterclass),
        )
        independent = curriculum._current_activity(state)
        assert independent is not None
        assert independent["level_id"] == expected_level_id
        assert independent["kind"] == "independent_check"
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=independent["activity_id"],
            answer=_correct_answer(independent),
        )

    assert state["phase"] == "chapter_check"
    assert state["chapter_assessment"]["attempt_no"] == 2


def test_frog_open_answer_preflights_check_structure_without_keyword_grading():
    compare_activity = {"preflight_rule": "frog_compare_25_50"}
    message_activity = {"preflight_rule": "frog_message_35_60"}
    valid_compare = (
        "A frog can move across wet ground and swim through a pond. A fish stays "
        "in water, while the frog can use both places during its life."
    )
    valid_message = (
        "Dear Hopper, I enjoy cycling near my home and reading funny stories after "
        "school. On rainy days, I watch puddles form beside the garden. What games "
        "do you play with the other frogs? Your friend, Meera."
    )

    assert curriculum._open_answer_preflight(compare_activity, "Frogs differ.") is False
    assert curriculum._open_answer_preflight(compare_activity, valid_compare) is True
    assert curriculum._open_answer_preflight(message_activity, "Hello. Bye.") is False
    assert curriculum._open_answer_preflight(message_activity, valid_message) is True


def test_legacy_completed_state_normalizes_to_complete_phase():
    state = {
        "engine_version": "school-rebuild-curriculum-1",
        "status": "complete",
        "levels": [
            {
                "level_id": "legacy_level",
                "status": "complete",
                "current_step": "complete",
                "attempts": [],
            }
        ],
        "current_level_index": 0,
    }

    normalized = curriculum.normalize_curriculum_state(state)

    assert normalized["status"] == "complete"
    assert normalized["phase"] == "complete"


def test_engine_rejects_a_form_that_cannot_cover_every_assessed_skill(monkeypatch):
    chapter = _chapter_with_assessment()
    chapter["levels"][0]["skill_ids"] = [f"test.skill.{index}" for index in range(13)]
    chapter["chapter_assessment"]["items"] = [
        _assessment_item(index, f"test.skill.{(index - 1) % 13}")
        for index in range(1, 27)
    ]
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={"report_id": "placement", "unlock_state": "target_unlocked"},
        recap_session=None,
    )
    state["levels"][0]["current_step"] = "independent_check"
    activity = curriculum._current_activity(state)
    assert activity is not None

    with pytest.raises(ValueError, match="chapter_assessment_form_cannot_cover_skills"):
        curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=_correct_answer(activity),
        )


def test_remediation_focus_is_separate_from_the_point_six_weak_skill_floor():
    chapter = _chapter_with_assessment()
    skill_ids = list(chapter["levels"][0]["skill_ids"])
    assessment = copy.deepcopy(chapter["chapter_assessment"])
    assessment.update(
        {
            "attempt_no": 1,
            "selected_item_ids": [item["item_id"] for item in assessment["items"][:12]],
            "current_index": 12,
            "attempt_history": [],
            "responses": [
                {
                    "activity_id": f"chapter_check:1:{index}",
                    "item_id": f"item-{index}",
                    "skill_ids": [skill_ids[index % len(skill_ids)]],
                    "score": 0.75,
                }
                for index in range(12)
            ],
        }
    )
    state = {
        "status": "active",
        "phase": "chapter_check",
        "chapter": {"chapter_id": chapter["chapter_id"]},
        "completed_chapter_ids": [],
        "levels": [
            {
                **copy.deepcopy(chapter["levels"][0]),
                "status": "complete",
                "current_step": "complete",
                "attempts": [],
            }
        ],
        "current_level_index": 0,
        "chapter_assessment": assessment,
    }

    updated = curriculum._finish_chapter_assessment_attempt(state)

    result = updated["chapter_assessment"]["attempt_history"][-1]
    assert result["passed"] is False
    assert result["weak_skill_ids"] == []
    assert set(result["remediation_skill_ids"]) == set(skill_ids)
    assert updated["phase"] == "remediation"


def test_concept_slot_grading_accepts_paraphrase_and_blocks_contradiction():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "land_evidence",
                "description": "Names evidence that the animal moved on land.",
                "any_of": ["moss", "ground", "land", "hopped"],
            },
            {
                "id": "water_evidence",
                "description": "Names evidence that the animal entered or used water.",
                "any_of": ["ditch", "water", "underwater"],
            },
        ],
        "forbidden_phrases": [
            "does not use water",
            "never enters water",
            "cannot enter water",
        ],
    }

    valid = curriculum._evaluate_deterministic_answer(
        activity,
        "It hopped on moss and later hid in the ditch.",
    )
    contradictory = curriculum._evaluate_deterministic_answer(
        activity,
        "The frog uses land and water, but it does not use water.",
    )
    partial = curriculum._evaluate_deterministic_answer(
        activity,
        "It moved across the moss.",
    )

    assert valid["correct"] is True
    assert valid["score"] == 1.0
    assert [criterion["id"] for criterion in valid["criteria"]] == [
        "land_evidence",
        "water_evidence",
    ]
    assert contradictory["correct"] is False
    assert "contradictory_response" in contradictory["blockers"]
    assert partial["correct"] is False
    assert partial["score"] == 0.5
    assert partial["missing_criteria"] == ["water_evidence"]


def test_concept_slot_grading_does_not_count_a_locally_negated_concept():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "water_use",
                "description": "States that the animal uses water.",
                "any_of": ["use water", "enters the pond"],
            }
        ],
    }

    evaluation = curriculum._evaluate_deterministic_answer(
        activity,
        "The animal does not use water.",
    )

    assert evaluation["correct"] is False
    assert evaluation["missing_criteria"] == ["water_use"]


def test_concept_slot_grading_does_not_count_a_later_adversative_negation():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "water_use",
                "description": "States that the animal uses water.",
                "any_of": ["used the water filled ditch"],
            }
        ],
    }

    evaluation = curriculum._evaluate_deterministic_answer(
        activity,
        "It used the water-filled ditch, but it was not actually in the water.",
    )

    assert evaluation["correct"] is False
    assert evaluation["missing_criteria"] == ["water_use"]


def test_concept_slot_grading_accepts_local_word_order_paraphrase():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "point_not_search",
                "description": "Explains that pointing means a search is unnecessary.",
                "any_of": ["no search is needed"],
            }
        ],
        "min_response_words": 8,
    }

    evaluation = curriculum.evaluate_deterministic_answer(
        activity,
        "The apprentice can point to the bowl because there is no need to search.",
    )

    assert evaluation["correct"] is True
    assert evaluation["missing_criteria"] == []


def test_adversative_negation_builds_a_strict_semantic_rubric_fallback():
    activity = {
        "activity_id": "frog_habitat:independent_check:1",
        "answer_rule": "concept_slots",
        "skill_ids": ["reading.sentence_comprehension"],
        "concept_slots": [
            {
                "id": "water_use",
                "description": "States that the frog uses water.",
                "any_of": ["used the water filled ditch"],
            }
        ],
        "min_response_words": 6,
    }
    nuanced = (
        "It used the water-filled ditch, but the ditch did not cover its eyes."
    )

    fallback = curriculum.evaluator_activity_for_answer(activity, nuanced)

    assert fallback is not None
    assert fallback["evaluation_mode"] == "llm_rubric"
    assert fallback["activity_id"] == activity["activity_id"]
    assert fallback["rubric_criteria"] == [
        {
            "id": "water_use",
            "description": "States that the frog uses water.",
            "required": True,
            "min_quality": 0.7,
        }
    ]
    assert curriculum.evaluator_activity_for_answer(
        activity,
        "It used the water-filled ditch and kept its eyes above water.",
    ) is None


def test_natural_concept_paraphrase_uses_semantic_fallback_before_rejection():
    activity = {
        "activity_id": "humour:independent_check:1",
        "answer_rule": "concept_slots",
        "skill_ids": ["reading.inference_reason", "writing.reason_answer"],
        "concept_slots": [
            {
                "id": "pencil_in_hand",
                "description": "States that Ishita is holding or tapping the pencil.",
                "any_of": ["pencil is in her hand", "she is tapping the pencil"],
            },
            {
                "id": "search_mistake",
                "description": "Explains that she searches for an object she already has.",
                "any_of": [
                    "searching for something she already has",
                    "her search is unnecessary",
                ],
            },
        ],
        "min_response_words": 10,
        "forbidden_phrases": ["a friend stole it"],
    }
    answer = (
        "Ishita mistakenly searched for the pencil even though she was already "
        "tapping that same pencil against her notebook, so a friend might smile."
    )

    deterministic = curriculum.evaluate_deterministic_answer(activity, answer)
    fallback = curriculum.evaluator_activity_for_answer(activity, answer)

    assert deterministic["correct"] is False
    assert fallback is not None
    assert [criterion["id"] for criterion in fallback["rubric_criteria"]] == [
        "pencil_in_hand",
        "search_mistake",
    ]


def test_semantic_fallback_preserves_authored_concept_sequence():
    activity = {
        "activity_id": "frog_cycle:independent_check:1",
        "answer_rule": "concept_slots",
        "skill_ids": ["writing.summary_own_words"],
        "concept_slots": [
            {"id": "egg", "description": "Starts with eggs.", "any_of": ["eggs"]},
            {
                "id": "tadpole",
                "description": "Continues with tadpoles.",
                "any_of": ["tadpoles"],
            },
            {
                "id": "frog",
                "description": "Ends with frogs.",
                "any_of": ["frogs"],
            },
        ],
        "ordered_concept_slot_ids": ["egg", "tadpole", "frog"],
    }

    fallback = curriculum.evaluator_activity_for_answer(
        activity,
        "Although frogs do not come first, tadpoles and eggs are also named.",
    )

    assert fallback is not None
    assert [criterion["id"] for criterion in fallback["rubric_criteria"]] == [
        "egg",
        "tadpole",
        "frog",
        "concept_sequence",
    ]
    assert "egg -> tadpole -> frog" in fallback["rubric_criteria"][-1]["description"]


def test_semantic_concept_fallback_keeps_backend_owned_structural_gates():
    activity = {
        "activity_id": "frog_habitat:independent_check:1",
        "answer_rule": "concept_slots",
        "skill_ids": ["reading.sentence_comprehension"],
        "concept_slots": [
            {
                "id": "water_use",
                "description": "States that the frog uses water.",
                "any_of": ["used the water filled ditch"],
            }
        ],
        "min_response_words": 6,
        "forbidden_phrases": ["does not use water"],
    }
    answer = "It used the ditch, but the ditch did not cover its eyes."
    raw_evaluation = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 1.0,
        "confidence": 0.9,
        "language_detected": "en",
        "criteria": [
            {
                "id": "water_use",
                "met": True,
                "quality": 1.0,
                "evidence_quote": "used the ditch",
            }
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The water use is clear.",
    }

    evaluation = curriculum.decide_semantic_concept_evaluation(
        activity,
        raw_evaluation,
        answer=answer,
    )

    assert evaluation["correct"] is True
    assert evaluation["score"] == 1.0
    assert evaluation["model_score"] == 1.0
    assert {criterion["id"] for criterion in evaluation["criteria"]} == {
        "water_use",
        "response_min_words",
    }


def test_chapter_check_persists_semantic_fallback_evaluation_mode(monkeypatch):
    chapter = _chapter_with_assessment()
    item = chapter["chapter_assessment"]["items"][0]
    item.update(
        {
            "options": [],
            "accepted_answers": [],
            "answer_rule": "concept_slots",
            "concept_slots": [
                {
                    "id": "water_use",
                    "description": "States that the frog uses water.",
                    "any_of": ["used the ditch"],
                }
            ],
        }
    )
    state = _enter_chapter_check_for(monkeypatch, chapter)
    activity = curriculum._current_activity(state)
    answer = "It used the ditch, but the ditch did not cover its eyes."
    raw_evaluation = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 1.0,
        "confidence": 0.9,
        "language_detected": "en",
        "criteria": [
            {
                "id": "water_use",
                "met": True,
                "quality": 1.0,
                "evidence_quote": "used the ditch",
            }
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Water use is supported.",
    }

    updated, evaluation = curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=raw_evaluation,
    )

    assert evaluation["evaluation_mode"] == "semantic_llm_rubric"
    assert updated["chapter_assessment"]["responses"][0]["evaluation_mode"] == (
        "semantic_llm_rubric"
    )


def test_concept_slot_grading_does_not_join_tokens_across_unrelated_content():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "water_use",
                "description": "States that the frog uses water.",
                "any_of": ["frog uses pond water"],
            }
        ],
    }
    filler = " ".join(f"unrelated{index}" for index in range(30))

    evaluation = curriculum._evaluate_deterministic_answer(
        activity,
        f"The frog {filler} uses pond water.",
    )

    assert evaluation["correct"] is False
    assert evaluation["missing_criteria"] == ["water_use"]


def test_concept_slot_grading_enforces_minimum_words_with_auditable_criterion():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "egg_stage",
                "description": "Names the egg stage.",
                "any_of": ["eggs", "frogspawn"],
            },
            {
                "id": "tadpole_stage",
                "description": "Names the tadpole stage.",
                "any_of": ["tadpole"],
            },
        ],
        "min_response_words": 6,
    }

    evaluation = curriculum._evaluate_deterministic_answer(
        activity,
        "Eggs become a tadpole.",
    )

    criterion = next(
        item for item in evaluation["criteria"] if item["id"] == "response_min_words"
    )
    assert evaluation["correct"] is False
    assert criterion["met"] is False
    assert criterion["quality"] == 0.0
    assert criterion["evidence_quote"] == "4 words (minimum 6)"
    assert "response_min_words" in evaluation["missing_criteria"]


def test_concept_slot_grading_enforces_authored_sequence_by_match_position():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "egg_stage",
                "description": "Names the egg stage.",
                "any_of": ["eggs", "frogspawn"],
            },
            {
                "id": "tadpole_stage",
                "description": "Names the tadpole stage.",
                "any_of": ["tadpole"],
            },
            {
                "id": "froglet_stage",
                "description": "Names the froglet stage.",
                "any_of": ["froglet"],
            },
            {
                "id": "adult_stage",
                "description": "Names the adult stage.",
                "any_of": ["adult frog", "frog"],
            },
        ],
        "ordered_concept_slot_ids": [
            "egg_stage",
            "tadpole_stage",
            "froglet_stage",
            "adult_stage",
        ],
    }

    ordered = curriculum._evaluate_deterministic_answer(
        activity,
        "Frogspawn becomes a tadpole, then a froglet, and finally an adult frog.",
    )
    reversed_order = curriculum._evaluate_deterministic_answer(
        activity,
        "An adult frog came after a froglet, which came after a tadpole and frogspawn.",
    )

    ordered_criterion = next(
        item for item in ordered["criteria"] if item["id"] == "concept_sequence"
    )
    reversed_criterion = next(
        item
        for item in reversed_order["criteria"]
        if item["id"] == "concept_sequence"
    )
    assert ordered["correct"] is True
    assert ordered_criterion["met"] is True
    assert reversed_order["correct"] is False
    assert reversed_criterion["met"] is False
    assert "concept_sequence" in reversed_order["missing_criteria"]


def test_concept_sequence_uses_later_alias_when_earliest_alias_is_incidental():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "egg_stage",
                "description": "Names the egg stage.",
                "any_of": ["frogspawn"],
            },
            {
                "id": "tadpole_stage",
                "description": "Names the tadpole stage.",
                "any_of": ["tadpole"],
            },
            {
                "id": "froglet_stage",
                "description": "Names the froglet stage.",
                "any_of": ["froglet"],
            },
            {
                "id": "adult_stage",
                "description": "Names the adult stage.",
                "any_of": ["frog", "adult frog"],
            },
        ],
        "ordered_concept_slot_ids": [
            "egg_stage",
            "tadpole_stage",
            "froglet_stage",
            "adult_stage",
        ],
    }

    evaluation = curriculum._evaluate_deterministic_answer(
        activity,
        "A frog begins as frogspawn, becomes a tadpole, then a froglet, and finally an adult frog.",
    )

    criterion = next(
        item for item in evaluation["criteria"] if item["id"] == "concept_sequence"
    )
    assert evaluation["correct"] is True
    assert criterion["met"] is True
    assert "adult_stage: adult frog" in criterion["evidence_quote"]


def test_concept_sequence_rejects_overlapping_alias_spans():
    activity = {
        "answer_rule": "concept_slots",
        "concept_slots": [
            {
                "id": "adult_stage",
                "description": "Names the adult frog stage.",
                "any_of": ["adult frog"],
            },
            {
                "id": "frog_term",
                "description": "Names frog as a separate later term.",
                "any_of": ["frog"],
            },
        ],
        "ordered_concept_slot_ids": ["adult_stage", "frog_term"],
    }

    evaluation = curriculum._evaluate_deterministic_answer(
        activity,
        "The adult frog rests.",
    )

    criterion = next(
        item for item in evaluation["criteria"] if item["id"] == "concept_sequence"
    )
    assert evaluation["correct"] is False
    assert criterion["met"] is False
    assert "concept_sequence" in evaluation["missing_criteria"]


def test_open_answer_zero_pass_score_is_not_replaced_by_default():
    activity = {
        "activity_id": "chapter_check:1:zero-pass-score",
        "skill_ids": ["writing.boundary"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.0,
        "rubric_criteria": [
            {
                "id": "attempt",
                "description": "Makes an attempt.",
                "required": True,
                "min_quality": 0.0,
            }
        ],
    }
    answer = "A valid attempt."
    raw_evaluation = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.5,
        "confidence": 0.9,
        "language_detected": "en",
        "criteria": [
            {
                "id": "attempt",
                "met": True,
                "quality": 0.5,
                "evidence_quote": "valid attempt",
            }
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Attempt recorded.",
    }

    evaluation = curriculum.decide_open_answer_evaluation(
        activity,
        raw_evaluation,
        answer=answer,
    )

    assert evaluation["score"] == 0.5
    assert evaluation["correct"] is True


def test_open_answer_untraceable_model_quote_is_replaced_with_learner_evidence():
    activity = {
        "activity_id": "chapter_check:1:reason-answer",
        "skill_ids": ["writing.reason_answer"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.8,
        "rubric_criteria": [
            {
                "id": "reason",
                "description": "Gives a relevant reason.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
    }
    answer = "Papa laughed because the spectacles had been on his head all along."
    raw_evaluation = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.9,
        "confidence": 0.9,
        "language_detected": "en",
        "criteria": [
            {
                "id": "reason",
                "met": True,
                "quality": 0.9,
                "evidence_quote": "The family searched every shelf in the room.",
            }
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The reason is supported.",
    }

    evaluation = curriculum.decide_open_answer_evaluation(
        activity,
        raw_evaluation,
        answer=answer,
    )

    assert evaluation["correct"] is True
    assert evaluation["criteria"][0]["evidence_quote"] == answer


def test_summary_source_accuracy_is_backend_confirmed_when_model_flags_a_passage_fact():
    activity = {
        "activity_id": "chapter_check:2:eng_c5_ch01_assess_21",
        "passage": (
            "Renu could not find her recipe notebook after preparing snacks. "
            "She remembered carrying it to the balcony, followed a trail of flour "
            "marks, and found it under a seed tray. She brushed it clean and "
            "returned it to the kitchen shelf."
        ),
        "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
        ],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.8,
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": criterion_id,
                "required": True,
                "min_quality": 0.7,
            }
            for criterion_id in (
                "summary_word_range",
                "summary_problem",
                "summary_evidence_action",
                "summary_result",
                "summary_source_accuracy",
            )
        ],
    }
    answer = (
        "Renu lost her recipe notebook after making snacks. Remembering the "
        "balcony and following flour marks, she found it beneath a seed tray, "
        "cleaned it, and returned it to the kitchen shelf."
    )
    raw_evaluation = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.9,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": criterion["id"] != "summary_source_accuracy",
                "quality": (
                    0.5 if criterion["id"] == "summary_source_accuracy" else 1.0
                ),
                "evidence_quote": (
                    "Remembering the balcony"
                    if criterion["id"] == "summary_source_accuracy"
                    else answer
                ),
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": True,
        "feedback_to_learner": "Review source accuracy.",
    }

    evaluation = curriculum.decide_open_answer_evaluation(
        activity,
        raw_evaluation,
        answer=answer,
    )

    source_accuracy = next(
        criterion
        for criterion in evaluation["criteria"]
        if criterion["id"] == "summary_source_accuracy"
    )
    assert source_accuracy["met"] is True
    assert source_accuracy["quality"] >= 0.9
    assert evaluation["missing_criteria"] == []
    assert "needs_human_review" not in evaluation["blockers"]
    assert evaluation["correct"] is True


def test_summary_source_accuracy_keeps_human_review_for_an_invented_detail():
    activity = {
        "activity_id": "chapter_check:2:summary-invention",
        "passage": (
            "Renu followed flour marks, found the notebook under a seed tray, "
            "and returned it to the kitchen shelf."
        ),
        "skill_ids": ["writing.summary_own_words"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.8,
        "rubric_criteria": [
            {
                "id": "summary_result",
                "description": "States the result.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "summary_source_accuracy",
                "description": "Does not invent details.",
                "required": True,
                "min_quality": 0.7,
            },
        ],
    }
    answer = (
        "Renu found the notebook under a seed tray and a teacher rewarded her "
        "before she returned it to the kitchen shelf."
    )
    raw_evaluation = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.75,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": "summary_result",
                "met": True,
                "quality": 1.0,
                "evidence_quote": "returned it to the kitchen shelf",
            },
            {
                "id": "summary_source_accuracy",
                "met": False,
                "quality": 0.5,
                "evidence_quote": "a teacher rewarded her",
            },
        ],
        "misconception_tags": ["invented_detail"],
        "blockers": [],
        "needs_human_review": True,
        "feedback_to_learner": "Remove the invented detail.",
    }

    evaluation = curriculum.decide_open_answer_evaluation(
        activity,
        raw_evaluation,
        answer=answer,
    )

    assert "summary_source_accuracy" in evaluation["missing_criteria"]
    assert "needs_human_review" in evaluation["blockers"]
    assert evaluation["correct"] is False


def _historical_summary_support_state(*, answer: str, cited_concern: str) -> dict:
    passage = (
        "Renu could not find her recipe notebook after preparing snacks. "
        "She remembered carrying it to the balcony, followed a trail of flour "
        "marks, and found it under a seed tray. She brushed it clean and "
        "returned it to the kitchen shelf."
    )
    item_id = "eng_c5_ch01_assess_21"
    skill_ids = [
        "reading.paragraph_main_idea",
        "writing.summary_own_words",
    ]
    rubric_criteria = [
        {
            "id": criterion_id,
            "description": criterion_id,
            "required": True,
            "min_quality": 0.7,
        }
        for criterion_id in (
            "summary_word_range",
            "summary_problem",
            "summary_evidence_action",
            "summary_result",
            "summary_source_accuracy",
        )
    ]
    saved_criteria = [
        {
            "id": criterion["id"],
            "met": criterion["id"] != "summary_source_accuracy",
            "quality": (
                0.5 if criterion["id"] == "summary_source_accuracy" else 1.0
            ),
            "evidence_quote": (
                cited_concern
                if criterion["id"] == "summary_source_accuracy"
                else answer
            ),
        }
        for criterion in rubric_criteria
    ]
    return {
        "engine_version": "school-rebuild-curriculum-2",
        "status": "active",
        "phase": "needs_support",
        "subject_id": "english",
        "target_class_no": 5,
        "chapter": {
            "chapter_id": "eng_c5_ch01",
            "content_version": "chapter-content-v1",
            "certification_version": "chapter-certification-v1",
        },
        "completed_chapter_ids": [],
        "completed_chapter_versions": {},
        "completed_chapter_certification_versions": {},
        "current_level_index": 0,
        "levels": [
            {
                "level_id": "papas_spectacles_summary",
                "status": "complete",
                "current_step": "complete",
                "attempts": [],
                "skill_ids": skill_ids,
            }
        ],
        "chapter_assessment": {
            "items_per_attempt": 1,
            "pass_score": 0.8,
            "max_attempts": 2,
            "attempt_no": 2,
            "selected_item_ids": [item_id],
            "current_index": 1,
            "items": [
                {
                    "item_id": item_id,
                    "passage": passage,
                    "prompt": "Summarise the passage in your own words.",
                    "skill_ids": skill_ids,
                    "evaluation_mode": "llm_rubric",
                    "pass_score": 0.8,
                    "rubric_criteria": rubric_criteria,
                }
            ],
            "responses": [
                {
                    "activity_id": f"chapter_check:2:{item_id}",
                    "item_id": item_id,
                    "answer": answer,
                    "skill_ids": skill_ids,
                    "correct": False,
                    "score": 0.9,
                    "confidence": 0.95,
                    "criteria": saved_criteria,
                    "blockers": ["needs_human_review"],
                    "evaluation_mode": "llm_rubric",
                }
            ],
            "attempt_history": [
                {
                    "attempt_no": 2,
                    "score": 0.9,
                    "skill_scores": {
                        "reading.paragraph_main_idea": 0.9,
                        "writing.summary_own_words": 0.9,
                    },
                    "passed": False,
                    "failed_rubric_item_ids": [item_id],
                    "failed_hard_blocker_item_ids": [],
                    "weak_skill_ids": [],
                    "remediation_skill_ids": skill_ids,
                }
            ],
        },
        "support_required": {
            "reason": "chapter_check_attempts_exhausted",
            "attempt_count": 2,
            "weak_skill_ids": [],
            "remediation_skill_ids": skill_ids,
        },
    }


def test_reconcile_curriculum_state_repairs_saved_source_accuracy_false_negative():
    answer = (
        "Renu lost her recipe notebook after making snacks. Remembering the "
        "balcony and following flour marks, she found it beneath a seed tray, "
        "cleaned it, and returned it to the kitchen shelf."
    )
    state = _historical_summary_support_state(
        answer=answer,
        cited_concern="Remembering the balcony",
    )

    reconciled, repair = curriculum.reconcile_curriculum_state(state)

    assert repair == {
        "kind": "chapter_certification_reconciled",
        "chapter_id": "eng_c5_ch01",
        "attempt_no": 2,
        "skill_scores": {
            "reading.paragraph_main_idea": 1.0,
            "writing.summary_own_words": 1.0,
        },
    }
    assert reconciled["engine_version"] == curriculum.ENGINE_VERSION
    assert reconciled["status"] == "complete"
    assert reconciled["phase"] == "complete"
    assert reconciled["completed_chapter_ids"] == ["eng_c5_ch01"]
    assert "support_required" not in reconciled
    assert reconciled["chapter_assessment"]["attempt_history"][-1]["passed"] is True


def test_reconcile_curriculum_state_does_not_certify_an_invented_summary_detail():
    answer = (
        "Renu found the notebook under a seed tray and a teacher rewarded her "
        "before she returned it to the kitchen shelf."
    )
    state = _historical_summary_support_state(
        answer=answer,
        cited_concern="a teacher rewarded her",
    )

    reconciled, repair = curriculum.reconcile_curriculum_state(state)

    assert repair is None
    assert reconciled["engine_version"] == curriculum.ENGINE_VERSION
    assert reconciled["status"] == "active"
    assert reconciled["phase"] == "needs_support"
    assert reconciled["chapter_assessment"]["attempt_history"][-1]["passed"] is False
    assert reconciled["support_required"]["focus"] == (
        "Paragraph Main Idea; Summary Own Words"
    )
    assert reconciled["support_required"]["cap"] == {
        "used": 2,
        "limit": 2,
        "scope": "chapter_check",
    }
    assert reconciled["support_required"]["history"][-1]["path_type"] == (
        "parent_supported_pause"
    )


def test_failed_required_production_skill_cannot_be_averaged_away():
    skill_ids = [f"test.skill.{index}" for index in range(12)] + [
        "writing.compare_contrast"
    ]
    assessment = {
        "items_per_attempt": 13,
        "pass_score": 0.8,
        "max_attempts": 2,
        "attempt_no": 1,
        "selected_item_ids": [f"item-{index}" for index in range(13)],
        "current_index": 13,
        "attempt_history": [],
        "responses": [
            {
                "activity_id": f"chapter_check:1:item-{index}",
                "item_id": f"item-{index}",
                "skill_ids": [skill_id],
                "score": 0.0 if skill_id == "writing.compare_contrast" else 1.0,
            }
            for index, skill_id in enumerate(skill_ids)
        ],
    }
    state = {
        "status": "active",
        "phase": "chapter_check",
        "chapter": {"chapter_id": "production-gate"},
        "completed_chapter_ids": [],
        "levels": [
            {
                "level_id": "all_skills",
                "skill_ids": skill_ids,
                "status": "complete",
                "current_step": "complete",
                "attempts": [],
            }
        ],
        "current_level_index": 0,
        "chapter_assessment": assessment,
    }

    updated = curriculum._finish_chapter_assessment_attempt(state)

    result = updated["chapter_assessment"]["attempt_history"][-1]
    assert result["score"] > 0.9
    assert result["passed"] is False
    assert result["weak_skill_ids"] == ["writing.compare_contrast"]
    assert updated["phase"] == "remediation"
    assert updated["completed_chapter_ids"] == []


def test_rubric_item_below_its_own_pass_mark_blocks_chapter_completion():
    skill_ids = [f"test.skill.{index}" for index in range(12)] + [
        "writing.friendly_message"
    ]
    responses = []
    for index, skill_id in enumerate(skill_ids):
        is_production = skill_id == "writing.friendly_message"
        responses.append(
            {
                "activity_id": f"chapter_check:1:item-{index}",
                "item_id": f"item-{index}",
                "skill_ids": [skill_id],
                "score": 0.7 if is_production else 1.0,
                "correct": not is_production,
                "evaluation_mode": "llm_rubric" if is_production else "deterministic",
            }
        )
    state = {
        "status": "active",
        "phase": "chapter_check",
        "chapter": {"chapter_id": "rubric-item-gate"},
        "completed_chapter_ids": [],
        "levels": [
            {
                "level_id": "all_skills",
                "skill_ids": skill_ids,
                "status": "complete",
                "current_step": "complete",
                "attempts": [],
            }
        ],
        "current_level_index": 0,
        "chapter_assessment": {
            "items_per_attempt": 13,
            "pass_score": 0.8,
            "max_attempts": 2,
            "attempt_no": 1,
            "selected_item_ids": [response["item_id"] for response in responses],
            "current_index": 13,
            "attempt_history": [],
            "responses": responses,
        },
    }

    updated = curriculum._finish_chapter_assessment_attempt(state)

    result = updated["chapter_assessment"]["attempt_history"][-1]
    assert result["score"] > 0.95
    assert result["skill_scores"]["writing.friendly_message"] == 0.7
    assert result["passed"] is False
    assert result["failed_rubric_item_ids"] == ["item-12"]
    assert updated["completed_chapter_ids"] == []


def test_persisted_llm_item_failure_cannot_be_averaged_into_chapter_pass(monkeypatch):
    chapter = _chapter_with_assessment()
    skill_id = chapter["levels"][0]["skill_ids"][0]
    chapter["levels"][0]["skill_ids"] = [skill_id]
    for item in chapter["chapter_assessment"]["items"]:
        item["skill_ids"] = [skill_id]
    rubric_item = chapter["chapter_assessment"]["items"][0]
    rubric_item.update(
        {
            "options": [],
            "accepted_answers": [],
            "response_mode": "paragraph",
            "evaluation_mode": "llm_rubric",
            "preflight_rule": "Require relevant evidence.",
            "pass_score": 0.8,
            "rubric_criteria": [
                {
                    "id": "relevance",
                    "description": "Gives relevant evidence.",
                    "required": True,
                    "min_quality": 0.6,
                }
            ],
        }
    )
    state = _enter_chapter_check_for(monkeypatch, chapter)

    for item_number in range(12):
        activity = curriculum._current_activity(state)
        assert activity is not None
        if item_number == 0:
            answer = "Relevant evidence supports the answer."
            open_evaluation = {
                "schema_version": "school-v3-rubric-1",
                "item_id": activity["activity_id"],
                "skill_ids": [skill_id],
                "score": 0.7,
                "confidence": 0.9,
                "language_detected": "en",
                "criteria": [
                    {
                        "id": "relevance",
                        "met": True,
                        "quality": 0.7,
                        "evidence_quote": "Relevant evidence",
                    }
                ],
                "misconception_tags": [],
                "blockers": [],
                "needs_human_review": False,
                "feedback_to_learner": "Add stronger evidence.",
            }
        else:
            answer = "correct"
            open_evaluation = None
        state, _ = curriculum.apply_curriculum_answer(
            state,
            activity_id=activity["activity_id"],
            answer=answer,
            open_answer_evaluation=open_evaluation,
        )

    result = state["chapter_assessment"]["attempt_history"][-1]
    first_response = state["chapter_assessment"]["responses"][0]
    assert first_response["evaluation_mode"] == "llm_rubric"
    assert first_response["correct"] is False
    assert result["score"] > 0.95
    assert result["skill_scores"][skill_id] > 0.95
    assert result["failed_rubric_item_ids"] == [rubric_item["item_id"]]
    assert result["passed"] is False
    assert state["completed_chapter_ids"] == []
    public = curriculum.public_curriculum_response(
        {
            "session_id": "curriculum-session",
            "status": "active",
            "subject_id": "english",
            "class_no": 5,
            "state_json": state,
        }
    )
    serialized = json.dumps(public)
    assert "rubric_criteria" not in serialized
    assert "Relevant evidence" not in serialized
