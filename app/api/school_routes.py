"""School curriculum + assessment API.

The legacy session API has no test path. This exposes the NCERT class -> chapter
structure and a serve / submit / score loop for chapter tests and milestone exams,
backed by the deterministic assessment engine. Answer keys stay server-side: the
learner receives items, submits answers, and gets a scored report naming the exact
skills they still need to work on.
"""
import logging
import time
from dataclasses import replace as dataclass_replace
from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from app.content import curriculum as cur
from app.content.assessment import milestone_due, score_assessment
from app.services.school_v2_placement import (
    PlacementSessionState,
    placement_outcome,
    state_from_json as placement_state_from_json,
    state_to_json as placement_state_to_json,
)
from app.services.school_v2_placement_flow import (
    apply_answer,
    find_item,
    next_item,
    public_item,
    readiness_summary,
    record_placement_attempts,
    required_skill_ids,
)
from app.services.school_v2_practice_flow import (
    apply_practice_answer,
    lesson_for_skill,
    next_practice_item,
    practice_status,
    public_lesson,
    public_practice_item,
    record_practice_attempt,
    state_from_json as practice_state_from_json,
    state_from_profile as practice_state_from_profile,
    state_to_json as practice_state_to_json,
)
from app.services.school_v2_curriculum_flow import (
    apply_chapter_answer,
    chapter_for_id,
    chapter_score,
    curriculum_status,
    find_chapter_item,
    first_chapter_for_class,
    next_chapter_item,
    public_chapter,
    public_chapter_item,
    public_chapter_lesson,
    record_chapter_attempt,
    state_from_json as curriculum_state_from_json,
    state_from_profiles as curriculum_state_from_profiles,
    state_to_json as curriculum_state_to_json,
)
from app.services.school_v2_readiness import classify_skill_status
from app.services import school_v3_runtime as v3
from app.services.school_v3_readiness_path import build_readiness_path
from app.services.school_v3_evaluator import grade_deterministic_item
from app.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/school", tags=["school"])


class SchoolV2PlacementStart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = "english"
    target_class_no: int = Field(default=5, ge=5, le=5)
    preferred_language: str = Field(default="en", pattern="^(|en)$")


class SchoolV2PlacementAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    answer: str


class SchoolV2PracticeStart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = "english"
    target_class_no: int = Field(default=5, ge=5, le=5)
    skill_id: str


class SchoolV2PracticeAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    answer: str


class SchoolV2CurriculumStart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = "english"
    target_class_no: int = Field(default=5, ge=5, le=5)
    chapter_id: str


class SchoolV2CurriculumAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    answer: str


class SchoolV3PlacementStart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = "english"
    target_class_no: int = Field(default=2, ge=2, le=5)
    preferred_language: str = Field(default="en", pattern="^(en|hi|hi_en)$")


class SchoolV3Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    answer: str


class SchoolV3CurriculumStart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = "english"
    target_class_no: int = Field(default=2, ge=2, le=5)
    chapter_id: str
    watchlist_skill_ids: list[str] = Field(default_factory=list)


class SchoolV3PathRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = "english"
    target_class_no: int = Field(default=2, ge=2, le=5)
    weak_skill_ids: list[str] = Field(default_factory=list)
    non_blocking_weak_skill_ids: list[str] = Field(default_factory=list)


def _uid(request: Request) -> str:
    return getattr(request.state, "user_id", None) or ""


def _public_item(item) -> dict:
    """Strip the answer key — a learner must never receive it with the question."""
    return {"id": item.id, "type": item.type, "prompt": item.prompt,
            "options": item.options, "skill": item.skill}


