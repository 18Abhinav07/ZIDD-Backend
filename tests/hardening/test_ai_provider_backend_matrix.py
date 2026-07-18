from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
import json

import pytest
import requests
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.config import Settings


class TinyResult(BaseModel):
    value: str


class DefaultedResult(BaseModel):
    required_value: str
    optional_value: str = "fallback"


def test_settings_accepts_gemini_as_complete_backend() -> None:
    settings = Settings(
        ai_backend="gemini",
        _env_file=None,
    )

    assert settings.ai_backend == "gemini"


def test_settings_default_gemini_fallback_chain_and_school_cloud_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "GEMINI_TEXT_MODEL",
        "GEMINI_TEXT_FALLBACK_MODEL",
        "GEMINI_STRUCTURED_MODEL",
        "GEMINI_STRUCTURED_FALLBACK_MODEL",
        "SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)

    assert settings.gemini_text_model == "gemini-2.5-flash-lite"
    assert settings.gemini_text_fallback_model == "gemini-3.1-flash-lite"
    assert settings.gemini_structured_model == "gemini-2.5-flash-lite"
    assert settings.gemini_structured_fallback_model == "gemini-3.1-flash-lite"
    assert settings.school_open_answer_timeout_seconds == 20.0


def test_legacy_gemini_generation_default_uses_the_primary_lite_model() -> None:
    from app.ai.calls import GEMINI_FLASH

    assert GEMINI_FLASH == "gemini-2.5-flash-lite"


def test_numbered_gemini_credentials_discover_any_positive_index_in_stable_order() -> None:
    from app.ai import clients

    class IsolatedSettings:
        gemini_api_key = "legacy"
        gemini_api_key_1 = None
        gemini_api_key_2 = None
        gemini_api_key_3 = None
        gemini_api_key_4 = " fourth "
        gemini_api_key_5 = None

    assert clients.configured_gemini_api_keys(
        settings=IsolatedSettings(),
        dotenv_environment={
            "GEMINI_API_KEY_10": "dotenv-tenth",
            "GEMINI_API_KEY_2": "dotenv-second",
            "GEMINI_API_KEY_0": "ignore-zero",
            "GEMINI_API_KEY_x": "ignore-nonnumeric",
        },
        environment={
            "GEMINI_API_KEY_10": "tenth",
            "GEMINI_API_KEY_3": "third",
            "GEMINI_API_KEY_1": "first",
            "GEMINI_API_KEY_2": "first",
            "GEMINI_API_KEY_9": "ninth",
            "GEMINI_API_KEY_0": "ignore-zero-again",
            "GEMINI_API_KEY": "runtime-legacy",
        },
    ) == (
        "first",
        "third",
        "fourth",
        "ninth",
        "tenth",
        "runtime-legacy",
    )


@pytest.mark.asyncio
async def test_gemini_provider_falls_back_to_3_1_only_when_2_5_model_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    models: list[str] = []

    class Models:
        async def generate_content(self, *, model, **kwargs):
            del kwargs
            models.append(model)
            if model == "gemini-2.5-flash-lite":
                raise _api_error(404)
            return type("Response", (), {"text": "ready"})()

    class Client:
        aio = type("Async", (), {"models": Models()})()

    class ProviderSettings:
        gemini_text_model = "gemini-2.5-flash-lite"
        gemini_text_fallback_model = "gemini-3.1-flash-lite"
        gemini_request_timeout_seconds = 1.0

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager._clients = {0: Client()}  # noqa: SLF001 - deterministic client
    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    assert await provider_module.GeminiProvider().complete("teach", "help") == "ready"
    assert models == ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]


@pytest.mark.asyncio
async def test_gemini_structured_generation_falls_back_to_3_1_when_primary_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    models: list[str] = []

    class Models:
        async def generate_content(self, *, model, **kwargs):
            del kwargs
            models.append(model)
            if model == "gemini-2.5-flash-lite":
                raise _api_error(404)
            return type("Response", (), {"text": '{"value":"ready"}'})()

    class Client:
        aio = type("Async", (), {"models": Models()})()

    class ProviderSettings:
        gemini_structured_model = "gemini-2.5-flash-lite"
        gemini_structured_fallback_model = "gemini-3.1-flash-lite"
        gemini_request_timeout_seconds = 1.0

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager._clients = {0: Client()}  # noqa: SLF001 - deterministic client
    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    result = await provider_module.GeminiProvider().structured(
        "evaluate",
        "score this",
        TinyResult,
    )

    assert result == TinyResult(value="ready")
    assert models == ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]


