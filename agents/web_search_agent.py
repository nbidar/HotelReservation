from __future__ import annotations

from langchain_core.messages import SystemMessage

from utils.prompts import WEB_SEARCH_AGENT_PROMPT
from workflows.state import AppState


def web_search_node(state: AppState, llm_with_search_tools) -> AppState:
    messages = state["messages"]
    sys_msg = SystemMessage(content=WEB_SEARCH_AGENT_PROMPT)
    response = llm_with_search_tools.invoke([sys_msg] + messages)
    return {"messages": [response], "confidence": state.get("confidence", 100), "last_active_agent": "web_search_assistant"}

