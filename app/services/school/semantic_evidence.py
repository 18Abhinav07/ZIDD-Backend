"""Backend-owned checks for semantic rubric criteria models commonly misread."""

from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
import re
from typing import Mapping

from app.content.school.content_schema import SchoolRubricCriterion


_EVIDENCE_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "to",
        "was",
        "were",
        "with",
    }
)

_NAMED_RELATION_WORDS = frozenset(
    {
        "after",
        "although",
        "because",
        "before",
        "but",
        "however",
        "so",
        "then",
        "when",
        "while",
        "yet",
    }
)


def authored_evidence_can_prove_criterion(
    description: str,
    evidence: str,
) -> bool:
    """Reject one-fragment evidence for criteria that explicitly require a set."""

    description_words = re.findall(r"[a-z0-9]+", description.casefold())
    description_text = " ".join(description_words)
    named_relations = _NAMED_RELATION_WORDS.intersection(description_words)
    composite = bool(
        re.search(
            r"\b(?:all|every|both|two|three|sequence|sequences|ordered|order)\b",
            description_text,
        )
        or len(named_relations) >= 2
    )
    if not composite:
        return True

    evidence_words = re.findall(r"[a-z0-9]+", evidence.casefold())
    content_words = [
        word for word in evidence_words if word not in _EVIDENCE_STOP_WORDS
    ]
    if named_relations:
        return named_relations.issubset(evidence_words) and len(content_words) >= 4

    ordered_claim = bool(
        {"order", "ordered", "sequence", "sequences"}.intersection(
            description_words
        )
    )
    if ordered_claim:
        return len(content_words) >= 3

    explicit_join = bool(
        {"and", *_NAMED_RELATION_WORDS}.intersection(evidence_words)
        or ("from" in evidence_words and "to" in evidence_words)
        or re.search(r"[.!?;:]\s+[^\W\d_]", evidence, flags=re.UNICODE)
    )
    return explicit_join and len(content_words) >= 4


def correct_semantic_criterion(
    criterion: SchoolRubricCriterion,
    *,
    passage: str,
    answer: str,
    criterion_by_id: Mapping[str, SchoolRubricCriterion],
) -> SchoolRubricCriterion:
    """Correct only criteria the backend can prove from learner-visible text."""

    if criterion.id == "clue_supports_inference":
        inference = criterion_by_id.get("plausible_inference")
        clue = criterion_by_id.get("relevant_text_clue")
        linked = bool(
            inference
            and clue
            and inference.met
            and clue.met
            and _has_explicit_reason_link(
                answer,
                passage=passage,
                inference_quote=inference.evidence_quote,
                clue_quote=clue.evidence_quote,
            )
        )
        return criterion.model_copy(
            update={
                "met": linked,
                "quality": 1.0 if linked else 0.0,
                "evidence_quote": answer.strip() or "(empty answer)",
            }
        )

    if criterion.id != "own_words":
        return criterion
    if len(_tokens(answer)) < 4 or len(_tokens(passage)) < 4:
        return criterion

    copied = copies_source_passage(passage=passage, answer=answer)
    return criterion.model_copy(
        update={
            "met": not copied,
            "quality": 0.1 if copied else 1.0,
            "evidence_quote": answer.strip(),
        }
    )


def copies_source_passage(*, passage: str, answer: str) -> bool:
    answer_tokens = _tokens(answer)
    passage_tokens = _tokens(passage)
    if len(answer_tokens) < 4 or len(passage_tokens) < 4:
        return False
    matcher = SequenceMatcher(
        None,
        passage_tokens,
        answer_tokens,
        autojunk=False,
    )
    longest_run = matcher.find_longest_match().size
    substantial_runs = [
        block.size
        for block in matcher.get_matching_blocks()
        if block.size >= 4
    ]
    substantial_source_coverage = sum(substantial_runs) / len(passage_tokens)
    copied_fraction = longest_run / len(answer_tokens)
    reused_source_tokens = sum(
        (Counter(passage_tokens) & Counter(answer_tokens)).values()
    )
    source_token_reuse = reused_source_tokens / len(passage_tokens)
    ordered_source_reuse = _ordered_source_token_coverage(
        passage_tokens,
        answer_tokens,
    )
    return (
        longest_run >= 8
        or substantial_source_coverage >= 0.6
        or (longest_run >= 5 and copied_fraction >= 0.7)
        or source_token_reuse >= 0.85
        or (source_token_reuse >= 0.7 and ordered_source_reuse >= 0.85)
        or matcher.ratio() >= 0.86
    )


