"""Context-bound validation for canonical School rubric evaluations.

The model reports evidence. Backend-authored context owns the item, scored
skills, criteria, and human-review policy used by downstream projection.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.content.school.content_schema import SchoolRubricEvaluation


RUBRIC_SCHEMA_VERSION = "school-v3-rubric-1"
HumanReviewPolicy = Literal["forbid", "allow"]


class SchoolCriterionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: str
    required: bool
    min_quality: float = Field(ge=0.0, le=1.0)

    @field_validator("id")
    @classmethod
    def _clean_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("school_criterion_policy_id_empty")
        return cleaned


class SchoolEvaluationContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    expected_item_id: str
    scored_skill_ids: tuple[str, ...] = Field(min_length=1)
    criterion_policies: tuple[SchoolCriterionPolicy, ...] = Field(min_length=1)
    pass_score: float = Field(ge=0.0, le=1.0)
    minimum_confidence: float = Field(ge=0.0, le=1.0)
    learner_answer: str
    human_review_policy: HumanReviewPolicy

    @field_validator("scored_skill_ids", "criterion_policies", mode="before")
    @classmethod
    def _tuple_collections(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("expected_item_id", "learner_answer")
    @classmethod
    def _clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("school_evaluation_context_field_empty")
        return cleaned

    @field_validator("scored_skill_ids")
    @classmethod
    def _validate_unique_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned):
            raise ValueError("school_evaluation_context_id_empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("school_evaluation_context_id_duplicate")
        return cleaned

    @model_validator(mode="after")
    def _validate_unique_criterion_policies(self) -> "SchoolEvaluationContext":
        criterion_ids = [policy.id for policy in self.criterion_policies]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("school_evaluation_context_criterion_duplicate")
        return self

    @property
    def expected_criterion_ids(self) -> tuple[str, ...]:
        return tuple(policy.id for policy in self.criterion_policies)


@dataclass(frozen=True)
class ValidatedSchoolRubricEvaluation:
    evaluation: SchoolRubricEvaluation
    context: SchoolEvaluationContext

    @property
    def scored_skill_ids(self) -> tuple[str, ...]:
        """Return backend-authored projection targets, never model-selected IDs."""

        return self.context.scored_skill_ids

    @property
    def aggregate_score(self) -> float:
        qualities = [criterion.quality for criterion in self.evaluation.criteria]
        return sum(qualities) / len(qualities)

    @property
    def meets_required_criteria(self) -> bool:
        qualities = {
            criterion.id: criterion.quality
            for criterion in self.evaluation.criteria
        }
        return all(
            qualities[policy.id] >= policy.min_quality
            for policy in self.context.criterion_policies
            if policy.required
        )

    @property
    def meets_confidence_requirement(self) -> bool:
        return self.evaluation.confidence >= self.context.minimum_confidence

    @property
    def requires_human_review(self) -> bool:
        return (
            self.evaluation.needs_human_review
            or not self.meets_confidence_requirement
        )

    @property
    def certification_eligible(self) -> bool:
        return (
            self.aggregate_score >= self.context.pass_score
            and self.meets_required_criteria
            and self.meets_confidence_requirement
            and not self.requires_human_review
        )


def _normalized_trace_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def validate_school_rubric_evaluation(
    payload: Mapping[str, Any] | SchoolRubricEvaluation,
    *,
    context: SchoolEvaluationContext,
) -> ValidatedSchoolRubricEvaluation:
    evaluation = (
        payload
        if isinstance(payload, SchoolRubricEvaluation)
        else SchoolRubricEvaluation.model_validate(dict(payload))
    )
    if evaluation.schema_version != RUBRIC_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported_school_rubric_schema:{evaluation.schema_version}"
        )
    if evaluation.item_id != context.expected_item_id:
        raise ValueError(
            f"rubric_item_id_mismatch:{context.expected_item_id}:"
            f"{evaluation.item_id}"
        )
    if evaluation.skill_ids != context.scored_skill_ids:
        raise ValueError("rubric_scored_skill_ids_mismatch")

    criterion_ids = tuple(criterion.id for criterion in evaluation.criteria)
    if criterion_ids != context.expected_criterion_ids:
        raise ValueError("rubric_criterion_ids_mismatch")

    learner_answer = _normalized_trace_text(context.learner_answer)
    for criterion in evaluation.criteria:
        if not criterion.met and criterion.quality > 0.0:
            raise ValueError(
                f"rubric_unmet_criterion_has_quality:{criterion.id}"
            )
        evidence_quote = _normalized_trace_text(criterion.evidence_quote)
        if evidence_quote not in learner_answer:
            raise ValueError(
                f"rubric_evidence_quote_untraceable:{criterion.id}"
            )

    if (
        evaluation.needs_human_review
        and context.human_review_policy == "forbid"
    ):
        raise ValueError("rubric_human_review_disallowed")

    return ValidatedSchoolRubricEvaluation(
        evaluation=evaluation,
        context=context,
    )


def parse_school_rubric_json(
    raw: str,
    *,
    context: SchoolEvaluationContext,
) -> ValidatedSchoolRubricEvaluation:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_school_rubric_json") from exc
    if not isinstance(payload, dict):
        raise ValueError("invalid_school_rubric_json")
    return validate_school_rubric_evaluation(payload, context=context)


def criterion_scores(
    validated: ValidatedSchoolRubricEvaluation,
) -> dict[str, float]:
    return {
        criterion.id: criterion.quality
        for criterion in validated.evaluation.criteria
    }


# Compatibility parser name retained while Task 0.4 moves existing callers.
parse_school_v3_rubric_json = parse_school_rubric_json


__all__ = [
    "HumanReviewPolicy",
    "RUBRIC_SCHEMA_VERSION",
    "SchoolCriterionPolicy",
    "SchoolEvaluationContext",
    "ValidatedSchoolRubricEvaluation",
    "criterion_scores",
    "parse_school_rubric_json",
    "parse_school_v3_rubric_json",
    "validate_school_rubric_evaluation",
]
