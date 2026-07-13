"""Strict evaluator adapter for authored School Rebuild placement items."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.content.school_rebuild_placement_bank import SchoolPlacementBankItem
from app.content.school_rebuild_placement_validation import (
    RUBRIC_REMEDIATION_BY_CRITERION,
    STRICT_RUBRIC_CRITERIA_BY_REF,
    normalize_placement_answer,
)
from app.content.school.content_schema import (
    SchoolRubricCriterion,
    SchoolRubricEvaluation,
)
from app.services.school.evaluator_contract import RUBRIC_SCHEMA_VERSION


EVALUATOR_UNAVAILABLE_CODE = "school_placement_evaluator_unavailable"
REQUIRED_CRITERION_MIN_QUALITY = 0.7

PlacementEvaluationProvider = Callable[
    [dict[str, Any], str],
    Awaitable[SchoolRubricEvaluation | dict[str, Any]],
]


class SchoolPlacementEvaluatorUnavailableError(RuntimeError):
    """Raised when placement evaluation cannot produce trusted evidence."""


def grade_deterministic_placement_item(
    item: SchoolPlacementBankItem,
    answer: str,
    *,
    language_detected: str = "en",
) -> SchoolRubricEvaluation:
    """Grade one deterministic item against every authored alternative."""

    if item.evaluation_mode != "deterministic" or not item.accepted_answers:
        raise ValueError("deterministic_placement_item_requires_accepted_answers")

    normalized_answer = normalize_placement_answer(answer)
    normalized_accepted = {
        normalize_placement_answer(accepted)
        for accepted in item.accepted_answers
    }
    met = normalized_answer in normalized_accepted
    score = 1.0 if met else 0.0
    return SchoolRubricEvaluation(
        schema_version=RUBRIC_SCHEMA_VERSION,
        item_id=item.item_id,
        skill_ids=[item.primary_skill_id],
        score=score,
        confidence=1.0,
        language_detected=language_detected,
        criteria=[
            SchoolRubricCriterion(
                id="accepted_answer_match",
                met=met,
                quality=score,
                evidence_quote=answer.strip() or "(empty answer)",
            )
        ],
        misconception_tags=[] if met else list(item.misconception_tags),
        blockers=[],
        needs_human_review=False,
        feedback_to_learner=(
            "Correct."
            if met
            else "Re-read the clue and try the same skill again."
        ),
    )


def build_placement_evaluator_activity(
    item: SchoolPlacementBankItem,
) -> dict[str, Any]:
    """Build the strict provider activity from the item's authored rubric."""

    criterion_ids = _strict_criterion_ids(item)
    return {
        "activity_id": item.item_id,
        "item_id": item.item_id,
        "evaluation_mode": "llm_rubric",
        "rubric_ref": item.rubric_ref,
        "skill_ids": [item.primary_skill_id],
        "task_prompt": item.prompt,
        "prompt": item.prompt,
        "passage": item.passage,
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": RUBRIC_REMEDIATION_BY_CRITERION[criterion_id],
                "required": True,
                "min_quality": REQUIRED_CRITERION_MIN_QUALITY,
            }
            for criterion_id in criterion_ids
        ],
    }


async def evaluate_school_placement_item(
    item: SchoolPlacementBankItem,
    answer: str,
    *,
    provider: PlacementEvaluationProvider | None = None,
    language_detected: str = "en",
) -> SchoolRubricEvaluation:
    """Return trusted placement evidence without owning provider selection."""

    if item.evaluation_mode == "deterministic":
        return grade_deterministic_placement_item(
            item,
            answer,
            language_detected=language_detected,
        )
    if provider is None:
        raise SchoolPlacementEvaluatorUnavailableError(EVALUATOR_UNAVAILABLE_CODE)

    try:
        activity = build_placement_evaluator_activity(item)
        raw_evaluation = await provider(activity, answer)
        return validate_placement_provider_evaluation(
            item,
            answer,
            raw_evaluation,
        )
    except SchoolPlacementEvaluatorUnavailableError:
        raise
    except Exception as exc:
        raise SchoolPlacementEvaluatorUnavailableError(
            EVALUATOR_UNAVAILABLE_CODE
        ) from exc