@pytest.mark.asyncio
async def test_gemini_stream_falls_back_to_3_1_before_any_text_is_emitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    models: list[str] = []

    class SyncModels:
        def generate_content_stream(self, *, model, **kwargs):
            del kwargs
            models.append(model)
            if model == "gemini-2.5-flash-lite":
                raise _api_error(404)
            return iter([type("Chunk", (), {"text": "ready"})()])

    class Client:
        models = SyncModels()

    class ProviderSettings:
        gemini_text_model = "gemini-2.5-flash-lite"
        gemini_text_fallback_model = "gemini-3.1-flash-lite"
        gemini_request_timeout_seconds = 1.0

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager._clients = {0: Client()}  # noqa: SLF001 - deterministic client
    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    chunks = [
        chunk
        async for chunk in provider_module.GeminiProvider().stream(
            "teach",
            "help",
        )
    ]

    assert chunks == ["ready"]
    assert models == ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]


@pytest.mark.asyncio
async def test_gemini_provider_does_not_fallback_models_for_invalid_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    models: list[str] = []

    class Models:
        async def generate_content(self, *, model, **kwargs):
            del kwargs
            models.append(model)
            raise _api_error(400)

    class Client:
        aio = type("Async", (), {"models": Models()})()

    class ProviderSettings:
        gemini_text_model = "gemini-2.5-flash-lite"
        gemini_text_fallback_model = "gemini-3.1-flash-lite"
        gemini_request_timeout_seconds = 1.0

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager._clients = {0: Client()}  # noqa: SLF001 - deterministic client
    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    with pytest.raises(genai_errors.APIError) as caught:
        await provider_module.GeminiProvider().complete("teach", "help")

    assert caught.value.code == 400
    assert models == ["gemini-2.5-flash-lite"]


@pytest.mark.asyncio
async def test_health_reports_gemini_readiness_without_an_ollama_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api import health as health_module

    class Settings:
        ai_backend = "gemini"
        gemini_text_model = "gemini-2.5-flash-lite"
        gemini_text_fallback_model = "gemini-3.1-flash-lite"
        gemini_structured_model = "gemini-2.5-flash-lite"
        gemini_structured_fallback_model = "gemini-3.1-flash-lite"

    class Storage:
        async def ping_writable(self) -> bool:
            return True

    async def ollama_probe_must_not_run() -> bool:
        raise AssertionError("Gemini health must not probe Ollama")

    monkeypatch.setattr(health_module, "get_settings", lambda: Settings())
    monkeypatch.setattr(
        health_module,
        "configured_gemini_api_keys",
        lambda: ("configured-but-never-returned",),
    )
    monkeypatch.setattr(health_module, "get_storage", lambda: Storage())
    monkeypatch.setattr(health_module, "SessionStore", {})
    monkeypatch.setattr(health_module, "_ollama_reachable", ollama_probe_must_not_run)

    payload = await health_module.health()

    assert payload["ollama_reachable"] is None
    assert payload["ai"]["backend"] == "gemini"
    assert payload["ai"]["ready"] is True
    assert payload["ai"]["gemini_credential_count"] == 1
    assert "configured-but-never-returned" not in repr(payload)


@pytest.mark.asyncio
async def test_health_keeps_the_local_ollama_probe_for_qwen_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api import health as health_module

    class Settings:
        ai_backend = "local"
        ollama_base_url = "http://qwen.local:11434"

    class Storage:
        async def ping_writable(self) -> bool:
            return True

    probes: list[str] = []

    async def successful_ollama_probe(base_url: str) -> bool:
        probes.append(base_url)
        return True

    monkeypatch.setattr(health_module, "get_settings", lambda: Settings())
    monkeypatch.setattr(health_module, "get_storage", lambda: Storage())
    monkeypatch.setattr(health_module, "SessionStore", {})
    monkeypatch.setattr(health_module, "_ollama_reachable", successful_ollama_probe)

    payload = await health_module.health()

    assert probes == ["http://qwen.local:11434"]
    assert payload["ollama_reachable"] is True
    assert payload["ai"] == {"backend": "local", "ready": True}


def _api_error(status: int, *, retry_after: str | None = None):
    response = requests.Response()
    response.status_code = status
    response.reason = "test"
    response._content = json.dumps(  # noqa: SLF001 - requests test fixture
        {
            "error": {
                "code": status,
                "status": "RESOURCE_EXHAUSTED" if status == 429 else "UNAVAILABLE",
                "message": "test failure",
            }
        }
    ).encode()
    if retry_after is not None:
        response.headers["Retry-After"] = retry_after
    return genai_errors.APIError(status, response)


