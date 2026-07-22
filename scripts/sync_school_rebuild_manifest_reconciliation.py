#!/usr/bin/env python3
"""Generate or verify the checked release overlay for deep School manifests.

The live chapter JSON remains the reviewed learner-facing release. This script
derives the narrow release overlay needed to reproduce it from the canonical
Python/JSON manifests, and rejects any runtime difference outside that overlay.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school_rebuild_content import LIVE_CHAPTER_ROOT, load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from scripts.build_school_deep_chapter import (
    MANIFEST_ACTIVITY_FINGERPRINT_SCHEMA_VERSION,
    MANIFEST_RECONCILIATION_PATH,
    MANIFEST_ROOT,
    ManifestReconciliationRegistry,
    _canonical_sha256,
    _iter_manifest_open_activities,
    apply_manifest_reconciliation,
    build_deep_chapter,
    load_manifest,
    manifest_activity_fingerprint,
)


def _canonical_manifest_paths() -> list[Path]:
    """Prefer a canonical Python manifest over a historical JSON duplicate."""

    paths_by_chapter: dict[str, Path] = {}
    for path in sorted(MANIFEST_ROOT.glob("english/class_*/*")):
        if path.suffix not in {".json", ".py"}:
            continue
        existing = paths_by_chapter.get(path.stem)
        if existing is None or path.suffix == ".py":
            paths_by_chapter[path.stem] = path
    return [paths_by_chapter[chapter_id] for chapter_id in sorted(paths_by_chapter)]


def _runtime_open_activities(payload: object) -> list[tuple[str, dict[str, Any]]]:
    activities: list[tuple[str, dict[str, Any]]] = []

    def visit(value: object, path: tuple[str, ...] = ()) -> None:
        if isinstance(value, dict):
            if all(
                isinstance(value.get(key), str)
                for key in ("passage", "prompt", "model_answer")
            ):
                activities.append(("/" + "/".join(path), value))
                return
            for key, child in value.items():
                visit(child, (*path, str(key)))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, (*path, str(index)))

    visit(payload)
    return activities


def _first_difference(left: object, right: object, path: str = "") -> str | None:
    if type(left) is not type(right):
        return f"{path or '<root>'}:type:{type(left).__name__}!={type(right).__name__}"
    if isinstance(left, dict):
        keys = sorted(set(left) | set(right))
        for key in keys:
            next_path = f"{path}.{key}" if path else key
            if key not in left or key not in right:
                return f"{next_path}:key-mismatch"
            difference = _first_difference(left[key], right[key], next_path)
            if difference:
                return difference
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}:length:{len(left)}!={len(right)}"
        for index, (left_value, right_value) in enumerate(zip(left, right, strict=True)):
            difference = _first_difference(left_value, right_value, f"{path}[{index}]")
            if difference:
                return difference
        return None
    if left != right:
        return f"{path}:value-mismatch"
    return None


def _chapter_record(manifest_path: Path) -> dict[str, Any] | None:
    raw_manifest = load_manifest(manifest_path, apply_reconciliation=False)
    raw_payload = raw_manifest.model_dump(mode="json", exclude_none=True)
    chapter_id = raw_manifest.chapter.chapter_id
    live_path = LIVE_CHAPTER_ROOT / "english" / manifest_path.parent.name / f"{chapter_id}.json"
    if not live_path.is_file():
        raise ValueError(f"manifest_reconciliation_live_chapter_missing:{chapter_id}")
    live = load_live_chapter_file(live_path)
    raw_runtime = LiveSchoolChapter.model_validate(
        build_deep_chapter(None, raw_manifest)
    ).runtime_dict()

    source_by_fingerprint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for activity in _iter_manifest_open_activities(raw_payload):
        source_by_fingerprint[manifest_activity_fingerprint(activity)].append(activity)

    raw_nodes = dict(_runtime_open_activities(raw_runtime))
    nodes: list[tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], str]] = []
    for runtime_path, runtime_activity in _runtime_open_activities(live.runtime_dict()):
        raw_activity = raw_nodes.get(runtime_path)
        if raw_activity is None:
            raise ValueError(
                f"manifest_reconciliation_runtime_path_missing:{chapter_id}:{runtime_path}"
            )
        fingerprint = manifest_activity_fingerprint(runtime_activity)
        if manifest_activity_fingerprint(raw_activity) != fingerprint:
            raise ValueError(
                f"manifest_reconciliation_runtime_fingerprint_changed:{chapter_id}:{runtime_path}"
            )
        candidates = source_by_fingerprint[fingerprint]
        runtime_node_id = runtime_activity.get("variant_id") or runtime_activity.get("item_id")
        if isinstance(runtime_node_id, str):
            candidates = [
                activity
                for activity in candidates
                if activity["activity_id"] == runtime_node_id
            ]
        if len(candidates) != 1:
            state = "missing" if not candidates else "ambiguous"
            raise ValueError(
                "manifest_reconciliation_runtime_activity_"
                f"{state}:{chapter_id}:{runtime_node_id or fingerprint}"
            )
        source = candidates[0]
        nodes.append((runtime_path, runtime_activity, raw_activity, source, fingerprint))

    policies_by_source: dict[tuple[str, str], set[object]] = defaultdict(set)
    source_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for _, runtime_activity, _, source, fingerprint in nodes:
        key = (source["activity_id"], fingerprint)
        policies_by_source[key].add(runtime_activity.get("semantic_evidence_policy"))
        source_by_key[key] = source

    activity_overrides: list[dict[str, Any]] = []
    source_policy_overrides: set[tuple[str, str]] = set()
    for key, target_policies in sorted(policies_by_source.items()):
        source = source_by_key[key]
        source_policy = source.get("semantic_evidence_policy")
        if target_policies == {source_policy}:
            continue
        if target_policies == {"traceable_rubric"}:
            activity_overrides.append(
                {
                    "node_id": source["activity_id"],
                    "fingerprint": key[1],
                    "semantic_evidence_policy": "traceable_rubric",
                }
            )
            source_policy_overrides.add(key)

    runtime_activity_overrides: list[dict[str, Any]] = []
    for runtime_path, runtime_activity, raw_activity, source, fingerprint in nodes:
        override: dict[str, Any] = {
            "runtime_path": runtime_path,
            "fingerprint": fingerprint,
        }
        source_key = (source["activity_id"], fingerprint)
        target_policy = runtime_activity.get("semantic_evidence_policy")
        if (
            source_key not in source_policy_overrides
            and target_policy != raw_activity.get("semantic_evidence_policy")
        ):
            if target_policy != "traceable_rubric":
                raise ValueError(
                    "manifest_reconciliation_unsupported_semantic_policy:"
                    f"{chapter_id}:{runtime_path}"
                )
            override["semantic_evidence_policy"] = target_policy
        target_feedback = runtime_activity.get("success_feedback")
        if target_feedback != raw_activity.get("success_feedback"):
            if not isinstance(target_feedback, str) or not target_feedback.strip():
                raise ValueError(
                    "manifest_reconciliation_unsupported_success_feedback:"
                    f"{chapter_id}:{runtime_path}"
                )
            override["success_feedback"] = target_feedback
        if len(override) > 2:
            runtime_activity_overrides.append(override)

    versions_changed = (
        raw_manifest.chapter.content_version != live.content_version
        or raw_manifest.chapter.certification_version != live.certification_version
    )
    if not activity_overrides and not runtime_activity_overrides and not versions_changed:
        return None
    semantic_evidence = [
        evidence
        for evidence in live.review_evidence
        if "semantic" in evidence.casefold() or "feedback" in evidence.casefold()
    ]
    return {
        "fingerprint_schema_version": MANIFEST_ACTIVITY_FINGERPRINT_SCHEMA_VERSION,
        "chapter_id": chapter_id,
        "change_id": (
            "semantic-evidence-corpus-review-2026-07-21"
            if activity_overrides
            else "runtime-release-reconciliation-2026-07-21"
        ),
        "review_evidence": semantic_evidence
        or ["Reviewed release runtime matches the declared source manifest."],
        "base_manifest_sha256": _canonical_sha256(raw_payload),
        "base_content_version": raw_manifest.chapter.content_version,
        "base_certification_version": raw_manifest.chapter.certification_version,
        "content_version": live.content_version,
        "certification_version": live.certification_version,
        "activity_overrides": activity_overrides,
        "runtime_activity_overrides": runtime_activity_overrides,
    }


def build_registry_payload() -> dict[str, Any]:
    records = [
        record
        for manifest_path in _canonical_manifest_paths()
        if (record := _chapter_record(manifest_path)) is not None
    ]
    payload = {
        "schema_version": "school-manifest-reconciliation-v1",
        "chapters": sorted(records, key=lambda record: record["chapter_id"]),
    }
    registry = ManifestReconciliationRegistry.model_validate(payload)

    for manifest_path in _canonical_manifest_paths():
        raw_manifest = load_manifest(manifest_path, apply_reconciliation=False)
        reconciled = apply_manifest_reconciliation(raw_manifest, registry)
        rebuilt = LiveSchoolChapter.model_validate(
            build_deep_chapter(None, reconciled)
        )
        live = load_live_chapter_file(
            LIVE_CHAPTER_ROOT
            / "english"
            / manifest_path.parent.name
            / f"{raw_manifest.chapter.chapter_id}.json"
        )
        difference = _first_difference(rebuilt.runtime_dict(), live.runtime_dict())
        if difference:
            raise ValueError(
                "manifest_reconciliation_runtime_drift:"
                f"{raw_manifest.chapter.chapter_id}:{difference}"
            )
    return registry.model_dump(mode="json")


def _render(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = _render(build_registry_payload())
    if args.check:
        if not MANIFEST_RECONCILIATION_PATH.is_file():
            print("school_manifest_reconciliation_missing")
            return 1
        if MANIFEST_RECONCILIATION_PATH.read_text(encoding="utf-8") != rendered:
            print("school_manifest_reconciliation_drift")
            return 1
        print("school_manifest_reconciliation_ok")
        return 0

    MANIFEST_RECONCILIATION_PATH.write_text(rendered, encoding="utf-8")
    print(
        "school_manifest_reconciliation_written "
        f"chapters={len(json.loads(rendered)['chapters'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
