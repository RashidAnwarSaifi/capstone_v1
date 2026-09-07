"""Loads the app's CSS and JS helpers from ui/static/.

The assets live in real .css/.js files rather than Python strings so they
stay readable and syntax-highlighted. They're read on each rerun (cheap,
a few KB) so edits show up without restarting the server.
"""

from pathlib import Path

import streamlit as st

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def _read(filename: str) -> str:
    return (_STATIC_DIR / filename).read_text(encoding="utf-8")


def inject_css():
    st.markdown(f"<style>{_read('styles.css')}</style>", unsafe_allow_html=True)


def sync_sidebar_offset():
    """Keeps --sidebar-w in sync with the sidebar's real width. st.markdown()
    strips <script> tags for security, so this needs the st.iframe embed
    (same-origin, so it can reach window.parent)."""
    st.iframe(f"<script>{_read('sidebar_sync.js')}</script>", height=1)


def scroll_chat_to_bottom(nonce):
    """Scrolls the conversation to the latest message. 'nonce' (e.g. the
    message count) must change whenever there's new content - Streamlit skips
    an st.iframe whose HTML is byte-for-byte identical to the previous run,
    so an unchanging script would only ever scroll once."""
    st.iframe(f"<script>/* nonce:{nonce} */\n{_read('scroll_bottom.js')}</script>", height=1)


def bind_chat_history(nonce):
    """Binds Up/Down history navigation to the chat input in the parent page."""
    st.iframe(f"<script>/* nonce:{nonce} */\n{_read('chat_history.js')}</script>", height=1)


def bind_chat_actions(nonce):
    """Binds clipboard actions to the rendered chat messages."""
    st.iframe(f"<script>/* nonce:{nonce} */\n{_read('chat_actions.js')}</script>", height=1)