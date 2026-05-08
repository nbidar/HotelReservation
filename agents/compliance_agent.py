from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from rag.retriever import similarity_search
from utils.prompts import COMPLIANCE_RAG_PROMPT_TEMPLATE
from workflows.state import AppState


def make_retrieve_tool(vectorstore):
    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        return similarity_search(vectorstore, query=query, k=2)

    return retrieve


def compliance_node(state: AppState, llm_with_rag_tools, rules_text: str) -> AppState:
    """
    Compliance / RAG agent (ported from Agent3 + later notebooks).
    """
    messages = state["messages"]
    sys_msg = SystemMessage(content=COMPLIANCE_RAG_PROMPT_TEMPLATE.format(rules_text=rules_text))
    response = llm_with_rag_tools.invoke([sys_msg] + messages)
    return {"messages": [response], "confidence": state.get("confidence", 100), "last_active_agent": "compliance_checker"}


def compliance_generate_node(state: AppState, llm, rules_text: str) -> AppState:
    """
    Ported from the notebooks' `generate()` node: after tool execution, produce a compliance assessment message.
    """
    messages = state["messages"]

    # Collect recent tool messages
    recent_tool_messages = []
    for message in reversed(messages):
        if getattr(message, "type", None) == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = list(reversed(recent_tool_messages))

    state["rag_artifact"] = [getattr(m, "content", "") for m in tool_messages]

    conversation_messages = [
        message
        for message in messages
        if getattr(message, "type", None) in ("human", "system")
        or (getattr(message, "type", None) == "ai" and not getattr(message, "tool_calls", None))
    ]

    sys_msg = SystemMessage(content=COMPLIANCE_RAG_PROMPT_TEMPLATE.format(rules_text=rules_text))
    response = llm.invoke([sys_msg] + conversation_messages)
    return {
        "messages": [response],
        "confidence": state.get("confidence", 100),
        "rag_artifact": state.get("rag_artifact"),
        "last_active_agent": "retriever",
    }

