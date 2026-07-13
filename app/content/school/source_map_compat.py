"""Phase 0 adapter from immutable release modules to beta flat chapter IDs.

Removal boundary: delete this module in Phase 2 when the canonical content
loader owns learner-serving module IDs. It must never become a second title or
ordering authority.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.content.school.release_loader import load_current_release
from app.content.school.release_schema import normalize_release_title


PHASE_2_REMOVAL_BOUNDARY = (
    "Remove in Phase 2 when app.content.school.content_loader serves canonical module IDs."
)
LEGACY_SOURCE_MAP_ROOT = Path(__file__).resolve().parents[1] / "ncert_source_map"

normalize_compat_title = normalize_release_title


def _release_beta_modules(subject_id: str, class_no: int):
    release = load_current_release(subject_id, class_no)
    modules = tuple(
        module
        for unit in release.units
        for module in unit.modules
        if module.kind == "lesson"
        or (class_no == 2 and module.kind == "picture_reading")
    )
    return release, modules


@lru_cache(maxsize=8)
def _validated_projection(subject_id: str, class_no: int) -> tuple[str, tuple[tuple[str, str], ...]]:
    release, modules = _release_beta_modules(subject_id, class_no)
    path = LEGACY_SOURCE_MAP_ROOT / subject_id / f"class_{class_no}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LookupError(f"legacy_school_source_map_not_found:{subject_id}:{class_no}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"legacy_school_source_map_invalid_json:{subject_id}:{class_no}") from exc

    if payload.get("subject_id") != subject_id or payload.get("class_no") != class_no:
        raise ValueError(f"legacy_source_identity_mismatch:{subject_id}:{class_no}")
    if payload.get("book_code") != release.book_code or payload.get("book_title") != release.book_title:
        raise ValueError(f"legacy_source_release_mismatch:{subject_id}:{class_no}")

    chapters = payload.get("chapters")
    if not isinstance(chapters, list) or len(chapters) != len(modules):
        raise ValueError(f"legacy_source_module_count_mismatch:{subject_id}:{class_no}")
    if payload.get("chapter_count") != len(modules):
        raise ValueError(f"legacy_source_chapter_count_mismatch:{subject_id}:{class_no}")

    mapping: list[tuple[str, str]] = []
    projected_chapters: list[dict[str, Any]] = []
    for chapter_no, (chapter, module) in enumerate(zip(chapters, modules, strict=True), start=1):
        expected_flat_id = f"eng_c{class_no}_ch{chapter_no:02d}"
        if chapter.get("chapter_id") != expected_flat_id:
            raise ValueError(f"legacy_source_id_mismatch:{expected_flat_id}")
        if chapter.get("chapter_no") != chapter_no:
            raise ValueError(f"legacy_source_order_mismatch:{expected_flat_id}")
        if normalize_compat_title(chapter.get("chapter_title") or "") != (
            normalize_compat_title(module.title)
        ):
            raise ValueError(f"legacy_source_title_mismatch:{expected_flat_id}:{module.module_id}")
        mapping.append((expected_flat_id, module.module_id))
        projected_chapters.append(
            {
                **chapter,
                "chapter_id": expected_flat_id,
                "chapter_no": chapter_no,
                "chapter_title": (
                    module.phase_0_public_display_title or module.title
                ),
            }
        )

    projected_payload = {
        **payload,
        "book_code": release.book_code,
        "book_title": release.book_title,
        "chapter_count": len(projected_chapters),
        "chapters": projected_chapters,
        "class_no": release.class_no,
        "subject_id": release.subject_id,
    }

    return (
        json.dumps(projected_payload, ensure_ascii=True, separators=(",", ":")),
        tuple(mapping),
    )


def load_beta_source_map(subject_id: str, class_no: int) -> dict[str, Any]:
    serialized, _mapping = _validated_projection(subject_id, int(class_no))
    return json.loads(serialized)


def legacy_flat_module_mapping(subject_id: str, class_no: int) -> dict[str, str]:
    _serialized, mapping = _validated_projection(subject_id, int(class_no))
    return dict(mapping)


load_beta_source_map.cache_clear = _validated_projection.cache_clear  # type: ignore[attr-defined]


__all__ = [
    "LEGACY_SOURCE_MAP_ROOT",
    "PHASE_2_REMOVAL_BOUNDARY",
    "legacy_flat_module_mapping",
    "load_beta_source_map",
    "normalize_compat_title",
]
