#!/usr/bin/env python3
"""Construct a canonical deep manifest from a reviewed runtime chapter.

This is a migration tool, not a content generator. It preserves the existing
Zidd-authored learner-facing content, makes every grading contract explicit in
the manifest, and refuses any runtime difference other than a narrowly
declared release override. It is intended for the one-time recovery of a
reviewed chapter that predates the canonical deep-manifest pipeline.
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

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from scripts.build_school_deep_chapter import (
    MANIFEST_SCHEMA_VERSION,
    DeepChapterManifest,
    _canonical_sha256,
    build_deep_chapter,
    manifest_activity_fingerprint,
)


_RUNTIME_ONLY_ACTIVITY_FIELDS = {
    "schema_version",
    "episode_kind",
    "teaching_phase",
    "evidence_role",
    "source_anchor_ids",
    "knowledge_components",
    "pool_id",
    "variant_id",
    "certifying_language",
    "response_mode",
    "evaluation_mode",
    "answer_rule",
}
_OVERRIDABLE_FIELDS = {
    "semantic_evidence_policy",
    "success_feedback",
    "target_misconception_tags",
}


def _activity_id(activity: dict[str, Any], fallback: str) -> str:
    for key in ("variant_id", "item_id"):
        value = activity.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return fallback


def _source_activity(
    activity: dict[str, Any],
    *,
    fallback_id: str,
    assessment: bool = False,
) -> dict[str, Any]:
    """Map one typed runtime activity to an explicit source activity."""

    mode = str(activity["grading_mode"])
    skills = list(
        activity.get("skill_ids")
        if assessment
        else activity.get("knowledge_components") or []
    )
    source: dict[str, Any] = {
        "kind": {
            "selected_option": "selected_option",
            "strict_open_rubric": "open_response",
            "exact_text": "exact_text",
            "ordered_slots": "ordered_slots",
        }[mode],
        "activity_id": _activity_id(activity, fallback_id),
        # Assessment runtime does not expose teaching copy. This source-only
        # guidance is intentionally not emitted in the assessment projection.
        "teaching_block": (
            activity.get("teaching_block")
            or "Return to the visible passage and check each requested detail before answering."
        ),
        "passage": activity["passage"],
        "prompt": activity["prompt"],
        "skill_ids": skills,
    }
    target_tags = activity.get("target_misconception_tags")
    if isinstance(target_tags, list) and target_tags:
        source["target_misconception_tags"] = target_tags
    # A reviewed legacy runtime may deliberately treat a guided choice as an
    # unscored experience. Preserve that authored pedagogical role instead of
    # silently upgrading it to supported evidence when compiling the manifest.
    if activity.get("evidence_role") is not None:
        source["evidence_role_override"] = activity["evidence_role"]
    if activity.get("teaching_phase") is not None:
        source["teaching_phase_override"] = activity["teaching_phase"]
    if activity.get("source_anchor_ids") is not None:
        source["source_anchor_ids_override"] = list(activity["source_anchor_ids"])

    if mode == "selected_option":
        source.update(
            options=list(activity["options"]),
            accepted_answers=list(activity["accepted_answers"]),
        )
        for key in ("wrong_answer_misconception_tags", "success_feedback"):
            if activity.get(key) is not None:
                source[key] = activity[key]
        return source

    if mode == "exact_text":
        source.update(
            interaction_type=activity.get("interaction_type") or "cloze",
            accepted_answers=list(activity["accepted_answers"]),
        )
        return source

    if mode == "ordered_slots":
        source.update(
            interaction_type=activity.get("interaction_type") or "ordering",
            concept_slots=list(activity["concept_slots"]),
            ordered_concept_slot_ids=list(activity["ordered_concept_slot_ids"]),
        )
        return source

    if mode != "strict_open_rubric":
        raise ValueError(f"manifest_extract_unsupported_mode:{mode}")
    source.update(
        interaction_type=activity.get("interaction_type") or "paragraph_text",
        rubric_criteria=list(activity["rubric_criteria"]),
        forbidden_phrases=list(activity["forbidden_phrases"]),
        min_response_words=activity["min_response_words"],
        relevance_terms=list(activity["relevance_terms"]),
        model_answer=activity["model_answer"],
        pass_score=activity["pass_score"],
        preflight_rule=activity["preflight_rule"],
    )
    if activity.get("concept_slots") is not None:
        source["concept_slots"] = list(activity["concept_slots"])
    for key in (
        "ordered_concept_slot_ids",
        "semantic_evidence_policy",
        "semantic_validator_id",
        "actor_action_receiver_slot_ids",
        "criterion_misconception_tags",
        "success_feedback",
    ):
        if activity.get(key) is not None:
            source[key] = activity[key]
    return source


def _support_clusters(
    *,
    level: dict[str, Any],
    support_checks: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Preserve support routing tags while supplying a complete source graph."""

    level_skills = list(level["skill_ids"])
    skill_ids_by_tag: dict[str, set[str]] = defaultdict(set)
    support_ids_by_tag: dict[str, list[str]] = defaultdict(list)
    all_activities: list[dict[str, Any]] = []
    for step in level["teaching_steps"]:
        if "activity" in step:
            all_activities.append(step["activity"])
        else:
            all_activities.extend(step["variant_pool"])
    all_activities.extend(support_checks.values())
    for activity in all_activities:
        tags = activity.get("target_misconception_tags") or []
        skills = activity.get("knowledge_components") or level_skills
        for tag in tags:
            skill_ids_by_tag[tag].update(skills)
    for name, activity in support_checks.items():
        for tag in activity.get("target_misconception_tags") or []:
            support_ids_by_tag[tag].append(
                _activity_id(activity, f"{level['level_id']}:{name}")
            )

    if not skill_ids_by_tag:
        skill_ids_by_tag["reviewed_learning_gap"].update(level_skills)
    clusters: list[dict[str, Any]] = []
    fallback_support_ids = [
        _activity_id(activity, f"{level['level_id']}:{name}")
        for name, activity in support_checks.items()
    ]
    for index, tag in enumerate(sorted(skill_ids_by_tag)):
        cluster_skills = sorted(
            set(level_skills).intersection(skill_ids_by_tag[tag]) or set(level_skills)
        )
        support_ids = list(dict.fromkeys(support_ids_by_tag.get(tag) or fallback_support_ids))
        clusters.append(
            {
                "cluster_id": f"{level['level_id']}:{tag}",
                "skill_ids": cluster_skills,
                "misconception": (
                    f"The learner may show the reviewed misconception tagged {tag.replace('_', ' ')}."
                ),
                "remediation": (
                    "Return to the decisive passage clue, compare the tempting alternative, "
                    "and complete a fresh supported check before trying independently again."
                ),
                "support_check_ids": support_ids,
            }
        )
    return clusters


