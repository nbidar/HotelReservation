from __future__ import annotations

import uuid
from dataclasses import replace

import streamlit as st

from ui.chat_ui import append_assistant_message, append_user_message, render_chat_history, render_message
from ui.components import hero_header, inject_css
from ui.sidebar import render_sidebar
from utils.config import Settings, load_settings
from utils.logger import setup_logger
from workflows.graph import build_graph


@st.cache_resource(show_spinner=False)
def _graph_cached(settings: Settings, model: str, temperature: float):
    effective = replace(settings, openai_model=model, openai_temperature=temperature)
    logger = setup_logger("hotel-mas", effective.log_dir, effective.log_level)
    graph = build_graph(settings=effective, logger=logger)
    return graph, logger


def _ensure_session():
    st.session_state.setdefault("thread_id", str(uuid.uuid4()))
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("agent_activity", [])
    st.session_state.setdefault("session_history", [])
    st.session_state.setdefault("last_panels", {})
    st.session_state.setdefault("booking_context", {})
    st.session_state.setdefault("language", "en")


def _extract_tool_messages(messages):
    out = []
    for m in messages:
        if getattr(m, "type", None) == "tool":
            out.append({"name": getattr(m, "name", None), "content": getattr(m, "content", "")})
    return out


def main():
    st.set_page_config(page_title="Hotel MAS", layout="wide")
    inject_css()
    _ensure_session()

    # Load env config
    config_error: str | None = None
    try:
        settings = load_settings()
        api_ok = True
    except Exception as exc:
        settings = None
        api_ok = False
        config_error = str(exc)

    sidebar = render_sidebar(api_key_ok=api_ok)

    if config_error:
        st.error(config_error)

    if sidebar["new_thread"]:
        st.session_state["session_history"].append(st.session_state["thread_id"])
        st.session_state["thread_id"] = str(uuid.uuid4())
        st.session_state["chat_messages"] = []
        st.session_state["agent_activity"] = []
        st.session_state["last_panels"] = {}
        st.session_state["booking_context"] = {}
        st.rerun()

    if sidebar["clear"]:
        st.session_state["chat_messages"] = []
        st.session_state["agent_activity"] = []
        st.session_state["last_panels"] = {}
        st.session_state["booking_context"] = {}
        st.rerun()

    hero_header(
        title="AI‑Powered Multi‑Agent Hotel Customer Support",
        subtitle="Chat‑first support · Reservations (SQL) · Compliance RAG · Web search",
        status_text="Online",
    )

    tabs = st.tabs(["Chat", "Reservation", "Sentiment", "Web Search", "Debug"])

    with tabs[0]:
        with st.container():
            render_chat_history()
        user_text = st.chat_input("Ask about bookings, amenities, policies, or nearby places…")

        if user_text:
            append_user_message(user_text)
            render_message(st.session_state["chat_messages"][-1])
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown(
                    "<div class='glass' style='padding: 10px 12px; border-radius: 16px; display:inline-block;'>"
                    "<span class='muted'>Thinking</span>"
                    "<span class='muted' style='margin-left:8px'>•••</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

            if not settings:
                msg = config_error or "Missing `OPENAI_API_KEY`. Copy `.env.example` to `.env` and set your key."
                append_assistant_message(msg)
                st.rerun()

            graph, logger = _graph_cached(settings, sidebar["model"], sidebar["temperature"])

            final_text = None
            last_state = None
            try:
                # New message only; booking_context mirrored in session (checkpoint may not restore it).
                graph_input: dict = {
                    "messages": [st.session_state["chat_messages"][-1]],
                    "confidence": 100,
                }
                if st.session_state.get("booking_context"):
                    graph_input["booking_context"] = st.session_state["booking_context"]
                events = graph.stream(
                    graph_input,
                    config={"configurable": {"thread_id": st.session_state["thread_id"]}},
                    stream_mode="values",
                )
                for event in events:
                    last_state = event
                    last_msg = event["messages"][-1]
                    last_agent = event.get("last_active_agent")
                    if last_agent:
                        st.session_state["agent_activity"].append(last_agent)
                    final_text = getattr(last_msg, "content", None)
            except Exception as exc:
                err_name = type(exc).__name__
                if err_name == "AuthenticationError" or "invalid_api_key" in str(exc).lower():
                    append_assistant_message(
                        "OpenAI rejected the API key (401). Update `OPENAI_API_KEY` in `.env` with a valid "
                        "key from https://platform.openai.com/account/api-keys, then restart Streamlit."
                    )
                else:
                    append_assistant_message(f"Something went wrong while processing your message: {exc}")
                st.rerun()

            if final_text:
                append_assistant_message(final_text)
                with st.chat_message("assistant"):
                    st.markdown(final_text)

            if last_state:
                tool_msgs = _extract_tool_messages(last_state.get("messages", []))
                if last_state.get("booking_context") is not None:
                    st.session_state["booking_context"] = last_state["booking_context"]
                st.session_state["last_panels"] = {
                    "sentiment": last_state.get("sentiment", st.session_state.get("last_panels", {}).get("sentiment", "—")),
                    "language": "en",
                    "last_active_agent": last_state.get("last_active_agent", "—"),
                    "tool_messages": tool_msgs,
                    "rag_artifact": last_state.get("rag_artifact"),
                    "booking_artifact": last_state.get("sql_artifact"),
                    "booking_context": st.session_state.get("booking_context"),
                }

            st.rerun()

    with tabs[1]:
        st.markdown("### Reservation")
        st.caption("SQL tool outputs and booking-related results.")
        tool_msgs = st.session_state.get("last_panels", {}).get("tool_messages", [])
        booking_artifact = st.session_state.get("last_panels", {}).get("booking_artifact")
        sql_msgs = [m for m in tool_msgs if (m.get("name") or "").startswith("sql_db_")]
        if booking_artifact:
            st.json(booking_artifact)
        elif not sql_msgs:
            st.markdown(
                """
<div class="glass glow-border" style="padding: 16px 16px;">
  <div style="font-weight:750; font-size: 16px;">No reservation activity yet</div>
  <div class="muted" style="margin-top:6px;">
    Ask something like <span class="mono">“Book a Family Suite from 2026‑06‑12 to 2026‑06‑15”</span> to activate the SQL agent.
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            for m in sql_msgs:
                with st.expander(m.get("name") or "sql_tool", expanded=False):
                    st.code(m.get("content", ""))

    with tabs[2]:
        st.markdown("### Sentiment")
        sentiment = st.session_state.get("last_panels", {}).get("sentiment", "—")
        if sentiment == "Negative":
            st.warning("User sentiment is **Negative**. Consider escalation.", icon="⚠️")
        else:
            st.success(f"User sentiment: **{sentiment}**")

    with tabs[3]:
        st.markdown("### Web Search")
        st.caption("Tavily results appear as tool outputs when routed.")
        tool_msgs = st.session_state.get("last_panels", {}).get("tool_messages", [])
        tavily = [m for m in tool_msgs if (m.get("name") or "") == "tavily_search"]
        if not tavily:
            st.markdown(
                """
<div class="glass glow-border" style="padding: 16px 16px;">
  <div style="font-weight:750; font-size: 16px;">No web results yet</div>
  <div class="muted" style="margin-top:6px;">
    Ask: <span class="mono">“What are points of interest near 36 W 106th St, New York?”</span>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            for m in tavily:
                with st.expander("tavily_search results", expanded=True):
                    st.code(m.get("content", ""))

    with tabs[4]:
        st.markdown("### Debug")
        st.caption("Raw internal state + agent activity timeline.")
        st.json(st.session_state.get("last_panels", {}))
        with st.expander("Agent activity log", expanded=True):
            st.write(st.session_state.get("agent_activity", [])[-200:])


if __name__ == "__main__":
    main()

