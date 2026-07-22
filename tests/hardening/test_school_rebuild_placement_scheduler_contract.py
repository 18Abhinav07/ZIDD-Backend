from dataclasses import replace

import pytest

from app.content.school_rebuild_placement_bank import (
    PLACEMENT_TRACKS_BY_CLASS,
    PlacementBand,
    placement_tracks_for,
)
from app.content.school_rebuild_placement_validation import (
    PlacementBankValidationError,
    validate_placement_bank,
)
from app.services import school_rebuild_placement as placement


def _profile(class_no: int = 5) -> dict:
    return {
        "profile_version_id": "scheduler-contract-profile",
        "target_class_no": class_no,
        "subject_ids": ["english"],
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    }


def _answer(
    envelope: placement.PlacementEnvelope,
    score: float,
    *,
    learner_seconds: int = 0,
    evaluator_seconds: int = 0,
) -> placement.PlacementEnvelope:
    item = placement.next_item(envelope)
    assert item is not None
    return placement.apply_evaluated_attempt(
        envelope,
        item,
        evaluator_score=score,
        evaluator_confidence=1.0,
        elapsed_seconds_delta=learner_seconds,
        evaluator_wait_seconds_delta=evaluator_seconds,
    )


def _finish_snapshots(
    envelope: placement.PlacementEnvelope,
    *,
    exceptional_track_id: str,
    exceptional_score: float,
) -> placement.PlacementEnvelope:
    while envelope.state.stage == "snapshot" and placement.next_item(envelope):
        item = placement.next_item(envelope)
        score = exceptional_score if item.track_id == exceptional_track_id else 1.0
        envelope = _answer(envelope, score)
    return envelope


def _class_five_inference_track():
    return next(
        track
        for track in placement_tracks_for("english", 5)
        if track.track_id == "english.c5.inference"
    )


def _two_class_two_contradictions() -> placement.PlacementEnvelope:
    envelope = placement.new_placement_envelope(_profile(class_no=2))
    contradicted_track_ids = tuple(envelope.state.track_states)[:2]
    while envelope.state.stage == "snapshot":
        item = placement.next_item(envelope)
        assert item is not None
        envelope = _answer(
            envelope,
            0.0 if item.track_id in contradicted_track_ids else 1.0,
        )
    while envelope.state.stage == "targeted_diagnostic":
        item = placement.next_item(envelope)
        assert item is not None
        assert item.track_id in contradicted_track_ids
        envelope = _answer(envelope, 1.0)
    assert envelope.state.stage == "confirmatory"
    assert envelope.state.confirmatory_track_ids == contradicted_track_ids
    return envelope


def test_scheduler_preflight_covers_all_class_two_to_five_tracks():
    assert placement.preflight_placement_track_plans(PLACEMENT_TRACKS_BY_CLASS) is True


def test_placement_validator_rejects_an_invented_class_two_v06_item_id():
    original_track = PLACEMENT_TRACKS_BY_CLASS[2][0]
    mutated_snapshot = replace(
        original_track.snapshot_item,
        item_id="spv_c02_t01_v06",
    )
    mutated_track = replace(original_track, snapshot_item=mutated_snapshot)
    mutated_plans = dict(PLACEMENT_TRACKS_BY_CLASS)
    mutated_plans[2] = tuple(
        mutated_track if track.track_id == original_track.track_id else track
        for track in mutated_plans[2]
    )

    with pytest.raises(PlacementBankValidationError, match="opaque stable ID"):
        validate_placement_bank(mutated_plans)


def test_scheduler_preflight_rejects_reachable_missing_target_confirmation():
    inference = _class_five_inference_track()
    target_band = next(
        band for band in inference.bands if band.source_class_no == 5
    )
    broken_band = PlacementBand(
        source_class_no=5,
        variants=tuple(
            item for item in target_band.variants if item.stage != "confirmatory"
        ),
    )
    broken_track = replace(
        inference,
        bands=tuple(
            broken_band if band.source_class_no == 5 else band
            for band in inference.bands
        ),
    )
    plans = dict(PLACEMENT_TRACKS_BY_CLASS)
    plans[5] = tuple(
        broken_track if track.track_id == inference.track_id else track
        for track in plans[5]
    )

    with pytest.raises(
        ValueError,
        match=(
            "placement_preflight_missing_confirmatory_item:"
            "english.c5.inference:5"
        ),
    ):
        placement.preflight_placement_track_plans(plans)


