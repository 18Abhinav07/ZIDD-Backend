import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.content.registry import module_of
from app.services.learning_profile import CareerLearningProfileService
from app.storage import get_storage

router = APIRouter(prefix="/me", tags=["me"])
logger = logging.getLogger("zidd.me")

ARCHIVED_MODULES = {"communication"}
CAREER_MODULES = {"interview", "group_discussion"}
CAREER_TASK_TYPES = {
    "interview",
    "group_discussion",
    "interview_prep",
    "interview_test",
    "gd_prep",
    "gd_test",
}


class PreferencesPatch(BaseModel):
    active_module: str | None = None
    pending_module: str | None = None
    test_mode: bool | None = None
    first_sim_complete: bool | None = None


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


def _sanitize_preferences(raw: dict[str, Any]) -> dict[str, Any]:
    prefs = dict(raw or {})
    prefs.pop("school_class", None)
    prefs.pop("placed_modules", None)
    for key in ("active_module", "pending_module"):
        if prefs.get(key) in ARCHIVED_MODULES:
            prefs[key] = None
    return prefs


def _onboarding(profile: dict[str, Any]) -> dict[str, Any]:
    primary = profile.get("primary_motive")
    return {
        "completed": bool(profile.get("onboarding_completed_at")),
        "completed_at": profile.get("onboarding_completed_at"),
        "primary_motive": primary,
    }


def _career_public(profile: dict[str, Any] | None) -> dict[str, Any]:
    raw = dict(profile or {})
    resume_text = (raw.get("resume_text") or "").strip()
    raw.pop("resume_text", None)
    return {**raw, "resume_present": bool(resume_text)}


def _home_for_profile(profile: dict[str, Any]) -> str:
    if not profile.get("onboarding_completed_at"):
        return "/onboarding"
    return "/subjects" if profile.get("primary_motive") == "school" else "/career"


def _is_career_node(node_id: object) -> bool:
    if not isinstance(node_id, str) or not node_id:
        return False
    try:
        return module_of(node_id) in CAREER_MODULES
    except Exception:
        return False


def _is_career_progression_row(row: dict[str, Any]) -> bool:
    node_id = row.get("node_id")
    if node_id:
        return _is_career_node(node_id)
    # Compatibility for older/json-string activity snapshots used by tests and
    # dev traces before node_id was always selected into the aggregate.
    return any(key in row for key in ("attempts", "clean_pass", "node_completed"))


@router.get("/gate")
async def gate(request: Request) -> dict:
    user_id = _uid(request)
    profile = await _profile_or_401(user_id)
    return {
        "user_id": user_id,
        "onboarding": {
            "completed": bool(profile.get("onboarding_completed_at")),
            "primary_motive": profile.get("primary_motive"),
        },
        "home": _home_for_profile(profile),
    }


def _activity_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return _activity_list(json.loads(value))
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _activity_rows(value: Any) -> list[dict[str, Any]]:
    return [item for item in _activity_list(value) if isinstance(item, dict)]