def _require_uid(request: Request) -> str:
    user_id = _uid(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


async def _require_existing_uid(request: Request) -> str:
    user_id = _require_uid(request)
    if not await get_storage().get_profile(user_id):
        raise HTTPException(status_code=401, detail="Profile not found; sign in again")
    return user_id


async def _persist_placement_row(
    *,
    store,
    placement_session_id: str,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    preferred_language: str,
    status: str,
    state: PlacementSessionState,
) -> None:
    await store.upsert_school_v2_placement_session(
        placement_session_id=placement_session_id,
        user_id=user_id,
        subject_id=subject_id,
        target_class_no=target_class_no,
        preferred_language=preferred_language,
        status=status,
        state_json=placement_state_to_json(state),
    )


def _placement_response(
    *,
    placement_session_id: str,
    subject_id: str,
    target_class_no: int,
    preferred_language: str,
    status: str,
    state: PlacementSessionState,
    resume: bool = False,
) -> dict:
    item = next_item(state)
    return {
        "placement_session_id": placement_session_id,
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "preferred_language": preferred_language,
        "status": status,
        "resume": resume,
        "total_items": state.total_items,
        "scorable_answers": state.scorable_answers,
        "max_items": 18,
        "min_scorable": 8,
        "readiness_summary": readiness_summary(state),
        "next_item": public_item(item) if item else None,
    }


async def _persist_practice_row(
    *,
    store,
    practice_session_id: str,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    skill_id: str,
    status: str,
    state,
) -> None:
    await store.upsert_school_v2_practice_session(
        practice_session_id=practice_session_id,
        user_id=user_id,
        subject_id=subject_id,
        target_class_no=target_class_no,
        skill_id=skill_id,
        status=status,
        state_json=practice_state_to_json(state),
    )


def _practice_response(
    *,
    practice_session_id: str,
    subject_id: str,
    target_class_no: int,
    skill_id: str,
    state,
    resume: bool = False,
) -> dict:
    lesson = lesson_for_skill(skill_id)
    item = next_practice_item(state)
    status = practice_status(state)
    return {
        "practice_session_id": practice_session_id,
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "skill_id": skill_id,
        "status": status,
        "resume": resume,
        "lesson": public_lesson(lesson) if lesson else None,
        "answered_count": len(state.answered_item_ids),
        "total_items": len(lesson.items) if lesson else 0,
        "skill_status": classify_skill_status(state.skill_state),
        "readiness": state.skill_state.certified_readiness
            if state.skill_state.certified_readiness is not None
            else state.skill_state.practice_readiness,
        "last_result": None if state.last_result is None else {
            "item_id": state.last_result.item_id,
            "score": state.last_result.score,
            "correct": state.last_result.correct,
            "feedback": state.last_result.feedback,
        },
        "next_item": public_practice_item(item) if item else None,
    }


async def _persist_curriculum_row(
    *,
    store,
    curriculum_session_id: str,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    chapter_id: str,
    status: str,
    state,
) -> None:
    await store.upsert_school_v2_curriculum_session(
        curriculum_session_id=curriculum_session_id,
        user_id=user_id,
        subject_id=subject_id,
        target_class_no=target_class_no,
        chapter_id=chapter_id,
        status=status,
        state_json=curriculum_state_to_json(state),
    )


def _curriculum_response(
    *,
    curriculum_session_id: str,
    subject_id: str,
    target_class_no: int,
    chapter_id: str,
    state,
    resume: bool = False,
) -> dict:
    chapter = chapter_for_id(chapter_id)
    item = next_chapter_item(state)
    status = curriculum_status(state)
    return {
        "curriculum_session_id": curriculum_session_id,
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "chapter_id": chapter_id,
        "status": status,
        "resume": resume,
        "chapter": public_chapter(chapter) if chapter else None,
        "lesson": public_chapter_lesson(chapter) if chapter else None,
        "answered_count": len(state.answered_item_ids),
        "total_items": len(chapter.items) if chapter else 0,
        "chapter_score": chapter_score(state),
        "last_result": None if state.last_result is None else {
            "item_id": state.last_result.item_id,
            "score": state.last_result.score,
            "correct": state.last_result.correct,
            "feedback": state.last_result.feedback,
            "skill_status": state.last_result.skill_status,
        },
        "skill_statuses": {
            skill_id: classify_skill_status(skill_state)
            for skill_id, skill_state in sorted(state.skill_states.items())
        },
        "next_item": public_chapter_item(item) if item else None,
    }


async def _school_v2_profiles(user_id: str) -> list[dict]:
    graph = await get_storage().get_learning_graph(user_id)
    profiles = [
        dict(row)
        for row in graph.get("profiles", [])
        if row.get("domain") == "school"
    ]
    profiles.sort(key=lambda row: str(row.get("skill_id") or ""))
    return profiles


async def _school_v2_profile_for_skill(user_id: str, skill_id: str) -> dict | None:
    for profile in await _school_v2_profiles(user_id):
        if profile.get("skill_id") == skill_id:
            return profile
    return None


def _target_curriculum_ready(
    profiles: list[dict],
    target_class_no: int,
) -> bool:
    profile_by_skill = {
        str(row.get("skill_id") or ""): row
        for row in profiles
        if row.get("skill_id")
    }
    required = required_skill_ids(target_class_no)
    if not required:
        return False
    for skill_id in required:
        row = profile_by_skill.get(skill_id)
        if not row or not _profile_is_target_ready(row):
            return False
    return True


def _profile_is_target_ready(row: dict) -> bool:
    evidence = dict(row.get("evidence_json") or {})
    status = evidence.get("status") or "weak"
    readiness = float(row.get("readiness") or 0.0)
    return status in {"ready", "mastered"} and readiness >= 0.80


def _school_v3_elapsed_delta(row: dict) -> int:
    updated_at = row.get("updated_at")
    if isinstance(updated_at, (int, float)):
        return max(0, int(time.time() - float(updated_at)))
    if hasattr(updated_at, "timestamp"):
        return max(0, int(time.time() - updated_at.timestamp()))
    return 0


def _school_v3_state_json(state_json: dict | None, **patch: object) -> dict:
    clean = dict(state_json or {})
    clean.update(patch)
    return clean


async def _persist_school_v3_session(
    *,
    store,
    session_id: str,
    user_id: str,
    flow_type: str,
    subject_id: str,
    class_no: int,
    status: str,
    current_stage: str,
    state_json: dict,
    linked_session_id: str | None = None,
) -> None:
    await store.upsert_school_session(
        session_id=session_id,
        user_id=user_id,
        api_version="v3",
        flow_type=flow_type,
        subject_id=subject_id,
        class_no=class_no,
        status=status,
        current_stage=current_stage,
        state_json=state_json,
        linked_session_id=linked_session_id,
    )


def _school_v3_placement_response(
    *,
    session_id: str,
    subject_id: str,
    class_no: int,
    preferred_language: str,
    state,
    resume: bool = False,
) -> dict:
    payload = v3.placement_response_state(state)
    return {
        "session_id": session_id,
        "flow_type": "placement",
        "subject_id": subject_id,
        "target_class_no": class_no,
        "preferred_language": preferred_language,
        "resume": resume,
        **payload,
    }


def _school_v3_curriculum_response(
    *,
    session_id: str,
    subject_id: str,
    class_no: int,
    state,
    resume: bool = False,
) -> dict:
    payload = v3.curriculum_response_state(state)
    return {
        "session_id": session_id,
        "flow_type": "curriculum",
        "subject_id": subject_id,
        "target_class_no": class_no,
        "resume": resume,
        **payload,
    }


def _school_v3_masterclass_response(
    *,
    session_id: str,
    subject_id: str,
    class_no: int,
    state,
) -> dict:
    payload = v3.masterclass_response_state(state)
    return {
        "session_id": session_id,
        "flow_type": "masterclass",
        "subject_id": subject_id,
        "target_class_no": class_no,
        **payload,
    }


def _require_school_v3_supported(subject_id: str, class_no: int) -> None:
    if subject_id != "english":
        raise HTTPException(status_code=404, detail={"code": "unsupported_subject"})
    if class_no not in v3.supported_classes(subject_id):
        raise HTTPException(status_code=404, detail={"code": "unsupported_class"})


async def _record_school_v3_event(
    *,
    store,
    user_id: str,
    session_id: str,
    subject_id: str,
    class_no: int,
    flow_type: str,
    item,
    answer: str,
) -> None:
    evaluation = grade_deterministic_item(item, answer)
    skill_id = item.skill_ids[0]
    await store.record_learning_event(
        source_event_key=f"school_v3:{session_id}:{item.item_id}",
        user_id=user_id,
        domain="school",
        task_type=f"school_v3_{flow_type}",
        module_id=subject_id,
        session_id=session_id,
        node_id=item.item_id,
        skill_id=skill_id,
        source="school_v3",
        attempt_type=item.stage,
        score=evaluation.score,
        confidence=evaluation.confidence,
        criteria_json=[
            {
                "id": criterion.id,
                "met": criterion.met,
                "quality": criterion.quality,
                "evidence_quote": criterion.evidence_quote,
            }
            for criterion in evaluation.criteria
        ],
        evidence_json={
            "class_no": class_no,
            "stage": item.stage,
            "item_type": item.item_type,
            "correct": evaluation.score >= 0.80,
        },
        blockers=list(evaluation.blockers),
        gap="" if evaluation.score >= 0.80 else "school_v3_gap",
    )


def _school_v3_certifying_events(graph: dict) -> list[dict]:
    certifying = {"independent_check", "transfer_check", "review_check", "chapter_check"}
    return [
        row
        for row in graph.get("events", [])
        if row.get("domain") == "school"
        and row.get("source") == "school_v3"
        and row.get("attempt_type") in certifying
    ]


def _event_day(event: dict) -> str:
    raw = event.get("occurred_at") or event.get("created_at") or event.get("updated_at")
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, str) and raw:
        normalized = raw.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).date().isoformat()
        except ValueError:
            return raw[:10] if len(raw) >= 10 else date.today().isoformat()
    return date.today().isoformat()