def test_gemini_credential_manager_applies_transient_cooldown_and_recovers() -> None:
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    now = [100.0]
    manager = GeminiCredentialManager(("one",), clock=lambda: now[0])

    manager.record_failure(
        attempted_slot=0,
        status=429,
        retry_after_seconds=75.0,
    )

    with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
        manager.request_client_with_slot()
    assert caught.value.retry_after_seconds == pytest.approx(75.0)

    now[0] += 75.0
    assert manager.request_client_with_slot()[0] == 0

    manager.record_failure(attempted_slot=0, status=503)
    with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
        manager.request_client_with_slot()
    assert caught.value.retry_after_seconds == pytest.approx(10.0)

    manager.record_success(0)
    assert manager.request_client_with_slot()[0] == 0


@pytest.mark.parametrize("status", [401, 403])
def test_gemini_credential_manager_permanently_disables_auth_failures(
    status: int,
) -> None:
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    manager = GeminiCredentialManager(("one",))

    manager.record_failure(attempted_slot=0, status=status)
    with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
        manager.request_client_with_slot()
    assert caught.value.retry_after_seconds is None


def test_gemini_rate_limit_cooldown_exponentially_caps_at_fifteen_minutes() -> None:
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    now = [0.0]
    manager = GeminiCredentialManager(("one",), clock=lambda: now[0])

    for expected_delay in (60.0, 120.0, 240.0, 480.0, 900.0, 900.0):
        manager.record_failure(attempted_slot=0, status=429)
        with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
            manager.request_client_with_slot()
        assert caught.value.retry_after_seconds == pytest.approx(expected_delay)
        now[0] += expected_delay


@pytest.mark.parametrize("status", [408, 500, 502, 503, 504])
def test_gemini_server_failure_cooldown_starts_at_five_seconds(status: int) -> None:
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager.record_failure(attempted_slot=0, status=status)

    with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
        manager.request_client_with_slot()
    assert caught.value.retry_after_seconds == pytest.approx(5.0)


def test_gemini_transient_cooldown_exponentially_caps_at_sixty_seconds() -> None:
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    now = [0.0]
    manager = GeminiCredentialManager(("one",), clock=lambda: now[0])

    for expected_delay in (5.0, 10.0, 20.0, 40.0, 60.0, 60.0):
        manager.record_failure(attempted_slot=0, status=503)
        with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
            manager.request_client_with_slot()
        assert caught.value.retry_after_seconds == pytest.approx(expected_delay)
        now[0] += expected_delay


def test_concurrent_credential_failure_does_not_skip_an_untried_key() -> None:
    from app.ai.clients import GeminiCredentialManager

    manager = GeminiCredentialManager(("one", "two", "three"))

    assert manager.rotate_after_status(401, attempted_slot=0) is True
    assert manager.active_slot == 1
    assert manager.rotate_after_status(401, attempted_slot=0) is True
    assert manager.active_slot == 1


def test_gemini_credential_manager_distributes_requests_across_all_healthy_keys() -> None:
    from app.ai.clients import GeminiCredentialManager

    manager = GeminiCredentialManager(("one", "two", "three"))

    slots = [manager.request_client_with_slot()[0] for _ in range(5)]

    assert slots == [0, 1, 2, 0, 1]

    assert manager.rotate_after_status(401, attempted_slot=1) is True
    slots_after_failure = [manager.request_client_with_slot()[0] for _ in range(4)]
    assert slots_after_failure == [2, 0, 2, 0]


@pytest.mark.asyncio
async def test_gemini_pool_uses_distinct_keys_for_429_then_503_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    manager = GeminiCredentialManager(("one", "two", "three"), clock=lambda: 0.0)
    manager._clients = {0: 0, 1: 1, 2: 2}  # noqa: SLF001 - deterministic clients
    calls: list[int] = []

    async def invoke(client: int) -> str:
        calls.append(client)
        if client == 0:
            raise _api_error(429)
        if client == 1:
            raise _api_error(503)
        return "ready"

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )

    result = await provider_module.GeminiProvider()._with_credentials(
        invoke,
        timeout=5.0,
    )

    assert result == "ready"
    assert calls == [0, 1, 2]


@pytest.mark.asyncio
async def test_gemini_pool_exhaustion_is_typed_and_finite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    manager = GeminiCredentialManager(
        ("one", "two", "three", "four", "five"),
        clock=lambda: 0.0,
    )
    manager._clients = {slot: slot for slot in range(5)}  # noqa: SLF001
    calls: list[int] = []

    async def invoke(client: int) -> str:
        calls.append(client)
        raise _api_error(429, retry_after="120")

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )

    with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
        await provider_module.GeminiProvider()._with_credentials(
            invoke,
            timeout=5.0,
        )

    assert calls == [0, 1, 2, 3, 4]
    assert caught.value.retry_after_seconds == pytest.approx(120.0)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 404, 422])
