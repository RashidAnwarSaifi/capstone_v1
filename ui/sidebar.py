"""Sidebar: page navigation, chat list, user badge."""

import streamlit as st

from ui.state import new_conversation_dict, request_save

NAV_ITEMS = [
    ("home", "💬 Home"),
    ("agents", "🤖 Agents"),
    ("sources", "📁 Document Upload"),
    ("settings", "⚙️ Settings"),
    ("architecture", "📐 Architecture"),
    ("instructions", "📖 Instructions"),
]


def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧠 Rashid A Saifi GenAI")

        for key, label in NAV_ITEMS:
            is_active = st.session_state.get("page", "home") == key
            if st.button(label, use_container_width=True, type="primary" if is_active else "secondary", key=f"nav_{key}"):
                st.session_state.page = key
                st.rerun()

        st.divider()

        if st.button("➕ New chat", use_container_width=True):
            conv = new_conversation_dict()
            st.session_state.conversations.insert(0, conv)
            st.session_state.active_conv_id = conv["id"]
            request_save("conversations_dirty")
            st.session_state.page = "home"
            st.rerun()

        st.caption("Recent chats")
        for conv in st.session_state.conversations:
            cols = st.columns([5, 1])
            is_active = conv["id"] == st.session_state.active_conv_id
            with cols[0]:
                if st.button(
                    conv["title"] or "New chat",
                    key=f"conv_{conv['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.active_conv_id = conv["id"]
                    st.session_state.page = "home"
                    st.rerun()
            with cols[1]:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    st.session_state.conversations = [
                        c for c in st.session_state.conversations if c["id"] != conv["id"]
                    ]
                    if not st.session_state.conversations:
                        st.session_state.conversations = [new_conversation_dict()]
                    st.session_state.active_conv_id = st.session_state.conversations[0]["id"]
                    request_save("conversations_dirty")
                    st.rerun()

    with st.container(key="sidebar_user_badge"):
        email = "rashid.saifi@rbccm.com"
        display_name = " ".join(p.capitalize() for p in email.split("@")[0].split("."))
        initials = "".join(p[0].upper() for p in display_name.split()[:2])
        st.caption(f"👤 {initials} • {display_name}")