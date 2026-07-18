from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

import pytest

from app.content import school_rebuild_placement_bank as bank
from app.content import school_rebuild_placement_validation as placement_validation
from app.content.school_v3_taxonomy import locked_english_skill_ids
from app.services import school_rebuild_placement as placement_runtime


LANGUAGES = {"en", "hi", "hi_en"}
FORBIDDEN_PUBLIC_KEYS = {
    "accepted_answers",
    "answer_key",
    "evaluation_mode",
    "hidden_rubric",
    "model_answer",
    "rubric_ref",
    "rubric_criteria",
    "scoring_criteria",
}
OPAQUE_ITEM_ID = re.compile(
    r"^spv_c0[2-5]_t0[1-8]_v0[1-6]$"
)


def _all_tracks():
    return tuple(
        track
        for class_no in range(2, 6)
        for track in bank.placement_tracks_for("english", class_no)
    )


def _all_items():
    return tuple(
        item
        for track in _all_tracks()
        for item in (
            track.snapshot_item,
            *(variant for band in track.bands for variant in band.variants),
        )
    )


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            nested_key
            for nested_value in value.values()
            for nested_key in _walk_keys(nested_value)
        }
    if isinstance(value, (list, tuple)):
        return {
            nested_key
            for nested_value in value
            for nested_key in _walk_keys(nested_value)
        }
    return set()


