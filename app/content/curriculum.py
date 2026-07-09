"""School curriculum registry — loads NCERT chapter modules + class manifests.

The main registry serves the legacy flat modules (comm/gd/interview/old school).
This loads the NEW structure from data/school/: each `classN_chXX_*.json` is a
chapter (a Module with chapter metadata + a chapter_test), and each `classN.json`
is a SchoolClass manifest (ordered chapters + milestone exams). Kept separate so
the rebuild can grow without touching the legacy serving path.

Loaded once at import; cross-references are validated (a class may only list
chapters that exist), so a broken manifest fails fast instead of at runtime.
"""
import json
from pathlib import Path

from app.content.schema import Module, SchoolClass

_DIR = Path(__file__).parent / "data" / "school"

_CHAPTERS: dict[str, Module] = {}
_CLASSES: dict[int, SchoolClass] = {}


def _load() -> None:
    for f in sorted(_DIR.glob("class*_ch*.json")):
        m = Module.model_validate(json.load(open(f)))
        _CHAPTERS[m.id] = m
    for f in sorted(_DIR.glob("class*.json")):
        if "_ch" in f.stem:
            continue
        c = SchoolClass.model_validate(json.load(open(f)))
        # fail fast on a manifest that points at a chapter we never loaded
        missing = [cid for cid in c.chapters if cid not in _CHAPTERS]
        if missing:
            raise ValueError(f"class {c.class_no} manifest references unknown chapters: {missing}")
        _CLASSES[c.class_no] = c


if _DIR.exists():
    _load()


def all_classes() -> list[int]:
    return sorted(_CLASSES)


def get_class(class_no: int) -> SchoolClass:
    return _CLASSES[class_no]


def get_chapter(chapter_id: str) -> Module:
    return _CHAPTERS[chapter_id]


def class_chapters(class_no: int) -> list[Module]:
    """The class's chapters as Modules, in manifest order."""
    return [_CHAPTERS[cid] for cid in _CLASSES[class_no].chapters]


def chapter_count(class_no: int) -> int:
    return len(_CLASSES[class_no].chapters)


def next_chapter(class_no: int, chapter_id: str) -> Module | None:
    """The chapter after `chapter_id` in the class, or None at the end."""
    order = _CLASSES[class_no].chapters
    i = order.index(chapter_id)
    return _CHAPTERS[order[i + 1]] if i + 1 < len(order) else None


def chapter_of_level(level_id: str) -> Module | None:
    """The chapter (module) that owns a given level (node) id."""
    for ch in _CHAPTERS.values():
        if any(n.id == level_id for n in ch.nodes):
            return ch
    return None


def find_assessment(test_id: str):
    """Locate any assessment by id — a chapter test or a class milestone exam."""
    for ch in _CHAPTERS.values():
        if ch.chapter_test and ch.chapter_test.id == test_id:
            return ch.chapter_test
    for cls in _CLASSES.values():
        for m in cls.milestones:
            if m.id == test_id:
                return m
    return None


def class_of_assessment(test_id: str) -> int | None:
    """The class number that owns an assessment (chapter test or milestone)."""
    for ch in _CHAPTERS.values():
        if ch.chapter_test and ch.chapter_test.id == test_id:
            return ch.class_no
    for cls in _CLASSES.values():
        if any(m.id == test_id for m in cls.milestones):
            return cls.class_no
    return None


def all_chapters() -> list[Module]:
    return list(_CHAPTERS.values())
