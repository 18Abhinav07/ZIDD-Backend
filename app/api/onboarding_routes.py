from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.storage import get_storage

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class SchoolProfileIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    school_name: str = ""
    learning_goal: str = ""


class CareerProfileIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resume_text: str = ""
    target_roles: list[str] = Field(default_factory=list)
    interview_goals: list[str] = Field(default_factory=list)
    gd_topic_ids: list[str] = Field(default_factory=list)
    custom_gd_topics: list[str] = Field(default_factory=list)


class OnboardingCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str
    primary_motive: Literal["school", "career"]
    school_profile: SchoolProfileIn = Field(default_factory=SchoolProfileIn)
    career_profile: CareerProfileIn = Field(default_factory=CareerProfileIn)


class OnboardingDraftPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft: dict[str, Any] = Field(default_factory=dict)


def _uid(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return uid


async def _profile_or_401(user_id: str) -> dict[str, Any]:
    profile = await get_storage().get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=401, detail="Profile not found; sign in again")
    return profile


def _text(value: str | None, max_len: int = 4000) -> str:
    return (value or "").strip()[:max_len]


def _text_list(values: list[str] | None, max_items: int = 12, max_len: int = 120) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        item = _text(raw, max_len)
        key = item.casefold()
        if not item or key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= max_items:
            break
    return out


def _school_profile(req: SchoolProfileIn) -> dict:
    profile = {
        "school_name": _text(req.school_name, 160),
        "learning_goal": _text(req.learning_goal, 280),
    }
    if not profile["school_name"]:
        raise HTTPException(status_code=422, detail="school_name is required for school onboarding")
    return {k: v for k, v in profile.items() if v}


def _career_profile(req: CareerProfileIn) -> dict:
    profile = {
        "resume_text": _text(req.resume_text, 12000),
        "target_roles": _text_list(req.target_roles),
        "interview_goals": _text_list(req.interview_goals),
        "gd_topic_ids": _text_list(req.gd_topic_ids, max_items=20, max_len=80),
        "custom_gd_topics": _text_list(req.custom_gd_topics, max_items=10, max_len=160),
    }
    useful = bool(
        profile["resume_text"]
        or profile["target_roles"]
        or profile["interview_goals"]
        or profile["gd_topic_ids"]
        or profile["custom_gd_topics"]
    )
    if not useful:
        raise HTTPException(
            status_code=422,
            detail="Add a resume, target role, interview goal, or GD topic to personalize career prep",
        )
    return {k: v for k, v in profile.items() if v}


def _public_career_profile(profile: dict | None) -> dict:
    raw = dict(profile or {})
    resume_text = _text(raw.get("resume_text"), 12000)
    raw.pop("resume_text", None)
    return {
        **raw,
        "resume_present": bool(resume_text),
    }


def _destination(primary_motive: str) -> str:
    return "/school" if primary_motive == "school" else "/career"


@router.get("/state")
async def onboarding_state(request: Request) -> dict:
    user_id = _uid(request)
    profile = await _profile_or_401(user_id)
    primary = profile.get("primary_motive")
    return {
        "completed": bool(profile.get("onboarding_completed_at")),
        "completed_at": profile.get("onboarding_completed_at"),
        "primary_motive": primary,
        "destination": _destination(primary) if primary else "/onboarding",
        "display_name": profile.get("name", "") or "",
        "draft": profile.get("onboarding_state") or {},
    }


@router.patch("/state")
async def update_onboarding_state(req: OnboardingDraftPatch, request: Request) -> dict:
    user_id = _uid(request)
    store = get_storage()
    await _profile_or_401(user_id)
    draft = await store.update_onboarding_state(user_id, req.draft)
    return {"draft": draft}


@router.post("/complete")
async def complete_onboarding(req: OnboardingCompleteRequest, request: Request) -> dict:
    user_id = _uid(request)
    display_name = _text(req.display_name, 120)
    if not display_name:
        raise HTTPException(status_code=422, detail="display_name is required")

    store = get_storage()
    existing_profile = await _profile_or_401(user_id)
    school_profile = dict(existing_profile.get("school_profile") or {})
    career_profile = dict(existing_profile.get("career_profile") or {})
    if req.primary_motive == "school":
        school_profile = _school_profile(req.school_profile)
    else:
        career_profile = _career_profile(req.career_profile)

    profile = await store.complete_onboarding(
        user_id=user_id,
        display_name=display_name,
        primary_motive=req.primary_motive,
        school_profile=school_profile,
        career_profile=career_profile,
    )
    destination = _destination(req.primary_motive)
    return {
        "destination": destination,
        "onboarding": {
            "completed": True,
            "completed_at": profile.get("onboarding_completed_at"),
            "primary_motive": req.primary_motive,
        },
        "school_profile": profile.get("school_profile") or {},
        "career_profile": _public_career_profile(profile.get("career_profile") or {}),
    }
