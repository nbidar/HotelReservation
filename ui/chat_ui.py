from __future__ import annotations

from datetime import datetime

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage


def _fmt_ts(ts: str | None) -> str:
    if not ts:
        return ""
    return str(ts).strip()


def render_message(msg: HumanMessage | AIMessage) -> None:
    """Render one chat bubble (e.g. show the latest user turn before the reply arrives)."""
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    avatar = "👤" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.content)
        ts = _fmt_ts(msg.additional_kwargs.get("ts", ""))
        if ts:
            st.markdown(f"<div class='ts'>{ts}</div>", unsafe_allow_html=True)


def render_chat_history() -> None:
    for msg in st.session_state.get("chat_messages", []):
        render_message(msg)


def append_user_message(text: str) -> None:
    msg = HumanMessage(content=text, additional_kwargs={"ts": datetime.now().strftime("%H:%M:%S")})
    st.session_state.setdefault("chat_messages", []).append(msg)


def append_assistant_message(text: str) -> None:
    msg = AIMessage(content=text, additional_kwargs={"ts": datetime.now().strftime("%H:%M:%S")})
    st.session_state.setdefault("chat_messages", []).append(msg)
