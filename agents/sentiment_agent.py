from __future__ import annotations

from textblob import TextBlob
from textblob.exceptions import MissingCorpusError
from textblob.sentiments import NaiveBayesAnalyzer, PatternAnalyzer

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from workflows.state import AppState
from utils.prompts import SENTIMENT_AGENT_PROMPT


@tool(response_format="content")
def get_sentiment(query: str) -> str:
    """Get the sentiment of a query."""
    sentiment_1 = TextBlob(query, analyzer=PatternAnalyzer()).sentiment.polarity
    sentiment_2 = None
    try:
        # NaiveBayesAnalyzer requires TextBlob corpora (often missing on Streamlit Cloud).
        sentiment_2 = TextBlob(query, analyzer=NaiveBayesAnalyzer()).sentiment.p_neg
    except MissingCorpusError:
        sentiment_2 = None

    # Pattern polarity is the primary signal. NaiveBayes alone mislabels neutral
    # booking requests (e.g. "book a Deluxe room") as strongly negative.
    if sentiment_1 < -0.3:
        return "Negative"
    if sentiment_2 is not None and sentiment_2 > 0.85 and sentiment_1 < 0.0:
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

    # Prefer deterministic tool output for UI (LLM content is often empty when tools are called).
    last_human = ""
    for message in reversed(messages):
        if getattr(message, "type", None) in ("human", "user") or isinstance(message, HumanMessage):
            last_human = (getattr(message, "content", None) or "").strip()
            if last_human:
                break
    sentiment = get_sentiment.invoke({"query": last_human}) if last_human else "Positive"
    if not sentiment and getattr(out, "content", None):
        sentiment = str(out.content).strip()

    return {"messages": [out], "confidence": state.get("confidence", 100), "sentiment": sentiment}

