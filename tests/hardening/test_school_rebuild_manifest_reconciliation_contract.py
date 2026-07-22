"""Keep reviewed School runtime content reproducible from canonical manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.content.school_rebuild_content import LIVE_CHAPTER_ROOT, load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from scripts.build_school_deep_chapter import (
    MANIFEST_RECONCILIATION_PATH,
    ManifestChapterReconciliation,
    RuntimeActivityReconciliation,
    build_deep_chapter,
    load_manifest,
    manifest_activity_fingerprint,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_ROOT = ROOT / "app" / "content" / "school_rebuild_manifests" / "english"


def _canonical_manifest_paths() -> list[Path]:
    """Prefer the canonical Python manifest where a historical JSON also exists."""

    paths_by_chapter: dict[str, Path] = {}
    for path in sorted(MANIFEST_ROOT.glob("class_*/*")):
        if path.suffix not in {".json", ".py"}:
            continue
        existing = paths_by_chapter.get(path.stem)
        if existing is None or path.suffix == ".py":
            paths_by_chapter[path.stem] = path
    return [paths_by_chapter[chapter_id] for chapter_id in sorted(paths_by_chapter)]


def _live_chapter_ids() -> set[str]:
    return {
        path.stem
        for path in LIVE_CHAPTER_ROOT.glob("english/class_*/*.json")
    }


def test_manifest_reconciliation_registry_is_checked_and_nonempty() -> None:
    payload = json.loads(MANIFEST_RECONCILIATION_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "school-manifest-reconciliation-v1"
    assert payload["chapters"]
    assert all(
        record["activity_overrides"] or record["runtime_activity_overrides"]
        for record in payload["chapters"]
    )


def test_every_live_chapter_has_exactly_one_canonical_manifest() -> None:
    """A reviewed runtime cannot be the only source of its own content."""

    manifest_ids = [path.stem for path in _canonical_manifest_paths()]

    assert len(manifest_ids) == len(set(manifest_ids))
    assert set(manifest_ids) == _live_chapter_ids()


def test_runtime_reconciliation_path_rejects_noncanonical_array_indexes() -> None:
    with pytest.raises(ValueError, match="noncanonical_runtime_index"):
        RuntimeActivityReconciliation.model_validate(
            {
                "runtime_path": "/levels/00/checks/bridge",
                "fingerprint": "a" * 64,
                "success_feedback": "This is reviewed learner feedback.",
            }
        )


def test_version_only_reconciliation_record_is_valid() -> None:
    record = ManifestChapterReconciliation.model_validate(
        {
            "fingerprint_schema_version": "school-manifest-activity-v3",
            "chapter_id": "eng_c5_ch01",
            "change_id": "release-version-correction",
            "review_evidence": ["Reviewed release metadata correction."],
            "base_manifest_sha256": "a" * 64,
            "base_content_version": "2026-07-21.base",
            "base_certification_version": "2026-07-21.base",
            "content_version": "2026-07-22.release",
            "certification_version": "2026-07-22.release",
            "activity_overrides": [],
            "runtime_activity_overrides": [],
        }
    )

    assert record.chapter_id == "eng_c5_ch01"


def test_activity_fingerprint_is_stable_across_assessment_projection() -> None:
    """Assessment items intentionally omit the learner interaction renderer."""

    source = {
        "kind": "open_response",
        "activity_id": "fixture-open",
        "passage": "A lantern grew dim after its battery ran low.",
        "prompt": "Explain what the learner should infer from the clue.",
        "skill_ids": ["reading.sentence_comprehension"],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
            {
                "id": "inference",
                "description": "Infers that the battery needs power.",
                "required": True,
                "min_quality": 0.8,
            }
        ],
        "concept_slots": [
            {
                "id": "inference",
                "description": "Names the battery power inference.",
                "any_of": ["needs power"],
            }
        ],
        "forbidden_phrases": ["I do not know"],
        "min_response_words": 4,
        "relevance_terms": ["lantern", "battery"],
        "model_answer": "The lantern needs power because its battery ran low.",
        "pass_score": 0.8,
    }
    runtime = {
        **source,
        "grading_mode": "strict_open_rubric",
        "options": [],
        "accepted_answers": [],
        "response_mode": "paragraph",
        "evaluation_mode": "llm_rubric",
        "preflight_rule": "relevant_english_response",
    }
    runtime.pop("kind")
    runtime.pop("activity_id")
    runtime.pop("interaction_type")

    assert manifest_activity_fingerprint(source) == manifest_activity_fingerprint(
        runtime
    )


def test_activity_fingerprint_normalizes_empty_optional_source_collections() -> None:
    source = {
        "kind": "open_response",
        "activity_id": "fixture-bridge",
        "passage": "Mina last used her ruler at the library table.",
        "prompt": "Write a short response that gives a reason.",
        "skill_ids": ["writing.short_answer"],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
            {
                "id": "reason",
                "description": "Gives a relevant reason.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
        "concept_slots": [],
        "forbidden_phrases": ["I do not know"],
        "min_response_words": 4,
        "relevance_terms": ["library", "ruler"],
        "model_answer": "I would check the library table because Mina used her ruler there.",
        "pass_score": 0.7,
    }
    runtime = {
        **source,
        "grading_mode": "strict_open_rubric",
        "options": [],
        "accepted_answers": [],
        "response_mode": "paragraph",
        "evaluation_mode": "llm_rubric",
        "preflight_rule": "relevant_english_response",
    }
    for key in ("kind", "activity_id", "interaction_type", "concept_slots"):
        runtime.pop(key)

    assert manifest_activity_fingerprint(source) == manifest_activity_fingerprint(
        runtime
    )


@pytest.mark.parametrize("manifest_path", _canonical_manifest_paths())
def test_canonical_manifest_rebuild_matches_reviewed_runtime(manifest_path: Path) -> None:
    chapter_id = manifest_path.stem
    class_no = int(manifest_path.parent.name.removeprefix("class_"))
    live = load_live_chapter_file(
        LIVE_CHAPTER_ROOT / "english" / f"class_{class_no}" / f"{chapter_id}.json"
    )
    rebuilt = LiveSchoolChapter.model_validate(
        build_deep_chapter(None, load_manifest(manifest_path))
    )

    assert rebuilt.runtime_dict() == live.runtime_dict()
