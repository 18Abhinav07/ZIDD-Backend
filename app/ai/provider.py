"""Single runtime boundary for local, Gemini-only, and legacy cloud AI."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
import logging
import queue
import threading
import time
from typing import Protocol, TypeVar

import httpx
from google.genai import errors as genai_errors
from pydantic import BaseModel, ValidationError
from requests import exceptions as requests_exceptions

from app.ai.clients import (
    GeminiKeyPoolExhaustedError,
    get_gemini_credential_manager,
    get_groq_client,
)
from app.ai.local import ollama_complete, ollama_stream, ollama_structured
from app.ai.structured import (
    _generate_once,
    _schema_repair_prompt,
    structured_output_token_limit,
)
from app.config import get_settings

T = TypeVar("T", bound=BaseModel)
_AUTH_FAILURE_STATUS = {401, 403}
_RATE_LIMIT_STATUS = {429}
_TRANSIENT_STATUS = {408, 500, 502, 503, 504}
_NON_RETRYABLE_CLIENT_STATUS = {400, 404, 422}
_MODEL_UNAVAILABLE_STATUS = {404}
_DEFAULT_GEMINI_CREDENTIAL_ATTEMPT_TIMEOUT_SECONDS = 8.0
_EMBED_DIMENSION = 768
_DEFAULT_TEXT_OUTPUT_TOKENS = 640
_TEXT_OUTPUT_TOKENS_BY_OPERATION = {
    "bridge": 480,
    "challenge": 640,
    "ease": 400,
    "health_probe": 16,
    "opening": 420,
    "redirect": 360,
    "summary": 384,
    "teach": 640,
}

logger = logging.getLogger(__name__)


@dataclass
class _GeminiRuntimeState:
    state: str = "unverified"
    last_model: str | None = None
    last_failure: str | None = None


_gemini_runtime_state = _GeminiRuntimeState()
_gemini_runtime_lock = threading.Lock()


def _gemini_failure_code(exc: BaseException) -> str:
    status = _api_status(exc)
    return f"http_{status}" if status is not None else type(exc).__name__


def _mark_gemini_runtime_success(model: str) -> None:
    with _gemini_runtime_lock:
        _gemini_runtime_state.state = "ready"
        _gemini_runtime_state.last_model = model
        _gemini_runtime_state.last_failure = None


def _mark_gemini_runtime_failure(model: str, exc: BaseException) -> None:
    with _gemini_runtime_lock:
        _gemini_runtime_state.state = "degraded" if (
            _gemini_runtime_state.last_model is not None
        ) else "unavailable"
        _gemini_runtime_state.last_model = model
        _gemini_runtime_state.last_failure = _gemini_failure_code(exc)


def _should_mark_gemini_runtime_failure(exc: BaseException) -> bool:
    return (
        isinstance(exc, GeminiKeyPoolExhaustedError)
        or _retryable_failure(exc) is not None
    )


def gemini_runtime_status() -> dict[str, object]:
    """Return safe, process-local Gemini readiness without exposing credentials."""

    with _gemini_runtime_lock:
        return {
            "state": _gemini_runtime_state.state,
            "ready": _gemini_runtime_state.state == "ready",
            "last_model": _gemini_runtime_state.last_model,
            "last_failure": _gemini_runtime_state.last_failure,
        }


def _log_gemini_call(
    *,
    operation: str,
    model: str,
    outcome: str,
    started_at: float,
    fallback_index: int,
    error: BaseException | None = None,
) -> None:
    """Emit latency-safe operator telemetry without prompts, answers, or keys."""

    fields = {
        "operation": operation,
        "model": model,
        "outcome": outcome,
        "elapsed_ms": round((time.perf_counter() - started_at) * 1000),
        "fallback_index": fallback_index,
    }
    if error is not None:
        fields["failure"] = _gemini_failure_code(error)
    logger.info("gemini_call %s", fields)


def _text_output_token_limit(operation: str) -> int:
    return _TEXT_OUTPUT_TOKENS_BY_OPERATION.get(
        str(operation or "").strip(),
        _DEFAULT_TEXT_OUTPUT_TOKENS,
    )


def _api_status(exc: BaseException) -> int | None:
    value = getattr(exc, "code", None)
    if value is None:
        value = getattr(exc, "status_code", None)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _request_client_with_slot(
    manager,
    attempted_slots: set[int],
    *,
    quota_scope: str | None = None,
):
    selector = getattr(manager, "request_client_with_slot", None)
    if selector is not None:
        if quota_scope is not None:
            try:
                return selector(
                    attempted_slots=attempted_slots,
                    quota_scope=quota_scope,
                )
            except TypeError as exc:
                if "quota_scope" not in str(exc):
                    raise
        try:
            return selector(attempted_slots=attempted_slots)
        except TypeError as exc:
            if "attempted_slots" not in str(exc):
                raise
            return selector()
    selector = manager.active_client_with_slot
    if quota_scope is not None:
        try:
            return selector(quota_scope=quota_scope)
        except TypeError as exc:
            if "quota_scope" not in str(exc):
                raise
    return selector()


def _request_attempt_with_slot(
    manager,
    attempted_slots: set[int],
    *,
    quota_scope: str | None = None,
) -> tuple[int, object, int | None]:
    selector = getattr(manager, "request_attempt_with_slot", None)
    if selector is not None:
        if quota_scope is not None:
            try:
                return selector(
                    attempted_slots=attempted_slots,
                    quota_scope=quota_scope,
                )
            except TypeError as exc:
                if "quota_scope" not in str(exc):
                    raise
        try:
            return selector(attempted_slots=attempted_slots)
        except TypeError as exc:
            if "attempted_slots" not in str(exc):
                raise
            return selector()
    slot, client = _request_client_with_slot(
        manager,
        attempted_slots,
        quota_scope=quota_scope,
    )
    return slot, client, None


def _duration_seconds(value) -> float | None:
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("s"):
            normalized = normalized[:-1]
        try:
            return max(0.0, float(normalized))
        except ValueError:
            return None
    if isinstance(value, dict):
        seconds = value.get("seconds", 0)
        nanos = value.get("nanos", 0)
        try:
            return max(0.0, float(seconds) + float(nanos) / 1_000_000_000)
        except (TypeError, ValueError):
            return None
    return None


def _retry_delay_from_details(value) -> float | None:
    if isinstance(value, dict):
        for key in ("retryDelay", "retry_delay", "retryAfter", "retry_after"):
            if key in value:
                delay = _duration_seconds(value[key])
                if delay is not None:
                    return delay
        for nested in value.values():
            delay = _retry_delay_from_details(nested)
            if delay is not None:
                return delay
    elif isinstance(value, list):
        for nested in value:
            delay = _retry_delay_from_details(nested)
            if delay is not None:
                return delay
    return None


def _retry_after_seconds(exc: BaseException) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    header_value = headers.get("Retry-After") if headers is not None else None
    if header_value:
        delay = _duration_seconds(header_value)
        if delay is not None:
            return delay
        try:
            retry_at = parsedate_to_datetime(str(header_value))
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            pass
    return _retry_delay_from_details(getattr(exc, "details", None))


def _is_transport_failure(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            httpx.TimeoutException,
            httpx.TransportError,
            requests_exceptions.Timeout,
            requests_exceptions.ConnectionError,
            requests_exceptions.ChunkedEncodingError,
        ),
    )


def _retryable_failure(
    exc: BaseException,
) -> tuple[int | None, float | None, bool] | None:
    if isinstance(exc, genai_errors.APIError):
        status = _api_status(exc)
        if status in _MODEL_UNAVAILABLE_STATUS:
            return status, None, False
        if status in _NON_RETRYABLE_CLIENT_STATUS:
            return None
        if status in _AUTH_FAILURE_STATUS | _RATE_LIMIT_STATUS | _TRANSIENT_STATUS:
            return status, _retry_after_seconds(exc), False
        return None
    if _is_transport_failure(exc):
        return None, None, True
    return None


def _model_unavailable(exc: BaseException) -> bool:
    """Only a missing model moves an operation to its configured fallback."""

    return (
        isinstance(exc, genai_errors.APIError)
        and _api_status(exc) in _MODEL_UNAVAILABLE_STATUS
    )


def _can_fallback_to_next_model(exc: BaseException) -> bool:
    """A model can fall back when absent or all keys hit its model-local quota."""

    return _model_unavailable(exc) or (
        isinstance(exc, GeminiKeyPoolExhaustedError)
        and (
            exc.retry_after_seconds is not None
            or exc.model_unavailable
        )
    )


def _model_chain(primary: object, fallback: object) -> tuple[str, ...]:
    """Return a stable, de-duplicated primary/fallback model sequence."""

    models: list[str] = []
    for raw_model in (primary, fallback):
        model = str(raw_model or "").strip()
        if model and model not in models:
            models.append(model)
    if not models:
        raise RuntimeError("gemini_model_chain_empty")
    return tuple(models)


def _record_failure(
    manager,
    *,
    slot: int,
    status: int | None,
    retry_after_seconds: float | None,
    transport_failure: bool,
    quota_scope: str | None = None,
) -> bool:
    recorder = getattr(manager, "record_failure", None)
    if recorder is not None:
        kwargs = {
            "attempted_slot": slot,
            "status": status,
            "retry_after_seconds": retry_after_seconds,
            "transport_failure": transport_failure,
        }
        if quota_scope is not None:
            try:
                recorder(**kwargs, quota_scope=quota_scope)
                return True
            except TypeError as exc:
                if "quota_scope" not in str(exc):
                    raise
        recorder(
            **kwargs,
        )
        return True
    rotator = getattr(manager, "rotate_after_status", None)
    if rotator is None:
        return False
    if quota_scope is not None:
        try:
            return bool(rotator(status, attempted_slot=slot, quota_scope=quota_scope))
        except TypeError as exc:
            if "quota_scope" not in str(exc):
                raise
    return bool(rotator(status, attempted_slot=slot))


def _record_success(
    manager,
    slot: int,
    failure_epoch: int | None = None,
    *,
    quota_scope: str | None = None,
) -> None:
    guarded_recorder = getattr(manager, "record_success_if_current", None)
    if guarded_recorder is not None and failure_epoch is not None:
        if quota_scope is not None:
            try:
                guarded_recorder(slot, failure_epoch, quota_scope=quota_scope)
                return
            except TypeError as exc:
                if "quota_scope" not in str(exc):
                    raise
        guarded_recorder(slot, failure_epoch)
        return
    recorder = getattr(manager, "record_success", None)
    if recorder is not None:
        if quota_scope is not None:
            try:
                recorder(slot, quota_scope=quota_scope)
                return
            except TypeError as exc:
                if "quota_scope" not in str(exc):
                    raise
        recorder(slot)


def _remaining_seconds(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    remaining = deadline - asyncio.get_running_loop().time()
    if remaining <= 0:
        raise TimeoutError
    return remaining


def _attempt_timeout(
    deadline: float | None,
    credential_attempt_timeout_seconds: float,
) -> float | None:
    remaining = _remaining_seconds(deadline)
    if remaining is None:
        return None
    return min(remaining, credential_attempt_timeout_seconds)


async def _threaded_gemini_stream(
    client,
    *,
    model: str,
    prompt: str,
    request_timeout: float | None,
    max_output_tokens: int,
) -> AsyncIterator[object]:
    """Bridge the pinned SDK's blocking stream iterator into asyncio."""

    loop = asyncio.get_running_loop()
    messages: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=1)
    ready = asyncio.Event()
    stopped = threading.Event()
    config: dict[str, object] = {
        "temperature": 0.6,
        "max_output_tokens": max_output_tokens,
    }
    if request_timeout is not None:
        config["http_options"] = {
            "timeout": max(1, int(request_timeout * 1000)),
        }

    def notify() -> None:
        try:
            loop.call_soon_threadsafe(ready.set)
        except RuntimeError:
            pass

    def enqueue(kind: str, value: object) -> bool:
        while not stopped.is_set():
            try:
                messages.put((kind, value), timeout=0.05)
            except queue.Full:
                continue
            notify()
            return True
        return False

    def consume_sync_stream() -> None:
        stream = client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=config,
        )
        try:
            for chunk in stream:
                if not enqueue("chunk", chunk):
                    return
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                close()

    async def consume_async_stream() -> None:
        stream = await client.aio.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=config,
        )
        try:
            async for chunk in stream:
                if not enqueue("chunk", chunk):
                    return
        finally:
            close = getattr(stream, "aclose", None)
            if close is not None:
                await close()

    def produce() -> None:
        try:
            sync_models = getattr(client, "models", None)
            sync_generate = getattr(sync_models, "generate_content_stream", None)
            if callable(sync_generate):
                consume_sync_stream()
            else:
                asyncio.run(consume_async_stream())
        except BaseException as exc:
            enqueue("error", exc)
            return
        enqueue("done", None)

    worker = threading.Thread(
        target=produce,
        name="gemini-stream-bridge",
        daemon=True,
    )
    worker.start()

    async def receive() -> tuple[str, object]:
        while True:
            try:
                return messages.get_nowait()
            except queue.Empty:
                ready.clear()
                try:
                    return messages.get_nowait()
                except queue.Empty:
                    if not worker.is_alive():
                        try:
                            return messages.get_nowait()
                        except queue.Empty as exc:
                            raise RuntimeError(
                                "gemini_stream_worker_ended_without_result"
                            ) from exc
                    await ready.wait()

    try:
        while True:
            kind, value = await receive()
            if kind == "chunk":
                yield value
            elif kind == "error":
                if isinstance(value, BaseException):
                    raise value
                raise RuntimeError("gemini_stream_worker_invalid_error")
            else:
                return
    finally:
        stopped.set()
        ready.set()


