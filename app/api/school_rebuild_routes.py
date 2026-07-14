import asyncio
import hashlib
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import get_settings
from app.services.school.authority import school_route_owner
from app.services.school.availability import (
    school_availability,
    unavailable_school_state,
)
from app.services.school.open_answer_ai import evaluate_school_open_answer
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_masterclass as masterclass
from app.services.school_rebuild_learning import (
    SchoolLearningProfileService,
    build_school_memory_context,
)
from app.services.school.language_confidence import (
    LanguageConfidenceState,
    load_language_confidence,
)
from app.services import school_rebuild_placement as placement
from app.services import school_rebuild_placement_evaluator as placement_evaluator
from app.services import school_rebuild_recap as recap
from app.services import school_rebuild_report as reports
from app.services import school_rebuild_support as support
from app.services.school_rebuild_profile import (
    SCHOOL_PROFILE_FIELDS,
    SchoolOnboardingCompleteIn,
    SchoolOnboardingDraftPatchIn,
    SchoolRebuildProfileIn,
    choose_school_coach_identity,
    public_school_catalog,
    public_school_profile,
    public_school_profile_draft,
    school_catalog_selection_available,
    school_coach_identity,
)
from app.services.school_rebuild_state import (
    school_state_for_profile,
    unauthenticated_school_state,
)
from app.storage import get_storage

async def _require_school_available(request: Request) -> None:
    # State remains readable so clients can hide School without probing any
    # learner data. Retirement endpoints live on a separate router.
    if request.url.path.rstrip("/") == "/school/state":
        return
    availability = school_availability()
    if not availability.available:
        raise HTTPException(
            status_code=503,
            detail={"code": availability.reason or "school_unavailable"},
        )


router = APIRouter(
    prefix="/school",
    tags=["school-rebuild"],
    dependencies=[Depends(_require_school_available)],
)
logger = logging.getLogger(__name__)
SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS = 8.0
SCHOOL_ANSWER_HEARTBEAT_SECONDS = 30.0


def _school_open_answer_timeout_seconds() -> float | None:
    """Local models may need a minute or more; cloud requests stay bounded."""
    if get_settings().ai_backend == "local":
        return None
    return SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS


async def _evaluate_school_open_answer_with_runtime_policy(
    activity: dict,
    answer: str,
):
    timeout_seconds = _school_open_answer_timeout_seconds()
    if timeout_seconds is None:
        return await evaluate_school_open_answer(activity, answer)
    async with asyncio.timeout(timeout_seconds):
        return await evaluate_school_open_answer(activity, answer)


async def _renew_school_answer_claim(
    *,
    store,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    claim_token: str,
) -> None:
    while True:
        await asyncio.sleep(SCHOOL_ANSWER_HEARTBEAT_SECONDS)
        renewed = await store.renew_school_answer_request(
            user_id,
            session_id,
            activity_id,
            answer_hash,
            claim_token,
        )
        if not renewed:
            raise ValueError("stale_school_answer_request")


