"""Fail-hard validation for the authored School Prep placement bank."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any
import unicodedata

from app.content.school.standards import locked_english_skill_ids


class PlacementBankValidationError(ValueError):
    """Raised when placement content cannot satisfy the diagnostic contract."""


_OPAQUE_ITEM_ID = re.compile(
    r"^(?:spv_c0[2-5]_t0[1-8]_v0[1-5]|spv_c05_t03_v06)$"
)
_REVIEW_MANIFEST_REFERENCE = "app/content/school_rebuild_placement_review_manifest.json"
_REVIEW_MANIFEST_PATH = Path(__file__).with_name(
    "school_rebuild_placement_review_manifest.json"
)
_REVIEW_MANIFEST = MappingProxyType(
    json.loads(_REVIEW_MANIFEST_PATH.read_text(encoding="utf-8"))
)
_SUPPORTED_ITEM_TYPES = frozenset({"short_answer", "multiple_choice", "fill_blank"})
_PUBLIC_SCORING_LEAK_MARKERS = (
    "accepted answer",
    "answer key",
    "correct answer",
    "correct option",
    "model answer",
    "rubric ref",
    "rubric:",
    "scoring criteria",
    "criterion:",
    "the answer is",
    "answer is",
    "sahi answer",
    "sahi uttar",
    "सही उत्तर",
    "उत्तर है",
    "जवाब है",
)

_FOUNDATION_SENTENCE_CRITERIA = (
    "complete_idea",
    "relevant_to_prompt",
    "understandable_word_order",
    "english_response",
)
_CLASS_2_SENTENCE_CRITERIA = (
    "complete_idea",
    "subject_and_action_or_description",
    "relevant_to_prompt",
    "understandable_word_order",
    "english_response",
)
_CLASS_3_SENTENCE_CRITERIA = (
    "complete_idea",
    "subject_and_predicate",
    "subject_verb_agreement",
    "relevant_detail",
    "basic_capitalization_and_terminal_punctuation",
    "english_response",
)

COMPLETE_SENTENCE_RUBRICS_BY_SOURCE_BAND: Mapping[
    int,
    Mapping[str, str | tuple[str, ...]],
] = MappingProxyType({
    1: MappingProxyType({
        "rubric_ref": "school.strict.complete_sentence.foundation.v1",
        "criteria": _FOUNDATION_SENTENCE_CRITERIA,
    }),
    2: MappingProxyType({
        "rubric_ref": "school.strict.complete_sentence.class2.v1",
        "criteria": _CLASS_2_SENTENCE_CRITERIA,
    }),
    3: MappingProxyType({
        "rubric_ref": "school.strict.complete_sentence.class3.v1",
        "criteria": _CLASS_3_SENTENCE_CRITERIA,
    }),
})

STRICT_RUBRIC_CRITERIA_BY_REF: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "school.strict.complete_sentence.foundation.v1": _FOUNDATION_SENTENCE_CRITERIA,
    "school.strict.complete_sentence.class2.v1": _CLASS_2_SENTENCE_CRITERIA,
    "school.strict.complete_sentence.class3.v1": _CLASS_3_SENTENCE_CRITERIA,
    "school.strict.reason_from_text.v1": (
        "answers_question",
        "text_based_reason",
        "relevant_text_detail",
        "clear_complete_response",
        "english_response",
    ),
    "school.strict.short_answer.v1": (
        "answers_question",
        "relevant_detail",
        "complete_response",
        "english_response",
    ),
    "school.strict.summary.v1": (
        "main_idea_or_event",
        "essential_details",
        "own_words",
        "concise_complete_response",
        "english_response",
    ),
    "school.strict.reason_answer.v1": (
        "clear_answer_or_action",
        "relevant_reason",
        "reason_supports_answer",
        "complete_response",
        "english_response",
    ),
    "school.strict.inference.v1": (
        "plausible_inference",
        "relevant_text_clue",
        "clue_supports_inference",
        "complete_response",
        "english_response",
    ),
})

RUBRIC_REMEDIATION_BY_CRITERION: Mapping[str, str] = MappingProxyType({
    "complete_idea": "Write one whole idea rather than a word or fragment.",
    "relevant_to_prompt": "Keep the sentence focused on the requested subject.",
    "understandable_word_order": "Put the English words in an order that is easy to understand.",
    "english_response": "Write the certifying response in English.",
    "subject_and_action_or_description": "Name the subject and add an action or description.",
    "subject_and_predicate": "Include both who or what the sentence is about and what is said about it.",
    "subject_verb_agreement": "Make the subject and verb agree.",
    "relevant_detail": "Add a detail that directly answers the question.",
    "basic_capitalization_and_terminal_punctuation": "Begin with a capital and finish with suitable punctuation.",
    "answers_question": "Answer the question directly.",
    "text_based_reason": "Use a reason supported by the text.",
    "relevant_text_detail": "Include the text detail that supports the reason.",
    "clear_complete_response": "State the response clearly and completely.",
    "complete_response": "Finish the response so the meaning is complete.",
    "main_idea_or_event": "State the passage's main idea or event.",
    "essential_details": "Keep the details needed to understand the summary.",
    "own_words": "Retell the idea in your own words.",
    "concise_complete_response": "Keep the summary brief while preserving the whole meaning.",
    "clear_answer_or_action": "State the answer or proposed action clearly.",
    "relevant_reason": "Give a reason that fits the situation.",
    "reason_supports_answer": "Make the reason support the answer you chose.",
    "plausible_inference": "Make an inference that is possible from the passage.",
    "relevant_text_clue": "Name a text clue connected to the inference.",
    "clue_supports_inference": "Explain how the clue supports the inference.",
})


def normalize_placement_answer(value: str) -> str:
    """Normalize learner answers while preserving meaningful internal punctuation."""

    normalized = " ".join(
        unicodedata.normalize("NFKC", str(value)).casefold().strip().split()
    )
    while normalized and unicodedata.category(normalized[-1]).startswith("P"):
        normalized = normalized[:-1].rstrip()
    return normalized


def _normalized_identifier_part(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _normalize_public_surface(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlacementBankValidationError(message)


def _validate_approval(approval: Any, owner: str) -> None:
    _require(
        getattr(approval, "engineering_qa_status", None)
        == _REVIEW_MANIFEST["engineering_qa_status"]
        and _REVIEW_MANIFEST["engineering_qa_status"] in {"in_progress", "passed"},
        f"{owner} has an inaccurate engineering-QA status",
    )
    _require(
        getattr(approval, "content_review_status", None)
        == _REVIEW_MANIFEST["content_review_status"]
        == "agent_reviewed",
        f"{owner} has an inaccurate content-review status",
    )
    _require(
        getattr(approval, "launch_status", None)
        == _REVIEW_MANIFEST["launch_status"]
        == "qa_only",
        f"{owner} has an inaccurate launch status",
    )
    _require(bool(getattr(approval, "reviewed_by", "").strip()), f"{owner} has no QA reviewer")
    _require(
        getattr(approval, "reviewed_on", None) == _REVIEW_MANIFEST["reviewed_on"],
        f"{owner} has a review-date mismatch",
    )
    _require(
        getattr(approval, "version", None) == _REVIEW_MANIFEST["content_version"],
        f"{owner} has an approval-version mismatch",
    )
    _require(
        getattr(approval, "reference", None) == _REVIEW_MANIFEST_REFERENCE,
        f"{owner} does not reference the backend-local review manifest",
    )


def _contains_public_scoring_leak(value: str, item: Any) -> bool:
    folded = unicodedata.normalize("NFKC", str(value)).casefold()
    if any(marker in folded for marker in _PUBLIC_SCORING_LEAK_MARKERS):
        return True
    if item.rubric_ref and item.rubric_ref.casefold() in folded:
        return True
    if item.rubric_ref:
        for criterion_id in STRICT_RUBRIC_CRITERIA_BY_REF.get(item.rubric_ref, ()):
            if criterion_id.casefold() in folded:
                return True
    return False


def _validate_item(
    item: Any,
    track: Any,
    item_ids: set[str],
    prompt_keys: set[tuple[str, str]],
    track_prompt_surfaces: set[str],
    track_passage_surfaces: set[str],
) -> None:
    owner = f"item {item.item_id!r}"
    _require(bool(item.item_id.strip()), "placement item ID is empty")
    _require(bool(_OPAQUE_ITEM_ID.fullmatch(item.item_id)), f"{owner} does not use an opaque stable ID")
    _require(item.item_id not in item_ids, f"duplicate placement item ID: {item.item_id}")
    item_ids.add(item.item_id)

    _require(item.subject_id == "english", f"{owner} has unsupported subject")
    _require(item.target_class_no == track.target_class_no, f"{owner} has wrong target class")
    _require(item.track_id == track.track_id, f"{owner} has wrong track ID")
    _require(item.primary_skill_id == track.primary_skill_id, f"{owner} has wrong primary skill")
    _require(item.primary_skill_id not in item.telemetry_skill_ids, f"{owner} repeats its primary skill as telemetry")
    _require(bool(item.learner_skill_label.strip()), f"{owner} has no learner-safe label")
    _require(item.item_type in _SUPPORTED_ITEM_TYPES, f"{owner} has unsupported item type")
    _require(item.source_class_no in {max(1, track.target_class_no - 1), track.target_class_no}, f"{owner} has unreachable source band")
    _require(bool(item.prompt.strip()), f"{owner} has no prompt")
    if item.evaluation_mode == "strict_rubric":
        _require(not item.options, f"{owner} strict-rubric items must not expose answer options")

    public_text_fields = [
        ("learner_skill_label", item.learner_skill_label),
        ("prompt", item.prompt),
        ("passage", item.passage),
        *(("option", option) for option in item.options),
    ]
    public_text_fields.extend(
        (field_name, text)
        for learner_copy in item.localized_copy.values()
        for field_name, text in (
            ("localized_instruction", learner_copy.instruction),
            ("localized_support", learner_copy.support),
        )
    )
    normalized_hidden_answers = {
        normalize_placement_answer(value)
        for value in (item.answer_key, *item.accepted_answers)
        if value
    }
    public_scoring_leak = any(
        _contains_public_scoring_leak(text, item)
        or (
            field_name != "option"
            and bool(normalized_hidden_answers)
            and normalize_placement_answer(text) in normalized_hidden_answers
        )
        for field_name, text in public_text_fields
    )
    _require(
        not public_scoring_leak,
        f"{owner} contains a public scoring leak",
    )

    prompt_key = (item.passage.strip().casefold(), item.prompt.strip().casefold())
    _require(prompt_key not in prompt_keys, f"{owner} repeats another placement prompt")
    prompt_keys.add(prompt_key)
    prompt_surface = _normalize_public_surface(item.prompt)
    _require(
        prompt_surface not in track_prompt_surfaces,
        f"{owner} repeats a prompt surface within {track.track_id}",
    )
    track_prompt_surfaces.add(prompt_surface)
    passage_surface = _normalize_public_surface(item.passage)
    if passage_surface:
        _require(
            passage_surface not in track_passage_surfaces,
            f"{owner} repeats a passage within {track.track_id}",
        )
        track_passage_surfaces.add(passage_surface)

    _require(set(item.localized_copy) == {"en", "hi", "hi_en"}, f"{owner} is missing en/hi/hi_en localizations")
    for language, learner_copy in item.localized_copy.items():
        _require(bool(learner_copy.instruction.strip()), f"{owner} has no {language} instruction")
        _require(bool(learner_copy.support.strip()), f"{owner} has no {language} support copy")

    _validate_approval(item.approval, owner)
    _require(bool(item.misconception_clusters), f"{owner} has no misconception clusters")
    cluster_codes = tuple(
        cluster.code.strip() for cluster in item.misconception_clusters
    )
    _require(
        all(cluster_codes),
        f"{owner} has an empty misconception cluster code",
    )
    _require(
        len(set(cluster_codes)) == len(cluster_codes),
        f"{owner} must use unique misconception cluster codes",
    )
    _require(
        all(cluster.learner_safe_label.strip() for cluster in item.misconception_clusters),
        f"{owner} has an empty learner-safe remediation label",
    )

    if item.primary_skill_id == "writing.complete_sentence":
        rubric_contract = COMPLETE_SENTENCE_RUBRICS_BY_SOURCE_BAND.get(item.source_class_no)
        _require(rubric_contract is not None, f"{owner} has no sentence-production band rubric")
        _require(
            item.item_type == "short_answer"
            and item.evaluation_mode == "strict_rubric"
            and not item.answer_key
            and not item.accepted_answers,
            f"{owner} must assess authentic sentence production",
        )
        _require(
            item.rubric_ref == rubric_contract["rubric_ref"],
            f"{owner} has the wrong sentence-production band rubric",
        )
        _require(
            "complete english sentence" in item.prompt.casefold(),
            f"{owner} does not request a complete English sentence",
        )

    if item.evaluation_mode == "deterministic":
        _require(bool(item.accepted_answers), f"{owner} has no accepted answers")
        _require(item.rubric_ref is None, f"{owner} mixes deterministic answers and a rubric")
        _require(bool(item.answer_key), f"{owner} has no deterministic answer key")
        normalized_answers = tuple(
            normalize_placement_answer(answer) for answer in item.accepted_answers
        )
        _require(
            all(normalized_answers)
            and len(set(normalized_answers)) == len(normalized_answers),
            f"{owner} has empty or repeated accepted alternatives",
        )
        normalized_key = normalize_placement_answer(item.answer_key)
        _require(
            normalized_key in set(normalized_answers),
            f"{owner} answer key is not among accepted answers",
        )
        normalized_id = _normalized_identifier_part(item.item_id)
        for accepted_answer in item.accepted_answers:
            normalized_answer = _normalized_identifier_part(accepted_answer)
            _require(
                len(normalized_answer) < 3 or normalized_answer not in normalized_id,
                f"{owner} semantically leaks an accepted answer",
            )
    elif item.evaluation_mode == "strict_rubric":
        _require(not item.accepted_answers, f"{owner} leaks accepted answers for a strict rubric")
        _require(not item.answer_key, f"{owner} leaks a model answer for a strict rubric")
        _require(bool(item.rubric_ref and item.rubric_ref.startswith("school.strict.")), f"{owner} has no strict rubric reference")
        declared_criteria = STRICT_RUBRIC_CRITERIA_BY_REF.get(item.rubric_ref)
        _require(declared_criteria is not None, f"{owner} references an undeclared strict rubric")
        expected_triggers = {
            f"criterion:{criterion_id}" for criterion_id in declared_criteria
        }
        actual_triggers = {
            trigger
            for cluster in item.misconception_clusters
            for trigger in cluster.triggers
        }
        _require(
            actual_triggers == expected_triggers
            and len(item.misconception_clusters) == len(declared_criteria)
            and all(len(cluster.triggers) == 1 for cluster in item.misconception_clusters),
            f"{owner} has incomplete or extra rubric criterion coverage",
        )
        clusters_by_trigger = {
            cluster.triggers[0]: cluster
            for cluster in item.misconception_clusters
        }
        _require(
            all(
                clusters_by_trigger[f"criterion:{criterion_id}"].learner_safe_label
                == RUBRIC_REMEDIATION_BY_CRITERION[criterion_id]
                for criterion_id in declared_criteria
            ),
            f"{owner} does not use canonical remediation text",
        )
    else:
        raise PlacementBankValidationError(f"{owner} has unsupported evaluation mode")

    if item.item_type == "multiple_choice":
        _require(len(item.options) >= 3, f"{owner} has too few options")
        normalized_options = tuple(
            normalize_placement_answer(option) for option in item.options
        )
        _require(
            all(normalized_options)
            and len(set(normalized_options)) == len(normalized_options),
            f"{owner} has empty or repeated options",
        )
        normalized_key = normalize_placement_answer(item.answer_key)
        _require(
            normalized_options.count(normalized_key) == 1,
            f"{owner} does not have exactly one consistent correct option",
        )
        wrong_options = set(item.options) - {item.answer_key}
        mapped = {
            trigger
            for cluster in item.misconception_clusters
            for trigger in cluster.triggers
        }
        _require(wrong_options <= mapped, f"{owner} has an unmapped wrong alternative")

    if item.primary_skill_id == "grammar.connectors_because_and_but":
        scoped_relationship = any(
            marker in item.prompt.casefold()
            for marker in ("reason", "contrast", "add", "addition")
        )
        _require(scoped_relationship, f"{owner} does not identify the connector relationship")


def validate_placement_bank(tracks_by_class: Mapping[int, Sequence[Any]]) -> bool:
    """Validate every authored track and raise on the first unsafe gap."""

    _require(set(tracks_by_class) == {2, 3, 4, 5}, "placement bank must define Classes 2-5")
    locked_skills = set(locked_english_skill_ids())
    track_ids: set[str] = set()
    item_ids: set[str] = set()
    prompt_keys: set[tuple[str, str]] = set()

    for class_no in range(2, 6):
        tracks = tuple(tracks_by_class[class_no])
        _require(len(tracks) == 8, f"Class {class_no} must expose exactly 8 snapshot tracks")
        _require({track.domain for track in tracks} == {"reading", "vocabulary", "grammar", "writing"}, f"Class {class_no} tracks do not span all four domains")

        for track in tracks:
            owner = f"track {track.track_id!r}"
            _require(bool(track.track_id.strip()), "placement track ID is empty")
            _require(track.track_id not in track_ids, f"duplicate placement track ID: {track.track_id}")
            track_ids.add(track.track_id)
            _require(track.subject_id == "english", f"{owner} has unsupported subject")
            _require(track.target_class_no == class_no, f"{owner} has wrong target class")
            _require(track.primary_skill_id in locked_skills, f"{owner} uses an unlocked primary skill")
            _require(bool(track.learner_skill_label.strip()), f"{owner} has no learner-safe label")
            _validate_approval(track.approval, owner)
            track_prompt_surfaces: set[str] = set()
            track_passage_surfaces: set[str] = set()

            expected_bands = {max(1, class_no - 1), class_no}
            actual_bands = {band.source_class_no for band in track.bands}
            _require(actual_bands == expected_bands, f"{owner} source bands must be {sorted(expected_bands)}")
            _require(track.snapshot_item.stage == "snapshot", f"{owner} has no snapshot item")
            _require(track.snapshot_item.source_class_no in expected_bands, f"{owner} snapshot uses an unreachable source band")
            _validate_item(
                track.snapshot_item,
                track,
                item_ids,
                prompt_keys,
                track_prompt_surfaces,
                track_passage_surfaces,
            )

            for band in track.bands:
                _require(len(band.variants) >= 2, f"{owner} source band {band.source_class_no} needs two unused variants")
                stages = {item.stage for item in band.variants}
                _require({"targeted_diagnostic", "confirmatory"} <= stages, f"{owner} source band {band.source_class_no} lacks targeted/confirmatory variants")
                for item in band.variants:
                    _require(item.source_class_no == band.source_class_no, f"{owner} variant is stored in the wrong source band")
                    _validate_item(
                        item,
                        track,
                        item_ids,
                        prompt_keys,
                        track_prompt_surfaces,
                        track_passage_surfaces,
                    )

    return True
