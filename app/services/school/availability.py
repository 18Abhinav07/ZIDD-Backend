"""Fail-closed availability gate for the canonical School runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import logging

from app.config import get_settings


EXPECTED_RELEASE_CHAPTERS = 47
logger = logging.getLogger("zidd.school.availability")


@dataclass(frozen=True)
class SchoolAvailability:
    available: bool
    reason: str | None
    expected_chapters: int
    authored_chapters: int
    human_approved_chapters: int
    release_digest: str | None

    def public_dict(self) -> dict:
        return asdict(self)


def _release_closure() -> SchoolAvailability:
    # Keep disabled School completely outside the Career boot dependency graph.
    # These modules discover and validate the authored corpus at import time.
    from app.content.school.source_map_compat import load_beta_source_map
    from app.content.school_rebuild_content import (
        LIVE_CHAPTER_ROOT,
        load_live_chapter_file,
    )

    expected_ids: set[str] = set()
    for class_no in range(2, 6):
        source_map = load_beta_source_map("english", class_no)
        expected_ids.update(
            str(chapter.get("chapter_id") or "")
            for chapter in source_map.get("chapters") or []
            if str(chapter.get("chapter_id") or "")
        )

    authored_paths = sorted((LIVE_CHAPTER_ROOT / "english").glob("class_*/*.json"))
    authored = [load_live_chapter_file(path) for path in authored_paths]
    authored_ids = {chapter.chapter_id for chapter in authored}
    approved_ids = {
        chapter.chapter_id
        for chapter in authored
        if chapter.approval_status == "human_approved"
    }
    closure_rows = sorted(
        (
            chapter.chapter_id,
            chapter.runtime_sha256,
            chapter.approval_status,
            chapter.reviewed_by,
            chapter.reviewed_at,
            tuple(chapter.review_evidence),
        )
        for chapter in authored
    )
    digest = hashlib.sha256(
        json.dumps(closure_rows, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()

    if (
        len(expected_ids) != EXPECTED_RELEASE_CHAPTERS
        or len(authored_ids) != EXPECTED_RELEASE_CHAPTERS
        or authored_ids != expected_ids
    ):
        return SchoolAvailability(
            False,
            "school_release_chapter_closure_incomplete",
            len(expected_ids),
            len(authored_ids),
            len(approved_ids),
            digest,
        )
    if (
        len(approved_ids) != EXPECTED_RELEASE_CHAPTERS
        or approved_ids != expected_ids
    ):
        return SchoolAvailability(
            False,
            "school_release_human_approval_incomplete",
            len(expected_ids),
            len(authored_ids),
            len(approved_ids),
            digest,
        )
    trusted_digest = get_settings().school_release_attestation_sha256.strip().lower()
    if not trusted_digest or trusted_digest != digest:
        return SchoolAvailability(
            False,
            "school_release_attestation_mismatch",
            len(expected_ids),
            len(authored_ids),
            len(approved_ids),
            digest,
        )
    return SchoolAvailability(
        True,
        None,
        len(expected_ids),
        len(authored_ids),
        len(approved_ids),
        digest,
    )


def school_availability() -> SchoolAvailability:
    settings = get_settings()
    if not settings.school_enabled:
        return SchoolAvailability(
            False,
            "school_disabled",
            EXPECTED_RELEASE_CHAPTERS,
            0,
            0,
            None,
        )
    if settings.app_env.strip().lower() not in {"prod", "production"}:
        return SchoolAvailability(
            True,
            None,
            EXPECTED_RELEASE_CHAPTERS,
            0,
            0,
            None,
        )
    try:
        return _release_closure()
    except Exception:
        logger.exception("School release validation failed; disabling School runtime")
        return SchoolAvailability(
            False,
            "school_release_validation_failed",
            EXPECTED_RELEASE_CHAPTERS,
            0,
            0,
            None,
        )


def unavailable_school_state(
    availability: SchoolAvailability | None = None,
) -> dict:
    availability = availability or school_availability()
    return {
        "available": False,
        "availability_reason": availability.reason,
        "profile_status": "missing",
        "target_class_no": None,
        "subject_id": None,
        "profile_version_id": None,
        "preferred_teaching_language": None,
        "coach_avatar_id": None,
        "coach_palette_id": None,
        "active_flow": "none",
        "active_session_id": None,
        "placement_status": "not_started",
        "unlock_state": "locked",
        "evaluated_class_no": None,
        "active_learning_class_no": None,
        "status": "recoverable_error",
        "next_action": None,
        "next_action_url": "/career",
        "allowed_next_actions": [],
        "learner_message": "School prep is not available in this release.",
        "parent_message": "School prep is not available in this release.",
        "blocked_reason": availability.reason,
    }


__all__ = [
    "EXPECTED_RELEASE_CHAPTERS",
    "SchoolAvailability",
    "school_availability",
    "unavailable_school_state",
]
