import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ai import calls
from app.ai.structured import structured_output_token_limit
from app.ai.prompts import build_school_open_answer_prompt
from app.config import Settings
from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_content import load_live_chapter_file
from app.middleware import rate_limit
from app.services.school import evaluation_jobs, open_answer_ai
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_recap as recap
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    SchoolOpenAnswerRetryableError,
)
from app.services.school.semantic_evidence import (
    authored_evidence_can_prove_criterion,
)
from app.services.school.open_answer_prompt import (
    build_school_open_answer_prompt as canonical_prompt_builder,
)


ACTIVITY = {
    "activity_id": "wise_parrot_story_continuation:independent_check:1",
    "skill_ids": [
        "writing.summary_own_words",
        "writing.reason_answer",
        "grammar.tense_usage",
    ],
    "prompt": "Write your story continuation in 60 to 90 words.",
    "passage": "Continue the story after the parrot flies into the open sky.",
    "rubric_criteria": [
        {
            "id": "continues_story",
            "description": "Continues from the authored final event.",
            "required": True,
        },
        {
            "id": "narrative_coherence",
            "description": "Connects actions and consequences in a coherent order.",
            "required": True,
        },
        {
            "id": "language_control",
            "description": "Uses understandable past-tense English.",
            "required": False,
        },
    ],
    "model_answer": "This hidden answer must never reach the provider prompt.",
}


def test_ai_backend_is_normalized_and_closed(monkeypatch):
    local_settings = Settings(ai_backend=" LOCAL ")
    cloud_settings = Settings(ai_backend="cloud")
    gemini_settings = Settings(ai_backend=" GEMINI ")

    assert local_settings.ai_backend == "local"
    assert cloud_settings.ai_backend == "cloud"
    assert gemini_settings.ai_backend == "gemini"
    monkeypatch.setattr(calls, "get_settings", lambda: local_settings)
    assert calls._local() is True

    with pytest.raises(ValidationError):
        Settings(ai_backend="unknown")

LEARNER_ANSWER = (
    "The parrot crossed the trees and found a quiet garden. It warned the other "
    "birds about the trader, so they moved deeper into the forest."
)


def test_school_open_answer_budget_fits_a_full_certifying_rubric_payload():
    """Five evidence rows must not be truncated before the closing JSON brace."""

    assert structured_output_token_limit("school_open_answer") == 768


def test_strict_open_provider_copying_flag_cannot_override_a_complete_summary():
    """The model cannot turn a fully evidenced recap answer into a false miss."""

    answer = (
        "Families donated more books, and older students organised them on "
        "labelled shelves."
    )
    activity = recap.evaluator_activity_for_answer(
        {
            "activity_id": "recap_summary:independent_check:1",
            "skill_ids": ["writing.summary_own_words"],
            "passage": (
                "A reading club had few books in different languages. Families "
                "donated stories, and older students organised them on labelled shelves."
            ),
            "prompt": "Summarize how the reading club improved its collection.",
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.summary.v1",
        }
    )
    assert activity is not None
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": ["copied_exemplar"],
            "needs_human_review": False,
            "feedback_to_learner": "You included the two changes clearly.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True, decision
    assert "copied_exemplar" not in decision["blockers"]


def test_strict_open_prompt_keeps_copy_detection_backend_owned():
    prompt = canonical_prompt_builder(
        item_id="recap_summary:independent_check:1",
        skill_ids=["writing.summary_own_words"],
        task_prompt="Summarize the change in your own words.",
        passage="Families donated stories and older students organised them.",
        learner_answer="Families gave books, and students sorted them.",
        rubric_criteria=[
            {
                "id": "main_idea_or_event",
                "description": "States the central change.",
                "required": True,
            }
        ],
        schema_version=OPEN_RUBRIC_SCHEMA_VERSION,
    )

    assert "Do not add copied_exemplar" in prompt


SUPPORTED_BRIDGE_ACTIVITY = {
    "activity_id": "event_sequence:bridge:1",
    "skill_ids": ["reading.event_sequence"],
    "prompt": "Name the start, middle, and ending in order.",
    "passage": "A wristband fell at the gate, rolled under a bench, and was found by the monitor.",
    "grading_mode": "strict_open_rubric",
    "evaluation_mode": "llm_rubric",
    "evidence_role": "supported",
    "pass_score": 0.8,
    "minimum_confidence": 0.65,
    "min_response_words": 6,
    "rubric_criteria": [
        {
            "id": "event_sequence:bridge:1:start",
            "description": "Names the fall at the gate as the start.",
            "required": True,
            "min_quality": 0.65,
        },
        {
            "id": "event_sequence:bridge:1:middle",
            "description": "Names rolling under the bench as the middle.",
            "required": True,
            "min_quality": 0.65,
        },
        {
            "id": "event_sequence:bridge:1:end",
            "description": "Names the monitor finding it as the ending.",
            "required": True,
            "min_quality": 0.65,
        },
    ],
    "concept_slots": [
        {"id": "event_sequence:bridge:1:start", "any_of": ["fell at the gate"]},
        {"id": "event_sequence:bridge:1:middle", "any_of": ["rolled under the bench"]},
        {"id": "event_sequence:bridge:1:end", "any_of": ["found by the monitor"]},
    ],
    "ordered_concept_slot_ids": [
        "event_sequence:bridge:1:start",
        "event_sequence:bridge:1:middle",
        "event_sequence:bridge:1:end",
    ],
}


@pytest.mark.asyncio
async def test_supported_open_answer_uses_a_safe_authored_evidence_fast_path(
    monkeypatch,
):
    answer = (
        "First it fell at the gate, then it rolled under the bench, and finally "
        "it was found by the monitor."
    )

    async def provider_must_not_run(*args, **kwargs):
        del args, kwargs
        raise AssertionError("fully evidenced supported bridge work must not call an LLM")

    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "structured_generate", provider_must_not_run)

    result = await open_answer_ai.evaluate_school_open_answer(
        SUPPORTED_BRIDGE_ACTIVITY,
        answer,
    )

    assert result.schema_version == OPEN_RUBRIC_SCHEMA_VERSION
    assert result.score == 1.0
    assert result.confidence == 1.0
    assert all(criterion.met for criterion in result.criteria)
    assert all(criterion.evidence_quote in answer for criterion in result.criteria)