def test_class_five_ambiguous_inference_requires_more_evidence_without_unlock():
    inference = _class_five_inference_track()
    envelope = _finish_snapshots(
        placement.new_placement_envelope(_profile()),
        exceptional_track_id=inference.track_id,
        exceptional_score=0.70,
    )

    target_probe = placement.next_item(envelope)
    assert target_probe.track_id == inference.track_id
    assert target_probe.stage == "targeted_diagnostic"
    assert target_probe.source_class_no == 5
    envelope = _answer(envelope, 1.0)

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert envelope.state.total_items == 9
    assert envelope.state.confirmatory_track_ids == ()
    assert envelope.state.track_states[inference.track_id].status == "unresolved"
    assert placement.next_item(envelope) is None


def test_same_band_contradictions_are_the_only_stage_three_trigger():
    envelope = _two_class_two_contradictions()

    assert placement.placement_status(envelope) == "in_progress"
    assert envelope.state.total_items == 10
    assert all(
        track.unresolved_reason == "contradictory_evidence"
        for track in (
            envelope.state.track_states[track_id]
            for track_id in envelope.state.confirmatory_track_ids
        )
    )


def test_total_question_budget_is_the_sum_of_the_three_bounded_stages():
    assert placement.MAX_SNAPSHOT_ITEMS == 8
    assert placement.MAX_TARGETED_DIAGNOSTIC_ITEMS == 4
    assert placement.MAX_CONFIRMATORY_ITEMS == 2
    assert placement.MAX_PLACEMENT_ITEMS == 14


