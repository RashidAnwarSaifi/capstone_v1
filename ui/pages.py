"""Smaller pages: Agents catalog, Architecture diagram, Instructions (README),
Sources (upload/delete), and Settings (LLM provider config)."""

import streamlit as st

from agents.registry import list_agents
from config import settings
from ui.state import (
    PROVIDER_FIELDS,
    delete_source,
    get_vectorstore,
    ingest_uploaded_file,
    request_save,
)
from utils.guardrails import ValidationError


def render_agents():
    st.title("Agents")
    st.caption("Agents available to select in the chat window. Pick one or several per question.")
    for agent in list_agents():
        with st.container(border=True):
            st.subheader(agent.label)
            st.write(agent.description)
            st.caption(f"key: `{agent.key}`")


def render_architecture():
    st.title("Architecture")
    html_path = settings.BASE_DIR / "docs" / "architecture.html"
    if not html_path.exists():
        st.error(f"Diagram not found at {html_path}")
        return
    st.iframe(html_path, height=900)


def render_instructions():
    st.title("Instructions")
    readme_path = settings.BASE_DIR / "README.md"
    if not readme_path.exists():
        st.error(f"README not found at {readme_path}")
        return
    st.markdown(readme_path.read_text(encoding="utf-8"))


def render_sources():
    st.title("Document Upload")

    uploaded_files = st.file_uploader(
        "Upload documents (PDF, TXT, CSV, XLSX)",
        type=["pdf", "txt", "csv", "xlsx", "xls"],
        accept_multiple_files=True,
    )
    if uploaded_files and st.button("Process documents"):
        with st.spinner("Processing and embedding documents..."):
            for uploaded_file in uploaded_files:
                try:
                    n_chunks = ingest_uploaded_file(uploaded_file)
                    st.success(f"{uploaded_file.name}: {n_chunks} chunks indexed")
                except ValidationError as e:
                    st.error(f"{uploaded_file.name}: {e}")
                except Exception as e:
                    st.error(f"{uploaded_file.name}: Failed to process ({e})")

    st.divider()
    st.subheader("Indexed documents")
    sources = get_vectorstore().list_sources()
    if not sources:
        st.info("No documents indexed yet.")
        return

    for name in sources:
        cols = st.columns([6, 1])
        with cols[0]:
            st.write(f"📄 {name}")
        with cols[1]:
            if st.button("🗑️ Delete", key=f"delete_{name}"):
                delete_source(name)
                st.rerun()

    st.caption(
        "Use the 'Limit to documents' selector on the Home/chat page to scope "
        "retrieval to specific files; leave it empty to search all documents."
    )

    st.divider()
    if st.button("🗑️ Clear entire knowledge base"):
        get_vectorstore().clear()
        st.session_state.selected_sources = []
        st.success("Knowledge base cleared.")
        st.rerun()


def render_settings():
    st.title("Settings")
    st.caption(
        "Changes are saved to your browser's IndexedDB and override the "
        "`.env` defaults for this browser. Use Reset to fall back to `.env`."
    )

    overrides = st.session_state.llm_overrides
    provider_options = list(PROVIDER_FIELDS.keys())
    current_provider = overrides.get("provider") or settings.LLM_PROVIDER
    provider = st.selectbox(
        "LLM Provider",
        options=provider_options,
        index=provider_options.index(current_provider) if current_provider in provider_options else 0,
    )

    st.markdown(f"**{provider.upper()} settings**")
    field_values = {}
    for override_key, label, env_default, is_secret in PROVIDER_FIELDS[provider]:
        current_value = overrides.get(override_key, "")
        placeholder = "(using .env default)" if not current_value else ""
        field_values[override_key] = st.text_input(
            label,
            value=current_value,
            type="password" if is_secret else "default",
            placeholder=placeholder,
            key=f"field_{override_key}",
        )
        if is_secret:
            st.caption(f".env default: {'set' if env_default else 'not set'}")
        else:
            st.caption(f".env default: {env_default or '(not set)'}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save settings", use_container_width=True):
            new_overrides = dict(overrides)
            new_overrides["provider"] = provider
            for k, v in field_values.items():
                if v:
                    new_overrides[k] = v
                else:
                    new_overrides.pop(k, None)
            st.session_state.llm_overrides = new_overrides
            request_save("llm_overrides_dirty")
            st.success("Settings saved to this browser.")
            st.rerun()
    with col2:
        if st.button("🔄 Reset to .env defaults", use_container_width=True):
            st.session_state.llm_overrides = {}
            request_save("llm_overrides_reset")
            st.success("Reset. Now using .env defaults.")
            st.rerun()

    st.divider()
    st.subheader("Retrieval (read-only, set via .env)")
    st.write(f"Embedding model: `{settings.EMBEDDING_MODEL_NAME}` (Hugging Face)")
    st.write(f"Chunk size / overlap: `{settings.CHUNK_SIZE}` / `{settings.CHUNK_OVERLAP}`")
    st.write(f"Top K retrieved chunks: `{settings.TOP_K}`")