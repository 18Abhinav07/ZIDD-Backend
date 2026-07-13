"""Target-class curriculum loop for the rebuilt School Prep flow."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school.source_map_compat import load_beta_source_map
from app.content.school_rebuild_content import load_approved_live_chapters_for_class
from app.services.school.evaluator_contract import RUBRIC_SCHEMA_VERSION
from app.services.school_rebuild_language import localized_teaching_support
from app.services.school_rebuild_profile import school_coach_identity


ENGINE_VERSION = "school-rebuild-curriculum-3"
_PREVIOUS_ENGINE_VERSION = "school-rebuild-curriculum-2"
REVISION_STEPS = ("revision_level_1", "revision_level_2", "revision_level_3")
MAX_MASTERCLASS_INTERRUPTS_PER_LEVEL = 2
CHAPTER_ASSESSMENT_HARD_BLOCKERS = frozenset({"contradictory_response"})


CLASS_3_CURRICULUM_CHAPTERS: tuple[dict[str, Any], ...] = (
    load_approved_live_chapters_for_class("english", 3)
)
CLASS_2_CURRICULUM_CHAPTERS: tuple[dict[str, Any], ...] = (
    load_approved_live_chapters_for_class("english", 2)
)
CLASS_4_CURRICULUM_CHAPTERS: tuple[dict[str, Any], ...] = (
    load_approved_live_chapters_for_class("english", 4)
)
CLASS_5_CURRICULUM_CHAPTERS: tuple[dict[str, Any], ...] = (
    load_approved_live_chapters_for_class("english", 5)
)


def _live_chapter_by_id(
    chapters: tuple[dict[str, Any], ...],
    chapter_id: str,
) -> dict[str, Any]:
    return next(
        (chapter for chapter in chapters if chapter["chapter_id"] == chapter_id),
        {},
    )


# Compatibility aliases for tests and callers that inspect the authored chapter contract.
CLASS_5_PAPAS_SPECTACLES_CHAPTER = _live_chapter_by_id(
    CLASS_5_CURRICULUM_CHAPTERS, "eng_c5_ch01"
)
CLASS_5_GONE_WITH_SCOOTER_CHAPTER = _live_chapter_by_id(
    CLASS_5_CURRICULUM_CHAPTERS, "eng_c5_ch02"
)
CLASS_5_RAINBOW_CHAPTER = _live_chapter_by_id(
    CLASS_5_CURRICULUM_CHAPTERS, "eng_c5_ch03"
)
CLASS_5_WISE_PARROT_CHAPTER = _live_chapter_by_id(
    CLASS_5_CURRICULUM_CHAPTERS, "eng_c5_ch04"
)


def is_curriculum_unlocked(
    *,
    placement_report: dict[str, Any] | None,
    recap_session: dict[str, Any] | None,
) -> bool:
    if not placement_report:
        return False
    if placement_report.get("unlock_state") == "target_unlocked":
        return True
    if not recap_session or _session_status(recap_session) != "complete":
        return False
    recap_state = dict(recap_session.get("state_json") or {})
    recap_profile_version_id = str(
        recap_session.get("profile_version_id")
        or recap_state.get("profile_version_id")
        or ""
    )
    recap_report_id = str(
        recap_session.get("source_placement_report_id")
        or recap_state.get("source_placement_report_id")
        or ""
    )
    return (
        recap_profile_version_id == str(placement_report.get("profile_version_id") or "")
        and recap_report_id == str(placement_report.get("report_id") or "")
    )


def curriculum_landing(
    *,
    school_profile: dict[str, Any],
    placement_report: dict[str, Any] | None,
    recap_session: dict[str, Any] | None,
    latest_curriculum_session: dict[str, Any] | None = None,
) -> dict[str, Any]:
    subject_id = (school_profile.get("subject_ids") or ["english"])[0]
    target_class_no = int(school_profile["target_class_no"])
    source_map = _source_map(subject_id, target_class_no)
    completed_ids = _completed_chapter_ids(latest_curriculum_session)
    next_chapter = _next_available_chapter(subject_id, target_class_no, completed_ids)
    next_chapter_no = int(next_chapter.get("chapter_no") or 0) if next_chapter else None
    return {
        "flow_type": "curriculum",
        **school_coach_identity(school_profile),
        "status": "unlocked",
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "active_learning_class_no": target_class_no,
        "preferred_teaching_language": str(
            school_profile.get("preferred_teaching_language") or "en"
        ),
        "source_recap_session_id": (
            str(recap_session["session_id"])
            if recap_session and _session_status(recap_session) == "complete"
            else None
        ),
        "source_placement_report_id": (
            str(placement_report["report_id"]) if placement_report else None
        ),
        "book_title": source_map.get("book_title") or "",
        "source_note": (
            f"Target class is unlocked. Start Chapter {next_chapter_no} when you are ready."
            if next_chapter_no
            else "All available target-class chapters are complete."
        ),
        "chapters_preview": [
            {
                "chapter_id": chapter["chapter_id"],
                "chapter_no": int(chapter["chapter_no"]),
                "title": chapter["chapter_title"],
                "status": _chapter_preview_status(
                    chapter["chapter_id"],
                    completed_ids,
                    next_chapter,
                ),
            }
            for chapter in source_map.get("chapters") or []
        ],
    }


def select_startable_chapter(
    *,
    subject_id: str,
    class_no: int,
    chapter_id: str,
    latest_curriculum_session: dict[str, Any] | None,
    active_curriculum_session: dict[str, Any] | None,
) -> dict[str, Any]:
    available = _available_chapters(subject_id, class_no)
    requested = next(
        (chapter for chapter in available if chapter["chapter_id"] == chapter_id),
        None,
    )
    if requested is None:
        raise ValueError("curriculum_chapter_not_authored")

    active_state = dict((active_curriculum_session or {}).get("state_json") or {})
    active_chapter_id = str(
        (active_state.get("chapter") or {}).get("chapter_id") or ""
    )
    if active_chapter_id:
        if active_chapter_id != chapter_id:
            raise ValueError("curriculum_active_session_conflict")
        return requested

    completed_ids = _completed_chapter_ids(latest_curriculum_session)
    if chapter_id in completed_ids:
        raise ValueError("curriculum_chapter_complete")
    next_chapter = _next_available_chapter(subject_id, class_no, completed_ids)
    if next_chapter is None:
        raise ValueError("no_curriculum_chapter_available")
    if next_chapter["chapter_id"] != chapter_id:
        raise ValueError("curriculum_chapter_locked")
    return requested


def class_chapter_map(
    *,
    subject_id: str,
    class_no: int,
    curriculum_unlocked: bool,
    latest_curriculum_session: dict[str, Any] | None,
    active_curriculum_session: dict[str, Any] | None,
    learning_memory: dict[str, Any] | None = None,
    coach_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chapters = _available_chapters(subject_id, class_no)
    completed_ids = _completed_chapter_ids(latest_curriculum_session)
    active_state = normalize_curriculum_state(
        dict((active_curriculum_session or {}).get("state_json") or {})
    )
    active_chapter_id = str(
        (active_state.get("chapter") or {}).get("chapter_id") or ""
    )
    next_chapter = _next_available_chapter(subject_id, class_no, completed_ids)
    selected_chapter_id = active_chapter_id or (
        str(next_chapter["chapter_id"])
        if curriculum_unlocked and next_chapter
        else None
    )

    summaries = []
    for chapter in chapters:
        chapter_id = str(chapter["chapter_id"])
        total_levels = len(chapter.get("levels") or [])
        is_active = chapter_id == active_chapter_id
        if chapter_id in completed_ids:
            status = "complete"
            completed_levels = total_levels
        elif is_active:
            status = (
                "needs_support"
                if active_state.get("phase") in {"needs_support", "capped_support"}
                else "active"
            )
            completed_levels = sum(
                1
                for level in active_state.get("levels") or []
                if level.get("status") == "complete"
            )
        elif (
            curriculum_unlocked
            and next_chapter
            and chapter_id == next_chapter.get("chapter_id")
        ):
            status = "ready"
            completed_levels = 0
        else:
            status = "locked"
            completed_levels = 0
        summaries.append(
            {
                "chapter_id": chapter_id,
                "chapter_no": int(chapter["chapter_no"]),
                "title": str(chapter.get("title") or ""),
                "status": status,
                "completed_levels": completed_levels,
                "total_levels": total_levels,
                "active_session_id": (
                    str(active_curriculum_session["session_id"])
                    if is_active and active_curriculum_session
                    else None
                ),
            }
        )

    return {
        "subject_id": subject_id,
        "class_no": int(class_no),
        "book_title": str(chapters[0].get("book_title") or "") if chapters else "",
        **school_coach_identity(coach_source),
        "active_chapter_id": selected_chapter_id,
        "chapters": summaries,
        "recent_growth": {
            "improving_count": len((learning_memory or {}).get("improving_gaps") or []),
            "strong_count": len((learning_memory or {}).get("strong_skills") or [])
            + len((learning_memory or {}).get("mastered_skills") or []),
            "active_focus_count": len((learning_memory or {}).get("active_gaps") or []),
        },
    }


def _learner_stage(level_index: int, total_levels: int) -> str:
    if level_index == 0:
        return "Discover"
    if level_index == total_levels - 1:
        return "Use It Somewhere New"
    if level_index == total_levels - 2:
        return "Try It Yourself"
    return "Practise Together"


def chapter_level_map(
    *,
    subject_id: str,
    class_no: int,
    chapter_id: str,
    curriculum_unlocked: bool,
    latest_curriculum_session: dict[str, Any] | None,
    active_curriculum_session: dict[str, Any] | None,
    coach_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chapters = _available_chapters(subject_id, class_no)
    chapter = next(
        (candidate for candidate in chapters if candidate["chapter_id"] == chapter_id),
        None,
    )
    if chapter is None:
        raise ValueError("curriculum_chapter_not_authored")

    class_map = class_chapter_map(
        subject_id=subject_id,
        class_no=class_no,
        curriculum_unlocked=curriculum_unlocked,
        latest_curriculum_session=latest_curriculum_session,
        active_curriculum_session=active_curriculum_session,
        coach_source=coach_source,
    )
    chapter_summary = next(
        summary
        for summary in class_map["chapters"]
        if summary["chapter_id"] == chapter_id
    )
    chapter_status = str(chapter_summary["status"])
    active_state = normalize_curriculum_state(
        dict((active_curriculum_session or {}).get("state_json") or {})
    )
    active_levels = {
        str(level.get("level_id") or ""): level
        for level in active_state.get("levels") or []
    }
    total_levels = len(chapter.get("levels") or [])
    levels = []
    for index, level in enumerate(chapter.get("levels") or []):
        saved_level = active_levels.get(str(level["level_id"]))
        if chapter_status == "complete":
            level_status = "complete"
        elif saved_level:
            saved_status = str(saved_level.get("status") or "not_started")
            if saved_status == "complete":
                level_status = "complete"
            elif saved_status == "in_progress":
                level_status = (
                    "needs_support"
                    if chapter_status == "needs_support"
                    else "active"
                )
            else:
                level_status = "locked"
        elif chapter_status == "ready" and index == 0:
            level_status = "ready"
        else:
            level_status = "locked"
        levels.append(
            {
                "level_id": str(level["level_id"]),
                "title": str(level.get("title") or ""),
                "learner_stage": _learner_stage(index, total_levels),
                "status": level_status,
            }
        )

    phase = str(active_state.get("phase") or "")
    if chapter_status == "complete":
        chapter_check_status = "complete"
    elif chapter_status == "needs_support":
        chapter_check_status = "needs_support"
    elif chapter_status == "active" and phase == "chapter_check":
        chapter_check_status = "active"
    else:
        chapter_check_status = "locked"
    return {
        "subject_id": subject_id,
        "class_no": int(class_no),
        **school_coach_identity(coach_source),
        "chapter_id": chapter_id,
        "chapter_no": int(chapter["chapter_no"]),
        "title": str(chapter.get("title") or ""),
        "book_title": str(chapter.get("book_title") or ""),
        "status": chapter_status,
        "active_session_id": chapter_summary["active_session_id"],
        "levels": levels,
        "chapter_check": {
            "title": "Chapter challenge",
            "status": chapter_check_status,
        },
    }


def new_curriculum_state(
    *,
    school_profile: dict[str, Any],
    placement_report: dict[str, Any] | None,
    recap_session: dict[str, Any] | None,
    latest_curriculum_session: dict[str, Any] | None = None,
    requested_chapter_id: str | None = None,
    learning_memory: dict[str, Any] | None = None,
    en_production_confidence: float = 0.0,
    language_signal_count: int = 0,
) -> dict[str, Any]:
    subject_id = (school_profile.get("subject_ids") or ["english"])[0]
    target_class_no = int(school_profile["target_class_no"])
    completed_chapter_ids = _completed_chapter_ids(latest_curriculum_session)
    chapter = _next_available_chapter(subject_id, target_class_no, completed_chapter_ids)
    if chapter is None:
        raise ValueError("no_curriculum_chapter_available")
    if requested_chapter_id and chapter["chapter_id"] != requested_chapter_id:
        if not any(
            candidate["chapter_id"] == requested_chapter_id
            for candidate in _available_chapters(subject_id, target_class_no)
        ):
            raise ValueError("curriculum_chapter_not_authored")
        raise ValueError("curriculum_chapter_locked")
    chapter = dict(chapter)
    levels = []
    for index, level in enumerate(chapter["levels"]):
        levels.append({
            **level,
            "status": "in_progress" if index == 0 else "not_started",
            "current_step": "guided_check",
            "attempts": [],
        })
    return normalize_curriculum_state({
        "engine_version": ENGINE_VERSION,
        "profile_version_id": str(school_profile.get("profile_version_id") or ""),
        "status": "active",
        "phase": "learning",
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "active_learning_class_no": target_class_no,
        "preferred_teaching_language": str(
            school_profile.get("preferred_teaching_language") or "en"
        ),
        "en_production_confidence": max(
            0.0,
            min(1.0, float(en_production_confidence)),
        ),
        "language_signal_count": max(0, int(language_signal_count)),
        "source_recap_session_id": (
            str(recap_session["session_id"])
            if recap_session and _session_status(recap_session) == "complete"
            else None
        ),
        "source_placement_report_id": (
            str(placement_report["report_id"]) if placement_report else None
        ),
        "chapter": {
            key: value
            for key, value in chapter.items()
            if key not in {"levels", "chapter_assessment"}
        },
        "chapter_assessment": _new_chapter_assessment_state(
            chapter.get("chapter_assessment")
        ),
        "completed_chapter_ids": completed_chapter_ids,
        "completed_chapter_versions": _completed_chapter_versions(latest_curriculum_session),
        "completed_chapter_certification_versions": (
            _completed_chapter_certification_versions(latest_curriculum_session)
        ),
        "carry_forward_focuses": _merge_memory_focuses(
            _carry_forward_focuses(recap_session, placement_report),
            learning_memory,
        ),
        "learner_memory": dict(learning_memory or {}),
        "current_level_index": 0,
        "levels": levels,
        "last_feedback": None,
        "active_interrupt": None,
        "interrupt_history": [],
        "interrupt_counts": {},
    })


def public_curriculum_response(session_row: dict[str, Any]) -> dict[str, Any]:
    state = normalize_curriculum_state(dict(session_row.get("state_json") or {}))
    status = state.get("status") or session_row.get("status")
    subject_id = state.get("subject_id") or session_row.get("subject_id")
    target_class_no = int(state.get("target_class_no") or session_row.get("class_no") or 0)
    completed_chapter_ids = _completed_chapter_ids({
        **session_row,
        "state_json": state,
        "status": status,
    })
    next_available_chapter = (
        _public_chapter_summary(
            _next_available_chapter(subject_id, target_class_no, completed_chapter_ids)
        )
        if status == "complete" and subject_id and target_class_no
        else None
    )
    return {
        "session_id": str(session_row["session_id"]),
        "flow_type": "curriculum",
        **school_coach_identity(state),
        "status": status,
        "profile_version_id": str(
            session_row.get("profile_version_id")
            or state.get("profile_version_id")
            or ""
        ),
        "phase": state.get("phase") or "learning",
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "active_learning_class_no": int(state.get("active_learning_class_no") or 0),
        "preferred_teaching_language": str(
            state.get("preferred_teaching_language") or "en"
        ),
        "source_recap_session_id": state.get("source_recap_session_id"),
        "source_placement_report_id": state.get("source_placement_report_id"),
        "chapter": _public_active_chapter(state.get("chapter") or {}),
        "completed_chapter_ids": completed_chapter_ids,
        "next_available_chapter": next_available_chapter,
        "carry_forward_focuses": list(state.get("carry_forward_focuses") or []),
        "memory_summary": _public_memory_summary(state.get("learner_memory")),
        "progress": _progress(state),
        "chapter_assessment": _public_chapter_assessment_progress(state),
        "levels": [_public_level(level) for level in state.get("levels") or []],
        "current_activity": _public_activity(_current_activity(state)),
        "last_feedback": state.get("last_feedback"),
        "active_interrupt": _public_interrupt(state.get("active_interrupt")),
        "interrupt_history": _public_interrupt_history(
            state.get("interrupt_history") or []
        ),
    }


def current_curriculum_activity_id(state: Any) -> str | None:
    if not isinstance(state, dict) or state.get("status") == "complete":
        return None
    if state.get("phase") == "chapter_check":
        assessment = state.get("chapter_assessment")
        if not isinstance(assessment, dict):
            return None
        selected_ids = assessment.get("selected_item_ids")
        if not isinstance(selected_ids, list):
            return None
        try:
            current_index = int(assessment.get("current_index") or 0)
            attempt_no = int(assessment.get("attempt_no") or 1)
        except (TypeError, ValueError):
            return None
        if current_index < 0 or current_index >= len(selected_ids):
            return None
        item_id = str(selected_ids[current_index] or "")
        return f"chapter_check:{attempt_no}:{item_id}" if item_id else None

    levels = state.get("levels")
    if not isinstance(levels, list) or any(not isinstance(level, dict) for level in levels):
        return None
    try:
        level_index = int(state.get("current_level_index") or 0)
    except (TypeError, ValueError):
        return None
    if level_index < 0 or level_index >= len(levels):
        return None
    level = levels[level_index]
    if level.get("status") == "complete":
        return None
    attempts = level.get("attempts") or []
    if not isinstance(attempts, list) or any(
        not isinstance(attempt, dict) for attempt in attempts
    ):
        return None
    level_id = str(level.get("level_id") or "")
    if not level_id:
        return None
    kind = str(level.get("current_step") or "guided_check")
    attempt_no = 1 + sum(1 for attempt in attempts if attempt.get("kind") == kind)
    return f"{level_id}:{kind}:{attempt_no}"


def resume_after_masterclass(
    state: dict[str, Any],
    *,
    masterclass_session_id: str,
    resolution: str,
) -> dict[str, Any]:
    normalized = normalize_curriculum_state(state)
    interrupt = normalized.get("active_interrupt")
    if (
        normalized.get("status") != "paused_for_masterclass"
        or normalized.get("phase") != "paused_for_masterclass"
        or not isinstance(interrupt, dict)
    ):
        raise ValueError("curriculum_not_paused_for_masterclass")
    if resolution not in {"complete", "abandoned"}:
        raise ValueError("invalid_masterclass_resolution")
    level_id = str(interrupt.get("level_id") or "")
    levels = list(normalized.get("levels") or [])
    level_index = next(
        (
            index
            for index, candidate in enumerate(levels)
            if str(candidate.get("level_id") or "") == level_id
        ),
        None,
    )
    if level_index is None:
        raise ValueError("masterclass_level_not_found")
    level = dict(levels[level_index])
    level["status"] = "in_progress"
    level["current_step"] = str(
        interrupt.get("return_step") or "independent_check"
    )
    levels[level_index] = level
    normalized["levels"] = levels
    normalized["current_level_index"] = level_index
    normalized["status"] = "active"
    normalized["phase"] = "learning"
    normalized["active_interrupt"] = None
    normalized["interrupt_history"] = list(
        normalized.get("interrupt_history") or []
    ) + [{
        **interrupt,
        "masterclass_session_id": masterclass_session_id,
        "resolution": resolution,
    }]
    normalized["last_feedback"] = {
        "activity_id": str(interrupt.get("interrupt_id") or ""),
        "level_id": level_id,
        "kind": "masterclass",
        "correct": True if resolution == "complete" else None,
        "message": (
            "Focused practice complete. Return to the same lesson step you paused."
            if resolution == "complete"
            else "Focused practice was left unfinished. Return to the same lesson step when you are ready."
        ),
    }
    return normalize_curriculum_state(normalized)


def attach_masterclass_session(
    state: dict[str, Any],
    *,
    masterclass_session_id: str,
) -> dict[str, Any]:
    normalized = normalize_curriculum_state(state)
    interrupt = normalized.get("active_interrupt")
    if not isinstance(interrupt, dict):
        raise ValueError("curriculum_not_paused_for_masterclass")
    existing = str(interrupt.get("masterclass_session_id") or "")
    if existing and existing != masterclass_session_id:
        raise ValueError("masterclass_session_conflict")
    normalized["active_interrupt"] = {
        **interrupt,
        "masterclass_session_id": masterclass_session_id,
    }
    return normalize_curriculum_state(normalized)


def normalize_curriculum_state(state: dict[str, Any]) -> dict[str, Any]:
    levels = []
    for index, level in enumerate(state.get("levels") or []):
        normalized = dict(level)
        normalized.setdefault("status", "in_progress" if index == int(state.get("current_level_index") or 0) else "not_started")
        normalized.setdefault("current_step", "guided_check")
        normalized.setdefault("attempts", [])
        levels.append(normalized)
    if levels and not any(level.get("status") == "in_progress" for level in levels):
        current_index = min(int(state.get("current_level_index") or 0), len(levels) - 1)
        if levels[current_index].get("status") != "complete":
            levels[current_index]["status"] = "in_progress"
    all_levels_complete = bool(levels) and all(
        level.get("status") == "complete" for level in levels
    )
    phase = str(state.get("phase") or "learning")
    assessment_pending = bool(state.get("chapter_assessment")) and phase != "complete"
    status = (
        "complete"
        if all_levels_complete and not assessment_pending
        else state.get("status", "active")
    )
    if status == "complete":
        phase = "complete"
    current_index = min(int(state.get("current_level_index") or 0), max(0, len(levels) - 1))
    normalized_state = {
        **state,
        "engine_version": state.get("engine_version") or ENGINE_VERSION,
        "status": status,
        "phase": phase,
        "current_level_index": current_index,
        "levels": levels,
        "last_feedback": state.get("last_feedback"),
        "active_interrupt": state.get("active_interrupt"),
        "interrupt_history": list(state.get("interrupt_history") or []),
        "interrupt_counts": dict(state.get("interrupt_counts") or {}),
    }
    return _ensure_assessment_support_contract(normalized_state)


def reconcile_curriculum_state(
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Upgrade persisted state and repair only deterministic historical false negatives."""

    normalized = normalize_curriculum_state(state)
    previous_version = str(normalized.get("engine_version") or "")
    if previous_version == ENGINE_VERSION:
        return normalized, None

    updated = dict(normalized)
    repair = None
    if previous_version == _PREVIOUS_ENGINE_VERSION:
        updated, repair = _reconcile_v2_chapter_assessment(updated)
    updated["engine_version"] = ENGINE_VERSION
    return normalize_curriculum_state(updated), repair


