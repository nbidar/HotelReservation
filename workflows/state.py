from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AppState(TypedDict, total=False):
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]

    # Quality/self-assessment (ported from notebooks)
    confidence: int

    # Derived signals for UI
    sentiment: str
    language: str  # kept for UI; English-only uses "en"

    # Reservation flow (deterministic booking + LLM extraction)
    booking_context: dict[str, Any]

    # Tool/agent artifacts for UI
    sql_artifact: Any
    rag_artifact: Any
    web_search_artifact: Any

    # Error handling
    error: Exception | None
    last_active_agent: str
    route_decision: dict[str, Any]
    compliance_terminal: bool