def _normalized_identifier_part(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _bank_with_replaced_item(original, replacement):
    valid = bank.PLACEMENT_TRACKS_BY_CLASS
    target_track = next(
        track
        for track in valid[original.target_class_no]
        if track.track_id == original.track_id
    )
    if target_track.snapshot_item.item_id == original.item_id:
        changed_track = replace(target_track, snapshot_item=replacement)
    else:
        changed_track = replace(
            target_track,
            bands=tuple(
                replace(
                    source_band,
                    variants=tuple(
                        replacement if item.item_id == original.item_id else item
                        for item in source_band.variants
                    ),
                )
                for source_band in target_track.bands
            ),
        )
    return {
        **valid,
        original.target_class_no: tuple(
            changed_track if track.track_id == target_track.track_id else track
            for track in valid[original.target_class_no]
        ),
    }


@pytest.mark.parametrize("class_no", [2, 3, 4, 5])
def test_each_target_class_has_exactly_eight_engineering_qa_snapshot_tracks(class_no):
    tracks = bank.placement_tracks_for("english", class_no)

    assert len(tracks) == 8
    assert {track.domain for track in tracks} == {
        "reading",
        "vocabulary",
        "grammar",
        "writing",
    }
    assert all(track.target_class_no == class_no for track in tracks)
    assert all(track.snapshot_item.stage == "snapshot" for track in tracks)
    assert all(track.approval.engineering_qa_status == "passed" for track in tracks)
    assert all(
        track.approval.content_review_status == "agent_reviewed"
        for track in tracks
    )
    assert all(track.approval.launch_status == "qa_only" for track in tracks)
    assert all(
        track.approval.reference == "app/content/school_rebuild_placement_review_manifest.json"
        for track in tracks
    )


def test_snapshot_items_are_fast_provider_free_checks():
    for track in _all_tracks():
        item = track.snapshot_item

        assert item.evaluation_mode == "deterministic"
        assert item.answer_key
        assert item.accepted_answers
        assert item.rubric_ref is None


def test_items_score_one_locked_primary_skill_and_only_telemetry_secondary_tags():
    locked_skills = set(locked_english_skill_ids())

    for track in _all_tracks():
        assert track.primary_skill_id in locked_skills
        for item in (
            track.snapshot_item,
            *(variant for band in track.bands for variant in band.variants),
        ):
            assert item.primary_skill_id == track.primary_skill_id
            assert item.primary_skill_id not in item.telemetry_skill_ids
            assert item.skill_ids == (item.primary_skill_id,)


def test_every_reachable_source_band_has_two_independent_unused_variants():
    for track in _all_tracks():
        expected_bands = {max(1, track.target_class_no - 1), track.target_class_no}
        assert {band.source_class_no for band in track.bands} == expected_bands
        assert track.snapshot_item.source_class_no in expected_bands

        for source_band in track.bands:
            assert len(source_band.variants) >= 2
            assert {item.stage for item in source_band.variants} >= {
                "targeted_diagnostic",
                "confirmatory",
            }
            assert len({item.item_id for item in source_band.variants}) == len(
                source_band.variants
            )
            assert len(
                {(item.passage.strip(), item.prompt.strip()) for item in source_band.variants}
            ) == len(source_band.variants)
            assert all(
                item.item_id != track.snapshot_item.item_id
                for item in source_band.variants
            )


def test_each_track_uses_a_distinct_prompt_surface_for_every_probe():
    for track in _all_tracks():
        items = (
            track.snapshot_item,
            *(variant for band in track.bands for variant in band.variants),
        )
        normalized_prompts = [
            " ".join(item.prompt.casefold().split())
            for item in items
        ]

        assert len(normalized_prompts) == len(set(normalized_prompts)), track.track_id


def test_validator_rejects_normalized_passage_reuse_with_distinct_prompts():
    track = next(track for track in _all_tracks() if track.snapshot_item.passage.strip())
    original = track.bands[0].variants[0]
    reused_passage = "   ".join(track.snapshot_item.passage.swapcase().split())
    replacement = replace(original, passage=f"  {reused_passage}  ")

    with pytest.raises(
        placement_validation.PlacementBankValidationError,
        match="repeats a passage within",
    ):
        placement_validation.validate_placement_bank(
            _bank_with_replaced_item(original, replacement)
        )


def test_every_item_has_three_learner_safe_localizations_and_approved_evaluation():
    unsafe_support_phrases = ("answer is", "correct answer", "rubric", "score")

    for item in _all_items():
        assert set(item.localized_copy) == LANGUAGES
        for copy in item.localized_copy.values():
            assert copy.instruction.strip()
            assert copy.support.strip()
            assert not any(
                phrase in copy.support.casefold() for phrase in unsafe_support_phrases
            )

        assert item.approval.engineering_qa_status == "passed"
        assert item.approval.content_review_status == "agent_reviewed"
        assert item.approval.launch_status == "qa_only"
        assert item.misconception_clusters

        if item.evaluation_mode == "deterministic":
            assert item.accepted_answers
            assert item.rubric_ref is None
        else:
            assert item.evaluation_mode == "strict_rubric"
            assert item.rubric_ref and item.rubric_ref.startswith("school.strict.")
            assert not item.accepted_answers


def test_deterministic_short_answers_explain_the_closed_response_contract():
    items = [
        item
        for item in _all_items()
        if item.evaluation_mode == "deterministic"
        and item.item_type == "short_answer"
    ]

    assert items
    for item in items:
        assert "only" in item.localized_copy["en"].instruction.casefold()
        assert "smallest complete response" in item.localized_copy["en"].support.casefold()


def test_multiple_choice_wrong_options_map_to_explicit_misconception_clusters():
    for item in _all_items():
        if item.item_type != "multiple_choice":
            continue

        wrong_options = set(item.options) - {item.answer_key}
        mapped_alternatives = {
            trigger
            for cluster in item.misconception_clusters
            for trigger in cluster.triggers
        }
        assert wrong_options <= mapped_alternatives


def test_item_and_track_ids_are_globally_unique_and_bank_validates_at_load():
    tracks = _all_tracks()
    items = _all_items()

    assert len({track.track_id for track in tracks}) == len(tracks)
    assert len({item.item_id for item in items}) == len(items)
    assert bank.PLACEMENT_BANK_VALIDATED is True


def test_registry_and_localization_are_deeply_immutable_without_divergent_banks():
    assert isinstance(bank.PLACEMENT_TRACKS_BY_CLASS, MappingProxyType)
    assert isinstance(bank.PLACEMENT_BANK_BY_CLASS, MappingProxyType)
    with pytest.raises(TypeError):
        bank.PLACEMENT_TRACKS_BY_CLASS[2] = ()
    with pytest.raises(TypeError):
        bank.PLACEMENT_BANK_BY_CLASS[2] = ()

    first_item = _all_items()[0]
    assert isinstance(first_item.localized_copy, MappingProxyType)
    with pytest.raises(TypeError):
        first_item.localized_copy["en"] = first_item.localized_copy["hi"]

    assert bank.CLASS_2_PLACEMENT_BANK is bank.PLACEMENT_BANK_BY_CLASS[2]
    assert bank.CLASS_3_PLACEMENT_BANK is bank.PLACEMENT_BANK_BY_CLASS[3]
    assert bank.CLASS_4_PLACEMENT_BANK is bank.PLACEMENT_BANK_BY_CLASS[4]
    assert bank.CLASS_5_PLACEMENT_BANK is bank.PLACEMENT_BANK_BY_CLASS[5]
    for class_no in range(2, 6):
        assert bank.placement_bank_for("english", class_no) is bank.PLACEMENT_BANK_BY_CLASS[class_no]


def test_engineering_qa_approval_uses_backend_local_manifest_without_claiming_human_review():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        validate_placement_bank,
    )

    manifest_path = Path(bank.__file__).with_name(
        "school_rebuild_placement_review_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["content_version"] == "placement-bank-v1"
    assert manifest["engineering_qa_status"] == "passed"
    assert manifest["content_review_status"] == "agent_reviewed"
    assert manifest["launch_status"] == "qa_only"
    for track in _all_tracks():
        assert track.approval.reference == (
            "app/content/school_rebuild_placement_review_manifest.json"
        )
        assert track.approval.content_review_status != "release_approved"

    item = _all_items()[0]
    false_approval = replace(
        item.approval,
        content_review_status="release_approved",
        launch_status="release_approved",
    )
    falsely_approved_item = replace(item, approval=false_approval)
    with pytest.raises(PlacementBankValidationError, match="content-review status"):
        validate_placement_bank(_bank_with_replaced_item(item, falsely_approved_item))


def test_public_item_ids_are_opaque_and_do_not_semantically_leak_answers():
    for item in _all_items():
        public_id = bank.public_placement_item(item)["item_id"]
        normalized_id = _normalized_identifier_part(public_id)

        assert OPAQUE_ITEM_ID.fullmatch(public_id)
        for accepted_answer in item.accepted_answers:
            normalized_answer = _normalized_identifier_part(accepted_answer)
            if len(normalized_answer) >= 3:
                assert normalized_answer not in normalized_id


def test_opaque_item_id_contract_allows_one_extra_authored_diagnostic_variant():
    assert OPAQUE_ITEM_ID.fullmatch("spv_c05_t03_v06")
    assert OPAQUE_ITEM_ID.fullmatch("spv_c02_t01_v05")
    assert OPAQUE_ITEM_ID.fullmatch("spv_c02_t07_v06")
    assert not OPAQUE_ITEM_ID.fullmatch("spv_c02_t01_v07")


def test_complete_sentence_snapshots_are_fast_checks_and_diagnostics_keep_band_rubrics():
    rubric_contracts = getattr(
        placement_validation,
        "COMPLETE_SENTENCE_RUBRICS_BY_SOURCE_BAND",
        {},
    )
    assert set(rubric_contracts) == {1, 2, 3}

    complete_sentence_items = tuple(
        item
        for item in _all_items()
        if item.primary_skill_id == "writing.complete_sentence"
    )
    assert complete_sentence_items
    for item in complete_sentence_items:
        contract = rubric_contracts[item.source_class_no]
        assert item.item_type == "short_answer"
        if item.stage == "snapshot":
            assert item.evaluation_mode == "deterministic"
            assert item.answer_key
            assert item.accepted_answers
            assert item.rubric_ref is None
        else:
            assert item.evaluation_mode == "strict_rubric"
            assert item.answer_key is None
            assert item.accepted_answers == ()
            assert item.rubric_ref == contract["rubric_ref"]
            assert "complete_idea" in contract["criteria"]
            assert "english_response" in contract["criteria"]
        assert "complete English sentence" in item.prompt


def test_strict_rubric_items_map_every_declared_criterion_to_exact_remediation():
    criteria_by_ref = getattr(
        placement_validation,
        "STRICT_RUBRIC_CRITERIA_BY_REF",
        {},
    )
    strict_items = tuple(
        item for item in _all_items() if item.evaluation_mode == "strict_rubric"
    )

    assert strict_items
    assert {item.rubric_ref for item in strict_items} == set(criteria_by_ref)
    for item in strict_items:
        declared_criteria = set(criteria_by_ref[item.rubric_ref])
        mapped_criteria = {
            trigger.removeprefix("criterion:")
            for cluster in item.misconception_clusters
            for trigger in cluster.triggers
            if trigger.startswith("criterion:")
        }
        all_triggers = {
            trigger
            for cluster in item.misconception_clusters
            for trigger in cluster.triggers
        }

        assert mapped_criteria == declared_criteria
        assert all_triggers == {
            f"criterion:{criterion_id}" for criterion_id in declared_criteria
        }
        assert len(item.misconception_clusters) == len(declared_criteria)
        assert all(cluster.learner_safe_label.strip() for cluster in item.misconception_clusters)


def test_validator_rejects_strict_item_with_incomplete_rubric_criterion_coverage():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        validate_placement_bank,
    )

    valid = bank.PLACEMENT_TRACKS_BY_CLASS
    strict_item = next(
        item for item in _all_items() if item.evaluation_mode == "strict_rubric"
    )
    strict_track = next(
        track
        for track in valid[strict_item.target_class_no]
        if track.track_id == strict_item.track_id
    )
    incomplete_item = replace(
        strict_item,
        misconception_clusters=strict_item.misconception_clusters[:-1],
    )
    if strict_track.snapshot_item.item_id == strict_item.item_id:
        incomplete_track = replace(strict_track, snapshot_item=incomplete_item)
    else:
        incomplete_track = replace(
            strict_track,
            bands=tuple(
                replace(
                    source_band,
                    variants=tuple(
                        incomplete_item if item.item_id == strict_item.item_id else item
                        for item in source_band.variants
                    ),
                )
                for source_band in strict_track.bands
            ),
        )

    with pytest.raises(PlacementBankValidationError, match="rubric criterion coverage"):
        validate_placement_bank(
            {
                **valid,
                strict_item.target_class_no: tuple(
                    incomplete_track if track.track_id == strict_track.track_id else track
                    for track in valid[strict_item.target_class_no]
                ),
            }
        )

    unrelated_remediation = replace(
        strict_item,
        misconception_clusters=(
            replace(
                strict_item.misconception_clusters[0],
                learner_safe_label="Try again with more care.",
            ),
            *strict_item.misconception_clusters[1:],
        ),
    )
    with pytest.raises(PlacementBankValidationError, match="canonical remediation"):
        validate_placement_bank(
            _bank_with_replaced_item(strict_item, unrelated_remediation)
        )


