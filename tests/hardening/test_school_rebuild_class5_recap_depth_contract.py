from __future__ import annotations

from typing import Any

import pytest

from app.content.school_rebuild_placement_bank import placement_tracks_for
from app.services import school_rebuild_recap as recap
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    RUBRIC_SCHEMA_VERSION,
)


CLASS_5_TRACK_IDS = (
    "english.c5.sentence_detail",
    "english.c5.main_idea",
    "english.c5.inference",
    "english.c5.context_word",
    "english.c5.word_usage",
    "english.c5.tense",
    "english.c5.sentence_order",
    "english.c5.summary",
)

CLASS_2_TRACK_IDS = (
    "english.c2.sentence_detail_place",
    "english.c2.sentence_detail_action",
    "english.c2.context_word",
    "english.c2.word_choice",
    "english.c2.naming_words",
    "english.c2.sentence_order",
    "english.c2.complete_sentence_action",
    "english.c2.complete_sentence_idea",
)

CLASS_3_TRACK_IDS = (
    "english.c3.sentence_detail",
    "english.c3.main_idea",
    "english.c3.reason_inference",
    "english.c3.context_word",
    "english.c3.word_roles",
    "english.c3.past_tense",
    "english.c3.complete_sentence",
    "english.c3.short_answer",
)

CLASS_4_TRACK_IDS = (
    "english.c4.sentence_detail",
    "english.c4.main_idea",
    "english.c4.reason_inference",
    "english.c4.context_word",
    "english.c4.connectors",
    "english.c4.tense",
    "english.c4.summary",
    "english.c4.reason_answer",
)

RECAP_STAGES = (
    "guided_check",
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
    "independent_check",
    "transfer_check",
)

CLASS_2_WRITING_TRACK_IDS = {
    "english.c2.complete_sentence_action",
    "english.c2.complete_sentence_idea",
}

CLASS_2_OPEN_RESPONSE_STAGES = {
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
    "independent_check",
    "transfer_check",
}

CLASS_3_STRICT_RUBRIC_STAGES = {
    "english.c3.reason_inference": {
        "revision_level_3",
        "independent_check",
        "transfer_check",
    },
    "english.c3.complete_sentence": {
        "revision_level_2",
        "revision_level_3",
        "independent_check",
        "transfer_check",
    },
    "english.c3.short_answer": {
        "revision_level_2",
        "revision_level_3",
        "independent_check",
        "transfer_check",
    },
}

CLASS_4_STRICT_RUBRIC_STAGES = {
    "english.c4.reason_inference": {
        "revision_level_3",
        "independent_check",
        "transfer_check",
    },
    "english.c4.summary": {
        "revision_level_2",
        "revision_level_3",
        "independent_check",
        "transfer_check",
    },
    "english.c4.reason_answer": {
        "revision_level_2",
        "revision_level_3",
        "independent_check",
        "transfer_check",
    },
}

AUTHORING_JARGON = {
    "authoring",
    "authored",
    "certification",
    "diagnostic",
    "engine",
    "evaluation",
    "placement",
    "prerequisite",
    "rubric",
}


def _normalized_text(value: Any) -> str:
    return " ".join(str(value).casefold().split())


def _normalized_task(item: Any) -> tuple[str, str]:
    prompt = item["prompt"] if isinstance(item, dict) else item.prompt
    passage = item["passage"] if isinstance(item, dict) else item.passage
    return (
        " ".join(str(prompt).casefold().split()),
        " ".join(str(passage).casefold().split()),
    )


def _state_for(track_id: str) -> dict[str, Any]:
    track = next(
        item
        for item in placement_tracks_for("english", 5)
        if item.track_id == track_id
    )
    return recap.new_recap_state({
        "profile_version_id": "profile-version",
        "report_id": "report-id",
        "placement_session_id": "placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [{
            "module_id": f"recap-{track_id.rsplit('.', 1)[-1]}",
            "title": f"Recap: {track.learner_skill_label}",
            "source_class_no": 4,
            "target_class_no": 5,
            "focus": track.learner_skill_label,
            "placement_track_id": track.track_id,
            "primary_skill_id": track.primary_skill_id,
        }],
    })


