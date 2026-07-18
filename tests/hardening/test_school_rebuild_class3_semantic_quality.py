from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHAPTER_ROOT = (
    ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_3"
)
CHAPTER_PATHS = tuple(sorted(CHAPTER_ROOT.glob("eng_c3_ch*.json")))

GENERIC_OPEN_INSTRUCTION = (
    "Read the card. Write a clear answer in full sentences. Use the card clues "
    "and include every part the question asks for."
)
PASSAGE_COPY_PREFIX = "Use this part of the card:"
BROKEN_COPY = (
    "an clue-based inference",
    "an careful check",
    "asks a shelf for",
    "explain the focus colour expression",
    "form the focus spelling or compound",
    "use the focus chapter word",
    "use the focus chapter trait",
    "and explains its effect",
    "and cites the relevant step",
    "cites a visible behaviour",
    "and explains its rhythmic or meaning effect",
)
IMPLAUSIBLE_OPTIONS = {
    "a bent link is always stronger.",
    "the chain is singing a game song.",
    "the coin disappears before touching water.",
    "the line says the cone is a house.",
    "the poem warns readers never to use colour.",
    "the runners never move.",
    "the shelf orders her to plant a tree.",
    "the swing needs faster use.",
    "the test has no result because the cork is small.",
    "traffic makes the ball softer.",
}
MALFORMED_OPTIONS = {
    "although why",
    "and because why",
    "and then because",
    "and with no contrast",
    "and without contrast",
    "and without reason",
    "because it is small therefore",
    "because without cause",
    "because without reason",
    "unless so",
    "unless why",
    "or else and",
    "or why",
    "so that reason",
    "so that why",
    "so why",
    "is fly",
    "is graze",
    "are roar",
    "are run",
    "are swing",
}
REUSED_ASSESSMENT_IDS = {
    "eng_c3_ch01:assessment:01",
    "eng_c3_ch02:assessment:11",
    "eng_c3_ch03:assessment:18",
    "eng_c3_ch04:assessment:07",
    "eng_c3_ch04:assessment:17",
    "eng_c3_ch04:assessment:18",
    "eng_c3_ch04:assessment:22",
    "eng_c3_ch04:assessment:23",
    "eng_c3_ch04:assessment:28",
    "eng_c3_ch05:assessment:07",
    "eng_c3_ch05:assessment:10",
    "eng_c3_ch05:assessment:11",
    "eng_c3_ch05:assessment:12",
    "eng_c3_ch05:assessment:13",
    "eng_c3_ch05:assessment:20",
    "eng_c3_ch06:assessment:03",
    "eng_c3_ch06:assessment:05",
    "eng_c3_ch06:assessment:18",
    "eng_c3_ch06:assessment:20",
    "eng_c3_ch07:assessment:07",
    "eng_c3_ch10:assessment:17",
}

_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "after",
    "answer",
    "because",
    "before",
    "card",
    "choose",
    "complete",
    "does",
    "every",
    "explain",
    "facts",
    "from",
    "given",
    "into",
    "only",
    "passage",
    "scene",
    "sentence",
    "state",
    "that",
    "their",
    "then",
    "these",
    "they",
    "this",
    "those",
    "which",
    "while",
    "with",
    "words",
    "write",
}


def _payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _content_words(value: str) -> set[str]:
    return {
        word
        for word in _WORD_PATTERN.findall(value.casefold())
        if len(word) > 2 and word not in _STOP_WORDS
    }


def _normalise(value: str) -> str:
    return " ".join(sorted(_content_words(value)))


def _semantic_jaccard(left: str, right: str) -> float:
    left_words = _content_words(left)
    right_words = _content_words(right)
    union = left_words | right_words
    return len(left_words & right_words) / len(union) if union else 1.0


@pytest.mark.parametrize("path", CHAPTER_PATHS, ids=lambda path: path.stem)
def test_class3_learner_copy_is_specific_and_grammatical(path: Path) -> None:
    payload = _payload(path)
    visible_strings: list[str] = []
    for obj in _objects({"levels": payload["levels"]}):
        for field in ("teaching_block", "passage", "prompt"):
            value = obj.get(field)
            if isinstance(value, str):
                visible_strings.append(value)
        prompt = obj.get("prompt")
        if isinstance(prompt, str):
            assert PASSAGE_COPY_PREFIX not in prompt

    learner_text = " ".join(visible_strings).casefold()
    assert GENERIC_OPEN_INSTRUCTION.casefold() not in learner_text
    assert all(fragment not in learner_text for fragment in BROKEN_COPY)


@pytest.mark.parametrize("path", CHAPTER_PATHS, ids=lambda path: path.stem)
def test_class3_choice_distractors_are_credible_language(path: Path) -> None:
    payload = _payload(path)
    for obj in _objects(payload):
        for option in obj.get("options") or ():
            lowered = option.casefold()
            assert lowered not in IMPLAUSIBLE_OPTIONS
            assert lowered not in MALFORMED_OPTIONS


def test_reused_assessment_scenarios_are_reauthored() -> None:
    found_ids: set[str] = set()

    for path in CHAPTER_PATHS:
        payload = _payload(path)
        learning_passages = {
            obj["passage"]
            for obj in _objects(payload["levels"])
            if isinstance(obj.get("passage"), str)
        }
        for item in payload["chapter_assessment"]["items"]:
            if item["item_id"] not in REUSED_ASSESSMENT_IDS:
                continue
            found_ids.add(item["item_id"])
            item_words = _content_words(item["passage"])
            item_normalised = _normalise(item["passage"])
            for teaching_passage in learning_passages:
                teaching_words = _content_words(teaching_passage)
                if not item_words or not teaching_words:
                    continue
                jaccard = len(item_words & teaching_words) / len(
                    item_words | teaching_words
                )
                sequence = SequenceMatcher(
                    None,
                    item_normalised,
                    _normalise(teaching_passage),
                ).ratio()
                assert jaccard < 0.60
                assert sequence < 0.75

    assert found_ids == REUSED_ASSESSMENT_IDS


@pytest.mark.parametrize("path", CHAPTER_PATHS, ids=lambda path: path.stem)
def test_transfer_and_review_variants_are_distinct_scenarios(path: Path) -> None:
    payload = _payload(path)

    for level in payload["levels"]:
        by_phase = {step["phase"]: step for step in level["teaching_steps"]}
        variants = [
            *by_phase["transfer"]["variant_pool"],
            *by_phase["review"]["variant_pool"],
        ]

        assert len(by_phase["transfer"]["variant_pool"]) >= 4
        assert len(by_phase["review"]["variant_pool"]) >= 4
        assert len({_normalise(item["passage"]) for item in variants}) == len(variants)

        for index, left in enumerate(variants):
            left_passage = left["passage"]
            assert len(_content_words(left_passage)) >= 5
            for right in variants[index + 1 :]:
                right_passage = right["passage"]
                assert _semantic_jaccard(left_passage, right_passage) < 0.60, (
                    path.stem,
                    level["level_id"],
                    left["variant_id"],
                    right["variant_id"],
                )
                assert SequenceMatcher(
                    None,
                    left_passage.casefold(),
                    right_passage.casefold(),
                    autojunk=False,
                ).ratio() < 0.78, (
                    path.stem,
                    level["level_id"],
                    left["variant_id"],
                    right["variant_id"],
                )
