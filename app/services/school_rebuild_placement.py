"""Canonical per-track placement runtime for the rebuilt `/school` surface."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from types import MappingProxyType
from typing import Any, Literal

from app.config import get_jwt_secret
from app.content.school_rebuild_placement_bank import (
    PLACEMENT_TRACKS_BY_CLASS,
    SIGNAL_SKILL_PRIORITY,
    PlacementTrack,
    SchoolPlacementBankItem,
    placement_tracks_for,
    public_placement_item,
)
from app.services.school_rebuild_placement_evaluator import (
    deterministic_placement_answer_matches,
)
from app.services.school_core.readiness import (
    AttemptEvidence,
    SkillReadinessState,
    apply_attempt_evidence,
    apply_placement_ready_seed,
)


ENGINE_VERSION = "school-rebuild-placement-2"
LEGACY_ENGINE_VERSION = "school-rebuild-placement-1"
MAX_SNAPSHOT_ITEMS = 8
MAX_TARGETED_DIAGNOSTIC_ITEMS = 4
MAX_CONFIRMATORY_ITEMS = 2
MAX_PLACEMENT_ITEMS = (
    MAX_SNAPSHOT_ITEMS
    + MAX_TARGETED_DIAGNOSTIC_ITEMS
    + MAX_CONFIRMATORY_ITEMS
)
MIN_SCORABLE_FOR_TERMINAL_PLACEMENT = 8
SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS = 240
TARGETED_DIAGNOSTIC_LEARNER_TIME_BUDGET_SECONDS = 300
CONFIRMATORY_LEARNER_TIME_BUDGET_SECONDS = 180
PLACEMENT_LEARNER_TIME_BUDGET_SECONDS = 720
PRIVATE_PLACEMENT_TIMING_KEY = "_placement_item_timing"

PlacementStage = Literal["snapshot", "targeted_diagnostic", "confirmatory"]
PlacementClassification = Literal["pass", "fail", "ambiguous", "unscorable"]
PlacementTrackStatus = Literal[
    "pending",
    "provisional_ready",
    "provisional_weak",
    "ambiguous",
    "resolved_ready",
    "confirmed_weak",
    "unresolved",
]
PlacementTerminalStatus = Literal[
    "target_ready",
    "below_target",
    "insufficient_evidence",
    "abandoned",
]


@dataclass(frozen=True)
class PlacementAttemptEvidence:
    item_id: str
    track_id: str
    primary_skill_id: str
    source_class_no: int
    stage: PlacementStage
    classification: PlacementClassification
    evaluator_score: float
    evaluator_confidence: float
    certifying_blockers: tuple[str, ...] = ()
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class PlacementTrackState:
    track_id: str
    primary_skill_id: str
    learner_skill_label: str
    snapshot_item_id: str
    snapshot_source_band: int
    authored_bands: tuple[int, ...]
    status: PlacementTrackStatus = "pending"
    evidence: tuple[PlacementAttemptEvidence, ...] = ()
    highest_passed_band: int | None = None
    first_failed_band: int | None = None
    boundary_band: int | None = None
    unresolved_reason: str | None = None


@dataclass(frozen=True)
class PlacementSessionState:
    subject_id: str
    class_no: int
    stage: PlacementStage = "snapshot"
    track_states: Mapping[str, PlacementTrackState] = field(
        default_factory=lambda: MappingProxyType({})
    )
    skill_states: Mapping[str, SkillReadinessState] = field(
        default_factory=lambda: MappingProxyType({})
    )
    answered_item_ids: tuple[str, ...] = ()
    total_items: int = 0
    scorable_answers: int = 0
    unscorable_attempts: int = 0
    elapsed_seconds: float = 0.0
    sitting_elapsed_seconds: float | None = None
    evaluator_wait_seconds: int = 0
    stage_items: int = 0
    stage_elapsed_seconds: float = 0.0
    pending_track_ids: tuple[str, ...] = ()
    confirmatory_track_ids: tuple[str, ...] = ()
    terminal_status: PlacementTerminalStatus | None = None
    terminal_reason: str | None = None
    readiness_seeds_applied: bool = False

    @property
    def required_skill_ids(self) -> tuple[str, ...]:
        return tuple(track.primary_skill_id for track in self.track_states.values())

    @property
    def targeted_skill_ids(self) -> tuple[str, ...]:
        return tuple(
            self.track_states[track_id].primary_skill_id
            for track_id in self.pending_track_ids
        )

    @property
    def confirmatory_skill_ids(self) -> tuple[str, ...]:
        return tuple(
            self.track_states[track_id].primary_skill_id
            for track_id in self.confirmatory_track_ids
        )


@dataclass(frozen=True)
class PlacementEnvelope:
    profile_version_id: str
    preferred_teaching_language: str
    prior_difficulty_signals: tuple[str, ...]
    state: PlacementSessionState


def placement_supported(subject_id: str, target_class_no: int) -> bool:
    return bool(placement_tracks_for(subject_id, target_class_no))


def preflight_placement_track_plans(
    tracks_by_class: Mapping[int, tuple[PlacementTrack, ...]],
) -> bool:
    """Fail before session creation when the scheduler can outrun its bank.

    A snapshot miss can descend to any authored band, while an ambiguous
    snapshot probes the target band first. Every authored boundary therefore
    needs its own targeted item and a distinct confirmation from the same
    track. Runtime may use additional confirmations when authors provide them,
    but never borrows evidence from another track.
    """

    if set(tracks_by_class) != {2, 3, 4, 5}:
        raise ValueError("placement_preflight_class_plan_incomplete")
    seen_item_ids: set[str] = set()
    for class_no in range(2, 6):
        tracks = tuple(tracks_by_class[class_no])
        if len(tracks) != 8:
            raise ValueError(f"placement_preflight_track_count:{class_no}")
        for track in tracks:
            if track.target_class_no != class_no:
                raise ValueError(
                    f"placement_preflight_track_class_mismatch:{track.track_id}"
                )
            if track.snapshot_item.track_id != track.track_id:
                raise ValueError(
                    f"placement_preflight_snapshot_track_mismatch:{track.track_id}"
                )
            if track.snapshot_item.evaluation_mode != "deterministic":
                raise ValueError(
                    f"placement_preflight_snapshot_requires_local_grading:{track.track_id}"
                )
            authored_bands = tuple(
                sorted({int(band.source_class_no) for band in track.bands})
            )
            if int(track.snapshot_item.source_class_no) not in authored_bands:
                raise ValueError(
                    f"placement_preflight_snapshot_band_unreachable:{track.track_id}"
                )
            track_item_ids = {track.snapshot_item.item_id}
            if track_item_ids & seen_item_ids:
                raise ValueError(
                    f"placement_preflight_duplicate_item:{track.snapshot_item.item_id}"
                )
            for band in track.bands:
                targeted = tuple(
                    item
                    for item in band.variants
                    if item.stage == "targeted_diagnostic"
                    and item.track_id == track.track_id
                    and int(item.source_class_no) == int(band.source_class_no)
                )
                confirmations = tuple(
                    item
                    for item in band.variants
                    if item.stage == "confirmatory"
                    and item.track_id == track.track_id
                    and int(item.source_class_no) == int(band.source_class_no)
                )
                if not targeted:
                    raise ValueError(
                        "placement_preflight_missing_targeted_item:"
                        f"{track.track_id}:{band.source_class_no}"
                    )
                if not confirmations:
                    raise ValueError(
                        "placement_preflight_missing_confirmatory_item:"
                        f"{track.track_id}:{band.source_class_no}"
                    )
                for item in targeted + confirmations:
                    if item.item_id in track_item_ids or item.item_id in seen_item_ids:
                        raise ValueError(
                            f"placement_preflight_duplicate_item:{item.item_id}"
                        )
                    track_item_ids.add(item.item_id)
            seen_item_ids.update(track_item_ids)
    return True


def new_placement_envelope(profile: dict[str, Any]) -> PlacementEnvelope:
    preflight_placement_track_plans(PLACEMENT_TRACKS_BY_CLASS)
    subject_id = _subject_id(profile)
    target_class_no = int(profile["target_class_no"])
    tracks = _ordered_tracks(
        placement_tracks_for(subject_id, target_class_no),
        tuple(str(value) for value in profile.get("prior_difficulty_signals") or ()),
    )
    if not tracks:
        raise ValueError("placement_slice_not_ready")
    if len(tracks) != 8:
        raise ValueError("placement_track_plan_incomplete")
    track_states = {
        track.track_id: PlacementTrackState(
            track_id=track.track_id,
            primary_skill_id=track.primary_skill_id,
            learner_skill_label=track.learner_skill_label,
            snapshot_item_id=track.snapshot_item.item_id,
            snapshot_source_band=int(track.snapshot_item.source_class_no),
            authored_bands=tuple(sorted({int(band.source_class_no) for band in track.bands})),
        )
        for track in tracks
    }
    return PlacementEnvelope(
        profile_version_id=str(profile["profile_version_id"]),
        preferred_teaching_language=str(profile.get("preferred_teaching_language") or "en"),
        prior_difficulty_signals=tuple(
            str(value) for value in profile.get("prior_difficulty_signals") or ()
        ),
        state=PlacementSessionState(
            subject_id=subject_id,
            class_no=target_class_no,
            track_states=_frozen_mapping(track_states),
            skill_states=_frozen_mapping({
                track.primary_skill_id: SkillReadinessState(
                    skill_id=track.primary_skill_id
                )
                for track in tracks
            }),
        ),
    )


def envelope_to_json(envelope: PlacementEnvelope) -> dict[str, Any]:
    return {
        "engine_version": ENGINE_VERSION,
        "profile_version_id": envelope.profile_version_id,
        "preferred_teaching_language": envelope.preferred_teaching_language,
        "prior_difficulty_signals": list(envelope.prior_difficulty_signals),
        "placement_state": _placement_state_to_json(envelope.state),
    }


def envelope_from_json(payload: dict[str, Any]) -> PlacementEnvelope:
    version = str(payload.get("engine_version") or "")
    if version == LEGACY_ENGINE_VERSION:
        return _migrate_pristine_legacy_envelope(payload)
    if version != ENGINE_VERSION:
        raise ValueError("unsupported_placement_engine_version")
    return PlacementEnvelope(
        profile_version_id=str(payload.get("profile_version_id") or ""),
        preferred_teaching_language=str(payload.get("preferred_teaching_language") or "en"),
        prior_difficulty_signals=tuple(
            str(value) for value in payload.get("prior_difficulty_signals") or ()
        ),
        state=_placement_state_from_json(dict(payload.get("placement_state") or {})),
    )


def placement_response(
    *,
    session_id: str,
    envelope: PlacementEnvelope,
) -> dict[str, Any]:
    state = envelope.state
    item = next_item(envelope)
    status = placement_status(envelope)
    return {
        "session_id": session_id,
        "profile_version_id": envelope.profile_version_id,
        "subject_id": state.subject_id,
        "target_class_no": state.class_no,
        "preferred_teaching_language": envelope.preferred_teaching_language,
        "stage": state.stage,
        "status": status,
        "answered_count": len(state.answered_item_ids),
        "scorable_answers": state.scorable_answers,
        "max_items": MAX_PLACEMENT_ITEMS,
        "readiness_summary": readiness_summary(state, status_override=status),
        "track_verdicts": public_track_verdicts(state),
        "next_item": (
            _public_placement_item_for_session(
                item,
                language=envelope.preferred_teaching_language,
                session_id=session_id,
            )
            if item
            else None
        ),
    }


def _public_placement_item_for_session(
    item: SchoolPlacementBankItem,
    *,
    language: str,
    session_id: str,
) -> dict[str, Any]:
    public_item = public_placement_item(item, language)
    if not item.options:
        return public_item

    secret = get_jwt_secret().encode("utf-8")
    ordered = sorted(
        enumerate(item.options),
        key=lambda indexed_option: hmac.new(
            secret,
            (
                "school-placement-option-v1\0"
                f"{session_id}\0{item.item_id}\0"
                f"{indexed_option[0]}\0{indexed_option[1]}"
            ).encode("utf-8"),
            hashlib.sha256,
        ).digest(),
    )
    return {
        **public_item,
        "options": [option for _index, option in ordered],
    }


def placement_status(envelope: PlacementEnvelope) -> str:
    return envelope.state.terminal_status or "in_progress"


def abandon_placement(envelope: PlacementEnvelope) -> PlacementEnvelope:
    """Terminalize an active placement without creating readiness evidence."""

    terminal_status = envelope.state.terminal_status
    if terminal_status == "abandoned":
        return envelope
    if terminal_status is not None:
        raise ValueError("placement_not_active")
    return replace(
        envelope,
        state=replace(
            envelope.state,
            terminal_status="abandoned",
            terminal_reason="learner_abandoned",
            pending_track_ids=(),
            confirmatory_track_ids=(),
            readiness_seeds_applied=False,
        ),
    )


def resume_placement(envelope: PlacementEnvelope) -> PlacementEnvelope:
    """Resume the same insufficient placement only when fresh evidence exists.

    Resumption never clears attempts, readiness evidence, learner time, or the
    item budget. It only reconstructs a queue from unused authored items that
    belong to unresolved tracks.
    """

    state = envelope.state
    if state.terminal_status != "insufficient_evidence":
        raise ValueError("placement_not_resumable")
    if state.total_items >= MAX_PLACEMENT_ITEMS:
        raise ValueError("placement_resume_evidence_unavailable")
    if (
        _outer_learner_budget_reason(state) is not None
        and state.terminal_reason != "placement_learner_time_budget_exhausted"
    ):
        raise ValueError("placement_resume_evidence_unavailable")

    tracks = _tracks_by_id(state)
    answered = set(state.answered_item_ids)
    unresolved_ids = tuple(
        track_id
        for track_id, track_state in state.track_states.items()
        if track_state.status not in {
            "provisional_ready",
            "resolved_ready",
            "confirmed_weak",
        }
    )
    snapshot_ids = tuple(
        track_id
        for track_id in unresolved_ids
        if state.track_states[track_id].status == "pending"
        and (track := tracks.get(track_id)) is not None
        and track.snapshot_item.item_id not in answered
    )
    targeted_ids = tuple(
        track_id
        for track_id in unresolved_ids
        if (track := tracks.get(track_id)) is not None
        and _targeted_item(track, state.track_states[track_id], answered) is not None
    )
    confirmatory_ids = tuple(
        track_id
        for track_id in unresolved_ids
        if (track := tracks.get(track_id)) is not None
        and _unused_confirmation_for(track, state.track_states[track_id], answered)
        is not None
    )

    if state.stage == "confirmatory" and confirmatory_ids:
        resumed_state = replace(
            state,
            stage="confirmatory",
            pending_track_ids=(),
            confirmatory_track_ids=confirmatory_ids,
            terminal_status=None,
            terminal_reason=None,
            stage_items=0,
            stage_elapsed_seconds=0,
        )
    elif state.stage == "targeted_diagnostic" and targeted_ids:
        resumed_state = replace(
            state,
            stage="targeted_diagnostic",
            pending_track_ids=targeted_ids,
            confirmatory_track_ids=confirmatory_ids,
            terminal_status=None,
            terminal_reason=None,
            stage_items=0,
            stage_elapsed_seconds=0,
        )
    elif snapshot_ids:
        resumed_state = replace(
            state,
            stage="snapshot",
            pending_track_ids=(),
            confirmatory_track_ids=(),
            terminal_status=None,
            terminal_reason=None,
            stage_items=0,
            stage_elapsed_seconds=0,
        )
    elif targeted_ids:
        resumed_state = replace(
            state,
            stage="targeted_diagnostic",
            pending_track_ids=targeted_ids,
            confirmatory_track_ids=confirmatory_ids,
            terminal_status=None,
            terminal_reason=None,
            stage_items=0,
            stage_elapsed_seconds=0,
        )
    elif confirmatory_ids:
        resumed_state = replace(
            state,
            stage="confirmatory",
            pending_track_ids=(),
            confirmatory_track_ids=confirmatory_ids,
            terminal_status=None,
            terminal_reason=None,
            stage_items=0,
            stage_elapsed_seconds=0,
        )
    else:
        raise ValueError("placement_resume_evidence_unavailable")

    resumed_state = replace(resumed_state, sitting_elapsed_seconds=0.0)
    resumed = replace(envelope, state=resumed_state)
    item = next_item(resumed)
    if (
        item is None
        or item.item_id in answered
        or item.track_id not in unresolved_ids
    ):
        raise ValueError("placement_resume_evidence_unavailable")
    return resumed


def can_resume_placement(envelope: PlacementEnvelope) -> bool:
    try:
        resume_placement(envelope)
    except ValueError:
        return False
    return True


def validate_placement_resume_state_json(
    previous_state_json: dict[str, Any],
    proposed_state_json: dict[str, Any],
    *,
    profile_version_id: str,
) -> None:
    """Reject resume writes that mutate evidence, counters, or profile lineage."""

    previous = envelope_from_json(previous_state_json)
    if previous.profile_version_id != str(profile_version_id):
        raise ValueError("school_session_lineage_conflict")
    expected = resume_placement(previous)
    try:
        proposed = envelope_from_json(proposed_state_json)
    except (TypeError, ValueError) as exc:
        raise ValueError("placement_session_resume_conflict") from exc
    if envelope_to_json(proposed) != envelope_to_json(expected):
        raise ValueError("placement_session_resume_conflict")

    expected_public_metadata = {
        key: value
        for key, value in previous_state_json.items()
        if key not in {"placement_state", PRIVATE_PLACEMENT_TIMING_KEY}
    }
    proposed_public_metadata = {
        key: value
        for key, value in proposed_state_json.items()
        if key not in {"placement_state", PRIVATE_PLACEMENT_TIMING_KEY}
    }
    if proposed_public_metadata != expected_public_metadata:
        raise ValueError("placement_session_resume_conflict")

    if PRIVATE_PLACEMENT_TIMING_KEY not in proposed_state_json:
        return
    timing = proposed_state_json.get(PRIVATE_PLACEMENT_TIMING_KEY)
    next_expected = next_item(expected)
    if next_expected is None or not isinstance(timing, dict):
        raise ValueError("placement_session_resume_conflict")
    if str(timing.get("item_id") or "") != next_expected.item_id:
        raise ValueError("placement_session_resume_conflict")
    if not isinstance(timing.get("presented_at"), str) or not timing["presented_at"]:
        raise ValueError("placement_session_resume_conflict")
    try:
        datetime.fromisoformat(timing["presented_at"])
    except ValueError as exc:
        raise ValueError("placement_session_resume_conflict") from exc


def next_item(envelope: PlacementEnvelope) -> SchoolPlacementBankItem | None:
    state = envelope.state
    if state.terminal_status is not None:
        return None
    tracks = _tracks_by_id(state)
    answered = set(state.answered_item_ids)
    if state.stage == "snapshot":
        for track_state in state.track_states.values():
            if track_state.status != "pending":
                continue
            track = tracks.get(track_state.track_id)
            if track and track.snapshot_item.item_id not in answered:
                return track.snapshot_item
        return None
    if state.stage == "targeted_diagnostic" and state.pending_track_ids:
        track_state = state.track_states[state.pending_track_ids[0]]
        track = tracks.get(track_state.track_id)
        if not track:
            return None
        return _targeted_item(track, track_state, answered)
    if state.stage == "confirmatory" and state.confirmatory_track_ids:
        track_state = state.track_states[state.confirmatory_track_ids[0]]
        track = tracks.get(track_state.track_id)
        if not track or track_state.boundary_band is None:
            return None
        return _variant_for(
            track,
            source_band=track_state.boundary_band,
            stage="confirmatory",
            answered=answered,
        )
    return None


def apply_answer(
    envelope: PlacementEnvelope,
    item: SchoolPlacementBankItem,
    answer: str,
) -> PlacementEnvelope:
    return apply_evaluated_attempt(
        envelope,
        item,
        evaluator_score=1.0 if answer_matches(item, answer) else 0.0,
        evaluator_confidence=1.0,
    )


def apply_evaluated_attempt(
    envelope: PlacementEnvelope,
    item: SchoolPlacementBankItem,
    *,
    evaluator_score: float,
    evaluator_confidence: float,
    scorable: bool = True,
    certifying_blockers: tuple[str, ...] = (),
    elapsed_seconds_delta: float = 0.0,
    evaluator_wait_seconds_delta: int = 0,
) -> PlacementEnvelope:
    state = envelope.state
    if item.item_id in state.answered_item_ids:
        return envelope
    classification = classify_placement_evidence(
        evaluator_score=evaluator_score,
        evaluator_confidence=evaluator_confidence,
        scorable=scorable,
        certifying_blockers=certifying_blockers,
    )
    if classification == "unscorable":
        elapsed = max(0.0, float(elapsed_seconds_delta))
        updated_state = replace(
            state,
            unscorable_attempts=state.unscorable_attempts + 1,
            elapsed_seconds=state.elapsed_seconds + elapsed,
            sitting_elapsed_seconds=_current_sitting_elapsed(state) + elapsed,
            evaluator_wait_seconds=(
                state.evaluator_wait_seconds
                + max(0, int(evaluator_wait_seconds_delta))
            ),
            stage_elapsed_seconds=state.stage_elapsed_seconds + elapsed,
        )
        return replace(
            envelope,
            state=_advance_after_unscorable_attempt(updated_state),
        )
    track_state = state.track_states.get(item.track_id)
    if track_state is None or track_state.primary_skill_id != item.primary_skill_id:
        raise ValueError("placement_item_track_mismatch")
    evidence = PlacementAttemptEvidence(
        item_id=item.item_id,
        track_id=item.track_id,
        primary_skill_id=item.primary_skill_id,
        source_class_no=int(item.source_class_no),
        stage=item.stage,
        classification=classification,
        evaluator_score=float(evaluator_score),
        evaluator_confidence=float(evaluator_confidence),
        certifying_blockers=tuple(sorted(set(certifying_blockers))),
        elapsed_seconds=max(0.0, float(elapsed_seconds_delta)),
    )
    updated_track = _record_track_evidence(track_state, evidence)
    track_states = dict(state.track_states)
    track_states[item.track_id] = updated_track
    skill_states = dict(state.skill_states)
    current_skill = skill_states.get(item.primary_skill_id) or SkillReadinessState(
        skill_id=item.primary_skill_id
    )
    skill_states[item.primary_skill_id] = apply_attempt_evidence(
        current_skill,
        AttemptEvidence(
            attempt_type="placement",
            evaluator_score=float(evaluator_score),
            evaluator_confidence=float(evaluator_confidence),
            skill_ids=(item.primary_skill_id,),
            support_level="independent",
            blockers=tuple(sorted(set(certifying_blockers))),
        ),
    )
    elapsed = max(0.0, float(elapsed_seconds_delta))
    updated_state = replace(
        state,
        track_states=_frozen_mapping(track_states),
        skill_states=_frozen_mapping(skill_states),
        answered_item_ids=state.answered_item_ids + (item.item_id,),
        total_items=state.total_items + 1,
        scorable_answers=state.scorable_answers + 1,
        elapsed_seconds=state.elapsed_seconds + elapsed,
        sitting_elapsed_seconds=_current_sitting_elapsed(state) + elapsed,
        evaluator_wait_seconds=(
            state.evaluator_wait_seconds + max(0, int(evaluator_wait_seconds_delta))
        ),
        stage_items=state.stage_items + 1,
        stage_elapsed_seconds=state.stage_elapsed_seconds + elapsed,
    )
    advanced = _advance_after_attempt(updated_state, item.track_id)
    return replace(envelope, state=advanced)


def _advance_after_unscorable_attempt(
    state: PlacementSessionState,
) -> PlacementSessionState:
    outer_budget_reason = _outer_learner_budget_reason(state)
    if outer_budget_reason is not None:
        return _finalize_from_available_evidence(
            state,
            budget_reason=outer_budget_reason,
        )

    stage_budget_reason = _stage_budget_reason(state)
    if stage_budget_reason is None:
        return state
    if state.stage == "snapshot":
        return _finish_snapshot(state, include_unseen=True)
    if state.stage == "targeted_diagnostic":
        return _finish_targeted_on_budget(
            state,
            budget_reason=stage_budget_reason,
        )
    return _finalize_from_available_evidence(
        state,
        budget_reason=stage_budget_reason,
    )


def classify_placement_evidence(
    *,
    evaluator_score: float,
    evaluator_confidence: float,
    scorable: bool = True,
    certifying_blockers: tuple[str, ...] = (),
) -> PlacementClassification:
    if not scorable:
        return "unscorable"
    score = max(0.0, min(1.0, float(evaluator_score)))
    confidence = max(0.0, min(1.0, float(evaluator_confidence)))
    if score >= 0.80 and confidence >= 0.75 and not certifying_blockers:
        return "pass"
    if score < 0.60 and confidence >= 0.70:
        return "fail"
    return "ambiguous"


def find_item(envelope: PlacementEnvelope, item_id: str) -> SchoolPlacementBankItem:
    for track in placement_tracks_for(envelope.state.subject_id, envelope.state.class_no):
        for item in _track_items(track):
            if item.item_id == item_id:
                return item
    raise KeyError(item_id)


def answer_matches(item: SchoolPlacementBankItem, answer: str) -> bool:
    return deterministic_placement_answer_matches(item, answer)


def readiness_summary(
    state: PlacementSessionState,
    *,
    status_override: str | None = None,
) -> dict[str, Any]:
    statuses = {
        track.primary_skill_id: _public_track_skill_status(track)
        for track in state.track_states.values()
    }
    return {
        "stage": state.stage,
        "status": status_override or state.terminal_status or "in_progress",
        "required_skill_count": len(state.track_states),
        "ready_skill_ids": [
            skill_id for skill_id, status in statuses.items() if status == "ready"
        ],
        "weak_skill_ids": [
            skill_id for skill_id, status in statuses.items() if status == "weak"
        ],
        "watchlist_skill_ids": [
            track.primary_skill_id
            for track in state.track_states.values()
            if track.status in {
                "pending",
                "provisional_weak",
                "ambiguous",
                "unresolved",
            }
        ],
        "skill_statuses": statuses,
        "track_verdicts": public_track_verdicts(state),
    }


def public_track_verdicts(state: PlacementSessionState) -> list[dict[str, Any]]:
    verdicts: list[dict[str, Any]] = []
    for track in state.track_states.values():
        evidence = track.evidence
        confidence = (
            sum(row.evaluator_confidence for row in evidence) / len(evidence)
            if evidence
            else 0.0
        )
        pass_bands = _bands_for(track, "pass")
        fail_bands = _bands_for(track, "fail")
        verdicts.append(
            {
                "track_id": track.track_id,
                "skill_ids": [track.primary_skill_id],
                "evidence_count": len(evidence),
                "highest_clear_pass_band": (
                    max(pass_bands) if pass_bands else None
                ),
                "lowest_clear_fail_band": (
                    min(fail_bands) if fail_bands else None
                ),
                "confidence": round(confidence, 3),
                "status": track.status,
                "unresolved_reason": track.unresolved_reason,
            }
        )
    return verdicts


def _advance_after_attempt(state: PlacementSessionState, track_id: str) -> PlacementSessionState:
    if state.stage == "snapshot":
        if any(track.status == "pending" for track in state.track_states.values()):
            advanced = state
        else:
            advanced = _finish_snapshot(state)
    elif state.stage == "targeted_diagnostic":
        advanced = _advance_targeted(state, track_id)
    else:
        advanced = _advance_confirmatory(state, track_id)

    if advanced.terminal_status in {"target_ready", "below_target"}:
        return advanced

    outer_budget_reason = _outer_learner_budget_reason(state)
    if outer_budget_reason is not None:
        return _finalize_from_available_evidence(
            advanced,
            budget_reason=outer_budget_reason,
        )

    stage_budget_reason = _stage_budget_reason(state)
    if (
        stage_budget_reason is not None
        and advanced.terminal_status is None
        and advanced.stage == state.stage
    ):
        if state.stage == "snapshot":
            advanced = _finish_snapshot(advanced, include_unseen=True)
        elif state.stage == "targeted_diagnostic":
            advanced = _finish_targeted_on_budget(
                advanced,
                budget_reason=stage_budget_reason,
            )
        else:
            advanced = _finalize_from_available_evidence(
                advanced,
                budget_reason=stage_budget_reason,
            )

    if advanced.terminal_status in {"target_ready", "below_target"}:
        return advanced

    terminal_reason = None
    if state.total_items >= MAX_PLACEMENT_ITEMS:
        terminal_reason = "item_budget_exhausted_without_honest_boundary"
    if terminal_reason is None:
        return advanced
    if advanced.terminal_status in {"target_ready", "below_target"}:
        return advanced
    if advanced.terminal_status == "insufficient_evidence":
        return replace(advanced, terminal_reason=terminal_reason)
    return _finalize_from_available_evidence(
        advanced,
        budget_reason=terminal_reason,
    )


def _finish_snapshot(
    state: PlacementSessionState,
    *,
    include_unseen: bool = False,
) -> PlacementSessionState:
    if all(
        track.status == "provisional_ready"
        for track in state.track_states.values()
    ):
        return _finalize_target_ready(state)
    candidates = tuple(
        track_id
        for track_id, track in state.track_states.items()
        if track.status in {
            "provisional_weak",
            "ambiguous",
        }
    )
    pending = candidates[:MAX_TARGETED_DIAGNOSTIC_ITEMS]
    track_states = dict(state.track_states)
    for track_id in candidates[MAX_TARGETED_DIAGNOSTIC_ITEMS:]:
        track_states[track_id] = _as_watchlist(
            track_states[track_id],
            reason="stage_two_question_limit",
        )
    if include_unseen:
        for track_id, track in state.track_states.items():
            if track.status == "pending":
                track_states[track_id] = _as_watchlist(
                    track,
                    reason="snapshot_budget_unanswered",
                )
    staged = replace(
        state,
        stage="targeted_diagnostic",
        track_states=_frozen_mapping(track_states),
        pending_track_ids=pending,
        stage_items=0,
        stage_elapsed_seconds=0,
        terminal_reason=None,
    )
    staged = _drop_missing_targeted_items(staged)
    if staged.pending_track_ids:
        return staged
    if staged.confirmatory_track_ids:
        return _enter_confirmatory(staged)
    return _finalize_from_available_evidence(staged)


def _finish_targeted_on_budget(
    state: PlacementSessionState,
    *,
    budget_reason: str,
) -> PlacementSessionState:
    track_states = dict(state.track_states)
    confirmatory = list(state.confirmatory_track_ids)
    for track_id in state.pending_track_ids:
        resolved, confirmation_reason = _resolve_targeted_track(
            track_states[track_id]
        )
        if confirmation_reason == "contradictory_evidence":
            resolved = replace(
                resolved,
                status="ambiguous",
                boundary_band=_confirmation_band(resolved),
                unresolved_reason=confirmation_reason,
            )
            confirmatory.append(track_id)
        elif confirmation_reason or resolved.status in {
            "pending",
            "provisional_weak",
            "ambiguous",
            "unresolved",
        }:
            resolved = _as_watchlist(
                resolved,
                reason=(
                    confirmation_reason
                    or budget_reason
                ),
            )
        track_states[track_id] = resolved

    staged = replace(
        state,
        track_states=_frozen_mapping(track_states),
        pending_track_ids=(),
        confirmatory_track_ids=tuple(dict.fromkeys(confirmatory)),
    )
    if staged.confirmatory_track_ids:
        return _enter_confirmatory(staged)
    return _finalize_from_available_evidence(
        staged,
        budget_reason=budget_reason,
    )


def _advance_targeted(state: PlacementSessionState, track_id: str) -> PlacementSessionState:
    track = state.track_states[track_id]
    resolved, confirmation_reason = _resolve_targeted_track(track)
    track_states = dict(state.track_states)
    track_states[track_id] = resolved
    pending = tuple(value for value in state.pending_track_ids if value != track_id)
    confirmatory = state.confirmatory_track_ids
    if confirmation_reason == "contradictory_evidence":
        resolved = replace(
            resolved,
            status="ambiguous",
            boundary_band=_confirmation_band(resolved),
            unresolved_reason=confirmation_reason,
        )
        track_states[track_id] = resolved
        confirmatory = _append_unique(confirmatory, track_id)
    elif confirmation_reason:
        resolved = _as_watchlist(resolved, reason=confirmation_reason)
        track_states[track_id] = resolved
    elif resolved.status in {"provisional_weak", "ambiguous"}:
        pending = (track_id,) + pending
    staged = replace(
        state,
        track_states=_frozen_mapping(track_states),
        pending_track_ids=pending,
        confirmatory_track_ids=confirmatory,
    )
    staged = _drop_missing_targeted_items(staged)
    if staged.pending_track_ids:
        return staged
    if staged.confirmatory_track_ids:
        return _enter_confirmatory(staged)
    return _finalize_from_available_evidence(staged)


def _advance_confirmatory(state: PlacementSessionState, track_id: str) -> PlacementSessionState:
    track = _resolve_confirmed_track(state.track_states[track_id])
    track_states = dict(state.track_states)
    track_states[track_id] = track
    confirmatory = tuple(
        value for value in state.confirmatory_track_ids if value != track_id
    )
    authored_track = _tracks_by_id(state).get(track_id)
    if track.status == "unresolved":
        fresh_item = (
            _unused_confirmation_for(
                authored_track,
                track,
                set(state.answered_item_ids),
            )
            if authored_track
            else None
        )
        if (
            fresh_item is not None
            and state.stage_items < MAX_CONFIRMATORY_ITEMS
        ):
            confirmatory = confirmatory + (track_id,)
        else:
            track = replace(
                track,
                unresolved_reason=(
                    "missing_additional_authored_same_track_confirmatory_item"
                ),
            )
            track_states[track_id] = track
    staged = replace(
        state,
        track_states=_frozen_mapping(track_states),
        confirmatory_track_ids=confirmatory,
    )
    staged = _drop_missing_confirmatory_items(staged)
    if staged.confirmatory_track_ids:
        return staged
    return _finalize_from_available_evidence(staged)


def _record_track_evidence(
    track: PlacementTrackState,
    evidence: PlacementAttemptEvidence,
) -> PlacementTrackState:
    status = track.status
    if evidence.stage == "snapshot":
        status = {
            "pass": "provisional_ready",
            "fail": "provisional_weak",
            "ambiguous": "ambiguous",
        }[evidence.classification]
    updated = replace(track, status=status, evidence=track.evidence + (evidence,))
    return _with_boundary_facts(updated)


def _with_boundary_facts(track: PlacementTrackState) -> PlacementTrackState:
    pass_bands = _bands_for(track, "pass")
    fail_bands = _bands_for(track, "fail")
    return replace(
        track,
        highest_passed_band=max(pass_bands) if pass_bands else None,
        first_failed_band=min(fail_bands) if fail_bands else None,
    )


def _resolve_targeted_track(
    track: PlacementTrackState,
) -> tuple[PlacementTrackState, str | None]:
    pass_bands = _bands_for(track, "pass")
    fail_bands = _bands_for(track, "fail")
    if _contradictory(pass_bands, fail_bands):
        return track, "contradictory_evidence"
    if pass_bands and fail_bands:
        between = _bands_between(track.authored_bands, max(pass_bands), min(fail_bands))
        if not between:
            return (
                replace(
                    track,
                    status="confirmed_weak",
                    boundary_band=max(pass_bands),
                    unresolved_reason=None,
                ),
                None,
            )
        return replace(track, status="provisional_weak"), None
    if pass_bands:
        max_band = max(track.authored_bands, default=track.snapshot_source_band)
        if max(pass_bands) == max_band and len(_clear_evidence(track, "pass")) >= 2:
            return replace(track, status="resolved_ready", unresolved_reason=None), None
        if _choose_targeted_band(track) is None:
            return track, "insufficient_boundary_evidence"
        return replace(track, status="ambiguous"), None
    if fail_bands:
        authored_floor = min(track.authored_bands, default=None)
        if (
            authored_floor is not None
            and authored_floor in fail_bands
            and len(_clear_evidence(track, "fail")) >= 2
        ):
            return (
                replace(
                    track,
                    status="confirmed_weak",
                    boundary_band=authored_floor,
                    unresolved_reason="below_authored_floor",
                ),
                None,
            )
        if _choose_targeted_band(track) is None:
            return track, "insufficient_boundary_evidence"
        return replace(track, status="provisional_weak"), None
    return track, "insufficient_boundary_evidence"


def _resolve_confirmed_track(track: PlacementTrackState) -> PlacementTrackState:
    pass_bands = _bands_for(track, "pass")
    fail_bands = _bands_for(track, "fail")
    if not _contradictory(pass_bands, fail_bands) and pass_bands and fail_bands:
        if not _bands_between(track.authored_bands, max(pass_bands), min(fail_bands)):
            return replace(
                track,
                status="confirmed_weak",
                boundary_band=max(pass_bands),
                unresolved_reason=None,
            )
    max_band = max(track.authored_bands, default=track.snapshot_source_band)
    if (
        pass_bands
        and not fail_bands
        and max(pass_bands) == max_band
        and len(_clear_evidence(track, "pass")) >= 2
    ):
        return replace(track, status="resolved_ready", unresolved_reason=None)
    reason = (
        "continued_contradiction"
        if _contradictory(pass_bands, fail_bands)
        else "insufficient_boundary_evidence"
    )
    return replace(track, status="unresolved", unresolved_reason=reason)


def _as_watchlist(
    track: PlacementTrackState,
    *,
    reason: str,
) -> PlacementTrackState:
    if track.status == "confirmed_weak":
        return track
    return replace(
        track,
        status="unresolved",
        unresolved_reason=track.unresolved_reason or reason,
    )


def _targeted_item(
    track: PlacementTrack,
    track_state: PlacementTrackState,
    answered: set[str],
) -> SchoolPlacementBankItem | None:
    band = _choose_targeted_band(track_state)
    if band is None:
        return None
    return _variant_for(
        track,
        source_band=band,
        stage="targeted_diagnostic",
        answered=answered,
    )


def _unused_confirmation_for(
    track: PlacementTrack,
    track_state: PlacementTrackState,
    answered: set[str],
) -> SchoolPlacementBankItem | None:
    boundary_band = track_state.boundary_band
    if boundary_band is None:
        boundary_band = _confirmation_band(track_state)
    return _variant_for(
        track,
        source_band=boundary_band,
        stage="confirmatory",
        answered=answered,
    )


def _choose_targeted_band(track: PlacementTrackState) -> int | None:
    bands = tuple(sorted(set(track.authored_bands)))
    pass_bands = _bands_for(track, "pass")
    fail_bands = _bands_for(track, "fail")
    targeted_bands = {
        evidence.source_class_no
        for evidence in track.evidence
        if evidence.stage == "targeted_diagnostic"
    }
    if _contradictory(pass_bands, fail_bands):
        return None
    if pass_bands and fail_bands:
        candidates = tuple(
            band
            for band in _bands_between(bands, max(pass_bands), min(fail_bands))
            if band not in targeted_bands
        )
        return _midpoint_band(candidates)
    if fail_bands:
        failed_floor = min(fail_bands)
        lower = tuple(
            band
            for band in bands
            if band < failed_floor and band not in targeted_bands
        )
        if lower:
            return _midpoint_band(lower)
        if failed_floor not in targeted_bands:
            return failed_floor
        return None
    if pass_bands:
        passed_ceiling = max(pass_bands)
        higher = tuple(
            band
            for band in bands
            if band > passed_ceiling and band not in targeted_bands
        )
        if higher:
            return _midpoint_band(higher)
        if passed_ceiling not in targeted_bands:
            return passed_ceiling
        return None
    untested = tuple(band for band in bands if band not in targeted_bands)
    return max(untested) if untested else None


def _drop_missing_targeted_items(state: PlacementSessionState) -> PlacementSessionState:
    track_states = dict(state.track_states)
    pending: list[str] = []
    confirmatory = list(state.confirmatory_track_ids)
    tracks = _tracks_by_id(state)
    answered = set(state.answered_item_ids)
    for track_id in state.pending_track_ids:
        track_state = track_states[track_id]
        track = tracks.get(track_id)
        if track and _targeted_item(track, track_state, answered):
            pending.append(track_id)
            continue
        if _choose_targeted_band(track_state) is None and track_state.evidence:
            track_states[track_id] = _as_watchlist(
                track_state,
                reason="insufficient_boundary_evidence",
            )
            continue
        track_states[track_id] = replace(
            track_state,
            status="unresolved",
            unresolved_reason="missing_authored_same_track_item",
        )
    return replace(
        state,
        track_states=_frozen_mapping(track_states),
        pending_track_ids=tuple(pending),
        confirmatory_track_ids=tuple(dict.fromkeys(confirmatory)),
    )


def _drop_missing_confirmatory_items(state: PlacementSessionState) -> PlacementSessionState:
    track_states = dict(state.track_states)
    pending: list[str] = []
    tracks = _tracks_by_id(state)
    answered = set(state.answered_item_ids)
    for track_id in state.confirmatory_track_ids:
        track_state = track_states[track_id]
        track = tracks.get(track_id)
        item = (
            _variant_for(
                track,
                source_band=track_state.boundary_band,
                stage="confirmatory",
                answered=answered,
            )
            if track and track_state.boundary_band is not None
            else None
        )
        if item:
            pending.append(track_id)
        else:
            track_states[track_id] = replace(
                track_state,
                status="unresolved",
                unresolved_reason="missing_authored_same_track_item",
            )
    return replace(
        state,
        track_states=_frozen_mapping(track_states),
        confirmatory_track_ids=tuple(pending),
    )


def _enter_confirmatory(state: PlacementSessionState) -> PlacementSessionState:
    track_states = dict(state.track_states)
    confirmatory = state.confirmatory_track_ids[:MAX_CONFIRMATORY_ITEMS]
    for track_id in state.confirmatory_track_ids[MAX_CONFIRMATORY_ITEMS:]:
        track_states[track_id] = _as_watchlist(
            track_states[track_id],
            reason="stage_three_question_limit",
        )
    staged = replace(
        state,
        stage="confirmatory",
        track_states=_frozen_mapping(track_states),
        confirmatory_track_ids=confirmatory,
        stage_items=0,
        stage_elapsed_seconds=0,
    )
    staged = _drop_missing_confirmatory_items(staged)
    if staged.confirmatory_track_ids:
        return staged
    return _finalize_from_available_evidence(staged)


def _outer_learner_budget_reason(state: PlacementSessionState) -> str | None:
    if _current_sitting_elapsed(state) >= PLACEMENT_LEARNER_TIME_BUDGET_SECONDS:
        return "placement_learner_time_budget_exhausted"
    return None


def _current_sitting_elapsed(state: PlacementSessionState) -> float:
    if state.sitting_elapsed_seconds is None:
        return float(state.elapsed_seconds)
    return float(state.sitting_elapsed_seconds)


def _stage_budget_reason(state: PlacementSessionState) -> str | None:
    stage_limits = {
        "snapshot": SNAPSHOT_LEARNER_TIME_BUDGET_SECONDS,
        "targeted_diagnostic": TARGETED_DIAGNOSTIC_LEARNER_TIME_BUDGET_SECONDS,
        "confirmatory": CONFIRMATORY_LEARNER_TIME_BUDGET_SECONDS,
    }
    if state.stage_elapsed_seconds >= stage_limits[state.stage]:
        return f"{state.stage}_learner_time_budget_exhausted"
    item_limits = {
        "snapshot": MAX_SNAPSHOT_ITEMS,
        "targeted_diagnostic": MAX_TARGETED_DIAGNOSTIC_ITEMS,
        "confirmatory": MAX_CONFIRMATORY_ITEMS,
    }
    if state.stage_items >= item_limits[state.stage]:
        return f"{state.stage}_item_budget_exhausted"
    return None


def _learner_budget_reason(state: PlacementSessionState) -> str | None:
    return _outer_learner_budget_reason(state) or _stage_budget_reason(state)


def _finalize_target_ready(state: PlacementSessionState) -> PlacementSessionState:
    track_states = {
        track_id: replace(
            track,
            status="resolved_ready",
            unresolved_reason=None,
        )
        for track_id, track in state.track_states.items()
    }
    skill_states = dict(state.skill_states)
    for track in track_states.values():
        current = skill_states.get(track.primary_skill_id) or SkillReadinessState(
            skill_id=track.primary_skill_id
        )
        skill_states[track.primary_skill_id] = apply_placement_ready_seed(
            current,
            confidence=1.0,
        )
    return replace(
        state,
        track_states=_frozen_mapping(track_states),
        skill_states=_frozen_mapping(skill_states),
        pending_track_ids=(),
        confirmatory_track_ids=(),
        terminal_status="target_ready",
        terminal_reason="all_required_tracks_ready",
        readiness_seeds_applied=True,
    )


def _finalize_with_watchlist(
    state: PlacementSessionState,
    *,
    budget_reason: str | None,
) -> PlacementSessionState:
    track_states: dict[str, PlacementTrackState] = {}
    skill_states = dict(state.skill_states)
    seeded_ready_skills = False
    for track_id, track in state.track_states.items():
        if track.status in {"provisional_ready", "resolved_ready"}:
            resolved = replace(
                track,
                status="resolved_ready",
                unresolved_reason=None,
            )
            current = skill_states.get(resolved.primary_skill_id) or SkillReadinessState(
                skill_id=resolved.primary_skill_id
            )
            skill_states[resolved.primary_skill_id] = apply_placement_ready_seed(
                current,
                confidence=1.0,
            )
            seeded_ready_skills = True
        else:
            resolved = _as_watchlist(
                track,
                reason="nonblocking_uncertainty_watchlist",
            )
        track_states[track_id] = resolved
    return replace(
        state,
        track_states=_frozen_mapping(track_states),
        skill_states=_frozen_mapping(skill_states),
        pending_track_ids=(),
        confirmatory_track_ids=(),
        terminal_status="target_ready",
        terminal_reason=(
            f"watchlist_after_{budget_reason}"
            if budget_reason
            else "nonblocking_uncertainty_watchlist"
        ),
        readiness_seeds_applied=seeded_ready_skills,
    )


def _finalize_from_available_evidence(
    state: PlacementSessionState,
    *,
    budget_reason: str | None = None,
) -> PlacementSessionState:
    if all(
        track.status in {"provisional_ready", "resolved_ready"}
        for track in state.track_states.values()
    ):
        return _finalize_target_ready(state)
    state, has_authored_floor_gap = _resolve_authored_floor_failures(state)
    confirmed_weak = [
        track
        for track in state.track_states.values()
        if track.status == "confirmed_weak" and track.boundary_band is not None
    ]
    if state.scorable_answers >= MIN_SCORABLE_FOR_TERMINAL_PLACEMENT and confirmed_weak:
        return replace(
            state,
            pending_track_ids=(),
            confirmatory_track_ids=(),
            terminal_status="below_target",
            terminal_reason=(
                "authored_floor_rebuild_required"
                if has_authored_floor_gap
                else "confirmed_lower_boundary"
            ),
            readiness_seeds_applied=False,
        )
    return _finalize_with_watchlist(
        state,
        budget_reason=budget_reason,
    )


def _resolve_authored_floor_failures(
    state: PlacementSessionState,
) -> tuple[PlacementSessionState, bool]:
    """Turn repeated misses at the lowest supported band into a support path.

    A learner who gives enough scorable evidence and misses both the target band
    and the lowest authored band needs the earliest support we can teach. The
    absence of a lower pass means we must not claim mastery of that lower band,
    but it must not strand the learner in an impossible "answer more" loop.
    """

    if state.scorable_answers < MIN_SCORABLE_FOR_TERMINAL_PLACEMENT:
        return state, False

    track_states = dict(state.track_states)
    changed = False
    has_authored_floor_gap = any(
        track.status == "confirmed_weak"
        and track.unresolved_reason == "below_authored_floor"
        for track in track_states.values()
    )
    for track_id, track in track_states.items():
        if track.status == "confirmed_weak" or track.highest_passed_band is not None:
            continue
        authored_floor = min(track.authored_bands, default=None)
        if authored_floor is None:
            continue
        clear_failures = [
            evidence
            for evidence in track.evidence
            if evidence.classification == "fail"
        ]
        if (
            len(clear_failures) < 2
            or min(evidence.source_class_no for evidence in clear_failures)
            != authored_floor
        ):
            continue
        track_states[track_id] = replace(
            track,
            status="confirmed_weak",
            boundary_band=authored_floor,
            unresolved_reason="below_authored_floor",
        )
        changed = True
        has_authored_floor_gap = True

    if not changed:
        return state, has_authored_floor_gap
    return (
        replace(state, track_states=_frozen_mapping(track_states)),
        has_authored_floor_gap,
    )


def _variant_for(
    track: PlacementTrack,
    *,
    source_band: int,
    stage: PlacementStage,
    answered: set[str],
) -> SchoolPlacementBankItem | None:
    for band in track.bands:
        if int(band.source_class_no) != int(source_band):
            continue
        for item in band.variants:
            if item.stage == stage and item.item_id not in answered:
                return item
        return None
    return None


def _track_items(track: PlacementTrack) -> tuple[SchoolPlacementBankItem, ...]:
    return (track.snapshot_item,) + tuple(
        item for band in track.bands for item in band.variants
    )


def _tracks_by_id(state: PlacementSessionState) -> dict[str, PlacementTrack]:
    return {
        track.track_id: track
        for track in placement_tracks_for(state.subject_id, state.class_no)
    }


def _ordered_tracks(
    tracks: tuple[PlacementTrack, ...],
    prior_difficulty_signals: tuple[str, ...],
) -> tuple[PlacementTrack, ...]:
    priority = _skill_priority(prior_difficulty_signals)
    if not priority:
        return tracks
    indexed = {track.track_id: index for index, track in enumerate(tracks)}
    return tuple(
        sorted(
            tracks,
            key=lambda track: (
                priority.get(track.primary_skill_id, 999),
                indexed[track.track_id],
            ),
        )
    )


def _public_track_skill_status(track: PlacementTrackState) -> str:
    if track.status == "resolved_ready":
        return "ready"
    if track.status == "provisional_ready":
        return "practice_ready"
    if track.status == "pending":
        return "unseen"
    return "weak"


def _bands_for(
    track: PlacementTrackState,
    classification: Literal["pass", "fail"],
) -> tuple[int, ...]:
    return tuple(
        evidence.source_class_no
        for evidence in track.evidence
        if evidence.classification == classification
    )


def _clear_evidence(
    track: PlacementTrackState,
    classification: Literal["pass", "fail"],
) -> tuple[PlacementAttemptEvidence, ...]:
    return tuple(
        evidence
        for evidence in track.evidence
        if evidence.classification == classification
    )


def _contradictory(pass_bands: tuple[int, ...], fail_bands: tuple[int, ...]) -> bool:
    return bool(pass_bands and fail_bands and max(pass_bands) >= min(fail_bands))


def _bands_between(bands: tuple[int, ...], lower: int, upper: int) -> tuple[int, ...]:
    return tuple(band for band in bands if lower < band < upper)


def _midpoint_band(bands: tuple[int, ...]) -> int | None:
    if not bands:
        return None
    return bands[len(bands) // 2]


def _confirmation_band(track: PlacementTrackState) -> int:
    if track.evidence:
        return track.evidence[-1].source_class_no
    return track.snapshot_source_band


def _append_unique(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    return values if value in values else values + (value,)


def _subject_id(profile: dict[str, Any]) -> str:
    subject_ids = profile.get("subject_ids") or ["english"]
    return str(subject_ids[0])


def _skill_priority(prior_difficulty_signals: tuple[str, ...]) -> dict[str, int]:
    priority: dict[str, int] = {}
    cursor = 0
    for signal in prior_difficulty_signals:
        for skill_id in SIGNAL_SKILL_PRIORITY.get(signal, ()):
            if skill_id not in priority:
                priority[skill_id] = cursor
                cursor += 1
    return priority


def _placement_state_to_json(state: PlacementSessionState) -> dict[str, Any]:
    return {
        "subject_id": state.subject_id,
        "class_no": state.class_no,
        "stage": state.stage,
        "track_states": {
            track_id: {
                "track_id": track.track_id,
                "primary_skill_id": track.primary_skill_id,
                "learner_skill_label": track.learner_skill_label,
                "snapshot_item_id": track.snapshot_item_id,
                "snapshot_source_band": track.snapshot_source_band,
                "authored_bands": list(track.authored_bands),
                "status": track.status,
                "evidence": [
                    {
                        **asdict(evidence),
                        "certifying_blockers": list(evidence.certifying_blockers),
                    }
                    for evidence in track.evidence
                ],
                "highest_passed_band": track.highest_passed_band,
                "first_failed_band": track.first_failed_band,
                "boundary_band": track.boundary_band,
                "unresolved_reason": track.unresolved_reason,
            }
            for track_id, track in state.track_states.items()
        },
        "skill_states": {
            skill_id: {
                **asdict(skill_state),
                "active_blockers": list(skill_state.active_blockers),
                "recent_hint_flags": list(skill_state.recent_hint_flags),
            }
            for skill_id, skill_state in state.skill_states.items()
        },
        "answered_item_ids": list(state.answered_item_ids),
        "total_items": state.total_items,
        "scorable_answers": state.scorable_answers,
        "unscorable_attempts": state.unscorable_attempts,
        "elapsed_seconds": state.elapsed_seconds,
        "sitting_elapsed_seconds": state.sitting_elapsed_seconds,
        "evaluator_wait_seconds": state.evaluator_wait_seconds,
        "stage_items": state.stage_items,
        "stage_elapsed_seconds": state.stage_elapsed_seconds,
        "pending_track_ids": list(state.pending_track_ids),
        "confirmatory_track_ids": list(state.confirmatory_track_ids),
        "terminal_status": state.terminal_status,
        "terminal_reason": state.terminal_reason,
        "readiness_seeds_applied": state.readiness_seeds_applied,
    }


def _placement_state_from_json(payload: dict[str, Any]) -> PlacementSessionState:
    track_states = {
        track_id: PlacementTrackState(
            track_id=str(value.get("track_id") or track_id),
            primary_skill_id=str(value.get("primary_skill_id") or ""),
            learner_skill_label=str(value.get("learner_skill_label") or ""),
            snapshot_item_id=str(value.get("snapshot_item_id") or ""),
            snapshot_source_band=int(value.get("snapshot_source_band") or 1),
            authored_bands=tuple(int(band) for band in value.get("authored_bands") or ()),
            status=value.get("status") or "pending",
            evidence=tuple(
                PlacementAttemptEvidence(
                    item_id=str(evidence.get("item_id") or ""),
                    track_id=str(evidence.get("track_id") or track_id),
                    primary_skill_id=str(evidence.get("primary_skill_id") or ""),
                    source_class_no=int(evidence.get("source_class_no") or 1),
                    stage=evidence.get("stage") or "snapshot",
                    classification=evidence.get("classification") or "ambiguous",
                    evaluator_score=float(evidence.get("evaluator_score") or 0.0),
                    evaluator_confidence=float(evidence.get("evaluator_confidence") or 0.0),
                    certifying_blockers=tuple(evidence.get("certifying_blockers") or ()),
                    elapsed_seconds=float(evidence.get("elapsed_seconds") or 0.0),
                )
                for evidence in value.get("evidence") or ()
            ),
            highest_passed_band=_optional_int(value.get("highest_passed_band")),
            first_failed_band=_optional_int(value.get("first_failed_band")),
            boundary_band=_optional_int(value.get("boundary_band")),
            unresolved_reason=value.get("unresolved_reason"),
        )
        for track_id, value in dict(payload.get("track_states") or {}).items()
    }
    skill_states = {
        skill_id: SkillReadinessState(
            **{
                **value,
                "skill_id": str(value.get("skill_id") or skill_id),
                "active_blockers": tuple(value.get("active_blockers") or ()),
                "recent_hint_flags": tuple(value.get("recent_hint_flags") or ()),
            }
        )
        for skill_id, value in dict(payload.get("skill_states") or {}).items()
    }
    return PlacementSessionState(
        subject_id=str(payload.get("subject_id") or "english"),
        class_no=int(payload.get("class_no") or 2),
        stage=payload.get("stage") or "snapshot",
        track_states=_frozen_mapping(track_states),
        skill_states=_frozen_mapping(skill_states),
        answered_item_ids=tuple(payload.get("answered_item_ids") or ()),
        total_items=int(payload.get("total_items") or 0),
        scorable_answers=int(payload.get("scorable_answers") or 0),
        unscorable_attempts=int(payload.get("unscorable_attempts") or 0),
        elapsed_seconds=float(payload.get("elapsed_seconds") or 0.0),
        sitting_elapsed_seconds=(
            float(payload.get("sitting_elapsed_seconds") or 0.0)
            if "sitting_elapsed_seconds" in payload
            and payload.get("sitting_elapsed_seconds") is not None
            else None
        ),
        evaluator_wait_seconds=int(payload.get("evaluator_wait_seconds") or 0),
        stage_items=int(payload.get("stage_items") or 0),
        stage_elapsed_seconds=float(payload.get("stage_elapsed_seconds") or 0.0),
        pending_track_ids=tuple(payload.get("pending_track_ids") or ()),
        confirmatory_track_ids=tuple(payload.get("confirmatory_track_ids") or ()),
        terminal_status=payload.get("terminal_status"),
        terminal_reason=payload.get("terminal_reason"),
        readiness_seeds_applied=bool(payload.get("readiness_seeds_applied", False)),
    )


def _migrate_pristine_legacy_envelope(payload: dict[str, Any]) -> PlacementEnvelope:
    legacy_state = dict(payload.get("placement_state") or {})
    if (
        legacy_state.get("answered_item_ids")
        or int(legacy_state.get("total_items") or 0) > 0
        or int(legacy_state.get("scorable_answers") or 0) > 0
    ):
        raise ValueError("placement_state_migration_required")
    return new_placement_envelope(
        {
            "profile_version_id": str(payload.get("profile_version_id") or ""),
            "preferred_teaching_language": str(
                payload.get("preferred_teaching_language") or "en"
            ),
            "prior_difficulty_signals": list(
                payload.get("prior_difficulty_signals") or ()
            ),
            "subject_ids": [str(legacy_state.get("subject_id") or "english")],
            "target_class_no": int(legacy_state.get("class_no") or 2),
        }
    )


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _frozen_mapping(values: dict[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))