def inference_clue_is_explicitly_linked(
    *,
    passage: str,
    answer: str,
    inference_quote: str,
    clue_quote: str,
) -> bool:
    """Prove that learner-authored inference and clue spans are connected."""

    return _has_explicit_reason_link(
        answer,
        passage=passage,
        inference_quote=inference_quote,
        clue_quote=clue_quote,
    )


def _has_explicit_reason_link(
    answer: str,
    *,
    passage: str,
    inference_quote: str,
    clue_quote: str,
) -> bool:
    normalized = str(answer).casefold()
    inference_span = _evidence_span(normalized, inference_quote)
    clue_span = _evidence_span(normalized, clue_quote)
    if inference_span is None or clue_span is None:
        return False

    combined_start = min(inference_span[0], clue_span[0])
    combined_end = max(inference_span[1], clue_span[1])
    sentence_start, sentence_end = _containing_sentence_span(
        normalized,
        combined_start,
        combined_end,
    )
    combined_sentence = normalized[sentence_start:sentence_end]
    clue_text = normalized[clue_span[0] : clue_span[1]]
    if not _shares_passage_clue(passage, clue_text, minimum=2):
        return False
    if re.search(
        r"\b(?:not\s+(?:because|due\s+to)|"
        r"does\s+not\s+(?:support|show|suggest|indicate)|"
        r"doesn't\s+(?:support|show|suggest|indicate)|unrelated\s+to)\b",
        combined_sentence,
    ):
        return False

    for match in re.finditer(
        r"\b(?:because(?:\s+of)?|since|due\s+to)\b",
        normalized,
    ):
        if (
            inference_span[1] <= match.start()
            and clue_span[0] >= match.end()
            and _has_only_clue_lead_words(
                normalized,
                match.end(),
                clue_span[0],
            )
            and _same_sentence(normalized, inference_span[0], clue_span[1])
        ):
            return True
        if (
            match.end() <= clue_span[0]
            and clue_span[1] <= inference_span[0]
            and _has_only_clue_lead_words(
                normalized,
                match.end(),
                clue_span[0],
            )
            and _same_sentence(normalized, match.start(), inference_span[1])
        ):
            return True
    for match in re.finditer(
        r"\b(?:therefore|thus|so|"
        r"(?:this|which)\s+(?:shows|suggests|indicates)(?:\s+that)?|"
        r"(?:show|shows|showed|suggest|suggests|suggested|indicate|indicates|"
        r"indicated|showing|suggesting|indicating|mean|means|meant|meaning)"
        r"(?:\s+that)?)\b",
        normalized,
    ):
        if (
            clue_span[1] <= match.start()
            and inference_span[0] >= match.end()
            and _has_no_intervening_words(
                normalized,
                match.end(),
                inference_span[0],
            )
            and _same_sentence(normalized, clue_span[0], inference_span[1])
        ):
            return True
    if _has_infer_from_link(
        normalized,
        inference_span=inference_span,
        clue_span=clue_span,
        sentence_start=sentence_start,
        sentence_end=sentence_end,
    ):
        return True
    if _has_evidence_that_link(
        normalized,
        inference_span=inference_span,
        clue_span=clue_span,
    ):
        return True
    return _has_grounded_reason_inside_coarse_clue(
        normalized,
        passage=passage,
        inference_span=inference_span,
        clue_span=clue_span,
    )


def _has_infer_from_link(
    answer: str,
    *,
    inference_span: tuple[int, int],
    clue_span: tuple[int, int],
    sentence_start: int,
    sentence_end: int,
) -> bool:
    if not (
        sentence_start <= inference_span[0]
        and inference_span[1] <= clue_span[0]
        and clue_span[1] <= sentence_end
    ):
        return False
    lead = answer[sentence_start : inference_span[0]]
    bridge = answer[inference_span[1] : clue_span[0]]
    return bool(
        re.search(
            r"\b(?:i|we)\s+(?:can\s+)?infer(?:red)?\s+that\s*$",
            lead,
        )
        and re.fullmatch(r"\s+from\s+", bridge)
    )


def _has_evidence_that_link(
    answer: str,
    *,
    inference_span: tuple[int, int],
    clue_span: tuple[int, int],
) -> bool:
    if clue_span[1] > inference_span[0]:
        return False
    bridge = answer[clue_span[1] : inference_span[0]]
    return bool(
        re.fullmatch(
            r"\s+(?:is|are|was|were)\s+(?:clear\s+)?evidence\s+that\s+",
            bridge,
        )
        and _same_sentence(answer, clue_span[0], inference_span[1])
    )


