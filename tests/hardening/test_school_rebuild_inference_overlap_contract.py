from __future__ import annotations

import pytest

from app.content.school.content_schema import SchoolRubricCriterion
from app.services.school.semantic_evidence import correct_semantic_criterion


RAIN_PASSAGE = (
    "The sky was clear when Ira left. She returned with wet shoes and a closed "
    "umbrella dripping by the door."
)


def _criterion(
    criterion_id: str,
    *,
    met: bool,
    evidence_quote: str,
) -> SchoolRubricCriterion:
    return SchoolRubricCriterion(
        id=criterion_id,
        met=met,
        quality=1.0 if met else 0.0,
        evidence_quote=evidence_quote,
    )


def _correct_linkage(
    *,
    passage: str,
    answer: str,
    inference_quote: str,
    clue_quote: str | None = None,
) -> SchoolRubricCriterion:
    inference = _criterion(
        "plausible_inference",
        met=True,
        evidence_quote=inference_quote,
    )
    clue = _criterion(
        "relevant_text_clue",
        met=True,
        evidence_quote=clue_quote or answer,
    )
    linkage = _criterion(
        "clue_supports_inference",
        met=False,
        evidence_quote="(empty answer)",
    )
    return correct_semantic_criterion(
        linkage,
        passage=passage,
        answer=answer,
        criterion_by_id={
            inference.id: inference,
            clue.id: clue,
            linkage.id: linkage,
        },
    )


@pytest.mark.parametrize(
    ("passage", "answer", "inference_quote"),
    (
        (
            RAIN_PASSAGE,
            "It probably rained while Ira was outside because her wet shoes "
            "and dripping umbrella show that she was caught in rain.",
            "It probably rained while Ira was outside",
        ),
        (
            "The balcony plants drooped, the soil was dry, and the watering "
            "can had been empty for days.",
            "The plants probably drooped because they had not been watered; "
            "the soil was dry and the watering can had been empty for days.",
            "they had not been watered",
        ),
    ),
)
def test_backend_accepts_explicit_cause_when_clue_quote_covers_the_answer(
    passage: str,
    answer: str,
    inference_quote: str,
) -> None:
    corrected = _correct_linkage(
        passage=passage,
        answer=answer,
        inference_quote=inference_quote,
    )

    assert corrected.met is True
    assert corrected.quality == 1.0


@pytest.mark.parametrize(
    ("answer", "inference_quote", "clue_quote"),
    (
        (
            "I infer that it rained from her wet shoes.",
            "it rained",
            "her wet shoes",
        ),
        (
            "Her wet shoes are evidence that it rained.",
            "it rained",
            "Her wet shoes",
        ),
    ),
)
def test_backend_accepts_explicit_evidence_to_inference_formulations(
    answer: str,
    inference_quote: str,
    clue_quote: str,
) -> None:
    corrected = _correct_linkage(
        passage=RAIN_PASSAGE,
        answer=answer,
        inference_quote=inference_quote,
        clue_quote=clue_quote,
    )

    assert corrected.met is True
    assert corrected.quality == 1.0


def test_backend_rejects_later_denial_outside_the_clue_quote() -> None:
    answer = (
        "It probably rained because her shoes were wet, but that clue is "
        "unrelated to rain."
    )

    corrected = _correct_linkage(
        passage=RAIN_PASSAGE,
        answer=answer,
        inference_quote="It probably rained",
        clue_quote="her shoes were wet",
    )

    assert corrected.met is False
    assert corrected.quality == 0.0


def test_backend_rejects_provider_positive_clue_absent_from_passage() -> None:
    answer = "It probably rained because the streetlights were on."

    corrected = _correct_linkage(
        passage=RAIN_PASSAGE,
        answer=answer,
        inference_quote="It probably rained",
        clue_quote="the streetlights were on",
    )

    assert corrected.met is False
    assert corrected.quality == 0.0


@pytest.mark.parametrize(
    "answer",
    (
        "It probably rained while Ira was outside, but not because her wet "
        "shoes and dripping umbrella were clues.",
        "It probably rained while Ira was outside because I guessed, while "
        "her shoes were wet and her umbrella was dripping.",
        "It probably rained while Ira was outside because I was curious; her "
        "shoes were wet and her umbrella was dripping.",
        "It probably rained while Ira was outside. I stayed home because I "
        "was tired. Her shoes were wet and her umbrella was dripping.",
    ),
)
def test_backend_rejects_unsafe_connectors_when_clue_quote_covers_the_answer(
    answer: str,
) -> None:
    corrected = _correct_linkage(
        passage=RAIN_PASSAGE,
        answer=answer,
        inference_quote="It probably rained while Ira was outside",
    )

    assert corrected.met is False
    assert corrected.quality == 0.0
