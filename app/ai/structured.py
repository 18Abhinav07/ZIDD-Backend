"""Flash-Lite structured-output helper.

Council verdict (ITEM 5): Flash-Lite 2.0 is reliable for structured JSON
(~0.39% schema-fail), BUT it ignores schema `description` fields. Rules:
  - put instructions in the prompt, NOT in schema descriptions
  - keep schema string fields < 200 tokens
  - validate + retry (max 2) on ValidationError
  - retry with backoff on transient server errors (503/429/500) — Flash-Lite
    free tier returns 503 UNAVAILABLE under load; without this the whole turn
    crashes the SSE stream
  - model = gemini-2.5-flash-lite (NOT non-lite flash for structured output)
"""
import asyncio

from google.genai import errors as genai_errors
from pydantic import BaseModel, ValidationError

STRUCTURED_MODEL = "gemini-2.5-flash-lite"  # 2.0-flash-lite free tier zeroed (2026)

_TRANSIENT_STATUS = {429, 500, 502, 503, 504}  # retryable server-side codes


async def call_with_structured_output(
    client,
    prompt: str,
    schema_cls: type[BaseModel],
    max_retries: int = 2,
    server_retries: int = 3,
    base_delay: float = 0.5,
) -> BaseModel:
    """Call Flash-Lite for structured JSON.

    Two independent retry budgets:
      - server_retries: transient API errors (503/429/...) with exp backoff
      - max_retries: schema ValidationError on the returned JSON
    """
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        response = await _generate_with_backoff(
            client, prompt, schema_cls, server_retries, base_delay
        )
        try:
            return schema_cls.model_validate_json(response.text)
        except ValidationError as err:
            last_err = err
            if attempt == max_retries:
                raise
    raise last_err  # unreachable; satisfies type checker


async def _generate_with_backoff(
    client,
    prompt: str,
    schema_cls: type[BaseModel],
    server_retries: int,
    base_delay: float,
):
    """generate_content with exp backoff on transient server errors."""
    last_err: Exception | None = None
    for attempt in range(server_retries + 1):
        try:
            return await client.aio.models.generate_content(
                model=STRUCTURED_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema_cls,
                },
            )
        except genai_errors.APIError as err:
            if getattr(err, "code", None) not in _TRANSIENT_STATUS:
                raise
            last_err = err
            if attempt == server_retries:
                raise
            await asyncio.sleep(base_delay * (2 ** attempt))
    raise last_err  # unreachable; satisfies type checker
