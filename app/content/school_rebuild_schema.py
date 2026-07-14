"""Strict authoring contract for chapters served by the rebuilt School tutor."""

from __future__ import annotations

import hashlib
import json
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


LiveDeterministicAnswerRule = Literal[
    "concept_slots",
    "past_tense_travel_sentence",
    "wise_parrot_reason",
    "release_opinion_reason",
    "bird_feeder_procedure",
]

LiveEpisodeKind = Literal[
    "meaning_encounter",
    "comprehension_studio",
    "language_lab",
    "expression_workshop",
    "application_mission",
    "retrieval_challenge",
]
LiveTeachingPhase = Literal[
    "connect",
    "explain",
    "model",
    "co_construct",
    "guided_practice",
    "feedback",
    "independent_application",
]
LiveInteractionType = Literal[
    "continue",
    "single_choice",
    "multi_select",
    "cloze",
    "matching",
    "ordering",
    "classification",
    "sentence_completion",
    "short_text",
    "evidence_text",
    "paragraph_text",
    "dialogue",
    "creative_continuation",
    "summary",
    "reflection",
]
LiveEvidenceRole = Literal[
    "experience",
    "formative",
    "supported",
    "certifying",
    "reflection",
]
LiveCoverageTreatment = Literal[
    "taught_and_assessed",
    "zidd_equivalent",
    "textbook_companion",
    "guided_only",
    "optional_creative",
    "offline_group_activity",
]


