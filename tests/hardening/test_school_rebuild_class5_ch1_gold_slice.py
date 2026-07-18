from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import get_args

import pytest
from pydantic import ValidationError

from app.content.school.standards import locked_english_taxonomy
from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.content import school_rebuild_schema as school_schema
from app.content.school_rebuild_schema import LiveChapterAssessmentItem
from app.services.school import open_answer_ai
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_masterclass as masterclass
from scripts.audit_school_rebuild_content import _launch_level_count_is_valid
from scripts import upgrade_school_chapter1_deep_loop as chapter1_upgrader


CHAPTER_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
    / "eng_c5_ch01.json"
)

EXPECTED_SOURCE_SECTIONS = {
    "recitation",
    "new_words",
    "think_questions",
    "attribute_ordering",
    "pair_phrases",
    "spelling_choices",
    "prepositions_in_context",
    "opposites_crossword",
    "speaking_language_words",
    "listening_sound_pairs",
    "poem_to_story",
    "visual_play",
    "riddle",
}
EXPECTED_LEVEL_IDS = (
    "papas_spectacles_poem_comprehension",
    "papas_spectacles_chapter_words",
    "papas_spectacles_personal_response",
    "papas_spectacles_order_and_pairs",
    "papas_spectacles_spelling_and_opposites",
    "papas_spectacles_prepositions",
    "papas_spectacles_poem_to_story",
    "papas_spectacles_sound_lab",
    "papas_spectacles_visual_fun_and_riddle",
)
NEW_TAXONOMY_SKILLS = {
    "vocab.attribute_ordering",
    "vocab.spelling",
    "vocab.antonyms",
    "grammar.prepositions",
    "speaking.recitation",
    "speaking.multilingual_expression",
    "listening.sound_discrimination",
}
NON_CERTIFYING_ANCHOR_SUFFIXES = {
    "recitation",
    "speaking_language_words",
    "listening_sound_pairs",
    "visual_play",
    "riddle",
}
INTERNAL_LEARNER_TERMS = (
    "browser lesson",
    "scored response",
    "typed response",
    "typed work",
    "certifies",
    "certification",
)


def _chapter() -> dict:
    return load_live_chapter_file(CHAPTER_PATH).runtime_dict()


def _level(chapter: dict, level_id: str) -> dict:
    return next(
        level for level in chapter["levels"] if level["level_id"] == level_id
    )


def _phase_variants(level: dict, phase: str) -> list[dict]:
    step = next(
        step for step in level["teaching_steps"] if step["phase"] == phase
    )
    return list(step["variant_pool"])


def _phase_activities(level: dict, phase: str) -> list[dict]:
    step = next(
        step for step in level["teaching_steps"] if step["phase"] == phase
    )
    if "activity" in step:
        return [step["activity"]]
    return list(step["variant_pool"])


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _word_ngrams(value: str, size: int) -> set[tuple[str, ...]]:
    words = _normalized(value).replace(",", "").replace(".", "").split()
    return {
        tuple(words[index : index + size])
        for index in range(max(0, len(words) - size + 1))
    }


def _personal_response_variant(variant_id: str) -> dict:
    level = _level(_chapter(), "papas_spectacles_personal_response")
    activity = next(
        item
        for step in level["teaching_steps"]
        for item in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if item.get("variant_id") == variant_id
    )
    return {
        **activity,
        "activity_id": variant_id,
        "skill_ids": list(activity["knowledge_components"]),
    }


def _authored_personal_response_variant(variant_id: str) -> dict:
    activity = _personal_response_variant(variant_id)
    return {
        key: value
        for key, value in activity.items()
        if key not in {"activity_id", "skill_ids"}
    }


def test_semantic_validator_literal_contains_exactly_two_closed_rules():
    assert set(get_args(school_schema.SchoolOpenSemanticValidatorId)) == {
        "evidence_over_unsupported_guess_v1",
        "affirmative_support_or_no_mocking_v1",
    }


def test_semantic_validator_ids_are_preserved_only_on_two_target_variants():
    chapter = _chapter()
    tagged = {
        item["variant_id"]: item["semantic_validator_id"]
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        for item in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if item.get("semantic_validator_id")
    }

    assert tagged == {
        "papas_spectacles_personal_response:independent_application:v4": (
            "evidence_over_unsupported_guess_v1"
        ),
        "papas_spectacles_personal_response:review:v2": (
            "affirmative_support_or_no_mocking_v1"
        ),
    }
    for variant_id, validator_id in tagged.items():
        activity = _personal_response_variant(variant_id)
        context = school_open_context_from_activity(
            activity,
            activity["model_answer"],
        )
        assert context.semantic_validator_id == validator_id
        assert context.model_dump()["semantic_validator_id"] == validator_id


def test_semantic_validator_id_is_only_legal_for_strict_open_activities():
    activity = _authored_personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )

    with pytest.raises(
        ValidationError,
        match="semantic_validator_requires_strict_open_rubric",
    ):
        school_schema.LiveChapterActivity.model_validate(
            {
                **activity,
                "grading_mode": "selected_option",
                "semantic_validator_id": (
                    "evidence_over_unsupported_guess_v1"
                ),
            }
        )


def test_unknown_semantic_validator_id_fails_schema_and_context_validation():
    authored = _authored_personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    with pytest.raises(ValidationError) as schema_error:
        school_schema.LiveChapterActivity.model_validate(
            {**authored, "semantic_validator_id": "unregistered_rule_v1"}
        )
    assert any(
        error["loc"] == ("semantic_validator_id",)
        and error["type"] == "literal_error"
        for error in schema_error.value.errors()
    )

    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    with pytest.raises(ValidationError) as context_error:
        school_open_context_from_activity(
            {**activity, "semantic_validator_id": "unregistered_rule_v1"},
            activity["model_answer"],
        )
    assert any(
        error["loc"] == ("semantic_validator_id",)
        and error["type"] == "literal_error"
        for error in context_error.value.errors()
    )


def _model_overgraded_decision(
    activity: dict,
    answer: str,
    semantic_evidence: dict[str, str],
) -> dict:
    evidence_by_id = {
        **semantic_evidence,
        "personal_response_target:reason_link": "because",
        "personal_response_target:contrast_link": "but",
        "clear_relevant_english": answer,
    }
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 0.99,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": evidence_by_id[criterion["id"]],
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The response addresses the situation.",
        }
    )
    return curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )


def test_clue_choice_strong_answer_passes_real_evaluator_decision_path():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    answer = (
        "I would test the reading-room clue first because the pencil was last "
        "used in the reading room, but the art-room claim is only a guess."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "test the reading-room clue first",
            "personal_response_target:detail_2": (
                "the pencil was last used in the reading room"
            ),
            "personal_response_target:detail_3": (
                "the art-room claim is only a guess"
            ),
        },
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []
    assert "pencil was last used in the reading room" in activity[
        "passage"
    ].casefold()
    assert "notebook" not in activity["passage"].casefold()


def test_clue_choice_rejects_preference_reason_without_pencil_last_use_evidence():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    answer = (
        "I would test the reading-room clue first because I like reading, but "
        "the art-room guess sounds silly."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "test the reading-room clue first",
            "personal_response_target:detail_2": "I like reading",
            "personal_response_target:detail_3": (
                "art-room guess sounds silly"
            ),
        },
    )

    assert decision["correct"] is False, decision
    assert "semantic_required_claim_missing" in decision["blockers"]


def test_clue_choice_rejects_wrong_polarity_despite_authority_phrases():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    answer = (
        "I would test the art room first because I prefer it, but the "
        "reading-room clue first seems useless and the art-room guess is best."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "reading-room clue first",
            "personal_response_target:detail_2": "I prefer it",
            "personal_response_target:detail_3": "art-room guess is best",
        },
    )

    assert decision["correct"] is False, decision
    assert "semantic_required_claim_missing" in decision["blockers"]


def test_clue_choice_rejects_later_contradictory_art_room_choice():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    answer = (
        "I would test the reading-room clue first because the pencil was last "
        "used there, but the art-room clue is unsupported. Still, I would "
        "begin in the art room."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "test the reading-room clue first",
            "personal_response_target:detail_2": (
                "the pencil was last used there"
            ),
            "personal_response_target:detail_3": (
                "the art-room clue is unsupported"
            ),
        },
    )

    assert decision["correct"] is False, decision
    assert "authored_contradiction" in decision["blockers"]