def _float_or_zero(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


async def _career_attempt_count(store: Any, user_id: str) -> int:
    count_attempts = getattr(store, "count_attempts", None)
    if not callable(count_attempts):
        return 0
    total = 0
    for module_id in sorted(CAREER_MODULES):
        total += _int_or_zero(await count_attempts(user_id, module_id))
    return total


def _legacy_progression_attempt_count(rows: list[dict[str, Any]]) -> int:
    """Best-effort compatibility for pre-node-attempt activity snapshots.

    Durable `node_attempts` are authoritative. Older dev/test snapshots only had
    progression rows, sometimes without node_id, so use their attempts count only
    when the durable attempt ledger is empty.
    """
    total = 0
    for row in rows:
        if row.get("node_id"):
            continue
        total += _int_or_zero(row.get("attempts"))
    return total


@router.get("")
async def me(request: Request) -> dict:
    user_id = _uid(request)
    store = get_storage()
    profile = await _profile_or_401(user_id)
    prefs = _sanitize_preferences(profile.get("preferences") or {})
    if prefs != (profile.get("preferences") or {}):
        prefs = await store.update_preferences(user_id, prefs)
    return {
        "user_id": user_id,
        "name": profile.get("name", "") or "",
        "email": profile.get("email"),
        "google_sub": profile.get("google_sub"),
        "credits": profile.get("credits", 0) or 0,
        "demo_unlimited": bool(profile.get("demo_unlimited", False)),
        "onboarding": _onboarding(profile),
        "school_profile": profile.get("school_profile") or {},
        "career_profile": _career_public(profile.get("career_profile") or {}),
        "preferences": prefs,
    }


@router.get("/activity")
async def activity(request: Request) -> dict:
    user_id = _uid(request)
    store = get_storage()
    profile = await _profile_or_401(user_id)
    degraded = False
    try:
        snapshot = await store.get_activity_snapshot(user_id)
    except Exception:
        degraded = True
        logger.exception("activity snapshot unavailable for user=%s", user_id)
        snapshot = {}

    school_results = _activity_rows(snapshot.get("school_results"))
    school_mastery = _activity_rows(snapshot.get("school_skill_mastery"))
    school_weak = [str(skill) for skill in _activity_list(snapshot.get("school_weak_skills")) if skill]
    progression = _activity_rows(snapshot.get("progression"))
    weaknesses = _activity_rows(snapshot.get("weaknesses"))

    scores = [_float_or_zero(r.get("score")) for r in school_results]
    average = round(sum(scores) / len(scores), 4) if scores else 0.0
    recent_classes = sorted({
        _int_or_zero(r.get("class_no"))
        for r in school_results
        if _int_or_zero(r.get("class_no")) > 0
    })
    career_progression = [p for p in progression if _is_career_progression_row(p)]
    career_weaknesses = [w for w in weaknesses if w.get("task_type") in CAREER_TASK_TYPES]
    completed_nodes = [
        p for p in career_progression
        if p.get("node_completed")
    ]
    try:
        career_attempts = await _career_attempt_count(store, user_id)
    except Exception:
        degraded = True
        logger.exception("career attempt count unavailable for user=%s", user_id)
        career_attempts = 0
    if career_attempts == 0:
        career_attempts = _legacy_progression_attempt_count(career_progression)
    career_profile = profile.get("career_profile") or {}
    career_ready = bool(
        career_profile.get("resume_text")
        or career_profile.get("target_roles")
        or career_profile.get("interview_goals")
        or career_profile.get("gd_topic_ids")
        or career_profile.get("custom_gd_topics")
    )

    recommendations: list[dict[str, str]] = []
    if profile.get("primary_motive") == "school" or not profile.get("primary_motive"):
        if school_weak:
            recommendations.append({
                "kind": "school",
                "title": "Review your focus areas",
                "body": ", ".join(school_weak[:3]).replace("_", " "),
                "href": "/subjects",
            })
        else:
            recommendations.append({
                "kind": "school",
                "title": "Open English curriculum",
                "body": "Pick any available class and continue the NCERT English path.",
                "href": "/subjects",
            })
    if not career_ready:
        recommendations.append({
            "kind": "career",
            "title": "Complete career personalization",
            "body": "Add resume details, target roles, or GD topics for sharper practice.",
            "href": "/profile",
        })

    return {
        "school": {
            "results_count": len(school_results),
            "recent_classes": recent_classes,
            "average_score": average,
            "weak_skills": school_weak,
            "skill_mastery": [
                {
                    "skill": m.get("skill"),
                    "mastery": round(_float_or_zero(m.get("ema")), 4),
                    "attempts": _int_or_zero(m.get("attempts")),
                }
                for m in school_mastery
            ],
        },
        "career": {
            "completed_nodes": len(completed_nodes),
            "attempts": career_attempts,
            "weaknesses": [
                {
                    "task_type": w.get("task_type"),
                    "skill_id": w.get("skill_id"),
                    "hit_count": _int_or_zero(w.get("hit_count")),
                    "last_raw": w.get("last_raw") or "",
                }
                for w in career_weaknesses
            ],
            "profile_complete": career_ready,
            "resume_present": bool((career_profile.get("resume_text") or "").strip()),
        },
        "recommendations": recommendations,
        "degraded": degraded,
    }


@router.get("/learning-graph")
async def learning_graph(request: Request) -> dict:
    user_id = _uid(request)
    store = get_storage()
    profile = await _profile_or_401(user_id)
    degraded = False
    try:
        graph = await CareerLearningProfileService(store).get_learning_graph(user_id)
    except Exception:
        degraded = True
        logger.exception("learning graph unavailable for user=%s", user_id)
        graph = {"profiles": [], "reports": [], "events": []}
    return {
        "career_profile": _career_public(profile.get("career_profile") or {}),
        "profiles": _activity_rows(graph.get("profiles")),
        "reports": _activity_rows(graph.get("reports")),
        "events": _activity_rows(graph.get("events")),
        "degraded": degraded,
    }


@router.patch("/preferences")
async def update_preferences(req: PreferencesPatch, request: Request) -> dict:
    user_id = _uid(request)
    store = get_storage()
    await _profile_or_401(user_id)
    patch = req.model_dump(exclude_unset=True)
    prefs = _sanitize_preferences(await store.update_preferences(user_id, patch))
    if prefs != await store.get_preferences(user_id):
        prefs = await store.update_preferences(user_id, prefs)
    return {"preferences": prefs}