async def _evaluate_school_open_answer_with_claim_heartbeat(
    *,
    store,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    claim_token: str,
    activity: dict,
    answer: str,
):
    evaluation_task = asyncio.create_task(
        _evaluate_school_open_answer_with_runtime_policy(activity, answer)
    )
    heartbeat_task = asyncio.create_task(
        _renew_school_answer_claim(
            store=store,
            user_id=user_id,
            session_id=session_id,
            activity_id=activity_id,
            answer_hash=answer_hash,
            claim_token=claim_token,
        )
    )
    try:
        done, _pending = await asyncio.wait(
            {evaluation_task, heartbeat_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if evaluation_task in done:
            return await evaluation_task
        # A lost lease must fence the model result before persistence.
        await heartbeat_task
        raise RuntimeError("school_answer_heartbeat_ended_without_result")
    finally:
        for task in (evaluation_task, heartbeat_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(
            evaluation_task,
            heartbeat_task,
            return_exceptions=True,
        )


class SchoolPlacementAnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1)
    answer: str = Field(default="", max_length=800)


class SchoolRecapAnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(min_length=1)
    answer: str = Field(default="", max_length=800)


class SchoolCurriculumAnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(min_length=1)
    answer: str = Field(default="", max_length=800)


class SchoolCurriculumStartIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chapter_id: str = Field(min_length=1, max_length=120)
    client_start_id: str = Field(min_length=1, max_length=160)


def _require_available_school_selection(profile: dict) -> None:
    if school_catalog_selection_available(profile):
        return
    raise HTTPException(
        status_code=409,
        detail={"code": "school_catalog_selection_unavailable"},
    )


def _state_with_school_coach(
    state_json: dict,
    source: dict | None,
) -> dict:
    return {
        **state_json,
        **school_coach_identity(source),
    }


def _state_with_new_linked_school_coach(state_json: dict) -> dict:
    return {
        **state_json,
        **choose_school_coach_identity(),
    }


def _public_session_with_school_coach(response: dict, session_row: dict) -> dict:
    return {
        **response,
        **school_coach_identity(session_row.get("state_json")),
    }


def _canonical_state_allows(state: dict, action: str) -> bool:
    allowed = state.get("allowed_next_actions")
    return (
        state.get("next_action") == action
        and isinstance(allowed, list)
        and action in allowed
    )


async def _require_canonical_school_action(
    request: Request,
    accepted_actions: set[str],
    *,
    error_code: str,
) -> dict:
    canonical_state = await school_state(request)
    allowed = canonical_state.get("allowed_next_actions")
    allowed_actions = set(allowed) if isinstance(allowed, list) else set()
    next_action = canonical_state.get("next_action")
    if next_action in accepted_actions and next_action in allowed_actions:
        return canonical_state
    raise HTTPException(
        status_code=409,
        detail={
            "code": error_code,
            "next_action": next_action,
            "allowed_next_actions": sorted(allowed_actions),
        },
    )


def _uid(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return user_id


async def _learner_profile(user_id: str) -> dict:
    profile = await get_storage().get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=401, detail="Profile not found; sign in again")
    return profile


_SCHOOL_SESSION_WRITE_CONFLICTS = {
    "active_school_session_profile_lineage_required",
    "linked_school_session_not_found",
    "school_session_lineage_conflict",
    "school_session_transition_requires_active",
    "school_session_start_conflict",
    "stale_school_profile_lineage",
    "stale_school_answer_request",
    "stale_school_answer_session",
    "stale_school_session_transition",
    "duplicate_evidence_conflict",
}


async def _upsert_school_session(store, **kwargs) -> None:
    try:
        await store.upsert_school_session(**kwargs)
    except ValueError as exc:
        code = str(exc)
        if code in _SCHOOL_SESSION_WRITE_CONFLICTS:
            raise HTTPException(status_code=409, detail={"code": code}) from exc
        raise


async def _get_or_create_school_session(store, **kwargs) -> dict:
    if kwargs.get("flow_type") in {"masterclass", "support"}:
        winner = await store.get_active_school_session(
            str(kwargs["user_id"]),
            str(kwargs["api_version"]),
            str(kwargs["flow_type"]),
            str(kwargs["subject_id"]),
            int(kwargs["class_no"]),
            profile_version_id=kwargs.get("profile_version_id"),
            source_placement_report_id=kwargs.get("source_placement_report_id"),
        )
        if winner:
            return winner
        identity = school_coach_identity(kwargs.get("state_json"))
        if not all(identity.values()):
            kwargs["state_json"] = _state_with_new_linked_school_coach(
                dict(kwargs.get("state_json") or {})
            )
    try:
        return await store.get_or_create_school_session(**kwargs)
    except ValueError as exc:
        code = str(exc)
        if code in _SCHOOL_SESSION_WRITE_CONFLICTS:
            raise HTTPException(status_code=409, detail={"code": code}) from exc
        raise


async def _school_answer_replay(
    store,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    conflict_code: str,
    in_progress_code: str,
) -> dict | None:
    request_row = await store.get_school_answer_request(
        user_id,
        session_id,
        activity_id,
    )
    if not request_row:
        return None
    request_status = str(request_row.get("status") or "")
    if request_status != "failed" and request_row.get("answer_hash") != answer_hash:
        raise HTTPException(status_code=409, detail={"code": conflict_code})
    if request_status == "completed":
        return dict(request_row.get("response_json") or {})
    if request_status == "processing" and not request_row.get("stale"):
        raise HTTPException(status_code=409, detail={"code": in_progress_code})
    return None


async def _claim_school_answer(
    store,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    conflict_code: str,
    in_progress_code: str,
) -> str | dict:
    claim = await store.claim_school_answer_request(
        user_id,
        session_id,
        activity_id,
        answer_hash,
    )
    if claim.get("outcome") == "completed":
        return dict(claim.get("response_json") or {})
    if claim.get("outcome") == "in_progress":
        raise HTTPException(status_code=409, detail={"code": in_progress_code})
    if claim.get("outcome") == "conflict":
        raise HTTPException(status_code=409, detail={"code": conflict_code})
    if claim.get("outcome") != "claimed" or not claim.get("claim_token"):
        raise RuntimeError("invalid_school_answer_request_claim")
    return str(claim["claim_token"])


def _matches_profile_lineage(row: dict | None, public_profile: dict | None) -> bool:
    return bool(
        row
        and public_profile
        and str(row.get("profile_version_id") or "")
        == str(public_profile.get("profile_version_id") or "")
    )


def _matches_report_lineage(
    row: dict | None,
    public_profile: dict | None,
    placement_report: dict | None,
) -> bool:
    return bool(
        _matches_profile_lineage(row, public_profile)
        and placement_report
        and str(row.get("source_placement_report_id") or "")
        == str(placement_report.get("report_id") or "")
    )


async def _placement_row_with_effective_status(row: dict) -> dict:
    state_json = row.get("state_json")
    if not isinstance(state_json, dict):
        invalid_row = dict(row)
        invalid_row["status"] = "invalid_state"
        return invalid_row
    try:
        envelope = placement.envelope_from_json(state_json)
    except (AttributeError, KeyError, TypeError, ValueError):
        invalid_row = dict(row)
        invalid_row["status"] = "invalid_state"
        return invalid_row
    effective_status = placement.placement_status(envelope)
    if row.get("status") == "active" and effective_status != "in_progress":
        await _upsert_school_session(
            get_storage(),
            session_id=row["session_id"],
            user_id=row["user_id"],
            api_version=row["api_version"],
            flow_type=row["flow_type"],
            subject_id=row["subject_id"],
            class_no=int(row["class_no"]),
            status=effective_status,
            current_stage=envelope.state.stage,
            linked_session_id=row.get("linked_session_id"),
            profile_version_id=row.get("profile_version_id"),
            source_placement_report_id=row.get("source_placement_report_id"),
            state_json=_state_with_school_coach(
                placement.envelope_to_json(envelope),
                row.get("state_json"),
            ),
        )
        row = dict(row)
        row["status"] = effective_status
    return row


async def _latest_placement_for_profile(user_id: str, public_profile: dict) -> dict | None:
    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    target_class_no = int(public_profile["target_class_no"])
    active_placement = await get_storage().get_active_school_session(
        user_id,
        "rebuild",
        "placement",
        subject_id,
        target_class_no,
        profile_version_id=str(public_profile["profile_version_id"]),
    )
    if active_placement:
        return await _placement_row_with_effective_status(active_placement)
    latest_placement = await get_storage().get_latest_school_session(
        user_id,
        "rebuild",
        "placement",
        subject_id,
        target_class_no,
        profile_version_id=str(public_profile["profile_version_id"]),
    )
    if latest_placement:
        return await _placement_row_with_effective_status(latest_placement)
    return None


async def _latest_placement_report_for_profile(
    user_id: str,
    public_profile: dict,
) -> dict | None:
    placement_session = await _latest_placement_for_profile(user_id, public_profile)
    if placement_session:
        report = await get_storage().get_school_placement_report(
            user_id,
            placement_session["session_id"],
            profile_version_id=str(public_profile["profile_version_id"]),
        )
        if report:
            return report
        return None

    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    target_class_no = int(public_profile["target_class_no"])
    compatible_report = (
        await get_storage().get_latest_compatible_school_placement_report(
            user_id,
            str(public_profile["profile_version_id"]),
            subject_id,
            target_class_no,
        )
    )
    if compatible_report:
        return compatible_report
    for flow_type in ("curriculum", "recap"):
        active_session = await get_storage().get_active_school_session(
            user_id,
            "rebuild",
            flow_type,
            subject_id,
            target_class_no,
            profile_version_id=str(public_profile["profile_version_id"]),
        )
        source_report_id = (
            str(active_session.get("source_placement_report_id") or "")
            if active_session
            else ""
        )
        if source_report_id:
            return await get_storage().get_school_placement_report_by_id(
                user_id,
                source_report_id,
            )
    return None


async def _active_recap_for_profile(
    user_id: str,
    public_profile: dict,
    source_placement_report_id: str | None,
) -> dict | None:
    if not source_placement_report_id:
        return None
    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    return await get_storage().get_active_school_session(
        user_id,
        "rebuild",
        "recap",
        subject_id,
        int(public_profile["target_class_no"]),
        profile_version_id=str(public_profile["profile_version_id"]),
        source_placement_report_id=source_placement_report_id,
    )


async def _latest_recap_for_profile(
    user_id: str,
    public_profile: dict,
    source_placement_report_id: str | None,
) -> dict | None:
    if not source_placement_report_id:
        return None
    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    active = await _active_recap_for_profile(
        user_id,
        public_profile,
        source_placement_report_id,
    )
    if active:
        return active
    latest = await get_storage().get_latest_school_session(
        user_id,
        "rebuild",
        "recap",
        subject_id,
        int(public_profile["target_class_no"]),
        profile_version_id=str(public_profile["profile_version_id"]),
        source_placement_report_id=source_placement_report_id,
    )
    if latest:
        return latest
    return await get_storage().get_latest_school_session(
        user_id,
        "rebuild",
        "recap",
        subject_id,
        int(public_profile["target_class_no"]),
        source_placement_report_id=source_placement_report_id,
    )


async def _active_curriculum_for_profile(
    user_id: str,
    public_profile: dict,
    source_placement_report_id: str | None,
) -> dict | None:
    if not source_placement_report_id:
        return None
    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    store = get_storage()
    active = await store.get_active_school_session(
        user_id,
        "rebuild",
        "curriculum",
        subject_id,
        int(public_profile["target_class_no"]),
        profile_version_id=str(public_profile["profile_version_id"]),
        source_placement_report_id=source_placement_report_id,
    )
    if not active or curriculum.session_content_version_is_current(active):
        return active
    stale_state = {
        **dict(active.get("state_json") or {}),
        "status": "expired",
        "phase": "content_refresh_required",
        "active_interrupt": None,
        "expiration_reason": "authored_content_version_changed",
    }
    await store.upsert_school_session(
        session_id=str(active["session_id"]),
        user_id=user_id,
        api_version="rebuild",
        flow_type="curriculum",
        subject_id=subject_id,
        class_no=int(public_profile["target_class_no"]),
        status="expired",
        current_stage=str(active.get("current_stage") or ""),
        linked_session_id=(
            str(active["linked_session_id"])
            if active.get("linked_session_id")
            else None
        ),
        profile_version_id=str(public_profile["profile_version_id"]),
        source_placement_report_id=source_placement_report_id,
        state_json=stale_state,
    )
    return None


async def _latest_curriculum_for_profile(
    user_id: str,
    public_profile: dict,
    source_placement_report_id: str | None,
) -> dict | None:
    if not source_placement_report_id:
        return None
    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    active = await _active_curriculum_for_profile(
        user_id,
        public_profile,
        source_placement_report_id,
    )
    if active:
        return active
    latest = await get_storage().get_latest_school_session(
        user_id,
        "rebuild",
        "curriculum",
        subject_id,
        int(public_profile["target_class_no"]),
        profile_version_id=str(public_profile["profile_version_id"]),
        source_placement_report_id=source_placement_report_id,
    )
    if latest and latest.get("status") == "expired":
        return None
    return latest


async def _learning_events(user_id: str) -> list[dict]:
    if not hasattr(get_storage(), "get_school_learning_graph"):
        return []
    graph = await get_storage().get_school_learning_graph(user_id)
    return list(graph.get("events") or [])


def _state_report_with_recap_unlock(
    *,
    placement_report: dict | None,
    recap_session: dict | None,
    curriculum_session: dict | None,
) -> dict | None:
    if not placement_report or not recap_session or not curriculum_session:
        return placement_report
    if (
        placement_report.get("placement_status"),
        placement_report.get("unlock_state"),
    ) != ("below_target", "recap_required"):
        return placement_report
    recap_state = recap_session.get("state_json")
    if not isinstance(recap_state, dict) or recap_state.get("status") != "complete":
        return placement_report
    return {
        **placement_report,
        "placement_status": "target_ready",
        "unlock_state": "target_unlocked",
        "allowed_next_actions": ["start_curriculum"],
    }


async def _current_linked_school_sessions(
    *,
    user_id: str,
    parent_session: dict | None,
    public_profile: dict,
    source_placement_report_id: str | None,
) -> tuple[dict | None, dict | None]:
    if not parent_session or not source_placement_report_id:
        return None, None
    rows = await get_storage().get_school_sessions_linked_to(
        user_id,
        str(parent_session["session_id"]),
    )
    current_profile_id = str(public_profile["profile_version_id"])
    current_rows = [
        row
        for row in rows
        if row.get("api_version") == "rebuild"
        and row.get("status") in {"active", "paused_for_masterclass"}
        and str(row.get("profile_version_id") or "") == current_profile_id
        and str(row.get("source_placement_report_id") or "")
        == source_placement_report_id
    ]
    masterclass = next(
        (row for row in current_rows if row.get("flow_type") == "masterclass"),
        None,
    )
    support = next(
        (row for row in current_rows if row.get("flow_type") == "support"),
        None,
    )
    return masterclass, support


async def _processing_curriculum_answer_request(
    *,
    user_id: str,
    curriculum_session: dict | None,
) -> dict | None:
    if not curriculum_session:
        return None
    state_json = curriculum_session.get("state_json")
    if not isinstance(state_json, dict):
        return None
    chapter = state_json.get("chapter")
    if chapter is not None and not isinstance(chapter, dict):
        return None
    activity_id = curriculum.current_curriculum_activity_id(state_json)
    if not activity_id:
        return None
    request_row = await get_storage().get_school_answer_request(
        user_id,
        str(curriculum_session["session_id"]),
        activity_id,
    )
    if not request_row or request_row.get("status") != "processing":
        return None
    return request_row


def _linked_school_sessions_from_snapshot(
    *,
    rows: list[dict],
    public_profile: dict,
    source_placement_report_id: str | None,
) -> tuple[dict | None, dict | None]:
    if not source_placement_report_id:
        return None, None
    current_profile_id = str(public_profile["profile_version_id"])
    current_rows = [
        row
        for row in rows
        if row.get("api_version") == "rebuild"
        and row.get("status") in {"active", "paused_for_masterclass"}
        and str(row.get("profile_version_id") or "") == current_profile_id
        and str(row.get("source_placement_report_id") or "")
        == source_placement_report_id
    ]
    return (
        next(
            (row for row in current_rows if row.get("flow_type") == "masterclass"),
            None,
        ),
        next(
            (row for row in current_rows if row.get("flow_type") == "support"),
            None,
        ),
    )


def _processing_curriculum_request_from_snapshot(
    *,
    rows: list[dict],
    curriculum_session: dict | None,
) -> dict | None:
    if not curriculum_session:
        return None
    state_json = curriculum_session.get("state_json")
    if not isinstance(state_json, dict):
        return None
    activity_id = curriculum.current_curriculum_activity_id(state_json)
    if not activity_id:
        return None
    return next(
        (
            row
            for row in rows
            if str(row.get("activity_id") or "") == activity_id
            and row.get("status") == "processing"
        ),
        None,
    )


async def _canonical_school_read_context(request: Request) -> dict:
    """Return one request-scoped, lineage-consistent School read model."""

    cached = getattr(request.state, "school_read_context", None)
    if isinstance(cached, dict):
        return cached

    user_id = _uid(request)
    store = get_storage()
    snapshot = await store.get_school_state_snapshot(user_id)
    learner = snapshot.get("learner_profile")
    if not isinstance(learner, dict):
        raise HTTPException(status_code=401, detail="Profile not found; sign in again")

    school_profile = snapshot.get("school_profile")
    public_profile = (
        public_school_profile(school_profile)
        if isinstance(school_profile, dict)
        else None
    )
    placement_session = None
    placement_report = None
    recap_session = None
    curriculum_session = None
    source_report_id = None

    if public_profile:
        raw_placement = snapshot.get("placement_session")
        if isinstance(raw_placement, dict):
            placement_session = await _placement_row_with_effective_status(
                raw_placement
            )

        raw_report = snapshot.get("placement_report")
        if isinstance(raw_report, dict):
            placement_report = raw_report
        if placement_session and placement_report and str(
            placement_report.get("placement_session_id") or ""
        ) != str(placement_session.get("session_id") or ""):
            # A new placement without a report must not inherit an older result.
            placement_report = None

        if placement_session is None and placement_report is None:
            placement_report = await _latest_placement_report_for_profile(
                user_id,
                public_profile,
            )
            if placement_report:
                placement_session = await store.get_school_session(
                    user_id,
                    str(placement_report["placement_session_id"]),
                )

        source_report_id = (
            str(placement_report["report_id"]) if placement_report else None
        )
        raw_recap = snapshot.get("recap_session")
        raw_curriculum = snapshot.get("curriculum_session")
        recap_session = raw_recap if isinstance(raw_recap, dict) else None
        curriculum_session = (
            raw_curriculum if isinstance(raw_curriculum, dict) else None
        )

        snapshot_has_current_lineage = bool(
            source_report_id
            and (
                (recap_session and _matches_report_lineage(
                    recap_session,
                    public_profile,
                    placement_report,
                ))
                or (curriculum_session and _matches_report_lineage(
                    curriculum_session,
                    public_profile,
                    placement_report,
                ))
                or (
                    recap_session is None
                    and curriculum_session is None
                    and str(placement_report.get("profile_version_id") or "")
                    == str(public_profile["profile_version_id"])
                )
            )
        )
        if source_report_id and not snapshot_has_current_lineage:
            recap_session, curriculum_session = await asyncio.gather(
                _latest_recap_for_profile(
                    user_id,
                    public_profile,
                    source_report_id,
                ),
                _latest_curriculum_for_profile(
                    user_id,
                    public_profile,
                    source_report_id,
                ),
            )

        if (
            curriculum_session
            and curriculum_session.get("status")
            in {"active", "paused_for_masterclass"}
            and not curriculum.session_content_version_is_current(curriculum_session)
        ):
            stale_state = {
                **dict(curriculum_session.get("state_json") or {}),
                "status": "expired",
                "phase": "content_refresh_required",
                "active_interrupt": None,
                "expiration_reason": "authored_content_version_changed",
            }
            await _upsert_school_session(
                store,
                session_id=str(curriculum_session["session_id"]),
                user_id=user_id,
                api_version="rebuild",
                flow_type="curriculum",
                subject_id=str(curriculum_session["subject_id"]),
                class_no=int(curriculum_session["class_no"]),
                status="expired",
                current_stage=str(curriculum_session.get("current_stage") or ""),
                linked_session_id=(
                    str(curriculum_session["linked_session_id"])
                    if curriculum_session.get("linked_session_id")
                    else None
                ),
                profile_version_id=str(public_profile["profile_version_id"]),
                source_placement_report_id=source_report_id,
                state_json=stale_state,
            )
            curriculum_session = None

        if curriculum_session and curriculum_session.get("status") == "complete":
            curriculum_public = curriculum.public_curriculum_response(
                curriculum_session
            )
            curriculum_session = {
                **curriculum_session,
                "state_json": {
                    **(curriculum_session.get("state_json") or {}),
                    "next_available_chapter": curriculum_public.get(
                        "next_available_chapter"
                    ),
                },
            }

    active_curriculum = (
        curriculum_session
        if curriculum_session
        and curriculum_session.get("status")
        in {"active", "paused_for_masterclass"}
        else None
    )
    active_masterclass, active_support = _linked_school_sessions_from_snapshot(
        rows=list(snapshot.get("linked_sessions") or []),
        public_profile=public_profile or {},
        source_placement_report_id=source_report_id,
    ) if public_profile else (None, None)
    processing_answer_request = _processing_curriculum_request_from_snapshot(
        rows=list(snapshot.get("processing_answer_requests") or []),
        curriculum_session=curriculum_session,
    )
    learning_memory = build_school_memory_context(
        {"profiles": list(snapshot.get("school_skill_profiles") or [])}
    )
    if curriculum_session:
        curriculum_session = {
            **curriculum_session,
            "state_json": {
                **dict(curriculum_session.get("state_json") or {}),
                "learner_memory": learning_memory,
            },
        }
        if active_curriculum:
            active_curriculum = curriculum_session
    context = {
        "user_id": user_id,
        "learner_profile": learner,
        "school_profile": public_profile,
        "placement_session": placement_session,
        "placement_report": placement_report,
        "recap_session": recap_session,
        "curriculum_session": curriculum_session,
        "active_curriculum_session": active_curriculum,
        "processing_answer_request": processing_answer_request,
        "active_masterclass_session": active_masterclass,
        "active_support_session": active_support,
        "learning_memory": learning_memory,
    }
    request.state.school_read_context = context
    return context


@router.get("/state")
@school_route_owner("app.services.school_rebuild_state")
async def school_state(request: Request) -> dict:
    availability = school_availability()
    if not availability.available:
        return unavailable_school_state(availability)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {**unauthenticated_school_state(), "available": True}
    context = await _canonical_school_read_context(request)
    state_placement_report = _state_report_with_recap_unlock(
        placement_report=context["placement_report"],
        recap_session=context["recap_session"],
        curriculum_session=context["curriculum_session"],
    )
    return {
        **school_state_for_profile(
            learner_profile=context["learner_profile"],
            school_profile=context["school_profile"],
            placement_session=context["placement_session"],
            placement_report=state_placement_report,
            active_recap_session=context["recap_session"],
            active_curriculum_session=context["curriculum_session"],
            processing_answer_request=context["processing_answer_request"],
            active_masterclass_session=context["active_masterclass_session"],
            active_support_session=context["active_support_session"],
        ),
        "available": True,
    }


def _catalog_has_choice(board_id: str, subject_id: str, class_no: int) -> bool:
    return school_catalog_selection_available(
        {
            "board_id": board_id,
            "subject_ids": [subject_id],
            "target_class_no": class_no,
        },
    )


async def _active_catalog_profile(
    user_id: str,
    *,
    subject_id: str,
    class_no: int,
) -> dict:
    school_profile = await get_storage().get_active_school_profile_version(user_id)
    public_profile = public_school_profile(school_profile) if school_profile else None
    if not public_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    active_subject_id = str((public_profile.get("subject_ids") or ["english"])[0])
    active_class_no = int(public_profile["target_class_no"])
    if active_subject_id != subject_id or active_class_no != int(class_no):
        raise HTTPException(
            status_code=409,
            detail={"code": "school_catalog_profile_mismatch"},
        )
    if not _catalog_has_choice(
        str(public_profile.get("board_id") or ""),
        subject_id,
        class_no,
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "school_catalog_content_not_found"},
        )
    return public_profile


def _require_catalog_profile_match(
    public_profile: dict | None,
    *,
    subject_id: str,
    class_no: int,
) -> dict:
    if not public_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    active_subject_id = str((public_profile.get("subject_ids") or ["english"])[0])
    active_class_no = int(public_profile["target_class_no"])
    if active_subject_id != subject_id or active_class_no != int(class_no):
        raise HTTPException(
            status_code=409,
            detail={"code": "school_catalog_profile_mismatch"},
        )
    if not _catalog_has_choice(
        str(public_profile.get("board_id") or ""),
        subject_id,
        class_no,
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "school_catalog_content_not_found"},
        )
    return public_profile