def _public_current(state: dict[str, Any]) -> dict[str, Any]:
    return recap.public_recap_response({
        "session_id": "recap-session",
        "status": state["status"],
        "subject_id": "english",
        "class_no": 5,
        "state_json": state,
    })["current_activity"]


def _current_internal(state: dict[str, Any]) -> dict[str, Any]:
    public = _public_current(state)
    return recap.recap_activity_for_answer(
        state,
        activity_id=public["activity_id"],
    )


def _evaluation(activity: dict[str, Any], *, passed: bool) -> dict[str, Any] | None:
    evaluator_activity = recap.evaluator_activity_for_answer(activity)
    if evaluator_activity is None:
        return None
    answer = (
        "The answer is supported because the passage gives a clear clue."
        if passed
        else "wrong"
    )
    return {
        "schema_version": (
            OPEN_RUBRIC_SCHEMA_VERSION
            if evaluator_activity.get("grading_mode") == "strict_open_rubric"
            else RUBRIC_SCHEMA_VERSION
        ),
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
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
            for criterion in evaluator_activity["rubric_criteria"]
        ],
        "misconception_tags": [] if passed else ["recap_gap"],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Evidence recorded.",
    }


def _apply(
    state: dict[str, Any],
    activity: dict[str, Any],
    *,
    passed: bool,
) -> dict[str, Any]:
    answer = (
        (
            activity["accepted_answers"][0]
            if activity.get("accepted_answers")
            else "The answer is supported because the passage gives a clear clue."
        )
        if passed
        else "wrong"
    )
    updated, _ = recap.apply_recap_answer(
        state,
        activity_id=activity["activity_id"],
        answer=answer,
        open_answer_evaluation=_evaluation(activity, passed=passed),
    )
    return updated


def _assert_public_activity_has_no_hidden_grading_fields(
    activity: dict[str, Any],
) -> None:
    assert not {
        "accepted_answers",
        "answer_key",
        "evaluation_mode",
        "rubric",
        "rubric_ref",
        "rubric_criteria",
        "pass_score",
        "source_item_id",
    }.intersection(activity)


def test_every_class5_track_has_eight_fresh_authored_recap_activities() -> None:
    placement_by_track = {
        track.track_id: track for track in placement_tracks_for("english", 5)
    }

    assert set(CLASS_5_TRACK_IDS).issubset(recap.RECAP_TRACK_CHECK_BANK)
    for track_id in CLASS_5_TRACK_IDS:
        checks = recap.RECAP_TRACK_CHECK_BANK[track_id]
        assert tuple(checks) == RECAP_STAGES
        assert len({check["source_item_id"] for check in checks.values()}) == 8
        assert len({
            " ".join(check["prompt"].casefold().split())
            for check in checks.values()
        }) == 8
        assert len({
            " ".join(check["passage"].casefold().split())
            for check in checks.values()
        }) == 8
        assert len({_normalized_task(check) for check in checks.values()}) == 8

        placement_track = placement_by_track[track_id]
        placement_items = [
            placement_track.snapshot_item,
            *(
                item
                for band in placement_track.bands
                for item in band.variants
            ),
        ]
        assert len(placement_items) >= 6
        placement_tasks = {_normalized_task(item) for item in placement_items}
        assert not placement_tasks.intersection(
            _normalized_task(check) for check in checks.values()
        )


