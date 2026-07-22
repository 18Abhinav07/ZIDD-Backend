#!/usr/bin/env python3
"""Compile an explicitly authored English deep-chapter manifest for Classes 2-5.

This module is intentionally non-generative. It does not contain textbook
body text, invent prompts, or fill missing authoring fields. A chapter can be
built only when every teaching activity, rubric, misconception response, and
assessment strand is supplied by the manifest author.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from functools import lru_cache
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
    LiveEvidenceRole,
    LiveEpisodeKind,
    LiveTeachingPhase,
    LiveRubricCriterion,
    LiveSchoolChapter,
    LiveSourceAnchor,
    SemanticEvidencePolicy,
    SchoolOpenSemanticValidatorId,
)


# Keep the established wire value so existing Class 5 manifests remain valid.
MANIFEST_SCHEMA_VERSION = "school-class5-deep-manifest-v1"
ACTIVITY_SCHEMA_VERSION = "school-activity-v2"
MANIFEST_RECONCILIATION_SCHEMA_VERSION = "school-manifest-reconciliation-v1"
MANIFEST_ACTIVITY_FINGERPRINT_SCHEMA_VERSION = "school-manifest-activity-v3"
MANIFEST_RECONCILIATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "content"
    / "school_rebuild_manifest_reconciliation.json"
)
MANIFEST_ROOT = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "content"
    / "school_rebuild_manifests"
)
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


def _clean_optional_identifiers(
    values: list[str] | None,
    *,
    error: str,
) -> list[str] | None:
    if values is None:
        return None
    return _clean_identifiers(values, error=error)


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


def _canonical_sha256(payload: object) -> str:
    """Hash a validated source payload independently of file formatting."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def manifest_activity_fingerprint(payload: dict[str, Any]) -> str:
    """Bind a reconciliation override to the full authored activity contract.

    Runtime-only phase metadata is intentionally omitted, as are the two fields
    this reconciliation layer is allowed to patch. The base-manifest digest
    protects all authoring copy; this fingerprint covers the complete emitted
    grading and learner-prompt contract shared by teaching and assessment use.
    Interaction rendering is deliberately excluded because chapter-assessment
    projections do not carry a tutor renderer.
    """

    if not isinstance(payload.get("passage"), str) or not isinstance(
        payload.get("prompt"), str
    ):
        raise ValueError("deep_manifest_reconciliation_activity_not_authored")
    grading_mode = str(
        payload.get("grading_mode")
        or ("strict_open_rubric" if isinstance(payload.get("model_answer"), str) else "selected_option")
    )
    kind = {
        "strict_open_rubric": "open_response",
        "selected_option": "selected_option",
        "exact_text": "exact_text",
        "ordered_slots": "ordered_slots",
    }.get(grading_mode, grading_mode)
    preflight_rule = payload.get("preflight_rule") or (
        "relevant_english_response"
        if grading_mode == "strict_open_rubric"
        else None
    )
    return _canonical_sha256(
        {
            "schema_version": MANIFEST_ACTIVITY_FINGERPRINT_SCHEMA_VERSION,
            "kind": kind,
            "passage": str(payload["passage"]).strip(),
            "prompt": str(payload["prompt"]).strip(),
            "skill_ids": list(
                payload.get("skill_ids")
                or payload.get("knowledge_components")
                or []
            ),
            "options": list(payload.get("options") or []),
            "accepted_answers": list(payload.get("accepted_answers") or []),
            "grading_mode": grading_mode,
            "answer_rule": payload.get("answer_rule"),
            "preflight_rule": preflight_rule,
            "pass_score": payload.get("pass_score"),
            "rubric_criteria": payload.get("rubric_criteria"),
            "concept_slots": payload.get("concept_slots") or None,
            "forbidden_phrases": payload.get("forbidden_phrases"),
            "min_response_words": payload.get("min_response_words"),
            "ordered_concept_slot_ids": payload.get("ordered_concept_slot_ids"),
            "relevance_terms": payload.get("relevance_terms"),
            "model_answer": payload.get("model_answer"),
            "semantic_validator_id": payload.get("semantic_validator_id"),
            "actor_action_receiver_slot_ids": payload.get(
                "actor_action_receiver_slot_ids"
            ),
            "wrong_answer_misconception_tags": payload.get(
                "wrong_answer_misconception_tags"
            ),
            "criterion_misconception_tags": payload.get(
                "criterion_misconception_tags"
            ),
        }
    )


class ManifestActivityReconciliation(_StrictModel):
    node_id: str
    fingerprint: str
    semantic_evidence_policy: Literal["traceable_rubric"]

    @field_validator("node_id")
    @classmethod
    def _valid_node_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_reconciliation_node_id")

    @field_validator("fingerprint")
    @classmethod
    def _valid_fingerprint(cls, value: str) -> str:
        cleaned = value.strip().casefold()
        if re.fullmatch(r"[0-9a-f]{64}", cleaned) is None:
            raise ValueError("deep_manifest_reconciliation_invalid_fingerprint")
        return cleaned