async def _catalog_curriculum_context(
    user_id: str,
    public_profile: dict,
    canonical_state: dict,
) -> tuple[bool, dict | None, dict | None]:
    placement_report = await _latest_placement_report_for_profile(
        user_id,
        public_profile,
    )
    source_report_id = str(placement_report["report_id"]) if placement_report else None
    active_curriculum = await _active_curriculum_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    latest_curriculum = await _latest_curriculum_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    return (
        _canonical_state_allows(canonical_state, "start_curriculum"),
        latest_curriculum,
        active_curriculum,
    )


@router.get("/catalog")
@school_route_owner("app.content.school_rebuild_content")
async def get_school_catalog(request: Request) -> dict:
    context = await _canonical_school_read_context(request)
    public_profile = context["school_profile"]
    catalog = public_school_catalog()
    return {
        **catalog,
        "active_board_id": (
            str(public_profile.get("board_id")) if public_profile else None
        ),
        "active_subject_id": (
            str((public_profile.get("subject_ids") or ["english"])[0])
            if public_profile
            else None
        ),
        "active_class_no": (
            int(public_profile["target_class_no"]) if public_profile else None
        ),
    }


@router.get("/catalog/{subject_id}/classes/{class_no}")
@school_route_owner("app.services.school_rebuild_curriculum")
async def get_school_class_map(
    subject_id: str,
    class_no: int,
    request: Request,
) -> dict:
    context = await _canonical_school_read_context(request)
    public_profile = _require_catalog_profile_match(
        context["school_profile"],
        subject_id=subject_id,
        class_no=class_no,
    )
    canonical_state = await school_state(request)
    return curriculum.class_chapter_map(
        subject_id=subject_id,
        class_no=class_no,
        curriculum_unlocked=canonical_state.get("unlock_state") == "target_unlocked",
        latest_curriculum_session=context["curriculum_session"],
        active_curriculum_session=context["active_curriculum_session"],
        learning_memory=context["learning_memory"],
        coach_source=public_profile,
    )


@router.get("/catalog/{subject_id}/classes/{class_no}/chapters/{chapter_id}")
@school_route_owner("app.services.school_rebuild_curriculum")
async def get_school_chapter_map(
    subject_id: str,
    class_no: int,
    chapter_id: str,
    request: Request,
) -> dict:
    context = await _canonical_school_read_context(request)
    public_profile = _require_catalog_profile_match(
        context["school_profile"],
        subject_id=subject_id,
        class_no=class_no,
    )
    canonical_state = await school_state(request)
    try:
        return curriculum.chapter_level_map(
            subject_id=subject_id,
            class_no=class_no,
            chapter_id=chapter_id,
            curriculum_unlocked=(
                canonical_state.get("unlock_state") == "target_unlocked"
            ),
            latest_curriculum_session=context["curriculum_session"],
            active_curriculum_session=context["active_curriculum_session"],
            coach_source=public_profile,
        )
    except ValueError as exc:
        if str(exc) == "curriculum_chapter_not_authored":
            raise HTTPException(
                status_code=404,
                detail={"code": "curriculum_chapter_not_authored"},
            ) from exc
        raise


