"""The AI execution boundary.

Every real model call goes through here. Graph nodes build a `GenSpec`
(which model, what prompt) but never call a provider directly — so tests
monkeypatch the three functions below and exercise the full loop offline.

Model routing (architecture-v3 §59 routing table):
  evaluate   -> Gemini Flash-Lite (structured JSON)
  teach      -> Groq 70B
  bridge     -> Gemini Flash
  strengthen -> Gemini Flash
  redirect   -> Gemini Flash   (fluent-but-off-task steer-back)
  ease       -> Gemini Flash   (graceful off-ramp after long fail run)
  challenge  -> Groq 70B
  summary    -> Groq 70B
"""
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.clients import get_gemini_client, get_groq_client
from app.ai.local import ollama_complete, ollama_stream, ollama_structured
from app.ai.behaviors import behavior_for
from app.ai.prompts import (
    build_eval_prompt,
    build_placement_prompt,
    build_simulation_score_prompt,
    build_summary_prompt,
    build_teach_game_prompt,
)
from app.ai.schemas import DiagnosisEval, FillBlankGame, PlacementEval, SimulationReport
from app.ai.structured import call_with_structured_output
from app.config import get_settings
from app.content.schema import Concept
from app.content.task_types import TaskType

GROQ_70B = "llama-3.3-70b-versatile"
GROQ_8B = "llama-3.1-8b-instant"
GEMINI_FLASH = "gemini-flash-latest"  # 2.0-flash free tier zeroed; 2.5-flash stream 503s (2026)


def _local() -> bool:
    """True when the local Ollama backend is active (dev/build)."""
    return get_settings().ai_backend == "local"


@dataclass(frozen=True)
class GenSpec:
    """A pending streamed generation the service will execute."""

    provider: str   # "groq" | "gemini"
    model: str
    prompt: str
    kind: str       # opening | teach | bridge | strengthen | redirect | ease | challenge


from app.middleware.rate_limit import llm_semaphore

async def evaluate_answer(
    node: Concept, messages: list[dict], user_input: str
) -> DiagnosisEval:
    """Structured assessment of the latest learner answer."""
    prompt = build_eval_prompt(node, messages, user_input)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, DiagnosisEval)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, DiagnosisEval)


async def evaluate_placement(module_title: str, writing_sample: str) -> PlacementEval:
    """Structured CEFR estimate from an onboarding writing sample."""
    prompt = build_placement_prompt(module_title, writing_sample)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, PlacementEval)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, PlacementEval)


async def evaluate_simulation(
    task_type: TaskType, topic: str, messages: list[dict]
) -> SimulationReport:
    """Structured end-of-session score for a TEST-mode simulation.

    Test sessions are scored, not coached mid-stream; this runs once at the end
    over the whole transcript with the task's (strict) behavior pack."""
    prompt = build_simulation_score_prompt(behavior_for(task_type), topic, messages)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, SimulationReport)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, SimulationReport)


async def generate_game_item(
    node: Concept, diagnosis: dict, coach: dict | None = None
) -> FillBlankGame:
    """Gamified fill-blank for scaffold turns (scaffold >= 1).

    Structured call — same pattern as evaluate_answer. Returns FillBlankGame;
    teach_node stores it as pending_game in state (no pending/stream GenSpec)."""
    prompt = build_teach_game_prompt(node, diagnosis, coach)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, FillBlankGame)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, FillBlankGame)


async def stream_generation(spec: GenSpec) -> AsyncIterator[str]:
    """Stream a pedagogy generation token-by-token from the chosen provider."""
    async with llm_semaphore:
        if _local():
            async for chunk in ollama_stream(spec.prompt):
                yield chunk
            return
        if spec.provider == "groq":
            async for chunk in _stream_groq(spec.model, spec.prompt):
                yield chunk
        elif spec.provider == "gemini":
            async for chunk in _stream_gemini(spec.model, spec.prompt):
                yield chunk
        else:  # pragma: no cover - guard
            raise ValueError(f"unknown provider: {spec.provider}")


async def _stream_groq(model: str, prompt: str) -> AsyncIterator[str]:
    client = get_groq_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def _stream_gemini(model: str, prompt: str) -> AsyncIterator[str]:
    client = get_gemini_client()
    stream = await client.aio.models.generate_content_stream(
        model=model, contents=prompt
    )
    async for chunk in stream:
        if chunk.text:
            yield chunk.text


async def summarize_session(node: Concept, messages: list[dict]) -> str:
    """Writes the <=200-token memory summary at session end."""
    prompt = build_summary_prompt(node, messages)
    async with llm_semaphore:
        if _local():
            return await ollama_complete(prompt)
        client = get_groq_client()
        resp = await client.chat.completions.create(
            model=GROQ_70B,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""
