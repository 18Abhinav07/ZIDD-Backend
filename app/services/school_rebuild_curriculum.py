"""Target-class curriculum loop for the rebuilt School Prep flow."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
import hashlib
import json
import re
from difflib import SequenceMatcher
from typing import Any

from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school.source_map_compat import load_beta_source_map
from app.content.school.standards import locked_english_taxonomy
from app.content.school_rebuild_content import load_approved_live_chapters_for_class
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    RUBRIC_SCHEMA_VERSION,
    grade_typed_school_answer,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services.school.semantic_evidence import (
    authored_evidence_can_prove_criterion,
    inference_clue_is_explicitly_linked,
)
from app.services.school_rebuild_language import localized_teaching_support
from app.services.school_rebuild_profile import school_coach_identity


ENGINE_VERSION = "school-rebuild-curriculum-6"
_COMPACT_RUNTIME_SCHEMA_VERSION = "school-curriculum-runtime-v1"
_ASSESSMENT_REPAIR_ENGINE_VERSION = "school-rebuild-curriculum-2"
_SUPPORTED_PREVIOUS_ENGINE_VERSIONS = frozenset(
    {
        _ASSESSMENT_REPAIR_ENGINE_VERSION,
        "school-rebuild-curriculum-3",
        "school-rebuild-curriculum-4",
        "school-rebuild-curriculum-5",
    }
)
REVISION_STEPS = ("revision_level_1", "revision_level_2", "revision_level_3")
MAX_MASTERCLASS_INTERRUPTS_PER_LEVEL = 2
CHAPTER_ASSESSMENT_HARD_BLOCKERS = frozenset({"contradictory_response"})
_V2_SUPPORT_KINDS = (
    "bridge",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
    "revision_level_4",
)
_V2_EXHAUSTED_SUPPORT_MASTERCLASS_REASONS = frozenset(
    {
        "authored_targeted_support_unavailable",
        "authored_support_pool_exhausted",
        "authored_support_not_available_for_trigger",
        "authored_source_semantic_support_unavailable",
    }
)
# Populate only for a release that changes aliases and nothing else. The current
# Class 5 semantic-evidence release changes grading policy, so historical
# snapshots must refresh rather than be silently reinterpreted.
_SAFE_STRICT_OPEN_ALIAS_MIGRATIONS: dict[tuple[str, str, str], frozenset[str]] = {
    (
        "eng_c5_ch01",
        "2026-07-21.ch1-gold.22.semantic-evidence-v1",
        "2026-07-21.ch1-gold.24.semantic-alias-v2",
    ): frozenset(
        {
            "papas_spectacles_sound_lab:independent_application:v1",
            "papas_spectacles_sound_lab:independent_application:v2",
            "papas_spectacles_sound_lab:independent_application:v3",
            "papas_spectacles_sound_lab:independent_application:v4",
        }
    ),
    (
        "eng_c5_ch01",
        "2026-07-21.ch1-gold.23.semantic-alias-v1",
        "2026-07-21.ch1-gold.24.semantic-alias-v2",
    ): frozenset(
        {
            "papas_spectacles_sound_lab:independent_application:v1",
            "papas_spectacles_sound_lab:independent_application:v2",
            "papas_spectacles_sound_lab:independent_application:v3",
            "papas_spectacles_sound_lab:independent_application:v4",
        }
    ),
    (
        "eng_c5_ch02",
        "2026-07-15.4.semantic-evidence-v1",
        "2026-07-15.4.semantic-evidence-v2",
    ): frozenset(
        {
            "scooter_inference_and_fair_choice:independent:2",
        }
    ),
    (
        "eng_c5_ch03",
        "2026-07-15.5.semantic-evidence-v1",
        "2026-07-15.5.semantic-alias-v3",
    ): frozenset(
        {
            "rainbow_image_and_idea:independent:1",
            "rainbow_image_and_idea:review:1",
        }
    ),
    (
        "eng_c5_ch03",
        "2026-07-15.5.semantic-alias-v2",
        "2026-07-15.5.semantic-alias-v3",
    ): frozenset(
        {
            "rainbow_image_and_idea:review:1",
        }
    ),
}
_PUBLIC_FEEDBACK_OUTCOMES = frozenset(
    {
        "advanced",
        "correct",
        "needs_support",
        "paused_for_masterclass",
        "capped_support",
        "masterclass_complete",
        "masterclass_complete_advanced",
        "masterclass_abandoned",
        "continued_after_support_cap",
        "continued_after_support_cap_advanced",
        "chapter_check_answer_saved",
    }
)
_PUBLIC_FEEDBACK_TYPES = frozenset(
    {
        "instruction",
        "affirmation",
        "corrective",
        "masterclass",
        "support_limit",
        "support_resolution",
        "chapter_check_progress",
    }
)
_PUBLIC_RETRY_POLICIES = frozenset(
    {
        "advance",
        "advance_assessment_remediation",
        "advance_with_diagnostic_support",
        "advance_without_skill_evidence",
        "bridge_then_fresh_variant",
        "challenge_fallback",
        "continue_after_support_cap",
        "advance_after_exhausted_return",
        "fresh_variant",
        "fresh_variant_without_skill_evidence",
        "fresh_variant_without_auto_masterclass",
        "open_support_plan",
        "start_masterclass",
        "continue_chapter_check",
    }
)
_PUBLIC_FEEDBACK_ACTIONS = frozenset(
    {
        "answer_next_activity",
        "continue_after_support_cap",
        "start_masterclass",
        "view_chapter_result",
        "view_support_plan",
    }
)
_FEEDBACK_V2_PUBLIC_KEYS = (
    "outcome",
    "feedback_type",
    "correct",
    "scored",
    "response_excerpt",
    "what_worked",
    "criterion_gap",
    "misconception_tag",
    "next_support",
    "retry_policy",
    "allowed_next_actions",
)
_PRIVATE_FEEDBACK_VALUE_KEYS = frozenset(
    {
        "accepted_answers",
        "active_blockers",
        "answer_key",
        "blockers",
        "criterion_gap_ids",
        "criterion_id",
        "failed_hard_blocker_item_ids",
        "failed_rubric_item_ids",
        "missing_criteria",
        "model_answer",
        "recent_criterion_gaps",
        "rubric_criteria",
    }
)
_PRIVATE_FEEDBACK_SECRET_VALUE_KEYS = frozenset(
    {
        "accepted_answers",
        "answer_key",
        "model_answer",
    }
)
_PRIVATE_FEEDBACK_MARKERS = (
    "accepted_answer",
    "answer_key",
    "blocker_id",
    "criterion:",
    "model_answer",
    "private_rubric",
)
_PRIVATE_FEEDBACK_IDENTIFIER_PATTERN = re.compile(
    r"\b(?:[a-z][a-z0-9]*(?::[a-z0-9]+)+|"
    r"(?:accepted|answer|authored|blocker|criterion|model|private|rubric)"
    r"(?:_[a-z0-9]+)+)\b",
    re.IGNORECASE,
)
_LEARNER_SKILL_LABELS = {
    entry.skill_id: entry.name for entry in locked_english_taxonomy().entries
}


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
    if (
        placement_report.get("placement_status"),
        placement_report.get("unlock_state"),
    ) == ("target_ready", "target_unlocked"):
        return True
    if (
        placement_report.get("placement_status"),
        placement_report.get("unlock_state"),
    ) != ("below_target", "recap_required"):
        return False
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
    review_due_ids = set(_review_due_chapter_ids(latest_curriculum_session))
    completed_ids = [
        chapter_id
        for chapter_id in _completed_chapter_ids(latest_curriculum_session)
        if chapter_id not in review_due_ids
    ]
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
    review_due_ids = set(_review_due_chapter_ids(latest_curriculum_session))
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
                "review_due": chapter_id in review_due_ids,
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


def _memory_skill_ids(
    learning_memory: dict[str, Any] | None,
    *buckets: str,
) -> set[str]:
    return {
        str(item.get("skill_id") or "")
        for bucket in buckets
        for item in (learning_memory or {}).get(bucket) or []
        if isinstance(item, dict) and str(item.get("skill_id") or "")
    }


def _level_entry_mode(
    level: dict[str, Any],
    *,
    placement_report: dict[str, Any] | None,
    learning_memory: dict[str, Any] | None,
) -> str:
    skill_ids = {
        str(skill_id)
        for skill_id in level.get("skill_ids") or []
        if str(skill_id)
    }
    active_gap_ids = _memory_skill_ids(
        learning_memory,
        "active_gaps",
        "improving_gaps",
    )
    if skill_ids & active_gap_ids:
        return "full_cycle"
    confirmed_ids = _memory_skill_ids(
        learning_memory,
        "strong_skills",
        "mastered_skills",
    )
    return "challenge" if skill_ids and skill_ids <= confirmed_ids else "full_cycle"


def _independent_application_index(level: dict[str, Any]) -> int:
    return next(
        (
            index
            for index, step in enumerate(level.get("teaching_steps") or [])
            if step.get("phase") == "independent_application"
        ),
        0,
    )


def _authored_chapter_for_runtime_state(
    state: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the immutable chapter named by a persisted curriculum state."""

    chapter_state = state.get("chapter")
    if not isinstance(chapter_state, dict):
        return None
    chapter_id = str(chapter_state.get("chapter_id") or "")
    subject_id = str(state.get("subject_id") or "")
    try:
        class_no = int(state.get("target_class_no") or 0)
    except (TypeError, ValueError, OverflowError):
        return None
    if not chapter_id or not subject_id or class_no <= 0:
        return None
    return next(
        (
            chapter
            for chapter in _available_chapters(subject_id, class_no)
            if str(chapter.get("chapter_id") or "") == chapter_id
        ),
        None,
    )


def _runtime_overlay(
    value: dict[str, Any],
    authored: dict[str, Any],
) -> dict[str, Any] | None:
    """Split a runtime object only when its authored portion is unchanged."""

    if any(value.get(key) != authored_value for key, authored_value in authored.items()):
        return None
    return {
        key: deepcopy(runtime_value)
        for key, runtime_value in value.items()
        if key not in authored
    }


def _hydrate_compact_curriculum_state(state: dict[str, Any]) -> dict[str, Any]:
    """Rebuild immutable authored activities around a compact learner overlay.

    Curriculum sessions are version-gated. A compact state therefore hydrates
    only when the stored chapter reference still names the exact live content
    version; stale sessions stay compact and are expired by the normal route
    gate instead of being silently interpreted with changed teaching content.
    """

    reference = state.get("authored_content_reference")
    if (
        not isinstance(reference, dict)
        or reference.get("schema_version") != _COMPACT_RUNTIME_SCHEMA_VERSION
        or isinstance(state.get("levels"), list)
    ):
        return state
    chapter_state = state.get("chapter")
    if not isinstance(chapter_state, dict):
        return state
    authored = _authored_chapter_for_runtime_state(state)
    if not isinstance(authored, dict):
        return state
    chapter_id = str(chapter_state.get("chapter_id") or "")
    content_version = str(chapter_state.get("content_version") or "")
    if (
        reference.get("chapter_id") != chapter_id
        or reference.get("content_version") != content_version
        or str(authored.get("content_version") or "") != content_version
    ):
        return state
    try:
        class_no = int(state.get("target_class_no") or 0)
    except (TypeError, ValueError, OverflowError):
        return state
    if (
        reference.get("subject_id") != str(state.get("subject_id") or "")
        or reference.get("class_no") != class_no
    ):
        return state
    level_runtime_by_id = reference.get("level_runtime_by_id")
    if not isinstance(level_runtime_by_id, dict):
        return state
    authored_levels = list(authored.get("levels") or [])
    authored_level_ids = [
        str(level.get("level_id") or "")
        for level in authored_levels
        if isinstance(level, dict)
    ]
    if (
        not authored_level_ids
        or len(authored_level_ids) != len(authored_levels)
        or set(level_runtime_by_id) != set(authored_level_ids)
    ):
        return state
    levels: list[dict[str, Any]] = []
    for authored_level in authored_levels:
        level_id = str(authored_level["level_id"])
        runtime = level_runtime_by_id.get(level_id)
        if not isinstance(runtime, dict):
            return state
        levels.append({**deepcopy(authored_level), **deepcopy(runtime)})

    authored_assessment = authored.get("chapter_assessment")
    assessment_runtime = reference.get("chapter_assessment_runtime")
    if authored_assessment is None:
        if assessment_runtime is not None:
            return state
        chapter_assessment = None
    elif not isinstance(authored_assessment, dict) or not isinstance(
        assessment_runtime, dict
    ):
        return state
    else:
        chapter_assessment = {
            **_new_chapter_assessment_state(authored_assessment),
            **deepcopy(assessment_runtime),
        }

    hydrated = dict(state)
    hydrated.pop("authored_content_reference", None)
    hydrated["levels"] = levels
    hydrated["chapter_assessment"] = chapter_assessment
    return hydrated


def compact_curriculum_state(state: dict[str, Any]) -> dict[str, Any]:
    """Persist only mutable curriculum state for a current active lesson.

    The original implementation stored the complete chapter activity and
    assessment banks in every learner row. That is correct but needlessly
    sends hundreds of KB across Supabase for each answer. This codec keeps the
    learner-specific overlay and rehydrates it from the immutable, versioned
    authored chapter on the next request.
    """

    if (
        str(state.get("status") or "active") != "active"
        or str(state.get("phase") or "learning") != "learning"
    ):
        return deepcopy(state)
    if (
        isinstance(state.get("authored_content_reference"), dict)
        and not isinstance(state.get("levels"), list)
    ):
        return deepcopy(state)
    chapter_state = state.get("chapter")
    levels = state.get("levels")
    if not isinstance(chapter_state, dict) or not isinstance(levels, list):
        return deepcopy(state)
    authored = _authored_chapter_for_runtime_state(state)
    if not isinstance(authored, dict):
        return deepcopy(state)
    content_version = str(chapter_state.get("content_version") or "")
    if not content_version or content_version != str(authored.get("content_version") or ""):
        return deepcopy(state)
    authored_levels = list(authored.get("levels") or [])
    if len(levels) != len(authored_levels):
        return deepcopy(state)
    runtime_by_id: dict[str, dict[str, Any]] = {}
    for level, authored_level in zip(levels, authored_levels, strict=True):
        if not isinstance(level, dict) or not isinstance(authored_level, dict):
            return deepcopy(state)
        level_id = str(level.get("level_id") or "")
        if not level_id or level_id != str(authored_level.get("level_id") or ""):
            return deepcopy(state)
        runtime = _runtime_overlay(level, authored_level)
        if runtime is None or level_id in runtime_by_id:
            return deepcopy(state)
        runtime_by_id[level_id] = runtime

    authored_assessment = authored.get("chapter_assessment")
    current_assessment = state.get("chapter_assessment")
    if authored_assessment is None:
        if current_assessment is not None:
            return deepcopy(state)
        assessment_runtime = None
    elif not isinstance(authored_assessment, dict) or not isinstance(
        current_assessment, dict
    ):
        return deepcopy(state)
    else:
        assessment_runtime = _runtime_overlay(current_assessment, authored_assessment)
        if assessment_runtime is None:
            return deepcopy(state)

    compact = {
        key: deepcopy(value)
        for key, value in state.items()
        if key not in {"levels", "chapter_assessment", "authored_content_reference"}
    }
    compact["authored_content_reference"] = {
        "schema_version": _COMPACT_RUNTIME_SCHEMA_VERSION,
        "chapter_id": str(chapter_state.get("chapter_id") or ""),
        "subject_id": str(state.get("subject_id") or ""),
        "class_no": int(state.get("target_class_no") or 0),
        "content_version": content_version,
        "level_runtime_by_id": runtime_by_id,
        "chapter_assessment_runtime": assessment_runtime,
    }
    return compact


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
    # A session owns its mutable teaching state. Authored catalog objects remain
    # immutable for later learners and for compatibility reconciliation.
    chapter = deepcopy(chapter)
    levels = []
    for index, level in enumerate(chapter["levels"]):
        uses_v2 = bool(level.get("teaching_steps"))
        entry_mode = _level_entry_mode(
            level,
            placement_report=placement_report,
            learning_memory=learning_memory,
        )
        start_step_index = (
            _independent_application_index(level)
            if uses_v2 and entry_mode == "challenge"
            else 0
        )
        levels.append({
            **level,
            "status": "in_progress" if index == 0 else "not_started",
            "current_step": (
                str(level["teaching_steps"][start_step_index]["phase"])
                if uses_v2
                else "guided_check"
            ),
            "entry_mode": entry_mode,
            "attempts": [],
            "v2_step_index": start_step_index,
            "v2_support_mode": None,
            "used_variant_ids": [],
        })
    prior_memory_tags = _prior_memory_targeting_tags(learning_memory, chapter)
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
        "feedback_v2": None,
        "hot_session_memory": {
            "revision": 1,
            "recent_outcomes": [],
            "skill_streaks": {},
            "used_variant_ids": [],
            "served_activity_ids": [],
            "passage_fingerprints": [],
            "prompt_fingerprints": [],
            "recent_evidence_ids": [],
            "recent_criterion_gaps": [],
            "support_history": [],
            "unresolved_misconception_tags": prior_memory_tags,
            "active_support_count": 0,
            "last_activity_id": None,
            "last_response_language": None,
            "unresolved_outcome_id": None,
            "next_instructional_action": None,
        },
        "active_interrupt": None,
        "interrupt_history": [],
        "interrupt_counts": {},
    })


def public_curriculum_response(session_row: dict[str, Any]) -> dict[str, Any]:
    state = normalize_curriculum_state(dict(session_row.get("state_json") or {}))
    private_feedback_tokens = _private_feedback_tokens(state)
    private_feedback_secret_tokens = _feedback_secret_tokens_for_last_activity(state)
    public_feedback = _public_feedback_v2(
        state.get("feedback_v2"),
        public_digest=state.get("feedback_v2_public_digest"),
        private_tokens=private_feedback_secret_tokens,
    )
    status = state.get("status") or session_row.get("status")
    subject_id = state.get("subject_id") or session_row.get("subject_id")
    target_class_no = int(state.get("target_class_no") or session_row.get("class_no") or 0)
    completed_chapter_ids = _completed_chapter_ids({
        **session_row,
        "state_json": state,
        "status": status,
    })
    review_due_chapter_ids = _review_due_chapter_ids({
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
        "review_due_chapter_ids": review_due_chapter_ids,
        "next_available_chapter": next_available_chapter,
        "carry_forward_focuses": list(state.get("carry_forward_focuses") or []),
        "memory_summary": _public_memory_summary(state.get("learner_memory")),
        "progress": _progress(state),
        "chapter_assessment": _public_chapter_assessment_progress(state),
        "levels": [_public_level(level) for level in state.get("levels") or []],
        "current_activity": _public_activity(
            _current_activity(state),
            chapter=state.get("chapter") or {},
        ),
        "last_feedback": _public_last_feedback(
            state.get("last_feedback"),
            public_feedback=public_feedback,
            private_tokens=private_feedback_tokens,
        ),
        "feedback_v2": public_feedback,
        "session_memory": _public_hot_session_memory(
            state.get("hot_session_memory")
        ),
        "active_interrupt": _public_interrupt(state.get("active_interrupt")),
        "interrupt_history": _public_interrupt_history(
            state.get("interrupt_history") or []
        ),
        "support_required": _public_support_required(
            state.get("support_required")
        ),
        "next_action": _public_curriculum_next_action(
            state,
            session_id=str(session_row["session_id"]),
        ),
    }


def _feedback_v2_public_digest(value: dict[str, Any]) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _set_feedback_v2(state: dict[str, Any], value: dict[str, Any]) -> None:
    state["feedback_v2"] = value
    state["feedback_v2_public_digest"] = _feedback_v2_public_digest(value)


def _feedback_v2_has_public_shape(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != set(_FEEDBACK_V2_PUBLIC_KEYS):
        return False
    if not isinstance(value["outcome"], str) or value["outcome"] not in (
        _PUBLIC_FEEDBACK_OUTCOMES
    ):
        return False
    if not isinstance(value["feedback_type"], str) or value["feedback_type"] not in (
        _PUBLIC_FEEDBACK_TYPES
    ):
        return False
    if value["correct"] is not None and not isinstance(value["correct"], bool):
        return False
    if not isinstance(value["scored"], bool) or value["response_excerpt"] != "":
        return False
    if not isinstance(value["what_worked"], str):
        return False
    if value["criterion_gap"] is not None and not isinstance(
        value["criterion_gap"], str
    ):
        return False
    if value["misconception_tag"] is not None and not isinstance(
        value["misconception_tag"], str
    ):
        return False
    if not isinstance(value["next_support"], str):
        return False
    if not isinstance(value["retry_policy"], str) or value["retry_policy"] not in (
        _PUBLIC_RETRY_POLICIES
    ):
        return False
    return isinstance(value["allowed_next_actions"], list) and all(
        isinstance(action, str) and action in _PUBLIC_FEEDBACK_ACTIONS
        for action in value["allowed_next_actions"]
    )


def _feedback_v2_is_trusted(value: Any, *, public_digest: Any) -> bool:
    return (
        _feedback_v2_has_public_shape(value)
        and _feedback_v2_has_safe_text(value)
        and str(public_digest or "") == _feedback_v2_public_digest(value)
    )


def _safe_feedback_v2_fallback() -> dict[str, Any]:
    return {
        "outcome": None,
        "feedback_type": None,
        "correct": None,
        "scored": False,
        "response_excerpt": "",
        "what_worked": "This learning step needs another visible clue.",
        "criterion_gap": "Use the visible prompt to choose one next move.",
        "misconception_tag": None,
        "next_support": "Continue with the next visible learning step.",
        "retry_policy": None,
        "allowed_next_actions": [],
    }


def _safe_signed_feedback_v2_fallback(value: dict[str, Any]) -> dict[str, Any]:
    """Retain a signed feedback result when only its old free text is unsafe."""

    correct = value["correct"]
    if correct is True:
        what_worked = "You completed this learning step."
        criterion_gap = None
    elif bool(value["scored"]):
        what_worked = "Your answer is saved."
        criterion_gap = (
            "Complete each part of the visible task, then try the next example."
        )
    else:
        what_worked = "You reviewed this learning step."
        criterion_gap = "Continue with the next visible learning step."
    return {
        "outcome": value["outcome"],
        "feedback_type": value["feedback_type"],
        "correct": correct,
        "scored": value["scored"],
        "response_excerpt": "",
        "what_worked": what_worked,
        "criterion_gap": criterion_gap,
        "misconception_tag": None,
        "next_support": "Continue with the next visible learning step.",
        "retry_policy": value["retry_policy"],
        "allowed_next_actions": list(value["allowed_next_actions"]),
    }


def _private_feedback_tokens(state: dict[str, Any]) -> set[str]:
    return _feedback_tokens_for_keys(state, value_keys=_PRIVATE_FEEDBACK_VALUE_KEYS)


def _private_feedback_secret_tokens(state: dict[str, Any]) -> set[str]:
    return _feedback_tokens_for_keys(
        state,
        value_keys=_PRIVATE_FEEDBACK_SECRET_VALUE_KEYS,
    )


def _feedback_secret_tokens_for_last_activity(state: dict[str, Any]) -> set[str]:
    """Use answer keys from the answered activity, not every future lesson.

    Global answer-key matching makes ordinary explanatory words unsafe when a
    different future activity happens to use that word as its answer. Legacy
    and non-v2 feedback still use the conservative global fallback.
    """

    last_feedback = state.get("last_feedback")
    activity_id = (
        str(last_feedback.get("activity_id") or "")
        if isinstance(last_feedback, dict)
        else ""
    )
    if not activity_id:
        return _private_feedback_secret_tokens(state)
    for level in state.get("levels") or []:
        if not isinstance(level, dict):
            continue
        level_id = str(level.get("level_id") or "")
        for step in level.get("teaching_steps") or []:
            if not isinstance(step, dict):
                continue
            step_id = str(step.get("step_id") or "")
            candidates = []
            if isinstance(step.get("activity"), dict):
                candidates.append(step["activity"])
            candidates.extend(
                item
                for item in step.get("variant_pool") or []
                if isinstance(item, dict)
            )
            for authored in candidates:
                variant_id = str(
                    authored.get("variant_id") or f"{step_id}:single"
                )
                if activity_id.startswith(
                    f"{level_id}:{step_id}:{variant_id}:"
                ):
                    return _feedback_tokens_for_keys(
                        authored,
                        value_keys=_PRIVATE_FEEDBACK_SECRET_VALUE_KEYS,
                    )
    return _private_feedback_secret_tokens(state)


def _feedback_tokens_for_keys(
    state: dict[str, Any],
    *,
    value_keys: frozenset[str],
) -> set[str]:
    tokens: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, str):
            cleaned = value.strip().casefold()
            if len(cleaned) >= 4:
                tokens.add(cleaned)
                public_form = cleaned.removeprefix("criterion:").replace("_", " ")
                if len(public_form) >= 4:
                    tokens.add(public_form)
            return
        if isinstance(value, dict):
            for item in value.values():
                collect(item)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                collect(item)

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key) in value_keys:
                    collect(item)
                if isinstance(item, str) and item.casefold().startswith("criterion:"):
                    collect(item)
                visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                visit(item)

    visit(state)
    return tokens