def test_known_fish_bird_and_connector_prompts_have_one_defensible_scoring_path():
    fish_item = next(item for item in _all_items() if "A fish" in item.passage)
    bird_item = next(
        item for item in _all_items() if "bird" in item.passage.casefold() and "branch" in item.passage.casefold()
    )
    connector_item = next(item for item in _all_items() if "Leena wanted" in item.passage)

    for sentence_item in (fish_item, bird_item):
        assert sentence_item.evaluation_mode == "deterministic"
        assert sentence_item.item_type == "short_answer"
        assert sentence_item.accepted_answers
        assert "complete English sentence" in sentence_item.prompt

    assert connector_item.answer_key == "but"
    assert "contrast" in connector_item.prompt.casefold()
    assert connector_item.options == ("but", "because", "so")


def test_validator_rejects_deterministic_diagnostic_sentence_production_and_unscoped_connectors():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        validate_placement_bank,
    )

    valid = bank.PLACEMENT_TRACKS_BY_CLASS
    sentence_item = next(
        item
        for item in _all_items()
        if item.primary_skill_id == "writing.complete_sentence"
        and item.stage != "snapshot"
    )
    invalid_sentence = replace(
        sentence_item,
        evaluation_mode="deterministic",
        answer_key="swims",
        accepted_answers=("swims",),
        rubric_ref=None,
    )
    with pytest.raises(PlacementBankValidationError, match="sentence production"):
        validate_placement_bank(_bank_with_replaced_item(sentence_item, invalid_sentence))

    connector_track = next(
        track
        for track in valid[4]
        if track.primary_skill_id == "grammar.connectors_because_and_but"
    )
    invalid_connector = replace(
        connector_track.snapshot_item,
        prompt="Which connector fits?",
    )
    invalid_connector_track = replace(connector_track, snapshot_item=invalid_connector)
    with pytest.raises(PlacementBankValidationError, match="connector relationship"):
        validate_placement_bank(
            {
                **valid,
                4: tuple(
                    invalid_connector_track if track.track_id == connector_track.track_id else track
                    for track in valid[4]
                ),
            }
        )