async def test_gemini_pool_does_not_rotate_invalid_requests(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: 0, 1: 1}  # noqa: SLF001
    calls: list[int] = []

    async def invoke(client: int) -> str:
        calls.append(client)
        raise _api_error(status)

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )

    with pytest.raises(genai_errors.APIError) as caught:
        await provider_module.GeminiProvider()._with_credentials(
            invoke,
            timeout=5.0,
        )

    assert caught.value.code == status
    assert calls == [0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        ConnectionError("offline"),
        TimeoutError(),
        requests.exceptions.ChunkedEncodingError("truncated stream"),
    ],
)
async def test_gemini_pool_rotates_transport_and_timeout_failures(
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: 0, 1: 1}  # noqa: SLF001
    calls: list[int] = []

    async def invoke(client: int) -> str:
        calls.append(client)
        if client == 0:
            raise failure
        return "ready"

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )

    assert (
        await provider_module.GeminiProvider()._with_credentials(
            invoke,
            timeout=5.0,
        )
        == "ready"
    )
    assert calls == [0, 1]


@pytest.mark.asyncio
async def test_gemini_pool_rotates_a_real_per_attempt_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: 0, 1: 1}  # noqa: SLF001
    calls: list[int] = []

    async def invoke(client: int) -> str:
        calls.append(client)
        if client == 0:
            await asyncio.sleep(0.05)
        return "ready"

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(
        provider_module,
        "_PER_KEY_ATTEMPT_TIMEOUT_SECONDS",
        0.005,
    )

    assert (
        await provider_module.GeminiProvider()._with_credentials(
            invoke,
            timeout=0.1,
        )
        == "ready"
    )
    assert calls == [0, 1]


@pytest.mark.asyncio
async def test_stale_concurrent_success_does_not_clear_newer_slot_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager, GeminiKeyPoolExhaustedError

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager._clients = {0: 0}  # noqa: SLF001 - deterministic client
    first_started = asyncio.Event()
    release_first = asyncio.Event()

    async def delayed_success(client: int) -> str:
        assert client == 0
        first_started.set()
        await release_first.wait()
        return "stale-success"

    async def newer_failure(client: int) -> str:
        assert client == 0
        raise _api_error(503)

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    provider = provider_module.GeminiProvider()
    delayed_task = asyncio.create_task(
        provider._with_credentials(delayed_success, timeout=1.0)
    )
    await first_started.wait()

    with pytest.raises(GeminiKeyPoolExhaustedError):
        await provider._with_credentials(newer_failure, timeout=1.0)

    release_first.set()
    assert await delayed_task == "stale-success"
    with pytest.raises(GeminiKeyPoolExhaustedError) as caught:
        manager.request_client_with_slot()
    assert caught.value.retry_after_seconds == pytest.approx(5.0)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["complete", "structured", "embed"])
async def test_gemini_public_operations_share_pool_failover(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    calls: list[tuple[str, int]] = []

    class Models:
        def __init__(self, slot: int):
            self.slot = slot

        async def generate_content(self, *, config, **kwargs):
            del kwargs
            call_kind = "structured" if "response_schema" in config else "complete"
            calls.append((call_kind, self.slot))
            if self.slot == 0:
                raise _api_error(503)
            text = '{"value":"ready"}' if "response_schema" in config else "ready"
            return type("Response", (), {"text": text})()

        async def embed_content(self, **kwargs):
            del kwargs
            calls.append(("embed", self.slot))
            if self.slot == 0:
                raise _api_error(503)
            embedding = type("Embedding", (), {"values": [0.5] * 768})()
            return type("Response", (), {"embeddings": [embedding]})()

    class Client:
        def __init__(self, slot: int):
            self.aio = type("Async", (), {"models": Models(slot)})()

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: Client(0), 1: Client(1)}  # noqa: SLF001

    class ProviderSettings:
        gemini_text_model = "gemini-test"
        gemini_structured_model = "gemini-test"
        gemini_embedding_model = "gemini-embedding-test"
        gemini_request_timeout_seconds = 1.0

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    provider = provider_module.GeminiProvider()
    if operation == "complete":
        assert await provider.complete("test", "help", timeout=1.0) == "ready"
    elif operation == "structured":
        assert await provider.structured("test", "help", TinyResult, timeout=1.0) == TinyResult(
            value="ready"
        )
    else:
        vector, source, model = await provider.embed("help")
        assert len(vector) == 768
        assert (source, model) == ("gemini", "gemini-embedding-test")

    assert calls == [(operation, 0), (operation, 1)]