class AIProvider(Protocol):
    async def structured(
        self,
        operation: str,
        prompt: str,
        schema: type[T],
        *,
        timeout: float | None = None,
    ) -> T: ...

    def stream(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]: ...

    async def complete(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> str: ...

    async def embed(self, text: str) -> tuple[list[float], str, str]: ...


class OllamaQwenProvider:
    async def structured(
        self,
        operation: str,
        prompt: str,
        schema: type[T],
        *,
        timeout: float | None = None,
    ) -> T:
        del operation
        return await ollama_structured(prompt, schema, timeout=timeout)

    async def stream(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        del operation, legacy_provider, legacy_model
        async for chunk in ollama_stream(prompt, timeout=timeout):
            yield chunk

    async def complete(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> str:
        del operation, legacy_provider, legacy_model
        return await ollama_complete(prompt, timeout=timeout)

    async def embed(self, text: str) -> tuple[list[float], str, str]:
        settings = get_settings()
        url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json={"model": "nomic-embed-text", "prompt": text},
            )
            response.raise_for_status()
            vector = response.json().get("embedding")
        if not isinstance(vector, list) or len(vector) != _EMBED_DIMENSION:
            raise ValueError("invalid_ollama_embedding")
        return [float(value) for value in vector], "ollama", "nomic-embed-text"


class GeminiProvider:
    def _request_timeout(self, timeout: float | None) -> float:
        if timeout is not None:
            return timeout
        return float(getattr(get_settings(), "gemini_request_timeout_seconds", 180.0))

    def _credential_attempt_timeout_seconds(
        self,
        request_timeout_seconds: float | None,
    ) -> float:
        """Resolve the credential cap once per caller-owned Gemini operation."""

        configured = float(
            getattr(
                get_settings(),
                "gemini_credential_attempt_timeout_seconds",
                _DEFAULT_GEMINI_CREDENTIAL_ATTEMPT_TIMEOUT_SECONDS,
            )
        )
        if request_timeout_seconds is not None:
            configured = min(configured, request_timeout_seconds / 2)
        return max(0.001, configured)

    def _text_model_chain(
        self,
        legacy_provider: str | None,
        legacy_model: str | None,
    ) -> tuple[str, ...]:
        del legacy_provider, legacy_model
        settings = get_settings()
        return _model_chain(
            settings.gemini_text_model,
            getattr(settings, "gemini_text_fallback_model", "gemini-3.1-flash-lite"),
        )

    def _structured_model_chain(self) -> tuple[str, ...]:
        settings = get_settings()
        return _model_chain(
            settings.gemini_structured_model,
            getattr(
                settings,
                "gemini_structured_fallback_model",
                "gemini-3.1-flash-lite",
            ),
        )

    async def _with_model_fallback(self, models, invoke, *, operation: str):
        """Try the next model when the current model or its quota is unavailable."""

        model_chain = tuple(models)
        started_at = time.perf_counter()
        for index, model in enumerate(model_chain):
            try:
                result = await invoke(model)
            except Exception as exc:
                if _should_mark_gemini_runtime_failure(exc):
                    _mark_gemini_runtime_failure(model, exc)
                _log_gemini_call(
                    operation=operation,
                    model=model,
                    outcome="failure",
                    started_at=started_at,
                    fallback_index=index,
                    error=exc,
                )
                if index + 1 >= len(model_chain) or not _can_fallback_to_next_model(exc):
                    raise
            else:
                _mark_gemini_runtime_success(model)
                _log_gemini_call(
                    operation=operation,
                    model=model,
                    outcome="success",
                    started_at=started_at,
                    fallback_index=index,
                )
                return result
        raise RuntimeError("gemini_model_chain_exhausted")  # pragma: no cover

    async def _with_credentials(
        self,
        call,
        *,
        timeout: float | None = None,
        quota_scope: str | None = None,
    ):
        manager = get_gemini_credential_manager()
        attempted_slots: set[int] = set()
        deadline = (
            asyncio.get_running_loop().time() + timeout
            if timeout is not None
            else None
        )
        return await self._with_credential_context(
            call,
            manager=manager,
            attempted_slots=attempted_slots,
            deadline=deadline,
            credential_attempt_timeout_seconds=(
                self._credential_attempt_timeout_seconds(timeout)
            ),
            quota_scope=quota_scope,
        )

    async def _with_credential_context(
        self,
        call,
        *,
        manager,
        attempted_slots: set[int],
        deadline: float | None,
        credential_attempt_timeout_seconds: float,
        quota_scope: str | None = None,
    ):
        while True:
            _remaining_seconds(deadline)
            slot, client, failure_epoch = _request_attempt_with_slot(
                manager,
                attempted_slots,
                quota_scope=quota_scope,
            )
            if slot in attempted_slots:
                raise GeminiKeyPoolExhaustedError(attempted_slots=attempted_slots)
            attempted_slots.add(slot)
            try:
                attempt_timeout = _attempt_timeout(
                    deadline,
                    credential_attempt_timeout_seconds,
                )
                if attempt_timeout is None:
                    result = await call(client)
                else:
                    async with asyncio.timeout(attempt_timeout):
                        result = await call(client)
            except Exception as exc:
                failure = _retryable_failure(exc)
                # A bare client call has no model scope. Its 404 is an invalid
                # request and must retain the old fail-fast behavior; only a
                # model-scoped generation may quarantine that model per key.
                if (
                    failure is not None
                    and failure[0] in _MODEL_UNAVAILABLE_STATUS
                    and quota_scope is None
                ):
                    raise
                if failure is None:
                    raise
                status, retry_after, transport_failure = failure
                if not _record_failure(
                    manager,
                    slot=slot,
                    status=status,
                    retry_after_seconds=retry_after,
                    transport_failure=transport_failure,
                    quota_scope=quota_scope,
                ):
                    raise
                continue
            _record_success(
                manager,
                slot,
                failure_epoch,
                quota_scope=quota_scope,
            )
            return result

    async def structured(
        self,
        operation: str,
        prompt: str,
        schema: type[T],
        *,
        timeout: float | None = None,
    ) -> T:
        request_timeout = self._request_timeout(timeout)
        deadline = asyncio.get_running_loop().time() + request_timeout
        credential_attempt_timeout_seconds = self._credential_attempt_timeout_seconds(
            request_timeout
        )
        output_token_limit = structured_output_token_limit(operation)

        async def invoke_for_model(model: str) -> T:
            manager = get_gemini_credential_manager()
            attempted_slots: set[int] = set()
            request_prompt = prompt

            for repair_attempt in range(2):
                response_text = ""

                async def invoke(client):
                    nonlocal response_text
                    response = await _generate_once(
                        client,
                        request_prompt,
                        schema,
                        model=model,
                        max_output_tokens=output_token_limit,
                    )
                    response_text = str(getattr(response, "text", "") or "")
                    return schema.model_validate_json(response_text)

                try:
                    return await self._with_credential_context(
                        invoke,
                        manager=manager,
                        attempted_slots=attempted_slots,
                        deadline=deadline,
                        credential_attempt_timeout_seconds=(
                            credential_attempt_timeout_seconds
                        ),
                        quota_scope=model,
                    )
                except ValidationError as exc:
                    if repair_attempt == 1:
                        raise
                    request_prompt = _schema_repair_prompt(
                        prompt,
                        response_text,
                        exc,
                    )

            raise RuntimeError("structured_repair_budget_exhausted")

        return await self._with_model_fallback(
            self._structured_model_chain(),
            invoke_for_model,
            operation=operation,
        )

    async def stream(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        request_timeout = self._request_timeout(timeout)
        deadline = asyncio.get_running_loop().time() + request_timeout
        credential_attempt_timeout_seconds = self._credential_attempt_timeout_seconds(
            request_timeout
        )
        output_token_limit = _text_output_token_limit(operation)

        model_chain = self._text_model_chain(legacy_provider, legacy_model)
        started_at = time.perf_counter()
        for index, model in enumerate(model_chain):
            emitted_for_model = False
            try:
                async for chunk in self._stream_model(
                    model,
                    prompt,
                    deadline=deadline,
                    credential_attempt_timeout_seconds=(
                        credential_attempt_timeout_seconds
                    ),
                    max_output_tokens=output_token_limit,
                ):
                    emitted_for_model = True
                    yield chunk
                _mark_gemini_runtime_success(model)
                _log_gemini_call(
                    operation=operation,
                    model=model,
                    outcome="success",
                    started_at=started_at,
                    fallback_index=index,
                )
                return
            except Exception as exc:
                if _should_mark_gemini_runtime_failure(exc):
                    _mark_gemini_runtime_failure(model, exc)
                _log_gemini_call(
                    operation=operation,
                    model=model,
                    outcome="failure",
                    started_at=started_at,
                    fallback_index=index,
                    error=exc,
                )
                if (
                    emitted_for_model
                    or not _can_fallback_to_next_model(exc)
                    or index + 1 >= len(model_chain)
                ):
                    raise
        raise RuntimeError("gemini_model_chain_exhausted")  # pragma: no cover

    async def _stream_model(
        self,
        model: str,
        prompt: str,
        *,
        deadline: float,
        credential_attempt_timeout_seconds: float,
        max_output_tokens: int,
    ) -> AsyncIterator[str]:
        manager = get_gemini_credential_manager()
        attempted_slots: set[int] = set()
        emitted = False
        while True:
            _remaining_seconds(deadline)
            slot, client, failure_epoch = _request_attempt_with_slot(
                manager,
                attempted_slots,
                quota_scope=model,
            )
            if slot in attempted_slots:
                raise GeminiKeyPoolExhaustedError(attempted_slots=attempted_slots)
            attempted_slots.add(slot)
            try:
                attempt_timeout = _attempt_timeout(
                    deadline,
                    credential_attempt_timeout_seconds,
                )
                attempt_deadline = (
                    asyncio.get_running_loop().time() + attempt_timeout
                    if attempt_timeout is not None
                    else None
                )
                stream = _threaded_gemini_stream(
                    client,
                    model=model,
                    prompt=prompt,
                    request_timeout=attempt_timeout,
                    max_output_tokens=max_output_tokens,
                )
                iterator = stream.__aiter__()
                try:
                    while True:
                        try:
                            # The first token is still the per-key attempt. Once
                            # text is visible, keep the remaining whole-call
                            # budget rather than resetting the timeout per chunk.
                            chunk_timeout = _remaining_seconds(
                                attempt_deadline if not emitted else deadline
                            )
                            chunk = await asyncio.wait_for(
                                anext(iterator),
                                chunk_timeout,
                            )
                        except StopAsyncIteration:
                            break
                        text = getattr(chunk, "text", None)
                        if text:
                            emitted = True
                            yield text
                finally:
                    close = getattr(iterator, "aclose", None)
                    if close is not None:
                        await close()
                _record_success(
                    manager,
                    slot,
                    failure_epoch,
                    quota_scope=model,
                )
                return
            except Exception as exc:
                failure = _retryable_failure(exc)
                if failure is None:
                    raise
                status, retry_after, transport_failure = failure
                recorded = _record_failure(
                    manager,
                    slot=slot,
                    status=status,
                    retry_after_seconds=retry_after,
                    transport_failure=transport_failure,
                    quota_scope=model,
                )
                if emitted or not recorded:
                    raise
                continue

    async def complete(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> str:
        request_timeout = self._request_timeout(timeout)
        deadline = asyncio.get_running_loop().time() + request_timeout
        credential_attempt_timeout_seconds = self._credential_attempt_timeout_seconds(
            request_timeout
        )
        output_token_limit = _text_output_token_limit(operation)

        async def invoke_for_model(model: str) -> str:
            manager = get_gemini_credential_manager()
            attempted_slots: set[int] = set()

            async def invoke(client):
                return await client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "temperature": 0.3,
                        "max_output_tokens": output_token_limit,
                    },
                )

            response = await self._with_credential_context(
                invoke,
                manager=manager,
                attempted_slots=attempted_slots,
                deadline=deadline,
                credential_attempt_timeout_seconds=(
                    credential_attempt_timeout_seconds
                ),
                quota_scope=model,
            )
            return str(getattr(response, "text", "") or "")

        return await self._with_model_fallback(
            self._text_model_chain(legacy_provider, legacy_model),
            invoke_for_model,
            operation=operation,
        )

    async def embed(self, text: str) -> tuple[list[float], str, str]:
        settings = get_settings()
        request_timeout = self._request_timeout(None)

        async def invoke(client):
            return await client.aio.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
                config={"output_dimensionality": _EMBED_DIMENSION},
            )

        response = await self._with_credentials(
            invoke,
            timeout=request_timeout,
            quota_scope=settings.gemini_embedding_model,
        )
        embeddings = list(getattr(response, "embeddings", None) or [])
        values = list(getattr(embeddings[0], "values", None) or []) if embeddings else []
        if len(values) != _EMBED_DIMENSION:
            raise ValueError("invalid_gemini_embedding")
        return (
            [float(value) for value in values],
            "gemini",
            settings.gemini_embedding_model,
        )


class LegacyCloudProvider(GeminiProvider):
    def _text_model_chain(
        self,
        legacy_provider: str | None,
        legacy_model: str | None,
    ) -> tuple[str, ...]:
        if legacy_provider == "gemini" and legacy_model:
            settings = get_settings()
            if legacy_model == settings.gemini_text_model:
                return _model_chain(
                    legacy_model,
                    getattr(
                        settings,
                        "gemini_text_fallback_model",
                        "gemini-3.1-flash-lite",
                    ),
                )
            return (legacy_model,)
        return super()._text_model_chain(legacy_provider, legacy_model)

    async def stream(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        if legacy_provider != "groq":
            async for chunk in super().stream(
                operation,
                prompt,
                legacy_provider=legacy_provider,
                legacy_model=legacy_model,
                timeout=timeout,
            ):
                yield chunk
            return
        client = get_groq_client()
        stream = await client.chat.completions.create(
            model=legacy_model or "llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def complete(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> str:
        if legacy_provider != "groq":
            return await super().complete(
                operation,
                prompt,
                legacy_provider=legacy_provider,
                legacy_model=legacy_model,
                timeout=timeout,
            )
        client = get_groq_client()
        response = await client.chat.completions.create(
            model=legacy_model or "llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""


@lru_cache(maxsize=3)
def _provider_for_backend(backend: str) -> AIProvider:
    if backend == "local":
        return OllamaQwenProvider()
    if backend == "gemini":
        return GeminiProvider()
    if backend == "cloud":
        return LegacyCloudProvider()
    raise RuntimeError(f"unsupported_ai_backend:{backend}")


def get_ai_provider() -> AIProvider:
    return _provider_for_backend(get_settings().ai_backend)


async def structured_generate(
    operation: str,
    prompt: str,
    schema: type[T],
    *,
    timeout: float | None = None,
) -> T:
    return await get_ai_provider().structured(
        operation,
        prompt,
        schema,
        timeout=timeout,
    )


async def warm_gemini_provider(*, timeout: float = 5.0) -> dict[str, object]:
    """Probe the configured cloud chain once during boot without learner data.

    A configured key is not evidence that the selected model is available to
    its Google project. The health endpoint consumes this process-local result
    so deployment checks do not claim readiness until a real generation works.
    """

    settings = get_settings()
    if settings.ai_backend not in {"gemini", "cloud"}:
        return gemini_runtime_status()
    bounded_timeout = max(1.0, min(float(timeout), 5.0))
    try:
        await GeminiProvider().complete(
            "health_probe",
            "Return exactly: ready",
            timeout=bounded_timeout,
        )
    except Exception as exc:
        _mark_gemini_runtime_failure(settings.gemini_text_model, exc)
        logger.warning(
            "gemini_warmup_failed %s",
            {"failure": _gemini_failure_code(exc)},
        )
    return gemini_runtime_status()


def reset_ai_provider() -> None:
    _provider_for_backend.cache_clear()
    with _gemini_runtime_lock:
        _gemini_runtime_state.state = "unverified"
        _gemini_runtime_state.last_model = None
        _gemini_runtime_state.last_failure = None
