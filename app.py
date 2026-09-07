"""Streamlit UI: upload enterprise documents, build a searchable knowledge
base, and chat with one or more agents that answer grounded in those
documents. Conversations and LLM setting overrides persist in the
browser's IndexedDB (see storage/indexeddb.py), not on the server disk."""

import streamlit as st

from ui.home import render_home
from ui.pages import (
    render_agents,
    render_architecture,
    render_instructions,
    render_settings,
    render_sources,
)
from ui.sidebar import render_sidebar
from ui.state import flush_pending_saves, hydrate_from_indexeddb
from ui.styles import inject_css, sync_sidebar_offset

st.set_page_config(page_title="Rashid A Saifi GenAI Agent", page_icon="🧠", layout="wide")

PAGES = {
    "home": render_home,
    "agents": render_agents,
    "sources": render_sources,
    "settings": render_settings,
    "architecture": render_architecture,
    "instructions": render_instructions,
}


def main():
    inject_css()
    hydrate_from_indexeddb()
    if not st.session_state.get("hydrated"):
        st.info("Loading your saved conversations and settings...")
        return

    flush_pending_saves()

    st.session_state.setdefault("page", "home")
    render_sidebar()
    sync_sidebar_offset()

    PAGES[st.session_state.page]()


if __name__ == "__main__":
    main()