@pytest.mark.asyncio
async def test_ch01_story_revision_uses_deterministic_supported_evidence(monkeypatch):
    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "content"
        / "school_rebuild_chapters"
        / "english"
        / "class_5"
        / "eng_c5_ch01.json"
    )
    chapter = load_live_chapter_file(chapter_path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "papas_spectacles_poem_to_story"
    )
    activity = level.checks.revision_level_1.model_dump(exclude_none=True)
    activity["activity_id"] = "papas_spectacles_poem_to_story:revision_level_1"
    activity["skill_ids"] = list(activity["knowledge_components"])
    answer = "Mira opened the gate and walked into the garden."

    async def provider_must_not_run(*args, **kwargs):
        del args, kwargs
        raise AssertionError("fully evidenced supported revision work must not call an LLM")

    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "structured_generate", provider_must_not_run)

    result = await open_answer_ai.evaluate_school_open_answer(activity, answer)

    assert result.score == 1.0
    assert all(criterion.met for criterion in result.criteria)


@pytest.mark.asyncio
async def test_certifying_open_answer_never_uses_the_supported_fast_path(monkeypatch):
    answer = (
        "First it fell at the gate, then it rolled under the bench, and finally "
        "it was found by the monitor."
    )
    activity = {
        **SUPPORTED_BRIDGE_ACTIVITY,
        "evidence_role": "certifying",
        "certifying_language": "en",
    }
    calls = []

    async def provider(operation, prompt, schema, *, timeout=None):
        del operation, prompt, timeout
        calls.append(schema)
        return schema.model_validate(
            {
                "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
                "item_id": activity["activity_id"],
                "skill_ids": activity["skill_ids"],
                "score": 1.0,
                "confidence": 1.0,
                "language_detected": "en",
                "criteria": [
                    {
                        "id": criterion["id"],
                        "met": True,
                        "quality": 1.0,
                        "evidence_quote": slot["any_of"][0],
                    }
                    for criterion, slot in zip(
                        activity["rubric_criteria"], activity["concept_slots"]
                    )
                ],
                "misconception_tags": [],
                "blockers": [],
                "needs_human_review": False,
                "feedback_to_learner": "You put each event in order.",
            }
        )

    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "structured_generate", provider)

    await open_answer_ai.evaluate_school_open_answer(activity, answer)

    assert len(calls) == 1


def _evaluation() -> SchoolRubricEvaluation:
    return SchoolRubricEvaluation.model_validate(
        {
            "schema_version": "school-v3-rubric-1",
            "item_id": ACTIVITY["activity_id"],
            "skill_ids": list(ACTIVITY["skill_ids"]),
            "score": 0.8,
            "confidence": 0.9,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 0.8,
                    "evidence_quote": "The parrot crossed the trees",
                }
                for criterion in ACTIVITY["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Your events connect clearly; check the word range.",
        }
    )


def test_school_open_answer_prompt_contains_every_authored_criterion():
    assert build_school_open_answer_prompt is canonical_prompt_builder
    prompt = build_school_open_answer_prompt(
        item_id=ACTIVITY["activity_id"],
        skill_ids=ACTIVITY["skill_ids"],
        task_prompt=ACTIVITY["prompt"],
        passage=ACTIVITY["passage"],
        learner_answer=LEARNER_ANSWER,
        rubric_criteria=ACTIVITY["rubric_criteria"],
    )

    assert ACTIVITY["activity_id"] in prompt
    assert ACTIVITY["prompt"] in prompt
    assert ACTIVITY["passage"] in prompt
    assert LEARNER_ANSWER in prompt
    for skill_id in ACTIVITY["skill_ids"]:
        assert skill_id in prompt
    for criterion in ACTIVITY["rubric_criteria"]:
        assert criterion["id"] in prompt
        assert criterion["description"] in prompt
        assert str(criterion["required"]).lower() in prompt.lower()
    assert "score must be a decimal from 0.0 to 1.0" in prompt
    assert "confidence must be a decimal from 0.0 to 1.0" in prompt
    assert "quality must be a decimal from 0.0 to 1.0" in prompt
    assert "SchoolV3RubricEvaluation" in prompt
    assert "language_detected" in prompt
    assert '"en", "hi", "hi_en", "other", or "unknown"' in prompt
    assert "evidence_quote" in prompt
    assert "Do not decide progression, readiness, mastery, unlocks, or pass/fail" in prompt


def test_school_rubric_evaluation_rejects_unbounded_language_labels():
    payload = _evaluation().model_dump(mode="json")
    payload["language_detected"] = "English"

    with pytest.raises(ValidationError):
        SchoolRubricEvaluation.model_validate(payload)


@pytest.mark.asyncio
async def test_local_school_open_answer_dispatches_authoritative_schema_once(monkeypatch):
    captured = []

    async def fake_ollama_structured(prompt, schema, *, timeout):
        captured.append((prompt, schema, timeout))
        return _evaluation()

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(ACTIVITY, LEARNER_ANSWER)

    assert result == _evaluation()
    assert len(captured) == 1
    prompt, schema, timeout = captured[0]
    assert schema is not SchoolRubricEvaluation
    assert issubclass(schema, SchoolRubricEvaluation)
    properties = schema.model_json_schema()["properties"]
    assert properties["schema_version"]["const"] == "school-v3-rubric-1"
    assert properties["item_id"]["const"] == ACTIVITY["activity_id"]
    assert timeout is None
    assert ACTIVITY["model_answer"] not in prompt
    for criterion in ACTIVITY["rubric_criteria"]:
        assert criterion["id"] in prompt
        assert criterion["description"] in prompt


@pytest.mark.asyncio
async def test_chapter_check_provider_identity_uses_immutable_activity_id(monkeypatch):
    activity = {
        **ACTIVITY,
        "activity_id": "chapter_check:1:eng_c5_ch05_assess_11",
        "item_id": "eng_c5_ch05_assess_11",
    }
    captured = []

    async def fake_ollama_structured(prompt, schema, *, timeout):
        captured.append((prompt, timeout))
        return _evaluation().model_copy(
            update={"item_id": activity["activity_id"]},
        )

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(activity, LEARNER_ANSWER)

    assert result.item_id == activity["activity_id"]
    assert f'"item_id": "{activity["activity_id"]}"' in captured[0][0]
    assert captured[0][1] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "identity_update",
    (
        {"schema_version": "school-v3-rubric-1"},
        {"item_id": "stale-or-cross-item"},
        {"skill_ids": ("model.selected.skill",)},
    ),
)
async def test_strict_open_rejects_stale_or_cross_item_provider_identity(
    monkeypatch,
    identity_update,
):
    activity = {
        **ACTIVITY,
        "grading_mode": "strict_open_rubric",
        "activity_id": (
            "papas_spectacles_poem_comprehension:"
            "papas_spectacles_poem_comprehension:review:"
            "papas_spectacles_poem_comprehension:review:v1:1"
        ),
    }

    async def fake_ollama_structured(prompt, schema, *, timeout):
        return _evaluation().model_copy(
            update={
                "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
                "item_id": activity["activity_id"],
                "skill_ids": tuple(activity["skill_ids"]),
                **identity_update,
            },
        )

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    with pytest.raises(SchoolOpenAnswerRetryableError) as raised:
        await open_answer_ai.evaluate_school_open_answer(
            activity,
            LEARNER_ANSWER,
        )

    assert raised.value.code == "school_open_schema_failure"
    assert raised.value.evidence is None


