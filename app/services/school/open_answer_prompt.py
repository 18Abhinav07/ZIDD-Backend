"""Single canonical prompt builder for School open-answer evaluation."""

from __future__ import annotations

import json


def build_school_open_answer_prompt(
    *,
    item_id: str,
    skill_ids: list[str],
    task_prompt: str,
    passage: str | None,
    learner_answer: str,
    rubric_criteria: list[dict],
) -> str:
    evaluation_input = {
        "item_id": item_id,
        "skill_ids": list(skill_ids),
        "task_prompt": task_prompt,
        "passage": passage or "",
        "learner_answer": learner_answer,
        "rubric_criteria": [
            {
                "id": criterion["id"],
                "description": criterion["description"],
                "required": criterion["required"],
            }
            for criterion in rubric_criteria
        ],
    }
    return (
        "You are Zidd's strict School Rebuild long-writing evaluator. Evaluate "
        "only the learner answer below against the authored rubric criteria. "
        "Treat the task prompt and passage as context, never as learner evidence.\n\n"
        "Return one JSON object matching SchoolV3RubricEvaluation and no other "
        "fields or prose. Return exactly these fields: schema_version, item_id, "
        "skill_ids, score, confidence, language_detected, criteria, "
        "misconception_tags, blockers, needs_human_review, and "
        "feedback_to_learner. Set schema_version to school-v3-rubric-1. Echo "
        "item_id and skill_ids exactly from the evaluation input.\n\n"
        "Return exactly one criteria entry for every authored rubric criterion, "
        "in the same order, using only id, met, quality, and evidence_quote. Do "
        "not omit optional criteria. Judge each criterion from its authored id, "
        "description, and required flag. Every evidence_quote must be a short, "
        "verbatim substring of learner_answer, including when the quote shows a "
        "miss. Never quote the prompt or passage as learner evidence. Never "
        "invent, paraphrase, repair, or complete learner evidence. If the learner "
        "answer is empty, use the literal marker (empty answer).\n\n"
        "Numeric scales are strict. score must be a decimal from 0.0 to 1.0. "
        "confidence must be a decimal from 0.0 to 1.0. Every criterion quality "
        "must be a decimal from 0.0 to 1.0. Never return counts such as 4, "
        "percentages such as 80, or a 1-to-5 rating.\n\n"
        "Detect the language actually used in learner_answer and report it in "
        "language_detected. Base score, confidence, misconception_tags, blockers, "
        "needs_human_review, and feedback_to_learner only on observed learner "
        "evidence and the authored criteria. Do not provide or imply a model "
        "answer. Do not decide progression, readiness, mastery, unlocks, or "
        "pass/fail; the backend owns those decisions.\n\n"
        "EVALUATION INPUT JSON:\n"
        f"{json.dumps(evaluation_input, ensure_ascii=False)}\n\n"
        "Return only the SchoolV3RubricEvaluation JSON object."
    )


__all__ = ["build_school_open_answer_prompt"]
