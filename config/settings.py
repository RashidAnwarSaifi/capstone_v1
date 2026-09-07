"""Central place for all configuration. Everything is loaded from environment
variables (via a local .env file) so no config is hardcoded in the app."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"

for _dir in (DATA_DIR, UPLOAD_DIR, CHROMA_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# --- LLM provider selection (swap providers without touching code) ---
# "groq" (default) | "gemini" (secondary option)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# --- Embeddings (local Hugging Face sentence-transformer model, no API key
# needed - downloads from the HF Hub on first use, then cached on disk) ---
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# --- RAG tuning knobs ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
TOP_K = int(os.getenv("TOP_K", "4"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".csv", ".xlsx", ".xls"}