@pytest.mark.asyncio
async def test_strict_open_schema_constrains_identity_before_qwen_generation(
    monkeypatch,
):
    activity = {
        **ACTIVITY,
        "grading_mode": "strict_open_rubric",
        "activity_id": (
            "papas_spectacles_poem_comprehension:"
            "papas_spectacles_poem_comprehension:review:"
            "papas_spectacles_poem_comprehension:review:v1:1"
        ),
    }
    captured = []

    async def fake_ollama_structured(prompt, schema, *, timeout):
        captured.append(schema)
        return schema.model_validate(
            _evaluation().model_copy(
                update={
                    "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
                    "item_id": activity["activity_id"],
                },
            ).model_dump()
        )

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(
        activity,
        LEARNER_ANSWER,
    )

    assert result.item_id == activity["activity_id"]
    properties = captured[0].model_json_schema()["properties"]
    assert properties["schema_version"]["const"] == OPEN_RUBRIC_SCHEMA_VERSION
    assert properties["item_id"]["const"] == activity["activity_id"]
    criterion_ref = properties["criteria"]["prefixItems"][0]["$ref"]
    criterion_schema_name = criterion_ref.rsplit("/", maxsplit=1)[-1]
    criterion_properties = captured[0].model_json_schema()["$defs"][
        criterion_schema_name
    ]["properties"]
    assert criterion_properties["evidence_quote"]["minLength"] == 1

    valid_payload = _evaluation().model_copy(
        update={
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
        },
    ).model_dump(mode="python")
    invalid_skill_payload = {
        **valid_payload,
        "skill_ids": ["model.selected.skill"],
    }
    invalid_criterion_payload = {
        **valid_payload,
        "criteria": [
            *valid_payload["criteria"][:2],
            {
                **valid_payload["criteria"][2],
                "id": "model_renamed_criterion",
            },
        ],
    }

    with pytest.raises(ValidationError):
        captured[0].model_validate(invalid_skill_payload)
    with pytest.raises(ValidationError):
        captured[0].model_validate(invalid_criterion_payload)


@pytest.mark.asyncio
async def test_strict_open_provider_normalizes_unmet_criterion_quality_fail_closed(
    monkeypatch,
):
    activity = {
        **ACTIVITY,
        "grading_mode": "strict_open_rubric",
    }

    async def fake_ollama_structured(prompt, schema, *, timeout):
        payload = _evaluation().model_copy(
            update={
                "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
                "criteria": tuple(
                    criterion.model_copy(
                        update={"met": False, "quality": 0.25}
                    )
                    if index == 1
                    else criterion
                    for index, criterion in enumerate(_evaluation().criteria)
                ),
            }
        ).model_dump(mode="python")
        return schema.model_validate(payload)

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(
        activity,
        LEARNER_ANSWER,
    )

    assert result.criteria[1].met is False
    assert result.criteria[1].quality == 0.0


@pytest.mark.asyncio
async def test_strict_open_downgrades_untraceable_model_evidence_instead_of_failing(
    monkeypatch,
):
    activity = {
        **ACTIVITY,
        "grading_mode": "strict_open_rubric",
    }
    generated = _evaluation().model_copy(
        update={
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "criteria": [
                criterion.model_copy(
                    update={
                        "evidence_quote": (
                            "a passage clue the learner never wrote"
                            if index == 0
                            else criterion.evidence_quote
                        )
                    }
                )
                for index, criterion in enumerate(_evaluation().criteria)
            ],
        }
    )

    async def fake_ollama_structured(prompt, schema, *, timeout):
        return generated

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(
        activity,
        LEARNER_ANSWER,
    )

    assert result.criteria[0].met is False
    assert result.criteria[0].quality == 0.0
    assert result.criteria[0].evidence_quote == LEARNER_ANSWER
    assert "evaluator_evidence_untraceable" in result.blockers


@pytest.mark.asyncio
async def test_strict_open_recovers_a_passage_grounded_clue_from_the_learner_answer(
    monkeypatch,
):
    answer = (
        "Many people borrowed books over the weekend because the shelves had "
        "empty spaces, and they returned them afterward, filling the cart."
    )
    activity = {
        "activity_id": "recap-inference:independent:1",
        "skill_ids": ["reading.inference_reason"],
        "prompt": "What probably happened over the weekend? Use one clue.",
        "passage": (
            "The library return cart was overflowing, and several spaces on "
            "the shelves were empty after the long weekend."
        ),
        "grading_mode": "strict_open_rubric",
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "certifying_language": "en",
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": criterion_id,
                "required": True,
                "min_quality": 0.7,
            }
            for criterion_id in (
                "plausible_inference",
                "relevant_text_clue",
                "clue_supports_inference",
                "complete_response",
                "english_response",
            )
        ],
    }
    evidence_by_id = {
        "plausible_inference": "Many people borrowed books over the weekend",
        "relevant_text_clue": "books disappeared from all the library shelves",
        "clue_supports_inference": answer,
        "complete_response": answer,
        "english_response": answer,
    }
    generated = SchoolRubricEvaluation.model_validate({
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
                "evidence_quote": evidence_by_id[criterion["id"]],
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The inference is linked to a passage clue.",
    })

    async def fake_ollama_structured(prompt, schema, *, timeout):
        return generated

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(activity, answer)

    clue = next(
        criterion
        for criterion in result.criteria
        if criterion.id == "relevant_text_clue"
    )
    assert clue.met is True
    assert clue.evidence_quote in answer
    assert "evaluator_evidence_untraceable" not in result.blockers
    decision = curriculum.decide_open_answer_evaluation(
        activity,
        result,
        answer=answer,
    )
    assert decision["correct"] is True