@router.get("/curriculum")
@school_route_owner("app.services.school_rebuild_curriculum")
async def get_school_curriculum_landing(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    school_profile = await get_storage().get_active_school_profile_version(user_id)
    public_profile = public_school_profile(school_profile) if school_profile else None
    if not public_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    await _require_canonical_school_action(
        request,
        {"start_curriculum", "resume_curriculum"},
        error_code="curriculum_locked",
    )
    placement_report = await _latest_placement_report_for_profile(
        user_id,
        public_profile,
    )
    source_report_id = str(placement_report["report_id"]) if placement_report else None
    recap_session = await _latest_recap_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    latest_curriculum = await _latest_curriculum_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    if not curriculum.is_curriculum_unlocked(
        placement_report=placement_report,
        recap_session=recap_session,
    ):
        raise HTTPException(status_code=409, detail={"code": "curriculum_locked"})
    return curriculum.curriculum_landing(
        school_profile=public_profile,
        placement_report=placement_report,
        recap_session=recap_session,
        latest_curriculum_session=latest_curriculum,
    )


@router.post("/curriculum/start")
@school_route_owner("app.services.school_rebuild_curriculum")
async def start_school_curriculum(
    request: Request,
    req: SchoolCurriculumStartIn | None = None,
) -> dict:
    user_id = _uid(request)
    store = get_storage()
    await _learner_profile(user_id)
    school_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(school_profile) if school_profile else None
    if not public_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    _require_available_school_selection(public_profile)
    await _require_canonical_school_action(
        request,
        {"start_curriculum", "resume_curriculum"},
        error_code="curriculum_locked",
    )

    placement_report = await _latest_placement_report_for_profile(
        user_id,
        public_profile,
    )
    source_report_id = str(placement_report["report_id"]) if placement_report else None
    recap_session = await _latest_recap_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    if not curriculum.is_curriculum_unlocked(
        placement_report=placement_report,
        recap_session=recap_session,
    ):
        raise HTTPException(status_code=409, detail={"code": "curriculum_locked"})

    subject_id = (public_profile.get("subject_ids") or ["english"])[0]
    target_class_no = int(public_profile["target_class_no"])
    active = await _active_curriculum_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    latest_curriculum = await _latest_curriculum_for_profile(
        user_id,
        public_profile,
        source_report_id,
    )
    start_hash = None
    existing_start = None
    if req is not None:
        start_hash = hashlib.sha256(
            (
                "school-curriculum-start-v1:"
                f"{public_profile['profile_version_id']}:"
                f"{subject_id}:{target_class_no}:"
                f"{source_report_id or 'no-report'}:{req.chapter_id}"
            ).encode("utf-8")
        ).hexdigest()
        existing_start = await store.get_start_request(
            user_id,
            req.client_start_id,
        )
        if existing_start:
            if existing_start.get("request_hash") != start_hash:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "client_start_id_reused_with_different_payload"
                    },
                )
            if existing_start.get("status") == "completed":
                return dict(existing_start.get("response_json") or {})

        try:
            curriculum.select_startable_chapter(
                subject_id=subject_id,
                class_no=target_class_no,
                chapter_id=req.chapter_id,
                latest_curriculum_session=latest_curriculum,
                active_curriculum_session=active,
            )
        except ValueError as exc:
            code = str(exc)
            if code == "no_curriculum_chapter_available":
                code = "all_curriculum_chapters_complete"
            status_code = 404 if code == "curriculum_chapter_not_authored" else 409
            raise HTTPException(status_code=status_code, detail={"code": code}) from exc

        if existing_start and existing_start.get("status") == "in_progress":
            if not active:
                raise HTTPException(
                    status_code=409,
                    detail={"code": "curriculum_start_in_progress"},
                )
            response = _public_session_with_school_coach(
                curriculum.public_curriculum_response(active),
                active,
            )
            await store.complete_start_request(
                user_id,
                req.client_start_id,
                "completed",
                session_id=str(active["session_id"]),
                response_json=response,
            )
            return response

        if existing_start and existing_start.get("status") == "failed":
            start_latch = await store.reset_start_request(
                user_id,
                req.client_start_id,
                start_hash,
            )
        else:
            start_latch = await store.begin_start_request(
                user_id,
                req.client_start_id,
                start_hash,
            )
        if start_latch.get("request_mismatch"):
            raise HTTPException(
                status_code=409,
                detail={"code": "client_start_id_reused_with_different_payload"},
            )
        if not start_latch.get("accepted"):
            if start_latch.get("status") == "completed":
                return dict(start_latch.get("response_json") or {})
            raise HTTPException(
                status_code=409,
                detail={"code": "curriculum_start_in_progress"},
            )

    if active:
        response = _public_session_with_school_coach(
            curriculum.public_curriculum_response(active),
            active,
        )
        if req is not None:
            await store.complete_start_request(
                user_id,
                req.client_start_id,
                "completed",
                session_id=str(active["session_id"]),
                response_json=response,
            )
        return response

    session_id = str(uuid4())
    learning_memory = await SchoolLearningProfileService(
        store
    ).get_memory_context(user_id)
    try:
        language_confidence = await load_language_confidence(store, user_id)
    except Exception as language_load_error:
        logger.warning(
            "School language confidence load failed for curriculum start: %s",
            type(language_load_error).__name__,
        )
        language_confidence = LanguageConfidenceState(user_id=user_id)
    try:
        state_json = _state_with_school_coach(
            curriculum.new_curriculum_state(
                school_profile=public_profile,
                placement_report=placement_report,
                recap_session=recap_session,
                latest_curriculum_session=latest_curriculum,
                requested_chapter_id=req.chapter_id if req is not None else None,
                learning_memory=learning_memory,
                en_production_confidence=(
                    language_confidence.en_production_confidence
                ),
                language_signal_count=language_confidence.total_signals,
            ),
            public_profile,
        )
    except ValueError as exc:
        if str(exc) == "no_curriculum_chapter_available":
            if req is not None:
                await store.complete_start_request(
                    user_id,
                    req.client_start_id,
                    "failed",
                    error_code="all_curriculum_chapters_complete",
                )
            raise HTTPException(
                status_code=409,
                detail={"code": "all_curriculum_chapters_complete"},
            ) from exc
        raise
    linked_session_id = None
    if latest_curriculum:
        linked_session_id = latest_curriculum["session_id"]
    elif recap_session:
        linked_session_id = recap_session["session_id"]
    elif placement_report and placement_report.get("placement_session_id"):
        linked_session_id = str(placement_report["placement_session_id"])
    row = await _get_or_create_school_session(
        store,
        session_id=session_id,
        user_id=user_id,
        api_version="rebuild",
        flow_type="curriculum",
        subject_id=subject_id,
        class_no=target_class_no,
        status="active",
        current_stage="0",
        linked_session_id=linked_session_id,
        profile_version_id=str(public_profile["profile_version_id"]),
        source_placement_report_id=source_report_id,
        state_json=state_json,
    )
    if not row:
        if req is not None:
            await store.complete_start_request(
                user_id,
                req.client_start_id,
                "failed",
                error_code="curriculum_session_create_failed",
            )
        raise HTTPException(status_code=500, detail={"code": "curriculum_session_create_failed"})
    response = _public_session_with_school_coach(
        curriculum.public_curriculum_response(row),
        row,
    )
    if req is not None:
        await store.complete_start_request(
            user_id,
            req.client_start_id,
            "completed",
            session_id=str(row["session_id"]),
            response_json=response,
        )
    return response


async def _reconcile_saved_curriculum_session(
    *,
    store,
    row: dict,
    user_id: str,
) -> dict:
    expected_state = dict(row.get("state_json") or {})
    reconciled_state, repair = curriculum.reconcile_curriculum_state(expected_state)
    if reconciled_state == expected_state:
        return row

    state_status = str(reconciled_state.get("status") or "active")
    persisted_status = (
        "complete"
        if state_status == "complete"
        else "paused_for_masterclass"
        if state_status == "paused_for_masterclass"
        else "active"
    )
    school_session = {
        "session_id": row["session_id"],
        "user_id": user_id,
        "api_version": row["api_version"],
        "flow_type": row["flow_type"],
        "subject_id": row["subject_id"],
        "class_no": int(row["class_no"]),
        "status": persisted_status,
        "current_stage": (
            "complete"
            if persisted_status == "complete"
            else str(reconciled_state.get("current_level_index") or 0)
        ),
        "linked_session_id": row.get("linked_session_id"),
        "profile_version_id": row.get("profile_version_id"),
        "source_placement_report_id": row.get("source_placement_report_id"),
        "state_json": reconciled_state,
    }
    changed = await store.compare_and_set_school_session(
        school_session=school_session,
        expected_state_json=expected_state,
    )
    if not changed:
        current = await store.get_school_session(user_id, str(row["session_id"]))
        return current or row

    updated_row = await store.get_school_session(user_id, str(row["session_id"]))
    updated_row = updated_row or {**row, **school_session}
    if repair and repair.get("kind") == "chapter_certification_reconciled":
        try:
            await SchoolLearningProfileService(store).record_chapter_certification(
                user_id=user_id,
                session_id=str(row["session_id"]),
                chapter_id=str(repair.get("chapter_id") or ""),
                skill_scores=dict(repair.get("skill_scores") or {}),
            )
        except Exception as projection_error:
            logger.warning(
                "School reconciled certification projection failed for %s: %s",
                row["session_id"],
                type(projection_error).__name__,
            )
    return updated_row


@router.get("/curriculum/{session_id}")
@school_route_owner("app.services.school_rebuild_curriculum")
async def get_school_curriculum_session(session_id: UUID, request: Request) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    await _learner_profile(user_id)
    active_profile = await get_storage().get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    store = get_storage()
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "curriculum"
    ):
        raise HTTPException(status_code=404, detail={"code": "curriculum_session_not_found"})
    row = await _reconcile_saved_curriculum_session(
        store=store,
        row=row,
        user_id=user_id,
    )
    learning_memory = await SchoolLearningProfileService(
        store
    ).get_memory_context(user_id)
    row = {
        **row,
        "state_json": {
            **dict(row.get("state_json") or {}),
            "learner_memory": learning_memory,
        },
    }
    return _public_session_with_school_coach(
        curriculum.public_curriculum_response(row),
        row,
    )


@router.get("/support/{session_id}")
@school_route_owner("app.services.school_rebuild_support")
async def get_school_support(session_id: UUID, request: Request) -> dict:
    user_id = _uid(request)
    session_id = str(session_id)
    store = get_storage()
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "support_session_not_found"},
        )

    if support.parent_support_plan(row) is not None:
        return support.public_support_response(row, parent_session=row)
    if row.get("flow_type") != "support":
        raise HTTPException(
            status_code=404,
            detail={"code": "support_session_not_found"},
        )

    parent_session_id = str(row.get("linked_session_id") or "")
    parent = (
        await store.get_school_session(user_id, parent_session_id)
        if parent_session_id
        else None
    )
    if (
        not parent
        or parent.get("api_version") != "rebuild"
        or parent.get("flow_type") not in support.SUPPORT_PARENT_FLOWS
        or str(parent.get("profile_version_id") or "")
        != str(row.get("profile_version_id") or "")
        or str(parent.get("source_placement_report_id") or "")
        != str(row.get("source_placement_report_id") or "")
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": "school_support_lineage_invalid"},
        )
    return support.public_support_response(row, parent_session=parent)


