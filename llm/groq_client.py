from groq import Groq

from config import settings
from llm.base import BaseLLM
from utils.timeouts import call_with_timeout

_TIMEOUT_SECONDS = 20


class GroqLLM(BaseLLM):
    name = "groq"

    def __init__(self, api_key: str = None, model: str = None):
        api_key = api_key or settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")
        self.model = model or settings.GROQ_MODEL
        self._client = Groq(api_key=api_key, timeout=_TIMEOUT_SECONDS)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        def _call():
            return self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )

        try:
            response = call_with_timeout(_call, _TIMEOUT_SECONDS)
        except Exception as e:
            raise RuntimeError(f"Could not get a response from Groq: {e}") from e
        return response.choices[0].message.content.strip()