@pytest.mark.parametrize(
    "contradictory_choice",
    (
        "I would choose the art room",
        "I would pick the art room",
        "I would select the art room",
        "I would prefer the art room",
        "I would prioritize the art room",
        "I would investigate the art room",
        "I would explore the art room",
        "I would examine the art room",
        "I would begin in the art room",
        "I will start in art room",
        "I should check the art room",
        "I could search art room",
        "I can look in the art room",
        "I might go to art room",
        "I would go straight to the art room",
        "I may head to the art room",
        "I'd try art room",
        "I'll test the art room",
        "We would visit the art room",
        "I would inspect the art room",
        "I would follow the art-room clue",
        "I would take the art-room clue",
        "I would opt for the art room",
    ),
)
def test_clue_choice_rejects_natural_art_room_choice_verbs(
    contradictory_choice,
):
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    answer = (
        "I would test the reading-room clue first because the pencil was last "
        "used there, but the art-room clue is unsupported. Still, "
        f"{contradictory_choice}."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "test the reading-room clue first",
            "personal_response_target:detail_2": (
                "the pencil was last used there"
            ),
            "personal_response_target:detail_3": (
                "the art-room clue is unsupported"
            ),
        },
    )

    assert decision["correct"] is False, (contradictory_choice, decision)
    assert "authored_contradiction" in decision["blockers"]


@pytest.mark.parametrize(
    "rejected_choice",
    (
        "I would not pick the art room",
        "I would never select the art-room clue",
        "I refuse to visit the art room",
        "I reject the idea that we should search the art room",
        "I dismiss the suggestion to inspect the art room",
        "I oppose trying the art room",
    ),
)
def test_clue_choice_allows_negated_or_rejected_art_room_actions(
    rejected_choice,
):
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:independent_application:v4"
    )
    answer = (
        "I would test the reading-room clue first because the pencil was last "
        "used there, but the art-room clue is unsupported. Also, "
        f"{rejected_choice}."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "test the reading-room clue first",
            "personal_response_target:detail_2": (
                "the pencil was last used there"
            ),
            "personal_response_target:detail_3": (
                "the art-room clue is unsupported"
            ),
        },
    )

    assert decision["correct"] is True, (rejected_choice, decision)
    assert decision["blockers"] == []


def test_kind_humour_strong_answer_passes_real_evaluator_decision_path():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The moment is funny because Kabir is already holding the pencil he is "
        "searching for, but I would not mock him."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": (
                "already holding the pencil he is searching for"
            ),
            "personal_response_target:detail_2": "would not mock him",
        },
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_kind_humour_accepts_explicit_helping_response():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The mix-up is funny because Kabir is holding the pencil while "
        "searching for it, but I would help him notice the pencil."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": (
                "holding the pencil while searching for it"
            ),
            "personal_response_target:detail_2": (
                "help him notice the pencil"
            ),
        },
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_kind_humour_accepts_affirmative_kind_explanation():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The mix-up is funny because Kabir is holding the pencil while "
        "searching, but I would explain kindly."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "holding the pencil while searching",
            "personal_response_target:detail_2": "I would explain kindly",
        },
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_kind_humour_rejects_help_phrase_inside_never_negation():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The mix-up is funny because Kabir is holding the pencil while "
        "searching, but I would never help him notice it."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "holding the pencil while searching",
            "personal_response_target:detail_2": "help him notice it",
        },
    )

    assert decision["correct"] is False, decision
    assert "authored_contradiction" in decision["blockers"]


@pytest.mark.parametrize(
    "hostile_response",
    (
        "I would not help him notice the pencil",
        "I wouldn't help him notice it",
        "I would give no help to him",
        "I decline to help him notice the pencil",
        "I refuse to help him notice it",
        "I refuse ever to help him notice the pencil",
        "I refuse under any circumstance now or ever to help him",
        "I never intend to help him notice the pencil",
        "I do not think that we should help him notice it",
        "I would avoid helping him notice the pencil",
        "I would rather not help him notice the pencil",
        "I cannot help him notice the pencil",
        "I would continue without helping him notice it",
        "I continue without choosing to help him notice the pencil",
        "I would not point out the pencil to him",
        "I refuse to show him the pencil",
        "I would continue without guiding him",
        "I would help him notice it and ridicule him",
        "I would help him notice it and tease him",
        "I would never treat him kindly",
        "I wouldn't explain kindly",
        "I refuse to be kind to him",
        "I would respond without kindness",
        "I would never respond kindly",
    ),
)
def test_kind_humour_rejects_negated_refused_or_hostile_responses(
    hostile_response,
):
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The mix-up is funny because Kabir is holding the pencil while "
        f"searching, but {hostile_response}."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "holding the pencil while searching",
            "personal_response_target:detail_2": answer,
        },
    )

    assert decision["correct"] is False, (hostile_response, decision)
    assert "authored_contradiction" in decision["blockers"]


@pytest.mark.parametrize(
    "support_response",
    (
        "I would help him notice the pencil",
        "I would explain kindly",
        "I would point out the pencil to him",
        "I would point him to the pencil",
        "I would show him the pencil",
        "I would show the pencil to him",
        "I would guide him to notice the pencil",
        "I would guide Kabir toward the pencil",
        "without hesitation I would help him",
        "without delay I would guide him",
        (
            "I would not point it out in front of everyone, but I would help "
            "him notice the pencil quietly"
        ),
        "I would not mock him",
        "I would not make fun of him",
    ),
)
def test_kind_humour_allows_support_or_explicit_no_mocking(
    support_response,
):
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The mix-up is funny because Kabir is holding the pencil while "
        f"searching for it, but {support_response}."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": (
                "holding the pencil while searching for it"
            ),
            "personal_response_target:detail_2": support_response,
        },
    )

    assert decision["correct"] is True, (support_response, decision)
    assert decision["blockers"] == []


def test_kind_humour_rejects_mockery_when_model_overgrades_embarrassment():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The moment is funny because Kabir is holding the pencil while "
        "searching, but I would mock him for looking embarrassed."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "holding the pencil",
            "personal_response_target:detail_2": "embarrassed",
        },
    )

    assert decision["correct"] is False, decision
    assert "semantic_required_claim_missing" in decision["blockers"]


def test_kind_humour_rejects_kind_phrase_inside_explicit_negation():
    activity = _personal_response_variant(
        "papas_spectacles_personal_response:review:v2"
    )
    answer = (
        "The mix-up is funny because Kabir is holding the pencil while "
        "searching, but I would not be kind to him."
    )

    decision = _model_overgraded_decision(
        activity,
        answer,
        {
            "personal_response_target": "holding the pencil while searching",
            "personal_response_target:detail_2": "not be kind to him",
        },
    )

    assert decision["correct"] is False, decision
    assert "semantic_required_claim_missing" in decision["blockers"]
    assert "authored_contradiction" in decision["blockers"]