@router.post("/curriculum/{session_id}/answer")
@school_route_owner("app.services.school_rebuild_curriculum")
async def answer_school_curriculum(
    session_id: UUID,
    req: SchoolCurriculumAnswerIn,
    request: Request,
) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    store = get_storage()
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "curriculum"
    ):
        raise HTTPException(status_code=404, detail={"code": "curriculum_session_not_found"})
    answer_hash = hashlib.sha256(req.answer.encode("utf-8")).hexdigest()
    existing_request = await store.get_school_answer_request(
        user_id, session_id, req.activity_id
    )
    if existing_request:
        request_status = str(existing_request.get("status") or "")
        if (
            request_status != "failed"
            and existing_request.get("answer_hash") != answer_hash
        ):
            raise HTTPException(
                status_code=409,
                detail={"code": "curriculum_answer_conflict"},
            )
        if request_status == "completed":
            return dict(existing_request.get("response_json") or {})
        if (
            request_status == "processing"
            and not existing_request.get("stale")
        ):
            raise HTTPException(
                status_code=409,
                detail={"code": "curriculum_answer_in_progress"},
            )
    if row.get("status") != "active":
        raise HTTPException(status_code=409, detail={"code": "curriculum_not_active"})
    try:
        activity = curriculum.curriculum_activity_for_answer(
            row.get("state_json") or {},
            activity_id=req.activity_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_curriculum_activity"},
        ) from exc

    claim = await store.claim_school_answer_request(
        user_id, session_id, req.activity_id, answer_hash
    )
    if claim.get("outcome") == "completed":
        return dict(claim.get("response_json") or {})
    if claim.get("outcome") == "in_progress":
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_answer_in_progress"},
        )
    if claim.get("outcome") == "conflict":
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_answer_conflict"},
        )
    if claim.get("outcome") != "claimed":
        raise RuntimeError("invalid_school_answer_request_claim")
    claim_token = str(claim.get("claim_token") or "")
    if not claim_token:
        raise RuntimeError("missing_school_answer_request_claim_token")

    try:
        open_answer_evaluation = None
        open_answer_preflight_failed = False
        evaluator_invoked = False
        evaluator_activity = curriculum.evaluator_activity_for_answer(
            activity,
            req.answer,
        )
        if evaluator_activity is not None:
            if not curriculum._open_answer_preflight(evaluator_activity, req.answer):
                open_answer_preflight_failed = True
            else:
                evaluator_invoked = True
                open_answer_evaluation = (
                    await _evaluate_school_open_answer_with_claim_heartbeat(
                        store=store,
                        user_id=user_id,
                        session_id=session_id,
                        activity_id=req.activity_id,
                        answer_hash=answer_hash,
                        claim_token=claim_token,
                        activity=evaluator_activity,
                        answer=req.answer,
                    )
                )
        try:
            updated_state, evaluation = curriculum.apply_curriculum_answer(
                row.get("state_json") or {},
                activity_id=req.activity_id,
                answer=req.answer,
                open_answer_evaluation=open_answer_evaluation,
                open_answer_preflight_failed=open_answer_preflight_failed,
            )
        except ValueError as exc:
            if str(exc) == "unexpected_curriculum_activity":
                raise HTTPException(
                    status_code=409,
                    detail={"code": "unexpected_curriculum_activity"},
                ) from exc
            if str(exc) in {
                "invalid_open_answer_evaluation_contract",
                "open_answer_evaluation_required",
                "untraceable_open_answer_evidence",
            }:
                raise HTTPException(
                    status_code=503,
                    detail={"code": "open_answer_evaluation_unavailable"},
                ) from exc
            raise

        learning_event = {
            "source_event_key": (
                f"school_rebuild:curriculum:{row['session_id']}:"
                f"{req.activity_id}:attempt:{evaluation.get('attempt_no', 1)}"
            ),
            "user_id": user_id,
            "domain": "school",
            "task_type": "school_rebuild_curriculum",
            "module_id": evaluation["level_id"],
            "session_id": row["session_id"],
            "node_id": req.activity_id,
            "skill_id": next(
                iter(evaluation.get("skill_ids") or []),
                f"curriculum.{evaluation['level_id']}",
            ),
            "source": "school_rebuild",
            "attempt_type": evaluation["kind"],
            "score": float(evaluation["score"]),
            "confidence": float(evaluation["confidence"]),
            "criteria_json": list(evaluation["criteria"]),
            "evidence_json": {
                "focus": evaluation["focus"],
                "activity_id": req.activity_id,
                "level_id": evaluation["level_id"],
                "skill_ids": list(evaluation.get("skill_ids") or []),
                "active_learning_class_no": updated_state.get("active_learning_class_no"),
                "chapter_id": (updated_state.get("chapter") or {}).get("chapter_id"),
                "evaluation_mode": evaluation.get("evaluation_mode"),
                "model_score": evaluation.get("model_score"),
                "language_detected": evaluation.get("language_detected"),
                "misconception_tags": list(evaluation.get("misconception_tags") or []),
            },
            "blockers": list(
                dict.fromkeys(
                    list(evaluation.get("blockers") or [])
                    + ([] if evaluation["correct"] else ["curriculum_gap"])
                )
            ),
            "gap": "" if evaluation["correct"] else str(evaluation["focus"]),
        }
        school_session = {
            "session_id": row["session_id"],
            "user_id": user_id,
            "api_version": row["api_version"],
            "flow_type": row["flow_type"],
            "subject_id": row["subject_id"],
            "class_no": int(row["class_no"]),
            "status": (
                "complete"
                if updated_state.get("status") == "complete"
                else "paused_for_masterclass"
                if updated_state.get("status") == "paused_for_masterclass"
                else "active"
            ),
            "current_stage": str(updated_state.get("current_level_index") or 0),
            "linked_session_id": row.get("linked_session_id"),
            "profile_version_id": row.get("profile_version_id"),
            "source_placement_report_id": row.get("source_placement_report_id"),
            "state_json": updated_state,
        }
        updated_row = {
            **row,
            "status": school_session["status"],
            "current_stage": school_session["current_stage"],
            "state_json": updated_state,
        }
        public_response = _public_session_with_school_coach(
            curriculum.public_curriculum_response(updated_row),
            updated_row,
        )
        certified_skill_scores: dict[str, float] = {}
        if (
            evaluation["kind"] == "chapter_check"
            and updated_state.get("status") == "complete"
            and updated_state.get("phase") == "complete"
        ):
            assessment_history = list(
                (updated_state.get("chapter_assessment") or {}).get("attempt_history")
                or []
            )
            final_result = assessment_history[-1] if assessment_history else {}
            if final_result.get("passed"):
                certified_skill_scores = {
                    str(skill_id): float(score)
                    for skill_id, score in dict(final_result.get("skill_scores") or {}).items()
                }
        await store.persist_school_curriculum_attempt(
            learning_event=learning_event,
            school_session=school_session,
            expected_state_json=row.get("state_json") or {},
            request_activity_id=req.activity_id,
            request_answer_hash=answer_hash,
            request_claim_token=claim_token,
            response_json=public_response,
            projection_evidence={
                "session_id": row["session_id"],
                "chapter_id": str(
                    (updated_state.get("chapter") or {}).get("chapter_id") or ""
                ),
                "level_id": evaluation["level_id"],
                "module_id": str(
                    (updated_state.get("chapter") or {}).get("chapter_id") or ""
                ),
                "task_type": "school_rebuild_curriculum",
                "focus": evaluation["focus"],
                "skill_ids": list(evaluation.get("skill_ids") or []),
                "attempt_type": evaluation["kind"],
                "score": float(evaluation["score"]),
                "confidence": float(evaluation["confidence"]),
                "criteria": list(evaluation.get("criteria") or []),
                "blockers": list(evaluation.get("blockers") or []),
                "answer_excerpt": req.answer,
                "attempt_passed": bool(evaluation["correct"]),
                "certified_skill_scores": certified_skill_scores,
            },
            language_evaluation=evaluation,
        )
        return public_response
    except TimeoutError as exc:
        logger.warning(
            "School open-answer evaluator timed out for activity %s",
            req.activity_id,
        )
        await store.fail_school_answer_request(
            user_id, session_id, req.activity_id, answer_hash, claim_token
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "open_answer_evaluation_timeout"},
        ) from exc
    except ValidationError as exc:
        await store.fail_school_answer_request(
            user_id, session_id, req.activity_id, answer_hash, claim_token
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "open_answer_evaluation_unavailable"},
        ) from exc
    except ValueError as exc:
        await store.fail_school_answer_request(
            user_id, session_id, req.activity_id, answer_hash, claim_token
        )
        if str(exc) in _SCHOOL_SESSION_WRITE_CONFLICTS:
            raise HTTPException(
                status_code=409,
                detail={"code": str(exc)},
            ) from exc
        if str(exc) in {"stale_school_answer_session", "stale_school_answer_request"}:
            raise HTTPException(
                status_code=409,
                detail={"code": "stale_curriculum_answer"},
            ) from exc
        raise
    except HTTPException:
        await store.fail_school_answer_request(
            user_id, session_id, req.activity_id, answer_hash, claim_token
        )
        raise
    except Exception as exc:
        logger.warning(
            "School curriculum answer failed for activity %s: %s",
            req.activity_id,
            type(exc).__name__,
        )
        await store.fail_school_answer_request(
            user_id, session_id, req.activity_id, answer_hash, claim_token
        )
        if evaluator_invoked and open_answer_evaluation is None:
            raise HTTPException(
                status_code=503,
                detail={"code": "open_answer_evaluation_unavailable"},
            ) from exc
        raise


async def _curriculum_parent_for_masterclass(
    *,
    user_id: str,
    session_id: str,
) -> tuple[object, dict, dict | None, dict | None]:
    store = get_storage()
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "curriculum"
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "curriculum_session_not_found"},
        )
    return store, row, public_profile, placement_report


def _school_session_write_payload(
    row: dict,
    *,
    status: str,
    state_json: dict,
    current_stage: str | None = None,
) -> dict:
    state_json = _state_with_school_coach(
        state_json,
        row.get("state_json"),
    )
    return {
        "session_id": row["session_id"],
        "user_id": row["user_id"],
        "api_version": row["api_version"],
        "flow_type": row["flow_type"],
        "subject_id": row["subject_id"],
        "class_no": int(row["class_no"]),
        "status": status,
        "current_stage": current_stage or str(row.get("current_stage") or ""),
        "linked_session_id": row.get("linked_session_id"),
        "profile_version_id": row.get("profile_version_id"),
        "source_placement_report_id": row.get("source_placement_report_id"),
        "state_json": state_json,
    }


@router.post("/curriculum/{session_id}/masterclass/start")
@school_route_owner("app.services.school_rebuild_masterclass")
async def start_school_curriculum_masterclass(
    session_id: UUID,
    request: Request,
) -> dict:
    user_id = _uid(request)
    await _require_canonical_school_action(
        request,
        {"start_masterclass", "resume_masterclass"},
        error_code="curriculum_not_paused_for_masterclass",
    )
    session_id = str(session_id)
    store, parent, _profile, _report = await _curriculum_parent_for_masterclass(
        user_id=user_id,
        session_id=session_id,
    )
    parent_state = dict(parent.get("state_json") or {})
    interrupt = parent_state.get("active_interrupt")
    if (
        parent.get("status") != "paused_for_masterclass"
        or not isinstance(interrupt, dict)
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_not_paused_for_masterclass"},
        )
    existing_id = str(interrupt.get("masterclass_session_id") or "")
    if existing_id:
        existing = await store.get_school_session(user_id, existing_id)
        if existing and existing.get("flow_type") == "masterclass":
            return _public_session_with_school_coach(
                masterclass.public_masterclass_response(existing),
                existing,
            )

    child_session_id = str(uuid4())
    child_state = _state_with_new_linked_school_coach(
        masterclass.new_masterclass_state(
            curriculum_session_id=session_id,
            curriculum_state=parent_state,
        )
    )
    child = await _get_or_create_school_session(
        store,
        session_id=child_session_id,
        user_id=user_id,
        api_version="rebuild",
        flow_type="masterclass",
        subject_id=parent["subject_id"],
        class_no=int(parent["class_no"]),
        status="active",
        current_stage="focused_practice",
        linked_session_id=session_id,
        profile_version_id=parent.get("profile_version_id"),
        source_placement_report_id=parent.get("source_placement_report_id"),
        state_json=child_state,
    )
    attached_state = curriculum.attach_masterclass_session(
        parent_state,
        masterclass_session_id=str(child["session_id"]),
    )
    await _upsert_school_session(
        store,
        **_school_session_write_payload(
            parent,
            status="paused_for_masterclass",
            state_json=attached_state,
        ),
    )
    return _public_session_with_school_coach(
        masterclass.public_masterclass_response(child),
        child,
    )


@router.get("/masterclass/{session_id}")
@school_route_owner("app.services.school_rebuild_masterclass")
async def get_school_masterclass(session_id: UUID, request: Request) -> dict:
    user_id = _uid(request)
    session_id = str(session_id)
    store = get_storage()
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "masterclass"
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "masterclass_session_not_found"},
        )
    return _public_session_with_school_coach(
        masterclass.public_masterclass_response(row),
        row,
    )


