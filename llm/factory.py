"""Single entry point the rest of the app uses to get an LLM instance.

Switching providers is just changing LLM_PROVIDER in .env - or, at runtime,
picking a different provider in the Settings page, which passes an
`overrides` dict here. Every backend implements the same BaseLLM.generate(),
so no other code in the app needs to change when the provider changes.
Default is "groq"; "gemini" is the secondary option.
"""

import json

from config import settings
from llm.base import BaseLLM

_PROVIDERS = {
    "groq": "llm.groq_client.GroqLLM",
    "gemini": "llm.gemini_client.GeminiLLM",
}

_llm_cache: dict[str, BaseLLM] = {}


def _import_class(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


def _build(provider: str, overrides: dict) -> BaseLLM:
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. Choose one of: {list(_PROVIDERS)}"
        )

    llm_class = _import_class(_PROVIDERS[provider])

    if provider == "groq":
        kwargs = {
            "api_key": overrides.get("groq_api_key") or None,
            "model": overrides.get("groq_model") or None,
        }
    else:
        kwargs = {
            "api_key": overrides.get("gemini_api_key") or None,
            "model": overrides.get("gemini_model") or None,
        }

    return llm_class(**kwargs)


def get_llm(overrides: dict | None = None) -> BaseLLM:
    """Return a cached LLM instance for the given provider + overrides.

    `overrides` mirrors what the Settings page lets a user edit (provider,
    api keys, model names). Missing/empty fields fall back to `.env`
    defaults inside each client. Instances are cached by
    provider+overrides so repeated calls with the same settings (e.g. every
    chat turn) reuse the same client instead of re-authenticating each time.
    """
    overrides = overrides or {}
    provider = (overrides.get("provider") or settings.LLM_PROVIDER).strip().lower()

    cache_key = provider + "|" + json.dumps(overrides, sort_keys=True)
    if cache_key not in _llm_cache:
        _llm_cache[cache_key] = _build(provider, overrides)
    return _llm_cache[cache_key]