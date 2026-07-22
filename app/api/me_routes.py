import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.content.registry import module_of
from app.content.school.standards import locked_english_taxonomy
from app.services.learning_profile import CareerLearningProfileService, build_career_memory_context
from app.services.school_rebuild_learning import build_school_memory_context
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
_SCHOOL_LEARNER_SKILL_LABELS = {
    entry.skill_id: entry.name
    for entry in locked_english_taxonomy().entries
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
    return "/school" if profile.get("primary_motive") == "school" else "/career"


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


def _school_learner_skill_label(skill_id: str) -> str:
    label = _SCHOOL_LEARNER_SKILL_LABELS.get(skill_id)
    if label:
        return label
    fallback = skill_id.rsplit(".", 1)[-1].replace("_", " ").strip()
    return fallback.capitalize() if fallback else "English skill"


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
    wallet = (
        await store.get_wallet_summary(user_id)
        if hasattr(store, "get_wallet_summary")
        else {"credits": profile.get("credits", 0) or 0}
    )
    return {
        "user_id": user_id,
        "name": profile.get("name", "") or "",
        "email": profile.get("email"),
        "google_sub": profile.get("google_sub"),
        "credits": int(wallet.get("credits") or 0),
        "beta_credits": int(wallet.get("beta_credits") or 0),
        "paid_credits": int(wallet.get("paid_credits") or 0),
        "promo_credits": int(wallet.get("promo_credits") or 0),
        "beta_expires_at": wallet.get("beta_expires_at"),
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

    try:
        school_graph = await store.get_school_learning_graph(user_id)
    except Exception:
        degraded = True
        logger.exception("school activity unavailable for user=%s", user_id)
        school_graph = {"profiles": [], "reports": [], "events": [], "sessions": []}

    school_profiles = [
        row
        for row in _activity_rows(school_graph.get("profiles"))
        if row.get("domain") == "school"
    ]
    school_events = [
        row
        for row in _activity_rows(school_graph.get("events"))
        if row.get("domain") == "school"
    ]
    school_sessions = [
        row
        for row in _activity_rows(school_graph.get("sessions"))
        if row.get("api_version") == "rebuild"
        and row.get("domain") in (None, "school")
    ]
    school_reports = [
        row
        for row in _activity_rows(school_graph.get("reports"))
        if row.get("domain") in (None, "school")
    ]
    school_memory = build_school_memory_context(
        {"profiles": school_profiles, "events": school_events}
    )
    school_weak = list(
        dict.fromkeys(
            str(row.get("skill_id"))
            for bucket in ("active_gaps", "improving_gaps")
            for row in _activity_rows(school_memory.get(bucket))
            if row.get("skill_id")
        )
    )
    progression = _activity_rows(snapshot.get("progression"))
    weaknesses = _activity_rows(snapshot.get("weaknesses"))

    school_test_events = [
        row
        for row in school_events
        if row.get("attempt_type") == "chapter_check" and row.get("session_id")
    ]
    scores = [_float_or_zero(row.get("score")) for row in school_test_events]
    average = round(sum(scores) / len(scores), 4) if scores else 0.0
    school_test_session_ids = {
        str(row["session_id"])
        for row in school_test_events
        if str(row.get("session_id") or "")
    }
    recent_class_values = [row.get("class_no") for row in school_sessions]
    recent_class_values.extend(
        report.get("active_learning_class_no")
        or report.get("evaluated_class_no")
        or report.get("target_class_no")
        for report in school_reports
    )
    recent_classes = sorted(
        {
            _int_or_zero(class_no)
            for class_no in recent_class_values
            if _int_or_zero(class_no) > 0
        }
    )
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
                "body": ", ".join(
                    _school_learner_skill_label(skill_id)
                    for skill_id in school_weak[:3]
                ),
                "href": "/school",
            })
        else:
            recommendations.append({
                "kind": "school",
                "title": "Open school prep",
                "body": "Set up your class and start with a readiness check.",
                "href": "/school",
            })
    if profile.get("primary_motive") != "school" and not career_ready:
        recommendations.append({
            "kind": "career",
            "title": "Complete career personalization",
            "body": "Add resume details, target roles, or GD topics for sharper practice.",
            "href": "/profile",
        })

    return {
        "school": {
            "results_count": len(school_test_session_ids),
            "recent_classes": recent_classes,
            "average_score": average,
            "weak_skills": school_weak,
            "skill_mastery": [
                {
                    "skill": m.get("skill_id"),
                    "mastery": round(_float_or_zero(m.get("mastery")), 4),
                    "attempts": _int_or_zero(m.get("attempts")),
                }
                for m in school_profiles
                if m.get("skill_id")
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
        "active_sessions": _activity_rows(graph.get("active_sessions")),
        "memory_context": build_career_memory_context(graph),
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