def test_snapshot_learner_budget_moves_to_targeted_without_losing_evidence():
    envelope = placement.new_placement_envelope(_profile())
    item = placement.next_item(envelope)
    assert item is not None

    envelope = _answer(
        envelope,
        0.70,
        learner_seconds=placement.SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert placement.placement_status(envelope) == "in_progress"
    assert envelope.state.stage == "targeted_diagnostic"
    assert envelope.state.total_items == 1
    assert len(envelope.state.answered_item_ids) == 1
    assert envelope.state.stage_elapsed_seconds == 0
    assert placement.next_item(envelope).stage == "targeted_diagnostic"
    assert envelope.state.pending_track_ids == (item.track_id,)
    assert all(
        track.status == "unresolved"
        for track_id, track in envelope.state.track_states.items()
        if track_id != item.track_id
    )


def test_snapshot_timeout_resume_restores_unused_snapshot_checks_before_later_stages():
    envelope = placement.new_placement_envelope(_profile())
    first_item = placement.next_item(envelope)
    assert first_item is not None

    envelope = _answer(
        envelope,
        1.0,
        learner_seconds=placement.SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert placement.can_resume_placement(envelope) is True
    assert all(
        track.status == "unresolved"
        and track.unresolved_reason == "snapshot_budget_unanswered"
        for track_id, track in envelope.state.track_states.items()
        if track_id != first_item.track_id
    )

    resumed = placement.resume_placement(envelope)

    assert resumed.state.stage == "snapshot"
    assert resumed.state.track_states[first_item.track_id].status == "provisional_ready"
    next_snapshot = placement.next_item(resumed)
    assert next_snapshot is not None
    assert next_snapshot.item_id != first_item.item_id
    assert next_snapshot.stage == "snapshot"

    while placement.placement_status(resumed) == "in_progress":
        item = placement.next_item(resumed)
        assert item is not None
        assert item.stage == "snapshot"
        resumed = _answer(resumed, 1.0)

    assert placement.placement_status(resumed) == "target_ready"
    assert resumed.state.total_items == placement.MAX_SNAPSHOT_ITEMS
    assert set(resumed.state.answered_item_ids) == {
        track.snapshot_item.item_id
        for track in placement_tracks_for("english", 5)
    }
    assert all(
        track.unresolved_reason is None
        for track in resumed.state.track_states.values()
    )


def test_targeted_learner_budget_requires_more_evidence_without_unlock():
    inference = _class_five_inference_track()
    envelope = _finish_snapshots(
        placement.new_placement_envelope(_profile()),
        exceptional_track_id=inference.track_id,
        exceptional_score=0.70,
    )

    envelope = _answer(
        envelope,
        0.0,
        learner_seconds=placement.TARGETED_DIAGNOSTIC_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert (
        envelope.state.terminal_reason
        == "watchlist_after_targeted_diagnostic_learner_time_budget_exhausted"
    )
    assert envelope.state.confirmatory_track_ids == ()
    assert placement.next_item(envelope) is None
    assert envelope.state.readiness_seeds_applied is False
    assert envelope.state.track_states[inference.track_id].status == "unresolved"


def test_targeted_learner_budget_reason_is_preserved_on_the_watchlist_track():
    inference = _class_five_inference_track()
    envelope = _finish_snapshots(
        placement.new_placement_envelope(_profile()),
        exceptional_track_id=inference.track_id,
        exceptional_score=0.70,
    )

    envelope = _answer(
        envelope,
        0.0,
        learner_seconds=placement.TARGETED_DIAGNOSTIC_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert (
        envelope.state.track_states[inference.track_id].unresolved_reason
        == "targeted_diagnostic_learner_time_budget_exhausted"
    )


def test_targeted_resolving_answer_at_exact_stage_boundary_is_honored():
    inference = _class_five_inference_track()
    envelope = _finish_snapshots(
        placement.new_placement_envelope(_profile()),
        exceptional_track_id=inference.track_id,
        exceptional_score=0.70,
    )
    item = placement.next_item(envelope)
    assert item is not None

    envelope = _answer(
        envelope,
        1.0,
        learner_seconds=placement.TARGETED_DIAGNOSTIC_LEARNER_TIME_BUDGET_SECONDS,
    )

    evidence = envelope.state.track_states[inference.track_id].evidence
    assert evidence[-1].item_id == item.item_id
    assert evidence[-1].classification == "pass"
    assert item.item_id in envelope.state.answered_item_ids
    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert envelope.state.terminal_reason == "nonblocking_uncertainty_watchlist"
    assert placement.next_item(envelope) is None


def test_confirmatory_budget_keeps_duration_truthful_and_requires_more_evidence():
    envelope = _two_class_two_contradictions()

    envelope = _answer(
        envelope,
        0.70,
        learner_seconds=placement.CONFIRMATORY_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert (
        envelope.state.terminal_reason
        == "watchlist_after_confirmatory_learner_time_budget_exhausted"
    )
    assert envelope.state.elapsed_seconds == (
        placement.CONFIRMATORY_LEARNER_TIME_BUDGET_SECONDS
    )
    assert placement.next_item(envelope) is None
    assert placement.can_resume_placement(envelope) is True


def test_confirmatory_resolving_answer_at_exact_stage_boundary_is_honored():
    envelope = _two_class_two_contradictions()
    item = placement.next_item(envelope)
    assert item is not None
    track_id = item.track_id

    envelope = _answer(
        envelope,
        1.0,
        learner_seconds=placement.CONFIRMATORY_LEARNER_TIME_BUDGET_SECONDS,
    )

    evidence = envelope.state.track_states[track_id].evidence
    assert evidence[-1].item_id == item.item_id
    assert evidence[-1].classification == "pass"
    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert (
        envelope.state.terminal_reason
        == "watchlist_after_confirmatory_learner_time_budget_exhausted"
    )


def test_outer_learner_budget_is_independent_and_named():
    envelope = placement.new_placement_envelope(_profile())
    first_item = placement.next_item(envelope)
    assert first_item is not None
    envelope = replace(
        envelope,
        state=replace(
            envelope.state,
            elapsed_seconds=placement.PLACEMENT_LEARNER_TIME_BUDGET_SECONDS,
        ),
    )

    envelope = _answer(envelope, 0.70)

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert (
        envelope.state.terminal_reason
        == "watchlist_after_placement_learner_time_budget_exhausted"
    )
    assert placement.can_resume_placement(envelope) is True
    assert placement.next_item(envelope) is None

    resumed = placement.resume_placement(envelope)

    assert resumed.state.sitting_elapsed_seconds == 0.0
    assert resumed.state.answered_item_ids == envelope.state.answered_item_ids
    assert placement.next_item(resumed) is not None
    assert placement.next_item(resumed).item_id != first_item.item_id


def test_resolving_snapshot_answer_at_exact_stage_boundary_is_honored():
    envelope = placement.new_placement_envelope(_profile())
    while (
        placement.placement_status(envelope) == "in_progress"
        and envelope.state.stage == "snapshot"
    ):
        item = placement.next_item(envelope)
        assert item is not None
        is_last_snapshot = all(
            track.track_id == item.track_id or track.status != "pending"
            for track in envelope.state.track_states.values()
        )
        envelope = _answer(
            envelope,
            1.0,
            learner_seconds=(
                placement.SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS
                if is_last_snapshot
                else 0
            ),
        )

    assert placement.placement_status(envelope) == "target_ready"
    assert envelope.state.readiness_seeds_applied is True


def test_low_score_with_moderate_confidence_is_a_clear_fail():
    assert placement.classify_placement_evidence(
        evaluator_score=0.59,
        evaluator_confidence=0.70,
    ) == "fail"
    assert placement.classify_placement_evidence(
        evaluator_score=0.59,
        evaluator_confidence=0.74,
    ) == "fail"


def test_consistently_weak_moderate_confidence_profile_resolves_below_target():
    envelope = placement.new_placement_envelope(_profile())
    for _ in range(placement.MAX_PLACEMENT_ITEMS):
        item = placement.next_item(envelope)
        if item is None:
            break
        envelope = placement.apply_evaluated_attempt(
            envelope,
            item,
            evaluator_score=0.40,
            evaluator_confidence=0.72,
        )

    assert placement.placement_status(envelope) == "below_target"
    assert envelope.state.terminal_reason == "authored_floor_rebuild_required"


def test_public_track_verdicts_are_complete_and_contain_no_item_authority():
    envelope = _answer(
        placement.new_placement_envelope(_profile()),
        0.0,
    )

    response = placement.placement_response(
        session_id="placement-contract",
        envelope=envelope,
    )
    verdict = next(
        row
        for row in response["track_verdicts"]
        if row["track_id"] == next(iter(envelope.state.track_states))
    )

    assert set(verdict) == {
        "track_id",
        "skill_ids",
        "evidence_count",
        "highest_clear_pass_band",
        "lowest_clear_fail_band",
        "confidence",
        "status",
        "unresolved_reason",
    }
    assert verdict["evidence_count"] == 1
    assert verdict["highest_clear_pass_band"] is None
    assert verdict["lowest_clear_fail_band"] is not None
    assert "answer_key" not in repr(response)
    assert "accepted_answers" not in repr(response)


def test_public_mcq_options_are_session_stable_without_a_fixed_key_position():
    profile = _profile(class_no=3)
    profile["prior_difficulty_signals"] = ["vocabulary"]
    envelope = placement.new_placement_envelope(profile)
    item = placement.next_item(envelope)
    assert item is not None
    assert item.item_type == "multiple_choice"
    assert item.answer_key is not None

    first = placement.placement_response(
        session_id="placement-options-0",
        envelope=envelope,
    )["next_item"]["options"]
    hydrated = placement.placement_response(
        session_id="placement-options-0",
        envelope=envelope,
    )["next_item"]["options"]

    assert hydrated == first
    key_positions = {
        placement.placement_response(
            session_id=f"placement-options-{index}",
            envelope=envelope,
        )["next_item"]["options"].index(item.answer_key)
        for index in range(32)
    }
    assert len(key_positions) > 1
    assert key_positions != {0}


def test_fractional_learner_time_is_not_floored_before_hard_budget_checks():
    envelope = placement.new_placement_envelope(_profile())
    intervals = [29.99] * 7 + [30.20]

    for learner_seconds in intervals:
        envelope = _answer(
            envelope,
            0.70,
            learner_seconds=learner_seconds,
        )

    assert sum(intervals) > placement.SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS
    assert envelope.state.elapsed_seconds == pytest.approx(sum(intervals))
    assert placement.placement_status(envelope) == "in_progress"
    assert envelope.state.stage == "targeted_diagnostic"
    assert envelope.state.stage_elapsed_seconds == 0


def test_fractional_learner_time_round_trips_without_precision_loss():
    envelope = placement.new_placement_envelope(_profile())
    envelope = _answer(envelope, 0.70, learner_seconds=1.875)

    restored = placement.envelope_from_json(placement.envelope_to_json(envelope))

    assert restored.state.elapsed_seconds == pytest.approx(1.875)
    assert restored.state.stage_elapsed_seconds == pytest.approx(1.875)
    evidence = next(iter(restored.state.track_states.values())).evidence
    assert evidence[0].elapsed_seconds == pytest.approx(1.875)


def test_evaluator_wait_never_consumes_learner_time_budget():
    envelope = placement.new_placement_envelope(_profile())

    envelope = _answer(
        envelope,
        1.0,
        evaluator_seconds=placement.PLACEMENT_LEARNER_TIME_BUDGET_SECONDS + 1,
    )

    assert placement.placement_status(envelope) == "in_progress"
    assert envelope.state.elapsed_seconds == 0
    assert envelope.state.stage_elapsed_seconds == 0
    assert (
        envelope.state.evaluator_wait_seconds
        == placement.PLACEMENT_LEARNER_TIME_BUDGET_SECONDS + 1
    )


def test_unscorable_attempt_consumes_stage_time_without_scoring_the_item():
    envelope = placement.new_placement_envelope(_profile())
    item = placement.next_item(envelope)
    assert item is not None

    envelope = placement.apply_evaluated_attempt(
        envelope,
        item,
        evaluator_score=0.0,
        evaluator_confidence=0.0,
        scorable=False,
        elapsed_seconds_delta=placement.SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert envelope.state.unscorable_attempts == 1
    assert envelope.state.total_items == 0
    assert envelope.state.scorable_answers == 0
    assert envelope.state.answered_item_ids == ()
    assert envelope.state.elapsed_seconds == placement.SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS
    assert envelope.state.stage_elapsed_seconds == 0
    assert placement.next_item(envelope) is None


def test_unscorable_attempt_cannot_bypass_the_outer_learner_budget():
    envelope = placement.new_placement_envelope(_profile())
    item = placement.next_item(envelope)
    assert item is not None

    envelope = placement.apply_evaluated_attempt(
        envelope,
        item,
        evaluator_score=0.0,
        evaluator_confidence=0.0,
        scorable=False,
        elapsed_seconds_delta=placement.PLACEMENT_LEARNER_TIME_BUDGET_SECONDS,
    )

    assert placement.placement_status(envelope) == "insufficient_evidence"
    assert (
        envelope.state.terminal_reason
        == "watchlist_after_placement_learner_time_budget_exhausted"
    )
    assert envelope.state.unscorable_attempts == 1
    assert envelope.state.total_items == 0
    assert envelope.state.answered_item_ids == ()
    assert placement.next_item(envelope) is None


def test_resume_insufficient_evidence_preserves_attempts_and_schedules_fresh_item():
    envelope = _answer(placement.new_placement_envelope(_profile()), 0.70)
    interrupted = replace(
        envelope,
        state=replace(
            envelope.state,
            terminal_status="insufficient_evidence",
            terminal_reason="required_tracks_unresolved",
        ),
    )
    track_id = next(iter(interrupted.state.track_states))
    evidence_before = interrupted.state.track_states[track_id].evidence
    answered_before = interrupted.state.answered_item_ids

    resumed = placement.resume_placement(interrupted)

    assert placement.placement_status(resumed) == "in_progress"
    assert resumed.state.answered_item_ids == answered_before
    assert resumed.state.track_states[track_id].evidence == evidence_before
    assert resumed.state.total_items == interrupted.state.total_items
    assert placement.next_item(resumed).item_id not in answered_before
    assert placement.next_item(resumed).track_id != track_id


def test_resume_rejects_legacy_insufficient_evidence_at_the_question_budget():
    envelope = _answer(placement.new_placement_envelope(_profile()), 0.70)
    terminal = replace(
        envelope,
        state=replace(
            envelope.state,
            total_items=placement.MAX_PLACEMENT_ITEMS,
            terminal_status="insufficient_evidence",
            terminal_reason="required_tracks_unresolved",
        ),
    )

    with pytest.raises(ValueError, match="placement_resume_evidence_unavailable"):
        placement.resume_placement(terminal)


def test_abandoned_terminal_status_survives_serialization():
    abandoned = placement.abandon_placement(
        placement.new_placement_envelope(_profile())
    )

    restored = placement.envelope_from_json(placement.envelope_to_json(abandoned))

    assert restored.state.terminal_status == "abandoned"
    assert placement.placement_status(restored) == "abandoned"
