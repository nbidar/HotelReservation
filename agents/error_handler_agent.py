from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import Command

from utils.prompts import CONVERSATION_COORDINATOR_PROMPT
from workflows.state import AppState


class NotSureException(Exception):
    pass


class LLMCallException(Exception):
    pass


class RetrievalException(Exception):
    pass


def error_handler_node(state: AppState, logger) -> AppState:
    err = state.get("error")
    logger.error("Error routed to handler: %s", str(err))
    return {"messages": state["messages"], "confidence": state.get("confidence", 100), "error": err, "last_active_agent": "error_handler"}


def human_intervention_node(state: AppState, llm_fallback) -> AppState:
    """
    Fallback to a stronger/alternative model for critical errors.
    """
    response = llm_fallback.invoke([SystemMessage(content=CONVERSATION_COORDINATOR_PROMPT)] + state["messages"])
    return {"messages": [response], "confidence": state.get("confidence", 100), "error": None, "last_active_agent": "human_intervention"}


def alternative_model_node(state: AppState, llm_fallback) -> AppState:
    response = llm_fallback.invoke([SystemMessage(content=CONVERSATION_COORDINATOR_PROMPT)] + state["messages"])
    return {"messages": [response], "confidence": state.get("confidence", 100), "error": None, "last_active_agent": "alternative_model"}


def degraded_functionality_node(state: AppState) -> Command:
    """
    Uses a hard-coded document set when retrieval fails (ported from notebook behavior).
    """
    message = AIMessage(
        """The system should refuse or redirect queries with:
- Illegal requests (e.g., falsifying documents, fraudulent bookings).
- Hate speech, harassment, or explicit threats toward individuals or groups.
- Offensive, obscene, or otherwise harmful content.
- Requests for information about other guests (never share names or dates of stay).

Hard-coded document set was used as the vectorDB doesn't work."""
    )
    from langgraph.graph.message import add_messages

    return Command(
        update={
            "messages": add_messages(state["messages"], message),
            "confidence": state.get("confidence", 100),
            "error": None,
            "last_active_agent": "degraded_functionality_retrieval",
        },
        goto="retriever",
    )