def test_transfer_accepts_the_contextually_clear_label_paraphrase():
    level = _level(_chapter(), "papas_spectacles_poem_comprehension")
    activity = next(
        item
        for item in _phase_variants(level, "transfer")
        if item["passage"].startswith("A gardener looks for the seed label")
    )
    activity = {
        **activity,
        "activity_id": "class5-gold:transfer:gardener",
        "skill_ids": list(activity["knowledge_components"]),
    }
    detail_slot = next(
        slot
        for slot in activity["concept_slots"]
        if slot["id"] == "poem_comprehension_target:detail_2"
    )
    assert detail_slot["any_of"] == ["seed label", "label"]

    answer = (
        "The gardener should check the soil beside the row because that is "
        "where the label was pushed in. The last stated action gives the "
        "strongest clue to its location."
    )
    evidence_quotes = {
        "poem_comprehension_target": (
            "The gardener should check the soil beside the row"
        ),
        "poem_comprehension_target:detail_2": "the seed label",
        "clear_relevant_english": (
            "The last stated action gives the strongest clue to its location"
        ),
    }
    raw = SchoolRubricEvaluation.model_validate({
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 1.0,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": True,
                "quality": 1.0,
                "evidence_quote": evidence_quotes[criterion["id"]],
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The place and reason are supported.",
    })

    traceable = open_answer_ai._downgrade_untraceable_evidence(
        raw,
        answer,
        activity,
    )
    decision = curriculum.decide_open_answer_evaluation(
        activity,
        traceable,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_personal_response_accepts_give_as_a_safe_action_paraphrase():
    level = _level(_chapter(), "papas_spectacles_personal_response")
    activity = next(
        item
        for item in _phase_variants(level, "independent_application")
        if item["passage"]
        == "A water bottle has no name label and was found near the stairs."
    )
    activity = {
        **activity,
        "activity_id": "class5-gold:personal-response:water-bottle",
        "skill_ids": list(activity["knowledge_components"]),
    }
    answer = (
        "I would give the bottle to a teacher because its owner may be looking "
        "for it, but I would not open or keep it."
    )
    raw = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.78,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"]
                    != "personal_response_target:detail_2",
                    "quality": (
                        0.0
                        if criterion["id"] == "personal_response_target:detail_2"
                        else 0.9
                    ),
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The response gives a safe action and limit.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        raw,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_personal_response_review_accepts_contextual_last_used_route_paraphrase():
    level = _level(_chapter(), "papas_spectacles_personal_response")
    activity = _phase_variants(level, "review")[0]
    activity = {
        **activity,
        "activity_id": "class5-gold:personal-response:review-route",
        "skill_ids": list(activity["knowledge_components"]),
    }
    answer = (
        "I would retrace their recent route because the last-used places provide "
        "better clues, but I would not keep checking the same drawer."
    )
    raw = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.8,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"]
                    != "personal_response_target:detail_2",
                    "quality": (
                        0.0
                        if criterion["id"] == "personal_response_target:detail_2"
                        else 1.0
                    ),
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The response proposes a focused search plan.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        raw,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_sound_lab_review_accepts_plain_language_definition_of_night():
    level = _level(_chapter(), "papas_spectacles_sound_lab")
    activity = _phase_variants(level, "review")[0]
    activity = {
        **activity,
        "activity_id": "class5-gold:sound-lab:review-night",
        "skill_ids": list(activity["knowledge_components"]),
    }
    answer = (
        "Right and night share -ight but begin with different letters. Right "
        "means correct, while night is the dark part of the day. Meera chose "
        "the right answer after checking her work."
    )
    missed_id = "sound_lab_review_v1_second_meaning"
    raw = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.8,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"] != missed_id,
                    "quality": 0.0 if criterion["id"] == missed_id else 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The pattern and both meanings are clear.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        raw,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_chapter_check_accepts_teacher_or_lost_and_found_as_safe_handoff():
    item = next(
        item
        for item in _chapter()["chapter_assessment"]["items"]
        if item["item_id"]
        == "eng_c5_ch01:form_a:15:writing_short_answer"
    )
    activity = {**item, "activity_id": item["item_id"]}
    answer = (
        "I would give the pouch to the teacher or lost-and-found instead of "
        "opening it. I would mention the rocket patch so the owner can identify it."
    )
    missed_id = "writing_short_answer_evidence:detail_2"
    raw = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.75,
            "confidence": 0.9,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"] != missed_id,
                    "quality": 0.0 if criterion["id"] == missed_id else 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The response uses a safe handoff.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        raw,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_chapter_check_accepts_returned_it_as_gave_it_back_paraphrase():
    item = next(
        item
        for item in _chapter()["chapter_assessment"]["items"]
        if item["item_id"]
        == "eng_c5_ch01:form_a:16:writing_summary_own_words"
    )
    activity = {**item, "activity_id": item["item_id"]}
    answer = (
        "After losing a card, Ria retraced her steps, found it by the atlas, "
        "and returned it."
    )
    missed_id = "writing_summary_own_words_evidence:detail_2"
    raw = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.8,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"] != missed_id,
                    "quality": 0.0 if criterion["id"] == missed_id else 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The summary preserves the event sequence.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        raw,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_personal_response_semantic_slots_name_situation_content_not_answer_stems():
    level = _level(_chapter(), "papas_spectacles_personal_response")
    authored = [
        activity
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
    ]
    authored.extend(level["checks"].values())

    for activity in authored:
        if activity.get("grading_mode") != "strict_open_rubric":
            continue
        for slot in activity.get("concept_slots") or []:
            if ":detail_" not in slot["id"]:
                continue
            assert not any(
                re.match(
                    r"^(?:i|we|he|she|they)\s+"
                    r"(?:would|will|should|could)\b",
                    alias,
                    flags=re.IGNORECASE,
                )
                for alias in slot["any_of"]
            ), (activity.get("variant_id"), slot)


def test_personal_response_target_and_detail_keep_distinct_required_authority():
    level = _level(_chapter(), "papas_spectacles_personal_response")
    activities = {
        activity["variant_id"]: activity
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if activity.get("variant_id")
    }

    for variant_id in (
        "papas_spectacles_personal_response:independent_application:v4",
        "papas_spectacles_personal_response:review:v2",
    ):
        activity = activities[variant_id]
        criteria = {
            criterion["id"]: criterion
            for criterion in activity["rubric_criteria"]
        }
        slots = {
            slot["id"]: {_normalized(alias) for alias in slot["any_of"]}
            for slot in activity["concept_slots"]
        }

        assert criteria["personal_response_target"]["required"] is True
        assert criteria["personal_response_target:detail_2"]["required"] is True
        assert slots["personal_response_target"].isdisjoint(
            slots["personal_response_target:detail_2"]
        ), variant_id


def test_chapter_one_hides_platform_language_and_uses_plausible_main_idea_choices():
    chapter = _chapter()
    learner_keys = {
        "teaching_block",
        "passage",
        "prompt",
        "teaching_goal",
        "title",
        "focus",
    }

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in learner_keys and isinstance(value, str):
                    lowered = value.casefold()
                    assert not any(term in lowered for term in INTERNAL_LEARNER_TERMS)
                else:
                    visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(chapter)
    options = {
        option
        for item in chapter["chapter_assessment"]["items"]
        for option in item["options"]
    }
    assert "Paint trays should be blue." not in options
    assert "Leaf trays should be locked." not in options


def test_chapter_one_accounts_for_every_official_learning_section():
    chapter = _chapter()
    anchors = {
        anchor["anchor_id"].rsplit(":", 1)[-1]: anchor
        for anchor in chapter["source_anchors"]
    }

    assert set(anchors) == EXPECTED_SOURCE_SECTIONS
    assert anchors["recitation"]["coverage_treatment"] == (
        "offline_group_activity"
    )
    assert anchors["speaking_language_words"]["coverage_treatment"] == (
        "offline_group_activity"
    )
    assert anchors["listening_sound_pairs"]["coverage_treatment"] == "guided_only"
    assert anchors["visual_play"]["coverage_treatment"] == "optional_creative"
    assert anchors["riddle"]["coverage_treatment"] == "optional_creative"
    assert all(
        not anchors[suffix]["required_for_chapter_certification"]
        for suffix in NON_CERTIFYING_ANCHOR_SUFFIXES
    )

    covered = {
        anchor_id
        for level in chapter["levels"]
        for anchor_id in level["source_anchor_ids"]
    }
    required = {
        anchor["anchor_id"]
        for anchor in chapter["source_anchors"]
        if anchor["required_for_chapter_certification"]
    }
    assert required <= covered


def test_chapter_one_uses_complete_activity_v2_teaching_cycles():
    chapter_model = load_live_chapter_file(CHAPTER_PATH)
    chapter = chapter_model.runtime_dict()
    phases = (
        "connect",
        "co_construct",
        "guided_practice",
        "independent_application",
        "transfer",
        "review",
    )

    assert tuple(level["level_id"] for level in chapter["levels"]) == (
        EXPECTED_LEVEL_IDS
    )
    assert {
        "comprehension_studio",
        "language_lab",
        "expression_workshop",
        "application_mission",
    } <= {level["episode_kind"] for level in chapter["levels"]}
    assert _launch_level_count_is_valid(chapter_model)

    for level in chapter["levels"]:
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps if step["required"]) == phases
        for step in steps:
            activities = (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
            for activity in activities:
                assert activity["schema_version"] == "school-activity-v2"
                assert activity["source_anchor_ids"]
                if not activity["knowledge_components"]:
                    assert activity["evidence_role"] == "experience"
                if activity["interaction_type"] != "continue":
                    assert activity["grading_mode"] in {
                        "selected_option",
                        "exact_text",
                        "punctuation_symbol",
                        "ordered_slots",
                        "strict_open_rubric",
                    }
                if activity["evidence_role"] == "certifying":
                    assert activity["certifying_language"] == "en"
                    assert not {
                        anchor_id.rsplit(":", 1)[-1]
                        for anchor_id in activity["source_anchor_ids"]
                    }.intersection(NON_CERTIFYING_ANCHOR_SUFFIXES)
            if step["phase"] in {
                "independent_application",
                "transfer",
                "review",
            }:
                assert "variant_pool" in step
                assert len(step["variant_pool"]) >= 3


def test_chapter_one_adds_banded_taxonomy_without_false_modality_certification():
    chapter = _chapter()
    taxonomy = locked_english_taxonomy()
    taught_skills = {
        skill_id for level in chapter["levels"] for skill_id in level["skill_ids"]
    }

    assert NEW_TAXONOMY_SKILLS <= taxonomy.skill_ids()
    for skill_id in NEW_TAXONOMY_SKILLS:
        entry = taxonomy.get(skill_id)
        assert entry.class_min <= 5 <= entry.class_max
        assert all(
            prerequisite in taxonomy.skill_ids()
            for prerequisite in entry.prerequisite_skill_ids
        )
    assert "speaking.recitation" not in taught_skills
    assert "speaking.multilingual_expression" not in taught_skills
    assert "listening.sound_discrimination" not in taught_skills


def test_chapter_one_assessment_is_deep_and_source_grounded():
    chapter = _chapter()
    assessment = chapter["chapter_assessment"]
    taught_skills = {
        skill_id for level in chapter["levels"] for skill_id in level["skill_ids"]
    }

    assert len(assessment["items"]) >= 24
    assert assessment["items_per_attempt"] >= 12
    assert assessment["max_attempts"] >= 2
    assert all(item["skill_ids"] for item in assessment["items"])
    assert {
        skill_id
        for item in assessment["items"]
        for skill_id in item["skill_ids"]
    } == taught_skills
    assert sum(
        item.get("grading_mode") == "strict_open_rubric"
        for item in assessment["items"]
    ) >= 4
    form_a_signatures = {
        (item["passage"], item["prompt"])
        for item in assessment["items"]
        if ":form_a:" in item["item_id"]
    }
    form_b_signatures = {
        (item["passage"], item["prompt"])
        for item in assessment["items"]
        if ":form_b:" in item["item_id"]
    }
    assert form_a_signatures.isdisjoint(form_b_signatures)
    assert chapter["content_version"] == "2026-07-17.ch1-gold.15"
    assert chapter["certification_version"] == "2026-07-17.ch1-gold.13"


def test_semantic_contract_version_bump_invalidates_pre_validator_session():
    chapter = _chapter()
    session = {
        "subject_id": "english",
        "class_no": 5,
        "state_json": {
            "subject_id": "english",
            "target_class_no": 5,
            "chapter": {
                "chapter_id": chapter["chapter_id"],
                "content_version": "2026-07-16.ch1-gold.14",
            },
        },
    }

    assert curriculum.session_content_version_is_current(session) is False
    session["state_json"]["chapter"]["content_version"] = chapter[
        "content_version"
    ]
    assert curriculum.session_content_version_is_current(session) is True


def test_chapter_one_strict_open_items_have_authored_grading_authority():
    chapter = _chapter()
    strict_activities = [
        activity
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if activity.get("grading_mode") == "strict_open_rubric"
    ]
    strict_checks = [
        check
        for level in chapter["levels"]
        for check in level["checks"].values()
        if check.get("grading_mode") == "strict_open_rubric"
    ]
    strict_assessment_items = [
        item
        for item in chapter["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    ]

    assert strict_activities
    assert strict_assessment_items
    strict_authored = [
        *strict_activities,
        *strict_checks,
        *strict_assessment_items,
    ]
    for authored in strict_authored:
        relevance_terms = authored.get("relevance_terms") or []
        forbidden_phrases = authored.get("forbidden_phrases") or []
        assert len(relevance_terms) >= 3
        assert len(relevance_terms) == len(set(relevance_terms))
        assert len(forbidden_phrases) >= 2
        assert len(forbidden_phrases) == len(set(forbidden_phrases))
        assert all(len(phrase.split()) >= 3 for phrase in forbidden_phrases)
        assert forbidden_phrases != ["I do not know"]
        model_answer = authored.get("model_answer") or ""
        assert model_answer
        assert len(model_answer.split()) >= authored["min_response_words"]
        assert any(
            term.casefold() in model_answer.casefold()
            for term in relevance_terms
        )
        assert not any(
            phrase.casefold() in model_answer.casefold()
            for phrase in forbidden_phrases
        )

    model_answers = [authored["model_answer"] for authored in strict_authored]
    assert len(model_answers) == len(set(model_answers))

    activity_guard_sets = {
        tuple(activity["forbidden_phrases"])
        for activity in [*strict_activities, *strict_checks]
    }
    assert len(activity_guard_sets) >= len(EXPECTED_LEVEL_IDS)
    assert "model_answer" in LiveChapterAssessmentItem.model_fields


def test_chapter_one_all_certifying_open_work_has_semantic_authority():
    chapter = _chapter()
    certifying = [
        activity
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if activity.get("grading_mode") == "strict_open_rubric"
        and activity.get("evidence_role") == "certifying"
    ]
    certifying.extend(
        check
        for level in chapter["levels"]
        for check in level["checks"].values()
        if check.get("grading_mode") == "strict_open_rubric"
        and check.get("evidence_role") == "certifying"
    )
    certifying.extend(
        item
        for item in chapter["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    )

    assert len(certifying) == 110
    for authored in certifying:
        slots = authored.get("concept_slots") or []
        criterion_ids = {
            criterion["id"] for criterion in authored["rubric_criteria"]
        }
        assert slots, authored.get("variant_id", authored.get("item_id"))
        assert len({slot["id"] for slot in slots}) == len(slots)
        assert {slot["id"] for slot in slots} <= criterion_ids
        assert all(slot["any_of"] for slot in slots)


def test_chapter_one_wrong_glanced_meaning_cannot_certify_when_model_overgrades():
    chapter = _chapter()
    activity = next(
        item
        for item in chapter["chapter_assessment"]["items"]
        if item["item_id"] == "eng_c5_ch01:form_a:11:vocab_chapter_word_usage"
    )
    answer = (
        "I glanced at the football loudly because glanced means shouting at "
        "it every morning."
    )
    evidence_by_id = {
        "vocab_target_word": "glanced",
        "vocab_meaning_context": "glanced means shouting",
        "clear_relevant_english": answer,
    }
    payload = {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["item_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.95,
        "confidence": 0.99,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": True,
                "quality": 0.95,
                "evidence_quote": evidence_by_id[criterion["id"]],
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The sentence uses the target word.",
    }

    validated = validate_school_open_evaluation(
        payload,
        context=school_open_context_from_activity(activity, answer),
    )

    assert "authored_contradiction" in validated.effective_blockers
    assert validated.certification_eligible is False


def test_chapter_one_form_b_preposition_item_keeps_one_visible_referent_set():
    chapter = _chapter()
    item = next(
        item
        for item in chapter["chapter_assessment"]["items"]
        if item["item_id"] == "eng_c5_ch01:form_b:02:grammar_prepositions"
    )

    visible = f"{item['passage']} {item['prompt']}".casefold()
    assert "blue card" in visible
    assert "two red cards" in visible
    assert "bus token" not in visible


def test_chapter_one_has_global_freshness_for_every_teaching_candidate():
    chapter = _chapter()
    all_candidates = []
    strong_path = []
    for level in chapter["levels"]:
        for step in level["teaching_steps"]:
            candidates = (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
            all_candidates.extend(candidates)
            strong_path.append(candidates[0])

    def normalized(value: str) -> str:
        return " ".join(value.split()).casefold()

    def duplicates(key: str, candidates: list[dict]) -> dict[str, int]:
        counts = Counter(normalized(candidate[key]) for candidate in candidates)
        return {value: count for value, count in counts.items() if count > 1}

    assert len(all_candidates) == 162
    assert len(strong_path) == 54
    assert duplicates("passage", all_candidates) == {}
    assert duplicates("prompt", all_candidates) == {}
    assert duplicates("passage", strong_path) == {}
    assert duplicates("prompt", strong_path) == {}

    all_servables = [*all_candidates]
    all_servables.extend(
        check
        for level in chapter["levels"]
        for check in level["checks"].values()
    )
    all_servables.extend(chapter["chapter_assessment"]["items"])
    assert len(all_servables) == 267
    assert duplicates("passage", all_servables) == {}
    assert duplicates("prompt", all_servables) == {}


def test_ordered_tasks_show_scrambled_material_to_the_learner():
    chapter = _chapter()
    ordered_tasks = [
        activity
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if activity.get("grading_mode") == "ordered_slots"
    ]
    ordered_tasks.extend(
        item
        for item in chapter["chapter_assessment"]["items"]
        if item.get("grading_mode") == "ordered_slots"
    )

    assert ordered_tasks
    for task in ordered_tasks:
        slots = {slot["id"]: slot for slot in task["concept_slots"]}
        ordered_answers = [
            slots[slot_id]["any_of"][0]
            for slot_id in task["ordered_concept_slot_ids"]
        ]
        visible = _normalized(
            " ".join(
                [task["passage"], task["prompt"], *task.get("options", [])]
            )
        )
        positions = [visible.find(_normalized(answer)) for answer in ordered_answers]

        assert all(position >= 0 for position in positions), task.get(
            "variant_id", task.get("item_id")
        )
        assert positions != sorted(positions), task.get(
            "variant_id", task.get("item_id")
        )


def test_first_high_evidence_variants_cover_every_declared_level_skill():
    chapter = _chapter()

    for level in chapter["levels"]:
        first_path_skills = {
            skill_id
            for phase in ("independent_application", "transfer", "review")
            for skill_id in _phase_variants(level, phase)[0][
                "knowledge_components"
            ]
        }
        assert set(level["skill_ids"]) <= first_path_skills, level["level_id"]


def test_guided_bridge_masterclass_and_revision_checks_are_fresh_work():
    chapter = _chapter()
    support_names = (
        "guided_check",
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )

    for level in chapter["levels"]:
        teaching = [
            activity
            for step in level["teaching_steps"]
            for activity in (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
        ]
        teaching_answers = {
            _normalized(answer)
            for activity in teaching
            for answer in activity.get("accepted_answers", [])
        }
        checks = [level["checks"][name] for name in support_names]
        support_answers = [
            _normalized(
                check["accepted_answers"][0]
                if check.get("accepted_answers")
                else check["model_answer"]
            )
            for check in checks
        ]

        assert all(
            masterclass._authored_check_is_evaluable(check) for check in checks
        )
        assert len(support_answers) == len(set(support_answers)), level[
            "level_id"
        ]
        assert teaching_answers.isdisjoint(support_answers), level["level_id"]

        for check in checks:
            check_passage = _normalized(check["passage"])
            for activity in teaching:
                teaching_passage = _normalized(activity["passage"])
                if len(teaching_passage.split()) >= 5:
                    assert teaching_passage not in check_passage, level[
                        "level_id"
                    ]


def test_language_labs_assess_the_claimed_constructs_without_false_modality():
    chapter = _chapter()
    spelling = _level(chapter, "papas_spectacles_spelling_and_opposites")
    for phase in ("independent_application", "transfer", "review"):
        for activity in _phase_variants(spelling, phase):
            if "vocab.spelling" not in activity["knowledge_components"]:
                continue
            answer = activity["accepted_answers"][0]
            assert "rewrite" in activity["prompt"].casefold()
            assert "spelling" in activity["prompt"].casefold()
            assert answer.casefold() not in activity["passage"].casefold()

    prepositions = _level(chapter, "papas_spectacles_prepositions")
    v2_passages = {
        phase: next(
            activity
            for activity in _phase_variants(prepositions, phase)
            if activity["variant_id"].endswith(":v2")
        )["passage"].casefold()
        for phase in ("independent_application", "transfer", "review")
    }
    assert "one red book on each side" in v2_passages["independent_application"]
    assert "started at the east bank" in v2_passages["transfer"]
    assert "reached the west bank" in v2_passages["transfer"]
    assert "covered the note completely" in v2_passages["review"]

    sound_lab = _level(chapter, "papas_spectacles_sound_lab")
    for phase in ("independent_application", "transfer", "review"):
        for activity in _phase_variants(sound_lab, phase):
            if not activity["variant_id"].endswith((":v3", ":v4")):
                continue
            assert activity["grading_mode"] == "strict_open_rubric"
            assert "use" in activity["prompt"].casefold()
            assert "complete sentence" in activity["prompt"].casefold()
            assert "vocab.chapter_word_usage" in activity[
                "knowledge_components"
            ]
            assert len(activity["model_answer"].split()) >= activity[
                "min_response_words"
            ]

    claimed_level_anchors = {
        anchor_id
        for level in chapter["levels"]
        for anchor_id in level["source_anchor_ids"]
    }
    claimed_activity_anchors = {
        anchor_id
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        for anchor_id in activity["source_anchor_ids"]
    }
    assert "eng_c5_ch01:recitation" not in claimed_level_anchors
    assert "eng_c5_ch01:visual_play" not in claimed_level_anchors
    assert "eng_c5_ch01:recitation" not in claimed_activity_anchors
    assert "eng_c5_ch01:visual_play" not in claimed_activity_anchors


def test_sound_lab_integrates_written_patterns_with_meaning_in_context():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_sound_lab")
    guided_skills = {"vocab.spelling", "reading.word_meaning_context"}
    certifying_skills = {
        "vocab.spelling",
        "reading.word_meaning_context",
        "vocab.chapter_word_usage",
    }

    assert set(level["skill_ids"]) == certifying_skills

    guided = _phase_variants(level, "guided_practice")
    assert len(guided) == 4
    for activity in guided:
        assert set(activity["knowledge_components"]) == guided_skills
        assert activity["grading_mode"] == "selected_option"
        assert "written pattern" in activity["prompt"].casefold()
        assert "meaning" in activity["prompt"].casefold()
        supported = activity["accepted_answers"][0].casefold()
        assert "means" in supported
        assert any(comparison in supported for comparison in ("share", "differ"))

    honesty = next(
        activity
        for activity in guided
        if activity["variant_id"].endswith(":v4")
    )
    assert "printed text does not prove pronunciation" in honesty[
        "accepted_answers"
    ][0].casefold()

    for phase in ("independent_application", "transfer", "review"):
        variants = _phase_variants(level, phase)
        assert len(variants) == 4
        for activity in variants:
            assert set(activity["knowledge_components"]) == certifying_skills
            assert activity["grading_mode"] == "strict_open_rubric"
            assert activity["interaction_type"] == "paragraph_text"
            assert activity["accepted_answers"] == []
            assert "_" not in activity["passage"]
            prompt = activity["prompt"].casefold()
            assert "explain" in prompt or (
                "sentence" in prompt
                and any(kind in prompt for kind in ("new", "original"))
            )
            criterion_ids = {
                criterion["id"] for criterion in activity["rubric_criteria"]
            }
            assert any("pattern" in criterion_id for criterion_id in criterion_ids)
            assert any(
                "first_meaning" in criterion_id
                for criterion_id in criterion_ids
            )
            assert any(
                "second_meaning" in criterion_id
                for criterion_id in criterion_ids
            )

    transfer_text = _normalized(
        " ".join(
            activity["passage"]
            for activity in _phase_variants(level, "transfer")
        )
    )
    non_transfer_text = _normalized(
        " ".join(
            activity["passage"]
            for phase in (
                "guided_practice",
                "independent_application",
                "review",
            )
            for activity in _phase_variants(level, phase)
        )
    )
    for new_pair in (
        "plain and plane",
        "brain and grain",
        "coach and roach",
        "flight and slight",
    ):
        assert new_pair in transfer_text
        assert new_pair not in non_transfer_text

    for check_name in ("independent_check", "transfer_check"):
        check = level["checks"][check_name]
        assert set(check["knowledge_components"]) == certifying_skills
        assert check["grading_mode"] == "strict_open_rubric"
        assert "_" not in check["passage"]
        assert "explain" in check["prompt"].casefold()
        assert "new complete sentence" in check["prompt"].casefold()
        criterion_ids = {
            criterion["id"] for criterion in check["rubric_criteria"]
        }
        assert any("pattern" in criterion_id for criterion_id in criterion_ids)
        assert any(
            "first_meaning" in criterion_id for criterion_id in criterion_ids
        )
        assert any(
            "second_meaning" in criterion_id for criterion_id in criterion_ids
        )


def test_named_review_conflicts_are_resolved_and_inference_uses_two_clues():
    chapter = _chapter()
    prepositions = _level(chapter, "papas_spectacles_prepositions")
    for check_name in ("independent_check", "transfer_check"):
        check = prepositions["checks"][check_name]
        assert "complete sentence" in check["prompt"].casefold()
        assert "which preposition" not in check["prompt"].casefold()

    chapter_words = _level(chapter, "papas_spectacles_chapter_words")
    word_transfer = chapter_words["checks"]["transfer_check"]
    assert "mechanic" not in word_transfer["model_answer"].casefold()
    assert "cart" not in word_transfer["model_answer"].casefold()
    assert "strolled" in word_transfer["model_answer"].casefold()

    poem_story = _level(chapter, "papas_spectacles_poem_to_story")
    assert poem_story["checks"]["revision_level_1"]["knowledge_components"] == [
        "grammar.tense_usage",
        "writing.complete_sentence",
    ]
    poem_transfer = _phase_variants(poem_story, "transfer")[0]
    assert "recovered" not in poem_transfer["model_answer"].casefold()
    assert "took it down" not in poem_transfer["model_answer"].casefold()

    visual_riddle = _level(
        chapter, "papas_spectacles_visual_fun_and_riddle"
    )
    visual_transfer = _phase_variants(visual_riddle, "transfer")[2]
    assert "now" in visual_transfer["passage"].casefold()
    assert "moved" in visual_transfer["model_answer"].casefold()

    assessment_by_id = {
        item["item_id"]: item for item in chapter["chapter_assessment"]["items"]
    }
    summary = assessment_by_id[
        "eng_c5_ch01:form_a:16:writing_summary_own_words"
    ]
    assert _word_ngrams(summary["passage"], 4).isdisjoint(
        _word_ngrams(summary["model_answer"], 4)
    )

    for item_id in (
        "eng_c5_ch01:form_a:05:reading_inference_reason",
        "eng_c5_ch01:form_b:05:reading_inference_reason",
    ):
        item = assessment_by_id[item_id]
        assert "two clues" in item["prompt"].casefold()
        assert "infer" in item["prompt"].casefold()
        assert "two" in item["rubric_criteria"][0]["description"].casefold()
        assert "clue" in item["rubric_criteria"][0]["description"].casefold()


def test_attribute_ordering_supplies_visible_facts_for_one_defensible_order():
    chapter = _chapter()
    ordering = _level(chapter, "papas_spectacles_order_and_pairs")
    ordered_activities = [
        activity
        for step in ordering["teaching_steps"]
        for activity in (
            [step["activity"]] if "activity" in step else step["variant_pool"]
        )
        if activity.get("grading_mode") == "ordered_slots"
    ]
    ordered_assessment = [
        item
        for item in chapter["chapter_assessment"]["items"]
        if "vocab.attribute_ordering" in item["skill_ids"]
    ]

    for task in [*ordered_activities, *ordered_assessment]:
        ordered_slots = list(task["ordered_concept_slot_ids"])
        visible_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", task["passage"])
        assert len(visible_numbers) >= len(ordered_slots), task.get(
            "variant_id", task.get("item_id")
        )

    for check_name in ("independent_check", "transfer_check"):
        check = ordering["checks"][check_name]
        assert len(re.findall(r"\b\d+(?:\.\d+)?\b", check["passage"])) >= 3
        for term in check["relevance_terms"]:
            assert term.casefold() in (
                check["passage"] + " " + check["prompt"]
            ).casefold()


def test_reviewed_single_choice_items_have_one_passage_supported_answer():
    chapter = _chapter()
    comprehension = _level(chapter, "papas_spectacles_poem_comprehension")
    humour = next(
        activity
        for activity in _phase_variants(comprehension, "guided_practice")
        if activity["variant_id"].endswith(":v4")
    )
    assert humour["accepted_answers"] == [
        "explain that the cook is holding the bowl with the spoon while searching"
    ]
    assert all(
        "cook" in option.casefold() and "spoon" in option.casefold()
        for option in humour["options"]
    )

    sound = _level(chapter, "papas_spectacles_sound_lab")
    sound_choice = next(
        step["activity"]
        for step in sound["teaching_steps"]
        if step["phase"] == "co_construct"
    )
    assert sound_choice["accepted_answers"] == [
        "coat and goat have different first letters"
    ]
    assert all(
        "coat" in option.casefold() and "goat" in option.casefold()
        for option in sound_choice["options"]
    )


def test_named_prompt_model_and_relation_authority_are_aligned():
    chapter = _chapter()
    chapter_words = _level(chapter, "papas_spectacles_chapter_words")
    glanced = next(
        item
        for item in _phase_variants(chapter_words, "review")
        if item["variant_id"].endswith(":v1")
    )
    assert "use glanced" in glanced["prompt"].casefold()
    assert "new sentence" in glanced["prompt"].casefold()
    assert glanced["model_answer"].casefold().count("glanced") >= 2

    prepositions = _level(chapter, "papas_spectacles_prepositions")
    relation = next(
        item
        for item in _phase_variants(prepositions, "review")
        if item["variant_id"].endswith(":v1")
    )
    assert "directly beside" in relation["passage"].casefold()
    assert set(relation["accepted_answers"]) == {"beside", "next to"}

    visual = _level(chapter, "papas_spectacles_visual_fun_and_riddle")
    bookmark = next(
        item
        for item in _phase_variants(visual, "transfer")
        if item["variant_id"].endswith(":v4")
    )
    assert "bookmark is missing" in bookmark["passage"].casefold()
    assert "lies on the desk" not in bookmark["passage"].casefold()
    assert "between its pages" in bookmark["model_answer"].casefold()


def test_connector_certification_requires_because_and_but_production():
    chapter = _chapter()
    personal_response = _level(chapter, "papas_spectacles_personal_response")
    certifying = [
        activity
        for phase in ("independent_application", "transfer", "review")
        for activity in _phase_variants(personal_response, phase)
        if "grammar.connectors_because_and_but"
        in activity["knowledge_components"]
    ]

    assert certifying
    for activity in certifying:
        assert "because" in activity["prompt"].casefold()
        assert "but" in activity["prompt"].casefold()
        assert "because" in activity["model_answer"].casefold()
        assert "but" in activity["model_answer"].casefold()
        assert "because" in activity["rubric_criteria"][0][
            "description"
        ].casefold()
        assert "but" in activity["rubric_criteria"][0][
            "description"
        ].casefold()

    connector_assessment = [
        item
        for item in chapter["chapter_assessment"]["items"]
        if "grammar.connectors_because_and_but" in item["skill_ids"]
    ]
    assert connector_assessment
    for item in connector_assessment:
        assert "because" in item["prompt"].casefold()
        assert "but" in item["prompt"].casefold()
        assert "because" in item["model_answer"].casefold()
        assert "but" in item["model_answer"].casefold()


def test_personal_response_guided_route_item_has_one_evidence_backed_answer():
    chapter = _chapter()
    personal_response = _level(chapter, "papas_spectacles_personal_response")
    guided = next(
        item
        for item in _phase_variants(personal_response, "guided_practice")
        if item["variant_id"].endswith(":v1")
    )

    assert "cupboard" in guided["passage"].casefold()
    assert "notice board" in guided["passage"].casefold()
    assert "route" in guided["prompt"].casefold()
    assert guided["accepted_answers"] == [
        "I would retrace the route from the cupboard to the notice board "
        "because those are the last two places the learner visited."
    ]
    assert "check the stated location" not in {
        option.casefold() for option in guided["options"]
    }


def test_sound_lab_uses_child_facing_language_and_tense_repair_is_targeted():
    chapter = _chapter()
    sound = _level(chapter, "papas_spectacles_sound_lab")
    child_visible = " ".join(
        str(value)
        for step in sound["teaching_steps"]
        for activity in (
            [step["activity"]] if "activity" in step else step["variant_pool"]
        )
        for value in (
            activity.get("teaching_block", ""),
            activity.get("passage", ""),
            activity.get("prompt", ""),
            *(activity.get("options") or []),
        )
    ).casefold()
    for jargon in (
        "records no mastery",
        "facilitator",
        "certifies",
        "observable evidence",
    ):
        assert jargon not in child_visible

    poem_story = _level(chapter, "papas_spectacles_poem_to_story")
    assert "tense_shift" in poem_story["checks"]["revision_level_1"][
        "target_misconception_tags"
    ]
    assert "event_invented" in poem_story["checks"]["revision_level_2"][
        "target_misconception_tags"
    ]
    assert "sequence_lost" in poem_story["checks"]["revision_level_3"][
        "target_misconception_tags"
    ]


def test_spelling_and_sound_activities_declare_only_genuinely_assessed_skills():
    chapter = _chapter()
    spelling = _level(chapter, "papas_spectacles_spelling_and_opposites")
    sound = _level(chapter, "papas_spectacles_sound_lab")

    spelling_expected = {
        "papas_spectacles_spelling_and_opposites:co_construct": {
            "vocab.spelling"
        },
        "papas_spectacles_spelling_and_opposites:guided:v1": {
            "vocab.spelling"
        },
        "papas_spectacles_spelling_and_opposites:guided:v2": {
            "vocab.spelling"
        },
        "papas_spectacles_spelling_and_opposites:guided:v3": {
            "vocab.antonyms"
        },
        "papas_spectacles_spelling_and_opposites:guided:v4": {
            "vocab.antonyms"
        },
    }
    spelling_activities = {
        (
            activity.get("variant_id")
            or "papas_spectacles_spelling_and_opposites:co_construct"
        ): activity
        for phase in ("co_construct", "guided_practice")
        for activity in _phase_activities(spelling, phase)
    }
    assert set(spelling_activities) == set(spelling_expected)
    for activity_id, expected_skills in spelling_expected.items():
        assert set(spelling_activities[activity_id]["knowledge_components"]) == (
            expected_skills
        )

    sound_expected = {
        "papas_spectacles_sound_lab:co_construct": {"vocab.spelling"},
        "papas_spectacles_sound_lab:guided:v1": {
            "vocab.spelling",
            "reading.word_meaning_context",
        },
        "papas_spectacles_sound_lab:guided:v2": {
            "vocab.spelling",
            "reading.word_meaning_context",
        },
        "papas_spectacles_sound_lab:guided:v3": {
            "vocab.spelling",
            "reading.word_meaning_context",
        },
        "papas_spectacles_sound_lab:guided:v4": {
            "vocab.spelling",
            "reading.word_meaning_context",
        },
    }
    sound_activities = {
        (
            activity.get("variant_id")
            or "papas_spectacles_sound_lab:co_construct"
        ): activity
        for phase in ("co_construct", "guided_practice")
        for activity in _phase_activities(sound, phase)
    }
    assert set(sound_activities) == set(sound_expected)
    for activity_id, expected_skills in sound_expected.items():
        activity = sound_activities[activity_id]
        assert set(activity["knowledge_components"]) == expected_skills
        if not expected_skills:
            assert activity["evidence_role"] == "experience"


def test_spelling_and_antonym_support_metadata_targets_the_failed_skill():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_spelling_and_opposites")
    checks = level["checks"]

    spelling_checks = (
        "guided_check",
        "bridge",
        "masterclass",
        "revision_level_3",
    )
    antonym_checks = ("revision_level_1", "revision_level_2")
    for name in spelling_checks:
        assert checks[name]["knowledge_components"] == ["vocab.spelling"]
        assert checks[name]["target_misconception_tags"] == [
            "letter_order_error"
        ]
    for name in antonym_checks:
        assert checks[name]["knowledge_components"] == ["vocab.antonyms"]
        assert checks[name]["target_misconception_tags"] == [
            "related_not_opposite"
        ]

    for phase in ("independent_application", "transfer", "review"):
        for activity in _phase_variants(level, phase):
            expected_tag = (
                "letter_order_error"
                if activity["knowledge_components"] == ["vocab.spelling"]
                else "related_not_opposite"
            )
            assert activity["target_misconception_tags"] == [expected_tag]


def test_sound_support_metadata_repairs_spelling_and_word_use_separately():
    chapter = _chapter()
    checks = _level(chapter, "papas_spectacles_sound_lab")["checks"]

    for name in ("bridge", "revision_level_1"):
        assert checks[name]["knowledge_components"] == ["vocab.spelling"]
        assert checks[name]["target_misconception_tags"] == [
            "letter_pattern_missed"
        ]
    for name in ("revision_level_2", "revision_level_3"):
        assert checks[name]["knowledge_components"] == [
            "vocab.chapter_word_usage"
        ]
        assert set(checks[name]["target_misconception_tags"]) == {
            "target_word_copied_without_context",
            "word_meaning_not_demonstrated",
        }


def test_connector_assessment_literal_request_matches_the_open_rubric():
    chapter = _chapter()
    connector_items = [
        item
        for item in chapter["chapter_assessment"]["items"]
        if "grammar.connectors_because_and_but" in item["skill_ids"]
    ]

    assert len(connector_items) == 2
    for item in connector_items:
        assert item["prompt"].startswith("Write one sentence that uses because")
        assert item["grading_mode"] == "strict_open_rubric"
        assert not item["accepted_answers"]
        assert not item["options"]
        assert "because" in item["model_answer"].casefold()
        assert "but" in item["model_answer"].casefold()


def test_public_selected_options_are_stable_without_systematic_key_position():
    chapter = _chapter()
    activities: list[dict] = []
    for level in chapter["levels"]:
        for step in level["teaching_steps"]:
            activities.extend(
                [step["activity"]]
                if "activity" in step
                else step.get("variant_pool") or []
            )
        activities.extend(
            check
            for check in (level.get("checks") or {}).values()
            if isinstance(check, dict)
        )
    activities.extend(chapter["chapter_assessment"]["items"])

    keyed_positions: list[int] = []
    for index, authored in enumerate(activities):
        options = list(authored.get("options") or [])
        accepted = list(authored.get("accepted_answers") or [])
        if len(options) < 2 or not accepted:
            continue
        activity_id = str(
            authored.get("variant_id")
            or authored.get("activity_id")
            or authored.get("item_id")
            or f"chapter-one-option-{index}"
        )
        public_once = curriculum._stable_public_options(activity_id, options)
        public_twice = curriculum._stable_public_options(activity_id, options)
        assert public_once == public_twice
        assert sorted(public_once) == sorted(options)
        keyed_positions.append(public_once.index(accepted[0]))

    # Five riddle checks now require clue-justified open responses.
    assert len(keyed_positions) >= 93
    assert len(set(keyed_positions)) > 1
    assert any(position != 0 for position in keyed_positions)


def test_selected_options_never_award_production_skills():
    chapter = _chapter()
    production_skills = {
        "grammar.connectors_because_and_but",
        "grammar.sentence_order",
        "vocab.chapter_word_usage",
        "writing.complete_sentence",
        "writing.reason_answer",
        "writing.short_answer",
        "writing.summary_own_words",
    }
    authored: list[dict] = []
    for level in chapter["levels"]:
        for step in level["teaching_steps"]:
            authored.extend(
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
        authored.extend(level["checks"].values())
    authored.extend(chapter["chapter_assessment"]["items"])

    for activity in authored:
        if activity.get("grading_mode") != "selected_option":
            continue
        claimed_skills = set(
            activity.get("knowledge_components")
            or activity.get("skill_ids")
            or []
        )
        assert claimed_skills.isdisjoint(production_skills), activity.get(
            "variant_id", activity.get("item_id", activity.get("prompt"))
        )


def test_every_assessment_skill_has_matching_evaluable_authored_remediation():
    chapter = _chapter()
    eligible_kinds = (
        "bridge",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    remediation = [
        (level["level_id"], kind, level["checks"][kind])
        for level in chapter["levels"]
        for kind in eligible_kinds
    ]
    assessment_skills = {
        skill_id
        for item in chapter["chapter_assessment"]["items"]
        for skill_id in item["skill_ids"]
    }
    production_skills = {
        "grammar.connectors_because_and_but",
        "grammar.sentence_order",
        "vocab.chapter_word_usage",
        "writing.complete_sentence",
        "writing.reason_answer",
        "writing.short_answer",
        "writing.summary_own_words",
    }

    for skill_id in assessment_skills:
        candidates = [
            (level_id, kind, check)
            for level_id, kind, check in remediation
            if skill_id in check["knowledge_components"]
        ]
        assert candidates, skill_id
        assert any(
            masterclass._authored_check_is_evaluable(check)
            for _, _, check in candidates
        ), skill_id
        if skill_id in production_skills:
            assert any(
                check.get("grading_mode") == "strict_open_rubric"
                and check.get("evaluation_mode") == "llm_rubric"
                and not check.get("options")
                for _, _, check in candidates
            ), skill_id

    main_idea_candidates = [
        check
        for _, _, check in remediation
        if "reading.paragraph_main_idea" in check["knowledge_components"]
    ]
    assert main_idea_candidates
    assert all(
        "main idea" in f"{check['passage']} {check['prompt']}".casefold()
        or "main problem" in f"{check['passage']} {check['prompt']}".casefold()
        for check in main_idea_candidates
    )


def test_connector_remediation_and_assessment_require_both_connectors():
    chapter = _chapter()
    personal = _level(chapter, "papas_spectacles_personal_response")
    connector_checks = [
        personal["checks"][kind]
        for kind in (
            "bridge",
            "revision_level_1",
            "revision_level_2",
            "revision_level_3",
        )
        if "grammar.connectors_because_and_but"
        in personal["checks"][kind]["knowledge_components"]
    ]
    connector_items = [
        item
        for item in chapter["chapter_assessment"]["items"]
        if "grammar.connectors_because_and_but" in item["skill_ids"]
    ]

    assert connector_checks
    assert connector_items
    for activity in [*connector_checks, *connector_items]:
        assert activity["grading_mode"] == "strict_open_rubric"
        assert activity["evaluation_mode"] == "llm_rubric"
        assert not activity["options"]
        assert not activity["accepted_answers"]
        visible_requirement = " ".join(
            [
                activity["prompt"],
                activity["model_answer"],
                *(
                    criterion["description"]
                    for criterion in activity["rubric_criteria"]
                ),
            ]
        ).casefold()
        assert "because" in visible_requirement
        assert "but" in visible_requirement
    for check in connector_checks:
        assert {"missing_because", "missing_but"} <= set(
            check["target_misconception_tags"]
        )


def test_prompts_do_not_reveal_keys_or_require_optional_assets():
    chapter = _chapter()
    authored: list[dict] = []
    for level in chapter["levels"]:
        for step in level["teaching_steps"]:
            authored.extend(
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
        authored.extend(level["checks"].values())
    authored.extend(chapter["chapter_assessment"]["items"])

    required_asset_phrases = {
        "look at the image",
        "look at the picture",
        "listen to the audio",
        "listen to the recording",
        "watch the video",
    }
    for activity in authored:
        prompt = _normalized(activity["prompt"])
        visible_text = _normalized(
            " ".join(
                (
                    activity.get("teaching_block", ""),
                    activity.get("passage", ""),
                    activity["prompt"],
                )
            )
        )
        for accepted in activity.get("accepted_answers") or []:
            normalized_answer = _normalized(accepted)
            assert normalized_answer not in prompt, activity.get(
                "variant_id", activity.get("item_id", prompt)
            )
        assert not any(
            phrase in visible_text for phrase in required_asset_phrases
        )


def test_comprehension_transfer_changes_the_reasoning_scenario_not_only_the_nouns():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_poem_comprehension")
    transfer = next(
        step for step in level["teaching_steps"] if step["phase"] == "transfer"
    )["variant_pool"]
    passages = {item["variant_id"]: item["passage"] for item in transfer}

    assert "closed curtain" in passages[
        "papas_spectacles_poem_comprehension:transfer:v1"
    ].casefold()
    assert "gear lever" in passages[
        "papas_spectacles_poem_comprehension:transfer:v4"
    ].casefold()
    assert not any(
        phrase in " ".join(passages.values()).casefold()
        for phrase in ("bell while its ribbon", "gloves while they hang")
    )


def test_riddle_model_and_learner_checks_are_distinct_and_clue_justified():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_visual_fun_and_riddle")
    connect = next(
        step["activity"]
        for step in level["teaching_steps"]
        if step["phase"] == "connect"
    )
    model_match = re.search(
        r"Worked example riddle:\s*(.+?)\s*Model answer:\s*([^.]+)\.",
        connect["passage"],
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert model_match is not None
    modelled_riddle = _normalized(model_match.group(1))
    modelled_answer = _normalized(model_match.group(2))

    learner_checks = [
        *_phase_activities(level, "co_construct"),
        *_phase_variants(level, "guided_practice"),
    ]
    assert len(learner_checks) == 5
    assert len({_normalized(item["passage"]) for item in learner_checks}) == 5

    for activity in learner_checks:
        learner_riddle = _normalized(activity["passage"])
        learner_answer = _normalized(activity["model_answer"])
        assert modelled_riddle not in learner_riddle
        assert modelled_answer not in learner_answer
        assert activity["grading_mode"] == "strict_open_rubric"
        assert activity["interaction_type"] == "paragraph_text"
        assert activity["options"] == []
        assert activity["accepted_answers"] == []
        assert "clue" in activity["prompt"].casefold()
        assert any(
            "clue" in criterion["description"].casefold()
            for criterion in activity["rubric_criteria"]
            if criterion["id"] != "clear_relevant_english"
        )


def test_chapter_one_strict_open_models_trace_every_authored_slot():
    missing_slots = tuple(
        issue
        for issue in chapter_quality_issues(load_live_chapter_file(CHAPTER_PATH))
        if issue.startswith("strict_open_model_missing_slot:")
    )

    assert missing_slots == ()


def test_riddle_transfer_umbrella_inference_has_one_sufficient_evidence_chain():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_visual_fun_and_riddle")
    transfer = next(
        activity
        for activity in _phase_variants(level, "transfer")
        if activity["variant_id"].endswith(":v1")
    )
    visible = _normalized(
        " ".join(
            (
                transfer["passage"],
                transfer["prompt"],
                transfer["model_answer"],
            )
        )
    )

    assert "community library entrance" in visible
    assert "placed her striped umbrella in the drying rack" in visible
    assert "curved red handle" in visible
    assert "explain" in transfer["prompt"].casefold()
    assert "two clues" in transfer["prompt"].casefold()
    assert transfer["grading_mode"] == "strict_open_rubric"
    assert transfer["accepted_answers"] == []
    assert {
        "umbrella_transfer_location",
        "umbrella_transfer_placement_clue",
        "umbrella_transfer_visible_clue",
    } <= {
        criterion["id"] for criterion in transfer["rubric_criteria"]
    }
    assert not any(
        ambiguous in transfer["passage"].casefold()
        for ambiguous in (
            "trail of wet prints",
            "ends beside the open umbrella stand",
        )
    )


def test_sound_level_is_truthfully_a_text_pattern_level_without_adult_dependency():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_sound_lab")
    visible = " ".join(
        [level["title"], level["focus"], level["teaching_goal"]]
        + [
            " ".join(
                [
                    activity.get("teaching_block", ""),
                    activity.get("passage", ""),
                    activity.get("prompt", ""),
                ]
            )
            for step in level["teaching_steps"]
            for activity in (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
        ]
    ).casefold()

    assert "sound" not in level["title"].casefold()
    assert not any(
        phrase in visible
        for phrase in (
            "ask a teacher",
            "ask a trusted adult",
            "ask a family member",
            "check their sounds later",
            "no audio has been played",
        )
    )


def test_comprehension_activities_author_distinct_remediation_targets():
    chapter = _chapter()
    level = _level(chapter, "papas_spectacles_poem_comprehension")
    activities = [
        activity
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
    ]

    for activity in activities:
        tags = set(activity.get("target_misconception_tags") or [])
        if activity.get("options") and len(tags) > 1:
            wrong_options = set(activity["options"]).difference(
                activity["accepted_answers"]
            )
            mapping = activity.get("wrong_answer_misconception_tags") or {}
            assert set(mapping) == wrong_options, activity.get("variant_id")
            assert all(set(mapped).issubset(tags) for mapped in mapping.values())
        if activity.get("rubric_criteria") and len(tags) > 1:
            criterion_ids = {
                criterion["id"] for criterion in activity["rubric_criteria"]
            }
            mapping = activity.get("criterion_misconception_tags") or {}
            assert mapping, activity.get("variant_id")
            assert set(mapping).issubset(criterion_ids)
            assert all(set(mapped).issubset(tags) for mapped in mapping.values())


def test_all_three_phase_masterclass_checks_are_evaluable():
    chapter = _chapter()
    for level in chapter["levels"]:
        for kind in (
            "bridge",
            "masterclass",
            "revision_level_1",
            "revision_level_2",
            "revision_level_3",
            "independent_check",
            "transfer_check",
        ):
            check = level["checks"][kind]
            assert masterclass._authored_check_is_evaluable(check), (
                level["level_id"],
                kind,
            )
            if check.get("accepted_answers"):
                evaluation = curriculum.evaluate_deterministic_answer(
                    check,
                    check["accepted_answers"][0],
                )
                assert evaluation["correct"], (level["level_id"], kind)
            else:
                evaluator_activity = curriculum.evaluator_activity_for_answer(
                    check,
                    check["model_answer"],
                )
                assert evaluator_activity is not None, (
                    level["level_id"],
                    kind,
                )


def test_chapter_one_runtime_sha_matches_the_approved_loader():
    chapter = load_live_chapter_file(CHAPTER_PATH)
    assert chapter.calculated_runtime_sha256() == chapter.runtime_sha256


def test_upgrader_rejects_old_six_level_seed_with_clear_prerequisite(
    tmp_path,
    monkeypatch,
):
    payload = json.loads(CHAPTER_PATH.read_text(encoding="utf-8"))
    payload["levels"] = payload["levels"][:6]
    seed_path = tmp_path / "eng_c5_ch01.json"
    seed_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    seed_before = seed_path.read_bytes()
    monkeypatch.setattr(chapter1_upgrader, "CHAPTER_PATH", seed_path)

    with pytest.raises(
        ValueError,
        match="chapter_one_nine_level_gold_structure_required",
    ):
        chapter1_upgrader.main()

    assert seed_path.read_bytes() == seed_before