@router.post("/masterclass/{session_id}/answer")
@school_route_owner("app.services.school_rebuild_masterclass")
async def answer_school_masterclass(
    session_id: UUID,
    req: SchoolCurriculumAnswerIn,
    request: Request,
) -> dict:
    user_id = _uid(request)
    session_id = str(session_id)
    store = get_storage()
    answer_hash = hashlib.sha256(req.answer.encode("utf-8")).hexdigest()
    replay = await _school_answer_replay(
        store,
        user_id=user_id,
        session_id=session_id,
        activity_id=req.activity_id,
        answer_hash=answer_hash,
        conflict_code="masterclass_answer_conflict",
        in_progress_code="masterclass_answer_in_progress",
    )
    if replay is not None:
        return replay
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "masterclass"
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "masterclass_session_not_found"},
        )
    if row.get("status") != "active":
        raise HTTPException(
            status_code=409,
            detail={"code": "masterclass_not_active"},
        )
    try:
        updated_state, evaluation = masterclass.apply_masterclass_answer(
            row.get("state_json") or {},
            activity_id=req.activity_id,
            answer=req.answer,
        )
    except ValueError as exc:
        if str(exc) == "unexpected_masterclass_activity":
            raise HTTPException(
                status_code=409,
                detail={"code": "unexpected_masterclass_activity"},
            ) from exc
        raise
    claim = await _claim_school_answer(
        store,
        user_id=user_id,
        session_id=session_id,
        activity_id=req.activity_id,
        answer_hash=answer_hash,
        conflict_code="masterclass_answer_conflict",
        in_progress_code="masterclass_answer_in_progress",
    )
    if isinstance(claim, dict):
        return claim
    claim_token = claim
    learning_event = {
        "source_event_key": (
            f"school_rebuild:masterclass:{session_id}:"
            f"{req.activity_id}:attempt:{evaluation['attempt_no']}"
        ),
        "user_id": user_id,
        "domain": "school",
        "task_type": "school_rebuild_masterclass",
        "module_id": evaluation["level_id"],
        "session_id": session_id,
        "node_id": req.activity_id,
        "skill_id": next(
            iter(evaluation.get("skill_ids") or []),
            f"curriculum.{evaluation['level_id']}",
        ),
        "source": "school_rebuild",
        "attempt_type": "masterclass",
        "score": float(evaluation["score"]),
        "confidence": float(evaluation["confidence"]),
        "criteria_json": list(evaluation["criteria"]),
        "evidence_json": {
            "focus": evaluation["focus"],
            "level_id": evaluation["level_id"],
            "linked_curriculum_session_id": row.get("linked_session_id"),
        },
        "blockers": list(
            dict.fromkeys(
                list(evaluation.get("blockers") or [])
                + ([] if evaluation["correct"] else ["masterclass_gap"])
            )
        ),
        "gap": "" if evaluation["correct"] else evaluation["focus"],
    }
    school_session = _school_session_write_payload(
        row,
        status=updated_state["status"],
        current_stage=(
            "complete"
            if updated_state["status"] == "complete"
            else "focused_practice"
        ),
        state_json=updated_state,
    )
    public_response = _public_session_with_school_coach(
        masterclass.public_masterclass_response(school_session),
        school_session,
    )
    try:
        await store.persist_school_answer_attempt(
            learning_event=learning_event,
            school_session=school_session,
            expected_state_json=row.get("state_json") or {},
            request_activity_id=req.activity_id,
            request_answer_hash=answer_hash,
            request_claim_token=claim_token,
            response_json=public_response,
            projection_evidence={
                "session_id": session_id,
                "chapter_id": str(evaluation.get("chapter_id") or ""),
                "level_id": evaluation["level_id"],
                "module_id": str(evaluation.get("chapter_id") or evaluation["level_id"]),
                "task_type": "school_rebuild_masterclass",
                "focus": evaluation["focus"],
                "skill_ids": list(evaluation.get("skill_ids") or []),
                "attempt_type": "masterclass",
                "score": float(evaluation["score"]),
                "confidence": float(evaluation["confidence"]),
                "criteria": learning_event["criteria_json"],
                "blockers": learning_event["blockers"],
                "answer_excerpt": req.answer,
                "attempt_passed": bool(evaluation["correct"]),
            },
        )
    except Exception as exc:
        await store.fail_school_answer_request(
            user_id,
            session_id,
            req.activity_id,
            answer_hash,
            claim_token,
        )
        if isinstance(exc, ValueError) and str(exc) in _SCHOOL_SESSION_WRITE_CONFLICTS:
            raise HTTPException(status_code=409, detail={"code": str(exc)}) from exc
        raise
    return public_response


@router.post("/curriculum/{session_id}/resume-masterclass")
@school_route_owner("app.services.school_rebuild_masterclass")
async def resume_school_curriculum_masterclass(
    session_id: UUID,
    request: Request,
) -> dict:
    user_id = _uid(request)
    session_id = str(session_id)
    store, parent, _profile, _report = await _curriculum_parent_for_masterclass(
        user_id=user_id,
        session_id=session_id,
    )
    parent_state = dict(parent.get("state_json") or {})
    interrupt = parent_state.get("active_interrupt")
    if not isinstance(interrupt, dict):
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_not_paused_for_masterclass"},
        )
    child_id = str(interrupt.get("masterclass_session_id") or "")
    child = await store.get_school_session(user_id, child_id) if child_id else None
    if not child or child.get("flow_type") != "masterclass" or child.get("status") != "complete":
        raise HTTPException(
            status_code=409,
            detail={"code": "masterclass_not_complete"},
        )
    resumed = curriculum.resume_after_masterclass(
        parent_state,
        masterclass_session_id=child_id,
        resolution="complete",
    )
    parent_write = _school_session_write_payload(
        parent,
        status="active",
        state_json=resumed,
    )
    updated_parent = {**parent, **parent_write}
    changed = await store.compare_and_set_school_session(
        school_session=parent_write,
        expected_state_json=parent_state,
    )
    if not changed:
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_masterclass_transition_conflict"},
        )
    return _public_session_with_school_coach(
        curriculum.public_curriculum_response(updated_parent),
        updated_parent,
    )


@router.post("/curriculum/{session_id}/abandon-masterclass")
@school_route_owner("app.services.school_rebuild_masterclass")
async def abandon_school_curriculum_masterclass(
    session_id: UUID,
    request: Request,
) -> dict:
    user_id = _uid(request)
    session_id = str(session_id)
    store, parent, _profile, _report = await _curriculum_parent_for_masterclass(
        user_id=user_id,
        session_id=session_id,
    )
    parent_state = dict(parent.get("state_json") or {})
    interrupt = parent_state.get("active_interrupt")
    if not isinstance(interrupt, dict):
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_not_paused_for_masterclass"},
        )
    child_id = str(interrupt.get("masterclass_session_id") or "")
    if child_id:
        child = await store.get_school_session(user_id, child_id)
        if child and child.get("status") == "active":
            abandoned_state = {
                **dict(child.get("state_json") or {}),
                "status": "abandoned",
            }
            await _upsert_school_session(
                store,
                **_school_session_write_payload(
                    child,
                    status="abandoned",
                    state_json=abandoned_state,
                ),
            )
    resolution_id = child_id or f"not-started:{interrupt.get('interrupt_id') or ''}"
    resumed = curriculum.resume_after_masterclass(
        parent_state,
        masterclass_session_id=resolution_id,
        resolution="abandoned",
    )
    parent_write = _school_session_write_payload(
        parent,
        status="active",
        state_json=resumed,
    )
    updated_parent = {**parent, **parent_write}
    changed = await store.compare_and_set_school_session(
        school_session=parent_write,
        expected_state_json=parent_state,
    )
    if not changed:
        raise HTTPException(
            status_code=409,
            detail={"code": "curriculum_masterclass_transition_conflict"},
        )
    return _public_session_with_school_coach(
        curriculum.public_curriculum_response(updated_parent),
        updated_parent,
    )


@router.get("/onboarding")
@school_route_owner("app.services.school_rebuild_profile")
async def school_onboarding(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    active = await store.get_active_school_profile_version(user_id)
    draft = await store.get_school_profile_draft(user_id)
    return _school_onboarding_response(active=active, draft=draft)


def _school_onboarding_response(*, active: dict | None, draft: dict | None) -> dict:
    public_active = public_school_profile(active) if active else None
    public_draft = public_school_profile_draft(draft) if draft else None
    profile_status = "complete" if public_active else "incomplete" if public_draft else "missing"
    return {
        "profile_status": profile_status,
        "active_profile": public_active,
        "draft": public_draft,
        "profile": public_active,
    }


_SCHOOL_DRAFT_CONFLICT_CODES = {
    "school_draft_lineage_required",
    "school_draft_request_conflict",
    "school_draft_profile_conflict",
    "school_draft_revision_conflict",
    "school_draft_not_found",
}
_SCHOOL_ACTIVATION_CONFLICT_CODES = {
    "school_activation_request_conflict",
    "school_activation_result_missing",
    "school_profile_not_found",
    "school_profile_revision_conflict",
    "school_profile_already_active",
    "school_profile_not_draft",
}


@router.post("/onboarding")
@school_route_owner("app.services.school_rebuild_profile")
async def save_school_onboarding(
    req: SchoolOnboardingDraftPatchIn,
    request: Request,
) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    try:
        draft = await store.save_school_profile_draft(
            user_id=user_id,
            profile_version_id=(
                str(req.profile_version_id) if req.profile_version_id else None
            ),
            expected_revision=req.expected_revision,
            current_step=req.current_step,
            request_id=str(req.request_id),
            payload_hash=req.payload_hash(),
            patch=req.profile_patch(),
        )
    except ValueError as exc:
        code = str(exc)
        if code in _SCHOOL_DRAFT_CONFLICT_CODES:
            raise HTTPException(status_code=409, detail={"code": code}) from exc
        raise
    active = await store.get_active_school_profile_version(user_id)
    return _school_onboarding_response(active=active, draft=draft)


@router.post("/onboarding/complete")
@school_route_owner("app.services.school_rebuild_profile")
async def complete_school_onboarding(
    req: SchoolOnboardingCompleteIn,
    request: Request,
) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    profile_version_id = str(req.profile_version_id)
    persisted = await store.get_school_profile_version(user_id, profile_version_id)
    if persisted is None:
        raise HTTPException(
            status_code=409,
            detail={"code": "school_profile_not_found"},
        )
    if int(persisted.get("draft_revision") or 1) != req.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": "school_profile_revision_conflict"},
        )
    try:
        SchoolRebuildProfileIn.model_validate(
            {field: persisted.get(field) for field in SCHOOL_PROFILE_FIELDS}
        )
    except ValidationError as exc:
        errors = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        raise HTTPException(
            status_code=422,
            detail={"code": "school_profile_incomplete", "errors": errors},
        ) from exc
    _require_available_school_selection(persisted)
    try:
        saved = await store.activate_school_profile_draft(
            user_id=user_id,
            profile_version_id=profile_version_id,
            expected_revision=req.expected_revision,
            request_id=str(req.request_id),
            payload_hash=req.payload_hash(),
        )
    except ValueError as exc:
        code = str(exc)
        if code in _SCHOOL_ACTIVATION_CONFLICT_CODES:
            raise HTTPException(status_code=409, detail={"code": code}) from exc
        raise
    public = public_school_profile(saved)
    return {"profile_status": "complete", "profile": public}


@router.post("/placement/start")
@school_route_owner("app.services.school_rebuild_placement")
async def start_school_placement(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    for attempt in range(2):
        active_profile = await store.get_active_school_profile_version(user_id)
        if not active_profile:
            raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
        profile = public_school_profile(active_profile)
        _require_available_school_selection(profile)
        subject_id = (profile.get("subject_ids") or ["english"])[0]
        target_class_no = int(profile["target_class_no"])
        if not placement.placement_supported(subject_id, target_class_no):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "placement_slice_not_ready",
                    "supported_target_class_nos": [2, 3, 4, 5],
                },
            )

        canonical_state = await school_state(request)
        allowed_next_actions = canonical_state.get("allowed_next_actions")
        if not isinstance(allowed_next_actions, list):
            allowed_next_actions = []
        next_action = canonical_state.get("next_action")
        authorized_action = (
            next_action in {"start_placement", "resume_placement"}
            and next_action in allowed_next_actions
        )
        if not authorized_action:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "school_placement_start_not_allowed",
                    "next_action": next_action,
                    "allowed_next_actions": allowed_next_actions,
                },
            )

        session_id = str(uuid4())
        envelope = placement.new_placement_envelope(profile)
        try:
            row = await store.get_or_create_active_school_placement_session(
                session_id=session_id,
                user_id=user_id,
                profile_version_id=str(profile["profile_version_id"]),
                subject_id=subject_id,
                class_no=target_class_no,
                current_stage=envelope.state.stage,
                state_json=_state_with_school_coach(
                    placement.envelope_to_json(envelope),
                    profile,
                ),
            )
        except ValueError as exc:
            code = str(exc)
            if code == "stale_school_profile_lineage" and attempt == 0:
                continue
            if code in _SCHOOL_SESSION_WRITE_CONFLICTS:
                raise HTTPException(status_code=409, detail={"code": code}) from exc
            raise
        winner_envelope = placement.envelope_from_json(row.get("state_json") or {})
        return _public_session_with_school_coach(
            placement.placement_response(
                session_id=row["session_id"],
                envelope=winner_envelope,
            ),
            row,
        )
    raise HTTPException(status_code=409, detail={"code": "stale_school_profile_lineage"})


