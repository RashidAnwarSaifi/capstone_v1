"""Session/conversation state, IndexedDB hydration, and document ingestion."""

import uuid
from datetime import datetime

import streamlit as st

from config import settings
from ingestion.chunker import chunk_text
from ingestion.loaders import load_document
from storage.indexeddb import LOADING, idb_delete, idb_get_multi, idb_set
from utils.guardrails import validate_upload
from vectorstore.store import VectorStore

PROVIDER_FIELDS = {
    "groq": [
        ("groq_api_key", "API Key", settings.GROQ_API_KEY, True),
        ("groq_model", "Model Name", settings.GROQ_MODEL, False),
    ],
    "gemini": [
        ("gemini_api_key", "API Key", settings.GEMINI_API_KEY, True),
        ("gemini_model", "Model Name", settings.GEMINI_MODEL, False),
    ],
}


@st.cache_resource
def get_vectorstore() -> VectorStore:
    return VectorStore()


def hydrate_from_indexeddb():
    if st.session_state.get("hydrated"):
        return

    hydrated_values = idb_get_multi(["conversations", "llm_overrides"])
    if hydrated_values is LOADING:
        return  # browser round trip still in flight; Streamlit will rerun us

    conversations = hydrated_values.get("conversations")
    overrides = hydrated_values.get("llm_overrides")

    st.session_state.conversations = conversations if isinstance(conversations, list) else []
    st.session_state.llm_overrides = overrides if isinstance(overrides, dict) else {}
    if not st.session_state.conversations:
        st.session_state.conversations = [new_conversation_dict()]
    st.session_state.active_conv_id = st.session_state.conversations[0]["id"]
    st.session_state.hydrated = True


def new_conversation_dict() -> dict:
    return {
        "id": uuid.uuid4().hex[:12],
        "title": "New chat",
        "messages": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def get_active_conversation() -> dict:
    for conv in st.session_state.conversations:
        if conv["id"] == st.session_state.active_conv_id:
            return conv
    conv = new_conversation_dict()
    st.session_state.conversations.insert(0, conv)
    st.session_state.active_conv_id = conv["id"]
    return conv


def request_save(flag: str) -> None:
    """Mark a value dirty; pair with an entry in `flush_pending_saves()`."""
    st.session_state[flag] = True


def flush_pending_saves() -> None:
    """Retry any save `request_save()` flagged, one at a time (see
    storage/indexeddb.py - more than one idb_store round trip in flight at
    once is unreliable). Doesn't block page rendering: an unconfirmed save
    just gets retried on the next rerun, whatever triggers it."""
    if _flush("conversations_dirty", lambda: idb_set("conversations", st.session_state.conversations)):
        return
    if _flush("llm_overrides_dirty", lambda: idb_set("llm_overrides", st.session_state.llm_overrides)):
        return
    _flush("llm_overrides_reset", lambda: idb_delete("llm_overrides"))


def _flush(flag: str, write) -> bool:
    """Returns True if `write()` ran this call, so the caller stops there."""
    if not st.session_state.get(flag):
        return False
    if write():
        st.session_state[flag] = False
    return True


def ingest_uploaded_file(uploaded_file) -> int:
    validate_upload(uploaded_file.name, uploaded_file.size)
    dest = settings.UPLOAD_DIR / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    text = load_document(dest)
    chunks = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
    return get_vectorstore().add_documents(chunks, source=uploaded_file.name)


def delete_source(name: str):
    get_vectorstore().delete_source(name)
    upload_path = settings.UPLOAD_DIR / name
    if upload_path.exists():
        upload_path.unlink()
    st.session_state.selected_sources = [
        s for s in st.session_state.get("selected_sources", []) if s != name
    ]