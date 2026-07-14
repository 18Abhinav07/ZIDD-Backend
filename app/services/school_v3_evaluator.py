"""Strict School V3 evaluator contract.

The evaluator can grade deterministic answer-key items and can parse model
rubric JSON for open answers. It never decides mastery; it only converts
evidence into the shared readiness AttemptEvidence contract.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from app.content.school_v3_schema import (
    SchoolV3AssessmentItem,
    SchoolV3RubricCriterion,
    SchoolV3RubricEvaluation,
)

try:
    from app.services.school_core.readiness import AttemptEvidence, AttemptType
except ImportError:  # pragma: no cover - compatibility for older slices
    from app.services.school_v2_readiness import AttemptEvidence, AttemptType


RUBRIC_SCHEMA_VERSION = "school-v3-rubric-1"
SupportLevel = Literal["independent", "guided", "bridge", "scaffolded"]


def parse_school_v3_rubric_json(raw: str) -> SchoolV3RubricEvaluation:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_school_v3_rubric_json") from exc
    return SchoolV3RubricEvaluation.model_validate(payload)


def grade_deterministic_item(
    item: SchoolV3AssessmentItem,
    answer: str,
    *,
    language_detected: str = "en",
) -> SchoolV3RubricEvaluation:
    if not item.answer_key:
        raise ValueError("deterministic_item_requires_answer_key")

    expected = _normalize(item.answer_key)
    actual = _normalize(answer)
    if item.item_type == "short_answer":
        met = bool(expected and expected in actual)
    else:
        met = actual == expected
    score = 1.0 if met else 0.0
    return SchoolV3RubricEvaluation(
        schema_version=RUBRIC_SCHEMA_VERSION,
        item_id=item.item_id,
        skill_ids=list(item.skill_ids),
        score=score,
        confidence=1.0,
        language_detected=language_detected,
        criteria=[
            SchoolV3RubricCriterion(
                id="answer_key_match",
                met=met,
                quality=score,
                evidence_quote=_evidence_quote(answer),
            )
        ],
        misconception_tags=[] if met else ["answer_key_mismatch"],
        blockers=[],
        needs_human_review=False,
        feedback_to_learner="Correct." if met else "Check the answer and try again.",
    )


def to_attempt_evidence(
    evaluation: SchoolV3RubricEvaluation,
    *,
    attempt_type: AttemptType,
    support_level: SupportLevel,
    language_required: str | None = None,
) -> AttemptEvidence:
    blockers = list(evaluation.blockers)
    if evaluation.needs_human_review and "needs_human_review" not in blockers:
        blockers.append("needs_human_review")
    return AttemptEvidence(
        attempt_type=attempt_type,
        evaluator_score=evaluation.score,
        evaluator_confidence=evaluation.confidence,
        skill_ids=tuple(evaluation.skill_ids),
        support_level=support_level,
        language_required=language_required,
        language_detected=evaluation.language_detected,
        blockers=tuple(blockers),
    )


def criterion_scores(evaluation: SchoolV3RubricEvaluation) -> dict[str, float]:
    return {criterion.id: criterion.quality for criterion in evaluation.criteria}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _evidence_quote(answer: str) -> str:
    cleaned = answer.strip()
    return cleaned if cleaned else "(empty answer)"