def _containing_sentence_span(
    answer: str,
    start: int,
    end: int,
) -> tuple[int, int]:
    sentence_start = max(
        answer.rfind(".", 0, start),
        answer.rfind("!", 0, start),
        answer.rfind("?", 0, start),
    ) + 1
    sentence_ends = [
        boundary
        for marker in ".!?"
        if (boundary := answer.find(marker, end)) >= 0
    ]
    sentence_end = min(sentence_ends) + 1 if sentence_ends else len(answer)
    return sentence_start, sentence_end


def _has_grounded_reason_inside_coarse_clue(
    answer: str,
    *,
    passage: str,
    inference_span: tuple[int, int],
    clue_span: tuple[int, int],
) -> bool:
    if (
        clue_span == inference_span
        or clue_span[0] > inference_span[0]
        or inference_span[1] > clue_span[1]
        or not _same_sentence(answer, clue_span[0], clue_span[1])
    ):
        return False

    for match in re.finditer(
        r"\b(?:because(?:\s+of)?|since|due\s+to)\b",
        answer,
    ):
        if not (
            clue_span[0] <= match.start()
            and match.end() <= clue_span[1]
        ):
            continue
        claim = answer[clue_span[0] : match.start()]
        reason = answer[match.end() : clue_span[1]]
        immediate_reason = re.split(r"[,;]", reason, maxsplit=1)[0]
        if len(_tokens(claim)) < 2 or len(_tokens(reason)) < 2:
            continue
        if re.search(
            r"(?:^|[,;])\s*(?:but|however|although|though|while|whereas|yet)\b",
            reason,
        ):
            continue
        if re.match(
            r"\s*(?:i|we)\s+(?:guess(?:ed)?|think|thought|believe|believed|"
            r"feel|felt)\b",
            reason,
        ):
            continue
        if _shares_passage_clue(
            passage,
            immediate_reason,
            minimum=1,
        ) and _shares_passage_clue(passage, reason, minimum=2):
            return True
    return False


def _shares_passage_clue(
    passage: str,
    reason: str,
    *,
    minimum: int,
) -> bool:
    ignored = {
        "and",
        "are",
        "been",
        "because",
        "but",
        "for",
        "from",
        "had",
        "has",
        "have",
        "her",
        "his",
        "into",
        "not",
        "she",
        "that",
        "the",
        "their",
        "them",
        "they",
        "this",
        "was",
        "were",
        "with",
    }
    passage_tokens = {
        _clue_token(token)
        for token in _tokens(passage)
        if len(token) >= 3 and token not in ignored
    }
    reason_tokens = {
        _clue_token(token)
        for token in _tokens(reason)
        if len(token) >= 3 and token not in ignored
    }
    return len(passage_tokens & reason_tokens) >= minimum


def _clue_token(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    return token


def _has_no_intervening_words(value: str, start: int, end: int) -> bool:
    return re.search(r"\w", value[start:end], flags=re.UNICODE) is None


def _has_only_clue_lead_words(value: str, start: int, end: int) -> bool:
    """Allow a determiner omitted from a provider's exact clue quote."""

    words = re.findall(
        r"[^\W\d_]+",
        value[start:end].casefold(),
        flags=re.UNICODE,
    )
    return len(words) <= 2 and all(
        word
        in {
            "a",
            "an",
            "her",
            "his",
            "its",
            "my",
            "our",
            "the",
            "their",
            "these",
            "this",
            "those",
            "your",
        }
        for word in words
    )


def _same_sentence(value: str, start: int, end: int) -> bool:
    return re.search(r"[.!?]", value[start:end]) is None


def _ordered_source_token_coverage(
    passage_tokens: list[str],
    answer_tokens: list[str],
) -> float:
    """Return the fraction of source tokens reused in their original order."""

    previous = [0] * (len(answer_tokens) + 1)
    for passage_token in passage_tokens:
        current = [0]
        for answer_index, answer_token in enumerate(answer_tokens, start=1):
            if passage_token == answer_token:
                current.append(previous[answer_index - 1] + 1)
            else:
                current.append(max(current[-1], previous[answer_index]))
        previous = current
    return previous[-1] / len(passage_tokens)


def _evidence_span(answer: str, quote: str) -> tuple[int, int] | None:
    normalized_quote = str(quote).strip().casefold()
    if not normalized_quote or normalized_quote == "(empty answer)":
        return None
    span_quote = normalized_quote.rstrip(".!?")
    if not span_quote:
        return None
    start = answer.find(span_quote)
    if start < 0:
        return None
    return start, start + len(span_quote)


def _tokens(value: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", str(value).casefold(), flags=re.UNICODE)