@pytest.mark.asyncio
async def test_strict_open_recovers_single_word_slots_and_clear_english_evidence(
    monkeypatch,
):
    answer = (
        "Here, scanned means looked carefully across the whole corridor. "
        "The teacher scanned the classroom to find an empty seat."
    )
    activity = {
        "activity_id": "chapter-words:independent:1",
        "skill_ids": ["reading.word_meaning_context", "vocab.chapter_word_usage"],
        "prompt": "What does scanned mean here? Use scanned in a new sentence.",
        "passage": "The guard scanned the empty corridor before locking the door.",
        "grading_mode": "strict_open_rubric",
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "certifying_language": "en",
        "rubric_criteria": [
            {
                "id": "chapter_words_target",
                "description": "Infers the contextual meaning.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "chapter_words_target:detail_2",
                "description": "Includes carefully or a valid paraphrase.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "chapter_words_target:detail_3",
                "description": "Uses scanned accurately in a new sentence.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "clear_relevant_english",
                "description": "Communicates the idea in clear English.",
                "required": True,
                "min_quality": 0.6,
            },
        ],
        "concept_slots": [
            {"id": "chapter_words_target", "any_of": ["looked"]},
            {"id": "chapter_words_target:detail_2", "any_of": ["carefully"]},
            {"id": "chapter_words_target:detail_3", "any_of": ["scanned"]},
        ],
    }
    generated = SchoolRubricEvaluation.model_validate({
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.8,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": "chapter_words_target",
                "met": True,
                "quality": 0.8,
                "evidence_quote": "looked across the corridor",
            },
            {
                "id": "chapter_words_target:detail_2",
                "met": True,
                "quality": 0.8,
                "evidence_quote": "carefully across the corridor",
            },
            {
                "id": "chapter_words_target:detail_3",
                "met": True,
                "quality": 0.8,
                "evidence_quote": "scanned",
            },
            {
                "id": "clear_relevant_english",
                "met": True,
                "quality": 0.8,
                "evidence_quote": "The response is clear English.",
            },
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The contextual meaning and new use are clear.",
    })

    async def fake_ollama_structured(prompt, schema, *, timeout):
        return generated

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(activity, answer)

    assert [criterion.met for criterion in result.criteria] == [True] * 4
    assert all(criterion.evidence_quote in answer for criterion in result.criteria)
    assert "evaluator_evidence_untraceable" not in result.blockers
    decision = curriculum.decide_open_answer_evaluation(
        activity,
        result,
        answer=answer,
    )
    assert decision["correct"] is True


@pytest.mark.asyncio
async def test_strict_open_backend_recovers_an_atomic_detail_the_model_missed(
    monkeypatch,
):
    answer = (
        "Leena is searching for a key. We can infer that it is on the desk in "
        "front of her because she used it to hold down the papers there."
    )
    activity = {
        "activity_id": "poem-comprehension:review:v1:1",
        "skill_ids": [
            "reading.sentence_comprehension",
            "reading.inference_reason",
            "reading.paragraph_main_idea",
        ],
        "prompt": "Give the main situation, best inference, and evidence.",
        "passage": (
            "Leena searches the desk for a key that she used to hold down the "
            "papers in front of her."
        ),
        "grading_mode": "strict_open_rubric",
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "min_response_words": 6,
        "certifying_language": "en",
        "relevance_terms": ["key", "papers", "desk"],
        "rubric_criteria": [
            {
                "id": "poem_comprehension_target",
                "description": "Identifies the situation and a supported inference.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "poem_comprehension_target:detail_2",
                "description": "Includes the papers detail.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "poem_comprehension_target:detail_3",
                "description": "Includes the desk detail.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "clear_relevant_english",
                "description": "Communicates the idea in clear English.",
                "required": True,
                "min_quality": 0.6,
            },
        ],
        "concept_slots": [
            {"id": "poem_comprehension_target", "any_of": ["key"]},
            {
                "id": "poem_comprehension_target:detail_2",
                "any_of": ["papers"],
            },
            {
                "id": "poem_comprehension_target:detail_3",
                "any_of": ["desk"],
            },
        ],
    }
    generated = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.75,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": "poem_comprehension_target",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "Leena is searching for a key.",
                },
                {
                    "id": "poem_comprehension_target:detail_2",
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": "The learner did not mention the papers.",
                },
                {
                    "id": "poem_comprehension_target:detail_3",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "on the desk in front of her",
                },
                {
                    "id": "clear_relevant_english",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                },
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The situation and inference are clear.",
        }
    )

    async def fake_ollama_structured(prompt, schema, *, timeout):
        return generated

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    evaluation = await open_answer_ai.evaluate_school_open_answer(activity, answer)
    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    provider_detail = next(
        item
        for item in evaluation.criteria
        if item.id == "poem_comprehension_target:detail_2"
    )
    decided_detail = next(
        item
        for item in decision["criteria"]
        if item["id"] == "poem_comprehension_target:detail_2"
    )
    assert provider_detail.met is False
    assert provider_detail.evidence_quote == answer
    assert "evaluator_evidence_untraceable" not in evaluation.blockers
    assert decided_detail["met"] is True
    assert decided_detail["quality"] == 1.0
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []
    assert decision["correct"] is True


def test_review_accepts_supported_search_inference_without_repeating_desk_noun():
    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
    )
    chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
    review_step = next(
        step
        for level in chapter["levels"]
        for step in level["teaching_steps"]
        if step["step_id"] == "papas_spectacles_poem_comprehension:review"
    )
    authored_activity = review_step["variant_pool"][0]
    activity = {
        **authored_activity,
        "activity_id": authored_activity["variant_id"],
        "skill_ids": authored_activity["knowledge_components"],
    }
    answer = (
        "Leena is searching for her key. She should check the papers in front "
        "of her because the passage says she used the key to hold them down."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["variant_id"],
            "skill_ids": activity["knowledge_components"],
            "score": 0.75,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": "poem_comprehension_target",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "Leena is searching for her key.",
                },
                {
                    "id": "poem_comprehension_target:detail_2",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "papers in front of her",
                },
                {
                    "id": "poem_comprehension_target:detail_3",
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": answer,
                },
                {
                    "id": "clear_relevant_english",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                },
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The inference and clue are connected.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    desk_criterion = next(
        criterion
        for criterion in activity["rubric_criteria"]
        if criterion["id"] == "poem_comprehension_target:detail_3"
    )
    assert desk_criterion["required"] is False
    assert all(
        slot["id"] != "poem_comprehension_target:detail_3"
        for slot in activity["concept_slots"]
    )
    assert decision["correct"] is True
    assert decision["missing_criteria"] == []