def _reconcile_v2_chapter_assessment(
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if state.get("phase") != "needs_support":
        return state, None
    assessment = state.get("chapter_assessment")
    if not isinstance(assessment, dict):
        return state, None
    responses = assessment.get("responses")
    items = assessment.get("items")
    history = assessment.get("attempt_history")
    if not isinstance(responses, list) or not isinstance(items, list) or not history:
        return state, None

    items_by_id = {
        str(item.get("item_id") or ""): item
        for item in items
        if isinstance(item, dict) and item.get("item_id")
    }
    reconciled_responses: list[dict[str, Any]] = []
    response_changed = False
    for response in responses:
        if not isinstance(response, dict):
            reconciled_responses.append(response)
            continue
        item = items_by_id.get(str(response.get("item_id") or ""))
        reconciled, changed = _reconcile_saved_summary_source_accuracy(
            item=item,
            response=response,
        )
        reconciled_responses.append(reconciled)
        response_changed = response_changed or changed
    if not response_changed:
        return state, None

    updated_assessment = {
        **assessment,
        "responses": reconciled_responses,
    }
    result = _chapter_assessment_result(updated_assessment)
    updated_history = list(history)
    updated_history[-1] = result
    updated_assessment["attempt_history"] = updated_history
    updated = {
        **state,
        "chapter_assessment": updated_assessment,
    }
    if not result["passed"]:
        updated["support_required"] = {
            "reason": "chapter_check_attempts_exhausted",
            "attempt_count": int(updated_assessment.get("attempt_no") or 1),
            "weak_skill_ids": list(result["weak_skill_ids"]),
            "remediation_skill_ids": list(result["remediation_skill_ids"]),
        }
        return updated, None

    updated = _complete_chapter(updated)
    updated.pop("support_required", None)
    updated["last_feedback"] = {
        "activity_id": reconciled_responses[-1]["activity_id"],
        "level_id": "chapter_assessment",
        "kind": "chapter_check",
        "correct": True,
        "result_visible": True,
        "message": "Chapter check passed. The next chapter is ready.",
    }
    chapter_id = str((updated.get("chapter") or {}).get("chapter_id") or "")
    repair = {
        "kind": "chapter_certification_reconciled",
        "chapter_id": chapter_id,
        "attempt_no": int(result["attempt_no"]),
        "skill_scores": dict(result["skill_scores"]),
    }
    updated["state_reconciliations"] = list(
        updated.get("state_reconciliations") or []
    ) + [{
        "from_engine_version": _PREVIOUS_ENGINE_VERSION,
        "to_engine_version": ENGINE_VERSION,
        **repair,
    }]
    return updated, repair


def _reconcile_saved_summary_source_accuracy(
    *,
    item: dict[str, Any] | None,
    response: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    if (
        not item
        or response.get("evaluation_mode") != "llm_rubric"
        or not item.get("passage")
    ):
        return response, False
    authored_criteria = list(item.get("rubric_criteria") or [])
    authored_by_id = {
        str(criterion.get("id") or ""): criterion
        for criterion in authored_criteria
        if isinstance(criterion, dict)
    }
    source_rule = authored_by_id.get("summary_source_accuracy")
    if not source_rule:
        return response, False
    criteria = [
        dict(criterion)
        for criterion in response.get("criteria") or []
        if isinstance(criterion, dict)
    ]
    source_criterion = next(
        (
            criterion
            for criterion in criteria
            if criterion.get("id") == "summary_source_accuracy"
        ),
        None,
    )
    if not source_criterion or (
        source_criterion.get("met")
        and float(source_criterion.get("quality") or 0.0)
        >= float(source_rule.get("min_quality", 0.6))
    ):
        return response, False

    answer = str(response.get("answer") or "")
    concern = _normalize(str(source_criterion.get("evidence_quote") or ""))
    passage = str(item.get("passage") or "")
    if (
        not concern
        or not _concept_phrase_spans(_normalize(passage), concern)
        or _copies_source_passage(passage=passage, answer=answer)
    ):
        return response, False

    source_criterion.update({"met": True, "quality": 1.0})
    required = [
        criterion
        for criterion in authored_criteria
        if criterion.get("required", True)
    ]
    criteria_by_id = {
        str(criterion.get("id") or ""): criterion for criterion in criteria
    }
    missing = [
        str(rule.get("id") or "")
        for rule in required
        if not criteria_by_id.get(str(rule.get("id") or ""), {}).get("met")
        or float(
            criteria_by_id.get(str(rule.get("id") or ""), {}).get("quality")
            or 0.0
        )
        < float(rule.get("min_quality", 0.6))
    ]
    blockers = list(response.get("blockers") or [])
    if not missing:
        blockers = [blocker for blocker in blockers if blocker != "needs_human_review"]
    scored_rules = required or authored_criteria
    score = (
        sum(
            float(criteria_by_id[str(rule.get("id") or "")].get("quality") or 0.0)
            for rule in scored_rules
        )
        / len(scored_rules)
        if scored_rules
        else 0.0
    )
    pass_score = float(item.get("pass_score") or 0.75)
    return {
        **response,
        "criteria": criteria,
        "blockers": blockers,
        "score": round(score, 4),
        "correct": not missing and not blockers and score >= pass_score,
    }, True


def apply_curriculum_answer(
    state: dict[str, Any],
    *,
    activity_id: str,
    answer: str,
    open_answer_evaluation: SchoolRubricEvaluation | dict[str, Any] | None = None,
    open_answer_preflight_failed: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_curriculum_state(state)
    activity = _current_activity(normalized)
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_curriculum_activity")

    level_index = int(activity["level_index"])
    levels = list(normalized.get("levels") or [])
    level = dict(levels[level_index])
    evaluator_activity = evaluator_activity_for_answer(activity, answer)
    if evaluator_activity is not None:
        if open_answer_preflight_failed:
            answer_evaluation = _open_answer_preflight_failure(evaluator_activity)
        elif open_answer_evaluation is None:
            raise ValueError("open_answer_evaluation_required")
        elif activity.get("evaluation_mode") == "llm_rubric":
            answer_evaluation = decide_open_answer_evaluation(
                evaluator_activity,
                open_answer_evaluation,
                answer=answer,
            )
        else:
            answer_evaluation = decide_semantic_concept_evaluation(
                activity,
                open_answer_evaluation,
                answer=answer,
            )
    else:
        answer_evaluation = evaluate_deterministic_answer(activity, answer)
    effective_evaluation_mode = (
        "llm_rubric"
        if activity.get("evaluation_mode") == "llm_rubric"
        else "semantic_llm_rubric"
        if evaluator_activity is not None
        else "deterministic"
    )
    answer_evaluation = {
        **answer_evaluation,
        "_evaluation_mode": effective_evaluation_mode,
    }
    correct = bool(answer_evaluation["correct"])
    if activity["kind"] == "chapter_check":
        return _apply_chapter_check_answer(
            normalized,
            activity=activity,
            answer=answer,
            answer_evaluation=answer_evaluation,
        )
    attempt_no = 1 + sum(
        1
        for previous in level.get("attempts") or []
        if previous.get("kind") == activity["kind"]
    )
    attempt = {
        "activity_id": activity_id,
        "kind": activity["kind"],
        "attempt_no": attempt_no,
        "answer": answer,
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
        "evaluation_mode": effective_evaluation_mode,
    }
    level["attempts"] = list(level.get("attempts") or []) + [attempt]

    if correct:
        if (
            activity["kind"] in REVISION_STEPS
            and normalized.get("remediation_mode") == "expanded_revision"
        ):
            normalized, levels, level = _advance_expanded_revision(
                normalized,
                levels=levels,
                level=level,
                level_index=level_index,
                kind=activity["kind"],
            )
        elif activity["kind"] in REVISION_STEPS:
            current_revision_index = REVISION_STEPS.index(activity["kind"])
            if current_revision_index + 1 < len(REVISION_STEPS):
                level["status"] = "in_progress"
                level["current_step"] = REVISION_STEPS[current_revision_index + 1]
            else:
                level["status"] = "in_progress"
                level["current_step"] = str(
                    level.get("return_step") or "independent_check"
                )
        elif activity["kind"] in {"guided_check", "bridge", "masterclass"}:
            level["status"] = "in_progress"
            level["current_step"] = str(
                level.get("return_step") or "independent_check"
            )
        elif (
            activity["kind"] == "independent_check"
            and "transfer_check" in (level.get("checks") or {})
        ):
            level["status"] = "in_progress"
            level["current_step"] = "transfer_check"
        elif activity["kind"] in {"independent_check", "transfer_check"}:
            level["status"] = "complete"
            level["current_step"] = "complete"
            if normalized.get("phase") == "remediation":
                queue = list(normalized.get("remediation_queue") or [])
                if not queue or queue[0] != level.get("level_id"):
                    raise ValueError("chapter_remediation_queue_mismatch")
                remaining_queue = queue[1:]
                normalized["remediation_queue"] = remaining_queue
                if remaining_queue:
                    next_index = next(
                        index
                        for index, candidate in enumerate(levels)
                        if candidate.get("level_id") == remaining_queue[0]
                    )
                    next_level = dict(levels[next_index])
                    next_level["status"] = "in_progress"
                    next_level["current_step"] = _remediation_start_step(normalized)
                    levels[next_index] = next_level
                    normalized["current_level_index"] = next_index
                else:
                    normalized["current_level_index"] = level_index
                    normalized = _begin_chapter_assessment(normalized)
            elif (next_index := level_index + 1) < len(levels):
                next_level = dict(levels[next_index])
                next_level["status"] = "in_progress"
                next_level["current_step"] = "guided_check"
                levels[next_index] = next_level
                normalized["current_level_index"] = next_index
            else:
                normalized["current_level_index"] = level_index
                if normalized.get("chapter_assessment"):
                    normalized = _begin_chapter_assessment(normalized)
                else:
                    normalized = _complete_chapter(normalized)
    elif (
        activity["kind"] in REVISION_STEPS
        and normalized.get("remediation_mode") == "expanded_revision"
    ):
        normalized, levels, level = _advance_expanded_revision(
            normalized,
            levels=levels,
            level=level,
            level_index=level_index,
            kind=activity["kind"],
        )
    else:
        level["status"] = "in_progress"
        if activity["kind"] in {"independent_check", "transfer_check"}:
            level["return_step"] = activity["kind"]
        if activity["kind"] in REVISION_STEPS:
            level["current_step"] = activity["kind"]
        elif activity["kind"] == "masterclass" and attempt_no >= 2:
            level["current_step"] = "revision_level_1"
            level["revision_expanded"] = True
        elif activity["kind"] == "bridge":
            return_step = str(level.get("return_step") or "independent_check")
            counts = dict(normalized.get("interrupt_counts") or {})
            trigger_count = int(counts.get(level["level_id"]) or 0) + 1
            counts[level["level_id"]] = trigger_count
            normalized["interrupt_counts"] = counts
            if trigger_count <= MAX_MASTERCLASS_INTERRUPTS_PER_LEVEL:
                level["current_step"] = "masterclass"
                normalized["status"] = "paused_for_masterclass"
                normalized["phase"] = "paused_for_masterclass"
                normalized["active_interrupt"] = {
                    "interrupt_id": (
                        f"{level['level_id']}:masterclass:{trigger_count}"
                    ),
                    "level_id": level["level_id"],
                    "focus": level.get("focus") or "",
                    "trigger_count": trigger_count,
                    "return_step": return_step,
                    "masterclass_session_id": None,
                }
            else:
                level["current_step"] = return_step
                normalized["status"] = "active"
                normalized["phase"] = "capped_support"
                normalized["active_interrupt"] = None
                normalized["interrupt_history"] = list(
                    normalized.get("interrupt_history") or []
                ) + [{
                    "interrupt_id": f"{level['level_id']}:masterclass:{trigger_count}",
                    "level_id": level["level_id"],
                    "focus": level.get("focus") or "",
                    "trigger_count": trigger_count,
                    "masterclass_session_id": None,
                    "resolution": "capped_out",
                }]
        elif activity["kind"] == "masterclass":
            level["current_step"] = "masterclass"
        else:
            level["current_step"] = "bridge"

    levels[level_index] = level
    normalized["levels"] = levels
    expanded_revision = (
        activity["kind"] in REVISION_STEPS
        and state.get("remediation_mode") == "expanded_revision"
    )
    normalized["last_feedback"] = {
        "activity_id": activity_id,
        "level_id": activity["level_id"],
        "kind": activity["kind"],
        "correct": correct,
        "message": (
            "This support answer is saved. Zidd is moving to a different "
            "example before the final chapter check."
            if expanded_revision
            else _evaluation_feedback_message(
                activity,
                answer_evaluation,
                next_step=str(level.get("current_step") or ""),
            )
        ),
    }
    updated = normalize_curriculum_state(normalized)
    evaluation = {
        "activity_id": activity_id,
        "level_id": activity["level_id"],
        "kind": activity["kind"],
        "focus": activity["focus"],
        "skill_ids": list(activity.get("skill_ids") or []),
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "missing_criteria": list(answer_evaluation["missing_criteria"]),
        "misconception_tags": list(answer_evaluation["misconception_tags"]),
        "blockers": list(answer_evaluation["blockers"]),
        "language_detected": str(answer_evaluation["language_detected"]),
        "model_score": answer_evaluation.get("model_score"),
        "evaluation_mode": effective_evaluation_mode,
        "attempt_no": attempt_no,
    }
    return updated, evaluation


def curriculum_activity_for_answer(
    state: dict[str, Any],
    *,
    activity_id: str,
) -> dict[str, Any]:
    activity = _current_activity(normalize_curriculum_state(state))
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_curriculum_activity")
    return activity


def _session_status(session: dict[str, Any]) -> str:
    state_json = session.get("state_json") or {}
    return str(state_json.get("status") or session.get("status") or "")


def _source_map(subject_id: str, class_no: int) -> dict[str, Any]:
    return load_beta_source_map(subject_id, class_no)


def _available_chapters(subject_id: str, class_no: int) -> tuple[dict[str, Any], ...]:
    if subject_id == "english" and int(class_no) == 2:
        return CLASS_2_CURRICULUM_CHAPTERS
    if subject_id == "english" and int(class_no) == 3:
        return CLASS_3_CURRICULUM_CHAPTERS
    if subject_id == "english" and int(class_no) == 4:
        return CLASS_4_CURRICULUM_CHAPTERS
    if subject_id == "english" and int(class_no) == 5:
        return CLASS_5_CURRICULUM_CHAPTERS
    return ()


def session_content_version_is_current(session: dict[str, Any] | None) -> bool:
    if not session:
        return False
    state = session.get("state_json")
    if not isinstance(state, dict):
        # Structural recovery belongs to the state normalizer, not version expiry.
        return True
    chapter_state = state.get("chapter")
    if not isinstance(chapter_state, dict):
        return True
    chapter_id = str(chapter_state.get("chapter_id") or "")
    subject_id = str(state.get("subject_id") or session.get("subject_id") or "")
    try:
        class_no = int(state.get("target_class_no") or session.get("class_no") or 0)
    except (TypeError, ValueError, OverflowError):
        return True
    live_chapter = next(
        (
            chapter
            for chapter in _available_chapters(subject_id, class_no)
            if str(chapter.get("chapter_id") or "") == chapter_id
        ),
        None,
    )
    if not live_chapter:
        return False
    expected = str(live_chapter.get("content_version") or "")
    stored = str(chapter_state.get("content_version") or "")
    return bool(expected and stored == expected)


def _completed_chapter_ids(latest_curriculum_session: dict[str, Any] | None) -> list[str]:
    if not latest_curriculum_session:
        return []
    state_json = latest_curriculum_session.get("state_json") or {}
    subject_id = str(
        state_json.get("subject_id") or latest_curriculum_session.get("subject_id") or ""
    )
    class_no = int(
        state_json.get("target_class_no") or latest_curriculum_session.get("class_no") or 0
    )
    available_by_id = {
        str(chapter.get("chapter_id") or ""): chapter
        for chapter in _available_chapters(subject_id, class_no)
    }
    completed_versions = dict(state_json.get("completed_chapter_versions") or {})
    completed_certification_versions = dict(
        state_json.get("completed_chapter_certification_versions") or {}
    )

    def completion_is_current(chapter_id: str) -> bool:
        chapter = available_by_id.get(chapter_id) or {}
        required_version = str(
            chapter.get("certification_version")
            or chapter.get("content_version")
            or ""
        ).strip()
        completed_version = (
            completed_certification_versions.get(chapter_id)
            or completed_versions.get(chapter_id)
        )
        return not required_version or completed_version == required_version

    completed: list[str] = []
    for chapter_id in state_json.get("completed_chapter_ids") or []:
        cleaned = str(chapter_id).strip()
        if cleaned and completion_is_current(cleaned) and cleaned not in completed:
            completed.append(cleaned)
    if _session_status(latest_curriculum_session) == "complete":
        chapter_id = str((state_json.get("chapter") or {}).get("chapter_id") or "").strip()
        if chapter_id and completion_is_current(chapter_id) and chapter_id not in completed:
            completed.append(chapter_id)
    return completed


def _completed_chapter_versions(
    latest_curriculum_session: dict[str, Any] | None,
) -> dict[str, str]:
    if not latest_curriculum_session:
        return {}
    state_json = latest_curriculum_session.get("state_json") or {}
    return {
        str(chapter_id): str(content_version)
        for chapter_id, content_version in dict(
            state_json.get("completed_chapter_versions") or {}
        ).items()
        if str(chapter_id).strip() and str(content_version).strip()
    }


def _completed_chapter_certification_versions(
    latest_curriculum_session: dict[str, Any] | None,
) -> dict[str, str]:
    if not latest_curriculum_session:
        return {}
    state_json = latest_curriculum_session.get("state_json") or {}
    return {
        str(chapter_id): str(certification_version)
        for chapter_id, certification_version in dict(
            state_json.get("completed_chapter_certification_versions") or {}
        ).items()
        if str(chapter_id).strip() and str(certification_version).strip()
    }


def _next_available_chapter(
    subject_id: str,
    class_no: int,
    completed_chapter_ids: list[str],
) -> dict[str, Any] | None:
    completed = set(completed_chapter_ids)
    for chapter in _available_chapters(subject_id, class_no):
        if chapter["chapter_id"] not in completed:
            return chapter
    return None


def _public_chapter_summary(chapter: dict[str, Any] | None) -> dict[str, Any] | None:
    if not chapter:
        return None
    return {
        "chapter_id": chapter["chapter_id"],
        "chapter_no": int(chapter["chapter_no"]),
        "title": chapter.get("title") or chapter.get("chapter_title") or "",
        "book_title": chapter.get("book_title") or "",
        "unit_title": chapter.get("unit_title") or "",
        "source_url": chapter.get("source_url") or "",
        "source_note": chapter.get("source_note") or "",
    }


def _public_active_chapter(chapter: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = (
        "chapter_id",
        "chapter_no",
        "title",
        "book_title",
        "unit_title",
        "source_url",
        "source_note",
        "content_version",
    )
    return {key: chapter[key] for key in allowed_keys if key in chapter}


def _public_interrupt(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "interrupt_id": str(value.get("interrupt_id") or ""),
        "level_id": str(value.get("level_id") or ""),
        "focus": str(value.get("focus") or ""),
        "trigger_count": int(value.get("trigger_count") or 0),
        "masterclass_session_id": (
            str(value["masterclass_session_id"])
            if value.get("masterclass_session_id")
            else None
        ),
    }


def _public_interrupt_history(values: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            **(_public_interrupt(value) or {}),
            "resolution": str(value.get("resolution") or ""),
        }
        for value in values
        if isinstance(value, dict)
    ]


def _chapter_preview_status(
    chapter_id: str,
    completed_chapter_ids: list[str],
    next_chapter: dict[str, Any] | None,
) -> str:
    if chapter_id in completed_chapter_ids:
        return "complete"
    if next_chapter and chapter_id == next_chapter.get("chapter_id"):
        return "ready"
    return "locked_next"


def _carry_forward_focuses(
    recap_session: dict[str, Any] | None,
    placement_report: dict[str, Any] | None,
) -> list[str]:
    focuses: list[str] = []
    if recap_session:
        state_json = recap_session.get("state_json") or {}
        for module in state_json.get("modules") or []:
            focus = str(module.get("focus") or "").strip().lower()
            if focus and focus not in focuses:
                focuses.append(focus)
    if placement_report:
        for skill in placement_report.get("watchlist_skills") or []:
            label = str(skill.get("label") or "").strip().lower()
            if label and label not in focuses:
                focuses.append(label)
    return focuses[:8]


def _merge_memory_focuses(
    focuses: list[str],
    learning_memory: dict[str, Any] | None,
) -> list[str]:
    merged = list(focuses)
    for bucket in ("active_gaps", "improving_gaps"):
        for item in (learning_memory or {}).get(bucket) or []:
            if not isinstance(item, dict):
                continue
            label = str(item.get("gap") or item.get("skill_id") or "").strip().lower()
            if label and label not in merged:
                merged.append(label)
    return merged[:8]


def _public_memory_summary(value: Any) -> dict[str, Any]:
    memory = value if isinstance(value, dict) else {}
    def public_skill_evidence(items: Any) -> list[dict[str, Any]]:
        return [
            {
                "skill_id": str(item.get("skill_id") or ""),
                "latest_evidence": str(item.get("latest_evidence") or "")[:240],
                "last_attempt_type": str(item.get("last_attempt_type") or ""),
                "last_chapter_id": str(item.get("last_chapter_id") or ""),
                "attempts": int(item.get("attempts") or 0),
            }
            for item in items or []
            if isinstance(item, dict) and item.get("skill_id")
        ][:4]

    confirmed_skills = list(memory.get("mastered_skills") or []) + list(
        memory.get("strong_skills") or []
    )
    return {
        "active_gaps": [
            {
                "skill_id": str(item.get("skill_id") or ""),
                "gap": str(item.get("gap") or ""),
                "recommended_next_action": str(
                    item.get("recommended_next_action") or ""
                ),
                "latest_evidence": str(item.get("latest_evidence") or "")[:240],
                "last_attempt_type": str(item.get("last_attempt_type") or ""),
                "last_chapter_id": str(item.get("last_chapter_id") or ""),
            }
            for item in memory.get("active_gaps") or []
            if isinstance(item, dict)
        ][:4],
        "improving_skill_ids": [
            str(item.get("skill_id") or "")
            for item in memory.get("improving_gaps") or []
            if isinstance(item, dict) and item.get("skill_id")
        ][:4],
        "strong_skill_ids": [
            str(item.get("skill_id") or "")
            for item in confirmed_skills
            if isinstance(item, dict) and item.get("skill_id")
        ][:4],
        "improving_skills": public_skill_evidence(memory.get("improving_gaps")),
        "strong_skills": public_skill_evidence(confirmed_skills),
    }


def _progress(state: dict[str, Any]) -> dict[str, int]:
    levels = state.get("levels") or []
    return {
        "completed_levels": sum(1 for level in levels if level.get("status") == "complete"),
        "total_levels": len(levels),
        "current_level_index": int(state.get("current_level_index") or 0),
    }


def _public_chapter_assessment_progress(
    state: dict[str, Any],
) -> dict[str, Any] | None:
    assessment = state.get("chapter_assessment")
    if not assessment:
        return None
    selected_ids = list(assessment.get("selected_item_ids") or [])
    current_index = int(assessment.get("current_index") or 0)
    phase = str(state.get("phase") or "learning")
    status_by_phase = {
        "chapter_check": "in_progress",
        "remediation": "remediation",
        "needs_support": "needs_support",
        "complete": "passed",
    }
    history = list(assessment.get("attempt_history") or [])
    public_last_result = None
    if history:
        last_result = history[-1]
        public_last_result = {
            "attempt_no": int(last_result.get("attempt_no") or 0),
            "score": float(last_result.get("score") or 0.0),
            "passed": bool(last_result.get("passed")),
        }
    return {
        "status": status_by_phase.get(phase, "not_started"),
        "attempt_no": int(assessment.get("attempt_no") or 0),
        "item_number": min(current_index + 1, len(selected_ids)) if selected_ids else 0,
        "total_items": len(selected_ids),
        "last_result": public_last_result,
    }


def _public_level(level: dict[str, Any]) -> dict[str, Any]:
    return {
        "level_id": level["level_id"],
        "title": level["title"],
        "focus": level["focus"],
        "skill_ids": list(level.get("skill_ids") or []),
        "status": level.get("status") or "not_started",
        "teaching_goal": level.get("teaching_goal") or "",
        "guided_check_label": "Learn with a worked clue",
        "bridge_label": "Slow support if the clue is missed",
        "masterclass_label": "Focused reteach after repeated struggle",
        "independent_check_label": "Try without hints",
        "transfer_check_label": "Use the skill in a new example",
    }


def _current_activity(state: dict[str, Any]) -> dict[str, Any] | None:
    if state.get("status") in {"complete", "paused_for_masterclass"} or state.get(
        "phase"
    ) in {"paused_for_masterclass", "capped_support"}:
        return None
    if state.get("phase") == "chapter_check":
        return _current_chapter_check_activity(state)
    levels = state.get("levels") or []
    if not levels:
        return None
    level_index = int(state.get("current_level_index") or 0)
    if level_index >= len(levels):
        return None
    level = levels[level_index]
    if level.get("status") == "complete":
        return None
    kind = str(level.get("current_step") or "guided_check")
    check = _check_for_level(level, kind)
    attempt_no = 1 + sum(
        1 for previous in level.get("attempts") or [] if previous.get("kind") == kind
    )
    memory_note = _memory_support_note(state, level)
    language_support = localized_teaching_support(
        preferred_language=str(state.get("preferred_teaching_language") or "en"),
        skill_ids=level.get("skill_ids") or [],
        stage=kind,
        en_production_confidence=float(
            state.get("en_production_confidence") or 0.0
        ),
    )
    return {
        "activity_id": f"{level['level_id']}:{kind}:{attempt_no}",
        "level_id": level["level_id"],
        "level_index": level_index,
        "kind": kind,
        "title": _activity_title(level, kind),
        "focus": level.get("focus") or "",
        "skill_ids": list(level.get("skill_ids") or []),
        "teaching_block": " ".join(
            part
            for part in (language_support, memory_note, check["teaching_block"])
            if part
        ),
        "passage": check["passage"],
        "prompt": check["prompt"],
        "options": list(check.get("options") or []),
        "response_mode": check.get("response_mode") or "short",
        "answer_rule": check.get("answer_rule"),
        "evaluation_mode": check.get("evaluation_mode"),
        "preflight_rule": check.get("preflight_rule"),
        "pass_score": check.get("pass_score"),
        "rubric_criteria": [dict(criterion) for criterion in check.get("rubric_criteria") or []],
        "concept_slots": [dict(slot) for slot in check.get("concept_slots") or []],
        "forbidden_phrases": list(check.get("forbidden_phrases") or []),
        "min_response_words": check.get("min_response_words"),
        "ordered_concept_slot_ids": list(
            check.get("ordered_concept_slot_ids") or []
        ),
        "accepted_answers": list(check.get("accepted_answers") or []),
        "attempt_no": attempt_no,
    }


def _memory_support_note(state: dict[str, Any], level: dict[str, Any]) -> str:
    skill_ids = set(level.get("skill_ids") or [])
    memory = state.get("learner_memory")
    if not isinstance(memory, dict):
        return ""
    for bucket in ("active_gaps", "improving_gaps"):
        for item in memory.get(bucket) or []:
            if not isinstance(item, dict) or item.get("skill_id") not in skill_ids:
                continue
            action = str(item.get("recommended_next_action") or "").strip()
            gap = str(item.get("gap") or level.get("focus") or "this skill").strip()
            return (
                f"Zidd remembers that you are building {gap}. "
                f"{action}".strip()
            )
    return ""


def _new_chapter_assessment_state(definition: dict[str, Any] | None) -> dict[str, Any] | None:
    if not definition:
        return None
    return {
        **definition,
        "attempt_no": 0,
        "selected_item_ids": [],
        "current_index": 0,
        "responses": [],
        "attempt_history": [],
        "used_item_ids": [],
    }


def _begin_chapter_assessment(state: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    assessment = dict(updated.get("chapter_assessment") or {})
    attempt_no = int(assessment.get("attempt_no") or 0) + 1
    max_attempts = int(assessment.get("max_attempts") or 2)
    if attempt_no > max_attempts:
        raise ValueError("chapter_assessment_attempt_limit_exhausted")
    item_count = int(assessment.get("items_per_attempt") or 12)
    items = list(assessment.get("items") or [])
    used_item_ids = list(assessment.get("used_item_ids") or [])
    used_item_ids = list(
        dict.fromkeys(used_item_ids + list(assessment.get("selected_item_ids") or []))
    )
    selected_items = _select_chapter_assessment_items(
        items,
        item_count=item_count,
        attempt_no=attempt_no,
        used_item_ids=set(used_item_ids),
    )
    selected_item_ids = [str(item["item_id"]) for item in selected_items]
    if max_attempts >= 3 and (
        len(selected_item_ids) != item_count
        or set(selected_item_ids).intersection(used_item_ids)
    ):
        raise ValueError("chapter_assessment_fresh_form_unavailable")
    required_skill_ids = {
        skill_id for item in items for skill_id in item.get("skill_ids") or []
    }
    selected_skill_ids = {
        skill_id
        for item in selected_items
        for skill_id in item.get("skill_ids") or []
    }
    if selected_skill_ids != required_skill_ids:
        raise ValueError("chapter_assessment_form_cannot_cover_skills")
    assessment.update(
        {
            "attempt_no": attempt_no,
            "selected_item_ids": selected_item_ids,
            "current_index": 0,
            "responses": [],
            "used_item_ids": used_item_ids,
        }
    )
    updated["chapter_assessment"] = assessment
    updated["remediation_queue"] = []
    updated.pop("remediation_mode", None)
    updated["phase"] = "chapter_check"
    updated["status"] = "active"
    return updated


def _select_chapter_assessment_items(
    items: list[dict[str, Any]],
    *,
    item_count: int,
    attempt_no: int,
    used_item_ids: set[str],
) -> list[dict[str, Any]]:
    if not items:
        return []
    offset = ((attempt_no - 1) * item_count) % len(items)
    rotated = items[offset:] + items[:offset]
    taught_skills = list(
        dict.fromkeys(
            skill_id
            for item in items
            for skill_id in item.get("skill_ids") or []
        )
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add(candidate: dict[str, Any]) -> None:
        item_id = str(candidate["item_id"])
        if item_id not in selected_ids and len(selected) < item_count:
            selected.append(candidate)
            selected_ids.add(item_id)

    for skill_id in taught_skills:
        candidates = [
            item for item in rotated if skill_id in (item.get("skill_ids") or [])
        ]
        candidate = next(
            (
                item
                for item in candidates
                if str(item["item_id"]) not in used_item_ids
            ),
            candidates[0] if candidates else None,
        )
        if candidate:
            add(candidate)
    for candidate in rotated:
        if str(candidate["item_id"]) not in used_item_ids:
            add(candidate)
    for candidate in rotated:
        add(candidate)
    return selected


def _current_chapter_check_activity(state: dict[str, Any]) -> dict[str, Any] | None:
    assessment = state.get("chapter_assessment") or {}
    selected_ids = list(assessment.get("selected_item_ids") or [])
    current_index = int(assessment.get("current_index") or 0)
    if current_index >= len(selected_ids):
        return None
    item_id = selected_ids[current_index]
    item = next(
        (
            candidate
            for candidate in assessment.get("items") or []
            if str(candidate.get("item_id") or "") == item_id
        ),
        None,
    )
    if not item:
        raise ValueError("chapter_assessment_item_missing")
    attempt_no = int(assessment.get("attempt_no") or 1)
    return {
        **item,
        "activity_id": f"chapter_check:{attempt_no}:{item_id}",
        "authored_item_id": item_id,
        "level_id": "chapter_assessment",
        "level_index": -1,
        "kind": "chapter_check",
        "title": "Chapter check",
        "focus": "show what you can do across this chapter",
        "teaching_block": (
            "Work independently. Answer in English. "
            "Zidd will share the result after the chapter check."
        ),
        "response_mode": item.get("response_mode") or "short",
        "attempt_no": current_index + 1,
    }


def _apply_chapter_check_answer(
    state: dict[str, Any],
    *,
    activity: dict[str, Any],
    answer: str,
    answer_evaluation: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = dict(state)
    assessment = dict(updated.get("chapter_assessment") or {})
    responses = list(assessment.get("responses") or [])
    response = {
        "activity_id": activity["activity_id"],
        "item_id": activity["authored_item_id"],
        "answer": answer,
        "skill_ids": list(activity.get("skill_ids") or []),
        "correct": bool(answer_evaluation["correct"]),
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
        "evaluation_mode": (
            answer_evaluation.get("_evaluation_mode")
            or activity.get("evaluation_mode")
            or "deterministic"
        ),
    }
    responses.append(response)
    assessment["responses"] = responses
    assessment["current_index"] = int(assessment.get("current_index") or 0) + 1
    updated["chapter_assessment"] = assessment

    selected_ids = list(assessment.get("selected_item_ids") or [])
    if int(assessment["current_index"]) < len(selected_ids):
        updated["last_feedback"] = {
            "activity_id": activity["activity_id"],
            "level_id": "chapter_assessment",
            "kind": "chapter_check",
            "correct": None,
            "result_visible": False,
            "message": (
                "Answer saved. Keep going; results appear after the chapter check."
            ),
        }
    else:
        updated = _finish_chapter_assessment_attempt(updated)

    evaluation = {
        "activity_id": activity["activity_id"],
        "level_id": "chapter_assessment",
        "kind": "chapter_check",
        "focus": activity["focus"],
        "skill_ids": list(activity.get("skill_ids") or []),
        "correct": bool(answer_evaluation["correct"]),
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "missing_criteria": list(answer_evaluation["missing_criteria"]),
        "misconception_tags": list(answer_evaluation["misconception_tags"]),
        "blockers": list(answer_evaluation["blockers"]),
        "language_detected": str(answer_evaluation["language_detected"]),
        "model_score": answer_evaluation.get("model_score"),
        "evaluation_mode": (
            answer_evaluation.get("_evaluation_mode")
            or activity.get("evaluation_mode")
            or "deterministic"
        ),
        "attempt_no": int(activity.get("attempt_no") or 1),
    }
    return normalize_curriculum_state(updated), evaluation


def _chapter_assessment_result(assessment: dict[str, Any]) -> dict[str, Any]:
    responses = list(assessment.get("responses") or [])
    score = (
        sum(float(response.get("score") or 0.0) for response in responses)
        / len(responses)
        if responses
        else 0.0
    )
    taught_skill_ids = list(
        dict.fromkeys(
            skill_id
            for response in responses
            for skill_id in response.get("skill_ids") or []
        )
    )
    skill_scores = {}
    for skill_id in taught_skill_ids:
        skill_responses = [
            response
            for response in responses
            if skill_id in (response.get("skill_ids") or [])
        ]
        skill_scores[skill_id] = round(
            sum(float(response.get("score") or 0.0) for response in skill_responses)
            / len(skill_responses),
            4,
        )
    failed_rubric_responses = [
        response
        for response in responses
        if response.get("evaluation_mode") == "llm_rubric"
        and not bool(response.get("correct"))
    ]
    failed_rubric_item_ids = [
        str(response.get("item_id") or "")
        for response in failed_rubric_responses
    ]
    failed_hard_blocker_responses = [
        response
        for response in responses
        if CHAPTER_ASSESSMENT_HARD_BLOCKERS.intersection(
            response.get("blockers") or []
        )
    ]
    failed_hard_blocker_item_ids = [
        str(response.get("item_id") or "")
        for response in failed_hard_blocker_responses
    ]
    hard_blocker_skill_ids = list(
        dict.fromkeys(
            skill_id
            for response in failed_hard_blocker_responses
            for skill_id in response.get("skill_ids") or []
        )
    )
    gated_responses = failed_hard_blocker_responses + failed_rubric_responses
    remediation_skill_ids = [
        skill_id
        for skill_id in taught_skill_ids
        if skill_scores[skill_id] < float(assessment.get("pass_score") or 0.8)
        or any(
            skill_id in (response.get("skill_ids") or [])
            for response in gated_responses
        )
    ]
    passed = (
        score >= float(assessment.get("pass_score") or 0.8)
        and all(skill_score >= 0.6 for skill_score in skill_scores.values())
        and not failed_rubric_item_ids
        and not failed_hard_blocker_item_ids
    )
    return {
        "attempt_no": int(assessment.get("attempt_no") or 1),
        "score": round(score, 4),
        "skill_scores": skill_scores,
        "passed": passed,
        "failed_rubric_item_ids": failed_rubric_item_ids,
        "failed_hard_blocker_item_ids": failed_hard_blocker_item_ids,
        "hard_blocker_skill_ids": hard_blocker_skill_ids,
        "weak_skill_ids": [
            skill_id
            for skill_id, skill_score in skill_scores.items()
            if skill_score < 0.6
        ],
        "remediation_skill_ids": remediation_skill_ids,
    }


def _finish_chapter_assessment_attempt(state: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    assessment = dict(updated.get("chapter_assessment") or {})
    responses = list(assessment.get("responses") or [])
    result = _chapter_assessment_result(assessment)
    passed = bool(result["passed"])
    assessment["attempt_history"] = list(assessment.get("attempt_history") or []) + [
        result
    ]
    updated["chapter_assessment"] = assessment
    attempt_no = int(assessment.get("attempt_no") or 1)
    max_attempts = int(assessment.get("max_attempts") or 2)
    if passed:
        updated = _complete_chapter(updated)
        updated["last_feedback"] = {
            "activity_id": responses[-1]["activity_id"],
            "level_id": "chapter_assessment",
            "kind": "chapter_check",
            "correct": True,
            "result_visible": True,
            "message": "Chapter check passed. The next chapter is ready.",
        }
    elif attempt_no >= max_attempts:
        updated = _record_assessment_support_event(
            updated,
            result=result,
            path_type="parent_supported_pause",
        )
        focus = _assessment_support_focus(
            updated,
            result["remediation_skill_ids"],
        )
        updated["phase"] = "needs_support"
        updated["status"] = "active"
        updated["remediation_queue"] = []
        updated.pop("remediation_mode", None)
        updated["support_required"] = {
            "reason": "chapter_check_attempts_exhausted",
            "attempt_count": attempt_no,
            "weak_skill_ids": list(result["weak_skill_ids"]),
            "remediation_skill_ids": list(result["remediation_skill_ids"]),
            "focus": focus,
            "cap": {
                "used": attempt_no,
                "limit": max_attempts,
                "scope": "chapter_check",
            },
            "history": list(updated.get("assessment_support_history") or []),
        }
        updated["last_feedback"] = {
            "activity_id": responses[-1]["activity_id"],
            "level_id": "chapter_assessment",
            "kind": "chapter_check",
            "correct": False,
            "result_visible": True,
            "message": (
                "This chapter is paused. Zidd has saved the exact skills that need "
                "a revised support path."
            ),
        }
    else:
        path_type = (
            "expanded_revision" if attempt_no >= 2 else "focused_revision"
        )
        updated = _record_assessment_support_event(
            updated,
            result=result,
            path_type=path_type,
        )
        updated = _start_assessment_remediation(
            updated,
            result["remediation_skill_ids"],
            mode=path_type,
            skill_scores=result["skill_scores"],
            priority_skill_ids=result["hard_blocker_skill_ids"],
        )
        updated["last_feedback"] = {
            "activity_id": responses[-1]["activity_id"],
            "level_id": "chapter_assessment",
            "kind": "chapter_check",
            "correct": False,
            "result_visible": True,
            "message": (
                "Zidd added three focused revision levels before one final check."
                if path_type == "expanded_revision"
                else "This chapter needs focused revision before another check."
            ),
        }
    return updated


def _start_assessment_remediation(
    state: dict[str, Any],
    weak_skill_ids: list[str],
    *,
    mode: str = "focused_revision",
    skill_scores: dict[str, float] | None = None,
    priority_skill_ids: list[str] | None = None,
) -> dict[str, Any]:
    updated = dict(state)
    levels = [dict(level) for level in updated.get("levels") or []]
    if mode == "expanded_revision":
        plan, targeted_skill_ids, deferred_skill_ids = _build_assessment_revision_plan(
            levels,
            weak_skill_ids,
            skill_scores=skill_scores,
            priority_skill_ids=priority_skill_ids,
        )
        updated["levels"] = levels
        updated["assessment_revision_plan"] = plan
        updated["assessment_revision_index"] = 0
        updated["assessment_revision_targeted_skill_ids"] = targeted_skill_ids
        updated["assessment_revision_deferred_skill_ids"] = deferred_skill_ids
        updated["remediation_queue"] = list(
            dict.fromkeys(entry["level_id"] for entry in plan)
        )
        updated["remediation_mode"] = mode
        updated["phase"] = "remediation"
        updated["status"] = "active"
        return _activate_assessment_revision_entry(updated, plan_index=0)

    weak = set(weak_skill_ids)
    remediation_queue = [
        str(level["level_id"])
        for level in levels
        if weak.intersection(level.get("skill_ids") or [])
    ]
    if not remediation_queue:
        raise ValueError("chapter_assessment_remediation_level_missing")
    start_step = "revision_level_1" if mode == "expanded_revision" else "masterclass"
    for level in levels:
        if level["level_id"] == remediation_queue[0]:
            level["status"] = "in_progress"
            level["current_step"] = start_step
            level["return_step"] = "independent_check"
    updated["levels"] = levels
    updated["current_level_index"] = next(
        index
        for index, level in enumerate(levels)
        if level["level_id"] == remediation_queue[0]
    )
    updated["remediation_queue"] = remediation_queue
    updated["remediation_mode"] = mode
    updated["phase"] = "remediation"
    updated["status"] = "active"
    return updated


def _build_assessment_revision_plan(
    levels: list[dict[str, Any]],
    weak_skill_ids: list[str],
    *,
    skill_scores: dict[str, float] | None = None,
    priority_skill_ids: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    scores = skill_scores or {}
    original_order = {
        skill_id: index
        for index, skill_id in enumerate(dict.fromkeys(weak_skill_ids))
    }
    priority = set(priority_skill_ids or [])
    ordered_skills = sorted(
        original_order,
        key=lambda skill_id: (
            0 if skill_id in priority else 1,
            float(scores.get(skill_id, 1.0)),
            original_order[skill_id],
        ),
    )
    weak = set(ordered_skills)
    candidates = [
        {
            "level_index": index,
            "level_id": str(level["level_id"]),
            "targeted_skill_ids": [
                skill_id
                for skill_id in ordered_skills
                if skill_id in set(level.get("skill_ids") or [])
            ],
        }
        for index, level in enumerate(levels)
        if weak.intersection(level.get("skill_ids") or [])
    ]
    if not candidates:
        raise ValueError("chapter_assessment_remediation_level_missing")

    plan: list[dict[str, Any]] = []
    usage_by_level: dict[str, int] = {}
    uncovered = set(ordered_skills)
    while len(plan) < len(REVISION_STEPS):
        eligible = [
            candidate
            for candidate in candidates
            if usage_by_level.get(candidate["level_id"], 0) < len(REVISION_STEPS)
        ]
        if not eligible:
            break

        def candidate_rank(candidate: dict[str, Any]) -> tuple[int, int, int, int]:
            targeted = set(candidate["targeted_skill_ids"])
            new_skills = targeted.intersection(uncovered)
            earliest_priority = min(
                (
                    ordered_skills.index(skill_id)
                    for skill_id in new_skills
                ),
                default=len(ordered_skills),
            )
            return (
                -len(new_skills),
                earliest_priority,
                usage_by_level.get(candidate["level_id"], 0),
                int(candidate["level_index"]),
            )

        selected = min(eligible, key=candidate_rank)
        level_id = str(selected["level_id"])
        revision_index = usage_by_level.get(level_id, 0)
        kind = REVISION_STEPS[revision_index]
        level = levels[int(selected["level_index"])]
        if kind not in (level.get("checks") or {}):
            raise ValueError(
                f"chapter_assessment_revision_activity_missing:{level_id}:{kind}"
            )
        plan.append(
            {
                "level_id": level_id,
                "kind": kind,
                "targeted_skill_ids": list(selected["targeted_skill_ids"]),
            }
        )
        usage_by_level[level_id] = revision_index + 1
        uncovered.difference_update(selected["targeted_skill_ids"])

    if len(plan) != len(REVISION_STEPS):
        raise ValueError("chapter_assessment_revision_plan_incomplete")
    targeted = [skill_id for skill_id in ordered_skills if skill_id not in uncovered]
    deferred = [skill_id for skill_id in ordered_skills if skill_id in uncovered]
    return plan, targeted, deferred


def _activate_assessment_revision_entry(
    state: dict[str, Any],
    *,
    plan_index: int,
) -> dict[str, Any]:
    updated = dict(state)
    plan = list(updated.get("assessment_revision_plan") or [])
    if plan_index < 0 or plan_index >= len(plan):
        raise ValueError("chapter_assessment_revision_plan_index_invalid")
    entry = dict(plan[plan_index])
    levels = [dict(level) for level in updated.get("levels") or []]
    level_index = next(
        (
            index
            for index, level in enumerate(levels)
            if level.get("level_id") == entry.get("level_id")
        ),
        None,
    )
    if level_index is None:
        raise ValueError("chapter_assessment_remediation_level_missing")
    level = dict(levels[level_index])
    if entry.get("kind") not in (level.get("checks") or {}):
        raise ValueError(
            "chapter_assessment_revision_activity_missing:"
            f"{entry.get('level_id')}:{entry.get('kind')}"
        )
    level["status"] = "in_progress"
    level["current_step"] = str(entry["kind"])
    level["return_step"] = "independent_check"
    levels[level_index] = level
    updated["levels"] = levels
    updated["current_level_index"] = level_index
    updated["assessment_revision_index"] = plan_index
    return updated


def _remediation_start_step(state: dict[str, Any]) -> str:
    return (
        "revision_level_1"
        if state.get("remediation_mode") == "expanded_revision"
        else "masterclass"
    )


def _advance_expanded_revision(
    state: dict[str, Any],
    *,
    levels: list[dict[str, Any]],
    level: dict[str, Any],
    level_index: int,
    kind: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    plan = list(state.get("assessment_revision_plan") or [])
    plan_index = int(state.get("assessment_revision_index") or 0)
    if plan_index >= len(plan):
        raise ValueError("chapter_assessment_revision_plan_index_invalid")
    entry = plan[plan_index]
    if entry.get("level_id") != level.get("level_id") or entry.get("kind") != kind:
        raise ValueError("chapter_assessment_revision_plan_mismatch")
    level["status"] = "complete"
    level["current_step"] = "complete"
    levels[level_index] = level
    state["levels"] = levels
    next_plan_index = plan_index + 1
    if next_plan_index < len(plan):
        state = _activate_assessment_revision_entry(
            state,
            plan_index=next_plan_index,
        )
        levels = list(state.get("levels") or levels)
    else:
        state["assessment_revision_index"] = next_plan_index
        state["remediation_queue"] = []
        state["current_level_index"] = level_index
        state = _begin_chapter_assessment(state)
        levels = list(state.get("levels") or levels)
    return state, levels, dict(levels[level_index])


def _record_assessment_support_event(
    state: dict[str, Any],
    *,
    result: dict[str, Any],
    path_type: str,
) -> dict[str, Any]:
    updated = dict(state)
    updated["assessment_support_history"] = list(
        updated.get("assessment_support_history") or []
    ) + [{
        "attempt_no": int(result.get("attempt_no") or 1),
        "score": float(result.get("score") or 0.0),
        "skill_ids": list(result.get("remediation_skill_ids") or []),
        "path_type": path_type,
    }]
    return updated


def _assessment_support_focus(
    state: dict[str, Any],
    skill_ids: list[str],
) -> str:
    weak = set(skill_ids)
    focuses = list(
        dict.fromkeys(
            str(level.get("focus") or "").strip()
            for level in state.get("levels") or []
            if weak.intersection(level.get("skill_ids") or [])
            and str(level.get("focus") or "").strip()
        )
    )
    if focuses:
        return "; ".join(focuses)
    return "; ".join(
        dict.fromkeys(
            str(skill_id)
            .split(".")[-1]
            .replace("_", " ")
            .title()
            for skill_id in skill_ids
            if str(skill_id).strip()
        )
    )


def _ensure_assessment_support_contract(
    state: dict[str, Any],
) -> dict[str, Any]:
    if state.get("phase") != "needs_support":
        return state
    support_required = state.get("support_required")
    assessment = state.get("chapter_assessment")
    if (
        not isinstance(support_required, dict)
        or support_required.get("reason") != "chapter_check_attempts_exhausted"
        or not isinstance(assessment, dict)
    ):
        return state

    attempt_no = int(
        support_required.get("attempt_count")
        or assessment.get("attempt_no")
        or 1
    )
    max_attempts = int(assessment.get("max_attempts") or attempt_no)
    remediation_skill_ids = list(
        support_required.get("remediation_skill_ids") or []
    )
    history = support_required.get("history")
    if not isinstance(history, list) or not history:
        history = []
        for result in assessment.get("attempt_history") or []:
            if not isinstance(result, dict):
                continue
            result_attempt_no = int(result.get("attempt_no") or 1)
            history.append({
                "attempt_no": result_attempt_no,
                "score": float(result.get("score") or 0.0),
                "skill_ids": list(result.get("remediation_skill_ids") or []),
                "path_type": (
                    "parent_supported_pause"
                    if result_attempt_no >= max_attempts
                    else "expanded_revision"
                    if result_attempt_no >= 2
                    else "focused_revision"
                ),
            })
    enriched = {
        **support_required,
        "focus": str(support_required.get("focus") or "").strip()
        or _assessment_support_focus(state, remediation_skill_ids),
        "cap": (
            dict(support_required["cap"])
            if isinstance(support_required.get("cap"), dict)
            else {
                "used": attempt_no,
                "limit": max_attempts,
                "scope": "chapter_check",
            }
        ),
        "history": history,
    }
    return {
        **state,
        "assessment_support_history": list(
            state.get("assessment_support_history") or history
        ),
        "support_required": enriched,
    }


def _complete_chapter(state: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    updated["status"] = "complete"
    updated["phase"] = "complete"
    completed_ids = list(updated.get("completed_chapter_ids") or [])
    chapter_id = str((updated.get("chapter") or {}).get("chapter_id") or "")
    if chapter_id and chapter_id not in completed_ids:
        completed_ids.append(chapter_id)
    updated["completed_chapter_ids"] = completed_ids
    chapter_version = str(
        (updated.get("chapter") or {}).get("content_version") or ""
    ).strip()
    if chapter_id and chapter_version:
        completed_versions = dict(updated.get("completed_chapter_versions") or {})
        completed_versions[chapter_id] = chapter_version
        updated["completed_chapter_versions"] = completed_versions
    certification_version = str(
        (updated.get("chapter") or {}).get("certification_version")
        or chapter_version
    ).strip()
    if chapter_id and certification_version:
        completed_certification_versions = dict(
            updated.get("completed_chapter_certification_versions") or {}
        )
        completed_certification_versions[chapter_id] = certification_version
        updated["completed_chapter_certification_versions"] = (
            completed_certification_versions
        )
    return updated


def _public_activity(activity: dict[str, Any] | None) -> dict[str, Any] | None:
    if not activity:
        return None
    return {
        "activity_id": activity["activity_id"],
        "level_id": activity["level_id"],
        "kind": activity["kind"],
        "title": activity["title"],
        "focus": activity["focus"],
        "skill_ids": list(activity.get("skill_ids") or []),
        "teaching_block": activity["teaching_block"],
        "passage": activity["passage"],
        "prompt": activity["prompt"],
        "options": list(activity.get("options") or []) or None,
        "response_mode": activity.get("response_mode") or "short",
        "attempt_no": int(activity.get("attempt_no") or 1),
        "can_answer": True,
    }


def _check_for_level(level: dict[str, Any], kind: str) -> dict[str, Any]:
    checks = level.get("checks") or {}
    if kind in checks:
        return checks[kind]
    if kind in REVISION_STEPS:
        base = checks.get("masterclass") or checks.get("bridge") or checks["guided_check"]
        revision_no = REVISION_STEPS.index(kind) + 1
        return {
            **base,
            "teaching_block": (
                f"Revision level {revision_no}: rebuild {level['focus']} with one more "
                "supported check before returning to the independent attempt. "
                f"{base['teaching_block']}"
            ),
        }
    return checks["guided_check"]


def _activity_title(level: dict[str, Any], kind: str) -> str:
    if kind == "guided_check":
        return f"Learn: {level['title']}"
    if kind == "bridge":
        return f"Bridge: {level['title']}"
    if kind == "masterclass":
        return f"Masterclass: {level['title']}"
    if kind.startswith("revision_level_"):
        return f"Revision {kind.replace('revision_level_', '')}: {level['title']}"
    if kind == "transfer_check":
        return f"Use it again: {level['title']}"
    return f"Show it: {level['title']}"


def _answer_matches(activity: dict[str, Any], answer: str) -> bool:
    cleaned = _normalize(answer)
    if activity.get("evaluation_mode") == "llm_rubric":
        raise ValueError("open_answer_evaluation_required")
    if activity.get("answer_rule") == "past_tense_travel_sentence":
        return _matches_past_tense_travel_sentence(cleaned)
    if activity.get("answer_rule") == "wise_parrot_reason":
        return _matches_wise_parrot_reason(cleaned)
    if activity.get("answer_rule") == "release_opinion_reason":
        return _matches_release_opinion_reason(cleaned)
    if activity.get("answer_rule") == "bird_feeder_procedure":
        return _matches_bird_feeder_procedure(cleaned)
    return any(
        _accepted_phrase_matches(cleaned, _normalize(expected))
        for expected in activity.get("accepted_answers") or []
    )


def evaluate_deterministic_answer(
    activity: dict[str, Any],
    answer: str,
) -> dict[str, Any]:
    if activity.get("answer_rule") != "concept_slots":
        correct = _answer_matches(activity, answer)
        return {
            "correct": correct,
            "score": 1.0 if correct else 0.0,
            "confidence": 1.0,
            "criteria": [
                {
                    "id": "curriculum_answer_match",
                    "met": correct,
                    "quality": 1.0 if correct else 0.0,
                    "evidence_quote": answer.strip() or "(empty answer)",
                }
            ],
            "missing_criteria": [] if correct else ["curriculum_answer_match"],
            "misconception_tags": [],
            "blockers": [] if correct else ["curriculum_gap"],
            "language_detected": _detect_answer_language(answer),
            "model_score": None,
        }

    cleaned_answer = _normalize(answer)
    forbidden_match = next(
        (
            phrase
            for phrase in activity.get("forbidden_phrases") or []
            if _contains_normalized_phrase(cleaned_answer, _normalize(phrase))
        ),
        None,
    )
    criteria = []
    missing_criteria = []
    matched_candidates: dict[str, list[tuple[int, int, int, str]]] = {}
    matched_phrases: dict[str, str | None] = {}
    for slot in activity.get("concept_slots") or []:
        matches = [
            (*span, -len(normalized_phrase.split()), phrase)
            for phrase in slot.get("any_of") or []
            for normalized_phrase in [_normalize(phrase)]
            for span in _concept_phrase_spans(cleaned_answer, normalized_phrase)
        ]
        matches.sort(key=lambda match: (match[0], match[2]))
        matched_phrase = matches[0][3] if matches else None
        met = matched_phrase is not None
        criterion_id = str(slot.get("id") or "").strip()
        matched_candidates[criterion_id] = matches
        matched_phrases[criterion_id] = matched_phrase
        criteria.append(
            {
                "id": criterion_id,
                "met": met,
                "quality": 1.0 if met else 0.0,
                "evidence_quote": matched_phrase or "(missing concept)",
            }
        )
        if not met:
            missing_criteria.append(criterion_id)

    min_response_words = activity.get("min_response_words")
    if min_response_words is not None:
        word_count = len(cleaned_answer.split())
        minimum_met = word_count >= int(min_response_words)
        criteria.append(
            {
                "id": "response_min_words",
                "met": minimum_met,
                "quality": 1.0 if minimum_met else 0.0,
                "evidence_quote": (
                    f"{word_count} words (minimum {int(min_response_words)})"
                ),
            }
        )
        if not minimum_met:
            missing_criteria.append("response_min_words")

    ordered_slot_ids = list(activity.get("ordered_concept_slot_ids") or [])
    if ordered_slot_ids:
        selected_sequence: list[tuple[int, int, int, str]] = []
        previous_end = 0
        for slot_id in ordered_slot_ids:
            candidate = next(
                (
                    match
                    for match in matched_candidates.get(str(slot_id), [])
                    if match[0] >= previous_end
                ),
                None,
            )
            if candidate is None:
                break
            selected_sequence.append(candidate)
            previous_end = candidate[1]
        sequence_met = len(selected_sequence) == len(ordered_slot_ids)
        sequence_phrases = (
            [match[3] for match in selected_sequence]
            if sequence_met
            else [matched_phrases.get(str(slot_id)) for slot_id in ordered_slot_ids]
        )
        criteria.append(
            {
                "id": "concept_sequence",
                "met": sequence_met,
                "quality": 1.0 if sequence_met else 0.0,
                "evidence_quote": "; ".join(
                    f"{slot_id}: {phrase or '(missing concept)'}"
                    for slot_id, phrase in zip(
                        ordered_slot_ids,
                        sequence_phrases,
                    )
                ),
            }
        )
        if not sequence_met:
            missing_criteria.append("concept_sequence")
    score = (
        sum(float(criterion["quality"]) for criterion in criteria) / len(criteria)
        if criteria
        else 0.0
    )
    blockers = ["contradictory_response"] if forbidden_match else []
    correct = bool(criteria) and not missing_criteria and not blockers
    return {
        "correct": correct,
        "score": round(score, 4),
        "confidence": 1.0,
        "criteria": criteria,
        "missing_criteria": missing_criteria,
        "misconception_tags": (
            ["explicit_contradiction"] if forbidden_match else []
        ),
        "blockers": blockers or ([] if correct else ["curriculum_gap"]),
        "language_detected": _detect_answer_language(answer),
        "model_score": None,
    }


# Compatibility for callers that still use the former private name.
_evaluate_deterministic_answer = evaluate_deterministic_answer


def _detect_answer_language(answer: str) -> str:
    if re.search(r"[\u0900-\u097f]", answer):
        return "hi"
    return "en"


def _contains_normalized_phrase(text: str, phrase: str) -> bool:
    return _normalized_phrase_position(text, phrase) is not None


def _normalized_phrase_position(text: str, phrase: str) -> int | None:
    return next(iter(_normalized_phrase_positions(text, phrase)), None)


def _normalized_phrase_positions(text: str, phrase: str) -> list[int]:
    if not text or not phrase:
        return []
    text_words = text.split()
    phrase_words = phrase.split()
    span = len(phrase_words)
    return [
        start
        for start in range(len(text_words) - span + 1)
        if text_words[start : start + span] == phrase_words
    ]


_CONCEPT_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "to",
    "was",
    "were",
    "with",
}
_NEGATION_WORDS = {
    "ain",
    "aren",
    "cannot",
    "couldn",
    "didn",
    "doesn",
    "don",
    "isn",
    "never",
    "no",
    "not",
    "wasn",
    "weren",
    "won",
    "wouldn",
}
_CONCEPT_TOKEN_ALIASES = {
    "blended": "blend",
    "blending": "blend",
    "blends": "blend",
    "camouflage": "blend",
    "camouflaged": "blend",
    "camouflages": "blend",
    "camouflaging": "blend",
    "dived": "dive",
    "dives": "dive",
    "diving": "dive",
    "eyes": "eye",
    "hopped": "hop",
    "hopping": "hop",
    "leaves": "leaf",
    "locations": "place",
    "match": "blend",
    "matched": "blend",
    "matches": "blend",
    "matching": "blend",
    "needed": "need",
    "needs": "need",
    "parts": "place",
    "places": "place",
    "provided": "provide",
    "provides": "provide",
    "providing": "provide",
    "remembered": "remember",
    "remembering": "remember",
    "remembers": "remember",
    "reeds": "reed",
    "spaces": "place",
    "speckled": "speckle",
    "speckles": "speckle",
    "uses": "use",
    "used": "use",
    "using": "use",
}


def _concept_token(word: str) -> str:
    aliased = _CONCEPT_TOKEN_ALIASES.get(word)
    if aliased:
        return aliased
    if len(word) > 4 and word.endswith("ies"):
        return f"{word[:-3]}y"
    if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _concept_phrase_spans(text: str, phrase: str) -> list[tuple[int, int]]:
    answer_words = text.split()
    phrase_words = phrase.split()
    expected_has_negation = _has_negation(phrase_words)
    expected_tokens = [
        _concept_token(word)
        for word in phrase_words
        if word not in _CONCEPT_STOP_WORDS
    ]

    def allowed(span: tuple[int, int]) -> bool:
        if expected_has_negation:
            return True
        start, end = span
        if _has_negation(answer_words[max(0, start - 3) : end]):
            return False
        for index in range(end, len(answer_words)):
            if answer_words[index] not in {"but", "however", "yet"}:
                continue
            tail = answer_words[index + 1 : index + 10]
            tail_tokens = {
                _concept_token(word)
                for word in tail
                if word not in _CONCEPT_STOP_WORDS
            }
            if _has_negation(tail) and tail_tokens.intersection(expected_tokens):
                return False
        return True

    exact = _normalized_phrase_positions(text, phrase)
    if exact:
        span = len(phrase.split())
        return [
            candidate
            for position in exact
            for candidate in [(position, position + span)]
            if allowed(candidate)
        ]

    if not expected_tokens:
        return []
    answer_tokens = [
        (index, _concept_token(word))
        for index, word in enumerate(answer_words)
        if word not in _CONCEPT_STOP_WORDS
    ]
    ordered_spans: list[tuple[int, int]] = []
    for first_index, (first_answer_index, first_token) in enumerate(answer_tokens):
        if first_token != expected_tokens[0]:
            continue
        matched_positions = [first_answer_index]
        cursor = first_index + 1
        for expected in expected_tokens[1:]:
            match = next(
                (
                    (answer_index, token_index)
                    for token_index, (answer_index, token) in enumerate(
                        answer_tokens[cursor:],
                        start=cursor,
                    )
                    if token == expected
                ),
                None,
            )
            if match is None:
                break
            answer_index, token_index = match
            matched_positions.append(answer_index)
            cursor = token_index + 1
        if len(matched_positions) == len(expected_tokens):
            candidate = (matched_positions[0], matched_positions[-1] + 1)
            raw_span = candidate[1] - candidate[0]
            if raw_span <= max(8, len(expected_tokens) * 4) and allowed(candidate):
                ordered_spans.append(candidate)
    if ordered_spans:
        return list(dict.fromkeys(ordered_spans))

    max_window = max(8, len(expected_tokens) * 4)
    unordered_spans: list[tuple[int, int]] = []
    for start_index in range(len(answer_tokens)):
        for end_index in range(
            start_index + 1,
            min(len(answer_tokens), start_index + max_window) + 1,
        ):
            window = answer_tokens[start_index:end_index]
            window_tokens = {token for _, token in window}
            if not set(expected_tokens).issubset(window_tokens):
                continue
            candidate = (window[0][0], window[-1][0] + 1)
            if candidate[1] - candidate[0] <= max_window and allowed(candidate):
                unordered_spans.append(candidate)
            break
    if unordered_spans:
        return list(dict.fromkeys(unordered_spans))
    return []


def _has_negation(words: list[str]) -> bool:
    return bool(
        _NEGATION_WORDS.intersection(words)
        or any(left == "can" and right == "t" for left, right in zip(words, words[1:]))
    )


def _normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split())


def _accepted_phrase_matches(cleaned_answer: str, expected: str) -> bool:
    if not cleaned_answer or not expected:
        return False
    if cleaned_answer == expected:
        return True
    answer_words = cleaned_answer.split()
    expected_words = expected.split()
    span = len(expected_words)
    for start in range(0, len(answer_words) - span + 1):
        if answer_words[start : start + span] != expected_words:
            continue
        preceding_words = answer_words[:start]
        if _has_negation(preceding_words):
            continue
        return True
    return False


def _open_answer_preflight(activity: dict[str, Any], answer: str) -> bool:
    rule = activity.get("preflight_rule")
    if rule == "journey_paragraph_80_100":
        return _matches_journey_paragraph(answer)
    if rule == "story_continuation_60_90":
        return _matches_story_continuation(answer)
    if rule == "frog_compare_25_50":
        return _matches_long_writing_structure(
            answer,
            min_words=25,
            max_words=50,
            min_sentences=2,
            min_unique_words=14,
        )
    if rule == "frog_message_35_60":
        return _matches_long_writing_structure(
            answer,
            min_words=35,
            max_words=60,
            min_sentences=3,
            min_unique_words=18,
            require_first_person=True,
        )
    return bool(answer.strip())


def evaluator_activity_for_answer(
    activity: dict[str, Any],
    answer: str,
) -> dict[str, Any] | None:
    if activity.get("evaluation_mode") == "llm_rubric":
        return dict(activity)
    if activity.get("answer_rule") != "concept_slots":
        return None
    words = _normalize(answer).split()
    adversative_review = any(
        word in {"although", "but", "however", "though", "yet"}
        and _has_negation(words[index + 1 :])
        for index, word in enumerate(words)
    )
    deterministic = evaluate_deterministic_answer(activity, answer)
    min_response_words = int(activity.get("min_response_words") or 0)
    substantial_paraphrase = len(words) >= max(5, min_response_words)
    needs_semantic_review = adversative_review or bool(
        not deterministic["correct"]
        and substantial_paraphrase
        and "contradictory_response" not in deterministic["blockers"]
    )
    if not needs_semantic_review:
        return None
    rubric_criteria = [
        {
            "id": str(slot["id"]),
            "description": str(slot.get("description") or slot["id"]),
            "required": True,
            "min_quality": 0.7,
        }
        for slot in activity.get("concept_slots") or []
    ]
    ordered_slot_ids = [
        str(slot_id) for slot_id in activity.get("ordered_concept_slot_ids") or []
    ]
    if ordered_slot_ids:
        rubric_criteria.append(
            {
                "id": "concept_sequence",
                "description": (
                    "Presents the required concepts in this order: "
                    + " -> ".join(ordered_slot_ids)
                    + "."
                ),
                "required": True,
                "min_quality": 0.7,
            }
        )
    return {
        **activity,
        "evaluation_mode": "llm_rubric",
        "rubric_criteria": rubric_criteria,
    }


def decide_open_answer_evaluation(
    activity: dict[str, Any],
    raw_evaluation: SchoolRubricEvaluation | dict[str, Any],
    *,
    answer: str,
) -> dict[str, Any]:
    evaluation = (
        raw_evaluation
        if isinstance(raw_evaluation, SchoolRubricEvaluation)
        else SchoolRubricEvaluation.model_validate(
            raw_evaluation
            if isinstance(raw_evaluation, dict)
            else raw_evaluation.model_dump()
        )
    )
    authored_criteria = list(activity.get("rubric_criteria") or [])
    authored_ids = [str(criterion.get("id") or "") for criterion in authored_criteria]
    evaluated_ids = [criterion.id for criterion in evaluation.criteria]
    if (
        activity.get("evaluation_mode") != "llm_rubric"
        or evaluation.schema_version != RUBRIC_SCHEMA_VERSION
        or evaluation.item_id != activity.get("activity_id")
        or set(evaluation.skill_ids) != set(activity.get("skill_ids") or [])
        or len(evaluation.skill_ids) != len(set(evaluation.skill_ids))
        or not authored_ids
        or len(authored_ids) != len(set(authored_ids))
        or evaluated_ids != authored_ids
        or len(evaluated_ids) != len(set(evaluated_ids))
    ):
        raise ValueError("invalid_open_answer_evaluation_contract")

    normalized_answer = _normalize(answer)
    canonical_criteria = []
    for criterion in evaluation.criteria:
        quote = _normalize(criterion.evidence_quote)
        traceable = bool(
            quote
            and quote not in {"empty answer", "(empty answer)"}
            and quote in normalized_answer
        )
        if traceable:
            canonical_criteria.append(criterion)
            continue
        canonical_criteria.append(
            criterion.model_copy(
                update={
                    "evidence_quote": (
                        answer.strip()
                        if criterion.met and answer.strip()
                        else "(empty answer)"
                    )
                }
            )
        )
    evaluation = evaluation.model_copy(update={"criteria": canonical_criteria})

    required = [criterion for criterion in authored_criteria if criterion.get("required", True)]
    model_failed_criterion_ids = {
        str(criterion["id"])
        for criterion in required
        if not next(
            item for item in evaluation.criteria if item.id == str(criterion["id"])
        ).met
        or next(
            item for item in evaluation.criteria if item.id == str(criterion["id"])
        ).quality
        < float(criterion.get("min_quality", 0.6))
    }

    passage = str(activity.get("passage") or "").strip()
    if passage:
        canonical_by_id = {
            criterion.id: criterion for criterion in evaluation.criteria
        }
        evaluation = evaluation.model_copy(
            update={
                "criteria": [
                    _backend_owned_open_answer_criterion(
                        criterion,
                        passage=passage,
                        answer=answer,
                        criterion_by_id=canonical_by_id,
                    )
                    for criterion in evaluation.criteria
                ]
            }
        )

    criterion_by_id = {criterion.id: criterion for criterion in evaluation.criteria}
    scored_ids = [str(criterion["id"]) for criterion in required] or authored_ids
    backend_score = sum(criterion_by_id[criterion_id].quality for criterion_id in scored_ids) / len(scored_ids)
    missing_criteria = [
        str(criterion["id"])
        for criterion in required
        if not criterion_by_id[str(criterion["id"])].met
        or criterion_by_id[str(criterion["id"])].quality < float(criterion.get("min_quality", 0.6))
    ]
    human_review_resolved = bool(model_failed_criterion_ids) and not set(
        missing_criteria
    ).intersection(model_failed_criterion_ids)
    blockers = [
        blocker
        for blocker in evaluation.blockers
        if blocker != "needs_human_review" or not human_review_resolved
    ]
    if (
        evaluation.needs_human_review
        and not human_review_resolved
        and "needs_human_review" not in blockers
    ):
        blockers.append("needs_human_review")
    if evaluation.language_detected.strip().lower() not in {"en", "english"}:
        blockers.append("language_mismatch")
    if evaluation.confidence < 0.65:
        blockers.append("low_evaluator_confidence")

    authored_pass_score = activity.get("pass_score")
    pass_score = (
        0.75 if authored_pass_score is None else float(authored_pass_score)
    )
    correct = not missing_criteria and not blockers and backend_score >= pass_score
    return {
        "correct": correct,
        "score": round(backend_score, 4),
        "model_score": float(evaluation.score),
        "confidence": float(evaluation.confidence),
        "criteria": [criterion.model_dump() for criterion in evaluation.criteria],
        "missing_criteria": missing_criteria,
        "misconception_tags": list(evaluation.misconception_tags),
        "blockers": list(dict.fromkeys(blockers)),
        "language_detected": evaluation.language_detected,
    }


def _backend_owned_open_answer_criterion(
    criterion: Any,
    *,
    passage: str,
    answer: str,
    criterion_by_id: dict[str, Any],
) -> Any:
    if criterion.id == "clue_supports_inference":
        inference = criterion_by_id.get("plausible_inference")
        clue = criterion_by_id.get("relevant_text_clue")
        normalized_answer = _normalize(answer)
        explicit_link = bool(
            re.search(r"\b(?:because|since|therefore|thus|so)\b", normalized_answer)
            or any(
                phrase in normalized_answer
                for phrase in (
                    "due to",
                    "this shows",
                    "this suggests",
                    "which shows",
                    "which suggests",
                )
            )
        )
        if inference and clue and inference.met and clue.met and explicit_link:
            return criterion.model_copy(
                update={
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer.strip(),
                }
            )
        return criterion
    if criterion.id == "summary_source_accuracy":
        cited_concern = _normalize(criterion.evidence_quote)
        if (
            not criterion.met
            and cited_concern
            and _concept_phrase_spans(_normalize(passage), cited_concern)
            and not _copies_source_passage(passage=passage, answer=answer)
        ):
            return criterion.model_copy(
                update={
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": criterion.evidence_quote,
                }
            )
        return criterion
    if criterion.id != "own_words":
        return criterion
    if len(_normalize(answer).split()) < 4 or len(_normalize(passage).split()) < 4:
        return criterion
    copied = _copies_source_passage(passage=passage, answer=answer)
    return criterion.model_copy(
        update={
            "met": not copied,
            "quality": 0.1 if copied else 1.0,
            "evidence_quote": answer.strip(),
        }
    )


def _copies_source_passage(*, passage: str, answer: str) -> bool:
    answer_tokens = _normalize(answer).split()
    passage_tokens = _normalize(passage).split()
    if len(answer_tokens) < 4 or len(passage_tokens) < 4:
        return False
    matcher = SequenceMatcher(
        None,
        passage_tokens,
        answer_tokens,
        autojunk=False,
    )
    longest_run = matcher.find_longest_match().size
    copied_fraction = longest_run / len(answer_tokens)
    return (
        (longest_run >= 5 and copied_fraction >= 0.7)
        or matcher.ratio() >= 0.86
    )


def decide_semantic_concept_evaluation(
    activity: dict[str, Any],
    raw_evaluation: SchoolRubricEvaluation | dict[str, Any],
    *,
    answer: str,
) -> dict[str, Any]:
    evaluator_activity = evaluator_activity_for_answer(activity, answer)
    if evaluator_activity is None:
        raise ValueError("semantic_concept_evaluation_not_required")
    result = decide_open_answer_evaluation(
        evaluator_activity,
        raw_evaluation,
        answer=answer,
    )
    criteria = list(result["criteria"])
    missing_criteria = list(result["missing_criteria"])
    blockers = list(result["blockers"])
    misconceptions = list(result["misconception_tags"])

    min_response_words = activity.get("min_response_words")
    if min_response_words is not None:
        word_count = len(_normalize(answer).split())
        minimum_met = word_count >= int(min_response_words)
        criteria.append(
            {
                "id": "response_min_words",
                "met": minimum_met,
                "quality": 1.0 if minimum_met else 0.0,
                "evidence_quote": (
                    f"{word_count} words (minimum {int(min_response_words)})"
                ),
            }
        )
        if not minimum_met:
            missing_criteria.append("response_min_words")

    cleaned_answer = _normalize(answer)
    forbidden_match = next(
        (
            phrase
            for phrase in activity.get("forbidden_phrases") or []
            if _contains_normalized_phrase(cleaned_answer, _normalize(phrase))
        ),
        None,
    )
    if forbidden_match:
        blockers.append("contradictory_response")
        misconceptions.append("explicit_contradiction")

    score = (
        sum(float(criterion["quality"]) for criterion in criteria) / len(criteria)
        if criteria
        else 0.0
    )
    blockers = list(dict.fromkeys(blockers))
    missing_criteria = list(dict.fromkeys(missing_criteria))
    return {
        **result,
        "correct": bool(result["correct"] and not missing_criteria and not blockers),
        "score": round(score, 4),
        "criteria": criteria,
        "missing_criteria": missing_criteria,
        "blockers": blockers,
        "misconception_tags": list(dict.fromkeys(misconceptions)),
    }


def _open_answer_preflight_failure(activity: dict[str, Any]) -> dict[str, Any]:
    criteria = [
        {
            "id": str(criterion["id"]),
            "met": False,
            "quality": 0.0,
            "evidence_quote": "(insufficient structured response)",
        }
        for criterion in activity.get("rubric_criteria") or []
    ]
    return {
        "correct": False,
        "score": 0.0,
        "model_score": None,
        "confidence": 1.0,
        "criteria": criteria,
        "missing_criteria": [
            str(criterion["id"])
            for criterion in activity.get("rubric_criteria") or []
            if criterion.get("required", True)
        ],
        "misconception_tags": ["open_answer_structure_incomplete"],
        "blockers": ["open_answer_preflight_failed"],
        "language_detected": "undetermined",
    }


def _matches_past_tense_travel_sentence(cleaned_answer: str) -> bool:
    words = cleaned_answer.split()
    if len(words) < 3 or "i" not in words[:2]:
        return False
    past_travel_verbs = {
        "drove",
        "flew",
        "rode",
        "took",
        "travelled",
        "traveled",
        "visited",
        "walked",
        "went",
    }
    return any(word in past_travel_verbs for word in words)


def _matches_journey_paragraph(answer: str) -> bool:
    return _matches_long_writing_structure(
        answer,
        min_words=80,
        max_words=100,
        min_sentences=4,
        min_unique_words=30,
        require_first_person=True,
    )


def _matches_story_continuation(answer: str) -> bool:
    return _matches_long_writing_structure(
        answer,
        min_words=60,
        max_words=90,
        min_sentences=3,
        min_unique_words=25,
    )


def _matches_long_writing_structure(
    answer: str,
    *,
    min_words: int,
    max_words: int,
    min_sentences: int,
    min_unique_words: int,
    require_first_person: bool = False,
) -> bool:
    words = _normalize(answer).split()
    if not min_words <= len(words) <= max_words:
        return False
    if require_first_person and "i" not in words:
        return False
    complete_sentences = [
        sentence
        for sentence in re.split(r"[.!?]+", answer)
        if len(_normalize(sentence).split()) >= 5
    ]
    return len(complete_sentences) >= min_sentences and len(set(words)) >= min_unique_words


def _matches_wise_parrot_reason(cleaned_answer: str) -> bool:
    words = set(cleaned_answer.split())
    if len(words) < 5:
        return False
    selected_parrot = bool(
        {"parrot", "parrots", "bird", "birds"}.intersection(words)
        and {"forest", "wild", "pet", "caged", "both"}.intersection(words)
    )
    reasoning = bool(
        {
            "clue",
            "clever",
            "created",
            "escape",
            "idea",
            "plan",
            "planned",
            "showed",
            "understood",
            "used",
            "wise",
        }.intersection(words)
    )
    return selected_parrot and reasoning


def _matches_release_opinion_reason(cleaned_answer: str) -> bool:
    words = set(cleaned_answer.split())
    if len(cleaned_answer.split()) < 6:
        return False
    release_action = bool(
        {"free", "freed", "release", "released", "unlock", "unlocked"}.intersection(words)
        or "open the cage" in cleaned_answer
        or "let the bird fly" in cleaned_answer
        or "let it fly" in cleaned_answer
        or "set it free" in cleaned_answer
    )
    reason_connector = bool({"because", "since"}.intersection(words)) or "so that" in cleaned_answer
    humane_reason = bool(
        {
            "belong",
            "belongs",
            "choose",
            "choice",
            "deserve",
            "deserves",
            "fair",
            "freedom",
            "habitat",
            "sky",
            "trapped",
            "unfair",
        }.intersection(words)
        or "live freely" in cleaned_answer
    )
    return release_action and reason_connector and humane_reason


def _matches_bird_feeder_procedure(cleaned_answer: str) -> bool:
    start_clean = _first_phrase_index(cleaned_answer, ("clean", "wash"))
    add_food = _first_phrase_index(cleaned_answer, ("add", "fill"), after=start_clean)
    place_safely = _first_phrase_index(
        cleaned_answer,
        ("place", "hang", "put"),
        after=add_food,
    )
    maintain = _first_phrase_index(
        cleaned_answer,
        ("clean", "wash", "replace", "refill", "change"),
        after=place_safely,
    )
    food_or_water = _first_phrase_index(
        cleaned_answer,
        ("grain", "grains", "seed", "seeds", "food", "water"),
        after=add_food - 1,
    )
    safe_location = _first_phrase_index(
        cleaned_answer,
        ("safe", "safely", "shade", "shaded", "quiet", "traffic", "ground"),
        after=place_safely - 1,
    )
    maintenance_signal = _first_phrase_index(
        cleaned_answer,
        ("regularly", "daily", "fresh", "stale", "dirty"),
        after=maintain - 1,
    )
    return (
        0 <= start_clean < add_food < place_safely < maintain
        and food_or_water >= add_food
        and safe_location >= place_safely
        and maintenance_signal >= maintain
    )


def _first_phrase_index(text: str, phrases: tuple[str, ...], *, after: int = -1) -> int:
    candidates = [
        index
        for phrase in phrases
        if (index := text.find(phrase, after + 1)) >= 0
    ]
    return min(candidates) if candidates else -1


def _evaluation_feedback_message(
    activity: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    next_step: str,
) -> str:
    base = _feedback_message(activity["kind"], bool(evaluation["correct"]), next_step)
    if activity.get("evaluation_mode") != "llm_rubric" or evaluation["correct"]:
        return base
    descriptions = {
        str(criterion["id"]): str(criterion.get("description") or "").strip()
        for criterion in activity.get("rubric_criteria") or []
    }
    missing = [
        descriptions.get(criterion_id, criterion_id.replace("_", " "))
        for criterion_id in evaluation.get("missing_criteria") or []
    ]
    if not missing:
        return base
    return f"{base} Focus next on this: {missing[0]}"


def _feedback_message(kind: str, correct: bool, next_step: str) -> str:
    if correct:
        if kind == "independent_check" and next_step == "transfer_check":
            return "Good. One more step: use the same skill in a new example."
        if kind in {"independent_check", "transfer_check"}:
            return "Good. This chapter level is complete, so the next level is ready."
        if next_step.startswith("revision_level_"):
            return "Good. Move to the next revision level."
        return "Good. Now try the same chapter skill without hints."
    if kind in {"independent_check", "transfer_check"} and next_step == "bridge":
        return "Not yet. Zidd will slow this chapter level down with a bridge check."
    if kind == "guided_check":
        return "Not yet. Zidd will slow this chapter level down with a bridge check."
    if kind == "bridge":
        return "Not yet. Zidd is opening a focused masterclass for this chapter skill."
    if kind == "masterclass":
        if next_step.startswith("revision_level_"):
            return "This needs a short revision run before trying again."
        return "Not yet. Stay in the masterclass and try one more supported check."
    return "Not yet. Stay with this revision level and try again."