def test_public_projection_recursively_excludes_hidden_answers_and_rubrics():
    for item in _all_items():
        public = bank.public_placement_item(item, language="hi_en")

        assert not (_walk_keys(public) & FORBIDDEN_PUBLIC_KEYS)
        assert public["instruction"] == item.localized_copy["hi_en"].instruction
        assert public["support"] == item.localized_copy["hi_en"].support


def test_deterministic_answer_keys_and_mcq_options_are_normalization_consistent():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        normalize_placement_answer,
        validate_placement_bank,
    )

    deterministic = tuple(
        item for item in _all_items() if item.evaluation_mode == "deterministic"
    )
    assert len(deterministic) == 120
    for item in deterministic:
        normalized_answers = {
            normalize_placement_answer(answer) for answer in item.accepted_answers
        }
        assert normalize_placement_answer(item.answer_key) in normalized_answers
        if item.item_type == "multiple_choice":
            matching_options = [
                option
                for option in item.options
                if normalize_placement_answer(option)
                == normalize_placement_answer(item.answer_key)
            ]
            assert len(matching_options) == 1

    missing_key_item = replace(
        deterministic[0],
        accepted_answers=("genuinely different",),
    )
    with pytest.raises(PlacementBankValidationError, match="answer key.*accepted"):
        validate_placement_bank(
            _bank_with_replaced_item(deterministic[0], missing_key_item)
        )

    mcq_item = next(item for item in deterministic if item.item_type == "multiple_choice")
    inconsistent_mcq = replace(
        mcq_item,
        options=tuple(
            "unrelated choice" if option == mcq_item.answer_key else option
            for option in mcq_item.options
        ),
    )
    with pytest.raises(PlacementBankValidationError, match="correct option"):
        validate_placement_bank(_bank_with_replaced_item(mcq_item, inconsistent_mcq))


