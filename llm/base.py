"""Common interface every LLM backend must implement. Keeping this contract
small is what makes swapping Groq for Gemini/Cohere/an enterprise LLM a
one-file change (add a new client + one branch in factory.py)."""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send a system + user prompt to the LLM and return the text reply."""
        raise NotImplementedError