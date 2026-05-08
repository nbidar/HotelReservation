from __future__ import annotations

from datetime import datetime

from langchain_core.messages import AIMessage, SystemMessage

from utils.prompts import SQL_RESERVATION_PROMPT
from workflows.state import AppState


def reservation_node(state: AppState, llm, llm_with_sql_tools) -> AppState:
    """
    Reservation / SQL agent (ported from Agent2/Agent3).
    """
    messages = state["messages"]
    date_today = datetime.now().strftime("%Y-%m-%d")

    date_check_sys_msg = SystemMessage(
        content=(
            "If the current request is related to a reservation. Make sure that all the dates are not in the past.\n"
            f"Today is {date_today}. Answer with the single digit 0 if there is any problem otherwise answer with the single digit 1."
        )
    )

    check = str(llm.invoke([date_check_sys_msg] + messages).content)
    if " 0" in check or check.strip() == "0":
        response = llm.invoke(
            [SystemMessage(content=SQL_RESERVATION_PROMPT)]
            + messages
            + [AIMessage(content=f"The reservation is in past. Please provide the actual dates. The date today is {date_today}")]
        )
        return {"messages": [response], "confidence": state.get("confidence", 100), "last_active_agent": "reservation_assistant"}

    response = llm_with_sql_tools.invoke([SystemMessage(content=SQL_RESERVATION_PROMPT)] + messages)
    return {"messages": [response], "confidence": state.get("confidence", 100), "last_active_agent": "reservation_assistant"}

