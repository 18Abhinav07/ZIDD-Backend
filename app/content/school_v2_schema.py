"""School V2 content contract.

This is the authoring boundary for the rebuilt school surface. It keeps skill
IDs closed and validates a pilot slice separately from the larger launch gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


LearningStage = Literal["guided", "bridge", "independent_check", "transfer_check"]
SchoolItemType = Literal["fill_blank", "multiple_choice", "short_answer", "spoken"]

PILOT_REQUIRED_STAGES: set[str] = {
    "guided",
    "bridge",
    "independent_check",
    "transfer_check",
}
PILOT_MIN_OUTCOMES = 3


class ContentGateError(ValueError):
    pass


class SkillTaxonomyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str
    subject_id: str
    class_min: int
    class_max: int
    name: str
    description: str
    prerequisite_skill_ids: list[str] = Field(default_factory=list)
    certifying_language: str = "en"

    @field_validator(
        "skill_id",
        "subject_id",
        "name",
        "description",
        "certifying_language",
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def _valid_class_range(self) -> "SkillTaxonomyEntry":
        if self.class_min > self.class_max:
            raise ValueError("class_min cannot exceed class_max")
        return self


class SkillTaxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[SkillTaxonomyEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_skill_ids(self) -> "SkillTaxonomy":
        seen: set[str] = set()
        for entry in self.entries:
            if entry.skill_id in seen:
                raise ValueError(f"duplicate_skill_id:{entry.skill_id}")
            seen.add(entry.skill_id)
        return self

    def skill_ids(self) -> set[str]:
        return {entry.skill_id for entry in self.entries}


class SchoolV2AssessmentItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    stage: LearningStage
    item_type: SchoolItemType
    prompt: str
    skill_ids: list[str] = Field(min_length=1)
    answer_key: str | None = None
    options: list[str] | None = None

    @field_validator("item_id", "prompt")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned

    @field_validator("skill_ids")
    @classmethod
    def _non_empty_skill_ids(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("skill_ids must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def _deterministic_items_have_keys(self) -> "SchoolV2AssessmentItem":
        if self.item_type in {"fill_blank", "multiple_choice"} and not (self.answer_key or "").strip():
            raise ValueError("deterministic_item_requires_answer_key")
        if self.item_type == "multiple_choice":
            options = self.options or []
            if len(options) < 2:
                raise ValueError("multiple_choice_requires_options")
            if self.answer_key not in options:
                raise ValueError("answer_key_must_be_option")
        return self


class SchoolV2LessonOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome_id: str
    title: str
    skill_ids: list[str] = Field(min_length=1)
    items: list[SchoolV2AssessmentItem] = Field(min_length=1)

    @field_validator("outcome_id", "title")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


class SchoolV2ChapterBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str
    class_no: int
    book_title: str
    curriculum_version: str
    chapter_id: str
    chapter_title: str
    source_url: str
    outcomes: list[SchoolV2LessonOutcome] = Field(min_length=1)

    @field_validator(
        "subject_id",
        "book_title",
        "curriculum_version",
        "chapter_id",
        "chapter_title",
        "source_url",
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


@dataclass(frozen=True)
class PilotGateResult:
    outcome_count: int
    item_count: int
    required_stages: set[str]


def validate_pilot_content_gate(
    blueprint: SchoolV2ChapterBlueprint,
    taxonomy: SkillTaxonomy,
) -> PilotGateResult:
    taxonomy_ids = taxonomy.skill_ids()
    _validate_unique_outcomes_and_items(blueprint)
    _validate_known_skill_ids(blueprint, taxonomy_ids)

    if len(blueprint.outcomes) < PILOT_MIN_OUTCOMES:
        raise ContentGateError(f"pilot_gate_min_outcomes:{PILOT_MIN_OUTCOMES}")

    for outcome in blueprint.outcomes:
        stages = {item.stage for item in outcome.items}
        missing = PILOT_REQUIRED_STAGES - stages
        if missing:
            raise ContentGateError(f"missing_stage:{outcome.outcome_id}:{sorted(missing)}")

    all_stages = {item.stage for outcome in blueprint.outcomes for item in outcome.items}
    item_count = sum(len(outcome.items) for outcome in blueprint.outcomes)
    return PilotGateResult(
        outcome_count=len(blueprint.outcomes),
        item_count=item_count,
        required_stages=PILOT_REQUIRED_STAGES & all_stages,
    )


def _validate_unique_outcomes_and_items(blueprint: SchoolV2ChapterBlueprint) -> None:
    outcome_ids: set[str] = set()
    item_ids: set[str] = set()
    for outcome in blueprint.outcomes:
        if outcome.outcome_id in outcome_ids:
            raise ContentGateError(f"duplicate_outcome_id:{outcome.outcome_id}")
        outcome_ids.add(outcome.outcome_id)
        for item in outcome.items:
            if item.item_id in item_ids:
                raise ContentGateError(f"duplicate_item_id:{item.item_id}")
            item_ids.add(item.item_id)


def _validate_known_skill_ids(blueprint: SchoolV2ChapterBlueprint, taxonomy_ids: set[str]) -> None:
    for outcome in blueprint.outcomes:
        for skill_id in outcome.skill_ids:
            if skill_id not in taxonomy_ids:
                raise ContentGateError(f"unknown_skill_id:{skill_id}")
        for item in outcome.items:
            for skill_id in item.skill_ids:
                if skill_id not in taxonomy_ids:
                    raise ContentGateError(f"unknown_skill_id:{skill_id}")
