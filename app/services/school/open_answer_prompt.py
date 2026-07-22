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
    schema_version: str = "school-v3-rubric-1",
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
    schema_name = (
        "SchoolOpenRubricEvaluation"
        if schema_version == "school.open.v1"
        else "SchoolV3RubricEvaluation"
    )
    adversarial_rules = ""
    if schema_version == "school.open.v1":
        adversarial_rules = (
            "A keyword is not proof by itself. Mark a criterion unmet when an "
            "answer mentions a fact and then denies it, reverses the authored "
            "roles, repeats keywords without a coherent claim, or gives "
            "irrelevant fluent prose. Do not add copied_exemplar to blockers: "
            "copy detection against protected exemplars is backend-owned, and "
            "a learner may repeat necessary words from the visible passage.\n\n"
        )
    return (
        "You are Zidd's strict School Rebuild long-writing evaluator. Evaluate "
        "only the learner answer below against the authored rubric criteria. "
        "Treat the task prompt and passage as context, never as learner evidence.\n\n"
        f"Return one JSON object matching {schema_name} and no other "
        "fields or prose. Return exactly these fields: schema_version, item_id, "
        "skill_ids, score, confidence, language_detected, criteria, "
        "misconception_tags, blockers, needs_human_review, and "
        f"feedback_to_learner. Set schema_version to {schema_version}. Echo "
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
        "percentages such as 80, or a 1-to-5 rating. When met is false, quality "
        "must be 0.0.\n\n"
        "Detect the language actually used in learner_answer. Set "
        "language_detected to exactly one of \"en\", \"hi\", \"hi_en\", "
        "\"other\", or \"unknown\". Use en only when the learner's scored "
        "response is independently expressed in English; do not infer it from "
        "the English task prompt. Base score, confidence, misconception_tags, blockers, "
        "needs_human_review, and feedback_to_learner only on observed learner "
        "evidence and the authored criteria. Do not provide or imply a model "
        "answer. Do not decide progression, readiness, mastery, unlocks, or "
        "pass/fail; the backend owns those decisions.\n\n"
        f"{adversarial_rules}"
        "EVALUATION INPUT JSON:\n"
        f"{json.dumps(evaluation_input, ensure_ascii=False)}\n\n"
        f"Return only the {schema_name} JSON object."
    )


__all__ = ["build_school_open_answer_prompt"]