@router.get("/v3/classes")
async def school_v3_classes(request: Request) -> dict:
    await _require_existing_uid(request)
    return v3.school_v3_classes_payload("english")


@router.post("/v3/placement/start")
async def school_v3_placement_start(req: SchoolV3PlacementStart, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    _require_school_v3_supported(req.subject_id, req.target_class_no)
    store = get_storage()
    existing = await store.get_active_school_session(
        user_id,
        "v3",
        "placement",
        req.subject_id,
        req.target_class_no,
    )
    if existing:
        raw_state = existing.get("state_json") or {}
        state = v3.placement_state_from_json(raw_state)
        return _school_v3_placement_response(
            session_id=existing["session_id"],
            subject_id=existing["subject_id"],
            class_no=existing["class_no"],
            preferred_language=raw_state.get("preferred_language") or req.preferred_language,
            state=state,
            resume=True,
        )

    session_id = str(uuid4())
    state = v3.new_placement_state(req.subject_id, req.target_class_no)
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="placement",
        subject_id=req.subject_id,
        class_no=req.target_class_no,
        status="active",
        current_stage=state.stage,
        state_json=_school_v3_state_json(
            v3.placement_state_to_json(state),
            preferred_language=req.preferred_language,
        ),
    )
    return _school_v3_placement_response(
        session_id=session_id,
        subject_id=req.subject_id,
        class_no=req.target_class_no,
        preferred_language=req.preferred_language,
        state=state,
    )


@router.post("/v3/placement/{session_id}/answer")
async def school_v3_placement_answer(
    session_id: str,
    req: SchoolV3Answer,
    request: Request,
) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_session(user_id, session_id)
    if row is None or row.get("flow_type") != "placement":
        raise HTTPException(status_code=404, detail={"code": "placement_session_not_found"})
    raw_state = row.get("state_json") or {}
    state = v3.placement_state_from_json(raw_state)
    preferred_language = raw_state.get("preferred_language") or "en"
    if row.get("status") != "active":
        return _school_v3_placement_response(
            session_id=session_id,
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            preferred_language=preferred_language,
            state=state,
        )
    if req.item_id in state.answered_item_ids:
        return _school_v3_placement_response(
            session_id=session_id,
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            preferred_language=preferred_language,
            state=state,
        )
    expected = v3.next_placement_item(state)
    if expected is None:
        outcome = v3.placement_outcome(state)
        await _persist_school_v3_session(
            store=store,
            session_id=session_id,
            user_id=user_id,
            flow_type="placement",
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            status="active" if outcome == "in_progress" else outcome,
            current_stage=state.stage,
            state_json=_school_v3_state_json(v3.placement_state_to_json(state), preferred_language=preferred_language),
        )
        return _school_v3_placement_response(
            session_id=session_id,
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            preferred_language=preferred_language,
            state=state,
        )
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_placement_item", "expected_item_id": expected.item_id},
        )
    item = v3.find_placement_item(state, req.item_id)
    updated = v3.apply_placement_answer_to_state(
        state,
        item,
        req.answer,
        elapsed_seconds_delta=_school_v3_elapsed_delta(row),
    )
    await _record_school_v3_event(
        store=store,
        user_id=user_id,
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        flow_type="placement",
        item=item,
        answer=req.answer,
    )
    outcome = v3.placement_outcome(updated)
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="placement",
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        status="active" if outcome == "in_progress" else outcome,
        current_stage=updated.stage,
        state_json=_school_v3_state_json(v3.placement_state_to_json(updated), preferred_language=preferred_language),
    )
    return _school_v3_placement_response(
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        preferred_language=preferred_language,
        state=updated,
    )


@router.post("/v3/curriculum/start")
async def school_v3_curriculum_start(req: SchoolV3CurriculumStart, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    _require_school_v3_supported(req.subject_id, req.target_class_no)
    chapter = v3.chapter_for_id(req.subject_id, req.chapter_id)
    if chapter is None or chapter.class_no != req.target_class_no:
        raise HTTPException(status_code=404, detail={"code": "chapter_not_found"})
    store = get_storage()
    existing = await store.get_active_school_session(
        user_id,
        "v3",
        "curriculum",
        req.subject_id,
        req.target_class_no,
    )
    if existing:
        state = v3.curriculum_state_from_json(existing.get("state_json") or {})
        return _school_v3_curriculum_response(
            session_id=existing["session_id"],
            subject_id=existing["subject_id"],
            class_no=existing["class_no"],
            state=state,
            resume=True,
        )

    session_id = str(uuid4())
    state = v3.new_curriculum_state(
        req.subject_id,
        req.target_class_no,
        req.chapter_id,
        watchlist_skill_ids=tuple(req.watchlist_skill_ids),
    )
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="curriculum",
        subject_id=req.subject_id,
        class_no=req.target_class_no,
        status=state.status,
        current_stage="curriculum",
        state_json=v3.curriculum_state_to_json(state),
    )
    return _school_v3_curriculum_response(
        session_id=session_id,
        subject_id=req.subject_id,
        class_no=req.target_class_no,
        state=state,
    )


@router.post("/v3/path")
async def school_v3_path(req: SchoolV3PathRequest, request: Request) -> dict:
    await _require_existing_uid(request)
    _require_school_v3_supported(req.subject_id, req.target_class_no)
    return build_readiness_path(
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
        weak_skill_ids=tuple(req.weak_skill_ids),
        non_blocking_weak_skill_ids=tuple(req.non_blocking_weak_skill_ids),
    )


