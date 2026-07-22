from copy import deepcopy

from app.services import school_rebuild_curriculum as curriculum


def test_class_two_live_curriculum_is_discoverable():
    chapters = curriculum._available_chapters("english", 2)
    assert len(chapters) == 13
    assert chapters[0]["chapter_id"] == "eng_c2_ch01"
    assert all(chapter.get("chapter_assessment") for chapter in chapters)


def _authored_check_variants(kind: str) -> list[dict]:
    situations = (
        (
            "Meera has red pencils. Dev has blue pencils. Each needs both colours.",
            "What can Meera and Dev do?",
        ),
        (
            "Sana has storybooks. Kabir has puzzle books. "
            "They each want something new to read.",
            "How can Sana and Kabir help each other?",
        ),
        (
            "Tara has paper. Rohan has crayons. They want to make posters together.",
            "What should Tara and Rohan do?",
        ),
    )
    return [
        {
            "variant_id": f"{kind}-{variant_no}",
            "teaching_block": f"Use sharing to solve {kind} situation {variant_no}.",
            "passage": f"{kind.replace('_', ' ').title()} {variant_no}: {passage}",
            "prompt": f"For {kind.replace('_', ' ')} {variant_no}, {prompt}",
            "options": [],
            "accepted_answers": ["share", "they should share"],
        }
        for variant_no, (passage, prompt) in enumerate(situations, start=1)
    ]


def _chapter_with_transfer() -> tuple[dict, dict[str, list[dict]]]:
    chapter = deepcopy(curriculum.CLASS_3_CURRICULUM_CHAPTERS[0])
    chapter["chapter_id"] = "transfer-contract-chapter"
    chapter["levels"] = chapter["levels"][:1]
    level = chapter["levels"][0]
    level.pop("teaching_steps", None)
    variants_by_kind = {
        kind: _authored_check_variants(kind)
        for kind in (
            "guided_check",
            "bridge",
            "masterclass",
            "independent_check",
            "transfer_check",
        )
    }
    for kind in ("guided_check", "bridge", "masterclass", "independent_check"):
        level["checks"][kind] = variants_by_kind[kind][0]
    level["checks"]["transfer_check"] = variants_by_kind["transfer_check"][0]
    return chapter, variants_by_kind


def _new_state(monkeypatch) -> dict:
    chapter, variants_by_kind = _chapter_with_transfer()
    original_check_for_level = curriculum._check_for_level

    def check_for_level(level: dict, kind: str) -> dict:
        variants = variants_by_kind.get(kind)
        if variants is None:
            return original_check_for_level(level, kind)
        attempt_index = sum(
            previous.get("kind") == kind
            for previous in level.get("attempts") or []
            if isinstance(previous, dict)
        )
        if attempt_index >= len(variants):
            raise AssertionError(f"synthetic authored variants exhausted for {kind}")
        return variants[attempt_index]

    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    monkeypatch.setattr(curriculum, "_check_for_level", check_for_level)
    return curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 3},
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
    )


def _answer(state: dict, value: str) -> tuple[dict, dict]:
    activity = curriculum._current_activity(state)
    assert activity is not None
    return curriculum.apply_curriculum_answer(
        state,
        activity_id=activity["activity_id"],
        answer=value,
    )


def test_independent_success_requires_transfer_before_level_completion(monkeypatch):
    state = _new_state(monkeypatch)
    state, _ = _answer(state, "share")
    assert curriculum._current_activity(state)["kind"] == "independent_check"

    state, independent = _answer(state, "share")
    assert independent["correct"] is True
    assert state["status"] == "active"
    assert state["levels"][0]["status"] == "in_progress"
    assert curriculum._current_activity(state)["kind"] == "transfer_check"
    assert "complete" not in state["last_feedback"]["message"].lower()

    state, transfer = _answer(state, "share")
    assert transfer["correct"] is True
    assert state["status"] == "active"
    assert state["levels"][0]["status"] == "complete"
    assert curriculum._current_activity(state)["kind"] == "chapter_check"


def test_transfer_miss_returns_through_support_to_transfer_not_independent(monkeypatch):
    state = _new_state(monkeypatch)
    state, _ = _answer(state, "share")
    state, _ = _answer(state, "share")
    state, _ = _answer(state, "hide")
    assert curriculum._current_activity(state)["kind"] == "bridge"

    state, _ = _answer(state, "share")
    assert curriculum._current_activity(state)["kind"] == "transfer_check"


def test_bridge_failure_pauses_for_a_linked_masterclass_and_resumes_exact_step(monkeypatch):
    state = _new_state(monkeypatch)
    state, _ = _answer(state, "hide")
    assert curriculum._current_activity(state)["kind"] == "bridge"

    state, _ = _answer(state, "hide")
    assert state["status"] == "paused_for_masterclass"
    assert state["phase"] == "paused_for_masterclass"
    assert state["active_interrupt"]["trigger_count"] == 1
    assert state["active_interrupt"]["return_step"] == "independent_check"
    assert curriculum._current_activity(state) is None

    state = curriculum.resume_after_masterclass(
        state,
        masterclass_session_id="masterclass-1",
        resolution="complete",
    )
    assert state["status"] == "active"
    assert state["phase"] == "learning"
    assert state["active_interrupt"] is None
    assert curriculum._current_activity(state)["kind"] == "independent_check"
    assert state["interrupt_history"][-1]["resolution"] == "complete"
    assert "same lesson step" in state["last_feedback"]["message"].lower()
    assert "chapter check" not in state["last_feedback"]["message"].lower()


def test_abandoned_masterclass_consumes_cap_and_third_trigger_stops_looping(monkeypatch):
    state = _new_state(monkeypatch)
    for trigger_number in (1, 2):
        state, _ = _answer(state, "hide")
        state, _ = _answer(state, "hide")
        assert state["active_interrupt"]["trigger_count"] == trigger_number
        state = curriculum.resume_after_masterclass(
            state,
            masterclass_session_id=f"masterclass-{trigger_number}",
            resolution="abandoned",
        )

    state, _ = _answer(state, "hide")
    state, _ = _answer(state, "hide")
    assert state["phase"] == "capped_support"
    assert state["status"] == "active"
    assert state["active_interrupt"] is None
    assert state["interrupt_history"][-1]["resolution"] == "capped_out"