def _scarf_sequence_activity() -> dict:
    return {
        "activity_id": "scooter_event_sequence:independent:2",
        "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea",
        ],
        "prompt": "State the main event and two details that build it.",
        "passage": (
            "A red scarf blew from a railing onto the roof of a parked van. "
            "The van moved to the shade, where a cleaner spotted the scarf."
        ),
        "grading_mode": "strict_open_rubric",
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.8,
        "min_response_words": 6,
        "certifying_language": "en",
        "relevance_terms": ["scarf", "van", "cleaner"],
        "rubric_criteria": [
            {
                "id": "scooter_event_sequence:independent:2:main",
                "description": "States that the scarf accidentally travelled with the van.",
                "required": True,
                "min_quality": 0.65,
            },
            {
                "id": "scooter_event_sequence:independent:2:detail",
                "description": "Uses both the wind and later discovery as supporting events.",
                "required": True,
                "min_quality": 0.65,
            },
        ],
        "concept_slots": [
            {
                "id": "scooter_event_sequence:independent:2:main",
                "description": "States that the scarf accidentally travelled with the van.",
                "any_of": ["scarf travelled on the van"],
            },
            {
                "id": "scooter_event_sequence:independent:2:detail",
                "description": "Uses both the wind and later discovery as supporting events.",
                "any_of": [
                    "blew from the railing onto the van roof and the cleaner spotted it"
                ],
            },
        ],
    }


def _scarf_sequence_evaluation(
    answer: str,
    *,
    main_met: bool,
) -> SchoolRubricEvaluation:
    activity = _scarf_sequence_activity()
    return SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.5 if main_met else 0.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": "scooter_event_sequence:independent:2:main",
                    "met": main_met,
                    "quality": 1.0 if main_met else 0.0,
                    "evidence_quote": answer,
                },
                {
                    "id": "scooter_event_sequence:independent:2:detail",
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": answer,
                },
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Check both supporting events.",
        }
    )


def test_strict_open_backend_recovers_complete_authored_semantic_evidence():
    answer = (
        "The main event is the scarf travelling on the van until it was found. "
        "It blew from the railing onto the van roof, and the cleaner spotted it "
        "after the van moved to the shade."
    )

    decision = curriculum.decide_open_answer_evaluation(
        _scarf_sequence_activity(),
        _scarf_sequence_evaluation(answer, main_met=True),
        answer=answer,
    )

    assert decision["correct"] is True
    assert decision["missing_criteria"] == []
    assert decision["blockers"] == []


