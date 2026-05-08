from __future__ import annotations
import httpx
from .base import LLMProvider, ChatMessage


class GroqProvider(LLMProvider):
    name = "groq"
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not configured.")
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[ChatMessage], temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(self.BASE_URL, json=payload, headers=headers)
            if r.status_code >= 400:
                raise RuntimeError(f"Groq error {r.status_code}: {r.text}")
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
