"""AI client factories. Single-key dev; key-pool rotation added at scale."""
from functools import lru_cache

from groq import AsyncGroq
from google import genai

from app.config import get_settings


@lru_cache
def get_gemini_client() -> genai.Client:
    """Gemini client (Flash diagnose/eval). Async via client.aio.*."""
    return genai.Client(api_key=get_settings().gemini_api_key)


@lru_cache
def get_groq_client() -> AsyncGroq:
    """Groq client (70B teach / challenge / GD peers)."""
    return AsyncGroq(api_key=get_settings().groq_api_key)
