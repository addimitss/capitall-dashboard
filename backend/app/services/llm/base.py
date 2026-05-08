from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def chat(self, messages: list[ChatMessage], temperature: float = 0.2) -> str: ...
