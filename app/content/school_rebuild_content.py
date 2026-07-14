"""Approved live-chapter loader for the rebuilt School tutor."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from app.config import get_settings
from app.content.school.source_map_compat import (
    load_beta_source_map as load_ncert_source_map,
)
from app.content.school.standards import locked_english_taxonomy
from app.content.school_rebuild_schema import LiveSchoolChapter


LIVE_CHAPTER_ROOT = Path(__file__).resolve().parent / "school_rebuild_chapters"
_QA_DEFAULT_ENABLED_ENVS = {"dev", "development", "local", "test", "ci"}
_CLASS_DIRECTORY_PATTERN = re.compile(r"class_(\d+)$")
_NON_LIVE_APPROVAL_ERRORS = (
    "live_chapter_not_approved:",
    "live_chapter_not_human_approved:",
)


def qa_live_content_enabled() -> bool:
    explicit = os.environ.get("SCHOOL_REBUILD_ALLOW_QA_CONTENT")
    if explicit is not None:
        return explicit == "1"
    app_env = os.environ.get("APP_ENV")
    if app_env is None:
        app_env = get_settings().app_env
    app_env = app_env.strip().lower()
    return app_env in _QA_DEFAULT_ENABLED_ENVS


def _collect_authored_skill_ids(chapter: LiveSchoolChapter) -> set[str]:
    skill_ids = {
        skill_id for level in chapter.levels for skill_id in level.skill_ids
    }
    if chapter.chapter_assessment is not None:
        skill_ids.update(
            skill_id
            for item in chapter.chapter_assessment.items
            for skill_id in item.skill_ids
        )
    return skill_ids


def load_live_chapter_file(path: Path) -> LiveSchoolChapter:
    with path.open("r", encoding="utf-8") as handle:
        chapter = LiveSchoolChapter.model_validate(json.load(handle))
    taxonomy = locked_english_taxonomy()
    known_skill_ids = taxonomy.skill_ids()
    unknown = sorted(
        skill_id
        for skill_id in _collect_authored_skill_ids(chapter)
        if skill_id not in known_skill_ids
    )
    if unknown:
        raise ValueError(f"unknown_live_chapter_skill:{','.join(unknown)}")
    class_match = _CLASS_DIRECTORY_PATTERN.fullmatch(path.parent.name)
    if class_match is not None and chapter.source_anchors is not None:
        class_no = int(class_match.group(1))
        out_of_band = sorted(
            skill_id
            for skill_id in _collect_authored_skill_ids(chapter)
            if not (
                taxonomy.get(skill_id).class_min
                <= class_no
                <= taxonomy.get(skill_id).class_max
            )
        )
        if out_of_band:
            raise ValueError(
                f"out_of_band_live_chapter_skill:{','.join(out_of_band)}"
            )
    if chapter.calculated_runtime_sha256() != chapter.runtime_sha256:
        raise ValueError(f"live_chapter_runtime_hash_mismatch:{chapter.chapter_id}")
    return chapter


def load_approved_live_chapter(
    subject_id: str,
    class_no: int,
    chapter_id: str,
) -> dict:
    path = LIVE_CHAPTER_ROOT / subject_id / f"class_{class_no}" / f"{chapter_id}.json"
    chapter = load_live_chapter_file(path)
    if chapter.chapter_id != chapter_id:
        raise ValueError(
            f"live_chapter_id_mismatch:{chapter_id}:{chapter.chapter_id}"
        )
    if chapter.approval_status == "draft":
        raise ValueError(f"live_chapter_not_approved:{chapter_id}")
    if chapter.approval_status == "qa_approved" and not qa_live_content_enabled():
        raise ValueError(f"live_chapter_not_human_approved:{chapter_id}")

    source_map = load_ncert_source_map(subject_id, class_no)
    source_entry = next(
        (
            entry
            for entry in source_map.get("chapters") or []
            if str(entry.get("chapter_id") or "") == chapter_id
        ),
        None,
    )
    if not source_entry:
        raise ValueError(f"live_chapter_missing_from_source_map:{chapter_id}")
    if (
        int(source_entry.get("chapter_no") or 0) != chapter.chapter_no
        or str(source_entry.get("chapter_title") or "").strip() != chapter.title
    ):
        raise ValueError(f"live_chapter_source_map_mismatch:{chapter_id}")
    runtime = chapter.runtime_dict()
    runtime.setdefault("content_version", chapter.runtime_sha256)
    runtime.setdefault(
        "certification_version",
        chapter.certification_version or runtime["content_version"],
    )
    return runtime


def load_approved_live_chapters_for_class(
    subject_id: str,
    class_no: int,
) -> tuple[dict, ...]:
    return _catalog_chapters_for_class(subject_id, class_no)


def _catalog_chapters_for_class(
    subject_id: str,
    class_no: int,
) -> tuple[dict, ...]:
    root = LIVE_CHAPTER_ROOT / subject_id / f"class_{class_no}"
    if not root.exists():
        return ()
    chapters = []
    for path in sorted(root.glob("*.json")):
        try:
            chapters.append(
                load_approved_live_chapter(subject_id, class_no, path.stem)
            )
        except ValueError as exc:
            if str(exc).startswith(_NON_LIVE_APPROVAL_ERRORS):
                continue
            raise
    return tuple(sorted(chapters, key=lambda chapter: int(chapter["chapter_no"])))


def approved_school_catalog() -> tuple[dict, ...]:
    """Return only subject/class pairs that have learner-servable live chapters."""
    if not LIVE_CHAPTER_ROOT.exists():
        return ()
    subjects = []
    for subject_root in sorted(path for path in LIVE_CHAPTER_ROOT.iterdir() if path.is_dir()):
        classes = []
        for class_root in sorted(path for path in subject_root.iterdir() if path.is_dir()):
            match = _CLASS_DIRECTORY_PATTERN.fullmatch(class_root.name)
            if not match:
                continue
            class_no = int(match.group(1))
            live_chapters = _catalog_chapters_for_class(subject_root.name, class_no)
            expected_ids = {
                str(chapter.get("chapter_id") or "")
                for chapter in load_ncert_source_map(subject_root.name, class_no).get(
                    "chapters", []
                )
            }
            live_ids = {
                str(chapter.get("chapter_id") or "") for chapter in live_chapters
            }
            if expected_ids and live_ids == expected_ids:
                classes.append(class_no)
        if classes:
            subjects.append(
                {
                    "subject_id": subject_root.name,
                    "title": subject_root.name.replace("_", " ").title(),
                    "classes": sorted(classes),
                }
            )
    return tuple(subjects)
