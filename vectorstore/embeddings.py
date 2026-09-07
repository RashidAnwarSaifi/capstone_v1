"""Embedding backend for the vector store: a local Hugging Face
sentence-transformer model (via the 'sentence-transformers' library, which
wraps HF `transformers` + the HF Hub download client). The model is
downloaded from the Hugging Face Hub the first time it's used and cached on
disk afterward - point HF_ENDPOINT at an internal Artifactory HF proxy if
huggingface.co isn't reachable from your network (see README's Setup)."""

import hashlib
import re

from config import settings
from utils.timeouts import call_with_timeout


class HashingEmbedder:
    """Deterministic, offline fallback that requires no native ML runtime."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * settings.EMBEDDING_DIM
            tokens = re.findall(r"[\w]+", text.lower())
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % settings.EMBEDDING_DIM
                vector[index] += 1.0
            norm = sum(value * value for value in vector) ** 0.5
            vectors.append([value / norm for value in vector] if norm else vector)
        return vectors

class HuggingFaceEmbedder:
    def __init__(self, model_name: str = None):
        model_name = model_name or settings.EMBEDDING_MODEL_NAME

        def _load():
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(model_name)

        try:
            self._model = call_with_timeout(_load, settings.EMBEDDING_LOAD_TIMEOUT_SECONDS)
        except TimeoutError:
            raise TimeoutError(
                f"Timed out after {settings.EMBEDDING_LOAD_TIMEOUT_SECONDS}s downloading the Hugging "
                f"Face embedding model '{model_name}'. Check your network access to "
                f"huggingface.co, or set HF_ENDPOINT to your Artifactory HF proxy."
            ) from None

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, show_progress_bar=False).tolist()


def get_embedder() -> HuggingFaceEmbedder:
    if settings.EMBEDDING_BACKEND in {"hashing", "offline"}:
        return HashingEmbedder()
    if settings.EMBEDDING_BACKEND in {"sentence_transformers", "huggingface", "hf"}:
        return HuggingFaceEmbedder()
    raise ValueError(
        f"Unknown embedding backend '{settings.EMBEDDING_BACKEND}'. "
        "Use 'hashing' or 'sentence_transformers'."
    )