class RuntimeActivityReconciliation(_StrictModel):
    runtime_path: str
    fingerprint: str
    semantic_evidence_policy: SemanticEvidencePolicy | None = None
    success_feedback: str | None = None
    target_misconception_tags: list[str] | None = None

    @field_validator("runtime_path")
    @classmethod
    def _valid_runtime_path(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.startswith("/") or "//" in cleaned:
            raise ValueError("deep_manifest_reconciliation_runtime_path")
        segments = cleaned.removeprefix("/").split("/")
        if any(not segment for segment in segments):
            raise ValueError("deep_manifest_reconciliation_runtime_path")
        for segment in segments:
            if segment.isdigit():
                if str(int(segment)) != segment:
                    raise ValueError(
                        "deep_manifest_reconciliation_noncanonical_runtime_index"
                    )
                continue
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", segment) is None:
                raise ValueError("deep_manifest_reconciliation_runtime_path")
        return "/" + "/".join(segments)

    @field_validator("fingerprint")
    @classmethod
    def _valid_fingerprint(cls, value: str) -> str:
        cleaned = value.strip().casefold()
        if re.fullmatch(r"[0-9a-f]{64}", cleaned) is None:
            raise ValueError("deep_manifest_reconciliation_invalid_fingerprint")
        return cleaned

    @field_validator("success_feedback")
    @classmethod
    def _valid_success_feedback(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_text(
            value,
            error="deep_manifest_reconciliation_success_feedback",
        )

    @field_validator("target_misconception_tags")
    @classmethod
    def _valid_target_misconception_tags(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None
        return _clean_identifiers(
            value,
            error="invalid_deep_manifest_target_misconception_tags",
        )

    @model_validator(mode="after")
    def _changes_a_supported_field(self) -> "RuntimeActivityReconciliation":
        if (
            self.semantic_evidence_policy is None
            and self.success_feedback is None
            and self.target_misconception_tags is None
        ):
            raise ValueError("deep_manifest_reconciliation_empty_runtime_override")
        return self


class ManifestChapterReconciliation(_StrictModel):
    fingerprint_schema_version: Literal[
        MANIFEST_ACTIVITY_FINGERPRINT_SCHEMA_VERSION
    ]
    chapter_id: str
    change_id: str
    review_evidence: list[str] = Field(min_length=1)
    base_manifest_sha256: str
    base_content_version: str
    base_certification_version: str
    content_version: str
    certification_version: str
    activity_overrides: list[ManifestActivityReconciliation] = Field(
        default_factory=list
    )
    runtime_activity_overrides: list[RuntimeActivityReconciliation] = Field(
        default_factory=list
    )

    @field_validator(
        "chapter_id",
        "change_id",
        "base_content_version",
        "base_certification_version",
        "content_version",
        "certification_version",
    )
    @classmethod
    def _valid_metadata(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_reconciliation_metadata")

    @field_validator("review_evidence")
    @classmethod
    def _valid_review_evidence(cls, values: list[str]) -> list[str]:
        return [
            _clean_text(
                value,
                error="deep_manifest_reconciliation_review_evidence",
            )
            for value in values
        ]

    @field_validator("base_manifest_sha256")
    @classmethod
    def _valid_manifest_sha(cls, value: str) -> str:
        cleaned = value.strip().casefold()
        if re.fullmatch(r"[0-9a-f]{64}", cleaned) is None:
            raise ValueError("deep_manifest_reconciliation_invalid_manifest_sha")
        return cleaned

    @model_validator(mode="after")
    def _unique_overrides(self) -> "ManifestChapterReconciliation":
        identities = [
            (override.node_id, override.fingerprint)
            for override in self.activity_overrides
        ]
        if len(identities) != len(set(identities)):
            raise ValueError("deep_manifest_reconciliation_duplicate_activity")
        runtime_identities = [override.runtime_path for override in self.runtime_activity_overrides]
        if len(runtime_identities) != len(set(runtime_identities)):
            raise ValueError("deep_manifest_reconciliation_duplicate_runtime_activity")
        return self


class ManifestReconciliationRegistry(_StrictModel):
    schema_version: Literal[MANIFEST_RECONCILIATION_SCHEMA_VERSION]
    chapters: list[ManifestChapterReconciliation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_chapter_ids(self) -> "ManifestReconciliationRegistry":
        chapter_ids = [chapter.chapter_id for chapter in self.chapters]
        if len(chapter_ids) != len(set(chapter_ids)):
            raise ValueError("deep_manifest_reconciliation_duplicate_chapter")
        return self


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
    source_anchor_ids_override: list[str] | None = None
    knowledge_components_override: list[str] | None = None

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

    @field_validator("source_anchor_ids_override")
    @classmethod
    def _valid_source_anchor_ids(cls, values: list[str] | None) -> list[str] | None:
        return _clean_optional_identifiers(
            values,
            error="invalid_deep_manifest_connect_source_anchor_ids",
        )

    @field_validator("knowledge_components_override")
    @classmethod
    def _valid_knowledge_components(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        return _clean_optional_identifiers(
            values,
            error="invalid_deep_manifest_connect_knowledge_components",
        )


class ChoiceActivitySpec(_StrictModel):
    kind: Literal["selected_option"]
    activity_id: str
    teaching_block: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(default_factory=list)
    options: list[str] = Field(min_length=2)
    accepted_answers: list[str] = Field(min_length=1)
    target_misconception_tags: list[str] | None = None
    wrong_answer_misconception_tags: dict[str, list[str]] | None = None
    success_feedback: str | None = None
    evidence_role_override: LiveEvidenceRole | None = None
    teaching_phase_override: LiveTeachingPhase | None = None
    source_anchor_ids_override: list[str] | None = None

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

    @field_validator("skill_ids", "target_misconception_tags")
    @classmethod
    def _valid_skill_ids(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
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

    @field_validator("wrong_answer_misconception_tags")
    @classmethod
    def _valid_wrong_answer_tags(
        cls,
        value: dict[str, list[str]] | None,
    ) -> dict[str, list[str]] | None:
        if value is None:
            return None
        return {
            _clean_text(option, error="deep_manifest_wrong_option_empty"): _clean_identifiers(
                tags,
                error="invalid_deep_manifest_wrong_answer_tags",
            )
            for option, tags in value.items()
        }

    @field_validator("success_feedback")
    @classmethod
    def _valid_success_feedback(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_text(value, error="deep_manifest_success_feedback_empty")

    @field_validator("source_anchor_ids_override")
    @classmethod
    def _valid_source_anchor_ids(cls, values: list[str] | None) -> list[str] | None:
        return _clean_optional_identifiers(
            values,
            error="invalid_deep_manifest_activity_source_anchor_ids",
        )

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
        if self.wrong_answer_misconception_tags is not None:
            wrong_options = set(self.options).difference(self.accepted_answers)
            if set(self.wrong_answer_misconception_tags) != wrong_options:
                raise ValueError("deep_manifest_wrong_answer_tags_require_all_wrong_options")
            allowed_tags = set(self.target_misconception_tags or ())
            if not allowed_tags or any(
                not set(tags).issubset(allowed_tags)
                for tags in self.wrong_answer_misconception_tags.values()
            ):
                raise ValueError("deep_manifest_wrong_answer_tag_not_authored")
        return self


class OpenActivitySpec(_StrictModel):
    kind: Literal["open_response"]
    activity_id: str
    teaching_block: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(default_factory=list)
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
    concept_slots: list[LiveConceptSlot] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(min_length=1)
    min_response_words: int = Field(ge=2, le=100)
    ordered_concept_slot_ids: list[str] | None = Field(default=None, min_length=2)
    relevance_terms: list[str] = Field(min_length=2)
    model_answer: str
    pass_score: float = Field(default=0.8, ge=0.6, le=1.0)
    preflight_rule: str = "relevant_english_response"
    semantic_evidence_policy: SemanticEvidencePolicy | None = None
    semantic_validator_id: SchoolOpenSemanticValidatorId | None = None
    actor_action_receiver_slot_ids: list[str] | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )
    target_misconception_tags: list[str] | None = None
    criterion_misconception_tags: dict[str, list[str]] | None = None
    success_feedback: str | None = None
    evidence_role_override: LiveEvidenceRole | None = None
    teaching_phase_override: LiveTeachingPhase | None = None
    source_anchor_ids_override: list[str] | None = None

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

    @field_validator("success_feedback")
    @classmethod
    def _valid_success_feedback(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_text(value, error="deep_manifest_success_feedback_empty")

    @field_validator("skill_ids", "target_misconception_tags")
    @classmethod
    def _valid_skill_ids(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return _clean_identifiers(
            values,
            error="invalid_deep_manifest_activity_skill_ids",
        )

    @field_validator("source_anchor_ids_override")
    @classmethod
    def _valid_source_anchor_ids(cls, values: list[str] | None) -> list[str] | None:
        return _clean_optional_identifiers(
            values,
            error="invalid_deep_manifest_activity_source_anchor_ids",
        )

    @field_validator("criterion_misconception_tags")
    @classmethod
    def _valid_criterion_tags(
        cls,
        value: dict[str, list[str]] | None,
    ) -> dict[str, list[str]] | None:
        if value is None:
            return None
        return {
            _clean_text(criterion_id, error="deep_manifest_criterion_id_empty"): _clean_identifiers(
                tags,
                error="invalid_deep_manifest_criterion_tags",
            )
            for criterion_id, tags in value.items()
        }

    @field_validator(
        "forbidden_phrases",
        "relevance_terms",
        "ordered_concept_slot_ids",
        "actor_action_receiver_slot_ids",
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
        if slot_ids and not set(slot_ids).issubset(set(criterion_ids)):
            raise ValueError("deep_manifest_rubric_slot_ids_must_match_in_order")
        if self.ordered_concept_slot_ids and not set(
            self.ordered_concept_slot_ids
        ).issubset(set(slot_ids)):
            raise ValueError("deep_manifest_unknown_ordered_concept_slot")
        if (
            self.semantic_evidence_policy == "traceable_rubric"
            and self.ordered_concept_slot_ids
        ):
            raise ValueError(
                "deep_manifest_traceable_rubric_forbids_ordered_semantic_guards"
            )
        if (
            self.semantic_evidence_policy == "traceable_rubric"
            and self.semantic_validator_id is not None
        ):
            raise ValueError(
                "deep_manifest_traceable_rubric_forbids_structured_semantic_guards"
            )
        if (
            self.semantic_evidence_policy == "traceable_rubric"
            and self.actor_action_receiver_slot_ids is not None
        ):
            raise ValueError(
                "deep_manifest_traceable_rubric_forbids_structured_semantic_guards"
            )
        if self.actor_action_receiver_slot_ids is not None:
            if (
                self.ordered_concept_slot_ids is None
                or self.ordered_concept_slot_ids[:3]
                != self.actor_action_receiver_slot_ids
            ):
                raise ValueError(
                    "deep_manifest_actor_action_receiver_slots_require_ordered_prefix"
                )
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
        if self.criterion_misconception_tags is not None:
            allowed_tags = set(self.target_misconception_tags or ())
            if not allowed_tags or not set(
                self.criterion_misconception_tags
            ).issubset(set(criterion_ids)):
                raise ValueError("deep_manifest_criterion_tag_not_authored")
            if any(
                not set(tags).issubset(allowed_tags)
                for tags in self.criterion_misconception_tags.values()
            ):
                raise ValueError("deep_manifest_criterion_tag_not_authored")
            if "clear_relevant_english" in self.criterion_misconception_tags:
                raise ValueError("deep_manifest_generic_criterion_tag_forbidden")
        return self


class ExactTextActivitySpec(_StrictModel):
    """An authored short deterministic response such as a spelling correction."""

    kind: Literal["exact_text"]
    activity_id: str
    teaching_block: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(default_factory=list)
    interaction_type: Literal["cloze"]
    accepted_answers: list[str] = Field(min_length=1)
    target_misconception_tags: list[str] | None = None
    evidence_role_override: LiveEvidenceRole | None = None
    teaching_phase_override: LiveTeachingPhase | None = None
    source_anchor_ids_override: list[str] | None = None

    @field_validator("activity_id")
    @classmethod
    def _valid_activity_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_id_empty")

    @field_validator("teaching_block", "passage")
    @classmethod
    def _substantial_copy(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_copy_too_shallow", minimum=20)

    @field_validator("prompt")
    @classmethod
    def _substantial_prompt(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_prompt_too_shallow", minimum=10)

    @field_validator("skill_ids", "target_misconception_tags")
    @classmethod
    def _valid_identifiers(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return _clean_identifiers(values, error="invalid_deep_manifest_activity_skill_ids")

    @field_validator("source_anchor_ids_override")
    @classmethod
    def _valid_source_anchor_ids(cls, values: list[str] | None) -> list[str] | None:
        return _clean_optional_identifiers(
            values,
            error="invalid_deep_manifest_activity_source_anchor_ids",
        )

    @field_validator("accepted_answers")
    @classmethod
    def _valid_answers(cls, values: list[str]) -> list[str]:
        cleaned = [_clean_text(value, error="deep_manifest_answer_empty") for value in values]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("duplicate_deep_manifest_answer")
        if any(len(answer.split()) > 12 or "\n" in answer for answer in cleaned):
            raise ValueError("deep_manifest_exact_text_requires_short_answers")
        return cleaned


class OrderedSlotsActivitySpec(_StrictModel):
    """An authored deterministic ordering task with an explicit slot contract."""

    kind: Literal["ordered_slots"]
    activity_id: str
    teaching_block: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(default_factory=list)
    interaction_type: Literal["ordering"]
    concept_slots: list[LiveConceptSlot] = Field(min_length=2)
    ordered_concept_slot_ids: list[str] = Field(min_length=2)
    target_misconception_tags: list[str] | None = None
    evidence_role_override: LiveEvidenceRole | None = None
    teaching_phase_override: LiveTeachingPhase | None = None
    source_anchor_ids_override: list[str] | None = None

    @field_validator("activity_id")
    @classmethod
    def _valid_activity_id(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_id_empty")

    @field_validator("teaching_block", "passage")
    @classmethod
    def _substantial_copy(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_copy_too_shallow", minimum=20)

    @field_validator("prompt")
    @classmethod
    def _substantial_prompt(cls, value: str) -> str:
        return _clean_text(value, error="deep_manifest_activity_prompt_too_shallow", minimum=10)

    @field_validator(
        "skill_ids",
        "target_misconception_tags",
        "ordered_concept_slot_ids",
    )
    @classmethod
    def _valid_identifiers(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return _clean_identifiers(values, error="invalid_deep_manifest_activity_skill_ids")

    @field_validator("source_anchor_ids_override")
    @classmethod
    def _valid_source_anchor_ids(cls, values: list[str] | None) -> list[str] | None:
        return _clean_optional_identifiers(
            values,
            error="invalid_deep_manifest_activity_source_anchor_ids",
        )

    @model_validator(mode="after")
    def _slots_are_complete_and_ordered(self) -> "OrderedSlotsActivitySpec":
        slot_ids = [slot.id for slot in self.concept_slots]
        if self.ordered_concept_slot_ids != slot_ids:
            raise ValueError("deep_manifest_ordered_slots_require_all_slot_ids")
        return self


AuthoredActivitySpec: TypeAlias = Annotated[
    ChoiceActivitySpec
    | OpenActivitySpec
    | ExactTextActivitySpec
    | OrderedSlotsActivitySpec,
    Field(discriminator="kind"),
]


class SupportChecksSpec(_StrictModel):
    # Most levels reuse the co-construction choice as their low-stakes guided
    # check. A distinct authored choice is required when co-construction is an
    # open discussion, ordering task, or another interaction that is not a
    # valid guided check under the live learner contract.
    guided_check: ChoiceActivitySpec | None = None
    # A reviewed release can pin separate certifying checks when the first
    # pool item is not the cleanest diagnostic of the same outcome.
    independent_check: AuthoredActivitySpec | None = None
    transfer_check: AuthoredActivitySpec | None = None
    bridge: AuthoredActivitySpec
    masterclass: AuthoredActivitySpec
    revision_level_1: AuthoredActivitySpec
    revision_level_2: AuthoredActivitySpec
    revision_level_3: AuthoredActivitySpec
    revision_level_4: AuthoredActivitySpec | None = None

    def activities(self) -> dict[str, AuthoredActivitySpec]:
        checks: dict[str, AuthoredActivitySpec] = {
            "bridge": self.bridge,
            "masterclass": self.masterclass,
            "revision_level_1": self.revision_level_1,
            "revision_level_2": self.revision_level_2,
            "revision_level_3": self.revision_level_3,
        }
        if self.revision_level_4 is not None:
            checks["revision_level_4"] = self.revision_level_4
        return checks


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
    independent_variants: list[AuthoredActivitySpec] = Field(min_length=4)
    transfer_variants: list[AuthoredActivitySpec] = Field(min_length=3)
    review_variants: list[AuthoredActivitySpec] = Field(min_length=2)
    guided_pool_id: str | None = None
    independent_pool_id: str | None = None
    transfer_pool_id: str | None = None
    review_pool_id: str | None = None
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

    @field_validator(
        "guided_pool_id",
        "independent_pool_id",
        "transfer_pool_id",
        "review_pool_id",
    )
    @classmethod
    def _valid_pool_ids(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_text(value, error="deep_manifest_pool_id_empty")

    @model_validator(mode="after")
    def _complete_authored_depth(self) -> "DeepLevelManifest":
        support = self.support_checks.activities()
        diagnostic_checks = [
            check
            for check in (
                self.support_checks.guided_check,
                self.support_checks.independent_check,
                self.support_checks.transfer_check,
            )
            if check is not None
        ]
        activities: list[AuthoredActivitySpec] = [
            self.co_construct,
            *self.guided_variants,
            *self.independent_variants,
            *self.transfer_variants,
            *self.review_variants,
            *diagnostic_checks,
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
    release_runtime_overrides: list[RuntimeActivityReconciliation] = Field(
        default_factory=list
    )

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
        chapter_activity_ids = [
            activity.activity_id
            for level in self.levels
            for activity in (
                level.co_construct,
                *level.guided_variants,
                *level.independent_variants,
                *level.transfer_variants,
                *level.review_variants,
                *level.support_checks.activities().values(),
            )
        ] + [item.activity_id for item in self.chapter_assessment.items]
        if len(chapter_activity_ids) != len(set(chapter_activity_ids)):
            raise ValueError("duplicate_deep_manifest_chapter_activity_id")
        return self


def _load_raw_manifest(path: str | Path) -> DeepChapterManifest:
    """Load a JSON manifest or Python ``MANIFEST`` without release overlays."""

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


def _iter_manifest_open_activities(
    payload: object,
) -> list[dict[str, Any]]:
    """Return mutable authored open-response nodes from a dumped manifest."""

    activities: list[dict[str, Any]] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if (
                value.get("kind") == "open_response"
                and isinstance(value.get("activity_id"), str)
                and isinstance(value.get("passage"), str)
                and isinstance(value.get("prompt"), str)
                and isinstance(value.get("model_answer"), str)
            ):
                activities.append(value)
                return
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return activities


@lru_cache(maxsize=1)
def _load_manifest_reconciliation_registry() -> ManifestReconciliationRegistry:
    if not MANIFEST_RECONCILIATION_PATH.is_file():
        raise ValueError("deep_manifest_reconciliation_registry_missing")
    raw = json.loads(MANIFEST_RECONCILIATION_PATH.read_text(encoding="utf-8"))
    return ManifestReconciliationRegistry.model_validate(raw)


def apply_manifest_reconciliation(
    manifest: DeepChapterManifest,
    registry: ManifestReconciliationRegistry,
) -> DeepChapterManifest:
    """Apply a checked release overlay to a canonical authored manifest.

    The registry is deliberately narrow: it can only attach reviewed semantic
    evidence policy or author-only success feedback to an exact source prompt.
    A raw-manifest digest and activity fingerprint make silent drift fail fast.
    """

    record = next(
        (
            item
            for item in registry.chapters
            if item.chapter_id == manifest.chapter.chapter_id
        ),
        None,
    )
    if record is None:
        return manifest

    # Optional source fields evolve over time. Omit absent values so adding a
    # backward-compatible field does not invalidate the hash of every older
    # canonical manifest and its reviewed release overlay.
    payload = manifest.model_dump(mode="json", exclude_none=True)
    actual_manifest_sha = _canonical_sha256(payload)
    if actual_manifest_sha != record.base_manifest_sha256:
        raise ValueError(
            "deep_manifest_reconciliation_base_sha_mismatch:"
            + manifest.chapter.chapter_id
        )
    if payload["chapter"]["content_version"] != record.base_content_version:
        raise ValueError(
            "deep_manifest_reconciliation_base_content_version_mismatch:"
            + manifest.chapter.chapter_id
        )
    if (
        payload["chapter"]["certification_version"]
        != record.base_certification_version
    ):
        raise ValueError(
            "deep_manifest_reconciliation_base_certification_version_mismatch:"
            + manifest.chapter.chapter_id
        )

    activities = _iter_manifest_open_activities(payload)
    applied: set[tuple[str, str]] = set()
    for override in record.activity_overrides:
        matches = [
            activity
            for activity in activities
            if activity["activity_id"] == override.node_id
            and manifest_activity_fingerprint(activity) == override.fingerprint
        ]
        if len(matches) != 1:
            reason = "missing" if not matches else "ambiguous"
            raise ValueError(
                "deep_manifest_reconciliation_activity_"
                + reason
                + ":"
                + manifest.chapter.chapter_id
                + ":"
                + override.node_id
            )
        activity = matches[0]
        activity["semantic_evidence_policy"] = override.semantic_evidence_policy
        applied.add((override.node_id, override.fingerprint))

    if len(applied) != len(record.activity_overrides):
        raise RuntimeError("deep_manifest_reconciliation_apply_incomplete")
    if payload["release_runtime_overrides"]:
        raise ValueError(
            "deep_manifest_reconciliation_source_runtime_overrides_forbidden:"
            + manifest.chapter.chapter_id
        )
    payload["release_runtime_overrides"] = [
        override.model_dump(mode="json")
        for override in record.runtime_activity_overrides
    ]
    payload["chapter"]["content_version"] = record.content_version
    payload["chapter"]["certification_version"] = record.certification_version
    # Class 2-4 manifests are validated subclasses with their own literal
    # schema version. Preserve that contract instead of coercing every
    # reconciled payload through the Class 5 base type.
    return type(manifest).model_validate(payload)


def load_manifest(
    path: str | Path,
    *,
    apply_reconciliation: bool = True,
) -> DeepChapterManifest:
    """Load a canonical manifest, then apply its checked release overlay."""

    manifest = _load_raw_manifest(path)
    if not apply_reconciliation:
        return manifest
    manifest_path = Path(path).resolve()
    try:
        is_canonical_manifest = manifest_path.is_relative_to(MANIFEST_ROOT)
    except AttributeError:  # pragma: no cover - Python 3.8 compatibility guard.
        is_canonical_manifest = str(manifest_path).startswith(str(MANIFEST_ROOT))
    if not is_canonical_manifest:
        return manifest
    return apply_manifest_reconciliation(
        manifest,
        _load_manifest_reconciliation_registry(),
    )


def _activity_payload(
    *,
    spec: AuthoredActivitySpec,
    level: DeepLevelManifest,
    phase: str,
    evidence_role: Literal["formative", "supported", "certifying"],
    pool_id: str | None = None,
    target_misconception_tags: list[str] | None = None,
) -> dict[str, Any]:
    resolved_evidence_role = spec.evidence_role_override or evidence_role
    resolved_teaching_phase = spec.teaching_phase_override or phase
    allowed_anchor_ids = {
        *level.source_anchor_ids,
        *level.companion_source_anchor_ids,
    }
    resolved_source_anchor_ids = (
        spec.source_anchor_ids_override or list(level.source_anchor_ids)
    )
    if not set(resolved_source_anchor_ids).issubset(allowed_anchor_ids):
        raise ValueError("deep_manifest_activity_source_anchor_outside_level")
    payload: dict[str, Any] = {
        "teaching_block": spec.teaching_block,
        "passage": spec.passage,
        "prompt": spec.prompt,
        "schema_version": ACTIVITY_SCHEMA_VERSION,
        "episode_kind": level.episode_kind,
        "teaching_phase": resolved_teaching_phase,
        "interaction_type": (
            "single_choice"
            if isinstance(spec, ChoiceActivitySpec)
            else spec.interaction_type
        ),
        "evidence_role": resolved_evidence_role,
        "source_anchor_ids": resolved_source_anchor_ids,
        "knowledge_components": list(spec.skill_ids),
    }
    explicit_target_tags = getattr(spec, "target_misconception_tags", None)
    resolved_target_tags = (
        explicit_target_tags
        if explicit_target_tags is not None
        else target_misconception_tags
    )
    if resolved_target_tags:
        payload["target_misconception_tags"] = list(
            dict.fromkeys(resolved_target_tags)
        )
    if pool_id is not None:
        payload["pool_id"] = pool_id
        payload["variant_id"] = spec.activity_id
    if resolved_evidence_role == "certifying":
        payload["certifying_language"] = "en"

    if isinstance(spec, ChoiceActivitySpec):
        payload.update(
            options=list(spec.options),
            accepted_answers=list(spec.accepted_answers),
            grading_mode="selected_option",
            response_mode="short",
        )
        if spec.wrong_answer_misconception_tags is not None:
            payload["wrong_answer_misconception_tags"] = {
                option: list(tags)
                for option, tags in spec.wrong_answer_misconception_tags.items()
            }
        if spec.success_feedback is not None:
            payload["success_feedback"] = spec.success_feedback
        return payload

    if isinstance(spec, ExactTextActivitySpec):
        payload.update(
            options=[],
            accepted_answers=list(spec.accepted_answers),
            grading_mode="exact_text",
            response_mode="short",
        )
        return payload

    if isinstance(spec, OrderedSlotsActivitySpec):
        payload.update(
            options=[],
            accepted_answers=[],
            grading_mode="ordered_slots",
            answer_rule="concept_slots",
            concept_slots=[slot.model_dump() for slot in spec.concept_slots],
            ordered_concept_slot_ids=list(spec.ordered_concept_slot_ids),
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
        forbidden_phrases=list(spec.forbidden_phrases),
        min_response_words=spec.min_response_words,
        relevance_terms=list(spec.relevance_terms),
        model_answer=spec.model_answer,
    )
    if spec.concept_slots:
        payload["concept_slots"] = [slot.model_dump() for slot in spec.concept_slots]
    if spec.semantic_evidence_policy is not None:
        payload["semantic_evidence_policy"] = spec.semantic_evidence_policy
    if spec.semantic_validator_id is not None:
        payload["semantic_validator_id"] = spec.semantic_validator_id
    if spec.actor_action_receiver_slot_ids is not None:
        payload["actor_action_receiver_slot_ids"] = list(
            spec.actor_action_receiver_slot_ids
        )
    if spec.criterion_misconception_tags is not None:
        payload["criterion_misconception_tags"] = {
            criterion_id: list(tags)
            for criterion_id, tags in spec.criterion_misconception_tags.items()
        }
    if spec.success_feedback is not None:
        payload["success_feedback"] = spec.success_feedback
    if spec.ordered_concept_slot_ids:
        payload["ordered_concept_slot_ids"] = list(
            spec.ordered_concept_slot_ids
        )
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

    if isinstance(spec, ExactTextActivitySpec):
        payload.update(
            options=[],
            accepted_answers=list(spec.accepted_answers),
            grading_mode="exact_text",
            response_mode="short",
        )
        return payload

    if isinstance(spec, OrderedSlotsActivitySpec):
        payload.update(
            options=[],
            accepted_answers=[],
            grading_mode="ordered_slots",
            answer_rule="concept_slots",
            concept_slots=[slot.model_dump() for slot in spec.concept_slots],
            ordered_concept_slot_ids=list(spec.ordered_concept_slot_ids),
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
        forbidden_phrases=list(spec.forbidden_phrases),
        min_response_words=spec.min_response_words,
        relevance_terms=list(spec.relevance_terms),
        model_answer=spec.model_answer,
    )
    if spec.concept_slots:
        payload["concept_slots"] = [slot.model_dump() for slot in spec.concept_slots]
    if spec.semantic_evidence_policy is not None:
        payload["semantic_evidence_policy"] = spec.semantic_evidence_policy
    if spec.semantic_validator_id is not None:
        payload["semantic_validator_id"] = spec.semantic_validator_id
    if spec.actor_action_receiver_slot_ids is not None:
        payload["actor_action_receiver_slot_ids"] = list(
            spec.actor_action_receiver_slot_ids
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
    available_anchor_ids = [
        *level.source_anchor_ids,
        *level.companion_source_anchor_ids,
    ]
    connect_anchor_ids = level.connect.source_anchor_ids_override or list(
        dict.fromkeys(available_anchor_ids)
    )
    if not set(connect_anchor_ids).issubset(set(available_anchor_ids)):
        raise ValueError("deep_manifest_connect_source_anchor_outside_level")
    connect_knowledge_components = (
        level.connect.knowledge_components_override
        if level.connect.knowledge_components_override is not None
        else list(level.skill_ids)
    )
    if not set(connect_knowledge_components).issubset(set(level.skill_ids)):
        raise ValueError("deep_manifest_connect_skill_outside_level")
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
            "knowledge_components": connect_knowledge_components,
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
    pool_id: str | None = None,
) -> dict[str, Any]:
    resolved_pool_id = pool_id or f"{level.level_id}:{phase}"
    return {
        "step_id": f"{level.level_id}:{phase}",
        "phase": phase,
        "required": True,
        "pool_id": resolved_pool_id,
        "variant_pool": [
            _activity_payload(
                spec=spec,
                level=level,
                phase=phase,
                evidence_role=evidence_role,
                pool_id=resolved_pool_id,
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
            pool_id=level.guided_pool_id,
        ),
        _pool_step(
            level=level,
            phase="independent_application",
            specs=list(level.independent_variants),
            evidence_role="certifying",
            pool_id=level.independent_pool_id,
        ),
        _pool_step(
            level=level,
            phase="transfer",
            specs=list(level.transfer_variants),
            evidence_role="certifying",
            pool_id=level.transfer_pool_id,
        ),
        _pool_step(
            level=level,
            phase="review",
            specs=list(level.review_variants),
            evidence_role="certifying",
            pool_id=level.review_pool_id,
        ),
    ]
    if tuple(step["phase"] for step in steps) != COMPACT_PHASES:
        raise RuntimeError("deep_chapter_phase_sequence_internal_error")
    return steps


def build_level_checks(level: DeepLevelManifest) -> dict[str, Any]:
    support = level.support_checks.activities()
    guided_check = level.support_checks.guided_check or level.co_construct
    independent_check = (
        level.support_checks.independent_check or level.independent_variants[0]
    )
    transfer_check = level.support_checks.transfer_check or level.transfer_variants[0]
    checks: dict[str, Any] = {
        "guided_check": _activity_payload(
            spec=guided_check,
            level=level,
            phase="co_construct",
            evidence_role="formative",
            target_misconception_tags=_clusters_for_activity(
                level, guided_check
            ),
        ),
        "independent_check": _activity_payload(
            spec=independent_check,
            level=level,
            phase="independent_application",
            evidence_role="certifying",
        ),
        "transfer_check": _activity_payload(
            spec=transfer_check,
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


def _runtime_activity_at_path(
    payload: dict[str, Any],
    runtime_path: str,
) -> dict[str, Any]:
    current: Any = payload
    for segment in runtime_path.removeprefix("/").split("/"):
        if isinstance(current, dict):
            if segment not in current:
                raise ValueError(
                    "deep_manifest_reconciliation_runtime_path_missing:"
                    + runtime_path
                )
            current = current[segment]
        elif isinstance(current, list):
            if not segment.isdigit() or int(segment) >= len(current):
                raise ValueError(
                    "deep_manifest_reconciliation_runtime_path_missing:"
                    + runtime_path
                )
            current = current[int(segment)]
        else:
            raise ValueError(
                "deep_manifest_reconciliation_runtime_path_not_container:"
                + runtime_path
            )
    if not isinstance(current, dict):
        raise ValueError(
            "deep_manifest_reconciliation_runtime_path_not_activity:"
            + runtime_path
        )
    return current


def _apply_runtime_activity_overrides(
    payload: dict[str, Any],
    overrides: list[RuntimeActivityReconciliation],
) -> None:
    for override in overrides:
        activity = _runtime_activity_at_path(payload, override.runtime_path)
        if manifest_activity_fingerprint(activity) != override.fingerprint:
            raise ValueError(
                "deep_manifest_reconciliation_runtime_fingerprint_mismatch:"
                + override.runtime_path
            )
        if override.semantic_evidence_policy is not None:
            activity["semantic_evidence_policy"] = override.semantic_evidence_policy
        if override.success_feedback is not None:
            activity["success_feedback"] = override.success_feedback
        if override.target_misconception_tags is not None:
            activity["target_misconception_tags"] = list(
                override.target_misconception_tags
            )


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

    existing_release_metadata = (
        {
            "approval_status": chapter.approval_status,
            "reviewed_by": chapter.reviewed_by,
            "reviewed_at": chapter.reviewed_at,
            "review_evidence": list(chapter.review_evidence),
        }
        if chapter is not None
        else {
            "approval_status": "draft",
            "reviewed_by": None,
            "reviewed_at": None,
            "review_evidence": [],
        }
    )
    result: dict[str, Any] = {
        **existing_release_metadata,
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
    _apply_runtime_activity_overrides(result, manifest.release_runtime_overrides)

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