async def _ensure_school_placement_report(
    *,
    user_id: str,
    profile: dict,
    placement_row: dict,
) -> dict:
    store = get_storage()
    existing = await store.get_school_placement_report(
        user_id,
        placement_row["session_id"],
        profile_version_id=str(profile["profile_version_id"]),
    )
    report = reports.build_placement_report(
        user_id=user_id,
        placement_session_id=placement_row["session_id"],
        placement_row=placement_row,
        learning_events=await _learning_events(user_id),
        report_id=existing.get("report_id") if existing else None,
    )
    return await store.upsert_school_placement_report(**report)


async def _public_school_placement_report(
    *,
    user_id: str,
    report: dict,
    fallback_profile: dict,
) -> dict:
    placement_row = await get_storage().get_school_session(
        user_id,
        str(report["placement_session_id"]),
    )
    placement_state = (
        placement_row.get("state_json")
        if isinstance(placement_row, dict)
        and isinstance(placement_row.get("state_json"), dict)
        else None
    )
    identity = school_coach_identity(placement_state)
    coach_source = placement_state if all(identity.values()) else fallback_profile
    return reports.public_placement_report(
        report,
        coach_source=coach_source,
    )


@router.get("/placement/report")
@school_route_owner("app.services.school_rebuild_report")
async def get_school_placement_report(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    active_profile = await get_storage().get_active_school_profile_version(user_id)
    if not active_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    profile = public_school_profile(active_profile)
    compatible_report = await _latest_placement_report_for_profile(user_id, profile)
    if compatible_report:
        return await _public_school_placement_report(
            user_id=user_id,
            report=compatible_report,
            fallback_profile=profile,
        )
    placement_row = await _latest_placement_for_profile(user_id, profile)
    if not placement_row:
        raise HTTPException(status_code=404, detail={"code": "placement_session_not_found"})
    if placement_row.get("status") == "active":
        raise HTTPException(status_code=409, detail={"code": "placement_in_progress"})

    saved = await _ensure_school_placement_report(
        user_id=user_id,
        profile=profile,
        placement_row=placement_row,
    )
    return await _public_school_placement_report(
        user_id=user_id,
        report=saved,
        fallback_profile=profile,
    )


@router.get("/placement/{session_id}")
@school_route_owner("app.services.school_rebuild_placement")
async def get_school_placement(session_id: UUID, request: Request) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    await _learner_profile(user_id)
    active_profile = await get_storage().get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    row = await get_storage().get_school_session(user_id, session_id)
    if (
        not _matches_profile_lineage(row, public_profile)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "placement"
    ):
        raise HTTPException(status_code=404, detail={"code": "placement_session_not_found"})
    row = await _placement_row_with_effective_status(row)
    envelope = placement.envelope_from_json(row.get("state_json") or {})
    return _public_session_with_school_coach(
        placement.placement_response(
            session_id=row["session_id"],
            envelope=envelope,
        ),
        row,
    )


@router.post("/placement/{session_id}/answer")
@school_route_owner("app.services.school_rebuild_placement")
async def answer_school_placement(
    session_id: UUID,
    req: SchoolPlacementAnswerIn,
    request: Request,
) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    answer_hash = hashlib.sha256(req.answer.encode("utf-8")).hexdigest()
    replay = await _school_answer_replay(
        store,
        user_id=user_id,
        session_id=session_id,
        activity_id=req.item_id,
        answer_hash=answer_hash,
        conflict_code="placement_answer_conflict",
        in_progress_code="placement_answer_in_progress",
    )
    if replay is not None:
        return replay
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_profile_lineage(row, public_profile)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "placement"
    ):
        raise HTTPException(status_code=404, detail={"code": "placement_session_not_found"})
    row = await _placement_row_with_effective_status(row)
    envelope = placement.envelope_from_json(row.get("state_json") or {})
    if row.get("status") != "active":
        if row.get("status") in {"complete", "insufficient_evidence"}:
            await _ensure_school_placement_report(
                user_id=user_id,
                profile=public_profile,
                placement_row=row,
            )
        return _public_session_with_school_coach(
            placement.placement_response(
                session_id=row["session_id"],
                envelope=envelope,
            ),
            row,
        )
    expected = placement.next_item(envelope)
    if expected is None:
        return _public_session_with_school_coach(
            placement.placement_response(
                session_id=row["session_id"],
                envelope=envelope,
            ),
            row,
        )
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_placement_item", "expected_item_id": expected.item_id},
        )

    item = placement.find_item(envelope, req.item_id)
    claim = await _claim_school_answer(
        store,
        user_id=user_id,
        session_id=session_id,
        activity_id=req.item_id,
        answer_hash=answer_hash,
        conflict_code="placement_answer_conflict",
        in_progress_code="placement_answer_in_progress",
    )
    if isinstance(claim, dict):
        return claim
    claim_token = claim
    try:
        async def placement_provider(activity: dict, answer: str):
            return await _evaluate_school_open_answer_with_claim_heartbeat(
                store=store,
                user_id=user_id,
                session_id=session_id,
                activity_id=req.item_id,
                answer_hash=answer_hash,
                claim_token=claim_token,
                activity=activity,
                answer=answer,
            )

        try:
            evaluation = await placement_evaluator.evaluate_school_placement_item(
                item,
                req.answer,
                provider=placement_provider,
            )
        except placement_evaluator.SchoolPlacementEvaluatorUnavailableError as exc:
            raise HTTPException(
                status_code=503,
                detail={"code": placement_evaluator.EVALUATOR_UNAVAILABLE_CODE},
            ) from exc

        if "language_mismatch" in evaluation.blockers:
            raise HTTPException(
                status_code=422,
                detail={"code": "placement_english_response_required"},
            )

        score = float(evaluation.score)
        confidence = float(evaluation.confidence)
        updated = placement.apply_evaluated_attempt(
            envelope,
            item,
            evaluator_score=score,
            evaluator_confidence=confidence,
            certifying_blockers=tuple(evaluation.blockers),
        )
        status = placement.placement_status(updated)
        learning_event = {
            "source_event_key": (
                f"school_rebuild:placement:{row['session_id']}:{item.item_id}"
            ),
            "user_id": user_id,
            "domain": "school",
            "task_type": "school_rebuild_placement",
            "module_id": item.subject_id,
            "session_id": row["session_id"],
            "node_id": item.item_id,
            "skill_id": item.skill_ids[0],
            "source": "school_rebuild",
            "attempt_type": item.stage,
            "score": score,
            "confidence": confidence,
            "criteria_json": [
                criterion.model_dump() for criterion in evaluation.criteria
            ],
            "evidence_json": {
                "profile_version_id": updated.profile_version_id,
                "target_class_no": item.target_class_no,
                "source_class_no": item.source_class_no,
                "diagnostic_stage": item.stage,
                "item_type": item.item_type,
                "evaluation_mode": item.evaluation_mode,
                "learner_skill_label": item.learner_skill_label,
                "language_detected": evaluation.language_detected,
                "misconception_tags": list(evaluation.misconception_tags),
            },
            "blockers": list(evaluation.blockers),
            "gap": (
                ""
                if placement.classify_placement_evidence(
                    evaluator_score=score,
                    evaluator_confidence=confidence,
                    certifying_blockers=tuple(evaluation.blockers),
                ) == "pass"
                else ",".join(
                    tuple(evaluation.misconception_tags)
                    or item.misconception_tags
                    or ("placement_gap",)
                )
            ),
        }
        state_json = _state_with_school_coach(
            placement.envelope_to_json(updated),
            row.get("state_json"),
        )
        school_session = {
            "session_id": row["session_id"],
            "user_id": user_id,
            "api_version": "rebuild",
            "flow_type": "placement",
            "subject_id": row["subject_id"],
            "class_no": int(row["class_no"]),
            "status": "active" if status == "in_progress" else status,
            "current_stage": updated.state.stage,
            "profile_version_id": row.get("profile_version_id"),
            "source_placement_report_id": None,
            "state_json": state_json,
        }
        public_response = _public_session_with_school_coach(
            placement.placement_response(
                session_id=row["session_id"],
                envelope=updated,
            ),
            {**row, "state_json": state_json},
        )
        placement_report = None
        if status != "in_progress":
            terminal_row = {
                **row,
                "status": status,
                "current_stage": updated.state.stage,
                "state_json": state_json,
            }
            existing_report = await store.get_school_placement_report(
                user_id,
                row["session_id"],
                profile_version_id=str(public_profile["profile_version_id"]),
            )
            placement_report = reports.build_placement_report(
                user_id=user_id,
                placement_session_id=row["session_id"],
                placement_row=terminal_row,
                learning_events=[
                    *(await _learning_events(user_id)),
                    learning_event,
                ],
                report_id=(existing_report or {}).get("report_id"),
            )
        await store.persist_school_answer_attempt(
            learning_event=learning_event,
            school_session=school_session,
            expected_state_json=row.get("state_json") or {},
            request_activity_id=req.item_id,
            request_answer_hash=answer_hash,
            request_claim_token=claim_token,
            response_json=public_response,
            placement_report=placement_report,
            projection_evidence={
                "session_id": row["session_id"],
                "chapter_id": "",
                "level_id": item.stage,
                "module_id": item.subject_id,
                "task_type": "school_rebuild_placement",
                "focus": item.learner_skill_label,
                "skill_ids": list(item.skill_ids),
                "attempt_type": item.stage,
                "score": score,
                "confidence": confidence,
                "criteria": learning_event["criteria_json"],
                "blockers": learning_event["blockers"],
                "answer_excerpt": req.answer,
                "attempt_passed": not learning_event["gap"],
                "placement_ready_skill_confidence": {
                    str(skill_id): float(skill_state.last_confidence)
                    for skill_id, skill_state in updated.state.skill_states.items()
                    if skill_state.ready_source == "placement"
                },
            },
        )
    except Exception as exc:
        await store.fail_school_answer_request(
            user_id,
            session_id,
            req.item_id,
            answer_hash,
            claim_token,
        )
        if isinstance(exc, ValueError):
            code = str(exc)
            if code in _SCHOOL_SESSION_WRITE_CONFLICTS or code in {
                "stale_school_answer_session",
                "stale_school_answer_request",
            }:
                raise HTTPException(status_code=409, detail={"code": code}) from exc
        raise
    return public_response


