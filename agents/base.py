"""Common interface every agent implements, so the chat UI can run any
combination of agents (single or multi-select) the same way."""

from abc import ABC, abstractmethod

from llm.base import BaseLLM
from vectorstore.store import VectorStore


class BaseAgent(ABC):
    key: str = "base"
    label: str = "Base Agent"
    description: str = ""

    @abstractmethod
    def run(
        self,
        query: str,
        chat_history: list[dict],
        llm: BaseLLM,
        vectorstore: VectorStore,
        sources: list[str] | None = None,
    ) -> dict:
        """Return {"answer": str, "sources": list[str], "trace": dict}."""
        raise NotImplementedError