@pytest.mark.parametrize("track_id", CLASS_5_TRACK_IDS)
def test_class5_wrong_answers_open_fresh_support_then_valid_checks_complete(
    track_id: str,
) -> None:
    state = _state_for(track_id)
    visible_tasks: list[tuple[str, str]] = []

    activity = _current_internal(state)
    assert activity["kind"] == "guided_check"
    visible_tasks.append(_normalized_task(activity))
    _assert_public_activity_has_no_hidden_grading_fields(_public_current(state))

    for expected_kind in ("bridge", "masterclass", "revision_level_1"):
        state = _apply(state, activity, passed=False)
        activity = _current_internal(state)
        assert activity["kind"] == expected_kind
        visible_tasks.append(_normalized_task(activity))
        _assert_public_activity_has_no_hidden_grading_fields(_public_current(state))

    for expected_kind in (
        "revision_level_2",
        "revision_level_3",
        "independent_check",
    ):
        state = _apply(state, activity, passed=True)
        activity = _current_internal(state)
        assert activity["kind"] == expected_kind
        visible_tasks.append(_normalized_task(activity))
        _assert_public_activity_has_no_hidden_grading_fields(_public_current(state))

    assert len(set(visible_tasks)) == len(visible_tasks)

    public_independent = recap.public_recap_response({
        "session_id": "recap-session",
        "status": state["status"],
        "subject_id": "english",
        "class_no": 5,
        "state_json": state,
    })["current_activity"]
    _assert_public_activity_has_no_hidden_grading_fields(public_independent)

    state = _apply(state, activity, passed=True)
    transfer = _current_internal(state)
    assert transfer["kind"] == "transfer_check"
    assert _normalized_task(transfer) not in visible_tasks

    public_transfer = recap.public_recap_response({
        "session_id": "recap-session",
        "status": state["status"],
        "subject_id": "english",
        "class_no": 5,
        "state_json": state,
    })["current_activity"]
    _assert_public_activity_has_no_hidden_grading_fields(public_transfer)

    state = _apply(state, transfer, passed=True)
    assert state["status"] == "complete"
    assert state["modules"][0]["status"] == "complete"


def test_class5_track_without_a_deep_authored_sequence_fails_hard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shallow_bank = dict(recap.RECAP_TRACK_CHECK_BANK)
    shallow_bank.pop("english.c5.summary", None)
    monkeypatch.setattr(recap, "RECAP_TRACK_CHECK_BANK", shallow_bank)

    with pytest.raises(ValueError, match="recap_content_not_authored"):
        recap._checks_for_track(
            subject_id="english",
            target_class_no=5,
            track_id="english.c5.summary",
            source_class_no=4,
        )


def test_class5_shallow_authored_sequence_fails_hard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shallow_bank = dict(recap.RECAP_TRACK_CHECK_BANK)
    shallow_summary = {
        stage: dict(check)
        for stage, check in shallow_bank["english.c5.summary"].items()
    }
    shallow_summary["masterclass"] = dict(shallow_summary["bridge"])
    shallow_bank["english.c5.summary"] = shallow_summary
    monkeypatch.setattr(recap, "RECAP_TRACK_CHECK_BANK", shallow_bank)

    with pytest.raises(ValueError, match="recap_content_not_authored"):
        recap._checks_for_track(
            subject_id="english",
            target_class_no=5,
            track_id="english.c5.summary",
            source_class_no=4,
        )


def test_every_class2_track_has_a_fresh_progressive_authored_sequence() -> None:
    placement_by_track = {
        track.track_id: track for track in placement_tracks_for("english", 2)
    }
    all_source_item_ids: set[str] = set()
    all_task_pairs: set[tuple[str, str]] = set()

    assert set(CLASS_2_TRACK_IDS) == set(placement_by_track)
    assert set(CLASS_2_TRACK_IDS).issubset(recap.RECAP_TRACK_CHECK_BANK)

    for track_id in CLASS_2_TRACK_IDS:
        checks = recap._checks_for_track(
            subject_id="english",
            target_class_no=2,
            track_id=track_id,
            source_class_no=1,
        )

        assert tuple(checks) == RECAP_STAGES
        assert tuple(check["source_class_no"] for check in checks.values()) == (
            1,
            1,
            1,
            1,
            2,
            2,
            2,
            2,
        )
        assert len({check["source_item_id"] for check in checks.values()}) == 8
        assert len({_normalized_text(check["prompt"]) for check in checks.values()}) == 8
        assert len({_normalized_text(check["passage"]) for check in checks.values()}) == 8
        assert len({_normalized_task(check) for check in checks.values()}) == 8

        placement_track = placement_by_track[track_id]
        placement_items = [
            placement_track.snapshot_item,
            *(item for band in placement_track.bands for item in band.variants),
        ]
        placement_tasks = {_normalized_task(item) for item in placement_items}
        assert not placement_tasks.intersection(
            _normalized_task(check) for check in checks.values()
        )

        for stage, check in checks.items():
            source_item_id = check["source_item_id"]
            task_pair = _normalized_task(check)
            assert source_item_id not in all_source_item_ids
            assert task_pair not in all_task_pairs
            all_source_item_ids.add(source_item_id)
            all_task_pairs.add(task_pair)

            child_copy = f"{check['passage']} {check['prompt']}".casefold()
            assert not any(term in child_copy for term in AUTHORING_JARGON)
            assert len(str(check["passage"]).split()) <= 28
            assert len(str(check["prompt"]).split()) <= 18

            needs_open_response = (
                track_id in CLASS_2_WRITING_TRACK_IDS
                and stage in CLASS_2_OPEN_RESPONSE_STAGES
            )
            if needs_open_response:
                assert check["evaluation_mode"] == "strict_rubric"
                assert check["rubric_ref"]
                assert check["accepted_answers"] == []
            else:
                assert check["evaluation_mode"] == "deterministic"
                assert check["rubric_ref"] is None
                assert check["accepted_answers"]
                if check["options"]:
                    normalized_options = {
                        _normalized_text(option) for option in check["options"]
                    }
                    assert _normalized_text(check["accepted_answers"][0]) in normalized_options

    assert len(all_source_item_ids) == 64
    assert len(all_task_pairs) == 64