@pytest.mark.asyncio
async def test_structured_schema_repair_uses_a_new_untried_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    calls: list[tuple[int, str]] = []

    class Models:
        def __init__(self, slot: int):
            self.slot = slot

        async def generate_content(self, *, contents, **kwargs):
            del kwargs
            calls.append((self.slot, contents))
            if self.slot == 0:
                raise _api_error(503)
            text = '{"wrong_field":"repair me"}' if self.slot == 1 else '{"value":"ready"}'
            return type("Response", (), {"text": text})()

    class Client:
        def __init__(self, slot: int):
            self.aio = type("Async", (), {"models": Models(slot)})()

    manager = GeminiCredentialManager(("one", "two", "three"), clock=lambda: 0.0)
    manager._clients = {  # noqa: SLF001 - deterministic clients
        slot: Client(slot) for slot in range(3)
    }

    class ProviderSettings:
        gemini_structured_model = "gemini-test"
        gemini_request_timeout_seconds = 1.0

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    result = await provider_module.GeminiProvider().structured(
        "test",
        "return the required value",
        TinyResult,
        timeout=1.0,
    )

    assert result == TinyResult(value="ready")
    assert [slot for slot, _prompt in calls] == [0, 1, 2]
    assert calls[1][1] == "return the required value"
    assert "corrected JSON object" in calls[2][1]
    assert '{"wrong_field":"repair me"}' in calls[2][1]


@dataclass
class _FakeProvider:
    streamed_operation: str | None = None
    completed_operation: str | None = None

    async def structured(
        self,
        operation: str,
        prompt: str,
        schema: type[BaseModel],
        *,
        timeout: float | None = None,
    ) -> BaseModel:
        del prompt, timeout
        return schema(value=operation)

    async def stream(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        del prompt, legacy_provider, legacy_model, timeout
        self.streamed_operation = operation
        yield "gemini-only"

    async def complete(
        self,
        operation: str,
        prompt: str,
        *,
        legacy_provider: str | None = None,
        legacy_model: str | None = None,
        timeout: float | None = None,
    ) -> str:
        del prompt, legacy_provider, legacy_model, timeout
        self.completed_operation = operation
        return "summary"

    async def embed(self, text: str) -> tuple[list[float], str, str]:
        del text
        return [0.25] * 768, "gemini", "gemini-embedding-2"


@pytest.mark.asyncio
async def test_stream_generation_routes_legacy_groq_spec_through_selected_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import calls

    provider = _FakeProvider()
    monkeypatch.setattr(calls, "_local", lambda: False)
    monkeypatch.setattr(calls, "get_ai_provider", lambda: provider)

    spec = calls.GenSpec(
        provider="groq",
        model="legacy-groq-model",
        prompt="teach",
        kind="teach",
    )
    chunks = [chunk async for chunk in calls.stream_generation(spec)]

    assert chunks == ["gemini-only"]
    assert provider.streamed_operation == "teach"


@pytest.mark.asyncio
async def test_memory_embedding_exposes_provider_metadata_and_768_dimensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.memory import embed as embedding

    provider = _FakeProvider()
    monkeypatch.setattr(embedding, "get_ai_provider", lambda: provider)

    result = await embedding.embed_with_metadata("remember this")

    assert result is not None
    assert len(result.vector) == 768
    assert result.provider == "gemini"
    assert result.model == "gemini-embedding-2"


@pytest.mark.asyncio
async def test_selected_provider_handles_structured_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module

    provider = _FakeProvider()
    monkeypatch.setattr(provider_module, "get_ai_provider", lambda: provider)

    result = await provider_module.structured_generate(
        "school_open_answer",
        "score it",
        TinyResult,
        timeout=8.0,
    )

    assert result == TinyResult(value="school_open_answer")


@pytest.mark.asyncio
async def test_career_probe_timeout_is_owned_and_recorded_by_gemini_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai import test_gen
    from app.ai.clients import GeminiCredentialManager
    from app.content.task_types import TaskType

    timeout_values: list[float | None] = []

    class Models:
        async def generate_content(self, **kwargs):
            del kwargs
            await asyncio.sleep(0.05)
            return type("Response", (), {"text": '{"items":[]}'})()

    class Client:
        aio = type("Async", (), {"models": Models()})()

    class Storage:
        async def get_weaknesses(self, user_id: str, task_type: str):
            del user_id, task_type
            return []

    class ProviderSettings:
        gemini_structured_model = "gemini-test"
        gemini_request_timeout_seconds = 1.0

    manager = GeminiCredentialManager(("one",), clock=lambda: 0.0)
    manager._clients = {0: Client()}  # noqa: SLF001 - deterministic client
    provider = provider_module.GeminiProvider()

    async def provider_owned_generate(operation, prompt, schema, *, timeout=None):
        timeout_values.append(timeout)
        return await provider.structured(
            operation,
            prompt,
            schema,
            timeout=timeout,
        )

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())
    monkeypatch.setattr(test_gen, "get_storage", lambda: Storage())
    monkeypatch.setattr(test_gen, "_local", lambda: False)
    monkeypatch.setattr(test_gen, "structured_generate", provider_owned_generate)
    monkeypatch.setattr(test_gen, "PROBE_GENERATION_TIMEOUT_SECONDS", 0.005)

    items = await test_gen.generate_test_items(
        "career-user",
        TaskType.INTERVIEW_TEST.value,
        career_context={
            "role_family": "software_technical",
            "primary_role": "Backend Software Engineer",
        },
    )

    assert items
    assert timeout_values == [0.005]
    assert manager._states[0].cooldown_until == pytest.approx(5.0)  # noqa: SLF001