def test_ch02_scooter_safety_paraphrase_recovers_each_authored_detail():
    """A complete child answer must not fail just because it avoids model phrasing."""

    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "content"
        / "school_rebuild_chapters"
        / "english"
        / "class_5"
        / "eng_c5_ch02.json"
    )
    chapter = load_live_chapter_file(chapter_path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "scooter_inference_and_fair_choice"
    )
    independent_step = next(
        item
        for item in level.teaching_steps
        if item.phase == "independent_application"
    )
    raw_activity = next(
        item
        for item in independent_step.variant_pool
        if item.variant_id == "scooter_inference_and_fair_choice:independent:2"
    ).model_dump(exclude_none=True)
    activity = {
        **raw_activity,
        "activity_id": raw_activity["variant_id"],
        "skill_ids": raw_activity["knowledge_components"],
    }
    answer = (
        "The loose chin strap means the helmet may not protect the cyclist if a "
        "speed breaker makes the bike jolt. The cyclist should fasten the strap "
        "before riding slowly over the speed breakers."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.0,
            "confidence": 0.95,
            "language_detected": "en",
                "criteria": [
                    {
                        "id": criterion["id"],
                        "met": False,
                        "quality": 0.0,
                        # A provider may quote the relevant sentence but still
                        # miss the criterion. The backend must recover only
                        # author-approved equivalent evidence from that answer.
                        "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Check the safety clues.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["missing_criteria"] == [], decision
    assert decision["correct"] is True, decision


def test_ch03_rainbow_bridge_paraphrase_recovers_each_authored_detail():
    """A natural conjugated bridge explanation must retain both required clues."""

    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "content"
        / "school_rebuild_chapters"
        / "english"
        / "class_5"
        / "eng_c5_ch03.json"
    )
    chapter = load_live_chapter_file(chapter_path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "rainbow_image_and_idea"
    )
    independent_step = next(
        item
        for item in level.teaching_steps
        if item.phase == "independent_application"
    )
    raw_activity = next(
        item
        for item in independent_step.variant_pool
        if item.variant_id == "rainbow_image_and_idea:independent:1"
    ).model_dump(exclude_none=True)
    activity = {
        **raw_activity,
        "activity_id": raw_activity["variant_id"],
        "skill_ids": raw_activity["knowledge_components"],
    }
    answer = (
        "A poet may call it a bridge because the coloured curve arches over the "
        "river. It looks like it connects the reeds on one bank with the old "
        "fort on the other side."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Check the bridge clues.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["missing_criteria"] == [], decision
    assert decision["correct"] is True, decision


def test_paired_place_connection_requires_a_complete_authored_relation():
    description = "Uses the apparent connection between two places."

    assert authored_evidence_can_prove_criterion(
        description,
        "connects the reeds with the old fort",
    )
    assert not authored_evidence_can_prove_criterion(
        description,
        "connects the reeds",
    )


def test_ch03_ribbon_review_recovers_a_complete_nonliteral_paraphrase():
    """A complete browser-grounded image explanation must not enter support."""

    chapter_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "content"
        / "school_rebuild_chapters"
        / "english"
        / "class_5"
        / "eng_c5_ch03.json"
    )
    chapter = load_live_chapter_file(chapter_path)
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "rainbow_image_and_idea"
    )
    review_step = next(
        item for item in level.teaching_steps if item.phase == "review"
    )
    raw_activity = next(
        item
        for item in review_step.variant_pool
        if item.variant_id == "rainbow_image_and_idea:review:1"
    ).model_dump(exclude_none=True)
    activity = {
        **raw_activity,
        "activity_id": raw_activity["variant_id"],
        "skill_ids": raw_activity["knowledge_components"],
    }
    answer = (
        "A ribbon is a curved strip, so the pale curve looks like a ribbon "
        "stretched between two clouds. It is a comparison, not a real ribbon."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": False,
                    "quality": 0.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Check the picture clues.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["missing_criteria"] == [], decision
    assert decision["correct"] is True, decision


def test_strict_open_negative_alias_does_not_accept_a_negated_positive_claim():
    assert (
        curriculum._authored_concept_evidence_quote(
            "The helmet may not protect the cyclist at a speed breaker.",
            "helmet may not protect",
        )
        == "helmet may not protect"
    )
    assert (
        curriculum._authored_concept_evidence_quote(
            "The helmet may not come off at a speed breaker.",
            "helmet may come off",
        )
        is None
    )


def test_ch02_alias_only_release_repairs_an_in_progress_scooter_activity(
    monkeypatch,
):
    chapter = next(
        item
        for item in curriculum.CLASS_5_CURRICULUM_CHAPTERS
        if item["chapter_id"] == "eng_c5_ch02"
    )
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda _subject_id, _class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "scooter-alias-repair-profile",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "scooter-alias-repair-placement",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
        requested_chapter_id="eng_c5_ch02",
    )
    state["chapter"]["content_version"] = "2026-07-15.4.semantic-evidence-v1"
    level = next(
        item
        for item in state["levels"]
        if item["level_id"] == "scooter_inference_and_fair_choice"
    )
    independent_step = next(
        item
        for item in level["teaching_steps"]
        if item["phase"] == "independent_application"
    )
    persisted = next(
        item
        for item in independent_step["variant_pool"]
        if item["variant_id"] == "scooter_inference_and_fair_choice:independent:2"
    )
    for slot in persisted["concept_slots"]:
        slot["any_of"] = [
            alias
            for alias in slot["any_of"]
            if alias
            not in {
                "helmet may not protect",
                "speed breaker makes the bike jolt",
                "fasten the strap before riding",
            }
        ]

    reconciled, repair = curriculum.reconcile_curriculum_state(state)

    assert repair == {
        "kind": "strict_open_alias_expansion_reconciled",
        "chapter_id": "eng_c5_ch02",
        "from_content_version": "2026-07-15.4.semantic-evidence-v1",
        "to_content_version": "2026-07-15.4.semantic-evidence-v2",
        "variant_ids": ["scooter_inference_and_fair_choice:independent:2"],
    }
    assert reconciled["chapter"]["content_version"] == (
        "2026-07-15.4.semantic-evidence-v2"
    )
    repaired_level = next(
        item
        for item in reconciled["levels"]
        if item["level_id"] == "scooter_inference_and_fair_choice"
    )
    repaired_step = next(
        item
        for item in repaired_level["teaching_steps"]
        if item["phase"] == "independent_application"
    )
    repaired = next(
        item
        for item in repaired_step["variant_pool"]
        if item["variant_id"] == "scooter_inference_and_fair_choice:independent:2"
    )
    assert "helmet may not protect" in repaired["concept_slots"][0]["any_of"]
    assert "speed breaker makes the bike jolt" in repaired["concept_slots"][2]["any_of"]


def test_ch03_alias_only_release_repairs_an_in_progress_rainbow_activity(
    monkeypatch,
):
    chapter = next(
        item
        for item in curriculum.CLASS_5_CURRICULUM_CHAPTERS
        if item["chapter_id"] == "eng_c5_ch03"
    )
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda _subject_id, _class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "rainbow-alias-repair-profile",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "rainbow-alias-repair-placement",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
        requested_chapter_id="eng_c5_ch03",
    )
    state["chapter"]["content_version"] = "2026-07-15.5.semantic-evidence-v1"
    level = next(
        item
        for item in state["levels"]
        if item["level_id"] == "rainbow_image_and_idea"
    )
    independent_step = next(
        item
        for item in level["teaching_steps"]
        if item["phase"] == "independent_application"
    )
    persisted = next(
        item
        for item in independent_step["variant_pool"]
        if item["variant_id"] == "rainbow_image_and_idea:independent:1"
    )
    for slot in persisted["concept_slots"]:
        slot["any_of"] = [
            alias
            for alias in slot["any_of"]
            if alias != "connects the reeds with the old fort"
        ]
    review_step = next(
        item for item in level["teaching_steps"] if item["phase"] == "review"
    )
    review = next(
        item
        for item in review_step["variant_pool"]
        if item["variant_id"] == "rainbow_image_and_idea:review:1"
    )
    for slot in review["concept_slots"]:
        slot["any_of"] = [
            alias
            for alias in slot["any_of"]
            if alias not in {"curved strip and stretched between", "not a real ribbon"}
        ]

    reconciled, repair = curriculum.reconcile_curriculum_state(state)

    assert repair == {
        "kind": "strict_open_alias_expansion_reconciled",
        "chapter_id": "eng_c5_ch03",
        "from_content_version": "2026-07-15.5.semantic-evidence-v1",
        "to_content_version": "2026-07-15.5.semantic-alias-v3",
        "variant_ids": [
            "rainbow_image_and_idea:independent:1",
            "rainbow_image_and_idea:review:1",
        ],
    }
    assert reconciled["chapter"]["content_version"] == (
        "2026-07-15.5.semantic-alias-v3"
    )
    repaired_level = next(
        item
        for item in reconciled["levels"]
        if item["level_id"] == "rainbow_image_and_idea"
    )
    repaired_step = next(
        item
        for item in repaired_level["teaching_steps"]
        if item["phase"] == "independent_application"
    )
    repaired = next(
        item
        for item in repaired_step["variant_pool"]
        if item["variant_id"] == "rainbow_image_and_idea:independent:1"
    )
    assert "connects the reeds with the old fort" in repaired["concept_slots"][1][
        "any_of"
    ]
    repaired_review_step = next(
        item
        for item in repaired_level["teaching_steps"]
        if item["phase"] == "review"
    )
    repaired_review = next(
        item
        for item in repaired_review_step["variant_pool"]
        if item["variant_id"] == "rainbow_image_and_idea:review:1"
    )
    assert "curved strip and stretched between" in repaired_review["concept_slots"][
        0
    ]["any_of"]
    assert "not a real ribbon" in repaired_review["concept_slots"][1]["any_of"]


