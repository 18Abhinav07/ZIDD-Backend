import json

import httpx
import pytest
from pydantic import BaseModel, Field, field_validator


class TinyModel(BaseModel):
    ok: bool


class BoundedScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)


class NonEmptyFeedback(BaseModel):
    feedback: str

    @field_validator("feedback")
    @classmethod
    def feedback_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("feedback must be non-empty")
        return value


class _FakeStructuredResponse:
    def __init__(self, payload: dict | None = None, status_code: int = 200) -> None:
        self.payload = payload or {}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://ollama.test/api/chat")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("transient", request=request, response=response)

    def json(self) -> dict:
        return self.payload


class _FakeStreamResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://ollama.test/api/chat")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("transient", request=request, response=response)

    async def aiter_lines(self):
        yield json.dumps({"message": {"content": "Recovered"}, "done": False})
        yield json.dumps({"done": True})


@pytest.mark.asyncio
async def test_ollama_structured_retries_transient_http_status(monkeypatch):
    import app.ai.local as local

    class FakeClient:
        calls = 0

        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **_kwargs):
            FakeClient.calls += 1
            if FakeClient.calls == 1:
                return _FakeStructuredResponse(status_code=503)
            return _FakeStructuredResponse(
                {"message": {"content": TinyModel(ok=True).model_dump_json()}}
            )

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    result = await local.ollama_structured("prompt", TinyModel)

    assert result.ok is True
    assert FakeClient.calls == 2


@pytest.mark.asyncio
async def test_ollama_structured_uses_career_default_deadline(monkeypatch):
    import app.ai.local as local

    captured_timeouts = []

    class FakeClient:
        def __init__(self, *_args, **kwargs):
            captured_timeouts.append(kwargs.get("timeout"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **_kwargs):
            return _FakeStructuredResponse(
                {"message": {"content": TinyModel(ok=True).model_dump_json()}}
            )

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    result = await local.ollama_structured("prompt", TinyModel)

    assert result.ok is True
    assert captured_timeouts == [180.0]


@pytest.mark.asyncio
async def test_ollama_structured_retry_includes_schema_failure_feedback(monkeypatch):
    import app.ai.local as local

    captured_bodies = []

    class FakeClient:
        calls = 0

        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **kwargs):
            FakeClient.calls += 1
            captured_bodies.append(json.loads(json.dumps(kwargs["json"])))
            score = 4 if FakeClient.calls == 1 else 0.8
            return _FakeStructuredResponse(
                {"message": {"content": json.dumps({"score": score})}}
            )

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    result = await local.ollama_structured("score this", BoundedScore, max_retries=1)

    assert result.score == 0.8
    assert len(captured_bodies) == 2
    repair_message = captured_bodies[1]["messages"][-1]["content"]
    assert "failed schema validation" in repair_message
    assert "less_than_equal" in repair_message
    assert "0.0 to 1.0" in repair_message


@pytest.mark.asyncio
async def test_ollama_structured_serializes_validator_context_before_repair(monkeypatch):
    import app.ai.local as local

    captured_bodies = []

    class FakeClient:
        calls = 0

        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **kwargs):
            FakeClient.calls += 1
            captured_bodies.append(json.loads(json.dumps(kwargs["json"])))
            feedback = "" if FakeClient.calls == 1 else "Try the clue again."
            return _FakeStructuredResponse(
                {"message": {"content": json.dumps({"feedback": feedback})}}
            )

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    result = await local.ollama_structured(
        "give feedback",
        NonEmptyFeedback,
        max_retries=1,
    )

    assert result.feedback == "Try the clue again."
    assert len(captured_bodies) == 2
    repair_message = captured_bodies[1]["messages"][-1]["content"]
    assert "feedback must be non-empty" in repair_message


@pytest.mark.asyncio
async def test_ollama_stream_retries_before_first_token(monkeypatch):
    import app.ai.local as local

    class FakeClient:
        calls = 0

        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def stream(self, *_args, **_kwargs):
            FakeClient.calls += 1
            if FakeClient.calls == 1:
                return _FakeStreamResponse(status_code=503)
            return _FakeStreamResponse(status_code=200)

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    chunks = [chunk async for chunk in local.ollama_stream("prompt")]

    assert chunks == ["Recovered"]
    assert FakeClient.calls == 2


@pytest.mark.asyncio
async def test_ollama_stream_uses_career_default_deadline(monkeypatch):
    import app.ai.local as local

    captured_timeouts = []

    class FakeClient:
        def __init__(self, *_args, **kwargs):
            captured_timeouts.append(kwargs.get("timeout"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def stream(self, *_args, **_kwargs):
            return _FakeStreamResponse(status_code=200)

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    chunks = [chunk async for chunk in local.ollama_stream("prompt")]

    assert chunks == ["Recovered"]
    assert captured_timeouts == [300.0]


@pytest.mark.asyncio
async def test_ollama_complete_uses_career_default_deadline(monkeypatch):
    import app.ai.local as local

    captured_timeouts = []

    class FakeClient:
        def __init__(self, *_args, **kwargs):
            captured_timeouts.append(kwargs.get("timeout"))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def post(self, *_args, **_kwargs):
            return _FakeStructuredResponse(
                {"message": {"content": "Completed without a deadline"}}
            )

    monkeypatch.setattr(local.httpx, "AsyncClient", FakeClient)

    result = await local.ollama_complete("prompt")

    assert result == "Completed without a deadline"
    assert captured_timeouts == [180.0]
