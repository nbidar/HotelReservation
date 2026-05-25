from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from utils.prompts import CONVERSATION_COORDINATOR_PROMPT
from workflows.state import AppState


class RouteDecision(BaseModel):
    route: Literal[
        "direct_response",
        "reservation_assistant",
        "compliance_checker",
        "web_search_assistant",
    ]
    reason: str = Field(default="general_info")
    reply: str = Field(default="")
    route_confidence: int = Field(default=90, ge=0, le=100)


def conversation_node(state: AppState, llm) -> AppState:
    """
    Conversation Coordinator (ported from Agent1/Agent2/Agent3 + sentiment/multilingual variants).

    - Computes an LLM self-confidence score (0-100)
    - If confident, produces the routing/assistant response
    - English-only responses (multilingual stack removed)
    """
    messages = state["messages"]

    # Self-confidence check (ported logic)
    date_check_sys_msg = SystemMessage(
        content="Please rate how confident you are that the AI assistant understands the user's request correctly from 0 to 100. Answer only with this number without any additional text."
    )
    confidence_raw = llm.invoke([date_check_sys_msg] + messages).content
    try:
        confidence = int(str(confidence_raw).strip().split()[0])
    except Exception:
        confidence = 90

    state["confidence"] = confidence

    if confidence <= 80:
        apology = AIMessage(
            content="You are extremely unsure. Please apologize for that and ask the user to repeat everything."
        )
        response = llm.invoke([SystemMessage(content=CONVERSATION_COORDINATOR_PROMPT)] + messages + [apology])
        return {
            "messages": [response],
            "confidence": confidence,
            "last_active_agent": "conv_assistant",
            "route_decision": {
                "route": "direct_response",
                "reason": "low_understanding_confidence",
                "reply": str(response.content),
                "route_confidence": confidence,
            },
        }

    router = llm.with_structured_output(RouteDecision)
    decision = router.invoke([SystemMessage(content=CONVERSATION_COORDINATOR_PROMPT)] + messages)
    assistant_msg = AIMessage(content=decision.reply) if decision.route == "direct_response" else AIMessage(content="")

    return {
        "messages": [assistant_msg],
        "confidence": confidence,
        "last_active_agent": "conv_assistant",
        "route_decision": decision.model_dump(),
    }

