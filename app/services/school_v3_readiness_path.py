"""Focused Readiness Path builder for School V3."""

from __future__ import annotations

from app.content.school_v3_taxonomy import locked_english_taxonomy


def build_readiness_path(
    *,
    subject_id: str,
    target_class_no: int,
    weak_skill_ids: tuple[str, ...],
    non_blocking_weak_skill_ids: tuple[str, ...] = (),
) -> dict:
    taxonomy = locked_english_taxonomy()
    entries = {entry.skill_id: entry for entry in taxonomy.entries if entry.subject_id == subject_id}
    non_blocking = set(non_blocking_weak_skill_ids)
    blocking_weak = tuple(skill_id for skill_id in _unique(weak_skill_ids) if skill_id not in non_blocking)

    ordered_blocking = _ordered_with_prerequisites(blocking_weak, entries)
    modules = [
        {
            "skill_id": skill_id,
            "title": entries[skill_id].name,
            "source_class_no": entries[skill_id].class_min,
            "target_class_no": target_class_no,
            "reason": "missing_prerequisite" if skill_id not in blocking_weak else "placement_gap",
        }
        for skill_id in ordered_blocking
        if skill_id in entries
    ]
    watchlist = [skill_id for skill_id in _unique(weak_skill_ids) if skill_id in non_blocking]
    target_unlocked = not modules
    deviation_note = ""
    if target_unlocked and watchlist:
        deviation_note = (
            "Target class is unlocked with a watchlist. These skills are non-blocking now, "
            "but the curriculum will pause for a focused masterclass if they resurface."
        )
    return {
        "subject_id": subject_id,
        "target_class_no": target_class_no,
        "path_type": "target_curriculum" if target_unlocked else "readiness_path",
        "target_unlocked": target_unlocked,
        "modules": modules,
        "watchlist_skill_ids": watchlist,
        "deviation_note": deviation_note,
    }


def _ordered_with_prerequisites(skill_ids: tuple[str, ...], entries: dict) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    def visit(skill_id: str) -> None:
        if skill_id in seen or skill_id not in entries:
            return
        seen.add(skill_id)
        for prerequisite in entries[skill_id].prerequisite_skill_ids:
            visit(prerequisite)
        ordered.append(skill_id)

    for skill_id in skill_ids:
        visit(skill_id)
    positions = {skill_id: index for index, skill_id in enumerate(ordered)}
    return sorted(ordered, key=lambda skill_id: (entries[skill_id].class_min, positions[skill_id]))


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return tuple(result)