@pytest.mark.asyncio
async def test_gemini_schema_removes_defaults_before_sdk_conversion() -> None:
    from app.ai.structured import call_with_structured_output

    captured = {}

    class Response:
        text = '{"required_value":"ready"}'

    class Models:
        async def generate_content(self, *, model, contents, config):
            captured["schema"] = config["response_schema"]
            return Response()

    class AsyncClient:
        models = Models()

    class Client:
        aio = AsyncClient()

    result = await call_with_structured_output(
        Client(),
        "return JSON",
        DefaultedResult,
        max_retries=0,
        server_retries=0,
    )

    def contains_default(value) -> bool:
        if isinstance(value, dict):
            return "default" in value or any(
                contains_default(item) for item in value.values()
            )
        if isinstance(value, list):
            return any(contains_default(item) for item in value)
        return False

    assert isinstance(captured["schema"], dict)
    assert contains_default(captured["schema"]) is False
    assert result == DefaultedResult(
        required_value="ready",
        optional_value="fallback",
    )


@pytest.mark.asyncio
async def test_structured_transport_failure_is_not_retried_on_the_same_key() -> None:
    from app.ai.structured import call_with_structured_output

    calls = 0

    class Models:
        async def generate_content(self, **kwargs):
            nonlocal calls
            del kwargs
            calls += 1
            raise _api_error(503)

    class AsyncClient:
        models = Models()

    class Client:
        aio = AsyncClient()

    with pytest.raises(genai_errors.APIError):
        await call_with_structured_output(
            Client(),
            "return JSON",
            TinyResult,
            max_retries=1,
            server_retries=9,
            base_delay=0,
        )

    assert calls == 1


def test_gemini_schema_flattens_school_literal_tuple_contract_for_pinned_sdk() -> None:
    from google.genai.types import Schema

    from app.ai.structured import _gemini_response_schema
    from app.services.school.open_answer_ai import _request_bound_evaluation_schema

    response_schema = _request_bound_evaluation_schema(
        schema_version="school.open.v1",
        item_id="item-1",
        skill_ids=["writing.summary_own_words"],
        criterion_ids=["main_idea_or_event", "essential_details"],
    )
    payload = _gemini_response_schema(response_schema)

    Schema.model_validate(payload)

    def keys(value) -> set[str]:
        if isinstance(value, dict):
            return set(value).union(*(keys(item) for item in value.values()))
        if isinstance(value, list):
            return set().union(*(keys(item) for item in value))
        return set()

    assert not {
        "$defs",
        "$ref",
        "additionalProperties",
        "anyOf",
        "const",
        "prefixItems",
    }.intersection(keys(payload))

    def assert_required_properties_exist(value) -> None:
        if isinstance(value, dict):
            required = set(value.get("required") or [])
            if required:
                assert required.issubset(set((value.get("properties") or {}).keys()))
            for item in value.values():
                assert_required_properties_exist(item)
        elif isinstance(value, list):
            for item in value:
                assert_required_properties_exist(item)

    assert_required_properties_exist(payload)


@pytest.mark.asyncio
async def test_structured_helper_never_repairs_on_the_same_client() -> None:
    from pydantic import ValidationError

    from app.ai.structured import call_with_structured_output

    prompts: list[str] = []

    class Response:
        text = '{"wrong_field":"not ready"}'

    class Models:
        async def generate_content(self, *, model, contents, config):
            del model, config
            prompts.append(contents)
            return Response()

    class AsyncClient:
        models = Models()

    class Client:
        aio = AsyncClient()

    with pytest.raises(ValidationError):
        await call_with_structured_output(
            Client(),
            "return the required value",
            TinyResult,
            max_retries=9,
            server_retries=0,
            base_delay=0,
        )

    assert len(prompts) == 1
    assert prompts[0] == "return the required value"