def test_missing_class2_authored_track_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authored_bank = dict(recap.RECAP_TRACK_CHECK_BANK)
    authored_bank.pop("english.c2.complete_sentence_idea", None)
    monkeypatch.setattr(recap, "RECAP_TRACK_CHECK_BANK", authored_bank)

    with pytest.raises(ValueError, match="recap_content_not_authored"):
        recap._checks_for_track(
            subject_id="english",
            target_class_no=2,
            track_id="english.c2.complete_sentence_idea",
            source_class_no=1,
        )


def test_every_class3_track_has_a_fresh_progressive_authored_sequence() -> None:
    placement_tracks = placement_tracks_for("english", 3)
    placement_by_track = {track.track_id: track for track in placement_tracks}
    placement_tasks = {
        _normalized_task(item)
        for track in placement_tracks
        for item in (
            track.snapshot_item,
            *(item for band in track.bands for item in band.variants),
        )
    }
    all_source_item_ids: set[str] = set()
    all_task_pairs: set[tuple[str, str]] = set()

    assert set(CLASS_3_TRACK_IDS) == set(placement_by_track)
    assert set(CLASS_3_TRACK_IDS).issubset(recap.RECAP_TRACK_CHECK_BANK)

    for track_id in CLASS_3_TRACK_IDS:
        checks = recap._checks_for_track(
            subject_id="english",
            target_class_no=3,
            track_id=track_id,
            source_class_no=2,
        )

        assert tuple(checks) == RECAP_STAGES
        assert tuple(check["source_class_no"] for check in checks.values()) == (
            1,
            1,
            2,
            2,
            3,
            3,
            3,
            3,
        )
        assert len({check["source_item_id"] for check in checks.values()}) == 8
        assert len({_normalized_text(check["prompt"]) for check in checks.values()}) == 8
        assert len({_normalized_text(check["passage"]) for check in checks.values()}) == 8
        assert len({_normalized_task(check) for check in checks.values()}) == 8
        assert not placement_tasks.intersection(
            _normalized_task(check) for check in checks.values()
        )

        strict_rubric_stages = CLASS_3_STRICT_RUBRIC_STAGES.get(track_id, set())
        for stage, check in checks.items():
            source_item_id = check["source_item_id"]
            task_pair = _normalized_task(check)
            assert source_item_id not in all_source_item_ids
            assert task_pair not in all_task_pairs
            all_source_item_ids.add(source_item_id)
            all_task_pairs.add(task_pair)

            child_copy = f"{check['passage']} {check['prompt']}".casefold()
            assert not any(term in child_copy for term in AUTHORING_JARGON)
            assert len(str(check["passage"]).split()) <= 40
            assert len(str(check["prompt"]).split()) <= 20

            if stage in strict_rubric_stages:
                assert check["evaluation_mode"] == "strict_rubric"
                assert check["rubric_ref"]
                assert check["accepted_answers"] == []
                assert check["options"] == []
            else:
                assert check["evaluation_mode"] == "deterministic"
                assert check["rubric_ref"] is None
                assert check["accepted_answers"]
                if check["options"]:
                    normalized_options = {
                        _normalized_text(option) for option in check["options"]
                    }
                    assert _normalized_text(check["accepted_answers"][0]) in normalized_options

    assert len(all_source_item_ids) == 64
    assert len(all_task_pairs) == 64


