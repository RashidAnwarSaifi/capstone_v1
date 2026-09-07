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
        def _call(model: str):
            return self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )

        models = (self.model,) + tuple(
            model for model in settings.GROQ_FALLBACK_MODELS if model != self.model
        )
        errors = []
        for model in models:
            try:
                return call_with_timeout(lambda: _call(model), _TIMEOUT_SECONDS).choices[0].message.content.strip()
            except Exception as error:
                errors.append(f"{model}: {error}")
                if "model_not_found" not in str(error) and "does not exist" not in str(error):
                    break
        raise RuntimeError("Could not get a response from Groq. " + " | ".join(errors)) from None