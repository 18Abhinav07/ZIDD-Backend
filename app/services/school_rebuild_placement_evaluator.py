"""Strict evaluator adapter for authored School Rebuild placement items."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import re
from typing import Any, Literal

from app.content.school_rebuild_placement_bank import (
    PlacementSemanticClaimSlot,
    SchoolPlacementBankItem,
    placement_bank_for,
)
from app.content.school_rebuild_placement_validation import (
    RUBRIC_REMEDIATION_BY_CRITERION,
    STRICT_RUBRIC_CRITERIA_BY_REF,
    normalize_placement_answer,
)
from app.content.school.content_schema import (
    SchoolRubricCriterion,
    SchoolRubricEvaluation,
)
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    RUBRIC_SCHEMA_VERSION,
    SchoolOpenAnswerRetryableError,
)
from app.services.school.semantic_evidence import (
    copies_source_passage,
    correct_semantic_criterion,
    inference_clue_is_explicitly_linked,
)


EVALUATOR_UNAVAILABLE_CODE = "school_placement_evaluator_unavailable"
REQUIRED_CRITERION_MIN_QUALITY = 0.7

AuthoredClaimResponseVerdict = Literal[
    "proven_true",
    "proven_false",
    "unknown",
]
AuthoredSummaryResponseVerdict = Literal[
    "proven_true",
    "factual_false",
    "form_false",
    "unknown",
]

_AUTHORED_EXTRA_NEGATION_TOKENS = frozenset(
    {
        "didn",
        "didnt",
        "doesn",
        "doesnt",
        "never",
        "no",
        "not",
        "wasn",
        "wasnt",
        "weren",
        "werent",
        "without",
        "fail",
        "failed",
        "fails",
        "failing",
        "unable",
    }
)
_AUTHORED_COMPLETE_SENTENCE_CRITERIA = frozenset(
    {
        "complete_idea",
        "subject_and_predicate",
        "relevant_detail",
        "basic_capitalization_and_terminal_punctuation",
    }
)
_AUTHORED_SHORT_ANSWER_CRITERIA = frozenset(
    {"answers_question", "relevant_detail", "complete_response"}
)
_AUTHORED_SUMMARY_CRITERIA = frozenset(
    {
        "main_idea_or_event",
        "essential_details",
        "own_words",
        "concise_complete_response",
        "english_response",
    }
)
_AUTHORED_JOIN_TOKENS = frozenset(
    {"and", "because", "but", "so", "then", "when", "while"}
)
_AUTHORED_CLAUSE_MARKERS = frozenset(
    {"although", "and", "but", "however", "while", "yet"}
)
_AUTHORED_FUNCTION_TOKENS = frozenset(
    {
        "a",
        "after",
        "an",
        "and",
        "as",
        "at",
        "because",
        "before",
        "by",
        "for",
        "from",
        "her",
        "him",
        "his",
        "in",
        "into",
        "it",
        "its",
        "of",
        "on",
        "or",
        "she",
        "so",
        "that",
        "the",
        "their",
        "them",
        "then",
        "they",
        "this",
        "to",
        "toward",
        "towards",
        "up",
        "was",
        "were",
        "when",
        "which",
        "while",
        "with",
    }
)
_AUTHORED_SUMMARY_GLUE_TOKENS = frozenset(
    {"cared", "finally", "made", "putting", "used"}
)
_AUTHORED_INFERENCE_GLUE_TOKENS = frozenset(
    {"are", "clue", "clues", "probably"}
)

PlacementEvaluationProvider = Callable[
    [dict[str, Any], str],
    Awaitable[SchoolRubricEvaluation | dict[str, Any]],
]


class SchoolPlacementEvaluatorUnavailableError(RuntimeError):
    """Raised when placement evaluation cannot produce trusted evidence."""


def deterministic_placement_answer_matches(
    item: SchoolPlacementBankItem,
    answer: str,
    *,
    language_detected: str = "en",
) -> bool:
    """Match exact answers or a uniquely authored snapshot rubric sibling."""

    normalized_answer = normalize_placement_answer(answer)
    normalized_accepted = {
        normalize_placement_answer(accepted)
        for accepted in item.accepted_answers
    }
    normalized_accepted.update(
        normalize_placement_answer(alias)
        for slot in item.semantic_claim_slots
        for alias in slot.aliases
    )
    if normalized_answer in normalized_accepted:
        return True

    rubric_item = _authored_snapshot_rubric_item(item)
    if rubric_item is None:
        return False
    if rubric_item.rubric_ref == "school.strict.inference.v1":
        return (
            _authored_inference_fallback(
                rubric_item,
                answer,
                language_detected=language_detected,
            )
            is not None
        )
    if rubric_item.rubric_ref == "school.strict.summary.v1":
        return _authored_summary_response_verdict(rubric_item, answer) == "proven_true"
    return authored_claim_response_verdict(rubric_item, answer) == "proven_true"


def _authored_snapshot_rubric_item(
    item: SchoolPlacementBankItem,
) -> SchoolPlacementBankItem | None:
    """Return the sole private rubric source for a generated quick-check."""

    if (
        item.stage != "snapshot"
        or item.evaluation_mode != "deterministic"
        or not item.passage.startswith("Quick check: ")
        or not item.prompt.startswith("Quick check: ")
    ):
        return None

    source_passage = item.passage.removeprefix("Quick check: ")
    source_prompt = item.prompt.removeprefix("Quick check: ")
    matches = tuple(
        candidate
        for candidate in placement_bank_for(item.subject_id, item.target_class_no)
        if (
            candidate.track_id == item.track_id
            and candidate.source_class_no == item.source_class_no
            and candidate.primary_skill_id == item.primary_skill_id
            and candidate.rubric_ref is not None
            and candidate.passage == source_passage
            and candidate.prompt == source_prompt
        )
    )
    return matches[0] if len(matches) == 1 else None


def grade_deterministic_placement_item(
    item: SchoolPlacementBankItem,
    answer: str,
    *,
    language_detected: str = "en",
) -> SchoolRubricEvaluation:
    """Grade one deterministic item against every authored alternative."""

    if item.evaluation_mode != "deterministic" or not item.accepted_answers:
        raise ValueError("deterministic_placement_item_requires_accepted_answers")

    met = deterministic_placement_answer_matches(
        item,
        answer,
        language_detected=language_detected,
    )
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


def deterministic_insufficient_strict_placement_evaluation(
    item: SchoolPlacementBankItem,
    answer: str,
) -> SchoolRubricEvaluation | None:
    """Reject a response that cannot satisfy any strict placement rubric.

    Strict placement items normally need the provider because several natural
    phrasings can be valid. A one-word English reply cannot meet the authored
    complete-response criteria, though. Sending it through the provider adds
    latency and cost without improving the learner's evidence. Native-script
    responses deliberately stay on the provider path so its language-mismatch
    contract remains intact.
    """

    if item.evaluation_mode != "strict_rubric":
        return None
    normalized_answer = normalize_placement_answer(answer)
    if re.search(r"[\u0900-\u097f]", normalized_answer):
        return None
    english_words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", normalized_answer)
    if len(english_words) > 1:
        return None

    criterion_ids = _strict_criterion_ids(item)
    evidence_quote = answer.strip() or "(empty answer)"
    return SchoolRubricEvaluation(
        schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
        item_id=item.item_id,
        skill_ids=(item.primary_skill_id,),
        score=0.0,
        confidence=1.0,
        language_detected="en" if english_words else "unknown",
        criteria=tuple(
            SchoolRubricCriterion(
                id=criterion_id,
                met=False,
                quality=0.0,
                evidence_quote=evidence_quote,
            )
            for criterion_id in criterion_ids
        ),
        misconception_tags=tuple(item.misconception_tags),
        blockers=("required_criteria_missing",),
        needs_human_review=False,
        feedback_to_learner="Write a complete answer that uses the clue in the question.",
    )


def build_placement_evaluator_activity(
    item: SchoolPlacementBankItem,
) -> dict[str, Any]:
    """Build the strict provider activity from the item's authored rubric."""

    criterion_ids = _strict_criterion_ids(item)
    activity = {
        "activity_id": item.item_id,
        "item_id": item.item_id,
        "evaluation_mode": "llm_rubric",
        "grading_mode": "strict_open_rubric",
        "rubric_ref": item.rubric_ref,
        "skill_ids": [item.primary_skill_id],
        "task_prompt": item.prompt,
        "prompt": item.prompt,
        "passage": item.passage,
        "certifying_language": "en",
        "pass_score": 0.8,
        "minimum_confidence": 0.75,
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
    if item.semantic_claim_slots:
        activity.update(
            {
                "concept_slots": [
                    {
                        "id": slot.id,
                        "any_of": list(slot.aliases),
                    }
                    for slot in item.semantic_claim_slots
                ],
                "ordered_concept_slot_ids": list(
                    item.ordered_semantic_claim_slot_ids
                ),
                "forbidden_phrases": list(item.forbidden_phrases),
            }
        )
    return activity


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
    insufficient = deterministic_insufficient_strict_placement_evaluation(
        item,
        answer,
    )
    if insufficient is not None:
        return insufficient
    if provider is None:
        raise SchoolPlacementEvaluatorUnavailableError(EVALUATOR_UNAVAILABLE_CODE)

    activity = build_placement_evaluator_activity(item)
    authored_inference = _authored_inference_fallback(
        item,
        answer,
        language_detected=language_detected,
    )
    try:
        raw_evaluation = await provider(activity, answer)
    except SchoolOpenAnswerRetryableError as exc:
        if authored_inference is None:
            raise
        raw_evaluation = authored_inference
    except Exception as exc:
        raise SchoolPlacementEvaluatorUnavailableError(
            EVALUATOR_UNAVAILABLE_CODE
        ) from exc

    try:
        evaluation = validate_placement_provider_evaluation(
            item,
            answer,
            raw_evaluation,
        )
        if (
            authored_inference is not None
            and set(evaluation.blockers).issubset(
                {
                    "evaluator_evidence_untraceable",
                    "required_criteria_missing",
                    "semantic_required_claim_missing",
                }
            )
        ):
            return authored_inference
        return evaluation
    except SchoolPlacementEvaluatorUnavailableError:
        raise
    except Exception as exc:
        raise SchoolPlacementEvaluatorUnavailableError(
            EVALUATOR_UNAVAILABLE_CODE
        ) from exc


def _authored_inference_fallback(
    item: SchoolPlacementBankItem,
    answer: str,
    *,
    language_detected: str,
) -> SchoolRubricEvaluation | None:
    """Recover only inference evidence the authored bank can prove itself."""

    if (
        item.rubric_ref != "school.strict.inference.v1"
        or len(item.semantic_claim_slots) != 2
    ):
        return None
    slots = {slot.id: slot for slot in item.semantic_claim_slots}
    inference_slot = slots.get("inference_claim")
    clue_slot = slots.get("passage_clue")
    if inference_slot is None or clue_slot is None:
        return None
    if any(
        _authored_slot_has_locally_negated_alias(answer, slot)
        for slot in (inference_slot, clue_slot)
    ):
        return None

    inference_quote = _flexible_authored_alias_quote(
        answer,
        inference_slot.aliases,
    )
    clue_quote = _flexible_authored_alias_quote(answer, clue_slot.aliases)
    if not inference_quote or not clue_quote:
        return None
    linkage_clue_quote = clue_quote
    linked = inference_clue_is_explicitly_linked(
        passage=item.passage,
        answer=answer,
        inference_quote=inference_quote,
        clue_quote=linkage_clue_quote,
    )
    if not linked:
        linkage_clue_quote = answer.strip()
        linked = inference_clue_is_explicitly_linked(
            passage=item.passage,
            answer=answer,
            inference_quote=inference_quote,
            clue_quote=linkage_clue_quote,
        )
    if not linked:
        return None

    if _authored_response_has_unsupported_content(
        item,
        answer,
        extra_allowed_tokens=_AUTHORED_INFERENCE_GLUE_TOKENS,
        require_one_sentence=True,
    ):
        return None

    normalized_answer = " ".join(answer.casefold().split())
    if any(
        " ".join(phrase.casefold().split()) in normalized_answer
        for phrase in item.forbidden_phrases
    ):
        return None
    # A deterministic rescue must stay narrower than the provider. Adversative
    # clauses can reverse an otherwise matching inference or clue, so those
    # answers remain provider-owned rather than being auto-certified here.
    if re.search(r"\b(?:although|but|however|though|whereas|yet)\b", normalized_answer):
        return None
    answer_tokens = _word_tokens(answer)
    if (
        len(answer_tokens) < 6
        or len(answer_tokens) > 36
        or not _is_complete_english_response(answer)
    ):
        return None

    evidence_by_criterion = {
        "plausible_inference": inference_quote,
        "relevant_text_clue": linkage_clue_quote,
        "clue_supports_inference": answer.strip(),
        "complete_response": answer.strip(),
        "english_response": answer.strip(),
    }
    criterion_ids = _strict_criterion_ids(item)
    if set(criterion_ids) != set(evidence_by_criterion):
        return None
    return SchoolRubricEvaluation(
        schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
        item_id=item.item_id,
        skill_ids=(item.primary_skill_id,),
        score=1.0,
        confidence=0.98,
        language_detected=(
            "en"
            if language_detected.strip().casefold() in {"en", "eng", "english"}
            else "unknown"
        ),
        criteria=tuple(
            SchoolRubricCriterion(
                id=criterion_id,
                met=True,
                quality=1.0,
                evidence_quote=evidence_by_criterion[criterion_id],
            )
            for criterion_id in criterion_ids
        ),
        misconception_tags=(),
        blockers=(),
        needs_human_review=False,
        feedback_to_learner="Your inference and supporting clue were recorded.",
    )


def _flexible_authored_alias_quote(
    answer: str,
    aliases: tuple[str, ...],
) -> str | None:
    """Find an authored phrase while allowing a small non-negating modifier."""

    match = _flexible_authored_alias_match(answer, aliases)
    return match[2] if match is not None else None


def _flexible_authored_alias_match(
    answer: str,
    aliases: tuple[str, ...],
) -> tuple[int, int, str] | None:
    matches = _flexible_authored_alias_matches(answer, aliases)
    return matches[0] if matches else None


def _flexible_authored_alias_matches(
    answer: str,
    aliases: tuple[str, ...],
) -> tuple[tuple[int, int, str], ...]:
    candidates: list[tuple[int, int, str]] = []
    for alias in aliases:
        alias_tokens = _word_tokens(alias)
        if not alias_tokens:
            continue
        pattern = _flexible_authored_alias_pattern(alias_tokens)
        for match in re.finditer(pattern, answer, flags=re.IGNORECASE | re.UNICODE):
            quote = answer[match.start() : match.end()]
            if _authored_alias_match_is_locally_negated(
                answer,
                start=match.start(),
                end=match.end(),
                alias_tokens=alias_tokens,
            ):
                continue
            candidates.append((match.start(), match.end(), quote))
    return tuple(
        sorted(
            set(candidates),
            key=lambda candidate: (candidate[0], -len(candidate[2])),
        )
    )


def _flexible_authored_alias_pattern(alias_tokens: tuple[str, ...]) -> str:
    separator = r"(?:\W+[^\W\d_]+){0,2}\W+"
    return r"(?<!\w)" + separator.join(
        re.escape(token) for token in alias_tokens
    ) + r"(?!\w)"


def _authored_alias_match_is_locally_negated(
    answer: str,
    *,
    start: int,
    end: int,
    alias_tokens: tuple[str, ...],
) -> bool:
    alias_negations = set(alias_tokens) & _AUTHORED_EXTRA_NEGATION_TOKENS
    quote_negations = (
        set(_word_tokens(answer[start:end])) & _AUTHORED_EXTRA_NEGATION_TOKENS
    )
    if quote_negations - alias_negations:
        return True

    prefix = answer[:start]
    boundaries = tuple(
        re.finditer(
            r"[,;.!?]|\b(?:although|and|because|but|however|or|so|though|"
            r"whereas|while|yet)\b",
            prefix,
            flags=re.IGNORECASE | re.UNICODE,
        )
    )
    local_prefix = prefix[boundaries[-1].end() :] if boundaries else prefix
    return bool(
        set(_word_tokens(local_prefix)[-4:])
        & _AUTHORED_EXTRA_NEGATION_TOKENS
    )


def _authored_slot_has_locally_negated_alias(
    answer: str,
    slot: PlacementSemanticClaimSlot,
) -> bool:
    for alias in slot.aliases:
        alias_tokens = _word_tokens(alias)
        if not alias_tokens:
            continue
        pattern = _flexible_authored_alias_pattern(alias_tokens)
        if any(
            _authored_alias_match_is_locally_negated(
                answer,
                start=match.start(),
                end=match.end(),
                alias_tokens=alias_tokens,
            )
            for match in re.finditer(
                pattern,
                answer,
                flags=re.IGNORECASE | re.UNICODE,
            )
        ):
            return True
    return False


def _looks_like_english_response(answer: str) -> bool:
    letters = re.findall(r"[^\W\d_]", answer, flags=re.UNICODE)
    if not letters:
        return False
    devanagari = re.findall(r"[\u0900-\u097f]", answer)
    latin = re.findall(r"[A-Za-z]", answer)
    return bool(latin) and len(devanagari) / len(letters) < 0.2


def _word_tokens(value: str) -> tuple[str, ...]:
    return tuple(
        re.findall(r"[^\W\d_]+", value.casefold(), flags=re.UNICODE)
    )


def _correct_authored_inference_criteria(
    item: SchoolPlacementBankItem,
    answer: str,
    evaluation: SchoolRubricEvaluation,
) -> SchoolRubricEvaluation:
    """Reject only inference evidence contradicted by a locally negated slot."""

    if item.rubric_ref != "school.strict.inference.v1":
        return evaluation

    negated_slot_ids = {
        slot.id
        for slot in item.semantic_claim_slots
        if _authored_slot_has_locally_negated_alias(answer, slot)
    }
    controlled_ids: set[str] = set()
    if "inference_claim" in negated_slot_ids:
        controlled_ids.add("plausible_inference")
    if "passage_clue" in negated_slot_ids:
        controlled_ids.add("relevant_text_clue")
    if controlled_ids:
        controlled_ids.add("clue_supports_inference")
    if not controlled_ids:
        return evaluation

    evidence_quote = answer.strip() or "(empty answer)"
    return evaluation.model_copy(
        update={
            "criteria": [
                criterion.model_copy(
                    update={
                        "met": False,
                        "quality": 0.0,
                        "evidence_quote": evidence_quote,
                    }
                )
                if criterion.id in controlled_ids
                else criterion
                for criterion in evaluation.criteria
            ]
        }
    )


def _correct_authored_claim_criteria(
    item: SchoolPlacementBankItem,
    answer: str,
    evaluation: SchoolRubricEvaluation,
) -> SchoolRubricEvaluation:
    """Make authored item claims authoritative over generic model semantics."""

    if (
        not item.semantic_claim_slots
        or item.rubric_ref == "school.strict.inference.v1"
    ):
        return evaluation

    if item.rubric_ref == "school.strict.complete_sentence.class3.v1":
        controlled_ids = _AUTHORED_COMPLETE_SENTENCE_CRITERIA
    elif item.rubric_ref == "school.strict.short_answer.v1":
        controlled_ids = _AUTHORED_SHORT_ANSWER_CRITERIA
    else:
        return evaluation

    verdict = authored_claim_response_verdict(item, answer)
    if verdict == "unknown":
        return evaluation

    met = verdict == "proven_true"
    evidence_quote = answer.strip() or "(empty answer)"
    return evaluation.model_copy(
        update={
            "criteria": [
                criterion.model_copy(
                    update={
                        "met": met,
                        "quality": 1.0 if met else 0.0,
                        "evidence_quote": evidence_quote,
                    }
                )
                if criterion.id in controlled_ids
                else criterion
                for criterion in evaluation.criteria
            ],
            "blockers": (
                _without_repaired_evidence_blockers(evaluation.blockers)
                if met
                else evaluation.blockers
            ),
        }
    )


def _correct_authored_summary_criteria(
    item: SchoolPlacementBankItem,
    answer: str,
    evaluation: SchoolRubricEvaluation,
) -> SchoolRubricEvaluation:
    """Correct only the summary criteria the authored evidence can prove."""

    verdict = _authored_summary_response_verdict(item, answer)
    if verdict == "unknown":
        return evaluation

    met = verdict == "proven_true"
    if verdict == "factual_false":
        controlled_ids = frozenset({"essential_details"})
    elif verdict == "form_false":
        controlled_ids = frozenset({"concise_complete_response"})
    else:
        controlled_ids = _AUTHORED_SUMMARY_CRITERIA
    evidence_quote = answer.strip() or "(empty answer)"
    return evaluation.model_copy(
        update={
            "criteria": [
                criterion.model_copy(
                    update={
                        "met": met,
                        "quality": 1.0 if met else 0.0,
                        "evidence_quote": evidence_quote,
                    }
                )
                if criterion.id in controlled_ids
                else criterion
                for criterion in evaluation.criteria
            ],
            "blockers": (
                _without_repaired_evidence_blockers(evaluation.blockers)
                if met
                else evaluation.blockers
            ),
        }
    )


def _authored_summary_response_verdict(
    item: SchoolPlacementBankItem,
    answer: str,
) -> AuthoredSummaryResponseVerdict:
    """Return only criterion-level conclusions the authored summary can prove."""

    if item.rubric_ref != "school.strict.summary.v1" or not item.semantic_claim_slots:
        return "unknown"

    if any(
        _authored_slot_has_locally_negated_alias(answer, slot)
        for slot in item.semantic_claim_slots
    ):
        return "factual_false"

    slot_matches = tuple(
        _flexible_authored_alias_match(answer, slot.aliases)
        for slot in item.semantic_claim_slots
    )
    matched_spans = tuple(
        (match[0], match[1])
        for match in slot_matches
        if match is not None
    )
    if all(match is not None for match in slot_matches):
        if _authored_response_has_unsupported_content(
            item,
            answer,
            extra_allowed_tokens=_AUTHORED_SUMMARY_GLUE_TOKENS,
            require_one_sentence=False,
        ):
            return "factual_false"
    elif matched_spans and not _has_substantive_unmatched_content(
        answer,
        matched_spans,
    ):
        return "factual_false"
    else:
        return "unknown"

    # Copy is direct evidence only for own_words. That criterion has already
    # been corrected by correct_semantic_criterion before this authored pass.
    if copies_source_passage(passage=item.passage, answer=answer):
        return "unknown"
    if (
        not _is_complete_english_response(answer)
        or len(_word_tokens(answer)) > 42
    ):
        return "form_false"
    return "proven_true"


def _without_repaired_evidence_blockers(blockers: tuple[str, ...] | list[str]) -> list[str]:
    return [
        blocker
        for blocker in blockers
        if blocker not in {
            "evaluator_evidence_untraceable",
            "required_criteria_missing",
            "semantic_required_claim_missing",
        }
    ]


def _authored_response_has_unsupported_content(
    item: SchoolPlacementBankItem,
    answer: str,
    *,
    extra_allowed_tokens: frozenset[str],
    require_one_sentence: bool,
) -> bool:
    """Reject authored rescue when the response adds claims the bank cannot prove."""

    normalized = answer.casefold()
    sentence_count = len(
        tuple(
            sentence
            for sentence in re.split(r"(?<=[.!?])\s+", answer.strip())
            if sentence.strip()
        )
    )
    if require_one_sentence and sentence_count != 1:
        return True
    if re.search(r"\b(?:although|but|however|though|whereas|yet)\b", normalized):
        return True

    matched_spans = tuple(
        (match_start, match_end)
        for slot in item.semantic_claim_slots
        for match_start, match_end, _quote in _flexible_authored_alias_matches(
            answer,
            slot.aliases,
        )
    )
    if (
        item.rubric_ref == "school.strict.summary.v1"
        and _has_unmatched_authored_clause(
            answer,
            matched_spans,
            extra_allowed_tokens=extra_allowed_tokens,
        )
    ):
        return True

    allowed_tokens = (
        set(_word_tokens(item.passage))
        | set(_word_tokens(item.prompt))
        | set(_AUTHORED_FUNCTION_TOKENS)
        | set(extra_allowed_tokens)
        | {
            token
            for slot in item.semantic_claim_slots
            for alias in slot.aliases
            for token in _word_tokens(alias)
        }
    )
    unsupported = tuple(
        token for token in _word_tokens(answer) if token not in allowed_tokens
    )
    return len(unsupported) >= 2


def _has_unmatched_authored_clause(
    answer: str,
    matched_spans: tuple[tuple[int, int], ...],
    *,
    extra_allowed_tokens: frozenset[str],
) -> bool:
    boundaries = tuple(
        re.finditer(
            r"[,;.!?]+|\b(?:although|and|because|but|however|or|so|then|"
            r"though|whereas|while|yet)\b",
            answer,
            flags=re.IGNORECASE | re.UNICODE,
        )
    )
    clause_spans: list[tuple[int, int]] = []
    start = 0
    for boundary in boundaries:
        if start < boundary.start():
            clause_spans.append((start, boundary.start()))
        start = boundary.end()
    if start < len(answer):
        clause_spans.append((start, len(answer)))

    ignored_tokens = (
        set(_AUTHORED_FUNCTION_TOKENS)
        | set(_AUTHORED_JOIN_TOKENS)
        | set(extra_allowed_tokens)
    )
    for clause_start, clause_end in clause_spans:
        if any(
            match_start < clause_end and clause_start < match_end
            for match_start, match_end in matched_spans
        ):
            continue
        content_tokens = tuple(
            token
            for token in _word_tokens(answer[clause_start:clause_end])
            if token not in ignored_tokens
        )
        if len(content_tokens) >= 2:
            return True
    return False


def _has_substantive_unmatched_content(
    answer: str,
    matched_spans: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> bool:
    remainder = list(answer)
    for start, end in matched_spans:
        remainder[start:end] = " " * (end - start)
    ignored_tokens = set(_AUTHORED_FUNCTION_TOKENS) | set(_AUTHORED_JOIN_TOKENS)
    substantive_tokens = tuple(
        token
        for token in _word_tokens("".join(remainder))
        if token not in ignored_tokens
    )
    return len(substantive_tokens) >= 2


def authored_claim_response_verdict(
    item: SchoolPlacementBankItem,
    answer: str,
) -> AuthoredClaimResponseVerdict:
    """Return only semantic conclusions the authored item can prove."""

    if (
        not item.semantic_claim_slots
        or item.rubric_ref
        not in {
            "school.strict.complete_sentence.class3.v1",
            "school.strict.short_answer.v1",
        }
    ):
        return "unknown"

    response = answer.strip()
    normalized = normalize_placement_answer(response)
    if not normalized:
        return "unknown"
    if any(
        _normalized_phrase_spans(normalized, forbidden)
        for forbidden in item.forbidden_phrases
    ):
        return "proven_false"

    matched_spans: list[tuple[int, int]] = []
    missing_slot = False
    for slot in item.semantic_claim_slots:
        if _authored_slot_has_locally_negated_alias(response, slot):
            return "proven_false"
        slot_spans: list[tuple[int, int]] = []
        for alias in slot.aliases:
            normalized_alias = normalize_placement_answer(alias)
            slot_spans.extend(
                _normalized_phrase_spans(normalized, normalized_alias)
            )
        if not slot_spans:
            if _contains_authored_predicate_fragment(normalized, slot):
                return "proven_false"
            missing_slot = True
            continue
        matched_spans.extend(slot_spans)

    if missing_slot:
        # A matched slot proves nothing about substantive unmatched text: that
        # text may be a valid paraphrase owned by the provider. Only an answer
        # with no remaining claim content is provably partial here.
        if matched_spans and not _has_substantive_unmatched_content(
            normalized,
            matched_spans,
        ):
            return "proven_false"
        return "unknown"

    if not _is_complete_english_response(response):
        return "proven_false"

    remainder = list(normalized)
    for start, end in matched_spans:
        remainder[start:end] = " " * (end - start)
    remainder_text = "".join(remainder)
    remainder_tokens = _word_tokens(remainder_text)
    unsupported_tokens = tuple(
        token
        for token in remainder_tokens
        if token not in _AUTHORED_JOIN_TOKENS
    )
    if not unsupported_tokens:
        return "proven_true"
    if _AUTHORED_EXTRA_NEGATION_TOKENS.intersection(remainder_tokens):
        return "unknown"
    if _has_unsupported_extra_clause(remainder_text, remainder_tokens):
        return "proven_false"
    return "unknown"


def _normalized_phrase_spans(
    normalized_response: str,
    phrase: str,
) -> tuple[tuple[int, int], ...]:
    normalized_phrase = normalize_placement_answer(phrase)
    if not normalized_phrase:
        return ()
    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"
    return tuple(
        (match.start(), match.end())
        for match in re.finditer(pattern, normalized_response)
    )


def _contains_authored_predicate_fragment(
    normalized_response: str,
    slot: PlacementSemanticClaimSlot,
) -> bool:
    for alias in slot.aliases:
        alias_tokens = _word_tokens(normalize_placement_answer(alias))
        for anchor in slot.predicate_anchors:
            anchor_tokens = _word_tokens(normalize_placement_answer(anchor))
            anchor_size = len(anchor_tokens)
            if not anchor_size:
                continue
            for index in range(len(alias_tokens) - anchor_size + 1):
                if alias_tokens[index:index + anchor_size] != anchor_tokens:
                    continue
                fragment_tokens = (
                    alias_tokens[:index] + alias_tokens[index + anchor_size:]
                )
                if len(fragment_tokens) < 3:
                    continue
                fragment = " ".join(fragment_tokens)
                if _normalized_phrase_spans(normalized_response, fragment):
                    return True
    return False


def _is_complete_english_response(response: str) -> bool:
    if (
        not response
        or not _looks_like_english_response(response)
        or not re.search(r"[.!?][\"']?$", response)
    ):
        return False
    if re.search(
        r"\b(?:although|and|because|but|however|or|so|then|when|while|yet)[.!?][\"']?$",
        response.casefold(),
    ):
        return False
    sentence_texts = tuple(
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", response)
        if sentence.strip()
    )
    return bool(sentence_texts) and len(sentence_texts) <= 2 and all(
        len(_word_tokens(sentence)) >= 3
        and next(
            (character.isupper() for character in sentence if character.isalpha()),
            False,
        )
        for sentence in sentence_texts
    )


def _has_unsupported_extra_clause(
    remainder_text: str,
    remainder_tokens: tuple[str, ...],
) -> bool:
    if re.search(r"[.;!?]", remainder_text):
        return True
    return bool(
        _AUTHORED_CLAUSE_MARKERS.intersection(remainder_tokens)
        and len(
            tuple(
                token
                for token in remainder_tokens
                if token not in _AUTHORED_JOIN_TOKENS
            )
        )
        >= 2
    )


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
            evaluation.schema_version != OPEN_RUBRIC_SCHEMA_VERSION
            or evaluation.item_id != item.item_id
            or evaluation.skill_ids != (item.primary_skill_id,)
            or [criterion.id for criterion in evaluation.criteria]
            != list(criterion_ids)
            or evaluation.needs_human_review
            or "needs_human_review" in evaluation.blockers
        ):
            raise ValueError("invalid_placement_evaluator_contract")

        evaluation = _canonicalize_evidence_quotes(evaluation, answer)
        criterion_by_id = {
            criterion.id: criterion for criterion in evaluation.criteria
        }
        evaluation = evaluation.model_copy(
            update={
                "criteria": [
                    correct_semantic_criterion(
                        criterion,
                        passage=item.passage,
                        answer=answer,
                        criterion_by_id=criterion_by_id,
                    )
                    for criterion in evaluation.criteria
                ]
            }
        )
        evaluation = _correct_authored_inference_criteria(
            item,
            answer,
            evaluation,
        )
        evaluation = _correct_authored_claim_criteria(
            item,
            answer,
            evaluation,
        )
        evaluation = _correct_authored_summary_criteria(
            item,
            answer,
            evaluation,
        )
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

        blockers = [
            blocker
            for blocker in evaluation.blockers
            if blocker not in {"language_mismatch", "required_criteria_missing"}
        ]
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
        canonical_quote = _traceable_quote(answer, quote)
        if quote == "(empty answer)":
            if criterion.met:
                if not learner_evidence:
                    raise ValueError("untraceable_placement_evidence")
                quote = learner_evidence
        elif canonical_quote is not None:
            quote = canonical_quote
        elif quote not in answer:
            if criterion.met:
                if not learner_evidence:
                    raise ValueError("untraceable_placement_evidence")
                quote = learner_evidence
            else:
                quote = "(empty answer)"
        criteria.append(criterion.model_copy(update={"evidence_quote": quote}))
    return evaluation.model_copy(update={"criteria": criteria})


def _traceable_quote(answer: str, quote: str) -> str | None:
    if not quote or quote == "(empty answer)":
        return None
    exact_start = answer.find(quote)
    if exact_start >= 0:
        return answer[exact_start : exact_start + len(quote)]
    trimmed = quote.strip().strip(".,!?;:\"'“”‘’")
    if not trimmed:
        return None
    start = answer.casefold().find(trimmed.casefold())
    if start < 0:
        return None
    return answer[start : start + len(trimmed)]