@router.post("/v3/curriculum/{session_id}/answer")
async def school_v3_curriculum_answer(
    session_id: str,
    req: SchoolV3Answer,
    request: Request,
) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_session(user_id, session_id)
    if row is None or row.get("flow_type") != "curriculum":
        raise HTTPException(status_code=404, detail={"code": "curriculum_session_not_found"})
    state = v3.curriculum_state_from_json(row.get("state_json") or {})
    if state.status == "paused_for_masterclass":
        raise HTTPException(status_code=423, detail={"code": "curriculum_paused_for_masterclass"})
    expected = v3.next_curriculum_item(state)
    if expected is None:
        complete = dataclass_replace(state, status="complete")
        await _persist_school_v3_session(
            store=store,
            session_id=session_id,
            user_id=user_id,
            flow_type="curriculum",
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            status="complete",
            current_stage="complete",
            state_json=v3.curriculum_state_to_json(complete),
        )
        return _school_v3_curriculum_response(
            session_id=session_id,
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            state=complete,
        )
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_curriculum_item", "expected_item_id": expected.item_id},
        )
    masterclass_id = str(uuid4())
    draft_masterclass = v3.new_masterclass_state(
        linked_curriculum_session_id=session_id,
        curriculum_state=state,
        skill_id=expected.skill_ids[0],
    )
    masterclass_item = v3.next_masterclass_item(draft_masterclass)
    updated = v3.apply_curriculum_answer_to_state(
        state,
        expected,
        req.answer,
        masterclass_session_id=masterclass_id,
        masterclass_next_item=v3.public_school_v3_item(masterclass_item) if masterclass_item else None,
    )
    await _record_school_v3_event(
        store=store,
        user_id=user_id,
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        flow_type="curriculum",
        item=expected,
        answer=req.answer,
    )
    if updated.status == "paused_for_masterclass":
        await _persist_school_v3_session(
            store=store,
            session_id=masterclass_id,
            user_id=user_id,
            flow_type="masterclass",
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            status="active",
            current_stage="bridge",
            state_json=v3.masterclass_state_to_json(draft_masterclass),
            linked_session_id=session_id,
        )
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="curriculum",
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        status=updated.status,
        current_stage="curriculum",
        state_json=v3.curriculum_state_to_json(updated),
    )
    return _school_v3_curriculum_response(
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        state=updated,
    )


@router.post("/v3/masterclass/{session_id}/answer")
async def school_v3_masterclass_answer(
    session_id: str,
    req: SchoolV3Answer,
    request: Request,
) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_session(user_id, session_id)
    if row is None or row.get("flow_type") != "masterclass":
        raise HTTPException(status_code=404, detail={"code": "masterclass_session_not_found"})
    state = v3.masterclass_state_from_json(row.get("state_json") or {})
    if state.status != "active":
        return _school_v3_masterclass_response(
            session_id=session_id,
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            state=state,
        )
    expected = v3.next_masterclass_item(state)
    if expected is None:
        raise HTTPException(status_code=409, detail={"code": "masterclass_has_no_next_item"})
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_masterclass_item", "expected_item_id": expected.item_id},
        )
    updated = v3.apply_masterclass_answer_to_state(state, expected, req.answer)
    await _record_school_v3_event(
        store=store,
        user_id=user_id,
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        flow_type="masterclass",
        item=expected,
        answer=req.answer,
    )
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="masterclass",
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        status=updated.status,
        current_stage="complete" if updated.status == "complete" else "bridge",
        state_json=v3.masterclass_state_to_json(updated),
        linked_session_id=row.get("linked_session_id"),
    )
    return _school_v3_masterclass_response(
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        state=updated,
    )


@router.post("/v3/curriculum/{session_id}/resume")
async def school_v3_curriculum_resume(session_id: str, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_session(user_id, session_id)
    if row is None or row.get("flow_type") != "curriculum":
        raise HTTPException(status_code=404, detail={"code": "curriculum_session_not_found"})
    state = v3.curriculum_state_from_json(row.get("state_json") or {})
    interrupt = state.active_interrupt or {}
    masterclass_id = interrupt.get("masterclass_session_id")
    if not masterclass_id:
        return _school_v3_curriculum_response(
            session_id=session_id,
            subject_id=row["subject_id"],
            class_no=row["class_no"],
            state=state,
        )
    masterclass_row = await store.get_school_session(user_id, masterclass_id)
    if not masterclass_row or masterclass_row.get("status") != "complete":
        raise HTTPException(status_code=409, detail={"code": "masterclass_not_complete"})
    updated = v3.resolve_curriculum_interrupt(state, resolution="completed")
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="curriculum",
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        status=updated.status,
        current_stage="curriculum",
        state_json=v3.curriculum_state_to_json(updated),
    )
    return _school_v3_curriculum_response(
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        state=updated,
    )