def test_runtime_answer_matching_uses_shared_punctuation_tolerant_normalization():
    deterministic = tuple(
        item for item in _all_items() if item.evaluation_mode == "deterministic"
    )
    assert len(deterministic) == 120

    for item in deterministic:
        assert placement_runtime.answer_matches(item, f"  {item.answer_key}.  ")
        assert placement_runtime.answer_matches(item, f"{item.answer_key}?!")
        assert not placement_runtime.answer_matches(
            item,
            f"{item.answer_key} genuinely different",
        )


def test_validator_rejects_public_scoring_leaks_and_strict_answer_options():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        validate_placement_bank,
    )

    deterministic = next(
        item for item in _all_items() if item.evaluation_mode == "deterministic"
    )
    leaked_copy = dict(deterministic.localized_copy)
    leaked_copy["en"] = replace(
        leaked_copy["en"],
        support=f"The correct answer is {deterministic.answer_key}.",
    )
    leaked_support = replace(deterministic, localized_copy=leaked_copy)
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(_bank_with_replaced_item(deterministic, leaked_support))

    bare_answer_copy = dict(deterministic.localized_copy)
    bare_answer_copy["en"] = replace(
        bare_answer_copy["en"],
        support=deterministic.answer_key,
    )
    bare_answer_support = replace(
        deterministic,
        localized_copy=bare_answer_copy,
    )
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(
            _bank_with_replaced_item(deterministic, bare_answer_support)
        )

    marker_label = replace(
        deterministic,
        learner_skill_label=f"Correct answer: {deterministic.answer_key}",
    )
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(_bank_with_replaced_item(deterministic, marker_label))

    leaked_instruction_copy = dict(deterministic.localized_copy)
    leaked_instruction_copy["hi_en"] = replace(
        leaked_instruction_copy["hi_en"],
        instruction="Sahi answer ko seedha copy karo.",
    )
    leaked_instruction = replace(
        deterministic,
        localized_copy=leaked_instruction_copy,
    )
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(
            _bank_with_replaced_item(deterministic, leaked_instruction)
        )

    leaked_passage = replace(
        deterministic,
        passage="Rubric: award full marks for copying the hidden key.",
    )
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(_bank_with_replaced_item(deterministic, leaked_passage))

    strict_item = next(
        item for item in _all_items() if item.evaluation_mode == "strict_rubric"
    )
    leaked_model = replace(
        strict_item,
        prompt="Model answer: copy the passage exactly.",
    )
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(_bank_with_replaced_item(strict_item, leaked_model))

    strict_options = replace(strict_item, options=("hidden model answer",))
    with pytest.raises(PlacementBankValidationError, match="strict-rubric.*options"):
        validate_placement_bank(_bank_with_replaced_item(strict_item, strict_options))

    mcq_item = next(item for item in _all_items() if item.item_type == "multiple_choice")
    leaked_options = replace(
        mcq_item,
        options=(
            *mcq_item.options[:-1],
            f"{mcq_item.options[-1]} (correct answer)",
        ),
    )
    with pytest.raises(PlacementBankValidationError, match="public scoring leak"):
        validate_placement_bank(_bank_with_replaced_item(mcq_item, leaked_options))