def test_ch03_v3_alias_only_release_repairs_an_in_progress_ribbon_review(
    monkeypatch,
):
    chapter = next(
        item
        for item in curriculum.CLASS_5_CURRICULUM_CHAPTERS
        if item["chapter_id"] == "eng_c5_ch03"
    )
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda _subject_id, _class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={
            "profile_version_id": "ribbon-alias-repair-profile",
            "target_class_no": 5,
            "subject_ids": ["english"],
            "preferred_teaching_language": "en",
        },
        placement_report={
            "report_id": "ribbon-alias-repair-placement",
            "unlock_state": "target_unlocked",
        },
        recap_session=None,
        requested_chapter_id="eng_c5_ch03",
    )
    state["chapter"]["content_version"] = "2026-07-15.5.semantic-alias-v2"
    level = next(
        item
        for item in state["levels"]
        if item["level_id"] == "rainbow_image_and_idea"
    )
    review_step = next(
        item for item in level["teaching_steps"] if item["phase"] == "review"
    )
    persisted = next(
        item
        for item in review_step["variant_pool"]
        if item["variant_id"] == "rainbow_image_and_idea:review:1"
    )
    for slot in persisted["concept_slots"]:
        slot["any_of"] = [
            alias
            for alias in slot["any_of"]
            if alias not in {"curved strip and stretched between", "not a real ribbon"}
        ]

    reconciled, repair = curriculum.reconcile_curriculum_state(state)

    assert repair == {
        "kind": "strict_open_alias_expansion_reconciled",
        "chapter_id": "eng_c5_ch03",
        "from_content_version": "2026-07-15.5.semantic-alias-v2",
        "to_content_version": "2026-07-15.5.semantic-alias-v3",
        "variant_ids": ["rainbow_image_and_idea:review:1"],
    }
    assert reconciled["chapter"]["content_version"] == (
        "2026-07-15.5.semantic-alias-v3"
    )
    repaired_level = next(
        item
        for item in reconciled["levels"]
        if item["level_id"] == "rainbow_image_and_idea"
    )
    repaired_step = next(
        item for item in repaired_level["teaching_steps"] if item["phase"] == "review"
    )
    repaired = next(
        item
        for item in repaired_step["variant_pool"]
        if item["variant_id"] == "rainbow_image_and_idea:review:1"
    )
    assert "curved strip and stretched between" in repaired["concept_slots"][0][
        "any_of"
    ]
    assert "not a real ribbon" in repaired["concept_slots"][1]["any_of"]


def test_strict_open_backend_does_not_recover_one_partial_supporting_event():
    answer = "The wind put the scarf on the van roof."
    activity = _scarf_sequence_activity()
    activity["concept_slots"][1]["any_of"] = [
        "wind put the scarf on the van roof",
        "cleaner found the scarf",
    ]

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        _scarf_sequence_evaluation(answer, main_met=False),
        answer=answer,
    )

    assert decision["correct"] is False
    assert "scooter_event_sequence:independent:2:detail" in decision[
        "missing_criteria"
    ]


@pytest.mark.asyncio
async def test_strict_open_recovers_exact_evidence_for_an_authored_semantic_paraphrase(
    monkeypatch,
):
    answer = (
        "The captain speaks first to Ravi and reports the missing scoreboard key. "
        "Ravi is the listener in that line. Ravi then contributes that he found "
        "the key hanging beside the whistle."
    )
    activity = {
        "activity_id": "dialogue-attribution:independent:1",
        "skill_ids": ["reading.dialogue_attribution", "writing.dialogue"],
        "prompt": "Identify both speakers, the listener, and Ravi's contribution.",
        "passage": (
            "'The scoreboard key is missing,' the captain told Ravi. Ravi said, "
            "'It is hanging beside the whistle.'"
        ),
        "grading_mode": "strict_open_rubric",
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.8,
        "relevance_terms": ["captain", "Ravi", "key"],
        "rubric_criteria": [
            {
                "id": "attribution",
                "description": "Identifies the captain as speaker and Ravi as listener.",
                "required": True,
                "min_quality": 0.65,
            },
            {
                "id": "contribution",
                "description": "States the location Ravi supplies.",
                "required": True,
                "min_quality": 0.65,
            },
        ],
        "concept_slots": [
            {
                "id": "attribution",
                "any_of": ["captain speaks to Ravi", "Ravi is the listener"],
            },
            {
                "id": "contribution",
                "any_of": ["key hanging beside the whistle"],
            },
        ],
    }
    generated = SchoolRubricEvaluation.model_validate({
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": activity["activity_id"],
        "skill_ids": activity["skill_ids"],
        "score": 0.8,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": "attribution",
                "met": True,
                "quality": 0.8,
                "evidence_quote": (
                    "The captain speaks first to Ravi and Ravi is the listener "
                    "in that line."
                ),
            },
            {
                "id": "contribution",
                "met": True,
                "quality": 0.8,
                "evidence_quote": (
                    "Ravi then contributes that he found the key hanging beside "
                    "the whistle."
                ),
            },
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The speakers and contribution are clear.",
    })

    async def fake_ollama_structured(prompt, schema, *, timeout):
        return generated

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(activity, answer)

    attribution = result.criteria[0]
    assert attribution.met is True
    assert attribution.evidence_quote in answer
    assert "evaluator_evidence_untraceable" not in result.blockers
    assert "semantic_required_claim_missing" not in result.blockers
    decision = curriculum.decide_open_answer_evaluation(
        activity,
        result,
        answer=answer,
    )
    assert decision["correct"] is True


@pytest.mark.asyncio
async def test_school_open_answer_uses_selected_nonlocal_provider(monkeypatch):
    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    captured: list[tuple[str, str, type]] = []

    async def fake_structured(operation, prompt, schema):
        captured.append((operation, prompt, schema))
        return schema.model_validate(_evaluation().model_dump(mode="python"))

    monkeypatch.setattr(open_answer_ai, "structured_generate", fake_structured)

    result = await open_answer_ai.evaluate_school_open_answer(
        ACTIVITY,
        LEARNER_ANSWER,
    )

    assert result.item_id == ACTIVITY["activity_id"]
    assert captured[0][0] == "school_open_answer"
    assert ACTIVITY["model_answer"] not in captured[0][1]


