import pytest
from pydantic import ValidationError

from app.ai import calls
from app.ai.prompts import build_school_open_answer_prompt
from app.config import Settings
from app.content.school.content_schema import SchoolRubricEvaluation
from app.services.school import open_answer_ai
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

    assert local_settings.ai_backend == "local"
    assert cloud_settings.ai_backend == "cloud"
    monkeypatch.setattr(calls, "get_settings", lambda: local_settings)
    assert calls._local() is True

    with pytest.raises(ValidationError):
        Settings(ai_backend="gemini")

LEARNER_ANSWER = (
    "The parrot crossed the trees and found a quiet garden. It warned the other "
    "birds about the trader, so they moved deeper into the forest."
)


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
    assert "evidence_quote" in prompt
    assert "Do not decide progression, readiness, mastery, unlocks, or pass/fail" in prompt


@pytest.mark.asyncio
async def test_local_school_open_answer_dispatches_authoritative_schema_once(monkeypatch):
    captured = []

    async def fake_ollama_structured(prompt, schema):
        captured.append((prompt, schema))
        return _evaluation()

    async def unexpected_cloud_call(*args, **kwargs):
        raise AssertionError("cloud provider must not be called for local evaluation")

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)
    monkeypatch.setattr(
        open_answer_ai,
        "call_with_structured_output",
        unexpected_cloud_call,
    )

    result = await open_answer_ai.evaluate_school_open_answer(ACTIVITY, LEARNER_ANSWER)

    assert result == _evaluation()
    assert len(captured) == 1
    prompt, schema = captured[0]
    assert schema is SchoolRubricEvaluation
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

    async def fake_ollama_structured(prompt, schema):
        captured.append(prompt)
        return _evaluation().model_copy(
            update={"item_id": activity["activity_id"]},
        )

    monkeypatch.setattr(open_answer_ai, "_local", lambda: True)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", fake_ollama_structured)

    result = await open_answer_ai.evaluate_school_open_answer(activity, LEARNER_ANSWER)

    assert result.item_id == activity["activity_id"]
    assert f'"item_id": "{activity["activity_id"]}"' in captured[0]


@pytest.mark.asyncio
async def test_cloud_school_open_answer_dispatches_authoritative_schema_once(monkeypatch):
    client = object()
    captured = []

    async def unexpected_local_call(*args, **kwargs):
        raise AssertionError("local provider must not be called for cloud evaluation")

    async def fake_cloud_call(provider_client, prompt, schema):
        captured.append((provider_client, prompt, schema))
        return _evaluation()

    monkeypatch.setattr(open_answer_ai, "_local", lambda: False)
    monkeypatch.setattr(open_answer_ai, "get_gemini_client", lambda: client)
    monkeypatch.setattr(open_answer_ai, "ollama_structured", unexpected_local_call)
    monkeypatch.setattr(open_answer_ai, "call_with_structured_output", fake_cloud_call)

    result = await open_answer_ai.evaluate_school_open_answer(ACTIVITY, LEARNER_ANSWER)

    assert result == _evaluation()
    assert len(captured) == 1
    provider_client, prompt, schema = captured[0]
    assert provider_client is client
    assert schema is SchoolRubricEvaluation
    assert ACTIVITY["model_answer"] not in prompt
    for criterion in ACTIVITY["rubric_criteria"]:
        assert criterion["id"] in prompt
        assert criterion["description"] in prompt


def test_legacy_calls_path_delegates_to_canonical_school_provider():
    assert calls.evaluate_school_open_answer is open_answer_ai.evaluate_school_open_answer