def validate_placement_provider_evaluation(
    item: SchoolPlacementBankItem,
    answer: str,
    raw_evaluation: SchoolRubricEvaluation | dict[str, Any],
) -> SchoolRubricEvaluation:
    """Validate provider evidence and replace its score with backend authority."""

    try:
        evaluation = (
            raw_evaluation
            if isinstance(raw_evaluation, SchoolRubricEvaluation)
            else SchoolRubricEvaluation.model_validate(
                raw_evaluation
                if isinstance(raw_evaluation, dict)
                else raw_evaluation.model_dump()
            )
        )
        criterion_ids = _strict_criterion_ids(item)
        if (
            evaluation.schema_version != RUBRIC_SCHEMA_VERSION
            or evaluation.item_id != item.item_id
            or evaluation.skill_ids != (item.primary_skill_id,)
            or [criterion.id for criterion in evaluation.criteria]
            != list(criterion_ids)
            or evaluation.needs_human_review
            or "needs_human_review" in evaluation.blockers
        ):
            raise ValueError("invalid_placement_evaluator_contract")

        evaluation = _canonicalize_evidence_quotes(evaluation, answer)
        _validate_evidence_quotes(evaluation, answer)
        language_mismatch = (
            "english_response" in criterion_ids
            and evaluation.language_detected.strip().casefold()
            not in {"en", "eng", "english"}
        )
        missing_required = any(
            not criterion.met
            or criterion.quality < REQUIRED_CRITERION_MIN_QUALITY
            for criterion in evaluation.criteria
        )
        backend_score = sum(
            criterion.quality if criterion.met else 0.0
            for criterion in evaluation.criteria
        ) / len(evaluation.criteria)

        blockers = list(evaluation.blockers)
        if language_mismatch:
            blockers.append("language_mismatch")
        elif missing_required:
            blockers.append("required_criteria_missing")

        return evaluation.model_copy(
            update={
                "score": round(backend_score, 4),
                "blockers": list(dict.fromkeys(blockers)),
                "needs_human_review": False,
            }
        )
    except SchoolPlacementEvaluatorUnavailableError:
        raise
    except Exception as exc:
        raise SchoolPlacementEvaluatorUnavailableError(
            EVALUATOR_UNAVAILABLE_CODE
        ) from exc


def _strict_criterion_ids(item: SchoolPlacementBankItem) -> tuple[str, ...]:
    if item.evaluation_mode != "strict_rubric" or not item.rubric_ref:
        raise SchoolPlacementEvaluatorUnavailableError(EVALUATOR_UNAVAILABLE_CODE)
    criterion_ids = STRICT_RUBRIC_CRITERIA_BY_REF.get(item.rubric_ref)
    if not criterion_ids:
        raise SchoolPlacementEvaluatorUnavailableError(EVALUATOR_UNAVAILABLE_CODE)
    return criterion_ids


def _validate_evidence_quotes(
    evaluation: SchoolRubricEvaluation,
    answer: str,
) -> None:
    for criterion in evaluation.criteria:
        quote = criterion.evidence_quote
        if quote == "(empty answer)":
            if criterion.met:
                raise ValueError("untraceable_placement_evidence")
            continue
        if quote not in answer:
            raise ValueError("untraceable_placement_evidence")


def _canonicalize_evidence_quotes(
    evaluation: SchoolRubricEvaluation,
    answer: str,
) -> SchoolRubricEvaluation:
    learner_evidence = answer.strip()
    criteria: list[SchoolRubricCriterion] = []
    for criterion in evaluation.criteria:
        quote = criterion.evidence_quote
        if quote == "(empty answer)":
            if criterion.met:
                if not learner_evidence:
                    raise ValueError("untraceable_placement_evidence")
                quote = learner_evidence
        elif quote not in answer:
            if criterion.met:
                if not learner_evidence:
                    raise ValueError("untraceable_placement_evidence")
                quote = learner_evidence
            else:
                quote = "(empty answer)"
        criteria.append(criterion.model_copy(update={"evidence_quote": quote}))
    return evaluation.model_copy(update={"criteria": criteria})
