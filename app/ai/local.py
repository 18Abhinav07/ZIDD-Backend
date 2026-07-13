"""Local Ollama backend — the dev/build AI layer.

Why this exists: the cloud free tiers throttle iteration. Gemini Flash-Lite
(structured eval) caps at 20 requests/DAY on the free tier, so a single test
session of the tutor loop exhausts the quota and the SSE turn 429-crashes
before the learner ever reaches bridge/strengthen/challenge/module-complete.

Local Ollama has no quota, so we build + tune the agent (routing, mastery EMA,
content shape) against a real model, then flip AI_BACKEND=cloud for the XPRIZE
submission. The agent/graph logic is provider-agnostic — only this file and the
branch points in `calls.py` know which backend is live.

Model: qwen2.5:14b (q4) — strong JSON + instruction-following on 24GB M4 Pro.
Uses /api/chat with `format=<pydantic json schema>` for structured output and
streamed deltas for pedagogy generations. Same httpx pattern as memory/embed.py.
"""
import asyncio
import json

import httpx
from pydantic import BaseModel, ValidationError

from app.config import get_settings

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
_NUM_CTX = 8192              # history + node prompt; default 4096 risks truncation
_KEEP_ALIVE = "30m"         # keep model resident; default 5m evicts mid-session
_NUM_PREDICT = 700          # cap pedagogy gen; stops rare runaway mid-sentence cut
_TRANSIENT_STATUS = {429, 500, 502, 503, 504}


def _model() -> str:
    return get_settings().ollama_model


def _is_transient_http_error(err: Exception) -> bool:
    if isinstance(err, httpx.RequestError):
        return True
    if isinstance(err, httpx.HTTPStatusError):
        return err.response.status_code in _TRANSIENT_STATUS
    return False


async def ollama_structured(
    prompt: str,
    schema_cls: type[BaseModel],
    max_retries: int = 2,
    server_retries: int = 3,
    base_delay: float = 0.25,
) -> BaseModel:
    """Structured JSON from local model, validated against `schema_cls`.

    Ollama honours `format` = a JSON schema and constrains decoding to it, so
    schema-fail is rare; we still validate + retry on ValidationError.
    """
    body = {
        "model": _model(),
        "messages": [{"role": "user", "content": prompt}],
        "format": schema_cls.model_json_schema(),
        "stream": False,
        "keep_alive": _KEEP_ALIVE,
        "options": {"temperature": 0.0, "num_ctx": _NUM_CTX},
    }
    last_err: Exception | None = None
    # Local structured evaluation is intentionally unbounded. A loaded 14B model
    # commonly needs 50-60 seconds and may take longer under memory pressure.
    async with httpx.AsyncClient(timeout=None) as client:
        for attempt in range(max_retries + 1):
            # temp 0 is deterministic, so a retry of the SAME body reproduces the
            # same bad parse. Nudge temperature up on each retry to vary output.
            body["options"]["temperature"] = 0.0 if attempt == 0 else 0.3 * attempt
            for server_attempt in range(server_retries + 1):
                try:
                    resp = await client.post(OLLAMA_CHAT_URL, json=body)
                    resp.raise_for_status()
                    break
                except Exception as err:
                    if not _is_transient_http_error(err) or server_attempt == server_retries:
                        raise
                    await asyncio.sleep(base_delay * (2 ** server_attempt))
            content = resp.json()["message"]["content"]
            try:
                return schema_cls.model_validate_json(content)
            except ValidationError as err:
                last_err = err
                if attempt == max_retries:
                    raise
                validation_errors = json.dumps(
                    err.errors(include_url=False, include_input=False),
                    ensure_ascii=False,
                    default=str,
                )
                body["messages"] = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            "Your JSON failed schema validation. Correct only the "
                            "invalid fields and return the complete JSON object again. "
                            "All score, confidence, and quality values must be decimals "
                            "from 0.0 to 1.0, never counts, percentages, or 1-to-5 "
                            "ratings. Return JSON only. Validation errors: "
                            f"{validation_errors}"
                        ),
                    },
                ]
    raise last_err  # unreachable; satisfies type checker


async def ollama_stream(
    prompt: str,
    temperature: float = 0.6,
    server_retries: int = 3,
    base_delay: float = 0.25,
):
    """Stream pedagogy text token-by-token from the local model."""
    body = {
        "model": _model(),
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "keep_alive": _KEEP_ALIVE,
        "options": {
            "temperature": temperature,
            "num_ctx": _NUM_CTX,
            "num_predict": _NUM_PREDICT,
            # Stop the model from hallucinating a fake multi-turn dialogue
            # (writing the learner's next line for them, then replying to it).
            "stop": ["\nuser:", "\nUser:", "\nassistant:", "\nAssistant:"],
        },
    }
    async with httpx.AsyncClient(timeout=None) as client:
        for server_attempt in range(server_retries + 1):
            try:
                async with client.stream("POST", OLLAMA_CHAT_URL, json=body) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        chunk = json.loads(line)
                        tok = chunk.get("message", {}).get("content")
                        if tok:
                            yield tok
                        if chunk.get("done"):
                            continue
                    return
            except Exception as err:
                if not _is_transient_http_error(err) or server_attempt == server_retries:
                    raise
                await asyncio.sleep(base_delay * (2 ** server_attempt))


async def ollama_complete(prompt: str, temperature: float = 0.3) -> str:
    """Full (non-streamed) completion — used for the end-of-session summary."""
    body = {
        "model": _model(),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "keep_alive": _KEEP_ALIVE,
        "options": {"temperature": temperature, "num_ctx": _NUM_CTX},
    }
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(OLLAMA_CHAT_URL, json=body)
        resp.raise_for_status()
        return resp.json()["message"]["content"] or ""
