import json

import httpx
import pytest
from pydantic import BaseModel


class TinyModel(BaseModel):
    ok: bool


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
