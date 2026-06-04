"""Embeddings via local Ollama (nomic-embed-text, 768-dim).

Local + free — keeps the $300 GCP credit for infra, not embeddings, and the
Gemini quota for tutoring. The whole memory layer degrades gracefully: if
Ollama is not running, embed() returns None and callers skip vector memory
rather than crashing the turn.
"""
import httpx

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768
_TIMEOUT = 5.0


async def embed(text: str) -> list[float] | None:
    """768-dim embedding, or None if Ollama is unavailable/misbehaving."""
    if not text or not text.strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": text}
            )
            resp.raise_for_status()
            vec = resp.json().get("embedding")
    except (httpx.HTTPError, ValueError, KeyError):
        return None
    if not isinstance(vec, list) or len(vec) != EMBED_DIM:
        return None
    return vec
