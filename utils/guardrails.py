"""Basic reliability/safety checks: input validation and a lightweight
grounding check to reduce hallucinated answers."""

from pathlib import Path

from config import settings

NO_CONTEXT_MESSAGE = (
    "I don't have enough information in the uploaded documents to answer that. "
    "Try rephrasing the question or upload a document that covers this topic."
)


class ValidationError(Exception):
    pass


def validate_query(query: str) -> str:
    query = (query or "").strip()
    if not query:
        raise ValidationError("Please enter a question.")
    if len(query) > 2000:
        raise ValidationError("Question is too long (max 2000 characters).")
    return query


def validate_upload(filename: str, size_bytes: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in settings.SUPPORTED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(settings.SUPPORTED_EXTENSIONS))}"
        )
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(f"File exceeds the {settings.MAX_UPLOAD_MB}MB upload limit.")


def has_sufficient_context(retrieved_chunks: list[dict]) -> bool:
    return len(retrieved_chunks) > 0