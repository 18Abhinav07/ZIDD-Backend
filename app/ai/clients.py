"""AI client factories. Single-key dev; key-pool rotation added at scale."""
from functools import lru_cache

from groq import AsyncGroq
from google import genai

from app.config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client:
    """Gemini client (Flash diagnose/eval). Async via client.aio.*."""
    api_key = get_settings().gemini_api_key
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set; required when calling the Gemini client."
        )
    return genai.Client(api_key=api_key)


@lru_cache
def get_groq_client() -> AsyncGroq:
    """Groq client (70B teach / challenge / GD peers)."""
    api_key = get_settings().groq_api_key
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set; required when calling the Groq client."
        )
    return AsyncGroq(api_key=api_key)
