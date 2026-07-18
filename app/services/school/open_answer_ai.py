"""Isolated provider boundary for canonical School open-answer evaluation."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Literal, Tuple

from pydantic import ValidationError, create_model, model_validator

from app.ai.local import ollama_structured
from app.ai.provider import structured_generate
from app.config import get_settings
from app.content.school.content_schema import (
    SchoolRubricCriterion,
    SchoolRubricEvaluation,
)
from app.middleware.rate_limit import llm_semaphore
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    SchoolOpenAnswerRetryableError,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services.school.open_answer_prompt import build_school_open_answer_prompt


logger = logging.getLogger(__name__)


class _ProviderSchoolRubricEvaluation(SchoolRubricEvaluation):
    """Wire model that only repairs a fail-closed provider contradiction."""

    @model_validator(mode="before")
    @classmethod
    def _zero_quality_for_unmet_criteria(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        raw_criteria = value.get("criteria")
        if not isinstance(raw_criteria, (list, tuple)):
            return value

        normalized_criteria = []
        changed = False
        for raw_criterion in raw_criteria:
            if not isinstance(raw_criterion, Mapping):
                normalized_criteria.append(raw_criterion)
                continue
            quality = raw_criterion.get("quality")
            should_zero = (
                raw_criterion.get("met") is False
                and isinstance(quality, (int, float))
                and not isinstance(quality, bool)
                and 0.0 < quality <= 1.0
            )
            if not should_zero:
                normalized_criteria.append(raw_criterion)
                continue
            normalized_criteria.append({**raw_criterion, "quality": 0.0})
            changed = True

        if not changed:
            return value
        return {**value, "criteria": normalized_criteria}


def _request_bound_evaluation_schema(
    *,
    schema_version: str,
    item_id: str,
    skill_ids: list[str],
    criterion_ids: list[str],
) -> type[SchoolRubricEvaluation]:
    """Constrain provider-owned JSON to the current authored request."""

    if not skill_ids:
        raise ValueError("school_open_answer_requires_skill_ids")
    if not criterion_ids:
        raise ValueError("school_open_answer_requires_rubric_criteria")

    bound_skill_ids = Tuple[
        tuple(Literal[skill_id] for skill_id in skill_ids)
    ]
    bound_criterion_models = tuple(
        create_model(
            f"RequestBoundSchoolRubricCriterion{index}",
            __base__=SchoolRubricCriterion,
            id=(Literal[criterion_id], ...),
        )
        for index, criterion_id in enumerate(criterion_ids)
    )
    bound_criteria = Tuple[bound_criterion_models]

    return create_model(
        "RequestBoundSchoolRubricEvaluation",
        __base__=_ProviderSchoolRubricEvaluation,
        schema_version=(Literal[schema_version], ...),
        item_id=(Literal[item_id], ...),
        skill_ids=(bound_skill_ids, ...),
        criteria=(bound_criteria, ...),
    )


def _local() -> bool:
    return get_settings().ai_backend == "local"


def _qwen_model_selected() -> bool:
    model = get_settings().ollama_model.strip().casefold()
    return bool(re.search(r"(?:^|[/_-])qwen(?:[0-9]|[.:_-]|$)", model))


def _downgrade_untraceable_evidence(
    evaluation: SchoolRubricEvaluation,
    answer: str,
    activity: dict,
) -> SchoolRubricEvaluation:
    """Fail closed when the model cites words the learner did not write."""

    learner_evidence = answer.strip()
    if not learner_evidence:
        return evaluation
    downgraded = False
    criteria = []
    for criterion in evaluation.criteria:
        if criterion.evidence_quote.strip() in answer:
            criteria.append(criterion)
            continue
        if not criterion.met:
            criteria.append(
                criterion.model_copy(update={"evidence_quote": learner_evidence})
            )
            continue
        recovered = (
            _traceable_semantic_evidence(
                activity,
                criterion_id=criterion.id,
                answer=answer,
            )
        )
        if recovered:
            criteria.append(
                criterion.model_copy(update={"evidence_quote": recovered})
            )
            continue
        if criterion.id == "relevant_text_clue":
            recovered = _traceable_passage_evidence(activity, answer)
            if recovered:
                criteria.append(
                    criterion.model_copy(update={"evidence_quote": recovered})
                )
                continue
        if criterion.id == "clear_relevant_english":
            criteria.append(
                criterion.model_copy(update={"evidence_quote": learner_evidence})
            )
            continue
        downgraded = True
        criteria.append(
            criterion.model_copy(
                update={
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": learner_evidence,
                }
            )
        )
    if not downgraded:
        if tuple(criteria) == tuple(evaluation.criteria):
            return evaluation
        return evaluation.model_copy(update={"criteria": tuple(criteria)})
    if not criteria:
        return evaluation
    return evaluation.model_copy(
        update={
            "criteria": tuple(criteria),
            "blockers": tuple(
                dict.fromkeys(
                    (*evaluation.blockers, "evaluator_evidence_untraceable")
                )
            ),
        }
    )


def _traceable_semantic_evidence(
    activity: dict,
    *,
    criterion_id: str,
    answer: str,
) -> str | None:
    """Recover an exact learner span only from backend-authored claim aliases."""

    slot = next(
        (
            item
            for item in activity.get("concept_slots") or []
            if str(item.get("id") or "") == criterion_id
        ),
        None,
    )
    if not isinstance(slot, dict):
        return None
    answer_tokens = tuple(
        (
            match.group(0).casefold(),
            match.start(),
            match.end(),
        )
        for match in re.finditer(r"[^\W_]+(?:'[^\W_]+)?", answer, re.UNICODE)
    )
    for alias in slot.get("any_of") or []:
        alias_tokens = tuple(
            match.group(0).casefold()
            for match in re.finditer(
                r"[^\W_]+(?:'[^\W_]+)?",
                str(alias),
                re.UNICODE,
            )
        )
        specific_tokens = tuple(
            token for token in alias_tokens if len(token) >= 3
        )
        if not alias_tokens or not specific_tokens:
            continue
        for start_index, (token, start, _end) in enumerate(answer_tokens):
            if token != alias_tokens[0]:
                continue
            matched_indexes = [start_index]
            cursor = start_index + 1
            for alias_token in alias_tokens[1:]:
                match_index = next(
                    (
                        index
                        for index in range(cursor, min(len(answer_tokens), cursor + 4))
                        if answer_tokens[index][0] == alias_token
                    ),
                    None,
                )
                if match_index is None:
                    break
                matched_indexes.append(match_index)
                cursor = match_index + 1
            if len(matched_indexes) != len(alias_tokens):
                continue
            inserted_tokens = matched_indexes[-1] - matched_indexes[0] + 1 - len(
                alias_tokens
            )
            if inserted_tokens > max(2, len(alias_tokens) // 2):
                continue
            end = answer_tokens[matched_indexes[-1]][2]
            return answer[start:end]
    return None


def _traceable_passage_evidence(activity: dict, answer: str) -> str | None:
    """Return learner-authored clue text only when the passage proves overlap."""

    passage = str(activity.get("passage") or "").strip()
    learner_evidence = answer.strip()
    if not passage or not learner_evidence:
        return None
    ignored = {
        "after",
        "and",
        "because",
        "before",
        "from",
        "have",
        "into",
        "over",
        "that",
        "their",
        "them",
        "there",
        "these",
        "they",
        "this",
        "those",
        "were",
        "with",
    }
    passage_tokens = {
        token
        for token in re.findall(
            r"[^\W\d_]+",
            passage.casefold(),
            flags=re.UNICODE,
        )
        if len(token) >= 4 and token not in ignored
    }
    answer_tokens = {
        token
        for token in re.findall(
            r"[^\W\d_]+",
            learner_evidence.casefold(),
            flags=re.UNICODE,
        )
        if len(token) >= 4 and token not in ignored
    }
    if len(passage_tokens.intersection(answer_tokens)) < 2:
        return None
    return learner_evidence


async def evaluate_school_open_answer(
    activity: dict,
    answer: str,
) -> SchoolRubricEvaluation:
    """Evaluate one School long-writing answer with one provider call."""

    authored_item_id = activity.get("activity_id") or activity.get("item_id")
    if not authored_item_id:
        raise ValueError("school_open_answer_requires_item_id")
    item_id = str(authored_item_id)
    strict_open = activity.get("grading_mode") == "strict_open_rubric"
    schema_version = (
        OPEN_RUBRIC_SCHEMA_VERSION
        if strict_open
        else "school-v3-rubric-1"
    )
    prompt = build_school_open_answer_prompt(
        item_id=item_id,
        skill_ids=activity["skill_ids"],
        task_prompt=activity.get("task_prompt") or activity.get("prompt") or "",
        passage=activity.get("passage"),
        learner_answer=answer,
        rubric_criteria=activity["rubric_criteria"],
        schema_version=schema_version,
    )
    response_schema = _request_bound_evaluation_schema(
        schema_version=schema_version,
        item_id=item_id,
        skill_ids=list(activity["skill_ids"]),
        criterion_ids=[
            str(criterion["id"])
            for criterion in activity["rubric_criteria"]
        ],
    )
    try:
        if _local() and not _qwen_model_selected():
            raise SchoolOpenAnswerRetryableError(
                "school_open_qwen_model_required"
            )
        async with llm_semaphore:
            if _local():
                evaluation = await ollama_structured(
                    prompt,
                    response_schema,
                    timeout=None,
                )
            else:
                evaluation = await structured_generate(
                    "school_open_answer",
                    prompt,
                    response_schema,
                )
    except SchoolOpenAnswerRetryableError:
        raise
    except ValidationError as exc:
        logger.warning(
            "School open-answer provider schema failed for item %s: %s",
            item_id,
            type(exc).__name__,
        )
        raise SchoolOpenAnswerRetryableError(
            "school_open_schema_failure"
        ) from exc
    except Exception as exc:
        raise SchoolOpenAnswerRetryableError(
            "school_open_provider_failure"
        ) from exc

    try:
        payload = (
            evaluation.model_dump(mode="python")
            if isinstance(evaluation, SchoolRubricEvaluation)
            else evaluation
        )
        request_bound = response_schema.model_validate(payload)
        evaluation = SchoolRubricEvaluation.model_validate(
            request_bound.model_dump(mode="python")
        )
        if not strict_open:
            return evaluation
        evaluation = _downgrade_untraceable_evidence(
            evaluation,
            answer,
            activity,
        )
        validated = validate_school_open_evaluation(
            evaluation,
            context=school_open_context_from_activity(activity, answer),
        )
    except Exception as exc:
        logger.warning(
            "School open-answer contract validation failed for item %s: %s",
            item_id,
            type(exc).__name__,
        )
        raise SchoolOpenAnswerRetryableError(
            "school_open_schema_failure"
        ) from exc
    return validated.evaluation.model_copy(
        update={"blockers": validated.effective_blockers},
    )


__all__ = ["build_school_open_answer_prompt", "evaluate_school_open_answer"]
