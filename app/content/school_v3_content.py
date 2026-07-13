"""School V3 content boundary helpers.

Only approved blueprint JSON files are live. NCERT is used as a structural
source map; teachable passages, prompts, exercises, answers, and rubrics are
Zidd-authored content in the blueprint files.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from app.content.school_v3_schema import (
    ContentGateError,
    LaunchGateResult,
    SchoolV3AssessmentItem,
    SchoolV3ChapterBlueprint,
    SkillTaxonomy,
    public_chapter_payload,
    public_item_payload,
    validate_launch_content_gate,
)
from app.content.school_v3_taxonomy import locked_english_taxonomy


CONTENT_ROOT = Path(__file__).resolve().parent
SOURCE_MAP_ROOT = CONTENT_ROOT / "ncert_source_map"
BLUEPRINT_ROOT = CONTENT_ROOT / "school_v3_blueprints"


def seed_content_enabled() -> bool:
    default = "0" if os.environ.get("APP_ENV", "dev").lower() == "prod" else "1"
    return os.environ.get("SCHOOL_V3_ALLOW_SEED_CONTENT", default) == "1"


def load_ncert_source_map(subject_id: str, class_no: int) -> dict:
    path = SOURCE_MAP_ROOT / subject_id / f"class_{class_no}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("subject_id") != subject_id or payload.get("class_no") != class_no:
        raise ContentGateError(f"source_map_identity_mismatch:{subject_id}:{class_no}")
    return payload


def supported_classes(subject_id: str = "english") -> tuple[int, ...]:
    subject_root = SOURCE_MAP_ROOT / subject_id
    if not subject_root.exists():
        return ()
    class_numbers: list[int] = []
    for path in subject_root.glob("class_*.json"):
        try:
            class_numbers.append(int(path.stem.replace("class_", "")))
        except ValueError:
            continue
    return tuple(sorted(class_numbers))


@lru_cache(maxsize=32)
def approved_chapters_for_class(
    subject_id: str,
    class_no: int,
) -> tuple[SchoolV3ChapterBlueprint, ...]:
    source_map = load_ncert_source_map(subject_id, class_no)
    root = BLUEPRINT_ROOT / subject_id / f"class_{class_no}"
    if not root.exists():
        raise FileNotFoundError(root)

    expected_ids = [str(chapter["chapter_id"]) for chapter in source_map["chapters"]]
    chapters_by_id: dict[str, SchoolV3ChapterBlueprint] = {}
    for path in sorted(root.glob("*.json")):
        if path.name == "REVIEW_STATUS.json":
            continue
        with path.open("r", encoding="utf-8") as handle:
            chapter = SchoolV3ChapterBlueprint.model_validate(json.load(handle))
        if chapter.approval_status == "draft":
            continue
        if chapter.approval_status == "seed" and not seed_content_enabled():
            continue
        if chapter.subject_id != subject_id or chapter.class_no != class_no:
            raise ContentGateError(f"blueprint_identity_mismatch:{path}")
        validate_school_v3_launch_gate(chapter)
        chapters_by_id[chapter.chapter_id] = chapter

    missing = [chapter_id for chapter_id in expected_ids if chapter_id not in chapters_by_id]
    if missing:
        raise ContentGateError(f"approved_blueprint_missing:{','.join(missing)}")
    return tuple(chapters_by_id[chapter_id] for chapter_id in expected_ids)


def all_approved_chapters(subject_id: str = "english") -> tuple[SchoolV3ChapterBlueprint, ...]:
    chapters: list[SchoolV3ChapterBlueprint] = []
    for class_no in supported_classes(subject_id):
        chapters.extend(approved_chapters_for_class(subject_id, class_no))
    return tuple(chapters)


def chapter_for_id(subject_id: str, chapter_id: str) -> SchoolV3ChapterBlueprint | None:
    for chapter in all_approved_chapters(subject_id):
        if chapter.chapter_id == chapter_id:
            return chapter
    return None


def first_chapter_for_class(subject_id: str, class_no: int) -> SchoolV3ChapterBlueprint | None:
    chapters = approved_chapters_for_class(subject_id, class_no)
    return chapters[0] if chapters else None


def validate_school_v3_launch_gate(
    blueprint: SchoolV3ChapterBlueprint,
    taxonomy: SkillTaxonomy | None = None,
) -> LaunchGateResult:
    return validate_launch_content_gate(
        blueprint,
        taxonomy or locked_english_taxonomy(),
    )


def public_school_v3_chapter(blueprint: SchoolV3ChapterBlueprint) -> dict:
    return public_chapter_payload(blueprint)


def public_school_v3_item(item: SchoolV3AssessmentItem) -> dict:
    return public_item_payload(item)
