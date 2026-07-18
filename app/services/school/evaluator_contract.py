"""Context-bound validation for canonical School rubric evaluations.

The model reports evidence. Backend-authored context owns the item, scored
skills, criteria, and human-review policy used by downstream projection.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_schema import (
    GradingMode,
    SchoolOpenSemanticValidatorId,
)
from app.services.school.semantic_evidence import (
    authored_evidence_can_prove_criterion,
)


RUBRIC_SCHEMA_VERSION = "school-v3-rubric-1"
OPEN_RUBRIC_SCHEMA_VERSION = "school.open.v1"
HumanReviewPolicy = Literal["forbid", "allow"]


class SchoolOpenAnswerRetryableError(RuntimeError):
    """A provider or wire-contract failure that must not produce evidence."""

    retryable = True
    evidence = None

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


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


class SchoolOpenEvaluationContext(SchoolEvaluationContext):
    """Backend-owned context for the strict School open-answer contract."""

    relevance_terms: tuple[str, ...] = ()
    source_texts: tuple[str, ...] = ()
    exemplar_texts: tuple[str, ...] = ()
    certifying_language: str | None = None
    semantic_claim_slots: tuple["SchoolSemanticClaimSlot", ...] = ()
    ordered_semantic_claim_slot_ids: tuple[str, ...] = ()
    forbidden_phrases: tuple[str, ...] = ()
    semantic_validator_id: SchoolOpenSemanticValidatorId | None = None

    @field_validator(
        "relevance_terms",
        "source_texts",
        "exemplar_texts",
        "semantic_claim_slots",
        "ordered_semantic_claim_slot_ids",
        "forbidden_phrases",
        mode="before",
    )
    @classmethod
    def _tuple_optional_collections(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator(
        "relevance_terms",
        "source_texts",
        "exemplar_texts",
        "ordered_semantic_claim_slot_ids",
        "forbidden_phrases",
    )
    @classmethod
    def _clean_optional_collections(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned) or len(cleaned) != len(
            set(cleaned)
        ):
            raise ValueError("school_open_context_list_value_invalid")
        return cleaned

    @field_validator("certifying_language")
    @classmethod
    def _clean_optional_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().casefold()
        if not cleaned:
            raise ValueError("school_open_context_language_empty")
        return cleaned

    @model_validator(mode="after")
    def _semantic_claim_order_is_authored(self) -> "SchoolOpenEvaluationContext":
        slot_ids = tuple(slot.id for slot in self.semantic_claim_slots)
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("school_open_semantic_claim_slot_duplicate")
        if self.ordered_semantic_claim_slot_ids and not set(
            self.ordered_semantic_claim_slot_ids
        ).issubset(slot_ids):
            raise ValueError("school_open_semantic_claim_order_invalid")
        return self


class SchoolSemanticClaimSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: str
    description: str = ""
    aliases: tuple[str, ...] = Field(min_length=1)

    @field_validator("aliases", mode="before")
    @classmethod
    def _tuple_aliases(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("id")
    @classmethod
    def _clean_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("school_open_semantic_claim_id_empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def _clean_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("aliases")
    @classmethod
    def _clean_aliases(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
            raise ValueError("school_open_semantic_claim_alias_invalid")
        return cleaned


_REPETITION_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "from",
        "he",
        "her",
        "his",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "she",
        "so",
        "that",
        "the",
        "their",
        "they",
        "this",
        "to",
        "was",
        "were",
        "with",
    }
)

_GENERIC_RELEVANCE_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "answer",
        "because",
        "believe",
        "but",
        "could",
        "feel",
        "i",
        "in",
        "it",
        "my",
        "opinion",
        "reason",
        "she",
        "should",
        "since",
        "so",
        "that",
        "the",
        "they",
        "think",
        "this",
        "we",
        "would",
    }
)

_ART_ROOM_INVESTIGATION_ROOTS = frozenset(
    {
        "check",
        "examine",
        "explore",
        "follow",
        "go",
        "head",
        "inspect",
        "investigate",
        "look",
        "search",
        "test",
        "try",
        "visit",
    }
)
_ART_ROOM_CHOICE_ROOTS = frozenset(
    {
        "begin",
        "choose",
        "opt",
        "pick",
        "prefer",
        "prioritise",
        "prioritize",
        "select",
        "start",
        "take",
    }
)
_ART_ROOM_ACTION_ROOTS = (
    _ART_ROOM_INVESTIGATION_ROOTS | _ART_ROOM_CHOICE_ROOTS
)
_SUPPORT_ACTION_ROOTS = frozenset(
    {"assist", "explain", "guide", "help", "point", "show"}
)
_REFUSAL_ROOTS = frozenset({"avoid", "decline", "refuse", "withhold"})
_ATTITUDE_REJECTION_ROOTS = frozenset(
    {"deny", "dismiss", "object", "oppose", "reject"}
)
_MOCKERY_ACTION_ROOTS = frozenset(
    {
        "belittle",
        "deride",
        "humiliate",
        "jeer",
        "mock",
        "ridicule",
        "taunt",
        "tease",
    }
)
_NEGATION_ROOTS = frozenset({"cannot", "neither", "never", "no", "not"})
_AFFIRMATIVE_WITHOUT_ATTITUDE_ROOTS = frozenset(
    {"delay", "doubt", "hesitation", "pause", "reluctance", "reservation"}
)
_KIND_ATTITUDE_ROOTS = frozenset(
    {"calmly", "gently", "kindly", "kindness", "politely"}
)
_SUBJECT_ROOTS = frozenset({"he", "i", "she", "they", "we", "you"})
_SEMANTIC_ROOT_VOCABULARY = frozenset(
    {
        *_AFFIRMATIVE_WITHOUT_ATTITUDE_ROOTS,
        *_ART_ROOM_ACTION_ROOTS,
        *_ATTITUDE_REJECTION_ROOTS,
        *_KIND_ATTITUDE_ROOTS,
        *_MOCKERY_ACTION_ROOTS,
        *_NEGATION_ROOTS,
        *_REFUSAL_ROOTS,
        *_SUBJECT_ROOTS,
        *_SUPPORT_ACTION_ROOTS,
        "art",
        "at",
        "fun",
        "laugh",
        "make",
        "only",
        "out",
        "room",
        "rule",
        "without",
    }
)
_IRREGULAR_SEMANTIC_ROOTS = {
    "began": "begin",
    "begun": "begin",
    "chose": "choose",
    "chosen": "choose",
    "gone": "go",
    "goes": "go",
    "made": "make",
    "showed": "show",
    "shown": "show",
    "taken": "take",
    "took": "take",
    "went": "go",
    "withheld": "withhold",
}
_SEMANTIC_CLAUSE_BOUNDARY_RE = re.compile(
    r"[.!?;:\n]+|\b(?:"
    r"although|and|because|but|however|since|so|still|then|though|while|yet"
    r")\b"
)
_SEMANTIC_WORD_RE = re.compile(r"[a-z]+(?:['\u2019][a-z]+)?")
_NEGATED_CONTRACTION_RE = re.compile(r"\b([a-z]+)n['\u2019]t\b")


@dataclass(frozen=True)
class _SemanticToken:
    text: str
    root: str


def school_open_context_from_activity(
    activity: Mapping[str, Any],
    answer: str,
) -> SchoolOpenEvaluationContext:
    """Build one backend authority packet for provider and commit validation."""

    if (
        activity.get("semantic_validator_id") is not None
        and activity.get("grading_mode") != "strict_open_rubric"
    ):
        raise ValueError("semantic_validator_requires_strict_open_rubric")
    item_id = activity.get("activity_id") or activity.get("item_id")
    explicit_relevance = tuple(activity.get("relevance_terms") or ())
    relevance_terms = tuple(
        dict.fromkeys(str(term).strip() for term in explicit_relevance)
    )
    source_texts = tuple(
        dict.fromkeys(
            str(value).strip()
            for value in (
                *(activity.get("source_texts") or ()),
                activity.get("passage"),
            )
            if value and str(value).strip()
        )
    )
    semantic_claim_slots = tuple(
        SchoolSemanticClaimSlot(
            id=str(slot.get("id") or ""),
            description=str(slot.get("description") or ""),
            aliases=tuple(str(alias) for alias in slot.get("any_of") or ()),
        )
        for slot in activity.get("concept_slots") or ()
    )
    return SchoolOpenEvaluationContext(
        expected_item_id=str(item_id or ""),
        scored_skill_ids=tuple(str(item) for item in activity.get("skill_ids") or ()),
        criterion_policies=tuple(
            SchoolCriterionPolicy(
                id=str(criterion["id"]),
                required=bool(criterion.get("required", True)),
                min_quality=float(criterion.get("min_quality", 0.6)),
            )
            for criterion in activity.get("rubric_criteria") or ()
        ),
        pass_score=float(activity.get("pass_score", 0.8)),
        minimum_confidence=float(activity.get("minimum_confidence", 0.65)),
        learner_answer=answer,
        human_review_policy="allow",
        relevance_terms=relevance_terms,
        source_texts=source_texts,
        exemplar_texts=tuple(
            str(value)
            for value in activity.get("exemplar_texts") or ()
            if str(value).strip()
        ),
        certifying_language=activity.get("certifying_language"),
        semantic_claim_slots=semantic_claim_slots,
        ordered_semantic_claim_slot_ids=tuple(
            str(item)
            for item in activity.get("ordered_concept_slot_ids") or ()
        ),
        forbidden_phrases=tuple(
            str(item) for item in activity.get("forbidden_phrases") or ()
        ),
        semantic_validator_id=activity.get("semantic_validator_id"),
    )

class SchoolTypedCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: str
    met: bool
    quality: float = Field(ge=0.0, le=1.0)
    evidence_quote: str


class SchoolTypedGradingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    grading_mode: GradingMode
    correct: bool
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    criteria: tuple[SchoolTypedCriterion, ...]
    missing_criteria: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    evidence_quote: str


@dataclass(frozen=True)
class ValidatedSchoolRubricEvaluation:
    evaluation: SchoolRubricEvaluation
    context: SchoolEvaluationContext
    backend_blockers: tuple[str, ...] = ()

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
    def effective_blockers(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((*self.evaluation.blockers, *self.backend_blockers))
        )

    @property
    def attempt_evidence_eligible(self) -> bool:
        """Whether this attempt may enter certification history.

        Readiness and mastery remain longitudinal shared-core decisions.
        """
        return (
            self.aggregate_score >= self.context.pass_score
            and self.meets_required_criteria
            and self.meets_confidence_requirement
            and not self.requires_human_review
            and not self.effective_blockers
        )

    @property
    def certification_eligible(self) -> bool:
        return self.attempt_evidence_eligible


def _normalized_trace_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _normalized_answer_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return re.sub(r"\s+", " ", normalized)


def _semantic_root(word: str) -> str:
    irregular = _IRREGULAR_SEMANTIC_ROOTS.get(word)
    if irregular is not None:
        return irregular
    if word in _SEMANTIC_ROOT_VOCABULARY:
        return word

    candidates: list[str] = []
    if len(word) > 4 and word.endswith(("ied", "ies")):
        candidates.append(f"{word[:-3]}y")
    if len(word) > 5 and word.endswith("ing"):
        stem = word[:-3]
        candidates.extend((stem, f"{stem}e"))
        if len(stem) > 2 and stem[-1] == stem[-2]:
            candidates.append(stem[:-1])
    if len(word) > 4 and word.endswith("ed"):
        stem = word[:-2]
        candidates.extend((stem, f"{stem}e"))
        if len(stem) > 2 and stem[-1] == stem[-2]:
            candidates.append(stem[:-1])
    if len(word) > 4 and word.endswith("es"):
        candidates.extend((word[:-2], word[:-1]))
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        candidates.append(word[:-1])
    return next(
        (
            candidate
            for candidate in candidates
            if candidate in _SEMANTIC_ROOT_VOCABULARY
        ),
        word,
    )


def _semantic_clauses(
    answer: str,
) -> tuple[tuple[_SemanticToken, ...], ...]:
    normalized = _normalized_answer_text(answer)
    expanded = _NEGATED_CONTRACTION_RE.sub(r"\1 not", normalized)
    clauses: list[tuple[_SemanticToken, ...]] = []
    for clause_text in _SEMANTIC_CLAUSE_BOUNDARY_RE.split(expanded):
        words = _SEMANTIC_WORD_RE.findall(clause_text)
        if words:
            clauses.append(
                tuple(
                    _SemanticToken(text=word, root=_semantic_root(word))
                    for word in words
                )
            )
    return tuple(clauses)


def _is_rejection_marker(
    clause: tuple[_SemanticToken, ...],
    index: int,
) -> bool:
    root = clause[index].root
    if root in _REFUSAL_ROOTS or root in _ATTITUDE_REJECTION_ROOTS:
        return True
    return (
        root == "rule"
        and index + 1 < len(clause)
        and clause[index + 1].root == "out"
    )


def _negation_precedes_action(
    clause: tuple[_SemanticToken, ...],
    action_index: int,
) -> bool:
    for index, token in enumerate(clause[:action_index]):
        if token.root not in _NEGATION_ROOTS:
            continue
        next_root = (
            clause[index + 1].root
            if index + 1 < action_index
            else None
        )
        if token.root == "not" and next_root == "only":
            continue
        if (
            token.root == "no"
            and next_root in _AFFIRMATIVE_WITHOUT_ATTITUDE_ROOTS
        ):
            continue
        return True
    return False


def _without_scopes_action(
    clause: tuple[_SemanticToken, ...],
    action_index: int,
) -> bool:
    for index, token in enumerate(clause[:action_index]):
        if token.root != "without":
            continue
        complement = clause[index + 1 : action_index]
        if any(
            item.root in _AFFIRMATIVE_WITHOUT_ATTITUDE_ROOTS
            for item in complement
        ):
            continue
        if any(item.root in _SUBJECT_ROOTS for item in complement):
            continue
        return True
    return False


def _action_is_rejected(
    clause: tuple[_SemanticToken, ...],
    action_index: int,
    *,
    target_index: int | None = None,
) -> bool:
    if _negation_precedes_action(clause, action_index):
        return True
    if any(
        _is_rejection_marker(clause, index)
        for index in range(action_index)
    ):
        return True
    if _without_scopes_action(clause, action_index):
        return True
    if target_index is not None and target_index > action_index:
        if any(
            token.root in _NEGATION_ROOTS
            for token in clause[action_index + 1 : target_index]
        ):
            return True
    return False


def _art_room_target_indices(
    clause: tuple[_SemanticToken, ...],
) -> tuple[int, ...]:
    return tuple(
        index
        for index, token in enumerate(clause[:-1])
        if token.root == "art" and clause[index + 1].root == "room"
    )


def _blocks_evidence_over_unsupported_guess(answer: str) -> bool:
    for clause in _semantic_clauses(answer):
        target_indices = _art_room_target_indices(clause)
        if not target_indices:
            continue
        for action_index, token in enumerate(clause):
            if token.root not in _ART_ROOM_ACTION_ROOTS:
                continue
            if any(
                not _action_is_rejected(
                    clause,
                    action_index,
                    target_index=target_index,
                )
                for target_index in target_indices
            ):
                return True
    return False


def _is_support_action(
    clause: tuple[_SemanticToken, ...],
    index: int,
) -> bool:
    root = clause[index].root
    if root not in _SUPPORT_ACTION_ROOTS:
        return False
    return root != "explain" or any(
        token.root in _KIND_ATTITUDE_ROOTS for token in clause
    )


def _mockery_action_indices(
    clause: tuple[_SemanticToken, ...],
) -> tuple[int, ...]:
    indices = {
        index
        for index, token in enumerate(clause)
        if token.root in _MOCKERY_ACTION_ROOTS
    }
    for index, token in enumerate(clause):
        if token.root == "make" and any(
            item.root == "fun" for item in clause[index + 1 :]
        ):
            indices.add(index)
        if token.root == "laugh" and any(
            item.root == "at" for item in clause[index + 1 :]
        ):
            indices.add(index)
    return tuple(sorted(indices))


def _blocks_affirmative_support_or_no_mocking(answer: str) -> bool:
    affirmative_support = False
    rejected_support = False
    rejected_mockery = False
    for clause in _semantic_clauses(answer):
        for action_index in range(len(clause)):
            if not _is_support_action(clause, action_index):
                continue
            if _action_is_rejected(clause, action_index):
                rejected_support = True
            else:
                affirmative_support = True
        for action_index in _mockery_action_indices(clause):
            if _action_is_rejected(clause, action_index):
                rejected_mockery = True
            else:
                return True
    return bool(
        rejected_support
        and not affirmative_support
        and not rejected_mockery
    )


SchoolOpenSemanticValidator = Callable[[str], bool]
_SCHOOL_OPEN_SEMANTIC_VALIDATORS: Mapping[
    SchoolOpenSemanticValidatorId,
    SchoolOpenSemanticValidator,
] = {
    "evidence_over_unsupported_guess_v1": (
        _blocks_evidence_over_unsupported_guess
    ),
    "affirmative_support_or_no_mocking_v1": (
        _blocks_affirmative_support_or_no_mocking
    ),
}


def _semantic_validator_blocks(
    validator_id: SchoolOpenSemanticValidatorId,
    answer: str,
) -> bool:
    return _SCHOOL_OPEN_SEMANTIC_VALIDATORS[validator_id](answer)


def _validate_typed_runtime_authority(
    activity: Mapping[str, Any],
    mode: GradingMode,
) -> None:
    options = tuple(str(item) for item in activity.get("options") or ())
    accepted = tuple(
        str(item) for item in activity.get("accepted_answers") or ()
    )
    semantic_ids = tuple(
        str(item)
        for field in ("skill_ids", "knowledge_components")
        for item in activity.get(field) or ()
    )
    semantic = any(
        marker in identifier.casefold()
        for identifier in semantic_ids
        for marker in (
            "inference",
            "reason",
            "summary",
            "relationship",
            "comparison",
            "own_words",
            "own-words",
        )
    )
    certifying = activity.get("evidence_role", "certifying") == "certifying"
    if semantic and certifying and mode != "strict_open_rubric":
        raise ValueError("semantic_activity_requires_strict_open")
    if mode == "selected_option":
        if len(options) < 2 or not accepted or not set(accepted).issubset(set(options)):
            raise ValueError("selected_option_requires_authored_options")
        return
    if mode == "exact_text":
        if options or not accepted or any(
            len(item.split()) > 12 or "\n" in item for item in accepted
        ):
            raise ValueError("exact_text_requires_short_facts")
        return
    if mode == "punctuation_symbol":
        if options or not accepted or not set(accepted).issubset(
            {"?", ".", "!", ",", '"', "'", "“”", "‘’"}
        ):
            raise ValueError("punctuation_symbol_requires_literal_marks")
        return
    if mode == "ordered_slots":
        slots = tuple(activity.get("concept_slots") or ())
        slot_ids = tuple(str(slot.get("id") or "") for slot in slots)
        ordered = tuple(
            str(item) for item in activity.get("ordered_concept_slot_ids") or ()
        )
        if (
            options
            or accepted
            or len(slot_ids) < 2
            or len(slot_ids) != len(set(slot_ids))
            or ordered != slot_ids
            or any(not tuple(slot.get("any_of") or ()) for slot in slots)
        ):
            raise ValueError("ordered_slots_require_all_slot_ids")


def _literal_result(
    *,
    mode: GradingMode,
    answer: str,
    met: bool,
) -> SchoolTypedGradingResult:
    evidence = answer.strip() or "(empty answer)"
    score = 1.0 if met else 0.0
    return SchoolTypedGradingResult(
        grading_mode=mode,
        correct=met,
        score=score,
        confidence=1.0,
        criteria=(
            SchoolTypedCriterion(
                id="authored_answer_match",
                met=met,
                quality=score,
                evidence_quote=evidence,
            ),
        ),
        missing_criteria=() if met else ("authored_answer_match",),
        blockers=(),
        evidence_quote=evidence,
    )


def grade_typed_school_answer(
    activity: Mapping[str, Any],
    answer: str,
) -> SchoolTypedGradingResult:
    """Grade an explicitly typed deterministic School activity."""

    mode = activity.get("grading_mode")
    if mode not in {
        "selected_option",
        "exact_text",
        "punctuation_symbol",
        "ordered_slots",
    }:
        raise ValueError("typed_deterministic_grading_mode_required")
    _validate_typed_runtime_authority(activity, mode)
    accepted_answers = tuple(
        str(item) for item in activity.get("accepted_answers") or ()
    )
    if mode == "punctuation_symbol":
        return _literal_result(
            mode=mode,
            answer=answer,
            met=answer.strip() in accepted_answers,
        )
    if mode in {"selected_option", "exact_text"}:
        normalized = _normalized_answer_text(answer)
        return _literal_result(
            mode=mode,
            answer=answer,
            met=normalized
            in {_normalized_answer_text(item) for item in accepted_answers},
        )
    return _grade_ordered_slots(activity, answer)


def _alias_matches(answer: str, alias: str) -> tuple[tuple[int, int], ...]:
    normalized_alias = _normalized_answer_text(alias)
    pattern = re.escape(normalized_alias).replace(r"\ ", r"\s+")
    left_boundary = r"(?<!\w)" if re.match(r"\w", normalized_alias[0]) else ""
    right_boundary = r"(?!\w)" if re.match(r"\w", normalized_alias[-1]) else ""
    return tuple(
        match.span()
        for match in re.finditer(
            rf"{left_boundary}{pattern}{right_boundary}",
            answer,
        )
    )


def _generic_relevance_term(term: str) -> bool:
    tokens = tuple(
        re.findall(r"[^\W\d_]+", _normalized_answer_text(term), flags=re.UNICODE)
    )
    return bool(tokens) and all(
        token in _GENERIC_RELEVANCE_TOKENS for token in tokens
    )


def _has_specific_source_overlap(
    answer: str,
    source_texts: tuple[str, ...],
) -> bool:
    answer_tokens = {
        token
        for token in re.findall(r"[^\W\d_]+", answer, flags=re.UNICODE)
        if len(token) >= 3
        and token not in _REPETITION_STOPWORDS
        and token not in _GENERIC_RELEVANCE_TOKENS
    }
    source_tokens = {
        token
        for source in source_texts
        for token in re.findall(
            r"[^\W\d_]+",
            _normalized_answer_text(source),
            flags=re.UNICODE,
        )
        if len(token) >= 3
        and token not in _REPETITION_STOPWORDS
        and token not in _GENERIC_RELEVANCE_TOKENS
    }
    return len(answer_tokens.intersection(source_tokens)) >= 2


def _grade_ordered_slots(
    activity: Mapping[str, Any],
    answer: str,
) -> SchoolTypedGradingResult:
    normalized = _normalized_answer_text(answer)
    slots = {
        str(slot["id"]): tuple(
            str(alias) for alias in slot.get("any_of") or ()
        )
        for slot in activity.get("concept_slots") or ()
    }
    ordered_ids = tuple(
        str(item) for item in activity.get("ordered_concept_slot_ids") or ()
    )
    if (
        not ordered_ids
        or len(ordered_ids) != len(slots)
        or set(ordered_ids) != set(slots)
    ):
        raise ValueError("ordered_slots_require_all_slot_ids")

    matches_by_slot: dict[str, tuple[tuple[int, int], ...]] = {}
    criteria: list[SchoolTypedCriterion] = []
    missing: list[str] = []
    for slot_id in ordered_ids:
        matches = tuple(
            span
            for alias in slots[slot_id]
            for span in _alias_matches(normalized, alias)
        )
        matches_by_slot[slot_id] = tuple(sorted(set(matches)))
        met = bool(matches)
        if not met:
            missing.append(slot_id)
        criteria.append(
            SchoolTypedCriterion(
                id=slot_id,
                met=met,
                quality=1.0 if met else 0.0,
                evidence_quote=(
                    normalized[matches[0][0] : matches[0][1]]
                    if matches
                    else answer.strip() or "(empty answer)"
                ),
            )
        )

    blockers: list[str] = []
    has_negation = bool(
        re.search(
            r"\b(?:no|not|never|without|cannot|can't|didn't|doesn't|isn't|wasn't)\b"
            r"|\b(?:did|does|is|was)\s+not\b",
            normalized,
        )
    )
    if has_negation:
        if re.search(r"\b(?:but|however|actually|yet)\b", normalized):
            blockers.append("contradictory_response")
        else:
            blockers.append("negated_slot_evidence")
    if any(len(matches) > 1 for matches in matches_by_slot.values()):
        blockers.append("ambiguous_repeated_slot_evidence")

    sequence_valid = not missing and all(
        matches_by_slot[left][0][1] <= matches_by_slot[right][0][0]
        for left, right in zip(ordered_ids, ordered_ids[1:])
    )
    if not sequence_valid and not missing:
        blockers.append("ordered_slot_sequence_invalid")
    criteria.append(
        SchoolTypedCriterion(
            id="ordered_slot_sequence",
            met=sequence_valid,
            quality=1.0 if sequence_valid else 0.0,
            evidence_quote=answer.strip() or "(empty answer)",
        )
    )
    if not sequence_valid:
        missing.append("ordered_slot_sequence")

    met_count = sum(criterion.met for criterion in criteria)
    score = met_count / len(criteria) if criteria else 0.0
    correct = not missing and not blockers
    return SchoolTypedGradingResult(
        grading_mode="ordered_slots",
        correct=correct,
        score=score if not blockers else min(score, 0.49),
        confidence=1.0,
        criteria=tuple(criteria),
        missing_criteria=tuple(dict.fromkeys(missing)),
        blockers=tuple(dict.fromkeys(blockers)),
        evidence_quote=answer.strip() or "(empty answer)",
    )


def validate_school_rubric_evaluation(
    payload: Mapping[str, Any] | SchoolRubricEvaluation,
    *,
    context: SchoolEvaluationContext,
) -> ValidatedSchoolRubricEvaluation:
    return _validate_evaluation_contract(
        payload,
        context=context,
        expected_schema_version=RUBRIC_SCHEMA_VERSION,
        schema_error="unsupported_school_rubric_schema",
    )


def _validate_evaluation_contract(
    payload: Mapping[str, Any] | SchoolRubricEvaluation,
    *,
    context: SchoolEvaluationContext,
    expected_schema_version: str,
    schema_error: str,
) -> ValidatedSchoolRubricEvaluation:
    if not isinstance(payload, SchoolRubricEvaluation):
        raw_schema_version = payload.get("schema_version")
        if raw_schema_version != expected_schema_version:
            raise ValueError(f"{schema_error}:{raw_schema_version}")
    evaluation = (
        payload
        if isinstance(payload, SchoolRubricEvaluation)
        else SchoolRubricEvaluation.model_validate(dict(payload))
    )
    if evaluation.schema_version != expected_schema_version:
        raise ValueError(f"{schema_error}:{evaluation.schema_version}")
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
        exact_quote_required = expected_schema_version == OPEN_RUBRIC_SCHEMA_VERSION
        quote_is_traceable = (
            criterion.evidence_quote.strip() in context.learner_answer
            if exact_quote_required
            else evidence_quote in learner_answer
        )
        if not quote_is_traceable:
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


def _school_open_backend_blockers(
    evaluation: SchoolRubricEvaluation,
    context: SchoolOpenEvaluationContext,
) -> tuple[str, ...]:
    blockers: list[str] = []
    answer = _normalized_answer_text(context.learner_answer)
    if context.relevance_terms:
        unique_terms = tuple(dict.fromkeys(context.relevance_terms))
        matched_terms = tuple(
            term for term in unique_terms if _alias_matches(answer, term)
        )
        has_specific_match = any(
            not _generic_relevance_term(term) for term in matched_terms
        )
        if not has_specific_match and not _has_specific_source_overlap(
            answer,
            context.source_texts,
        ):
            blockers.append("answer_not_relevant")

    if any(
        len(answer.split()) >= 5
        and SequenceMatcher(
            None,
            answer,
            _normalized_answer_text(exemplar),
        ).ratio()
        >= 0.88
        for exemplar in context.exemplar_texts
    ):
        blockers.append("copied_exemplar")

    if context.certifying_language == "en":
        devanagari_count = len(
            re.findall(r"[\u0900-\u097f]", context.learner_answer)
        )
        letter_count = len(re.findall(r"[^\W\d_]", context.learner_answer))
        mostly_devanagari = bool(
            letter_count and devanagari_count / letter_count >= 0.5
        )
        if evaluation.language_detected.casefold() != "en" or mostly_devanagari:
            blockers.append("language_mismatch")

    if any(_alias_matches(answer, phrase) for phrase in context.forbidden_phrases):
        blockers.append("authored_contradiction")
    if (
        context.semantic_validator_id is not None
        and _semantic_validator_blocks(
            context.semantic_validator_id,
            context.learner_answer,
        )
    ):
        blockers.append("authored_contradiction")

    answer_tokens = [
        token
        for token in re.findall(r"[^\W\d_]+", answer, flags=re.UNICODE)
        if len(token) >= 3 and token not in _REPETITION_STOPWORDS
    ]
    if len(answer_tokens) >= 6:
        token_counts = {
            token: answer_tokens.count(token) for token in set(answer_tokens)
        }
        unique_ratio = len(token_counts) / len(answer_tokens)
        if unique_ratio <= 0.5 and max(token_counts.values(), default=0) >= 3:
            blockers.append("repeated_keyword_gaming")

    slots = {slot.id: slot for slot in context.semantic_claim_slots}
    criteria_by_id = {
        criterion.id: criterion for criterion in evaluation.criteria
    }
    minimum_quality_by_id = {
        policy.id: policy.min_quality for policy in context.criterion_policies
    }
    first_positions: dict[str, int] = {}
    first_spans: dict[str, tuple[int, int]] = {}
    for slot_id, slot in slots.items():
        matches = [
            span
            for alias in slot.aliases
            for span in _alias_matches(answer, alias)
        ]
        if matches:
            first = min(matches, key=lambda span: span[0])
            first_positions[slot_id] = first[0]
            first_spans[slot_id] = first
            continue

        criterion = criteria_by_id.get(slot_id)
        if (
            criterion is None
            or not criterion.met
            or criterion.quality < minimum_quality_by_id.get(slot_id, 1.0)
            or not authored_evidence_can_prove_criterion(
                slot.description,
                criterion.evidence_quote,
            )
        ):
            continue
        evidence_matches = _alias_matches(
            answer,
            _normalized_answer_text(criterion.evidence_quote),
        )
        if evidence_matches:
            first = min(evidence_matches, key=lambda span: span[0])
            first_positions[slot_id] = first[0]
            first_spans[slot_id] = first
    if slots and set(first_positions) != set(slots):
        blockers.append("semantic_required_claim_missing")

    span_owners: dict[tuple[int, int], list[str]] = {}
    for slot_id, span in first_spans.items():
        span_owners.setdefault(span, []).append(slot_id)

    def shares_authored_component(owners: list[str]) -> bool:
        descriptions = []
        for owner in owners:
            description = re.sub(
                r"\s+required\s+part\s+\d+\s*\.?\s*$",
                "",
                slots[owner].description.strip(),
                flags=re.IGNORECASE,
            )
            normalized = _normalized_answer_text(description)
            if not normalized:
                return False
            descriptions.append(normalized)
        return len(set(descriptions)) == 1

    if any(
        len(owners) > 1 and not shares_authored_component(owners)
        for owners in span_owners.values()
    ):
        blockers.append("semantic_evidence_span_reused")

    ordered_ids = context.ordered_semantic_claim_slot_ids
    if ordered_ids and set(ordered_ids).issubset(first_positions):
        if any(
            first_positions[left] >= first_positions[right]
            for left, right in zip(ordered_ids, ordered_ids[1:])
        ):
            blockers.append("semantic_role_order_mismatch")
        if len(ordered_ids) >= 3 and all(
            slot_id in first_spans for slot_id in ordered_ids[:3]
        ):
            actor_id, action_id, receiver_id = ordered_ids[:3]
            actor_span = first_spans[actor_id]
            action_span = first_spans[action_id]
            receiver_span = first_spans[receiver_id]
            if actor_span[0] < action_span[0] < receiver_span[0]:
                after_action = answer[action_span[1] : receiver_span[0]]
                if re.search(r"\bby\b", after_action):
                    blockers.append("semantic_passive_role_reversal")
    return tuple(dict.fromkeys(blockers))


def validate_school_open_evaluation(
    payload: Mapping[str, Any] | SchoolRubricEvaluation,
    *,
    context: SchoolOpenEvaluationContext,
) -> ValidatedSchoolRubricEvaluation:
    """Validate the exact `school.open.v1` Qwen result against authored context."""

    validated = _validate_evaluation_contract(
        payload,
        context=context,
        expected_schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
        schema_error="unsupported_school_open_schema",
    )
    return ValidatedSchoolRubricEvaluation(
        evaluation=validated.evaluation,
        context=context,
        backend_blockers=_school_open_backend_blockers(
            validated.evaluation,
            context,
        ),
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
    "GradingMode",
    "HumanReviewPolicy",
    "OPEN_RUBRIC_SCHEMA_VERSION",
    "RUBRIC_SCHEMA_VERSION",
    "SchoolCriterionPolicy",
    "SchoolEvaluationContext",
    "SchoolOpenAnswerRetryableError",
    "SchoolOpenEvaluationContext",
    "SchoolSemanticClaimSlot",
    "SchoolTypedCriterion",
    "SchoolTypedGradingResult",
    "ValidatedSchoolRubricEvaluation",
    "criterion_scores",
    "grade_typed_school_answer",
    "parse_school_rubric_json",
    "parse_school_v3_rubric_json",
    "school_open_context_from_activity",
    "validate_school_open_evaluation",
    "validate_school_rubric_evaluation",
]
