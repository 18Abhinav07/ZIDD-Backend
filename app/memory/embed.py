"""Backend-selected 768-dimensional embeddings with graceful degradation."""
from dataclasses import dataclass

from app.ai.provider import get_ai_provider

EMBED_DIM = 768


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    provider: str
    model: str


async def embed_with_metadata(text: str) -> EmbeddingResult | None:
    if not text or not text.strip():
        return None
    try:
        vector, provider, model = await get_ai_provider().embed(text)
    except Exception:
        return None
    if len(vector) != EMBED_DIM:
        return None
    return EmbeddingResult(vector=vector, provider=provider, model=model)


async def embed(text: str) -> list[float] | None:
    """768-dim embedding, or None if Ollama is unavailable/misbehaving."""
    result = await embed_with_metadata(text)
    return result.vector if result is not None else None
