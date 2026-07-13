"""School V3 content and evaluator contract schema.

This module is the bounded authoring contract for School V3. It defines the
shape and launch gate, but it intentionally does not ship a class 2-5 corpus.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


LearningStage = Literal[
    "guided",
    "bridge",
    "independent_check",
    "transfer_check",
    "review_check",
    "chapter_check",
]
SchoolV3ItemType = Literal["fill_blank", "multiple_choice", "short_answer", "spoken"]
ApprovalStatus = Literal["draft", "seed", "approved"]

LAUNCH_MIN_OUTCOMES = 5
LAUNCH_MAX_OUTCOMES = 7
LAUNCH_MIN_GUIDED_PER_OUTCOME = 6
LAUNCH_MIN_BRIDGE_PER_OUTCOME = 4
LAUNCH_MIN_INDEPENDENT_PER_OUTCOME = 6
LAUNCH_MIN_TRANSFER_PER_OUTCOME = 3
LAUNCH_MIN_CHAPTER_CHECK_ITEMS = 20
PUBLIC_FORBIDDEN_KEYS = frozenset({"answer_key", "model_answer", "rubric"})


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

    @field_validator("prerequisite_skill_ids")
    @classmethod
    def _non_empty_prerequisites(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("prerequisite_skill_ids must be non-empty")
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
    def _unique_and_closed_skill_ids(self) -> "SkillTaxonomy":
        seen: set[str] = set()
        for entry in self.entries:
            if entry.skill_id in seen:
                raise ValueError(f"duplicate_skill_id:{entry.skill_id}")
            seen.add(entry.skill_id)
        for entry in self.entries:
            for prerequisite in entry.prerequisite_skill_ids:
                if prerequisite not in seen:
                    raise ValueError(f"unknown_prerequisite_skill_id:{prerequisite}")
        return self

    def skill_ids(self) -> set[str]:
        return {entry.skill_id for entry in self.entries}


class SchoolV3AssessmentItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    stage: LearningStage
    item_type: SchoolV3ItemType
    prompt: str
    skill_ids: list[str] = Field(min_length=1)
    answer_key: str | None = None
    model_answer: str | None = None
    rubric: dict[str, Any] | None = None
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

    @field_validator("answer_key", "model_answer")
    @classmethod
    def _optional_non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def _deterministic_items_have_keys(self) -> "SchoolV3AssessmentItem":
        if self.item_type in {"fill_blank", "multiple_choice"} and not self.answer_key:
            raise ValueError("deterministic_item_requires_answer_key")
        if self.item_type == "multiple_choice":
            options = self.options or []
            if len(options) < 2:
                raise ValueError("multiple_choice_requires_options")
            if self.answer_key not in options:
                raise ValueError("answer_key_must_be_option")
        return self


class SchoolV3LessonOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome_id: str
    title: str
    skill_ids: list[str] = Field(min_length=1)
    items: list[SchoolV3AssessmentItem] = Field(min_length=1)

    @field_validator("outcome_id", "title")
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


class SchoolV3ChapterBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str
    class_no: int
    book_title: str
    curriculum_version: str
    chapter_id: str
    chapter_title: str
    source_url: str
    approval_status: ApprovalStatus = "draft"
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    outcomes: list[SchoolV3LessonOutcome] = Field(min_length=1)

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

    @field_validator("reviewed_by", "reviewed_at")
    @classmethod
    def _optional_non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


class SchoolV3RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    met: bool
    quality: float = Field(ge=0.0, le=1.0)
    evidence_quote: str

    @field_validator("id", "evidence_quote")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


class SchoolV3RubricEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    item_id: str
    skill_ids: list[str] = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    language_detected: str
    criteria: list[SchoolV3RubricCriterion] = Field(min_length=1)
    misconception_tags: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    needs_human_review: bool
    feedback_to_learner: str

    @field_validator(
        "schema_version",
        "item_id",
        "language_detected",
        "feedback_to_learner",
    )
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned

    @field_validator("skill_ids", "misconception_tags", "blockers")
    @classmethod
    def _non_empty_strings(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("list values must be non-empty")
        return cleaned


@dataclass(frozen=True)
class LaunchGateResult:
    outcome_count: int
    item_count: int
    chapter_check_count: int
    stage_counts_by_outcome: dict[str, dict[str, int]]


def validate_launch_content_gate(
    blueprint: SchoolV3ChapterBlueprint,
    taxonomy: SkillTaxonomy,
) -> LaunchGateResult:
    taxonomy_ids = taxonomy.skill_ids()
    _validate_unique_outcomes_and_items(blueprint)
    _validate_known_skill_ids(blueprint, taxonomy_ids)

    outcome_count = len(blueprint.outcomes)
    if outcome_count < LAUNCH_MIN_OUTCOMES or outcome_count > LAUNCH_MAX_OUTCOMES:
        raise ContentGateError(f"launch_gate_outcome_count:{LAUNCH_MIN_OUTCOMES}:{LAUNCH_MAX_OUTCOMES}")

    stage_counts_by_outcome: dict[str, dict[str, int]] = {}
    chapter_check_count = 0
    item_count = 0
    for outcome in blueprint.outcomes:
        counts = Counter(item.stage for item in outcome.items)
        stage_counts_by_outcome[outcome.outcome_id] = dict(counts)
        item_count += len(outcome.items)
        chapter_check_count += counts["chapter_check"]
        _require_stage_count(
            outcome.outcome_id,
            counts,
            "guided",
            LAUNCH_MIN_GUIDED_PER_OUTCOME,
        )
        _require_stage_count(
            outcome.outcome_id,
            counts,
            "bridge",
            LAUNCH_MIN_BRIDGE_PER_OUTCOME,
        )
        _require_stage_count(
            outcome.outcome_id,
            counts,
            "independent_check",
            LAUNCH_MIN_INDEPENDENT_PER_OUTCOME,
        )
        _require_stage_count(
            outcome.outcome_id,
            counts,
            "transfer_check",
            LAUNCH_MIN_TRANSFER_PER_OUTCOME,
        )

    if chapter_check_count < LAUNCH_MIN_CHAPTER_CHECK_ITEMS:
        raise ContentGateError(f"launch_gate_min_chapter_check_items:{LAUNCH_MIN_CHAPTER_CHECK_ITEMS}")

    _assert_no_public_leaks(public_chapter_payload(blueprint))
    return LaunchGateResult(
        outcome_count=outcome_count,
        item_count=item_count,
        chapter_check_count=chapter_check_count,
        stage_counts_by_outcome=stage_counts_by_outcome,
    )


def public_item_payload(item: SchoolV3AssessmentItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "stage": item.stage,
        "type": item.item_type,
        "prompt": item.prompt,
        "skill_ids": list(item.skill_ids),
        "options": list(item.options) if item.options else None,
    }


def public_outcome_payload(outcome: SchoolV3LessonOutcome) -> dict[str, Any]:
    return {
        "outcome_id": outcome.outcome_id,
        "title": outcome.title,
        "skill_ids": list(outcome.skill_ids),
        "items": [public_item_payload(item) for item in outcome.items],
    }


def public_chapter_payload(blueprint: SchoolV3ChapterBlueprint) -> dict[str, Any]:
    return {
        "subject_id": blueprint.subject_id,
        "class_no": blueprint.class_no,
        "book_title": blueprint.book_title,
        "curriculum_version": blueprint.curriculum_version,
        "chapter_id": blueprint.chapter_id,
        "chapter_title": blueprint.chapter_title,
        "source_url": blueprint.source_url,
        "outcomes": [public_outcome_payload(outcome) for outcome in blueprint.outcomes],
    }


def _validate_unique_outcomes_and_items(blueprint: SchoolV3ChapterBlueprint) -> None:
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


def _validate_known_skill_ids(blueprint: SchoolV3ChapterBlueprint, taxonomy_ids: set[str]) -> None:
    for outcome in blueprint.outcomes:
        for skill_id in outcome.skill_ids:
            if skill_id not in taxonomy_ids:
                raise ContentGateError(f"unknown_skill_id:{skill_id}")
        for item in outcome.items:
            for skill_id in item.skill_ids:
                if skill_id not in taxonomy_ids:
                    raise ContentGateError(f"unknown_skill_id:{skill_id}")


def _require_stage_count(
    outcome_id: str,
    counts: Counter[str],
    stage: str,
    minimum: int,
) -> None:
    if counts[stage] < minimum:
        raise ContentGateError(f"launch_gate_min_stage_items:{outcome_id}:{stage}:{minimum}")


def _assert_no_public_leaks(value: Any) -> None:
    if isinstance(value, dict):
        leaked = PUBLIC_FORBIDDEN_KEYS & set(value)
        if leaked:
            raise ContentGateError(f"public_serializer_leak:{sorted(leaked)}")
        for child in value.values():
            _assert_no_public_leaks(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_public_leaks(child)