@pytest.mark.asyncio
async def test_legacy_cloud_preserves_authored_gemini_model(monkeypatch) -> None:
    from app.ai import provider as provider_module

    captured = {}

    class Chunk:
        text = "ready"

    async def stream_chunks():
        yield Chunk()

    class Models:
        async def generate_content_stream(self, *, model, contents, config):
            captured.update(model=model, contents=contents, config=config)
            return stream_chunks()

    class Client:
        class Async:
            models = Models()

        aio = Async()

    class Manager:
        def active_client_with_slot(self):
            return 0, Client()

        def rotate_after_status(self, status, *, attempted_slot=None):
            return False

    class ProviderSettings:
        ai_backend = "cloud"
        gemini_text_model = "global-cheap-model"

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: Manager(),
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    chunks = [
        chunk
        async for chunk in provider_module.LegacyCloudProvider().stream(
            "bridge",
            "help",
            legacy_provider="gemini",
            legacy_model="authored-gemini-model",
            timeout=1.0,
        )
    ]

    assert chunks == ["ready"]
    assert captured["model"] == "authored-gemini-model"


@pytest.mark.asyncio
async def test_gemini_stream_bridge_keeps_event_loop_responsive_and_rotates_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import threading
    import time

    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    loop_progress = threading.Event()
    first_attempt_observations: list[bool] = []
    calls: list[int] = []

    class BlockingStream:
        def __init__(self, slot: int):
            self.slot = slot
            self.done = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.done:
                raise StopAsyncIteration
            self.done = True
            calls.append(self.slot)
            if self.slot == 0:
                time.sleep(0.05)
                first_attempt_observations.append(loop_progress.is_set())
                return type("Chunk", (), {"text": "late"})()
            return type("Chunk", (), {"text": "ready"})()

    class AsyncModels:
        def __init__(self, slot: int):
            self.slot = slot

        async def generate_content_stream(self, **kwargs):
            del kwargs
            return BlockingStream(self.slot)

    class SyncModels:
        def __init__(self, slot: int):
            self.slot = slot

        def generate_content_stream(self, **kwargs):
            del kwargs

            def chunks():
                calls.append(self.slot)
                if self.slot == 0:
                    time.sleep(0.05)
                    first_attempt_observations.append(loop_progress.is_set())
                    yield type("Chunk", (), {"text": "late"})()
                else:
                    yield type("Chunk", (), {"text": "ready"})()

            return chunks()

    class Client:
        def __init__(self, slot: int):
            self.models = SyncModels(slot)
            self.aio = type("Async", (), {"models": AsyncModels(slot)})()

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: Client(0), 1: Client(1)}  # noqa: SLF001

    class ProviderSettings:
        gemini_text_model = "gemini-test"
        gemini_request_timeout_seconds = 1.0

    async def mark_loop_progress() -> None:
        await asyncio.sleep(0.001)
        loop_progress.set()

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())
    monkeypatch.setattr(provider_module, "_PER_KEY_ATTEMPT_TIMEOUT_SECONDS", 0.005)

    progress_task = asyncio.create_task(mark_loop_progress())
    chunks = [
        chunk
        async for chunk in provider_module.GeminiProvider().stream(
            "teach",
            "help",
            timeout=0.2,
        )
    ]
    await progress_task
    await asyncio.sleep(0.06)

    assert chunks == ["ready"]
    assert calls == [0, 1]
    assert first_attempt_observations == [True]


@pytest.mark.asyncio
async def test_gemini_stream_timeout_bounds_a_stalled_chunk(monkeypatch) -> None:
    import asyncio
    from app.ai import provider as provider_module

    async def stalled_stream():
        await asyncio.sleep(0.05)
        yield type("Chunk", (), {"text": "late"})()

    class Models:
        async def generate_content_stream(self, **kwargs):
            return stalled_stream()

    class Client:
        class Async:
            models = Models()

        aio = Async()

    class Manager:
        def active_client_with_slot(self):
            return 0, Client()

        def rotate_after_status(self, status, *, attempted_slot=None):
            return False

    class ProviderSettings:
        ai_backend = "gemini"
        gemini_text_model = "gemini-test"
        gemini_request_timeout_seconds = 0.001

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: Manager(),
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    with pytest.raises(TimeoutError):
        _ = [
            chunk
            async for chunk in provider_module.GeminiProvider().stream(
                "teach",
                "help",
                timeout=None,
            )
        ]