@router.post("/v3/curriculum/{session_id}/abandon-masterclass")
async def school_v3_curriculum_abandon_masterclass(session_id: str, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_session(user_id, session_id)
    if row is None or row.get("flow_type") != "curriculum":
        raise HTTPException(status_code=404, detail={"code": "curriculum_session_not_found"})
    state = v3.curriculum_state_from_json(row.get("state_json") or {})
    interrupt = state.active_interrupt or {}
    masterclass_id = interrupt.get("masterclass_session_id")
    if masterclass_id:
        masterclass_row = await store.get_school_session(user_id, masterclass_id)
        if masterclass_row and masterclass_row.get("status") == "active":
            masterclass_state = v3.masterclass_state_from_json(masterclass_row.get("state_json") or {})
            abandoned = dataclass_replace(masterclass_state, status="abandoned")
            await _persist_school_v3_session(
                store=store,
                session_id=masterclass_id,
                user_id=user_id,
                flow_type="masterclass",
                subject_id=masterclass_row["subject_id"],
                class_no=masterclass_row["class_no"],
                status="abandoned",
                current_stage="abandoned",
                state_json=v3.masterclass_state_to_json(abandoned),
                linked_session_id=session_id,
            )
    updated = v3.resolve_curriculum_interrupt(state, resolution="abandoned")
    await _persist_school_v3_session(
        store=store,
        session_id=session_id,
        user_id=user_id,
        flow_type="curriculum",
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        status=updated.status,
        current_stage="curriculum",
        state_json=v3.curriculum_state_to_json(updated),
    )
    return _school_v3_curriculum_response(
        session_id=session_id,
        subject_id=row["subject_id"],
        class_no=row["class_no"],
        state=updated,
    )


@router.get("/v3/language-confidence")
async def school_v3_language_confidence(request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    row = await get_storage().get_school_language_confidence(user_id)
    return {
        "user_id": user_id,
        "en_production_confidence": float((row or {}).get("en_production_confidence") or 0.0),
        "total_signals": int((row or {}).get("total_signals") or 0),
    }


@router.get("/v3/streaks")
async def school_v3_streaks(request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    graph = await get_storage().get_learning_graph(user_id)
    events = _school_v3_certifying_events(graph)
    passing_days = {
        _event_day(event)
        for event in events
        if float(event.get("score") or 0.0) >= 0.80
    }
    return {
        "user_id": user_id,
        "certifying_day_count": len(passing_days),
        "certifying_days": sorted(passing_days),
    }


@router.get("/v3/badges")
async def school_v3_badges(request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    graph = await get_storage().get_learning_graph(user_id)
    school_events = [
        row
        for row in graph.get("events", [])
        if row.get("domain") == "school" and row.get("source") == "school_v3"
    ]
    certifying_passes = [
        row
        for row in _school_v3_certifying_events(graph)
        if float(row.get("score") or 0.0) >= 0.80
    ]
    badges = []
    if school_events:
        badges.append({"badge_id": "first_school_v3_attempt", "label": "First School V3 attempt"})
    if certifying_passes:
        badges.append({"badge_id": "first_certifying_pass", "label": "First independent pass"})
    return {"user_id": user_id, "badges": badges}


@router.get("/classes")
async def classes() -> list[dict]:
    out = []
    for n in cur.all_classes():
        c = cur.get_class(n)
        out.append({
            "class_no": c.class_no, "title": c.title, "description": c.description,
            "chapter_count": cur.chapter_count(n),
        })
    return out


@router.post("/v2/placement/start")
async def school_v2_placement_start(req: SchoolV2PlacementStart, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    if req.subject_id != "english":
        raise HTTPException(status_code=404, detail={"code": "unsupported_subject"})
    store = get_storage()
    existing = await store.get_active_school_v2_placement_session(
        user_id,
        req.subject_id,
        req.target_class_no,
    )
    if existing:
        state = placement_state_from_json(existing.get("state_json") or {})
        return _placement_response(
            placement_session_id=existing["placement_session_id"],
            subject_id=existing["subject_id"],
            target_class_no=existing["target_class_no"],
            preferred_language=existing.get("preferred_language") or "",
            status=existing["status"],
            state=state,
            resume=True,
        )

    placement_session_id = f"schoolv2_plc_{uuid4().hex}"
    state = PlacementSessionState(
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
    )
    try:
        await _persist_placement_row(
            store=store,
            placement_session_id=placement_session_id,
            user_id=user_id,
            subject_id=req.subject_id,
            target_class_no=req.target_class_no,
            preferred_language=req.preferred_language,
            status="in_progress",
            state=state,
        )
    except Exception:
        existing = await store.get_active_school_v2_placement_session(
            user_id,
            req.subject_id,
            req.target_class_no,
        )
        if not existing:
            raise
        logger.info(
            "school_v2_placement_start: resumed active placement after insert conflict user=%s",
            user_id,
            exc_info=True,
        )
        state = placement_state_from_json(existing.get("state_json") or {})
        return _placement_response(
            placement_session_id=existing["placement_session_id"],
            subject_id=existing["subject_id"],
            target_class_no=existing["target_class_no"],
            preferred_language=existing.get("preferred_language") or "",
            status=existing["status"],
            state=state,
            resume=True,
        )
    return _placement_response(
        placement_session_id=placement_session_id,
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
        preferred_language=req.preferred_language,
        status="in_progress",
        state=state,
    )


@router.post("/v2/placement/{placement_session_id}/answer")
async def school_v2_placement_answer(
    placement_session_id: str,
    req: SchoolV2PlacementAnswer,
    request: Request,
) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_v2_placement_session(user_id, placement_session_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "placement_session_not_found"})
    if row.get("status") != "in_progress":
        state = placement_state_from_json(row.get("state_json") or {})
        if row.get("status") == "complete":
            try:
                await record_placement_attempts(
                    store,
                    placement_session_id=placement_session_id,
                    user_id=user_id,
                    state=state,
                )
            except Exception as exc:
                logger.warning(
                    "school_v2_placement_answer: failed to repair completed projection user=%s placement=%s",
                    user_id,
                    placement_session_id,
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail={"code": "school_v2_projection_failed"},
                ) from exc
        return _placement_response(
            placement_session_id=placement_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            preferred_language=row.get("preferred_language") or "",
            status=row["status"],
            state=state,
        )

    state = placement_state_from_json(row.get("state_json") or {})
    if req.item_id in state.answered_item_ids:
        return _placement_response(
            placement_session_id=placement_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            preferred_language=row.get("preferred_language") or "",
            status=row["status"],
            state=state,
        )
    expected = next_item(state)
    if expected is None:
        status = placement_outcome(state)
        await _persist_placement_row(
            store=store,
            placement_session_id=placement_session_id,
            user_id=user_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            preferred_language=row.get("preferred_language") or "",
            status=status,
            state=state,
        )
        return _placement_response(
            placement_session_id=placement_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            preferred_language=row.get("preferred_language") or "",
            status=status,
            state=state,
        )
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_placement_item", "expected_item_id": expected.item_id},
        )

    item = find_item(req.item_id)
    state = apply_answer(state, item, req.answer)
    status = placement_outcome(state)
    await _persist_placement_row(
        store=store,
        placement_session_id=placement_session_id,
        user_id=user_id,
        subject_id=row["subject_id"],
        target_class_no=row["target_class_no"],
        preferred_language=row.get("preferred_language") or "",
        status=status,
        state=state,
    )
    if status == "complete":
        try:
            await record_placement_attempts(
                store,
                placement_session_id=placement_session_id,
                user_id=user_id,
                state=state,
            )
        except Exception as exc:
            logger.warning(
                "school_v2_placement_answer: failed to project completed placement user=%s placement=%s",
                user_id,
                placement_session_id,
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail={"code": "school_v2_projection_failed"},
            ) from exc
    return _placement_response(
        placement_session_id=placement_session_id,
        subject_id=row["subject_id"],
        target_class_no=row["target_class_no"],
        preferred_language=row.get("preferred_language") or "",
        status=status,
        state=state,
    )


@router.post("/v2/practice/start")
async def school_v2_practice_start(req: SchoolV2PracticeStart, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    if req.subject_id != "english":
        raise HTTPException(status_code=404, detail={"code": "unsupported_subject"})
    if req.skill_id not in set(required_skill_ids(req.target_class_no)):
        raise HTTPException(status_code=422, detail={"code": "unsupported_practice_skill"})
    lesson = lesson_for_skill(req.skill_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail={"code": "practice_lesson_not_found"})

    store = get_storage()
    existing = await store.get_active_school_v2_practice_session(
        user_id,
        req.subject_id,
        req.target_class_no,
        req.skill_id,
    )
    if existing:
        state = practice_state_from_json(existing.get("state_json") or {})
        return _practice_response(
            practice_session_id=existing["practice_session_id"],
            subject_id=existing["subject_id"],
            target_class_no=existing["target_class_no"],
            skill_id=existing["skill_id"],
            state=state,
            resume=True,
        )

    profile = await _school_v2_profile_for_skill(user_id, req.skill_id)
    practice_session_id = f"schoolv2_prac_{uuid4().hex}"
    state = practice_state_from_profile(
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
        skill_id=req.skill_id,
        profile=profile,
    )
    try:
        await _persist_practice_row(
            store=store,
            practice_session_id=practice_session_id,
            user_id=user_id,
            subject_id=req.subject_id,
            target_class_no=req.target_class_no,
            skill_id=req.skill_id,
            status="in_progress",
            state=state,
        )
    except Exception:
        existing = await store.get_active_school_v2_practice_session(
            user_id,
            req.subject_id,
            req.target_class_no,
            req.skill_id,
        )
        if not existing:
            raise
        logger.info(
            "school_v2_practice_start: resumed active practice after insert conflict user=%s",
            user_id,
            exc_info=True,
        )
        state = practice_state_from_json(existing.get("state_json") or {})
        return _practice_response(
            practice_session_id=existing["practice_session_id"],
            subject_id=existing["subject_id"],
            target_class_no=existing["target_class_no"],
            skill_id=existing["skill_id"],
            state=state,
            resume=True,
        )
    return _practice_response(
        practice_session_id=practice_session_id,
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
        skill_id=req.skill_id,
        state=state,
    )


@router.post("/v2/practice/{practice_session_id}/answer")
async def school_v2_practice_answer(
    practice_session_id: str,
    req: SchoolV2PracticeAnswer,
    request: Request,
) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_v2_practice_session(user_id, practice_session_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "practice_session_not_found"})
    state = practice_state_from_json(row.get("state_json") or {})
    if row.get("status") != "in_progress" or req.item_id in state.answered_item_ids:
        lesson = lesson_for_skill(row["skill_id"])
        previous_item = next(
            (item for item in (lesson.items if lesson else ()) if item.item_id == req.item_id),
            None,
        )
        if previous_item and req.item_id in state.answered_item_ids:
            try:
                await record_practice_attempt(
                    store,
                    practice_session_id=practice_session_id,
                    user_id=user_id,
                    state=state,
                    item=previous_item,
                )
            except Exception as exc:
                logger.warning(
                    "school_v2_practice_answer: failed to repair practice projection user=%s practice=%s item=%s",
                    user_id,
                    practice_session_id,
                    previous_item.item_id,
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail={"code": "school_v2_practice_projection_failed"},
                ) from exc
        return _practice_response(
            practice_session_id=practice_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            skill_id=row["skill_id"],
            state=state,
        )

    expected = next_practice_item(state)
    if expected is None:
        await _persist_practice_row(
            store=store,
            practice_session_id=practice_session_id,
            user_id=user_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            skill_id=row["skill_id"],
            status="complete",
            state=state,
        )
        return _practice_response(
            practice_session_id=practice_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            skill_id=row["skill_id"],
            state=state,
        )
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_practice_item", "expected_item_id": expected.item_id},
        )

    state = apply_practice_answer(state, expected, req.answer)
    status = practice_status(state)
    try:
        await _persist_practice_row(
            store=store,
            practice_session_id=practice_session_id,
            user_id=user_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            skill_id=row["skill_id"],
            status=status,
            state=state,
        )
    except Exception as exc:
        logger.warning(
            "school_v2_practice_answer: failed to persist practice state user=%s practice=%s item=%s",
            user_id,
            practice_session_id,
            expected.item_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "school_v2_practice_state_not_saved"},
        ) from exc
    try:
        await record_practice_attempt(
            store,
            practice_session_id=practice_session_id,
            user_id=user_id,
            state=state,
            item=expected,
        )
    except Exception as exc:
        logger.warning(
            "school_v2_practice_answer: failed to project practice attempt user=%s practice=%s item=%s",
            user_id,
            practice_session_id,
            expected.item_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "school_v2_practice_projection_failed"},
        ) from exc
    return _practice_response(
        practice_session_id=practice_session_id,
        subject_id=row["subject_id"],
        target_class_no=row["target_class_no"],
        skill_id=row["skill_id"],
        state=state,
    )