def _source_level(level: dict[str, Any]) -> dict[str, Any]:
    steps = {step["phase"]: step for step in level["teaching_steps"]}
    required_phases = {
        "connect",
        "co_construct",
        "guided_practice",
        "independent_application",
        "transfer",
        "review",
    }
    if set(steps) != required_phases:
        raise ValueError(
            "manifest_extract_unexpected_teaching_phases:" + level["level_id"]
        )
    checks = level["checks"]
    support_names = (
        "guided_check",
        "independent_check",
        "transfer_check",
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
        "revision_level_4",
    )
    support_runtime = {
        name: checks[name] for name in support_names if name in checks
    }
    support_source = {
        name: _source_activity(
            activity,
            fallback_id=f"{level['level_id']}:{name}",
        )
        for name, activity in support_runtime.items()
    }
    source = {
        "level_id": level["level_id"],
        "title": level["title"],
        "focus": level["focus"],
        "outcome": level["teaching_goal"],
        "skill_ids": list(level["skill_ids"]),
        "episode_kind": level["episode_kind"],
        "source_anchor_ids": list(level["source_anchor_ids"]),
        "companion_source_anchor_ids": list(
            level.get("companion_source_anchor_ids") or []
        ),
        "connect": {
            key: steps["connect"]["activity"][key]
            for key in ("teaching_block", "passage", "prompt")
        }
        | {
            "source_anchor_ids_override": list(
                steps["connect"]["activity"]["source_anchor_ids"]
            ),
            "knowledge_components_override": list(
                steps["connect"]["activity"]["knowledge_components"]
            ),
        },
        "co_construct": _source_activity(
            steps["co_construct"]["activity"],
            fallback_id=f"{level['level_id']}:co_construct",
        ),
        "guided_variants": [
            _source_activity(activity, fallback_id=f"{level['level_id']}:guided")
            for activity in steps["guided_practice"]["variant_pool"]
        ],
        "independent_variants": [
            _source_activity(activity, fallback_id=f"{level['level_id']}:independent")
            for activity in steps["independent_application"]["variant_pool"]
        ],
        "transfer_variants": [
            _source_activity(activity, fallback_id=f"{level['level_id']}:transfer")
            for activity in steps["transfer"]["variant_pool"]
        ],
        "review_variants": [
            _source_activity(activity, fallback_id=f"{level['level_id']}:review")
            for activity in steps["review"]["variant_pool"]
        ],
        "guided_pool_id": steps["guided_practice"]["pool_id"],
        "independent_pool_id": steps["independent_application"]["pool_id"],
        "transfer_pool_id": steps["transfer"]["pool_id"],
        "review_pool_id": steps["review"]["pool_id"],
        "support_checks": support_source,
        "misconception_clusters": _support_clusters(
            level=level,
            support_checks={
                name: activity
                for name, activity in support_runtime.items()
                if name
                not in {"guided_check", "independent_check", "transfer_check"}
            },
        ),
    }
    return source