def _contains_private_feedback_detail(
    value: Any,
    *,
    private_tokens: set[str],
) -> bool:
    text = str(value or "").strip().casefold()
    if not text:
        return False
    if any(marker in text for marker in _PRIVATE_FEEDBACK_MARKERS):
        return True
    return any(
        re.search(
            rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])",
            text,
        )
        for token in private_tokens
        if token
    )


def _feedback_v2_has_safe_text(
    value: dict[str, Any],
    *,
    private_tokens: set[str] | None = None,
) -> bool:
    private_tokens = private_tokens or set()
    for field in ("what_worked", "criterion_gap", "next_support"):
        text = str(value.get(field) or "")
        if _contains_private_feedback_detail(
            text,
            private_tokens=private_tokens,
        ) or _PRIVATE_FEEDBACK_IDENTIFIER_PATTERN.search(text):
            return False
    return True


def _public_feedback_v2(
    value: Any,
    *,
    public_digest: Any = None,
    private_tokens: set[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    signed_public_feedback = _feedback_v2_has_public_shape(value) and (
        str(public_digest or "") == _feedback_v2_public_digest(value)
    )
    if not signed_public_feedback:
        return _safe_feedback_v2_fallback()
    if not _feedback_v2_has_safe_text(
        value,
        private_tokens=private_tokens,
    ):
        return _safe_signed_feedback_v2_fallback(value)
    return {
        "outcome": value["outcome"],
        "feedback_type": value["feedback_type"],
        "correct": value["correct"],
        "scored": value["scored"],
        "response_excerpt": "",
        "what_worked": value["what_worked"],
        "criterion_gap": value["criterion_gap"],
        "misconception_tag": None,
        "next_support": value["next_support"],
        "retry_policy": value["retry_policy"],
        "allowed_next_actions": list(value["allowed_next_actions"]),
    }


def _public_last_feedback(
    value: Any,
    *,
    public_feedback: dict[str, Any] | None,
    private_tokens: set[str] | None = None,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if public_feedback is not None:
        message = " ".join(
            part
            for part in (
                str(public_feedback.get("what_worked") or ""),
                str(public_feedback.get("criterion_gap") or ""),
            )
            if part
        )
    else:
        message = str(value.get("message") or "")
        if _contains_private_feedback_detail(
            message,
            private_tokens=private_tokens or set(),
        ):
            message = "Your latest learning step is saved."
    return {
        "activity_id": value.get("activity_id"),
        "level_id": value.get("level_id"),
        "kind": value.get("kind"),
        "correct": value.get("correct"),
        "message": message or "Your latest learning step is saved.",
    }


def current_curriculum_activity_id(state: Any) -> str | None:
    if not isinstance(state, dict) or state.get("status") == "complete":
        return None
    try:
        state, _repair = reconcile_curriculum_state(state)
    except (TypeError, ValueError):
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
    if level.get("teaching_steps"):
        activity = _current_activity(state)
        return str(activity.get("activity_id") or "") if activity else None
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
    consumed_variant_ids: Iterable[str] = (),
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
    is_v2_interrupt = str(interrupt.get("runtime_contract") or "") == "v2"
    attached_session_id = str(interrupt.get("masterclass_session_id") or "")
    if is_v2_interrupt and not attached_session_id:
        raise ValueError("masterclass_session_not_attached")
    if is_v2_interrupt and attached_session_id != masterclass_session_id:
        raise ValueError("masterclass_session_mismatch")
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
    advanced_past_exhausted_return = False
    if is_v2_interrupt:
        return_step_index = int(interrupt.get("return_step_index") or 0)
        teaching_steps = list(level.get("teaching_steps") or [])
        if return_step_index < 0 or return_step_index >= len(teaching_steps):
            raise ValueError("masterclass_return_step_not_found")
        level["v2_step_index"] = return_step_index
        level["v2_support_mode"] = None
        level["current_step"] = str(teaching_steps[return_step_index].get("phase") or "")
        level["v2_trigger_activity_id"] = interrupt.get("trigger_activity_id")
        level["v2_return_activity_id"] = interrupt.get("return_activity_id")
        level["v2_trigger_skill_ids"] = list(interrupt.get("skill_ids") or [])
        level["v2_last_interrupt_id"] = interrupt.get("interrupt_id")
        level["v2_last_masterclass_session_id"] = attached_session_id
        authored_variant_ids = {
            str(variant.get("variant_id") or "")
            for step in teaching_steps
            if isinstance(step, dict)
            for variant in step.get("variant_pool") or []
            if isinstance(variant, dict) and variant.get("variant_id")
        }
        used_variant_ids = list(level.get("used_variant_ids") or [])
        for candidate in consumed_variant_ids:
            variant_id = str(candidate or "")
            if (
                variant_id in authored_variant_ids
                and variant_id not in used_variant_ids
            ):
                used_variant_ids.append(variant_id)
        level["used_variant_ids"] = used_variant_ids
    else:
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
    if is_v2_interrupt and resolution == "complete":
        return_step = _v2_step(level)
        authored_return = (
            _v2_step_activity(normalized, level, return_step)[0]
            if return_step is not None
            else None
        )
        if authored_return is None:
            normalized, levels, level = _advance_v2_step(
                normalized,
                levels=list(normalized.get("levels") or []),
                level=level,
                level_index=level_index,
            )
            normalized["levels"] = levels
            advanced_past_exhausted_return = True
    normalized["last_feedback"] = {
        "activity_id": str(interrupt.get("interrupt_id") or ""),
        "level_id": level_id,
        "kind": "masterclass",
        "correct": True if resolution == "complete" else None,
        "message": (
            (
                "Focused practice complete. Every saved-step example was already "
                "used, so continue to the next authored lesson step."
            )
            if advanced_past_exhausted_return
            else "Focused practice complete. Return to the same lesson step you paused."
            if resolution == "complete"
            else "Focused practice was left unfinished. Return to the same lesson step when you are ready."
        ),
    }
    if is_v2_interrupt:
        _set_feedback_v2(normalized, {
            "outcome": (
                (
                    "masterclass_complete_advanced"
                    if advanced_past_exhausted_return
                    else "masterclass_complete"
                )
                if resolution == "complete"
                else "masterclass_abandoned"
            ),
            "feedback_type": "support_resolution",
            "correct": True if resolution == "complete" else None,
            "scored": False,
            "what_worked": (
                "The focused support session was completed."
                if resolution == "complete"
                else "The unfinished support session was recorded without awarding credit."
            ),
            "criterion_gap": None,
            "misconception_tag": None,
            "next_support": (
                "Continue to the next authored lesson step; the completed "
                "masterclass supplied the independent return evidence."
                if advanced_past_exhausted_return
                else "Return to the exact lesson phase with a fresh authored example."
            ),
            "retry_policy": (
                "advance_after_exhausted_return"
                if advanced_past_exhausted_return
                else "fresh_variant"
            ),
            "allowed_next_actions": ["answer_next_activity"],
            "response_excerpt": "",
        })
    return normalize_curriculum_state(normalized)


def recover_completed_masterclass_replay(
    state: dict[str, Any],
    *,
    masterclass_session_id: str,
) -> dict[str, Any] | None:
    """Repair a pre-fix resume that committed before its response rendered."""

    normalized = normalize_curriculum_state(state)
    if (
        normalized.get("status") != "active"
        or normalized.get("phase") != "learning"
        or normalized.get("active_interrupt") is not None
    ):
        return None
    history = list(normalized.get("interrupt_history") or [])
    last_resolution = history[-1] if history else None
    if (
        not isinstance(last_resolution, dict)
        or last_resolution.get("resolution") != "complete"
        or str(last_resolution.get("masterclass_session_id") or "")
        != masterclass_session_id
        or str(last_resolution.get("runtime_contract") or "") != "v2"
    ):
        return None
    levels = list(normalized.get("levels") or [])
    level_index = int(normalized.get("current_level_index") or 0)
    if level_index < 0 or level_index >= len(levels):
        return None
    level = dict(levels[level_index])
    if (
        str(level.get("level_id") or "")
        != str(last_resolution.get("level_id") or "")
        or str(level.get("v2_last_masterclass_session_id") or "")
        != masterclass_session_id
    ):
        return None
    return_step = _v2_step(level)
    if return_step is None:
        return None
    authored_return, _variant_id, _fresh = _v2_step_activity(
        normalized,
        level,
        return_step,
    )
    if authored_return is not None:
        return None

    levels[level_index] = level
    normalized, levels, _level = _advance_v2_step(
        normalized,
        levels=levels,
        level=level,
        level_index=level_index,
    )
    normalized["levels"] = levels
    normalized["last_feedback"] = {
        "activity_id": str(last_resolution.get("interrupt_id") or ""),
        "level_id": str(last_resolution.get("level_id") or ""),
        "kind": "masterclass",
        "correct": True,
        "message": (
            "Focused practice complete. Every saved-step example was already "
            "used, so continue to the next authored lesson step."
        ),
    }
    _set_feedback_v2(normalized, {
        "outcome": "masterclass_complete_advanced",
        "feedback_type": "support_resolution",
        "correct": True,
        "scored": False,
        "what_worked": "The focused support session was completed.",
        "criterion_gap": None,
        "misconception_tag": None,
        "next_support": (
            "Continue to the next authored lesson step; the completed "
            "masterclass supplied the independent return evidence."
        ),
        "retry_policy": "advance_after_exhausted_return",
        "allowed_next_actions": ["answer_next_activity"],
        "response_excerpt": "",
    })
    return normalize_curriculum_state(normalized)


def continue_after_support_cap(state: dict[str, Any]) -> dict[str, Any]:
    """Resume the preserved V2 phase without certifying or clearing the cap."""

    normalized = normalize_curriculum_state(state)
    if (
        normalized.get("status") != "active"
        or normalized.get("phase") != "capped_support"
        or normalized.get("active_interrupt") is not None
    ):
        raise ValueError("curriculum_not_capped_for_support")
    levels = list(normalized.get("levels") or [])
    level_index = int(normalized.get("current_level_index") or 0)
    if level_index < 0 or level_index >= len(levels):
        raise ValueError("capped_support_level_not_found")
    level = dict(levels[level_index])
    blockers = list(level.get("active_blockers") or [])
    if (
        not level.get("teaching_steps")
        or "masterclass_cap_exceeded" not in blockers
    ):
        raise ValueError("curriculum_not_capped_for_support")
    step = _v2_step(level)
    if step is None:
        raise ValueError("capped_support_return_step_not_found")

    level["status"] = "in_progress"
    level["current_step"] = str(step.get("phase") or "")
    level["v2_support_mode"] = None
    level["v2_auto_masterclass_disabled"] = True
    level["v2_support_cap_acknowledged_count"] = (
        int(level.get("v2_support_cap_acknowledged_count") or 0) + 1
    )
    levels[level_index] = level
    normalized["levels"] = levels
    normalized["status"] = "active"
    normalized["phase"] = "learning"
    normalized["active_interrupt"] = None
    advanced_past_exhausted_return = False
    if _v2_step_activity(normalized, level, step)[0] is None:
        try:
            normalized, levels, level = _advance_v2_step(
                normalized,
                levels=levels,
                level=level,
                level_index=level_index,
            )
        except ValueError as exc:
            if str(exc) == "chapter_assessment_required_for_v2":
                raise ValueError(
                    "capped_support_return_activity_unavailable"
                ) from exc
            raise
        normalized["levels"] = levels
        advanced_past_exhausted_return = True
    support_required = dict(normalized.get("support_required") or {})
    support_required.update(
        reason="masterclass_cap_exceeded",
        level_id=str(level.get("level_id") or ""),
        skill_ids=list(level.get("v2_trigger_skill_ids") or []),
        auto_masterclass_disabled=True,
        continuation_status="continued_with_warning",
    )
    normalized["support_required"] = support_required
    memory = _normalize_hot_session_memory(normalized.get("hot_session_memory"))
    memory["revision"] += 1
    memory["next_instructional_action"] = "answer_next_activity"
    normalized["hot_session_memory"] = memory
    _set_feedback_v2(normalized, {
        "outcome": (
            "continued_after_support_cap_advanced"
            if advanced_past_exhausted_return
            else "continued_after_support_cap"
        ),
        "feedback_type": "support_limit",
        "correct": None,
        "scored": False,
        "what_worked": "You chose to continue the lesson with the support limit recorded.",
        "criterion_gap": None,
        "misconception_tag": "masterclass_cap_exceeded",
        "next_support": (
            "Continue to the next authored lesson step; the exhausted return "
            "activity will not be repeated."
            if advanced_past_exhausted_return
            else "Try a fresh authored example in the same lesson phase."
        ),
        "retry_policy": (
            "advance_after_exhausted_return"
            if advanced_past_exhausted_return
            else "fresh_variant_without_auto_masterclass"
        ),
        "allowed_next_actions": ["answer_next_activity"],
        "response_excerpt": "",
    })
    normalized["last_feedback"] = {
        "activity_id": str(level.get("v2_return_activity_id") or ""),
        "level_id": str(level.get("level_id") or ""),
        "kind": "capped_support_continuation",
        "correct": None,
        "message": (
            "Continue at the next authored lesson step; the exhausted return "
            "activity will not be repeated."
            if advanced_past_exhausted_return
            else "Continue at the same lesson phase with a fresh example."
        ),
    }
    resumed = normalize_curriculum_state(normalized)
    try:
        current_activity = _current_activity(resumed)
    except ValueError as exc:
        if str(exc) in {
            "authored_activity_variant_unavailable",
            "authored_variant_pool_exhausted",
        }:
            raise ValueError(
                "capped_support_return_activity_unavailable"
            ) from exc
        raise
    if current_activity is None:
        raise ValueError("capped_support_return_activity_unavailable")
    return resumed


def attach_masterclass_session(
    state: dict[str, Any],
    *,
    masterclass_session_id: str,
) -> dict[str, Any]:
    normalized = normalize_curriculum_state(state)
    interrupt = normalized.get("active_interrupt")
    if (
        normalized.get("status") != "paused_for_masterclass"
        or normalized.get("phase") != "paused_for_masterclass"
        or not isinstance(interrupt, dict)
    ):
        raise ValueError("curriculum_not_paused_for_masterclass")
    existing = str(interrupt.get("masterclass_session_id") or "")
    if existing and existing != masterclass_session_id:
        raise ValueError("masterclass_session_conflict")
    normalized["active_interrupt"] = {
        **interrupt,
        "masterclass_session_id": masterclass_session_id,
    }
    return normalize_curriculum_state(normalized)


def _reconstruct_v2_trigger_relevance_terms(level: dict[str, Any]) -> list[str]:
    """Recover authored semantic anchors for pre-anchor support sessions."""

    stored_terms = [
        str(term).strip()
        for term in level.get("v2_trigger_relevance_terms") or []
        if str(term).strip()
    ]
    if stored_terms:
        return list(dict.fromkeys(stored_terms))
    trigger_activity_id = str(level.get("v2_trigger_activity_id") or "")
    if not trigger_activity_id:
        return []
    trigger_variant_id = next(
        (
            str(attempt.get("variant_id") or "")
            for attempt in level.get("attempts") or []
            if str(attempt.get("activity_id") or "") == trigger_activity_id
            and str(attempt.get("variant_id") or "")
        ),
        "",
    )
    for step in level.get("teaching_steps") or []:
        if not isinstance(step, dict):
            continue
        authored_candidates = []
        if isinstance(step.get("activity"), dict):
            authored_candidates.append(dict(step["activity"]))
        authored_candidates.extend(
            dict(item)
            for item in step.get("variant_pool") or []
            if isinstance(item, dict)
        )
        for authored in authored_candidates:
            variant_id = str(
                authored.get("variant_id")
                or f"{step.get('step_id') or ''}:single"
            )
            if variant_id != trigger_variant_id and (
                not variant_id or f":{variant_id}:" not in trigger_activity_id
            ):
                continue
            return list(
                dict.fromkeys(
                    str(term).strip()
                    for term in authored.get("relevance_terms") or []
                    if str(term).strip()
                )
            )
    return []


def normalize_curriculum_state(state: dict[str, Any]) -> dict[str, Any]:
    state = _hydrate_compact_curriculum_state(state)
    levels = []
    learner_memory = (
        dict(state.get("learner_memory") or {})
        if isinstance(state.get("learner_memory"), dict)
        else {}
    )
    for index, level in enumerate(state.get("levels") or []):
        normalized = dict(level)
        normalized.setdefault("status", "in_progress" if index == int(state.get("current_level_index") or 0) else "not_started")
        normalized.setdefault("current_step", "guided_check")
        normalized["attempts"] = [
            _sanitize_persisted_attempt(attempt)
            for attempt in normalized.get("attempts") or []
            if isinstance(attempt, dict)
        ]
        normalized.setdefault("v2_step_index", 0)
        normalized.setdefault("v2_support_mode", None)
        normalized.setdefault("entry_mode", "full_cycle")
        # Target-ready placement unlocks a class; it cannot certify the work
        # inside a chapter the learner has not encountered. Older session
        # snapshots created challenge entries from that broad verdict. Restore
        # untouched levels unless matching durable skill evidence still earns
        # the shorter path.
        if (
            normalized.get("status") != "complete"
            and normalized.get("entry_mode") == "challenge"
            and not normalized["attempts"]
            and normalized.get("teaching_steps")
            and _level_entry_mode(
                normalized,
                placement_report=None,
                learning_memory=learner_memory,
            )
            != "challenge"
        ):
            first_step = (normalized.get("teaching_steps") or [{}])[0]
            normalized["entry_mode"] = "full_cycle"
            normalized["v2_step_index"] = 0
            normalized["current_step"] = str(
                first_step.get("phase") if isinstance(first_step, dict) else "connect"
            ) or "connect"
            normalized["v2_support_mode"] = None
        normalized.setdefault("used_variant_ids", [])
        normalized.setdefault("v2_trigger_activity_id", None)
        normalized.setdefault("v2_return_activity_id", None)
        normalized.setdefault("v2_trigger_skill_ids", [])
        normalized.setdefault("v2_active_misconception_tags", [])
        normalized["v2_trigger_relevance_terms"] = (
            _reconstruct_v2_trigger_relevance_terms(normalized)
        )
        active_tags = {
            str(tag) for tag in normalized.get("v2_active_misconception_tags") or []
        }
        forced_support_kind = str(normalized.get("v2_forced_support_kind") or "")
        forced_tags = {
            str(tag)
            for tag in (
                (normalized.get("checks") or {}).get(forced_support_kind) or {}
            ).get("target_misconception_tags")
            or []
        }
        if forced_support_kind and active_tags and not active_tags.intersection(
            forced_tags
        ):
            normalized.pop("v2_forced_support_kind", None)
        normalized.setdefault("v2_auto_masterclass_disabled", False)
        normalized.setdefault("v2_support_cap_acknowledged_count", 0)
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
    feedback_v2 = state.get("feedback_v2")
    feedback_v2_public_digest = state.get("feedback_v2_public_digest")
    feedback_v2_is_trusted = _feedback_v2_is_trusted(
        feedback_v2,
        public_digest=feedback_v2_public_digest,
    )
    normalized_state = {
        **state,
        "engine_version": state.get("engine_version") or ENGINE_VERSION,
        "status": status,
        "phase": phase,
        "current_level_index": current_index,
        "levels": levels,
        "last_feedback": state.get("last_feedback"),
        "feedback_v2": _sanitize_feedback_v2(
            feedback_v2,
            public_digest=feedback_v2_public_digest,
        ),
        "feedback_v2_public_digest": (
            feedback_v2_public_digest if feedback_v2_is_trusted else None
        ),
        "chapter_assessment": _sanitize_chapter_assessment(
            state.get("chapter_assessment")
        ),
        "hot_session_memory": _normalize_hot_session_memory(
            state.get("hot_session_memory")
        ),
        "active_interrupt": state.get("active_interrupt"),
        "interrupt_history": list(state.get("interrupt_history") or []),
        "interrupt_counts": dict(state.get("interrupt_counts") or {}),
    }
    normalized_state["hot_session_memory"] = _reconstruct_hot_session_fingerprints(
        normalized_state,
        normalized_state["hot_session_memory"],
    )
    return _ensure_assessment_support_contract(
        _ensure_v2_support_availability_contract(normalized_state)
    )


def reconcile_curriculum_state(
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Upgrade persisted state and repair only deterministic historical false negatives."""

    previous_version = str(state.get("engine_version") or "")
    pre_normalized = state
    if previous_version == "school-rebuild-curriculum-5":
        pre_normalized = _reconcile_v5_source_semantic_support_contract(state)
    normalized = normalize_curriculum_state(pre_normalized)
    support_repair = _v2_exhausted_support_masterclass_repair(
        pre_normalized,
        normalized,
    )
    # A session owns its lesson snapshot so ordinary authored changes are
    # intentionally version-gated. The sole exception is an audited expansion
    # of literal aliases on an otherwise identical strict-open evaluator. It
    # can only make an already-authored claim easier to phrase; it cannot add a
    # criterion, remove a contradiction guard, or change learner-facing work.
    # This lets a false-negative correction reach an in-flight learner without
    # silently converting normal content-version expiry into a live migration.
    normalized, alias_repair = _reconcile_safe_evaluator_alias_expansions(
        normalized
    )
    if previous_version == ENGINE_VERSION:
        return normalized, alias_repair or support_repair

    updated = dict(normalized)
    repair = None
    if previous_version == _ASSESSMENT_REPAIR_ENGINE_VERSION:
        # Historical repair needs the original answer and evaluator evidence.
        # normalize_curriculum_state deliberately strips those private fields
        # before public persistence, so running the repair against `updated`
        # would make a legitimate deterministic correction impossible.
        repaired_state, repair = _reconcile_v2_chapter_assessment(pre_normalized)
        if repair:
            updated = repaired_state
    elif previous_version not in _SUPPORTED_PREVIOUS_ENGINE_VERSIONS:
        return normalized, alias_repair or support_repair
    updated["engine_version"] = ENGINE_VERSION
    updated = normalize_curriculum_state(updated)
    return updated, (
        repair
        or alias_repair
        or _v2_exhausted_support_masterclass_repair(
            pre_normalized,
            updated,
        )
    )


def _safe_strict_open_alias_expansion(
    persisted_activity: dict[str, Any],
    authored_activity: dict[str, Any],
) -> dict[str, Any] | None:
    """Return a safe alias-only evaluator update, or reject the migration.

    Content versions are a hard session boundary. This predicate deliberately
    permits only an additive correction to ``concept_slots[].any_of`` on an
    otherwise byte-equivalent strict-open activity. In particular, a changed
    prompt, rubric, validator, forbidden phrase, or slot definition makes the
    activity ineligible and leaves normal content-version expiry in force.
    """

    if (
        persisted_activity.get("grading_mode") != "strict_open_rubric"
        or authored_activity.get("grading_mode") != "strict_open_rubric"
    ):
        return None
    persisted_slots = persisted_activity.get("concept_slots")
    authored_slots = authored_activity.get("concept_slots")
    if not isinstance(persisted_slots, list) or not isinstance(authored_slots, list):
        return None

    persisted_without_slots = {
        key: value
        for key, value in persisted_activity.items()
        if key != "concept_slots"
    }
    authored_without_slots = {
        key: value
        for key, value in authored_activity.items()
        if key != "concept_slots"
    }
    if persisted_without_slots != authored_without_slots:
        return None

    authored_by_id = {
        str(slot.get("id") or ""): slot
        for slot in authored_slots
        if isinstance(slot, dict) and str(slot.get("id") or "")
    }
    if len(authored_by_id) != len(authored_slots):
        return None

    updated_slots: list[dict[str, Any]] = []
    changed = False
    seen_ids: set[str] = set()
    for persisted_slot in persisted_slots:
        if not isinstance(persisted_slot, dict):
            return None
        slot_id = str(persisted_slot.get("id") or "")
        authored_slot = authored_by_id.get(slot_id)
        if not slot_id or not isinstance(authored_slot, dict) or slot_id in seen_ids:
            return None
        seen_ids.add(slot_id)

        persisted_without_aliases = {
            key: value
            for key, value in persisted_slot.items()
            if key != "any_of"
        }
        authored_without_aliases = {
            key: value
            for key, value in authored_slot.items()
            if key != "any_of"
        }
        old_aliases = persisted_slot.get("any_of")
        new_aliases = authored_slot.get("any_of")
        if (
            persisted_without_aliases != authored_without_aliases
            or not isinstance(old_aliases, list)
            or not isinstance(new_aliases, list)
            or not all(isinstance(alias, str) and alias.strip() for alias in old_aliases)
            or not all(isinstance(alias, str) and alias.strip() for alias in new_aliases)
        ):
            return None
        old_set = set(old_aliases)
        new_set = set(new_aliases)
        if not old_set.issubset(new_set):
            return None
        changed = changed or old_set != new_set
        updated_slots.append(deepcopy(authored_slot))

    if not changed or seen_ids != set(authored_by_id):
        return None
    return {**persisted_activity, "concept_slots": updated_slots}


def _reconcile_safe_evaluator_alias_expansions(
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Apply an audited alias-only evaluator correction to a current snapshot.

    A normal stale session remains stale. The only allowed version transition
    must be listed in ``_SAFE_STRICT_OPEN_ALIAS_MIGRATIONS`` and each stored
    activity must independently pass the alias-only predicate above.
    """

    chapter_state = state.get("chapter")
    if not isinstance(chapter_state, dict):
        return state, None
    chapter_id = str(chapter_state.get("chapter_id") or "")
    subject_id = str(state.get("subject_id") or "")
    try:
        class_no = int(state.get("target_class_no") or 0)
    except (TypeError, ValueError, OverflowError):
        return state, None
    live_chapter = next(
        (
            chapter
            for chapter in _available_chapters(subject_id, class_no)
            if str(chapter.get("chapter_id") or "") == chapter_id
        ),
        None,
    )
    if not isinstance(live_chapter, dict):
        return state, None
    stored_content_version = str(chapter_state.get("content_version") or "")
    live_content_version = str(live_chapter.get("content_version") or "")
    if stored_content_version == live_content_version:
        return state, None
    allowed_variant_ids = _SAFE_STRICT_OPEN_ALIAS_MIGRATIONS.get(
        (chapter_id, stored_content_version, live_content_version)
    )
    if not allowed_variant_ids:
        return state, None

    live_levels = {
        str(level.get("level_id") or ""): level
        for level in live_chapter.get("levels") or []
        if isinstance(level, dict) and str(level.get("level_id") or "")
    }
    persisted_levels = state.get("levels")
    if not isinstance(persisted_levels, list):
        return state, None

    changed_variant_ids: list[str] = []
    updated_levels: list[dict[str, Any]] = []
    for persisted_level in persisted_levels:
        if not isinstance(persisted_level, dict):
            return state, None
        level_id = str(persisted_level.get("level_id") or "")
        authored_level = live_levels.get(level_id)
        if not isinstance(authored_level, dict):
            return state, None
        persisted_steps = persisted_level.get("teaching_steps")
        authored_steps = authored_level.get("teaching_steps")
        if not isinstance(persisted_steps, list) or not isinstance(authored_steps, list):
            updated_levels.append(persisted_level)
            continue
        authored_steps_by_id = {
            str(step.get("step_id") or ""): step
            for step in authored_steps
            if isinstance(step, dict) and str(step.get("step_id") or "")
        }
        if len(authored_steps_by_id) != len(authored_steps):
            return state, None
        updated_steps: list[dict[str, Any]] = []
        level_changed = False
        for persisted_step in persisted_steps:
            if not isinstance(persisted_step, dict):
                return state, None
            step_id = str(persisted_step.get("step_id") or "")
            authored_step = authored_steps_by_id.get(step_id)
            if not isinstance(authored_step, dict):
                return state, None

            persisted_variants = persisted_step.get("variant_pool")
            authored_variants = authored_step.get("variant_pool")
            if not isinstance(persisted_variants, list) or not isinstance(
                authored_variants, list
            ):
                updated_steps.append(persisted_step)
                continue
            authored_by_variant_id = {
                str(variant.get("variant_id") or ""): variant
                for variant in authored_variants
                if isinstance(variant, dict) and str(variant.get("variant_id") or "")
            }
            if len(authored_by_variant_id) != len(authored_variants):
                return state, None
            updated_variants: list[dict[str, Any]] = []
            variants_changed = False
            for persisted_variant in persisted_variants:
                if not isinstance(persisted_variant, dict):
                    return state, None
                variant_id = str(persisted_variant.get("variant_id") or "")
                authored_variant = authored_by_variant_id.get(variant_id)
                if not isinstance(authored_variant, dict):
                    return state, None
                if variant_id not in allowed_variant_ids:
                    updated_variants.append(persisted_variant)
                    continue
                patched_variant = _safe_strict_open_alias_expansion(
                    persisted_variant,
                    authored_variant,
                )
                if patched_variant is None:
                    updated_variants.append(persisted_variant)
                    continue
                updated_variants.append(patched_variant)
                variants_changed = True
                changed_variant_ids.append(variant_id)
            if variants_changed:
                updated_steps.append(
                    {**persisted_step, "variant_pool": updated_variants}
                )
                level_changed = True
            else:
                updated_steps.append(persisted_step)
        if level_changed:
            updated_levels.append({**persisted_level, "teaching_steps": updated_steps})
        else:
            updated_levels.append(persisted_level)

    if not changed_variant_ids:
        return state, None
    repair = {
        "kind": "strict_open_alias_expansion_reconciled",
        "chapter_id": chapter_id,
        "from_content_version": stored_content_version,
        "to_content_version": live_content_version,
        "variant_ids": sorted(set(changed_variant_ids)),
    }
    return {
        **state,
        "chapter": {
            **chapter_state,
            "content_version": live_content_version,
        },
        "levels": updated_levels,
        "state_reconciliations": list(state.get("state_reconciliations") or [])
        + [repair],
    }, repair


def _v2_exhausted_support_masterclass_repair(
    previous_state: dict[str, Any],
    normalized_state: dict[str, Any],
) -> dict[str, Any] | None:
    """Mark a persisted support dead-end for an atomic masterclass transition."""

    support_required = previous_state.get("support_required")
    reason = (
        str(support_required.get("reason") or "")
        if isinstance(support_required, dict)
        else ""
    )
    if (
        reason not in _V2_EXHAUSTED_SUPPORT_MASTERCLASS_REASONS
        or str(previous_state.get("phase") or "") != "needs_support"
    ):
        return None
    interrupt = normalized_state.get("active_interrupt")
    if (
        normalized_state.get("status") == "paused_for_masterclass"
        and normalized_state.get("phase") == "paused_for_masterclass"
        and isinstance(interrupt, dict)
        and str(interrupt.get("runtime_contract") or "") == "v2"
    ):
        return {
            "kind": "v2_exhausted_support_masterclass",
            "reason": reason,
        }
    if (
        normalized_state.get("status") == "active"
        and normalized_state.get("phase") == "capped_support"
        and isinstance(normalized_state.get("support_required"), dict)
        and str(
            normalized_state["support_required"].get("reason") or ""
        )
        == "masterclass_cap_exceeded"
    ):
        return {
            "kind": "v2_exhausted_support_cap",
            "reason": reason,
        }
    return None


def _reconcile_v5_source_semantic_support_contract(state: dict[str, Any]) -> dict[str, Any]:
    """Backfill additive authored support metadata into v5 in-progress snapshots."""

    chapter_state = state.get("chapter")
    if not isinstance(chapter_state, dict):
        return state
    chapter_id = str(chapter_state.get("chapter_id") or "")
    subject_id = str(state.get("subject_id") or "")
    try:
        class_no = int(state.get("target_class_no") or 0)
    except (TypeError, ValueError):
        return state
    live_chapter = next(
        (
            chapter
            for chapter in _available_chapters(subject_id, class_no)
            if str(chapter.get("chapter_id") or "") == chapter_id
        ),
        None,
    )
    levels = state.get("levels")
    if not live_chapter or not isinstance(levels, list):
        return state
    live_levels = {
        str(level.get("level_id") or ""): level
        for level in live_chapter.get("levels") or []
        if isinstance(level, dict) and level.get("level_id")
    }
    updated_levels: list[dict[str, Any]] = []
    changed = False
    for persisted_level in levels:
        if not isinstance(persisted_level, dict):
            updated_levels.append(persisted_level)
            continue
        authored_level = live_levels.get(str(persisted_level.get("level_id") or ""))
        if not isinstance(authored_level, dict):
            updated_levels.append(persisted_level)
            continue
        updated_level = dict(persisted_level)
        persisted_checks = persisted_level.get("checks")
        authored_checks = authored_level.get("checks")
        if (
            isinstance(persisted_checks, dict)
            and isinstance(authored_checks, dict)
            and "revision_level_4" not in persisted_checks
            and isinstance(authored_checks.get("revision_level_4"), dict)
        ):
            updated_level["checks"] = {
                **persisted_checks,
                "revision_level_4": deepcopy(authored_checks["revision_level_4"]),
            }
            changed = True

        persisted_steps = persisted_level.get("teaching_steps")
        authored_steps = authored_level.get("teaching_steps")
        if isinstance(persisted_steps, list) and isinstance(authored_steps, list):
            authored_steps_by_id = {
                str(step.get("step_id") or ""): step
                for step in authored_steps
                if isinstance(step, dict) and step.get("step_id")
            }
            updated_steps: list[dict[str, Any]] = []
            steps_changed = False
            for persisted_step in persisted_steps:
                if not isinstance(persisted_step, dict):
                    updated_steps.append(persisted_step)
                    continue
                authored_step = authored_steps_by_id.get(
                    str(persisted_step.get("step_id") or "")
                )
                variants = persisted_step.get("variant_pool")
                authored_variants = (
                    authored_step.get("variant_pool")
                    if isinstance(authored_step, dict)
                    else None
                )
                if not isinstance(variants, list) or not isinstance(authored_variants, list):
                    updated_steps.append(persisted_step)
                    continue
                authored_by_variant_id = {
                    str(variant.get("variant_id") or ""): variant
                    for variant in authored_variants
                    if isinstance(variant, dict) and variant.get("variant_id")
                }
                updated_variants: list[dict[str, Any]] = []
                variants_changed = False
                for persisted_variant in variants:
                    if not isinstance(persisted_variant, dict):
                        updated_variants.append(persisted_variant)
                        continue
                    authored_variant = authored_by_variant_id.get(
                        str(persisted_variant.get("variant_id") or "")
                    )
                    criterion_mapping = (
                        authored_variant.get("criterion_misconception_tags")
                        if isinstance(authored_variant, dict)
                        else None
                    )
                    if (
                        isinstance(criterion_mapping, dict)
                        and criterion_mapping
                        and "criterion_misconception_tags" not in persisted_variant
                    ):
                        updated_variants.append(
                            {
                                **persisted_variant,
                                "criterion_misconception_tags": deepcopy(
                                    criterion_mapping
                                ),
                            }
                        )
                        variants_changed = True
                    else:
                        updated_variants.append(persisted_variant)
                if variants_changed:
                    updated_steps.append(
                        {**persisted_step, "variant_pool": updated_variants}
                    )
                    steps_changed = True
                else:
                    updated_steps.append(persisted_step)
            if steps_changed:
                updated_level["teaching_steps"] = updated_steps
                changed = True
        updated_levels.append(updated_level)
    return {**state, "levels": updated_levels} if changed else state


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
        "from_engine_version": _ASSESSMENT_REPAIR_ENGINE_VERSION,
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
    evidence_id: str | None = None,
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
    if activity.get("schema_version") == "school-activity-v2":
        return _apply_v2_curriculum_answer(
            normalized,
            activity=activity,
            answer=answer,
            answer_evaluation=answer_evaluation,
            evaluation_mode=effective_evaluation_mode,
            evidence_id=evidence_id or activity_id,
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
        "response_excerpt": "",
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": _sanitize_persisted_criteria(answer_evaluation["criteria"]),
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
    normalized["hot_session_memory"] = _remember_activity_fingerprints(
        normalized.get("hot_session_memory"),
        activity,
    )
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


def _apply_v2_curriculum_answer(
    state: dict[str, Any],
    *,
    activity: dict[str, Any],
    answer: str,
    answer_evaluation: dict[str, Any],
    evaluation_mode: str,
    evidence_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    level_index = int(activity["level_index"])
    levels = list(state.get("levels") or [])
    level = dict(levels[level_index])
    correct = bool(answer_evaluation["correct"])
    scored = bool(answer_evaluation.get("scored", True))
    attempt_no = int(activity.get("attempt_no") or 1)
    variant = dict(activity.get("variant") or {})
    variant_id = str(variant.get("variant_id") or "")
    active_tags = _bounded_remediation_tags(
        activity,
        answer_evaluation,
        correct=correct,
    )
    resolved_tags = list(level.get("v2_active_misconception_tags") or [])
    bounded_criteria = _sanitize_persisted_criteria(
        answer_evaluation.get("criteria") or []
    )
    attempt = {
        "activity_id": activity["activity_id"],
        "step_id": activity.get("step_id"),
        "kind": activity["kind"],
        "phase": activity.get("phase"),
        "attempt_no": attempt_no,
        "response_excerpt": "",
        "correct": correct,
        "scored": scored,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": bounded_criteria,
        "missing_criteria": list(answer_evaluation.get("missing_criteria") or []),
        "misconception_tags": (
            active_tags
            if not correct
            else list(answer_evaluation.get("misconception_tags") or [])
        ),
        "blockers": list(answer_evaluation.get("blockers") or []),
        "evaluation_mode": evaluation_mode,
        "evidence_role": activity.get("evidence_role"),
        "support_mode": activity.get("support_mode"),
        "skill_ids": list(activity.get("assessed_skill_ids") or []),
        "variant_id": variant_id or None,
        "evidence_id": evidence_id,
    }
    level["attempts"] = list(level.get("attempts") or []) + [attempt]
    if variant_id:
        level["used_variant_ids"] = list(
            dict.fromkeys(list(level.get("used_variant_ids") or []) + [variant_id])
        )

    is_support = activity.get("support_mode") == "bridge"
    is_entry_challenge = (
        level.get("entry_mode") == "challenge"
        and activity.get("phase") == "independent_application"
    )
    next_action = "advance"
    if is_support:
        if correct:
            level["v2_support_mode"] = None
            level.pop("v2_forced_support_kind", None)
            if state.get("phase") == "remediation":
                if state.get("remediation_mode") == "expanded_revision":
                    state, levels, level = _advance_expanded_revision(
                        state,
                        levels=levels,
                        level=level,
                        level_index=level_index,
                        kind=variant_id,
                    )
                else:
                    state, levels, level = _advance_focused_v2_remediation(
                        state,
                        levels=levels,
                        level=level,
                        level_index=level_index,
                        assessed_skill_ids=list(
                            activity.get("assessed_skill_ids") or []
                        ),
                    )
                next_action = "advance_assessment_remediation"
            else:
                next_action = "fresh_variant"
        else:
            level["v2_support_mode"] = None
            level.pop("v2_forced_support_kind", None)
            state, level, next_action = _pause_v2_for_masterclass(
                state,
                level=level,
                activity=activity,
            )
    elif not correct and is_entry_challenge:
        level["entry_mode"] = "full_cycle"
        level["v2_step_index"] = 0
        level["v2_support_mode"] = None
        level["current_step"] = str(
            (level.get("teaching_steps") or [{}])[0].get("phase") or "connect"
        )
        level["v2_active_misconception_tags"] = active_tags
        next_action = "challenge_fallback"
    elif not activity.get("assessed_skill_ids"):
        if (
            not correct
            and activity.get("interaction_type") != "continue"
            and _v2_step_has_unused_variant(level)
        ):
            level["v2_active_misconception_tags"] = active_tags
            next_action = "fresh_variant_without_skill_evidence"
        else:
            if not correct:
                level["v2_active_misconception_tags"] = active_tags
            state, levels, level = _advance_v2_step(
                state,
                levels=levels,
                level=level,
                level_index=level_index,
            )
            next_action = (
                "advance_without_skill_evidence"
                if correct
                else "advance_with_diagnostic_support"
            )
    elif correct:
        if scored:
            level["v2_active_misconception_tags"] = []
        state, levels, level = _advance_v2_step(
            state,
            levels=levels,
            level=level,
            level_index=level_index,
        )
    elif activity.get("phase") in {"connect", "co_construct"}:
        level["v2_active_misconception_tags"] = active_tags
        state, levels, level = _advance_v2_step(
            state,
            levels=levels,
            level=level,
            level_index=level_index,
        )
        next_action = "advance_with_diagnostic_support"
    else:
        level["v2_trigger_activity_id"] = activity["activity_id"]
        level["v2_return_activity_id"] = activity["activity_id"]
        level["v2_trigger_skill_ids"] = list(
            activity.get("assessed_skill_ids") or []
        )
        level["v2_trigger_relevance_terms"] = list(
            dict.fromkeys(
                str(term).strip()
                for term in activity.get("relevance_terms") or []
                if str(term).strip()
            )
        )
        level["v2_active_misconception_tags"] = active_tags
        level.pop("v2_forced_support_kind", None)
        targeted_support_kinds = _fresh_v2_targeted_support_kinds(
            state,
            level,
            trigger_skill_ids=list(activity.get("assessed_skill_ids") or []),
            active_tags=active_tags,
        )
        if active_tags and not targeted_support_kinds:
            state, level, next_action = _pause_v2_for_exhausted_support(
                state,
                level=level,
                level_index=level_index,
                reason="authored_targeted_support_unavailable",
            )
        else:
            level["v2_support_mode"] = "bridge"
            if targeted_support_kinds:
                level["v2_forced_support_kind"] = _semantic_support_kind(
                    level,
                    targeted_support_kinds,
                )
            next_action = "bridge_then_fresh_variant"

    levels[level_index] = level
    state["levels"] = levels
    state["hot_session_memory"] = _update_v2_hot_session_memory(
        state.get("hot_session_memory"),
        activity=activity,
        evaluation=answer_evaluation,
        evidence_id=evidence_id,
        level=level,
        resolved_tags=resolved_tags,
        next_action=next_action,
    )
    updated = normalize_curriculum_state(state)
    feedback = _v2_feedback_action(
        activity=activity,
        answer=answer,
        evaluation=answer_evaluation,
        next_action=next_action,
        updated_state=updated,
    )
    _set_feedback_v2(updated, feedback)
    updated["last_feedback"] = {
        "activity_id": activity["activity_id"],
        "level_id": activity["level_id"],
        "kind": activity["kind"],
        "correct": correct if scored else None,
        "message": " ".join(
            part
            for part in (
                str(feedback["what_worked"] or ""),
                str(feedback["criterion_gap"] or ""),
            )
            if part
        ),
    }
    evaluation = {
        "activity_id": activity["activity_id"],
        "level_id": activity["level_id"],
        "kind": activity["kind"],
        "phase": activity.get("phase"),
        "focus": activity["focus"],
        "skill_ids": list(activity.get("assessed_skill_ids") or []),
        "correct": correct,
        "scored": scored,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation.get("criteria") or []),
        "missing_criteria": list(answer_evaluation.get("missing_criteria") or []),
        "misconception_tags": (
            active_tags
            if not correct
            else list(answer_evaluation.get("misconception_tags") or [])
        ),
        "blockers": list(answer_evaluation.get("blockers") or []),
        "language_detected": str(answer_evaluation.get("language_detected") or ""),
        "model_score": answer_evaluation.get("model_score"),
        "evaluation_mode": evaluation_mode,
        "evidence_role": activity.get("evidence_role"),
        "attempt_no": attempt_no,
        "evidence_id": evidence_id,
    }
    return normalize_curriculum_state(updated), evaluation


def _advance_v2_step(
    state: dict[str, Any],
    *,
    levels: list[dict[str, Any]],
    level: dict[str, Any],
    level_index: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    steps = list(level.get("teaching_steps") or [])
    next_step_index = int(level.get("v2_step_index") or 0) + 1
    if next_step_index < len(steps):
        next_step = steps[next_step_index]
        level["v2_step_index"] = next_step_index
        level["current_step"] = str(next_step.get("phase") or "")
        level["status"] = "in_progress"
        return state, levels, level

    level["status"] = "complete"
    level["current_step"] = "complete"
    level["v2_step_index"] = len(steps)
    if (next_level_index := level_index + 1) < len(levels):
        next_level = dict(levels[next_level_index])
        next_level["status"] = "in_progress"
        next_level["v2_step_index"] = int(next_level.get("v2_step_index") or 0)
        if next_level.get("teaching_steps"):
            next_level["current_step"] = str(
                next_level["teaching_steps"][next_level["v2_step_index"]]["phase"]
            )
        else:
            next_level["current_step"] = "guided_check"
        levels[next_level_index] = next_level
        state["current_level_index"] = next_level_index
        return state, levels, level

    state["current_level_index"] = level_index
    levels[level_index] = level
    state["levels"] = levels
    if not state.get("chapter_assessment"):
        raise ValueError("chapter_assessment_required_for_v2")
    state = _begin_chapter_assessment(state)
    return state, list(state.get("levels") or levels), level


def _configure_v2_assessment_remediation(
    level: dict[str, Any],
    *,
    targeted_skill_ids: list[str],
    forced_support_kind: str | None = None,
) -> dict[str, Any]:
    configured = dict(level)
    remediation_skill_ids = _assessment_remediation_skill_ids(configured)
    targeted = [
        skill_id
        for skill_id in dict.fromkeys(targeted_skill_ids)
        if skill_id in remediation_skill_ids
    ]
    if not targeted:
        raise ValueError("chapter_assessment_remediation_skill_missing")
    configured["status"] = "in_progress"
    configured["current_step"] = forced_support_kind or "bridge"
    configured["v2_support_mode"] = "bridge"
    configured["v2_trigger_skill_ids"] = targeted
    configured["v2_active_misconception_tags"] = []
    configured["v2_trigger_activity_id"] = "chapter_assessment"
    configured["v2_return_activity_id"] = "chapter_assessment"
    if forced_support_kind:
        configured["v2_forced_support_kind"] = forced_support_kind
    else:
        configured.pop("v2_forced_support_kind", None)
    return configured


def _advance_focused_v2_remediation(
    state: dict[str, Any],
    *,
    levels: list[dict[str, Any]],
    level: dict[str, Any],
    level_index: int,
    assessed_skill_ids: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    if not assessed_skill_ids:
        raise ValueError("chapter_assessment_remediation_evidence_missing")
    remaining = list(
        dict.fromkeys(
            str(item)
            for item in state.get("assessment_remediation_remaining_skill_ids")
            or level.get("v2_trigger_skill_ids")
            or []
        )
    )
    remaining = [
        skill_id for skill_id in remaining if skill_id not in set(assessed_skill_ids)
    ]
    state["assessment_remediation_remaining_skill_ids"] = remaining
    level.pop("v2_forced_support_kind", None)
    level["v2_support_mode"] = None

    current_remaining = [
        skill_id
        for skill_id in remaining
        if skill_id in _assessment_remediation_skill_ids(level)
    ]
    if current_remaining:
        level = _configure_v2_assessment_remediation(
            level,
            targeted_skill_ids=current_remaining,
        )
        levels[level_index] = level
        state["levels"] = levels
        return state, levels, level

    level["status"] = "complete"
    level["current_step"] = "complete"
    levels[level_index] = level
    queue = list(state.get("remediation_queue") or [])
    if not queue or queue[0] != level.get("level_id"):
        raise ValueError("chapter_remediation_queue_mismatch")
    queue = queue[1:]
    state["remediation_queue"] = queue
    if queue:
        next_level_index = next(
            index
            for index, candidate in enumerate(levels)
            if candidate.get("level_id") == queue[0]
        )
        next_level = _configure_v2_assessment_remediation(
            dict(levels[next_level_index]),
            targeted_skill_ids=remaining,
        )
        levels[next_level_index] = next_level
        state["levels"] = levels
        state["current_level_index"] = next_level_index
        return state, levels, level

    if remaining:
        raise ValueError("chapter_assessment_remediation_level_missing")
    state["levels"] = levels
    state["current_level_index"] = level_index
    state.pop("assessment_remediation_remaining_skill_ids", None)
    state = _begin_chapter_assessment(state)
    levels = list(state.get("levels") or levels)
    return state, levels, dict(levels[level_index])


def _masterclass_cap_support_plan(
    state: dict[str, Any],
    *,
    level: dict[str, Any],
    assessed_skill_ids: list[str],
) -> dict[str, Any]:
    level_id = str(level["level_id"])
    history = [
        {
            key: item.get(key)
            for key in (
                "interrupt_id",
                "level_id",
                "focus",
                "skill_ids",
                "trigger_count",
                "masterclass_session_id",
                "resolution",
            )
        }
        for raw_item in state.get("interrupt_history") or []
        if isinstance(raw_item, dict)
        for item in [dict(raw_item)]
        if str(item.get("level_id") or "") == level_id
        and item.get("resolution") in {"complete", "abandoned"}
        and item.get("masterclass_session_id")
    ]
    return {
        "reason": "masterclass_cap_exceeded",
        "level_id": level_id,
        "skill_ids": assessed_skill_ids,
        "focus": str(level.get("focus") or ""),
        "auto_masterclass_disabled": True,
        "continuation_action": "continue_after_support_cap",
        "cap": {
            "used": min(len(history), MAX_MASTERCLASS_INTERRUPTS_PER_LEVEL),
            "limit": MAX_MASTERCLASS_INTERRUPTS_PER_LEVEL,
            "scope": "level",
        },
        "history": history,
    }


def _pause_v2_for_masterclass(
    state: dict[str, Any],
    *,
    level: dict[str, Any],
    activity: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    state.pop("support_required", None)
    counts = dict(state.get("interrupt_counts") or {})
    level_id = str(level["level_id"])
    assessed_skill_ids = list(activity.get("assessed_skill_ids") or [])
    if not assessed_skill_ids:
        raise ValueError("masterclass_assessed_skills_missing")
    if level.get("v2_auto_masterclass_disabled"):
        state["status"] = "active"
        state["phase"] = "capped_support"
        state["active_interrupt"] = None
        state["support_required"] = _masterclass_cap_support_plan(
            state,
            level=level,
            assessed_skill_ids=assessed_skill_ids,
        )
        return state, level, "continue_after_support_cap"
    trigger_count = int(counts.get(level_id) or 0) + 1
    counts[level_id] = trigger_count
    state["interrupt_counts"] = counts
    if trigger_count <= MAX_MASTERCLASS_INTERRUPTS_PER_LEVEL:
        state["status"] = "paused_for_masterclass"
        state["phase"] = "paused_for_masterclass"
        state["active_interrupt"] = {
            "runtime_contract": "v2",
            "interrupt_id": f"{level_id}:masterclass:{trigger_count}",
            "level_id": level_id,
            "focus": level.get("focus") or "",
            "skill_ids": assessed_skill_ids,
            "trigger_count": trigger_count,
            "return_step": str(activity.get("phase") or "guided_practice"),
            "return_step_index": int(level.get("v2_step_index") or 0),
            "trigger_activity_id": level.get("v2_trigger_activity_id"),
            "return_activity_id": level.get("v2_return_activity_id"),
            "masterclass_session_id": None,
        }
        return state, level, "start_masterclass"

    state["status"] = "active"
    state["phase"] = "capped_support"
    state["active_interrupt"] = None
    level["v2_auto_masterclass_disabled"] = True
    state["interrupt_history"] = list(state.get("interrupt_history") or []) + [
        {
            "interrupt_id": f"{level_id}:masterclass:{trigger_count}",
            "level_id": level_id,
            "focus": level.get("focus") or "",
            "skill_ids": assessed_skill_ids,
            "trigger_count": trigger_count,
            "masterclass_session_id": None,
            "resolution": "capped_out",
        }
    ]
    state["support_required"] = _masterclass_cap_support_plan(
        state,
        level=level,
        assessed_skill_ids=assessed_skill_ids,
    )
    level["active_blockers"] = list(
        dict.fromkeys(
            list(level.get("active_blockers") or [])
            + ["masterclass_cap_exceeded"]
        )
    )
    return state, level, "continue_after_support_cap"


def _pause_v2_for_exhausted_support(
    state: dict[str, Any],
    *,
    level: dict[str, Any],
    level_index: int,
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Escalate an exhausted v2 bridge to durable, linked masterclass work.

    A learner must never be left at a report-only support page merely because
    the finite bridge pool for the exact misconception has been consumed. The
    target-class masterclass contract preserves the paused authored step and
    gives the learner a bounded, resumable route back into the chapter.
    """

    if reason not in _V2_EXHAUSTED_SUPPORT_MASTERCLASS_REASONS:
        raise ValueError("unsupported_v2_support_exhaustion_reason")
    if not level.get("teaching_steps"):
        raise ValueError("masterclass_requires_v2_level")
    assessed_skill_ids = list(
        dict.fromkeys(
            str(skill_id)
            for skill_id in (
                level.get("v2_trigger_skill_ids") or level.get("skill_ids") or []
            )
            if str(skill_id)
        )
    )
    if not assessed_skill_ids:
        raise ValueError("masterclass_assessed_skills_missing")

    step = _v2_step(level)
    if step is None:
        raise ValueError("masterclass_return_step_not_found")
    return_activity_id = str(
        level.get("v2_return_activity_id")
        or level.get("v2_trigger_activity_id")
        or f"{level['level_id']}:{step.get('step_id') or 'return'}:support-exhausted"
    )
    level["v2_trigger_activity_id"] = str(
        level.get("v2_trigger_activity_id") or return_activity_id
    )
    level["v2_return_activity_id"] = return_activity_id
    level["v2_trigger_skill_ids"] = assessed_skill_ids
    level["v2_support_mode"] = None
    level.pop("v2_forced_support_kind", None)

    levels = list(state.get("levels") or [])
    if level_index < 0 or level_index >= len(levels):
        raise ValueError("masterclass_level_not_found")
    levels[level_index] = level
    state["levels"] = levels
    state.pop("support_required", None)
    state["active_interrupt"] = None
    return _pause_v2_for_masterclass(
        state,
        level=level,
        activity={
            "activity_id": return_activity_id,
            "phase": str(step.get("phase") or "guided_practice"),
            "assessed_skill_ids": assessed_skill_ids,
        },
    )


def _update_v2_hot_session_memory(
    value: Any,
    *,
    activity: dict[str, Any],
    evaluation: dict[str, Any],
    evidence_id: str,
    level: dict[str, Any],
    resolved_tags: list[str],
    next_action: str,
) -> dict[str, Any]:
    memory = _normalize_hot_session_memory(value)
    correct = bool(evaluation["correct"])
    scored = bool(evaluation.get("scored", True))
    variant_id = str((activity.get("variant") or {}).get("variant_id") or "")
    memory["revision"] += 1
    memory["last_activity_id"] = activity["activity_id"]
    memory["last_response_language"] = evaluation.get("language_detected")
    memory["next_instructional_action"] = next_action
    memory["served_activity_ids"] = list(
        dict.fromkeys(memory["served_activity_ids"] + [activity["activity_id"]])
    )[-40:]
    memory = _remember_activity_fingerprints(memory, activity)
    if variant_id:
        memory["used_variant_ids"] = list(
            dict.fromkeys(memory["used_variant_ids"] + [variant_id])
        )
    memory["recent_evidence_ids"] = list(
        dict.fromkeys(memory["recent_evidence_ids"] + [evidence_id])
    )[-12:]
    missing_criteria = list(evaluation.get("missing_criteria") or [])
    memory["recent_criterion_gaps"] = (
        memory["recent_criterion_gaps"]
        + [
            {
                "activity_id": activity["activity_id"],
                "criterion_id": str(criterion_id),
            }
            for criterion_id in missing_criteria
        ]
    )[-12:]
    effective_misconception_tags = list(
        dict.fromkeys(
            list(evaluation.get("misconception_tags") or [])
            + (
                list(activity.get("target_misconception_tags") or [])
                if not correct
                else []
            )
        )
    )
    memory["recent_outcomes"] = (
        memory["recent_outcomes"]
        + [
            {
                "activity_id": activity["activity_id"],
                "phase": activity.get("phase"),
                "skill_ids": list(activity.get("skill_ids") or []),
                "correct": correct if scored else None,
                "scored": scored,
                "score": float(evaluation["score"]),
                "outcome": (
                    "not_scored"
                    if not scored
                    else "correct"
                    if correct
                    else "needs_support"
                ),
                "criterion_gap_ids": missing_criteria,
                "misconception_tags": effective_misconception_tags,
                "support_mode": activity.get("support_mode"),
            }
        ]
    )[-8:]
    if activity.get("support_mode"):
        memory["support_history"] = (
            memory["support_history"]
            + [
                {
                    "activity_id": activity["activity_id"],
                    "support_mode": activity.get("support_mode"),
                    "correct": correct,
                }
            ]
        )[-8:]
    if next_action == "bridge_then_fresh_variant":
        memory["active_support_count"] += 1
    if scored:
        streaks = dict(memory["skill_streaks"])
        for skill_id in activity.get("skill_ids") or []:
            streaks[str(skill_id)] = (
                int(streaks.get(str(skill_id)) or 0) + 1 if correct else 0
            )
        memory["skill_streaks"] = streaks
    if scored and correct and not activity.get("support_mode"):
        resolved_tag_set = set(resolved_tags)
        memory["unresolved_misconception_tags"] = [
            tag
            for tag in memory["unresolved_misconception_tags"]
            if tag not in resolved_tag_set
        ]
        memory["unresolved_outcome_id"] = None
    elif not correct:
        new_tags = list(
            dict.fromkeys(
                effective_misconception_tags
                + [f"criterion:{item}" for item in missing_criteria]
            )
        )
        memory["unresolved_misconception_tags"] = list(
            dict.fromkeys(memory["unresolved_misconception_tags"] + new_tags)
        )
        memory["unresolved_outcome_id"] = level.get("level_id")
    return _normalize_hot_session_memory(memory)


def _v2_feedback_action(
    *,
    activity: dict[str, Any],
    answer: str,
    evaluation: dict[str, Any],
    next_action: str,
    updated_state: dict[str, Any],
) -> dict[str, Any]:
    scored = bool(evaluation.get("scored", True))
    correct = bool(evaluation["correct"])
    missing = list(evaluation.get("missing_criteria") or [])
    if not scored:
        what_worked = "You reviewed this teaching step before moving on."
        criterion_gap = None
    elif correct:
        what_worked = _learner_visible_success_move(activity)
        criterion_gap = None
    else:
        skill_hint = _learner_visible_skill_coaching_hint(activity)
        if "vocab.spelling" in _activity_skill_ids(activity):
            what_worked = "That spelling needs another careful look."
        elif activity.get("grading_mode") == "selected_option":
            what_worked = "That choice does not fit the visible clue yet."
        elif skill_hint:
            what_worked = "This skill needs one more careful try."
        else:
            what_worked = "Start with one visible clue before you try again."
        criterion_gap = _learner_visible_criterion_gap(
            activity,
            missing_gaps=[str(value) for value in missing],
        )
    next_support_by_action = {
        "advance": "Continue to the next authored learning step.",
        "fresh_variant": "Try a fresh example without repeating the previous prompt.",
        "fresh_variant_without_skill_evidence": (
            "Try one fresh guided example before moving on."
        ),
        "bridge_then_fresh_variant": (
            "Use one smaller bridge example, then retry with a fresh prompt."
        ),
        "challenge_fallback": (
            "Build this skill from the first teaching step, then return to a fresh challenge."
        ),
        "advance_with_diagnostic_support": (
            "Continue to the explanation; Zidd will use this response to choose extra support."
        ),
        "start_masterclass": "Open the focused masterclass, then resume this exact step.",
        "open_support_plan": "Open the support plan; another automatic detour is blocked.",
        "continue_after_support_cap": (
            "Continue explicitly with the cap recorded and retry this phase using a fresh example."
        ),
    }
    if updated_state.get("status") == "paused_for_masterclass":
        allowed_next_actions = ["start_masterclass"]
    elif updated_state.get("phase") == "capped_support":
        allowed_next_actions = ["continue_after_support_cap"]
    elif updated_state.get("phase") == "needs_support":
        allowed_next_actions = ["view_support_plan"]
    elif updated_state.get("status") == "complete":
        allowed_next_actions = ["view_chapter_result"]
    else:
        allowed_next_actions = ["answer_next_activity"]
    if not scored:
        outcome = "advanced"
        feedback_type = "instruction"
    elif correct:
        outcome = "correct"
        feedback_type = "affirmation"
    elif updated_state.get("status") == "paused_for_masterclass":
        outcome = "paused_for_masterclass"
        feedback_type = "masterclass"
    elif updated_state.get("phase") == "capped_support":
        outcome = "capped_support"
        feedback_type = "support_limit"
    else:
        outcome = "needs_support"
        feedback_type = "corrective"
    return {
        "outcome": outcome,
        "feedback_type": feedback_type,
        "correct": correct,
        "scored": scored,
        "response_excerpt": "",
        "what_worked": what_worked,
        "criterion_gap": criterion_gap,
        "misconception_tag": None,
        "next_support": next_support_by_action.get(
            next_action,
            "Continue with the next learning step.",
        ),
        "retry_policy": next_action,
        "allowed_next_actions": allowed_next_actions,
    }


def _learner_visible_success_move(activity: dict[str, Any]) -> str:
    """Describe the prompt's public learning move without retaining learner text."""

    authored_feedback = str(activity.get("success_feedback") or "").strip()
    if authored_feedback:
        return authored_feedback

    prompt = " ".join(str(activity.get("prompt") or "").split()).casefold()
    skill_ids = _activity_skill_ids(activity)
    # Existing persisted sessions contain the original authored activity. Keep
    # their post-fix feedback pedagogically accurate without rewriting state.
    if "planning rule" in prompt:
        return "You chose the planning move that keeps the story clear."
    if "collective noun" in prompt and any(
        marker in prompt for marker in ("infer", "means", "explain")
    ):
        return (
            "You explained the word from its context and showed why the group word fits."
        )
    if "collective noun" in prompt:
        return "You identified the group word in the sentence."
    if "movement" in prompt and "cause to outcome" in prompt:
        return (
            "You tracked the object's movement from what started it to where it ended."
        )
    if "own words" in prompt:
        return "You put the idea into your own words."
    if "main idea" in prompt and "image" in prompt:
        return "You stated the main idea and explained what the image adds."
    if "sound image" in prompt and "message" in prompt:
        return "You connected the sound image to the teamwork message."
    if "image" in prompt and "message" in prompt:
        return "You connected the image to the teamwork message."
    if "where should" in prompt and any(
        marker in prompt for marker in ("look first", "search first")
    ):
        return "You used the visible action to decide where to look first."
    if any(marker in prompt for marker in ("humorous", "funny")) and any(
        marker in prompt for marker in ("central situation", "why")
    ):
        return (
            "You explained the mismatch between what the character believes and "
            "what the reader can see."
        )
    if "reader infer" in prompt and "visible clue" in prompt:
        return "You used the visible clue to make a careful inference."
    if "what does" in prompt and "mean here" in prompt and "new sentence" in prompt:
        return (
            "You worked out the word from its context and used it naturally in a "
            "new sentence."
        )
    if prompt.startswith("infer ") and "use the word in another setting" in prompt:
        return "You inferred the word's meaning from context and used it in a new setting."
    if "contrast" in prompt and "new sentence" in prompt:
        return "You compared the two meanings and used the word in a fresh sentence."
    if (
        "what would you" in prompt
        and "because" in prompt
        and "but" in prompt
    ):
        return "You gave a clear next step, a reason, and a careful contrast."
    if any(
        marker in prompt
        for marker in (
            "smallest to largest",
            "largest to smallest",
            "lightest to heaviest",
            "heaviest to lightest",
            "softest to loudest",
            "loudest to softest",
            "least to greatest",
            "least to the greatest",
            "greatest to least",
            "greatest to the least",
        )
    ):
        return "You ordered the items by the stated attribute."
    if "pair phrase" in prompt and "location detail" in prompt:
        return "You used a new pair phrase and placed it clearly."
    if "written pattern" in prompt and "both context" in prompt:
        return (
            "You compared the spelling pattern, explained both meanings from "
            "context, and used the word in a new sentence."
        )
    if "past-tense story" in prompt or (
        "story" in prompt
        and any(marker in prompt for marker in ("original verse", "these lines"))
    ):
        return (
            "You turned the verse into a clear past-tense story while keeping "
            "the events in order."
        )
    if "who promises" in prompt:
        return "You identified the speaker who makes the promise."
    if (
        "order" in prompt
        or "sequence" in prompt
        or any(
            phrase in prompt
            for phrase in (
                "happened first",
                "happened second",
                "happened third",
                "happened next",
                "happened last",
                "what happens next",
                "what happened next",
                "first, then",
                "first and then",
                "second, then",
                "third, then",
            )
        )
    ):
        return "You followed the events in the order the task asked for."
    if "compare" in prompt:
        return "You compared the details before giving your answer."
    if {
        "reading.dialogue_attribution",
        "writing.dialogue",
    }.issubset(skill_ids):
        return (
            "You identified the speakers and explained how the reply carries the "
            "conversation forward."
        )
    if "reading.dialogue_attribution" in skill_ids:
        return "You identified who is speaking and how the reply connects."
    if "writing.dialogue" in skill_ids:
        return "You wrote a clear reply that answers the line before it."
    skill_feedback = (
        ("vocab.attribute_ordering", "You ordered the items by the stated attribute."),
        ("vocab.spelling", "You checked the letters and used the standard spelling."),
        ("vocab.antonyms", "You chose an opposite that fits the sentence."),
        ("grammar.prepositions", "You used a position word that fits the situation."),
        (
            "grammar.sentence_order",
            "You put the words in an order that makes a clear sentence.",
        ),
        (
            "grammar.tense_usage",
            "You matched the verb form to the time in the sentence.",
        ),
        ("writing.summary_own_words", "You retold the idea in your own words."),
        ("writing.complete_sentence", "You wrote a complete sentence that makes sense."),
        ("writing.short_answer", "You gave a clear answer to the question."),
        (
            "reading.word_meaning_context",
            "You used the context to work out the word's meaning.",
        ),
        (
            "reading.inference_reason",
            "You used a clue to make a careful inference.",
        ),
        (
            "reading.paragraph_main_idea",
            "You identified the central idea from the details.",
        ),
        (
            "grammar.connectors_because_and_but",
            "You linked your ideas with a clear reason or contrast.",
        ),
        (
            "vocab.chapter_word_usage",
            "You used the chapter word in a context that fits.",
        ),
    )
    for skill_id, feedback in skill_feedback:
        if skill_id in skill_ids:
            return feedback
    if any(marker in prompt for marker in ("why", "because", "reason")):
        return "You gave a reason linked to a visible clue."
    if any(marker in prompt for marker in ("source clue", "passage", "evidence")):
        return "You used a source clue from the passage."
    if "clue" in prompt:
        return "You used a clue to support your answer."
    if activity.get("grading_mode") == "selected_option":
        return "You matched your choice to a visible clue."
    if "sentence" in prompt:
        return "You completed the sentence so it makes sense."
    return "You connected your answer to what the task asked."


def _activity_skill_ids(activity: dict[str, Any]) -> set[str]:
    return {
        str(skill_id)
        for skill_id in (
            activity.get("assessed_skill_ids")
            or activity.get("skill_ids")
            or activity.get("knowledge_components")
            or []
        )
    }


def _learner_visible_skill_coaching_hint(activity: dict[str, Any]) -> str:
    """Return an answer-free correction strategy for a closed school skill."""

    hints = (
        (
            "vocab.spelling",
            "Compare each letter with the familiar word pattern before you write it again.",
        ),
        (
            "vocab.antonyms",
            "Replace the word in the sentence and choose the opposite that keeps its meaning clear.",
        ),
        (
            "vocab.attribute_ordering",
            "Name the attribute first, then compare every item on that one scale.",
        ),
        (
            "grammar.prepositions",
            "Picture where each object is, then test the position word in the sentence.",
        ),
        (
            "grammar.sentence_order",
            "Read the words in order and check that the sentence has a clear subject and action.",
        ),
        (
            "grammar.tense_usage",
            "Find the time clue, then choose the verb form that matches it.",
        ),
        (
            "writing.summary_own_words",
            "Keep the main events and say them in your own words.",
        ),
        (
            "writing.complete_sentence",
            "Check that your sentence says who or what and what happens.",
        ),
        (
            "writing.short_answer",
            "Answer the question directly, then add one supporting detail.",
        ),
        (
            "reading.word_meaning_context",
            "Use the nearby words to work out the meaning before you answer.",
        ),
        (
            "reading.inference_reason",
            "Point to one visible clue, then explain what it suggests.",
        ),
        (
            "reading.paragraph_main_idea",
            "Choose the idea that connects all the details, not just one detail.",
        ),
        (
            "grammar.connectors_because_and_but",
            "Use because to give a reason or but to show a careful contrast.",
        ),
        (
            "vocab.chapter_word_usage",
            "Use the surrounding sentence to check how the chapter word is working.",
        ),
    )
    skill_ids = _activity_skill_ids(activity)
    return next(
        (hint for skill_id, hint in hints if skill_id in skill_ids),
        "",
    )


def _learner_visible_criterion_gap(
    activity: dict[str, Any],
    *,
    missing_gaps: list[str],
) -> str:
    prompt = " ".join(str(activity.get("prompt") or "").split()).strip()
    if prompt:
        specific_task_hint = _learner_visible_specific_task_recheck_hint(activity)
        if specific_task_hint:
            # Generic rubric suffixes such as ``detail_2`` are reused across
            # unrelated activities. A public task-level strategy is more useful
            # than guessing what a positional rubric slot means.
            return specific_task_hint
        task_hint = _learner_visible_task_recheck_hint(activity)
        skill_hint = _learner_visible_skill_coaching_hint(activity)
        criterion_hints = list(
            dict.fromkeys(
                hint
                for criterion_id in missing_gaps
                if (hint := _safe_criterion_coaching_hint(criterion_id))
            )
        )
        if skill_hint:
            specific_move = " ".join(criterion_hints[:2])
            return " ".join(
                part
                for part in (
                    skill_hint,
                    specific_move,
                    # A criterion-level move is more useful than repeating the
                    # visible prompt. Keep the prompt fallback for cases where
                    # the evaluator supplied no learner-safe criterion detail.
                    "" if specific_move else task_hint,
                )
                if part
            )
        if activity.get("grading_mode") == "selected_option":
            return f"{_selected_option_reasoning_hint(prompt)} {task_hint}"
        if criterion_hints:
            return f"{' '.join(criterion_hints[:3])} {task_hint}"
        return task_hint
    focus = str(activity.get("focus") or "this chapter skill").strip()
    return f"Use one clear clue from the passage to show {focus}."


def _learner_visible_task_recheck_hint(activity: dict[str, Any]) -> str:
    """Give a public next move without copying a prompt into feedback."""

    specific_hint = _learner_visible_specific_task_recheck_hint(activity)
    if specific_hint:
        return specific_hint

    prompt = " ".join(str(activity.get("prompt") or "").split()).casefold()
    if activity.get("grading_mode") == "selected_option":
        return "Re-read the visible question and choose the option that best fits the passage."
    if (
        ("both clues" in prompt or "two details" in prompt)
        and (
            "decide" in prompt
            or "what should" in prompt
            or "return action" in prompt
        )
    ):
        return "State your decision, then explain how both visible clues support it."
    if "collective noun" in prompt and (
        "different sentence" in prompt or "new sentence" in prompt
    ):
        return (
            "Work through all three parts: explain the word from its clue, name the "
            "collective noun, then write a new sentence that shows the word's meaning."
        )
    return "Re-read the visible task and include every requested part in your own words."


def _learner_visible_specific_task_recheck_hint(activity: dict[str, Any]) -> str:
    """Return task-specific support that never reveals an authored answer."""

    prompt = " ".join(str(activity.get("prompt") or "").split()).casefold()
    if (
        "past-tense story" in prompt
        or "story from these lines" in prompt
        or ("original verse" in prompt and "story" in prompt)
        or ("retell" in prompt and ("event" in prompt or "lines" in prompt))
    ):
        return (
            "Retell all supplied events in their original order. Keep the stated "
            "result instead of inventing a new ending."
        )
    if (
        "infer" in prompt
        and ("another setting" in prompt or "new sentence" in prompt)
        and ("word" in prompt or "meaning" in prompt)
    ):
        return (
            "Explain the word's meaning in your own words, then write a new "
            "sentence that uses it in a clear setting."
        )
    return ""


def _safe_criterion_coaching_hint(criterion_id: str) -> str:
    """Translate common rubric gaps without exposing a model answer or raw ID."""

    label = str(criterion_id or "").rsplit(":", 1)[-1].casefold()
    hints = {
        "chapter_words_target": (
            "Explain the word's meaning in your own words."
        ),
        "response_min_words": (
            "Use enough words to explain each requested part clearly."
        ),
        "own_words": (
            "Put the idea into your own words instead of copying labels or phrases "
            "from the notes."
        ),
        "structure": "Include every requested part and place the parts in a clear order.",
        "source": "Name the supplied source so the reader can trace the facts.",
        "facts": "Use the requested number of facts and keep each one supported by the packet.",
        "evidence": "Link your answer to a visible clue from the passage.",
        "reason": "Add a reason that explains how the visible clue supports your answer.",
        "order": "Put the events or ideas in the order shown by the passage.",
        "start": "Add where or how the event begins.",
        "beginning": "Add where or how the event begins.",
        "middle": "Add what happens between the beginning and ending.",
        "movement": "Add what happens between the beginning and ending.",
        "first_speaker": "Identify who speaks first.",
        "second_speaker": "Identify who gives the next reply.",
        "listener": "Name who hears the line.",
        "contribution": (
            "Explain what new information or action the reply adds."
        ),
        "cause": "Name the event or clue that caused the result.",
        "outcome": "State the final result clearly.",
        "tense": "Match the verb form to the visible time clue.",
    }
    return hints.get(label, "")


def _selected_option_reasoning_hint(prompt: str) -> str:
    """Give a visible-clue strategy without exposing an authored answer."""

    folded = prompt.casefold()
    if "immediately before" in folded:
        return (
            "Trace only the final two events. 'Immediately before' asks for the "
            "last place or action just before the stated outcome."
        )
    if "happened second" in folded or "second event" in folded:
        return (
            "Number the visible events 1, 2, 3 and check event 2 rather than the "
            "first or final event."
        )
    if "main idea" in folded or "central idea" in folded:
        return (
            "Test each choice against the whole passage; a single true detail is "
            "not enough to be the main idea."
        )
    if folded.startswith("who") and any(
        marker in folded
        for marker in ("promise", "said", "says", "speak", "reply", "told")
    ):
        return (
            "Find the exact spoken line, then follow the name or reporting verb "
            "attached to that line; do not choose the speaker of a different turn."
        )
    if folded.startswith("why") or " cause" in f" {folded}":
        return (
            "Find the clue that causes the event, then reject choices that only "
            "repeat the result."
        )
    if "meaning" in folded or "means" in folded:
        return (
            "Substitute each choice into the sentence and keep the one that fits "
            "the surrounding clue."
        )
    return (
        "Eliminate each choice with a visible clue; a related phrase is not "
        "automatically the requested answer."
    )


def _content_fingerprint(value: Any) -> str:
    cleaned = " ".join(str(value or "").split()).casefold()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest() if cleaned else ""


def _sanitize_persisted_criteria(value: Any) -> list[dict[str, Any]]:
    return [
        {
            **criterion,
            "evidence_quote": "",
        }
        for criterion in value or []
        if isinstance(criterion, dict)
    ]


def _sanitize_persisted_attempt(value: dict[str, Any]) -> dict[str, Any]:
    sanitized = {
        key: item
        for key, item in value.items()
        if key not in {"answer", "response_excerpt"}
    }
    sanitized["response_excerpt"] = ""
    if "criteria" in sanitized:
        sanitized["criteria"] = _sanitize_persisted_criteria(sanitized["criteria"])
    return sanitized


def _sanitize_chapter_assessment(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    sanitized = dict(value)
    sanitized["responses"] = [
        _sanitize_persisted_attempt(response)
        for response in value.get("responses") or []
        if isinstance(response, dict)
    ]
    return sanitized


def _sanitize_last_feedback(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    sanitized = dict(value)
    sanitized["message"] = (
        "Chapter check passed. The next chapter is ready."
        if sanitized.get("result_visible") and sanitized.get("correct")
        else "Your latest learning step is saved."
    )
    return sanitized


def _sanitize_feedback_v2(
    value: Any,
    *,
    public_digest: Any = None,
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if not _feedback_v2_is_trusted(value, public_digest=public_digest):
        return _safe_feedback_v2_fallback()
    return {key: value[key] for key in _FEEDBACK_V2_PUBLIC_KEYS}


def _activity_content_is_fresh(value: Any, activity: dict[str, Any]) -> bool:
    memory = _normalize_hot_session_memory(value)
    passage_fingerprint = _content_fingerprint(activity.get("passage"))
    prompt_fingerprint = _content_fingerprint(activity.get("prompt"))
    return (
        (not passage_fingerprint or passage_fingerprint not in memory["passage_fingerprints"])
        and (not prompt_fingerprint or prompt_fingerprint not in memory["prompt_fingerprints"])
    )


def _chapter_assessment_content_is_fresh(
    value: Any,
    activity: dict[str, Any],
) -> bool:
    """Keep assessment evidence new without rejecting a reusable question stem."""

    memory = _normalize_hot_session_memory(value)
    passage_fingerprint = _content_fingerprint(activity.get("passage"))
    return bool(passage_fingerprint) and (
        passage_fingerprint not in memory["passage_fingerprints"]
    )


def _remember_activity_fingerprints(value: Any, activity: dict[str, Any]) -> dict[str, Any]:
    memory = _normalize_hot_session_memory(value)
    passage_fingerprint = _content_fingerprint(activity.get("passage"))
    prompt_fingerprint = _content_fingerprint(activity.get("prompt"))
    if passage_fingerprint:
        memory["passage_fingerprints"] = list(
            dict.fromkeys(memory["passage_fingerprints"] + [passage_fingerprint])
        )
    if prompt_fingerprint:
        memory["prompt_fingerprints"] = list(
            dict.fromkeys(memory["prompt_fingerprints"] + [prompt_fingerprint])
        )
    return memory


def _attempt_authored_activity(
    level: dict[str, Any], attempt: dict[str, Any]
) -> dict[str, Any] | None:
    variant_id = str(attempt.get("variant_id") or "")
    if attempt.get("kind") == "v2_support":
        candidate = (level.get("checks") or {}).get(variant_id)
        return dict(candidate) if isinstance(candidate, dict) else None
    step_id = str(attempt.get("step_id") or "")
    for step in level.get("teaching_steps") or []:
        if not isinstance(step, dict) or str(step.get("step_id") or "") != step_id:
            continue
        if isinstance(step.get("activity"), dict):
            return dict(step["activity"])
        candidate = next(
            (
                item
                for item in step.get("variant_pool") or []
                if isinstance(item, dict)
                and str(item.get("variant_id") or "") == variant_id
            ),
            None,
        )
        return dict(candidate) if isinstance(candidate, dict) else None
    candidate = (level.get("checks") or {}).get(str(attempt.get("kind") or ""))
    return dict(candidate) if isinstance(candidate, dict) else None


def _reconstruct_hot_session_fingerprints(
    state: dict[str, Any], value: Any
) -> dict[str, Any]:
    memory = _normalize_hot_session_memory(value)
    for level in state.get("levels") or []:
        if not isinstance(level, dict):
            continue
        for attempt in level.get("attempts") or []:
            if isinstance(attempt, dict) and (
                activity := _attempt_authored_activity(level, attempt)
            ):
                memory = _remember_activity_fingerprints(memory, activity)
    assessment = state.get("chapter_assessment")
    if isinstance(assessment, dict):
        items_by_id = {
            str(item.get("item_id") or ""): item
            for item in assessment.get("items") or []
            if isinstance(item, dict)
        }
        for response in assessment.get("responses") or []:
            if isinstance(response, dict) and (
                item := items_by_id.get(str(response.get("item_id") or ""))
            ):
                memory = _remember_activity_fingerprints(memory, item)
    return memory


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
    completed: list[str] = []
    for chapter_id in state_json.get("completed_chapter_ids") or []:
        cleaned = str(chapter_id).strip()
        if cleaned in available_by_id and cleaned not in completed:
            completed.append(cleaned)
    if _session_status(latest_curriculum_session) == "complete":
        chapter_id = str((state_json.get("chapter") or {}).get("chapter_id") or "").strip()
        if chapter_id in available_by_id and chapter_id not in completed:
            completed.append(chapter_id)
    return completed


def _review_due_chapter_ids(
    latest_curriculum_session: dict[str, Any] | None,
) -> list[str]:
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
    review_due: list[str] = []
    for chapter_id in _completed_chapter_ids(latest_curriculum_session):
        chapter = available_by_id.get(chapter_id) or {}
        required_version = str(
            chapter.get("certification_version")
            or chapter.get("content_version")
            or ""
        ).strip()
        completed_version = str(
            completed_certification_versions.get(chapter_id)
            or completed_versions.get(chapter_id)
            or ""
        ).strip()
        if required_version and completed_version != required_version:
            review_due.append(chapter_id)
    return review_due


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


def _public_curriculum_next_action(
    state: dict[str, Any],
    *,
    session_id: str,
) -> dict[str, Any] | None:
    if (
        state.get("status") == "active"
        and state.get("phase") == "needs_support"
        and state.get("active_interrupt") is None
        and isinstance(state.get("support_required"), dict)
    ):
        return {
            "action": "view_support_plan",
            "next_action_url": f"/school/support/{session_id}",
            "reason": str(
                state["support_required"].get("reason")
                or "chapter_support_required"
            ),
            "requires_explicit_confirmation": False,
        }
    if (
        state.get("status") != "active"
        or state.get("phase") != "capped_support"
        or state.get("active_interrupt") is not None
    ):
        return None
    levels = list(state.get("levels") or [])
    level_index = int(state.get("current_level_index") or 0)
    if level_index < 0 or level_index >= len(levels):
        return None
    level = levels[level_index]
    if "masterclass_cap_exceeded" not in list(level.get("active_blockers") or []):
        return None
    return {
        "action": "continue_after_support_cap",
        "level_id": str(level.get("level_id") or ""),
        "reason": "masterclass_cap_exceeded",
        "requires_explicit_confirmation": True,
    }


def _public_support_required(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    cap = value.get("cap")
    history = value.get("history")
    return {
        "reason": str(value.get("reason") or "support_required"),
        "attempt_count": int(value.get("attempt_count") or 0),
        "weak_skill_ids": [str(item) for item in value.get("weak_skill_ids") or []],
        "remediation_skill_ids": [
            str(item) for item in value.get("remediation_skill_ids") or []
        ],
        "focus": str(value.get("focus") or ""),
        "cap": dict(cap) if isinstance(cap, dict) else {},
        "history": [dict(item) for item in history or [] if isinstance(item, dict)],
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


def _prior_memory_targeting_tags(
    learning_memory: dict[str, Any] | None,
    chapter: dict[str, Any],
) -> list[str]:
    chapter_skill_ids = {
        str(skill_id)
        for level in chapter.get("levels") or []
        for skill_id in level.get("skill_ids") or []
        if str(skill_id)
    }
    tags: list[str] = []
    for bucket in ("active_gaps", "improving_gaps"):
        for item in (learning_memory or {}).get(bucket) or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("skill_id") or "") not in chapter_skill_ids:
                continue
            tags.extend(
                str(value)
                for value in item.get("misconception_tags") or []
                if str(value)
            )
            tags.extend(
                f"criterion:{value}"
                for value in item.get("criterion_gap_ids") or []
                if str(value)
            )
    return list(dict.fromkeys(tags))[:16]


def _public_memory_summary(value: Any) -> dict[str, Any]:
    memory = value if isinstance(value, dict) else {}

    def learner_skill_label(skill_id: str) -> str:
        label = _LEARNER_SKILL_LABELS.get(skill_id)
        if label:
            return label
        fallback = skill_id.rsplit(".", 1)[-1].replace("_", " ").strip()
        return fallback.capitalize() if fallback else "English skill"

    def public_skill_evidence(items: Any) -> list[dict[str, Any]]:
        return [
            {
                "skill_id": (skill_id := str(item.get("skill_id") or "")),
                "skill_label": learner_skill_label(skill_id),
                "skill_status": str(item.get("skill_status") or ""),
                "readiness": float(item.get("readiness") or 0.0),
                "mastery": float(item.get("mastery") or 0.0),
                "confidence": float(item.get("confidence") or 0.0),
                "latest_evidence": str(item.get("latest_evidence") or "")[:240],
                "last_attempt_type": str(item.get("last_attempt_type") or ""),
                "last_chapter_id": str(item.get("last_chapter_id") or ""),
                "attempts": int(item.get("attempts") or 0),
                "certifying_attempts": int(item.get("certifying_attempts") or 0),
                "independent_passes": int(item.get("independent_passes") or 0),
                "transfer_passes": int(item.get("transfer_passes") or 0),
                "review_passes": int(item.get("review_passes") or 0),
                "chapter_passes": int(item.get("chapter_passes") or 0),
                "active_blockers": [
                    str(value)
                    for value in item.get("active_blockers") or []
                    if str(value)
                ],
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
                "skill_id": (skill_id := str(item.get("skill_id") or "")),
                "skill_label": learner_skill_label(skill_id),
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


def _normalize_hot_session_memory(value: Any) -> dict[str, Any]:
    memory = dict(value) if isinstance(value, dict) else {}
    recent_criterion_gaps = [
        {
            "activity_id": str(item.get("activity_id") or ""),
            "criterion_id": str(item.get("criterion_id") or ""),
        }
        for item in memory.get("recent_criterion_gaps") or []
        if isinstance(item, dict) and item.get("criterion_id")
    ][-12:]
    support_history = [
        {
            "activity_id": str(item.get("activity_id") or ""),
            "support_mode": str(item.get("support_mode") or ""),
            "correct": bool(item.get("correct")),
        }
        for item in memory.get("support_history") or []
        if isinstance(item, dict) and item.get("activity_id")
    ][-8:]
    return {
        "revision": max(1, int(memory.get("revision") or 1)),
        "recent_outcomes": [
            {
                "activity_id": str(item.get("activity_id") or ""),
                "phase": str(item.get("phase") or ""),
                "skill_ids": [str(value) for value in item.get("skill_ids") or []],
                "outcome": str(item.get("outcome") or ""),
                "correct": item.get("correct"),
                "scored": bool(item.get("scored")),
                "score": float(item.get("score") or 0.0),
                "criterion_gap_ids": [
                    str(value) for value in item.get("criterion_gap_ids") or []
                ],
                "misconception_tags": [
                    str(value) for value in item.get("misconception_tags") or []
                ],
                "support_mode": item.get("support_mode"),
            }
            for item in memory.get("recent_outcomes") or []
            if isinstance(item, dict)
        ][-8:],
        "skill_streaks": {
            str(skill_id): int(count)
            for skill_id, count in dict(memory.get("skill_streaks") or {}).items()
        },
        "used_variant_ids": list(
            dict.fromkeys(str(item) for item in memory.get("used_variant_ids") or [])
        ),
        "served_activity_ids": list(
            dict.fromkeys(
                str(item) for item in memory.get("served_activity_ids") or []
            )
        )[-40:],
        "passage_fingerprints": list(
            dict.fromkeys(
                str(item) for item in memory.get("passage_fingerprints") or []
            )
        ),
        "prompt_fingerprints": list(
            dict.fromkeys(
                str(item) for item in memory.get("prompt_fingerprints") or []
            )
        ),
        "recent_evidence_ids": list(
            dict.fromkeys(
                str(item) for item in memory.get("recent_evidence_ids") or []
            )
        )[-12:],
        "recent_criterion_gaps": recent_criterion_gaps,
        "support_history": support_history,
        "unresolved_misconception_tags": list(
            dict.fromkeys(
                str(item)
                for item in memory.get("unresolved_misconception_tags") or []
            )
        ),
        "active_support_count": max(
            0,
            int(memory.get("active_support_count") or 0),
        ),
        "last_activity_id": memory.get("last_activity_id"),
        "last_response_language": memory.get("last_response_language"),
        "unresolved_outcome_id": memory.get("unresolved_outcome_id"),
        "next_instructional_action": memory.get("next_instructional_action"),
    }


def _public_hot_session_memory(value: Any) -> dict[str, Any]:
    memory = _normalize_hot_session_memory(value)
    next_instructional_action = memory["next_instructional_action"]
    return {
        "recent_outcomes": [
            {
                key: item.get(key)
                for key in (
                    "activity_id",
                    "phase",
                    "skill_ids",
                    "correct",
                    "scored",
                    "score",
                    "outcome",
                    "support_mode",
                )
            }
            for item in memory["recent_outcomes"]
        ],
        "skill_streaks": memory["skill_streaks"],
        "unresolved_misconception_tags": [],
        "active_support_count": memory["active_support_count"],
        "last_activity_id": memory["last_activity_id"],
        "last_response_language": memory["last_response_language"],
        "unresolved_outcome_id": None,
        "next_instructional_action": (
            next_instructional_action
            if next_instructional_action in _PUBLIC_RETRY_POLICIES
            or next_instructional_action == "answer_next_activity"
            else None
        ),
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
        "entry_mode": level.get("entry_mode") or "full_cycle",
        "teaching_goal": level.get("teaching_goal") or "",
        "guided_check_label": "Learn with a worked clue",
        "bridge_label": "Slow support if the clue is missed",
        "masterclass_label": "Focused reteach after repeated struggle",
        "independent_check_label": "Try without hints",
        "transfer_check_label": "Use the skill in a new example",
    }


def _v2_step(level: dict[str, Any]) -> dict[str, Any] | None:
    steps = list(level.get("teaching_steps") or [])
    index = int(level.get("v2_step_index") or 0)
    if index < 0 or index >= len(steps):
        return None
    step = steps[index]
    return dict(step) if isinstance(step, dict) else None


def _v2_step_has_unused_variant(level: dict[str, Any]) -> bool:
    step = _v2_step(level)
    if not step:
        return False
    used = {str(item) for item in level.get("used_variant_ids") or []}
    return any(
        str(item.get("variant_id") or "")
        and str(item.get("variant_id")) not in used
        for item in step.get("variant_pool") or []
        if isinstance(item, dict)
    )


def _v2_step_activity(
    state: dict[str, Any],
    level: dict[str, Any],
    step: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None, bool]:
    memory = _normalize_hot_session_memory(state.get("hot_session_memory"))
    used = set(str(item) for item in level.get("used_variant_ids") or [])
    seen_passages = set(memory["passage_fingerprints"])
    seen_prompts = set(memory["prompt_fingerprints"])

    def is_fresh(variant_id: str) -> bool:
        return variant_id not in used

    def has_fresh_content(activity: dict[str, Any]) -> bool:
        passage_fresh = (
            _content_fingerprint(activity.get("passage")) not in seen_passages
        )
        if (
            activity.get("interaction_type") == "continue"
            and activity.get("evidence_role") == "experience"
        ):
            # These authored teaching steps intentionally share one neutral
            # acknowledgement prompt. The fresh passage is the new instruction.
            return passage_fresh
        return passage_fresh and (
            _content_fingerprint(activity.get("prompt")) not in seen_prompts
        )

    if isinstance(step.get("activity"), dict):
        activity = dict(step["activity"])
        variant_id = str(activity.get("variant_id") or f"{step['step_id']}:single")
        if not is_fresh(variant_id) or not has_fresh_content(activity):
            return None, variant_id, False
        return activity, variant_id, True

    variants = [
        dict(item)
        for item in step.get("variant_pool") or []
        if isinstance(item, dict)
    ]
    unused = [
        item
        for item in variants
        if is_fresh(str(item.get("variant_id") or ""))
        and has_fresh_content(item)
    ]
    if not unused:
        return None, None, False
    unresolved_tags = set(memory["unresolved_misconception_tags"])
    targeted = [
        item
        for item in unused
        if unresolved_tags.intersection(item.get("target_misconception_tags") or [])
    ]
    selected = (targeted or unused)[0]
    return selected, str(selected.get("variant_id") or ""), True


def _v2_assessed_skill_ids(
    authored: dict[str, Any],
    level: dict[str, Any],
) -> list[str]:
    """Return only skills for which this activity can create evidence."""

    level_skill_ids = list(
        dict.fromkeys(str(item) for item in level.get("skill_ids") or [])
    )
    authored_skill_ids = list(
        dict.fromkeys(
            str(item) for item in authored.get("knowledge_components") or []
        )
    )
    unknown = [
        skill_id for skill_id in authored_skill_ids if skill_id not in level_skill_ids
    ]
    if unknown:
        raise ValueError(
            "authored_activity_skill_outside_level:"
            + ",".join(sorted(unknown))
        )
    if (
        authored.get("interaction_type") == "continue"
        or authored.get("evidence_role") == "experience"
    ):
        return []
    if not authored_skill_ids:
        if authored.get("evidence_role") in {"formative", "reflection"}:
            return []
        raise ValueError("authored_activity_assessed_skills_missing")
    return authored_skill_ids


def _fresh_v2_targeted_support_kinds(
    state: dict[str, Any],
    level: dict[str, Any],
    *,
    trigger_skill_ids: list[str],
    active_tags: list[str],
) -> list[str]:
    """Return only fresh authored support that addresses the active mistake."""

    if not active_tags:
        return []
    support_kinds = _V2_SUPPORT_KINDS + (
        ("masterclass",) if state.get("phase") == "remediation" else ()
    )
    support_attempt_records = [
        attempt
        for attempt in level.get("attempts") or []
        if attempt.get("kind") == "v2_support"
    ]
    used_support_kinds = {
        str(attempt.get("variant_id") or "")
        for attempt in support_attempt_records
        if str(attempt.get("variant_id") or "")
    }
    legacy_attempt_count = sum(
        1 for attempt in support_attempt_records if not attempt.get("variant_id")
    )
    used_support_kinds.update(support_kinds[:legacy_attempt_count])
    checks = level.get("checks") or {}
    trigger_skill_set = {str(skill_id) for skill_id in trigger_skill_ids}
    active_tag_set = {str(tag) for tag in active_tags}
    return [
        kind
        for kind in support_kinds
        if isinstance(checks.get(kind), dict)
        and kind not in used_support_kinds
        and _activity_content_is_fresh(
            state.get("hot_session_memory"), checks.get(kind) or {}
        )
        and trigger_skill_set.intersection(
            str(skill_id)
            for skill_id in (checks.get(kind) or {}).get(
                "knowledge_components"
            )
            or []
        )
        and active_tag_set.intersection(
            str(tag)
            for tag in (checks.get(kind) or {}).get(
                "target_misconception_tags"
            )
            or []
        )
    ]


def _semantic_support_kind(
    level: dict[str, Any],
    support_kinds: list[str],
) -> str:
    """Prefer an authored support whose text names the failed task's anchor."""

    trigger_terms = [
        " ".join(str(term).casefold().split())
        for term in level.get("v2_trigger_relevance_terms") or []
        if len(" ".join(str(term).split())) >= 4
    ]
    if not trigger_terms:
        return support_kinds[0]
    checks = level.get("checks") or {}
    for kind in support_kinds:
        check = checks.get(kind) or {}
        support_text = " ".join(
            str(check.get(field) or "")
            for field in ("teaching_block", "passage", "prompt", "model_answer")
        ).casefold()
        if any(term in support_text for term in trigger_terms):
            return kind
    return support_kinds[0]


def _source_semantic_support_kinds(
    level: dict[str, Any],
    support_kinds: list[str],
) -> list[str]:
    """Return support whose authored text contains the failed source anchor."""

    trigger_terms = [
        " ".join(str(term).casefold().split())
        for term in level.get("v2_trigger_relevance_terms") or []
        if len(" ".join(str(term).split())) >= 4
    ]
    if not trigger_terms:
        return []
    checks = level.get("checks") or {}
    return [
        kind
        for kind in support_kinds
        if any(
            term
            in " ".join(
                str((checks.get(kind) or {}).get(field) or "")
                for field in (
                    "teaching_block",
                    "passage",
                    "prompt",
                    "model_answer",
                )
            ).casefold()
            for term in trigger_terms
        )
    ]


def _is_legacy_empty_tag_semantic_review_support(level: dict[str, Any]) -> bool:
    """Identify a persisted review failure that predates misconception tags."""

    trigger_activity_id = str(level.get("v2_trigger_activity_id") or "")
    return bool(
        level.get("v2_support_mode") == "bridge"
        and not level.get("v2_active_misconception_tags")
        and level.get("v2_trigger_relevance_terms")
        and any(
            str(attempt.get("activity_id") or "") == trigger_activity_id
            and str(attempt.get("phase") or "") == "review"
            and attempt.get("correct") is False
            for attempt in level.get("attempts") or []
            if isinstance(attempt, dict)
        )
    )


def _v2_support_activity(
    state: dict[str, Any],
    level: dict[str, Any],
    *,
    level_index: int,
) -> dict[str, Any]:
    support_kinds = _V2_SUPPORT_KINDS + (
        ("masterclass",) if state.get("phase") == "remediation" else ()
    )
    support_attempt_records = [
        attempt
        for attempt in level.get("attempts") or []
        if attempt.get("kind") == "v2_support"
    ]
    used_support_kinds = {
        str(attempt.get("variant_id") or "")
        for attempt in support_attempt_records
        if str(attempt.get("variant_id") or "")
    }
    legacy_attempt_count = sum(
        1 for attempt in support_attempt_records if not attempt.get("variant_id")
    )
    used_support_kinds.update(support_kinds[:legacy_attempt_count])
    checks = level.get("checks") or {}
    active_tags = set(level.get("v2_active_misconception_tags") or [])
    forced_support_kind = str(level.get("v2_forced_support_kind") or "")
    if forced_support_kind and active_tags and not active_tags.intersection(
        (checks.get(forced_support_kind) or {}).get(
            "target_misconception_tags"
        )
        or []
    ):
        forced_support_kind = ""
    candidate_support_kinds = (
        (forced_support_kind,) if forced_support_kind else support_kinds
    )
    authored_support_kinds = [
        kind
        for kind in candidate_support_kinds
        if isinstance(checks.get(kind), dict)
    ]
    available_support_kinds = [
        kind
        for kind in authored_support_kinds
        if kind not in used_support_kinds
        and _activity_content_is_fresh(
            state.get("hot_session_memory"), checks.get(kind) or {}
        )
    ]
    if not available_support_kinds:
        raise ValueError("authored_support_pool_exhausted")
    trigger_skill_ids = list(
        dict.fromkeys(
            str(item) for item in level.get("v2_trigger_skill_ids") or []
        )
    )
    trigger_skill_set = set(trigger_skill_ids)
    compatible_support_kinds = []
    for kind in available_support_kinds:
        authored_skill_ids = {
            str(item)
            for item in (checks.get(kind) or {}).get("knowledge_components") or []
        }
        if authored_skill_ids.intersection(trigger_skill_set):
            compatible_support_kinds.append(kind)
    if not compatible_support_kinds:
        raise ValueError("authored_support_not_available_for_trigger")
    targeted_support_kinds = [
        kind
        for kind in compatible_support_kinds
        if active_tags.intersection(
            (checks.get(kind) or {}).get("target_misconception_tags") or []
        )
    ]
    if active_tags and not targeted_support_kinds:
        raise ValueError("authored_targeted_support_unavailable")
    if active_tags:
        support_kind = _semantic_support_kind(level, targeted_support_kinds)
    elif _is_legacy_empty_tag_semantic_review_support(level):
        source_semantic_support_kinds = _source_semantic_support_kinds(
            level,
            compatible_support_kinds,
        )
        if not source_semantic_support_kinds:
            raise ValueError("authored_source_semantic_support_unavailable")
        support_kind = source_semantic_support_kinds[0]
    else:
        support_kind = _semantic_support_kind(level, compatible_support_kinds)
    raw_check = (level.get("checks") or {}).get(support_kind)
    check = dict(raw_check)
    attempt_no = len(support_attempt_records) + 1
    authored_skill_ids = list(
        dict.fromkeys(
            str(item) for item in check.get("knowledge_components") or []
        )
    )
    unknown_assessed_skill_ids = [
        skill_id
        for skill_id in authored_skill_ids
        if skill_id not in set(level.get("skill_ids") or [])
    ]
    if unknown_assessed_skill_ids:
        raise ValueError(
            "support_skill_outside_level:"
            + ",".join(sorted(unknown_assessed_skill_ids))
        )
    assessed_skill_ids = [
        skill_id for skill_id in authored_skill_ids if skill_id in trigger_skill_set
    ]
    if not assessed_skill_ids:
        raise ValueError("support_assessed_skills_missing")
    language_support = localized_teaching_support(
        preferred_language=str(state.get("preferred_teaching_language") or "en"),
        skill_ids=assessed_skill_ids,
        stage="bridge",
        en_production_confidence=float(
            state.get("en_production_confidence") or 0.0
        ),
    )
    return {
        "activity_id": f"{level['level_id']}:v2_support:{attempt_no}:{support_kind}",
        "level_id": level["level_id"],
        "level_index": level_index,
        "kind": "v2_support",
        "title": f"Support: {level['title']}",
        "focus": level.get("focus") or "",
        "skill_ids": assessed_skill_ids,
        "assessed_skill_ids": assessed_skill_ids,
        "teaching_block": " ".join(
            part for part in (language_support, check["teaching_block"]) if part
        ),
        "passage": check["passage"],
        "prompt": check["prompt"],
        "options": list(check.get("options") or []),
        "grading_mode": check.get("grading_mode"),
        "certifying_language": check.get("certifying_language"),
        "response_mode": check.get("response_mode") or "short",
        "answer_rule": check.get("answer_rule"),
        "evaluation_mode": check.get("evaluation_mode"),
        "semantic_evidence_policy": check.get("semantic_evidence_policy"),
        "preflight_rule": check.get("preflight_rule"),
        "pass_score": check.get("pass_score"),
        "rubric_criteria": [
            dict(item) for item in check.get("rubric_criteria") or []
        ],
        "concept_slots": [dict(item) for item in check.get("concept_slots") or []],
        "forbidden_phrases": list(check.get("forbidden_phrases") or []),
        "relevance_terms": list(check.get("relevance_terms") or []),
        "model_answer": check.get("model_answer"),
        "target_misconception_tags": list(
            check.get("target_misconception_tags") or []
        ),
        "min_response_words": check.get("min_response_words"),
        "ordered_concept_slot_ids": list(
            check.get("ordered_concept_slot_ids") or []
        ),
        "accepted_answers": list(check.get("accepted_answers") or []),
        "attempt_no": attempt_no,
        "schema_version": "school-activity-v2",
        "phase": "guided_practice",
        "interaction_type": (
            "single_choice" if check.get("options") else "short_text"
        ),
        "evidence_role": "supported",
        "source_anchor_ids": list(level.get("source_anchor_ids") or []),
        "knowledge_components": assessed_skill_ids,
        "support_mode": "bridge",
        "variant": {
            "pool_id": f"{level['level_id']}:support",
            "variant_id": support_kind,
            "ordinal": attempt_no,
            "fresh": support_kind not in used_support_kinds,
        },
        "lineage": {
            "parent_activity_id": _normalize_hot_session_memory(
                state.get("hot_session_memory")
            ).get("last_activity_id"),
            "trigger_activity_id": level.get("v2_trigger_activity_id"),
            "interrupt_id": None,
            "return_activity_id": level.get("v2_return_activity_id"),
            "masterclass_session_id": None,
        },
    }


def _ensure_v2_support_availability_contract(
    state: dict[str, Any],
) -> dict[str, Any]:
    """Escalate exhausted v2 bridge support through the masterclass contract."""

    phase = str(state.get("phase") or "")
    if phase == "capped_support":
        return state
    levels = list(state.get("levels") or [])
    level_index = int(state.get("current_level_index") or 0)
    if level_index < 0 or level_index >= len(levels):
        return state
    level = dict(levels[level_index])
    support_required = state.get("support_required")
    persisted_reason = (
        str(support_required.get("reason") or "")
        if isinstance(support_required, dict)
        else ""
    )
    if phase == "needs_support":
        if (
            state.get("status") == "active"
            and state.get("active_interrupt") is None
            and level.get("teaching_steps")
            and persisted_reason in _V2_EXHAUSTED_SUPPORT_MASTERCLASS_REASONS
        ):
            state, level, _next_action = _pause_v2_for_exhausted_support(
                state,
                level=level,
                level_index=level_index,
                reason=persisted_reason,
            )
            levels[level_index] = level
            state["levels"] = levels
            return state
        return state
    if level.get("v2_support_mode") != "bridge":
        return state
    legacy_empty_tag_support = _is_legacy_empty_tag_semantic_review_support(level)
    try:
        _v2_support_activity(state, level, level_index=level_index)
    except ValueError as exc:
        reason = str(exc)
        support_unavailable = {
            "authored_support_pool_exhausted",
            "authored_support_not_available_for_trigger",
            "authored_targeted_support_unavailable",
        }
        if reason not in support_unavailable and not (
            legacy_empty_tag_support
            and reason == "authored_source_semantic_support_unavailable"
        ):
            return state
    else:
        return state
    trigger_skill_ids = list(
        dict.fromkeys(
            str(skill_id) for skill_id in level.get("v2_trigger_skill_ids") or []
        )
    )
    if not trigger_skill_ids:
        return state
    state, level, _next_action = _pause_v2_for_exhausted_support(
        state,
        level=level,
        level_index=level_index,
        reason=reason,
    )
    levels[level_index] = level
    state["levels"] = levels
    return state


def _current_v2_activity(
    state: dict[str, Any],
    level: dict[str, Any],
    *,
    level_index: int,
) -> dict[str, Any] | None:
    if level.get("v2_support_mode") == "bridge":
        return _v2_support_activity(state, level, level_index=level_index)
    step = _v2_step(level)
    if step is None:
        return None
    authored, variant_id, fresh = _v2_step_activity(state, level, step)
    if authored is None or not variant_id:
        if step.get("variant_pool") and step.get("required", True):
            raise ValueError("authored_variant_pool_exhausted")
        raise ValueError("authored_activity_variant_unavailable")
    attempt_no = 1 + sum(
        1
        for attempt in level.get("attempts") or []
        if attempt.get("step_id") == step.get("step_id")
    )
    assessed_skill_ids = _v2_assessed_skill_ids(authored, level)
    memory_note = _memory_support_note(
        state,
        level,
        assessed_skill_ids=assessed_skill_ids,
    )
    language_support = localized_teaching_support(
        preferred_language=str(state.get("preferred_teaching_language") or "en"),
        skill_ids=level.get("skill_ids") or [],
        stage=str(step.get("phase") or "guided_practice"),
        en_production_confidence=float(
            state.get("en_production_confidence") or 0.0
        ),
    )
    phase = str(step.get("phase") or authored.get("teaching_phase") or "guided_practice")
    return {
        **authored,
        "activity_id": f"{level['level_id']}:{step['step_id']}:{variant_id}:{attempt_no}",
        "level_id": level["level_id"],
        "level_index": level_index,
        "step_id": str(step.get("step_id") or ""),
        "kind": f"v2_{phase}",
        "phase": phase,
        "title": f"{phase.replace('_', ' ').title()}: {level['title']}",
        "focus": level.get("focus") or "",
        "skill_ids": assessed_skill_ids,
        "assessed_skill_ids": assessed_skill_ids,
        "teaching_block": " ".join(
            part
            for part in (
                language_support,
                memory_note,
                authored.get("teaching_block"),
            )
            if part
        ),
        "options": list(authored.get("options") or []),
        "rubric_criteria": [
            dict(item) for item in authored.get("rubric_criteria") or []
        ],
        "concept_slots": [
            dict(item) for item in authored.get("concept_slots") or []
        ],
        "forbidden_phrases": list(authored.get("forbidden_phrases") or []),
        "ordered_concept_slot_ids": list(
            authored.get("ordered_concept_slot_ids") or []
        ),
        "accepted_answers": list(authored.get("accepted_answers") or []),
        "attempt_no": attempt_no,
        "entry_mode": level.get("entry_mode") or "full_cycle",
        "support_mode": None,
        "variant": {
            "pool_id": str(authored.get("pool_id") or step.get("pool_id") or step["step_id"]),
            "variant_id": variant_id,
            "ordinal": attempt_no,
            "fresh": fresh,
        },
        "lineage": {
            "parent_activity_id": _normalize_hot_session_memory(
                state.get("hot_session_memory")
            ).get("last_activity_id"),
            "trigger_activity_id": level.get("v2_trigger_activity_id"),
            "interrupt_id": (
                (state.get("active_interrupt") or {}).get("interrupt_id")
                if isinstance(state.get("active_interrupt"), dict)
                else level.get("v2_last_interrupt_id")
            ),
            "return_activity_id": level.get("v2_return_activity_id"),
            "masterclass_session_id": (
                (state.get("active_interrupt") or {}).get("masterclass_session_id")
                if isinstance(state.get("active_interrupt"), dict)
                else level.get("v2_last_masterclass_session_id")
            ),
        },
    }


def _current_activity(state: dict[str, Any]) -> dict[str, Any] | None:
    if state.get("status") in {"complete", "paused_for_masterclass"} or state.get(
        "phase"
    ) in {"paused_for_masterclass", "capped_support", "needs_support"}:
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
    if level.get("teaching_steps"):
        return _current_v2_activity(state, level, level_index=level_index)
    kind = str(level.get("current_step") or "guided_check")
    check = _check_for_level(level, kind)
    repeated_kind = any(
        previous.get("kind") == kind
        for previous in level.get("attempts") or []
        if isinstance(previous, dict)
    )
    if repeated_kind and not _activity_content_is_fresh(
        state.get("hot_session_memory"), check
    ):
        raise ValueError("authored_activity_variant_unavailable")
    attempt_no = 1 + sum(
        1 for previous in level.get("attempts") or [] if previous.get("kind") == kind
    )
    memory_note = _memory_support_note(
        state,
        level,
        assessed_skill_ids=list(level.get("skill_ids") or []),
    )
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
        "grading_mode": check.get("grading_mode"),
        "certifying_language": check.get("certifying_language"),
        "response_mode": check.get("response_mode") or "short",
        "answer_rule": check.get("answer_rule"),
        "evaluation_mode": check.get("evaluation_mode"),
        "preflight_rule": check.get("preflight_rule"),
        "pass_score": check.get("pass_score"),
        "rubric_criteria": [dict(criterion) for criterion in check.get("rubric_criteria") or []],
        "concept_slots": [dict(slot) for slot in check.get("concept_slots") or []],
        "forbidden_phrases": list(check.get("forbidden_phrases") or []),
        "relevance_terms": list(check.get("relevance_terms") or []),
        "model_answer": check.get("model_answer"),
        "target_misconception_tags": list(
            check.get("target_misconception_tags") or []
        ),
        "min_response_words": check.get("min_response_words"),
        "ordered_concept_slot_ids": list(
            check.get("ordered_concept_slot_ids") or []
        ),
        "accepted_answers": list(check.get("accepted_answers") or []),
        "attempt_no": attempt_no,
    }


def _memory_support_note(
    state: dict[str, Any],
    level: dict[str, Any],
    *,
    assessed_skill_ids: list[str],
) -> str:
    skill_ids = set(assessed_skill_ids)
    if not skill_ids:
        return ""
    memory = state.get("learner_memory")
    if not isinstance(memory, dict):
        return ""
    for bucket in ("active_gaps", "improving_gaps"):
        for item in memory.get(bucket) or []:
            if not isinstance(item, dict) or item.get("skill_id") not in skill_ids:
                continue
            focus = str(level.get("focus") or "this chapter skill").strip()
            status_copy = (
                "this skill needs another careful try"
                if bucket == "active_gaps"
                else "you are building confidence in this skill"
            )
            return (
                f"Zidd remembers that {status_copy}. "
                f"In this lesson, focus on {focus}."
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
        "planned_form_item_ids": [],
    }


def _begin_chapter_assessment(state: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    assessment = dict(updated.get("chapter_assessment") or {})
    attempt_no = int(assessment.get("attempt_no") or 0) + 1
    max_attempts = int(assessment.get("max_attempts") or 2)
    if attempt_no > max_attempts:
        raise ValueError("chapter_assessment_attempt_limit_exhausted")
    item_count = int(assessment.get("items_per_attempt") or 12)
    items = [
        dict(item)
        for item in assessment.get("items") or []
        if isinstance(item, dict)
        and _chapter_assessment_content_is_fresh(
            state.get("hot_session_memory"),
            item,
        )
    ]
    used_item_ids = list(assessment.get("used_item_ids") or [])
    used_item_ids = list(
        dict.fromkeys(used_item_ids + list(assessment.get("selected_item_ids") or []))
    )
    planned_forms = list(assessment.get("planned_form_item_ids") or [])
    if (
        max_attempts == 2
        and attempt_no == 1
        and len(items) == item_count * max_attempts
    ):
        planned_forms = _plan_two_fresh_assessment_forms(
            items,
            item_count=item_count,
        )
    if len(planned_forms) >= attempt_no:
        items_by_id = {str(item["item_id"]): item for item in items}
        selected_items = [
            items_by_id[item_id]
            for item_id in planned_forms[attempt_no - 1]
            if item_id in items_by_id
        ]
    else:
        selected_items = _select_chapter_assessment_items(
            items,
            item_count=item_count,
            attempt_no=attempt_no,
            used_item_ids=set(used_item_ids),
        )
    selected_item_ids = [str(item["item_id"]) for item in selected_items]
    requires_fresh_form = (
        max_attempts >= 3 or len(items) >= item_count * max_attempts
    )
    if (
        len(selected_item_ids) != item_count
        or (
            requires_fresh_form
            and set(selected_item_ids).intersection(used_item_ids)
        )
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
            "planned_form_item_ids": planned_forms,
        }
    )
    updated["chapter_assessment"] = assessment
    updated["remediation_queue"] = []
    updated.pop("remediation_mode", None)
    updated.pop("assessment_remediation_remaining_skill_ids", None)
    updated["phase"] = "chapter_check"
    updated["status"] = "active"
    return updated


def _plan_two_fresh_assessment_forms(
    items: list[dict[str, Any]],
    *,
    item_count: int,
) -> list[list[str]]:
    """Partition a two-attempt bank into fresh forms that each cover every skill."""

    if len(items) != item_count * 2:
        raise ValueError("chapter_assessment_two_form_bank_size_invalid")

    item_skill_ids = [
        {
            str(skill_id)
            for skill_id in item.get("skill_ids") or []
            if str(skill_id)
        }
        for item in items
    ]
    required_skill_ids = set().union(*item_skill_ids) if item_skill_ids else set()
    remaining_counts = {
        skill_id: sum(skill_id in skills for skills in item_skill_ids)
        for skill_id in required_skill_ids
    }
    if any(count < 2 for count in remaining_counts.values()):
        raise ValueError("chapter_assessment_fresh_form_unavailable")

    selected: list[int] = []
    selected_set: set[int] = set()
    dead_ends: set[tuple[int, ...]] = set()

    def can_select(index: int) -> bool:
        return all(
            remaining_counts[skill_id] > 1
            for skill_id in item_skill_ids[index]
        )

    def search(covered_skill_ids: set[str]) -> tuple[int, ...] | None:
        state_key = tuple(sorted(selected_set))
        if state_key in dead_ends:
            return None
        if len(selected) == item_count:
            if covered_skill_ids == required_skill_ids:
                return tuple(selected)
            dead_ends.add(state_key)
            return None

        available = [
            index
            for index in range(len(items))
            if index not in selected_set and can_select(index)
        ]
        slots_left = item_count - len(selected)
        if len(available) < slots_left:
            dead_ends.add(state_key)
            return None

        missing_skill_ids = required_skill_ids - covered_skill_ids
        if missing_skill_ids:
            candidates_by_skill = {
                skill_id: [
                    index
                    for index in available
                    if skill_id in item_skill_ids[index]
                ]
                for skill_id in missing_skill_ids
            }
            if any(not candidates for candidates in candidates_by_skill.values()):
                dead_ends.add(state_key)
                return None
            next_skill_id = min(
                missing_skill_ids,
                key=lambda skill_id: (
                    len(candidates_by_skill[skill_id]),
                    skill_id,
                ),
            )
            candidates = candidates_by_skill[next_skill_id]
        else:
            candidates = available

        def priority(index: int) -> tuple[int, int, str]:
            skills = item_skill_ids[index]
            coverage_gain = len(skills.intersection(missing_skill_ids))
            reserve = min(
                (remaining_counts[skill_id] - 1 for skill_id in skills),
                default=len(items),
            )
            return (-coverage_gain, -reserve, str(items[index]["item_id"]))

        for index in sorted(candidates, key=priority):
            selected.append(index)
            selected_set.add(index)
            for skill_id in item_skill_ids[index]:
                remaining_counts[skill_id] -= 1
            result = search(covered_skill_ids | item_skill_ids[index])
            if result is not None:
                return result
            for skill_id in item_skill_ids[index]:
                remaining_counts[skill_id] += 1
            selected_set.remove(index)
            selected.pop()

        dead_ends.add(state_key)
        return None

    first_form_indices = search(set())
    if first_form_indices is None:
        raise ValueError("chapter_assessment_fresh_form_unavailable")
    first_form_set = set(first_form_indices)
    second_form_indices = [
        index for index in range(len(items)) if index not in first_form_set
    ]
    if len(second_form_indices) != item_count:
        raise ValueError("chapter_assessment_fresh_form_unavailable")

    return [
        [str(items[index]["item_id"]) for index in first_form_indices],
        [str(items[index]["item_id"]) for index in second_form_indices],
    ]


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
    if not _chapter_assessment_content_is_fresh(
        state.get("hot_session_memory"),
        item,
    ):
        raise ValueError("chapter_assessment_fresh_form_unavailable")
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
        "skill_ids": list(activity.get("skill_ids") or []),
        "correct": bool(answer_evaluation["correct"]),
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": _sanitize_persisted_criteria(answer_evaluation["criteria"]),
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
    updated["hot_session_memory"] = _remember_activity_fingerprints(
        updated.get("hot_session_memory"), activity
    )

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
        _set_feedback_v2(updated, {
            "outcome": "chapter_check_answer_saved",
            "feedback_type": "chapter_check_progress",
            "correct": None,
            "scored": False,
            "what_worked": "Your answer is saved.",
            "criterion_gap": None,
            "misconception_tag": None,
            "next_support": (
                "Keep going; results appear after the chapter check."
            ),
            "retry_policy": "continue_chapter_check",
            "allowed_next_actions": ["answer_next_activity"],
            "response_excerpt": "",
        })
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


def _v2_authored_remediation_skill_ids(level: dict[str, Any]) -> set[str]:
    checks = level.get("checks") or {}
    return {
        str(skill_id)
        for kind in _V2_SUPPORT_KINDS + ("masterclass",)
        if isinstance(checks.get(kind), dict)
        for skill_id in (checks[kind].get("knowledge_components") or [])
    }


def _assessment_remediation_skill_ids(level: dict[str, Any]) -> set[str]:
    if level.get("teaching_steps"):
        return _v2_authored_remediation_skill_ids(level)
    return {str(skill_id) for skill_id in level.get("skill_ids") or []}


def _assessment_remediation_support_plan(
    state: dict[str, Any],
    skill_ids: list[str],
) -> dict[str, Any]:
    updated = dict(state)
    remediation_skill_ids = list(dict.fromkeys(str(item) for item in skill_ids))
    assessment = updated.get("chapter_assessment")
    attempt_count = (
        int(assessment.get("attempt_no") or 0)
        if isinstance(assessment, dict)
        else 0
    )
    updated["phase"] = "needs_support"
    updated["status"] = "active"
    updated["remediation_queue"] = []
    updated.pop("remediation_mode", None)
    updated.pop("assessment_remediation_remaining_skill_ids", None)
    updated["support_required"] = {
        "reason": "authored_remediation_unavailable",
        "attempt_count": attempt_count,
        "weak_skill_ids": remediation_skill_ids,
        "remediation_skill_ids": remediation_skill_ids,
        "focus": _assessment_support_focus(updated, remediation_skill_ids),
        "history": list(updated.get("assessment_support_history") or []),
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
        try:
            plan, targeted_skill_ids, deferred_skill_ids = (
                _build_assessment_revision_plan(
                    levels,
                    weak_skill_ids,
                    skill_scores=skill_scores,
                    priority_skill_ids=priority_skill_ids,
                )
            )
        except ValueError as exc:
            if (
                str(exc) != "chapter_assessment_remediation_level_missing"
                and not str(exc).startswith("chapter_assessment_revision_")
            ):
                raise
            updated["levels"] = levels
            return _assessment_remediation_support_plan(updated, weak_skill_ids)
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

    weak_skill_ids = list(dict.fromkeys(str(item) for item in weak_skill_ids))
    weak = set(weak_skill_ids)
    remediation_queue = []
    uncovered = set(weak)
    for level in levels:
        covered_here = uncovered.intersection(
            _assessment_remediation_skill_ids(level)
        )
        if not covered_here:
            continue
        remediation_queue.append(str(level["level_id"]))
        uncovered.difference_update(covered_here)
    if not remediation_queue or uncovered:
        updated["levels"] = levels
        return _assessment_remediation_support_plan(updated, weak_skill_ids)
    start_step = "revision_level_1" if mode == "expanded_revision" else "masterclass"
    updated["assessment_remediation_remaining_skill_ids"] = weak_skill_ids
    for level in levels:
        if level["level_id"] == remediation_queue[0]:
            if level.get("teaching_steps"):
                configured = _configure_v2_assessment_remediation(
                    level,
                    targeted_skill_ids=weak_skill_ids,
                )
                level.clear()
                level.update(configured)
            else:
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
    if level.get("teaching_steps"):
        level = _configure_v2_assessment_remediation(
            level,
            targeted_skill_ids=list(entry.get("targeted_skill_ids") or []),
            forced_support_kind=str(entry["kind"]),
        )
    else:
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


def _public_source_reference(
    chapter: dict[str, Any],
    anchor_ids: list[str],
) -> dict[str, Any] | None:
    """Expose source location metadata without ever exposing textbook text."""

    wanted = {str(anchor_id) for anchor_id in anchor_ids if str(anchor_id)}
    if not wanted:
        return None
    anchors_by_id = {
        str(anchor.get("anchor_id") or ""): anchor
        for anchor in chapter.get("source_anchors") or []
        if isinstance(anchor, dict) and str(anchor.get("anchor_id") or "")
    }
    public_anchors = []
    for anchor_id in anchor_ids:
        anchor = anchors_by_id.get(str(anchor_id))
        if not anchor:
            continue
        public_anchors.append(
            {
                "anchor_id": str(anchor["anchor_id"]),
                "section_label": str(anchor.get("section_label") or ""),
                "page_start": int(anchor.get("page_start") or 0),
                "page_end": int(anchor.get("page_end") or 0),
                "source_url": str(anchor.get("source_url") or ""),
                "coverage_treatment": str(anchor.get("coverage_treatment") or ""),
            }
        )
    if not public_anchors:
        return None
    return {
        "book_title": str(chapter.get("book_title") or ""),
        "chapter_title": str(chapter.get("title") or ""),
        "anchors": public_anchors,
    }


def _public_activity(
    activity: dict[str, Any] | None,
    *,
    chapter: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not activity:
        return None
    public = {
        "activity_id": activity["activity_id"],
        "level_id": activity["level_id"],
        "kind": activity["kind"],
        "title": activity["title"],
        "focus": activity["focus"],
        "skill_ids": list(activity.get("skill_ids") or []),
        "teaching_block": activity["teaching_block"],
        "passage": activity["passage"],
        "prompt": activity["prompt"],
        "options": _stable_public_options(
            str(activity["activity_id"]),
            list(activity.get("options") or []),
        ) or None,
        "response_mode": activity.get("response_mode") or "short",
        "attempt_no": int(activity.get("attempt_no") or 1),
        "can_answer": True,
    }
    if activity.get("schema_version") == "school-activity-v2":
        public.update(
            schema_version="school-activity-v2",
            phase=activity.get("phase") or activity.get("teaching_phase"),
            entry_mode=activity.get("entry_mode") or "full_cycle",
            support_mode=activity.get("support_mode"),
            interaction_type=activity.get("interaction_type"),
            evidence_role=activity.get("evidence_role"),
            source_anchor_ids=list(activity.get("source_anchor_ids") or []),
            knowledge_components=list(
                activity.get("knowledge_components") or []
            ),
            assessed_skill_ids=list(activity.get("assessed_skill_ids") or []),
            variant=dict(activity.get("variant") or {}),
            lineage=dict(activity.get("lineage") or {}),
        )
        source_reference = _public_source_reference(
            chapter or {},
            list(activity.get("source_anchor_ids") or []),
        )
        if source_reference is not None:
            public["source_reference"] = source_reference
    return public


def _stable_public_options(activity_id: str, options: list[str]) -> list[str]:
    indexed_options = list(enumerate(str(option) for option in options))
    indexed_options.sort(
        key=lambda item: hashlib.sha256(
            f"{activity_id}\0{item[0]}\0{item[1]}".encode("utf-8")
        ).digest()
    )
    return [option for _, option in indexed_options]


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
    return accepted_answer_matches(
        answer,
        list(activity.get("accepted_answers") or []),
    )


def evaluate_deterministic_answer(
    activity: dict[str, Any],
    answer: str,
) -> dict[str, Any]:
    if (
        activity.get("schema_version") == "school-activity-v2"
        and activity.get("interaction_type") == "continue"
    ):
        return {
            "correct": True,
            "score": 0.0,
            "confidence": 1.0,
            "criteria": [],
            "missing_criteria": [],
            "misconception_tags": [],
            "blockers": [],
            "language_detected": _detect_answer_language(answer),
            "model_score": None,
            "scored": False,
        }
    if activity.get("grading_mode") in {
        "selected_option",
        "exact_text",
        "punctuation_symbol",
        "ordered_slots",
    }:
        result = grade_typed_school_answer(activity, answer)
        mapped_misconceptions = (
            _wrong_answer_misconception_tags(activity, answer)
            if not result.correct
            else []
        )
        return {
            "correct": result.correct,
            "score": result.score,
            "confidence": result.confidence,
            "criteria": [criterion.model_dump() for criterion in result.criteria],
            "missing_criteria": list(result.missing_criteria),
            "misconception_tags": mapped_misconceptions,
            "blockers": list(result.blockers)
            if result.blockers
            else ([] if result.correct else ["curriculum_gap"]),
            "language_detected": _detect_answer_language(answer),
            "model_score": None,
        }
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


def _wrong_answer_misconception_tags(
    activity: dict[str, Any],
    answer: str,
) -> list[str]:
    normalized_answer = _normalize(answer)
    for option, tags in (
        activity.get("wrong_answer_misconception_tags") or {}
    ).items():
        if _normalize(str(option)) == normalized_answer:
            return list(dict.fromkeys(str(tag) for tag in tags))
    return []


def _bounded_remediation_tags(
    activity: dict[str, Any],
    answer_evaluation: dict[str, Any],
    *,
    correct: bool,
) -> list[str]:
    if correct:
        return []
    authored_tags = [
        str(tag) for tag in activity.get("target_misconception_tags") or []
    ]
    allowed_tags = set(authored_tags)
    evaluated_tags = [
        str(tag)
        for tag in answer_evaluation.get("misconception_tags") or []
        if str(tag) in allowed_tags
    ]
    criterion_mapping = activity.get("criterion_misconception_tags") or {}
    criterion_tags = [
        str(tag)
        for criterion_id in answer_evaluation.get("missing_criteria") or []
        for tag in criterion_mapping.get(str(criterion_id), [])
        if str(tag) in allowed_tags
    ]
    specific_tags = list(dict.fromkeys(evaluated_tags + criterion_tags))
    if specific_tags:
        return specific_tags
    return authored_tags if len(authored_tags) == 1 else []


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
_AUTHORED_PREFIX_NEGATION_WORDS = frozenset(
    _NEGATION_WORDS
    | {
        "hadn",
        "hasn",
        "haven",
        "mightn",
        "mustn",
        "needn",
        "shan",
        "shouldn",
    }
)
_AUTHORED_HARD_BOUNDARY_RE = re.compile(r"[.!?;]+")
_AUTHORED_CONTINUATION_BOUNDARY_RE = re.compile(r"[:\n]+")
_AUTHORED_COMMA_RE = re.compile(",")
_AUTHORED_COORDINATORS = frozenset(
    {"and", "but", "however", "then", "yet"}
)
_AUTHORED_PREDICATE_COORDINATORS = frozenset(
    {"but", "however", "then", "yet"}
)
_AUTHORED_CLAUSE_SUBJECT_CONNECTORS = frozenset(
    {"although", "and", "because", "whereas", "while"}
)
_AUTHORED_PROPOSITION_CONNECTORS = (
    _AUTHORED_CLAUSE_SUBJECT_CONNECTORS | _AUTHORED_PREDICATE_COORDINATORS
)
_AUTHORED_CLAUSE_LEADERS = frozenset(
    {"also", "instead", "now", "still", "then"}
)
_AUTHORED_SUBJECT_PRONOUNS = frozenset(
    {"he", "i", "it", "she", "they", "we", "you"}
)
_AUTHORED_KNOWN_PROPER_SUBJECTS = frozenset({"isha"})
_AUTHORED_SUBJECT_DETERMINERS = frozenset(
    {"a", "an", "that", "the", "these", "this", "those"}
)
_AUTHORED_FINITE_AUXILIARIES = frozenset(
    {
        "am",
        "are",
        "can",
        "could",
        "did",
        "do",
        "does",
        "had",
        "has",
        "have",
        "is",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "was",
        "were",
        "will",
        "would",
    }
)
_AUTHORED_WITHOUT_MODIFIERS = frozenset(
    {"actually", "completely", "even", "ever", "fully", "properly", "really"}
)
_AUTHORED_POSTPOSED_DENIAL_RE = re.compile(
    r"\b(?:assertion|claim|idea|report|statement)\s+that\b.*"
    r"\b(?:(?:is|was)\s+not|(?:isn|wasn)\s+t)\s+true\b"
)
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
    "wipe": "clean",
    "wiped": "clean",
    "wipes": "clean",
    "wiping": "clean",
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


def _concept_phrase_spans(
    text: str,
    phrase: str,
    *,
    enforce_polarity: bool = True,
) -> list[tuple[int, int]]:
    answer_words = text.split()
    phrase_words = phrase.split()
    expected_has_negation = _has_negation(phrase_words)
    expected_tokens = [
        _concept_token(word)
        for word in phrase_words
        if word not in _CONCEPT_STOP_WORDS
    ]

    def allowed(span: tuple[int, int]) -> bool:
        if not enforce_polarity or expected_has_negation:
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


def _first_word_at_or_after(
    source_words: list[re.Match[str]],
    offset: int,
) -> int:
    return next(
        (
            index
            for index, word_match in enumerate(source_words)
            if word_match.start() >= offset
        ),
        len(source_words),
    )


def _authored_clause_lookahead_limit(
    answer: str,
    source_words: list[re.Match[str]],
    offset: int,
) -> int:
    boundary_offsets = [len(answer)]
    for pattern in (
        _AUTHORED_HARD_BOUNDARY_RE,
        _AUTHORED_CONTINUATION_BOUNDARY_RE,
    ):
        if match := pattern.search(answer, offset):
            boundary_offsets.append(match.start())
    return _first_word_at_or_after(source_words, min(boundary_offsets))


def _starts_authored_clause(
    source_words: list[re.Match[str]],
    word_values: list[str],
    start: int,
    subject_limit: int,
    *,
    predicate_limit: int | None = None,
) -> bool:
    if predicate_limit is None:
        predicate_limit = subject_limit
    cursor = start
    while (
        cursor < subject_limit
        and word_values[cursor] in _AUTHORED_CLAUSE_LEADERS
    ):
        cursor += 1
    if cursor >= subject_limit:
        return False
    if word_values[cursor] in _AUTHORED_SUBJECT_PRONOUNS:
        return True
    if word_values[cursor] in _AUTHORED_SUBJECT_DETERMINERS:
        if cursor + 1 >= subject_limit:
            return False
        for index in range(cursor + 2, predicate_limit):
            if word_values[index] in _AUTHORED_PROPOSITION_CONNECTORS:
                return False
            surface = word_values[index]
            separator = source_words[index].string[
                source_words[index - 1].end() : source_words[index].start()
            ]
            if surface in _AUTHORED_FINITE_AUXILIARIES or (
                surface.endswith("ed") and separator != "-"
            ):
                return True
        return False
    if source_words[cursor].group(0)[:1].isupper():
        return True
    return word_values[cursor] in _AUTHORED_KNOWN_PROPER_SUBJECTS


def _authored_clause_subject_boundary_count(
    source_words: list[re.Match[str]],
    word_values: list[str],
    start: int,
    end: int,
    *,
    predicate_limit: int | None = None,
) -> int:
    return sum(
        word_values[index] in _AUTHORED_CLAUSE_SUBJECT_CONNECTORS
        and _starts_authored_clause(
            source_words,
            word_values,
            index + 1,
            end,
            predicate_limit=predicate_limit,
        )
        for index in range(start + 1, end)
    )


def _has_authored_negation(words: list[str]) -> bool:
    return bool(
        _AUTHORED_PREFIX_NEGATION_WORDS.intersection(words)
        or any(left == "can" and right == "t" for left, right in zip(words, words[1:]))
    )


def _authored_target_surface_is_finite(
    source_words: list[re.Match[str]],
    target_start: int,
) -> bool:
    surface = source_words[target_start].group(0).casefold()
    return surface.endswith("ed") or (
        len(surface) > 3 and surface.endswith("s") and not surface.endswith("ss")
    )


def _authored_coordinator_starts_predicate(
    source_words: list[re.Match[str]],
    word_values: list[str],
    index: int,
    limit: int,
    *,
    scope_start: int,
    concept_spans: list[tuple[int, int]],
    target_start: int,
) -> bool:
    coordinator = word_values[index]
    if coordinator in _AUTHORED_PREDICATE_COORDINATORS:
        return True
    if coordinator != "and":
        return False
    if _starts_authored_clause(
        source_words,
        word_values,
        index + 1,
        limit,
        predicate_limit=(
            min(limit + 1, len(source_words))
            if target_start == limit
            else limit
        ),
    ):
        return True
    target_started_before_coordinator = any(
        scope_start <= span_start < index for span_start, _ in concept_spans
    )
    return (
        _has_authored_negation(word_values[scope_start:index])
        and not target_started_before_coordinator
        and target_start > index
        and _authored_target_surface_is_finite(source_words, target_start)
    )


def _authored_proposition_bounds(
    answer: str,
    source_words: list[re.Match[str]],
    start: int,
    end: int,
    *,
    concept_spans: list[tuple[int, int]],
) -> tuple[int, int, int, int]:
    word_values = [word.group(0).casefold() for word in source_words]
    concept_start = source_words[start].start()
    concept_end = source_words[end - 1].end()
    hard_start = max(
        (
            match.end()
            for match in _AUTHORED_HARD_BOUNDARY_RE.finditer(
                answer,
                0,
                concept_start,
            )
        ),
        default=0,
    )
    hard_end_match = next(
        _AUTHORED_HARD_BOUNDARY_RE.finditer(answer, concept_end),
        None,
    )
    hard_end = hard_end_match.start() if hard_end_match else len(answer)
    scope_start = _first_word_at_or_after(source_words, hard_start)
    scope_end = _first_word_at_or_after(source_words, hard_end)

    start_candidates = [scope_start]
    for boundary in _AUTHORED_CONTINUATION_BOUNDARY_RE.finditer(
        answer,
        hard_start,
        concept_start,
    ):
        candidate = _first_word_at_or_after(source_words, boundary.end())
        if candidate < start and _starts_authored_clause(
            source_words,
            word_values,
            candidate,
            start,
            predicate_limit=min(start + 1, len(source_words)),
        ):
            start_candidates.append(candidate)
    for comma in _AUTHORED_COMMA_RE.finditer(answer, hard_start, concept_start):
        candidate = _first_word_at_or_after(source_words, comma.end())
        if candidate < start and _starts_authored_clause(
            source_words,
            word_values,
            candidate,
            start,
            predicate_limit=min(start + 1, len(source_words)),
        ):
            start_candidates.append(candidate)
    for index in range(scope_start, start):
        if (
            word_values[index] in _AUTHORED_COORDINATORS
            and _authored_coordinator_starts_predicate(
                source_words,
                word_values,
                index,
                start,
                scope_start=max(start_candidates),
                concept_spans=concept_spans,
                target_start=start,
            )
        ):
            start_candidates.append(index + 1)
    scope_start = max(start_candidates)

    end_candidates: list[tuple[int, int]] = []
    for boundary in _AUTHORED_CONTINUATION_BOUNDARY_RE.finditer(
        answer,
        concept_end,
        hard_end,
    ):
        candidate = _first_word_at_or_after(source_words, boundary.end())
        if candidate < scope_end and _starts_authored_clause(
            source_words,
            word_values,
            candidate,
            scope_end,
        ):
            end_candidates.append((boundary.start(), candidate))
    for comma in _AUTHORED_COMMA_RE.finditer(answer, concept_end, hard_end):
        candidate = _first_word_at_or_after(source_words, comma.end())
        if candidate < scope_end and _starts_authored_clause(
            source_words,
            word_values,
            candidate,
            scope_end,
        ):
            end_candidates.append((comma.start(), candidate))
    for index in range(end, scope_end):
        if (
            word_values[index] in _AUTHORED_COORDINATORS
            and _authored_coordinator_starts_predicate(
                source_words,
                word_values,
                index,
                scope_end,
                scope_start=scope_start,
                concept_spans=concept_spans,
                target_start=start,
            )
        ):
            end_candidates.append((source_words[index].start(), index))
    if end_candidates:
        hard_end, scope_end = min(end_candidates)

    scope_start_char = (
        source_words[scope_start].start() if scope_start < len(source_words) else 0
    )
    return scope_start, scope_end, scope_start_char, hard_end


def _authored_concept_span_is_affirmative(
    answer: str,
    source_words: list[re.Match[str]],
    start: int,
    end: int,
    *,
    allowed_clause_subject_boundaries: int,
    concept_spans: list[tuple[int, int]],
    allow_expected_negation: bool = False,
) -> bool:
    word_values = [word.group(0).casefold() for word in source_words]
    span_content_start = source_words[start].end()
    span_content_end = source_words[end - 1].start()
    predicate_limit = _authored_clause_lookahead_limit(
        answer,
        source_words,
        source_words[end - 1].end(),
    )
    if (
        _AUTHORED_HARD_BOUNDARY_RE.search(
            answer,
            span_content_start,
            span_content_end,
        )
        or _AUTHORED_CONTINUATION_BOUNDARY_RE.search(
            answer,
            span_content_start,
            span_content_end,
        )
        or any(
            word_values[index] in _AUTHORED_PREDICATE_COORDINATORS
            for index in range(start + 1, end)
        )
        or _authored_clause_subject_boundary_count(
            source_words,
            word_values,
            start,
            end,
            predicate_limit=predicate_limit,
        )
        > allowed_clause_subject_boundaries
    ):
        return False
    scope_start, scope_end, scope_start_char, scope_end_char = (
        _authored_proposition_bounds(
            answer,
            source_words,
            start,
            end,
            concept_spans=concept_spans,
        )
    )
    prefix = word_values[scope_start:start]
    matched_words = word_values[start:end]
    proposition = word_values[scope_start:scope_end]
    prefix_negates_claim = _has_authored_negation(prefix)
    matched_phrase_is_negative = _has_authored_negation(matched_words)
    # A child may legitimately state a negative safety claim, for example
    # "the helmet may not protect the cyclist." That is evidence only when the
    # authored alias itself includes the negation. A negation outside that
    # phrase remains a rejection guard against "the helmet may not come off."
    if prefix_negates_claim or (
        matched_phrase_is_negative and not allow_expected_negation
    ):
        return False
    if allow_expected_negation and not matched_phrase_is_negative:
        return False
    if "neither" in prefix and "nor" in proposition:
        return False

    concept_word = word_values[start]
    without_index = next(
        (
            index
            for index in range(start - 1, scope_start - 1, -1)
            if word_values[index] == "without"
        ),
        None,
    )
    if (
        concept_word.endswith("ing")
        and without_index is not None
        and all(
            word in _AUTHORED_WITHOUT_MODIFIERS
            for word in word_values[without_index + 1 : start]
        )
    ):
        return False

    proposition_text = _normalize(answer[scope_start_char:scope_end_char])
    return not _AUTHORED_POSTPOSED_DENIAL_RE.search(proposition_text)


def _authored_concept_evidence_quote(answer: str, alias: str) -> str | None:
    normalized_answer = _normalize(answer)
    spans = _concept_phrase_spans(
        normalized_answer,
        _normalize(alias),
        enforce_polarity=False,
    )
    if not spans:
        return None
    raw_words = list(re.finditer(r"[a-z0-9]+", answer, flags=re.IGNORECASE))
    alias_words = list(re.finditer(r"[a-z0-9]+", alias, flags=re.IGNORECASE))
    alias_word_values = [word.group(0).casefold() for word in alias_words]
    alias_has_expected_negation = _has_authored_negation(alias_word_values)
    allowed_clause_subject_boundaries = _authored_clause_subject_boundary_count(
        alias_words,
        alias_word_values,
        0,
        len(alias_words),
    )
    for start, end in sorted(spans, key=lambda span: (span[1] - span[0], span[0])):
        if start < 0 or end <= start or end > len(raw_words):
            continue
        if not _authored_concept_span_is_affirmative(
            answer,
            raw_words,
            start,
            end,
            allowed_clause_subject_boundaries=allowed_clause_subject_boundaries,
            concept_spans=spans,
            allow_expected_negation=alias_has_expected_negation,
        ):
            continue
        return answer[raw_words[start].start() : raw_words[end - 1].end()]
    return None


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


def accepted_answer_matches(answer: str, accepted_answers: list[str]) -> bool:
    """Accept an authored answer phrase inside a non-negated full response."""

    cleaned_answer = _normalize(answer)
    return any(
        _accepted_phrase_matches(cleaned_answer, _normalize(expected))
        for expected in accepted_answers
    )


def _open_answer_preflight(activity: dict[str, Any], answer: str) -> bool:
    min_response_words = int(activity.get("min_response_words") or 0)
    if min_response_words and len(_normalize(answer).split()) < min_response_words:
        return False
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
    # Persisted legacy state can outlive the content validator. Explicitly typed
    # choices and exact checks stay deterministic even if an obsolete snapshot
    # still carries an LLM evaluation marker.
    if activity.get("grading_mode") in {
        "selected_option",
        "exact_text",
        "punctuation_symbol",
        "ordered_slots",
    }:
        return None
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
    strict_open = activity.get("grading_mode") == "strict_open_rubric"
    strict_validated = (
        validate_school_open_evaluation(
            evaluation,
            context=school_open_context_from_activity(activity, answer),
        )
        if strict_open
        else None
    )
    initial_backend_blockers = set(
        strict_validated.backend_blockers if strict_validated is not None else ()
    )
    if strict_validated is not None:
        evaluation = strict_validated.evaluation
    authored_criteria = list(activity.get("rubric_criteria") or [])
    authored_ids = [str(criterion.get("id") or "") for criterion in authored_criteria]
    evaluated_ids = [criterion.id for criterion in evaluation.criteria]
    if (
        activity.get("evaluation_mode") != "llm_rubric"
        or evaluation.schema_version
        != (
            OPEN_RUBRIC_SCHEMA_VERSION
            if strict_open
            else RUBRIC_SCHEMA_VERSION
        )
        or evaluation.item_id != activity.get("activity_id")
        or set(evaluation.skill_ids) != set(activity.get("skill_ids") or [])
        or len(evaluation.skill_ids) != len(set(evaluation.skill_ids))
        or not authored_ids
        or len(authored_ids) != len(set(authored_ids))
        or evaluated_ids != authored_ids
        or len(evaluated_ids) != len(set(evaluated_ids))
    ):
        raise ValueError("invalid_open_answer_evaluation_contract")

    if not strict_open:
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
                        activity=activity,
                        passage=passage,
                        answer=answer,
                        criterion_by_id=canonical_by_id,
                    )
                    for criterion in evaluation.criteria
                ]
            }
        )
        if strict_open:
            strict_validated = validate_school_open_evaluation(
                evaluation,
                context=school_open_context_from_activity(activity, answer),
            )
            evaluation = strict_validated.evaluation

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
    # A strict-open provider may evaluate authored criteria, but it cannot add
    # a free-form blocker that changes progression. Those claims are too easy
    # to misapply to a child who necessarily repeats a few passage words.
    # Durable strict blockers are recomputed from backend-owned context below.
    provider_blockers = () if strict_open else evaluation.blockers
    blockers = [
        blocker
        for blocker in provider_blockers
        if blocker not in initial_backend_blockers
        and (blocker != "needs_human_review" or not human_review_resolved)
    ]
    if strict_validated is not None:
        blockers.extend(strict_validated.backend_blockers)
    if (
        not strict_open
        and evaluation.needs_human_review
        and not human_review_resolved
        and "needs_human_review" not in blockers
    ):
        blockers.append("needs_human_review")
    if (
        activity.get("certifying_language") == "en"
        and evaluation.language_detected != "en"
    ):
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
    activity: dict[str, Any],
    passage: str,
    answer: str,
    criterion_by_id: dict[str, Any],
) -> Any:
    if criterion.id == "complete_response":
        inference = criterion_by_id.get("plausible_inference")
        clue = criterion_by_id.get("relevant_text_clue")
        complete_inference = bool(
            inference
            and clue
            and inference.met
            and clue.met
            and len(_normalize(answer).split()) >= 5
            and _open_answer_preflight(activity, answer)
            and inference_clue_is_explicitly_linked(
                passage=passage,
                answer=answer,
                inference_quote=inference.evidence_quote,
                clue_quote=clue.evidence_quote,
            )
        )
        if complete_inference:
            return criterion.model_copy(
                update={
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer.strip(),
                }
            )
        return criterion
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
    detail_match = re.fullmatch(r"(.+):detail_[0-9]+", criterion.id)
    if detail_match and not criterion.met:
        parent = criterion_by_id.get(detail_match.group(1))
        normalized_answer = _normalize(answer)
        concept_slots = [
            slot
            for slot in activity.get("concept_slots") or []
            if isinstance(slot, dict) and slot.get("id")
        ]
        all_authored_slots_visible = bool(concept_slots) and all(
            any(
                _concept_phrase_spans(normalized_answer, _normalize(str(alias)))
                for alias in slot.get("any_of") or []
                if str(alias).strip()
            )
            for slot in concept_slots
        )
        if (
            parent is not None
            and parent.met
            and parent.quality >= 0.6
            and all_authored_slots_visible
            and _open_answer_preflight(activity, answer)
        ):
            return criterion.model_copy(
                update={
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer.strip(),
                }
            )
        return criterion
    authored_criterion = next(
        (
            item
            for item in activity.get("rubric_criteria") or []
            if isinstance(item, dict)
            and str(item.get("id") or "") == criterion.id
        ),
        None,
    )
    authored_min_quality = float(
        (authored_criterion or {}).get("min_quality", 0.6)
    )
    if not criterion.met or criterion.quality < authored_min_quality:
        authored_slot = next(
            (
                slot
                for slot in activity.get("concept_slots") or []
                if isinstance(slot, dict) and str(slot.get("id") or "") == criterion.id
            ),
            None,
        )
        authored_evidence_quote = next(
            (
                quote
                for alias in (authored_slot or {}).get("any_of") or []
                if str(alias).strip()
                and authored_evidence_can_prove_criterion(
                    str((authored_slot or {}).get("description") or ""),
                    str(alias),
                )
                and (
                    quote := _authored_concept_evidence_quote(
                        answer,
                        str(alias),
                    )
                )
            ),
            None,
        )
        if authored_evidence_quote and _open_answer_preflight(activity, answer):
            return criterion.model_copy(
                update={
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": authored_evidence_quote,
                }
            )
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
        "language_detected": "unknown",
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
    first_person_markers = {"i", "me", "my", "mine", "we", "us", "our", "ours"}
    if require_first_person and not first_person_markers.intersection(words):
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
