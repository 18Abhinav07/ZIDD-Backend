#!/usr/bin/env python3
"""Compile an explicitly authored English deep-chapter manifest for Classes 2-5.

This module is intentionally non-generative. It does not contain textbook
body text, invent prompts, or fill missing authoring fields. A chapter can be
built only when every teaching activity, rubric, misconception response, and
assessment strand is supplied by the manifest author.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.content.school_rebuild_schema import (
    LiveConceptSlot,
    LiveEpisodeKind,
    LiveRubricCriterion,
    LiveSchoolChapter,
    LiveSourceAnchor,
)


# Keep the established wire value so existing Class 5 manifests remain valid.
MANIFEST_SCHEMA_VERSION = "school-class5-deep-manifest-v1"
ACTIVITY_SCHEMA_VERSION = "school-activity-v2"
COMPACT_PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
_PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|FIXME|LOREM|PLACEHOLDER|INSERT HERE|REPLACE ME)\b",
    flags=re.IGNORECASE,
)
_ENGLISH_CHAPTER_ID_PATTERN = re.compile(r"eng_c[2-5]_ch[0-9]{2}")
_PRODUCTIVE_SKILL_PREFIXES = ("writing.", "speaking.", "oral.")


def _clean_text(value: str, *, error: str, minimum: int = 1) -> str:
    cleaned = value.strip()
    if len(cleaned) < minimum:
        raise ValueError(error)
    if _PLACEHOLDER_PATTERN.search(cleaned):
        raise ValueError("deep_manifest_placeholder_text")
    return cleaned


def _clean_identifiers(values: list[str], *, error: str) -> list[str]:
    cleaned = [value.strip() for value in values]
    if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
        raise ValueError(error)
    return cleaned


def _is_productive_skill(skill_id: str) -> bool:
    lowered = skill_id.casefold()
    return lowered.startswith(_PRODUCTIVE_SKILL_PREFIXES) or (
        ".production" in lowered or lowered.endswith("_production")
    )


def _word_count(value: str) -> int:
    return len(re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", value.casefold()))


def _phrase_matches(value: str, phrase: str) -> bool:
    normalized_value = " ".join(value.casefold().split())
    normalized_phrase = " ".join(phrase.casefold().split())
    if not normalized_phrase:
        return False
    prefix = r"(?<!\w)" if normalized_phrase[0].isalnum() else ""
    suffix = r"(?!\w)" if normalized_phrase[-1].isalnum() else ""
    return re.search(
        f"{prefix}{re.escape(normalized_phrase)}{suffix}",
        normalized_value,
    ) is not None


class _StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class OriginalContentAttestation(_StrictModel):
    zidd_authored_original: Literal[True]
    textbook_body_or_questions_copied: Literal[False]
    source_analysis_reference: str

    @field_validator("source_analysis_reference")
    @classmethod
    def _valid_reference(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_source_analysis_reference_required",
            minimum=8,
        )


class ChapterMetadataSpec(_StrictModel):
    chapter_id: str
    chapter_no: int = Field(ge=1)
    title: str
    book_title: str
    unit_title: str
    source_url: str
    source_note: str
    content_version: str
    certification_version: str
    authorship: OriginalContentAttestation

    @field_validator(
        "chapter_id",
        "title",
        "book_title",
        "unit_title",
        "source_url",
        "source_note",
        "content_version",
        "certification_version",
    )
    @classmethod
    def _valid_metadata(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_metadata_empty")

    @model_validator(mode="after")
    def _supported_english_identity(self) -> "ChapterMetadataSpec":
        if _ENGLISH_CHAPTER_ID_PATTERN.fullmatch(self.chapter_id) is None:
            raise ValueError(
                "deep_manifest_requires_english_class_2_to_5_chapter_id"
            )
        return self


class ConnectTeachingSpec(_StrictModel):
    teaching_block: str
    passage: str
    prompt: str

    @field_validator("teaching_block", "passage")
    @classmethod
    def _substantial_copy(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_connect_teaching_too_shallow",
            minimum=20,
        )

    @field_validator("prompt")
    @classmethod
    def _substantial_prompt(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_connect_prompt_too_shallow",
            minimum=10,
        )


class ChoiceActivitySpec(_StrictModel):
    kind: Literal["selected_option"]
    activity_id: str
    teaching_block: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(min_length=1)
    options: list[str] = Field(min_length=2)
    accepted_answers: list[str] = Field(min_length=1)

    @field_validator("activity_id")
    @classmethod
    def _valid_activity_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_id_empty")

    @field_validator("teaching_block", "passage")
    @classmethod
    def _substantial_copy(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_activity_copy_too_shallow",
            minimum=20,
        )

    @field_validator("prompt")
    @classmethod
    def _substantial_prompt(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_activity_prompt_too_shallow",
            minimum=10,
        )

    @field_validator("skill_ids")
    @classmethod
    def _valid_skill_ids(cls, values: list[str]) -> list[str]:
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_activity_skill_ids",
        )

    @field_validator("options", "accepted_answers")
    @classmethod
    def _valid_answers(cls, values: list[str]) -> list[str]:
        cleaned = [
            _clean_text(value, error="deep_manifest_answer_empty")
            for value in values
        ]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("duplicate_deep_manifest_answer")
        return cleaned

    @model_validator(mode="after")
    def _literal_answer_and_receptive_evidence(self) -> "ChoiceActivitySpec":
        if not set(self.accepted_answers).issubset(set(self.options)):
            raise ValueError("deep_manifest_choice_answer_not_literal_option")
        if len(self.accepted_answers) == len(self.options):
            raise ValueError("deep_manifest_choice_requires_distractor")
        productive = sorted(
            skill_id for skill_id in self.skill_ids if _is_productive_skill(skill_id)
        )
        if productive:
            raise ValueError(
                "selected_option_cannot_evidence_productive_skill:"
                + ",".join(productive)
            )
        return self


class OpenActivitySpec(_StrictModel):
    kind: Literal["open_response"]
    activity_id: str
    teaching_block: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(min_length=1)
    interaction_type: Literal[
        "short_text",
        "evidence_text",
        "paragraph_text",
        "dialogue",
        "creative_continuation",
        "summary",
        "reflection",
    ]
    rubric_criteria: list[LiveRubricCriterion] = Field(min_length=1)
    concept_slots: list[LiveConceptSlot] = Field(min_length=1)
    forbidden_phrases: list[str] = Field(min_length=1)
    min_response_words: int = Field(ge=6, le=100)
    ordered_concept_slot_ids: list[str] | None = Field(default=None, min_length=2)
    relevance_terms: list[str] = Field(min_length=2)
    model_answer: str
    pass_score: float = Field(default=0.8, ge=0.6, le=1.0)
    preflight_rule: str = "relevant_english_response"

    @field_validator("activity_id")
    @classmethod
    def _valid_activity_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_id_empty")

    @field_validator("teaching_block", "passage", "model_answer")
    @classmethod
    def _substantial_copy(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_open_authority_too_shallow",
            minimum=20,
        )

    @field_validator("prompt")
    @classmethod
    def _substantial_prompt(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_activity_prompt_too_shallow",
            minimum=10,
        )

    @field_validator("skill_ids")
    @classmethod
    def _valid_skill_ids(cls, values: list[str]) -> list[str]:
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_activity_skill_ids",
        )

    @field_validator(
        "forbidden_phrases",
        "relevance_terms",
        "ordered_concept_slot_ids",
    )
    @classmethod
    def _valid_identifier_lists(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_open_list",
        )

    @model_validator(mode="after")
    def _rubric_and_slots_agree(self) -> "OpenActivitySpec":
        criterion_ids = [criterion.id for criterion in self.rubric_criteria]
        slot_ids = [slot.id for slot in self.concept_slots]
        if criterion_ids != slot_ids:
            raise ValueError("deep_manifest_rubric_slot_ids_must_match_in_order")
        if self.ordered_concept_slot_ids and not set(
            self.ordered_concept_slot_ids
        ).issubset(set(slot_ids)):
            raise ValueError("deep_manifest_unknown_ordered_concept_slot")
        alias_owners: dict[str, set[str]] = {}
        for slot in self.concept_slots:
            for alias in slot.any_of:
                normalized_alias = " ".join(alias.casefold().split())
                alias_owners.setdefault(normalized_alias, set()).add(slot.id)
        shared_aliases = {
            alias: owners
            for alias, owners in alias_owners.items()
            if len(owners) > 1
        }
        if shared_aliases:
            alias, owners = sorted(shared_aliases.items())[0]
            raise ValueError(
                "deep_manifest_alias_shared_across_slots:"
                f"{self.activity_id}:{alias}:{','.join(sorted(owners))}"
            )
        model_words = _word_count(self.model_answer)
        if model_words < self.min_response_words:
            raise ValueError(
                "deep_manifest_model_below_word_floor:"
                f"{self.activity_id}:{model_words}:{self.min_response_words}"
            )
        missing_slots = [
            slot.id
            for slot in self.concept_slots
            if not any(
                _phrase_matches(self.model_answer, alias)
                for alias in slot.any_of
            )
        ]
        if missing_slots:
            raise ValueError(
                "deep_manifest_model_missing_slot:"
                f"{self.activity_id}:{','.join(missing_slots)}"
            )
        return self


AuthoredActivitySpec: TypeAlias = Annotated[
    ChoiceActivitySpec | OpenActivitySpec,
    Field(discriminator="kind"),
]


class SupportChecksSpec(_StrictModel):
    bridge: AuthoredActivitySpec
    masterclass: AuthoredActivitySpec
    revision_level_1: AuthoredActivitySpec
    revision_level_2: AuthoredActivitySpec
    revision_level_3: AuthoredActivitySpec

    def activities(self) -> dict[str, AuthoredActivitySpec]:
        return {
            "bridge": self.bridge,
            "masterclass": self.masterclass,
            "revision_level_1": self.revision_level_1,
            "revision_level_2": self.revision_level_2,
            "revision_level_3": self.revision_level_3,
        }


class MisconceptionClusterSpec(_StrictModel):
    cluster_id: str
    skill_ids: list[str] = Field(min_length=1)
    misconception: str
    remediation: str
    support_check_ids: list[str] = Field(min_length=1)

    @field_validator("cluster_id")
    @classmethod
    def _valid_cluster_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_cluster_id_empty")

    @field_validator("skill_ids", "support_check_ids")
    @classmethod
    def _valid_identifiers(cls, values: list[str]) -> list[str]:
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_cluster_identifiers",
        )

    @field_validator("misconception", "remediation")
    @classmethod
    def _substantial_remediation(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_remediation_too_shallow",
            minimum=20,
        )


class DeepLevelManifest(_StrictModel):
    level_id: str
    title: str
    focus: str
    outcome: str
    skill_ids: list[str] = Field(min_length=1)
    episode_kind: LiveEpisodeKind
    source_anchor_ids: list[str] = Field(min_length=1)
    companion_source_anchor_ids: list[str] = Field(default_factory=list)
    connect: ConnectTeachingSpec
    co_construct: AuthoredActivitySpec
    guided_variants: list[AuthoredActivitySpec] = Field(min_length=4)
    independent_variants: list[OpenActivitySpec] = Field(min_length=4)
    transfer_variants: list[OpenActivitySpec] = Field(min_length=3)
    review_variants: list[OpenActivitySpec] = Field(min_length=2)
    misconception_clusters: list[MisconceptionClusterSpec] = Field(min_length=1)
    support_checks: SupportChecksSpec

    @field_validator("level_id", "title", "focus")
    @classmethod
    def _valid_level_metadata(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_level_metadata_empty")

    @field_validator("outcome")
    @classmethod
    def _substantial_outcome(cls, value: str) -> str:
        return _clean_text(
            value,
            error="deep_manifest_outcome_too_shallow",
            minimum=20,
        )

    @field_validator(
        "skill_ids",
        "source_anchor_ids",
        "companion_source_anchor_ids",
    )
    @classmethod
    def _valid_identifiers(cls, values: list[str]) -> list[str]:
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_level_identifiers",
        )

    @model_validator(mode="after")
    def _complete_authored_depth(self) -> "DeepLevelManifest":
        support = self.support_checks.activities()
        activities: list[AuthoredActivitySpec] = [
            self.co_construct,
            *self.guided_variants,
            *self.independent_variants,
            *self.transfer_variants,
            *self.review_variants,
            *support.values(),
        ]
        activity_ids = [activity.activity_id for activity in activities]
        signatures = [
            (activity.teaching_block, activity.passage, activity.prompt)
            for activity in activities
        ]
        if len(activity_ids) != len(set(activity_ids)):
            raise ValueError("duplicate_deep_manifest_activity_id")
        if len(signatures) != len(set(signatures)):
            raise ValueError("duplicate_deep_manifest_activity_copy")

        level_skills = set(self.skill_ids)
        for activity in activities:
            unknown = set(activity.skill_ids) - level_skills
            if unknown:
                raise ValueError(
                    "deep_manifest_activity_has_unknown_skill:"
                    + ",".join(sorted(unknown))
                )

        cluster_ids = [cluster.cluster_id for cluster in self.misconception_clusters]
        if len(cluster_ids) != len(set(cluster_ids)):
            raise ValueError("duplicate_deep_manifest_cluster_id")
        support_ids = {activity.activity_id for activity in support.values()}
        remediated_skills: set[str] = set()
        referenced_support: set[str] = set()
        for cluster in self.misconception_clusters:
            if not set(cluster.skill_ids).issubset(level_skills):
                raise ValueError("deep_manifest_cluster_has_unknown_skill")
            unknown_checks = set(cluster.support_check_ids) - support_ids
            if unknown_checks:
                raise ValueError(
                    "deep_manifest_cluster_has_unknown_support_check:"
                    + ",".join(sorted(unknown_checks))
                )
            for support_check_id in cluster.support_check_ids:
                support_activity = next(
                    activity
                    for activity in support.values()
                    if activity.activity_id == support_check_id
                )
                if not set(support_activity.skill_ids).intersection(
                    cluster.skill_ids
                ):
                    raise ValueError(
                        "deep_manifest_support_check_skill_mismatch:"
                        + support_check_id
                    )
            remediated_skills.update(cluster.skill_ids)
            referenced_support.update(cluster.support_check_ids)
        if remediated_skills != level_skills:
            missing = sorted(level_skills - remediated_skills)
            raise ValueError(
                "deep_manifest_level_skill_has_no_remediation:"
                + ",".join(missing)
            )
        if referenced_support != support_ids:
            unused = sorted(support_ids - referenced_support)
            raise ValueError(
                "deep_manifest_support_check_not_mapped:" + ",".join(unused)
            )
        for pool_name, pool in (
            ("guided", self.guided_variants),
            ("independent", self.independent_variants),
            ("transfer", self.transfer_variants),
            ("review", self.review_variants),
        ):
            covered = {
                skill_id for activity in pool for skill_id in activity.skill_ids
            }
            missing = level_skills - covered
            if missing:
                raise ValueError(
                    f"deep_manifest_{pool_name}_pool_missing_skill:"
                    + ",".join(sorted(missing))
                )
        return self


AssessmentEvidenceForm = Literal["selected_option", "constructed_response"]


class AssessmentStrandSpec(_StrictModel):
    strand_id: str
    skill_ids: list[str] = Field(min_length=1)
    minimum_items: int = Field(ge=1)
    evidence_forms: list[AssessmentEvidenceForm] = Field(min_length=1)
    remediation_level_ids: list[str] = Field(min_length=1)

    @field_validator("strand_id")
    @classmethod
    def _valid_strand_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_strand_id_empty")

    @field_validator("skill_ids", "evidence_forms", "remediation_level_ids")
    @classmethod
    def _valid_identifiers(cls, values: list[str]) -> list[str]:
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_assessment_strand",
        )


class AssessmentBlueprintSpec(_StrictModel):
    items_per_attempt: int = Field(ge=10, le=20)
    pass_score: float = Field(ge=0.6, le=1.0)
    max_attempts: int = Field(ge=1, le=3)
    bank_item_count: int = Field(ge=20)
    items: list[AuthoredActivitySpec] = Field(min_length=20)
    strands: list[AssessmentStrandSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def _disjoint_strands(self) -> "AssessmentBlueprintSpec":
        strand_ids = [strand.strand_id for strand in self.strands]
        if len(strand_ids) != len(set(strand_ids)):
            raise ValueError("duplicate_deep_manifest_assessment_strand")
        claimed: set[str] = set()
        for strand in self.strands:
            overlap = claimed.intersection(strand.skill_ids)
            if overlap:
                raise ValueError(
                    "deep_manifest_assessment_skill_in_multiple_strands:"
                    + ",".join(sorted(overlap))
                )
            claimed.update(strand.skill_ids)
        if len(self.items) != self.bank_item_count:
            raise ValueError("deep_manifest_assessment_bank_count_mismatch")
        item_ids = [item.activity_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("duplicate_deep_manifest_assessment_item_id")
        item_skills = {
            skill_id for item in self.items for skill_id in item.skill_ids
        }
        if item_skills != claimed:
            missing = sorted(item_skills - claimed)
            extra = sorted(claimed - item_skills)
            raise ValueError(
                "deep_manifest_assessment_skill_set_mismatch:"
                f"missing={','.join(missing)};extra={','.join(extra)}"
            )
        return self


class DeepChapterManifest(_StrictModel):
    schema_version: Literal[MANIFEST_SCHEMA_VERSION]
    chapter: ChapterMetadataSpec
    source_anchors: list[LiveSourceAnchor] = Field(min_length=1)
    levels: list[DeepLevelManifest] = Field(min_length=1)
    chapter_assessment: AssessmentBlueprintSpec

    @model_validator(mode="after")
    def _unique_chapter_contract(self) -> "DeepChapterManifest":
        anchor_ids = [anchor.anchor_id for anchor in self.source_anchors]
        if len(anchor_ids) != len(set(anchor_ids)):
            raise ValueError("duplicate_deep_manifest_source_anchor")
        known_anchors = set(anchor_ids)
        required_anchors = {
            anchor.anchor_id
            for anchor in self.source_anchors
            if anchor.required_for_chapter_certification
        }
        level_ids = [level.level_id for level in self.levels]
        if len(level_ids) != len(set(level_ids)):
            raise ValueError("duplicate_deep_manifest_level_id")
        for level in self.levels:
            source_anchors = set(level.source_anchor_ids)
            companion_anchors = set(level.companion_source_anchor_ids)
            unknown = (source_anchors | companion_anchors) - known_anchors
            if unknown:
                raise ValueError(
                    "deep_manifest_level_has_unknown_source_anchor:"
                    + ",".join(sorted(unknown))
                )
            if source_anchors & companion_anchors:
                raise ValueError("deep_manifest_level_source_anchor_role_overlap")
            invalid_companions = companion_anchors & required_anchors
            if invalid_companions:
                raise ValueError(
                    "deep_manifest_required_anchor_cannot_be_companion:"
                    + ",".join(sorted(invalid_companions))
                )
        return self


def load_manifest(path: str | Path) -> DeepChapterManifest:
    """Load a JSON manifest or a Python module exporting ``MANIFEST``."""

    manifest_path = Path(path)
    if manifest_path.suffix == ".json":
        payload: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    elif manifest_path.suffix == ".py":
        module_spec = importlib.util.spec_from_file_location(
            f"school_manifest_{manifest_path.stem}",
            manifest_path,
        )
        if module_spec is None or module_spec.loader is None:
            raise ValueError("deep_manifest_python_module_unloadable")
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        if not hasattr(module, "MANIFEST"):
            raise ValueError("deep_manifest_python_requires_MANIFEST")
        payload = module.MANIFEST
    else:
        raise ValueError("deep_manifest_requires_json_or_python")
    if isinstance(payload, DeepChapterManifest):
        return payload
    return DeepChapterManifest.model_validate(payload)


def _activity_payload(
    *,
    spec: AuthoredActivitySpec,
    level: DeepLevelManifest,
    phase: str,
    evidence_role: Literal["formative", "supported", "certifying"],
    pool_id: str | None = None,
    target_misconception_tags: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "teaching_block": spec.teaching_block,
        "passage": spec.passage,
        "prompt": spec.prompt,
        "schema_version": ACTIVITY_SCHEMA_VERSION,
        "episode_kind": level.episode_kind,
        "teaching_phase": phase,
        "interaction_type": (
            "single_choice"
            if isinstance(spec, ChoiceActivitySpec)
            else spec.interaction_type
        ),
        "evidence_role": evidence_role,
        "source_anchor_ids": list(level.source_anchor_ids),
        "knowledge_components": list(spec.skill_ids),
    }
    if target_misconception_tags:
        payload["target_misconception_tags"] = list(
            dict.fromkeys(target_misconception_tags)
        )
    if pool_id is not None:
        payload["pool_id"] = pool_id
        payload["variant_id"] = spec.activity_id

    if isinstance(spec, ChoiceActivitySpec):
        payload.update(
            options=list(spec.options),
            accepted_answers=list(spec.accepted_answers),
            grading_mode="selected_option",
            response_mode="short",
        )
        return payload

    payload.update(
        options=[],
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        response_mode="paragraph",
        evaluation_mode="llm_rubric",
        preflight_rule=spec.preflight_rule,
        pass_score=spec.pass_score,
        rubric_criteria=[criterion.model_dump() for criterion in spec.rubric_criteria],
        concept_slots=[slot.model_dump() for slot in spec.concept_slots],
        forbidden_phrases=list(spec.forbidden_phrases),
        min_response_words=spec.min_response_words,
        relevance_terms=list(spec.relevance_terms),
        model_answer=spec.model_answer,
    )
    if spec.ordered_concept_slot_ids:
        payload["ordered_concept_slot_ids"] = list(
            spec.ordered_concept_slot_ids
        )
    if evidence_role == "certifying":
        payload["certifying_language"] = "en"
    return payload


def _assessment_item_payload(spec: AuthoredActivitySpec) -> dict[str, Any]:
    """Translate one fully authored manifest activity into a chapter-test item."""

    payload: dict[str, Any] = {
        "item_id": spec.activity_id,
        "passage": spec.passage,
        "prompt": spec.prompt,
        "skill_ids": list(spec.skill_ids),
    }
    if isinstance(spec, ChoiceActivitySpec):
        payload.update(
            options=list(spec.options),
            accepted_answers=list(spec.accepted_answers),
            grading_mode="selected_option",
            response_mode="short",
        )
        return payload

    payload.update(
        options=[],
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        certifying_language="en",
        response_mode="paragraph",
        evaluation_mode="llm_rubric",
        preflight_rule=spec.preflight_rule,
        pass_score=spec.pass_score,
        rubric_criteria=[criterion.model_dump() for criterion in spec.rubric_criteria],
        concept_slots=[slot.model_dump() for slot in spec.concept_slots],
        forbidden_phrases=list(spec.forbidden_phrases),
        min_response_words=spec.min_response_words,
        relevance_terms=list(spec.relevance_terms),
        model_answer=spec.model_answer,
    )
    if spec.ordered_concept_slot_ids:
        payload["ordered_concept_slot_ids"] = list(
            spec.ordered_concept_slot_ids
        )
    return payload


def _clusters_for_activity(
    level: DeepLevelManifest,
    activity: AuthoredActivitySpec,
) -> list[str]:
    activity_skills = set(activity.skill_ids)
    return [
        cluster.cluster_id
        for cluster in level.misconception_clusters
        if activity_skills.intersection(cluster.skill_ids)
    ]


def _clusters_for_support_check(
    level: DeepLevelManifest,
    activity_id: str,
) -> list[str]:
    return [
        cluster.cluster_id
        for cluster in level.misconception_clusters
        if activity_id in cluster.support_check_ids
    ]


def _connect_step(level: DeepLevelManifest) -> dict[str, Any]:
    connect_anchor_ids = list(
        dict.fromkeys(
            [*level.source_anchor_ids, *level.companion_source_anchor_ids]
        )
    )
    return {
        "step_id": f"{level.level_id}:connect",
        "phase": "connect",
        "required": True,
        "activity": {
            "teaching_block": level.connect.teaching_block,
            "passage": level.connect.passage,
            "prompt": level.connect.prompt,
            "options": [],
            "accepted_answers": [],
            "schema_version": ACTIVITY_SCHEMA_VERSION,
            "episode_kind": level.episode_kind,
            "teaching_phase": "connect",
            "interaction_type": "continue",
            "evidence_role": "experience",
            "source_anchor_ids": connect_anchor_ids,
            "knowledge_components": list(level.skill_ids),
        },
    }


def _single_step(
    *,
    level: DeepLevelManifest,
    phase: str,
    spec: AuthoredActivitySpec,
    evidence_role: Literal["formative", "supported", "certifying"],
) -> dict[str, Any]:
    return {
        "step_id": f"{level.level_id}:{phase}",
        "phase": phase,
        "required": True,
        "activity": _activity_payload(
            spec=spec,
            level=level,
            phase=phase,
            evidence_role=evidence_role,
            target_misconception_tags=_clusters_for_activity(level, spec),
        ),
    }


def _pool_step(
    *,
    level: DeepLevelManifest,
    phase: str,
    specs: list[AuthoredActivitySpec],
    evidence_role: Literal["supported", "certifying"],
) -> dict[str, Any]:
    pool_id = f"{level.level_id}:{phase}"
    return {
        "step_id": f"{level.level_id}:{phase}",
        "phase": phase,
        "required": True,
        "pool_id": pool_id,
        "variant_pool": [
            _activity_payload(
                spec=spec,
                level=level,
                phase=phase,
                evidence_role=evidence_role,
                pool_id=pool_id,
                target_misconception_tags=_clusters_for_activity(level, spec),
            )
            for spec in specs
        ],
    }


def build_level_teaching_steps(level: DeepLevelManifest) -> list[dict[str, Any]]:
    """Build the compact, schema-supported six-phase teaching sequence."""

    steps = [
        _connect_step(level),
        _single_step(
            level=level,
            phase="co_construct",
            spec=level.co_construct,
            evidence_role="formative",
        ),
        _pool_step(
            level=level,
            phase="guided_practice",
            specs=list(level.guided_variants),
            evidence_role="supported",
        ),
        _pool_step(
            level=level,
            phase="independent_application",
            specs=list(level.independent_variants),
            evidence_role="certifying",
        ),
        _pool_step(
            level=level,
            phase="transfer",
            specs=list(level.transfer_variants),
            evidence_role="certifying",
        ),
        _pool_step(
            level=level,
            phase="review",
            specs=list(level.review_variants),
            evidence_role="certifying",
        ),
    ]
    if tuple(step["phase"] for step in steps) != COMPACT_PHASES:
        raise RuntimeError("deep_chapter_phase_sequence_internal_error")
    return steps


def build_level_checks(level: DeepLevelManifest) -> dict[str, Any]:
    support = level.support_checks.activities()
    checks: dict[str, Any] = {
        "guided_check": _activity_payload(
            spec=level.co_construct,
            level=level,
            phase="co_construct",
            evidence_role="formative",
            target_misconception_tags=_clusters_for_activity(
                level, level.co_construct
            ),
        ),
        "independent_check": _activity_payload(
            spec=level.independent_variants[0],
            level=level,
            phase="independent_application",
            evidence_role="certifying",
        ),
        "transfer_check": _activity_payload(
            spec=level.transfer_variants[0],
            level=level,
            phase="transfer",
            evidence_role="certifying",
        ),
    }
    for check_name, activity in support.items():
        checks[check_name] = _activity_payload(
            spec=activity,
            level=level,
            phase="guided_practice",
            evidence_role="supported",
            target_misconception_tags=_clusters_for_support_check(
                level, activity.activity_id
            ),
        )
    return checks


def _validate_assessment_contract(
    chapter: LiveSchoolChapter,
    manifest: DeepChapterManifest,
) -> None:
    assessment = chapter.chapter_assessment
    if assessment is None:
        raise ValueError("deep_manifest_requires_chapter_assessment")
    blueprint = manifest.chapter_assessment
    if assessment.items_per_attempt != blueprint.items_per_attempt:
        raise ValueError("deep_manifest_assessment_items_per_attempt_mismatch")
    if assessment.pass_score != blueprint.pass_score:
        raise ValueError("deep_manifest_assessment_pass_score_mismatch")
    if assessment.max_attempts != blueprint.max_attempts:
        raise ValueError("deep_manifest_assessment_max_attempts_mismatch")
    if len(assessment.items) != blueprint.bank_item_count:
        raise ValueError("deep_manifest_assessment_bank_count_mismatch")

    actual_skills = {
        skill_id for item in assessment.items for skill_id in item.skill_ids
    }
    blueprint_skills = {
        skill_id
        for strand in blueprint.strands
        for skill_id in strand.skill_ids
    }
    if actual_skills != blueprint_skills:
        missing = sorted(actual_skills - blueprint_skills)
        extra = sorted(blueprint_skills - actual_skills)
        raise ValueError(
            "deep_manifest_assessment_skill_set_mismatch:"
            f"missing={','.join(missing)};extra={','.join(extra)}"
        )

    level_by_id = {level.level_id: level for level in manifest.levels}
    remediated_by_level = {
        level.level_id: {
            skill_id
            for cluster in level.misconception_clusters
            for skill_id in cluster.skill_ids
        }
        for level in manifest.levels
    }
    for strand in blueprint.strands:
        unknown_levels = set(strand.remediation_level_ids) - set(level_by_id)
        if unknown_levels:
            raise ValueError(
                "deep_manifest_assessment_unknown_remediation_level:"
                + ",".join(sorted(unknown_levels))
            )
        strand_skills = set(strand.skill_ids)
        matching_items = [
            item
            for item in assessment.items
            if set(item.skill_ids).issubset(strand_skills)
        ]
        cross_strand_items = [
            item.item_id
            for item in assessment.items
            if set(item.skill_ids).intersection(strand_skills)
            and not set(item.skill_ids).issubset(strand_skills)
        ]
        if cross_strand_items:
            raise ValueError(
                "deep_manifest_assessment_item_crosses_strands:"
                + ",".join(sorted(cross_strand_items))
            )
        if len(matching_items) < strand.minimum_items:
            raise ValueError(
                "deep_manifest_assessment_strand_underfilled:" + strand.strand_id
            )
        actual_forms = {
            "selected_option" if item.options else "constructed_response"
            for item in matching_items
        }
        if actual_forms != set(strand.evidence_forms):
            raise ValueError(
                "deep_manifest_assessment_evidence_forms_mismatch:"
                + strand.strand_id
            )
        remediated_skills = set().union(
            *(
                remediated_by_level[level_id]
                for level_id in strand.remediation_level_ids
            )
        )
        missing_remediation = strand_skills - remediated_skills
        if missing_remediation:
            raise ValueError(
                "deep_manifest_assessment_skill_has_no_remediation:"
                + ",".join(sorted(missing_remediation))
            )


def validate_manifest_against_chapter(
    chapter: LiveSchoolChapter | None,
    manifest: DeepChapterManifest,
) -> None:
    if chapter is None:
        return
    if chapter.chapter_id != manifest.chapter.chapter_id:
        raise ValueError("deep_manifest_chapter_id_mismatch")
    if chapter.chapter_no != manifest.chapter.chapter_no:
        raise ValueError("deep_manifest_chapter_no_mismatch")


def build_deep_chapter(
    chapter_payload: dict[str, Any] | None,
    manifest_payload: DeepChapterManifest | dict[str, Any],
) -> dict[str, Any]:
    """Return a complete validated draft chapter authored by the manifest."""

    chapter = (
        LiveSchoolChapter.model_validate(chapter_payload)
        if chapter_payload is not None
        else None
    )
    manifest = (
        manifest_payload
        if isinstance(manifest_payload, DeepChapterManifest)
        else DeepChapterManifest.model_validate(manifest_payload)
    )
    validate_manifest_against_chapter(chapter, manifest)

    result: dict[str, Any] = {
        "approval_status": "draft",
        "reviewed_by": None,
        "reviewed_at": None,
        "review_evidence": [],
        "runtime_sha256": "0" * 64,
        "chapter_id": manifest.chapter.chapter_id,
        "chapter_no": manifest.chapter.chapter_no,
        "title": manifest.chapter.title,
        "book_title": manifest.chapter.book_title,
        "unit_title": manifest.chapter.unit_title,
        "source_url": manifest.chapter.source_url,
        "source_note": manifest.chapter.source_note,
        "content_version": manifest.chapter.content_version,
        "certification_version": manifest.chapter.certification_version,
        "source_anchors": [
            anchor.model_dump() for anchor in manifest.source_anchors
        ],
        "levels": [
            {
                "level_id": authored.level_id,
                "title": authored.title,
                "focus": authored.focus,
                "skill_ids": list(authored.skill_ids),
                "teaching_goal": authored.outcome,
                "episode_kind": authored.episode_kind,
                "source_anchor_ids": list(authored.source_anchor_ids),
                "companion_source_anchor_ids": list(
                    authored.companion_source_anchor_ids
                ),
                "checks": build_level_checks(authored),
                "teaching_steps": build_level_teaching_steps(authored),
            }
            for authored in manifest.levels
        ],
        "chapter_assessment": {
            "items_per_attempt": manifest.chapter_assessment.items_per_attempt,
            "pass_score": manifest.chapter_assessment.pass_score,
            "max_attempts": manifest.chapter_assessment.max_attempts,
            "items": [
                _assessment_item_payload(item)
                for item in manifest.chapter_assessment.items
            ],
        },
    }

    validated = LiveSchoolChapter.model_validate(result)
    _validate_assessment_contract(validated, manifest)
    result["runtime_sha256"] = validated.calculated_runtime_sha256()
    checked = LiveSchoolChapter.model_validate(result)
    if checked.calculated_runtime_sha256() != result["runtime_sha256"]:
        raise RuntimeError("deep_chapter_runtime_hash_not_stable")
    return checked.model_dump(exclude_none=True)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chapter",
        type=Path,
        help="Optional existing chapter identity check; omit when creating a new chapter.",
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacing an existing output path, including the input chapter.",
    )
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error("output exists; pass --force to replace it")
    chapter_payload = (
        json.loads(args.chapter.read_text(encoding="utf-8"))
        if args.chapter is not None
        else None
    )
    built = build_deep_chapter(chapter_payload, load_manifest(args.manifest))
    _write_json(args.output, built)
    print(
        json.dumps(
            {
                "approval_status": built["approval_status"],
                "chapter_id": built["chapter_id"],
                "levels": len(built["levels"]),
                "runtime_sha256": built["runtime_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
