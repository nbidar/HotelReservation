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

    if "error" in content:
        return "error_handler"

    if ("reservation_assistant" in content) or ("reservation assistant" in content):
        return "reservation_assistant"

    if ("compliance_checker" in content) or ("compliance checker" in content):
        return "compliance_checker"

    if ("web_search" in content) or ("web search" in content):
        return "web_search_assistant"

    # Ported policy interruption (in-notebook behavior)
    if any(k in content.lower() for k in ("violate", "concern", "illegal", "manipultion")):
        raise NodeInterrupt(
            "Warning! The user request violates our policies. The conversation is forwarded to a human assistant for investigation."
        )

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

