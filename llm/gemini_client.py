import google.generativeai as genai

from config import settings
from llm.base import BaseLLM
from utils.timeouts import call_with_timeout

_TIMEOUT_SECONDS = 20


class GeminiLLM(BaseLLM):
    name = "gemini"

    def __init__(self, api_key: str = None, model: str = None):
        api_key = api_key or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing. Add it to your .env file.")
        genai.configure(api_key=api_key)
        self.model_name = model or settings.GEMINI_MODEL
        self._model = genai.GenerativeModel(self.model_name)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n\n{user_prompt}"

        def _call():
            return self._model.generate_content(prompt, request_options={"timeout": _TIMEOUT_SECONDS})

        try:
            response = call_with_timeout(_call, _TIMEOUT_SECONDS)
        except Exception as e:
            raise RuntimeError(f"Could not get a response from Gemini: {e}") from e
        return response.text.strip()