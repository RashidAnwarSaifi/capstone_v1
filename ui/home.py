"""Home / chat page: message history, agent picker, and the send flow."""

from datetime import datetime

import streamlit as st

from agents.registry import AGENTS, DEFAULT_AGENT_KEYS, list_agents
from llm.factory import get_llm
from ui.state import get_active_conversation, get_vectorstore, request_save
from ui.styles import scroll_chat_to_bottom
from utils.guardrails import ValidationError, validate_query


def render_home():
    st.title("How can I help you?")
    conv = get_active_conversation()

    for message in conv["messages"]:
        with st.chat_message(message["role"]):
            if message.get("agent"):
                st.caption(f"🤖 {message['agent']}")
            st.markdown(message["content"])
            if message.get("sources"):
                st.caption("Sources: " + ", ".join(message["sources"]))
            if message.get("trace"):
                trace_label = f"Agent trace - {message['agent']}" if message.get("agent") else "Agent trace"
                with st.expander(trace_label):
                    st.json(message["trace"])
            if message.get("timestamp"):
                st.markdown(f'<div class="msg-timestamp">{message["timestamp"]}</div>', unsafe_allow_html=True)

    pending = st.session_state.get("pending_turn")
    busy = pending is not None and pending.get("conv_id") == conv["id"]

    agent_options = {a.key: a.label for a in list_agents()}
    all_sources = get_vectorstore().list_sources()

    # Rendered before the (possibly slow) agent call below so it's on screen
    # immediately; position:fixed CSS means its code position doesn't affect
    # where it appears on screen.
    with st.container(key="chat_input_bar"):
        with st.form("chat_form", clear_on_submit=True, border=True):
            with st.container(key="input_row"):
                input_cols = st.columns([12, 1])
                with input_cols[0]:
                    query = st.text_input(
                        "Message",
                        label_visibility="collapsed",
                        placeholder="Ask a question about your documents...",
                        disabled=busy,
                    )
                with input_cols[1]:
                    with st.container(key="send_btn"):
                        submitted = st.form_submit_button(">", use_container_width=True, disabled=busy)

            toolbar_cols = st.columns(2)
            with toolbar_cols[0]:
                selected_agents = st.multiselect(
                    "Agents",
                    options=list(agent_options.keys()),
                    default=st.session_state.get("selected_agents", DEFAULT_AGENT_KEYS),
                    format_func=lambda k: agent_options[k],
                    key="selected_agents",
                    disabled=busy,
                )
            with toolbar_cols[1]:
                st.multiselect(
                    "Limit to documents (optional)",
                    options=all_sources,
                    default=[s for s in st.session_state.get("selected_sources", []) if s in all_sources],
                    key="selected_sources",
                    disabled=busy,
                )

    scroll_chat_to_bottom(len(conv["messages"]))

    if busy:
        _process_pending_turn(conv, pending)
        st.rerun()  # refresh so history shows the finished answer
        return

    if not submitted or not query:
        return

    try:
        query = validate_query(query)
    except ValidationError as e:
        st.error(str(e))
        return

    conv["messages"].append(
        {"role": "user", "content": query, "timestamp": datetime.now().strftime("%I:%M %p")}
    )
    if conv["title"] in ("New chat", "", None):
        conv["title"] = query[:40] + ("..." if len(query) > 40 else "")
    request_save("conversations_dirty")

    st.session_state.pending_turn = {"conv_id": conv["id"], "query": query, "agents": selected_agents}
    st.rerun()


def _process_pending_turn(conv: dict, pending: dict):
    query = pending["query"]
    selected_agents = pending["agents"]

    if not selected_agents:
        st.warning("Select at least one agent to get a response.")
        st.session_state.pending_turn = None
        return

    badge = st.empty()
    badge.markdown('<span class="generating-badge">● generating...</span>', unsafe_allow_html=True)

    try:
        llm = get_llm(st.session_state.llm_overrides)
        vectorstore = get_vectorstore()
        history_before = list(conv["messages"][:-1])
        sources_filter = st.session_state.get("selected_sources") or None

        for agent_key in selected_agents:
            agent = AGENTS[agent_key]
            with st.chat_message("assistant"):
                st.caption(f"🤖 {agent.label}")
                with st.spinner(f"{agent.label} is thinking..."):
                    try:
                        result = agent.run(query, history_before, llm, vectorstore, sources=sources_filter)
                    except Exception as e:
                        result = {"answer": f"⚠️ {e}", "sources": [], "trace": {}}
                    st.markdown(result["answer"])
                    if result.get("sources"):
                        st.caption("Sources: " + ", ".join(result["sources"]))
                    with st.expander(f"Agent trace - {agent.label}"):
                        st.json(result.get("trace", {}))
                    timestamp = datetime.now().strftime("%I:%M %p")
                    st.markdown(f'<div class="msg-timestamp">{timestamp}</div>', unsafe_allow_html=True)

                    conv["messages"].append(
                        {
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": result.get("sources", []),
                            "agent": agent.label,
                            "trace": result.get("trace", {}),
                            "timestamp": timestamp,
                        }
                    )

        request_save("conversations_dirty")
    except Exception as e:
        st.error(f"Something went wrong while handling your message: {e}")
        st.exception(e)
    finally:
        badge.empty()
        st.session_state.pending_turn = None