@router.post("/placement/{session_id}/abandon")
@school_route_owner("app.services.school_rebuild_placement")
async def abandon_school_placement(session_id: UUID, request: Request) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_profile_lineage(row, public_profile)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "placement"
    ):
        raise HTTPException(
            status_code=404,
            detail={"code": "placement_session_not_found"},
        )
    row = await _placement_row_with_effective_status(row)
    envelope = placement.envelope_from_json(row.get("state_json") or {})
    if row.get("status") == "abandoned":
        await _ensure_school_placement_report(
            user_id=user_id,
            profile=public_profile,
            placement_row=row,
        )
        return _public_session_with_school_coach(
            placement.placement_response(
                session_id=session_id,
                envelope=envelope,
            ),
            row,
        )
    if row.get("status") != "active":
        raise HTTPException(status_code=409, detail={"code": "placement_not_active"})

    abandoned = placement.abandon_placement(envelope)
    state_json = _state_with_school_coach(
        placement.envelope_to_json(abandoned),
        row.get("state_json"),
    )
    terminal_row = {
        **row,
        "status": "abandoned",
        "current_stage": abandoned.state.stage,
        "state_json": state_json,
    }
    await _upsert_school_session(
        store,
        session_id=session_id,
        user_id=user_id,
        api_version="rebuild",
        flow_type="placement",
        subject_id=row["subject_id"],
        class_no=int(row["class_no"]),
        status="abandoned",
        current_stage=abandoned.state.stage,
        linked_session_id=row.get("linked_session_id"),
        profile_version_id=row.get("profile_version_id"),
        source_placement_report_id=None,
        state_json=state_json,
    )
    await _ensure_school_placement_report(
        user_id=user_id,
        profile=public_profile,
        placement_row=terminal_row,
    )
    return _public_session_with_school_coach(
        placement.placement_response(
            session_id=session_id,
            envelope=abandoned,
        ),
        terminal_row,
    )


@router.post("/recap/start")
@school_route_owner("app.services.school_rebuild_recap")
async def start_school_recap(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    active_profile = await get_storage().get_active_school_profile_version(user_id)
    if not active_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    profile = public_school_profile(active_profile)
    _require_available_school_selection(profile)
    await _require_canonical_school_action(
        request,
        {"start_recap", "resume_recap"},
        error_code="recap_not_required",
    )
    report = await _latest_placement_report_for_profile(
        user_id,
        profile,
    )
    if not report:
        raise HTTPException(status_code=409, detail={"code": "placement_report_required"})
    if report.get("placement_status") != "below_target":
        raise HTTPException(status_code=409, detail={"code": "recap_not_required"})

    existing = await _latest_recap_for_profile(
        user_id,
        profile,
        str(report["report_id"]),
    )
    if existing:
        return _public_session_with_school_coach(
            recap.public_recap_response(existing),
            existing,
        )

    session_id = str(uuid4())
    state_json = _state_with_school_coach(
        recap.new_recap_state(report),
        profile,
    )
    row = await _get_or_create_school_session(
        get_storage(),
        session_id=session_id,
        user_id=user_id,
        api_version="rebuild",
        flow_type="recap",
        subject_id=report["subject_id"],
        class_no=int(report["target_class_no"]),
        status="active",
        current_stage="recap_path",
        linked_session_id=report["placement_session_id"],
        profile_version_id=str(profile["profile_version_id"]),
        source_placement_report_id=str(report["report_id"]),
        state_json=state_json,
    )
    if not row:
        raise HTTPException(status_code=500, detail={"code": "recap_session_create_failed"})
    return _public_session_with_school_coach(
        recap.public_recap_response(row),
        row,
    )


@router.get("/recap")
@school_route_owner("app.services.school_rebuild_recap")
async def get_active_school_recap(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    active_profile = await get_storage().get_active_school_profile_version(user_id)
    if not active_profile:
        raise HTTPException(status_code=409, detail={"code": "school_profile_required"})
    profile = public_school_profile(active_profile)
    report = await _latest_placement_report_for_profile(user_id, profile)
    latest = await _latest_recap_for_profile(
        user_id,
        profile,
        str(report["report_id"]) if report else None,
    )
    if not latest:
        raise HTTPException(status_code=404, detail={"code": "recap_session_not_found"})
    return _public_session_with_school_coach(
        recap.public_recap_response(latest),
        latest,
    )


@router.post("/recap/{session_id}/answer")
@school_route_owner("app.services.school_rebuild_recap")
async def answer_school_recap(
    session_id: UUID,
    req: SchoolRecapAnswerIn,
    request: Request,
) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    await _learner_profile(user_id)
    store = get_storage()
    answer_hash = hashlib.sha256(req.answer.encode("utf-8")).hexdigest()
    replay = await _school_answer_replay(
        store,
        user_id=user_id,
        session_id=session_id,
        activity_id=req.activity_id,
        answer_hash=answer_hash,
        conflict_code="recap_answer_conflict",
        in_progress_code="recap_answer_in_progress",
    )
    if replay is not None:
        return replay
    active_profile = await store.get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await store.get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "recap"
    ):
        raise HTTPException(status_code=404, detail={"code": "recap_session_not_found"})
    if row.get("status") != "active":
        raise HTTPException(status_code=409, detail={"code": "recap_not_active"})
    try:
        activity = recap.recap_activity_for_answer(
            row.get("state_json") or {},
            activity_id=req.activity_id,
        )
    except ValueError as exc:
        if str(exc) == "unexpected_recap_activity":
            raise HTTPException(
                status_code=409,
                detail={"code": "unexpected_recap_activity"},
            ) from exc
        raise

    claim = await _claim_school_answer(
        store,
        user_id=user_id,
        session_id=session_id,
        activity_id=req.activity_id,
        answer_hash=answer_hash,
        conflict_code="recap_answer_conflict",
        in_progress_code="recap_answer_in_progress",
    )
    if isinstance(claim, dict):
        return claim
    claim_token = claim
    try:
        open_answer_evaluation = None
        evaluator_activity = recap.evaluator_activity_for_answer(activity)
        if evaluator_activity is not None:
            open_answer_evaluation = (
                await _evaluate_school_open_answer_with_claim_heartbeat(
                    store=store,
                    user_id=user_id,
                    session_id=session_id,
                    activity_id=req.activity_id,
                    answer_hash=answer_hash,
                    claim_token=claim_token,
                    activity=evaluator_activity,
                    answer=req.answer,
                )
            )
        try:
            updated_state, evaluation = recap.apply_recap_answer(
                row.get("state_json") or {},
                activity_id=req.activity_id,
                answer=req.answer,
                open_answer_evaluation=open_answer_evaluation,
            )
        except ValueError as exc:
            if str(exc) in {
                "invalid_open_answer_evaluation_contract",
                "open_answer_evaluation_required",
                "recap_open_answer_rubric_missing",
                "untraceable_open_answer_evidence",
            }:
                raise HTTPException(
                    status_code=503,
                    detail={"code": "open_answer_evaluation_unavailable"},
                ) from exc
            raise

        learning_event = {
            "source_event_key": (
                f"school_rebuild:recap:{row['session_id']}:"
                f"{req.activity_id}:attempt:{evaluation.get('attempt_no', 1)}"
            ),
            "user_id": user_id,
            "domain": "school",
            "task_type": "school_rebuild_recap",
            "module_id": evaluation["module_id"],
            "session_id": row["session_id"],
            "node_id": req.activity_id,
            "skill_id": next(
                iter(evaluation.get("skill_ids") or []),
                f"recap.{evaluation['module_id']}",
            ),
            "source": "school_rebuild",
            "attempt_type": evaluation["kind"],
            "score": float(evaluation["score"]),
            "confidence": float(evaluation["confidence"]),
            "criteria_json": list(evaluation["criteria"]),
            "evidence_json": {
                "focus": evaluation["focus"],
                "activity_id": req.activity_id,
                "module_id": evaluation["module_id"],
                "skill_ids": list(evaluation.get("skill_ids") or []),
                "active_learning_class_no": updated_state.get(
                    "active_learning_class_no"
                ),
                "activity_source_class_no": evaluation.get("source_class_no"),
                "evaluation_mode": evaluation.get("evaluation_mode"),
                "model_score": evaluation.get("model_score"),
                "language_detected": evaluation.get("language_detected"),
                "misconception_tags": list(
                    evaluation.get("misconception_tags") or []
                ),
            },
            "blockers": list(
                dict.fromkeys(
                    list(evaluation.get("blockers") or [])
                    + ([] if evaluation["correct"] else ["recap_gap"])
                )
            ),
            "gap": "" if evaluation["correct"] else str(evaluation["focus"]),
        }
        school_session = {
            "session_id": row["session_id"],
            "user_id": user_id,
            "api_version": row["api_version"],
            "flow_type": row["flow_type"],
            "subject_id": row["subject_id"],
            "class_no": int(row["class_no"]),
            "status": (
                "complete" if updated_state.get("status") == "complete" else "active"
            ),
            "current_stage": str(updated_state.get("current_module_index") or 0),
            "linked_session_id": row.get("linked_session_id"),
            "profile_version_id": row.get("profile_version_id"),
            "source_placement_report_id": row.get("source_placement_report_id"),
            "state_json": updated_state,
        }
        public_response = _public_session_with_school_coach(
            recap.public_recap_response({**row, **school_session}),
            {**row, **school_session},
        )
        await store.persist_school_answer_attempt(
            learning_event=learning_event,
            school_session=school_session,
            expected_state_json=row.get("state_json") or {},
            request_activity_id=req.activity_id,
            request_answer_hash=answer_hash,
            request_claim_token=claim_token,
            response_json=public_response,
            projection_evidence={
                "session_id": row["session_id"],
                "chapter_id": evaluation["module_id"],
                "level_id": evaluation["module_id"],
                "module_id": evaluation["module_id"],
                "task_type": "school_rebuild_recap",
                "focus": evaluation["focus"],
                "skill_ids": list(evaluation.get("skill_ids") or []),
                "attempt_type": evaluation["kind"],
                "score": float(evaluation["score"]),
                "confidence": float(evaluation["confidence"]),
                "criteria": learning_event["criteria_json"],
                "blockers": learning_event["blockers"],
                "answer_excerpt": req.answer,
                "attempt_passed": bool(evaluation["correct"]),
            },
            language_evaluation=evaluation,
        )
    except Exception as exc:
        await store.fail_school_answer_request(
            user_id,
            session_id,
            req.activity_id,
            answer_hash,
            claim_token,
        )
        if isinstance(exc, ValueError):
            code = str(exc)
            if code in _SCHOOL_SESSION_WRITE_CONFLICTS or code in {
                "stale_school_answer_session",
                "stale_school_answer_request",
            }:
                raise HTTPException(status_code=409, detail={"code": code}) from exc
        raise
    return public_response


@router.get("/recap/{session_id}")
@school_route_owner("app.services.school_rebuild_recap")
async def get_school_recap(session_id: UUID, request: Request) -> dict:
    session_id = str(session_id)
    user_id = _uid(request)
    await _learner_profile(user_id)
    active_profile = await get_storage().get_active_school_profile_version(user_id)
    public_profile = public_school_profile(active_profile) if active_profile else None
    placement_report = (
        await _latest_placement_report_for_profile(user_id, public_profile)
        if public_profile
        else None
    )
    row = await get_storage().get_school_session(user_id, session_id)
    if (
        not _matches_report_lineage(row, public_profile, placement_report)
        or row.get("api_version") != "rebuild"
        or row.get("flow_type") != "recap"
    ):
        raise HTTPException(status_code=404, detail={"code": "recap_session_not_found"})
    return _public_session_with_school_coach(
        recap.public_recap_response(row),
        row,
    )