@pytest.mark.asyncio
async def test_gemini_stream_rotates_chunked_encoding_error_before_first_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    calls: list[int] = []

    async def broken_stream():
        raise requests.exceptions.ChunkedEncodingError("truncated stream")
        yield  # pragma: no cover - keeps this an async generator

    async def successful_stream():
        yield type("Chunk", (), {"text": "ready"})()

    class AsyncModels:
        def __init__(self, slot: int):
            self.slot = slot

        async def generate_content_stream(self, **kwargs):
            del kwargs
            calls.append(self.slot)
            return broken_stream() if self.slot == 0 else successful_stream()

    class SyncModels:
        def __init__(self, slot: int):
            self.slot = slot

        def generate_content_stream(self, **kwargs):
            del kwargs
            calls.append(self.slot)

            def chunks():
                if self.slot == 0:
                    raise requests.exceptions.ChunkedEncodingError("truncated stream")
                yield type("Chunk", (), {"text": "ready"})()

            return chunks()

    class Client:
        def __init__(self, slot: int):
            self.models = SyncModels(slot)
            self.aio = type("Async", (), {"models": AsyncModels(slot)})()

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: Client(0), 1: Client(1)}  # noqa: SLF001

    class ProviderSettings:
        gemini_text_model = "gemini-test"
        gemini_request_timeout_seconds = 1.0

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    chunks = [
        chunk
        async for chunk in provider_module.GeminiProvider().stream(
            "teach",
            "help",
            timeout=1.0,
        )
    ]

    assert chunks == ["ready"]
    assert calls == [0, 1]
    assert manager._states[0].cooldown_until == pytest.approx(5.0)  # noqa: SLF001


@pytest.mark.asyncio
async def test_gemini_stream_rotates_only_before_first_emitted_text(monkeypatch) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    calls: list[int] = []

    async def successful_stream():
        yield type("Chunk", (), {"text": "ready"})()

    class Models:
        def __init__(self, slot: int):
            self.slot = slot

        async def generate_content_stream(self, **kwargs):
            del kwargs
            calls.append(self.slot)
            if self.slot == 0:
                raise _api_error(503)
            return successful_stream()

    class Client:
        def __init__(self, slot: int):
            self.aio = type("Async", (), {"models": Models(slot)})()

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: Client(0), 1: Client(1)}  # noqa: SLF001

    class ProviderSettings:
        gemini_text_model = "gemini-test"
        gemini_request_timeout_seconds = 1.0

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    chunks = [
        chunk
        async for chunk in provider_module.GeminiProvider().stream(
            "teach",
            "help",
            timeout=1.0,
        )
    ]

    assert chunks == ["ready"]
    assert calls == [0, 1]


@pytest.mark.asyncio
async def test_gemini_stream_records_failure_after_text_without_replaying(monkeypatch) -> None:
    from app.ai import provider as provider_module
    from app.ai.clients import GeminiCredentialManager

    async def broken_stream():
        yield type("Chunk", (), {"text": "partial"})()
        raise requests.exceptions.ChunkedEncodingError("truncated stream")

    class Models:
        async def generate_content_stream(self, **kwargs):
            del kwargs
            return broken_stream()

    class SyncModels:
        def generate_content_stream(self, **kwargs):
            del kwargs

            def chunks():
                yield type("Chunk", (), {"text": "partial"})()
                raise requests.exceptions.ChunkedEncodingError("truncated stream")

            return chunks()

    class Client:
        models = SyncModels()
        aio = type("Async", (), {"models": Models()})()

    manager = GeminiCredentialManager(("one", "two"), clock=lambda: 0.0)
    manager._clients = {0: Client(), 1: object()}  # noqa: SLF001

    class ProviderSettings:
        gemini_text_model = "gemini-test"
        gemini_request_timeout_seconds = 1.0

    monkeypatch.setattr(
        provider_module,
        "get_gemini_credential_manager",
        lambda: manager,
    )
    monkeypatch.setattr(provider_module, "get_settings", lambda: ProviderSettings())

    seen: list[str] = []
    with pytest.raises(requests.exceptions.ChunkedEncodingError):
        async for chunk in provider_module.GeminiProvider().stream(
            "teach",
            "help",
            timeout=1.0,
        ):
            seen.append(chunk)

    assert seen == ["partial"]
    assert manager._states[0].cooldown_until == pytest.approx(5.0)  # noqa: SLF001
    assert manager.request_client_with_slot()[0] == 1