@router.post("/v2/curriculum/start")
async def school_v2_curriculum_start(req: SchoolV2CurriculumStart, request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    if req.subject_id != "english":
        raise HTTPException(status_code=422, detail={"code": "unsupported_subject"})
    chapter = chapter_for_id(req.chapter_id)
    if chapter is None or chapter.target_class_no != req.target_class_no:
        raise HTTPException(status_code=404, detail={"code": "target_chapter_not_found"})
    profiles = await _school_v2_profiles(user_id)
    if not _target_curriculum_ready(profiles, req.target_class_no):
        raise HTTPException(status_code=423, detail={"code": "target_curriculum_locked"})

    store = get_storage()
    existing = await store.get_active_school_v2_curriculum_session(
        user_id,
        req.subject_id,
        req.target_class_no,
        req.chapter_id,
    )
    if existing:
        state = curriculum_state_from_json(existing.get("state_json") or {})
        return _curriculum_response(
            curriculum_session_id=existing["curriculum_session_id"],
            subject_id=existing["subject_id"],
            target_class_no=existing["target_class_no"],
            chapter_id=existing["chapter_id"],
            state=state,
            resume=True,
        )

    curriculum_session_id = f"schoolv2_ch_{uuid4().hex}"
    state = curriculum_state_from_profiles(
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
        chapter_id=req.chapter_id,
        profiles=profiles,
    )
    try:
        await _persist_curriculum_row(
            store=store,
            curriculum_session_id=curriculum_session_id,
            user_id=user_id,
            subject_id=req.subject_id,
            target_class_no=req.target_class_no,
            chapter_id=req.chapter_id,
            status=curriculum_status(state),
            state=state,
        )
    except Exception as exc:
        existing = await store.get_active_school_v2_curriculum_session(
            user_id,
            req.subject_id,
            req.target_class_no,
            req.chapter_id,
        )
        if not existing:
            raise
        logger.info(
            "school_v2_curriculum_start: resumed active curriculum after insert conflict user=%s",
            user_id,
            exc_info=exc,
        )
        state = curriculum_state_from_json(existing.get("state_json") or {})
        return _curriculum_response(
            curriculum_session_id=existing["curriculum_session_id"],
            subject_id=existing["subject_id"],
            target_class_no=existing["target_class_no"],
            chapter_id=existing["chapter_id"],
            state=state,
            resume=True,
        )
    return _curriculum_response(
        curriculum_session_id=curriculum_session_id,
        subject_id=req.subject_id,
        target_class_no=req.target_class_no,
        chapter_id=req.chapter_id,
        state=state,
    )


@router.post("/v2/curriculum/{curriculum_session_id}/answer")
async def school_v2_curriculum_answer(
    curriculum_session_id: str,
    req: SchoolV2CurriculumAnswer,
    request: Request,
) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    row = await store.get_school_v2_curriculum_session(user_id, curriculum_session_id)
    if not row:
        raise HTTPException(status_code=404, detail={"code": "curriculum_session_not_found"})
    state = curriculum_state_from_json(row.get("state_json") or {})
    if req.item_id in state.answered_item_ids:
        answered_item = find_chapter_item(row["chapter_id"], req.item_id)
        if answered_item:
            try:
                await record_chapter_attempt(
                    store,
                    curriculum_session_id=curriculum_session_id,
                    user_id=user_id,
                    state=state,
                    item=answered_item,
                )
            except Exception as exc:
                logger.exception(
                    "school_v2_curriculum_answer: failed to repair chapter projection user=%s session=%s item=%s",
                    user_id,
                    curriculum_session_id,
                    req.item_id,
                )
                raise HTTPException(
                    status_code=500,
                    detail={"code": "school_v2_curriculum_projection_failed"},
                ) from exc
        return _curriculum_response(
            curriculum_session_id=curriculum_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            chapter_id=row["chapter_id"],
            state=state,
        )

    expected = next_chapter_item(state)
    if expected is None:
        await _persist_curriculum_row(
            store=store,
            curriculum_session_id=curriculum_session_id,
            user_id=user_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            chapter_id=row["chapter_id"],
            status="complete",
            state=state,
        )
        return _curriculum_response(
            curriculum_session_id=curriculum_session_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            chapter_id=row["chapter_id"],
            state=state,
        )
    if req.item_id != expected.item_id:
        raise HTTPException(
            status_code=409,
            detail={"code": "unexpected_chapter_item", "expected_item_id": expected.item_id},
        )

    state = apply_chapter_answer(state, expected, req.answer)
    status = curriculum_status(state)
    try:
        await _persist_curriculum_row(
            store=store,
            curriculum_session_id=curriculum_session_id,
            user_id=user_id,
            subject_id=row["subject_id"],
            target_class_no=row["target_class_no"],
            chapter_id=row["chapter_id"],
            status=status,
            state=state,
        )
    except Exception as exc:
        logger.exception(
            "school_v2_curriculum_answer: failed to persist curriculum state user=%s session=%s item=%s",
            user_id,
            curriculum_session_id,
            expected.item_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "school_v2_curriculum_state_not_saved"},
        ) from exc

    try:
        await record_chapter_attempt(
            store,
            curriculum_session_id=curriculum_session_id,
            user_id=user_id,
            state=state,
            item=expected,
        )
    except Exception as exc:
        logger.exception(
            "school_v2_curriculum_answer: failed to project chapter attempt user=%s session=%s item=%s",
            user_id,
            curriculum_session_id,
            expected.item_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "school_v2_curriculum_projection_failed"},
        ) from exc

    return _curriculum_response(
        curriculum_session_id=curriculum_session_id,
        subject_id=row["subject_id"],
        target_class_no=row["target_class_no"],
        chapter_id=row["chapter_id"],
        state=state,
    )