class LiveSourceAnchor(BaseModel):
    """Public metadata that links an activity to the official book.

    The anchor deliberately stores no textbook body text. It only records the
    source location and how Zidd accounts for that part of the curriculum.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    anchor_id: str
    section_label: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    source_url: str
    coverage_treatment: LiveCoverageTreatment
    required_for_chapter_certification: bool = False

    @field_validator("anchor_id", "section_label", "source_url")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_source_anchor_field_empty")
        return cleaned

    @field_validator("source_url")
    @classmethod
    def _official_ncert_source(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in {
            "ncert.nic.in",
            "www.ncert.nic.in",
        }:
            raise ValueError("live_source_anchor_requires_official_ncert_url")
        return value

    @model_validator(mode="after")
    def _valid_page_range(self) -> "LiveSourceAnchor":
        if self.page_end < self.page_start:
            raise ValueError("live_source_anchor_page_range_invalid")
        return self


class LiveRubricCriterion(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: str
    description: str
    required: bool = True
    min_quality: float = Field(default=0.6, ge=0.0, le=1.0)

    @field_validator("id", "description")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_rubric_field_empty")
        return cleaned


class LiveConceptSlot(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: str
    description: str
    any_of: list[str] = Field(min_length=1)

    @field_validator("id", "description")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_concept_slot_field_empty")
        return cleaned

    @field_validator("any_of")
    @classmethod
    def _clean_any_of(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("invalid_live_concept_slot_any_of")
        return cleaned


class LiveChapterActivity(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    teaching_block: str
    passage: str
    prompt: str
    options: list[str]
    accepted_answers: list[str]
    response_mode: Literal["short", "paragraph"] | None = None
    answer_rule: LiveDeterministicAnswerRule | None = None
    evaluation_mode: Literal["llm_rubric"] | None = None
    preflight_rule: str | None = None
    pass_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rubric_criteria: list[LiveRubricCriterion] | None = None
    concept_slots: list[LiveConceptSlot] | None = None
    forbidden_phrases: list[str] | None = None
    min_response_words: int | None = Field(
        default=None,
        strict=True,
        ge=2,
        le=100,
    )
    ordered_concept_slot_ids: list[str] | None = Field(
        default=None,
        min_length=2,
    )
    schema_version: Literal["school-activity-v2"] | None = None
    episode_kind: LiveEpisodeKind | None = None
    teaching_phase: LiveTeachingPhase | None = None
    interaction_type: LiveInteractionType | None = None
    evidence_role: LiveEvidenceRole | None = None
    source_anchor_ids: list[str] | None = None
    knowledge_components: list[str] | None = None

    @field_validator("teaching_block", "passage", "prompt")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_activity_text_empty")
        return cleaned

    @field_validator("answer_rule", "preflight_rule", mode="before")
    @classmethod
    def _clean_optional_text(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_activity_text_empty")
        return cleaned

    @field_validator("options", "accepted_answers")
    @classmethod
    def _clean_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("live_activity_list_value_empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("live_activity_list_value_duplicate")
        return cleaned

    @field_validator("source_anchor_ids", "knowledge_components")
    @classmethod
    def _clean_v2_identifiers(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("invalid_live_activity_v2_identifiers")
        return cleaned

    @field_validator("forbidden_phrases")
    @classmethod
    def _clean_forbidden_phrases(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("invalid_live_concept_forbidden_phrases")
        return cleaned

    @field_validator("concept_slots")
    @classmethod
    def _unique_concept_slot_ids(
        cls,
        values: list[LiveConceptSlot] | None,
    ) -> list[LiveConceptSlot] | None:
        if values is None:
            return None
        slot_ids = [slot.id for slot in values]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("duplicate_live_concept_slot_id")
        return values

    @field_validator("ordered_concept_slot_ids")
    @classmethod
    def _clean_ordered_concept_slot_ids(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("invalid_live_ordered_concept_slot_id")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("duplicate_live_ordered_concept_slot_id")
        return cleaned

    @field_validator("rubric_criteria")
    @classmethod
    def _unique_rubric_criterion_ids(
        cls,
        values: list[LiveRubricCriterion] | None,
    ) -> list[LiveRubricCriterion] | None:
        if values is None:
            return None
        criterion_ids = [criterion.id for criterion in values]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("duplicate_live_rubric_criterion_id")
        return values

    @model_validator(mode="after")
    def _valid_grading_contract(self) -> "LiveChapterActivity":
        v2_fields = (
            self.episode_kind,
            self.teaching_phase,
            self.interaction_type,
            self.evidence_role,
            self.source_anchor_ids,
            self.knowledge_components,
        )
        if any(value is not None for value in v2_fields):
            if self.schema_version != "school-activity-v2" or any(
                value is None
                for value in (
                    self.episode_kind,
                    self.teaching_phase,
                    self.interaction_type,
                    self.evidence_role,
                )
            ):
                raise ValueError("incomplete_live_activity_v2_contract")
        elif self.schema_version is not None:
            raise ValueError("empty_live_activity_v2_contract")
        has_concept_fields = (
            self.concept_slots is not None
            or self.forbidden_phrases is not None
            or self.min_response_words is not None
            or self.ordered_concept_slot_ids is not None
        )
        if self.evaluation_mode == "llm_rubric":
            if has_concept_fields:
                raise ValueError("live_concept_fields_require_concept_slots_rule")
            if (
                self.response_mode != "paragraph"
                or not self.preflight_rule
                or self.pass_score is None
                or not self.rubric_criteria
                or self.answer_rule
                or self.accepted_answers
            ):
                raise ValueError("invalid_live_open_answer_contract")
        else:
            if (
                self.preflight_rule is not None
                or self.pass_score is not None
                or self.rubric_criteria is not None
            ):
                raise ValueError("live_activity_deterministic_forbids_llm_fields")
            if self.answer_rule == "concept_slots":
                if not self.concept_slots or self.accepted_answers:
                    raise ValueError("live_concept_slots_rule_requires_slots")
                if not self.options and self.min_response_words is None:
                    raise ValueError(
                        "live_constructed_concept_response_requires_min_words"
                    )
                slot_ids = {slot.id for slot in self.concept_slots}
                if self.ordered_concept_slot_ids and not set(
                    self.ordered_concept_slot_ids
                ).issubset(slot_ids):
                    raise ValueError("unknown_live_ordered_concept_slot_id")
            elif has_concept_fields:
                raise ValueError("live_concept_fields_require_concept_slots_rule")
            has_accepted_answers = bool(self.accepted_answers)
            has_answer_rule = self.answer_rule is not None
            if has_accepted_answers == has_answer_rule:
                raise ValueError(
                    "live_activity_deterministic_grading_requires_exactly_one"
                )
        return self

    def runtime_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


class LiveTeachingStep(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    step_id: str
    phase: LiveTeachingPhase
    required: bool = True
    activity: LiveChapterActivity

    @field_validator("step_id")
    @classmethod
    def _non_empty_step_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_teaching_step_id_empty")
        return cleaned

    @model_validator(mode="after")
    def _phase_matches_activity(self) -> "LiveTeachingStep":
        if self.activity.teaching_phase != self.phase:
            raise ValueError("live_teaching_step_phase_mismatch")
        return self

    def runtime_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "phase": self.phase,
            "required": self.required,
            "activity": self.activity.runtime_dict(),
        }


class LiveChapterAssessmentItem(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    item_id: str
    passage: str
    prompt: str
    skill_ids: list[str] = Field(min_length=1)
    options: list[str]
    accepted_answers: list[str]
    response_mode: Literal["short", "paragraph"] | None = None
    answer_rule: LiveDeterministicAnswerRule | None = None
    evaluation_mode: Literal["llm_rubric"] | None = None
    preflight_rule: str | None = None
    pass_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rubric_criteria: list[LiveRubricCriterion] | None = None
    concept_slots: list[LiveConceptSlot] | None = None
    forbidden_phrases: list[str] | None = None
    min_response_words: int | None = Field(
        default=None,
        strict=True,
        ge=2,
        le=100,
    )
    ordered_concept_slot_ids: list[str] | None = Field(
        default=None,
        min_length=2,
    )

    @field_validator("item_id", "passage", "prompt")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_assessment_item_text_empty")
        return cleaned

    @field_validator("answer_rule", "preflight_rule", mode="before")
    @classmethod
    def _clean_optional_text(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_assessment_item_text_empty")
        return cleaned

    @field_validator("skill_ids", "options", "accepted_answers")
    @classmethod
    def _clean_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("live_assessment_item_list_value_empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("live_assessment_item_list_value_duplicate")
        return cleaned

    @field_validator("forbidden_phrases")
    @classmethod
    def _clean_forbidden_phrases(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("invalid_live_concept_forbidden_phrases")
        return cleaned

    @field_validator("concept_slots")
    @classmethod
    def _unique_concept_slot_ids(
        cls,
        values: list[LiveConceptSlot] | None,
    ) -> list[LiveConceptSlot] | None:
        if values is None:
            return None
        slot_ids = [slot.id for slot in values]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("duplicate_live_concept_slot_id")
        return values

    @field_validator("ordered_concept_slot_ids")
    @classmethod
    def _clean_ordered_concept_slot_ids(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("invalid_live_ordered_concept_slot_id")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("duplicate_live_ordered_concept_slot_id")
        return cleaned

    @field_validator("rubric_criteria")
    @classmethod
    def _unique_rubric_criterion_ids(
        cls,
        values: list[LiveRubricCriterion] | None,
    ) -> list[LiveRubricCriterion] | None:
        if values is None:
            return None
        criterion_ids = [criterion.id for criterion in values]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("duplicate_live_rubric_criterion_id")
        return values

    @model_validator(mode="after")
    def _valid_options_and_grading_contract(self) -> "LiveChapterAssessmentItem":
        if 0 < len(self.options) < 2:
            raise ValueError("live_assessment_item_options_require_two")
        has_concept_fields = (
            self.concept_slots is not None
            or self.forbidden_phrases is not None
            or self.min_response_words is not None
            or self.ordered_concept_slot_ids is not None
        )
        if self.evaluation_mode == "llm_rubric":
            if has_concept_fields:
                raise ValueError("live_concept_fields_require_concept_slots_rule")
            if (
                self.response_mode != "paragraph"
                or not self.preflight_rule
                or self.pass_score is None
                or not self.rubric_criteria
                or self.answer_rule
                or self.accepted_answers
            ):
                raise ValueError("invalid_live_assessment_open_answer_contract")
        else:
            if (
                self.preflight_rule is not None
                or self.pass_score is not None
                or self.rubric_criteria is not None
            ):
                raise ValueError(
                    "live_assessment_deterministic_forbids_llm_fields"
                )
            if self.answer_rule == "concept_slots":
                if not self.concept_slots or self.accepted_answers:
                    raise ValueError("live_concept_slots_rule_requires_slots")
                if not self.options and self.min_response_words is None:
                    raise ValueError(
                        "live_constructed_concept_response_requires_min_words"
                    )
                slot_ids = {slot.id for slot in self.concept_slots}
                if self.ordered_concept_slot_ids and not set(
                    self.ordered_concept_slot_ids
                ).issubset(slot_ids):
                    raise ValueError("unknown_live_ordered_concept_slot_id")
            elif has_concept_fields:
                raise ValueError("live_concept_fields_require_concept_slots_rule")
            has_accepted_answers = bool(self.accepted_answers)
            has_answer_rule = self.answer_rule is not None
            if has_accepted_answers == has_answer_rule:
                raise ValueError(
                    "live_assessment_deterministic_grading_requires_exactly_one"
                )
        return self

    def runtime_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


class LiveChapterAssessment(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    items_per_attempt: int = Field(default=12, ge=10, le=20)
    pass_score: float = Field(default=0.8, ge=0.6, le=1.0)
    max_attempts: int = Field(default=2, ge=1, le=3)
    items: list[LiveChapterAssessmentItem]

    @model_validator(mode="after")
    def _valid_bank(self) -> "LiveChapterAssessment":
        if len(self.items) < 20:
            raise ValueError("live_chapter_assessment_requires_20_items")
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("duplicate_live_chapter_assessment_item_id")
        if (
            self.max_attempts == 3
            and len(set(item_ids)) < self.max_attempts * self.items_per_attempt
        ):
            raise ValueError(
                "third_attempt_requires_fresh_assessment_item_bank"
            )
        with_options = sum(bool(item.options) for item in self.items)
        without_options = len(self.items) - with_options
        if with_options < 4 or without_options < 4:
            raise ValueError("mixed_live_chapter_assessment_bank_required")
        return self

    def runtime_dict(self) -> dict:
        return {
            "items_per_attempt": self.items_per_attempt,
            "pass_score": self.pass_score,
            "max_attempts": self.max_attempts,
            "items": [item.runtime_dict() for item in self.items],
        }


class LiveChapterChecks(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    guided_check: LiveChapterActivity
    bridge: LiveChapterActivity
    masterclass: LiveChapterActivity
    revision_level_1: LiveChapterActivity | None = None
    revision_level_2: LiveChapterActivity | None = None
    revision_level_3: LiveChapterActivity | None = None
    independent_check: LiveChapterActivity
    transfer_check: LiveChapterActivity | None = None

    @model_validator(mode="after")
    def _pedagogy_stages_are_distinct(self) -> "LiveChapterChecks":
        stages = [
            self.guided_check,
            self.bridge,
            self.masterclass,
            self.independent_check,
        ]
        revisions = [
            self.revision_level_1,
            self.revision_level_2,
            self.revision_level_3,
        ]
        if any(stage is not None for stage in revisions) and not all(
            stage is not None for stage in revisions
        ):
            raise ValueError("authored_revision_sequence_incomplete")
        stages.extend(stage for stage in revisions if stage is not None)
        if self.transfer_check is not None:
            stages.append(self.transfer_check)
        signatures = [
            (stage.teaching_block, stage.passage, stage.prompt)
            for stage in stages
        ]
        if len(signatures) != len(set(signatures)):
            raise ValueError("duplicate_pedagogy_stage")
        if len(self.guided_check.options) < 2:
            raise ValueError("guided_check_requires_options")
        supported_stages = [self.bridge, self.masterclass] + [
            stage for stage in revisions if stage is not None
        ]
        if any(len(stage.options) == 1 for stage in supported_stages):
            raise ValueError(
                "supported_stage_options_must_be_empty_or_multiple"
            )
        if self.independent_check.options:
            raise ValueError("independent_check_must_not_expose_options")
        if self.transfer_check is not None and self.transfer_check.options:
            raise ValueError("transfer_check_must_not_expose_options")
        return self

    def runtime_dict(self) -> dict:
        checks = {
            "guided_check": self.guided_check.runtime_dict(),
            "bridge": self.bridge.runtime_dict(),
            "masterclass": self.masterclass.runtime_dict(),
            "independent_check": self.independent_check.runtime_dict(),
        }
        for revision_no, revision in enumerate(
            (
                self.revision_level_1,
                self.revision_level_2,
                self.revision_level_3,
            ),
            start=1,
        ):
            if revision is not None:
                checks[f"revision_level_{revision_no}"] = revision.runtime_dict()
        if self.transfer_check is not None:
            checks["transfer_check"] = self.transfer_check.runtime_dict()
        return checks


class LiveChapterLevel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    level_id: str
    title: str
    focus: str
    skill_ids: list[str] = Field(min_length=1)
    teaching_goal: str
    checks: LiveChapterChecks
    episode_kind: LiveEpisodeKind | None = None
    source_anchor_ids: list[str] | None = None
    teaching_steps: list[LiveTeachingStep] | None = None

    @field_validator("level_id", "title", "focus", "teaching_goal")
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_level_field_empty")
        return cleaned

    @field_validator("skill_ids")
    @classmethod
    def _clean_skill_ids(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("invalid_live_level_skill_ids")
        return cleaned

    @field_validator("source_anchor_ids")
    @classmethod
    def _clean_source_anchor_ids(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("invalid_live_level_source_anchor_ids")
        return cleaned

    @model_validator(mode="after")
    def _validate_teaching_sequence(self) -> "LiveChapterLevel":
        v2_fields = (self.episode_kind, self.source_anchor_ids, self.teaching_steps)
        if any(value is not None for value in v2_fields):
            if any(value is None for value in v2_fields):
                raise ValueError("incomplete_live_level_v2_contract")
        else:
            return self

        assert self.episode_kind is not None
        assert self.source_anchor_ids is not None
        assert self.teaching_steps is not None
        if not self.source_anchor_ids or not self.teaching_steps:
            raise ValueError("empty_live_level_v2_contract")

        step_ids = [step.step_id for step in self.teaching_steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("duplicate_live_teaching_step_id")

        required_phases = [step.phase for step in self.teaching_steps if step.required]
        expected_phases: list[LiveTeachingPhase] = [
            "connect",
            "explain",
            "model",
            "co_construct",
            "guided_practice",
            "feedback",
            "independent_application",
        ]
        if required_phases != expected_phases:
            raise ValueError("invalid_live_teaching_phase_sequence")
        phase_order = {phase: index for index, phase in enumerate(expected_phases)}
        all_phase_indexes = [phase_order[step.phase] for step in self.teaching_steps]
        if all_phase_indexes != sorted(all_phase_indexes):
            raise ValueError("invalid_live_teaching_phase_sequence")

        anchor_ids = set(self.source_anchor_ids)
        skill_ids = set(self.skill_ids)
        for step in self.teaching_steps:
            activity = step.activity
            if activity.episode_kind != self.episode_kind:
                raise ValueError("live_teaching_step_episode_mismatch")
            if not set(activity.source_anchor_ids or ()).issubset(anchor_ids):
                raise ValueError("unknown_live_teaching_step_source_anchor")
            if not set(activity.knowledge_components or ()).issubset(skill_ids):
                raise ValueError("unknown_live_teaching_step_knowledge_component")
        return self

    def runtime_dict(self) -> dict:
        level = {
            "level_id": self.level_id,
            "title": self.title,
            "focus": self.focus,
            "skill_ids": list(self.skill_ids),
            "teaching_goal": self.teaching_goal,
            "checks": self.checks.runtime_dict(),
        }
        if self.episode_kind is not None:
            level["episode_kind"] = self.episode_kind
            level["source_anchor_ids"] = list(self.source_anchor_ids or ())
            level["teaching_steps"] = [
                step.runtime_dict() for step in self.teaching_steps or ()
            ]
        return level


class LiveSchoolChapter(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    approval_status: Literal["draft", "qa_approved", "human_approved"]
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_evidence: list[str] = Field(default_factory=list)
    runtime_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chapter_id: str
    chapter_no: int = Field(ge=1)
    content_version: str | None = None
    certification_version: str | None = None
    title: str
    book_title: str
    unit_title: str
    source_url: str
    source_note: str
    source_anchors: list[LiveSourceAnchor] | None = None
    levels: list[LiveChapterLevel] = Field(min_length=1)
    chapter_assessment: LiveChapterAssessment | None = None

    @field_validator(
        "chapter_id",
        "title",
        "book_title",
        "unit_title",
        "source_url",
        "source_note",
    )
    @classmethod
    def _non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("live_chapter_field_empty")
        return cleaned

    @field_validator("review_evidence")
    @classmethod
    def _clean_review_evidence(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("live_chapter_review_evidence_empty")
        return cleaned

    @model_validator(mode="after")
    def _approval_and_level_ids_are_valid(self) -> "LiveSchoolChapter":
        if self.approval_status != "draft" and not (
            self.reviewed_by
            and self.reviewed_by.strip()
            and self.reviewed_at
            and self.reviewed_at.strip()
            and self.review_evidence
        ):
            raise ValueError("reviewed_live_chapter_requires_review_evidence")
        level_ids = [level.level_id for level in self.levels]
        if len(level_ids) != len(set(level_ids)):
            raise ValueError("duplicate_live_chapter_level_id")
        source_anchor_ids = [
            anchor.anchor_id for anchor in self.source_anchors or ()
        ]
        if len(source_anchor_ids) != len(set(source_anchor_ids)):
            raise ValueError("duplicate_live_source_anchor_id")
        referenced_anchor_ids = {
            anchor_id
            for level in self.levels
            for anchor_id in level.source_anchor_ids or ()
        }
        unknown_anchor_ids = referenced_anchor_ids - set(source_anchor_ids)
        if unknown_anchor_ids:
            raise ValueError(
                "unknown_live_level_source_anchor:"
                + ",".join(sorted(unknown_anchor_ids))
            )
        required_anchor_ids = {
            anchor.anchor_id
            for anchor in self.source_anchors or ()
            if anchor.required_for_chapter_certification
        }
        uncovered_required_anchor_ids = required_anchor_ids - referenced_anchor_ids
        if uncovered_required_anchor_ids:
            raise ValueError(
                "uncovered_required_live_source_anchor:"
                + ",".join(sorted(uncovered_required_anchor_ids))
            )
        if self.chapter_assessment is not None:
            if self.chapter_assessment.max_attempts >= 3 and any(
                level.checks.revision_level_1 is None
                or level.checks.revision_level_2 is None
                or level.checks.revision_level_3 is None
                for level in self.levels
            ):
                raise ValueError(
                    "third_attempt_requires_authored_revision_levels"
                )
            taught_skill_ids = {
                skill_id for level in self.levels for skill_id in level.skill_ids
            }
            if len(taught_skill_ids) > self.chapter_assessment.items_per_attempt:
                raise ValueError(
                    "live_chapter_assessment_form_cannot_cover_skills"
                )
            assessment_skill_ids = {
                skill_id
                for item in self.chapter_assessment.items
                for skill_id in item.skill_ids
            }
            untaught_skill_ids = sorted(assessment_skill_ids - taught_skill_ids)
            if untaught_skill_ids:
                raise ValueError(
                    "untaught_live_chapter_assessment_skill:"
                    + ",".join(untaught_skill_ids)
                )
            required_skill_coverage = (
                3 if self.chapter_assessment.max_attempts == 3 else 2
            )
            coverage = {
                skill_id: len(
                    {
                        item.item_id
                        for item in self.chapter_assessment.items
                        if skill_id in item.skill_ids
                    }
                )
                for skill_id in taught_skill_ids
            }
            undercovered_skill_ids = sorted(
                skill_id
                for skill_id in taught_skill_ids
                if coverage[skill_id] < required_skill_coverage
            )
            if undercovered_skill_ids:
                raise ValueError(
                    "undercovered_live_chapter_assessment_skill:"
                    + ",".join(undercovered_skill_ids)
                )
        return self

    def runtime_dict(self) -> dict:
        chapter = {
            "chapter_id": self.chapter_id,
            "chapter_no": self.chapter_no,
            "title": self.title,
            "book_title": self.book_title,
            "unit_title": self.unit_title,
            "source_url": self.source_url,
            "source_note": self.source_note,
            "levels": [level.runtime_dict() for level in self.levels],
        }
        if self.source_anchors is not None:
            chapter["source_anchors"] = [
                anchor.model_dump() for anchor in self.source_anchors
            ]
        if self.content_version is not None:
            chapter["content_version"] = self.content_version
        if self.certification_version is not None:
            chapter["certification_version"] = self.certification_version
        if self.chapter_assessment is not None:
            chapter["chapter_assessment"] = self.chapter_assessment.runtime_dict()
        return chapter

    def calculated_runtime_sha256(self) -> str:
        encoded = json.dumps(
            self.runtime_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
