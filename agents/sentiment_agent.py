from __future__ import annotations

from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer, PatternAnalyzer

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from workflows.state import AppState
from utils.prompts import SENTIMENT_AGENT_PROMPT


@tool(response_format="content")
def get_sentiment(query: str) -> str:
    """Get the sentiment of a query."""
    sentiment_1 = TextBlob(query, analyzer=PatternAnalyzer()).sentiment.polarity
    sentiment_2 = TextBlob(query, analyzer=NaiveBayesAnalyzer()).sentiment.p_neg
    if (sentiment_1 < -0.3) or (sentiment_2 > 0.6):
        return "Negative"
    return "Positive"


def sentiment_node(state: AppState, llm_with_sentiment_tools) -> AppState:
    """
    Ported from `Sentiment_Analysis.ipynb`.
    English-only: multilingual translation/detection removed.
    """
    messages = state["messages"]
    last_message = messages[-1]

    sys_msg = SystemMessage(content=SENTIMENT_AGENT_PROMPT)

    out = llm_with_sentiment_tools.invoke([sys_msg] + messages)

    # The tool result is emitted as an AI message; UI can also read `state["sentiment"]`
    state["sentiment"] = str(getattr(out, "content", "")).strip()
    return {"messages": [out], "confidence": state.get("confidence", 100), "sentiment": state.get("sentiment", "")}

