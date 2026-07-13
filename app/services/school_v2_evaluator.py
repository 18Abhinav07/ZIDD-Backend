"""Strict School V2 evaluator contracts.

Open answers may need an LLM rubric, but the LLM only returns evidence. The
readiness service decides whether that evidence counts for certification.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.school_v2_readiness import AttemptEvidence, AttemptType


SupportLevel = Literal["independent", "guided", "bridge", "scaffolded"]


class SchoolCriterionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    evidence_quote: str

    @field_validator("criterion_id", "evidence_quote")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


class SchoolOpenAnswerEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_ids: list[str] = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    language_detected: str
    criteria: list[SchoolCriterionEvaluation] = Field(min_length=1)
    misconception_tags: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    feedback_to_learner: str

    @field_validator("skill_ids", "misconception_tags", "blockers")
    @classmethod
    def _non_empty_strings(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("list values must be non-empty")
        return cleaned

    @field_validator("language_detected", "feedback_to_learner")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must be non-empty")
        return cleaned


def parse_open_answer_evaluation(raw: str) -> SchoolOpenAnswerEvaluation:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_open_answer_json") from exc
    return SchoolOpenAnswerEvaluation.model_validate(payload)


def to_attempt_evidence(
    evaluation: SchoolOpenAnswerEvaluation,
    *,
    attempt_type: AttemptType,
    support_level: SupportLevel,
    language_required: str | None = None,
) -> AttemptEvidence:
    return AttemptEvidence(
        attempt_type=attempt_type,
        evaluator_score=evaluation.score,
        evaluator_confidence=evaluation.confidence,
        skill_ids=tuple(evaluation.skill_ids),
        support_level=support_level,
        language_required=language_required,
        language_detected=evaluation.language_detected,
        blockers=tuple(evaluation.blockers),
    )


def criterion_scores(evaluation: SchoolOpenAnswerEvaluation) -> dict[str, float]:
    return {criterion.criterion_id: criterion.score for criterion in evaluation.criteria}