def test_validator_rejects_invalid_misconception_metadata_and_item_types():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        validate_placement_bank,
    )

    item = next(item for item in _all_items() if len(item.misconception_clusters) >= 2)
    first_cluster = item.misconception_clusters[0]

    blank_code = replace(
        item,
        misconception_clusters=(
            replace(first_cluster, code=" "),
            *item.misconception_clusters[1:],
        ),
    )
    with pytest.raises(PlacementBankValidationError, match="misconception cluster code"):
        validate_placement_bank(_bank_with_replaced_item(item, blank_code))

    duplicate_codes = replace(
        item,
        misconception_clusters=(
            first_cluster,
            replace(item.misconception_clusters[1], code=first_cluster.code),
            *item.misconception_clusters[2:],
        ),
    )
    with pytest.raises(PlacementBankValidationError, match="unique misconception cluster"):
        validate_placement_bank(_bank_with_replaced_item(item, duplicate_codes))

    blank_label = replace(
        item,
        misconception_clusters=(
            replace(first_cluster, learner_safe_label=" "),
            *item.misconception_clusters[1:],
        ),
    )
    with pytest.raises(PlacementBankValidationError, match="learner-safe remediation"):
        validate_placement_bank(_bank_with_replaced_item(item, blank_label))

    unsupported_type = replace(item, item_type="essay")
    with pytest.raises(PlacementBankValidationError, match="unsupported item type"):
        validate_placement_bank(_bank_with_replaced_item(item, unsupported_type))


def test_validator_fails_hard_for_missing_track_band_localization_and_rubric():
    from app.content.school_rebuild_placement_validation import (
        PlacementBankValidationError,
        validate_placement_bank,
    )

    valid = bank.PLACEMENT_TRACKS_BY_CLASS
    missing_track = {**valid, 2: valid[2][:-1]}
    with pytest.raises(PlacementBankValidationError, match="exactly 8"):
        validate_placement_bank(missing_track)

    first_track = valid[2][0]
    missing_band = replace(first_track, bands=first_track.bands[:-1])
    with pytest.raises(PlacementBankValidationError, match="source bands"):
        validate_placement_bank({**valid, 2: (missing_band, *valid[2][1:])})

    snapshot = first_track.snapshot_item
    missing_localization = replace(
        snapshot,
        localized_copy={
            key: value for key, value in snapshot.localized_copy.items() if key != "hi"
        },
    )
    bad_localization_track = replace(first_track, snapshot_item=missing_localization)
    with pytest.raises(PlacementBankValidationError, match="localizations"):
        validate_placement_bank(
            {**valid, 2: (bad_localization_track, *valid[2][1:])}
        )

    strict_item = next(item for item in _all_items() if item.evaluation_mode == "strict_rubric")
    bad_strict_item = replace(strict_item, rubric_ref=None)
    strict_track = next(
        track
        for track in valid[strict_item.target_class_no]
        if track.track_id == strict_item.track_id
    )
    if strict_track.snapshot_item.item_id == strict_item.item_id:
        bad_strict_track = replace(strict_track, snapshot_item=bad_strict_item)
    else:
        bad_bands = tuple(
            replace(
                source_band,
                variants=tuple(
                    bad_strict_item if item.item_id == strict_item.item_id else item
                    for item in source_band.variants
                ),
            )
            for source_band in strict_track.bands
        )
        bad_strict_track = replace(strict_track, bands=bad_bands)

    class_tracks = valid[strict_item.target_class_no]
    with pytest.raises(PlacementBankValidationError, match="rubric"):
        validate_placement_bank(
            {
                **valid,
                strict_item.target_class_no: tuple(
                    bad_strict_track if track.track_id == strict_track.track_id else track
                    for track in class_tracks
                ),
            }
        )