def test_missing_class3_authored_track_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authored_bank = dict(recap.RECAP_TRACK_CHECK_BANK)
    authored_bank.pop("english.c3.short_answer", None)
    monkeypatch.setattr(recap, "RECAP_TRACK_CHECK_BANK", authored_bank)

    with pytest.raises(ValueError, match="recap_content_not_authored"):
        recap._checks_for_track(
            subject_id="english",
            target_class_no=3,
            track_id="english.c3.short_answer",
            source_class_no=2,
        )


def test_every_class4_track_has_a_fresh_progressive_authored_sequence() -> None:
    placement_tracks = placement_tracks_for("english", 4)
    placement_by_track = {track.track_id: track for track in placement_tracks}
    placement_tasks = {
        _normalized_task(item)
        for track in placement_tracks
        for item in (
            track.snapshot_item,
            *(item for band in track.bands for item in band.variants),
        )
    }
    all_source_item_ids: set[str] = set()
    all_task_pairs: set[tuple[str, str]] = set()

    assert set(CLASS_4_TRACK_IDS) == set(placement_by_track)
    assert set(CLASS_4_TRACK_IDS).issubset(recap.RECAP_TRACK_CHECK_BANK)

    for track_id in CLASS_4_TRACK_IDS:
        checks = recap._checks_for_track(
            subject_id="english",
            target_class_no=4,
            track_id=track_id,
            source_class_no=3,
        )

        assert tuple(checks) == RECAP_STAGES
        assert tuple(check["source_class_no"] for check in checks.values()) == (
            2,
            2,
            3,
            3,
            4,
            4,
            4,
            4,
        )
        assert len({check["source_item_id"] for check in checks.values()}) == 8
        assert len({_normalized_text(check["prompt"]) for check in checks.values()}) == 8
        assert len({_normalized_text(check["passage"]) for check in checks.values()}) == 8
        assert len({_normalized_task(check) for check in checks.values()}) == 8
        assert not placement_tasks.intersection(
            _normalized_task(check) for check in checks.values()
        )

        strict_rubric_stages = CLASS_4_STRICT_RUBRIC_STAGES.get(track_id, set())
        for stage, check in checks.items():
            source_item_id = check["source_item_id"]
            task_pair = _normalized_task(check)
            assert source_item_id not in all_source_item_ids
            assert task_pair not in all_task_pairs
            all_source_item_ids.add(source_item_id)
            all_task_pairs.add(task_pair)

            child_copy = f"{check['passage']} {check['prompt']}".casefold()
            assert not any(term in child_copy for term in AUTHORING_JARGON)
            assert len(str(check["passage"]).split()) <= 46
            assert len(str(check["prompt"]).split()) <= 22

            if stage in strict_rubric_stages:
                assert check["evaluation_mode"] == "strict_rubric"
                assert check["rubric_ref"]
                assert check["accepted_answers"] == []
                assert check["options"] == []
            else:
                assert check["evaluation_mode"] == "deterministic"
                assert check["rubric_ref"] is None
                assert check["accepted_answers"]
                if check["options"]:
                    normalized_options = {
                        _normalized_text(option) for option in check["options"]
                    }
                    assert _normalized_text(check["accepted_answers"][0]) in normalized_options

    assert len(all_source_item_ids) == 64
    assert len(all_task_pairs) == 64


def test_missing_class4_authored_track_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authored_bank = dict(recap.RECAP_TRACK_CHECK_BANK)
    authored_bank.pop("english.c4.reason_answer", None)
    monkeypatch.setattr(recap, "RECAP_TRACK_CHECK_BANK", authored_bank)

    with pytest.raises(ValueError, match="recap_content_not_authored"):
        recap._checks_for_track(
            subject_id="english",
            target_class_no=4,
            track_id="english.c4.reason_answer",
            source_class_no=3,
        )