def _runtime_activities(payload: object) -> list[tuple[str, dict[str, Any]]]:
    activities: list[tuple[str, dict[str, Any]]] = []

    def visit(value: object, path: tuple[str, ...] = ()) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("passage"), str) and isinstance(
                value.get("prompt"), str
            ) and isinstance(value.get("grading_mode"), str):
                activities.append(("/" + "/".join(path), value))
                return
            for key, child in value.items():
                visit(child, (*path, str(key)))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, (*path, str(index)))

    visit(payload)
    return activities


def _release_overrides(
    raw_runtime: dict[str, Any],
    live_runtime: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_by_path = dict(_runtime_activities(raw_runtime))
    live_by_path = dict(_runtime_activities(live_runtime))
    if set(raw_by_path) != set(live_by_path):
        raise ValueError("manifest_extract_runtime_activity_paths_changed")
    overrides: list[dict[str, Any]] = []
    for path in sorted(raw_by_path):
        raw = raw_by_path[path]
        live = live_by_path[path]
        raw_stable = {key: value for key, value in raw.items() if key not in _OVERRIDABLE_FIELDS}
        live_stable = {key: value for key, value in live.items() if key not in _OVERRIDABLE_FIELDS}
        if raw_stable != live_stable:
            raise ValueError(f"manifest_extract_unrepresentable_runtime_difference:{path}")
        changed = {
            key: live.get(key)
            for key in _OVERRIDABLE_FIELDS
            if raw.get(key) != live.get(key) and live.get(key) is not None
        }
        if not changed:
            continue
        overrides.append(
            {
                "runtime_path": path,
                "fingerprint": manifest_activity_fingerprint(raw),
                **changed,
            }
        )
    return overrides


def build_manifest(live: LiveSchoolChapter) -> dict[str, Any]:
    runtime = live.runtime_dict()
    assessment_items = [
        _source_activity(
            item,
            fallback_id=item["item_id"],
            assessment=True,
        )
        for item in runtime["chapter_assessment"]["items"]
    ]
    assessment_skills = sorted(
        {skill for item in assessment_items for skill in item["skill_ids"]}
    )
    evidence_forms = list(
        dict.fromkeys(
            "selected_option"
            if item["kind"] == "selected_option"
            else "constructed_response"
            for item in assessment_items
        )
    )
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "chapter": {
            key: runtime[key]
            for key in (
                "chapter_id",
                "chapter_no",
                "title",
                "book_title",
                "unit_title",
                "source_url",
                "source_note",
                "content_version",
                "certification_version",
            )
        }
        | {
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": (
                    "Reviewed Zidd-original Chapter 1 runtime migrated into the canonical deep-manifest contract."
                ),
            }
        },
        "source_anchors": runtime["source_anchors"],
        "levels": [_source_level(level) for level in runtime["levels"]],
        "chapter_assessment": {
            **{
                key: runtime["chapter_assessment"][key]
                for key in ("items_per_attempt", "pass_score", "max_attempts")
            },
            "bank_item_count": len(assessment_items),
            "items": assessment_items,
            "strands": [
                {
                    "strand_id": "reviewed_chapter_learning_surface",
                    "skill_ids": assessment_skills,
                    "minimum_items": len(assessment_items),
                    "evidence_forms": evidence_forms,
                    "remediation_level_ids": [
                        level["level_id"] for level in runtime["levels"]
                    ],
                }
            ],
        },
        "release_runtime_overrides": [],
    }
    parsed = DeepChapterManifest.model_validate(manifest)
    raw_runtime = build_deep_chapter(None, parsed)
    manifest["release_runtime_overrides"] = _release_overrides(
        raw_runtime,
        runtime,
    )
    final = DeepChapterManifest.model_validate(manifest)
    rebuilt = build_deep_chapter(None, final)
    if LiveSchoolChapter.model_validate(rebuilt).runtime_dict() != runtime:
        raise ValueError("manifest_extract_final_runtime_drift")
    return final.model_dump(mode="json", exclude_none=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error("output exists; pass --force to replace it")
    live = load_live_chapter_file(args.chapter)
    payload = build_manifest(live)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "chapter_id": live.chapter_id,
                "manifest_sha256": _canonical_sha256(payload),
                "runtime_sha256": live.runtime_sha256,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