@router.get("/v2/readiness")
async def school_v2_readiness(request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    skills = []
    for profile in await _school_v2_profiles(user_id):
        evidence = dict(profile.get("evidence_json") or {})
        skills.append({
            "skill_id": profile.get("skill_id") or "",
            "readiness": profile.get("readiness") or 0.0,
            "mastery": profile.get("mastery") or 0.0,
            "confidence": profile.get("confidence") or 0.0,
            "attempts": profile.get("attempts") or 0,
            "status": evidence.get("status") or ("mastered" if profile.get("mastery") else "weak"),
            "ready_source": evidence.get("ready_source") or "",
            "recommended_next_action": profile.get("recommended_next_action") or "",
        })
    return {"domain": "school", "skills": skills}


@router.get("/v2/home")
async def school_v2_home(request: Request) -> dict:
    user_id = await _require_existing_uid(request)
    store = get_storage()
    active = None
    for class_no in (5,):
        active = await store.get_active_school_v2_placement_session(user_id, "english", class_no)
        if active:
            break
    if active:
        state = placement_state_from_json(active.get("state_json") or {})
        return {
            "primary_action": {
                "kind": "finish_placement",
                "placement_session_id": active["placement_session_id"],
            },
            "placement": _placement_response(
                placement_session_id=active["placement_session_id"],
                subject_id=active["subject_id"],
                target_class_no=active["target_class_no"],
                preferred_language=active.get("preferred_language") or "",
                status=active["status"],
                state=state,
                resume=True,
            ),
        }
    profiles = await _school_v2_profiles(user_id)
    if profiles:
        return {"primary_action": {"kind": "start_prep_path"}, "ready_skill_count": len(profiles)}
    return {"primary_action": {"kind": "start_placement"}, "ready_skill_count": 0}


@router.get("/v2/prep-path")
async def school_v2_prep_path(
    request: Request,
    target_class_no: int = Query(default=5, ge=5, le=5),
) -> dict:
    user_id = await _require_existing_uid(request)
    profiles = await _school_v2_profiles(user_id)
    profile_by_skill = {
        str(row.get("skill_id") or ""): row
        for row in profiles
        if row.get("skill_id")
    }
    steps = []
    seen_required = set()
    for skill_id in required_skill_ids(target_class_no):
        seen_required.add(skill_id)
        row = profile_by_skill.get(skill_id)
        if row:
            evidence = dict(row.get("evidence_json") or {})
            status = evidence.get("status") or "weak"
            readiness = float(row.get("readiness") or 0.0)
            recommended_next_action = row.get("recommended_next_action") or (
                "" if _profile_is_target_ready(row) else "catch_up_required"
            )
        else:
            status = "unseen"
            readiness = 0.0
            recommended_next_action = "placement_or_catch_up_required"
        steps.append({
            "skill_id": skill_id,
            "status": status,
            "readiness": readiness,
            "kind": "target_ready" if row and _profile_is_target_ready(row) else "catch_up",
            "recommended_next_action": recommended_next_action,
        })
    for row in profiles:
        skill_id = str(row.get("skill_id") or "")
        if not skill_id or skill_id in seen_required:
            continue
        evidence = dict(row.get("evidence_json") or {})
        status = evidence.get("status") or "weak"
        readiness = float(row.get("readiness") or 0.0)
        steps.append({
            "skill_id": skill_id,
            "status": status,
            "readiness": readiness,
            "kind": "target_ready" if _profile_is_target_ready(row) else "catch_up",
            "recommended_next_action": row.get("recommended_next_action") or (
                "" if _profile_is_target_ready(row) else "catch_up_required"
            ),
        })
    steps.sort(key=lambda step: (step["kind"] == "target_ready", step["readiness"], step["skill_id"]))
    required = [
        step
        for step in steps
        if step["skill_id"] in set(required_skill_ids(target_class_no))
    ]
    target_unlocked = bool(required) and all(
        step["kind"] == "target_ready" for step in required
    )
    target_chapter = first_chapter_for_class(target_class_no)
    return {
        "subject_id": "english",
        "target_class_no": target_class_no,
        "target_unlocked": target_unlocked,
        "next_action": "start_target_curriculum" if target_unlocked else "catch_up",
        "target_chapter": public_chapter(target_chapter) if target_unlocked and target_chapter else None,
        "steps": steps,
    }


@router.get("/class/{class_no}")
async def class_detail(class_no: int) -> dict:
    try:
        c = cur.get_class(class_no)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown class") from e
    chapters = [
        {
            "id": ch.id, "title": ch.title, "ncert_unit": ch.ncert_unit,
            "chapter_no": ch.chapter_no, "genre": ch.genre,
            "levels": [{"id": n.id, "title": n.title} for n in ch.nodes],
            "chapter_test_id": ch.chapter_test.id if ch.chapter_test else None,
        }
        for ch in cur.class_chapters(class_no)
    ]
    return {
        "class_no": c.class_no, "title": c.title, "description": c.description,
        "chapters": chapters,
        "milestones": [
            {"id": m.id, "title": m.title, "at_percent": m.at_percent}
            for m in c.milestones
        ],
    }


@router.get("/test/{test_id}")
async def get_test(test_id: str) -> dict:
    a = cur.find_assessment(test_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Unknown test")
    return {
        "id": a.id, "title": a.title, "kind": a.kind, "pass_mark": a.pass_mark,
        "items": [_public_item(i) for i in a.items],
    }


@router.post("/test/{test_id}/submit")
async def submit_test(
    test_id: str, request: Request, answers: dict = Body(..., embed=True)
) -> dict:
    a = cur.find_assessment(test_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Unknown test")
    if not isinstance(answers, dict):
        raise HTTPException(status_code=400, detail="answers must map item_id -> response")
    r = score_assessment(a, answers)
    by_skill = [
        {"skill": s.skill, "correct": s.correct, "total": s.total,
         "mastery": round(s.mastery, 4)}
        for s in r.by_skill
    ]
    # Persist the result + fold per-skill ratios into the learner's school
    # mastery so progress is durable AND the live 'Learn' tutor can target real
    # weak spots. Best-effort: a storage hiccup must never fail a graded submit,
    # but it must be visible to the client so progress is not falsely presented
    # as saved.
    user_id = _uid(request)
    saved = False
    degraded = False
    persistence_error = None
    if user_id:
        try:
            await get_storage().record_assessment_result(
                user_id=user_id,
                test_id=r.assessment_id,
                class_no=cur.class_of_assessment(test_id) or 0,
                kind=r.kind,
                score=r.score,
                passed=r.passed,
                by_skill=[{"skill": s.skill, "correct": s.correct, "total": s.total}
                          for s in r.by_skill],
            )
            saved = True
        except Exception:
            logger.warning(
                "submit_test: failed to persist result for user=%s test=%s",
                user_id, test_id, exc_info=True,
            )
            raise HTTPException(
                status_code=503,
                detail={"code": "progress_not_saved", "test_id": test_id},
            )
    else:
        degraded = True
        persistence_error = "auth_missing"
    return {
        "test_id": r.assessment_id, "title": r.title, "kind": r.kind,
        "score": r.score, "correct": r.correct, "total": r.total, "passed": r.passed,
        "by_skill": by_skill,
        "weak_skills": r.weak_skills, "missed_item_ids": r.missed_item_ids,
        "saved": saved,
        "degraded": degraded,
        "persistence_error": persistence_error,
    }


@router.get("/progress")
async def progress(request: Request, class_no: int | None = None) -> dict:
    """Durable, server-side learning record for the authenticated learner.

    Tracks which chapter tests / milestones were passed, the per-skill mastery
    EMA, and the current weak skills — the same signal the live 'Learn' tutor
    uses to personalise. Empty when nothing has been attempted yet."""
    user_id = _uid(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    chapters = None
    if class_no is not None:
        try:
            chapters = list(cur.class_chapters(class_no))
        except KeyError as e:
            raise HTTPException(status_code=404, detail="Unknown class") from e
    store = get_storage()
    try:
        results = await store.get_school_results(user_id, class_no)
        mastery = await store.get_school_skill_mastery(user_id)
        tutor_progress = await store.get_progression(user_id)
        weak_skills = await store.get_school_weak_skills(user_id)
    except Exception as e:
        logger.exception(
            "school progress unavailable for user=%s class_no=%s",
            user_id,
            class_no,
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "progress_unavailable", "class_no": class_no},
        ) from e
    tutor_by_node = {row.get("node_id"): row for row in tutor_progress}
    lesson_progress: dict[str, str] = {}
    if chapters is not None:
        for chapter in chapters:
            for node in chapter.nodes:
                row = tutor_by_node.get(node.id) or {}
                if row.get("node_completed"):
                    status = "completed"
                elif row.get("attempts") or row.get("ema") or row.get("mastery"):
                    status = "in_progress"
                else:
                    status = "learn"
                lesson_progress[node.id] = status
    passed_tests = sorted(r["test_id"] for r in results if r["passed"])
    overall = round(sum(r["score"] for r in results) / len(results), 4) if results else 0.0
    return {
        "class_no": class_no,
        "results": [
            {"test_id": r["test_id"], "class_no": r["class_no"], "kind": r["kind"],
             "score": r["score"], "passed": r["passed"], "weak_skills": r["weak_skills"]}
            for r in results
        ],
        "passed_tests": passed_tests,
        "skill_mastery": [
            {"skill": m["skill"], "mastery": round(m["ema"], 4), "attempts": m["attempts"]}
            for m in mastery
        ],
        "lesson_progress": lesson_progress,
        "weak_skills": weak_skills,
        "overall": overall,
    }


@router.get("/class/{class_no}/milestone")
async def milestone_status(class_no: int, chapters_done: int = 0, fired: str = "") -> dict:
    """Which milestone exam is unlocked at this much class progress (stateless).

    `chapters_done` and `fired` (comma-separated already-taken percents) come from
    the learner's progress, so the client can prompt the right milestone."""
    try:
        c = cur.get_class(class_no)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown class") from e
    fired_set = {int(p) for p in fired.split(",") if p.strip().isdigit()}
    due = milestone_due(chapters_done, cur.chapter_count(class_no), c.milestones, fired_set)
    return {
        "due": (
            {"id": due.id, "title": due.title, "at_percent": due.at_percent}
            if due else None
        )
    }