@pytest.mark.asyncio
async def test_school_open_answer_emits_latency_safe_dev_telemetry(monkeypatch):
    """Local timing must identify provider cost without logging learner text."""

    captured_logs: list[tuple[object, tuple[object, ...]]] = []

    class Logger:
        def warning(self, message, *args):
            captured_logs.append((message, args))

    class Settings:
        app_env = "dev"

    async def fake_structured(operation, prompt, schema):
        del operation, prompt
        return schema.model_validate(_evaluation().model_dump(mode="python"))

    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "get_settings", lambda: Settings())
    monkeypatch.setattr(open_answer_ai, "logger", Logger())
    monkeypatch.setattr(open_answer_ai, "structured_generate", fake_structured)

    await open_answer_ai.evaluate_school_open_answer(
        ACTIVITY,
        LEARNER_ANSWER,
    )

    assert len(captured_logs) == 1
    message, args = captured_logs[0]
    assert message == "school_open_answer_timing %s"
    telemetry = args[0]
    assert telemetry["item_id"] == ACTIVITY["activity_id"]
    assert telemetry["criteria_count"] == len(ACTIVITY["rubric_criteria"])
    assert telemetry["answer_chars"] == len(LEARNER_ANSWER)
    assert telemetry["prompt_chars"] > 0
    assert telemetry["provider_ms"] >= 0
    assert telemetry["validation_ms"] >= 0
    assert telemetry["total_ms"] >= telemetry["provider_ms"]
    assert LEARNER_ANSWER not in str(telemetry)
    assert ACTIVITY["passage"] not in str(telemetry)


@pytest.mark.asyncio
async def test_school_open_answer_forwards_an_explicit_worker_timeout(monkeypatch):
    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    captured: list[float | None] = []

    async def fake_structured(operation, prompt, schema, *, timeout=None):
        del operation, prompt
        captured.append(timeout)
        return schema.model_validate(_evaluation().model_dump(mode="python"))

    monkeypatch.setattr(open_answer_ai, "structured_generate", fake_structured)

    await open_answer_ai.evaluate_school_open_answer(
        ACTIVITY,
        LEARNER_ANSWER,
        timeout_seconds=17.5,
    )

    assert captured == [17.5]


@pytest.mark.asyncio
async def test_queued_school_jobs_leave_a_shared_llm_slot_for_career(monkeypatch):
    shared_slots = asyncio.Semaphore(2)
    school_slots = asyncio.Semaphore(1)
    school_started = asyncio.Event()
    second_school_processor_started = asyncio.Event()
    career_started = asyncio.Event()
    release_providers = asyncio.Event()
    school_provider_calls = 0

    class _QueuedJobStore:
        def __init__(self, job_id: str) -> None:
            self.job: dict[str, str] | None = {"job_id": job_id}

        async def claim_school_evaluation_job(self):
            claimed, self.job = self.job, None
            return claimed

    async def school_provider(operation, prompt, schema, *, timeout=None):
        del operation, prompt, timeout
        nonlocal school_provider_calls
        school_provider_calls += 1
        school_started.set()
        await release_providers.wait()
        return schema.model_validate(_evaluation().model_dump(mode="python"))

    async def career_provider(operation, prompt, schema):
        del operation, prompt
        career_started.set()
        await release_providers.wait()
        return schema.model_construct()

    monkeypatch.setattr(rate_limit, "llm_semaphore", shared_slots)
    monkeypatch.setattr(
        rate_limit,
        "school_evaluation_semaphore",
        school_slots,
        raising=False,
    )
    monkeypatch.setattr(
        open_answer_ai,
        "llm_semaphore",
        shared_slots,
        raising=False,
    )
    monkeypatch.setattr(calls, "llm_semaphore", shared_slots)
    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(calls, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "structured_generate", school_provider)
    monkeypatch.setattr(calls, "structured_generate", career_provider)

    async def queued_school_processor(job, *, second: bool = False) -> None:
        del job
        if second:
            second_school_processor_started.set()
        await open_answer_ai.evaluate_school_open_answer(ACTIVITY, LEARNER_ANSWER)

    first_school_task = asyncio.create_task(
        evaluation_jobs.run_one_school_evaluation_job(
            store=_QueuedJobStore("first"),
            processor=queued_school_processor,
            max_attempts=1,
        )
    )
    second_school_task = None
    career_task = None
    try:
        await asyncio.wait_for(school_started.wait(), timeout=0.5)
        second_school_task = asyncio.create_task(
            evaluation_jobs.run_one_school_evaluation_job(
                store=_QueuedJobStore("second"),
                processor=lambda job: queued_school_processor(job, second=True),
                max_attempts=1,
            )
        )
        await asyncio.wait_for(second_school_processor_started.wait(), timeout=0.5)
        await asyncio.sleep(0)

        career_task = asyncio.create_task(
            calls.evaluate_placement("Career placement", "A short writing sample.")
        )
        await asyncio.wait_for(career_started.wait(), timeout=0.5)

        assert school_provider_calls == 1
    finally:
        release_providers.set()
        await asyncio.gather(
            first_school_task,
            *(
                task
                for task in (second_school_task, career_task)
                if task is not None
            ),
            return_exceptions=True,
        )


@pytest.mark.asyncio
async def test_school_open_answer_requires_a_local_qwen_model(monkeypatch):
    class NonQwenSettings:
        ai_backend = "local"
        ollama_model = "llama3.2:latest"

    monkeypatch.setattr(open_answer_ai, "get_settings", lambda: NonQwenSettings())

    with pytest.raises(SchoolOpenAnswerRetryableError) as raised:
        await open_answer_ai.evaluate_school_open_answer(ACTIVITY, LEARNER_ANSWER)

    assert raised.value.code == "school_open_qwen_model_required"
    assert raised.value.evidence is None


@pytest.mark.asyncio
async def test_school_open_answer_preserves_gemini_pool_retry_after(monkeypatch):
    from app.ai.clients import GeminiKeyPoolExhaustedError

    async def rate_limited_provider(*args, **kwargs):
        raise GeminiKeyPoolExhaustedError(
            attempted_slots=(1, 2),
            retry_after_seconds=42.5,
        )

    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "structured_generate", rate_limited_provider)

    with pytest.raises(SchoolOpenAnswerRetryableError) as raised:
        await open_answer_ai.evaluate_school_open_answer(ACTIVITY, LEARNER_ANSWER)

    assert raised.value.code == "school_open_provider_failure"
    assert raised.value.retry_after_seconds == pytest.approx(42.5)


def test_legacy_calls_path_delegates_to_canonical_school_provider():
    assert calls.evaluate_school_open_answer is open_answer_ai.evaluate_school_open_answer
