from __future__ import annotations

from typing import Literal

from langgraph.errors import NodeInterrupt

from workflows.state import AppState


def choose_next_node(state: AppState) -> Literal[
    "reservation_assistant",
    "compliance_checker",
    "web_search_assistant",
    "error_handler",
    "__end__",
]:
    last_message = state["messages"][-1]
    content = getattr(last_message, "content", "") or ""
    decision = state.get("route_decision") or {}
    route = decision.get("route")

    if "error" in content:
        return "error_handler"

    if route == "compliance_checker":
        return "compliance_checker"

    if route == "reservation_assistant":
        return "reservation_assistant"

    if route == "web_search_assistant":
        return "web_search_assistant"

    if route == "direct_response":
        return "__end__"

    # Keep a narrow safety net if the coordinator produces a harmful direct reply.
    if any(k in content.lower() for k in ("violate", "concern", "illegal", "manipultion")):
        raise NodeInterrupt(
            "Warning! The user request violates our policies. The conversation is forwarded to a human assistant for investigation."
        )

    return "__end__"


def choose_compliance_next_node(state: AppState) -> Literal["rag_tools", "__end__"]:
    last_message = state["messages"][-1]
    if state.get("compliance_terminal"):
        return "__end__"
    if getattr(last_message, "tool_calls", None):
        return "rag_tools"
    return "__end__"


def choose_error_recovery(state: AppState) -> Literal[
    "alternative_model",
    "degraded_functionality_retrieval",
    "human_intervention",
]:
    err = state.get("error")
    from agents.error_handler_agent import LLMCallException, RetrievalException

    if isinstance(err, LLMCallException):
        return "alternative_model"
    if isinstance(err, RetrievalException):
        return "degraded_functionality_retrieval"
    return "human_intervention"
