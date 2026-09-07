"""Embedding backend for the vector store: a local Hugging Face
sentence-transformer model (via the 'sentence-transformers' library, which
wraps HF `transformers` + the HF Hub download client). The model is
downloaded from the Hugging Face Hub the first time it's used and cached on
disk afterward - point HF_ENDPOINT at an internal Artifactory HF proxy if
huggingface.co isn't reachable from your network (see README's Setup)."""

from config import settings
from utils.timeouts import call_with_timeout

# huggingface_hub retries each file check up to 5 times with exponential
# backoff (23s), and a model load checks several files - a genuinely
# unreachable Hub can otherwise block for 1-2+ minutes with no feedback.
_LOAD_TIMEOUT_SECONDS = 20


class HuggingFaceEmbedder:
    def __init__(self, model_name: str = None):
        model_name = model_name or settings.EMBEDDING_MODEL_NAME

        def _load():
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(model_name)

        try:
            self._model = call_with_timeout(_load, _LOAD_TIMEOUT_SECONDS)
        except TimeoutError:
            raise TimeoutError(
                f"Timed out after {_LOAD_TIMEOUT_SECONDS}s downloading the Hugging "
                f"Face embedding model '{model_name}'. Check your network access to "
                f"huggingface.co, or set HF_ENDPOINT to your Artifactory HF proxy."
            ) from None

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, show_progress_bar=False).tolist()


def get_embedder() -> HuggingFaceEmbedder:
    return HuggingFaceEmbedder()