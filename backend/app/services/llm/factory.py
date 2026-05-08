from __future__ import annotations
from functools import lru_cache
from ...config import settings
from .base import LLMProvider
from .groq_provider import GroqProvider
from .bedrock_provider import BedrockProvider


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    p = settings.LLM_PROVIDER.lower()
    if p == "groq":
        return GroqProvider(settings.GROQ_API_KEY, settings.GROQ_MODEL)
    if p == "bedrock":
        return BedrockProvider(settings.AWS_REGION, settings.BEDROCK_MODEL_ID)
    raise RuntimeError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}")
